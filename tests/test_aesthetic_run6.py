"""Q3 follow-up: preparation gates and frozen prompt compatibility, without generation."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
from tests.test_pose_plan_v2 import sample_plan
from tests.test_style_pose_pool import module

library, task, poses = module('visual_library'), module('web-task'), module('pose_library')
ROOT = Path(__file__).resolve().parents[1]
STYLING_LINE = '不沿用商品原图模特的发型、头饰、妆容和配饰组合（手套、首饰等），除非它们是本次商品的一部分或用户明确要求。'
CUSTOM_REASON = '池内扶窗和交叉手臂会遮挡本格必须展示的袖口开合，改为双臂自然外展。'


def spec_for(sha, entry='french-effortless', library_count=4):
    plan = sample_plan(back=False)
    plan.update(variety_checks=2, framing_guidance=3)
    plan['coverage'][0]['sha256'] = sha
    for i, cell in enumerate(plan['looks']):
        cell.update(reference_sha256s=[sha], scene='Studio area ' + str(i % 3),
                    pose_decision=dict(kind='custom', reason=CUSTOM_REASON))
        if i >= 7:
            cell.update(framing='detail', pose_decision=dict(kind='not-applicable', reason='Only the source-backed cuff.'))
    safe = [row for row in library.card(entry).get('pose_vocabulary', [])
            if row['family'] != 'close' and 'back' not in row['views'] and row['id'] != 'fr-laugh-turn']
    for cell, row in zip(plan['looks'][:library_count], safe):
        cell.pop('pose_decision')
        cell.update(pose_id=row['id'], body_action=row['body'], hands=row['hands'], support=row['support'],
                    garment_views=row['views'])
    spec = dict(entry_id=entry, count=9, first_pose=1, output_form='human', shot_plan=plan,
                inventory=[dict(role='garment-source', sha256=sha)],
                model=dict(source_type='new', scope='full', subject='adult female model',
                           locked=[], adjustable=[], consent_note='', styling_lock='identity'),
                garment=dict(description='Synthetic blue garment.', keep=['Original blue colour and cuff.'],
                             source_sha256s=[sha]))
    if entry == 'qipao-urban':
        spec.update(culture_profile=dict(id='qipao-contemporary-daily', version=1, form='contemporary daily qipao'),
                    asset_trace=[dict(asset='C10', decision='translated', affects='Use the source-backed modern cut.',
                                      check='No invented historical costume details.')])
    return spec


def prompt_for(spec, visual, purpose='preview-grid'):
    data = dict(schema_version=2, model=spec['model'], identity=True,
                context=dict(outfit='synthetic-run6', style=spec['entry_id'], mode='C', output_form='human',
                             size=[20, 30], first_pose=1, purpose=purpose), size=[20, 30], route='codex_native',
                shot_plan=spec['shot_plan'], visual_plan=visual, prompt_contract_version=2,
                identity_instruction_version=1, references=spec['inventory'])
    look = None if purpose == 'preview-grid' else 1
    return task.handoff_prompt(data, dict(number=1, prompt=library._visual().compile_prompt(visual, look)), data['references'])


class AestheticRun6Tests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / 'source.png'
        Image.new('RGB', (20, 30), 'blue').save(self.source)
        self.sha = task.digest(self.source)

    def create(self, spec, visual, name='job', route='codex_native', workflow_version=1):
        refs = [dict(path=self.source, role='garment-source')]
        if spec['model']['source_type'] == 'ai':
            identity = self.root / 'identity.png'
            Image.new('RGB', (20, 30), 'purple').save(identity)
            refs.append(dict(path=identity, role='identity-reference'))
        job = self.root / name
        task.create(job, refs, None, [20, 30], model=spec['model'],
                    context=dict(outfit='synthetic-run6', style=spec['entry_id'], mode='C', output_form='human',
                                 size=[20, 30], first_pose=1, purpose='preview-grid'),
                    route=route, shot_plan=spec['shot_plan'], visual_plan=visual, workflow_version=workflow_version)
        return job

    def test_i21_e2_five_custom_of_seven_rejected_at_prepare_and_init(self):
        spec = spec_for(self.sha, library_count=2)
        visual = library.prepare(spec_for(self.sha))
        for entrypoint in ('prepare', 'init'):
            with self.subTest(entrypoint=entrypoint), self.assertRaisesRegex(ValueError, 'pose_library.py recommend'):
                if entrypoint == 'prepare':
                    library.prepare(spec)
                else:
                    self.create(spec, visual)
        self.assertFalse((self.root / 'job').exists())

    def test_i21_rounds_up_and_detail_library_ids_do_not_count(self):
        spec = spec_for(self.sha, library_count=3)
        # A library binding on a detail cell must not satisfy the body quota.
        detail = spec['shot_plan']['looks'][-1]
        detail.pop('pose_decision')
        detail['pose_id'] = 'fr-hair-tuck'
        with self.assertRaisesRegex(ValueError, 'at least 4 of 7 non-detail'):
            library.prepare(spec)

    def test_i21_e3_e4_pool_plans_and_half_rounded_up_pass(self):
        for entry, count in (('french-effortless', 4), ('resort-vacation', 7), ('qipao-urban', 7)):
            with self.subTest(entry=entry):
                spec = spec_for(self.sha, entry, count)
                frozen = library.prepare(spec)
                job = self.create(spec, frozen, entry)
                self.assertEqual(task.read(job)['attempts'], 0)

    def test_i21_custom_needs_specific_pool_mismatch(self):
        for reason in ('', '不适合', '池内动作不适合本格', 'Custom pose for variety.'):
            spec = spec_for(self.sha)
            spec['shot_plan']['looks'][4]['pose_decision']['reason'] = reason
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, 'pose_library.py recommend'):
                library.prepare(spec)
        spec = spec_for(self.sha)
        del spec['shot_plan']['looks'][4]['pose_decision']
        with self.assertRaisesRegex(ValueError, 'pose_library.py recommend'):
            library.prepare(spec)
        spec['shot_plan']['looks'][4]['pose_decision'] = dict(kind='custom', reason='池内手位遮领，改双手垂放。')
        library.prepare(spec)  # Concise concrete reasons do not need arbitrary minimum length.

    def test_i21_owned_selection_counts_toward_half(self):
        spec = spec_for(self.sha, library_count=3)
        spec['shot_plan'], _ = poses.apply(spec['shot_plan'], spec['shot_plan']['looks'][3]['shot_id'],
                                          'tt-stand-neutral', 'front')
        frozen = library.prepare(spec)
        self.create(spec, frozen)

    def test_i21_both_new_plan_gates_and_no_pool_exemption(self):
        for flags in (dict(variety_checks=2, framing_guidance=2), dict(framing_guidance=3)):
            spec = spec_for(self.sha, library_count=2)
            spec['shot_plan'].pop('variety_checks')
            spec['shot_plan'].update(flags)
            with self.subTest(flags=flags), self.assertRaisesRegex(ValueError, 'pose_library.py recommend'):
                library.prepare(spec)
        spec = spec_for(self.sha, 'ecommerce-studio', 0)
        self.create(spec, library.prepare(spec))

    def test_i21_old_plan_markers_keep_preparation_behavior(self):
        spec = spec_for(self.sha, library_count=0)
        spec['shot_plan'].pop('variety_checks')
        spec['shot_plan']['framing_guidance'] = 2
        self.create(spec, library.prepare(spec))

    def test_i21_even_half_and_selected_standalone_scope(self):
        spec = spec_for(self.sha, library_count=3)
        plan = spec['shot_plan']
        plan['looks'][6].update(framing='detail', pose_decision=dict(kind='not-applicable', reason='Only the source cuff.'))
        library.prepare(spec)  # Exactly three of six body cells.
        spec['shot_plan'] = task.shot_helper().subset(plan, 5)
        spec.update(count=1, first_pose=5)
        with self.assertRaisesRegex(ValueError, 'at least 1 of 1 non-detail'):
            library.prepare(spec)  # Unselected library cells cannot pad a standalone custom shot.

    def test_i21_init_rejects_generic_reason_even_with_enough_pool_poses(self):
        spec = spec_for(self.sha)
        visual = library.prepare(spec)
        spec['shot_plan']['looks'][4]['pose_decision']['reason'] = '池内动作不适合本格'
        with self.assertRaisesRegex(ValueError, 'pose_library.py recommend'):
            self.create(spec, visual)
        self.assertFalse((self.root / 'job').exists())

    def test_old_v3_under_quota_task_still_exports_and_continues_from_preview(self):
        spec = spec_for(self.sha, library_count=2)
        visual = library.prepare(spec_for(self.sha))
        visual['styling'] = [line for line in visual['styling'] if line != STYLING_LINE]
        # Seed the pre-run6 contract once; actual restore/export/continuation below is unmocked.
        with patch.object(task.shot_helper(), 'check_new_pose_pool', create=True):
            job = self.create(spec, visual, workflow_version=0)
        data = task.read(job)
        before = (job / 'task.json').read_bytes()
        task.check_evidence(job, data)
        task.export(job)
        self.assertEqual((job / 'task.json').read_bytes(), before)
        folder = task.handoff_directory(job, data, data['looks'][0])
        self.assertNotIn(STYLING_LINE, (folder / 'prompt.txt').read_text())
        task.update(job, 'authorize', limit=1, note='Synthetic ledger fixture only.')
        task.update(job, 'reserve', look=1, ready=True, refs=task.reference_hashes(job, 1),
                    expected_plan_sha256=task.plan_fingerprint(task.read(job)))
        output = self.root / 'output.png'
        Image.new('RGB', (20, 30), 'green').save(output)
        task.update(job, 'returned', look=1, file=output)
        task.update(job, 'accept', look=1, qa='qa-pass', note='Synthetic ledger fixture only.')
        task.update(job, 'finish-preview', decision='direction-confirmed', note='Synthetic direction confirmation.')
        child_root = self.root / 'delivery'
        child = task.create_from_preview(child_root, job,
            dict(context=dict(data['context'], purpose='delivery', first_pose=5), size=[20, 30], count=1),
            note='Continue the frozen custom shot.')
        task.export(child_root)
        self.assertEqual(child['attempts'], 0)
        self.assertIsNone(child['authorization'])
        self.assertEqual(child['visual_plan']['styling'], visual['styling'])
        # A freshly prepared revision must not inject new styling into the old contract.
        fresh = library.prepare(spec_for(self.sha))
        inherited = task.inherit_visual_rendering(fresh, visual)
        self.assertEqual(inherited['styling'], visual['styling'])

    def test_i19_new_ai_and_new_person_export_constraint_on_both_routes(self):
        for source in ('new', 'ai'):
            for route in ('codex_native', 'chatgpt_web'):
                with self.subTest(source=source, route=route):
                    spec = spec_for(self.sha)
                    spec['model']['source_type'] = source
                    frozen = library.prepare(spec)
                    job = self.create(spec, frozen, source + route, route)
                    task.export(job)
                    data = task.read(job)
                    folder = task.handoff_directory(job, data, data['looks'][0])
                    prompt = (folder / 'prompt.txt').read_text()
                    self.assertEqual(prompt.count(STYLING_LINE), 1)
                    if route == 'chatgpt_web':
                        packet = task.export_web_execution(job, 1)
                        self.assertIn(STYLING_LINE, Path(packet['submission_file']).read_text())
                    self.assertEqual(data['attempts'], 0)
                    self.assertIsNone(data['authorization'])

    def test_i19_real_and_frozen_prompts_match_pre_change_bytes(self):
        baseline = json.loads((ROOT / 'tests/fixtures/aesthetic-run6-prompts.json').read_text())
        for row in baseline['cases']:
            with self.subTest(name=row['name']):
                spec = copy.deepcopy(baseline['spec'])
                spec['model'].update(source_type=row['source'],
                                     consent_note='Synthetic consent fixture.' if row['source'] == 'real' else '')
                visual = copy.deepcopy(baseline['visual_plan'])
                visual['model_source_type'] = row['source']
                if 'persona_model_sha256' in visual:
                    visual['persona_model_sha256'] = task.object_hash(spec['model'])
                if row['source'] == 'real':
                    visual = library.prepare(spec)
                actual = prompt_for(spec, visual, row['purpose'])
                self.assertEqual(hashlib.sha256(actual.encode()).hexdigest(), row['prompt_sha256'])
                self.assertNotIn(STYLING_LINE, actual)


if __name__ == '__main__':
    unittest.main()
