"""Synthetic offline regressions: user revision, garment evidence and actual exports."""
import copy
import importlib.util
import json
import hashlib
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('plan_revision_task',ROOT/'skills/threadtruth-studio/scripts/web-task.py')
task=importlib.util.module_from_spec(spec);spec.loader.exec_module(task)


class PlanRevisionTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name);self.job=self.root/'preview'
        self.front=self.image('front','red');self.back=self.image('back','blue')
        self.model=dict(source_type='new',scope='full',subject='adult female model',
            locked=['mature adult','tied-back hair'],adjustable=[],consent_note='')
        self.context=dict(outfit='sku',style='nordic-minimal',mode='C',output_form='human',
            size=[60,40],first_pose=1,purpose='preview-grid')

    def image(self,name,color):
        p=self.root/(name+'.png');Image.new('RGB',(60,40),color).save(p);return p

    def plan(self,back=False):
        coverage=[dict(sha256=task.digest(self.front),views=['front','front-side'],usable=True,same_sku=True,note='Synthetic front reviewed')]
        if back:coverage.append(dict(sha256=task.digest(self.back),views=['back'],usable=True,same_sku=True,note='Synthetic same-SKU back reviewed'))
        return task.shot_helper().default_plan('sku',coverage)

    def create(self,plan=None):
        refs=[self.front,self.back] if plan and plan['route']=='A' else [self.front]
        return task.create(self.job,refs,['Gallery lighting and negative space.'],[60,40],
            model=self.model,context=self.context,shot_plan=plan)

    def reserve(self,job=None):
        job=job or self.job;d=task.read(job)
        return task.update(job,'reserve',look=1,ready=True,refs=task.reference_hashes(job,1),
            expected_plan_sha256=task.plan_fingerprint(d),expected_prompt_sha256=d['looks'][0]['prompt_sha256'])

    def returned(self,plan=None,qa='accepted'):
        self.create(plan);task.update(self.job,'authorize',limit=1,note='Synthetic one-request approval')
        self.reserve();task.update(self.job,'returned',look=1,file=self.image('grid','yellow'))
        task.update(self.job,'accept' if qa=='accepted' else 'reject',look=1,qa='qa-pass',note='Synthetic visual review')

    def revise(self,**extra):
        d=task.read(self.job)
        return task.update(self.job,'revise-preview',look=1,note='User asks for long hair; retain gallery and poses',
            expected_output_sha256=d['looks'][0].get('output',{}).get('sha256','0'*64),
            prompt='Gallery lighting and negative space.',**extra)

    def retry(self,**extra):
        d=task.read(self.job)
        return task.update(self.job,'retry-authorize',look=1,expected_attempt=d['looks'][0].get('attempt_number',1),
            approval_id='synthetic-'+str(d['attempts']),note='Synthetic explicit one-request retry approval',**extra)

    def test_accepted_preview_can_revise_without_fabricating_qa_failure(self):
        self.returned();before=task.read(self.job);changed=dict(self.model,locked=['mature adult','long loose hair'])
        d=self.revise(model=changed)
        self.assertEqual(d['looks'][0]['state'],'accepted');self.assertEqual(d['looks'][0]['qa'],'qa-pass')
        self.assertEqual(d['attempts'],1);self.assertEqual(d['model'],before['model'])
        self.assertEqual(len(d.get('retry_authorizations',[])),0)
        with self.assertRaises(ValueError):task.update(self.job,'finish-preview',decision='direction-confirmed',note='Cannot approve stale output')
        self.retry();d=task.read(self.job);self.assertEqual(d['model'],changed)
        self.assertEqual(d['looks'][0]['history'][0]['qa'],'qa-pass');self.assertEqual(d['attempts'],1)
        task.export(self.job);req=json.loads(next((self.job/'handoff').glob('*/request.json')).read_text())
        self.assertIn('long loose hair',req['prompt']);self.assertNotIn('tied-back hair',req['prompt'])
        with self.assertRaises(ValueError):task.update(self.job,'reserve',look=1,ready=True,refs=task.reference_hashes(self.job,1))
        self.reserve();self.assertEqual(task.read(self.job)['attempts'],2)

    def test_rejected_preview_can_change_model_and_handoff_inherits_latest(self):
        self.returned(qa='rejected');changed=dict(self.model,locked=['mature adult','long hair'])
        self.revise(model=changed);self.retry();self.reserve()
        task.update(self.job,'returned',look=1,file=self.image('new-grid','green'))
        task.update(self.job,'accept',look=1,qa='qa-pass',note='Synthetic accepted result')
        task.update(self.job,'finish-preview',decision='direction-confirmed',note='Synthetic direction acceptance')
        ctx=dict(self.context,purpose='delivery')
        child=task.create_from_preview(self.root/'delivery',self.job,dict(context=ctx,size=[60,40],prompts=['Gallery scene.']*6),note='Synthetic preparation only')
        self.assertEqual(child['model'],changed);self.assertIsNone(child['authorization'])
        self.assertIsNone(child['model_confirmation']);self.assertEqual(child['total_attempts'],2)
        self.assertEqual([r['role'] for r in child['references']],['garment-source'])

    def test_invalid_revision_is_atomic_and_no_identity_source_switch(self):
        self.returned();before=(self.job/'task.json').read_bytes()
        with self.assertRaises(ValueError):self.revise(model=dict(self.model,source_type='real'))
        self.assertEqual(before,(self.job/'task.json').read_bytes())
        with self.assertRaises(ValueError):task.update(self.job,'revise-preview',look=1,note='x',expected_output_sha256='0'*64,prompt='x')
        self.assertEqual(before,(self.job/'task.json').read_bytes())

    def test_pending_unknown_closed_are_not_revision_targets(self):
        self.create()
        with self.assertRaises(ValueError):self.revise()
        task.update(self.job,'authorize',limit=1,note='Synthetic one request');self.reserve()
        with self.assertRaises(ValueError):self.revise()
        task.update(self.job,'unknown',look=1)
        with self.assertRaises(ValueError):self.revise()

    def test_plan_route_and_relations_reach_real_request_and_handoff(self):
        for back in (False,True):
            with self.subTest(back=back):
                self.job=self.root/('A' if back else 'B');p=self.plan(back);self.returned(p)
                self.revise();self.retry();task.export(self.job)
                folder=next((self.job/'handoff').glob('look-*'))
                raw=json.loads((folder/'request.json').read_text())['prompt']
                self.assertIn('Framing: half-body',raw);self.assertIn('arms hanging naturally',raw)
                self.assertIn('BACK_TURN_GLANCE' if back else 'FRONT_RELAXED_STANDING',raw)
                self.assertEqual(raw.count('[Task shot plan]'),1)
                self.assertEqual(task.read(self.job)['shot_plan'],p)

    def test_route_b_rejects_back_claim_and_wrong_sku_or_unusable_back(self):
        p=self.plan();p['looks'][5]['master']='BACK_TURN_GLANCE'
        with self.assertRaises(ValueError):self.create(p)
        for field in ('usable','same_sku'):
            p=self.plan(True);p['coverage'][1][field]=False
            with self.assertRaises(ValueError):self.create(p)

    def test_invalid_reference_or_pose_does_not_create_task(self):
        for change in ('hash','pose','framing'):
            p=self.plan()
            if change=='hash':p['looks'][0]['reference_sha256s']=['f'*64]
            if change=='pose':p['looks'][0]['pose']=5
            if change=='framing':p['looks'][4]['framing']='full-body'
            with self.subTest(change=change),self.assertRaises(ValueError):self.create(p)
            self.assertFalse(self.job.exists())

    def test_adaptation_needs_note_and_explicit_mode(self):
        p=self.plan();p['looks'][4]['framing']='full-body';p['preservation']='adapted'
        with self.assertRaises(ValueError):self.create(p)
        p['adaptation_note']='User explicitly asks for full-body fifth frame'
        self.create(p)

    def test_plan_change_is_versioned_stale_handoff_blocked_and_no_free_retry(self):
        self.returned(self.plan());d=task.read(self.job);old=task.plan_fingerprint(d)
        p=copy.deepcopy(d['shot_plan']);p['preservation']='adapted';p['adaptation_note']='User wants full-body third';p['looks'][2]['framing']='full-body'
        self.revise(shot_plan=p);self.retry();d=task.read(self.job)
        self.assertNotEqual(task.plan_fingerprint(d),old)
        with self.assertRaises(ValueError):task.update(self.job,'reserve',look=1,ready=True,refs=task.reference_hashes(self.job,1),expected_plan_sha256=old)
        self.assertEqual(d['attempts'],1);self.assertEqual(d['looks'][0]['history'][0]['shot_plan']['looks'][2]['framing'],'half-body')

    def test_current_factor_replacement_removes_old_conditions(self):
        f=dict(name='hair',value='tied-back hair',status='target',source='recommendation',confirmed=False)
        model=dict(self.model,factors=[f]);changed=task.models.replace_factors(model,[dict(f,value='long loose hair',source='user')])
        self.assertNotIn('tied-back hair',changed['locked']);self.assertIn('long loose hair',changed['locked'])
        self.assertIn('mature adult',changed['locked']);task.models.validate_model(changed)

    def test_add_back_reference_adopts_route_a_without_resetting_budget(self):
        self.returned(self.plan());p=self.plan(True)
        self.revise(shot_plan=p,garment_references=[dict(path=str(self.back),sha256=task.digest(self.back))])
        self.assertEqual(len(task.read(self.job)['references']),1)
        self.retry();d=task.read(self.job)
        self.assertEqual(d['shot_plan']['route'],'A');self.assertEqual(len(d['references']),2)
        self.assertEqual(d['attempts'],1);self.assertEqual(d['authorization']['limit'],1)
        self.assertEqual(d['looks'][0]['history'][0]['shot_plan']['route'],'B')
        task.export(self.job);raw=json.loads(next((self.job/'handoff').glob('*/request.json')).read_text())
        self.assertEqual(len(raw['referenced_image_paths']),2)
        self.assertIn('BACK_TURN_GLANCE',raw['prompt'])

    def test_changed_proposed_source_is_not_adopted(self):
        self.returned(self.plan());self.revise(shot_plan=self.plan(True),
            garment_references=[dict(path=str(self.back),sha256=task.digest(self.back))])
        before=(self.job/'task.json').read_bytes()
        Image.new('RGB',(60,40),'purple').save(self.back)
        with self.assertRaises(ValueError):self.retry()
        self.assertEqual(before,(self.job/'task.json').read_bytes())

    def test_stopping_with_unrendered_revision_does_not_allow_handoff(self):
        self.returned();self.revise(model=dict(self.model,locked=['long hair']))
        task.update(self.job,'finish-preview',decision='stop',note='Synthetic stop')
        spec=dict(context=dict(self.context,purpose='delivery'),size=[60,40],prompts=['x'])
        with self.assertRaises(ValueError):task.create_from_preview(self.root/'child',self.job,spec,note='x')
        with self.assertRaises(ValueError):self.revise()

    def test_correction_cap_survives_normal_aesthetic_revision(self):
        self.returned()
        for i in range(3):
            self.revise();self.retry();self.reserve()
            task.update(self.job,'returned',look=1,file=self.image('revision-'+str(i),['green','purple','orange'][i]))
            task.update(self.job,'accept',look=1,qa='qa-pass',note='Synthetic technical acceptance')
        self.revise()
        with self.assertRaises(ValueError):self.retry()
        self.assertEqual(task.read(self.job)['attempts'],4)

    def test_handoff_keeps_shot_plan_but_does_not_inherit_preview_authorization(self):
        self.returned(self.plan());task.update(self.job,'finish-preview',decision='direction-confirmed',note='Synthetic direction')
        ctx=dict(self.context,purpose='delivery',first_pose=3)
        child=task.create_from_preview(self.root/'child',self.job,dict(context=ctx,size=[60,40],prompts=['Gallery.']),note='Synthetic one independent shot')
        self.assertEqual(child['shot_plan']['looks'][0]['pose'],3)
        self.assertIsNone(child['authorization']);self.assertEqual(child['total_attempts'],1)
        task.export(self.root/'child');raw=json.loads(next((self.root/'child/handoff').glob('*/request.json')).read_text())['prompt']
        self.assertIn('Shot 3: UPRIGHT_SEATED',raw);self.assertNotIn('Shot 1:',raw)

    def test_single_to_six_retains_original_shot_and_requires_new_plan(self):
        plan=self.plan();full=copy.deepcopy(plan);plan['looks']=plan['looks'][:1]
        context=dict(self.context,purpose='delivery')
        task.create(self.job,[self.front],['Gallery.'],[60,40],model=self.model,context=context,shot_plan=plan)
        task.update(self.job,'authorize',limit=1,note='Synthetic one');self.reserve()
        task.update(self.job,'returned',look=1,file=self.image('single','yellow'))
        task.update(self.job,'accept',look=1,qa='qa-pass',note='Synthetic QA')
        task.update(self.job,'confirm-model',look=1,note='Synthetic actual image acceptance')
        args=dict(note='Synthetic five additional calls',approval_id='five',prompts=['Gallery.']*5,context=context)
        with self.assertRaises(ValueError):task.update(self.job,'continue-authorize',**args)
        d=task.update(self.job,'continue-authorize',shot_plan=full,**args)
        self.assertEqual(len(d['looks']),6);self.assertEqual(d['attempts'],1)
        task.check_evidence(self.job,d)

    def test_unusable_or_other_sku_inputs_are_not_actual_attachments(self):
        plan=self.plan();plan['coverage'].append(dict(sha256=task.digest(self.back),views=['back'],usable=True,same_sku=False,note='Different SKU, excluded'))
        task.create(self.job,[self.front,self.back],['Gallery.'],[60,40],model=self.model,context=self.context,shot_plan=plan)
        task.export(self.job);folder=next((self.job/'handoff').glob('*/request.json')).parent
        self.assertEqual(len(json.loads((folder/'request.json').read_text())['referenced_image_paths']),1)
        self.assertIn(task.digest(self.back),json.loads((folder/'manifest.json').read_text())['omitted_reference_sha256s'])

    def test_conflicting_model_blocks_cannot_be_exported_as_current(self):
        self.returned();before=(self.job/'task.json').read_bytes()
        with self.assertRaises(ValueError):
            task.update(self.job,'revise-preview',look=1,note='Synthetic revision',expected_output_sha256=task.read(self.job)['looks'][0]['output']['sha256'],
                model=dict(self.model,locked=['long hair']),prompt='Fixed model conditions: tied-back hair')
        self.assertEqual(before,(self.job/'task.json').read_bytes())

    def test_duplicate_factor_and_mismatched_locked_values_rejected(self):
        f=dict(name='hair',value='tied-back hair',status='target',source='recommendation',confirmed=False)
        with self.assertRaises(ValueError):task.models.validate_model(dict(self.model,factors=[f,f]))
        with self.assertRaises(ValueError):task.models.validate_model(dict(self.model,factors=[dict(f,value='long hair')]))

    def test_route_requires_front_and_selected_source_views(self):
        p=self.plan(True);p['coverage']=p['coverage'][1:]
        with self.assertRaises(ValueError):self.create(p)
        p=self.plan();p['looks'][0]['garment_views']=['back']
        with self.assertRaises(ValueError):self.create(p)

    def test_front_pose_cannot_select_only_back_evidence(self):
        p=self.plan(True);p['looks'][3].update(garment_views=['back'],reference_sha256s=[task.digest(self.back)])
        with self.assertRaises(ValueError):self.create(p)

    def test_conflicting_pending_prompt_is_rejected_without_poisoning_ledger(self):
        self.create(self.plan());before=(self.job/'task.json').read_bytes();d=task.read(self.job)
        with self.assertRaises(ValueError):
            task.update(self.job,'revise-pending',look=1,note='Synthetic explicit plan change',
                expected_prompt_sha256=d['looks'][0]['prompt_sha256'],prompt='[Task shot plan]\nobsolete\n[/Task shot plan]')
        self.assertEqual(before,(self.job/'task.json').read_bytes());task.export(self.job)

    def test_real_face_selection_can_adopt_new_garment_back_without_new_face_view(self):
        face=self.image('face','green');fh=task.digest(face)
        model=dict(self.model,source_type='real',consent_note='Synthetic express likeness permission')
        looks=[dict(body_action='Natural agreed body arrangement',head_view='near-front',gaze='looking at camera',face_visible=True,
            reference_sha256s=[task.digest(self.front),fh],selection_note='Original front and original face retained') for _ in range(6)]
        face_plan=dict(primary_identity_sha256=fh,coverage=[dict(sha256=fh,views=['front'],note='Synthetic original front reviewed')],looks=looks)
        task.create(self.job,[dict(path=str(self.front),role='garment-source'),dict(path=str(face),role='identity-reference')],
            ['Gallery.'],[60,40],model=model,context=self.context,shot_plan=self.plan(),real_face_plan=face_plan)
        task.update(self.job,'authorize',limit=1,note='Synthetic one');self.reserve()
        task.update(self.job,'returned',look=1,file=self.image('real-grid','purple'))
        task.update(self.job,'accept',look=1,qa='qa-pass',note='Synthetic QA')
        self.revise(shot_plan=self.plan(True),garment_references=[dict(path=str(self.back),sha256=task.digest(self.back))]);self.retry()
        d=task.read(self.job);self.assertEqual(d['real_face_plan']['coverage'],face_plan['coverage'])
        self.assertEqual(d['real_face_plan']['primary_identity_sha256'],fh)
        self.assertFalse(d['real_face_plan']['looks'][5]['face_visible'])
        task.export(self.job);task.check_evidence(self.job,d)

    def test_planned_continuation_counts_actual_selection_not_whole_inventory(self):
        refs=[self.front]+[self.image('unused-'+str(i),color) for i,color in enumerate(['green','purple','orange','black'])]
        full=self.plan();single=copy.deepcopy(full);single['looks']=single['looks'][:1];context=dict(self.context,purpose='delivery')
        task.create(self.job,refs,['Gallery.'],[60,40],model=self.model,context=context,shot_plan=single)
        task.update(self.job,'authorize',limit=1,note='Synthetic one');self.reserve()
        task.update(self.job,'returned',look=1,file=self.image('single-many','yellow'))
        task.update(self.job,'accept',look=1,qa='qa-pass',note='Synthetic QA')
        task.update(self.job,'confirm-model',look=1,note='Synthetic acceptance')
        d=task.update(self.job,'continue-authorize',note='Synthetic +5',approval_id='five',prompts=['Gallery.']*5,context=context,shot_plan=full)
        self.assertEqual(len(d['looks']),6);self.assertEqual(len(task.references(self.job,d,2)),2)

    def test_cli_candidate_retry_export_uses_current_plan_manifest(self):
        self.returned(self.plan());d=task.read(self.job);spec=self.root/'revision.json'
        spec.write_text(json.dumps(dict(model=dict(self.model,locked=['long hair']),prompt='Gallery.')))
        script=ROOT/'skills/threadtruth-studio/scripts/web-task.py'
        for args in [
            ['revise-preview','--task',str(self.job),'--look','1','--spec',str(spec),'--note','Synthetic feedback','--expected-output-sha256',d['looks'][0]['output']['sha256']],
            ['retry-authorize','--task',str(self.job),'--look','1','--expected-attempt','1','--approval-id','cli-one','--note','Synthetic explicit one retry'],
            ['export','--task',str(self.job)],
        ]:
            result=subprocess.run([sys.executable,str(script),*args],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
        manifest=json.loads(next((self.job/'handoff').glob('*/manifest.json')).read_text())
        self.assertEqual(manifest['current_plan_sha256'],task.plan_fingerprint(task.read(self.job)))
        self.assertEqual(task.read(self.job)['attempts'],1)

    def test_case_snapshot_binds_existing_pose_and_style_assets(self):
        record=json.loads((ROOT/'evals/case-quality-baseline.json').read_text())
        self.assertEqual(len([r for r in record['cases'] if r['kind']=='pose']),6)
        self.assertEqual(len([r for r in record['cases'] if r['kind']=='photography']),24)
        for item in record['cases']:
            self.assertEqual(hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest(),item['sha256'])
        self.assertTrue(record['unknown'])

    def test_current_model_block_cannot_be_combined_with_obsolete_extra_clause(self):
        raw=task.models.apply_conditions('Gallery.',self.model)
        with self.assertRaises(ValueError):task.models.apply_conditions(raw+'\nFixed model conditions: long hair',self.model)
        self.assertEqual(raw.count('[Current model conditions]'),1)

if __name__=='__main__':unittest.main()
