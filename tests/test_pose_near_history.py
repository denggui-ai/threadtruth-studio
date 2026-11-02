"""Conservative field-text comparisons; synthetic ledgers, no model/image provider."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from tests import test_pose_history as fixtures

history, library, task, SKILL = fixtures.history, fixtures.library, fixtures.task, fixtures.SKILL


class NearPoseHistoryTests(unittest.TestCase):
    setUp = fixtures.PoseHistoryTests.setUp
    image = fixtures.PoseHistoryTests.image
    spec = fixtures.PoseHistoryTests.spec
    create = fixtures.PoseHistoryTests.create
    returned = fixtures.PoseHistoryTests.returned
    prior = fixtures.PoseHistoryTests.prior

    def custom(self):
        spec = self.spec()
        shot = spec['shot_plan']['looks'][0]
        shot.pop('pose_id')
        shot.update(body_action='Stand upright with the left foot forward, right foot behind, weight mainly on the left leg and shoulders relaxed.',
                    hands='The left hand rests on the left thigh, with the right hand relaxed beside the right hip.',
                    support='Both feet planted on the floor; no external support.')
        return spec

    def test_actual_library_pair_reports_near_fields_without_exact_identity(self):
        previous = self.spec('athleisure', pose_id='al-zip-close')
        proposed = self.spec('old-money', pose_id='om-cuff-close')
        job = self.prior(previous)
        before = (job / 'task.json').read_bytes()
        frozen = history.freeze([job])
        report = history.compare(frozen, proposed['shot_plan'], library.card('old-money'))
        match = report['repeats'][0]['matches'][0]
        self.assertEqual(match['basis'], ['near-body-hands-support'])
        self.assertEqual(match['state'], 'rejected')
        self.assertGreaterEqual(match['field_similarity']['body_action'], .8)
        self.assertEqual(match['field_similarity']['hands'], 1)
        self.assertEqual(match['field_similarity']['support'], 1)
        self.assertEqual(report['near_comparison']['compared_pairs'], 1)
        reverse = history.freeze([self.prior(proposed, 'reverse')])
        self.assertEqual(history.compare(reverse, previous['shot_plan'])['repeats'][0]['matches'][0]
                         ['field_similarity'], match['field_similarity'])
        proposed_path = self.root / 'proposal.json'
        proposed_path.write_text(json.dumps(proposed['shot_plan']))
        cli = subprocess.run([sys.executable, str(SKILL / 'scripts/pose_history.py'), '--task', str(job),
            '--plan', str(proposed_path)], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(cli.stdout)['comparison'], report)
        self.assertEqual((job / 'task.json').read_bytes(), before)

    def test_word_forms_match_actual_fields_while_camera_and_head_are_irrelevant(self):
        spec = self.custom()
        shot = spec['shot_plan']['looks'][0]
        shot.update(body_action='Stand upright, feet apart and knees relaxed.',
                    hands='Both hands hanging low outside the side seams.',
                    support='Both feet planted on the ground.')
        frozen = history.freeze([self.prior(spec)])
        shot.update(body_action='Standing upright, feet apart with knees relaxing.',
                    hands='Both hands hang low outside the side seams.',
                    support='Both feet planted on the floor.', head='Head slightly tilted.',
                    gaze='Eyes toward the window.', framing='half-body', scene='A different room.')
        match = history.compare(frozen, spec['shot_plan'])['repeats'][0]['matches'][0]
        self.assertEqual(match['basis'], ['near-body-hands-support'])
        self.assertEqual(set(match['field_similarity'].values()), {1.0})

    def test_critical_differences_are_not_outweighed_by_shared_long_text(self):
        spec = self.custom()
        frozen = history.freeze([self.prior(spec)])
        original = spec['shot_plan']['looks'][0]
        changes = [
            ('body_action', original['body_action'].replace('Stand', 'Sit')),
            ('body_action', original['body_action'].replace('Stand', 'Walk')),
            ('body_action', original['body_action'].replace('left foot forward, right foot behind',
                                                         'right foot forward, left foot behind')),
            ('body_action', original['body_action'].replace('on the left leg', 'on the right leg')),
            ('hands', original['hands'].replace('left hand rests on the left thigh',
                                              'right hand rests on the left thigh')),
            ('hands', original['hands'].replace('on the left thigh', 'inside the left pocket')),
            ('hands', original['hands'].replace('rests on', 'does not rest on')),
            ('support', original['support'].replace('no external support', 'external support')),
            ('support', original['support'].replace('floor', 'stool')),
            ('support', original['support'].replace('Both feet planted', 'One foot planted')),
        ]
        for field, text in changes:
            with self.subTest(field=field, action=text):
                plan = copy.deepcopy(spec['shot_plan'])
                plan['looks'][0][field] = text
                report = history.compare(frozen, plan)
                self.assertEqual(report['repeats'], [])
                self.assertEqual(report['near_comparison']['compared_pairs'], 1)
        # A family shared by two entries is not a match in the absence of field similarity.
        card = library.card('athleisure')
        a = self.spec('athleisure', pose_id='al-gym-window-stand')
        b = self.spec('athleisure', pose_id='al-gym-window-stand')
        # Use two genuinely different custom standing actions without relying on ID labels.
        b['shot_plan']['looks'][0].pop('pose_id')
        b['shot_plan']['looks'][0].update(body_action='Stand with knees deeply bent and the pelvis lowered.',
                                        hands='One hand raised above the shoulder.', support='Both feet on the floor.')
        self.assertEqual(history.compare(history.freeze([self.prior(a, 'another')]), b['shot_plan'], card)['repeats'], [])

    def test_missing_near_evidence_is_reported_for_short_or_uncovered_language(self):
        spec = self.custom()
        frozen = history.freeze([self.prior(spec)])
        for field, value in [('body_action', 'Stand.'), ('body_action', '自然站立，双脚分开，重心均匀。'),
                             ('hands', 'Relax.'), ('support', 'A sculpted display plinth.')]:
            with self.subTest(field=field):
                proposed = copy.deepcopy(spec['shot_plan'])
                proposed['looks'][0][field] = value
                report = history.compare(frozen, proposed)
                self.assertEqual(report['status'], 'no-matched-repeat')
                self.assertEqual(report['near_comparison']['compared_pairs'], 0)
                self.assertEqual(report['near_comparison']['unavailable_pairs'], 1)
        spec['shot_plan']['looks'][0]['support'] = 'A sculpted display plinth.'
        unsupported = history.freeze([self.prior(spec, 'uncovered-history')])
        self.assertEqual(history.compare(unsupported, self.custom()['shot_plan'])['near_comparison']['unavailable_pairs'], 1)

    def test_arm_height_and_extension_are_distinct_even_in_long_shared_descriptions(self):
        for before, after in [('raised high', 'raised low'), ('extended forward', 'folded forward')]:
            with self.subTest(change=after):
                spec = self.custom()
                spec['shot_plan']['looks'][0]['hands'] = (
                    'Both arms ' + before + ', hands well outside the garment edges with elbows gently bent.')
                frozen = history.freeze([self.prior(spec, before.replace(' ', '-'))])
                spec['shot_plan']['looks'][0]['hands'] = spec['shot_plan']['looks'][0]['hands'].replace(before, after)
                self.assertEqual(history.compare(frozen, spec['shot_plan'])['repeats'], [])

    def test_new_features_are_hashed_and_tampering_is_rejected(self):
        spec = self.custom()
        frozen = history.freeze([self.prior(spec)])
        self.assertEqual(frozen['version'], 2)
        raw = json.dumps(frozen)
        for field in ('body_action', 'hands', 'support'):
            self.assertNotIn(spec['shot_plan']['looks'][0][field], raw)
        broken = copy.deepcopy(frozen)
        broken['entries'][0]['action_features']['support']['words'][0] = 'a' * 64
        with self.assertRaisesRegex(ValueError, 'hash changed'):
            history.validate(broken)
        broken['entries'][0]['action_features']['support'] = dict(words=['invalid'], relations=['invalid'])
        broken['sha256'] = history.digest({k: v for k, v in broken.items() if k != 'sha256'})
        with self.assertRaisesRegex(ValueError, 'near-pose field features'):
            history.validate(broken)

    def test_near_reuse_reason_enforced_through_both_real_export_paths(self):
        prior = self.prior(self.spec('athleisure', pose_id='al-zip-close'))
        spec = self.spec('old-money', pose_id='om-cuff-close')
        spec['pose_history_tasks'] = [str(prior)]
        with self.assertRaisesRegex(ValueError, 'Cross-group pose repeats.*near field text'):
            library.prepare(spec)
        reason = 'Keep the same low-hand baseline to compare the new cuff construction.'
        spec['shot_plan']['looks'][0]['pose_reuse_reason'] = reason
        visual = library.prepare(spec)
        spec['shot_plan']['looks'][0].pop('pose_reuse_reason')
        with self.assertRaisesRegex(ValueError, 'Cross-group pose repeats.*near field text'):
            self.create(spec, 'blocked-init', visual=visual)
        spec['shot_plan']['looks'][0]['pose_reuse_reason'] = reason
        (prior / 'task.json').unlink()
        prompts = []
        for route in ('codex_native', 'chatgpt_web'):
            job = self.create(spec, route, route=route, visual=visual)
            task.export(job)
            data = task.read(job)
            folder = task.handoff_directory(job, data, data['looks'][0])
            prompt = (folder / 'prompt.txt').read_bytes()
            prompts.append(prompt)
            manifest = json.loads((folder / 'manifest.json').read_text())
            self.assertEqual(manifest['visual_plan']['pose_history'], visual['pose_history'])
            self.assertEqual(data['attempts'], 0)
            self.assertIsNone(data['authorization'])
            self.assertNotIn(reason.encode(), prompt)
            self.assertNotIn(b'action_features', prompt)
            if route == 'codex_native':
                self.assertEqual(json.loads((folder / 'request.json').read_text())['prompt'].encode(), prompt)
            else:
                packet = task.export_web_execution(job, 1)
                envelope = task.web_execution_helper()
                self.assertEqual(Path(packet['submission_file']).read_bytes(),
                                 envelope.prefix(envelope.version(data)) + prompt + envelope.SUFFIX)
        self.assertEqual(prompts[0], prompts[1])

    def test_near_repeat_on_local_retry_retains_frozen_scope_and_requires_reason(self):
        prior = self.prior(self.spec('athleisure', pose_id='al-zip-close'))
        spec = self.spec('old-money', pose_id='om-cuff-close')
        original_shot = copy.deepcopy(spec['shot_plan']['looks'][0])
        spec['shot_plan']['looks'][0].pop('pose_id')
        spec['shot_plan']['looks'][0].update(body_action='Sit upright on a chair with feet firmly apart.',
                                           hands='Both hands on the chair edges.', support='Chair supports the pelvis.')
        spec['pose_history_tasks'] = [str(prior)]
        job = self.create(spec, 'retry-group')
        self.returned(job)
        data = task.read(job)
        before = (job / 'task.json').read_bytes()
        revised = copy.deepcopy(spec['shot_plan'])
        revised['looks'][0] = original_shot
        args = dict(look=1, expected_attempt=1, approval_id='synthetic-near-retry',
                    note='Synthetic retry fixture.', shot_plan=revised, visual_plan=data['visual_plan'])
        with self.assertRaisesRegex(ValueError, 'Cross-group pose repeats.*near field text'):
            task.update(job, 'retry-authorize', **args)
        self.assertEqual((job / 'task.json').read_bytes(), before)
        revised['looks'][0]['pose_reuse_reason'] = 'Return to the low-hand baseline for a source-backed cuff comparison.'
        after = task.update(job, 'retry-authorize', **args)
        self.assertEqual(after['visual_plan']['pose_history'], data['visual_plan']['pose_history'])
        self.assertEqual(after['attempts'], 1)
        self.assertEqual(after['looks'][0]['history'][0]['state'], 'rejected')

    def test_frozen_v1_stays_exact_only_and_selected_shot_scope_is_preserved(self):
        prior = self.prior(self.spec('athleisure', pose_id='al-zip-close'))
        current = history.freeze([prior])
        legacy = copy.deepcopy(current)
        legacy['version'] = 1
        for entry in legacy['entries']:
            entry.pop('action_features')
        legacy['sha256'] = history.digest({k: v for k, v in legacy.items() if k != 'sha256'})
        new = self.spec('old-money', pose_id='om-cuff-close')
        raw = json.dumps(legacy, sort_keys=True)
        report = history.enforce(legacy, new['shot_plan'], library.card('old-money'))
        self.assertEqual(report['status'], 'no-exact-repeat')
        self.assertNotIn('near_comparison', report)
        self.assertEqual(json.dumps(legacy, sort_keys=True), raw)
        with self.assertRaisesRegex(ValueError, 'Cross-group pose repeats'):
            history.enforce(legacy, self.spec('athleisure', pose_id='al-zip-close')['shot_plan'])
        visual = library.prepare(new)
        control = self.create(new, 'no-history', visual=visual)
        task.export(control)
        control_data = task.read(control)
        expected = (task.handoff_directory(control, control_data, control_data['looks'][0]) / 'prompt.txt').read_bytes()
        visual['pose_history'] = legacy
        old = self.create(new, 'v1-history', visual=visual)
        task.export(old)
        old_data = task.read(old)
        actual = (task.handoff_directory(old, old_data, old_data['looks'][0]) / 'prompt.txt').read_bytes()
        self.assertEqual(actual, expected)
        self.assertEqual(old_data['visual_plan']['pose_history'], legacy)
        full = self.spec('old-money', pose_id='om-cuff-close', count=6)['shot_plan']
        self.assertEqual(history.enforce(current, task.shot_helper().subset(full, 6))['repeats'], [])
        with self.assertRaisesRegex(ValueError, 'near field text'):
            history.enforce(current, task.shot_helper().subset(full, 1, series_role='series-first'))


if __name__ == '__main__':
    unittest.main()
