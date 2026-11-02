"""Cross-group comparisons from synthetic existing ledgers, without image/model calls."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
from tests.test_pose_plan_v2 import sample_plan

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/threadtruth-studio'


def module(name):
    spec = importlib.util.spec_from_file_location('history_test_' + name, SKILL / 'scripts' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


history, library, task = module('pose_history'), module('visual_library'), module('web-task')


class PoseHistoryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.image('source', 'blue')
        self.sha = task.digest(self.source)
        self.model = dict(source_type='new', scope='full', subject='adult female model', locked=[],
                          adjustable=[], consent_note='', styling_lock='identity')
        self.output_counter = 0

    def image(self, name, colour):
        path = self.root / (name + '.png')
        Image.new('RGB', (20, 30), colour).save(path)
        return path

    def spec(self, entry='nordic-minimal', *, pose_id=None, count=1):
        card = library.card(entry)
        row = next((r for r in card['pose_vocabulary'] if r['id'] == pose_id), card['pose_vocabulary'][0])
        plan = sample_plan(count, back=False)
        plan.update(variety_checks=2, framing_guidance=2)
        plan['coverage'][0].update(sha256=self.sha)
        for i, shot in enumerate(plan['looks']):
            shot.update(reference_sha256s=[self.sha], head='Head upright.', gaze='Look at the lens.',
                        scene=['Gallery hall.', 'Window alcove.', 'Wooden room.'][i % 3])
        plan['looks'][0].update(pose_id=row['id'], body_action=row['body'], hands=row['hands'],
                               support=row['support'], garment_views=row['views'])
        return dict(entry_id=entry, count=count, first_pose=1, model=copy.deepcopy(self.model), output_form='human',
            inventory=[dict(sha256=self.sha, role='garment-source')], shot_plan=plan,
            garment=dict(description='Synthetic blue garment.', keep=['Keep original blue.'], source_sha256s=[self.sha]))

    def create(self, spec, name, *, route='codex_native', preview=False, visual=None):
        job = self.root / name
        context = dict(outfit='synthetic-history', style=spec['entry_id'], mode='C', output_form='human',
                       size=[20, 30], first_pose=spec['first_pose'], purpose='preview-grid' if preview else 'delivery')
        task.create(job, [self.source], None, [20, 30], model=spec['model'], context=context,
                    route=route, shot_plan=spec['shot_plan'], visual_plan=visual or library.prepare(spec))
        return job

    def returned(self, job, number=1, *, accepted=False):
        data = task.read(job)
        if data['authorization'] is None:
            task.update(job, 'authorize', limit=len(data['looks']), note='Synthetic fixture authority; no provider call.')
        data = task.read(job)
        task.update(job, 'reserve', look=number, ready=True, refs=task.reference_hashes(job, number),
                    expected_plan_sha256=task.plan_fingerprint(data),
                    expected_prompt_sha256=data['looks'][number - 1]['prompt_sha256'])
        self.output_counter += 1
        task.update(job, 'returned', look=number,
                    file=self.image(job.name + '-output-' + str(number), (20 * number, self.output_counter, 72)))
        task.update(job, 'accept' if accepted else 'reject', look=number,
                    qa='qa-pass' if accepted else 'qa-retry', note='Synthetic fixture review, no image quality claim.')
        if accepted and number == 1 and not task.is_preview(task.read(job)):
            task.update(job, 'confirm-model', look=1, note='Synthetic fixture first-model confirmation.')

    def prior(self, spec=None, name='prior', *, preview=False):
        job = self.create(spec or self.spec(), name, preview=preview)
        self.returned(job)
        return job

    def test_only_returned_selected_shots_are_counted_and_read_only(self):
        job = self.create(self.spec(count=6), 'partial')
        self.returned(job, accepted=True)
        self.returned(job, 2)
        before = (job / 'task.json').read_bytes()
        read_bytes = Path.read_bytes
        def json_only(path):
            self.assertEqual(path.name, 'task.json')
            return read_bytes(path)
        with patch.object(Path, 'read_bytes', json_only):
            frozen = history.freeze([job, job / 'task.json'])
        self.assertEqual(len(frozen['sources']), 1)
        self.assertEqual([e['shot_id'] for e in frozen['entries']], ['garment-shot-1', 'garment-shot-2'])
        self.assertEqual([e['state'] for e in frozen['entries']], ['accepted', 'rejected'])
        self.assertEqual(frozen['sources'][0]['skipped'], {'not-returned': 4})
        self.assertEqual((job / 'task.json').read_bytes(), before)
        self.assertNotIn(str(job), json.dumps(frozen))
        self.assertNotIn('Synthetic blue garment', json.dumps(frozen))

    def test_retry_reads_the_old_attempt_snapshot_not_the_new_pending_pose(self):
        job = self.prior()
        old = task.read(job)
        changed = self.spec(pose_id='nm-stair-pause')
        task.update(job, 'retry-authorize', look=1, expected_attempt=1, approval_id='synthetic-retry',
                    note='Synthetic fixture retry.', shot_plan=changed['shot_plan'], visual_plan=library.prepare(changed))
        frozen = history.freeze([job])
        self.assertEqual(len(frozen['entries']), 1)
        entry = frozen['entries'][0]
        self.assertEqual(entry['plan_sha256'], old['shot_plan_sha256'])
        self.assertIn('id:nm-open-stand', entry['pose_keys'])
        self.assertNotIn('id:nm-stair-pause', entry['pose_keys'])
        self.assertEqual(entry['state'], 'rejected')

    def test_shared_geometry_matches_across_style_ids_and_explicit_owned_selection(self):
        frozen = history.freeze([self.prior()])
        spec = self.spec('clean-fit', pose_id='cf-window-stand')
        report = history.compare(frozen, spec['shot_plan'], library.card('clean-fit'))
        self.assertEqual(report['repeats'][0]['matches'][0]['basis'], ['shared-geometry'])
        poses = module('pose_library')
        spec['shot_plan'], _ = poses.apply(spec['shot_plan'], 'garment-shot-1', 'tt-stand-neutral', 'front')
        self.assertIn('shared-geometry', history.compare(frozen, spec['shot_plan'])['repeats'][0]['matches'][0]['basis'])

    def test_exact_body_hands_support_ignores_camera_and_head_but_not_new_action(self):
        spec = self.spec()
        spec['shot_plan']['looks'][0].pop('pose_id')
        frozen = history.freeze([self.prior(spec)])
        shot = spec['shot_plan']['looks'][0]
        shot.update(framing='half-body', head='Head slightly tilted.', gaze='Eyes look to the side.', scene='Another room.')
        for key in ('body_action', 'hands', 'support'):
            shot[key] = '  ' + shot[key].upper().replace('.', ' ! ') + '  '
        report = history.compare(frozen, spec['shot_plan'])
        self.assertEqual(report['repeats'][0]['matches'][0]['basis'], ['body-hands-support'])
        shot['support'] = 'A chair supports the seated pelvis.'
        self.assertEqual(history.compare(frozen, spec['shot_plan'])['status'], 'no-matched-repeat')

    def test_prepare_blocks_unexplained_repeat_and_retains_concrete_reuse_reason(self):
        job = self.prior()
        spec = self.spec()
        spec['pose_history_tasks'] = [str(job)]
        with self.assertRaisesRegex(ValueError, 'Cross-group pose repeats.*garment-shot-1'):
            library.prepare(spec)
        reason = 'Retain the frontal comparison to show the new garment closure at the same angle.'
        spec['shot_plan']['looks'][0]['pose_reuse_reason'] = reason
        plan = library.prepare(spec)
        self.assertTrue(plan['pose_history']['entries'])
        self.assertEqual(history.enforce(plan['pose_history'], spec['shot_plan'], library.card('nordic-minimal'))
                         ['repeats'][0]['reuse_reason'], reason)
        for bad in ('', '   ', None):
            spec['shot_plan']['looks'][0]['pose_reuse_reason'] = bad
            with self.subTest(reason=bad), self.assertRaises(ValueError):
                library.prepare(spec)

    def test_both_exports_use_frozen_history_without_rereading_sources_or_rendering_it(self):
        prior = self.prior()
        spec = self.spec(pose_id='nm-stair-pause')
        spec['pose_history_tasks'] = [str(prior)]
        visual = library.prepare(spec)
        (prior / 'task.json').unlink()  # Only this synthetic source; no future dependency on its location.
        texts = []
        for route in ('codex_native', 'chatgpt_web'):
            job = self.create(spec, route, route=route, visual=visual)
            task.export(job)
            data = task.read(job)
            folder = task.handoff_directory(job, data, data['looks'][0])
            raw = (folder / 'prompt.txt').read_bytes()
            texts.append(raw)
            manifest = json.loads((folder / 'manifest.json').read_text())
            self.assertEqual(manifest['visual_plan']['pose_history'], visual['pose_history'])
            self.assertEqual(data['attempts'], 0)
            self.assertIsNone(data['authorization'])
            self.assertNotIn('history-1', raw.decode())
            self.assertIn(spec['shot_plan']['looks'][0]['body_action'], raw.decode())
            if route == 'codex_native':
                request = json.loads((folder / 'request.json').read_text())
                self.assertEqual(request['prompt'].encode(), raw)
            else:
                packet = task.export_web_execution(job, 1)
                envelope = task.web_execution_helper()
                self.assertEqual(Path(packet['submission_file']).read_bytes(),
                    envelope.prefix(envelope.version(data)) + raw + envelope.SUFFIX)
        self.assertEqual(texts[0], texts[1])

    def test_standalone_subset_checks_selected_shot_and_series_first_checks_full_plan(self):
        frozen = history.freeze([self.prior()])
        plan = self.spec(count=6)['shot_plan']
        shot = task.shot_helper()
        standalone = shot.subset(plan, 6)
        self.assertEqual(history.enforce(frozen, standalone, library.card('nordic-minimal'))['repeats'], [])
        trial = shot.subset(plan, 1, series_role='series-first')
        with self.assertRaisesRegex(ValueError, 'Cross-group pose repeats'):
            history.enforce(frozen, trial, library.card('nordic-minimal'))
        plan['looks'][0]['pose_reuse_reason'] = 'Same frontal baseline is required for this product comparison.'
        history.enforce(frozen, shot.subset(plan, 1, series_role='series-first'), library.card('nordic-minimal'))

    def test_preview_history_covers_its_active_cells_with_explicit_preview_status(self):
        spec = self.spec(count=6)
        job = self.prior(spec, preview=True)
        frozen = history.freeze([job])
        self.assertEqual(len(frozen['entries']), 6)
        self.assertEqual({e['purpose'] for e in frozen['entries']}, {'preview-grid'})
        self.assertEqual({e['state'] for e in frozen['entries']}, {'rejected'})

    def test_delivery_retry_cannot_introduce_a_historical_repeat_without_a_reason(self):
        prior = self.prior()
        spec = self.spec(pose_id='nm-stair-pause')
        spec['pose_history_tasks'] = [str(prior)]
        job = self.create(spec, 'new-group')
        self.returned(job)
        before = (job / 'task.json').read_bytes()
        data = task.read(job)
        changed = self.spec()['shot_plan']
        args = dict(look=1, expected_attempt=1, approval_id='synthetic-local',
                    note='Synthetic local retry fixture.', shot_plan=changed, visual_plan=data['visual_plan'])
        with self.assertRaisesRegex(ValueError, 'Cross-group pose repeats'):
            task.update(job, 'retry-authorize', **args)
        self.assertEqual((job / 'task.json').read_bytes(), before)
        changed['looks'][0]['pose_reuse_reason'] = 'Use the front baseline to compare the source-backed closure.'
        after = task.update(job, 'retry-authorize', **args)
        self.assertEqual(after['visual_plan']['pose_history'], data['visual_plan']['pose_history'])
        self.assertEqual(after['attempts'], 1)
        self.assertEqual(after['looks'][0]['history'][0]['state'], 'rejected')

    def test_preview_delivery_and_continuation_inherit_history_without_counting_themselves(self):
        prior = self.prior()
        spec = self.spec(pose_id='nm-stair-pause', count=6)
        spec['pose_history_tasks'] = [str(prior)]
        parent = self.create(spec, 'new-preview', preview=True)
        self.returned(parent, accepted=True)
        task.update(parent, 'finish-preview', decision='direction-confirmed', note='Synthetic direction confirmation.')
        original = task.read(parent)
        context = dict(original['context'], purpose='delivery')
        child = self.root / 'series-first'
        data = task.create_from_preview(child, parent, dict(context=context, size=[20, 30], count=1,
            series_role='series-first'), note='Synthetic first delivery preparation.')
        self.assertEqual(data['visual_plan']['pose_history'], original['visual_plan']['pose_history'])
        self.returned(child, accepted=True)
        data = task.read(child)
        continued = task.update(child, 'continue-authorize', context=data['context'], approval_id='synthetic-rest-five',
            note='Synthetic remaining five fixture.', shot_plan=spec['shot_plan'], visual_plan=original['visual_plan'])
        self.assertEqual(len(continued['looks']), 6)
        self.assertEqual(continued['visual_plan']['pose_history'], original['visual_plan']['pose_history'])
        self.assertEqual(len(continued['visual_plan']['pose_history']['sources']), 1)

    def test_invalid_history_hash_is_rejected_and_legacy_or_draft_gaps_are_visible(self):
        draft = self.create(self.spec(), 'draft')
        legacy = self.root / 'legacy.json'
        legacy.write_text(json.dumps(dict(schema_version=1, looks=[dict(number=1, state='accepted', output=dict(sha256='a' * 64))])))
        frozen = history.freeze([draft, legacy])
        report = history.compare(frozen, self.spec()['shot_plan'])
        self.assertEqual(report['status'], 'no-comparable-history')
        self.assertEqual(report['compared_records'], 0)
        self.assertEqual(frozen['sources'][1]['skipped'], {'unsupported-or-missing-plan': 1})
        changed = copy.deepcopy(frozen)
        changed['sources'][0]['skipped']['not-returned'] = 8
        with self.assertRaisesRegex(ValueError, 'hash changed'):
            history.validate(changed)
        data = task.read(draft)
        data['shot_plan']['looks'][0]['support'] = 'Unfrozen modification.'
        (draft / 'task.json').write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'shot plan hash changed'):
            history.freeze([draft])

    def test_cli_reports_repeats_and_pre_migration_inline_cards_keep_their_own_identity(self):
        fixture = json.loads((ROOT / 'tests/fixtures/style-pool-legacy.json').read_text())
        job = self.create(fixture['spec'], 'old-inline', visual=fixture['visual_plan'])
        self.returned(job)
        new = self.spec()
        path = self.root / 'proposed.json'
        path.write_text(json.dumps(new['shot_plan']))
        before = (job / 'task.json').read_bytes()
        result = subprocess.run([sys.executable, str(SKILL / 'scripts/pose_history.py'), '--task', str(job),
            '--plan', str(path), '--entry-id', 'nordic-minimal'], capture_output=True, text=True, check=True)
        report = json.loads(result.stdout)
        self.assertEqual(report['comparison']['status'], 'repeats')
        self.assertIn('pose-id', report['comparison']['repeats'][0]['matches'][0]['basis'])
        self.assertFalse(any(k.startswith('owned:') for k in report['pose_history']['entries'][0]['pose_keys']))
        self.assertEqual((job / 'task.json').read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
