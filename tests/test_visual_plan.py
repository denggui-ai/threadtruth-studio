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

    def test_cli_accepts_plan_without_free_prompt_and_manifest_contract(self):
        spec=dict(references=[str(self.front)],size=[60,40],context=self.context,model=self.model,visual_plan=self.plan(),shot_plan=self.shot_plan(1))
        path=self.root/'spec.json';path.write_text(json.dumps(spec))
        result=subprocess.run([sys.executable,str(ROOT/'skills/threadtruth-studio/scripts/web-task.py'),'init','--task',str(self.job),'--spec',str(path)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['prompt_contract_version'],2)
        raw,manifest=self.exported_prompt();self.assertEqual(manifest['prompt_contract_version'],2)


if __name__=='__main__':unittest.main()
