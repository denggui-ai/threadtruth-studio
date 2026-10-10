"""Real-person planning and per-image attachments; synthetic fixtures, no calls."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'real_face_task', ROOT / 'skills/threadtruth-studio/scripts/web-task.py')
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class RealFacePlanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.task = self.root / 'task'
        self.files = {name: self.image(name, color) for name, color in (
            ('garment', 'red'), ('back', 'green'), ('front', 'blue'),
            ('left', 'yellow'), ('right', 'cyan'), ('supplement', 'purple'),
            ('style', 'white'), ('target', 'black'))}
        self.model = dict(source_type='real', scope='face', subject='adult female model',
                          locked=['retain the original facial features'], adjustable=[],
                          consent_note='Express likeness permission recorded')
        self.context = dict(outfit='current-knit', style='french-effortless', mode='C',
                            output_form='human model', size=[20, 30], first_pose=1)

    def image(self, name, color):
        path = self.root / (name + '.png')
        Image.new('RGB', (20, 30), color).save(path)
        return path

    def sha(self, name):
        return m.digest(self.files[name])

    def inventory(self, extra=False, edit=False):
        rows = [dict(path=str(self.files['garment']), role='garment-source'),
                dict(path=str(self.files['front']), role='identity-reference')]
        if extra:
            rows.extend([dict(path=str(self.files['back']), role='garment-source'),
                         dict(path=str(self.files['left']), role='identity-reference'),
                         dict(path=str(self.files['right']), role='identity-reference'),
                         dict(path=str(self.files['style']), role='aesthetic-reference'),
                         dict(path=str(self.files['supplement']), role='model-supplement',
                              scope='face', sha256=self.sha('supplement'),
                              confirmation_note='Human accepted face continuity only')])
        if edit:
            rows.append(dict(path=str(self.files['target']), role='edit-target'))
        return rows

    def look(self, view='front', selected=None, visible=True, body='relaxed standing'):
        return dict(body_action=body, head_view=view if visible else 'hidden',
                    gaze='look naturally toward camera' if visible else 'face outside the frame',
                    face_visible=visible,
                    reference_sha256s=[self.sha(x) for x in (selected or ['garment', 'front'])],
                    selection_note='Use product and main original face; omit unrelated or redundant views')

    def plan(self, count=1, extra=False):
        coverage = [dict(sha256=self.sha('front'), views=['front'], note='Clear original frontal reference')]
        if extra:
            coverage.extend([dict(sha256=self.sha('left'), views=['left-three-quarter'], note='Clear original left turn'),
                             dict(sha256=self.sha('right'), views=['right-profile'], note='Clear original right profile')])
        return dict(primary_identity_sha256=self.sha('front'), coverage=coverage,
                    looks=[self.look(body='body action ' + str(i)) for i in range(count)])

    def create(self, plan=None, count=1, extra=False, context=None, model=None, edit=False):
        return m.create(self.task, self.inventory(extra=extra, edit=edit),
                        ['Photograph this garment; conflicting default head turn must yield.'] * count,
                        (20, 30), model=self.model if model is None else model,
                        context=self.context if context is None else context, route='codex_native',
                        real_face_plan=self.plan(count, extra) if plan is None else plan)

    def accept_first(self):
        m.update(self.task, 'authorize', limit=1, note='Human explicitly approves a single call')
        m.update(self.task, 'reserve', look=1, ready=True, refs=m.reference_hashes(self.task, 1))
        output = self.image('accepted-output', 'orange')
        m.update(self.task, 'returned', look=1, file=output)
        m.update(self.task, 'accept', look=1, qa='qa-pass', note='Synthetic ledger acceptance')
        m.update(self.task, 'confirm-model', look=1, note='Human accepts this exact output')
        return output

    def continue_args(self, looks):
        return dict(note='Human authorizes five more images', approval_id='five-new-images',
                    context=self.context, prompts=['next garment image'] * 5,
                    real_face_looks=looks)

    def test_large_inventory_freezes_every_input_but_exports_only_the_selected_order(self):
        plan = self.plan(extra=True)
        plan['looks'][0] = self.look('left-three-quarter', ['left', 'garment', 'front'])
        data = self.create(plan, extra=True)
        self.assertEqual(len(data['references']), 7)
        self.assertEqual(data['real_face_plan'], plan)
        self.assertEqual(data['attempts'], 0)
        self.assertIsNone(data['authorization'])
        m.export(self.task)
        handoff = self.task / 'handoff/look-1'
        request = json.loads((handoff / 'request.json').read_text())
        self.assertEqual([m.digest(p) for p in request['referenced_image_paths']],
                         [self.sha('left'), self.sha('garment'), self.sha('front')])
        manifest = json.loads((handoff / 'manifest.json').read_text())
        self.assertEqual(manifest['real_face_plan'], plan)
        self.assertEqual(manifest['real_face_look'], plan['looks'][0])
        self.assertEqual(set(manifest['omitted_reference_sha256s']),
                         {self.sha(x) for x in ['back', 'right', 'style', 'supplement']})
        self.assertEqual(m.read(self.task)['references'], data['references'])

    def test_coverage_cannot_be_supplied_by_an_ai_supplement_or_style_reference(self):
        for name in ('supplement', 'style'):
            plan = self.plan(extra=True)
            plan['coverage'].append(dict(sha256=self.sha(name), views=['left-profile'], note='Not an original'))
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.create(plan, extra=True)
            self.assertFalse(self.task.exists())

    def test_only_covered_original_directions_are_allowed_without_mirroring(self):
        for view in ('left-profile', 'right-three-quarter', 'right-profile', 'unknown'):
            plan = self.plan()
            plan['looks'][0] = self.look(view)
            with self.subTest(view=view), self.assertRaises(ValueError):
                self.create(plan)
            self.assertFalse(self.task.exists())
        plan = self.plan()
        plan['looks'][0] = self.look('near-front')
        self.create(plan)

    def test_side_direction_requires_its_original_in_the_actual_selected_attachments(self):
        plan = self.plan(extra=True)
        plan['looks'][0] = self.look('left-three-quarter')
        with self.assertRaises(ValueError):
            self.create(plan, extra=True)
        self.assertFalse(self.task.exists())

    def test_side_request_uses_image_direction_and_cannot_mirror_to_other_side(self):
        plan = self.plan(extra=True)
        plan['looks'][0] = self.look('left-three-quarter', ['front', 'left', 'garment'])
        self.create(plan, extra=True)
        m.export(self.task)
        request = json.loads((self.task / 'handoff/look-1/request.json').read_text())
        self.assertIn('head facing image-left in a three-quarter view', request['prompt'])
        self.assertNotIn('head facing image-right', request['prompt'])
        import shutil
        shutil.rmtree(self.task)
        plan['looks'][0]['head_view'] = 'right-three-quarter'
        with self.assertRaises(ValueError):
            self.create(plan, extra=True)
        self.assertFalse(self.task.exists())

    def test_hidden_back_view_does_not_require_an_unseen_face_direction(self):
        plan = self.plan(extra=True)
        plan['looks'][0] = self.look(selected=['front', 'back'], visible=False,
                                     body='natural back-facing garment display, no over-shoulder face')
        self.create(plan, extra=True)
        m.export(self.task)
        request = json.loads((self.task / 'handoff/look-1/request.json').read_text())
        self.assertIn('face is not visible', request['prompt'])
        self.assertIn(plan['looks'][0]['body_action'], request['prompt'])
        self.assertNotIn('Head direction: front', request['prompt'])

    def test_hidden_face_export_does_not_force_a_visible_camera_gaze(self):
        plan = self.plan()
        plan['looks'][0] = self.look(visible=False)
        plan['looks'][0]['gaze'] = 'unnecessary forced camera gaze'
        self.create(plan)
        m.export(self.task)
        prompt = (self.task / 'handoff/look-1/prompt.txt').read_text()
        self.assertNotIn('unnecessary forced camera gaze', prompt)
        self.assertIn('eye direction is not exposed', prompt)

    def test_primary_original_and_a_garment_are_mandatory_per_look(self):
        for selected in (['garment', 'left'], ['front', 'left']):
            plan = self.plan(extra=True)
            plan['looks'][0] = self.look('left-three-quarter', selected)
            with self.subTest(selected=selected), self.assertRaises(ValueError):
                self.create(plan, extra=True)
            self.assertFalse(self.task.exists())

    def test_plan_rejects_ai_new_nonportrait_and_legacy_without_changing_defaults(self):
        for source in ('ai', 'new'):
            with self.subTest(source=source), self.assertRaises(ValueError):
                self.create(model=dict(self.model, source_type=source, consent_note=''))
            self.assertFalse(self.task.exists())
        with self.assertRaises(ValueError):
            m.create(self.task, self.inventory(), ['x'], (20, 30), identity=False,
                     context=self.context, route='codex_native', real_face_plan=self.plan())
        with self.assertRaises(ValueError):
            m.create(self.task, [str(self.files['garment'])], ['x'], (20, 30), schema_version=1,
                     real_face_plan=self.plan())
        self.assertFalse(self.task.exists())
        ai = dict(self.model, source_type='ai', consent_note='')
        data = m.create(self.task, self.inventory(), ['default free head turn'], (20, 30),
                        model=ai, context=self.context, route='codex_native')
        before = (self.task / 'task.json').read_bytes()
        m.export(self.task)
        self.assertNotIn('real_face_plan', data)
        self.assertEqual((self.task / 'task.json').read_bytes(), before)
        prompt = (self.task / 'handoff/look-1/prompt.txt').read_text()
        self.assertNotIn('Real-person per-image plan', prompt)
        self.assertTrue(prompt.endswith('default free head turn'))

    def test_six_image_selection_reserves_space_for_first_image_on_later_looks(self):
        plan = self.plan(6, extra=True)
        plan['looks'][0] = self.look('front', ['garment', 'back', 'front', 'left', 'style'])
        self.create(plan, count=6, extra=True)
        self.accept_first()
        refs = m.references(self.task, m.read(self.task), 2)
        self.assertEqual([r['role'] for r in refs], ['garment-source', 'identity-reference', 'identity-only'])
        self.assertEqual(len(refs), 3)
        self.assertEqual(len(m.read(self.task)['references']), 7)

    def test_overfull_actual_selection_and_later_anchor_reservation_fail_before_freeze(self):
        for count, index, selected in (
                (1, 0, ['garment', 'back', 'front', 'left', 'right', 'style']),
                (6, 3, ['garment', 'back', 'front', 'left', 'style'])):
            plan = self.plan(count, extra=True)
            plan['looks'][index] = self.look(selected=selected)
            with self.subTest(count=count), self.assertRaises(ValueError):
                self.create(plan, count=count, extra=True)
            self.assertFalse(self.task.exists())

    def test_correction_keeps_unique_edit_target_in_every_selected_request(self):
        context = dict(self.context, purpose='correction-edit')
        plan = self.plan()
        with self.assertRaises(ValueError):
            self.create(plan, context=context, edit=True)
        self.assertFalse(self.task.exists())
        plan['looks'][0] = self.look(selected=['target', 'front', 'garment'])
        self.create(plan, context=context, edit=True)
        self.assertEqual([r['role'] for r in m.references(self.task, m.read(self.task), 1)],
                         ['edit-target', 'identity-reference', 'garment-source'])

    def test_plan_and_reference_role_tampering_block_export_reserve_and_leave_evidence(self):
        self.create()
        m.update(self.task, 'authorize', limit=1, note='Human explicitly approves one image')
        original = (self.task / 'task.json').read_bytes()
        data = json.loads(original)
        data['real_face_plan']['looks'][0]['head_view'] = 'left-profile'
        (self.task / 'task.json').write_text(json.dumps(data))
        changed = (self.task / 'task.json').read_bytes()
        with self.assertRaises(ValueError):
            m.export(self.task)
        with self.assertRaises(ValueError):
            m.update(self.task, 'reserve', look=1, ready=True,
                     refs=[self.sha('garment'), self.sha('front')])
        self.assertEqual((self.task / 'task.json').read_bytes(), changed)
        (self.task / 'task.json').write_bytes(original)
        data = json.loads(original)
        data['references'][0]['role'] = 'identity-reference'
        (self.task / 'task.json').write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            m.reference_hashes(self.task, 1)

    def test_plan_requires_inventory_metadata_hash_even_without_supplements(self):
        self.create()
        data = m.read(self.task)
        del data['references_sha256']
        (self.task / 'task.json').write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            m.reference_hashes(self.task, 1)

    def test_unselected_frozen_file_tampering_also_blocks_reference_selection(self):
        data = self.create(extra=True)
        unused = next(r for r in data['references'] if r['sha256'] == self.sha('right'))
        (self.task / unused['file']).write_bytes(b'changed unused inventory')
        with self.assertRaises(ValueError):
            m.reference_hashes(self.task, 1)
        with self.assertRaises(ValueError):
            m.export(self.task)

    def test_exported_plan_controls_body_head_and_gaze_after_the_manual_prompt(self):
        plan = self.plan()
        plan['looks'][0] = self.look(body='asymmetric supported sofa sitting')
        plan['looks'][0]['gaze'] = 'eyes softly to frame-left with head near frontal'
        self.create(plan)
        m.export(self.task)
        prompt = (self.task / 'handoff/look-1/prompt.txt').read_text()
        self.assertGreater(prompt.index('Real-person per-image plan'), prompt.index('conflicting default'))
        for value in (plan['looks'][0]['body_action'], plan['looks'][0]['gaze'], 'Head direction: front'):
            self.assertIn(value, prompt)
        self.assertIn('not garment facts', prompt)

    def test_continuation_extends_only_looks_and_preserves_original_plan_history(self):
        before = self.create(extra=True)
        self.accept_first()
        looks = [self.look('left-three-quarter', ['front', 'left', 'garment'], body='later action ' + str(i))
                 for i in range(5)]
        data = m.update(self.task, 'continue-authorize', **self.continue_args(looks))
        self.assertEqual(data['real_face_plan']['looks'], before['real_face_plan']['looks'] + looks)
        self.assertEqual(data['real_face_plan']['coverage'], before['real_face_plan']['coverage'])
        self.assertEqual(data['real_face_plan_history'][0]['plan'], before['real_face_plan'])
        self.assertEqual(data['authorization']['limit'], 1)
        self.assertEqual(data['attempts'], 1)
        self.assertEqual(data['continuation_authorization']['additional_requests'], 5)
        self.assertEqual(len(m.references(self.task, data, 2)), 4)
        m.export(self.task)
        prompt = (self.task / 'handoff/look-2/prompt.txt').read_text()
        self.assertIn('Head direction: left-three-quarter', prompt)

    def test_continuation_requires_complete_compatible_plan_and_cannot_reset_authority(self):
        self.create(extra=True)
        self.accept_first()
        before = (self.task / 'task.json').read_bytes()
        for looks in (None, [], [self.look()] * 4,
                      [self.look('left-profile')] * 5,
                      [self.look(selected=['front', 'garment', 'back', 'left', 'style'])] * 5):
            args = self.continue_args(looks)
            with self.subTest(looks=looks), self.assertRaises(ValueError):
                m.update(self.task, 'continue-authorize', **args)
            self.assertEqual((self.task / 'task.json').read_bytes(), before)
        with self.assertRaises(ValueError):
            m.update(self.task, 'authorize', limit=6, note='Cannot replace single grant')

    def test_planned_custom_diagnostic_and_correction_cannot_continue(self):
        for context, edit in (
                (dict(self.context, first_pose='custom', pose_description='barefoot folded legs'), False),
                (dict(self.context, purpose='model-check'), False),
                (dict(self.context, purpose='correction-edit'), True)):
            plan = self.plan()
            if edit:
                plan['looks'][0] = self.look(selected=['target', 'front', 'garment'])
            self.create(plan, context=context, edit=edit)
            self.accept_first()
            with self.subTest(context=context), self.assertRaises(ValueError):
                m.update(self.task, 'continue-authorize', **self.continue_args([self.look()] * 5))
            import shutil
            shutil.rmtree(self.task)

    def test_structural_errors_are_rejected_without_creating_task(self):
        changes = [lambda p: p.update(primary_identity_sha256=self.sha('garment')),
                   lambda p: p['looks'][0].update(face_visible=1),
                   lambda p: p['looks'][0].update(head_view='hidden'),
                   lambda p: p['looks'][0].update(selection_note=''),
                   lambda p: p['looks'][0].update(body_action=''),
                   lambda p: p['looks'][0].update(reference_sha256s=[self.sha('front')] * 2),
                   lambda p: p['looks'][0].update(reference_sha256s=[self.sha('garment'), 'f' * 64]),
                   lambda p: p.update(looks=[])]
        for change in changes:
            plan = self.plan()
            change(plan)
            with self.subTest(plan=plan), self.assertRaises(ValueError):
                self.create(plan)
            self.assertFalse(self.task.exists())

    def test_reference_changes_during_snapshot_do_not_leave_a_invalid_plan(self):
        from unittest.mock import patch
        import shutil
        original_copy = shutil.copyfile
        changed = False

        def mutate_then_copy(source, target):
            nonlocal changed
            if not changed and Path(source).resolve() == self.files['front'].resolve():
                changed = True
                Image.new('RGB', (20, 30), 'brown').save(source)
            return original_copy(source, target)

        with patch.object(m.shutil, 'copyfile', side_effect=mutate_then_copy):
            with self.assertRaises(ValueError):
                self.create()
        self.assertTrue(changed, 'Fixture must actually mutate the original during copy')
        self.assertFalse(self.task.exists())

    def test_continuation_history_cannot_be_deleted_or_change_original_first_look(self):
        self.create()
        self.accept_first()
        m.update(self.task, 'continue-authorize', **self.continue_args([self.look()] * 5))
        original = (self.task / 'task.json').read_bytes()
        for remove in (True, False):
            data = json.loads(original)
            if remove:
                del data['real_face_plan_history']
            else:
                data['real_face_plan_history'][0]['plan']['looks'][0]['body_action'] = 'changed old first action'
                data['real_face_plan_history'][0]['sha256'] = m.object_hash(data['real_face_plan_history'][0]['plan'])
            (self.task / 'task.json').write_text(json.dumps(data))
            with self.subTest(remove=remove), self.assertRaises(ValueError):
                m.reference_hashes(self.task, 2)
        (self.task / 'task.json').write_bytes(original)

    def test_cli_continuation_passes_five_look_records_without_changing_first_plan(self):
        first = self.create()['real_face_plan']
        self.accept_first()
        spec = dict(context=self.context, prompts=['new image'] * 5,
                    real_face_looks=[self.look(body='continuation action ' + str(i)) for i in range(5)])
        file = self.root / 'continue-spec.json'
        file.write_text(json.dumps(spec))
        result = subprocess.run([sys.executable, str(ROOT / 'skills/threadtruth-studio/scripts/web-task.py'),
                                 'continue-authorize', '--task', str(self.task), '--spec', str(file),
                                 '--approval-id', 'cli-five-images', '--note', 'Human approves five images'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = m.read(self.task)
        self.assertEqual(data['real_face_plan']['looks'][0], first['looks'][0])
        self.assertEqual(data['real_face_plan']['looks'][1:], spec['real_face_looks'])
        self.assertEqual(data['attempts'], 1)

    def test_original_plus_accepted_supplement_remains_real_on_export(self):
        self.create(extra=True)
        self.accept_first()
        package = self.root / 'package'
        m.export_model(self.task, package, 'Same real person')
        card = m.models.load_package(package)
        self.assertEqual(card['model']['source_type'], 'real')
        self.assertEqual(len(card['references']), 3)
        self.assertEqual([r['sha256'] for r in card['supplements']], [self.sha('supplement')])

    def test_new_ai_confirmation_export_and_new_product_reuse_remain_unrestricted(self):
        m.create(self.task, [dict(path=str(self.files['garment']), role='garment-source')],
                 ['new AI casting with free head direction'], (20, 30),
                 model=dict(self.model, source_type='new', consent_note=''),
                 context=self.context, route='codex_native')
        self.accept_first()
        package = self.root / 'new-ai-package'
        m.export_model(self.task, package, 'Accepted new AI model')
        self.assertEqual(m.models.load_package(package)['model']['source_type'], 'ai')
        reused = self.root / 'reuse-ai-task'
        data = m.create(reused, [dict(path=str(self.files['back']), role='garment-source')],
                        ['free AI head direction ' + str(i) for i in range(6)], (20, 30),
                        context=dict(self.context, outfit='second-knit'), route='codex_native',
                        model_package=package)
        self.assertEqual(data['model']['source_type'], 'ai')
        self.assertNotIn('real_face_plan', data)
        m.export(reused)
        prompt = (reused / 'handoff/look-1/prompt.txt').read_text()
        self.assertTrue(prompt.endswith('free AI head direction 0'))
        self.assertNotIn('Real-person per-image plan', prompt)

    def test_unplanned_real_task_cannot_be_retrofitted_via_continuation(self):
        m.create(self.task, self.inventory(), ['old real task'], (20, 30),
                 model=self.model, context=self.context, route='codex_native')
        self.accept_first()
        before = (self.task / 'task.json').read_bytes()
        with self.assertRaises(ValueError):
            m.update(self.task, 'continue-authorize', **self.continue_args([self.look()] * 5))
        self.assertEqual((self.task / 'task.json').read_bytes(), before)
        args = self.continue_args(None)
        del args['real_face_looks']
        data = m.update(self.task, 'continue-authorize', **args)
        self.assertNotIn('real_face_plan', data)
        self.assertEqual(len(data['looks']), 6)

    def test_cli_init_accepts_plan_and_does_not_create_generation_authority(self):
        spec = dict(references=self.inventory(extra=True), prompts=['garment image'], size=[20, 30],
                    model=self.model, context=self.context, route='codex_native',
                    real_face_plan=self.plan(extra=True))
        file = self.root / 'spec.json'
        file.write_text(json.dumps(spec))
        result = subprocess.run([sys.executable, str(ROOT / 'skills/threadtruth-studio/scripts/web-task.py'),
                                 'init', '--task', str(self.task), '--spec', str(file)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = m.read(self.task)
        self.assertEqual(data['real_face_plan'], spec['real_face_plan'])
        self.assertIsNone(data['authorization'])
        self.assertEqual(data['attempts'], 0)

    def test_frontal_only_coverage_rejects_new_directional_off_lens_gaze(self):
        for gaze in ('Eyes look gently just to image-right outside the lens',
                     'look away from the camera', 'off-lens eyes toward image-left', 'eyes drift off-frame',
                     'looks to the left of the camera', 'glances sideways'):
            plan = self.plan()
            plan['looks'][0]['gaze'] = gaze
            with self.subTest(gaze=gaze), self.assertRaisesRegex(ValueError, 'Frontal-only'):
                self.create(plan)
            self.assertFalse(self.task.exists())
        plan = self.plan()
        plan['looks'][0]['gaze'] = 'Eyes look slightly past the lens with the original slight smile'
        self.assertEqual(self.create(plan)['real_face_plan'], plan)

    def test_reviewed_side_coverage_still_permits_off_lens_gaze(self):
        plan = self.plan(extra=True)
        plan['looks'][0] = self.look('left-three-quarter', ['left', 'garment', 'front'])
        plan['looks'][0]['gaze'] = 'eyes toward image-left outside the lens'
        self.assertEqual(self.create(plan, extra=True)['real_face_plan'], plan)

    def test_frozen_off_lens_plan_still_reads_and_exports(self):
        self.create()
        data = json.loads((self.task / 'task.json').read_text())
        data['real_face_plan']['looks'][0]['gaze'] = 'Eyes look just to image-right outside the lens'
        data['real_face_plan_sha256'] = m.object_hash(data['real_face_plan'])
        m.save(self.task, data)
        m.export(self.task)
        prompt = (self.task / 'handoff/look-1/prompt.txt').read_text()
        self.assertIn('Eye gaze: Eyes look just to image-right outside the lens.', prompt)

    def test_continuation_judges_only_new_looks_by_the_gaze_rule(self):
        self.create()
        data = json.loads((self.task / 'task.json').read_text())
        data['real_face_plan']['looks'][0]['gaze'] = 'Eyes look just to image-right outside the lens'
        data['real_face_plan_sha256'] = m.object_hash(data['real_face_plan'])
        m.save(self.task, data)
        self.accept_first()
        bad = [self.look(body='next action ' + str(i)) for i in range(5)]
        bad[2]['gaze'] = 'eyes away from the camera'
        before = (self.task / 'task.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'Frontal-only'):
            m.update(self.task, 'continue-authorize', **self.continue_args(bad))
        self.assertEqual((self.task / 'task.json').read_bytes(), before)
        good = [self.look(body='next action ' + str(i)) for i in range(5)]
        data = m.update(self.task, 'continue-authorize', **self.continue_args(good))
        self.assertIn('outside the lens', data['real_face_plan']['looks'][0]['gaze'])


if __name__ == '__main__':
    unittest.main()
