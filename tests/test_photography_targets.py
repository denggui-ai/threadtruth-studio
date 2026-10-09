"""Offline task-level photography transport through actual helper and native handoff."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BEGIN = '[Task photography targets]'
END = '[/Task photography targets]'
TARGETS = ['Window side light with readable garment folds',
           'A quiet room with depth behind the subject',
           'Seated composition balanced against the furniture']


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


task = load('photography_task', 'skills/threadtruth-studio/scripts/web-task.py')
preview = load('photography_preview', 'tools/style_preview.py')


def block(targets=TARGETS):
    return BEGIN + '\n' + '\n'.join('- ' + target for target in targets) + '\n' + END


class PhotographyTaskTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.job = self.root / 'job'
        self.garment = self.image('garment', 'red')
        self.face = self.image('face', 'blue')
        self.context = dict(outfit='sku-a', style='japanese-lifestyle', mode='C',
                            output_form='real', size=[20, 30], first_pose=1,
                            photography_targets=copy.deepcopy(TARGETS))
        self.model = dict(source_type='ai', scope='face', subject='adult female model',
                          locked=['same original face'], adjustable=[], consent_note='')

    def image(self, name, color):
        path = self.root / (name + '.png')
        Image.new('RGB', (20, 30), color).save(path)
        return path

    def create(self, prompt='Keep the handwritten room description and product facts.', count=1,
               source_type='ai', context=None, refs=None):
        model = dict(self.model, source_type=source_type,
                     consent_note='Human authorized this real person' if source_type == 'real' else '')
        if refs is None:
            refs = [dict(path=str(self.garment), role='garment-source')]
            if source_type != 'new':
                refs.append(dict(path=str(self.face), role='identity-reference'))
        try:
            return task.create(self.job, refs, [prompt] * count, (20, 30), model=model,
                               context=context or self.context, route='codex_native')
        except ValueError as error:
            self.fail('Valid frozen photography context must be supported: ' + str(error))

    def request(self, look=1):
        task.export(self.job)
        folder = self.job / 'handoff' / f'look-{look}'
        request = json.loads((folder / 'request.json').read_text())
        manifest = json.loads((folder / 'manifest.json').read_text())
        self.assertEqual(request['prompt'], (folder / 'prompt.txt').read_text())
        self.assertEqual(manifest['tool_prompt_sha256'],
                         hashlib.sha256(request['prompt'].encode()).hexdigest())
        return request, manifest

    def assert_targets_once(self, prompt):
        self.assertEqual(prompt.count(BEGIN), 1)
        self.assertEqual(prompt.count(END), 1)
        self.assertIn(block(), prompt)
        for target in TARGETS:
            self.assertEqual(prompt.count(target), 1)

    def accept_first(self):
        task.update(self.job, 'authorize', limit=1, note='One actual request approved')
        task.update(self.job, 'reserve', look=1, ready=True, refs=task.reference_hashes(self.job, 1))
        task.update(self.job, 'returned', look=1, file=self.image('accepted-first', 'green'))
        task.update(self.job, 'accept', look=1, qa='qa-pass', note='Actual first image reviewed')
        task.update(self.job, 'confirm-model', look=1, note='Human accepts first-image person')

    def test_manual_prompt_reaches_native_request_with_bound_targets_and_original_hash(self):
        raw = 'Use a dark indigo wall. Preserve this manual sentence exactly.\nOnly the current garment is authoritative.'
        data = self.create(raw)
        request, manifest = self.request()
        self.assert_targets_once(request['prompt'])
        self.assertIn(raw, request['prompt'])
        self.assertEqual(data['looks'][0]['prompt'], raw)
        self.assertEqual(manifest['frozen_prompt_sha256'], hashlib.sha256(raw.encode()).hexdigest())
        self.assertEqual(data['context_sha256'], task.object_hash(self.context))
        self.assertEqual(len(request['referenced_image_paths']), 2)
        self.assertIn('01-garment-source.png', request['referenced_image_paths'][0])
        self.assertIn('02-identity-reference.png', request['referenced_image_paths'][1])
        self.assertEqual(data['model'], self.model)
        self.assertNotIn('real_face_plan', data)

    def test_already_rendered_matching_block_is_not_added_again(self):
        raw = 'Preserve a manually specified silhouette.\n' + block() + '\nKeep the same curtain.'
        self.create(raw)
        request, _ = self.request()
        self.assert_targets_once(request['prompt'])
        self.assertIn(raw, request['prompt'])

    def test_malformed_present_targets_reject_before_task_directory_exists(self):
        invalid = [None, '', {}, (), [], ['one'], ['x'] * 5,
                   ['valid', ''], ['valid', '  '], ['valid', 2],
                   ['valid', 'a\nb'], ['valid', 'a\u0085b'], ['valid', 'a\u2028b'],
                   ['valid', 'a\u2029b'], ['valid', 'a' * 241], ['valid', BEGIN]]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                task.create(self.job, [str(self.garment)], ['manual'], (20, 30),
                            context=dict(self.context, photography_targets=value), route='codex_native')
            self.assertFalse(self.job.exists())

    def test_two_and_four_short_targets_are_supported_and_whitespace_is_normalized(self):
        for values in ([' Scene depth ', ' Soft side light '],
                       ['Scene depth', 'Soft side light', 'Negative space', 'a' * 240]):
            with self.subTest(count=len(values)):
                self.job = self.root / ('bounds-' + str(len(values)))
                data = self.create(context=dict(self.context, photography_targets=values))
                request, _ = self.request()
                normalized = [value.strip() for value in values]
                self.assertEqual(data['context']['photography_targets'], normalized)
                self.assertIn(block(normalized), request['prompt'])
                self.assertEqual(request['prompt'].count(BEGIN), 1)

    def test_conflicting_duplicate_or_unclosed_canonical_block_rejects_before_freeze(self):
        bad_prompts = [block(['different light', 'different composition']),
                       block() + '\n' + block(), BEGIN + '\n- unfinished', END]
        for prompt in bad_prompts:
            with self.subTest(prompt=prompt), self.assertRaises(ValueError):
                task.create(self.job, [str(self.garment)], [prompt], (20, 30),
                            context=self.context, route='codex_native')
            self.assertFalse(self.job.exists())

    def test_changed_context_fails_existing_hash_before_export_or_reserve(self):
        data = self.create()
        task.update(self.job, 'authorize', limit=1, note='One request approved')
        data = task.read(self.job)
        data['context']['photography_targets'][0] = 'A changed unauthorized light'
        (self.job / 'task.json').write_text(json.dumps(data))
        before = (self.job / 'task.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'Frozen context/model changed'):
            task.export(self.job)
        with self.assertRaisesRegex(ValueError, 'Frozen context/model changed'):
            task.update(self.job, 'reserve', look=1, ready=True,
                        refs=[reference['sha256'] for reference in data['references']])
        self.assertEqual((self.job / 'task.json').read_bytes(), before)
        self.assertFalse((self.job / 'handoff').exists())

    def test_bound_context_with_mismatched_prompt_cannot_be_exported_or_submitted(self):
        data = self.create('manual\n' + block())
        data['looks'][0]['prompt'] = 'manual\n' + block(['other light', 'other depth'])
        data['looks'][0]['prompt_sha256'] = hashlib.sha256(data['looks'][0]['prompt'].encode()).hexdigest()
        (self.job / 'task.json').write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'photography'):
            task.export(self.job)
        with self.assertRaisesRegex(ValueError, 'photography'):
            task.update(self.job, 'authorize', limit=1, note='Cannot approve conflicting frozen block')

    def test_target_block_without_frozen_targets_is_rejected(self):
        context = {key: value for key, value in self.context.items() if key != 'photography_targets'}
        with self.assertRaisesRegex(ValueError, 'photography'):
            task.create(self.job, [str(self.garment)], ['manual\n' + block()], (20, 30),
                        context=context, route='codex_native')
        self.assertFalse(self.job.exists())

    def test_deleting_helper_target_block_fails_the_original_frozen_prompt_hash(self):
        data = self.create('manual\n' + block())
        data['looks'][0]['prompt'] = 'manual'
        (self.job / 'task.json').write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'Frozen prompt changed'):
            task.export(self.job)

    def test_continuation_keeps_targets_first_anchor_and_cumulative_budget(self):
        self.create()
        self.accept_first()
        before = (self.job / 'task.json').read_bytes()
        changed = dict(self.context, photography_targets=['different light', 'different scene'])
        with self.assertRaisesRegex(ValueError, 'Continuation'):
            task.update(self.job, 'continue-authorize', context=changed, prompts=['pose'] * 5,
                        approval_id='changed', note='Five requested')
        self.assertEqual((self.job / 'task.json').read_bytes(), before)
        data = task.update(self.job, 'continue-authorize', context=self.context, prompts=['pose'] * 5,
                           approval_id='five', note='Five more requested')
        request, _ = self.request(2)
        self.assert_targets_once(request['prompt'])
        self.assertEqual(data['attempts'], 1)
        self.assertEqual(data['authorization']['limit'], 1)
        self.assertEqual(data['continuation_authorization']['additional_requests'], 5)
        self.assertEqual(len(request['referenced_image_paths']), 3)
        self.assertIn('03-identity-only.png', request['referenced_image_paths'][-1])

    def test_continuation_rejects_conflicting_target_block_without_mutation(self):
        self.create()
        self.accept_first()
        before = (self.job / 'task.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'photography'):
            task.update(self.job, 'continue-authorize', context=self.context,
                        prompts=['pose'] * 4 + [block(['other light', 'other room'])],
                        approval_id='five', note='Five more requested')
        self.assertEqual((self.job / 'task.json').read_bytes(), before)

    def test_targets_preserve_real_ai_new_identity_roles(self):
        for source_type in ('real', 'ai', 'new'):
            with self.subTest(source_type=source_type):
                self.job = self.root / source_type
                data = self.create(source_type=source_type)
                request, _ = self.request()
                self.assert_targets_once(request['prompt'])
                expected = ['garment-source'] + ([] if source_type == 'new' else ['identity-reference'])
                self.assertEqual([ref['role'] for ref in data['references']], expected)
                self.assertEqual(len(request['referenced_image_paths']), len(expected))

    def test_targets_preserve_custom_correction_edit_reference_roles(self):
        context = dict(self.context, first_pose='custom', pose_description='Retain this seated furniture layout',
                       purpose='correction-edit')
        refs = [dict(path=str(self.garment), role='garment-source'),
                dict(path=str(self.face), role='identity-reference'),
                dict(path=str(self.image('edit-target', 'yellow')), role='edit-target')]
        data = self.create(context=context, refs=refs)
        request, _ = self.request()
        self.assert_targets_once(request['prompt'])
        self.assertIn(context['pose_description'], request['prompt'])
        self.assertIn('image to correct', request['prompt'])
        self.assertEqual([ref['role'] for ref in data['references']],
                         ['garment-source', 'identity-reference', 'edit-target'])

    def test_targets_do_not_bypass_five_reference_limit(self):
        refs = [dict(path=str(self.image('source-' + str(i), color)), role='garment-source')
                for i, color in enumerate(('red', 'green', 'blue', 'yellow', 'purple'))]
        refs.append(dict(path=str(self.face), role='identity-reference'))
        with self.assertRaisesRegex(ValueError, 'five'):
            task.create(self.job, refs, ['manual'], (20, 30), model=self.model,
                        context=self.context, route='codex_native')
        self.assertFalse(self.job.exists())

    def test_missing_targets_preserve_exact_schema1_and_schema2_handoff_bytes(self):
        raw = 'Legacy frozen prompt with manual light.\n'
        context = {key: value for key, value in self.context.items() if key != 'photography_targets'}
        for schema in (1, 2):
            with self.subTest(schema=schema):
                job = self.root / ('legacy-' + str(schema))
                kwargs = dict(schema_version=schema)
                if schema == 2:
                    kwargs.update(context=context, route='codex_native')
                data = task.create(job, [str(self.garment)], [raw], (20, 30), identity=False, **kwargs)
                task.export(job)
                expected = ('Only use built-in image generation, no other plugins. One standalone image.\n'
                            'Image 1: garment source; authoritative product facts\nExact canvas: 20x30.\n' + raw)
                self.assertEqual((job / 'handoff/look-1/prompt.txt').read_bytes(), expected.encode())
                self.assertNotIn('photography_targets', data.get('context', {}))
                self.assertEqual(data['looks'][0]['prompt_sha256'], hashlib.sha256(raw.encode()).hexdigest())


class PhotographyHelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        for path in ('docs/demo', 'skills/threadtruth-studio/references'):
            shutil.copytree(ROOT / path, cls.root / path)
        cls.model = dict(source_type='new', scope='full', subject='adult female model',
                         locked=[], adjustable=[], consent_note='')
        cls.plan = preview._plan_v5(cls.root, 'targets', 'beige-blazer-denim-outfit')

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def helper(self, style, action, targets=TARGETS):
        try:
            return preview.single_prompt(self.root, 'targets', style, 1,
                                         'beige-blazer-denim-outfit', '2:3', model=self.model,
                                         action=action, photography_targets=targets)
        except TypeError as error:
            self.fail('Helper must accept optional photography_targets: ' + str(error))

    def test_all_24_styles_helper_preview_and_single_prompt_reach_request_once(self):
        styles = [item['style'] for item in self.plan['previews']]
        self.assertEqual(len(styles), 24)
        for style in styles:
            for action in (0, 2):
                with self.subTest(style=style, action=action):
                    result = self.helper(style, action)
                    raw = (self.root / result['path']).read_text()
                    self.assertIn('style ' + style, raw)
                    self.assertEqual(raw.count(BEGIN), 1)
                    context = dict(outfit='outfit-a', style=style, mode='B', output_form='real',
                                   size=[20, 30], first_pose=1, photography_targets=copy.deepcopy(TARGETS))
                    refs = [{key: ref[key] for key in ('path', 'role')} for ref in result['references']]
                    job = self.root / f'task-{style}-{action}'
                    data = task.create(job, refs, [raw], (20, 30), model=self.model,
                                       context=context, route='codex_native')
                    task.export(job)
                    request = json.loads((job / 'handoff/look-1/request.json').read_text())
                    manifest = json.loads((job / 'handoff/look-1/manifest.json').read_text())
                    self.assertEqual(request['prompt'].count(BEGIN), 1)
                    self.assertIn(block(), request['prompt'])
                    self.assertEqual(manifest['tool_prompt_sha256'],
                                     hashlib.sha256(request['prompt'].encode()).hexdigest())
                    self.assertEqual(data['looks'][0]['prompt_sha256'], result['sha256'])
                    self.assertEqual([ref['sha256'] for ref in data['references']],
                                     [ref['sha256'] for ref in result['references']])

    def test_helper_absent_targets_retain_exact_old_prompt_and_return_shape(self):
        style = 'japanese-lifestyle'
        old = preview.single_prompt(self.root, 'old', style, 1, 'beige-blazer-denim-outfit',
                                    '2:3', model=self.model)
        old_bytes = (self.root / old['path']).read_bytes()
        new = self.helper(style, 2, None)
        self.assertEqual((self.root / new['path']).read_bytes(), old_bytes)
        self.assertEqual(new['sha256'], old['sha256'])
        self.assertEqual(set(new), set(old))
        self.assertNotIn(BEGIN.encode(), old_bytes)

    def test_helper_cli_accepts_repeated_optional_target_arguments(self):
        arguments = [sys.executable, str(ROOT / 'tools/style_preview.py'), '--root', str(self.root),
                     'single-prompt', '--run-id', 'cli-targets', '--source-case', 'beige-blazer-denim-outfit',
                     '--style', 'japanese-lifestyle', '--pose', '1']
        for target in TARGETS:
            arguments += ['--photography-target', target]
        run = subprocess.run(arguments, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        raw = (self.root / result['path']).read_text()
        self.assertEqual(raw.count(BEGIN), 1)
        self.assertIn(block(), raw)


if __name__ == '__main__':
    unittest.main()
