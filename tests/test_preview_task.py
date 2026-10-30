"""Preview bookkeeping with synthetic PNGs; no image-generation calls."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT/'skills/threadtruth-studio/scripts/web-task.py'
spec = importlib.util.spec_from_file_location('preview_ledger', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class PreviewTaskTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.job = self.root/'preview'
        self.ref = self.image('product', 'red')
        self.context = dict(outfit='sku', style='ecommerce-studio', mode='B',
                            output_form='human', size=[60, 40], first_pose=1,
                            purpose='preview-grid')

    def image(self, name, color, size=(60, 40)):
        path = self.root/(name+'.png')
        Image.new('RGB', size, color).save(path)
        return path

    def create(self, identity=True, **kw):
        return m.create(self.job, [self.ref], ['Six-panel direction preview'],
                        [60, 40], identity=identity, context=self.context, **kw)

    def reserve(self):
        return m.update(self.job, 'reserve', look=1, ready=True,
                        refs=m.reference_hashes(self.job, 1))

    def returned(self, accepted=True):
        self.create()
        m.update(self.job, 'authorize', limit=1, note='One synthetic preview request')
        self.reserve()
        m.update(self.job, 'returned', look=1, file=self.image('grid', 'blue'))
        if accepted:
            m.update(self.job, 'accept', look=1, qa='qa-pass', note='Synthetic preview layout review')

    def finish(self, decision='direction-confirmed'):
        return m.update(self.job, 'finish-preview', decision=decision, note='User preview decision')

    def delivery_spec(self, count=6):
        context=dict(self.context, purpose='delivery', size=[2, 3], canvas_policy='ratio-first')
        return dict(prompts=['Independent frame']*count, size=[2, 3], context=context)

    def test_export_is_one_marked_grid_not_standalone(self):
        d=self.create()
        self.assertEqual(d['attempts'], 0)
        self.assertIsNone(d['authorization'])
        m.export(self.job)
        prompt=(self.job/'handoff/look-1/prompt.txt').read_text()
        self.assertIn('PREVIEW ONLY', prompt)
        self.assertIn('six-panel', prompt)
        self.assertNotIn('One standalone image', prompt)
        self.assertTrue((self.job/'handoff/look-1/request.json').is_file())

    def test_result_is_preview_and_never_confirms_model_or_finishes_automatically(self):
        self.returned()
        d=m.read(self.job)
        self.assertEqual(d['delivery_status'], 'preview-grid')
        self.assertFalse(d['complete'])
        self.assertIsNone(d['model_confirmation'])
        for event,kw in [('confirm-model',dict(look=1,note='User likes direction')),
                         ('continue-authorize',dict(note='five',approval_id='five',context=d['context'],prompts=['x']*5))]:
            with self.assertRaises(ValueError):m.update(self.job,event,**kw)
        with self.assertRaises(ValueError):m.export_model(self.job,self.root/'person','person')

    def test_stop_records_decision_and_prevents_new_submission(self):
        self.returned()
        d=self.finish('stop')
        self.assertTrue(d['complete'])
        self.assertEqual(d['delivery_status'],'preview-grid')
        self.assertEqual(d['attempts'],1)
        with self.assertRaises(ValueError):m.update(self.job,'retry-authorize',look=1,expected_attempt=1,approval_id='x',note='x',prompt='x')
        before=(self.job/'task.json').read_bytes()
        m.read(self.job)
        self.assertEqual((self.job/'task.json').read_bytes(),before)

    def test_unknown_request_cannot_be_closed_or_handed_off(self):
        self.create();m.update(self.job,'authorize',limit=1,note='Synthetic permission');self.reserve()
        m.update(self.job,'unknown',look=1)
        with self.assertRaises(ValueError):self.finish('stop')
        with self.assertRaises(ValueError):m.create_from_preview(self.root/'child',self.job,self.delivery_spec(),note='Make final')
        self.assertEqual(m.read(self.job)['attempts'],1)

    def test_pending_preview_can_be_cancelled_without_fabricating_an_image(self):
        self.create();d=self.finish('stop')
        self.assertEqual(d['delivery_status'],'prepared')
        self.assertTrue(d['complete'])
        self.assertEqual(d['attempts'],0)
        with self.assertRaises(ValueError):m.create_from_preview(self.root/'child',self.job,self.delivery_spec(),note='Make final')

    def test_direction_confirmation_requires_reviewed_preview(self):
        self.returned(accepted=False)
        with self.assertRaises(ValueError):self.finish()
        m.update(self.job,'reject',look=1,note='Preview has wrong garment')
        with self.assertRaises(ValueError):self.finish()
        self.assertTrue(self.finish('stop')['complete'])

    def test_retry_keeps_preview_history_and_limits_three_corrections(self):
        self.returned(accepted=False)
        for attempt,color in enumerate(['green','yellow','purple'],1):
            m.update(self.job,'reject',look=1,note='Synthetic preview correction')
            m.update(self.job,'retry-authorize',look=1,expected_attempt=attempt,approval_id=str(attempt),note='One correction',prompt='Corrected grid')
            self.reserve()
            m.update(self.job,'returned',look=1,file=self.image('retry'+str(attempt),color))
            self.assertEqual(m.read(self.job)['delivery_status'],'preview-grid')
        m.update(self.job,'reject',look=1,note='Still wrong')
        with self.assertRaises(ValueError):m.update(self.job,'retry-authorize',look=1,expected_attempt=4,approval_id='four',note='one more',prompt='grid')
        self.assertEqual(m.read(self.job)['attempts'],4)

    def test_native_and_web_both_count_only_one_request(self):
        for route in ('codex_native','chatgpt_web'):
            with self.subTest(route=route):
                self.job=self.root/route;self.create(route=route)
                with self.assertRaises(ValueError):m.update(self.job,'authorize',limit=6,note='Six cells')
                m.update(self.job,'authorize',limit=1,note='One preview')
                m.update(self.job,'reserve',look=1,ready=True,refs=m.reference_hashes(self.job,1),conversation='https://chatgpt.com/c/test')
                self.assertEqual(m.read(self.job)['attempts'],1)

    def test_transition_creates_fresh_delivery_without_grid_anchor_or_canvas(self):
        self.returned();self.finish()
        child=self.root/'delivery'
        d=m.create_from_preview(child,self.job,self.delivery_spec(),note='User asks six independent images')
        self.assertEqual(len(d['looks']),6)
        self.assertEqual(d['attempts'],0)
        self.assertEqual(d['total_attempts'],1)
        self.assertIsNone(d['authorization'])
        self.assertIsNone(d['model_confirmation'])
        self.assertEqual(d['delivery_status'],'prepared')
        self.assertEqual(len(d['references']),1)
        self.assertIsNone(m.canvas_baseline(d))
        m.export(child)
        request=json.loads((child/'handoff/look-1/request.json').read_text())
        self.assertEqual(len(request['referenced_image_paths']),1)
        self.assertIn('One standalone image',request['prompt'])
        self.assertNotIn('PREVIEW ONLY',request['prompt'])
        with self.assertRaises(ValueError):m.update(child,'reserve',look=1,ready=True,refs=m.reference_hashes(child,1))
        with self.assertRaises(ValueError):m.create_from_preview(self.root/'duplicate',self.job,self.delivery_spec(),note='Duplicate link')
        m.update(child,'authorize',limit=6,note='User explicitly authorizes six independent outputs')
        m.update(child,'reserve',look=1,ready=True,refs=m.reference_hashes(child,1))
        d=m.update(child,'returned',look=1,file=self.image('independent-first','yellow',size=(20,30)))
        self.assertEqual(d['total_attempts'],2)
        m.update(child,'accept',look=1,qa='qa-pass',note='Independent first frame QA')
        with self.assertRaises(ValueError):m.reference_hashes(child,2)
        m.update(child,'confirm-model',look=1,note='User accepts actual independent first image')
        self.assertEqual(m.canvas_baseline(m.read(child)),[20,30])
        self.assertEqual(len(m.reference_hashes(child,2)),2)

    def test_single_transition_tracks_all_preview_retries_and_detects_provenance_tamper(self):
        self.returned(accepted=False)
        m.update(self.job,'reject',look=1,note='Correct direction')
        m.update(self.job,'retry-authorize',look=1,expected_attempt=1,approval_id='retry',note='One correction',prompt='Fixed grid')
        self.reserve();m.update(self.job,'returned',look=1,file=self.image('fixed','green'))
        m.update(self.job,'accept',look=1,qa='qa-pass',note='Preview reviewed');self.finish('stop')
        child=self.root/'single';d=m.create_from_preview(child,self.job,self.delivery_spec(1),note='Now one independent image')
        self.assertEqual(d['total_attempts'],2)
        m.update(child,'authorize',limit=1,note='One independent image')
        d=m.update(child,'reserve',look=1,ready=True,refs=m.reference_hashes(child,1))
        self.assertEqual(d['total_attempts'],3)
        (child/'provenance/preview-task.json').write_text('{}')
        with self.assertRaises(ValueError):m.read(child)
        with self.assertRaises(ValueError):m.export(child)

    def test_transition_rejects_context_changes_without_creating_child(self):
        self.returned();self.finish()
        for key,value in [('outfit','other'),('style','old-money'),('mode','C'),('output_form','flat')]:
            with self.subTest(key=key):
                spec=self.delivery_spec();spec['context'][key]=value
                with self.assertRaises(ValueError):m.create_from_preview(self.root/'bad',self.job,spec,note='Continue')
                self.assertFalse((self.root/'bad').exists())

    def test_preview_cannot_have_six_requests_or_custom_body_or_edit_target(self):
        for context,prompts in [(self.context,['grid']*6),(dict(self.context,first_pose='custom',pose_description='custom'),['grid'])]:
            with self.assertRaises(ValueError):m.create(self.job,[self.ref],prompts,[60,40],context=context)

    def test_cli_preview_finish_and_prepare_delivery(self):
        self.returned();self.finish()
        spec=self.root/'spec.json';spec.write_text(json.dumps(self.delivery_spec(1)))
        result=subprocess.run([sys.executable,str(SCRIPT),'prepare-delivery','--task',str(self.root/'cli-child'),'--preview-task',str(self.job),'--spec',str(spec),'--note','One final requested'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['total_attempts'],1)

    def real_spec(self, extra=0):
        face=self.image('original','green')
        refs=[dict(path=str(self.ref),role='garment-source'),dict(path=str(face),role='identity-reference')]
        for i,color in enumerate(['yellow','purple','cyan','white'][:extra]):
            refs.append(dict(path=str(self.image('detail'+str(i),color)),role='garment-source'))
        hashes=[m.digest(Path(r['path'])) for r in refs]
        looks=[dict(body_action='body '+str(n),head_view='front',gaze='toward camera',face_visible=True,
                    reference_sha256s=hashes[:2]+(hashes[2+n%extra:3+n%extra] if extra else []),selection_note='Actual originals for this cell') for n in range(6)]
        plan=dict(primary_identity_sha256=hashes[1],coverage=[dict(sha256=hashes[1],views=['front'],note='Original frontal view')],looks=looks)
        model=dict(source_type='real',scope='face',subject='adult female model',locked=[],adjustable=[],consent_note='User granted likeness permission')
        return refs,model,plan

    def test_real_preview_validates_six_cells_and_exports_union_without_anchor(self):
        refs,model,plan=self.real_spec(extra=3)
        m.create(self.job,refs,['Six-panel grid'],[60,40],model=model,context=self.context,real_face_plan=plan)
        m.export(self.job)
        request=json.loads((self.job/'handoff/look-1/request.json').read_text())
        manifest=json.loads((self.job/'handoff/look-1/manifest.json').read_text())
        self.assertEqual(len(request['referenced_image_paths']),5)
        self.assertEqual(len(manifest['preview_cell_plans']),6)
        self.assertEqual(manifest['omitted_reference_sha256s'],[])
        self.assertEqual(request['prompt'].count('Preview cell '),6)
        self.assertIn('Cell reference images: Image 1, Image 2, Image 3.',request['prompt'])
        self.assertIn('Cell reference images: Image 1, Image 2, Image 4.',request['prompt'])
        self.assertIn('Cell reference images: Image 1, Image 2, Image 5.',request['prompt'])

    def test_real_preview_cannot_hide_union_over_five_or_unsupported_cell_view(self):
        refs,model,plan=self.real_spec(extra=4)
        with self.assertRaises(ValueError):m.create(self.job,refs,['grid'],[60,40],model=model,context=self.context,real_face_plan=plan)
        refs,model,plan=self.real_spec()
        plan['looks'][5]['head_view']='right-profile'
        with self.assertRaises(ValueError):m.create(self.job,refs,['grid'],[60,40],model=model,context=self.context,real_face_plan=plan)

    def test_transition_preserves_real_originals_but_requires_new_delivery_confirmation(self):
        refs,model,plan=self.real_spec()
        m.create(self.job,refs,['grid'],[60,40],model=model,context=self.context,real_face_plan=plan)
        m.update(self.job,'authorize',limit=1,note='One preview');self.reserve()
        m.update(self.job,'returned',look=1,file=self.image('grid','blue'))
        m.update(self.job,'accept',look=1,qa='qa-pass',note='Preview direction review');self.finish()
        spec=self.delivery_spec(1);spec['real_face_plan']=dict(plan,looks=plan['looks'][:1])
        child=self.root/'real-final';d=m.create_from_preview(child,self.job,spec,note='One independent final')
        self.assertEqual(d['model'],model)
        self.assertIsNone(d['model_confirmation'])
        self.assertEqual([r['role'] for r in d['references']],['garment-source','identity-reference'])

    def test_multi_outfit_preview_handoff_selects_original_product_sources(self):
        second=self.image('second-product','green')
        m.create(self.job,[self.ref,second],['Six outfits direction board'],[60,40],context=self.context)
        m.update(self.job,'authorize',limit=1,note='One multi-outfit preview');self.reserve()
        m.update(self.job,'returned',look=1,file=self.image('grid','blue'))
        m.update(self.job,'accept',look=1,qa='qa-pass',note='Preview reviewed');self.finish()
        spec=self.delivery_spec(1);spec['context']['outfit']='selected-second-sku'
        spec['garment_sha256s']=[m.digest(second)]
        child=self.root/'selected';d=m.create_from_preview(child,self.job,spec,note='User explicitly selects the second outfit')
        self.assertEqual([r['sha256'] for r in d['references']],[m.digest(second)])
        self.assertEqual(d['context']['outfit'],'selected-second-sku')
        self.assertEqual(d['total_attempts'],1)


    def compose(self, donor, rectangle=(0, 0, 20, 20), **extra):
        d=m.read(self.job)
        return m.update(self.job, 'compose-preview', look=1, file=donor,
                        rectangle=list(rectangle), expected_donor_sha256=m.digest(donor),
                        expected_output_sha256=d['looks'][0]['output']['sha256'],
                        note='User authorized local panel replacement; donor generation is already counted separately.', **extra)

    def test_local_preview_composite_preserves_other_cells_and_consumed_budget(self):
        self.returned(accepted=False)
        m.update(self.job,'reject',look=1,note='First cell body turn is wrong')
        before=m.read(self.job); original=(self.job/before['looks'][0]['output']['file']).read_bytes()
        donor=self.image('donor','red')
        try:d=self.compose(donor)
        except ValueError as error:self.fail('Cannot retain the authorized local preview correction: '+str(error))
        result=Image.open(self.job/d['looks'][0]['output']['file']).convert('RGB')
        for y in range(40):
            for x in range(60):
                self.assertEqual(result.getpixel((x,y)), (255,0,0) if x<20 and y<20 else (0,0,255))
        self.assertEqual((self.job/before['looks'][0]['output']['file']).read_bytes(),original)
        self.assertEqual(d['attempts'],1);self.assertEqual(d['authorization'],before['authorization'])
        self.assertEqual(d['looks'][0]['state'],'returned');self.assertNotIn('qa',d['looks'][0])
        self.assertIsNone(d['model_confirmation']);self.assertFalse(d['complete'])
        edit=d['looks'][0]['local_edits'][0]
        self.assertEqual(edit['prior_review']['state'],'rejected')
        self.assertEqual(edit['generation_calls'],0)
        donor.write_bytes(b'external donor later removed')
        m.check_evidence(self.job,m.read(self.job))
        with self.assertRaises(ValueError):self.finish()
        m.update(self.job,'accept',look=1,qa='qa-pass',note='Actual corrected preview reviewed')
        self.finish()
        child=m.create_from_preview(self.root/'composite-final',self.job,self.delivery_spec(1),note='User asks independent image')
        self.assertEqual(child['total_attempts'],1);self.assertIsNone(child['authorization'])
        self.assertEqual(len(child['references']),1)
        self.assertEqual((self.root/'composite-final/provenance/preview.png').read_bytes(),(self.job/edit['output']['file']).read_bytes())

    def test_local_preview_plan_reaches_delivery_without_rewriting_generation_prompt(self):
        coverage=[dict(sha256=m.digest(self.ref),views=['front'],usable=True,same_sku=True,note='Synthetic front')]
        plan=m.shot_helper().default_plan('sku',coverage)
        m.create(self.job,[self.ref],['Gallery.'],[60,40],context=self.context,shot_plan=plan)
        m.update(self.job,'authorize',limit=1,note='One preview')
        m.update(self.job,'reserve',look=1,ready=True,refs=m.reference_hashes(self.job,1),expected_plan_sha256=m.plan_fingerprint(m.read(self.job)))
        m.update(self.job,'returned',look=1,file=self.image('grid','blue'))
        m.update(self.job,'reject',look=1,note='Body turn correction requested')
        original=m.read(self.job);changed=copy.deepcopy(plan)
        changed.update(preservation='adapted',adaptation_note='User approved first-panel torso correction')
        changed['looks'][0]['arrangement']='Turn shoulders and hips together toward image-left; near shoulder clear.'
        try:d=self.compose(self.image('donor','red'),shot_plan=changed)
        except ValueError as error:self.fail('Cannot preserve the corrected direction plan: '+str(error))
        self.assertEqual(d['looks'][0]['prompt'],original['looks'][0]['prompt'])
        self.assertEqual(d['shot_plan'],plan)
        m.update(self.job,'accept',look=1,qa='qa-pass',note='Review composite against local change and original constraints')
        self.finish();child=m.create_from_preview(self.root/'final',self.job,self.delivery_spec(1),note='Confirmed corrected direction')
        self.assertEqual(child['shot_plan']['looks'],changed['looks'][:1])
        self.assertEqual(child['shot_plan']['preservation'],'adapted')
        self.assertIsNone(child['model_confirmation'])
        m.export(self.root/'final')
        raw=next((self.root/'final/handoff').glob('*/prompt.txt')).read_text()
        self.assertIn(changed['looks'][0]['arrangement'],raw)

    def test_local_preview_rejects_wrong_hash_canvas_bounds_and_unresolved_states(self):
        self.returned();donor=self.image('donor','red');before=(self.job/'task.json').read_bytes()
        cases=[dict(rectangle=[0,0,61,20]),dict(rectangle=[0,0,0,20]),dict(rectangle=[True,0,20,20]),
               dict(rectangle=[0,0,20.5,20]),dict(expected_output_sha256='0'*64),
               dict(expected_donor_sha256='0'*64),dict(note='')]
        d=m.read(self.job)
        args=dict(look=1,file=donor,rectangle=[0,0,20,20],expected_output_sha256=d['looks'][0]['output']['sha256'],expected_donor_sha256=m.digest(donor),note='User approved')
        for changes in cases:
            with self.subTest(changes=changes),self.assertRaises(ValueError):m.update(self.job,'compose-preview',**dict(args,**changes))
            self.assertEqual((self.job/'task.json').read_bytes(),before)
        Image.new('RGB',(61,40),'red').save(donor)
        with self.assertRaises(ValueError):self.compose(donor)
        self.finish()
        with self.assertRaises(ValueError):self.compose(donor)
        other=self.root/'unknown';self.job=other;self.create();m.update(other,'authorize',limit=1,note='One preview');self.reserve()
        m.update(other,'unknown',look=1)
        with self.assertRaises(ValueError):m.update(other,'compose-preview',**args)

    def test_local_preview_frozen_sources_and_protected_pixels_detect_tampering(self):
        self.returned();donor=self.image('donor','red')
        try:d=self.compose(donor)
        except ValueError as error:self.fail('Local correction unavailable: '+str(error))
        edit=d['looks'][0]['local_edits'][0]
        for key in ('base_output','donor','output'):
            p=self.job/edit[key]['file'];saved=p.read_bytes();p.write_bytes(b'tampered')
            with self.assertRaises((ValueError,OSError)):m.check_evidence(self.job,m.read(self.job))
            p.write_bytes(saved)
        changed=copy.deepcopy(d);changed['looks'][0]['local_edits'][0]['rectangle']=[0,0,60,40]
        with self.assertRaises(ValueError):m.check_evidence(self.job,changed)
        changed=copy.deepcopy(d);changed['looks'][0]['local_edits'][0]['generation_calls']=1
        with self.assertRaises(ValueError):m.check_evidence(self.job,changed)


    def test_local_preview_cli_and_symlink_boundary(self):
        self.returned();donor=self.image('donor','red');d=m.read(self.job)
        output=self.root/'outside';output.mkdir();(self.job/'local-edits').symlink_to(output,target_is_directory=True)
        with self.assertRaises(ValueError):self.compose(donor)
        self.assertEqual(list(output.iterdir()),[])
        (self.job/'local-edits').unlink()
        run=subprocess.run([sys.executable,str(SCRIPT),'compose-preview','--task',str(self.job),'--look','1',
            '--file',str(donor),'--rectangle','0','0','20','20',
            '--expected-output-sha256',d['looks'][0]['output']['sha256'],
            '--expected-donor-sha256',m.digest(donor),'--note','User approved local correction; existing donor already charged.'],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        state=json.loads(run.stdout)
        self.assertEqual(state['attempts'],1);self.assertEqual(state['looks'][0]['state'],'returned')


    def test_local_plan_survives_later_generated_retry_and_retains_local_history(self):
        coverage=[dict(sha256=m.digest(self.ref),views=['front'],usable=True,same_sku=True,note='Reviewed synthetic front')]
        plan=m.shot_helper().default_plan('sku',coverage)
        m.create(self.job,[self.ref],['Gallery.'],[60,40],context=self.context,shot_plan=plan)
        m.update(self.job,'authorize',limit=1,note='One preview')
        m.update(self.job,'reserve',look=1,ready=True,refs=m.reference_hashes(self.job,1),expected_plan_sha256=m.plan_fingerprint(m.read(self.job)))
        m.update(self.job,'returned',look=1,file=self.image('grid','blue'))
        m.update(self.job,'accept',look=1,qa='qa-pass',note='Reviewed base')
        changed=copy.deepcopy(plan);changed.update(preservation='adapted',adaptation_note='User approved first-cell body correction')
        changed['looks'][0]['arrangement']='Turn the shoulders and hips together toward image-left.'
        d=self.compose(self.image('donor','red'),shot_plan=changed)
        m.update(self.job,'reject',look=1,note='A further user-approved scene revision is needed')
        with self.assertRaises(ValueError):m.update(self.job,'retry-authorize',look=1,expected_attempt=1,approval_id='next',note='New request',prompt='Gallery.')
        d=m.update(self.job,'revise-preview',look=1,expected_output_sha256=d['looks'][0]['output']['sha256'],prompt='Gallery.',note='User changes the scene; preserve local body correction')
        self.assertEqual(d['preview_revision']['candidate']['shot_plan'],changed)
        d=m.update(self.job,'retry-authorize',look=1,expected_attempt=1,approval_id='next',note='User grants one synthetic retry')
        m.update(self.job,'reserve',look=1,ready=True,refs=m.reference_hashes(self.job,1),expected_plan_sha256=m.plan_fingerprint(d))
        d=m.update(self.job,'returned',look=1,file=self.image('new-provider-result','green'))
        m.check_evidence(self.job,d)
        self.assertEqual(d['attempts'],2)
        self.assertEqual(d['shot_plan'],changed)
        self.assertEqual(d['looks'][0]['history'][0]['local_edits'][0]['generation_calls'],0)
