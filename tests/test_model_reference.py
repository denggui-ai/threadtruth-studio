import importlib.util
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/threadtruth-studio/scripts/model_reference.py'


class ModelReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.face = self.root / 'face.png'
        Image.new('RGB', (30, 40), 'blue').save(self.face)
        spec = importlib.util.spec_from_file_location('model_reference_tests', SCRIPT)
        if SCRIPT.exists():
            self.m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.m)

    def model(self, **changes):
        result = dict(source_type='ai', scope='full', subject='adult female model',
                      locked=['apparent age around 40', 'natural fuller proportions'],
                      adjustable=['gentle makeup'], consent_note='')
        result.update(changes)
        return result

    def test_cli_help_does_not_write_into_runtime_without_environment_setup(self):
        scripts=ROOT/'skills/threadtruth-studio/scripts'
        for command in ('model-reference.py','web-task.py'):
            with self.subTest(command=command):
                runtime=self.root/command.removesuffix('.py');runtime.mkdir()
                for filename in (command,'model_reference.py'):
                    shutil.copyfile(scripts/filename,runtime/filename)
                before={str(p.relative_to(runtime)):hashlib.sha256(p.read_bytes()).hexdigest() for p in runtime.rglob('*') if p.is_file()}
                env=dict(os.environ);env.pop('PYTHONDONTWRITEBYTECODE',None);env.pop('PYTHONPYCACHEPREFIX',None)
                result=subprocess.run([sys.executable,str(runtime/command),'--help'],env=env,capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
                after={str(p.relative_to(runtime)):hashlib.sha256(p.read_bytes()).hexdigest() for p in runtime.rglob('*') if p.is_file()}
                self.assertEqual(after,before,'A local help/read must not mutate the installed runtime')

    def supplement(self, **changes):
        path = self.root / 'accepted.png'
        Image.new('RGB', (30, 40), 'green').save(path)
        result = dict(path=str(path), sha256=self.m.digest(path), scope='face',
                      confirmation_note='User accepts this generated face presentation')
        result.update(changes)
        return result

    def test_empty_adjustable_respects_explicit_fixed_styling_targets(self):
        for source_type in ('ai', 'real'):
            model = self.model(source_type=source_type,
                               locked=['short black bob hairstyle', 'matte red lipstick'],
                               adjustable=[], consent_note='Declared likeness permission')
            with self.subTest(source_type=source_type):
                text = '\n'.join(self.m.prompt_lines(model))
                self.assertIn('short black bob hairstyle; matte red lipstick', text)
                self.assertNotIn('Permitted styling: retain reference hair and makeup', text)
                self.assertIn('unless the declared model conditions explicitly change them', text)

    def test_new_casting_empty_adjustable_does_not_require_identity_reference_styling(self):
        text = '\n'.join(self.m.prompt_lines(self.model(source_type='new', adjustable=[])))
        self.assertNotIn('retain reference hair and makeup', text)
        self.assertIn('selected style', text)

    def export_supplement(self, supplements):
        try:
            return self.m.export_package(self.root/'with-supplement', self.model(),
                                         [self.face], 'A', 'Accepted', supplements=supplements)
        except TypeError as error:
            self.fail('Accepted supplement export is missing: ' + str(error))

    def test_accepted_supplement_roundtrip_keeps_original_distinct(self):
        supplement = self.supplement()
        card = self.export_supplement([supplement])
        self.assertEqual(card['schema_version'], 2)
        self.assertEqual(card['references'][0]['sha256'], self.m.digest(self.face))
        self.assertEqual(card['supplements'][0]['role'], 'model-supplement')
        self.assertEqual(card['supplements'][0]['sha256'], supplement['sha256'])
        self.assertEqual(card['supplements'][0]['scope'], 'face')
        self.assertNotIn(str(self.root), (self.root/'with-supplement/model.json').read_text())
        self.assertEqual(self.m.load_package(self.root/'with-supplement'), card)

    def test_supplement_requires_hash_bound_acceptance_and_scope(self):
        for changes in [dict(confirmation_note=''), dict(sha256='0'*64), dict(scope='garment')]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.export_supplement([self.supplement(**changes)])
            self.assertFalse((self.root/'with-supplement').exists())

    def test_supplement_cannot_duplicate_original_or_another_supplement(self):
        original = self.supplement(path=str(self.face), sha256=self.m.digest(self.face))
        supplement = self.supplement()
        for rows in [[original], [supplement, supplement]]:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                self.export_supplement(rows)

    def test_missing_changed_and_escaping_supplement_files_block_package(self):
        card = self.export_supplement([self.supplement()])
        package = self.root/'with-supplement'
        image = package/card['supplements'][0]['file']
        original = image.read_bytes()
        image.write_bytes(b'changed')
        with self.assertRaises(ValueError): self.m.load_package(package)
        image.write_bytes(original)
        card['supplements'][0]['file'] = '../accepted.png'
        (package/'model.json').write_text(json.dumps(card))
        with self.assertRaises(ValueError): self.m.load_package(package)

    def test_portable_roundtrip_keeps_original_reference_and_no_absolute_paths(self):
        self.assertTrue(SCRIPT.exists(), 'portable reference helper is missing')
        package = self.root / 'brand-a'
        self.m.export_package(package, self.model(), [self.face], 'Brand A', 'User accepts this model')
        card = self.m.load_package(package)
        self.assertEqual(card['model']['locked'], self.model()['locked'])
        self.assertEqual(len(card['references']), 1)
        self.assertNotIn(str(self.root), (package / 'model.json').read_text())
        self.assertEqual((package / card['references'][0]['file']).read_bytes(), self.face.read_bytes())

    def test_export_requires_actual_confirmation_and_real_likeness_consent(self):
        self.assertTrue(SCRIPT.exists(), 'portable reference helper is missing')
        for model, confirmation in [(self.model(), ''), (self.model(source_type='real'), 'Accepted')]:
            with self.subTest(model=model, confirmation=confirmation), self.assertRaises(ValueError):
                self.m.export_package(self.root / 'bad', model, [self.face], 'A', confirmation)
        self.assertFalse((self.root / 'bad').exists())

    def test_tampered_missing_and_escaping_references_are_rejected(self):
        self.assertTrue(SCRIPT.exists(), 'portable reference helper is missing')
        package = self.root / 'a'
        self.m.export_package(package, self.model(), [self.face], 'A', 'Accepted')
        path = package / 'model.json'
        card = json.loads(path.read_text())
        image = package / card['references'][0]['file']
        image.write_bytes(b'changed')
        with self.assertRaises(ValueError): self.m.load_package(package)
        card['references'][0]['file'] = '../face.png'
        path.write_text(json.dumps(card))
        with self.assertRaises(ValueError): self.m.load_package(package)

    def test_face_only_prompt_does_not_claim_original_body_and_style_yields_to_user(self):
        self.assertTrue(SCRIPT.exists(), 'portable reference helper is missing')
        model = self.model(scope='face', locked=['same face'], adjustable=['friendly smile'])
        lines = self.m.prompt_lines(model)
        self.assertIn('face-only', '\n'.join(lines))
        persona, negatives = self.m.resolve_style(model, 'cold detached expression',
                                                  ['no sweet smile', 'no busy background'])
        self.assertNotIn('cold detached', persona)
        self.assertNotIn('no sweet smile', negatives)
        self.assertIn('no busy background', negatives)

    def test_factor_delivery_preserves_provenance_unknowns_and_runtime_conditions(self):
        factors = [dict(name='body', value='natural fuller proportions', status='fixed', source='recommendation', confirmed=True),
                   dict(name='makeup', value='gentle makeup', status='adjustable', source='user', confirmed=True),
                   dict(name='actual size', value='unknown', status='unknown', source='reference', confirmed=False)]
        model = self.model(factors=factors)
        package = self.root/'factors'
        card = self.m.export_package(package, model, [self.face], 'A', 'Accepted')
        self.assertEqual(card['model']['factors'], factors)
        self.assertIn('recommendation', (package/'README.md').read_text())
        self.assertIn('actual size', (package/'README.md').read_text())
        self.assertNotIn('actual size', '\n'.join(self.m.prompt_lines(model)))
        factors[0]['confirmed'] = False
        with self.assertRaises(ValueError): self.m.validate_model(self.model(factors=factors))

    def test_unknown_factor_cannot_be_prompt_condition_or_duplicate_another_state(self):
        for factors in [
            [dict(name='body',value='natural fuller proportions',status='unknown',source='reference',confirmed=False)],
            [dict(name='body',value='natural fuller proportions',status='fixed',source='user',confirmed=True), dict(name='body',value='unknown',status='unknown',source='reference',confirmed=False)]
        ]:
            with self.subTest(factors=factors),self.assertRaises(ValueError):self.m.validate_model(self.model(factors=factors))

    def test_proposed_factors_become_confirmed_only_on_export(self):
        model=self.model(factors=[dict(name='body', value='natural fuller proportions', status='target', source='recommendation', confirmed=False)])
        self.assertEqual(self.m.validate_model(model)['factors'][0]['status'], 'target')
        card=self.m.export_package(self.root/'proposed',model,[self.face],'A','First-image human approval')
        self.assertEqual(card['model']['factors'][0]['status'], 'fixed')
        self.assertTrue(card['model']['factors'][0]['confirmed'])
        self.assertFalse(model['factors'][0]['confirmed'])

    def test_non_person_negative_substrings_and_safety_are_preserved(self):
        _, negatives = self.m.resolve_style(self.model(), 'cold face', ['no vintage background', 'no sexualized body', 'no sweet smile'])
        self.assertIn('no vintage background', negatives)
        self.assertIn('no sexualized body', negatives)
        self.assertNotIn('no sweet smile', negatives)
        mood=self.m.resolve_mood(self.model(adjustable=['neutral expression']), 'quiet photographic mood; no sexualized body; sweet smile')
        self.assertIn('no sexualized body',mood)
        self.assertNotIn('sweet smile',mood)

    def test_card_rejects_unknown_product_fields_and_requires_identity_to_export(self):
        self.assertTrue(SCRIPT.exists(), 'portable reference helper is missing')
        for model, refs in [(self.model(garment='old shirt'), [self.face]), (self.model(), [])]:
            with self.subTest(model=model), self.assertRaises(ValueError):
                self.m.export_package(self.root / 'bad', model, refs, 'A', 'Accepted')

    def test_export_rejects_fake_empty_mislabeled_and_truncated_images(self):
        jpeg = self.root/'real.jpg'
        Image.new('RGB', (30, 40), 'red').save(jpeg)
        cases = {'fake.png': b'not an image', 'empty.png': b'',
                 'mislabeled.png': jpeg.read_bytes(), 'truncated.jpg': jpeg.read_bytes()[:-20]}
        for name, content in cases.items():
            image = self.root/name; image.write_bytes(content)
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'image|Image'):
                self.m.export_package(self.root/'bad', self.model(), [image], 'A', 'Accepted')
            self.assertFalse((self.root/'bad').exists())

    def test_read_rejects_undecodable_reference_even_with_matching_hash(self):
        for role in ('references', 'supplements', 'pose_mothers'):
            with self.subTest(role=role):
                package = self.root/role
                kwargs = {'supplements': [self.supplement()]} if role == 'supplements' else {}
                if role == 'pose_mothers': kwargs = {'pose_mothers': [self.mother()]}
                card = self.m.export_package(package, self.model(), [self.face], 'A', 'Accepted', **kwargs)
                row = card[role][0]; image = package/row['file']
                image.write_bytes(b'broken but hash-matched')
                row['sha256'] = self.m.digest(image)
                (package/'model.json').write_text(json.dumps(card))
                with self.assertRaisesRegex(ValueError, 'image|Image'): self.m.load_package(package)

    def test_supplement_and_pose_mother_require_decodable_image_before_export(self):
        broken = self.root/'broken.png'; broken.write_bytes(b'not an image')
        for key, row in [('supplements', self.supplement()), ('pose_mothers', self.mother())]:
            row.update(path=str(broken), sha256=self.m.digest(broken))
            with self.subTest(role=key), self.assertRaisesRegex(ValueError, 'image|Image'):
                self.m.export_package(self.root/'bad', self.model(), [self.face], 'A', 'Accepted', **{key:[row]})
            self.assertFalse((self.root/'bad').exists())

    def test_decoder_unavailable_blocks_without_partial_package(self):
        with patch.dict(sys.modules, {'PIL': None}), self.assertRaisesRegex(ValueError, 'tool-blocked.*decoder'):
            self.m.export_package(self.root/'bad', self.model(), [self.face], 'A', 'Accepted')
        self.assertFalse((self.root/'bad').exists())

    def test_missing_codec_and_permissive_decoder_block(self):
        with patch('PIL.features.check', return_value=False), self.assertRaisesRegex(ValueError, 'tool-blocked.*PNG'):
            self.m.validate_image(self.face)
        with patch('PIL.ImageFile.LOAD_TRUNCATED_IMAGES', True), self.assertRaisesRegex(ValueError, 'tool-blocked.*truncated'):
            self.m.validate_image(self.face)

    def test_export_validates_copies_after_external_reference_changes(self):
        original_validate = self.m.validate_image
        def mutate_after_source_check(path):
            result = original_validate(path)
            if Path(path).resolve() == self.face.resolve():
                self.face.write_bytes(b'changed between preflight and snapshot')
            return result
        with patch.object(self.m, 'validate_image', side_effect=mutate_after_source_check):
            with self.assertRaisesRegex(ValueError, 'image|Image'):
                self.m.export_package(self.root/'bad', self.model(), [self.face], 'A', 'Accepted')
        self.assertFalse((self.root/'bad').exists())

    def test_valid_supported_encodings_decode_and_export(self):
        for suffix, format_name in [('png', 'PNG'), ('jpg', 'JPEG'), ('webp', 'WEBP')]:
            with self.subTest(format=format_name):
                source = self.root/('source.' + suffix)
                Image.new('RGB', (30, 40), 'green').save(source)
                self.assertEqual(self.m.validate_image(source), {'format': format_name, 'size': [30, 40], 'frames': 1})
                package = self.root/('package-' + suffix)
                self.m.export_package(package, self.model(), [source], 'A', 'Accepted')
                self.assertEqual(self.m.load_package(package)['references'][0]['sha256'], self.m.digest(source))

    def test_all_frozen_pack_atmospheres_survive_explicit_casting(self):
        paths = sorted((ROOT/'skills/threadtruth-studio/references/styles').glob('*.pack.yaml'))
        self.assertEqual(len(paths), 24)
        model = self.model(subject='adult male model', adjustable=['friendly smile', 'gentle makeup', 'tidy tied hair'])
        for path in paths:
            mood = ' '.join(path.read_text().split('visual_language: >\n', 1)[1].split('\nmodel_persona:', 1)[0].split())
            actual = self.m.resolve_mood(model, mood)
            with self.subTest(pack=path.name):
                if path.stem != 'korean-cold-editorial.pack':
                    self.assertEqual(actual, mood)
                else:
                    for phrase in ['restrained editorial mood', 'soft even lighting', 'cold gray',
                                   'medium format film photography texture', 'realistic native skin texture',
                                   'subtle pores', 'no excessive retouching', 'referenced accessory']:
                        self.assertIn(phrase, actual)
                    for phrase in ['detached expression', 'melancholy', 'commercial smile', 'influencer style',
                                   'translucent makeup', 'eye makeup', 'dusty rose lips', 'flyaway hair']:
                        self.assertNotIn(phrase, actual)

    def test_mood_filters_only_explicit_conflicting_person_conditions(self):
        model = self.model(source_type='new', locked=[], adjustable=['friendly smile'])
        mood = 'warm light and calm detached expression, film texture, dewy makeup, natural flyaway hair'
        actual = self.m.resolve_mood(model, mood)
        for phrase in ['warm light', 'film texture', 'dewy makeup', 'natural flyaway hair']:
            self.assertIn(phrase, actual)
        self.assertNotIn('detached expression', actual)
        self.assertEqual(self.m.resolve_mood(model, 'friendly smile, warm light'), 'friendly smile, warm light')
        self.assertEqual(self.m.resolve_mood(self.model(source_type='new', locked=[], adjustable=[]), mood), mood)
        reused = self.m.resolve_mood(self.model(locked=[], adjustable=['friendly smile']), mood)
        self.assertEqual(reused, 'warm light, film texture')

    def test_unseparable_mixed_conflict_requires_review_without_discarding_photography(self):
        model = self.model(adjustable=['friendly smile'])
        with self.assertRaisesRegex(ValueError, 'Review mixed person/photography'):
            self.m.resolve_mood(model, 'smiling face light photography')

    def mother(self, pose='seated', **changes):
        row = self.supplement()
        row.pop('scope'); row.pop('confirmation_note')
        row.update(pose=pose, acceptance=dict(level='qualified', note='Usable with reservations'),
                   qa=dict(original_fidelity='uncertain', candidate_continuity='pass', garment='uncertain'))
        return dict(row, **changes)

    def test_pose_mother_roundtrip_retains_qualified_acceptance_and_original(self):
        mother = self.mother()
        card = self.m.export_package(self.root/'poses', self.model(), [self.face], 'A', 'Qualified use', pose_mothers=[mother])
        self.assertEqual(card['schema_version'], 3)
        self.assertEqual(card['references'][0]['sha256'], self.m.digest(self.face))
        self.assertEqual(card['supplements'], [])
        selected = self.m.select_pose_mother(self.root/'poses', 'SEATED')
        self.assertEqual(selected['acceptance']['level'], 'qualified')
        self.assertEqual(selected['qa']['original_fidelity'], 'uncertain')
        self.assertEqual(self.m.digest(selected['path']), mother['sha256'])
        self.assertNotIn(str(self.root), (self.root/'poses/model.json').read_text())
        with self.assertRaises(ValueError): self.m.select_pose_mother(self.root/'poses', 'back view')

    def test_pose_mother_rejects_missing_feedback_failed_qa_or_changed_image(self):
        for row in [self.mother(acceptance=dict(level='qualified', note='')),
                    self.mother(qa=dict(original_fidelity='fail', candidate_continuity='pass', garment='pass')),
                    self.mother(qa=dict(original_fidelity='uncertain', candidate_continuity='fail', garment='pass')),
                    self.mother(qa=dict(original_fidelity='uncertain', candidate_continuity='pass', garment='fail')),
                    self.mother(sha256='0'*64)]:
            with self.subTest(row=row), self.assertRaises(ValueError):
                self.m.export_package(self.root/'bad', self.model(), [self.face], 'A', 'Accepted', pose_mothers=[row])
            self.assertFalse((self.root/'bad').exists())

    def test_pose_mother_duplicates_traversal_and_legacy_packages(self):
        row = self.mother()
        with self.assertRaises(ValueError):
            self.m.export_package(self.root/'bad', self.model(), [self.face], 'A', 'Accepted', pose_mothers=[row, row])
        with self.assertRaises(ValueError):
            self.m.export_package(self.root/'bad', self.model(), [self.face], 'A', 'Accepted', pose_mothers=[dict(row, path=str(self.face), sha256=self.m.digest(self.face))])
        package = self.root/'a'
        card = self.m.export_package(package, self.model(), [self.face], 'A', 'Accepted', pose_mothers=[row])
        (package/card['pose_mothers'][0]['file']).write_bytes(b'tampered')
        with self.assertRaises(ValueError): self.m.load_package(package)
        card['pose_mothers'][0]['file'] = '../accepted.png'
        (package/'model.json').write_text(json.dumps(card))
        with self.assertRaises(ValueError): self.m.load_package(package)
        legacy = self.m.export_package(self.root/'legacy', self.model(), [self.face], 'A', 'Accepted')
        self.assertEqual(legacy['schema_version'], 1)
        with self.assertRaises(ValueError): self.m.select_pose_mother(self.root/'legacy', 'seated')


if __name__ == '__main__':
    unittest.main()
