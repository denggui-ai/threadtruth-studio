"""Synthetic workflow regressions: no customer assets, model calls or visual claims."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from tests import test_nine_task as fixtures

task = fixtures.task


class WorkflowClosureTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.NineTaskTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)

    def provider_failure(self, number, code='moderation_blocked'):
        receipt = self.f.root / ('failure-' + str(number) + '.txt')
        receipt.write_text('SYNTHETIC terminal ' + code)
        return task.update(self.f.job, 'failed', look=number, reason=code,
                           failure_receipt=receipt)

    def workflow(self, *, details=(), poses=True, preview=False, route='codex_native'):
        plan = self.f.plan()
        for shot in plan['looks']:
            shot.pop('pose_reference', None)
            shot.pop('aesthetic_reference_sha256s', None)
            if poses:
                shot['pose_decision'] = dict(kind='custom', reason='Keep both hands below the printed chest.')
            if shot['slot'] in details:
                shot['framing'] = 'detail'
        visual = self.f.visual(plan)
        for shot in visual['shots']:
            if shot['slot'] in details:
                shot['garment_focus'] = dict(description='Only the printed chest panel.', keep=['source print'])
        context = dict(self.f.context, purpose='preview-grid' if preview else 'delivery')
        return task.create(self.f.job, self.f.refs()[:2], None, [60, 40], model=self.f.model,
                           context=context, route=route, shot_plan=plan, visual_plan=visual)

    def confirm(self, path='direct', **overrides):
        data = task.read(self.f.job)
        decision = dict(style='nordic-minimal', path=path, image_count=len(data['looks']),
                        note='Synthetic confirmation of this complete named plan and route')
        decision.update(overrides)
        return task.update(self.f.job, 'confirm-plan', decision=decision)

    def review(self, *, goal='met', identity=True):
        result = {
            'goal': dict(expected='Show the printed chest and garment length.',
                         observed='Synthetic garment target observation', result=goal),
            'garment': dict(expected='Original print and hem', observed='Synthetic unchanged source features', result='met'),
            'photography': dict(expected='Soft window light', observed='Synthetic lighting observation', result='met'),
        }
        if identity:
            result.update(identity=dict(expected='Declared adult model', observed='Synthetic same model observation', result='met'),
                          anatomy=dict(expected='Natural support', observed='Synthetic natural support observation', result='met'))
        return result

    def finish(self, number=1, *, goal='met'):
        self.f.reserve(number)
        task.update(self.f.job, 'returned', look=number,
                    file=self.f.image('new-output-' + str(number), (10 * number, 74, 61)))
        task.update(self.f.job, 'reject' if goal=='unmet' else 'accept', look=number,
                    qa='qa-retry' if goal=='unmet' else 'qa-pass', review=self.review(goal=goal),
                    note='Synthetic factual review; not an actual visual evaluation')
        if number==1 and goal!='unmet' and not task.is_preview(task.read(self.f.job)):
            task.update(self.f.job, 'confirm-model', look=1, note='Synthetic actual-image model confirmation')

    def approved(self, **kwargs):
        self.workflow(**kwargs)
        self.confirm()
        return task.update(self.f.job, 'authorize', limit=9, note='Synthetic nine-image generation authority')

    def test_new_tasks_require_plan_confirmation_before_reserving(self):
        data = self.workflow()
        self.assertEqual(data.get('workflow_version'), 1)
        task.update(self.f.job, 'authorize', limit=9, note='Generation count alone does not choose the preview route')
        with self.assertRaisesRegex(ValueError, '[Cc]onfirm|confirmation'):
            self.f.reserve()
        self.assertEqual(task.read(self.f.job)['attempts'], 0)

    def test_legacy_status_remains_readable_without_rewriting_or_weakening_execution_checks(self):
        data=self.f.create()
        self.assertNotIn('workflow_version',data)
        # Status could inspect an old damaged handoff before this change; execution still cannot use it.
        data['looks'][0]['prompt']='Synthetic damaged old prompt'
        path=self.f.job/'task.json';path.write_text(json.dumps(data))
        before=path.read_bytes()
        self.assertEqual(task.series_status(self.f.job),task.read(self.f.job))
        self.assertEqual(path.read_bytes(),before)
        with self.assertRaises(ValueError):task.export(self.f.job)

    def test_plan_confirmation_checks_style_count_route_and_pose_decisions(self):
        self.workflow(poses=False)
        for overrides in (dict(style='resort-vacation'), dict(image_count=6), dict(path='after-preview'), {}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                self.confirm(**overrides)
        self.f.job = self.f.root / 'reviewed'
        self.workflow()
        data = self.confirm()
        self.assertEqual(data['plan_confirmation']['path'], 'direct')
        task.update(self.f.job, 'authorize', limit=9, note='Same confirmed plan: nine calls')
        self.f.reserve()
        after = task.read(self.f.job)
        self.assertEqual(after['attempts'], 1)
        self.assertEqual(after['plan_confirmation'], data['plan_confirmation'])

    def test_preview_route_cannot_be_silently_recorded_as_direct_delivery(self):
        self.workflow(preview=True)
        with self.assertRaises(ValueError):
            self.confirm()
        self.confirm('preview')
        task.update(self.f.job, 'authorize', limit=1, note='Synthetic one preview')
        self.f.reserve()
        self.assertEqual(task.read(self.f.job)['attempts'], 1)

    def test_detail_prompt_uses_focused_garment_without_dropping_identity_sources(self):
        data = self.workflow(details=(2,))
        focused = task.visual_helper().compile_prompt(data['visual_plan'], 2)
        self.assertIn('Only the printed chest panel.', focused)
        self.assertNotIn('Original printed red top.', focused)
        rows = task.selected_references(data['references'], data['context'], data['shot_plan'], None, 2)
        self.assertEqual([r['role'] for r in rows], ['garment-source', 'identity-reference'])

    def test_first_moderation_failure_holds_similar_shots_but_not_other_framings(self):
        self.approved(details=(2, 3))
        self.finish()
        self.f.reserve(2)
        failed = self.provider_failure(2)
        with self.assertRaisesRegex(ValueError, 'moderation|similar|hold'):
            self.f.reserve(3)
        self.f.reserve(4)
        self.assertEqual(task.read(self.f.job)['attempts'], 3)
        task.update(self.f.job, 'returned', look=4, file=self.f.image('four', 'gold'))
        task.update(self.f.job, 'accept', look=4, qa='qa-pass', review=self.review(), note='Synthetic target review')
        task.update(self.f.job, 'review-hold', look=3,
                    failure_sha256=task.object_hash(failed['looks'][1]['failure']),
                    note='Synthetic explicit review of this unchanged allowed garment target and wearing context')
        self.f.reserve(3)
        self.assertEqual(task.read(self.f.job)['attempts'], 4)

    def test_visible_goal_failure_cannot_be_accepted_as_user_review_or_erased_by_retention(self):
        self.approved()
        self.finish()
        self.f.reserve(2)
        returned = task.update(self.f.job, 'returned', look=2, file=self.f.image('wide-detail', 'yellow'))
        with self.assertRaises(ValueError):
            task.update(self.f.job, 'accept', look=2, qa='qa-user-review', review=self.review(goal='unmet'),
                        note='A wider image missed the declared detail target')
        task.update(self.f.job, 'reject', look=2, review=self.review(goal='unmet'), note='Declared target is not delivered')
        kept = task.update(self.f.job, 'retain-output', look=2,
                           expected_output_sha256=returned['looks'][1]['output']['sha256'],
                           note='Synthetic user keeps the picture with the disclosed target failure')
        self.assertEqual(kept['looks'][1]['state'], 'rejected')
        self.assertEqual(kept['looks'][1]['qa'], 'qa-retry')
        self.f.reserve(3)  # ordinary visual failure is not a moderation hold

    def revision_spec(self, *, still=False, number=1):
        original = task.read(self.f.job)
        output = self.f.job / original['looks'][number-1]['output']['file'] if original['looks'][number-1].get('output') else None
        form = 'flat-lay' if still else 'human'
        context = dict(self.f.context, output_form=form, first_pose='custom',
                       pose_description='Source-backed garment detail', purpose='delivery' if still or output is None else 'correction-edit')
        visual = copy.deepcopy(original['visual_plan'])
        visual.update(version=1, output_form=form)
        visual['shots'] = [dict(slot=1, pose='custom', scene='Gallery bay', lighting='Soft window light',
                               composition='Source-backed garment detail')]
        refs = [dict(path=self.f.front, role='garment-source')]
        if not still:
            if self.f.model['source_type']!='new':refs += [dict(path=self.f.face, role='identity-reference')]
            if output is not None:refs += [dict(path=output, role='edit-target')]
        return dict(references=refs, size=[60, 40], route='codex_native', identity=not still,
                    model=None if still else self.f.model, context=context, visual_plan=visual, count=1)

    def test_corrected_first_returns_to_original_series_with_one_counted_revision(self):
        self.approved()
        self.finish(goal='unmet')
        before = task.read(self.f.job)
        self.assertTrue(hasattr(task, 'create_revision'), 'Missing controlled revision creation')
        child = task.create_revision(self.f.job, 1, self.revision_spec(), approval_id='correction-one',
                                     note='Synthetic one-call approval to correct the same first-image person',
                                     identity_note='Synthetic user approves retaining this person')
        child_root = self.f.job / child['revision_origin']['path']
        root_job = self.f.job
        self.f.job = child_root
        self.finish()
        child = task.read(child_root)
        self.f.job = root_job
        adopted = task.adopt_revision(root_job, 'correction-one',
                                     expected_output_sha256=child['looks'][0]['output']['sha256'],
                                     note='Synthetic acceptance of corrected first image and continuation')
        self.assertEqual(adopted['attempts'], 1)  # direct requests only; the child is counted separately
        self.assertEqual(task.series_status(root_job)['series_attempts'], 2)
        self.assertEqual(adopted['looks'][0]['history'][0]['output'], before['looks'][0]['output'])
        self.assertEqual(adopted['looks'][0]['output']['sha256'], child['looks'][0]['output']['sha256'])
        self.assertEqual(adopted['model_confirmation']['output_sha256'], child['looks'][0]['output']['sha256'])
        task.adopt_revision(root_job, 'correction-one', expected_output_sha256=child['looks'][0]['output']['sha256'],
                            note='Idempotent re-reading of the same accepted result')
        self.assertEqual(task.series_status(root_job)['series_attempts'], 2)
        self.f.reserve(2)
        self.assertEqual(task.series_status(root_job)['series_attempts'], 3)

    def test_presentation_change_needs_confirmation_and_cannot_double_spend_original_slot(self):
        self.approved()
        self.finish()
        self.finish(2, goal='unmet')
        self.assertTrue(hasattr(task, 'create_revision'), 'Missing controlled revision creation')
        spec = self.revision_spec(still=True,number=2)
        with self.assertRaises(ValueError):
            task.create_revision(self.f.job, 2, spec, approval_id='static-two', note='One more call')
        child = task.create_revision(self.f.job, 2, spec, approval_id='static-two', note='One authorized call',
                                     form_change_note='Synthetic explicit change from worn detail to product still life')
        self.assertFalse(child['identity'])
        self.assertEqual([r['role'] for r in child['references']], ['garment-source'])
        with self.assertRaises(ValueError):
            task.create_revision(self.f.job, 2, spec, approval_id='static-two', note='Cannot reuse approval',
                                 form_change_note='Same change')
        with self.assertRaises(ValueError):
            task.update(self.f.job, 'retry-authorize', look=2, expected_attempt=1, approval_id='duplicate-slot',
                        note='Original slot is delegated', prompt='Unrelated retry')

    def test_changed_plan_invalidates_old_handoff_and_keeps_confirmation_history(self):
        self.approved()
        self.finish()
        self.finish(2,goal='unmet')
        before=task.read(self.f.job);plan=copy.deepcopy(before['shot_plan'])
        plan['looks'][1]['hands']='Hands rest flat below the printed panel, away from the garment.'
        changed=task.update(self.f.job,'retry-authorize',look=2,expected_attempt=1,approval_id='changed-plan',
            note='Synthetic explicit one-call revised action approval',shot_plan=plan,visual_plan=before['visual_plan'])
        self.assertEqual(len(changed['plan_confirmation_history']),1)
        with self.assertRaises(ValueError):
            task.update(self.f.job,'reserve',look=2,ready=True,refs=task.reference_hashes(self.f.job,2),
                        expected_plan_sha256=task.plan_fingerprint(before))
        self.assertEqual(task.read(self.f.job)['attempts'],2)
        self.f.reserve(2)
        self.assertEqual(task.read(self.f.job)['attempts'],3)

    def test_unknown_requests_and_unreconciled_failures_cannot_create_revisions(self):
        self.approved()
        self.finish()
        self.f.reserve(2)
        task.update(self.f.job,'unknown',look=2)
        spec=self.revision_spec(still=True,number=2)
        for state in ('unknown','failed'):
            with self.subTest(state=state):
                if state=='failed':self.provider_failure(2)
                with self.assertRaises(ValueError):
                    task.create_revision(self.f.job,2,spec,approval_id='not-checked',note='One correction',
                                         form_change_note='Explicit product presentation')
        self.assertEqual(task.series_status(self.f.job)['series_attempts'],2)
        self.assertFalse((self.f.job/'revisions/not-checked').exists())

    def test_checked_failed_first_can_retain_new_person_casting_without_an_invented_identity(self):
        self.f.model=dict(self.f.model,source_type='new')
        # New fictional casting has no identity reference.
        original=self.f.refs
        self.f.refs=lambda:original()[:1]
        self.approved()
        self.f.reserve()
        self.provider_failure(1)
        task.update(self.f.job,'reconcile-failure',look=1,expected_attempt=1,request_check_completed=True,
                    note='Synthetic original no-image request checked')
        child=task.create_revision(self.f.job,1,self.revision_spec(),approval_id='first-no-image',
                                   note='Synthetic one-call recovery with the same casting and target')
        root=self.f.job;self.f.job=root/child['revision_origin']['path']
        self.finish()
        accepted=task.read(self.f.job);self.f.job=root
        task.adopt_revision(root,'first-no-image',expected_output_sha256=accepted['looks'][0]['output']['sha256'],
                            note='Synthetic actual first-person acceptance')
        self.assertEqual(task.series_status(root)['series_attempts'],2)
        # Unreviewed same-group requests are still paused despite correcting this one slot.
        with self.assertRaisesRegex(ValueError,'moderation|hold'):self.f.reserve(2)

    def test_child_request_is_serialized_with_root_and_cannot_grant_itself_another_call(self):
        self.approved(details=(2,))
        self.finish();self.finish(2,goal='unmet')
        root=self.f.job
        child=task.create_revision(root,2,self.revision_spec(number=2),approval_id='serial-two',note='One corrected detail')
        self.f.job=root/child['revision_origin']['path'];self.f.reserve()
        with self.assertRaises(ValueError):task.update(self.f.job,'authorize',limit=1,note='Extra child budget')
        with self.assertRaises(ValueError):
            task.update(root,'reserve',look=3,ready=True,refs=task.reference_hashes(root,3),
                        expected_plan_sha256=task.plan_fingerprint(task.read(root)))
        with task.locked(root):
            with self.assertRaises(ValueError):task.update(self.f.job,'unknown',look=1)
        self.assertEqual(task.series_status(root)['series_attempts'],3)
        self.assertEqual(task.series_status(root)['series_authorized_requests'],10)

    def test_child_moderation_pauses_similar_root_shots_and_preserves_other_authority(self):
        self.approved(details=(2,3))
        self.finish();self.finish(2,goal='unmet')
        root=self.f.job
        child=task.create_revision(root,2,self.revision_spec(number=2),approval_id='moderation-child',note='One corrected detail')
        self.f.job=root/child['revision_origin']['path'];self.f.reserve();self.provider_failure(1)
        self.f.job=root
        with self.assertRaisesRegex(ValueError,'moderation|hold'):self.f.reserve(3)
        self.f.reserve(4)
        self.assertEqual(task.series_status(root)['series_attempts'],4)

    def test_non_moderation_provider_failure_does_not_use_the_unaffected_shot_exception(self):
        self.approved(details=(2,3));self.finish();self.f.reserve(2)
        self.provider_failure(2,'provider_error')
        with self.assertRaises(ValueError):self.f.reserve(4)
        self.assertEqual(task.read(self.f.job)['attempts'],2)

    def test_product_revision_adoption_reports_original_target_and_keeps_person_requirements_out(self):
        self.approved();self.finish();self.finish(2,goal='unmet')
        root=self.f.job
        child=task.create_revision(root,2,self.revision_spec(still=True,number=2),approval_id='static',
            note='One product detail',form_change_note='Synthetic user approves changing worn detail into still life')
        child_root=root/child['revision_origin']['path']
        task.export(child_root)
        request=json.loads(next((child_root/'handoff').glob('look-1-*/request.json')).read_text())
        self.assertIn('Show the printed chest and garment length.',request['prompt'])
        self.assertNotIn('Identity scope:',request['prompt'])
        self.assertEqual(len(request['referenced_image_paths']),1)
        self.f.job=child_root;self.f.reserve()
        returned=task.update(child_root,'returned',look=1,file=self.f.image('product-only','pink'))
        task.update(child_root,'accept',look=1,qa='qa-pass',review=self.review(identity=False),note='Synthetic product-only QA')
        self.f.job=root
        adopted=task.adopt_revision(root,'static',expected_output_sha256=returned['looks'][0]['output']['sha256'],note='Adopt this product detail')
        self.assertFalse(adopted['looks'][1]['adopted_revision']['identity'])
        self.assertEqual(task.series_status(root)['series_attempts'],3)
        with self.assertRaises(ValueError):task.update(child_root,'audit-reject',look=1,note='Cannot mutate an adopted child')
        with self.assertRaises(ValueError):task.update(root,'retry-authorize',look=2,expected_attempt=1,approval_id='static',note='Duplicate grant',prompt='x')
        task.check_evidence(root,task.read(root))

    def test_first_anchor_cannot_be_replaced_after_any_downstream_request(self):
        self.approved();self.finish();self.finish(2)
        with self.assertRaisesRegex(ValueError,'downstream'):
            task.create_revision(self.f.job,1,self.revision_spec(),approval_id='late-first',note='Change first after downstream')
        self.assertEqual(task.read(self.f.job)['attempts'],2)

    def test_ratio_first_revision_cannot_establish_a_different_pixel_baseline(self):
        self.f.context['canvas_policy']='ratio-first'
        self.approved();self.finish(goal='unmet')
        root=self.f.job
        child=task.create_revision(root,1,self.revision_spec(),approval_id='ratio-correction',note='One same-canvas correction')
        self.f.job=root/child['revision_origin']['path'];self.f.reserve()
        wrong=self.f.root/'same-ratio-wrong-pixels.png'
        fixtures.Image.new('RGB',(120,80),'pink').save(wrong)
        with self.assertRaisesRegex(ValueError,'canvas'):
            task.update(self.f.job,'returned',look=1,file=wrong)
        self.assertEqual(task.read(self.f.job)['looks'][0]['state'],'failed')
        self.assertEqual(task.series_status(root)['series_attempts'],2)

    def test_post_adoption_reassessment_keeps_source_review_and_actual_form(self):
        self.approved();self.finish();self.finish(2,goal='unmet')
        root=self.f.job
        child=task.create_revision(root,2,self.revision_spec(still=True,number=2),approval_id='still-first',
            note='One still correction',form_change_note='Actual synthetic change to still life')
        child_root=root/child['revision_origin']['path'];self.f.job=child_root;self.f.reserve()
        returned=task.update(child_root,'returned',look=1,file=self.f.image('new-still','pink'))
        task.update(child_root,'accept',look=1,qa='qa-pass',review=self.review(identity=False),note='Synthetic product review')
        self.f.job=root
        sha=returned['looks'][0]['output']['sha256']
        task.adopt_revision(root,'still-first',expected_output_sha256=sha,note='Adopt current still')
        reviewed=task.update(root,'review-output',look=2,expected_output_sha256=sha,qa='qa-retry',
                            review=self.review(identity=False,goal='unmet'),note='Later source review finds target missing')
        self.assertEqual(reviewed['looks'][1]['qa_history'][-1]['review']['goal']['result'],'met')
        self.assertEqual(task.read(child_root)['looks'][0]['review']['goal']['result'],'met')
        task.check_evidence(root,task.read(root))
        with self.assertRaises(ValueError):
            task.create_revision(root,2,self.revision_spec(number=2),approval_id='back-to-human',note='Another request without form approval')

    def test_source_unknown_and_photography_preferences_remain_separate_from_goal_failure(self):
        self.approved();self.f.reserve()
        task.update(self.f.job,'returned',look=1,file=self.f.image('source-unknown','lavender'))
        review=self.review();review['garment']['result']='unknown';review['photography']['result']='unmet'
        accepted=task.update(self.f.job,'accept',look=1,qa='qa-user-review',review=review,note='Source detail unknown; light is a preference')
        self.assertEqual(accepted['looks'][0]['qa'],'qa-user-review')
        self.assertFalse(accepted['files_complete']);self.assertFalse(accepted['goals_met'])
        self.assertEqual(accepted['delivery_status'],'image-draft')

    def test_library_text_selection_reaches_both_exports_without_history_or_lineart(self):
        for route in ('codex_native','chatgpt_web'):
            with self.subTest(route=route):
                self.f.job=self.f.root/route
                plan=self.f.plan()
                for shot in plan['looks']:
                    shot.pop('pose_reference',None);shot.pop('aesthetic_reference_sha256s',None)
                    shot['pose_decision']=dict(kind='custom',reason='Supported by the product front')
                plan=task.shot_helper().subset(plan,1,series_role='standalone')
                plan['looks']=plan['looks'][:1]
                plan,_=task.shot_helper().pose_library().apply(plan,plan['selected_shot_ids'][0],'tt-stand-neutral','front')
                self.assertNotIn('pose_decision',plan['looks'][0])
                visual=self.f.visual(plan)
                task.create(self.f.job,self.f.refs()[:2],None,[60,40],model=self.f.model,
                    context=self.f.context,shot_plan=plan,visual_plan=visual,route=route)
                self.confirm('single');task.update(self.f.job,'authorize',limit=1,note='One chosen pose')
                task.export(self.f.job)
                folder=next((self.f.job/'handoff').glob('look-1-*'))
                prompt=(folder/'prompt.txt').read_text();data=task.read(self.f.job)
                for field in ('body_action','hands','support'):
                    self.assertIn(plan['looks'][0]['pose_selection']['definition'][field],prompt)
                self.assertNotIn('pose_history',data['visual_plan'])
                self.assertEqual(len(task.references(self.f.job,data,1)),2)
                if route=='chatgpt_web':task.export_web_execution(self.f.job,1)

    def test_revision_cli_uses_the_same_root_authority_and_status(self):
        self.approved();self.finish(goal='unmet')
        spec=self.f.root/'revision.json';spec.write_text(json.dumps(self.revision_spec(),default=str))
        script=fixtures.ROOT/'skills/lookset/scripts/web-task.py'
        result=subprocess.run([sys.executable,str(script),'prepare-revision','--task',str(self.f.job),
            '--look','1','--spec',str(spec),'--approval-id','cli-revision','--note','One synthetic correction',
            '--identity-note','Keep this original model'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        child=json.loads(result.stdout)
        status=subprocess.run([sys.executable,str(script),'status','--task',str(self.f.job/child['revision_origin']['path'])],capture_output=True,text=True)
        self.assertEqual(status.returncode,0,status.stderr)
        self.assertEqual(json.loads(status.stdout)['series_authorized_requests'],10)

    def test_reconciled_provider_failure_can_revise_the_same_shot(self):
        self.f.create()
        task.update(self.f.job, 'authorize', limit=9, note='Synthetic nine-image approval')
        self.f.finish_one()
        self.f.reserve(2)
        failed = self.provider_failure(2)
        plan = copy.deepcopy(failed['shot_plan'])
        plan['looks'][1]['hands'] = 'Both hands rest below the garment hem, leaving its front clear.'
        visual = copy.deepcopy(failed['visual_plan'])
        visual['shots'][1]['composition'] = 'More space around the garment detail'
        args = dict(look=2, expected_attempt=1, approval_id='one-approved-revision',
                    note='Synthetic explicit approval for one revised request',
                    shot_plan=plan, visual_plan=visual)
        with self.assertRaises(ValueError):
            task.update(self.f.job, 'retry-authorize', **args)
        task.update(self.f.job, 'reconcile-failure', look=2, expected_attempt=1,
                    request_check_completed=True, note='Synthetic terminal failure checked; no image')
        try:
            revised = task.update(self.f.job, 'retry-authorize', **args)
        except ValueError as error:
            self.fail('A reconciled failure still cannot revise its plan: ' + str(error))
        self.assertEqual(revised['attempts'], 2)
        self.assertEqual(revised['looks'][1]['attempt_number'], 2)
        self.assertEqual(revised['looks'][1]['history'][0]['state'], 'failed')
        self.assertEqual(revised['looks'][0], failed['looks'][0])
        self.assertEqual(revised['looks'][2:], failed['looks'][2:])
        self.assertEqual(revised['shot_plan']['looks'][1]['hands'], plan['looks'][1]['hands'])
        self.assertEqual(revised['retry_authorizations'][0]['additional_requests'], 1)
        self.assertEqual(revised['retry_authorizations'][0]['source_state'], 'failed')
        task.check_evidence(self.f.job, task.read(self.f.job))
        with self.assertRaises(ValueError):
            task.update(self.f.job, 'retry-authorize', **args)

if __name__ == '__main__':
    unittest.main()
