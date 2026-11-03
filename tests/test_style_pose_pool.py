"""Shared card vocabulary reaches frozen requests without changing old tasks."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
from tests.test_pose_plan_v2 import sample_plan


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/threadtruth-studio'


def module(name):
    spec = importlib.util.spec_from_file_location('pool_' + name, SKILL / 'scripts' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


library, poses, task = module('visual_library'), module('pose_library'), module('web-task')


class StylePosePoolTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / 'synthetic-source.png'
        Image.new('RGB', (20, 30), 'blue').save(self.source)
        self.sha = task.digest(self.source)
        self.model = dict(source_type='new', scope='full', subject='adult female model',
                          locked=[], adjustable=[], consent_note='', styling_lock='identity')

    def spec(self, entry, row=None):
        card = library.card(entry)
        row = row or card['pose_vocabulary'][0]
        plan = sample_plan(1, back=False)
        plan.update(variety_checks=2, framing_guidance=2)
        plan['coverage'][0].update(sha256=self.sha, views=list(dict.fromkeys(['front'] + row['views'])))
        if 'back' in row['views']:
            plan['route'] = 'A'
        plan['looks'][0].update(pose_id=row['id'], body_action=row['body'], hands=row['hands'],
            support=row['support'], garment_views=row['views'], reference_sha256s=[self.sha],
            head='Head remains upright.', gaze='Eyes follow the facing direction.',
            display_goal='Show the source-supported garment panels.', must_show=['visible panels'])
        model = copy.deepcopy(self.model)
        if entry in ('korean-menswear', 'cityboy'):
            model['subject'] = 'adult male model'
        spec = dict(entry_id=entry, count=1, first_pose=1, model=model, output_form='human',
            inventory=[dict(role='garment-source', sha256=self.sha)], shot_plan=plan,
            garment=dict(description='Synthetic blue garment.', keep=['Keep the original blue colour.'],
                         source_sha256s=[self.sha]))
        if entry == 'qipao-urban':
            spec.update(culture_profile=dict(id='qipao-contemporary-daily', version=1, form='contemporary daily qipao'),
                        asset_trace=[dict(asset='C10', decision='translated', affects='Use the source-backed modern cut.',
                                          check='No invented historical costume details.')])
        return spec

    def export(self, spec, visual, route, name=None, context=None):
        job = self.root / (name or spec['entry_id'] + '-' + route)
        context = context or dict(outfit='synthetic-pool', style=spec['entry_id'], mode='C',
            output_form='human', size=[20, 30], first_pose=1, purpose='delivery')
        task.create(job, [self.source], None, [20, 30], model=spec['model'], context=context,
                    route=route, shot_plan=spec['shot_plan'], visual_plan=visual, count=1, workflow_version=0)
        task.export(job)
        data = task.read(job)
        folder = task.handoff_directory(job, data, data['looks'][0])
        raw = (folder / 'prompt.txt').read_bytes()
        manifest = json.loads((folder / 'manifest.json').read_text())
        self.assertEqual(manifest['visual_plan'], visual)
        self.assertEqual(manifest['reference_hashes'], [self.sha])
        self.assertEqual(data['attempts'], 0)
        self.assertIsNone(data['authorization'])
        if route == 'codex_native':
            request = json.loads((folder / 'request.json').read_text())
            self.assertEqual(request['prompt'].encode(), raw)
            self.assertEqual([task.digest(Path(p)) for p in request['referenced_image_paths']], [self.sha])
        else:
            packet = task.export_web_execution(job, 1)
            envelope = task.web_execution_helper()
            self.assertEqual(Path(packet['submission_file']).read_bytes(),
                             envelope.prefix(envelope.version(data)) + raw + envelope.SUFFIX)
        return raw

    def test_all_cards_resolve_complete_pools_with_stable_ids(self):
        source = json.loads(poses.VOCABULARY.read_text())
        by_id = {row['id']: row for row in source['entries']}
        used = []
        migrated = []
        for item in library.index()['entries']:
            raw = json.loads((SKILL / item['card']).read_text())
            card = library.card(item['id'])
            if 'pose_pool' not in raw:
                self.assertEqual(card, raw)
                continue
            migrated.append(item['id'])
            self.assertNotIn('pose_vocabulary', raw)
            self.assertEqual([r['id'] for r in card['pose_vocabulary']], raw['pose_pool'])
            library.component(card)
            for resolved in card['pose_vocabulary']:
                original = by_id[resolved['id']]
                if 'pose_id' not in original:
                    self.assertEqual(resolved, original)
                else:
                    self.assertIn(original['context'], resolved['body'])
                    self.assertEqual(resolved['check'], original['check'])
                    if original['avoid_when'] != 'none':
                        self.assertIn(original['avoid_when'], resolved['avoid_when'])
                used.append(resolved['id'])
        self.assertEqual(len(migrated), 25)
        self.assertEqual(len(used), 200)
        self.assertEqual(set(used), set(by_id))
        self.assertEqual(len(used), len(set(used)))

    def test_three_new_style_pools_freeze_each_action_and_keep_detail_commitments(self):
        for entry in ('resort-vacation', 'qipao-urban', 'romantic-bohemian'):
            card = library.card(entry)
            self.assertEqual(len(card['pose_vocabulary']), 8)
            self.assertTrue({'walk', 'sit', 'lean', 'turn', 'close'} <= {r['family'] for r in card['pose_vocabulary']})
            for row in card['pose_vocabulary']:
                with self.subTest(entry=entry, action=row['id']):
                    spec = self.spec(entry, row)
                    spec['shot_plan']['framing_guidance'] = 3
                    if row['family'] == 'close':
                        spec['shot_plan']['looks'][0]['framing'] = 'detail'
                    frozen = library.prepare(spec)
                    self.assertEqual(frozen['style']['primary']['snapshot']['pose_pool'], card['pose_pool'])
                    rendered = library._visual().render(frozen, 1)
                    for item in frozen.get('commitments', []):
                        self.assertIn(item['show'], rendered)

    def test_all_migrated_cards_reach_both_actual_exports(self):
        shared = {e['id'] for e in json.loads(poses.VOCABULARY.read_text())['entries'] if 'pose_id' in e}
        for item in library.index()['entries']:
            card = library.card(item['id'])
            if 'pose_pool' not in card:
                continue
            with self.subTest(entry=item['id']):
                row = next((r for r in card['pose_vocabulary'] if r['id'] in shared), card['pose_vocabulary'][0])
                spec = self.spec(item['id'], row)
                visual = library.prepare(spec)
                native = self.export(spec, visual, 'codex_native')
                web = self.export(spec, visual, 'chatgpt_web')
                self.assertEqual(native, web)
                text = native.decode()
                for field in ('body', 'hands', 'support'):
                    self.assertIn(row[field], text)
                self.assertNotIn('pose_pool_snapshot', text)
                self.assertNotIn('pose_selection', spec['shot_plan']['looks'][0])

    def test_every_geometry_binding_keeps_its_required_views(self):
        for item in library.index()['entries']:
            card = library.card(item['id'])
            for binding in card.get('pose_pool_snapshot', {}).get('entries', []):
                if 'base' not in binding:
                    continue
                row = next(r for r in card['pose_vocabulary'] if r['id'] == binding['entry']['id'])
                with self.subTest(entry=row['id']):
                    self.assertEqual(row['views'], binding['base']['definition']['garment_views'])
                    library.prepare(self.spec(item['id'], row))
                    bad = self.spec(item['id'], row)
                    bad['shot_plan']['looks'][0]['garment_views'] = ['detail']
                    bad['shot_plan']['coverage'][0]['views'] = ['front', 'detail']
                    bad['shot_plan']['route'] = 'B'
                    with self.assertRaisesRegex(ValueError, 'garment_views|coverage'):
                        library.prepare(bad)

    def test_frozen_pool_does_not_reload_shared_files(self):
        spec = self.spec('nordic-minimal')
        frozen = library.prepare(spec)
        original = copy.deepcopy(frozen)
        # Validate, subset and render an accepted snapshot with all JSON reads blocked.
        with patch.object(Path, 'read_text', side_effect=AssertionError('Unexpected live source read')):
            library._visual().validate(frozen, spec['inventory'],
                context=dict(style='nordic-minimal', first_pose=1, output_form='human'),
                count=1, identity=True, shot_plan=spec['shot_plan'])
            single = library._visual().subset(frozen, 1)
            self.assertEqual(library._visual().render(single), library._visual().render(original))
        self.assertEqual(frozen, original)

    def test_pool_tampering_fails_even_when_component_hash_is_recomputed(self):
        component = library.component(library.card('nordic-minimal'))
        for change in ('resolved', 'order', 'base'):
            with self.subTest(change=change):
                bad = copy.deepcopy(component)
                snap = bad['snapshot']
                if change == 'resolved':
                    snap['pose_vocabulary'][0]['hands'] = 'Different hands.'
                elif change == 'order':
                    snap['pose_pool'].reverse()
                else:
                    snap['pose_pool_snapshot']['entries'][0]['base']['definition']['body_action'] = 'Different body.'
                bad['sha256'] = library._visual().object_hash(snap)
                with self.assertRaisesRegex(ValueError, 'pose.pool|vocabulary'):
                    library._visual()._component(bad)

    def test_unknown_duplicate_and_restricted_pool_entries_are_rejected(self):
        for ids in ([], ['not-a-pose'], ['nm-open-stand', 'nm-open-stand']):
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                poses.freeze_vocabulary(ids)
        source = json.loads(poses.VOCABULARY.read_text())
        row = next(r for r in source['entries'] if r['id'] == 'nm-open-stand')
        path = self.root / 'vocabulary.json'
        for pose_id, view in [('tt-no-such-pose', 'front'), ('tt-stand-neutral', 'back'),
                              ('tt-close-sleeve-push', 'diag')]:
            row.update(pose_id=pose_id, view=view)
            path.write_text(json.dumps(source))
            with self.subTest(pose=pose_id, view=view), self.assertRaises(ValueError):
                poses.freeze_vocabulary(['nm-open-stand'], vocabulary_path=path)

    def test_text_menswear_does_not_expand_owned_image_scope(self):
        spec = self.spec('korean-menswear')
        library.prepare(spec)
        plan, _ = poses.apply(spec['shot_plan'], 'garment-shot-1', 'tt-stand-neutral', 'front', mode='text')
        spec['shot_plan'] = plan
        with self.assertRaisesRegex(ValueError, 'adult womenswear'):
            library.prepare(spec)

    def test_pre_migration_frozen_request_keeps_exact_bytes(self):
        # Keep the frozen source bytes independent of the host PNG encoder.
        self.source.write_bytes((ROOT / 'tests/fixtures/style-pool-legacy-source.png').read_bytes())
        self.sha = task.digest(self.source)
        fixture = json.loads((ROOT / 'tests/fixtures/style-pool-legacy.json').read_text())
        spec, visual = fixture['spec'], fixture['visual_plan']
        self.assertEqual(spec['inventory'][0]['sha256'], self.sha)
        self.assertNotIn('pose_pool', visual['style']['primary']['snapshot'])
        for route in ('codex_native', 'chatgpt_web'):
            raw = self.export(spec, visual, route, name='legacy-' + route, context=fixture['context'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), fixture['prompt_sha256'])


if __name__ == '__main__':
    unittest.main()
