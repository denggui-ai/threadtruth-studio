"""Offline photography decisions compile consistently before prompt freeze."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('photography_spec_preview', ROOT / 'tools/style_preview.py')
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)
spec = importlib.util.spec_from_file_location('photography_spec_task', ROOT / 'skills/threadtruth-studio/scripts/web-task.py')
task = importlib.util.module_from_spec(spec)
spec.loader.exec_module(task)


class PhotographySpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        for path in ('docs/demo', 'skills/threadtruth-studio/references'):
            shutil.copytree(ROOT / path, cls.root / path)
        cls.plan = preview._plan_v5(cls.root, 'spec', 'beige-blazer-denim-outfit')
        cls.model = dict(source_type='new', scope='full', subject='adult female model',
                         locked=[], adjustable=[], consent_note='')
        cls.face = cls.root / 'original.png'
        Image.new('RGB', (20, 30), 'blue').save(cls.face)
        cls.face_hash = preview.digest(cls.face.read_bytes())

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def helper(self, photography_spec=None, *, style='neo-chinese', pose=3, action=2,
               model=None, refs=None, real_face_plan=None, run_id='spec'):
        try:
            result = preview.single_prompt(self.root, run_id, style, pose,
                'beige-blazer-denim-outfit', '2:3', model=model or self.model,
                model_references=refs, action=action, photography_spec=photography_spec,
                real_face_plan=real_face_plan)
        except TypeError as error:
            self.fail('Photography compilation interface is missing: ' + str(error))
        return result, (self.root / result['path']).read_text()

    def test_seated_pose_can_choose_scene_one_and_full_body_before_compile(self):
        result, raw = self.helper(dict(mode='C', shots=[dict(pose=3, scene_index=1,
            framing='full-body', support='One hand supports the bench and one rests on the leg',
            gaze='Eyes look slightly away from the lens')]))
        shot = result['resolved_shots'][2]
        self.assertEqual(shot['pose'], 3)
        self.assertEqual(shot['master'], 'UPRIGHT_SEATED')
        self.assertEqual(shot['scene_index'], 1)
        self.assertEqual(shot['framing'], 'full-body')
        self.assertIn('Mode/scene: 现代茶室木墙', raw)
        self.assertIn('One hand supports the bench and one rests on the leg', raw)
        self.assertIn('Eye gaze: Eyes look slightly away from the lens', raw)
        self.assertIn('cropped shoes', raw)
        self.assertNotIn('端正半身坐姿', raw)

    def test_half_body_does_not_force_shoes_hem_or_full_body_crop_negative(self):
        _, raw = self.helper(dict(mode='C', shots=[dict(pose=3, framing='half-body')]))
        self.assertIn('Framing: half-body', raw)
        self.assertNotIn('shoes, bag and hem inside safe margins', raw)
        self.assertNotIn('Keep the complete coordinated outfit visible.', raw)
        self.assertNotIn('cropped shoes', raw)

    def test_preview_and_single_share_resolved_photography_and_cell_framing(self):
        value = dict(mode='C', shots=[dict(pose=3, scene_index=1, framing='full-body',
            support='Hands rest separately on the bench and leg', gaze='Eyes look gently past the camera')])
        single, single_text = self.helper(value)
        board, board_text = self.helper(value, action=0)
        self.assertEqual(single['resolved_shots'], board['resolved_shots'])
        for text in (single_text, board_text):
            self.assertIn('Mode/scene: 现代茶室木墙', text)
            self.assertIn(value['shots'][0]['support'], text)
            self.assertIn(value['shots'][0]['gaze'], text)
        self.assertNotIn('Keep the complete coordinated outfit visible in all six cells.', board_text)

    def test_b_is_studio_and_d_prefix_controls_studio_positions(self):
        b, _ = self.helper(dict(mode='B', shots=[]))
        self.assertTrue(all(s['scene_index'] is None and 'studio' in s['scene']
                            for s in b['resolved_shots']))
        for prefix in (2, 3):
            d, _ = self.helper(dict(mode='D', studio_prefix=prefix, shots=[]))
            self.assertEqual([s['scene_index'] is None for s in d['resolved_shots']],
                             [i <= prefix for i in range(1, 7)])
        d, _ = self.helper(dict(mode='D', shots=[]))
        self.assertEqual(d['studio_prefix'], 2)

    def test_location_selection_is_rejected_on_studio_positions(self):
        values = [dict(mode='B', shots=[dict(pose=6, scene_index=1)]),
                  dict(mode='D', shots=[dict(pose=2, scene_index=1)]),
                  dict(mode='D', studio_prefix=3, shots=[dict(pose=3, scene_index=1)])]
        for value in values:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'studio'):
                self.helper(value)

    def test_invalid_specs_cannot_reorder_add_mothers_or_hide_unknown_fields(self):
        values = [dict(mode='A'), dict(mode=[]), dict(mode={}), dict(mode='C', studio_prefix=2), dict(mode='D', studio_prefix=1),
                  dict(mode='D', studio_prefix=True), dict(shots={}), dict(shots=[dict(pose=0)]),
                  dict(shots=[dict(pose=7)]), dict(shots=[dict(pose=True)]),
                  dict(shots=[dict(pose=2), dict(pose=2)]), dict(shots=[dict(pose=1, scene_index=7)]),
                  dict(shots=[dict(pose=1, framing='tight-face')]), dict(shots=[dict(pose=1, framing=[])]),
                  dict(shots=[dict(pose=1, support='a\nb')]),
                  dict(shots=[dict(pose=1, gaze=' ')]), dict(shots=[dict(pose=1, support='a'*241)]),
                  dict(shots=[dict(pose=1, head_view='left-profile')]), dict(unknown=1)]
        for value in values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.helper(value)

    def real_fixture(self, count=1):
        source_hash = self.plan['source']['assets'][0]['sha256']
        model = dict(source_type='real', scope='face', subject='adult female model',
                     locked=['original expression and hairstyle'], adjustable=[],
                     consent_note='User authorized identity reuse')
        refs = [dict(path=str(self.face), role='identity-reference', sha256=self.face_hash)]
        look = dict(body_action='Upright seated with one hand on the bench and one on the leg',
                    head_view='near-front', gaze='Eyes look slightly past the lens', face_visible=True,
                    reference_sha256s=[source_hash, self.face_hash], selection_note='Original front reference retained')
        plan = dict(primary_identity_sha256=self.face_hash,
                    coverage=[dict(sha256=self.face_hash, views=['front'], note='Reviewed original front view')],
                    looks=[copy.deepcopy(look) for _ in range(count)])
        return model, refs, plan

    def test_real_plan_is_sole_body_head_gaze_authority_and_preserves_expression(self):
        model, refs, plan = self.real_fixture()
        value = dict(mode='C', shots=[dict(pose=3, scene_index=1, framing='full-body',
            support=plan['looks'][0]['body_action'], gaze=plan['looks'][0]['gaze'])])
        result, raw = self.helper(value, model=model, refs=refs, real_face_plan=plan)
        self.assertIn('Head direction: near-front', raw)
        self.assertIn(plan['looks'][0]['body_action'], raw)
        self.assertIn(plan['looks'][0]['gaze'], raw)
        self.assertIn('original expression and hairstyle', raw)
        self.assertNotIn('no fixed left/right direction', raw)
        self.assertEqual(result['resolved_shots'][2]['body_action'], plan['looks'][0]['body_action'])

    def test_real_support_or_gaze_disagreement_rejects_before_prompt_write(self):
        model, refs, plan = self.real_fixture()
        for field, text in [('support', 'Stand with hands clasped'), ('gaze', 'Look directly at lens')]:
            value = dict(mode='C', shots=[dict(pose=3, **{field: text})])
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'real_face_plan'):
                self.helper(value, model=model, refs=refs, real_face_plan=plan, run_id='real-conflict-'+field)
            self.assertFalse((preview.run_dir(self.root, 'real-conflict-'+field) / 'prompts').exists())

    def test_real_plan_cannot_supply_unknown_face_angle_or_change_ai_routing(self):
        model, refs, plan = self.real_fixture()
        plan['looks'][0]['head_view'] = 'left-profile'
        with self.assertRaisesRegex(ValueError, 'direction'):
            self.helper(model=model, refs=refs, real_face_plan=plan)
        plan['looks'][0]['head_view'] = 'near-front'
        with self.assertRaisesRegex(ValueError, 'real'):
            self.helper(model=dict(model, source_type='ai', consent_note=''), refs=refs, real_face_plan=plan)

    def test_new_real_photography_choices_require_reviewed_original_plan(self):
        model, refs, _ = self.real_fixture()
        for value in (dict(mode='C'), dict(shots=[dict(pose=3, gaze='Look outside')]),
                      dict(shots=[dict(pose=3, support='Seated on the bench')])):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'real_face_plan'):
                self.helper(value, model=model, refs=refs)
        result, raw = self.helper(model=model, refs=refs)
        self.assertIn('original expression and hairstyle', raw)
        self.assertEqual(result['resolved_shots'][2]['head_view'], None)

    def test_ai_and_new_defaults_keep_natural_head_variation_without_real_plan(self):
        new, raw = self.helper(dict(mode='C'))
        self.assertIn('no fixed left/right direction', raw)
        self.assertIsNone(new['resolved_shots'][2]['gaze'])
        model, refs, _ = self.real_fixture()
        ai, raw = self.helper(dict(mode='C'), model=dict(model, source_type='ai', consent_note=''), refs=refs)
        self.assertIn('no fixed left/right direction', raw)
        self.assertIsNone(ai['resolved_shots'][2]['gaze'])

    def test_cli_accepts_json_spec_for_preview_and_single(self):
        value = dict(mode='C', shots=[dict(pose=3, framing='full-body', scene_index=1)])
        photo = self.root / 'photography.json'
        photo.write_text(json.dumps(value))
        model = self.root / 'model.json'
        model.write_text(json.dumps(dict(model=self.model, references=[])))
        for action in (0, 2):
            run = subprocess.run([sys.executable, str(ROOT / 'tools/style_preview.py'), '--root', str(self.root),
                'single-prompt', '--run-id', 'spec-cli', '--source-case', 'beige-blazer-denim-outfit',
                '--style', 'neo-chinese', '--pose', '3', '--ratio', '2:3', '--action', str(action),
                '--model-spec', str(model), '--photography-spec', str(photo)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            result = json.loads(run.stdout)
            self.assertEqual(result['resolved_shots'][2]['scene_index'], 1)

    def test_override_mode_changes_preview_subtitle_and_not_only_pose_text(self):
        _, raw = self.helper(dict(mode='C'), style='ecommerce-studio', action=0)
        self.assertIn('C 场景版 · 六姿势预览', raw)
        self.assertNotIn('B 棚拍版 · 六姿势预览', raw)

    def test_real_preview_requires_all_six_reviewed_looks(self):
        model, refs, plan = self.real_fixture()
        with self.assertRaisesRegex(ValueError, 'six'):
            self.helper(dict(mode='C'), model=model, refs=refs, real_face_plan=plan, action=0)
        model, refs, plan = self.real_fixture(6)
        result, raw = self.helper(dict(mode='C'), model=model, refs=refs, real_face_plan=plan, action=0)
        self.assertEqual(len(result['resolved_shots']), 6)
        self.assertTrue(all('real_face_look' in row for row in result['resolved_shots']))
        self.assertNotIn('no fixed left/right direction', raw)

    def test_all_24_styles_compiled_photography_reaches_frozen_native_export(self):
        for item in self.plan['previews']:
            style = item['style']
            with self.subTest(style=style):
                result, raw = self.helper(dict(mode='C', shots=[dict(pose=3, scene_index=1, framing='full-body')]),
                                          style=style, run_id='spec-'+style)
                self.assertIn(item['visual']['lighting'], raw)
                self.assertIn(item['visual']['mood'], raw)
                self.assertIn(item['visual']['persona'], raw)
                job = self.root / ('export-'+style)
                refs = [{k: r[k] for k in ('path', 'role')} for r in result['references']]
                task.create(job, refs, [raw], (20, 30), model=self.model, route='codex_native',
                    context=dict(outfit='same-outfit', style=style, mode='C', output_form='real', size=[20, 30], first_pose=3))
                task.export(job)
                request = json.loads((job / 'handoff/look-1/request.json').read_text())
                self.assertIn(raw, request['prompt'])
                self.assertIn(result['resolved_shots'][2]['scene'], request['prompt'])
                self.assertEqual([r['sha256'] for r in task.read(job)['references']],
                                 [r['sha256'] for r in result['references']])


if __name__ == '__main__':
    unittest.main()
