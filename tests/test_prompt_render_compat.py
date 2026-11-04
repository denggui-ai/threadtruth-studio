"""Resume real e190988 exports without upgrading their prompt rendering."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tests.test_prompt_dedupe import task


FIXTURE = Path(__file__).with_name('fixtures') / 'prompt-render-e190988.json'


class PromptRenderCompatibilityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.job = self.root / 'legacy'
        self.fixture = json.loads(FIXTURE.read_text())
        self.assertTrue(self.fixture['baseline'].startswith('e190988'))
        self.before = {}
        for relative, content in self.fixture['files'].items():
            raw = base64.b64decode(content['base64']) if 'base64' in content else content['text'].encode()
            path = self.job / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            self.before[relative] = raw
        self.data = task.read(self.job)
        self.assertNotIn('prompt_render', self.data)
        self.assertEqual(self.data['shot_plan']['framing_guidance'], 3)
        self.handoff = task.handoff_directory(self.job, self.data, self.data['looks'][0])
        self.execution = self.handoff / 'web-execution-v2' / 'execution.json'
        self.metadata = json.loads(self.execution.read_text())

    def assert_preserved(self, *, reserved=False):
        for relative, raw in self.before.items():
            if not (reserved and relative == 'task.json'):
                self.assertEqual((self.job / relative).read_bytes(), raw, relative)
        self.assertEqual(task.digest(self.handoff / 'prompt.txt'), self.fixture['canonical_prompt_sha256'])
        self.assertNotIn('prompt_render', task.read(self.job))

    def reserve(self, job, execution, submission_hash):
        data = task.read(job)
        return task.update(job, 'reserve', look=1, ready=True, refs=task.reference_hashes(job, 1),
                           conversation='https://chatgpt.com/c/synthetic-render-compat',
                           expected_plan_sha256=task.plan_fingerprint(data),
                           expected_prompt_sha256=data['looks'][0]['prompt_sha256'],
                           execution_manifest=str(execution), expected_submission_sha256=submission_hash)

    def test_e190988_export_retains_every_byte(self):
        task.export(self.job)
        self.assert_preserved()

    def test_e190988_execution_export_reuses_original_package(self):
        packet = task.export_web_execution(self.job, 1)
        self.assertEqual(packet['canonical_prompt_sha256'], self.fixture['canonical_prompt_sha256'])
        self.assertEqual(packet['submission_sha256'], self.metadata['submission']['sha256'])
        self.assert_preserved()

    def test_e190988_reserve_accepts_original_execution_package(self):
        data = self.reserve(self.job, self.execution, self.metadata['submission']['sha256'])
        self.assertEqual(data['looks'][0]['state'], 'reserved')
        self.assertEqual(data['looks'][0]['web_execution']['sha256'], task.digest(self.execution))
        self.assert_preserved(reserved=True)

    def test_new_task_marks_rendering_and_exports_validated_standard_blocks(self):
        for include_shot_block in (False, True):
            with self.subTest(include_shot_block=include_shot_block):
                job = self.root / ('new-with-shot-block' if include_shot_block else 'new')
                prompt = self.data['looks'][0]['prompt']
                if include_shot_block:
                    prompt += task.shot_helper().render(self.data['shot_plan']) + '\n'
                created = task.create(job, [self.job / self.data['references'][0]['file']], [prompt],
                                      self.data['size'], model=copy.deepcopy(self.data['model']),
                                      context=copy.deepcopy(self.data['context']), route='chatgpt_web',
                                      shot_plan=copy.deepcopy(self.data['shot_plan']),
                                      visual_plan=copy.deepcopy(self.data['visual_plan']))
                self.assertEqual(created['prompt_render'], 2)
                self.assertEqual(created['looks'][0]['prompt'], prompt)
                task.update(job, 'confirm-plan', decision=dict(style=created['context']['style'], path='preview',
                            image_count=1, note='Synthetic confirmation; no external call.'))
                task.update(job, 'authorize', limit=1, note='Synthetic ledger-only authority; no external call.')
                task.export(job)
                out = task.handoff_directory(job, created, created['looks'][0])
                exported = (out / 'prompt.txt').read_text()
                for line in ('Lighting (all cells): Uniform cell light.',
                             'Composition (all cells): Uniform cell composition.',
                             'All preview cells use reference images:'):
                    self.assertEqual(exported.count(line), 1)
                self.assertNotIn('Selection reason:', exported)
                self.assertNotEqual(hashlib.sha256(exported.encode()).hexdigest(),
                                    self.fixture['canonical_prompt_sha256'])
                packet = task.export_web_execution(job, 1)
                self.assertEqual(packet['canonical_prompt_sha256'], task.digest(out / 'prompt.txt'))
                reserved = self.reserve(job, packet['execution_manifest'], packet['submission_sha256'])
                self.assertEqual(reserved['prompt_render'], 2)
                self.assertEqual(reserved['looks'][0]['state'], 'reserved')


if __name__ == '__main__':
    unittest.main()
