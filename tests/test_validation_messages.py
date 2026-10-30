"""Validation errors must name the JSON path, the expected shape and the offending value (WP-12).

Session-d of the WP-8a walk-through produced zero images because the assistant could not repair
`Declare distinct visible garment features for the shot purpose` or `[Errno 17] File exists`.
Every case here is a plan the runtime already rejected before WP-12; only the wording is new.
"""
import copy, hashlib, importlib.util, json, re, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/threadtruth-studio/scripts'
_SPEC = importlib.util.spec_from_file_location('validation_messages_shot_plan', SCRIPTS / 'shot_plan.py')
shot = importlib.util.module_from_spec(_SPEC); _SPEC.loader.exec_module(shot)

FRONT = 'a' * 64
BACK = 'b' * 64
PATH = re.compile(r'^(shot_plan|context|count|references|real_face_plan|series_role|looks\[\*\]|Version-2|Preview)')


def inventory():
    return [dict(sha256=FRONT, role='garment-source'), dict(sha256=BACK, role='garment-source')]


def plan(count=9):
    coverage = [dict(sha256=FRONT, views=['front', 'detail'], usable=True, same_sku=True, note='Synthetic front.'),
                dict(sha256=BACK, views=['back'], usable=True, same_sku=True, note='Synthetic back.')]
    looks = [dict(slot=n, shot_id='s-' + str(n), display_goal='Show the hem.', must_show=['collar', 'hem'],
                  reason='Hands clear the print.', body_action='Stand with a small weight shift.',
                  hands='Both hands low.', support='Both feet on the floor.', framing='full-body',
                  garment_views=['front'], reference_sha256s=[FRONT]) for n in range(1, count + 1)]
    return dict(version=2, sku='top', route='A', coverage=coverage, looks=looks,
                selected_shot_ids=[x['shot_id'] for x in looks], series_role='series' if count > 1 else 'standalone')


