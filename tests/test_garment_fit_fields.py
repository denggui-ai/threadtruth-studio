"""Optional garment fit and shared body-length facts render as fixed geometric sentences."""
import copy, hashlib, importlib.util, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/lookset/scripts'


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


class GarmentFitFieldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library = load('wp16_fit_library', 'visual_library.py')
        cls.vp = load('wp16_fit_visual_plan', 'visual_plan.py')
        from tests.test_runtime_quickstart import v2_plan
        cls.v2_plan = staticmethod(v2_plan)

    def spec(self, **garment_extra):
        h = 'd' * 64
        garment = dict(description='Synthetic red garment.', keep=['red'], source_sha256s=[h], **garment_extra)
        return dict(entry_id='french-effortless', garment=garment, inventory=[dict(role='garment-source', sha256=h)],
                    model=dict(source_type='new', scope='full', subject='adult female model', locked=[], adjustable=[], consent_note=''),
                    output_form='human', shot_plan=self.v2_plan(h))

    def prepared(self, **garment_extra):
        return self.library.prepare(self.spec(**garment_extra))

    def validate(self, plan):
        return self.vp.validate(plan, [dict(role='garment-source', sha256='d' * 64)],
                                context=dict(style='french-effortless', first_pose=1, output_form='human'),
                                count=9, identity=True, shot_plan=self.v2_plan('d' * 64))

    def test_bad_hem_state_names_path_choices_and_value(self):
        plan = self.prepared(); plan['garment']['hem_state'] = 'tuck'
        with self.assertRaises(ValueError) as caught:
            self.validate(plan)
        message = str(caught.exception)
        self.assertIn('visual_plan.garment.hem_state must be one of untucked, tucked, half-tucked', message)
        self.assertIn("got 'tuck'", message)

    def test_unhashable_silhouette_is_a_value_error_not_type_error(self):
        plan = self.prepared(); plan['garment']['silhouette'] = ['straight-leg']
        with self.assertRaises(ValueError) as caught:
            self.validate(plan)
        self.assertIn('visual_plan.garment.silhouette', str(caught.exception))
        self.assertIn('got list of 1', str(caught.exception))

    def test_unknown_garment_key_keeps_original_sentence_and_reports_got(self):
        plan = self.prepared(); plan['garment']['fit'] = 'loose'
        with self.assertRaises(ValueError) as caught:
            self.validate(plan)
        message = str(caught.exception)
        self.assertIn('Garment facts require description, keep and original source_sha256s', message)
        self.assertIn('got dict of 4', message)

    def test_render_adds_fixed_sentences_in_place(self):
        plan = self.prepared(hem_state='untucked', silhouette='straight-leg')
        text = self.vp.render(self.validate(plan))
        hem, leg = self.vp.HEM_STATES['untucked'], self.vp.SILHOUETTES['straight-leg']
        self.assertEqual(text.count(hem), 1); self.assertEqual(text.count(leg), 1)
        self.assertIn('hem opening is about as wide as the knee', text)
        self.assertIn('Never tuck it in', text)
        self.assertGreater(text.index(hem), text.index('Preserve original garment facts:'))
        self.assertGreater(text.index(hem), text.index('Primary style'))
        self.assertLess(text.index(leg), text.index('Shared scene'))
        self.assertLess(text.index(hem), text.index(leg))

    def test_every_sentence_avoids_reserved_and_owned_words(self):
        for sentence in list(self.vp.HEM_STATES.values()) + list(self.vp.SILHOUETTES.values()):
            for name in ('OWNED', 'V2_BODY', 'RESERVED', 'V2_RESERVED'):
                self.assertIsNone(getattr(self.vp, name).search(sentence), (name, sentence))

    def test_adding_then_removing_keys_leaves_render_bytes_unchanged(self):
        plan = self.prepared()
        before = self.vp.render(self.validate(plan))
        changed = copy.deepcopy(plan); changed['garment'].update(hem_state='tucked', silhouette='wide-leg')
        self.assertNotEqual(self.vp.render(self.validate(changed)), before)
        del changed['garment']['hem_state'], changed['garment']['silhouette']
        self.assertEqual(self.vp.render(self.validate(changed)), before)

    def test_prepare_passes_keys_through_to_compiled_prompt(self):
        plan = self.prepared(hem_state='half-tucked', silhouette='flared-leg')
        self.assertEqual((plan['garment']['hem_state'], plan['garment']['silhouette']), ('half-tucked', 'flared-leg'))
        prompt = self.vp.compile_prompt(plan, 1)
        self.assertIn(self.vp.HEM_STATES['half-tucked'], prompt)
        self.assertIn(self.vp.SILHOUETTES['flared-leg'], prompt)

    def test_all_lengths_and_sources_prepare_validate_and_render(self):
        positions = {
            'above-knee': 'above the knee', 'knee': 'at the knee',
            'below-knee': 'below the knee', 'mid-calf': 'at mid-calf',
            'ankle': 'at the ankle', 'floor': 'at floor level',
        }
        for length, position in positions.items():
            for source in ('photo', 'user', 'estimated'):
                with self.subTest(length=length, source=source):
                    plan = self.prepared(length=length, length_source=source)
                    self.assertEqual(plan['garment']['length'], length)
                    self.assertEqual(plan['garment']['length_source'], source)
                    self.assertIn('Garment length on the body: hem falls ' + position + '.',
                                  self.vp.compile_prompt(self.validate(plan)))

    def test_invalid_length_reports_field_choices_and_value(self):
        for value in ('mini', '', None, True, 1, ['knee'], {'value': 'knee'}):
            with self.subTest(value=value):
                plan = self.prepared()
                plan['garment'].update(length=value, length_source='photo')
                with self.assertRaises(ValueError) as caught:
                    self.validate(plan)
                self.assertIn('visual_plan.garment.length must be one of above-knee, knee, below-knee, mid-calf, ankle, floor',
                              str(caught.exception))
                self.assertIn('got ', str(caught.exception))

    def test_length_requires_source_during_prepare_and_validation(self):
        with self.assertRaisesRegex(ValueError, r'garment\.length_source is required when length is present'):
            self.prepared(length='knee')
        plan = self.prepared()
        plan['garment']['length'] = 'knee'
        with self.assertRaisesRegex(ValueError, r'garment\.length_source is required when length is present'):
            self.validate(plan)

    def test_invalid_length_source_is_rejected(self):
        for value in ('guess', '', None, True, 1, ['photo'], {'value': 'user'}):
            with self.subTest(value=value):
                plan = self.prepared()
                plan['garment'].update(length='knee', length_source=value)
                with self.assertRaisesRegex(ValueError, r'garment\.length_source must be one of photo, user, estimated'):
                    self.validate(plan)

    def test_shared_length_renders_once_in_preview_and_delivery_requests(self):
        from tests.test_prompt_dedupe import fixture, request
        for purpose in ('preview-grid', 'delivery'):
            with self.subTest(purpose=purpose):
                data = fixture(purpose=purpose)
                data['visual_plan']['garment'].update(length='mid-calf', length_source='user')
                prompt = request(data)
                self.assertEqual(prompt.count('Garment length on the body:'), 1)
                line = next(line for line in prompt.splitlines() if line.startswith('Garment length on the body:'))
                for phrase in ('hem falls at mid-calf.', 'same hem position in every cell',
                               'seated', 'kneeling', 'walking',
                               'sitting may lift the hem slightly but never lengthens or shortens the garment'):
                    self.assertIn(phrase, line)
                self.assertLess(prompt.index(line), prompt.index('Visual slot 1'))

    def test_detail_focus_keeps_shared_length_anchor(self):
        plan = self.prepared(length='ankle', length_source='estimated')
        plan['shots'][0]['garment_focus'] = dict(description='Visible red cuff.', keep=['red cuff seam'])
        self.validate(plan)
        for look in (None, 1):
            with self.subTest(look=look):
                prompt = self.vp.compile_prompt(plan, look)
                self.assertIn('Visible red cuff.', prompt)
                self.assertEqual(prompt.count('Garment length on the body: hem falls at the ankle.'), 1)

    def test_removing_length_restores_render_bytes(self):
        plan = self.prepared(hem_state='untucked', silhouette='straight-leg')
        before = {look: self.vp.render(plan, look).encode() for look in (None, 1)}
        changed = copy.deepcopy(plan)
        changed['garment'].update(length='knee', length_source='photo')
        self.validate(changed)
        for look in before:
            self.assertNotEqual(self.vp.render(changed, look).encode(), before[look])
        del changed['garment']['length'], changed['garment']['length_source']
        self.validate(changed)
        for look in before:
            self.assertEqual(self.vp.render(changed, look).encode(), before[look])

    def test_no_length_requests_keep_pre_change_bytes(self):
        from tests.test_prompt_dedupe import fixture, request
        # Frozen on 7a3c34a before adding length; existing tests cover the 78 legacy requests.
        expected = {
            'preview-grid': 'da87b665ac56b6aae290a1e7833877f378d5fee731443991fc809298f5e53da2',
            'delivery': '04f067a7d7729df4573856255795dae29ec39baf5c4daa48c59c587fd9435173',
        }
        for purpose, digest in expected.items():
            with self.subTest(purpose=purpose):
                self.assertEqual(hashlib.sha256(request(fixture(purpose=purpose)).encode()).hexdigest(), digest)


if __name__ == '__main__':
    unittest.main()
