"""Preview export deduplication is gated by the frozen shot-plan marker."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from tests.test_pose_plan_v2 import sample_plan
from tests.test_style_pose_pool import module

ROOT = Path(__file__).resolve().parents[1]
shot, visual, task = (module(name) for name in ('shot_plan', 'visual_plan', 'web-task'))


def fixture(framing=3, purpose='preview-grid'):
    source = json.loads((ROOT / 'tests/fixtures/style-pool-legacy.json').read_text())
    spec, plan = source['spec'], source['visual_plan']
    shots = sample_plan(back=False)
    shots['coverage'] = copy.deepcopy(spec['shot_plan']['coverage'])
    if framing is not None:
        shots['framing_guidance'] = framing
    for cell in shots['looks']:
        cell['reference_sha256s'] = spec['garment']['source_sha256s'][:]
    template = plan['shots'][0]
    plan['rendering_version'] = 2
    plan['shots'] = [dict(template, slot=cell['slot'], shot_id=cell['shot_id'],
                          framing=cell['framing'], lighting='Uniform cell light.',
                          composition='Uniform cell composition.') for cell in shots['looks']]
    return dict(schema_version=2, model=spec['model'], identity=True,
                context=dict(source['context'], purpose=purpose), size=[20, 30], route='codex_native',
                shot_plan=shots, visual_plan=plan, prompt_contract_version=2,
                identity_instruction_version=1, references=spec['inventory'])


def request(data):
    look = None if data['context']['purpose'] == 'preview-grid' else 1
    row = dict(number=1, prompt=visual.compile_prompt(data['visual_plan'], look))
    return task.handoff_prompt(data, row, data['references'])


class PromptDedupeTests(unittest.TestCase):
    def test_marked_preview_emits_shared_lines_once_and_no_selection_reason(self):
        data = fixture()
        original = copy.deepcopy(data)
        prompt = request(data)
        for text in ('Lighting (all cells): Uniform cell light.',
                     'Composition (all cells): Uniform cell composition.',
                     "All preview cells use reference images: Image 1; keep each declared role and do not borrow another cell's product or aesthetic input."):
            self.assertEqual(prompt.count(text), 1)
        for text in ('\nLighting:', '\nComposition:', '\nPreview cell ', '\nShot identity:',
                     '\nCell reference images:', 'Selection reason:'):
            self.assertNotIn(text, prompt)
        for cell in data['shot_plan']['looks']:
            self.assertIn(f"Shot {cell['slot']}: {cell['shot_id']}.", prompt)
            self.assertIn(shot.body_text(cell), prompt)
            self.assertIn('Must show: ' + ', '.join(cell['must_show']) + '.', prompt)
            self.assertIn(shot.framing_line(data['shot_plan'], cell['framing']), prompt)
        self.assertEqual(data, original)

    def test_nonidentical_lighting_and_composition_are_independent(self):
        for changed, shared in (('lighting', 'composition'), ('composition', 'lighting')):
            with self.subTest(changed=changed):
                data = fixture()
                # Raw texts differ even though compact rendering strips whitespace.
                data['visual_plan']['shots'][-1][changed] += ' '
                prompt = request(data)
                self.assertEqual(prompt.count('\n' + changed.capitalize() + ':'), 9)
                self.assertNotIn(changed.capitalize() + ' (all cells):', prompt)
                self.assertEqual(prompt.count(shared.capitalize() + ' (all cells):'), 1)

    def test_distinct_reference_selection_retains_each_cell_mapping(self):
        data = fixture()
        art = 'd' * 64
        data['references'].append(dict(role='aesthetic-reference', sha256=art))
        data['shot_plan']['looks'][4]['aesthetic_reference_sha256s'] = [art]
        prompt = request(data)
        self.assertNotIn('All preview cells use reference images:', prompt)
        self.assertEqual(prompt.count('\nCell reference images:'), 9)
        self.assertIn('Preview cell 5:\nShot identity: garment-shot-5.\nCell reference images: Image 1, Image 2.', prompt)
        self.assertIn('Preview cell 4:\nShot identity: garment-shot-4.\nCell reference images: Image 1.', prompt)

    def test_real_face_reference_branch_keeps_per_cell_text(self):
        data = fixture()
        data['real_face_plan'] = dict(looks=[dict(body_action=shot.body_text(cell),
            head_view='front', gaze='At the lens.', face_visible=True,
            reference_sha256s=cell['reference_sha256s'][:], selection_note='Reviewed original coverage.')
            for cell in data['shot_plan']['looks']])
        prompt = request(data)
        self.assertNotIn('All preview cells use reference images:', prompt)
        self.assertEqual(prompt.count('\nPreview cell '), 9)
        self.assertEqual(prompt.count('\nCell reference images: Image 1. Use only these references for this cell, retaining their declared garment/identity roles; do not mix product facts from other cells. Selection note: Reviewed original coverage.'), 9)

    def test_delivery_preserves_per_shot_photography_and_omits_reason(self):
        prompt = request(fixture(purpose='delivery'))
        self.assertIn('\nLighting: Uniform cell light.', prompt)
        self.assertIn('\nComposition: Uniform cell composition.', prompt)
        self.assertNotIn('(all cells)', prompt)
        self.assertNotIn('All preview cells use reference images:', prompt)
        self.assertNotIn('Selection reason:', prompt)

    def test_legacy_requests_match_pre_change_bytes_even_with_compact_visual_plan(self):
        # SHA-256 of e190988 exports; includes compact visual plans without the new-task marker.
        expected = {
            "None-preview-grid": "2ead5429454b782f027b50bf06aa8996feb9c7bdb4b271299b7e580f6fc40639",
            "None-delivery": "4ab839fddb5da9d888bae6afe3decf3a10da82f4e7fa42b57d59a937a4fde604",
            "1-preview-grid": "51ab103838b2f56bfe114611e338443cb440c4d79195087614a636e3cb82087a",
            "1-delivery": "334fde15ebe2d7e837aef67ff2311ea26cbecc95938c2c27a8b6a3c61ab8a6f6",
            "2-preview-grid": "f8a9ad0f0d6b04a8b9625d0ca2016de2e6e6b48ddc9057a28379745857c9e46e",
            "2-delivery": "3ca2d6b5f62f21443c8da568960feb03d26af8199c37fffb4149f974bfc349c5"
        }
        for framing in (None, 1, 2):
            for purpose in ('preview-grid', 'delivery'):
                with self.subTest(framing=framing, purpose=purpose):
                    prompt = request(fixture(framing=framing, purpose=purpose))
                    key = str(framing) + '-' + purpose
                    self.assertEqual(hashlib.sha256(prompt.encode()).hexdigest(), expected[key])

    def test_reason_remains_required_plan_metadata(self):
        data = fixture()
        plan = data['shot_plan']
        original = copy.deepcopy(plan)
        validated = shot.validate(plan, data['references'], context=data['context'], count=9,
                                  model_source='new')
        self.assertEqual(validated, original)
        plan['looks'][0]['reason'] = ''
        with self.assertRaisesRegex(ValueError, 'reason'):
            shot.validate(plan, data['references'], context=data['context'], count=9, model_source='new')

    def test_export_still_rejects_visual_text_that_disagrees_with_frozen_plan(self):
        data = fixture()
        row = dict(number=1, prompt=visual.compile_prompt(data['visual_plan']).replace(
            'Uniform cell light.', 'Unreviewed light.', 1))
        with self.assertRaisesRegex(ValueError, 'Frozen visual plan block conflicts'):
            task.handoff_prompt(data, row, data['references'])

    def test_existing_shared_photography_is_not_duplicated(self):
        data = fixture()
        for key in ('lighting', 'composition'):
            data['visual_plan']['photography'][key] = data['visual_plan']['shots'][0][key]
        prompt = request(data)
        self.assertEqual(prompt.count('Uniform cell light.'), 1)
        self.assertEqual(prompt.count('Uniform cell composition.'), 1)


if __name__ == '__main__':
    unittest.main()
