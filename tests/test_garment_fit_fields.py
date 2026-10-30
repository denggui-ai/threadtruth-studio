"""WP-16 C2: optional garment hem_state / silhouette facts render as fixed geometric sentences."""
import copy, importlib.util, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/threadtruth-studio/scripts'


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


if __name__ == '__main__':
    unittest.main()
