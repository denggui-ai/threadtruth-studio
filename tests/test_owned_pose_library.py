"""Owned selection must survive actual plan validation without changing old plans."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path
from test_pose_plan_v2 import sample_plan, inventory, shot, FRONT, BACK
import test_nine_task as ledger_fixtures

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('owned_poses', ROOT / 'skills/threadtruth-studio/scripts/pose_library.py')
library = importlib.util.module_from_spec(spec)
spec.loader.exec_module(library)


class OwnedPoseTests(unittest.TestCase):
    def checked(self, plan, extra=()):
        return shot.validate(plan, inventory()+list(extra), context=dict(first_pose=1, output_form='human', purpose='delivery'),
                             count=len(plan['selected_shot_ids']), model_source='ai')

    def choose(self, mode='text'):
        return library.apply(sample_plan(1), 'garment-shot-1', 'tt-stand-neutral', 'front', mode=mode)

    def test_catalog_is_portable_unique_and_hash_checked(self):
        rows = library.candidates(include_restricted=True)
        self.assertEqual((len(rows),len({r['group_id'] for r in rows})),(60,52))
        # Final gallery-data + correction targets, not the initial manifest's old filenames.
        inventory_digest=library.digest(sorted((r['group_id'],r['view'],r['path'],r['sha256']) for r in rows))
        self.assertEqual(inventory_digest,'2f950f254ae61a630290f3c01c52e5c66e84e0029dabb5d26b3f36e17aa5c755')
        for r in rows:
            selected, ref = library.selection(r['group_id'],r['view'],origin='user')
            self.assertEqual(r['sha256'], selected['definition']['sha256'])
            if ref is not None:self.assertEqual(ref['sha256'], r['sha256'])
        self.assertTrue(all(set(r['garment_views']) <= {'front'} for r in library.candidates(garment_views=['front'])))

    def test_page_and_images_use_the_same_complete_catalog(self):
        catalog = json.loads(library.CATALOG.read_text())['entries']
        page = library.CATALOG.with_name('index.html').read_text()
        embedded, _ = json.JSONDecoder().raw_decode(page.split('const entries=',1)[1])
        self.assertEqual(embedded,catalog)
        self.assertEqual({p.name for p in (library.CATALOG.parent/'images').iterdir()},
                         {Path(r['path']).name for r in catalog})
        for family in {r['family'] for r in catalog}:
            self.assertIn('value="'+family+'"',page)

    def test_restricted_sleeve_requires_user_selection_and_explicit_image_mode(self):
        pose,view='tt-close-sleeve-push','diag'
        self.assertFalse(library.candidates(query=pose))
        rows=library.candidates(query=pose,include_restricted=True)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['path'],'images/tt-close-sleeve-push--diag--v4.png')
        self.assertEqual(rows[0]['sha256'],'86304016ed6103496567a9bd9cf41a8a6e70aa492219f672bd27564c16bfc795')
        for origin,mode in [('auto','text'),('auto','image')]:
            with self.subTest(origin=origin,mode=mode),self.assertRaisesRegex(ValueError,'user-only'):
                library.selection(pose,view,origin=origin,mode=mode)
        selected,ref=library.selection(pose,view,origin='user')
        self.assertIsNone(ref)
        self.assertEqual(selected['definition']['selection_policy'],'user-only')
        explicit,image_ref=library.selection(pose,view,origin='user',mode='image')
        self.assertEqual(image_ref['sha256'],rows[0]['sha256'])
        self.assertIn('仍遮腹',image_ref['pose_source']['note'])
        helper=library._catalog()
        with self.assertRaisesRegex(ValueError,'user-only'):
            helper.reference(helper.load(library.CATALOG),pose,view)
        for value in (selected,explicit):
            with self.assertRaisesRegex(ValueError,'user-only'):
                library._validate_snapshot(dict(value,origin='auto'))
        for policy in ('unrestricted',None,[]):
            changed=copy.deepcopy(selected)
            changed['definition']['selection_policy']=policy
            changed['definition_sha256']=library.digest(changed['definition'])
            with self.assertRaisesRegex(ValueError,'policy'):library._validate_snapshot(changed)

    def test_new_side_view_cannot_use_front_only_evidence(self):
        with self.assertRaisesRegex(ValueError,'garment views'):
            library.apply(sample_plan(1),'garment-shot-1','tt-kneel-half','side')
        plan=sample_plan(1)
        plan['looks'][0]['garment_views']=['front-side']
        plan,_=library.apply(plan,'garment-shot-1','tt-kneel-half','side')
        plan['coverage'][0]['views']=['front']
        with self.assertRaisesRegex(ValueError,'coverage'):self.checked(plan)

    def test_all_added_definitions_validate_with_supported_product_views(self):
        for row in library.candidates(include_restricted=True)[16:]:
            with self.subTest(pose=row['group_id'],view=row['view']):
                plan=sample_plan(1)
                plan['looks'][0]['garment_views']=row['garment_views']
                plan,ref=library.apply(plan,'garment-shot-1',row['group_id'],row['view'],origin='user')
                self.assertIsNone(ref)
                self.checked(plan)

    def test_original_sixteen_frozen_definitions_remain_compatible(self):
        # Definition hashes from 44e7568; a catalog expansion must not migrate old selections.
        expected={
            ('tt-stand-neutral','front'):'aab79c26237c05261ed5c403faa2c032214302c30439c297b7e54718540e58cf',
            ('tt-stand-weight-shift','diag'):'65666a720356987f1d32f0bc08c74903465ea8ffe9fd94e4eed41c2c20dc3348',
            ('tt-turn-front-counter','diag'):'faa07862eafb4d25ec06286076ab32c7be87a7df1d25447d3dfe7e3071802d0a',
            ('tt-turn-front-counter','front'):'527aad04566b641745dd7f199b556106b37cfe7d16bd203bdabfd91e8a21691e',
            ('tt-walk-pause','front'):'1a9618d4c1920e7c80dee549f7bed42affd819b9ec3a3360ae4567a28edea6ff',
            ('tt-walk-pause','back'):'34f0bbe2a5ceb222edf8d68c72b9e0138f283c080ab80ca1a62c65c037471d36',
            ('tt-stand-wide-anchor','front'):'a83a3980ef9d696a52262d94443d46db8880a229934a850c653bc243be5955c1',
            ('tt-stand-hip-frame','front'):'aa8ed5c21d8f43ed9a24ef53015c0771939ad0a4dc6ddd1b371d7227ae51235b',
            ('tt-lean-shoulder-stagger','diag'):'31effefceafe55b816efed821acc0635d2a14c87ab9607120bf29f43dacb44b7',
            ('tt-sit-upright','front'):'eed7a5a3e3d7621452e5978f1d79c79ced60eb8540b13e70604c96982c994042',
            ('tt-close-collar-touch','front'):'5852eff70435a42bd7f9c6be8dc1bebaa60f7d53479c1cac4be813a202c930f3',
            ('tt-close-cuff-adjust','diag'):'58507e832ddc295314f13514fb3c50ec55529ad9bb12cb4c2259dabcd328198b',
            ('tt-close-ear-tuck','diag'):'75cba084703e9b2b5525ec25ade83f4febcd8ab34f2518dafac305f6713c5e14',
            ('tt-close-jaw-touch','diag'):'852667bc2a4d42f80322b7cc6ae40a0d90314969d1bb812d2db67988a6602585',
            ('tt-turn-back-still','back'):'426f9d88d0285afbd61e232bcc37e672febff0750ff8c5b2d43efd56c7aa108e',
            ('tt-turn-back-quarter','back'):'6f0cde3eac8b8cb8c2ad56296e6387de7715233557a298357090acdbc579bb64',
        }
        for (pose,view),digest in expected.items():
            with self.subTest(pose=pose,view=view):
                selected,_=library.selection(pose,view)
                self.assertEqual(selected['definition_sha256'],digest)
                self.assertEqual(set(selected['definition']),library.DEFINITION_FIELDS)

    def test_text_and_image_share_body_but_select_different_attachments(self):
        text, no_ref = self.choose()
        image, ref = self.choose('image')
        self.assertIsNone(no_ref)
        self.checked(text)
        self.checked(image,[ref])
        for key in ('body_action','hands','support'):
            self.assertEqual(text['looks'][0][key],image['looks'][0][key])
        self.assertEqual(shot.pose_selected(text,1),set())
        self.assertEqual(shot.pose_selected(image,1),{ref['sha256']})
        self.assertEqual(shot.pose_selected(image,1,preview=True),set())

    def test_selected_hash_view_id_and_mode_cannot_drift(self):
        plan,ref=self.choose('image')
        for change in ('sha256','view','group_id'):
            wrong=copy.deepcopy(ref)
            if change=='sha256':wrong[change]='d'*64
            else:wrong['pose_source'][change]='different'
            with self.assertRaises(ValueError):self.checked(plan,[wrong])
        bad=copy.deepcopy(plan);bad['looks'][0]['pose_id']='tt-turn-back-still'
        with self.assertRaises(ValueError):self.checked(bad,[ref])
        bad=copy.deepcopy(plan);bad['looks'][0]['pose_selection']['mode']='text'
        with self.assertRaisesRegex(ValueError,'silently'):self.checked(bad,[ref])

    def test_missing_back_does_not_become_supported_by_pose_image(self):
        with self.assertRaisesRegex(ValueError,'garment views'):
            library.apply(sample_plan(1,back=False),'garment-shot-1','tt-turn-back-still','back')

    def test_partial_change_and_subset_keep_other_shots(self):
        before=sample_plan(6)
        for i,s in enumerate(before['looks']):s['scene']=['wall','open floor','table'][i%3]
        after,ref=library.apply(before,'garment-shot-3','tt-stand-neutral','front')
        for i in (0,1,3,4,5):self.assertEqual(before['looks'][i],after['looks'][i])
        self.checked(after)
        subset=shot.subset(after,3)
        self.assertEqual(subset['looks'],after['looks'])
        self.assertEqual(shot.shot_at(subset,1)['pose_selection'],after['looks'][2]['pose_selection'])

    def test_new_library_and_style_story_can_coexist_without_five_old_ids(self):
        plan,_=self.choose()
        shot.check_poses(plan,[dict(id='tea-pour',views=['front'])])
        plan['looks'][0].pop('pose_selection');plan['looks'][0]['pose_id']='tea-pour'
        self.assertIsNone(shot.check_poses(plan,[dict(id='tea-pour',views=['front'])]))
        plan['variety_checks']=1;plan['looks'][0]['pose_id']='tt-stand-neutral'
        with self.assertRaisesRegex(ValueError,'style pose ids'):
            shot.check_poses(plan,[dict(id='tea-pour',views=['front'])])

    def test_definition_and_unexplained_body_changes_are_rejected(self):
        plan,_=self.choose();bad=copy.deepcopy(plan)
        bad['looks'][0]['pose_selection']['definition']['hands']='Both hands hold a bag.'
        with self.assertRaisesRegex(ValueError,'definition changed'):self.checked(bad)
        plan['looks'][0]['hands']='Right hand low; left hand clear of the side pocket.'
        with self.assertRaisesRegex(ValueError,'adaptation'):self.checked(plan)
        plan['looks'][0]['pose_selection']['adaptation_note']='Keep the product side pocket clear.'
        self.checked(plan)

    def test_scope_keeps_children_and_unreviewed_real_faces_out(self):
        plan,_=self.choose()
        for model,form in [(dict(subject='child model',source_type='new'),'human'),
                           (dict(subject='adult model',source_type='real'),'human')]:
            with self.assertRaises(ValueError):library.validate_scope(plan,model,form)
        library.validate_scope(plan,dict(subject='adult model',source_type='ai'),'human')
        library.validate_scope(plan,dict(subject='adult female model',source_type='ai'),'human')
        library.validate_scope(plan,dict(subject='adult model',source_type='real'),'faceless')
        library.validate_scope(sample_plan(1),dict(subject='child model',source_type='new'),'human')

    def test_classic_and_unselected_old_plan_are_unchanged(self):
        old=sample_plan(1);frozen=copy.deepcopy(old);render=shot.render(old)
        self.checked(old)
        self.assertEqual(old,frozen);self.assertEqual(shot.render(old),render)
        classic=shot.default_plan('old',old['coverage'])
        with self.assertRaisesRegex(ValueError,'classic'):
            library.apply(classic,'garment-shot-1','tt-stand-neutral','front')


class ExpandedPoseRequestTests(unittest.TestCase):
    def setUp(self):
        self.fixture=ledger_fixtures.NineTaskTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.task=ledger_fixtures.task
        spec=importlib.util.spec_from_file_location('expanded_pose_visual',ROOT/'skills/threadtruth-studio/scripts/visual_library.py')
        self.visual=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.visual)

    def prepare(self,pose,view,mode='text',model=None):
        fixture=self.fixture
        plan=sample_plan(1,back=False)
        garment_sha=self.task.digest(fixture.front)
        plan['coverage'][0]['sha256']=garment_sha
        plan['looks'][0].update(garment_views=['front','front-side'],reference_sha256s=[garment_sha])
        plan,ref=library.apply(plan,'garment-shot-1',pose,view,mode=mode,origin='user')
        refs=[dict(path=fixture.front,role='garment-source'),dict(path=fixture.face,role='identity-reference')]
        if ref:refs.append(ref)
        inventory=[dict(sha256=self.task.digest(r['path']),role=r['role'],
                        **({'pose_source':r['pose_source']} if 'pose_source' in r else {})) for r in refs]
        model=model or fixture.model
        visual=self.visual.prepare(dict(entry_id='nordic-minimal',inventory=inventory,model=model,shot_plan=plan,
            garment=dict(description='Synthetic garment fixture.',keep=['Preserve the source garment.'],source_sha256s=[garment_sha])))
        return plan,refs,visual

    def export(self,pose,view,mode='text'):
        plan,refs,visual=self.prepare(pose,view,mode)
        job=self.fixture.root/(pose+'-'+view+'-'+mode)
        self.task.create(job,refs,None,[60,40],model=self.fixture.model,context=self.fixture.context,
                         route='codex_native',shot_plan=plan,visual_plan=visual, workflow_version=0)
        data=self.task.read(job)
        self.task.export(job)
        folder=next((job/'handoff').glob('look-1-*'))
        prompt=(folder/'prompt.txt').read_text()
        manifest=json.loads((folder/'manifest.json').read_text())
        selected=plan['looks'][0]['pose_selection']
        self.assertEqual(manifest['shot_plan']['looks'][0]['pose_selection'],selected)
        for key in ('body_action','hands','support'):
            self.assertIn(selected['definition'][key],prompt)
        self.assertEqual(manifest['reference_hashes'],[self.task.digest(r['path']) for r in refs])
        self.assertEqual(data['attempts'],0)
        self.assertEqual(shot.pose_selected(plan,1,preview=True),set())
        return prompt,manifest

    def test_new_families_reach_frozen_requests_in_both_modes(self):
        for pose,view in [('tt-floor-side-fold','diag'),('tt-kneel-half','side'),
                          ('tt-squat-grounded','front'),('tt-lie-side-long','side')]:
            for mode in ('text','image'):
                with self.subTest(pose=pose,mode=mode):
                    self.export(pose,view,mode)

    def test_restricted_text_freezes_its_limit_without_attaching_the_drawing(self):
        prompt,manifest=self.export('tt-close-sleeve-push','diag')
        selected=manifest['shot_plan']['looks'][0]['pose_selection']
        self.assertEqual(selected['definition']['selection_policy'],'user-only')
        self.assertIn('does not provide an unobscured waist or abdomen',prompt)
        self.assertEqual(len(manifest['reference_hashes']),2)
        prompt,manifest=self.export('tt-close-sleeve-push','diag','image')
        self.assertIn('does not provide an unobscured waist or abdomen',prompt)
        self.assertEqual(len(manifest['reference_hashes']),3)

    def test_old_selection_still_exports_both_modes(self):
        for mode in ('text','image'):
            with self.subTest(mode=mode):self.export('tt-stand-neutral','front',mode)

    def test_expanded_selection_rejects_inapplicable_models_in_actual_prepare(self):
        for model in [dict(self.fixture.model,subject='child model',source_type='new'),
                      dict(self.fixture.model,subject='adult male model'),
                      dict(self.fixture.model,source_type='real')]:
            with self.subTest(model=model),self.assertRaises(ValueError):
                self.prepare('tt-floor-side-fold','diag',model=model)


if __name__=='__main__':unittest.main()
