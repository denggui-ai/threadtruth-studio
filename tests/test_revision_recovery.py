"""Offline counterexamples for R01–R05: exit paths, legacy records and real exports."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('recovery_fixtures',ROOT/'tests/test_plan_revision.py')
fixtures=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixtures)
task=fixtures.task


class RevisionRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.PlanRevisionTests();self.f.setUp();self.addCleanup(self.f.doCleanups)

    def cancel(self,**overrides):
        d=task.read(self.f.job);p=d['preview_revision']
        args=dict(look=1,note='Synthetic user withdraws unexecuted changes',
            expected_candidate_sha256=p['candidate_sha256'],expected_output_sha256=p['output_sha256'])
        args.update(overrides)
        return task.update(self.f.job,'cancel-preview-revision',**args)

    def expired(self,kind='deleted'):
        self.f.returned(self.f.plan())
        self.f.revise(shot_plan=self.f.plan(True),garment_references=[dict(path=str(self.f.back),sha256=task.digest(self.f.back))])
        if kind=='deleted':self.f.back.unlink()
        else:self.f.image('back','purple')

    def legacy(self,prompt,pending=False):
        # Unversioned schema-2 snapshot format accepted by the pre-bfd0087 writer.
        # Its legality was also cross-checked against the parent writer in the audit.
        if pending:self.f.create()
        else:self.f.returned()
        d=task.read(self.f.job);d.pop('prompt_contract_version',None)
        d['looks'][0].update(prompt=prompt,prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest())
        (self.f.job/'task.json').write_text(json.dumps(d))
        return d

    def test_cancel_restores_original_acceptance_without_authority_or_call(self):
        self.f.returned();original=task.read(self.f.job)
        self.f.revise(model=dict(self.f.model,locked=['long hair']))
        d=self.cancel()
        self.assertNotIn('preview_revision',d)
        self.assertEqual(d['looks'],original['looks']);self.assertEqual(d['model'],original['model'])
        self.assertEqual(d['authorization'],original['authorization']);self.assertEqual(d['attempts'],1)
        self.assertEqual(d['preview_revision_history'][-1]['disposition'],'cancelled')
        task.update(self.f.job,'finish-preview',decision='direction-confirmed',note='Synthetic original image acceptance')
        child=task.create_from_preview(self.f.root/'child',self.f.job,
            dict(context=dict(self.f.context,purpose='delivery'),size=[60,40],prompts=['Gallery.']),note='Synthetic prepare original direction')
        self.assertEqual(child['model'],original['model']);self.assertIsNone(child['authorization'])

    def test_cancel_requires_exact_candidate_and_output_and_preserves_rejected_qa(self):
        self.f.returned(qa='rejected');self.f.revise()
        before=(self.f.job/'task.json').read_bytes()
        for overrides in [dict(expected_candidate_sha256='0'*64),dict(expected_output_sha256='0'*64)]:
            with self.subTest(overrides=overrides),self.assertRaises(ValueError):self.cancel(**overrides)
            self.assertEqual(before,(self.f.job/'task.json').read_bytes())
        d=self.cancel();self.assertEqual(d['looks'][0]['state'],'rejected')
        with self.assertRaises(ValueError):task.update(self.f.job,'finish-preview',decision='direction-confirmed',note='Not technical acceptance')

    def test_expired_candidate_cannot_adopt_but_can_be_cancelled(self):
        self.expired();before=(self.f.job/'task.json').read_bytes()
        with self.assertRaises(ValueError):self.f.retry()
        self.assertEqual(before,(self.f.job/'task.json').read_bytes())
        d=self.cancel();self.assertEqual(d['attempts'],1);task.check_evidence(self.f.job,d)

    def test_expired_candidate_can_stop_without_accepting_direction(self):
        self.expired()
        d=task.update(self.f.job,'finish-preview',decision='stop',note='Synthetic stop with expired candidate')
        self.assertTrue(d['complete']);self.assertEqual(d['preview_decision']['decision'],'stop')
        self.assertEqual(d['attempts'],1);self.assertIsNone(d['model_confirmation'])

    def test_changed_candidate_can_be_replaced_without_clearing_history(self):
        self.expired('changed');self.f.revise(model=dict(self.f.model,locked=['long loose hair']))
        d=task.read(self.f.job)
        self.assertEqual(d['preview_revision']['candidate']['shot_plan']['route'],'B')
        self.assertEqual(len(d['preview_revision_history']),1)
        self.f.retry();task.check_evidence(self.f.job,task.read(self.f.job))

    def test_safe_exit_never_bypasses_frozen_evidence_or_candidate_binding(self):
        self.f.returned();self.f.revise()
        d=task.read(self.f.job);frozen=self.f.job/d['references'][0]['file'];frozen.write_bytes(b'corrupt')
        with self.assertRaises(ValueError):self.cancel()
        with self.assertRaises(ValueError):task.update(self.f.job,'finish-preview',decision='stop',note='Cannot ignore committed evidence')

    def test_candidate_metadata_tamper_is_not_treated_as_expired_external_input(self):
        self.f.returned();self.f.revise()
        d=task.read(self.f.job);d['preview_revision']['candidate']['prompt']='Tampered proposal'
        (self.f.job/'task.json').write_text(json.dumps(d))
        with self.assertRaises(ValueError):self.cancel()

    def real_inputs(self,covered=True):
        f=self.f;face=f.image('face','green');detail=f.image('detail','black');fh=task.digest(face);dh=task.digest(detail)
        plan=f.plan()
        if covered:plan['coverage'].append(dict(sha256=dh,views=['detail'],usable=True,same_sku=True,note='Synthetic same-SKU detail reviewed'))
        cell=dict(body_action='Natural agreed body action',head_view='near-front',gaze='looking at camera',face_visible=True,
            reference_sha256s=[task.digest(f.front),dh,fh],selection_note='Synthetic original face and necessary garment detail')
        fp=dict(primary_identity_sha256=fh,coverage=[dict(sha256=fh,views=['front'],note='Synthetic real original front')],looks=[copy.deepcopy(cell) for _ in range(6)])
        model=dict(f.model,source_type='real',consent_note='Synthetic express permission')
        refs=[dict(path=str(f.front),role='garment-source'),dict(path=str(detail),role='garment-source'),dict(path=str(face),role='identity-reference')]
        return plan,fp,model,refs,dh

    def test_real_extra_detail_is_retained_in_actual_cell_mapping(self):
        plan,fp,model,refs,dh=self.real_inputs()
        d=task.create(self.f.job,refs,['Gallery lighting.'],[60,40],model=model,context=self.f.context,shot_plan=plan,real_face_plan=fp)
        task.export(self.f.job)
        folder=next((self.f.job/'handoff').glob('look-*'))
        request=json.loads((folder/'request.json').read_text());manifest=json.loads((folder/'manifest.json').read_text())
        self.assertEqual(len(request['referenced_image_paths']),3)
        self.assertIn(dh,manifest['reference_hashes']);self.assertNotIn(dh,manifest['omitted_reference_sha256s'])
        self.assertIn('Image 1, Image 2, Image 3',request['prompt'])

    def test_real_extra_detail_needs_usable_same_sku_coverage(self):
        for case in ('uncovered','unusable','other-sku'):
            plan,fp,model,refs,dh=self.real_inputs(covered=case!='uncovered')
            if case=='unusable':plan['coverage'][-1]['usable']=False
            if case=='other-sku':plan['coverage'][-1]['same_sku']=False
            with self.subTest(case=case),self.assertRaises(ValueError):
                task.create(self.f.job,refs,['Gallery.'],[60,40],model=model,context=self.f.context,shot_plan=plan,real_face_plan=fp)
            self.assertFalse(self.f.job.exists())

    def test_legacy_plain_partial_and_complete_model_prose_remain_recoverable(self):
        prompts=['Gallery lighting.','Fixed model conditions: mature adult; tied-back hair',
            'Model subject: adult female model.\nFixed model conditions: mature adult; tied-back hair',
            '\n'.join(task.models.prompt_lines(self.f.model))]
        for i,raw in enumerate(prompts):
            self.f.job=self.f.root/('legacy-'+str(i));d=self.legacy(raw,pending=True)
            before=(self.f.job/'task.json').read_bytes();task.check_evidence(self.f.job,task.read(self.f.job))
            task.export(self.f.job);self.assertEqual(before,(self.f.job/'task.json').read_bytes())
            request=json.loads(next((self.f.job/'handoff').glob('*/request.json')).read_text())
            self.assertIn(raw,request['prompt'])
            ended=task.update(self.f.job,'finish-preview',decision='stop',note='Synthetic stop old task')
            self.assertEqual(ended['attempts'],d['attempts']);self.assertEqual(ended['looks'][0]['prompt'],raw)

    def test_accepted_legacy_partial_can_stop_but_bad_hash_still_blocks(self):
        raw='Fixed model conditions: mature adult; tied-back hair';self.legacy(raw)
        before=task.read(self.f.job)
        stopped=task.update(self.f.job,'finish-preview',decision='stop',note='Synthetic legacy accepted stop')
        self.assertEqual(stopped['looks'],before['looks']);self.assertEqual(stopped['attempts'],1)
        self.f.job=self.f.root/'corrupt-legacy';d=self.legacy(raw)
        d['looks'][0]['prompt']='Altered without hash update'
        (self.f.job/'task.json').write_text(json.dumps(d))
        with self.assertRaises(ValueError):task.update(self.f.job,'finish-preview',decision='stop',note='Cannot ignore original hash')

    def test_new_task_still_rejects_partial_or_conflicting_structured_model(self):
        for prompt in ['Fixed model conditions: mature adult; tied-back hair','Fixed model conditions: different old age']:
            with self.subTest(prompt=prompt),self.assertRaises(ValueError):
                task.create(self.f.job,[self.f.front],[prompt],[60,40],model=self.f.model,context=self.f.context)

    def test_legacy_retry_adopts_new_contract_without_revalidating_old_prose(self):
        raw='Fixed model conditions: mature adult; tied-back hair';self.legacy(raw)
        self.f.revise(model=dict(self.f.model,locked=['long hair']));self.f.retry()
        d=task.read(self.f.job);self.assertEqual(d['prompt_contract_version'],1)
        self.assertEqual(d['looks'][0]['history'][0]['prompt_contract_version'],0)
        self.assertEqual(d['looks'][0]['history'][0]['prompt'],raw)
        task.check_evidence(self.f.job,d);task.export(self.f.job)

    def test_legacy_pending_revision_preserves_original_prompt_history(self):
        raw='Fixed model conditions: mature adult; tied-back hair';d=self.legacy(raw,pending=True)
        task.update(self.f.job,'revise-pending',look=1,note='Synthetic explicit new preparation',
            expected_prompt_sha256=d['looks'][0]['prompt_sha256'],prompt='Updated gallery lighting.')
        d=task.read(self.f.job);task.check_evidence(self.f.job,d)
        self.assertEqual(d['looks'][0]['prompt_history'][0]['prompt'],raw)
        self.assertEqual(d['looks'][0]['prompt_history'][0]['prompt_contract_version'],0)
        self.assertEqual(d['prompt_contract_version'],1)

    def test_legacy_pose_syntax_rejected_for_managed_route_b_and_classic_three_five(self):
        for raw in ['POSE 6: BACK_TURN_GLANCE — show the back.',
                    'POSE 3: UPRIGHT_SEATED — full-body with shoes visible.',
                    'Shot 5: SLIGHT_FORWARD_LEAN — hands braced on thighs.']:
            with self.subTest(raw=raw),self.assertRaises(ValueError):
                task.create(self.f.job,[self.f.front],[raw],[60,40],model=self.f.model,context=self.f.context,shot_plan=self.f.plan())
            self.assertFalse(self.f.job.exists())

    def test_one_current_shot_block_preserves_scene_text_and_rejects_outside_pose(self):
        plan=self.f.plan();scene='Cool gray wall and soft window light; retain readable red fabric.'
        raw=task.shot_helper().apply(scene,plan)
        self.assertIn(scene,raw)
        self.assertEqual(task.shot_helper().apply(raw,plan),raw)
        with self.assertRaises(ValueError):task.shot_helper().apply(raw+'\nPOSE 6: BACK_TURN_GLANCE',plan)
        # Existing unplanned tasks are not silently rewritten by the new shot compiler.
        task.create(self.f.job,[self.f.front],['POSE 1: SIDE_TURN_STANDING'],[60,40],model=self.f.model,context=self.f.context)
        task.export(self.f.job)

    def legacy_planned(self,raw):
        self.f.create(self.f.plan())
        d=task.read(self.f.job);d.pop('prompt_contract_version',None)
        d['looks'][0].update(prompt=raw,prompt_sha256=hashlib.sha256(raw.encode()).hexdigest())
        (self.f.job/'task.json').write_text(json.dumps(d))
        return d

    def test_legacy_matching_planned_headers_export_without_rewriting_evidence(self):
        raw='Gallery lighting.\nPOSE 1: SIDE_TURN_STANDING. Framing: full-body.'
        self.legacy_planned(raw);before=(self.f.job/'task.json').read_bytes()
        task.check_evidence(self.f.job,task.read(self.f.job));task.export(self.f.job)
        request=json.loads(next((self.f.job/'handoff').glob('*/request.json')).read_text())
        self.assertIn(raw,request['prompt']);self.assertEqual(before,(self.f.job/'task.json').read_bytes())
        with self.assertRaises(ValueError):
            task.update(self.f.job,'revise-pending',look=1,note='Synthetic new preparation',
                expected_prompt_sha256=task.read(self.f.job)['looks'][0]['prompt_sha256'],prompt=raw)

    def test_legacy_conflicting_headers_allow_recovery_but_block_submission(self):
        for i,raw in enumerate(['POSE 6: BACK_TURN_GLANCE',
                'Shot 3: UPRIGHT_SEATED. Framing: full-body.', 'POSE 1: ???']):
            self.f.job=self.f.root/('legacy-plan-'+str(i));self.legacy_planned(raw)
            before=(self.f.job/'task.json').read_bytes()
            task.check_evidence(self.f.job,task.read(self.f.job))
            with self.assertRaises(ValueError):task.export(self.f.job)
            self.assertEqual(before,(self.f.job/'task.json').read_bytes())
            d=task.update(self.f.job,'finish-preview',decision='stop',note='Synthetic recover old conflict')
            self.assertTrue(d['complete']);self.assertEqual(d['looks'][0]['prompt'],raw)

    def test_cancel_cli_has_zero_call_side_effect(self):
        self.f.returned();self.f.revise();p=task.read(self.f.job)['preview_revision']
        result=subprocess.run([sys.executable,str(ROOT/'skills/threadtruth-studio/scripts/web-task.py'),
            'cancel-preview-revision','--task',str(self.f.job),'--look','1','--note','Synthetic withdraw',
            '--expected-candidate-sha256',p['candidate_sha256'],'--expected-output-sha256',p['output_sha256']],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(task.read(self.f.job)['attempts'],1)

if __name__=='__main__':unittest.main()
