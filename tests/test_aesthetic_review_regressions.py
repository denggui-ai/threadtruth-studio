"""Offline regressions converted from the aesthetic review's continuation/detail repros."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from PIL import Image
from tests import test_style_pose_pool as fixtures

library, task, recommend = (fixtures.module(name) for name in ('visual_library', 'web-task', 'pose_recommend'))
ROOT = Path(__file__).resolve().parents[1]


class AestheticReviewRegressionTests(unittest.TestCase):
    setUp = fixtures.StylePosePoolTests.setUp

    def legacy_series(self):
        fixture = json.loads((ROOT / 'tests/fixtures/aesthetic-legacy-series.json').read_text())
        self.assertEqual(fixture['baseline'], 'd7d7e66')
        spec, frozen = fixture['spec'], fixture['visual_plan']
        self.assertEqual(spec['garment']['source_sha256s'], [self.sha])
        context = dict(fixture['context'], purpose='delivery')
        return spec, frozen, context

    def create(self, spec, frozen, context, name='task'):
        job = self.root / name
        task.create(job, [self.source], None, [20, 30], model=spec['model'], context=context,
                    shot_plan=spec['shot_plan'], visual_plan=frozen, workflow_version=0)
        return job

    def reserve(self, job, number=1):
        task.update(job, 'reserve', look=number, ready=True, refs=task.reference_hashes(job, number),
                    expected_plan_sha256=task.plan_fingerprint(task.read(job)))

    def accepted(self, job):
        task.update(job, 'authorize', limit=1, note='Synthetic one-image authority.')
        self.reserve(job)
        output = self.root / 'accepted.png'
        Image.new('RGB', (20, 30), 'green').save(output)
        task.update(job, 'returned', look=1, file=output)
        task.update(job, 'accept', look=1, qa='qa-pass', note='Synthetic fixture only.')
        task.update(job, 'confirm-model', look=1, note='Synthetic fixture only.')

    def exported(self, job, number=1):
        task.export(job)
        data = task.read(job)
        folder = task.handoff_directory(job, data, data['looks'][number - 1])
        return json.loads((folder / 'request.json').read_text())['prompt']

    def current_prompt(self, job, number=1):
        data = task.read(job)
        return task.handoff_prompt(data, data['looks'][number - 1], task.references(job, data, number))

    def test_legacy_series_continuation_keeps_first_request_and_recovers_retry(self):
        spec, frozen, context = self.legacy_series()
        first = dict(spec, count=1, shot_plan=task.shot_helper().subset(spec['shot_plan'], 1, series_role='series-first'))
        job = self.create(first, frozen, context)
        self.accepted(job)
        before = task.read(job)
        first_request = task.handoff_prompt(before, before['looks'][0], task.references(job, before, 1))
        fresh = library.prepare(spec)
        self.assertEqual(fresh['model_source_type'], 'new')
        data = task.update(job, 'continue-authorize', approval_id='next-five', note='Synthetic continuation.',
                           context=context, shot_plan=spec['shot_plan'], visual_plan=fresh)
        # The review repro saved six rows, then failed these checks/exports.
        task.check_evidence(job, task.read(job))
        self.exported(job, 2)
        self.assertEqual(self.current_prompt(job), first_request)
        self.assertEqual(data['looks'][0], before['looks'][0])
        self.assertNotIn('model_source_type', data['visual_plan'])
        self.assertEqual(data['visual_plan_history'][0]['plan'], frozen)
        self.assertEqual(data['attempts'], 1)

        self.reserve(job, 2)
        receipt = self.root / 'failure.txt'
        receipt.write_text('Synthetic terminal failure; no provider called.')
        task.update(job, 'failed', look=2, reason='Synthetic failure', failure_receipt=receipt)
        task.update(job, 'reconcile-failure', look=2, expected_attempt=1,
                    request_check_completed=True, note='Synthetic original-request check.')
        fresh['shots'][1]['composition'] = 'Revised second-shot composition.'
        retried = task.update(job, 'retry-authorize', look=2, expected_attempt=1, approval_id='retry-two',
                              note='Synthetic one-call retry.', visual_plan=fresh)
        self.assertNotIn('model_source_type', retried['visual_plan'])
        self.assertEqual(retried['attempts'], 2)
        task.check_evidence(job, task.read(job))
        self.assertIn('Revised second-shot composition.', self.exported(job, 2))
        self.assertEqual(self.current_prompt(job), first_request)

    def test_legacy_v1_continuation_keeps_rendering_contract(self):
        spec, frozen, context = self.legacy_series()
        full = task.shot_helper().default_plan('synthetic', spec['shot_plan']['coverage'])
        spec['shot_plan'] = full
        frozen['version'] = 1
        frozen['shots'][0].pop('shot_id')
        frozen['shots'][0]['pose'] = 1
        first = dict(spec, count=1, shot_plan=task.shot_helper().subset(full, 1))
        job = self.create(first, frozen, context)
        self.accepted(job)
        before = self.current_prompt(job)
        fresh = library.prepare({key: value for key, value in spec.items() if key != 'shot_plan'})
        data = task.update(job, 'continue-authorize', approval_id='next-five', note='Synthetic continuation.',
                           context=context, shot_plan=full, visual_plan=fresh)
        self.assertNotIn('model_source_type', data['visual_plan'])
        task.check_evidence(job, task.read(job))
        self.exported(job, 2)
        self.assertEqual(self.current_prompt(job), before)

    def test_legacy_preview_revision_retains_rendering_contract(self):
        spec, frozen, context = self.legacy_series()
        frozen = dict(frozen, shots=library.prepare(spec)['shots'])
        context['purpose'] = 'preview-grid'
        job = self.create(spec, frozen, context)
        data = task.read(job)
        revised_spec = copy.deepcopy(spec)
        revised_spec['shot_plan']['framing_guidance'] = 3
        revised = library.prepare(revised_spec)
        revised['photography']['scene'] = 'Revised quiet room.'
        candidate = task.preview_candidate(data, data['looks'][0], visual_plan=revised)
        self.assertNotIn('model_source_type', candidate['visual_plan'])
        self.assertNotIn('rendering_version', candidate['visual_plan'])
        self.assertFalse(any('framing' in cell for cell in candidate['visual_plan']['shots']))
        self.assertIn('Revised quiet room.', candidate['prompt'])

    def test_front_only_excludes_review_back_actions_but_keeps_shallow_turn(self):
        spec, _, _ = self.legacy_series()
        spec['entry_id'] = 'gothic-editorial'
        target = spec['shot_plan']['looks'][0]
        target['must_show'] = ['visible panels']
        before = copy.deepcopy(spec)
        report = recommend.recommend(spec, target['shot_id'], limit=60)
        ids = {item['pose_id'] for row in report['candidates'] for item in [row, *row['alternatives']]}
        self.assertNotIn('ge-shadow-turn', ids)
        self.assertNotIn('tt-floor-torso-twist', ids)
        self.assertIn('tt-turn-front-counter', ids)
        self.assertGreater(report['excluded']['needs-back'], 0)
        self.assertEqual(spec, before)
        target['garment_views'] = ['front', 'front-side', 'back']
        spec['shot_plan']['coverage'][0]['views'] = target['garment_views'][:]
        backed = recommend.recommend(spec, target['shot_id'], limit=60)
        backed_ids = {item['pose_id'] for row in backed['candidates'] for item in [row, *row['alternatives']]}
        self.assertIn('ge-shadow-turn', backed_ids)
        self.assertIn('tt-floor-torso-twist', backed_ids)

    def test_front_only_checks_every_action_field_and_evidence_limit(self):
        spec, _, _ = self.legacy_series()
        target = spec['shot_plan']['looks'][0]
        target['must_show'] = ['visible panels']
        card = library.card(spec['entry_id'])
        row = copy.deepcopy(card['pose_vocabulary'][0])
        row.update(id='synthetic-back-requirement', views=['front-side'])
        real_module = recommend._module
        for key, value in (('body', 'Walking away.'), ('hands', 'Hands visible from behind.'),
                           ('support', 'Support seen from behind.'), ('head', 'Look over the shoulder.'),
                           ('avoid_when', '后侧商品依据不足'), ('check', 'Requires back garment evidence.')):
            with self.subTest(field=key):
                candidate = dict(row, **{key: value})
                with patch.object(library, 'card', return_value=dict(card, pose_vocabulary=[candidate])), \
                     patch.object(recommend, '_module', side_effect=lambda name: library if name == 'visual_library' else real_module(name)):
                    report = recommend.recommend(spec, target['shot_id'], limit=60)
                self.assertNotIn(row['id'], {r['pose_id'] for r in report['candidates']})

    def test_detail_export_keeps_mixed_locked_facts_verbatim(self):
        spec, _, context = self.legacy_series()
        spec['model']['locked'] = ['Deep brown skin with a cheerful expression.',
                                  'Broad shoulders with a confident attitude.']
        spec['model']['adjustable'] = ['A playful expression sentinel.']
        spec['shot_plan'] = task.shot_helper().subset(spec['shot_plan'], 1, series_role='standalone')
        spec['shot_plan']['framing_guidance'] = 3
        spec['shot_plan']['looks'][0]['framing'] = 'detail'
        spec['count'] = 1
        frozen = library.prepare(spec)
        job = self.create(spec, frozen, context)
        task.check_evidence(job, task.read(job))
        prompt = self.exported(job)
        for fact in spec['model']['locked']:
            self.assertIn(fact, prompt)
        self.assertNotIn('expression sentinel', prompt)
        self.assertNotIn('Style persona', prompt)


if __name__ == '__main__':
    unittest.main()
