"""Synthetic local images only; exercise task/export/import, never generation."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

SCRIPT = Path(__file__).resolve().parents[1]/'skills/threadtruth-studio/scripts/web-task.py'
spec = importlib.util.spec_from_file_location('common_flow_task', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class CommonFlowTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.job = self.root/'task'
        self.ref = self.image('garment', (20, 30), 'red')
        self.context = dict(outfit='sku', style='ecommerce-studio', mode='B',
                            output_form='flat', size=[20, 30], first_pose=1)

    def image(self, name, size, color):
        path = self.root/(name+'.png')
        Image.new('RGB', size, color).save(path)
        return path

    def create(self, count=1, policy=None, **kw):
        context = dict(self.context)
        if policy is not None:
            context['canvas_policy'] = policy
        return m.create(self.job, [self.ref], ['shot']*count, [20, 30],
                        identity=False, context=context, **kw)

    def reserve(self, number):
        return m.update(self.job, 'reserve', look=number, ready=True,
                        refs=m.reference_hashes(self.job, number))

    def test_omitted_route_exports_native_request_without_web_handoff(self):
        self.create()
        m.export(self.job)
        request = self.job/'handoff/look-1/request.json'
        self.assertTrue(request.is_file())
        self.assertEqual(len(json.loads(request.read_text())['referenced_image_paths']), 1)
        m.update(self.job, 'authorize', limit=1, note='Synthetic authorization')
        self.assertEqual(self.reserve(1)['attempts'], 1)

    def test_cli_omitted_route_uses_native_but_legacy_schema_stays_web(self):
        specfile = self.root/'spec.json'
        specfile.write_text(json.dumps(dict(references=[str(self.ref)], prompts=['shot'],
                            size=[20, 30], identity=False, context=self.context)))
        run = subprocess.run([sys.executable, str(SCRIPT), 'init', '--task', str(self.job),
                              '--spec', str(specfile)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)['route'], 'codex_native')
        legacy = m.create(self.root/'legacy', [self.ref], ['shot'], [20, 30],
                          identity=False, schema_version=1)
        self.assertEqual(legacy['route'], 'chatgpt_web')

    def test_existing_web_task_reads_without_rewrite_or_route_migration(self):
        self.create(route='chatgpt_web')
        before = (self.job/'task.json').read_bytes()
        self.assertEqual(m.read(self.job)['route'], 'chatgpt_web')
        self.assertEqual((self.job/'task.json').read_bytes(), before)

    def test_ratio_first_accepts_other_pixels_then_enforces_first_baseline(self):
        self.create(count=6, policy='ratio-first')
        m.export(self.job)
        prompt = (self.job/'handoff/look-1/prompt.txt').read_text()
        self.assertNotIn('Exact canvas:', prompt)
        m.update(self.job, 'authorize', limit=6, note='Synthetic six-image authorization')
        self.reserve(1)
        returned = m.update(self.job, 'returned', look=1,
                            file=self.image('first', (40, 60), 'blue'))
        self.assertEqual(returned['looks'][0]['output']['dimensions'], [40, 60])
        m.update(self.job, 'accept', look=1, qa='qa-pass', note='Synthetic QA')
        m.export(self.job)
        self.assertIn('Exact canvas: 40x60', (self.job/'handoff/look-2/prompt.txt').read_text())
        self.reserve(2)
        with self.assertRaisesRegex(ValueError, 'Wrong canvas'):
            m.update(self.job, 'returned', look=2,
                     file=self.image('changed', (20, 30), 'green'))
        self.assertEqual(m.read(self.job)['attempts'], 2)

    def test_ratio_first_wrong_ratio_retains_failure_without_establishing_baseline(self):
        self.create(policy='ratio-first')
        m.update(self.job, 'authorize', limit=1, note='Synthetic authorization')
        self.reserve(1)
        with self.assertRaisesRegex(ValueError, 'Wrong canvas'):
            m.update(self.job, 'returned', look=1,
                     file=self.image('wrong', (40, 61), 'blue'))
        d = m.read(self.job)
        self.assertNotIn('output', d['looks'][0])
        self.assertTrue((self.job/d['looks'][0]['failure']['evidence']['file']).is_file())

    def test_explicit_pixels_remain_strict(self):
        self.create()
        m.update(self.job, 'authorize', limit=1, note='Synthetic authorization')
        self.reserve(1)
        with self.assertRaisesRegex(ValueError, 'Wrong canvas'):
            m.update(self.job, 'returned', look=1,
                     file=self.image('other', (40, 60), 'blue'))

    def test_ratio_baseline_survives_rejection_retry_and_single_continuation(self):
        self.create(policy='ratio-first')
        m.update(self.job, 'authorize', limit=1, note='Synthetic authorization')
        self.reserve(1)
        m.update(self.job, 'returned', look=1, file=self.image('first', (40, 60), 'blue'))
        m.update(self.job, 'reject', look=1, note='Synthetic visual failure')
        m.update(self.job, 'retry-authorize', look=1, expected_attempt=1,
                 approval_id='retry', note='Synthetic one retry', prompt='corrected shot')
        m.export(self.job)
        self.assertIn('Exact canvas: 40x60', (self.job/'handoff/look-1-attempt-2/prompt.txt').read_text())
        self.reserve(1)
        m.update(self.job, 'returned', look=1, file=self.image('retry', (40, 60), 'green'))
        d = m.update(self.job, 'accept', look=1, qa='qa-pass', note='Synthetic QA')
        self.assertTrue(d['complete'])
        self.assertEqual(d['delivery_status'], 'image-draft')
        d = m.update(self.job, 'continue-authorize', note='Synthetic five more', approval_id='five',
                     context=d['context'], prompts=['next']*5)
        self.assertEqual(d['attempts'], 2)
        m.export(self.job)
        self.assertIn('Exact canvas: 40x60', (self.job/'handoff/look-2/prompt.txt').read_text())

    def test_invalid_canvas_policy_cannot_silently_relax_dimensions(self):
        with self.assertRaises(ValueError):
            self.create(policy='anything')

    def test_web_ratio_policy_and_frozen_context_use_same_import_gate(self):
        self.create(policy='ratio-first', route='chatgpt_web')
        m.update(self.job, 'authorize', limit=1, note='Synthetic web authorization')
        m.update(self.job, 'reserve', look=1, ready=True,
                 refs=m.reference_hashes(self.job, 1), conversation='https://chatgpt.com/c/synthetic')
        m.update(self.job, 'returned', look=1, file=self.image('web', (40, 60), 'blue'))
        d = m.read(self.job)
        d['context']['canvas_policy'] = 'exact'
        m.save(self.job, d)
        with self.assertRaisesRegex(ValueError, 'Frozen context'):
            m.export(self.job)
