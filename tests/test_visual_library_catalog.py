"""Catalog integrity and actual rendered-field regressions; zero image calls."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/threadtruth-studio'
LIBRARY = SKILL / 'references/visual-library'
NEW_ENTRIES = {
    'retro-americana', 'gothic-editorial', 'romantic-bohemian',
    'future-artificial-light', 'hanfu-form-specific', 'qipao-urban',
    'gongbu-dress', 'bridal-ethereal', 'lolita-layered',
    'garment-illustration', 'art-deco-set', 'surreal-space-ad',
}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


class VisualLibraryCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('catalog_library', SKILL / 'scripts/visual_library.py')
        cls.library = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.library)
        cls.index = cls.library.index()
        cls.cards = {entry['id']: cls.library.card(entry['id']) for entry in cls.index['entries']}
        cls.legacy = {key: card for key, card in cls.cards.items() if 'legacy' in card}

    def spec(self, entry, **kwargs):
        spec = dict(entry_id=entry,
                    garment=dict(description='Source garment with red beading and a visible front closure.',
                                 keep=['Keep the red color, bead count, front closure and actual ornament density.'],
                                 source_sha256s=['a' * 64]),
                    inventory=[dict(role='garment-source', sha256='a' * 64)], count=1, first_pose=3)
        spec.update(kwargs)
        return spec

    def test_index_preserves_old_24_and_registers_exact_new_12(self):
        packs = {p.name.removesuffix('.pack.yaml') for p in (SKILL / 'references/styles').glob('*.pack.yaml')}
        self.assertEqual(len(packs), 24)
        self.assertEqual(set(self.legacy), packs)
        self.assertEqual(set(self.cards) - packs, NEW_ENTRIES)
        self.assertEqual(len(self.cards), 36)
        self.assertEqual({p.stem for p in (LIBRARY / 'cards').glob('*.json')}, set(self.cards))
        for entry in self.index['entries']:
            with self.subTest(entry=entry['id']):
                card = self.cards[entry['id']]
                for key in ('name', 'version', 'entry_type', 'aliases', 'medium', 'purpose_support', 'status'):
                    self.assertEqual(entry[key], card[key])
                self.assertNotIn('..', Path(entry['card']).parts)
                self.assertFalse(Path(entry['card']).is_absolute())
                self.assertEqual((SKILL / entry['card']).resolve().parent, (LIBRARY / 'cards').resolve())
        self.assertTrue((SKILL / self.index['contract']).is_file())
        for relative in self.index['knowledge_sources']:
            self.assertTrue((SKILL / relative).is_file())

    def test_legacy_names_versions_hashes_and_six_real_scene_candidates(self):
        for slug, card in self.legacy.items():
            with self.subTest(entry=slug):
                path = SKILL / card['legacy']['pack_path']
                raw = path.read_bytes()
                text = raw.decode('utf-8')
                self.assertEqual(hashlib.sha256(raw).hexdigest(), card['legacy']['sha256'])
                for source_key, card_key in (('name', 'name'), ('slug', 'id')):
                    self.assertEqual(re.search(r'^' + source_key + r':\s*(.+)$', text, re.M)[1], card[card_key])
                self.assertEqual(re.search(r'^version:\s*(\S+)', text, re.M)[1], card['legacy']['version'])
                block = re.search(r'^scenes:\s*\n((?:[ \t]+.*\n)+)', text, re.M)[1]
                scenes = re.findall(r'^\s+-\s+(.+)$', block, re.M)
                self.assertEqual(len(scenes), 6)
                self.assertEqual(card['scene_options'], scenes)
                self.assertTrue(all(len(scene) > 2 for scene in scenes))

    def test_132_source_rows_and_75_china_records_are_knowledge_not_execution_ids(self):
        source = read(LIBRARY / 'source-catalog.json')
        self.assertRegex(source['provenance']['sha256'], r'^[a-f0-9]{64}$')
        expected = {f'R{i:02d}' for i in range(1, 25)} | {f'A{i:02d}' for i in range(1, 17)} | {f'K{i:03d}' for i in range(1, 93)}
        rows = source['records']
        self.assertEqual(len(rows), 132)
        self.assertEqual({row['id'] for row in rows}, expected)
        for row in rows:
            self.assertTrue(row['original_name'].strip())
            self.assertTrue(row['original_columns'])
            self.assertEqual(row['source_status'], 'historical-description-not-runtime-policy')
            self.assertLessEqual(set(row['execution_ids']), set(self.cards))
        market = read(LIBRARY / 'china-market.json')
        culture = read(LIBRARY / 'china-culture.json')
        groups = [(market['records'], 'M', 46), (market['modifiers'], 'T', 9), (culture['records'], 'C', 20)]
        china_ids = set()
        for group, prefix, count in groups:
            self.assertEqual(len(group), count)
            self.assertEqual({row['id'] for row in group}, {f'{prefix}{i:02d}' for i in range(1, count + 1)})
            for row in group:
                china_ids.add(row['id'])
                self.assertEqual(row['status'], 'knowledge-reference')
                self.assertTrue(row['distinction'].strip())
                self.assertTrue(row['prompt_fragment'].strip())
                self.assertLessEqual({ref['id'] for ref in row['execution_refs']}, set(self.cards))
        self.assertEqual(len(china_ids), 75)
        for card in self.cards.values():
            self.assertLessEqual(set(card['source_ids']), expected | china_ids)
        for identifier in ('R01', 'A01', 'K001', 'M01', 'C19', 'T01'):
            with self.subTest(identifier=identifier), self.assertRaises(ValueError):
                self.library.card(identifier)

    def test_cultural_records_retain_specificity_and_label_working_names(self):
        rows = {row['id']: row for row in read(LIBRARY / 'china-culture.json')['records']}
        for identifier in ('C01', 'C02', 'C03'):
            self.assertEqual(rows[identifier]['naming_status'], 'working-name')
            self.assertIn('工作命名', rows[identifier]['name'])
        for identifier, place in [('C16', '台江'), ('C17', '黔东南'), ('C18', '海南'), ('C19', '林芝工布'), ('C20', '乌珠穆沁')]:
            self.assertIn(place, rows[identifier]['name'])
            self.assertTrue(rows[identifier]['primary_sources'])
        self.assertEqual([ref['id'] for ref in rows['C19']['execution_refs']], ['gongbu-dress'])
        self.assertFalse(rows['C16']['execution_refs'])
        self.assertFalse(rows['C17']['execution_refs'])
        self.assertFalse(rows['C18']['execution_refs'])
        self.assertFalse(rows['C20']['execution_refs'])

    def test_every_declared_objective_compiles_actual_card_fields(self):
        for identifier, card in self.cards.items():
            for objective in card['purpose_support']:
                with self.subTest(entry=identifier, objective=objective):
                    plan = self.library.prepare(self.spec(identifier, objective=objective))
                    rendered = self.library._visual().compile_prompt(plan, 1)
                    self.assertEqual(plan['garment'], self.spec(identifier)['garment'])
                    self.assertEqual(plan['shots'][0]['pose'], 3)
                    self.assertEqual(plan['output_medium'], card['medium'])
                    for value in card['photography'].values():
                        self.assertIn(value, rendered)
                    self.assertIn(card['art']['direction'], rendered)
                    for limit in card['garment_preservation']:
                        self.assertIn(limit, rendered)
        for identifier in NEW_ENTRIES:
            plan = self.library.prepare(self.spec(identifier, count=6, first_pose=1))
            self.assertEqual([shot['pose'] for shot in plan['shots']], list(range(1, 7)))
            self.assertIn('Visual slot 6', self.library._visual().compile_prompt(plan, 6))

    def test_photography_override_does_not_render_stale_legacy_defaults(self):
        replacement = dict(scene='Outdoor red brick square.', lighting='Defined overhead key and a soft fill.',
                           composition='Balanced geometric rhythm with separated planes.', palette='Muted green environment.')
        for identifier, card in self.legacy.items():
            with self.subTest(entry=identifier):
                plan = self.library.prepare(self.spec(identifier, overrides=dict(photography=replacement)))
                rendered = self.library._visual().compile_prompt(plan, 1)
                for value in replacement.values():
                    self.assertIn(value, rendered)
                for value in card['photography'].values():
                    self.assertNotIn(value, rendered)
                self.assertEqual(plan['style']['primary']['snapshot']['photography'], card['photography'])
        japanese = self.library._visual().compile_prompt(self.library.prepare(self.spec('japanese-lifestyle', overrides=dict(photography=replacement))), 1)
        for stale in ('window light', 'interior backdrop', '原木公寓', '暖白自然漫射光', '榻榻米'):
            self.assertNotIn(stale, japanese)
        korean = self.library._visual().compile_prompt(self.library.prepare(self.spec('korean-cold-editorial')), 1)
        for stale in ('detached expression', 'no fake commercial smile', 'no sweet idol smile', 'no aegyo', '安静表情'):
            self.assertNotIn(stale, korean)
        self.assertIn('detached expression', self.cards['korean-cold-editorial']['persona_guidance'])

    def test_distinctive_fallbacks_reach_rendered_prompt(self):
        checks = {
            'quiet-luxury': ['材料优先', 'material-first', '不替换面料'],
            'neo-chinese': ['商品无中式结构', '建筑与构图', '不增添领型、盘扣或纹样'],
            'guochao-street': ['当代中国文化线索放在低干扰环境', '避免伪造文字或给衣服添图案'],
        }
        for identifier, phrases in checks.items():
            rendered = self.library._visual().compile_prompt(self.library.prepare(self.spec(identifier)), 1)
            for phrase in phrases:
                with self.subTest(entry=identifier, phrase=phrase):
                    self.assertIn(phrase, rendered)

    def test_no_evidence_is_invented_by_preparation(self):
        for identifier, card in self.cards.items():
            with self.subTest(entry=identifier):
                self.assertEqual(card['status'], 'draft')
                self.assertEqual(card['evidence']['visual_status'], 'unverified')
                self.assertEqual(card['evidence']['records'], [])
                before = json.dumps(card, ensure_ascii=False, sort_keys=True)
                self.library.prepare(self.spec(identifier))
                after = json.dumps(self.library.card(identifier), ensure_ascii=False, sort_keys=True)
                self.assertEqual(before, after)

    def human_model(self, **changes):
        model = dict(source_type='new', scope='full', subject='adult female model',
                     locked=['mature adult'], adjustable=[], consent_note='')
        model.update(changes)
        return model

    def test_prepare_with_model_freezes_filtered_persona_and_model_hash(self):
        visual = self.library._visual()
        models = self.library._models()
        for identifier in sorted(slug for slug, card in self.cards.items() if card.get('persona')):
            model = self.human_model()
            plan = self.library.prepare(self.spec(identifier, model=model))
            with self.subTest(entry=identifier):
                self.assertEqual(plan['persona'], self.cards[identifier]['persona'])
                self.assertEqual(plan['persona_model_sha256'], visual.object_hash(models.validate_model(model)))
                rows = visual.render(plan, 1).split('\n')
                last_limit = max(i for i, row in enumerate(rows) if row.startswith('Art limit: '))
                self.assertEqual(rows[last_limit + 1],
                                 'Style persona (yields to the declared model conditions): ' + plan['persona'])
        locked = self.human_model(source_type='real', locked=['same face', 'same expression'],
                                  consent_note='Express likeness permission')
        plan = self.library.prepare(self.spec('american-street', model=locked))
        self.assertEqual(plan['persona'], models.resolve_persona(locked, self.cards['american-street']['persona']))
        legacy_new = {slug for slug in self.cards if slug in NEW_ENTRIES}
        self.assertFalse(any(self.cards[slug].get('persona') for slug in legacy_new))
        self.assertEqual(len([c for c in self.cards.values() if c.get('persona')]), 24)

    def test_prepare_without_model_or_nonhuman_omits_persona(self):
        plan = self.library.prepare(self.spec('korean-cold-editorial'))
        self.assertNotIn('persona', plan)
        self.assertNotIn('persona_model_sha256', plan)
        for form in ('faceless', 'flat-lay', 'hanger', 'mannequin'):
            with self.subTest(form=form):
                plan = self.library.prepare(self.spec('korean-cold-editorial', model=self.human_model(), output_form=form))
                self.assertNotIn('persona', plan)
                self.assertNotIn('persona_model_sha256', plan)
        child = self.human_model(subject='child model')
        self.assertNotIn('persona', self.library.prepare(self.spec('korean-cold-editorial', model=child)))
        with self.assertRaises(ValueError):
            self.library.prepare(self.spec('korean-cold-editorial', model=dict(self.human_model(), subject='unknown')))
        self.assertNotIn('persona', self.library.prepare(self.spec('hanfu-form-specific', model=self.human_model())))


if __name__ == '__main__':
    unittest.main()
