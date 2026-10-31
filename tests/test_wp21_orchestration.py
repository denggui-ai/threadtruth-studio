"""WP-21 orchestration: identity-only lock, per-shot variety, commitments, asset trace."""
import copy
import importlib.util
import re
from pathlib import Path
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/threadtruth-studio/scripts'


def module(name):
    spec = importlib.util.spec_from_file_location('wp21_' + name, SCRIPTS / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


model_reference = module('model_reference')
BASE = 'd83e94d'


def legacy_module(name):
    """The d83e94d version of a script, for old-contract regression checks."""
    import subprocess, tempfile
    root = Path(__file__).resolve().parents[1]
    source = subprocess.run(['git', 'show', f'{BASE}:skills/threadtruth-studio/scripts/{name}.py'], cwd=root,
                            capture_output=True, text=True)
    if source.returncode:
        raise unittest.SkipTest('baseline commit unavailable')
    path = Path(tempfile.mkdtemp()) / (name + '.py')
    path.write_text(source.stdout)
    sibling = subprocess.run(['git', 'show', f'{BASE}:skills/threadtruth-studio/scripts/pose_catalog.py'], cwd=root,
                             capture_output=True, text=True)
    if not sibling.returncode:
        (path.parent / 'pose_catalog.py').write_text(sibling.stdout)
    spec = importlib.util.spec_from_file_location('legacy_' + name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class IdentityLockTests(unittest.TestCase):
    def model(self, **changes):
        result = dict(source_type='ai', scope='full', subject='adult female model',
                      locked=['apparent age around 40'], adjustable=['gentle makeup'], consent_note='')
        result.update(changes)
        return result

    def test_identity_lock_is_explicit_and_a_missing_key_keeps_the_legacy_text(self):
        legacy = '\n'.join(model_reference.prompt_lines(self.model()))
        self.assertIn('Retain reference hair and makeup', legacy)
        identity = '\n'.join(model_reference.prompt_lines(self.model(styling_lock='identity')))
        self.assertNotIn('Retain reference hair and makeup', identity)
        self.assertIn('hair, makeup and expression follow the selected style plan', identity)
        self.assertIn('body proportions', identity)
        full = '\n'.join(model_reference.prompt_lines(self.model(styling_lock='full')))
        self.assertIn('Retain reference hair and makeup', full)
        face_only = '\n'.join(model_reference.prompt_lines(self.model(scope='face', styling_lock='identity')))
        self.assertNotIn('body proportions', face_only.split('hair, makeup')[0].split('Identity references')[-1])
        with self.assertRaises(ValueError):
            model_reference.validate_model(self.model(styling_lock='half'))

    def test_old_model_blocks_still_pass_the_new_apply_conditions(self):
        old = legacy_module('model_reference')
        for source in ('ai', 'real'):
            model = self.model(source_type=source, consent_note='Declared likeness permission')
            block = old.apply_conditions('', model)
            self.assertEqual(model_reference.apply_conditions(block.strip(), model), block.strip())
            self.assertEqual(old.prompt_lines(model), model_reference.prompt_lines(model))

    def test_identity_lock_lets_style_hair_makeup_through_but_full_and_legacy_filter_them(self):
        persona = 'cool detached poise; soft matte makeup; loose hair'
        plain = self.model(adjustable=[], styling_lock='identity')
        self.assertIn('makeup', model_reference.resolve_persona(plain, persona))
        self.assertIn('loose hair', model_reference.resolve_persona(plain, persona))
        for lock in ({'styling_lock': 'full'}, {}):
            text = model_reference.resolve_persona(dict(plain, **lock) if lock else {k: v for k, v in plain.items() if k != 'styling_lock'}, persona)
            self.assertNotIn('makeup', text)
            self.assertNotIn('loose hair', text)


shot_plan = module('shot_plan')
library = module('visual_library')
visual_plan = module('visual_plan')
FRONT, BACK = 'a' * 64, 'b' * 64
ACTIONS = ['Stand with a small weight shift.', 'Walk one step toward the camera.', 'Rest one shoulder on a wall.',
           'Sit upright on a plain stool.', 'Lean slightly forward.', 'Adjust the cuff with one hand.',
           'Stand tall with arms relaxed.', 'Pause mid-step.', 'Look down at the hem.']


def sample_plan(count=9, checks=True):
    inventory = [dict(sha256=FRONT, role='garment-source')]
    coverage = [dict(sha256=FRONT, views=['front', 'front-side', 'detail'], usable=True, same_sku=True,
                     note='Synthetic front evidence.')]
    looks = [dict(slot=n, shot_id='shot-' + str(n), display_goal='Show the garment length.', must_show=['hem'],
                  reason='Hands clear the garment.', body_action=ACTIONS[n - 1], hands='Both hands low.',
                  support='Both feet on the floor.', framing='full-body', garment_views=['front'],
                  reference_sha256s=[FRONT]) for n in range(1, count + 1)]
    plan = dict(version=2, sku='top', route='B', coverage=coverage, looks=looks,
                selected_shot_ids=[x['shot_id'] for x in looks], series_role='series')
    if checks:
        plan['variety_checks'] = 1
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
            bad, _ = sample_plan(checks=True)
            bad['looks'][2][key] = text
            with self.assertRaisesRegex(ValueError, 'back'):
                self.validate(bad, inventory)
        bad, _ = sample_plan(checks=True)
        bad['looks'][1]['body_action'] = '  stand with a SMALL weight shift. '
        with self.assertRaisesRegex(ValueError, 'repeats'):
            self.validate(bad, inventory)
        bad, _ = sample_plan(checks=True)
        bad['looks'][1]['body_action'] = ACTIONS[0]
        bad['looks'][1]['framing'] = 'half-body'
        self.validate(bad, inventory)  # same action in another framing is a different shot

    def test_checks_apply_only_to_plans_that_opt_in_and_ignore_punctuation(self):
        old, inventory = sample_plan(checks=False)
        old['looks'][1]['body_action'] = old['looks'][0]['body_action']
        old['looks'][2]['body_action'] = 'Facing away, walking away from behind the camera.'
        self.validate(old, inventory)  # a frozen legacy plan keeps validating
        legacy = legacy_module('shot_plan')
        legacy.validate(old, inventory, context=dict(first_pose=1, output_form='human', purpose='delivery'), count=9, model_source='new')
        new, _ = sample_plan()
        new['looks'][1]['body_action'] = ACTIONS[0].upper().replace('.', '!!')
        with self.assertRaisesRegex(ValueError, 'repeats'):
            self.validate(new, inventory)
        for text in ('Facing away from the lens.', 'Walking away down the hall.', 'Seen from behind, hands low.', 'Looks over the shoulder.'):
            bad, _ = sample_plan()
            bad['looks'][2]['body_action'] = text
            with self.assertRaisesRegex(ValueError, 'back'):
                self.validate(bad, inventory)
        bad, _ = sample_plan()
        bad['variety_checks'] = 2
        with self.assertRaises(ValueError):
            self.validate(bad, inventory)

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


class MissingBackTests(unittest.TestCase):
    def spec(self, **changes):
        base = dict(entry_id='nordic-minimal', output_form='flat-lay', count=6,
                    inventory=[dict(sha256=FRONT, role='garment-source')],
                    garment=dict(description='A source-backed coat.', keep=['Keep the buttons.'], source_sha256s=[FRONT]))
        return dict(base, **changes)

    def test_flat_lay_without_back_source_swaps_slot_two_for_a_front_detail(self):
        plan = library.prepare(self.spec())
        self.assertIs(plan['presentation_2_substituted'], True)
        slot2 = visual_plan.render(plan, 2)
        self.assertIn('front detail', slot2)
        self.assertIsNone(re.search(r'\bback\b', slot2.lower()))
        self.assertNotIn('front detail', visual_plan.render(plan, 3))
        self.assertIn('front detail', visual_plan.render(plan))  # preview grid shows the same swap
        with_back = library.prepare(self.spec(back_source=True))
        self.assertNotIn('presentation_2_substituted', with_back)
        self.assertNotIn('front detail', visual_plan.render(with_back, 2))
        single = library.prepare(self.spec(count=1))
        self.assertNotIn('presentation_2_substituted', single)

    def test_subset_to_one_cell_keeps_the_flag_only_for_slot_two(self):
        plan = library.prepare(self.spec())
        inventory = self.spec()['inventory']
        for pose in range(1, 7):
            one = visual_plan.subset(plan, pose)
            self.assertEqual(one.get('presentation_2_substituted', False), pose == 2)
            visual_plan.validate(one, inventory, context=dict(style='nordic-minimal', first_pose=pose, output_form='flat-lay'),
                                 count=1, identity=False)

    def test_preview_converts_to_single_deliveries_with_and_without_the_flag(self):
        import tempfile
        from PIL import Image
        spec = importlib.util.spec_from_file_location('wp21_web_task2', SCRIPTS / 'web-task.py')
        task = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(task)
        for pose in (2, 4):
            with self.subTest(pose=pose), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                image = root / 'front.png'
                Image.new('RGB', (60, 40), 'red').save(image)
                digest = task.digest(image)
                plan = library.prepare(self.spec(inventory=[dict(sha256=digest, role='garment-source')],
                                                 garment=dict(description='A source-backed coat.', keep=['Keep the buttons.'],
                                                              source_sha256s=[digest])))
                context = dict(outfit='coat', style='nordic-minimal', mode='C', output_form='flat-lay', size=[60, 40],
                               first_pose=1, purpose='preview-grid')
                job = root / 'preview'
                task.create(job, [image], None, [60, 40], False, context=context, visual_plan=plan)
                task.update(job, 'authorize', limit=1, note='One preview')
                data = task.read(job)
                task.update(job, 'reserve', look=1, ready=True, refs=task.reference_hashes(job, 1),
                            expected_plan_sha256=task.plan_fingerprint(data), expected_prompt_sha256=data['looks'][0]['prompt_sha256'])
                out = root / 'out.png'
                Image.new('RGB', (60, 40), 'yellow').save(out)
                task.update(job, 'returned', look=1, file=out)
                task.update(job, 'accept', look=1, qa='qa-pass', note='Synthetic reviewed image')
                task.update(job, 'finish-preview', decision='direction-confirmed', note='Reviewed arrangements')
                child = task.create_from_preview(root / 'single', job, dict(context=dict(context, purpose='delivery', first_pose=pose),
                                                 size=[60, 40], count=1), note='One independent image')
                self.assertEqual(bool(child.get('presentation_2_substituted')), pose == 2)
                self.assertEqual('front detail' in child['looks'][0]['prompt'], pose == 2)

    def test_task_record_notes_the_substitution(self):
        import tempfile
        from PIL import Image
        spec = importlib.util.spec_from_file_location('wp21_web_task', SCRIPTS / 'web-task.py')
        task = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(task)
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / 'front.png'
            Image.new('RGB', (60, 40), 'red').save(image)
            digest = task.digest(image)
            plan = library.prepare(self.spec(inventory=[dict(sha256=digest, role='garment-source')],
                                             garment=dict(description='A source-backed coat.', keep=['Keep the buttons.'],
                                                          source_sha256s=[digest])))
            context = dict(outfit='coat', style='nordic-minimal', mode='C', output_form='flat-lay', size=[60, 40],
                           first_pose=1, purpose='preview-grid')
            record = task.create(Path(tmp) / 'job', [image], None, [60, 40], False, context=context, visual_plan=plan)
            self.assertIs(record['presentation_2_substituted'], True)
            self.assertIn('front detail', record['looks'][0]['prompt'])


class AssetTraceTests(unittest.TestCase):
    TRACE = [dict(asset='C11', decision='translated', affects='garment.keep and scene',
                  check='stand collar, side closure and slit match the source photo')]

    def spec(self, **changes):
        base = dict(entry_id='qipao-urban', inventory=[dict(sha256=FRONT, role='garment-source')],
                    garment=dict(description='A source-backed qipao.', keep=['Keep the stand collar.'], source_sha256s=[FRONT]),
                    culture_profile=dict(id='qipao-contemporary-daily', version=1, form='contemporary daily qipao'),
                    asset_trace=copy.deepcopy(self.TRACE))
        return dict(base, **changes)

    def test_cultural_entries_need_a_culture_profile_and_an_asset_trace(self):
        plan = library.prepare(self.spec())
        self.assertEqual(plan['asset_trace'], self.TRACE)
        self.assertNotIn('C11', visual_plan.render(plan))  # stored for QA and reports, never rendered
        for changes in (dict(asset_trace=[]), dict(asset_trace=None), dict(culture_profile=None),
                        dict(asset_trace=[dict(self.TRACE[0], asset='not-in-catalog')]),
                        dict(asset_trace=[dict(self.TRACE[0], decision='guessed')])):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                spec = self.spec(**changes)
                spec = {key: value for key, value in spec.items() if value is not None}
                library.prepare(spec)
        frozen = copy.deepcopy(plan)
        context = dict(style='qipao-urban', first_pose=1, output_form='human')
        inventory = [dict(sha256=FRONT, role='garment-source')]
        visual_plan.validate(frozen, inventory, context=context, count=9)
        for key in ('culture_profile', 'asset_trace'):
            stripped = {k: v for k, v in frozen.items() if k != key}
            with self.subTest(removed=key), self.assertRaisesRegex(ValueError, 'Cultural entries'):
                visual_plan.validate(stripped, inventory, context=context, count=9)
        # other entries may still skip the trace
        plain = library.prepare(dict(self.spec(entry_id='nordic-minimal'), asset_trace=None))
        self.assertNotIn('asset_trace', plain)


class ContractTests(unittest.TestCase):
    def plan(self, **spec):
        return CommitmentTests().plan(**spec)

    def test_plans_without_contract_render_and_apply_exactly_like_the_baseline(self):
        old = legacy_module('visual_plan')
        model = dict(source_type='new', scope='full', subject='adult female model', locked=[], adjustable=[], consent_note='')
        plan = self.plan(model=model)
        self.assertEqual(plan['contract'], 21)
        self.assertIn('identity stays as declared', visual_plan.render(plan))
        legacy = {k: v for k, v in plan.items() if k not in ('contract', 'commitments', 'commitments_skipped', 'open_variables')}
        self.assertIn('persona', legacy)
        for look in (None, 1):
            frozen = old.render(legacy, look)
            self.assertEqual(visual_plan.render(legacy, look), frozen)
            self.assertEqual(visual_plan.apply(frozen, legacy, look), frozen)
        self.assertIn('yields to the declared model conditions', visual_plan.render(legacy))

    def test_new_keys_require_the_contract(self):
        plan = self.plan()
        inventory = [dict(sha256=FRONT, role='garment-source')]
        context = dict(style='korean-cold-editorial', first_pose=1, output_form='human')
        bare = {k: v for k, v in plan.items() if k != 'contract'}
        with self.assertRaisesRegex(ValueError, 'contract'):
            visual_plan.validate(bare, inventory, context=context, count=9)

    def test_model_conditions_that_declare_expression_or_makeup_skip_the_matching_commitments(self):
        model = dict(source_type='ai', scope='full', subject='adult female model',
                     locked=['smiling expression', 'no makeup', 'tied-back hair'], adjustable=[], consent_note='')
        plan = self.plan(model=model)
        self.assertEqual(self.ids(plan['commitments']), ['kc-side-light', 'kc-negative-space', 'kc-cool-white-balance'])
        self.assertEqual(plan['commitments_skipped'],
                         [dict(id='kc-detached-expression', reason='model-condition'), dict(id='kc-dewy-makeup', reason='model-condition')])
        prompt = visual_plan.render(plan, 1)
        self.assertNotIn('no smile', prompt)
        self.assertNotIn('gray-brown eyeshadow', prompt)
        model_reference.apply_conditions(prompt, plan_model(model))

    def ids(self, rows):
        return [row['id'] for row in rows]


def plan_model(model):
    return dict(model, styling_lock='identity')


class PoseVocabularyTests(unittest.TestCase):
    """WP-21f: style pose vocabulary on korean-cold-editorial / french-effortless."""
    def vocab(self, entry='korean-cold-editorial'):
        return library.card(entry)['pose_vocabulary']

    def validate(self, plan, inventory, vocab):
        return shot_plan.validate(plan, inventory, context=dict(first_pose=1, output_form='human', purpose='delivery'),
                                  count=len(plan['selected_shot_ids']), model_source='new', pose_vocabulary=vocab)

    def with_poses(self, ids, count=9, checks=True):
        plan, inventory = sample_plan(count, checks)
        for look, pose_id in zip(plan['looks'], ids):
            look['pose_id'] = pose_id
        return plan, inventory

    FRONT_IDS = ['kc-wall-stand', 'kc-edge-sit', 'kc-pause-step', 'kc-seated-lean', 'kc-wall-stand']

    def test_unknown_pose_id_is_rejected_and_lists_the_available_ids(self):
        plan, inventory = self.with_poses(self.FRONT_IDS)
        self.validate(plan, inventory, self.vocab())
        plan['looks'][0]['pose_id'] = 'kc-not-a-pose'
        with self.assertRaisesRegex(ValueError, 'pose_id.*kc-wall-stand'):
            self.validate(plan, inventory, self.vocab())

    def test_nine_looks_need_five_pose_ids(self):
        inventory = sample_plan()[1]
        four, _ = self.with_poses(self.FRONT_IDS[:4])
        with self.assertRaisesRegex(ValueError, 'at least 5.*kc-wall-stand'):
            self.validate(four, inventory, self.vocab())
        five, _ = self.with_poses(self.FRONT_IDS)
        self.validate(five, inventory, self.vocab())

    def test_entry_views_must_be_covered_by_the_look(self):
        plan, inventory = self.with_poses(self.FRONT_IDS)
        plan['looks'][0]['pose_id'] = 'kc-back-turn'  # needs "back"; the look shows only "front"
        with self.assertRaisesRegex(ValueError, 'lacks: back'):
            self.validate(plan, inventory, self.vocab())

    def test_cards_without_a_vocabulary_are_not_checked(self):
        self.assertNotIn('pose_vocabulary', library.card('bridal-ethereal'))
        plan, inventory = self.with_poses(['whatever'] * 2)
        self.validate(plan, inventory, None)
        plan, inventory = sample_plan()
        self.validate(plan, inventory, library.card('bridal-ethereal').get('pose_vocabulary'))

    def test_plans_without_variety_checks_skip_the_pose_checks(self):
        plan, inventory = self.with_poses(['kc-not-a-pose'], checks=False)
        self.validate(plan, inventory, self.vocab())

    def test_card_vocabularies_are_valid_and_adjustable_styling_does_not_skip_commitments(self):
        for entry in ('korean-cold-editorial', 'french-effortless'):
            visual_plan.check_pose_vocabulary(self.vocab(entry), library.card(entry)['action_tendency'])
        bad = copy.deepcopy(self.vocab())
        bad[1]['id'] = bad[0]['id']
        with self.assertRaisesRegex(ValueError, 'repeats'):
            visual_plan.check_pose_vocabulary(bad)
        bad = copy.deepcopy(self.vocab())
        bad[0]['views'] = ['sideways']
        with self.assertRaisesRegex(ValueError, 'views'):
            visual_plan.check_pose_vocabulary(bad)
        make = CommitmentTests().plan
        model = dict(source_type='ai', scope='full', subject='adult female model',
                     locked=['apparent age around 40'], adjustable=['faint smile', 'soft makeup'], consent_note='')
        plan = make(model=model)
        self.assertEqual(plan['commitments_skipped'], [])
        locked = dict(model, locked=['smiling expression'], adjustable=[])
        self.assertEqual([r['id'] for r in make(model=locked)['commitments_skipped']], ['kc-detached-expression'])
