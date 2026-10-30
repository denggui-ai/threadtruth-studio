"""Regression evidence for retained photography and portable visual preparation."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VisualFallbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preview = load('expression_preview', 'tools/style_preview.py')

    def test_source_conditioned_photography_survives_wardrobe_filter(self):
        cases = {'quiet-luxury': ('light and framing',),
                 'neo-chinese': ('architecture', 'composition'),
                 'guochao-street': ('place contemporary Chinese cues', 'environment')}
        for entry, expected in cases.items():
            with self.subTest(entry=entry):
                text = (ROOT / 'skills/threadtruth-studio/references/styles' / (entry + '.pack.yaml')).read_text()
                mood = self.preview._visual(text)['mood']
                for phrase in expected:
                    self.assertIn(phrase, mood)

    def test_material_word_boundary_does_not_delete_palace_or_replace(self):
        text = 'visual_language: palace architecture, light in place, lace only when present\nmodel_persona: calm\nlighting_palette: daylight\n'
        mood = self.preview._visual(text)['mood']
        self.assertIn('palace architecture', mood)
        self.assertIn('light in place', mood)
        self.assertNotIn('lace only', mood)


class VisualLibraryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library = load('expression_library', 'skills/threadtruth-studio/scripts/visual_library.py')

    def spec(self, entry_id):
        return dict(entry_id=entry_id,
                    garment=dict(description='A white sleeveless padded vest from the original image.',
                                 keep=['Preserve the visible hood, front zipper and white shell.'],
                                 source_sha256s=['a' * 64]),
                    inventory=[dict(role='garment-source', sha256='a' * 64)], count=1, first_pose=3)

    def test_current_execution_entries_prepare_without_loading_knowledge_as_styles(self):
        entries = self.library.index()['entries']
        self.assertEqual(len(entries), 36)
        for entry in entries:
            with self.subTest(entry=entry['id']):
                card = self.library.card(entry['id'])
                spec = self.spec(entry['id'])
                spec['objective'] = card['purpose_support'][0]
                plan = self.library.prepare(spec)
                self.assertEqual(plan['shots'][0]['pose'], 3)
                self.assertEqual(plan['style']['primary']['snapshot'], card)
                self.assertEqual(plan['output_medium'], card['medium'])
                self.assertEqual(plan['garment'], spec['garment'])

    def test_unknown_entry_and_source_hash_cannot_be_prepared(self):
        with self.assertRaises(ValueError):
            self.library.card('../knowledge')
        spec = self.spec('french-effortless')
        spec['garment']['source_sha256s'] = ['b' * 64]
        with self.assertRaises(ValueError):
            self.library.prepare(spec)

    def test_frozen_plan_does_not_follow_later_card_changes(self):
        plan = self.library.prepare(self.spec('french-effortless'))
        before = json.dumps(plan, sort_keys=True)
        fresh_card = self.library.card('french-effortless')
        fresh_card['photography']['scene'] = 'a later library revision'
        self.assertEqual(json.dumps(plan, sort_keys=True), before)

    def test_fusion_requires_explicit_scope_and_no_medium_relabel(self):
        spec = self.spec('french-effortless')
        spec['supporting'] = ['old-money']
        with self.assertRaises(ValueError):
            self.library.prepare(spec)
        spec['fusion_note'] = 'French light and easy atmosphere are primary; old-money contributes a restrained stone setting only.'
        self.assertEqual(len(self.library.prepare(spec)['style']['supporting']), 1)
        spec['output_medium'] = 'illustration'
        with self.assertRaises(ValueError):
            self.library.prepare(spec)

    def test_all_output_forms_are_rendered_and_identity_scope_is_not_inferred(self):
        for form in ('human', 'faceless', 'flat-lay', 'hanger', 'mannequin'):
            with self.subTest(form=form):
                spec = self.spec('ecommerce-studio')
                spec['output_form'] = form
                plan = self.library.prepare(spec)
                text = self.library._visual().compile_prompt(plan, 1)
                self.assertEqual(plan['output_form'], form)
                self.assertIn(form, text)

    def test_selected_collection_can_freeze_two_entries_without_changing_old_24_rules(self):
        preview = load('expression_collection', 'tools/style_preview.py')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / 'skills/threadtruth-studio'
            for relative in ('scripts/visual_library.py', 'scripts/visual_plan.py'):
                destination = runtime / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / 'skills/threadtruth-studio' / relative, destination)
            library_source = ROOT / 'skills/threadtruth-studio/references/visual-library'
            shutil.copytree(library_source, runtime / 'references/visual-library')
            specs = [dict(self.spec(entry), count=6, first_pose=1) for entry in ('french-effortless', 'gothic-editorial')]
            path = preview.prepare_visual_collection(root, 'two-directions', specs)
            record = json.loads(path.read_text())
            self.assertEqual(record['selected_entry_ids'], ['french-effortless', 'gothic-editorial'])
            self.assertEqual(len(record['entries']), 2)
            self.assertEqual(record['image_calls'], 0)
            frozen = path.read_bytes()
            with self.assertRaises(ValueError):
                preview.prepare_visual_collection(root, 'two-directions', specs)
            self.assertEqual(path.read_bytes(), frozen)
            self.assertEqual(preview.CURRENT_SCHEMA, '5.0')

    def test_explicit_intent_and_negation_do_not_become_implicit_fusion(self):
        cases = [('法式、美拉德、居家', 'route'),
                 ('比较法式与日系', 'compare'),
                 ('法式为主、老钱为辅', 'fusion'),
                 ('法式和老钱', 'hold'),
                 ('不要法式和老钱', 'none'),
                 ('不要太暗的法式', 'route'),
                 ('美式复古厨房作为背景', 'none'),
                 ('美式', 'hold')]
        for query, decision in cases:
            with self.subTest(query=query):
                self.assertEqual(self.library.route(query)['decision'], decision)


if __name__ == '__main__':
    unittest.main()
