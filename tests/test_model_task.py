import copy
import json
import subprocess
import sys
import importlib.util
from pathlib import Path
import tempfile
import unittest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('model_task', ROOT/'skills/threadtruth-studio/scripts/web-task.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ModelTaskTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.job = self.root/'job'
        self.garment = self.image('garment', 'red')
        self.face = self.image('identity', 'blue')
        self.context = dict(outfit='sku-a', style='ecommerce-studio', mode='B', output_form='real', size=[20, 30], first_pose=1)
        self.model = dict(source_type='ai', scope='full', subject='adult female model',
                          locked=['same original face', 'natural fuller proportions'], adjustable=['friendly smile'], consent_note='')

    def image(self, name, color):
        path = self.root/(name+'.png')
        Image.new('RGB', (20, 30), color).save(path)
        return path

    def create(self, count=6, model=True, route='chatgpt_web'):
        refs = [dict(path=str(self.garment), role='garment-source')]
        if model: refs.append(dict(path=str(self.face), role='identity-reference'))
        return m.create(self.job, refs, ['pose '+str(i) for i in range(count)], (20,30),
                        model=self.model if model else dict(self.model, source_type='new'),
                        context=self.context, route=route)

    def first(self, count=6, route='chatgpt_web'):
        self.create(count, route=route)
        m.update(self.job, 'authorize', limit=count, note='Explicit generation approval')
        args = dict(look=1, ready=True, refs=m.reference_hashes(self.job,1))
        if route == 'chatgpt_web': args['conversation']='https://chatgpt.com/c/test'
        m.update(self.job, 'reserve', **args)
        m.update(self.job, 'returned', look=1, file=self.image('first', 'green'))
        m.update(self.job, 'accept', look=1, qa='qa-pass', note='Garment and identity QA')

    def confirm(self):
        return m.update(self.job, 'confirm-model', look=1, note='Human accepts this first-image model')

    def test_new_roles_and_prompt_reach_first_image(self):
        d=self.create()
        self.assertEqual(d['schema_version'],2)
        self.assertEqual([r['role'] for r in m.references(self.job,d,1)], ['garment-source','identity-reference'])
        m.export(self.job)
        prompt=(self.job/'handoff/look-1/prompt.txt').read_text()
        self.assertIn('original model identity',prompt)
        self.assertIn('natural fuller proportions',prompt)
        self.assertIn('never supply clothing',prompt)

    def test_internal_qa_does_not_unlock_later_images(self):
        self.first()
        with self.assertRaises(ValueError):m.reference_hashes(self.job,2)
        m.export(self.job)
        self.assertFalse((self.job/'handoff/look-2').exists())
        self.confirm()
        self.assertEqual(len(m.reference_hashes(self.job,2)),3)
        self.assertEqual(m.read(self.job)['attempts'],1)

    def test_native_route_obeys_the_same_first_confirmation_gate(self):
        self.first(route='codex_native')
        with self.assertRaises(ValueError):m.reference_hashes(self.job,2)
        self.confirm()
        self.assertEqual(m.read(self.job)['route'],'codex_native')
        self.assertEqual(len(m.reference_hashes(self.job,2)),3)

    def test_one_to_six_continuation_preserves_first_file_and_budget(self):
        self.first(count=1)
        before=m.read(self.job)
        args=dict(context=self.context, prompts=['pose '+str(i) for i in range(1,6)],
                  approval_id='five-a', note='User explicitly approves five more')
        with self.assertRaises(ValueError):m.update(self.job,'continue-authorize',**args)
        self.confirm()
        d=m.update(self.job,'continue-authorize',**args)
        self.assertEqual(d['looks'][0]['output'],before['looks'][0]['output'])
        self.assertEqual(d['attempts'],1)
        self.assertEqual(d['authorization'],before['authorization'])
        self.assertEqual(len(d['looks']),6)
        self.assertFalse(d['complete'])
        with self.assertRaises(ValueError):m.update(self.job,'continue-authorize',**args)
        for n,color in enumerate(['yellow','purple','orange','black','white'],2):
            m.update(self.job,'reserve',look=n,ready=True,refs=m.reference_hashes(self.job,n),conversation=f'https://chatgpt.com/c/{n}')
            m.update(self.job,'returned',look=n,file=self.image(str(n),color))
            m.update(self.job,'accept',look=n,qa='qa-pass',note='QA')
        self.assertEqual(m.read(self.job)['attempts'],6)
        self.assertTrue(m.read(self.job)['complete'])
        self.assertEqual(m.read(self.job)['delivery_status'],'image-draft')

    def test_changed_context_and_fake_confirmation_are_rejected(self):
        self.first(count=1)
        with self.assertRaises(ValueError):m.update(self.job,'confirm-model',look=1,note='')
        self.confirm()
        for key,value in [('outfit','sku-b'),('style','old-money'),('size',[30,20]),('mode','C')]:
            context=copy.deepcopy(self.context);context[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                m.update(self.job,'continue-authorize',context=context,prompts=['x']*5,approval_id='a',note='Approved')

    def test_identity_only_without_garment_or_real_consent_cannot_initialize(self):
        with self.assertRaises(ValueError):
            m.create(self.job,[dict(path=str(self.face),role='identity-reference')],['pose'],(20,30),model=self.model,context=self.context)
        self.model['source_type']='real'
        with self.assertRaises(ValueError):self.create()
        self.assertFalse(self.job.exists())

    def test_original_identity_survives_new_outfit_and_is_not_replaced_by_latest(self):
        self.first();self.confirm()
        d=m.read(self.job)
        roles=m.references(self.job,d,2)
        self.assertEqual([r['role'] for r in roles],['garment-source','identity-reference','identity-only'])
        self.assertNotEqual(roles[1]['sha256'],roles[2]['sha256'])
        (self.job/roles[1]['file']).write_bytes(b'changed')
        with self.assertRaises(ValueError):m.export(self.job)

    def test_package_export_and_new_sku_keep_original_not_outfit_anchor(self):
        self.first(count=1)
        with self.assertRaises(ValueError):m.export_model(self.job, self.root/'package', 'A')
        self.confirm()
        card=m.export_model(self.job, self.root/'package', 'A')
        self.assertEqual(card['references'][0]['sha256'], m.digest(self.face))
        newer=self.image('new-garment', 'orange')
        job2=self.root/'job2'
        d=m.create(job2,[str(newer)],['new pose'],(20,30),context=dict(self.context,outfit='sku-b'),model_package=self.root/'package')
        self.assertEqual([r['sha256'] for r in d['references']], [m.digest(newer), m.digest(self.face)])
        self.assertIsNone(d['model_confirmation'])
        self.assertNotIn(m.digest(self.garment), [r['sha256'] for r in d['references']])
        with self.assertRaises(ValueError):m.create(self.root/'bad',[],['x'],(20,30),context=self.context,model_package=self.root/'package')

    def test_trial_other_than_pose_one_cannot_continue(self):
        self.context['first_pose']=2
        self.first(count=1);self.confirm()
        with self.assertRaises(ValueError):m.update(self.job,'continue-authorize',context=self.context,prompts=['x']*5,approval_id='x',note='Approved')

    def test_user_can_reselect_unconfirmed_first_model_with_explicit_retry_only(self):
        self.first(count=1)
        before=m.read(self.job)
        m.update(self.job,'reject-model',look=1,note='User dislikes the fuller body target')
        with self.assertRaises(ValueError):m.update(self.job,'reserve',look=1,ready=True,refs=m.reference_hashes(self.job,1),conversation='https://chatgpt.com/c/test')
        changed=dict(self.model,locked=['same original face','medium body proportions'])
        d=m.update(self.job,'retry-authorize',look=1,expected_attempt=1,approval_id='reselect-a',note='Explicit user retry and model-adjustment authority',prompt='pose one with medium proportions',model=changed)
        self.assertEqual(d['attempts'],1)
        self.assertEqual(d['model'],changed)
        self.assertEqual(d['looks'][0]['history'][0]['output'],before['looks'][0]['output'])
        self.assertEqual(d['looks'][0]['history'][0]['model'],self.model)
        m.export(self.job)
        text=(self.job/'handoff/look-1-attempt-2/prompt.txt').read_text()
        self.assertIn('medium body proportions',text)
        self.assertNotIn('natural fuller proportions',text)
        m.update(self.job,'reserve',look=1,ready=True,refs=m.reference_hashes(self.job,1),conversation='https://chatgpt.com/c/test')
        m.update(self.job,'returned',look=1,file=self.image('new-first','orange'))
        m.update(self.job,'accept',look=1,qa='qa-pass',note='QA')
        self.confirm()
        self.assertEqual(m.read(self.job)['attempts'],2)
        with self.assertRaises(ValueError):m.update(self.job,'reject-model',look=1,note='replace confirmed')

    def test_native_cli_confirm_export_import_and_continue_end_to_end(self):
        script=ROOT/'skills/threadtruth-studio/scripts/web-task.py'
        def cli(command,job=self.job,*args):
            result=subprocess.run([sys.executable,str(script),command,'--task',str(job),*map(str,args)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            return json.loads(result.stdout)
        spec=self.root/'spec.json'
        spec.write_text(json.dumps(dict(route='codex_native',references=[dict(path=str(self.garment),role='garment-source'),dict(path=str(self.face),role='identity-reference')],prompts=['pose one'],size=[20,30],model=self.model,context=self.context)))
        cli('init',self.job,'--spec',spec)
        cli('authorize',self.job,'--limit',1,'--note','Actual explicit first-image authority')
        cli('reserve',self.job,'--look',1,'--ready','--refs',*m.reference_hashes(self.job,1))
        cli('returned',self.job,'--look',1,'--file',self.image('cli-first','green'))
        cli('accept',self.job,'--look',1,'--qa','qa-pass','--note','Technical QA')
        cli('reject-model',self.job,'--look',1,'--note','User requests medium proportions')
        patch_file=self.root/'patch.txt';patch_file.write_text('pose one with medium proportions')
        model_file=self.root/'model-patch.json'
        changed=dict(self.model,locked=['same original face','medium body proportions'])
        model_file.write_text(json.dumps(dict(model=changed)))
        result=cli('retry-authorize',self.job,'--look',1,'--expected-attempt',1,'--approval-id','cli-adjust','--note','Actual one-image retry plus adjustment authority','--prompt-file',patch_file,'--model-spec',model_file)
        self.assertEqual(result['model'],changed)
        cli('reserve',self.job,'--look',1,'--ready','--refs',*m.reference_hashes(self.job,1))
        cli('returned',self.job,'--look',1,'--file',self.image('cli-second','orange'))
        cli('accept',self.job,'--look',1,'--qa','qa-pass','--note','Technical QA')
        cli('confirm-model',self.job,'--look',1,'--note','Actual first-image human acceptance')
        package=self.root/'cli-package'
        cli('export-model',self.job,'--destination',package,'--name','A')
        continuation=self.root/'continue.json'
        continuation.write_text(json.dumps(dict(context=self.context,prompts=['pose '+str(n) for n in range(2,7)])))
        result=cli('continue-authorize',self.job,'--spec',continuation,'--approval-id','cli-five','--note','Actual five-image authority')
        self.assertEqual((result['attempts'],len(result['looks'])),(2,6))
        spec.write_text(json.dumps(dict(route='codex_native',references=[str(self.garment)],model_package=str(package),prompts=['pose one'],size=[20,30],context=dict(self.context,outfit='new-sku'))))
        result=cli('init',self.root/'cli-new','--spec',spec)
        self.assertEqual(result['references'][1]['sha256'],m.digest(self.face))
        self.assertIsNone(result['model_confirmation'])

    def test_native_handoff_names_actual_native_route(self):
        self.create(route='codex_native');m.export(self.job)
        readme=(self.job/'handoff/README.md').read_text()
        self.assertIn('Codex',readme)
        self.assertNotIn('网页',readme)
        d=m.update(self.job,'authorize',limit=6,note='Approved')
        self.assertEqual(d['authorization']['destination'],'codex_native')

    def test_aesthetic_reference_remains_non_identity(self):
        self.model['source_type']='new'
        refs=[dict(path=str(self.garment),role='garment-source'),dict(path=str(self.face),role='aesthetic-reference')]
        m.create(self.job,refs,['pose'],(20,30),model=self.model,context=self.context)
        m.export(self.job)
        prompt=(self.job/'handoff/look-1/prompt.txt').read_text()
        self.assertIn('aesthetic only; do not copy identity',prompt)


if __name__ == '__main__':unittest.main()
