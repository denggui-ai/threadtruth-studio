"""Nine-shot lifecycle and actual attachment regressions using synthetic PNGs.

Color blocks exercise the ledger only; no test asserts image quality or consent.
"""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image
from tests.test_pose_plan_v2 import sample_plan

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('nine_task_under_test', ROOT / 'skills/threadtruth-studio/scripts/web-task.py')
task = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(task)


class NineTaskTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.job = self.root / 'job'
        self.front = self.image('garment', 'red')
        self.face = self.image('identity', 'blue')
        self.pose_a = self.image('pose-a', 'green')
        self.pose_b = self.image('pose-b', 'orange')
        self.art_a = self.image('art-a', 'purple')
        self.art_b = self.image('art-b', 'cyan')
        self.context = dict(outfit='printed-top', style='nordic-minimal', mode='C', output_form='human',
                            size=[60, 40], first_pose=1, purpose='delivery')
        self.model = dict(source_type='ai', scope='full', subject='adult female model',
                          locked=['adult'], adjustable=[], consent_note='')

    def image(self, name, color):
        path = self.root / (name + '.png')
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new('RGB', (60, 40), color).save(path)
        return path

    def refs(self):
        rows = [dict(path=self.front, role='garment-source'), dict(path=self.face, role='identity-reference')]
        for name, path in (('pose-a', self.pose_a), ('pose-b', self.pose_b)):
            rows.append(dict(path=path, role='pose-reference', pose_source=dict(source_id='owned-studio',
                group_id=name, view='front', usage='owned', note='Synthetic owned view reviewed for ledger testing.')))
        rows.extend([dict(path=self.art_a, role='aesthetic-reference'), dict(path=self.art_b, role='aesthetic-reference')])
        return rows

    def plan(self):
        plan = sample_plan(back=False)
        plan['coverage'][0]['sha256'] = task.digest(self.front)
        for item in plan['looks']:
            item['reference_sha256s'] = [task.digest(self.front)]
        plan['looks'][6]['pose_reference'] = dict(sha256=task.digest(self.pose_a), reason='Reviewed support A.')
        plan['looks'][7]['pose_reference'] = dict(sha256=task.digest(self.pose_b), reason='Reviewed support B.')
        plan['looks'][1]['aesthetic_reference_sha256s'] = [task.digest(self.art_a)]
        plan['looks'][6]['aesthetic_reference_sha256s'] = [task.digest(self.art_b)]
        return plan

    def visual(self, plan):
        snapshot = dict(id='nordic-minimal', schema_version=1, photography=dict(scene='stone gallery'),
                        evidence=dict(visual_status='unverified', records=[]))
        component = dict(id='nordic-minimal', version=1, sha256=task.object_hash(snapshot), snapshot=snapshot)
        return dict(version=2, objective='styled-editorial', output_medium='photography', output_form='human',
            style=dict(primary=component, supporting=[], fusion_note=''),
            garment=dict(description='Original printed red top.', keep=['red color', 'source print', 'existing hem'],
                         source_sha256s=[task.digest(self.front)]),
            styling=[], photography=dict(scene='Quiet stone gallery', lighting='Soft window light',
                composition='Breathing space around the subject', palette='Neutral surroundings'),
            art=dict(direction='Restrained geometry', techniques=[], limits=['Do not alter original garment facts']),
            negatives=['No invented product structure'],
            shots=[dict(slot=item['slot'], shot_id=item['shot_id'], scene='Gallery bay', lighting='Soft window light',
                        composition='Negative space balanced with the subject') for item in task.shot_helper().active_looks(plan)])

    def create(self, *, plan=None, preview=False, route='codex_native', refs=None, real=None, model=None):
        plan = plan or self.plan()
        context = dict(self.context, first_pose=task.shot_helper().active_looks(plan)[0]['slot'],
                       purpose='preview-grid' if preview else 'delivery')
        return task.create(self.job, refs or self.refs(), None, [60, 40], model=model or self.model,
                           context=context, route=route, shot_plan=plan, visual_plan=self.visual(plan), real_face_plan=real)

    def reserve(self, number=1):
        data = task.read(self.job)
        return task.update(self.job, 'reserve', look=number, ready=True, refs=task.reference_hashes(self.job, number),
            expected_plan_sha256=task.plan_fingerprint(data), expected_prompt_sha256=data['looks'][number - 1]['prompt_sha256'],
            **({'conversation': 'https://chatgpt.com/c/synthetic-nine'} if data['route']=='chatgpt_web' else {}))

    def finish_one(self, number=1, reject=False):
        self.reserve(number)
        task.update(self.job, 'returned', look=number, file=self.image('output-' + str(number), (20 * number, 31, 72)))
        task.update(self.job, 'reject' if reject else 'accept', look=number, qa='qa-pass', note='Synthetic ledger review, no visual assertion.')
        if number == 1 and not reject and not task.is_preview(task.read(self.job)):
            task.update(self.job, 'confirm-model', look=1, note='Synthetic first-model acceptance fixture.')

    def preview(self):
        self.create(preview=True)
        task.update(self.job, 'authorize', limit=1, note='Synthetic preview request authority.')
        self.finish_one()
        return task.update(self.job, 'finish-preview', decision='direction-confirmed', note='Synthetic direction confirmation.')

    def complete_nine(self, reject_seven=False, route='codex_native'):
        self.create(route=route)
        task.update(self.job, 'authorize', limit=9, note='Synthetic nine request authority.')
        for n in range(1, 10):
            self.finish_one(n, reject=reject_seven and n == 7)
        return task.read(self.job)

    def test_new_casting_and_anchor_pose_instructions_reach_frozen_handoff(self):
        plan = self.plan()
        plan['looks'][2]['body_action'] = ('Retain anchor identity but do not copy its pose, hands, or support; '
                                           'stand with both hands visibly outside pockets.')
        visual = self.visual(plan)
        visual['garment']['description'] += ' Use garment facts only; do not copy the person face, hair or expression.'
        data = task.create(self.job, self.refs(), None, [60, 40], model=self.model,
                           context=self.context, route='codex_native', shot_plan=plan, visual_plan=visual)
        prompt = task.handoff_prompt(data, data['looks'][2], task.selected_references(
            data['references'], data['context'], data['shot_plan'], None, 3))
        self.assertIn('do not copy the person face, hair or expression', prompt)
        self.assertIn('do not copy its pose, hands, or support', prompt)
        self.assertIn('both hands visibly outside pockets', prompt)

    def test_new_identity_scope_and_anchor_pose_are_versioned(self):
        model = dict(source_type='new', scope='full', subject='adult female model',
                     locked=['adult'], adjustable=[], consent_note='')
        refs = [dict(path=self.front, role='garment-source')]
        plan = self.plan()
        for shot in plan['looks']:
            shot.pop('pose_reference', None)
            shot.pop('aesthetic_reference_sha256s', None)
        self.create(plan=plan, refs=refs, model=model)
        data = task.read(self.job)
        first = task.handoff_prompt(data, data['looks'][0], task.references(self.job, data, 1))
        self.assertIn('create a new fictional person distinct', first)
        self.assertNotIn('Identity scope: preserve visible face', first)
        task.update(self.job, 'authorize', limit=9, note='Synthetic authorization.')
        self.finish_one()
        data = task.read(self.job)
        later = task.handoff_prompt(data, data['looks'][1], task.references(self.job, data, 2))
        self.assertIn('preserve the accepted first-image identity', later)
        self.assertIn('do not copy its pose, hands, support or framing', later)
        legacy = dict(data)
        legacy.pop('identity_instruction_version')
        old = task.handoff_prompt(legacy, legacy['looks'][1], task.references(self.job, data, 2))
        self.assertIn('Identity scope: preserve visible face', old)
        self.assertNotIn('do not copy its pose, hands, support or framing', old)

    def test_two_routes_export_identical_nine_plan_first_prompt(self):
        prompts = []
        for route in ('codex_native', 'chatgpt_web'):
            self.job = self.root / route
            data = self.create(route=route)
            self.assertEqual(len(data['looks']), 9)
            task.export(self.job)
            folder = next((self.job / 'handoff').glob('look-1*'))
            prompts.append((folder / 'prompt.txt').read_text())
            manifest = json.loads((folder / 'manifest.json').read_text())
            self.assertEqual(manifest['shot_plan']['version'], 2)
            self.assertEqual(manifest['reference_hashes'], [task.digest(self.front), task.digest(self.face)])
        self.assertEqual(prompts[0], prompts[1])

    def test_actual_pose_and_aesthetic_references_do_not_leak_across_shots(self):
        data = self.complete_nine()
        expected = {2: (None, self.art_a), 7: (self.pose_a, self.art_b), 8: (self.pose_b, None)}
        for n in range(1, 10):
            rows = task.references(self.job, data, n)
            pose, art = expected.get(n, (None, None))
            self.assertEqual([r['sha256'] for r in rows if r['role']=='pose-reference'], [task.digest(pose)] if pose else [])
            self.assertEqual([r['sha256'] for r in rows if r['role']=='aesthetic-reference'], [task.digest(art)] if art else [])
            self.assertIn(task.digest(self.front), {r['sha256'] for r in rows})
            self.assertIn(task.digest(self.face), {r['sha256'] for r in rows})
            if n > 1:self.assertEqual(rows[-1]['role'], 'identity-only')
        self.assertEqual(data['attempts'], 9)

    def test_seventh_pose_export_uses_same_actual_attachment_order_on_both_routes(self):
        prompts = []
        for route in ('codex_native','chatgpt_web'):
            self.job = self.root / ('pose-export-' + route)
            self.create(route=route)
            task.update(self.job,'authorize',limit=9,note='Synthetic nine request authority.')
            for n in range(1,7):self.finish_one(n)
            data = task.read(self.job)
            rows = task.references(self.job,data,7)
            self.assertEqual([r['role'] for r in rows],
                             ['garment-source','identity-reference','pose-reference','aesthetic-reference','identity-only'])
            task.export(self.job)
            folder = next((self.job/'handoff').glob('look-7-*'))
            prompt = (folder/'prompt.txt').read_text()
            prompts.append(prompt)
            manifest = json.loads((folder/'manifest.json').read_text())
            self.assertEqual(manifest['reference_hashes'],[r['sha256'] for r in rows])
            self.assertIn('Image 3:',prompt)
            self.assertIn('Shot 7: garment-shot-7',prompt)
            self.assertNotIn('Reviewed support B.',prompt)
            self.assertEqual(len(list(folder.glob('*.png'))),5)
        self.assertEqual(prompts[0],prompts[1])

    def test_catalog_reference_hash_is_accepted_and_verified_at_import(self):
        refs = self.refs()
        refs[2]['sha256'] = task.digest(self.pose_a)
        data = self.create(refs=refs)
        self.assertEqual(next(r for r in data['references'] if r['sha256']==task.digest(self.pose_a))['pose_source'],refs[2]['pose_source'])
        self.job = self.root/'tampered-catalog'
        refs[2]['sha256'] = 'f'*64
        with self.assertRaisesRegex(ValueError,'hash'):
            self.create(refs=refs)
        self.assertFalse(self.job.exists())

    def test_preview_has_nine_cells_and_omits_pose_images(self):
        data = self.create(preview=True)
        rows = task.references(self.job, data, 1)
        self.assertFalse(any(r['role']=='pose-reference' for r in rows))
        prompt = task.handoff_prompt(data, data['looks'][0], rows)
        self.assertIn('nine-panel 3x3', prompt)
        self.assertIn('Shot 9: garment-shot-9', prompt)
        self.assertNotIn('Image 5:', prompt)

    def test_preview_seventh_single_retains_full_plan_and_has_no_inherited_authority(self):
        parent = self.preview()
        child_path = self.root / 'seventh'
        child = task.create_from_preview(child_path, self.job,
            dict(context=dict(self.context, first_pose=7), size=[60,40], count=1), note='Synthetic seventh single request.')
        self.assertEqual(len(child['looks']), 1)
        self.assertEqual(len(child['shot_plan']['looks']), 9)
        self.assertEqual(child['shot_plan']['selected_shot_ids'], ['garment-shot-7'])
        self.assertEqual(child['visual_plan']['shots'][0]['slot'], 7)
        self.assertEqual(child['shot_plan']['series_role'], 'standalone')
        self.assertIsNone(child['authorization'])
        self.assertIsNone(child['model_confirmation'])
        self.assertEqual(child['attempts'], 0)
        self.assertEqual(child['preview_origin']['attempts'], parent['attempts'])
        self.job = child_path
        task.update(self.job,'authorize',limit=1,note='Synthetic single request authority.')
        self.finish_one()
        with self.assertRaisesRegex(ValueError,'series-first'):
            task.update(self.job,'continue-authorize',context=child['context'],approval_id='bad-single',
                        note='Should not expand standalone.',prompts=['No.']*8)

    def test_complete_preview_defaults_to_nine_without_replanning(self):
        parent = self.preview()
        child = task.create_from_preview(self.root/'nine-child',self.job,
            dict(context=self.context,size=[60,40]),note='Synthetic complete delivery request.')
        self.assertEqual(len(child['looks']),9)
        self.assertEqual(child['shot_plan'],parent['shot_plan'])
        self.assertEqual(child['visual_plan'],parent['visual_plan'])
        self.assertEqual(child['preview_origin']['attempts'],1)
        self.assertEqual(child['attempts'],0)

    def test_series_first_continues_eight_preserving_first_and_budget(self):
        full = self.plan()
        trial = task.shot_helper().subset(full,1,series_role='series-first')
        data = self.create(plan=trial)
        task.update(self.job,'authorize',limit=1,note='Synthetic one-shot trial authority.')
        self.finish_one()
        before = task.read(self.job)
        first_prompt = task.handoff_prompt(before,before['looks'][0],task.references(self.job,before,1))
        data = task.update(self.job,'continue-authorize',context=data['context'],approval_id='rest-eight',
            note='Synthetic remaining eight authority.',shot_plan=full,visual_plan=self.visual(full))
        self.assertEqual(len(data['looks']),9)
        self.assertEqual(data['attempts'],1)
        self.assertEqual(data['authorization']['limit'],1)
        self.assertEqual(data['continuation_authorization']['additional_requests'],8)
        self.assertEqual(data['looks'][0],before['looks'][0])
        self.assertEqual(task.handoff_prompt(data,data['looks'][0],task.references(self.job,data,1)),first_prompt)
        for number in range(2,10):self.finish_one(number)
        self.assertEqual(task.read(self.job)['attempts'],9)

    def test_series_first_cannot_replan_remaining_shots_during_continuation(self):
        full = self.plan()
        trial = task.shot_helper().subset(full,1,series_role='series-first')
        data = self.create(plan=trial)
        task.update(self.job,'authorize',limit=1,note='Synthetic one request.')
        self.finish_one()
        changed = copy.deepcopy(full)
        changed['looks'][6]['body_action'] = 'An unreviewed replacement action.'
        saved = (self.job/'task.json').read_bytes()
        with self.assertRaisesRegex(ValueError,'without re-planning'):
            task.update(self.job,'continue-authorize',context=data['context'],approval_id='bad-replan',
                note='Invalid implicit plan change.',shot_plan=changed,visual_plan=self.visual(changed))
        self.assertEqual((self.job/'task.json').read_bytes(),saved)

    def test_required_source_capacity_rejects_before_creating_task(self):
        plan = self.plan()
        extra = self.image('third-art','pink')
        plan['looks'][6]['aesthetic_reference_sha256s'] = [task.digest(self.art_a),task.digest(self.art_b),task.digest(extra)]
        with self.assertRaisesRegex(ValueError,'five'):
            self.create(plan=plan,refs=self.refs()+[dict(path=extra,role='aesthetic-reference')])
        self.assertFalse(self.job.exists())

    def test_trial_and_preview_preflight_capacity_for_future_independent_shots(self):
        full = self.plan()
        full['looks'][6]['aesthetic_reference_sha256s'] = [task.digest(self.art_a),task.digest(self.art_b)]
        for preview in (False,True):
            self.job = self.root / ('future-capacity-' + str(preview))
            plan = full if preview else task.shot_helper().subset(full,1,series_role='series-first')
            with self.subTest(preview=preview), self.assertRaisesRegex(ValueError,'five'):
                self.create(plan=plan,preview=preview)
            self.assertFalse(self.job.exists())

    def test_research_source_cannot_be_routed_as_another_role(self):
        source = self.image('ai-pose-gallery-zh/img/fixture','white')
        for role in ('garment-source','aesthetic-reference','identity-reference'):
            with self.subTest(role=role), self.assertRaisesRegex(ValueError,'research'):
                self.create(refs=self.refs()+[dict(path=source,role=role)])
        self.assertFalse(self.job.exists())

    def test_retry_seventh_changes_only_failed_shot_and_keeps_output_history(self):
        before = self.complete_nine(reject_seven=True)
        changed = copy.deepcopy(before['shot_plan'])
        changed['looks'][6].update(body_action='Stand upright with hands clear of print.',framing='half-body',
                                  pose_reference=dict(sha256=task.digest(self.pose_b),reason='Reviewed alternative hand position.'))
        visual = copy.deepcopy(before['visual_plan'])
        visual['shots'][6]['composition'] = 'Keep balanced negative space for the accepted display purpose.'
        others = {n:task.handoff_prompt(before,before['looks'][n-1],task.references(self.job,before,n)) for n in range(1,10) if n!=7}
        after = task.update(self.job,'retry-authorize',look=7,expected_attempt=1,approval_id='retry-seven',
            note='Synthetic one targeted retry authority.',shot_plan=changed,visual_plan=visual)
        self.assertEqual(after['attempts'],9)
        self.assertEqual(after['authorization'],before['authorization'])
        self.assertEqual(after['model_confirmation'],before['model_confirmation'])
        self.assertEqual(after['looks'][6]['history'][0]['output'],before['looks'][6]['output'])
        self.assertEqual(after['looks'][6]['history'][0]['qa'],'qa-retry')
        self.assertEqual(after['looks'][6]['attempt_number'],2)
        for n,prompt in others.items():
            self.assertEqual(after['looks'][n-1],before['looks'][n-1])
            self.assertEqual(task.handoff_prompt(after,after['looks'][n-1],task.references(self.job,after,n)),prompt)
        task.check_evidence(self.job,after)

    def test_retry_seventh_rejects_other_shot_changes_atomically(self):
        before = self.complete_nine(reject_seven=True)
        changed = copy.deepcopy(before['shot_plan'])
        changed['looks'][6]['body_action'] = 'Reviewed correction.'
        changed['looks'][7]['body_action'] = 'Unrequested different shot.'
        saved = (self.job/'task.json').read_bytes()
        with self.assertRaisesRegex(ValueError,'only the rejected shot'):
            task.update(self.job,'retry-authorize',look=7,expected_attempt=1,approval_id='bad-seven',
                        note='Invalid collateral change.',shot_plan=changed,visual_plan=before['visual_plan'])
        self.assertEqual((self.job/'task.json').read_bytes(),saved)

    def test_standalone_seventh_can_retry_its_local_look_one_without_becoming_anchor(self):
        plan = task.shot_helper().subset(self.plan(),7)
        self.create(plan=plan)
        task.update(self.job,'authorize',limit=1,note='Synthetic standalone authority.')
        self.finish_one(reject=True)
        before = task.read(self.job)
        changed = copy.deepcopy(before['shot_plan'])
        changed['looks'][6].update(body_action='Reviewed relaxed standing correction.',framing='half-body')
        visual = copy.deepcopy(before['visual_plan'])
        visual['shots'][0]['composition'] = 'Clear negative space for the accepted purpose.'
        after = task.update(self.job,'retry-authorize',look=1,expected_attempt=1,approval_id='standalone-seven',
            note='Synthetic targeted single correction.',shot_plan=changed,visual_plan=visual)
        self.assertEqual(after['shot_plan']['series_role'],'standalone')
        self.assertEqual(after['shot_plan']['selected_shot_ids'],['garment-shot-7'])
        self.assertEqual(len(after['looks']),1)
        self.assertEqual(after['attempts'],1)
        self.assertEqual(after['looks'][0]['history'][0]['output'],before['looks'][0]['output'])
        self.assertIsNone(after['model_confirmation'])
        task.check_evidence(self.job,after)

    def test_pose_source_metadata_cannot_drop_its_freeze_hash(self):
        data = self.create()
        data.pop('references_sha256')
        next(r for r in data['references'] if r['role']=='pose-reference')['pose_source']['note'] = 'Changed review claim.'
        with self.assertRaisesRegex(ValueError,'metadata|reference'):
            task.check_evidence(self.job,data)

    def real_plan(self,plan):
        return dict(primary_identity_sha256=task.digest(self.face),
            coverage=[dict(sha256=task.digest(self.face),views=['front'],note='Synthetic original front coverage.')],
            looks=[dict(body_action='Preparation mirror will replace this draft.',head_view='front',gaze='At the camera.',
                        face_visible=True,reference_sha256s=[task.digest(self.face),task.digest(self.front)],
                        selection_note='Original identity and this garment.') for _ in task.shot_helper().active_looks(plan)])

    def test_real_nine_body_mirrors_shot_plan_and_original_face_coverage_remains_required(self):
        plan = self.plan()
        model = dict(self.model,source_type='real',scope='face',consent_note='Synthetic actual permission record.')
        bad = self.real_plan(plan)
        bad['looks'][6]['head_view'] = 'left-profile'
        with self.assertRaisesRegex(ValueError,'original view'):
            self.create(plan=plan,real=bad,model=model)
        data = self.create(plan=plan,real=self.real_plan(plan),model=model)
        for s,f in zip(plan['looks'],data['real_face_plan']['looks']):
            self.assertEqual(f['body_action'],task.shot_helper().body_text(s))
            self.assertEqual(f['head_view'],'front')
        task.check_evidence(self.job,data)

    def test_real_preview_cell_reference_labels_use_current_shot_selection(self):
        plan = self.plan()
        real = self.real_plan(plan)
        real['looks'][0]['reference_sha256s'].append(task.digest(self.art_a))
        model = dict(self.model,source_type='real',scope='face',consent_note='Synthetic actual permission record.')
        data = self.create(plan=plan,preview=True,real=real,model=model)
        rows = task.references(self.job,data,1)
        positions = {r['sha256']:i for i,r in enumerate(rows,1)}
        art_a_number = positions[task.digest(self.art_a)]
        raw = task.handoff_prompt(data,data['looks'][0],rows)
        first = raw.split('Preview cell 1:\n',1)[1].split('Preview cell 2:\n',1)[0]
        second = raw.split('Preview cell 2:\n',1)[1].split('Preview cell 3:\n',1)[0]
        self.assertNotIn('Image '+str(art_a_number),first)
        self.assertIn('Image '+str(art_a_number),second)
        self.assertFalse(any(r['role']=='pose-reference' for r in rows))

    def test_six_remains_explicit_v2_choice(self):
        plan = self.plan()
        plan['looks'] = plan['looks'][:6]
        plan['selected_shot_ids'] = plan['selected_shot_ids'][:6]
        data = self.create(plan=plan)
        self.assertEqual(len(data['looks']),6)
        self.assertEqual(data['shot_plan']['version'],2)

    def test_preview_revisions_preflight_future_delivery_capacity_atomically(self):
        self.create(preview=True)
        task.update(self.job,'authorize',limit=1,note='Synthetic preview authority.')
        self.finish_one()
        data = task.read(self.job)
        changed = copy.deepcopy(data['shot_plan'])
        changed['looks'][6]['aesthetic_reference_sha256s'] = [task.digest(self.art_a),task.digest(self.art_b)]
        before = (self.job/'task.json').read_bytes()
        # The preview union still fits, but the seventh independent shot plus
        # its required identity anchor would need six attachments.
        with self.assertRaisesRegex(ValueError,'five'):
            task.update(self.job,'revise-preview',look=1,shot_plan=changed,visual_plan=self.visual(changed),
                expected_output_sha256=data['looks'][0]['output']['sha256'],note='Synthetic revised pose selection.')
        self.assertEqual((self.job/'task.json').read_bytes(),before)
        donor = self.image('composition-donor','yellow')
        with self.assertRaisesRegex(ValueError,'five'):
            task.update(self.job,'compose-preview',look=1,file=donor,shot_plan=changed,
                expected_output_sha256=data['looks'][0]['output']['sha256'],
                expected_donor_sha256=task.digest(donor),rectangle=[0,0,2,2],note='Synthetic local preview revision.')
        self.assertEqual((self.job/'task.json').read_bytes(),before)

    def test_preview_added_garment_cannot_import_known_research_source(self):
        self.create(preview=True)
        task.update(self.job,'authorize',limit=1,note='Synthetic preview authority.')
        self.finish_one()
        data = task.read(self.job)
        research = self.image('ai-pose-gallery-zh/img/research','pink')
        digest = task.digest(research)
        changed = copy.deepcopy(data['shot_plan'])
        changed['coverage'].append(dict(sha256=digest,views=['front'],usable=True,same_sku=True,
            note='Synthetic attempted reassignment; this is not an authorized product source.'))
        changed['looks'][0]['reference_sha256s'] = [digest]
        before = (self.job/'task.json').read_bytes()
        for check_sources in (True,False):
            with self.subTest(check_sources=check_sources), self.assertRaisesRegex(ValueError,'research-only'):
                task.preview_candidate(data,data['looks'][0],shot_plan=changed,visual_plan=self.visual(changed),
                    garment_references=[dict(path=str(research),sha256=digest)],check_sources=check_sources)
        self.assertEqual((self.job/'task.json').read_bytes(),before)
        self.assertNotIn(digest,{r['sha256'] for r in task.read(self.job)['references']})

    def test_ai_and_new_previews_transmit_each_cells_selected_aesthetic_images(self):
        for source_type in ('ai','new'):
            with self.subTest(source_type=source_type):
                self.job = self.root/('cell-mapping-'+source_type)
                refs = [r for r in self.refs() if source_type=='ai' or r['role']!='identity-reference']
                data = self.create(preview=True,refs=refs,model=dict(self.model,source_type=source_type))
                rows = task.references(self.job,data,1)
                positions = {r['sha256']:i for i,r in enumerate(rows,1)}
                raw = task.handoff_prompt(data,data['looks'][0],rows)
                self.assertEqual(raw.count('Cell reference images:'),9)
                common = [positions[task.digest(self.front)]]
                if source_type=='ai':common.append(positions[task.digest(self.face)])
                for number,art in ((1,None),(2,self.art_a),(7,self.art_b)):
                    section = raw.split(f'Preview cell {number}:\n',1)[1].split('Preview cell ',1)[0]
                    actual = section.split('Cell reference images: ',1)[1].split('.',1)[0]
                    expected = common+([positions[task.digest(art)]] if art else [])
                    self.assertEqual(actual,', '.join(f'Image {i}' for i in expected))
                    self.assertIn('Shot identity: garment-shot-'+str(number),section)
                self.assertFalse(any(r['role']=='pose-reference' for r in rows))


if __name__ == '__main__':
    unittest.main()
