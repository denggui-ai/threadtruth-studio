"""Reference-role and actual native-request regressions; synthetic images only."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'reference_execution_task', ROOT / 'skills/threadtruth-studio/scripts/web-task.py')
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class ReferenceExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.job = self.root / 'task'
        self.garment = self.image('garment', 'red')
        self.original = self.image('original', 'blue')
        self.supplement = self.image('supplement', 'purple')
        self.edit_target = self.image('edit-target', 'green')
        self.model = dict(
            source_type='ai', scope='face', subject='adult female model',
            locked=['retain the original expression', 'soft rounded facial outline',
                    '参考中自然的眉形'],
            adjustable=['subtle brown eye makeup'], consent_note='')
        self.context = dict(outfit='current-knit', style='french-effortless', mode='C',
                            output_form='human model', size=[20, 30], first_pose=1)
        self.presentation = ('Supported kneeling beside a low bench; three-quarter torso, '
                             'waist-up composition with no required foot visibility.')

    def image(self, name, color):
        path = self.root / (name + '.png')
        Image.new('RGB', (20, 30), color).save(path)
        return path

    def refs(self, *, edit=False, supplement=True):
        rows = [dict(path=str(self.garment), role='garment-source'),
                dict(path=str(self.original), role='identity-reference')]
        if supplement:
            rows.append(dict(path=str(self.supplement), role='model-supplement',
                             scope='face', sha256=m.digest(self.supplement),
                             confirmation_note='Human accepted only this facial presentation'))
        if edit:
            # Deliberately not first: role semantics must follow actual order.
            rows.append(dict(path=str(self.edit_target), role='edit-target'))
        return rows

    def create(self, *, context=None, refs=None, count=1, identity=True, model=None):
        return m.create(self.job, self.refs() if refs is None else refs,
                        ['Photograph in a quiet room; preserve the current garment.'] * count,
                        (20, 30), identity=identity,
                        model=self.model if model is None else model,
                        context=self.context if context is None else context,
                        route='codex_native')

    def custom_context(self):
        return dict(self.context, first_pose='custom', pose_description=self.presentation)

    def correction_context(self, *, custom=True):
        context = self.custom_context() if custom else copy.deepcopy(self.context)
        context['purpose'] = 'correction-edit'
        return context

    def accept_first(self):
        m.update(self.job, 'authorize', limit=1, note='Human explicitly approves one call')
        m.update(self.job, 'reserve', look=1, ready=True,
                 refs=m.reference_hashes(self.job, 1))
        output = self.image('accepted-output', 'orange')
        m.update(self.job, 'returned', look=1, file=output)
        m.update(self.job, 'accept', look=1, qa='qa-pass',
                 note='Synthetic accepted output for ledger regression only')
        return output

    def continue_args(self, context):
        return dict(note='Human explicitly requests five more images',
                    approval_id='new-five-call-approval', context=context,
                    prompts=['next planned pose'] * 5)

    def test_custom_presentation_is_frozen_without_claiming_a_default_pose(self):
        data = self.create(context=self.custom_context())
        self.assertEqual(data['context']['first_pose'], 'custom')
        self.assertEqual(data['context']['pose_description'], self.presentation)
        self.assertEqual(data['attempts'], 0)
        self.assertIsNone(data['authorization'])
        self.assertIsNone(data['model_confirmation'])

    def test_custom_requires_a_nonempty_presentation_before_creating_files(self):
        for value in (None, '', '   ', 5):
            context = dict(self.context, first_pose='custom')
            if value is not None:
                context['pose_description'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.create(context=context)
            self.assertFalse(self.job.exists())

    def test_custom_cannot_start_or_silently_become_a_six_image_set(self):
        with self.assertRaises(ValueError):
            self.create(context=self.custom_context(), count=6)
        self.assertFalse(self.job.exists())
        context = self.custom_context()
        self.create(context=context)
        self.accept_first()
        m.update(self.job, 'confirm-model', look=1,
                 note='Human accepts the actual synthetic output')
        before = (self.job / 'task.json').read_bytes()
        with self.assertRaises(ValueError):
            m.update(self.job, 'continue-authorize', **self.continue_args(context))
        self.assertEqual((self.job / 'task.json').read_bytes(), before)

    def test_edit_target_is_forbidden_outside_a_correction(self):
        with self.assertRaises(ValueError):
            self.create(refs=self.refs(edit=True))
        self.assertFalse(self.job.exists())

    def test_correction_requires_exactly_one_edit_target(self):
        for rows in (self.refs(), self.refs(edit=True) + [
                dict(path=str(self.image('second-target', 'yellow')), role='edit-target')]):
            with self.subTest(count=sum(r['role'] == 'edit-target' for r in rows)):
                with self.assertRaises(ValueError):
                    self.create(context=self.correction_context(), refs=rows)
                self.assertFalse(self.job.exists())

    def test_correction_is_single_image_even_with_a_numbered_first_pose(self):
        with self.assertRaises(ValueError):
            self.create(context=self.correction_context(custom=False),
                        refs=self.refs(edit=True), count=6)
        self.assertFalse(self.job.exists())

    def test_correction_requires_existing_original_identity_and_a_portrait(self):
        rows = [dict(path=str(self.garment), role='garment-source'),
                dict(path=str(self.edit_target), role='edit-target')]
        with self.assertRaises(ValueError):
            self.create(context=self.correction_context(custom=False), refs=rows,
                        model=dict(self.model, source_type='new'))
        self.assertFalse(self.job.exists())
        with self.assertRaises(ValueError):
            m.create(self.job, rows, ['correct this image'], (20, 30), identity=False,
                     context=self.correction_context(custom=False), route='codex_native')
        self.assertFalse(self.job.exists())

    def test_correction_keeps_the_supplement_original_and_product_requirements(self):
        rows = self.refs(edit=True)
        rows.pop(1)
        with self.assertRaises(ValueError):
            self.create(context=self.correction_context(custom=False), refs=rows)
        self.assertFalse(self.job.exists())
        rows = [r for r in self.refs(edit=True) if r['role'] != 'garment-source']
        with self.assertRaises(ValueError):
            self.create(context=self.correction_context(custom=False), refs=rows)
        self.assertFalse(self.job.exists())
        rows = self.refs(edit=True)
        rows[2]['confirmation_note'] = ''
        with self.assertRaises(ValueError):
            self.create(context=self.correction_context(custom=False), refs=rows)
        self.assertFalse(self.job.exists())

    def test_edit_target_counts_toward_native_limit_before_freeze(self):
        rows = self.refs(edit=True)
        rows.extend(dict(path=str(self.image('detail-' + str(i), color)),
                         role='garment-source')
                    for i, color in enumerate(('black', 'white')))
        with self.assertRaises(ValueError):
            self.create(context=self.correction_context(custom=False), refs=rows)
        self.assertFalse(self.job.exists())
        self.create(context=self.correction_context(custom=False), refs=rows[:-1])
        self.assertEqual(len(m.read(self.job)['references']), 5)

    def test_edit_target_must_be_a_decodable_image_before_freeze(self):
        self.edit_target.write_bytes(b'not a decoded image despite the png extension')
        with self.assertRaises(ValueError):
            self.create(context=self.correction_context(custom=False), refs=self.refs(edit=True))
        self.assertFalse(self.job.exists())

    def test_actual_native_request_preserves_conditions_roles_and_frozen_images(self):
        data = self.create(context=self.correction_context(), refs=self.refs(edit=True))
        m.export(self.job)
        handoff = self.job / 'handoff/look-1'
        request_path = handoff / 'request.json'
        self.assertTrue(request_path.is_file(), 'Native execution must have exact tool arguments')
        request = json.loads(request_path.read_text())
        self.assertEqual(set(request), {'prompt', 'referenced_image_paths', 'transparent_background'})
        self.assertIs(request['transparent_background'], False)
        self.assertEqual(request['prompt'], (handoff / 'prompt.txt').read_text())
        # The free-form body above intentionally supplies none of these conditions.
        # This proves actual argument construction, not free-text semantic grading.
        for line in m.models.prompt_lines(self.model):
            self.assertIn(line, request['prompt'])
        self.assertIn(self.presentation, request['prompt'])
        self.assertIn(m.ROLE_TEXT['edit-target'], request['prompt'])
        actual_hashes = []
        for path, reference in zip(request['referenced_image_paths'], data['references']):
            frozen = Path(path)
            self.assertTrue(frozen.is_absolute())
            self.assertEqual(frozen.parent, handoff.resolve())
            self.assertEqual(m.digest(frozen), reference['sha256'])
            with Image.open(frozen) as image:
                image.load()
                self.assertEqual(image.size, (20, 30))
            actual_hashes.append(m.digest(frozen))
        self.assertEqual(len(request['referenced_image_paths']), len(data['references']))
        manifest = json.loads((handoff / 'manifest.json').read_text())
        self.assertEqual(manifest['reference_hashes'], actual_hashes)
        self.assertEqual(manifest['frozen_prompt_sha256'], data['looks'][0]['prompt_sha256'])
        self.assertEqual(manifest['tool_prompt_sha256'],
                         hashlib.sha256(request['prompt'].encode()).hexdigest())

    def test_changed_frozen_edit_target_blocks_export_and_reservation(self):
        self.create(context=self.correction_context(custom=False), refs=self.refs(edit=True))
        data = m.read(self.job)
        target = next(r for r in data['references'] if r['role'] == 'edit-target')
        (self.job / target['file']).write_bytes(b'damaged reference')
        before = (self.job / 'task.json').read_bytes()
        with self.assertRaises(ValueError):
            m.export(self.job)
        with self.assertRaises(ValueError):
            m.reference_hashes(self.job, 1)
        self.assertEqual((self.job / 'task.json').read_bytes(), before)

    def test_correction_cannot_continue_despite_pose_one_and_human_confirmation(self):
        context = self.correction_context(custom=False)
        self.create(context=context, refs=self.refs(edit=True))
        self.accept_first()
        m.update(self.job, 'confirm-model', look=1,
                 note='Human accepts this actual corrected output')
        before = (self.job / 'task.json').read_bytes()
        with self.assertRaises(ValueError):
            m.update(self.job, 'continue-authorize', **self.continue_args(context))
        self.assertEqual((self.job / 'task.json').read_bytes(), before)

    def test_edit_target_never_becomes_exported_identity_or_supplement(self):
        self.create(context=self.correction_context(custom=False), refs=self.refs(edit=True))
        output = self.accept_first()
        destination = self.root / 'package'
        with self.assertRaises(ValueError):
            m.export_model(self.job, destination, 'Synthetic model', include_accepted=True)
        self.assertFalse(destination.exists())
        m.update(self.job, 'confirm-model', look=1,
                 note='Human accepts the actual output face for this regression')
        m.export_model(self.job, destination, 'Synthetic model', include_accepted=True)
        card = m.models.load_package(destination)
        self.assertEqual([r['sha256'] for r in card['references']], [m.digest(self.original)])
        self.assertEqual({r['sha256'] for r in card['supplements']},
                         {m.digest(self.supplement), m.digest(output)})
        self.assertNotIn(m.digest(self.edit_target),
                         [r['sha256'] for r in card['references'] + card['supplements']])

    def test_existing_numbered_six_pose_task_keeps_its_progression_and_records(self):
        data = self.create(count=6)
        before = (self.job / 'task.json').read_bytes()
        m.export(self.job)
        self.assertEqual((self.job / 'task.json').read_bytes(), before)
        self.assertEqual(data['context']['first_pose'], 1)
        self.assertNotIn('pose_description', data['context'])
        self.assertFalse((self.job / 'handoff/look-2').exists())
        m.update(self.job, 'authorize', limit=6, note='Human approves six numbered images')
        m.update(self.job, 'reserve', look=1, ready=True,
                 refs=m.reference_hashes(self.job, 1))
        m.update(self.job, 'returned', look=1, file=self.image('numbered-first', 'orange'))
        m.update(self.job, 'accept', look=1, qa='qa-pass', note='Synthetic basic QA')
        with self.assertRaises(ValueError):
            m.reference_hashes(self.job, 2)
        m.update(self.job, 'confirm-model', look=1, note='Actual human model acceptance')
        second_refs = m.references(self.job, m.read(self.job), 2)
        self.assertEqual(second_refs[-1]['role'], 'identity-only')
        self.assertEqual(m.read(self.job)['attempts'], 1)
        self.assertEqual(m.read(self.job)['authorization']['limit'], 6)


if __name__ == '__main__':
    unittest.main()
