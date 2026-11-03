"""Linked corrections retain the generated person and the parent's frozen plan."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from PIL import Image
from tests import test_aesthetic_run6 as fixtures

library, task = fixtures.library, fixtures.task
ROOT = Path(__file__).resolve().parents[1]


class AestheticRun8Tests(unittest.TestCase):
    setUp = fixtures.AestheticRun6Tests.setUp

    def rejected_parent(self, *, styling=True, framing=3, name='job'):
        spec = fixtures.spec_for(self.sha)
        cells = spec['shot_plan']['looks']
        first, custom = copy.deepcopy(cells[0]), copy.deepcopy(cells[4])
        cells[0] = dict(custom, slot=first['slot'], shot_id=first['shot_id'])
        cells[4] = dict(first, slot=custom['slot'], shot_id=custom['shot_id'])
        spec['shot_plan']['framing_guidance'] = framing
        # Still four pool poses among seven body shots; the first is custom.
        visual = library.prepare(spec)
        if not styling:
            visual['styling'] = [line for line in visual['styling'] if line != fixtures.STYLING_LINE]
        for cell in visual['shots'][7:]:
            cell['garment_focus'] = dict(description='Only the source-backed cuff.',
                                         keep=['Original blue colour and cuff.'])
        context = dict(outfit='synthetic-run8', style=spec['entry_id'], mode='C', output_form='human',
                       size=[20, 30], first_pose=1, purpose='delivery')
        job = self.root / name
        task.create(job, [self.source], None, [20, 30], model=spec['model'], context=context,
                    shot_plan=spec['shot_plan'], visual_plan=visual)
        task.update(job, 'authorize', limit=1, note='One synthetic first shot.',
                    decision=dict(style=spec['entry_id'], path='direct', image_count=9,
                                  note='Confirm the complete synthetic plan.'))
        task.update(job, 'reserve', look=1, ready=True, refs=task.reference_hashes(job, 1),
                    expected_plan_sha256=task.plan_fingerprint(task.read(job)))
        output = self.root / (name + '-output.png')
        Image.new('RGB', (20, 30), 'green').save(output)
        task.update(job, 'returned', look=1, file=output)
        data = task.read(job)
        review = {key: dict(expected='Synthetic expected value.', observed='Synthetic result.',
                            result='unmet' if key == 'goal' else 'met')
                  for key in ('goal', 'garment', 'photography', 'identity', 'anatomy')}
        review['goal']['expected'] = task.workflow_helper().goal(data, data['looks'][0])
        task.update(job, 'reject', look=1, note='Correct the garment while retaining the generated person.', review=review)
        data = task.read(job)
        child_spec = copy.deepcopy(spec)
        child_spec.update(count=1, first_pose=1, shot_plan=task.shot_helper().subset(data['shot_plan'], 1))
        child_spec['model']['source_type'] = 'ai'
        child_spec['inventory'].append(dict(role='identity-reference', sha256=task.digest(output)))
        return job, child_spec, output

    def correction(self, job, spec, visual, output):
        return dict(references=[dict(path=str(self.source), role='garment-source'),
                                dict(path=str(output), role='identity-reference')],
                    size=[20, 30], identity=True, model=spec['model'], context=task.read(job)['context'],
                    shot_plan=spec['shot_plan'], visual_plan=visual, count=1)

    def check_revision(self, job, spec, visual, output):
        parent = task.read(job)
        frozen = parent['visual_plan']
        original_spec = copy.deepcopy(spec)
        child = task.create_revision(job, 1, self.correction(job, spec, visual, output),
                                     approval_id='retain-first', note='One authorized synthetic correction.',
                                     identity_note='Retain the actual generated first person.')
        child_root = job / child['revision_origin']['path']
        task.check_evidence(child_root, task.read(child_root))
        task.check_evidence(job, task.read(job))
        self.assertEqual(child['model']['source_type'], 'ai')
        self.assertEqual(child['shot_plan'], task.shot_helper().subset(parent['shot_plan'], 1))
        self.assertEqual(child['visual_plan']['shots'], frozen['shots'][:1])
        self.assertEqual(child['visual_plan']['styling'], frozen['styling'])
        self.assertEqual(child['visual_plan'].get('rendering_version'), frozen.get('rendering_version'))
        self.assertEqual(child['visual_plan'].get('model_source_type'),
                         'ai' if 'model_source_type' in frozen else None)
        self.assertEqual(task.read(job)['visual_plan'], frozen)
        self.assertEqual(spec, original_spec)
        self.assertEqual(child['attempts'], 0)
        self.assertEqual(task.read(job)['attempts'], 1)

    def test_review_r5_linked_custom_first_retains_frozen_contract(self):
        for styling, framing in ((True, 3), (False, 3), (False, 2)):
            with self.subTest(styling=styling, framing=framing):
                job, spec, output = self.rejected_parent(styling=styling, framing=framing,
                                                         name=f'job-{styling}-{framing}')
                frozen = task.read(job)['visual_plan']
                before = copy.deepcopy(frozen)
                visual = library.prepare(spec, frozen_visual_plan=frozen)
                self.assertEqual(frozen, before)
                self.check_revision(job, spec, visual, output)

    def test_review_r5_linked_prepare_cli_uses_parent_task(self):
        job, spec, output = self.rejected_parent()
        before = (job / 'task.json').read_bytes()
        source, prepared = self.root / 'prepare.json', self.root / 'prepared.json'
        source.write_text(json.dumps(spec))
        process = subprocess.run([sys.executable, str(ROOT / 'skills/threadtruth-studio/scripts/visual_library.py'),
                                  'prepare', '--task', str(job), '--spec', str(source), '--output', str(prepared)],
                                 capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual((job / 'task.json').read_bytes(), before)
        self.check_revision(job, spec, json.loads(prepared.read_text()), output)

    def test_prepare_rejects_all_other_model_source_transitions(self):
        for before, after in (('new', 'real'), ('ai', 'new'), ('ai', 'real'), ('real', 'new'), ('real', 'ai')):
            with self.subTest(before=before, after=after):
                spec = fixtures.spec_for(self.sha)
                spec['model'].update(source_type=before, consent_note='Synthetic consent fixture.')
                frozen = library.prepare(spec)
                spec['model']['source_type'] = after
                with self.assertRaisesRegex(ValueError, 'cannot change its frozen visual model_source_type'):
                    library.prepare(spec, frozen_visual_plan=frozen)

    def test_generic_rendering_inheritance_still_rejects_source_change(self):
        spec = fixtures.spec_for(self.sha)
        frozen = library.prepare(spec)
        spec['model']['source_type'] = 'ai'
        candidate = library.prepare(spec)
        with self.assertRaisesRegex(ValueError, 'cannot change its frozen visual model_source_type'):
            task.inherit_visual_rendering(candidate, frozen)

    def test_prepare_without_parent_still_enforces_new_task_quota(self):
        _, spec, _ = self.rejected_parent()
        with self.assertRaisesRegex(ValueError, r'at least 1 of 1 non-detail.*found 0'):
            library.prepare(spec)

    def test_linked_preparation_does_not_bypass_identity_provenance(self):
        job, spec, output = self.rejected_parent()
        visual = library.prepare(spec, frozen_visual_plan=task.read(job)['visual_plan'])
        wrong = self.root / 'other-person.png'
        Image.new('RGB', (20, 30), 'purple').save(wrong)
        for reference, identity_note in ((wrong, 'Retain the person.'), (output, '')):
            with self.subTest(reference=reference.name, identity_note=identity_note):
                with self.assertRaisesRegex(ValueError, 'Retain the exact generated first person'):
                    task.create_revision(job, 1, self.correction(job, spec, visual, reference),
                                         approval_id='invalid-identity', note='One synthetic correction.',
                                         identity_note=identity_note)
        self.assertFalse(task.read(job).get('linked_revisions'))
        self.assertFalse((job / 'revisions' / 'invalid-identity').exists())


if __name__ == '__main__':
    unittest.main()
