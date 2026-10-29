"""Versioned photography/face bindings; declared synthetic facts, no generation."""
import copy
import importlib.util
from pathlib import Path
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/threadtruth-studio/scripts'


def module(name):
    spec = importlib.util.spec_from_file_location('pose_v2_' + name, SCRIPTS / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


visual = module('visual_plan')
library = module('visual_library')
face = module('real_face_plan')


class VisualPoseV2Tests(unittest.TestCase):
    def setUp(self):
        self.inventory = [dict(role='garment-source', sha256='a' * 64)]
        self.spec = dict(entry_id='nordic-minimal', inventory=self.inventory,
                         garment=dict(description='A source-backed printed cotton top.',
                                      keep=['Keep the front print unobscured.'], source_sha256s=['a' * 64]))
        self.shot = dict(version=2, looks=[dict(slot=i, shot_id='sku-shot-' + str(i)) for i in range(1, 10)],
                         selected_shot_ids=['sku-shot-' + str(i) for i in range(1, 10)])
        self.context = dict(style='nordic-minimal', output_form='human', first_pose=1)

    def plan(self):
        return library.prepare(dict(self.spec, shot_plan=self.shot))

    def test_new_portrait_default_nine_has_explicit_stable_visual_binding(self):
        p = self.plan()
        self.assertEqual(p['version'], 2)
        self.assertEqual([(s['slot'], s['shot_id']) for s in p['shots']],
                         [(i, 'sku-shot-' + str(i)) for i in range(1, 10)])
        self.assertIn('sku-shot-9', visual.render(p, 9))
        visual.validate(p, self.inventory, context=self.context, count=9, shot_plan=self.shot)

    def test_selected_seventh_shot_keeps_source_slot_and_photography(self):
        p = self.plan()
        p['shots'][6]['composition'] = 'Seventh image has asymmetric breathing space.'
        selected = visual.subset(p, 7)
        shot = copy.deepcopy(self.shot)
        shot['selected_shot_ids'] = ['sku-shot-7']
        visual.validate(selected, self.inventory, context=dict(self.context, first_pose=7), count=1,
                        shot_plan=shot)
        self.assertEqual(selected['shots'], [p['shots'][6]])
        self.assertEqual(visual.bind_shots(p, shot), selected)
        self.assertIn('Visual slot 7', visual.render(selected, 1))
        self.assertNotIn('sku-shot-1', visual.render(selected, 1))
        self.assertEqual(visual.subset(p, 'sku-shot-7'), selected)

    def test_photography_cannot_bind_a_different_pose_or_duplicate_id(self):
        for mutate in (lambda p: p['shots'][6].update(shot_id='another-shot'),
                       lambda p: p['shots'][6].update(shot_id='sku-shot-1'),
                       lambda p: p['shots'][6].update(slot=2)):
            p = self.plan()
            mutate(p)
            with self.assertRaises(ValueError):
                visual.validate(p, self.inventory, context=self.context, count=9, shot_plan=self.shot)
        selected = visual.subset(self.plan(), 7)
        with self.assertRaises(ValueError):
            visual.validate(selected, self.inventory, context=self.context, count=1)
        with self.assertRaises(ValueError):
            visual.bind_shots(selected, self.shot)

    def test_visual_fields_cannot_smuggle_new_managed_shots_or_body_authority(self):
        for text in ('Shot 7: STANDING', 'POSE 9: WALK', 'Body action: deep forward bend',
                     'head direction left', 'full-body framing'):
            p = self.plan()
            p['shots'][0]['composition'] = text
            with self.subTest(text=text), self.assertRaises(ValueError):
                visual.validate(p, self.inventory, context=self.context, count=9)

    def test_explicit_legacy_counts_and_nonportrait_default_stay_v1(self):
        for count in (1, 6):
            p = library.prepare(dict(self.spec, count=count))
            self.assertEqual(p['version'], 1)
            self.assertEqual([s['pose'] for s in p['shots']], list(range(1, count + 1)))
        p = library.prepare(dict(self.spec, output_form='flat-lay'))
        self.assertEqual(p['version'], 1)
        self.assertEqual(len(p['shots']), 1)

    def test_selected_plan_count_cannot_be_overridden_or_remapped(self):
        shot = copy.deepcopy(self.shot)
        shot['selected_shot_ids'] = ['sku-shot-7']
        p = library.prepare(dict(self.spec, shot_plan=shot))
        self.assertEqual(p['shots'][0]['slot'], 7)
        for extra in (dict(count=9), dict(first_pose=1)):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                library.prepare(dict(self.spec, shot_plan=shot, **extra))

    def face_plan(self, count=9):
        return dict(primary_identity_sha256='b' * 64,
                    coverage=[dict(sha256='b' * 64, views=['front'], note='Original near-frontal adult.')],
                    looks=[dict(body_action='Supported body action ' + str(i), head_view='front',
                                gaze='near camera', face_visible=True,
                                reference_sha256s=['a' * 64, 'b' * 64, 'c' * 64],
                                selection_note='Original product and person, optional pose input.') for i in range(count)])

    def validate_face(self, plan, **kwargs):
        refs = self.inventory + [dict(role='identity-reference', sha256='b' * 64),
                                 dict(role='pose-reference', sha256='c' * 64)]
        args = dict(schema_version=2, identity=True, model=dict(source_type='real'),
                    context=dict(purpose='preview-grid'), count=len(plan['looks']), route='codex_native',
                    strict_looks=range(1, len(plan['looks']) + 1))
        args.update(kwargs)
        return face.validate(plan, refs, **args)

    def test_nine_real_face_rows_still_require_original_face_angles(self):
        p = self.face_plan()
        self.validate_face(p, shot_plan=self.shot)
        p['looks'][6]['head_view'] = 'left-profile'
        with self.assertRaisesRegex(ValueError, 'original view'):
            self.validate_face(p, shot_plan=self.shot)
        p = self.face_plan()
        p['coverage'].append(dict(sha256='c' * 64, views=['left-profile'], note='A pose drawing.'))
        with self.assertRaisesRegex(ValueError, 'identity references'):
            self.validate_face(p, shot_plan=self.shot)

    def test_real_face_binding_requires_same_active_count(self):
        shot = copy.deepcopy(self.shot)
        shot['selected_shot_ids'] = ['sku-shot-7']
        with self.assertRaises(ValueError):
            self.validate_face(self.face_plan(), shot_plan=shot)

    def test_v2_face_capacity_uses_actual_resolver_not_unused_pose_candidates(self):
        task = module('web-task')
        inventory = self.inventory + [dict(role='identity-reference', sha256='b' * 64)]
        inventory += [dict(role='pose-reference', sha256=h * 64) for h in ('c', 'd', 'e', 'f', '0')]
        inventory += [dict(role='aesthetic-reference', sha256='1' * 64)]
        p = self.face_plan(1)
        p['looks'][0]['reference_sha256s'] = [r['sha256'] for r in inventory]
        args = dict(schema_version=2, identity=True, model=dict(source_type='real'),
                    context=dict(purpose='delivery'), count=1, route='codex_native')
        # V1's explicit list is its actual list, so its original cap remains.
        with self.assertRaisesRegex(ValueError, 'five attachments'):
            face.validate(p, inventory, **args)
        shot = copy.deepcopy(self.shot)
        shot['selected_shot_ids'] = ['sku-shot-7']
        for row in shot['looks']:
            row.update(reference_sha256s=['a' * 64], pose_reference=dict(sha256='c' * 64, reason='Reviewed action.'))
        face.validate(p, inventory, shot_plan=shot, **args)
        rows = task.selected_references(inventory, args['context'], shot, p, 1)
        self.assertEqual([r['sha256'] for r in rows], [h * 64 for h in ('a', 'b', 'c')])
        task.preflight_references(inventory, args['context'], shot, p, 1, True, 'codex_native')
        # Capacity is still enforced against actual retained original identities.
        for h in ('2', '3', '4'):
            inventory.append(dict(role='identity-reference', sha256=h * 64))
            p['looks'][0]['reference_sha256s'].append(h * 64)
        face.validate(p, inventory, shot_plan=shot, **args)
        with self.assertRaisesRegex(ValueError, 'five references'):
            task.preflight_references(inventory, args['context'], shot, p, 1, True, 'codex_native')

    def test_nine_face_preview_omits_pose_candidates_before_capacity_check(self):
        task = module('web-task')
        inventory = self.inventory + [dict(role='identity-reference', sha256='b' * 64)]
        inventory += [dict(role='pose-reference', sha256=h * 64) for h in ('c', 'd', 'e', 'f', '0')]
        p = self.face_plan()
        for row in p['looks']:
            row['reference_sha256s'] = [r['sha256'] for r in inventory]
        shot = copy.deepcopy(self.shot)
        for row in shot['looks']:
            row.update(reference_sha256s=['a' * 64], pose_reference=dict(sha256='c' * 64, reason='Reviewed action.'))
        context = dict(purpose='preview-grid')
        face.validate(p, inventory, schema_version=2, identity=True, model=dict(source_type='real'),
                      context=context, count=9, route='codex_native', shot_plan=shot)
        rows = task.selected_references(inventory, context, shot, p, 1)
        self.assertEqual([r['sha256'] for r in rows], [h * 64 for h in ('a', 'b')])
        task.preflight_references(inventory, context, shot, p, 1, True, 'codex_native')


if __name__ == '__main__':
    unittest.main()
