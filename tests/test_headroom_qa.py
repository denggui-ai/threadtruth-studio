"""WP-16 C3: delivery accept records a head-top margin measurement; it never changes QA, state or notes."""
import random, sys, tempfile, unittest
import unittest.mock
from pathlib import Path

from PIL import Image, ImageDraw

import tests.test_nine_task as nine

GRAY = (235, 235, 235)


def figure(path, top=None, size=(60, 40)):
    image = Image.new('RGB', size, GRAY)
    if top is not None:
        ImageDraw.Draw(image).rectangle([24, top, 36, size[1] - 1], fill=(30, 30, 40))
    image.save(path)
    return path


class HeadroomMeasureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.task = nine.task

    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup); self.dir = Path(temp.name)

    def test_tight_and_loose_margins_measure_in_expected_ranges(self):
        tight = self.task.headroom_check(figure(self.dir / 'a.png', 1))
        loose = self.task.headroom_check(figure(self.dir / 'b.png', 8))
        self.assertEqual(tight['status'], 'measured'); self.assertLess(tight['ratio'], 0.05)
        self.assertEqual(loose['status'], 'measured'); self.assertGreater(loose['ratio'], 0.15)

    def test_plain_and_noisy_images_are_uncertain(self):
        self.assertEqual(self.task.headroom_check(figure(self.dir / 'plain.png')), {'status': 'uncertain', 'reason': 'no-subject-row'})
        random.seed(1)
        noise = Image.new('RGB', (60, 40))
        noise.putdata([tuple(random.randrange(256) for _ in range(3)) for _ in range(60 * 40)])
        noise.save(self.dir / 'noise.png')
        self.assertEqual(self.task.headroom_check(self.dir / 'noise.png'), {'status': 'uncertain', 'reason': 'busy-top-corners'})

    def test_missing_pillow_is_unavailable(self):
        path = figure(self.dir / 'a.png', 1)
        with unittest.mock.patch.dict(sys.modules, {'PIL': None}):
            self.assertEqual(self.task.headroom_check(path), {'status': 'unavailable'})


class HeadroomLedgerTests(unittest.TestCase):
    def setUp(self):
        self.nt = nine.NineTaskTests('create')
        self.nt.setUp()
        self.addCleanup(self.nt.doCleanups)
        self.task = nine.task

    def accept(self, top, *, preview=False, patch=None):
        self.nt.create(preview=preview)
        self.task.update(self.nt.job, 'authorize', limit=1 if preview else 9, note='Synthetic request authority.')
        self.nt.reserve(1)
        self.task.update(self.nt.job, 'returned', look=1, file=figure(self.nt.root / 'out.png', top))
        note = 'Synthetic ledger review, no visual assertion.'
        if patch:
            # check_evidence also decodes images with Pillow, so it is bypassed for this one call only.
            with unittest.mock.patch.dict(sys.modules, patch), unittest.mock.patch.object(self.task, 'check_evidence'):
                self.task.update(self.nt.job, 'accept', look=1, qa='qa-pass', note=note)
        else:
            self.task.update(self.nt.job, 'accept', look=1, qa='qa-pass', note=note)
        row = self.task.read(self.nt.job)['looks'][0]
        self.assertEqual((row['state'], row['qa'], row['qa_note']), ('accepted', 'qa-pass', note))
        return row

    def test_delivery_tight_margin_is_recorded_without_blocking(self):
        headroom = self.accept(1)['headroom']
        self.assertEqual(headroom['status'], 'measured'); self.assertLess(headroom['ratio'], 0.05)
        self.assertNotIn('minimum', headroom)

    def test_delivery_loose_margin_is_recorded(self):
        self.assertGreater(self.accept(8)['headroom']['ratio'], 0.15)

    def test_preview_accept_is_not_measured(self):
        self.assertNotIn('headroom', self.accept(1, preview=True))

    def test_plain_background_is_recorded_as_uncertain(self):
        self.assertEqual(self.accept(None)['headroom']['status'], 'uncertain')

    def test_missing_pillow_records_unavailable_and_still_accepts(self):
        self.assertEqual(self.accept(1, patch={'PIL': None})['headroom'], {'status': 'unavailable'})


if __name__ == '__main__':
    unittest.main()
