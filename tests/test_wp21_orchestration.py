"""WP-21 orchestration: identity-only lock, per-shot variety, commitments, asset trace."""
import copy
import importlib.util
from pathlib import Path
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/threadtruth-studio/scripts'


def module(name):
    spec = importlib.util.spec_from_file_location('wp21_' + name, SCRIPTS / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


model_reference = module('model_reference')


class IdentityLockTests(unittest.TestCase):
    def model(self, **changes):
        result = dict(source_type='ai', scope='full', subject='adult female model',
                      locked=['apparent age around 40'], adjustable=['gentle makeup'], consent_note='')
        result.update(changes)
        return result

    def test_styling_lock_default_is_identity_only_and_full_retains_hair_makeup(self):
        default = '\n'.join(model_reference.prompt_lines(self.model()))
        self.assertNotIn('Retain reference hair and makeup', default)
        self.assertIn('hair, makeup and expression follow the selected style plan', default)
        self.assertIn('body proportions', default)
        full = '\n'.join(model_reference.prompt_lines(self.model(styling_lock='full')))
        self.assertIn('Retain reference hair and makeup', full)
        face_only = '\n'.join(model_reference.prompt_lines(self.model(scope='face')))
        self.assertNotIn('body proportions', face_only.split('hair, makeup')[0].split('Identity references')[-1])
        with self.assertRaises(ValueError):
            model_reference.validate_model(self.model(styling_lock='half'))

    def test_identity_lock_lets_style_hair_makeup_through_but_full_filters_them(self):
        persona = 'cool detached poise; soft matte makeup; loose hair'
        plain = self.model(adjustable=[])
        self.assertIn('makeup', model_reference.resolve_persona(plain, persona))
        self.assertIn('loose hair', model_reference.resolve_persona(plain, persona))
        full = model_reference.resolve_persona(dict(plain, styling_lock='full'), persona)
        self.assertNotIn('makeup', full)
        self.assertNotIn('loose hair', full)


shot_plan = module('shot_plan')
library = module('visual_library')
visual_plan = module('visual_plan')
FRONT, BACK = 'a' * 64, 'b' * 64
ACTIONS = ['Stand with a small weight shift.', 'Walk one step toward the camera.', 'Rest one shoulder on a wall.',
           'Sit upright on a plain stool.', 'Lean slightly forward.', 'Adjust the cuff with one hand.',
           'Stand tall with arms relaxed.', 'Pause mid-step.', 'Look down at the hem.']


def sample_plan(count=9):
    inventory = [dict(sha256=FRONT, role='garment-source')]
    coverage = [dict(sha256=FRONT, views=['front', 'front-side', 'detail'], usable=True, same_sku=True,
                     note='Synthetic front evidence.')]
    looks = [dict(slot=n, shot_id='shot-' + str(n), display_goal='Show the garment length.', must_show=['hem'],
                  reason='Hands clear the garment.', body_action=ACTIONS[n - 1], hands='Both hands low.',
                  support='Both feet on the floor.', framing='full-body', garment_views=['front'],
                  reference_sha256s=[FRONT]) for n in range(1, count + 1)]
    plan = dict(version=2, sku='top', route='B', coverage=coverage, looks=looks,
                selected_shot_ids=[x['shot_id'] for x in looks], series_role='series')
    return plan, inventory


class ShotVarietyTests(unittest.TestCase):
    def validate(self, plan, inventory):
        return shot_plan.validate(plan, inventory, context=dict(first_pose=1, output_form='human', purpose='delivery'),
                                  count=len(plan['selected_shot_ids']), model_source='new')

    def test_back_words_without_back_coverage_and_duplicate_actions_are_rejected(self):
        plan, inventory = sample_plan()
        self.validate(plan, inventory)
        for key, text in (('body_action', 'Stand with the body over-shoulder to the lens.'),
                          ('body_action', 'Back to camera, then glance away.')):
            bad, _ = sample_plan()
            bad['looks'][2][key] = text
            with self.assertRaisesRegex(ValueError, 'back'):
                self.validate(bad, inventory)
        bad, _ = sample_plan()
        bad['looks'][1]['body_action'] = '  stand with a SMALL weight shift. '
        with self.assertRaisesRegex(ValueError, 'repeats'):
            self.validate(bad, inventory)
        bad, _ = sample_plan()
        bad['looks'][1]['body_action'] = ACTIONS[0]
        bad['looks'][1]['framing'] = 'half-body'
        self.validate(bad, inventory)  # same action in another framing is a different shot

    def test_look_scene_lighting_camera_override_the_card_per_shot(self):
        plan, inventory = sample_plan()
        plan['looks'][1]['scene'] = 'A sunlit stairwell with pale plaster walls.'
        plan['looks'][1]['lighting'] = 'Window light from the left with a dim right side.'
        plan['looks'][1]['camera'] = 'Eye-level lens with the subject off-centre.'
        self.validate(plan, inventory)
        spec = dict(entry_id='nordic-minimal', inventory=inventory, shot_plan=plan,
                    garment=dict(description='A source-backed top.', keep=['Keep the front.'], source_sha256s=[FRONT]))
        prepared = library.prepare(spec)
        scenes = [row for row in visual_plan.render(prepared).split('\n') if row.startswith('Scene: ')]
        self.assertEqual(len(scenes), 9)
        self.assertEqual(len(set(scenes)), 2)
        self.assertIn('Scene: A sunlit stairwell with pale plaster walls.', scenes)
        self.assertEqual(prepared['shots'][1]['composition'], 'Eye-level lens with the subject off-centre.')
        self.assertEqual(prepared['shots'][0]['lighting'], prepared['photography']['lighting'])


class CommitmentTests(unittest.TestCase):
    def plan(self, entry='korean-cold-editorial', **spec):
        inventory = [dict(sha256=FRONT, role='garment-source')]
        base = dict(entry_id=entry, inventory=inventory,
                    garment=dict(description='A source-backed vest.', keep=['Keep the zipper.'], source_sha256s=[FRONT]))
        return library.prepare(dict(base, **spec))

    def ids(self, rows):
        return [row['id'] for row in rows]

    def test_faceless_drops_expression_and_makeup_commitments_into_skipped(self):
        human = self.plan()
        self.assertEqual(self.ids(human['commitments']),
                         ['kc-side-light', 'kc-negative-space', 'kc-detached-expression', 'kc-dewy-makeup', 'kc-cool-white-balance'])
        self.assertEqual(human['commitments_skipped'], [])
        faceless = self.plan(output_form='faceless')
        self.assertEqual(self.ids(faceless['commitments']), ['kc-side-light', 'kc-negative-space', 'kc-cool-white-balance'])
        self.assertEqual(self.ids(faceless['commitments_skipped']), ['kc-detached-expression', 'kc-dewy-makeup'])
        text = visual_plan.render(faceless)
        self.assertIn('wide soft side light', text)
        self.assertNotIn('detached, quiet', text)
        self.assertNotIn('gray-brown eyeshadow', text)
        self.assertIn('detached, quiet', visual_plan.render(human))
        # a full styling lock keeps the reference makeup, so the makeup commitment is skipped
        locked = self.plan(model=dict(source_type='ai', scope='full', subject='adult female model',
                                      locked=['apparent age around 40'], adjustable=[], consent_note='', styling_lock='full'))
        self.assertEqual(self.ids(locked['commitments_skipped']), ['kc-dewy-makeup'])
        flat = self.plan(output_form='flat-lay', count=6)
        self.assertEqual(self.ids(flat['commitments']), ['kc-side-light', 'kc-negative-space', 'kc-cool-white-balance'])

    def test_commitment_validation_and_catalog_negative_follow_the_objective(self):
        plan = self.plan()
        bad = copy.deepcopy(plan)
        bad['commitments'][0]['needs'] = ['gaze']
        inventory = [dict(sha256=FRONT, role='garment-source')]
        context = dict(style='korean-cold-editorial', first_pose=1, output_form='human')
        with self.assertRaises(ValueError):
            visual_plan.validate(bad, inventory, context=context, count=9)
        bad = copy.deepcopy(plan)
        bad['open_variables'] = ['lighting']
        with self.assertRaises(ValueError):
            visual_plan.validate(bad, inventory, context=context, count=9)
        self.assertIn('no e-commerce catalog look', plan['negatives'])
        self.assertNotIn('no e-commerce catalog look', self.plan(objective='product-display')['negatives'])
        card = library.card('korean-cold-editorial')
        self.assertNotIn('唯一的暖色', card['photography']['palette'])
