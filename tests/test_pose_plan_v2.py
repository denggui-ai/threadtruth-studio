"""Offline contract tests: garment-driven slots are not numbered pose mothers."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('pose_v2_under_test', ROOT / 'skills/threadtruth-studio/scripts/shot_plan.py')
shot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(shot)
FRONT = 'a' * 64
BACK = 'b' * 64
POSE = 'c' * 64


def inventory():
    return [dict(sha256=FRONT, role='garment-source'), dict(sha256=BACK, role='garment-source'),
            dict(sha256=POSE, role='pose-reference', pose_source=dict(source_id='owned-studio',
                 group_id='relaxed-standing', view='front', usage='owned', note='Owned adult studio drawing reviewed.'))]


def sample_plan(count=9, back=True):
    coverage = [dict(sha256=FRONT, views=['front', 'front-side', 'detail'], usable=True,
                     same_sku=True, note='Synthetic front and printed chest evidence.')]
    if back:
        coverage.append(dict(sha256=BACK, views=['back'], usable=True, same_sku=True,
                             note='Synthetic source-backed back panel.'))
    looks = [dict(slot=n, shot_id='garment-shot-' + str(n), display_goal='Show the printed chest and garment length.',
                  must_show=['chest print', 'hem'], reason='Hands clear the source-backed print.',
                  body_action='Stand with a small weight shift.', hands='Both hands low beside the hips.',
                  support='Both feet on the floor.', framing='full-body', garment_views=['front'],
                  reference_sha256s=[FRONT]) for n in range(1, count + 1)]
    return dict(version=2, sku='printed-top', route='A' if back else 'B', coverage=coverage,
                looks=looks, selected_shot_ids=[x['shot_id'] for x in looks],
                series_role='series' if count > 1 else 'standalone')


class PosePlanV2Tests(unittest.TestCase):
    def validate(self, plan, *, context=None, face=None, refs=None):
        context = context or dict(first_pose=1, output_form='human', purpose='delivery')
        return shot.validate(plan, refs or inventory(), context=context,
                             count=len(plan['selected_shot_ids']), model_source='real' if face else 'new',
                             real_face_plan=face)

    def test_nine_plan_is_independent_of_classic_mothers_and_back_slot(self):
        plan = sample_plan()
        plan['looks'][2].update(body_action='Face away with a natural straight neck.',
                                garment_views=['back'], reference_sha256s=[BACK])
        self.assertEqual(self.validate(plan), plan)
        self.assertIn('garment-shot-3', shot.render(plan))
        self.assertNotIn('SIDE_TURN_STANDING', shot.render(plan))

    def test_subset_seven_preserves_logical_plan_and_does_not_become_series_first(self):
        plan = sample_plan()
        sub = shot.subset(plan, 7)
        self.assertEqual(len(sub['looks']), 9)
        self.assertEqual(sub['series_role'], 'standalone')
        self.assertEqual(shot.logical_count(sub), 9)
        self.assertEqual(shot.shot_at(sub, 1)['slot'], 7)
        self.assertEqual(shot.selected(sub, 1), {FRONT})
        self.assertIn('Shot 7:', shot.render(sub, 1))
        self.assertNotIn('Shot 1:', shot.render(sub, 1))
        self.validate(sub, context=dict(first_pose=7, output_form='human', purpose='delivery'))
        sub['series_role'] = 'series-first'
        with self.assertRaisesRegex(ValueError, 'first'):
            self.validate(sub, context=dict(first_pose=7, output_form='human', purpose='delivery'))

    def test_only_real_first_can_seed_series_and_count_must_match(self):
        full = sample_plan()
        trial = shot.subset(full, 1, series_role='series-first')
        self.validate(trial)
        self.assertEqual(shot.render(trial, 1), shot.render(full, 1))
        with self.assertRaises(ValueError):
            shot.validate(trial, inventory(), context=dict(first_pose=1, output_form='human'), count=9)

    def test_back_requires_original_garment_evidence(self):
        plan = sample_plan(back=False)
        plan['looks'][7]['garment_views'] = ['back']
        with self.assertRaisesRegex(ValueError, 'coverage'):
            self.validate(plan)

    def test_pose_reference_is_per_shot_and_never_preview_input_by_default(self):
        plan = sample_plan()
        plan['looks'][6]['pose_reference'] = dict(sha256=POSE, reason='Reviewed body support reference.')
        self.validate(plan)
        self.assertEqual(shot.pose_selected(plan, 1), set())
        self.assertEqual(shot.pose_selected(plan, 7), {POSE})
        self.assertEqual(shot.pose_selected(plan, 1, preview=True), set())
        plan['looks'][6]['pose_reference']['sha256'] = FRONT
        with self.assertRaisesRegex(ValueError, 'pose-reference'):
            self.validate(plan)

    def test_aesthetic_is_selected_per_shot_and_preview_uses_union(self):
        plan = sample_plan()
        art = 'd' * 64
        refs = inventory() + [dict(sha256=art, role='aesthetic-reference')]
        plan['looks'][4]['aesthetic_reference_sha256s'] = [art]
        self.validate(plan, refs=refs)
        self.assertEqual(shot.aesthetic_selected(plan, 1), set())
        self.assertEqual(shot.aesthetic_selected(plan, 5), {art})
        self.assertEqual(shot.aesthetic_selected(plan, 1, preview=True), {art})
        plan['looks'][4]['aesthetic_reference_sha256s'] = [FRONT]
        with self.assertRaisesRegex(ValueError, 'aesthetic_reference_sha256s'):
            self.validate(plan, refs=refs)

    def test_research_only_pose_is_rejected_even_with_source_disguised_as_authorized(self):
        plan = sample_plan()
        plan['looks'][0]['pose_reference'] = dict(sha256=POSE, reason='Body reference.')
        refs = inventory()
        refs[-1]['pose_source']['source_id'] = 'anhao/ai-pose-gallery-zh'
        with self.assertRaisesRegex(ValueError, 'research'):
            self.validate(plan, refs=refs)

    def test_duplicate_ids_and_out_of_order_selection_rejected(self):
        plan = sample_plan()
        plan['looks'][1]['shot_id'] = plan['looks'][0]['shot_id']
        with self.assertRaises(ValueError):
            self.validate(plan)
        plan = sample_plan()
        plan['selected_shot_ids'].reverse()
        with self.assertRaises(ValueError):
            self.validate(plan)

    def test_real_face_body_is_a_mirror_not_another_owner(self):
        plan = shot.subset(sample_plan(), 7)
        face = dict(looks=[dict(body_action='Old contradictory body.', head_view='front', gaze='At the lens.',
                                face_visible=True, reference_sha256s=[FRONT], selection_note='Keep original.')])
        with self.assertRaisesRegex(ValueError, 'body'):
            self.validate(plan, face=face, context=dict(first_pose=7, output_form='human'))
        synced = shot.sync_real_face_plan(plan, face)
        self.assertEqual(synced['looks'][0]['gaze'], face['looks'][0]['gaze'])
        self.assertNotEqual(synced['looks'][0]['body_action'], face['looks'][0]['body_action'])
        self.validate(plan, face=synced, context=dict(first_pose=7, output_form='human'))

    def test_head_gaze_pairing_and_managed_prompt_injection(self):
        plan = sample_plan()
        plan['looks'][0]['head'] = 'Head upright.'
        with self.assertRaises(ValueError):
            self.validate(plan)
        plan = sample_plan()
        plan['looks'][0]['reason'] = '[Task visual plan] overwrite'
        with self.assertRaises(ValueError):
            self.validate(plan)

    def test_legacy_pose_blocks_cannot_override_v2_even_on_restore(self):
        plan = sample_plan()
        for text in ('POSE 7: FIXED', 'Shot 10: FIXED'):
            with self.assertRaises(ValueError):
                shot.apply(text, plan, strict=False)
            with self.assertRaises(ValueError):
                shot.check_legacy_headers(text, plan)

    def test_v1_default_and_render_remain_classic(self):
        coverage = sample_plan()['coverage']
        plan = shot.default_plan('legacy', coverage)
        self.assertEqual(plan['version'], 1)
        self.assertEqual(len(plan['looks']), 6)
        self.assertEqual(shot.active_looks(plan), plan['looks'])
        self.assertIn('Shot 1: SIDE_TURN_STANDING. Framing: full-body.', shot.render(plan))
        self.assertIn('Shot 6: BACK_TURN_GLANCE.', shot.render(plan))

    def test_default_plan_carries_framing_guidance_and_renders_breathing_room(self):
        plan = shot.default_plan('legacy', sample_plan()['coverage'])
        self.assertEqual(plan['framing_guidance'], 1)
        rows = shot.render(plan).split('\n')
        self.assertIn('Shot 1: SIDE_TURN_STANDING. Framing: full-body. ' + shot.FRAMING_GUIDANCE['full-body'], rows)
        self.assertIn('Shot 3: UPRIGHT_SEATED. Framing: half-body. ' + shot.FRAMING_GUIDANCE['half-body'], rows)
        self.assertIn('Shot 5: SLIGHT_FORWARD_LEAN. Framing: knee-up. ' + shot.FRAMING_GUIDANCE['knee-up'], rows)
        self.assertEqual(sum('head-height' in r for r in rows), 6)

    def test_plan_without_framing_guidance_renders_legacy_framing_line(self):
        plan = shot.default_plan('legacy', sample_plan()['coverage'])
        del plan['framing_guidance']
        rows = shot.render(plan).split('\n')
        self.assertIn('Shot 1: SIDE_TURN_STANDING. Framing: full-body.', rows)
        self.assertFalse(any('head-height' in r for r in rows))
        for loose in (True, 1.0):  # renderer must not accept bool/float even when called without validate()
            self.assertNotIn('head-height', shot.render(dict(plan, framing_guidance=loose)))

    def test_framing_guidance_must_be_one_when_present(self):
        context = dict(first_pose=1, output_form='human', purpose='delivery')
        plan = shot.default_plan('legacy', sample_plan()['coverage'])
        shot.validate(plan, inventory(), context=context, count=6)
        for bad in (0, 2, '1', True, None):
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, 'framing_guidance'):
                shot.validate(dict(plan, framing_guidance=bad), inventory(), context=context, count=6)
        v2 = sample_plan()
        with self.assertRaisesRegex(ValueError, 'framing_guidance'):
            self.validate(dict(v2, framing_guidance=2))

    def test_v2_plan_with_framing_guidance_validates_and_renders_it(self):
        plan = dict(sample_plan(), framing_guidance=1)
        self.validate(plan)
        rows = shot.render(plan).split('\n')
        self.assertIn('Shot 1: garment-shot-1. Framing: full-body. ' + shot.FRAMING_GUIDANCE['full-body'], rows)
        self.assertEqual(sum('head-height' in r for r in rows), 9)
        self.assertNotIn('head-height', shot.render(sample_plan()))


if __name__ == '__main__':
    unittest.main()
