"""New aesthetic planning behavior; frozen legacy bytes live in a separate fixture."""
import copy
import json
from pathlib import Path
import unittest

from tests.test_pose_plan_v2 import sample_plan, shot
from tests.test_style_pose_pool import module, bind_pool_actions
from tests.test_aesthetic_review_regressions import baseline_model_block

library, visual, task = module('visual_library'), module('visual_plan'), module('web-task')
ROOT = Path(__file__).resolve().parents[1]


class AestheticPlanningTests(unittest.TestCase):
    def fixture(self):
        return json.loads((ROOT / 'tests/fixtures/style-pool-legacy.json').read_text())

    def new_spec(self):
        spec = self.fixture()['spec']
        plan = sample_plan(6, back=False)
        plan.update(framing_guidance=3, coverage=copy.deepcopy(spec['shot_plan']['coverage']))
        plan['coverage'][0]['views'] = ['front', 'front-side', 'detail']
        for cell in plan['looks']:
            cell.update(reference_sha256s=spec['garment']['source_sha256s'],
                        head='Head direction sentinel.', gaze='Eye direction sentinel.')
        plan['looks'][-1]['framing'] = 'detail'
        spec.update(shot_plan=plan, count=6, first_pose=1)
        spec['model']['locked'] = ['Warm olive skin tone; naturally broad body proportions.']
        spec['model']['adjustable'] = ['A playful expression sentinel.']
        return bind_pool_actions(spec)

    def test_f2_body_diversity_applies_to_preview_and_delivery_only_for_new_plans(self):
        plan = sample_plan()
        marker = 'Each non-detail cell is a distinct body action'
        for framing in (None, 1, 2, 3):
            if framing is not None:
                plan['framing_guidance'] = framing
            for look in (None, 1):
                with self.subTest(framing=framing, look=look):
                    rendered = shot.render(plan, look)
                    self.assertEqual(rendered.count(marker), int(framing == 3))
                    self.assertIn(plan['looks'][0]['display_goal'], rendered)
                    self.assertIn(', '.join(plan['looks'][0]['must_show']), rendered)

    def test_f6_new_and_ai_drop_real_identity_tail_real_and_frozen_keep_it(self):
        fixture = self.fixture()
        legacy = fixture['visual_plan']
        phrase = 'original identity, real-person view coverage'
        self.assertIn(phrase, visual.render(legacy))
        for source in ('new', 'ai', 'real'):
            spec = copy.deepcopy(fixture['spec'])
            spec['model'].update(source_type=source, consent_note='Synthetic consent fixture.')
            if source == 'real':
                for cell in spec['shot_plan']['looks']:
                    cell.pop('head', None)
                    cell.pop('gaze', None)
            prepared = library.prepare(spec)
            self.assertEqual(prepared['model_source_type'], source)
            self.assertEqual(phrase in visual.render(prepared), source == 'real')
            self.assertIn('Garment facts', visual.render(prepared))
            # The frozen source cannot be rebound to another model at export.
            wrong = copy.deepcopy(spec['model'])
            wrong['source_type'] = 'real' if source != 'real' else 'new'
            with self.assertRaisesRegex(ValueError, 'model source differs'):
                task.prompt_check(visual.compile_prompt(prepared), fixture['context'], wrong,
                                  spec['shot_plan'], 1, visual_plan=prepared)

    def test_f8_shared_photography_once_overrides_retained_and_directive_once(self):
        spec = self.new_spec()
        spec['overrides'] = dict(photography=dict(lighting='Warm shared light.',
            composition='Clear shared layers; 各格严格沿用冻结动作和景别。'))
        spec['shot_plan']['looks'][1].update(lighting='Cool reflected light.',
            camera='Distinct diagonal layers. 各格严格沿用冻结动作和景别。')
        prepared = library.prepare(spec)
        rendered = visual.render(prepared)
        self.assertEqual(rendered.count('Warm shared light.'), 1)
        self.assertEqual(rendered.count('Clear shared layers;'), 1)
        self.assertEqual(rendered.count('Cool reflected light.'), 1)
        self.assertIn('Composition: Distinct diagonal layers.', rendered)
        self.assertEqual(rendered.count(visual.FROZEN_SHOT_LINE), 1)
        self.assertNotIn('严格沿用', rendered)
        single = visual.render(prepared, 2)
        self.assertIn('Lighting: Cool reflected light.', single)
        self.assertEqual(single.count(visual.FROZEN_SHOT_LINE), 1)

    def test_f8_detail_retains_baseline_portrait_directions_in_both_request_shapes(self):
        spec = self.new_spec()
        prepared = library.prepare(spec)
        detail = visual.render(prepared, 6)
        self.assertIn('Style persona', detail)
        for commitment in prepared.get('commitments', []):
            if set(commitment['needs']) & {'expression', 'body'}:
                self.assertIn(commitment['show'], detail)
        self.assertIn('Head direction sentinel.', shot.render(spec['shot_plan'], 6))
        self.assertIn('Eye direction sentinel.', shot.render(spec['shot_plan'], 6))
        data = dict(schema_version=2, model=spec['model'], identity=True,
                    context=dict(self.fixture()['context'], purpose='delivery'), size=[20, 30], route='codex_native',
                    shot_plan=spec['shot_plan'], visual_plan=prepared, prompt_contract_version=2,
                    identity_instruction_version=1, references=spec['inventory'])
        prompt = task.handoff_prompt(data, dict(number=6, prompt=visual.compile_prompt(prepared, 6)), data['references'])
        self.assertIn('expression sentinel', prompt)
        self.assertIn('Head direction sentinel.', prompt)
        self.assertIn('Eye direction sentinel.', prompt)
        self.assertIn(baseline_model_block('portrait_directions'), prompt)
        self.assertIn('Warm olive skin tone', prompt)
        self.assertIn('naturally broad body proportions', prompt)
        data['context']['purpose'] = 'preview-grid'
        preview = task.handoff_prompt(data, dict(number=1, prompt=visual.compile_prompt(prepared)), data['references'])
        self.assertEqual(preview.count('Head direction sentinel.'), 6)
        self.assertEqual(preview.count('Eye direction sentinel.'), 6)
        self.assertIn('Style persona', preview)
        self.assertNotIn('non-detail cells only', preview.lower())


if __name__ == '__main__':
    unittest.main()
