"""Native product workflow with synthetic files; no generation or visual quality claims."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

from tests import test_visual_plan as fixtures

task = fixtures.task
ROOT = fixtures.ROOT
_spec = importlib.util.spec_from_file_location('product_library', ROOT / 'skills/threadtruth-studio/scripts/visual_library.py')
library = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(library)


class ProductEditTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.VisualPlanTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.target = self.f.image('derived-target', 'blue')
        self.source_hash = task.digest(self.f.front)
        self.target_hash = task.digest(self.target)
        self.inventory = [dict(role='garment-source', sha256=self.source_hash),
                          dict(role='edit-target', sha256=self.target_hash)]

    def spec(self, form='ghost-mannequin', operation='reconstruction'):
        edit = dict(version=1, operation=operation, source_form='human' if operation=='reconstruction' else form,
                    edit_target_sha256=self.target_hash, display_mode='single',
                    items=[dict(name='Original red shirt', kind='garment', source_sha256s=[self.source_hash])],
                    background=dict(color='#FFFFFF', shadow='none'),
                    structure_evidence=[dict(part='Visible inner collar and cuffs', source_sha256s=[self.source_hash])],
                    unresolved_parts=[])
        return dict(entry_id='ecommerce-studio', output_form=form,
                    garment=dict(description='Original red shirt', keep=['Original collar, cuffs, color and marks'],
                                 source_sha256s=[self.source_hash]),
                    inventory=copy.deepcopy(self.inventory), product_edit=edit)

    def create(self, spec=None, **overrides):
        spec = spec or self.spec()
        plan = library.prepare(spec)
        form = spec['output_form']
        identity = form in ('human', 'faceless')
        refs = [dict(path=self.f.front, role='garment-source'), dict(path=self.target, role='edit-target')]
        if identity:
            refs.append(dict(path=self.target, role='identity-reference'))
        ctx = dict(outfit='synthetic-sku', style='ecommerce-studio', mode='B', output_form=form,
                   size=[60,40], first_pose='custom', purpose='product-edit',
                   pose_description='Keep the source subject during cleanup.' if identity else 'Show only the selected complete garment.')
        model = dict(source_type='ai', scope='full', subject='adult female model', locked=[], adjustable=[], consent_note='') if identity else None
        kwargs = dict(model=model, context=ctx, route='codex_native', visual_plan=plan, count=1)
        kwargs.update(overrides)
        return task.create(self.f.job, refs, None, [60,40], identity, **kwargs)

    def confirm(self):
        task.update(self.f.job, 'confirm-plan', decision=dict(style='ecommerce-studio', path='single', image_count=1,
                                                          note='Synthetic one-image plan confirmation'))
        return task.update(self.f.job, 'authorize', limit=1, note='Synthetic one-call authorization')

    def returned(self):
        self.confirm()
        self.f.reserve()
        return task.update(self.f.job, 'returned', look=1, file=self.f.image('output', 'green'))

    def review(self):
        data = task.read(self.f.job)
        expected = dict(goal=task.workflow_helper().goal(data, data['looks'][0]),
                        garment='Original garment facts', photography='Declared studio presentation')
        expected.update(task.visual_helper().product_helper().requirements(data['visual_plan']['product_edit'], data['context']['output_form']))
        if data['identity']:
            expected.update(identity='Original person', anatomy='Original natural anatomy')
        return {k:dict(expected=v, observed='Synthetic observation for workflow only', result='met') for k,v in expected.items()}

    def test_native_export_binds_product_plan_target_originals_and_one_image(self):
        data = self.create()
        self.assertEqual(len(data['looks']), 1)
        self.assertFalse(data['identity'])
        self.assertNotIn('shot_plan', data)
        self.assertEqual(data['attempts'], 0)
        task.export(self.f.job)
        request = json.loads(next((self.f.job/'handoff').glob('*/request.json')).read_text())
        manifest = json.loads(next((self.f.job/'handoff').glob('*/manifest.json')).read_text())
        self.assertEqual(manifest['visual_plan'], data['visual_plan'])
        self.assertEqual(manifest['reference_hashes'], [self.source_hash, self.target_hash])
        self.assertEqual(len(request['referenced_image_paths']), 2)
        prompt = request['prompt']
        for text in ('ghost-mannequin', 'no feet', 'original lining', '#FFFFFF', 'shadow=none',
                     'Original garment-source images alone', 'no collage', 'no arms or legs'):
            self.assertIn(text, prompt)
        self.assertNotIn('six-panel', prompt)
        self.assertNotIn('[Current model conditions]', prompt)
        self.assertNotIn('no flat shadowless lighting', prompt)
        self.assertNotIn('soft fill from camera-right', prompt)
        self.assertEqual(task.read(self.f.job)['attempts'], 0)

    def test_white_cleanup_keeps_source_subject_and_identity_gates(self):
        data = self.create(self.spec('human', 'background-cleanup'))
        self.assertTrue(data['identity'])
        prompt = task.handoff_prompt(data, data['looks'][0], task.references(self.f.job, data, 1))
        self.assertIn('Retain every subject, pose', prompt)
        self.assertIn('[Current model conditions]', prompt)
        self.assertNotIn('Remove the source person completely', prompt)
        self.assertIn('identity', self.review())
        bad = self.spec('ghost-mannequin', 'background-cleanup')
        bad['product_edit']['source_form'] = 'human'
        with self.assertRaisesRegex(ValueError, 'retains the source'):
            library.prepare(bad)

    def test_outfit_inventory_requires_independent_accessories_without_adding_items(self):
        spec = self.spec()
        spec['product_edit']['display_mode'] = 'outfit'
        spec['product_edit']['items'].append(dict(name='Original pair of shoes', kind='accessory', source_sha256s=[self.source_hash]))
        self.create(spec)
        review = self.review()
        self.assertIn('accessories', review)
        self.assertIn('Original pair of shoes', review['product_scope']['expected'])
        spec['product_edit']['display_mode'] = 'single'
        with self.assertRaisesRegex(ValueError, 'Single mode'):
            library.prepare(spec)

    def test_missing_structure_or_derived_structure_is_not_factual_evidence(self):
        changes = [dict(structure_evidence=[]), dict(unresolved_parts=['Hidden inner collar']),
                   dict(structure_evidence=[dict(part='Inner collar', source_sha256s=[self.target_hash])]),
                   dict(edit_target_sha256=self.source_hash),
                   dict(items=[dict(name='Shoes alone',kind='accessory',source_sha256s=[self.source_hash])])]
        for patch in changes:
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                spec = self.spec(); spec['product_edit'].update(patch); library.prepare(spec)

    def test_product_branch_cannot_bypass_workflow_native_or_preview_boundaries(self):
        for override in (dict(workflow_version=0), dict(route='chatgpt_web')):
            with self.subTest(override=override), self.assertRaisesRegex(ValueError, 'native route'):
                self.create(**override)
        for patch in (dict(count=6), dict(first_pose=1), dict(shot_plan={}), dict(product_edit=None)):
            with self.subTest(patch=patch), self.assertRaises((ValueError, TypeError)):
                spec = self.spec(); spec.update(patch); library.prepare(spec)
        self.create()
        task.update(self.f.job, 'authorize', limit=1, note='Synthetic authorization without plan confirmation')
        with self.assertRaisesRegex(ValueError, '[Cc]onfirm'):
            self.f.reserve()
        self.assertEqual(task.read(self.f.job)['attempts'], 0)

    def test_ghost_never_falls_back_to_ordinary_mannequin_or_no_contract(self):
        spec = self.spec(); spec.pop('product_edit')
        with self.assertRaisesRegex(ValueError, 'Ghost mannequin'):
            library.prepare(spec)
        ordinary = library.prepare(dict(entry_id='ecommerce-studio', output_form='mannequin',
                                        garment=spec['garment'], inventory=[self.inventory[0]]))
        self.assertNotIn('product_edit', ordinary)
        self.assertEqual(ordinary['output_form'], 'mannequin')

    def test_qa_cannot_pass_missing_no_body_unknown_interior_or_wrong_white(self):
        data = self.create(); self.returned()
        review = self.review()
        missing = copy.deepcopy(review); missing.pop('no_body_support')
        with self.assertRaisesRegex(ValueError, 'QA records'):
            task.update(self.f.job, 'accept', look=1, qa='qa-pass', review=missing, note='Incomplete QA')
        substituted = copy.deepcopy(review); substituted['background']['expected'] = 'Looks nearly white'
        with self.assertRaisesRegex(ValueError, 'frozen product'):
            task.update(self.f.job, 'accept', look=1, qa='qa-pass', review=substituted, note='Substituted QA')
        for key, result, expected in [('openings','unknown','qa-user-review'), ('background','unmet','qa-retry'),
                                      ('no_body_support','unmet','qa-retry'), ('product_scope','unmet','qa-retry')]:
            checked=copy.deepcopy(review); checked[key]['result']=result
            self.assertEqual(task.workflow_helper().review_result(data,data['looks'][0],checked), expected)
            with self.assertRaises(ValueError):
                task.update(self.f.job, 'accept', look=1, qa='qa-pass', review=checked, note='Cannot overstate QA')
        task.update(self.f.job, 'accept', look=1, qa='qa-pass', review=review, note='Synthetic QA only')
        self.assertEqual(task.read(self.f.job)['attempts'], 1)
        with self.assertRaisesRegex(ValueError, 'cannot become'):
            task.update(self.f.job, 'continue-authorize', note='Not a six-pose trial', approval_id='bad', context=data['context'])

    def test_rejected_product_retry_retains_budget_sources_contract_and_old_qa(self):
        self.create(); self.returned()
        review=self.review(); review['no_body_support']['result']='unmet'
        task.update(self.f.job,'reject',look=1,review=review,note='Synthetic hand residue')
        old=task.read(self.f.job); revised=copy.deepcopy(old['visual_plan'])
        revised['product_edit']['correction']='Remove the residual hand in the sleeve opening; preserve its original seam.'
        with self.assertRaises(ValueError):
            bad=copy.deepcopy(revised); bad['product_edit']['background']['color']='#F2F2F2'
            task.update(self.f.job,'retry-authorize',look=1,expected_attempt=1,approval_id='bad',note='Synthetic',visual_plan=bad)
        task.update(self.f.job,'retry-authorize',look=1,expected_attempt=1,approval_id='repair-one',
                    note='Synthetic explicit one extra request',visual_plan=revised)
        data=task.read(self.f.job)
        self.assertEqual(data['attempts'],1)
        self.assertEqual(data['references'],old['references'])
        self.assertEqual(data['looks'][0]['history'][0]['review'],review)
        self.assertEqual(data['looks'][0]['history'][0]['visual_plan'],old['visual_plan'])
        task.export(self.f.job); self.f.reserve()
        self.assertEqual(task.read(self.f.job)['attempts'],2)
        with self.assertRaises(ValueError):
            task.update(self.f.job,'retry-authorize',look=1,expected_attempt=1,approval_id='repair-one',
                        note='No duplicate authorization',visual_plan=revised)

    def test_unknown_or_unreconciled_failure_cannot_gain_a_product_retry(self):
        self.create(); self.confirm(); self.f.reserve()
        task.update(self.f.job,'unknown',look=1)
        revised=copy.deepcopy(task.read(self.f.job)['visual_plan'])
        revised['product_edit']['correction']='Keep the reviewed garment opening, without any visible support.'
        kwargs=dict(look=1,expected_attempt=1,approval_id='after-check',note='Synthetic explicit one extra call',visual_plan=revised)
        with self.assertRaises(ValueError):task.update(self.f.job,'retry-authorize',**kwargs)
        receipt=self.f.root/'failure.txt';receipt.write_text('SYNTHETIC terminal provider failure')
        task.update(self.f.job,'failed',look=1,reason='provider failure',failure_receipt=receipt)
        with self.assertRaises(ValueError):task.update(self.f.job,'retry-authorize',**kwargs)
        task.update(self.f.job,'reconcile-failure',look=1,expected_attempt=1,request_check_completed=True,
                    note='Synthetic original request inspected; no returned image')
        task.update(self.f.job,'retry-authorize',**kwargs)
        self.f.reserve()
        data=task.read(self.f.job)
        self.assertEqual(data['attempts'],2)
        self.assertEqual(data['looks'][0]['history'][0]['state'],'failed')
        self.assertIn('failure_reconciliation',data['looks'][0]['history'][0])

    def test_cli_preparation_and_init_share_the_product_contract(self):
        spec_path=self.f.root/'prepare.json'; spec_path.write_text(json.dumps(self.spec('flat-lay','background-cleanup')))
        visual_path=self.f.root/'visual.json'
        scripts=ROOT/'skills/threadtruth-studio/scripts'
        result=subprocess.run([sys.executable,str(scripts/'visual_library.py'),'prepare','--spec',str(spec_path),
                               '--output',str(visual_path)],text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.create(self.spec('flat-lay','background-cleanup'))
        data=task.read(self.f.job)
        self.assertEqual(json.loads(visual_path.read_text()),data['visual_plan'])
        init=dict(references=[dict(path=str(self.f.front),role='garment-source'),dict(path=str(self.target),role='edit-target')],
                  size=data['size'],identity=False,context=data['context'],route='codex_native',
                  visual_plan=json.loads(visual_path.read_text()),count=1)
        init_path=self.f.root/'init.json'; init_path.write_text(json.dumps(init))
        cli_job=self.f.root/'cli-task'
        for args in [('init','--spec',str(init_path)),('export',)]:
            result=subprocess.run([sys.executable,str(scripts/'web-task.py'),args[0],'--task',str(cli_job),*args[1:]],
                                  text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
        request=json.loads(next((cli_job/'handoff').glob('*/request.json')).read_text())
        self.assertIn('background-cleanup',request['prompt'])
        self.assertEqual(task.read(cli_job)['attempts'],0)


if __name__ == '__main__':
    unittest.main()