class ValidationMessageTests(unittest.TestCase):
    def validate(self, p, **kw):
        context = kw.pop('context', dict(first_pose=1, output_form='human', purpose='delivery'))
        return shot.validate(p, kw.pop('refs', inventory()), context=context, count=kw.pop('count', len(p['selected_shot_ids'])),
                             model_source=kw.pop('model_source', 'new'), **kw)

    def test_valid_plan_still_passes_unchanged(self):
        p = plan()
        self.assertEqual(self.validate(p), p)
        self.assertEqual(self.validate(plan(1)), plan(1))

    def test_session_d_string_must_show_names_path_shape_example_and_value(self):
        p = plan(); p['looks'][1]['must_show'] = '衬衫、裤腿与鞋'
        with self.assertRaises(ValueError) as cm:
            self.validate(p)
        msg = str(cm.exception)
        self.assertTrue(msg.startswith('shot_plan.looks[1].must_show must be a nonempty list of distinct strings'), msg)
        self.assertIn('e.g. ["collar", "hem"]', msg)
        self.assertIn("got '衬衫、裤腿与鞋'", msg)

    def test_every_split_check_reports_one_field_with_path_and_value(self):
        def mutate(fn):
            p = plan(); fn(p); return p
        cases = {
            'shot_plan missing key': (mutate(lambda p: p.pop('series_role')), r'^shot_plan must have exactly the keys .*; missing: series_role; unexpected: none$'),
            'sku empty': (mutate(lambda p: p.update(sku='')), r"^shot_plan\.sku must be a nonempty single line; got ''$"),
            'route letter': (mutate(lambda p: p.update(route='C')), r"^shot_plan\.route must be \"A\" or \"B\"; got 'C'$"),
            'route vs coverage': (mutate(lambda p: p.update(route='B')), r'^shot_plan\.route must be "A" because usable same_sku back coverage is present; got \'B\'$'),
            'coverage key set': (mutate(lambda p: p['coverage'][0].pop('note')), r'^shot_plan\.coverage\[0\] must have exactly the keys note, same_sku, sha256, usable, views; got same_sku, sha256, usable, views$'),
            'coverage usable type': (mutate(lambda p: p['coverage'][1].update(usable='yes')), r"^shot_plan\.coverage\[1\]\.usable must be true or false; got 'yes'$"),
            'coverage view word': (mutate(lambda p: p['coverage'][0].update(views=['front', 'side'])), r"^shot_plan\.coverage\[0\]\.views must only contain front, front-side, back, detail; got 'side'$"),
            'no usable front': (mutate(lambda p: p['coverage'][0].update(usable=False)), r'^shot_plan\.coverage must include a usable same_sku entry whose views contain "front"; usable views: back$'),
            'look key set': (mutate(lambda p: p['looks'][2].pop('hands')), r'^shot_plan\.looks\[2\] must have exactly the keys .*; missing: hands; unexpected: none$'),
            'slot order': (mutate(lambda p: p['looks'][3].update(slot=9)), r'^shot_plan\.looks\[3\]\.slot must be 4 \(logical slots stay complete and ordered\); got 9$'),
            'shot_id chars': (mutate(lambda p: p['looks'][0].update(shot_id='bad id')), r"^shot_plan\.looks\[0\]\.shot_id must be 1-80 letters, digits, \"_\" or \"-\" starting with a letter or digit; got 'bad id'$"),
            'shot_id duplicate': (mutate(lambda p: p['looks'][5].update(shot_id='s-1')), r'^shot_plan\.looks\[5\]\.shot_id must be unique; "s-1" is already used by an earlier shot$'),
            'display_goal blank': (mutate(lambda p: p['looks'][0].update(display_goal='  ')), r"^shot_plan\.looks\[0\]\.display_goal must be a nonempty single line without POSE/Shot headers; got '  '$"),
            'must_show empty list': (mutate(lambda p: p['looks'][0].update(must_show=[])), r'^shot_plan\.looks\[0\]\.must_show must be a nonempty list of distinct strings, e\.g\. \["collar", "hem"\]; got list of 0$'),
            'must_show duplicate': (mutate(lambda p: p['looks'][0].update(must_show=['hem', 'hem'])), r"^shot_plan\.looks\[0\]\.must_show must not repeat an item; got list of 2$"),
            'framing word': (mutate(lambda p: p['looks'][0].update(framing='portrait')), r"^shot_plan\.looks\[0\]\.framing must be one of full-body, half-body, knee-up, detail; got 'portrait'$"),
            'gaze missing when head set': (mutate(lambda p: p['looks'][0].update(head='three-quarter')), r'^shot_plan\.looks\[0\]\.gaze must be a nonempty single line on every shot once any shot declares head/gaze; got None$'),
            'reference not usable': (mutate(lambda p: p['looks'][0].update(reference_sha256s=['c' * 64])), r"^shot_plan\.looks\[0\]\.reference_sha256s must only name usable same_sku coverage hashes; got 'ccc.*; usable: aaa.*, bbb.*$"),
            'views not covered': (mutate(lambda p: p['looks'][0].update(garment_views=['back'])), r'^shot_plan\.looks\[0\]\.garment_views must be covered by its reference_sha256s coverage; not covered: back \(covered: detail, front\)$'),
            'selected count': (mutate(lambda p: p['selected_shot_ids'].pop()), r'^shot_plan\.selected_shot_ids must have exactly 9 entries \(the active execution count\); got 8$'),
            'selected unknown': (mutate(lambda p: p['selected_shot_ids'].__setitem__(0, 'ghost')), r'^shot_plan\.selected_shot_ids must only name looks\[\*\]\.shot_id values; unknown: ghost$'),
            'series_role word': (mutate(lambda p: p.update(series_role='all')), r"^shot_plan\.series_role must be \"standalone\", \"series-first\" or \"series\"; got 'all'$"),
        }
        for name, (bad, pattern) in cases.items():
            with self.subTest(name):
                kw = {}
                if name == 'selected count':
                    kw['count'] = 9
                with self.assertRaises(ValueError) as cm:
                    self.validate(bad, **kw)
                self.assertRegex(str(cm.exception), pattern)

    def test_context_errors_name_the_context_field(self):
        p = plan()
        with self.assertRaisesRegex(ValueError, r'^context\.first_pose must equal the first selected shot slot 1; got 3$'):
            self.validate(p, context=dict(first_pose=3, output_form='human', purpose='delivery'))
        with self.assertRaisesRegex(ValueError, r"^Preview must show the complete frozen series: series_role must be \"series\" when purpose is preview-grid; got 'standalone'$"):
            self.validate(plan(1), context=dict(first_pose=1, output_form='human', purpose='preview-grid'))

    def test_prepare_refuses_existing_output_with_reason_and_free_path(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup); root = Path(temp.name)
        h = hashlib.sha256(b'synthetic').hexdigest()
        looks = [dict(slot=i, shot_id='qs-' + str(i), display_goal='Show the set', must_show=['hem'], reason='Front supports it.',
                      body_action='Stand naturally ' + str(i), hands='Hands relaxed', support='Both feet grounded', framing='full-body',
                      garment_views=['front'], reference_sha256s=[h]) for i in range(1, 10)]
        sp = dict(version=2, sku='qs', route='B', coverage=[dict(sha256=h, views=['front'], usable=True, same_sku=True, note='Synthetic front')],
                  looks=looks, selected_shot_ids=[l['shot_id'] for l in looks], series_role='series')
        prep = dict(entry_id='french-effortless', garment=dict(description='Synthetic red garment.', keep=['red'], source_sha256s=[h]),
                    inventory=[dict(role='garment-source', sha256=h)], output_form='human', shot_plan=sp,
                    model=dict(source_type='new', scope='full', subject='adult female model', locked=[], adjustable=[], consent_note=''))
        (root / 'prepare.json').write_text(json.dumps(prep))
        out = root / 'visual_plan.json'
        cmd = [sys.executable, str(SCRIPTS / 'visual_library.py'), 'prepare', '--spec', str(root / 'prepare.json'), '--output', str(out)]
        first = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        before = out.read_bytes()
        second = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
        self.assertEqual(second.returncode, 2)
        self.assertIn(f'--output {out} already exists and frozen plans are never overwritten', second.stderr)
        self.assertIn(f'e.g. --output {root / "visual_plan-2.json"}', second.stderr)
        self.assertNotIn('Errno 17', second.stderr)
        self.assertEqual(out.read_bytes(), before)
        self.assertFalse((root / 'visual_plan-2.json').exists())
        # A dangling symlink at -2 is not free either: open('x') would still fail there, so offer -3.
        (root / 'visual_plan-2.json').symlink_to(root / 'missing-target.json')
        third = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
        self.assertEqual(third.returncode, 2)
        self.assertIn(f'e.g. --output {root / "visual_plan-3.json"}', third.stderr)
        self.assertFalse((root / 'visual_plan-3.json').exists())
        # Paths with spaces are quoted so the suggestion can be pasted into a shell as-is.
        spaced = root / 'my plans'; spaced.mkdir()
        out2 = spaced / 'visual_plan.json'
        cmd2 = cmd[:-1] + [str(out2)]
        self.assertEqual(subprocess.run(cmd2, cwd=root, capture_output=True, text=True).returncode, 0)
        fourth = subprocess.run(cmd2, cwd=root, capture_output=True, text=True)
        self.assertEqual(fourth.returncode, 2)
        self.assertIn(f"e.g. --output '{spaced / 'visual_plan-2.json'}'", fourth.stderr)


if __name__ == '__main__':
    unittest.main()
