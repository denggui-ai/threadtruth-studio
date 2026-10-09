"""Scoped persona overrides through the shared resolver and actual prompt builders."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StylePersonaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load_module('persona_model_reference', ROOT/'skills/threadtruth-studio/scripts/model_reference.py')
        cls.preview = load_module('persona_style_preview', ROOT/'tools/style_preview.py')
        cls.packs = cls.preview._registered_packs(ROOT)

    def model(self, source='new', **changes):
        model = dict(source_type=source, scope='full', subject='adult female model',
                     locked=[], adjustable=[], consent_note='Express likeness permission')
        model.update(changes)
        return model

    def test_new_without_overrides_preserves_persona_and_person_negatives(self):
        persona = 'gentle natural ease, soft everyday calm, relaxed expression'
        negatives = ['no sweet smile', 'no dyed hair', 'no busy background']
        self.assertEqual(self.m.resolve_style(self.model(), persona, negatives), (persona, negatives))

    def test_identity_does_not_replace_expression_or_demeanor(self):
        persona = 'relaxed face, friendly expression, quiet confidence'
        for source in ('real', 'ai', 'new'):
            with self.subTest(source=source):
                actual, _ = self.m.resolve_style(self.model(source, locked=['same face']), persona, [])
                self.assertEqual(actual, persona)
                self.assertEqual(self.m.resolve_mood(self.model(source, locked=['same face']), persona), persona)

    def test_identity_keeps_case_variants_of_facial_expression_language(self):
        persona = 'RELAXED FACE, calm FACIAL EXPRESSION, quiet confidence'
        model = self.model('real', locked=['same face'])
        actual, _ = self.m.resolve_style(model, persona, [])
        self.assertEqual(actual, persona)
        self.assertEqual(self.m.resolve_mood(model, persona), persona)

    def test_body_conditions_preserve_relaxed_gestures_and_pose_instructions(self):
        persona = ('neutral approachable expression, relaxed jaw and shoulders, relaxed body language, '
                   'weight naturally on one leg when standing, hands at ease at the side, composed catalog attitude')
        model = self.model('real', locked=['same face', 'natural fuller body proportions'])
        actual, _ = self.m.resolve_style(model, persona, [])
        self.assertEqual(actual, persona)
        self.assertEqual(self.m.resolve_mood(model, 'relaxed body language, soft even lighting'),
                         'relaxed body language, soft even lighting')

    def test_explicit_expression_removes_alternative_and_preserves_demeanor(self):
        persona, negatives = self.m.resolve_style(
            self.model(adjustable=['friendly smile']),
            'cold detached expression, quiet confidence, relaxed shoulders',
            ['no sweet smile', 'no dyed hair', 'no glossy commercial retouch'])
        self.assertEqual(persona, 'quiet confidence, relaxed shoulders')
        self.assertEqual(negatives, ['no dyed hair', 'no glossy commercial retouch'])

    def test_fixed_and_adjustable_conditions_override_their_own_axes(self):
        persona = ('short bob hair, dewy makeup, angular facial features, youthful appearance, '
                   'slender physique, pale skin tone, quiet confidence, relaxed shoulders')
        model = self.model(locked=['long tied hair', 'mature apparent age', 'natural fuller proportions'],
                           adjustable=['matte makeup', 'rounded facial features', 'warm skin tone'])
        actual, _ = self.m.resolve_style(model, persona, [])
        self.assertEqual(actual, 'quiet confidence, relaxed shoulders')

    def test_existing_identity_retains_original_hair_makeup_defaults(self):
        persona = 'dewy makeup, natural flyaway hair, friendly expression, quiet confidence'
        negatives = ['no opera makeup', 'no dyed hair', 'no sweet smile', 'no busy background']
        for source in ('real', 'ai', 'new'):
            with self.subTest(source=source):
                actual, kept = self.m.resolve_style(self.model(source), persona, negatives)
                if source == 'new':
                    self.assertEqual((actual, kept), (persona, negatives))
                else:
                    self.assertEqual(actual, 'friendly expression, quiet confidence')
                    self.assertEqual(kept, ['no sweet smile', 'no busy background'])

    def test_coordinated_makeup_colors_yield_as_one_appearance_phrase(self):
        mood = 'soft even lighting; gray-brown and nude pink eye makeup; quiet confidence'
        for origin in ('real', 'ai', 'new'):
            with self.subTest(source=origin):
                expected = mood if origin == 'new' else 'soft even lighting; quiet confidence'
                self.assertEqual(self.m.resolve_mood(self.model(origin), mood), expected)
                persona, _ = self.m.resolve_style(self.model(origin), mood, [])
                self.assertEqual(persona, expected)

    def test_frozen_korean_pack_does_not_leave_an_orphan_makeup_color_in_mood(self):
        text = next(text for slug, _, text in self.packs if slug == 'korean-cold-editorial')
        preview = dict(visual=self.preview._visual(text),
                       negative_delta_add=self.preview._list_field(text, 'negative_delta_add'))
        for origin in ('real', 'ai'):
            with self.subTest(source=origin):
                actual = self.preview._model_preview(preview, self.model(origin))
                self.assertNotIn('gray-brown', actual['visual']['mood'])
                self.assertNotIn('nude pink eye makeup', actual['visual']['mood'])
                for photography in ('soft even lighting', 'cold gray', 'medium format film photography texture',
                                    'realistic native skin texture', 'subtle pores'):
                    self.assertIn(photography, actual['visual']['mood'])
                self.assertIn('quietly confident', actual['visual']['persona'])

    def test_coordinated_appearance_preserves_separate_gesture_and_photography_clauses(self):
        persona = ('angular face and relaxed shoulders; '
                   'gray-brown and nude pink eye makeup under soft window lighting and quiet confidence')
        actual, _ = self.m.resolve_style(self.model('real'), persona, [])
        self.assertEqual(actual, 'relaxed shoulders; soft window lighting quiet confidence')

    def test_unknown_coordinated_appearance_requires_review_instead_of_orphan_text(self):
        with self.assertRaisesRegex(ValueError, 'Review coordinated person/style'):
            self.m.resolve_mood(self.model('real'), 'soft even lighting; taupe and hazel eye makeup')

    def test_existing_scope_retains_known_identity_without_inventing_unseen_body(self):
        persona = ('angular facial features, youthful appearance, pale skin tone, slender physique, '
                   'relaxed face, relaxed body language, friendly expression, quiet confidence')
        for origin in ('real', 'ai', 'new'):
            for scope in ('face', 'full'):
                with self.subTest(source=origin, scope=scope):
                    actual, _ = self.m.resolve_style(self.model(origin, scope=scope), persona, [])
                    if origin == 'new':
                        self.assertEqual(actual, persona)
                    else:
                        preserved = 'relaxed face, relaxed body language, friendly expression, quiet confidence'
                        self.assertEqual(actual, ('slender physique, ' if scope == 'face' else '') + preserved)

    def test_negative_filter_preserves_safety_and_unrelated_person_constraints(self):
        negatives = ['no underage styling', 'no sexualized body', 'no deformed face',
                     'no extra fingers', 'no influencer style', 'no dyed hair', 'no sweet smile']
        actual, kept = self.m.resolve_style(self.model(locked=['neutral expression']), 'quiet confidence', negatives)
        self.assertEqual(actual, 'quiet confidence')
        self.assertEqual(kept, negatives[:-1])

    def test_mixed_clause_preserves_photography_after_conflicting_condition_yields(self):
        persona = 'cold detached expression under soft window lighting, relaxed shoulders, film grain'
        negatives = ['no sweet smile and no busy background', 'no sexualized pose']
        actual, kept = self.m.resolve_style(self.model(adjustable=['friendly smile']), persona, negatives)
        self.assertEqual(actual, 'soft window lighting, relaxed shoulders, film grain')
        self.assertEqual(kept, ['no busy background', 'no sexualized pose'])

    def test_inseparable_conflict_requires_review_instead_of_discarding_photography(self):
        for persona, negatives in [('smiling face light photography', []),
                                   ('quiet confidence', ['no smiling face light photography'])]:
            with self.subTest(persona=persona, negatives=negatives), self.assertRaisesRegex(ValueError, 'Review mixed person/photography'):
                self.m.resolve_style(self.model(adjustable=['neutral expression']), persona, negatives)

    def test_same_declared_phrase_is_retained(self):
        persona, _ = self.m.resolve_style(self.model(adjustable=['friendly smile']),
                                          'friendly smile, relaxed shoulders', [])
        self.assertEqual(persona, 'friendly smile, relaxed shoulders')

    def test_all_24_packs_without_explicit_person_overrides_preserve_their_personas(self):
        self.assertEqual(len(self.packs), 24)
        for slug, _, text in self.packs:
            persona = self.preview._field(text, 'model_persona')
            negatives = self.preview._list_field(text, 'negative_delta_add')
            for source in ('real', 'ai', 'new'):
                with self.subTest(pack=slug, source=source):
                    actual, kept = self.m.resolve_style(self.model(source), persona, negatives)
                    self.assertEqual(actual, persona)
                    expected = [n for n in negatives if not (source != 'new' and n == 'no opera makeup')]
                    self.assertEqual(kept, expected)

    def test_all_24_pack_source_and_declared_axis_conditions_matrix(self):
        # These alternatives are hand-checked pack clauses, independent of the resolver.
        removed = {
            'athleisure': ['energetic relaxed expression'],
            'balletcore': ['graceful calm expression'],
            'clean-fit': ['calm composed expression'],
            'ecommerce-studio': ['neutral approachable expression'],
            'french-effortless': ['relaxed natural expression', 'no aegyo'],
            'korean-cold-editorial': ['detached', 'no aegyo', 'no influencer mugging'],
            'nordic-minimal': ['calm reserved expression'],
        }
        expression_negatives = {'no cold detached expression', 'no sweet idol smile', 'no aegyo', 'no sweet aegyo mood'}
        conditions = [('empty', []), ('identity', ['same face']),
                      ('body', ['natural fuller body proportions']), ('expression', ['friendly smile']),
                      ('hair', ['tidy tied hair']), ('makeup', ['matte makeup'])]
        for slug, _, text in self.packs:
            persona = self.preview._field(text, 'model_persona')
            negatives = self.preview._list_field(text, 'negative_delta_add')
            for source in ('real', 'ai', 'new'):
                for axis, values in conditions:
                    with self.subTest(pack=slug, source=source, axis=axis):
                        actual, kept = self.m.resolve_style(self.model(source, locked=values), persona, negatives)
                        if axis == 'expression':
                            for clause in removed.get(slug, []):
                                self.assertNotIn(clause, actual)
                            if not removed.get(slug):
                                self.assertEqual(actual, persona)
                            for clause in persona.replace(';', ',').split(','):
                                clause = clause.strip()
                                if clause and clause not in removed.get(slug, []):
                                    self.assertIn(clause, actual)
                        else:
                            self.assertEqual(actual, persona)
                        dropped = expression_negatives if axis == 'expression' else set()
                        if source != 'new' or axis == 'makeup':
                            dropped = dropped | {'no opera makeup'}
                        self.assertEqual(kept, [n for n in negatives if n not in dropped])

    def test_actual_preview_and_single_prompt_paths_preserve_unconflicted_pack_style(self):
        # Exercise both final consumer paths with registered packs, without generating pixels.
        source = {'assets': [{'path': 'garment.png'}], 'outfit': {'core_items': ['existing linen shirt']}}
        anchor = {'path': 'identity.png'}
        for slug, _, text in self.packs:
            persona = self.preview._field(text, 'model_persona')
            pose = dict(ordinal=1, row=1, column=1, master='STAND', description='stand naturally',
                        head_gaze='follow pose', scene='low-distraction studio')
            preview = dict(style=slug, mode='B', visual=self.preview._visual(text),
                           negative_delta_add=self.preview._list_field(text, 'negative_delta_add'),
                           label_contract=dict(title='Direction', subtitle='Preview', footer='AI preview'),
                           poses=[pose], layout_contract={'framing': ['full-body']})
            for kind in ('preview', 'single'):
                for origin in ('real', 'ai', 'new'):
                    model = self.model(origin, locked=['same face', 'natural fuller body proportions'])
                    refs = [] if origin == 'new' else [dict(path='identity.png', role='identity-reference')]
                    with self.subTest(pack=slug, source=origin, path=kind):
                        if kind == 'preview':
                            actual = self.preview._prompt(preview, source, anchor, 'no deformed anatomy',
                                                          'follow pose', model=model, model_references=refs)
                        else:
                            actual = self.preview._single_prompt(preview, source, anchor, pose, 'no deformed anatomy',
                                                                 'keep feet', '2:3', False, 'follow pose',
                                                                 model=model, model_references=refs)
                        self.assertIn('Attitude: ' + persona, actual)
                        self.assertIn('Lighting/background palette: ' + preview['visual']['lighting'], actual)
                        self.assertIn('natural fuller body proportions', actual)


if __name__ == '__main__':
    unittest.main()
