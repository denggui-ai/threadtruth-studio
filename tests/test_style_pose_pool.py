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

Q6_POOL_IDS = {
    'neo-chinese': ('tea-room-stand', 'courtyard-step', 'screen-bench-seat', 'tea-table-palm',
                    'corridor-gather-turn', 'stone-ledge-forearm', 'halfbody-conversation', 'closure-detail'),
    'hanfu-form-specific': ('layer-stand', 'measured-step', 'broad-bench-seat', 'side-palm-rest',
                           'gathered-turn', 'low-sleeve-space', 'halfbody-bench-laugh', 'overlap-detail'),
    'lolita-layered': ('skirt-clear-stand', 'short-promenade', 'armless-bench-seat', 'side-console-palm',
                      'small-pivot', 'shoe-offset-pause', 'halfbody-shoulder-laugh', 'lace-layer-detail'),
    'gorpcore': ('trail-scout', 'incline-walk', 'boulder-rest', 'trail-rail-palm',
                'low-ledge-step', 'sheltered-squat', 'halfbody-van-laugh', 'construction-detail'),
    'y2k-millennium': ('pop-stand', 'record-shop-step', 'booth-bench-seat', 'metal-wall-shoulder',
                       'arcade-pivot', 'side-counter-palm', 'halfbody-sticker-grin', 'surface-detail'),
    'future-artificial-light': ('threshold-stand', 'strip-walk', 'practical-ledge-seat', 'mullion-shoulder',
                               'lightline-pivot', 'rail-palm', 'halfbody-warm-laugh', 'neutral-detail'),
    'ecommerce-studio': ('open-stand', 'forward-step', 'block-seat', 'wall-shoulder',
                         'settled-pivot', 'side-block-palm', 'halfbody-soft-smile', 'construction-detail'),
}

# Q6c appends two text-only, waist-up actions after each original eight-entry pool.
Q6C_HALF_BODY_IDS = {
    'american-street': ('as-halfbody-cuff-pause', 'as-halfbody-shutter-forearm'),
    'athleisure': ('al-halfbody-ear-tuck', 'al-halfbody-rail-elbows'),
    'balletcore': ('bc-halfbody-barre-forearms', 'bc-halfbody-soft-wrist'),
    'british-heritage': ('bh-halfbody-cuff-set', 'bh-halfbody-study-chin'),
    'cityboy': ('cb-halfbody-ear-tuck', 'cb-halfbody-bench-chin'),
    'clean-fit': ('cf-halfbody-cuff-pause', 'cf-halfbody-table-chin'),
    'coquette-ladylike': ('cq-halfbody-wrist-poise', 'cq-halfbody-chair-listen'),
    'ecommerce-studio': ('ecommerce-studio-halfbody-cuff-check', 'ecommerce-studio-halfbody-wall-forearm'),
    'french-effortless': ('fr-halfbody-cafe-chin', 'fr-halfbody-door-forearm'),
    'gorpcore': ('gorpcore-halfbody-cuff-check', 'gorpcore-halfbody-rail-elbows'),
    'guochao-street': ('gc-halfbody-folded-arms', 'gc-halfbody-wall-forearm'),
    'italian-luxe': ('il-halfbody-cuff-study', 'il-halfbody-terrace-chin'),
    'japanese-lifestyle': ('jl-halfbody-table-listen', 'jl-halfbody-curtain-guide'),
    'korean-cold-editorial': ('kc-halfbody-temple-rest', 'kc-halfbody-wall-forearm'),
    'korean-menswear': ('km-halfbody-cuff-align', 'km-halfbody-frame-forearm'),
    'neo-chinese': ('neo-chinese-halfbody-sleeve-study', 'neo-chinese-halfbody-table-chin'),
    'nordic-minimal': ('nm-halfbody-table-chin', 'nm-halfbody-ear-tuck'),
    'office-commute-women': ('oc-halfbody-cuff-check', 'oc-halfbody-desk-listen'),
    'old-money': ('om-halfbody-cuff-pause', 'om-halfbody-veranda-chin'),
    'preppy': ('pp-halfbody-ear-tuck', 'pp-halfbody-bench-chin'),
    'quiet-luxury': ('ql-halfbody-cuff-touch', 'ql-halfbody-sofa-forearms'),
    'resort-vacation': ('rv-halfbody-hair-tuck', 'rv-halfbody-balcony-chin'),
    'workwear-vintage': ('wv-halfbody-cuff-check', 'wv-halfbody-bench-elbows'),
    'y2k-millennium': ('y2k-millennium-halfbody-cheek-frame', 'y2k-millennium-halfbody-folded-arms'),
    'retro-americana': ('ra-halfbody-ear-tuck', 'ra-halfbody-booth-chin'),
    'gothic-editorial': ('ge-halfbody-folded-arms', 'ge-halfbody-chair-temple'),
    'romantic-bohemian': ('rb-halfbody-hair-tuck', 'rb-halfbody-tree-forearm'),
    'future-artificial-light': ('future-artificial-light-halfbody-mullion-forearm',
                                'future-artificial-light-halfbody-cuff-study'),
    'hanfu-form-specific': ('hanfu-form-specific-halfbody-sleeve-cradle',
                            'hanfu-form-specific-halfbody-ledge-elbows'),
    'qipao-urban': ('qp-halfbody-ear-tuck', 'qp-halfbody-door-forearm'),
    'bridal-ethereal': ('be-halfbody-wrist-cradle', 'be-halfbody-window-forearm'),
    'lolita-layered': ('lolita-layered-halfbody-wrist-cradle', 'lolita-layered-halfbody-curious-palm'),
}


