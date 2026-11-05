"""Existing tasks retain their contract through preparation, revision and continuation."""
import copy
import hashlib
import inspect
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from PIL import Image
from tests import test_aesthetic_run6 as fixtures
from tests.test_style_pose_pool import use_current_pool_in_fixture

library, task = fixtures.library, fixtures.task
ROOT = Path(__file__).resolve().parents[1]
STYLING = fixtures.STYLING_LINE


class AestheticRun7Tests(unittest.TestCase):
    setUp = fixtures.AestheticRun6Tests.setUp

    def legacy(self, framing=3, pool=2):
        spec = fixtures.spec_for(self.sha, library_count=pool)
        spec['shot_plan']['framing_guidance'] = framing
        source = json.loads((ROOT / 'tests/fixtures/aesthetic-run6-prompts.json').read_text())
        frozen = use_current_pool_in_fixture(copy.deepcopy(source['visual_plan']))
        frozen['garment']['source_sha256s'] = [self.sha]
        if framing == 2:
            for key in ('rendering_version', 'model_source_type'):
                frozen.pop(key, None)
            for cell in frozen['shots']:
                cell.pop('framing', None)
        return spec, frozen

    def create(self, spec, frozen, purpose='preview-grid', name='job'):
        job = self.root / name
        context = dict(outfit='synthetic-run7', style=spec['entry_id'], mode='C', output_form='human',
                       size=[20, 30], first_pose=1, purpose=purpose)
        # Only seed the historical task without today's new-task gate. All later
        # preparation, ledger events, validation and exports run without mocks.
        with patch.object(task.shot_helper(), 'check_new_pose_pool', create=True):
            task.create(job, [self.source], None, [20, 30], model=spec['model'], context=context,
                        shot_plan=spec['shot_plan'], visual_plan=frozen, workflow_version=0)
        data = task.read(job)
        data.pop('prompt_render', None)  # historical tasks predate the dedupe render marker
        task.save(job, data)
        return job

    def reprepare(self, spec, frozen):
        # On the review baseline, exercise the original prepare instead of failing
        # merely because the frozen-plan keyword has not been introduced yet.
        kw = {'frozen_visual_plan': frozen} if 'frozen_visual_plan' in inspect.signature(library.prepare).parameters else {}
        return library.prepare(spec, **kw)

    def returned(self, job, *, accepted=False):
        task.update(job, 'authorize', limit=1, note='Synthetic ledger fixture only.')
        task.update(job, 'reserve', look=1, ready=True, refs=task.reference_hashes(job, 1),
                    expected_plan_sha256=task.plan_fingerprint(task.read(job)))
        output = self.root / 'output.png'
        Image.new('RGB', (20, 30), 'green').save(output)
        task.update(job, 'returned', look=1, file=output)
        if accepted:
            task.update(job, 'accept', look=1, qa='qa-pass', note='Synthetic fixture only.')
            task.update(job, 'confirm-model', look=1, note='Synthetic fixture only.')
        else:
            task.update(job, 'reject', look=1, note='Revise the synthetic scene only.')

    def exported(self, job):
        task.check_evidence(job, task.read(job))
        task.export(job)
        data = task.read(job)
        prompts = []
        for row in data['looks']:
            prompt = task.handoff_prompt(data, row, task.references(job, data, row['number'])).encode()
            path = task.handoff_directory(job, data, row) / 'prompt.txt'
            if path.exists():
                self.assertEqual(path.read_bytes(), prompt)
            prompts.append(prompt)
        return prompts

    def revise(self, spec, frozen, *, fresh=False):
        job = self.create(spec, frozen)
        self.returned(job)
        revised_spec = copy.deepcopy(spec)
        revised_spec['overrides'] = dict(photography=dict(scene='Revised quiet room.'))
        revised = library.prepare(revised_spec) if fresh else self.reprepare(revised_spec, frozen)
        prompt = library._visual().compile_prompt(revised)
        original = copy.deepcopy(revised)
        before = task.read(job)
        reviewed = task.update(job, 'revise-preview', look=1, visual_plan=revised, prompt=prompt,
                               expected_output_sha256=before['looks'][0]['output']['sha256'],
                               note='Synthetic scene-only revision.')
        candidate = reviewed['preview_revision']['candidate']
        self.assertEqual(candidate['visual_plan']['styling'], frozen['styling'])
        self.assertEqual(candidate['shot_plan'], before['shot_plan'])
        task.update(job, 'retry-authorize', look=1, expected_attempt=1, approval_id='retry-scene',
                    visual_plan=revised, prompt=prompt, note='One synthetic scene retry.')
        self.assertEqual(revised, original)
        self.assertEqual(task.read(job)['attempts'], 1)
        result = self.exported(job)[0]
        self.assertIn(b'Revised quiet room.', result)
        self.assertEqual(task.read(job)['looks'][0]['history'][0]['prompt'], before['looks'][0]['prompt'])
        return result

    def continue_series(self, spec, frozen, *, fresh=False):
        first = dict(spec, count=1, shot_plan=task.shot_helper().subset(spec['shot_plan'], 1, series_role='series-first'))
        first_visual = task.visual_helper().bind_shots(frozen, first['shot_plan'])
        job = self.create(first, first_visual, purpose='delivery')
        self.returned(job, accepted=True)
        before = task.read(job)
        first_prompt = self.exported(job)[0]
        revised = library.prepare(spec) if fresh else self.reprepare(spec, before['visual_plan'])
        prompts = [library._visual().compile_prompt(revised, n) for n in range(2, 10)]
        data = task.update(job, 'continue-authorize', context=before['context'], approval_id='remaining-eight',
                           shot_plan=spec['shot_plan'], visual_plan=revised, prompts=prompts,
                           note='Synthetic remaining-image authorization.')
        self.assertEqual(data['looks'][0], before['looks'][0])
        self.assertEqual(data['visual_plan'], frozen)
        self.assertEqual(data['attempts'], 1)
        result = self.exported(job)
        self.assertEqual(result[0], first_prompt)
        return result

    def test_review_r4_under_quota_scene_revision(self):
        self.revise(*self.legacy())

    def test_review_r4_under_quota_continue_authorize(self):
        self.continue_series(*self.legacy())

    def test_review_r4_explicit_compiled_prompt_revision_and_retry(self):
        # Also cover older callers which prepared without the task context.
        self.revise(*self.legacy(pool=4), fresh=True)

    def test_explicit_continuation_prompts_keep_the_existing_contract(self):
        self.continue_series(*self.legacy(pool=4), fresh=True)

    def test_delivery_retry_with_explicit_prompt_keeps_other_shots(self):
        spec, frozen = self.legacy(pool=4)
        self.continue_series(spec, frozen)
        job = self.root / 'job'
        task.update(job, 'reserve', look=2, ready=True, refs=task.reference_hashes(job, 2),
                    expected_plan_sha256=task.plan_fingerprint(task.read(job)))
        receipt = self.root / 'failure.txt'
        receipt.write_text('Synthetic failure; no provider called.')
        task.update(job, 'failed', look=2, reason='Synthetic failure.', failure_receipt=receipt)
        task.update(job, 'reconcile-failure', look=2, expected_attempt=1,
                    request_check_completed=True, note='Synthetic request checked.')
        before = task.read(job)
        revised = library.prepare(spec)
        revised['shots'][1]['composition'] = 'Revised second-shot composition.'
        prompt = library._visual().compile_prompt(revised, 2)
        data = task.update(job, 'retry-authorize', look=2, expected_attempt=1, approval_id='retry-two',
                           visual_plan=revised, prompt=prompt, note='One synthetic retry.')
        self.assertEqual(data['visual_plan']['styling'], frozen['styling'])
        self.assertEqual(data['looks'][0], before['looks'][0])
        self.assertEqual(data['looks'][2:], before['looks'][2:])
        self.assertIn(b'Revised second-shot composition.', self.exported(job)[1])

    def test_existing_styling_is_not_removed_by_explicit_revision(self):
        spec, frozen = self.legacy(pool=4)
        frozen['styling'].append(STYLING)
        job = self.create(spec, frozen)
        data = task.read(job)
        revised = copy.deepcopy(frozen)
        revised['photography']['scene'] = 'Revised quiet room.'
        revised['styling'].remove(STYLING)
        candidate = task.preview_candidate(data, data['looks'][0], visual_plan=revised,
                                            prompt=library._visual().compile_prompt(revised))
        self.assertEqual(candidate['visual_plan']['styling'], frozen['styling'])
        self.assertEqual(candidate['prompt'].count(STYLING), 1)

    def test_beta18_scene_revision_matches_d7d7e66_bytes(self):
        expected = json.loads((ROOT / 'tests/fixtures/aesthetic-run7-digests.json').read_text())
        self.assertEqual(expected['baseline'], 'd7d7e66')
        actual = self.revise(*self.legacy(framing=2))
        self.assertEqual(hashlib.sha256(actual).hexdigest(), expected['preview_revision'])

    def test_beta18_continuation_matches_d7d7e66_bytes(self):
        expected = json.loads((ROOT / 'tests/fixtures/aesthetic-run7-digests.json').read_text())
        self.assertEqual(expected['baseline'], 'd7d7e66')
        actual = self.continue_series(*self.legacy(framing=2))
        self.assertEqual([hashlib.sha256(p).hexdigest() for p in actual], expected['continuation'])

    def test_existing_task_prepare_cli_keeps_frozen_plan_and_ledger(self):
        spec, frozen = self.legacy(framing=2)
        job = self.create(spec, frozen)
        before = (job / 'task.json').read_bytes()
        source, output = self.root / 'prepare.json', self.root / 'prepared.json'
        source.write_text(json.dumps(spec))
        process = subprocess.run([sys.executable, str(ROOT / 'skills/lookset/scripts/visual_library.py'),
                                  'prepare', '--task', str(job), '--spec', str(source), '--output', str(output)],
                                 capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(output.read_text()), frozen)
        self.assertEqual((job / 'task.json').read_bytes(), before)

    def test_frozen_styling_presence_is_retained_during_reprepare(self):
        spec, frozen = self.legacy(pool=4)
        for present in (False, True):
            with self.subTest(present=present):
                old = copy.deepcopy(frozen)
                if present:
                    old['styling'].append(STYLING)
                prepared = self.reprepare(spec, old)
                self.assertEqual(prepared['styling'], old['styling'])

    def test_mismatched_explicit_prompt_is_still_rejected(self):
        spec, frozen = self.legacy(pool=4)
        job = self.create(spec, frozen)
        data = task.read(job)
        revised = library.prepare(spec)
        revised['photography']['scene'] = 'Reviewed room.'
        wrong = copy.deepcopy(revised)
        wrong['photography']['scene'] = 'Unreviewed room.'
        for prompt in (library._visual().compile_prompt(wrong),
                       library._visual().compile_prompt(revised) + 'Unreviewed instruction.'):
            with self.subTest(prompt=prompt[-50:]), self.assertRaises(ValueError):
                task.preview_candidate(data, data['looks'][0], visual_plan=revised, prompt=prompt)


if __name__ == '__main__':
    unittest.main()
