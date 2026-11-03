"""Legacy variety checks use the task's frozen vocabulary when preparing again."""
import copy
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

from tests.test_pose_plan_v2 import sample_plan
from tests import test_style_pose_pool as fixtures

library, task = fixtures.library, fixtures.task
ENTRIES = (*fixtures.Q6_POOL_IDS, 'resort-vacation', 'qipao-urban', 'romantic-bohemian')
CLI = fixtures.SKILL / 'scripts/visual_library.py'


def without_pool(card):
    card = copy.deepcopy(card)
    for key in ('pose_pool', 'pose_pool_snapshot', 'pose_vocabulary', 'action_tendency'):
        card.pop(key, None)
    return card


class FrozenVocabularyPreparationTests(unittest.TestCase):
    setUp = fixtures.StylePosePoolTests.setUp

    def spec(self, entry='neo-chinese', *, with_ids=False, output_form='human'):
        spec = fixtures.StylePosePoolTests.spec(self, entry)
        plan = sample_plan(back=False)
        plan.update(variety_checks=1, framing_guidance=2)
        plan['coverage'][0]['sha256'] = self.sha
        for n, cell in enumerate(plan['looks']):
            cell.update(reference_sha256s=[self.sha], scene='Studio area ' + str(n % 3))
        if with_ids:
            rows = [row for row in library.card(entry)['pose_vocabulary']
                    if row['family'] != 'close' and 'back' not in row['views']]
            for cell, row in zip(plan['looks'][:5], rows):
                cell.update(pose_id=row['id'], body_action=row['body'], hands=row['hands'],
                            support=row['support'], garment_views=row['views'])
        spec.update(count=9, shot_plan=plan, output_form=output_form)
        return spec

    def test_no_pool_legacy_tasks_reprepare_via_cli_after_card_gains_pool(self):
        for entry in ENTRIES:
            for output_form in ('human', 'faceless'):
                with self.subTest(entry=entry, output_form=output_form):
                    spec = self.spec(entry, output_form=output_form)
                    # Recreate the old no-pool card shape only at initial freeze.
                    # The ledger, export and later CLI preparation use real code.
                    with patch.object(library, 'card', return_value=without_pool(library.card(entry))):
                        frozen = library.prepare(spec)
                    self.assertNotIn('pose_vocabulary', frozen['style']['primary']['snapshot'])
                    self.assertTrue(all('pose_id' not in cell for cell in spec['shot_plan']['looks']))
                    job = self.root / (entry + '-' + output_form)
                    context = dict(outfit='synthetic-legacy-pool', style=entry, mode='C',
                                   output_form=output_form, size=[20, 30], first_pose=1, purpose='preview-grid')
                    task.create(job, [self.source], None, [20, 30], model=spec['model'], context=context,
                                shot_plan=spec['shot_plan'], visual_plan=frozen, workflow_version=0)
                    task.export(job)
                    before = {path.relative_to(job): path.read_bytes() for path in job.rglob('*') if path.is_file()}
                    source, output = self.root / 'prepare.json', self.root / (job.name + '-prepared.json')
                    source.write_text(json.dumps(spec))
                    process = subprocess.run([sys.executable, str(CLI), 'prepare', '--task', str(job),
                                              '--spec', str(source), '--output', str(output)],
                                             capture_output=True, text=True)
                    self.assertEqual(process.returncode, 0, process.stderr)
                    self.assertEqual(json.loads(process.stdout)['image_calls'], 0)
                    prepared = json.loads(output.read_text())
                    self.assertEqual(prepared['shots'], frozen['shots'])
                    self.assertEqual(prepared['styling'], frozen['styling'])
                    self.assertEqual({path.relative_to(job): path.read_bytes() for path in job.rglob('*') if path.is_file()}, before)
                    self.assertEqual(task.read(job)['attempts'], 0)
                    self.assertIsNone(task.read(job)['authorization'])

    def test_frozen_vocabulary_still_requires_pose_ids_when_current_pool_is_removed(self):
        spec = self.spec(with_ids=True)
        frozen = library.prepare(spec)
        for cell in spec['shot_plan']['looks']:
            cell.pop('pose_id', None)
        current = library.card(spec['entry_id'])
        for card in (current, without_pool(current)):
            with self.subTest(current_has_pool='pose_pool' in card), patch.object(library, 'card', return_value=card):
                with self.assertRaisesRegex(ValueError, 'at least 5 looks must carry a pose_id'):
                    library.prepare(spec, frozen_visual_plan=frozen)

    def test_frozen_ids_remain_valid_after_current_vocabulary_changes(self):
        spec = self.spec(with_ids=True)
        frozen = library.prepare(spec)
        before = copy.deepcopy(frozen)
        current = without_pool(library.card(spec['entry_id']))
        current['pose_vocabulary'] = copy.deepcopy(frozen['style']['primary']['snapshot']['pose_vocabulary'])
        for row in current['pose_vocabulary']:
            row['id'] = 'later-' + row['id']
        with patch.object(library, 'card', return_value=current):
            prepared = library.prepare(spec, frozen_visual_plan=frozen)
        self.assertEqual(prepared['shots'], frozen['shots'])
        self.assertEqual(frozen, before)

    def test_current_only_pose_ids_are_rejected_against_frozen_vocabulary(self):
        spec = self.spec(with_ids=True)
        frozen = library.prepare(spec)
        current = without_pool(library.card(spec['entry_id']))
        current['pose_vocabulary'] = copy.deepcopy(frozen['style']['primary']['snapshot']['pose_vocabulary'])
        old_id = spec['shot_plan']['looks'][0]['pose_id']
        for row in current['pose_vocabulary']:
            if row['id'] == old_id:
                row['id'] = 'later-' + old_id
        spec['shot_plan']['looks'][0]['pose_id'] = 'later-' + old_id
        with patch.object(library, 'card', return_value=current):
            with self.assertRaisesRegex(ValueError, 'pose_id must be one of the style pose ids'):
                library.prepare(spec, frozen_visual_plan=frozen)

    def test_new_tasks_with_current_pool_still_require_pose_ids(self):
        for entry in ENTRIES:
            for output_form in ('human', 'faceless'):
                with self.subTest(entry=entry, output_form=output_form):
                    with self.assertRaisesRegex(ValueError, 'at least 5 looks must carry a pose_id'):
                        library.prepare(self.spec(entry, output_form=output_form))


if __name__ == '__main__':
    unittest.main()
