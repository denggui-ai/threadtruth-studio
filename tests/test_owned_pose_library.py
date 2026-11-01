"""Owned selection must survive actual plan validation without changing old plans."""
import copy
import importlib.util
import unittest
from pathlib import Path
from test_pose_plan_v2 import sample_plan, inventory, shot, FRONT, BACK

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
        rows = library.candidates()
        self.assertEqual((len(rows),len({r['group_id'] for r in rows})),(16,14))
        for r in rows:
            selected, ref = library.selection(r['group_id'],r['view'])
            self.assertEqual(ref['sha256'], selected['definition']['sha256'])
        self.assertTrue(all(set(r['garment_views']) <= {'front'} for r in library.candidates(garment_views=['front'])))

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


if __name__=='__main__':unittest.main()
