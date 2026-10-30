"""Frozen visual compiler, lifecycle and recovery regressions; no generation calls."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('visual_plan_task',ROOT/'skills/threadtruth-studio/scripts/web-task.py')
task=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(task)


class VisualPlanTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.job=self.root/'task'
        self.front=self.image('garment','red')
        self.context=dict(outfit='synthetic-sku',style='nordic-minimal',mode='C',
                          output_form='human',size=[60,40],first_pose=1)
        self.model=dict(source_type='new',scope='full',subject='adult female model',
                        locked=['mature adult','tied-back hair'],adjustable=[],consent_note='')

    def image(self,name,color):
        path=self.root/(name+'.png');Image.new('RGB',(60,40),color).save(path);return path

    def component(self,name='nordic-minimal'):
        snapshot=dict(id=name,schema_version=1,photography=dict(scene='stone gallery'),
                      evidence=dict(visual_status='unverified',records=[]))
        return dict(id=name,version=1,sha256=task.object_hash(snapshot),snapshot=snapshot)

    def plan(self,count=1,pose=1,form='human',medium='photography'):
        return dict(version=1,objective='styled-editorial',output_medium=medium,output_form=form,
            style=dict(primary=self.component(),supporting=[],fusion_note=''),
            garment=dict(description='Original red garment with its existing marks.',
                         keep=['original color','visible construction','existing source lettering'],
                         source_sha256s=[task.digest(self.front)]),
            styling=[],photography=dict(scene='Quiet stone gallery',lighting='Soft light from upper left',
                composition='Clear silhouette with breathing space',palette='Neutral stone surroundings'),
            art=dict(direction='Geometric rhythm in the surroundings',techniques=[],
                     limits=['Do not alter garment structure or original identity']),negatives=['No invented garment details'],
            shots=[dict(slot=i,pose=i if count==6 else pose,scene='Stone gallery bay '+str(i),
                        lighting='Soft side light '+str(i),composition='Balanced negative space '+str(i)) for i in range(1,count+1)])

    def shot_plan(self,count=6,pose=1):
        coverage=[dict(sha256=task.digest(self.front),views=['front','front-side'],usable=True,
                       same_sku=True,note='Synthetic front-only original')]
        result=task.shot_helper().default_plan('synthetic-sku',coverage)
        if count==1:result['looks']=[result['looks'][pose-1]]
        return result

    def create(self,plan=None,**kw):
        if self.context['first_pose']!='custom' and self.context.get('purpose') not in ('model-check','correction-edit'):
            count=len((plan or self.plan())['shots'])
            kw.setdefault('shot_plan',self.shot_plan(count,self.context['first_pose']))
        return task.create(self.job,[self.front],None,[60,40],model=self.model,
                           context=self.context,visual_plan=plan or self.plan(),**kw)

    def reserve(self,look=1):
        d=task.read(self.job)
        return task.update(self.job,'reserve',look=look,ready=True,refs=task.reference_hashes(self.job,look),
            expected_plan_sha256=task.plan_fingerprint(d),expected_prompt_sha256=d['looks'][look-1]['prompt_sha256'])

    def accept(self,name='output',color='yellow'):
        self.reserve();task.update(self.job,'returned',look=1,file=self.image(name,color))
        return task.update(self.job,'accept',look=1,qa='qa-pass',note='Synthetic reviewed image')

    def returned_preview(self):
        self.context['purpose']='preview-grid';self.create(self.plan(6),shot_plan=self.shot_plan())
        task.update(self.job,'authorize',limit=1,note='Synthetic one-call authority')
        return self.accept()

    def exported_prompt(self,job=None):
        job=job or self.job;task.export(job)
        folder=sorted((job/'handoff').glob('look-*'))[-1]
        return (folder/'prompt.txt').read_text(),json.loads((folder/'manifest.json').read_text())

    def test_structured_creation_freezes_snapshot_and_compiles_actual_request(self):
        plan=self.plan();d=self.create(plan)
        self.assertEqual(d['schema_version'],2);self.assertEqual(d['prompt_contract_version'],2)
        self.assertEqual(d['looks'][0]['prompt'],task.visual_helper().compile_prompt(plan,1))
        plan['photography']['scene']='Changed live draft'
        raw,manifest=self.exported_prompt()
        self.assertIn('Quiet stone gallery',raw);self.assertNotIn('Changed live draft',raw)
        self.assertEqual(manifest['visual_plan'],d['visual_plan'])
        self.assertEqual(manifest['visual_plan_sha256'],task.object_hash(d['visual_plan']))
        self.assertEqual(manifest['tool_prompt_sha256'],hashlib.sha256(raw.encode()).hexdigest())
        request=json.loads(next((self.job/'handoff').glob('*/request.json')).read_text())
        self.assertEqual(request['prompt'],raw);self.assertEqual(raw.count('[Task visual plan]'),1)
        self.assertIn('existing source garment marks',raw)

    def test_native_and_web_prompts_share_exact_compiler_bytes(self):
        self.create();native,_=self.exported_prompt()
        self.job=self.root/'web';self.create(route='chatgpt_web');web,_=self.exported_prompt()
        self.assertEqual(native,web)
        self.assertEqual(list((self.job/'handoff').glob('*/request.json')),[])

    def test_all_objectives_media_and_five_forms_retain_identity_boundary(self):
        for objective in task.visual_helper().OBJECTIVES:
            for medium in task.visual_helper().MEDIA:
                for form in task.visual_helper().OUTPUT_FORMS:
                    with self.subTest(objective=objective,medium=medium,form=form):
                        job=self.root/(objective+'-'+medium+'-'+form)
                        context=dict(self.context,output_form=form);plan=self.plan(form=form,medium=medium);plan['objective']=objective
                        identity=form in ('human','faceless')
                        d=task.create(job,[self.front],None,[60,40],identity,model=self.model if identity else None,
                                      context=context,visual_plan=plan,shot_plan=self.shot_plan(1) if identity else None)
                        raw,_=self.exported_prompt(job)
                        self.assertIn('Output presentation: '+form,raw)
                        self.assertIn('Output medium: '+medium,raw)
                        self.assertNotIn('photorealistic',raw)
                        self.assertEqual('[Current model conditions]' in raw,identity)
                        if not identity:self.assertIn('Non-portrait garment display',raw)
                        self.assertEqual(d['identity'],identity)

    def test_nonportrait_cannot_bypass_model_or_reference_rules(self):
        plan=self.plan(form='flat-lay');context=dict(self.context,output_form='flat-lay')
        with self.assertRaises(ValueError):
            task.create(self.job,[self.front],None,[60,40],True,context=context,visual_plan=plan)
        face=self.image('face','blue')
        with self.assertRaises(ValueError):
            task.create(self.job,[dict(path=self.front,role='garment-source'),dict(path=face,role='identity-reference')],
                        None,[60,40],False,context=context,visual_plan=plan)
        self.assertFalse(self.job.exists())

    def test_numbered_human_requires_shot_plan_while_custom_and_diagnostic_keep_their_contracts(self):
        with self.assertRaisesRegex(ValueError,'require a reviewed source-backed shot_plan'):
            task.create(self.job,[self.front],None,[60,40],model=self.model,context=self.context,visual_plan=self.plan())
        self.context.update(first_pose='custom',pose_description='Relaxed standing at an oblique angle')
        self.create(self.plan(pose='custom'))
        raw,_=self.exported_prompt();self.assertIn('Explicit user presentation: Relaxed standing',raw)
        self.job=self.root/'diagnostic';self.context.pop('pose_description');self.context.update(first_pose=1,purpose='model-check')
        d=self.create();self.assertNotIn('shot_plan',d)

    def test_nonportrait_preview_to_six_keeps_explicit_arrangements(self):
        self.context.update(output_form='flat-lay',purpose='preview-grid')
        p=self.plan(6,form='flat-lay')
        for i,shot in enumerate(p['shots'],1):shot['composition']='Explicit garment arrangement '+str(i)
        task.create(self.job,[self.front],None,[60,40],False,context=self.context,visual_plan=p)
        task.update(self.job,'authorize',limit=1,note='One preview');self.accept()
        task.update(self.job,'finish-preview',decision='direction-confirmed',note='Actual reviewed arrangements')
        child=self.root/'flat-delivery'
        d=task.create_from_preview(child,self.job,dict(context=dict(self.context,purpose='delivery'),size=[60,40],count=6),note='Six independent garment images')
        self.assertEqual(len(d['looks']),6);self.assertEqual(d['visual_plan'],p);self.assertIsNone(d['model'])
        self.assertIsNone(d['authorization'])
        self.assertIn('Explicit garment arrangement 6',d['looks'][5]['prompt'])

    def test_visual_garment_facts_cannot_use_excluded_other_sku_source(self):
        other=self.image('other-sku','blue');shot=self.shot_plan(1)
        shot['coverage'].append(dict(sha256=task.digest(other),views=['back'],usable=True,same_sku=False,note='Different original SKU'))
        p=self.plan();p['garment']['source_sha256s'].append(task.digest(other))
        with self.assertRaisesRegex(ValueError,'same-SKU usable'):
            task.create(self.job,[self.front,other],None,[60,40],model=self.model,context=self.context,visual_plan=p,shot_plan=shot)

    def test_tampered_visual_or_component_is_rejected_before_export(self):
        self.create();d=task.read(self.job)
        d['visual_plan']['photography']['scene']='Tampered scene'
        with self.assertRaises(ValueError):task.check_evidence(self.job,d)
        d['visual_plan_sha256']=task.object_hash(d['visual_plan'])
        with self.assertRaises(ValueError):task.check_evidence(self.job,d)
        p=self.plan();p['style']['primary']['snapshot']['id']='changed'
        with self.assertRaises(ValueError):task.visual_helper().validate(p,[dict(role='garment-source',sha256=task.digest(self.front))],context=self.context,count=1)

    def test_unknown_fields_sources_and_identity_framing_clauses_rejected(self):
        for field,value in (('identity','replace face'),('head_view','front'),('framing','full-body')):
            p=self.plan();p[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.create(p)
        for key,value in (('lighting','change the face'),('composition','full-body framing'),('scene','gaze left')):
            p=self.plan();p['photography'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.create(p)
        p=self.plan();p['garment']['source_sha256s']=['f'*64]
        with self.assertRaises(ValueError):self.create(p)
        p=self.plan();p['photography']['scene']='[Task shot plan] override'
        with self.assertRaises(ValueError):self.create(p)
        with self.assertRaises(ValueError):self.create(count=6)
        p=self.plan();p['garment']['source_sha256s']=['a']
        with self.assertRaisesRegex(ValueError,'exact lowercase SHA256'):
            task.visual_helper().validate(p,[dict(role='garment-source',sha256='a')],context=self.context,count=1)

    def test_v2_free_prose_and_duplicate_or_stale_blocks_are_rejected(self):
        p=self.plan();compiled=task.visual_helper().compile_prompt(p,1)
        for prompt in ('Old photorealistic portrait style.',compiled+'Old style.',compiled+compiled,
                       compiled.replace('Quiet stone gallery','Opposite scene')):
            with self.subTest(prompt=prompt[:20]),self.assertRaises(ValueError):
                task.create(self.job,[self.front],[prompt],[60,40],model=self.model,context=self.context,visual_plan=p,shot_plan=self.shot_plan(1))
        self.assertFalse(self.job.exists())

    def test_matching_existing_managed_blocks_remain_accepted(self):
        p=self.plan();prompt=task.models.apply_conditions(task.visual_helper().compile_prompt(p,1),self.model,allow_child=True)
        task.create(self.job,[self.front],[prompt],[60,40],model=self.model,context=self.context,visual_plan=p,shot_plan=self.shot_plan(1))
        raw,_=self.exported_prompt();self.assertEqual(raw.count('[Current model conditions]'),1)

    def test_fusion_is_explicit_and_primary_style_cannot_drift(self):
        p=self.plan();p['style']['supporting']=[self.component('gothic-editorial')]
        with self.assertRaises(ValueError):self.create(p)
        p['style']['fusion_note']='User selected gothic geometry in surroundings only'
        self.create(p);raw,_=self.exported_prompt();self.assertIn('Explicit fusion scope',raw)
        p['style']['primary']=self.component('other-style')
        with self.assertRaises(ValueError):task.visual_helper().validate(p,[dict(role='garment-source',sha256=task.digest(self.front))],context=self.context,count=1)

    def test_cultural_profile_freezes_source_and_preserves_form(self):
        p=self.plan();p['culture_profile']=self.component('hanfu-form-specific')
        self.create(p);raw,_=self.exported_prompt()
        self.assertIn('Cultural form profile: hanfu-form-specific',raw)
        self.assertIn('do not invent a dynasty',raw)

    def test_preview_revision_adopts_new_visual_only_with_retry_authority(self):
        initial=self.returned_preview();old_hash=task.plan_fingerprint(initial)
        p=copy.deepcopy(initial['visual_plan']);p['photography']['scene']='New arch gallery'
        candidate=task.update(self.job,'revise-preview',look=1,note='Actual scene revision',
            expected_output_sha256=initial['looks'][0]['output']['sha256'],visual_plan=p)
        self.assertEqual(candidate['visual_plan'],initial['visual_plan']);self.assertEqual(candidate['attempts'],1)
        self.assertIn('New arch gallery',candidate['preview_revision']['candidate']['prompt'])
        d=task.update(self.job,'retry-authorize',look=1,expected_attempt=1,approval_id='retry-1',note='Explicit one-call retry')
        self.assertEqual(d['visual_plan'],p);self.assertEqual(d['attempts'],1)
        self.assertEqual(d['looks'][0]['history'][0]['visual_plan'],initial['visual_plan'])
        self.assertNotEqual(task.plan_fingerprint(d),old_hash)
        task.check_evidence(self.job,d);raw,_=self.exported_prompt();self.assertIn('New arch gallery',raw)
        with self.assertRaises(ValueError):
            task.update(self.job,'reserve',look=1,ready=True,refs=task.reference_hashes(self.job,1),expected_plan_sha256=old_hash)
        self.assertEqual(task.read(self.job)['attempts'],1)

    def test_preview_to_selected_delivery_keeps_latest_snapshot_without_authority(self):
        d=self.returned_preview();p=copy.deepcopy(d['visual_plan']);p['photography']['scene']='Latest accepted setting'
        task.update(self.job,'revise-preview',look=1,note='Scene change',expected_output_sha256=d['looks'][0]['output']['sha256'],visual_plan=p)
        task.update(self.job,'retry-authorize',look=1,expected_attempt=1,approval_id='retry',note='One new call')
        self.accept('revised','green');task.update(self.job,'finish-preview',decision='direction-confirmed',note='Actual direction approval')
        child=self.root/'delivery';ctx=dict(self.context,purpose='delivery',first_pose=3)
        result=task.create_from_preview(child,self.job,dict(context=ctx,size=[60,40],count=1),note='Prepare selected independent shot')
        self.assertIsNone(result['authorization']);self.assertIsNone(result['model_confirmation'])
        self.assertEqual(result['total_attempts'],2);self.assertEqual(result['visual_plan']['shots'][0]['pose'],3)
        self.assertEqual(result['visual_plan']['shots'][0]['slot'],1)
        self.assertEqual(result['shot_plan']['looks'][0]['pose'],3)
        raw,_=self.exported_prompt(child);self.assertIn('Latest accepted setting',raw)
        self.assertIn('presentation 3',raw);self.assertNotIn('presentation 1',raw)

    def test_single_to_six_requires_unchanged_first_and_shared_visual_plan(self):
        full=self.plan(6);single=task.visual_helper().subset(full,1)
        self.create(single);task.update(self.job,'authorize',limit=1,note='One image')
        self.accept();task.update(self.job,'confirm-model',look=1,note='Actual person approval')
        args=dict(approval_id='five',note='Five explicitly authorized images',context=self.context,shot_plan=self.shot_plan())
        with self.assertRaises(ValueError):task.update(self.job,'continue-authorize',**args)
        changed=copy.deepcopy(full);changed['photography']['lighting']='Changed light'
        with self.assertRaises(ValueError):task.update(self.job,'continue-authorize',visual_plan=changed,**args)
        d=task.update(self.job,'continue-authorize',visual_plan=full,**args)
        self.assertEqual(len(d['looks']),6);self.assertEqual(d['prompt_contract_version'],2)
        self.assertEqual(d['visual_plan_history'][0]['plan'],single)
        self.assertEqual(d['looks'][0]['prompt'],task.visual_helper().compile_prompt(single,1))
        task.check_evidence(self.job,d)

    def test_failure_recovery_does_not_drop_visual_plan_or_add_unapproved_calls(self):
        self.create();task.update(self.job,'authorize',limit=1,note='One image');self.reserve()
        receipt=self.root/'receipt.txt';receipt.write_text('Synthetic terminal failure')
        task.update(self.job,'failed',look=1,reason='Synthetic provider failure',failure_receipt=receipt)
        before=task.read(self.job)
        with self.assertRaises(ValueError):task.update(self.job,'retry-authorize',look=1,expected_attempt=1,approval_id='r',note='Retry',prompt=before['looks'][0]['prompt'])
        task.update(self.job,'reconcile-failure',look=1,expected_attempt=1,request_check_completed=True,note='Original request checked')
        d=task.update(self.job,'retry-authorize',look=1,expected_attempt=1,approval_id='r',note='Explicit one-call retry',prompt=before['looks'][0]['prompt'])
        self.assertEqual(d['visual_plan'],before['visual_plan']);self.assertEqual(d['attempts'],1)
        task.check_evidence(self.job,d);self.reserve();self.assertEqual(task.read(self.job)['attempts'],2)

    def test_contract_downgrade_and_orphan_contract_rejected(self):
        self.create();d=task.read(self.job)
        d['prompt_contract_version']=1
        with self.assertRaises(ValueError):task.check_evidence(self.job,d)
        d=task.read(self.job);d.pop('visual_plan');d.pop('visual_plan_sha256')
        with self.assertRaises(ValueError):task.check_evidence(self.job,d)
        d=task.read(self.job);d['looks'][0]['prompt_contract_version']=1
        with self.assertRaises(ValueError):task.check_evidence(self.job,d)

    def test_real_preview_keeps_original_view_gate_and_cannot_change_identity(self):
        self.context['purpose']='preview-grid'
        face=self.image('original-face','blue');face_hash=task.digest(face)
        model=dict(source_type='real',scope='face',subject='adult female model',
                   locked=['retain original facial features'],adjustable=[],consent_note='Actual likeness permission')
        refs=[dict(path=self.front,role='garment-source'),dict(path=face,role='identity-reference')]
        args=dict(model=model,context=self.context,visual_plan=self.plan(6),shot_plan=self.shot_plan())
        with self.assertRaises(ValueError):task.create(self.job,refs,None,[60,40],**args)
        cell=dict(body_action='relaxed standing',head_view='front',face_visible=True,gaze='toward camera',
                  reference_sha256s=[task.digest(self.front),face_hash],selection_note='Use original front and garment')
        real=dict(primary_identity_sha256=face_hash,coverage=[dict(sha256=face_hash,views=['front'],note='Reviewed original front')],
                  looks=[copy.deepcopy(cell) for _ in range(6)])
        unsupported=copy.deepcopy(real);unsupported['looks'][2]['head_view']='left-profile'
        with self.assertRaises(ValueError):task.create(self.job,refs,None,[60,40],real_face_plan=unsupported,**args)
        d=task.create(self.job,refs,None,[60,40],real_face_plan=real,**args)
        task.update(self.job,'authorize',limit=1,note='One real preview');self.accept()
        d=task.read(self.job)
        with self.assertRaises(ValueError):task.update(self.job,'revise-preview',look=1,
            expected_output_sha256=d['looks'][0]['output']['sha256'],note='Invalid identity change',
            model=dict(model,source_type='ai'),visual_plan=self.plan(6))
        self.assertEqual(d['real_face_plan'],real)
        self.assertEqual(d['references'][1]['sha256'],face_hash)

    def test_faceless_plan_cannot_override_visible_real_face_cells(self):
        face=self.image('face','blue');face_hash=task.digest(face)
        context=dict(self.context,output_form='faceless')
        model=dict(source_type='real',scope='face',subject='adult female model',locked=[],adjustable=[],consent_note='Actual likeness permission')
        real=dict(primary_identity_sha256=face_hash,coverage=[dict(sha256=face_hash,views=['front'],note='Reviewed original front')],
            looks=[dict(body_action='relaxed standing',head_view='front',face_visible=True,gaze='toward camera',
                reference_sha256s=[task.digest(self.front),face_hash],selection_note='Use original references')])
        with self.assertRaises(ValueError):task.create(self.job,[dict(path=self.front,role='garment-source'),
            dict(path=face,role='identity-reference')],None,[60,40],model=model,context=context,
            visual_plan=self.plan(form='faceless'),real_face_plan=real,shot_plan=self.shot_plan(1))

    def test_existing_preview_can_explicitly_adopt_v2_without_rewriting_history(self):
        self.context['purpose']='preview-grid'
        task.create(self.job,[self.front],['Legacy preview bytes.'],[60,40],model=self.model,context=self.context)
        task.update(self.job,'authorize',limit=1,note='One request');d=self.accept()
        task.update(self.job,'revise-preview',look=1,expected_output_sha256=d['looks'][0]['output']['sha256'],
                    visual_plan=self.plan(6),shot_plan=self.shot_plan(),note='Explicit structured visual revision')
        d=task.update(self.job,'retry-authorize',look=1,expected_attempt=1,approval_id='adopt',note='One v2 request')
        self.assertEqual(d['prompt_contract_version'],2)
        self.assertEqual(d['looks'][0]['history'][0]['prompt'],'Legacy preview bytes.')
        self.assertEqual(d['looks'][0]['history'][0]['prompt_contract_version'],1)
        task.check_evidence(self.job,d)

    def test_legacy_no_plan_preserves_prompt_bytes_and_fingerprint(self):
        frozen='Legacy authored prompt.\nPreserve exact trailing whitespace.  \n'
        d=task.create(self.job,[self.front],[frozen],[60,40],model=self.model,context=self.context)
        self.assertEqual(d['looks'][0]['prompt'],frozen);self.assertNotIn('visual_plan',d)
        self.assertEqual(task.plan_fingerprint(d),task.object_hash(dict(version=0,context=d['context'],model=d['model'],shot_plan=None)))
        raw,_=self.exported_prompt();self.assertIn(frozen,raw);self.assertNotIn('[Task visual plan]',raw)
        self.assertEqual(d['prompt_contract_version'],1)

    def rejected_delivery(self,route='codex_native'):
        shot=self.shot_plan();shot.update(preservation='adapted',adaptation_note='Synthetic reviewed shot arrangements')
        self.create(self.plan(6),route=route,shot_plan=shot)
        task.update(self.job,'authorize',limit=6,note='Synthetic six-image authority')
        for n in range(1,7):
            d=task.read(self.job)
            task.update(self.job,'reserve',look=n,ready=True,refs=task.reference_hashes(self.job,n),
                expected_plan_sha256=task.plan_fingerprint(d),expected_prompt_sha256=d['looks'][n-1]['prompt_sha256'],
                **({'conversation':'https://chatgpt.com/c/synthetic-case'} if route=='chatgpt_web' else {}))
            task.update(self.job,'returned',look=n,file=self.image('output-'+str(n),(n*30,40,80)))
            task.update(self.job,'reject' if n in (3,5) else 'accept',look=n,
                qa='qa-pass',note='Synthetic actual output review')
            if n==1:task.update(self.job,'confirm-model',look=1,note='Synthetic human accepts first person')
        return task.read(self.job)

    def crop_revision(self,d,n=3):
        shot=copy.deepcopy(d['shot_plan']);shot['looks'][n-1]['arrangement']='Retain the seated support and crop at the hips; lower coat remains beyond the picture edge.'
        visual=copy.deepcopy(d['visual_plan']);visual['shots'][n-1]['composition']='Shared floor and contact targets apply only to the current visible crop; do not widen the camera distance.'
        return dict(shot_plan=shot,visual_plan=visual)

    def test_rejected_delivery_plan_retry_preserves_other_outputs_and_paid_history(self):
        for route in ('codex_native','chatgpt_web'):
            with self.subTest(route=route):
                self.job=self.root/route;before=self.rejected_delivery(route);revision=self.crop_revision(before)
                original={n:task.handoff_prompt(before,before['looks'][n-1],task.references(self.job,before,n)) for n in range(1,7)}
                after=task.update(self.job,'retry-authorize',look=3,expected_attempt=1,approval_id='synthetic-retry-3',
                    note='Synthetic one additional request, not live authority',**revision)
                self.assertEqual(after['attempts'],6);self.assertEqual(after['authorization'],before['authorization'])
                self.assertEqual(after['model_confirmation'],before['model_confirmation'])
                self.assertEqual(after['model'],before['model']);self.assertEqual(after['references'],before['references'])
                self.assertEqual(after['looks'][2]['history'][0]['output'],before['looks'][2]['output'])
                self.assertEqual(after['looks'][2]['history'][0]['qa'],'qa-retry')
                self.assertEqual(after['looks'][2]['attempt_number'],2)
                self.assertEqual(len(after['retry_authorizations']),1)
                for n in (1,2,4,5,6):
                    self.assertEqual(after['looks'][n-1],before['looks'][n-1])
                    self.assertEqual(task.handoff_prompt(after,after['looks'][n-1],task.references(self.job,after,n)),original[n])
                task.export(self.job)
                folder=task.handoff_directory(self.job,after,after['looks'][2]);prompt=(folder/'prompt.txt').read_text()
                self.assertIn('crop at the hips',prompt);self.assertIn('do not widen the camera distance',prompt)
                self.assertNotEqual(task.plan_fingerprint(after),task.plan_fingerprint(before))
                with self.assertRaises(ValueError):
                    task.update(self.job,'reserve',look=3,ready=True,refs=task.reference_hashes(self.job,3),expected_plan_sha256=task.plan_fingerprint(before))
                self.assertEqual(task.read(self.job)['attempts'],6)
                if route=='chatgpt_web':
                    receipt=task.export_web_execution(self.job,3)
                    self.assertIn(prompt,Path(receipt['submission_file']).read_text())

    def test_delivery_retry_rejects_changes_outside_the_failed_arrangement_atomically(self):
        before=self.rejected_delivery();saved=(self.job/'task.json').read_bytes()
        for kind in ('other-shot','first-shot','shared-scene','framing','garment-reference','gaze','extra-look-field'):
            with self.subTest(kind=kind):
                revision=self.crop_revision(before)
                if kind=='other-shot':revision['shot_plan']['looks'][4]['arrangement']='Different pose'
                elif kind=='first-shot':revision['visual_plan']['shots'][0]['composition']='Different first image'
                elif kind=='shared-scene':revision['visual_plan']['photography']['scene']='Different room'
                elif kind=='framing':revision['shot_plan']['looks'][2]['framing']='full-body'
                elif kind=='garment-reference':revision['shot_plan']['looks'][2]['reference_sha256s']=[]
                elif kind=='gaze':revision['shot_plan']['looks'][2].update(head='Turn away',gaze='Far away')
                else:revision['visual_plan']['shots'][2]['unreviewed']='extra'
                with self.assertRaises(ValueError):
                    task.update(self.job,'retry-authorize',look=3,expected_attempt=1,approval_id='bad-'+kind,note='Synthetic rejected proposal',**revision)
                self.assertEqual((self.job/'task.json').read_bytes(),saved)

    def test_delivery_plan_retry_requires_exact_failed_output_and_no_unresolved_request(self):
        before=self.rejected_delivery();revision=self.crop_revision(before)
        for n,attempt in ((1,1),(2,1),(3,2)):
            with self.subTest(look=n,attempt=attempt):
                with self.assertRaises(ValueError):
                    task.update(self.job,'retry-authorize',look=n,expected_attempt=attempt,approval_id='bad',note='Synthetic',**revision)
        task.update(self.job,'retry-authorize',look=5,expected_attempt=1,approval_id='retry-5',note='Synthetic one request',
                    prompt=before['looks'][4]['prompt'])
        self.reserve(5)
        with self.assertRaises(ValueError):
            task.update(self.job,'retry-authorize',look=3,expected_attempt=1,approval_id='retry-3',note='Synthetic',**revision)

    def test_cli_can_compile_rejected_delivery_revision_from_structured_spec(self):
        before=self.rejected_delivery();revision=self.crop_revision(before)
        path=self.root/'retry-spec.json';path.write_text(json.dumps(revision))
        result=subprocess.run([sys.executable,str(ROOT/'skills/threadtruth-studio/scripts/web-task.py'),'retry-authorize',
            '--task',str(self.job),'--look','3','--spec',str(path),'--expected-attempt','1',
            '--approval-id','synthetic-cli','--note','Synthetic one-request approval'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(task.read(self.job)['looks'][2]['attempt_number'],2)

    def test_cli_accepts_plan_without_free_prompt_and_manifest_contract(self):
        spec=dict(references=[str(self.front)],size=[60,40],context=self.context,model=self.model,visual_plan=self.plan(),shot_plan=self.shot_plan(1))
        path=self.root/'spec.json';path.write_text(json.dumps(spec))
        result=subprocess.run([sys.executable,str(ROOT/'skills/threadtruth-studio/scripts/web-task.py'),'init','--task',str(self.job),'--spec',str(path)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['prompt_contract_version'],2)
        raw,manifest=self.exported_prompt();self.assertEqual(manifest['prompt_contract_version'],2)

    PERSONA='calm, detached, quietly confident; restrained editorial attitude'

    def persona_plan(self,**changes):
        plan=self.plan();plan.update(persona=self.PERSONA,
            persona_model_sha256=task.object_hash(task.models.validate_model(self.model,allow_child=True)))
        plan.update(changes);return plan

    def validate(self,plan,form='human'):
        return task.visual_helper().validate(plan,[dict(role='garment-source',sha256=task.digest(self.front))],
            context=dict(self.context,output_form=form),count=len(plan['shots']),identity=form in ('human','faceless'))

    def test_persona_renders_one_line_after_art_limits(self):
        plan=self.validate(self.persona_plan());rows=task.visual_helper().render(plan).split('\n')
        line='Style persona (yields to the declared model conditions): '+self.PERSONA
        self.assertEqual(rows.count(line),1)
        last_limit=max(i for i,row in enumerate(rows) if row.startswith('Art limit: '))
        self.assertEqual(rows.index(line),last_limit+1)
        self.assertNotIn(plan['persona_model_sha256'],'\n'.join(rows))
        self.assertEqual(task.visual_helper().compile_prompt(plan,1).count(line),1)

    def test_plan_without_persona_renders_golden_bytes_from_17db89b(self):
        # Hashes taken on 17db89b before any persona code existed (outputs/caiguang-wp5-persona-20261030/golden-render-17db89b.json).
        helper=task.visual_helper();sha=lambda text:hashlib.sha256(text.encode()).hexdigest()
        self.assertEqual(sha(helper.render(self.plan(1))),'ecaaf249e0ac611bdc31fd7df1cb97331ca59786185f87970521d82583408c3c')
        self.assertEqual(sha(helper.render(self.plan(6))),'04c445906fc3ef03990b60376ae4308111a241ea646858f816a2a7cce743d05e')
        self.assertEqual(sha(helper.compile_prompt(self.plan(1),1)),'3b81e7cce0eb407a17629139c07ca7cb8045944644a3d7050fe9d3ffc5183bd7')
        self.assertNotIn('Style persona',helper.render(self.validate(self.plan())))

    def test_persona_rejects_owned_words_empty_text_nonhuman_and_missing_model_hash(self):
        self.validate(self.persona_plan())
        for text in ('full-body relaxed attitude','direct gaze at the lens, calm','','   ',7):
            with self.subTest(text=text),self.assertRaises(ValueError):
                self.validate(self.persona_plan(persona=text))
        with self.assertRaises(ValueError):
            self.validate(self.persona_plan(),form='faceless')
        plan=self.persona_plan();del plan['persona_model_sha256']
        with self.assertRaises(ValueError):self.validate(plan)
        plan=self.persona_plan();del plan['persona']
        with self.assertRaises(ValueError):self.validate(plan)
        for bad in ('abc','A'*64,None):
            with self.subTest(sha=bad),self.assertRaises(ValueError):
                self.validate(self.persona_plan(persona_model_sha256=bad))

    def test_create_rejects_persona_plan_prepared_for_a_different_model(self):
        plan=self.persona_plan()
        self.model=dict(self.model,locked=['mature adult','short bob'])
        with self.assertRaisesRegex(ValueError,'different model'):self.create(plan)
        self.assertFalse((self.job/'task.json').exists())
        self.model=dict(self.model,locked=['mature adult','tied-back hair'])
        d=self.create(self.persona_plan())
        self.assertEqual(d['visual_plan']['persona'],self.PERSONA)
        self.assertIn('Style persona (yields to the declared model conditions): '+self.PERSONA,d['looks'][0]['prompt'])

    def test_legacy_task_without_persona_exports_card_palette_and_no_persona_line(self):
        # Same fixture path as the WP-1 compile_head smoke. Until WP-4e this pinned the whole prompt sha256 (eb0cea4c... at 17db89b, 8947e0db... after WP-4d),
        # so every card wording edit broke it. Byte-level golden for a card-free plan stays in test_plan_without_persona_renders_golden_bytes_from_17db89b.
        spec=importlib.util.spec_from_file_location('legacy_library',ROOT/'skills/threadtruth-studio/scripts/visual_library.py')
        library=importlib.util.module_from_spec(spec);spec.loader.exec_module(library)
        source=ROOT/'docs/demo/preview-sources/beige-blazer-denim-outfit/source.jpg';h=task.digest(source)
        garment=dict(description='Beige single-breasted blazer worn open over a white top with mid-blue straight denim; engineering fixture.',
                     keep=['Keep blazer colour, lapel shape, button count and denim wash unchanged.'],source_sha256s=[h])
        plan=library.prepare(dict(entry_id='korean-cold-editorial',garment=garment,inventory=[dict(role='garment-source',sha256=h)],
                                  count=1,first_pose=1,output_medium='photography',output_form='human'))
        self.assertNotIn('persona',plan)
        coverage=[dict(sha256=h,views=['front','front-side'],usable=True,same_sku=True,note='fixture front image')]
        shot=task.shot_helper().default_plan('wp1-fixture',coverage);shot['looks']=shot['looks'][:1]
        context=dict(outfit='wp1-fixture',style='korean-cold-editorial',mode='C',output_form='human',size=[1024,1536],first_pose=1)
        model=dict(source_type='new',scope='full',subject='adult female model',locked=[],adjustable=[],consent_note='')
        task.create(self.job,[source],None,[1024,1536],True,model=model,context=context,visual_plan=plan,shot_plan=shot,count=1)
        task.export(self.job)
        request=json.loads(sorted(self.job.glob('handoff/look-1-v*/request.json'))[-1].read_text())
        prompt=request['prompt'];rows=prompt.split('\n')
        card=json.loads((ROOT/'skills/threadtruth-studio/references/visual-library/cards/korean-cold-editorial.json').read_text())
        self.assertEqual([row for row in rows if row.startswith('Shared palette: ')],['Shared palette: '+card['photography']['palette']])
        self.assertNotIn('Style persona',prompt)
        self.assertNotIn(card['persona'],prompt)
        self.assertIn(garment['description'],prompt)

    def test_continuation_cannot_toggle_framing_guidance_behind_the_frozen_first_shot(self):
        # codex-review f70dd13 major: a v1 continuation could add framing_guidance while look 1 kept its legacy frozen block,
        # after which every check failed with a frozen-block conflict.
        for legacy in (True,False):
            with self.subTest(legacy_first_shot=legacy):
                self.job=self.root/('continuation-'+str(legacy))
                full=self.shot_plan()
                if legacy:full.pop('framing_guidance')
                single=copy.deepcopy(full);single['looks']=single['looks'][:1]
                self.create(self.plan(),shot_plan=single)
                task.update(self.job,'authorize',limit=1,note='One trial');self.accept()
                task.update(self.job,'confirm-model',look=1,note='Person accepted')
                toggled=copy.deepcopy(full)
                if legacy:toggled['framing_guidance']=1
                else:toggled.pop('framing_guidance')
                with self.assertRaisesRegex(ValueError,'framing guidance'):
                    task.update(self.job,'continue-authorize',approval_id='five',note='Continue',context=self.context,shot_plan=toggled,visual_plan=self.plan(6))
                after=task.update(self.job,'continue-authorize',approval_id='five',note='Continue',context=self.context,shot_plan=full,visual_plan=self.plan(6))
                self.assertEqual(len(after['looks']),6)
                task.check_evidence(self.job,task.read(self.job));task.export(self.job)

    def test_rejected_first_model_retry_rebinds_persona_without_other_plan_changes(self):
        # codex-review f70dd13 major: after reject-model the stale persona hash blocked every retry path.
        plan=self.persona_plan();self.create(plan)
        task.update(self.job,'authorize',limit=1,note='One trial');self.accept()
        task.update(self.job,'reject-model',look=1,note='Change casting conditions')
        changed=task.models.validate_model(dict(self.model,locked=['mature adult','short bob']),allow_child=True)
        rebound=copy.deepcopy(plan);rebound['persona_model_sha256']=task.object_hash(changed)
        args=dict(look=1,expected_attempt=1,approval_id='retry',note='Approved revised casting retry',model=changed)
        with self.assertRaisesRegex(ValueError,'different model'):
            task.update(self.job,'retry-authorize',**args,prompt=task.visual_helper().compile_prompt(plan,1))
        tampered=copy.deepcopy(rebound);tampered['photography']['scene']='Somewhere else'
        with self.assertRaisesRegex(ValueError,'only the persona'):
            task.update(self.job,'retry-authorize',**args,visual_plan=tampered)
        with self.assertRaisesRegex(ValueError,'only the persona'):
            task.update(self.job,'retry-authorize',**args,visual_plan=copy.deepcopy(plan))
        d=task.update(self.job,'retry-authorize',**args,visual_plan=rebound)
        self.assertEqual(d['model'],changed)
        self.assertEqual(d['visual_plan'],rebound);self.assertEqual(d['visual_plan_sha256'],task.object_hash(rebound))
        self.assertEqual(d['visual_plan_history'][-1]['plan'],plan)
        self.assertEqual(d['looks'][0]['state'],'pending');self.assertEqual(d['looks'][0]['attempt_number'],2)
        self.assertEqual(d['looks'][0]['history'][-1]['visual_plan'],plan)
        self.assertIn('Style persona (yields to the declared model conditions): '+self.PERSONA,d['looks'][0]['prompt'])
        task.check_evidence(self.job,d);self.reserve()

    def test_create_rejects_persona_plan_for_a_child_model(self):
        # codex-review f70dd13 minor: visual_library.prepare drops personas for children; direct structured creation only checked the hash.
        self.model=dict(self.model,subject='child model',locked=['age-appropriate modest presentation'])
        with self.assertRaisesRegex(ValueError,'child'):self.create(self.persona_plan())
        self.assertFalse((self.job/'task.json').exists())
        d=self.create(self.plan())
        self.assertNotIn('Style persona',d['looks'][0]['prompt'])


if __name__=='__main__':unittest.main()
