import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/threadtruth-studio/scripts/model_reference.py'


class ModelReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.face = self.root / 'face.png'
        Image.new('RGB', (30, 40), 'blue').save(self.face)
        spec = importlib.util.spec_from_file_location('model_reference_tests', SCRIPT)
        if SCRIPT.exists():
            self.m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.m)

    def model(self, **changes):
        result = dict(source_type='ai', scope='full', subject='adult female model',
                      locked=['apparent age around 40', 'natural fuller proportions'],
                      adjustable=['gentle makeup'], consent_note='')
        result.update(changes)
        return result

    def test_portable_roundtrip_keeps_original_reference_and_no_absolute_paths(self):
        self.assertTrue(SCRIPT.exists(), 'portable reference helper is missing')
        package = self.root / 'brand-a'
        self.m.export_package(package, self.model(), [self.face], 'Brand A', 'User accepts this model')
        card = self.m.load_package(package)
        self.assertEqual(card['model']['locked'], self.model()['locked'])
        self.assertEqual(len(card['references']), 1)
        self.assertNotIn(str(self.root), (package / 'model.json').read_text())
        self.assertEqual((package / card['references'][0]['file']).read_bytes(), self.face.read_bytes())

    def test_export_requires_actual_confirmation_and_real_likeness_consent(self):
        self.assertTrue(SCRIPT.exists(), 'portable reference helper is missing')
        for model, confirmation in [(self.model(), ''), (self.model(source_type='real'), 'Accepted')]:
            with self.subTest(model=model, confirmation=confirmation), self.assertRaises(ValueError):
                self.m.export_package(self.root / 'bad', model, [self.face], 'A', confirmation)
        self.assertFalse((self.root / 'bad').exists())

    def test_tampered_missing_and_escaping_references_are_rejected(self):
        self.assertTrue(SCRIPT.exists(), 'portable reference helper is missing')
        package = self.root / 'a'
        self.m.export_package(package, self.model(), [self.face], 'A', 'Accepted')
        path = package / 'model.json'
        card = json.loads(path.read_text())
        image = package / card['references'][0]['file']
        image.write_bytes(b'changed')
        with self.assertRaises(ValueError): self.m.load_package(package)
        card['references'][0]['file'] = '../face.png'
        path.write_text(json.dumps(card))
        with self.assertRaises(ValueError): self.m.load_package(package)

    def test_face_only_prompt_does_not_claim_original_body_and_style_yields_to_user(self):
        self.assertTrue(SCRIPT.exists(), 'portable reference helper is missing')
        model = self.model(scope='face', locked=['same face'], adjustable=['friendly smile'])
        lines = self.m.prompt_lines(model)
        self.assertIn('face-only', '\n'.join(lines))
        persona, negatives = self.m.resolve_style(model, 'cold detached expression',
                                                  ['no sweet smile', 'no busy background'])
        self.assertNotIn('cold detached', persona)
        self.assertNotIn('no sweet smile', negatives)
        self.assertIn('no busy background', negatives)

    def test_factor_delivery_preserves_provenance_unknowns_and_runtime_conditions(self):
        factors = [dict(name='body', value='natural fuller proportions', status='fixed', source='recommendation', confirmed=True),
                   dict(name='makeup', value='gentle makeup', status='adjustable', source='user', confirmed=True),
                   dict(name='actual size', value='unknown', status='unknown', source='reference', confirmed=False)]
        model = self.model(factors=factors)
        package = self.root/'factors'
        card = self.m.export_package(package, model, [self.face], 'A', 'Accepted')
        self.assertEqual(card['model']['factors'], factors)
        self.assertIn('recommendation', (package/'README.md').read_text())
        self.assertIn('actual size', (package/'README.md').read_text())
        self.assertNotIn('actual size', '\n'.join(self.m.prompt_lines(model)))
        factors[0]['confirmed'] = False
        with self.assertRaises(ValueError): self.m.validate_model(self.model(factors=factors))

    def test_unknown_factor_cannot_be_prompt_condition_or_duplicate_another_state(self):
        for factors in [
            [dict(name='body',value='natural fuller proportions',status='unknown',source='reference',confirmed=False)],
            [dict(name='body',value='natural fuller proportions',status='fixed',source='user',confirmed=True), dict(name='body',value='unknown',status='unknown',source='reference',confirmed=False)]
        ]:
            with self.subTest(factors=factors),self.assertRaises(ValueError):self.m.validate_model(self.model(factors=factors))

    def test_proposed_factors_become_confirmed_only_on_export(self):
        model=self.model(factors=[dict(name='body', value='natural fuller proportions', status='target', source='recommendation', confirmed=False)])
        self.assertEqual(self.m.validate_model(model)['factors'][0]['status'], 'target')
        card=self.m.export_package(self.root/'proposed',model,[self.face],'A','First-image human approval')
        self.assertEqual(card['model']['factors'][0]['status'], 'fixed')
        self.assertTrue(card['model']['factors'][0]['confirmed'])
        self.assertFalse(model['factors'][0]['confirmed'])

    def test_non_person_negative_substrings_and_safety_are_preserved(self):
        _, negatives = self.m.resolve_style(self.model(), 'cold face', ['no vintage background', 'no sexualized body', 'no sweet smile'])
        self.assertIn('no vintage background', negatives)
        self.assertIn('no sexualized body', negatives)
        self.assertNotIn('no sweet smile', negatives)
        mood=self.m.resolve_mood(self.model(), 'quiet photographic mood; no sexualized body; sweet smile')
        self.assertIn('no sexualized body',mood)
        self.assertNotIn('sweet smile',mood)

    def test_card_rejects_unknown_product_fields_and_requires_identity_to_export(self):
        self.assertTrue(SCRIPT.exists(), 'portable reference helper is missing')
        for model, refs in [(self.model(garment='old shirt'), [self.face]), (self.model(), [])]:
            with self.subTest(model=model), self.assertRaises(ValueError):
                self.m.export_package(self.root / 'bad', model, refs, 'A', 'Accepted')


if __name__ == '__main__':
    unittest.main()