def module(name):
    spec = importlib.util.spec_from_file_location('pool_' + name, SKILL / 'scripts' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


library, poses, task = module('visual_library'), module('pose_library'), module('web-task')


def use_current_pool_in_fixture(frozen):
    """Keep rendering fixtures on current pool content without testing pool migration."""
    component = frozen['style']['primary']
    card = library.card(component['id'])
    for key in ('pose_pool', 'pose_pool_snapshot', 'pose_vocabulary'):
        component['snapshot'][key] = copy.deepcopy(card[key])
    component['sha256'] = library._visual().object_hash(component['snapshot'])
    return frozen


def bind_pool_actions(spec):
    """Give new synthetic rendering fixtures actual pool selections, preserving their test targets."""
    plan = spec['shot_plan']
    bodies = [cell for cell in plan['looks'] if cell['framing'] != 'detail']
    supported = set().union(*(set(row['views']) for row in plan['coverage']))
    rows = [row for row in library.card(spec['entry_id']).get('pose_vocabulary', [])
            if set(row['views']) <= supported and 'back' not in row['views']
            and row['id'] != 'fr-laugh-turn']
    for cell, row in zip(bodies[:(len(bodies) + 1) // 2], rows):
        cell.pop('pose_decision', None)
        cell.update(pose_id=row['id'], body_action=row['body'], hands=row['hands'],
                    support=row['support'], garment_views=row['views'])
    for cell in bodies:
        if 'pose_id' not in cell:
            cell['pose_decision'] = dict(kind='custom', reason='池内扶窗和交叉手臂会挡住本格袖口结构，改为双臂自然外展。')
    return spec


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
        elif entry == 'hanfu-form-specific':
            spec.update(culture_profile=dict(id='hanfu-test-form', version=1, form='synthetic source-backed layers'),
                        asset_trace=[dict(asset='C05', decision='translated', affects='Keep the supplied collar and layers.',
                                          check='Collar direction, sleeves and wearing order match the source.')])
        return spec

    def export(self, spec, visual, route, name=None, context=None):
        job = self.root / (name or spec['entry_id'] + '-' + route)
        context = context or dict(outfit='synthetic-pool', style=spec['entry_id'], mode='C',
            output_form='human', size=[20, 30], first_pose=1, purpose='delivery')
        task.create(job, [self.source], None, [20, 30], model=spec['model'], context=context,
                    route=route, shot_plan=spec['shot_plan'], visual_plan=visual, count=1, workflow_version=0)
        if name and name.startswith('legacy-'):
            data = task.read(job)
            data.pop('prompt_render', None)  # pre-migration tasks predate the dedupe render marker
            task.save(job, data)
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
        self.assertEqual(len(migrated), 32)
        self.assertEqual(len(used), 320)
        self.assertEqual(set(used), set(by_id))
        self.assertEqual(len(used), len(set(used)))

    def test_three_new_style_pools_freeze_each_action_and_keep_detail_commitments(self):
        for entry in ('resort-vacation', 'qipao-urban', 'romantic-bohemian'):
            card = library.card(entry)
            self.assertEqual(len(card['pose_vocabulary']), 10)
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

    def test_q6_style_pools_resolve_stable_ids_and_freeze_each_action(self):
        for entry, suffixes in Q6_POOL_IDS.items():
            card = library.card(entry)
            expected_ids = [entry + '-' + suffix for suffix in suffixes] + list(Q6C_HALF_BODY_IDS[entry])
            self.assertEqual(card['pose_pool'], expected_ids)
            self.assertEqual([row['id'] for row in card['pose_vocabulary']], expected_ids)
            self.assertEqual(len(set(expected_ids)), 10)
            self.assertTrue({'stand', 'walk', 'sit', 'lean', 'close'} <=
                            {row['family'] for row in card['pose_vocabulary']})
            self.assertEqual(sum('-halfbody-' in row['id'] for row in card['pose_vocabulary']), 3)
            self.assertEqual(sum(row['family'] == 'close' for row in card['pose_vocabulary']), 1)
            for row in card['pose_vocabulary']:
                with self.subTest(entry=entry, action=row['id']):
                    spec = self.spec(entry, row)
                    spec['shot_plan']['framing_guidance'] = 3
                    cell = spec['shot_plan']['looks'][0]
                    if row['family'] == 'close':
                        cell['framing'] = 'detail'
                    elif '-halfbody-' in row['id']:
                        cell['framing'] = 'half-body'
                    frozen = library.prepare(spec)
                    snapshot = frozen['style']['primary']['snapshot']
                    self.assertEqual(snapshot['pose_pool'], expected_ids)
                    self.assertEqual(snapshot['action_tendency'], card['action_tendency'])
                    self.assertEqual(snapshot['pose_vocabulary'], card['pose_vocabulary'])
                    rendered = self.export(spec, frozen, 'codex_native', name=row['id']).decode()
                    for field in ('body', 'hands', 'support'):
                        self.assertIn(row[field], rendered)
                    for item in frozen.get('commitments', []):
                        self.assertIn(item['show'], rendered)
                    self.assertEqual(frozen['shots'][0]['framing'], cell['framing'])

    def test_q6c_appends_stable_ids_and_preserves_original_vocabulary_bytes(self):
        # f8cf39c: every byte through the last original entry, plus original pool order.
        original_prefix = poses.VOCABULARY.read_bytes()[:137523]
        self.assertEqual(hashlib.sha256(original_prefix).hexdigest(),
                         '3c940e68294a604db9467982384bd45c699e7815c001e723c072ab270426d517')
        source = json.loads(poses.VOCABULARY.read_text())['entries']
        self.assertEqual(source[:256], json.loads(original_prefix + b'\n  ]\n}\n')['entries'])
        original_pools = {}
        new_ids = []
        for item in library.index()['entries']:
            card = library.card(item['id'])
            if 'pose_pool' not in card:
                self.assertNotIn(item['id'], Q6C_HALF_BODY_IDS)
                continue
            with self.subTest(entry=item['id']):
                expected = Q6C_HALF_BODY_IDS[item['id']]
                self.assertEqual(len(card['pose_pool']), 10)
                self.assertEqual(card['pose_pool'][8:], list(expected))
                original_pools[item['id']] = card['pose_pool'][:8]
                new_ids.extend(expected)
                for row in card['pose_vocabulary'][8:]:
                    self.assertEqual(set(row), {'id', 'family', 'body', 'hands', 'support',
                                                'views', 'avoid_when', 'check'})
                    self.assertIn('half-body', row['body'])
                    self.assertNotEqual(row['family'], 'close')
                    self.assertEqual(row['views'], ['front'])
                    for field in ('body', 'hands', 'support', 'avoid_when', 'check'):
                        self.assertTrue(row[field].strip())
                        self.assertNotIn('\n', row[field])
        self.assertEqual(set(original_pools), set(Q6C_HALF_BODY_IDS))
        self.assertEqual(hashlib.sha256(json.dumps(original_pools, sort_keys=True).encode()).hexdigest(),
                         '27a922279274053e15796ca133bb7bc8b1ccf1dade12754e3e6eb3dfd55969d7')
        self.assertEqual(len(new_ids), len(set(new_ids)))
        self.assertEqual([row['id'] for row in source[256:]], new_ids)

    def test_q6c_every_halfbody_action_freezes_and_reaches_both_exports(self):
        for entry in Q6C_HALF_BODY_IDS:
            card = library.card(entry)
            for row in card['pose_vocabulary'][8:]:
                with self.subTest(entry=entry, action=row['id']):
                    spec = self.spec(entry, row)
                    spec['shot_plan']['framing_guidance'] = 3
                    spec['shot_plan']['looks'][0]['framing'] = 'half-body'
                    frozen = library.prepare(spec)
                    snapshot = frozen['style']['primary']['snapshot']
                    self.assertEqual(snapshot['pose_pool'], card['pose_pool'])
                    self.assertEqual(snapshot['pose_vocabulary'][8:], card['pose_vocabulary'][8:])
                    self.assertEqual(frozen['shots'][0]['framing'], 'half-body')
                    native = self.export(spec, frozen, 'codex_native', name=row['id'] + '-native')
                    web = self.export(spec, frozen, 'chatgpt_web', name=row['id'] + '-web')
                    self.assertEqual(native, web)
                    rendered = native.decode()
                    for field in ('body', 'hands', 'support'):
                        self.assertIn(row[field], rendered)
                    for commitment in frozen.get('commitments', []):
                        self.assertIn(commitment['show'], rendered)
                    # Accepted snapshots validate and render without consulting shared source files.
                    visual = library._visual()
                    with patch.object(Path, 'read_text', side_effect=AssertionError('Unexpected live source read')):
                        visual.validate(frozen, spec['inventory'],
                            context=dict(style=entry, first_pose=1, output_form='human'),
                            count=1, identity=True, shot_plan=spec['shot_plan'])
                        self.assertEqual(visual.render(visual.subset(frozen, 1), 1),
                                         visual.render(frozen, 1))

    def test_q6_frozen_style_pools_do_not_reload_shared_files(self):
        for entry in Q6_POOL_IDS:
            card = library.card(entry)
            for row in card['pose_vocabulary']:
                with self.subTest(entry=entry, action=row['id']):
                    spec = self.spec(entry, row)
                    spec['shot_plan']['framing_guidance'] = 3
                    if row['family'] == 'close':
                        spec['shot_plan']['looks'][0]['framing'] = 'detail'
                    elif '-halfbody-' in row['id']:
                        spec['shot_plan']['looks'][0]['framing'] = 'half-body'
                    frozen = library.prepare(spec)
                    original = copy.deepcopy(frozen)
                    visual = library._visual()
                    rendered = visual.render(frozen, 1)
                    with patch.object(Path, 'read_text', side_effect=AssertionError('Unexpected live source read')):
                        visual.validate(frozen, spec['inventory'],
                            context=dict(style=entry, first_pose=1, output_form='human'),
                            count=1, identity=True, shot_plan=spec['shot_plan'])
                        self.assertEqual(visual.render(visual.subset(frozen, 1), 1), rendered)
                    self.assertEqual(frozen, original)

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
