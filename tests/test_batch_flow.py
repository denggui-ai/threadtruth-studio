"""Local ledger regressions; synthetic files only, no network or generation calls.

Run using unittest discovery from the repository root.
"""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from PIL import Image

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().parents[1] / 'skills/threadtruth-studio/scripts/web-task.py'
spec = importlib.util.spec_from_file_location('flow_ledger_under_test', SCRIPT)
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)


class FlowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.task = self.base / 'task'
        self.seq = 0
        self.sources = [self.png((1, 2, 3)), self.png((4, 5, 6))]
        self.model = dict(source_type='ai', scope='face', subject='adult female model',
                          locked=['reference face'], adjustable=[], consent_note='')
        self.context = dict(outfit='synthetic cardigan test', style='japanese-lifestyle',
                            mode='C', output_form='full body', size=[12, 18], first_pose=1)
        self.create()

    def png(self, rgb, size=(12, 18)):
        self.seq += 1
        p = self.base / f'image-{self.seq}.png'
        Image.new('RGB', size, rgb).save(p)
        return p

    def create(self, route='codex_native', task=None, schema=2):
        root = task or self.task
        if schema == 1:
            ledger.create(root, [self.sources[0]], ['p'+str(i) for i in range(6)], [12, 18],
                          schema_version=1)
        else:
            ledger.create(root, [dict(path=str(self.sources[0]), role='garment-source'),
                                 dict(path=str(self.sources[1]), role='identity-reference')],
                          ['p'+str(i) for i in range(6)], [12, 18], model=self.model,
                          context=self.context, route=route)
        ledger.update(root, 'authorize', limit=6, note='Synthetic test: six requests approved')

    def data(self):
        return ledger.read(self.task)

    def reserve(self, n, **extra):
        kw = dict(look=n, ready=True, refs=ledger.reference_hashes(self.task, n))
        if self.data()['route'] == 'chatgpt_web':
            kw['conversation'] = 'https://chatgpt.com/c/synthetic-test'
        kw.update(extra)
        return ledger.update(self.task, 'reserve', **kw)

    def result(self, n, accepted=True):
        self.reserve(n)
        ledger.update(self.task, 'returned', look=n, file=self.png((n*20, n*15, n*10)))
        if accepted:
            ledger.update(self.task, 'accept', look=n, qa='qa-pass', note='Synthetic visual acceptance')
        else:
            ledger.update(self.task, 'reject', look=n, note='Synthetic ordinary composition failure')

    def first(self, confirm=True):
        self.result(1)
        if confirm:
            ledger.update(self.task, 'confirm-model', look=1, note='Synthetic user accepts this first image')

    def four(self, rejected=True):
        self.first()
        self.result(2)
        self.result(3)
        self.result(4, accepted=not rejected)

    def exported_dirs(self):
        return [p.name for p in (self.task/'handoff').glob('look-*') if p.is_dir()]

    def test_non_anchor_rejection_does_not_block(self):
        self.four()
        before = self.data()
        ledger.export(self.task)
        self.assertIn('look-5', self.exported_dirs())
        after = self.reserve(5)
        self.assertEqual(after['attempts'], 5)
        self.assertEqual(after['looks'][3]['state'], 'rejected')
        self.assertFalse(after['complete'])
        self.assertEqual(after['authorization'], before['authorization'])
        refs = ledger.references(self.task, after, 5)
        self.assertEqual([r['role'] for r in refs], ['garment-source','identity-reference','identity-only'])
        self.assertEqual(refs[-1]['sha256'], after['looks'][0]['output']['sha256'])
        self.assertNotEqual(refs[-1]['sha256'], after['looks'][3]['output']['sha256'])

    def test_web_route_uses_same_non_anchor_rule(self):
        self.task = self.base/'web-task'
        self.create(route='chatgpt_web')
        self.four()
        self.reserve(5)
        self.assertEqual(self.data()['attempts'], 5)

    def test_first_user_confirmation_is_required(self):
        self.first(confirm=False)
        ledger.export(self.task)
        self.assertEqual(self.exported_dirs(), [])
        with self.assertRaises(ValueError): self.reserve(2)
        self.assertEqual(self.data()['attempts'], 1)

    def test_invalidated_anchor_stops_export_and_reserve(self):
        self.first()
        ledger.update(self.task, 'audit-reject', look=1, note='Synthetic hard identity failure')
        ledger.export(self.task)
        self.assertEqual(self.exported_dirs(), [])
        with self.assertRaises(ValueError): self.reserve(2)

    def test_unknown_request_blocks_no_extra_call(self):
        self.first()
        self.reserve(2)
        ledger.update(self.task, 'unknown', look=2)
        ledger.export(self.task)
        self.assertEqual(self.exported_dirs(), [])
        with self.assertRaises(ValueError): self.reserve(3)
        self.assertEqual(self.data()['attempts'], 2)

    def test_wrong_canvas_remains_global_block(self):
        self.first()
        self.reserve(2)
        wrong = self.png((111, 99, 88), size=(13,18))
        with self.assertRaisesRegex(ValueError, 'Wrong canvas'):
            ledger.update(self.task, 'returned', look=2, file=wrong)
        self.assertEqual(self.data()['looks'][1]['state'], 'failed')
        ledger.export(self.task)
        self.assertEqual(self.exported_dirs(), [])
        with self.assertRaises(ValueError): self.reserve(3)
        self.assertEqual(self.data()['attempts'], 2)

    def test_pending_and_unreviewed_predecessor_still_block(self):
        self.first()
        with self.assertRaises(ValueError): self.reserve(3)
        self.reserve(2)
        ledger.update(self.task, 'returned', look=2, file=self.png((76,65,54)))
        with self.assertRaises(ValueError): self.reserve(3)

    def test_review_preserves_image_history_budget_and_model(self):
        self.four()
        old = self.data()
        row = old['looks'][3]
        d = ledger.update(self.task, 'review-output', look=4, qa='qa-user-review',
                          expected_output_sha256=row['output']['sha256'],
                          note='Fresh visual review: natural occlusion, not product structure loss')
        self.assertEqual(d['looks'][3]['state'], 'accepted')
        self.assertEqual(d['looks'][3]['output'], row['output'])
        self.assertEqual(d['looks'][3]['prompt'], row['prompt'])
        self.assertEqual(d['looks'][3]['qa_history'][-1]['qa'], 'qa-retry')
        self.assertEqual(d['looks'][3]['qa_history'][-1]['qa_note'], row['qa_note'])
        for key in ('authorization','attempts','references','model','model_confirmation','context'):
            self.assertEqual(d[key], old[key], key)
        self.assertEqual(d['delivery_status'], 'image-draft')
        self.assertFalse(d['complete'])

    def test_review_requires_matching_output_and_real_note(self):
        self.four()
        before = (self.task/'task.json').read_bytes()
        for sha,note in [('0'*64,'review'), (self.data()['looks'][3]['output']['sha256'],'')]:
            with self.subTest(sha=sha,note=note), self.assertRaises(ValueError):
                ledger.update(self.task,'review-output',look=4,qa='qa-pass',
                              expected_output_sha256=sha,note=note)
            self.assertEqual((self.task/'task.json').read_bytes(), before)

    def test_malformed_review_history_is_rejected_without_mutation(self):
        self.four()
        original = self.data()
        invalid = ['not-a-list', {}, ['not-a-review'], [{}],
                   [dict(qa='qa-pass', qa_note='history', state='pending', at='date')]]
        for history in invalid:
            with self.subTest(history=history):
                data = copy.deepcopy(original)
                data['looks'][3]['qa_history'] = history
                (self.task/'task.json').write_text(json.dumps(data))
                before = (self.task/'task.json').read_bytes()
                with self.assertRaisesRegex(ValueError, 'QA review history'):
                    ledger.update(self.task, 'review-output', look=4, qa='qa-user-review',
                                  expected_output_sha256=data['looks'][3]['output']['sha256'],
                                  note='Recheck this exact image')
                self.assertEqual((self.task/'task.json').read_bytes(), before)
                with self.assertRaisesRegex(ValueError, 'QA review history'):
                    ledger.export(self.task)

    def test_review_cannot_accept_anchor_or_unreturned_request(self):
        self.first()
        with self.assertRaises(ValueError):
            ledger.update(self.task,'review-output',look=1,qa='qa-pass',
                          expected_output_sha256=self.data()['looks'][0]['output']['sha256'],note='review')
        self.reserve(2)
        with self.assertRaises(ValueError):
            ledger.update(self.task,'review-output',look=2,qa='qa-pass',expected_output_sha256='0'*64,note='review')

    def test_pending_revision_preserves_old_export_and_budget(self):
        self.four(rejected=False)
        ledger.export(self.task)
        old_export = (self.task/'handoff/look-5/prompt.txt').read_bytes()
        old = self.data()
        prior = old['looks'][4]
        d = ledger.update(self.task,'revise-pending',look=5,
                          expected_prompt_sha256=prior['prompt_sha256'],
                          prompt='Same cardigan and canvas; approved sofa seated forward lean.',
                          note='Synthetic user approves changed pending shot, no extra calls')
        self.assertEqual(d['attempts'], 4)
        self.assertEqual(d['authorization'], old['authorization'])
        self.assertEqual(d['looks'][:4], old['looks'][:4])
        self.assertEqual(d['looks'][4]['prompt_history'][0]['prompt'], prior['prompt'])
        self.assertEqual(d['looks'][4]['plan_revision'], 1)
        for key in ('references','model','context','model_confirmation'):
            self.assertEqual(d[key], old[key])
        ledger.export(self.task)
        self.assertEqual((self.task/'handoff/look-5/prompt.txt').read_bytes(), old_export)
        self.assertIn('look-5-plan-1', self.exported_dirs())
        manifest=json.loads((self.task/'handoff/look-5-plan-1/manifest.json').read_text())
        self.assertEqual(manifest['frozen_prompt_sha256'], d['looks'][4]['prompt_sha256'])
        with self.assertRaises(ValueError):
            self.reserve(5,expected_prompt_sha256=prior['prompt_sha256'])
        with self.assertRaises(ValueError): self.reserve(5)
        self.reserve(5,expected_prompt_sha256=d['looks'][4]['prompt_sha256'])
        self.assertEqual(self.data()['attempts'], 5)

    def test_revision_rejects_sent_look_stale_hash_and_no_note(self):
        self.first()
        before=(self.task/'task.json').read_bytes()
        for look,sha,note in [(1,self.data()['looks'][0]['prompt_sha256'],'approved'),
                              (2,'0'*64,'approved'),(2,self.data()['looks'][1]['prompt_sha256'],'')]:
            with self.subTest(look=look,sha=sha,note=note),self.assertRaises(ValueError):
                ledger.update(self.task,'revise-pending',look=look,expected_prompt_sha256=sha,
                              prompt='new pending prompt',note=note)
            self.assertEqual((self.task/'task.json').read_bytes(),before)

    def test_history_tamper_is_detected(self):
        self.first()
        ledger.update(self.task,'revise-pending',look=2,
                      expected_prompt_sha256=self.data()['looks'][1]['prompt_sha256'],
                      prompt='approved different pose',note='Synthetic approval')
        d=self.data();d['looks'][1]['prompt_history'][0]['prompt']='tampered'
        (self.task/'task.json').write_text(json.dumps(d))
        with self.assertRaises(ValueError): ledger.export(self.task)

    def test_output_tamper_cannot_be_reviewed(self):
        self.four()
        row=self.data()['looks'][3]
        (self.task/row['output']['file']).write_bytes(b'changed')
        with self.assertRaises(ValueError):
            ledger.update(self.task,'review-output',look=4,qa='qa-pass',
                          expected_output_sha256=row['output']['sha256'],note='Synthetic review')

    def test_original_six_call_budget_cannot_be_exceeded(self):
        self.four()
        self.result(5)
        self.result(6)
        d=self.data()
        self.assertEqual(d['attempts'],6)
        self.assertFalse(d['complete'])
        with self.assertRaises(ValueError): self.reserve(4)
        with self.assertRaises(ValueError): ledger.update(self.task,'authorize',limit=6,note='reset')
        self.assertEqual(self.data()['attempts'],6)

    def test_legacy_schema_one_remains_strict(self):
        self.task=self.base/'legacy'
        self.create(task=self.task,schema=1)
        self.result(1)
        self.result(2,accepted=False)
        with self.assertRaises(ValueError): self.reserve(3)
        with self.assertRaises(ValueError):
            ledger.update(self.task,'revise-pending',look=3,expected_prompt_sha256=self.data()['looks'][2]['prompt_sha256'],prompt='new',note='approval')

    def test_cli_supports_auditable_pending_revision(self):
        self.first()
        p=self.base/'new-prompt.txt';p.write_text('CLI approved sofa prompt')
        r=subprocess.run([sys.executable,'-B',str(SCRIPT),'revise-pending','--task',str(self.task),
                          '--look','2','--expected-prompt-sha256',self.data()['looks'][1]['prompt_sha256'],
                          '--prompt-file',str(p),'--note','Synthetic user approval'],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(self.data()['looks'][1]['prompt'],p.read_text())
        self.assertEqual(self.data()['attempts'],1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
