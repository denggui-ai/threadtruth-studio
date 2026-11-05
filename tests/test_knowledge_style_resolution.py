"""Selected knowledge and revised style rules reach frozen requests; no image calls."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from PIL import Image
from tests.test_pose_plan_v2 import sample_plan
from tests.test_style_pose_pool import bind_pool_actions


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/lookset'


def module(name):
    spec = importlib.util.spec_from_file_location('knowledge_' + name, SKILL / 'scripts' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


library = module('visual_library')
task = module('web-task')


class KnowledgeStyleResolutionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / 'synthetic-source.png'
        Image.new('RGB', (20, 30), 'blue').save(self.source)
        self.digest = task.digest(self.source)
        self.model = dict(source_type='new', scope='full', subject='adult female model',
                          locked=[], adjustable=[], consent_note='', styling_lock='identity')

    def spec(self, entry='korean-cold-editorial', **changes):
        result = dict(entry_id=entry, count=1, first_pose=1, model=copy.deepcopy(self.model),
                      output_form='human', inventory=[dict(role='garment-source', sha256=self.digest)],
                      garment=dict(description='Synthetic blue garment.', keep=['Keep the original blue colour.'],
                                   source_sha256s=[self.digest]))
        result.update(changes)
        return result

    def warm_spec(self, **changes):
        card = library.card('korean-cold-editorial')
        commitments = copy.deepcopy(card['commitments'])
        colour = next(row for row in commitments if row['id'] == 'kc-cool-white-balance')
        colour.update(show='Layered brown and caramel environment with neutral white balance; garment colours stay unchanged.',
                      check='The environment is brown with distinct light and dark layers; the source garment remains blue.')
        return self.spec(overrides=dict(photography=dict(
            palette='Environment dominated by brown and caramel, no yellow wash; keep original garment colours.'),
            commitments=commitments), asset_trace=[dict(asset='T02', decision='translated',
                affects='photography.palette and commitments.kc-cool-white-balance', check=colour['check'])], **changes)

    def with_shot(self, spec):
        plan = sample_plan(count=1, back=False)
        plan['coverage'][0]['sha256'] = self.digest
        plan['looks'][0].update(reference_sha256s=[self.digest],
                                display_goal='Show the source-supported front closure and visible layers.',
                                must_show=['front closure', 'visible layers'])
        spec['shot_plan'] = plan
        return bind_pool_actions(spec)

    def export_both(self, spec):
        """Exercise actual prepare/create/read/native and web export, without authorize/reserve."""
        plan = library.prepare(spec)
        texts = []
        for route in ('codex_native', 'chatgpt_web'):
            job = self.root / (spec['entry_id'] + '-' + route)
            context = dict(outfit='synthetic-knowledge-sku', style=spec['entry_id'], mode='C',
                           output_form=spec['output_form'], size=[20, 30], first_pose=1, purpose='delivery')
            prepared_input = copy.deepcopy(plan)
            task.create(job, [self.source], None, [20, 30], model=spec['model'], context=context,
                        route=route, shot_plan=spec['shot_plan'], visual_plan=prepared_input, count=1, workflow_version=0)
            task.export(job)
            data = task.read(job)
            folder = task.handoff_directory(job, data, data['looks'][0])
            raw = (folder / 'prompt.txt').read_bytes()
            manifest = json.loads((folder / 'manifest.json').read_text())
            self.assertEqual(manifest['visual_plan'], plan)
            self.assertEqual(manifest['reference_hashes'], [self.digest])
            if route == 'codex_native':
                request = json.loads((folder / 'request.json').read_text())
                self.assertEqual(request['prompt'].encode(), raw)
                self.assertEqual([task.digest(Path(p)) for p in request['referenced_image_paths']], [self.digest])
            else:
                packet = task.export_web_execution(job, 1)
                envelope = task.web_execution_helper()
                self.assertEqual(Path(packet['submission_file']).read_bytes(),
                                 envelope.prefix(envelope.version(data)) + raw + envelope.SUFFIX)
            self.assertEqual(data['attempts'], 0)
            self.assertIsNone(data['authorization'])
            texts.append(raw.decode())
            # Draft edits after freezing cannot alter the task or its request.
            prepared_input['photography']['palette'] = 'Unaccepted later draft'
            task.export(job)
            self.assertEqual((folder / 'prompt.txt').read_bytes(), raw)
        self.assertEqual(texts[0], texts[1])
        return plan, texts[0]

    def test_modifier_replaces_conflicting_commitment_in_both_actual_exports(self):
        card = library.card('korean-cold-editorial')
        old = next(row for row in card['commitments'] if row['id'] == 'kc-cool-white-balance')
        spec = self.with_shot(self.warm_spec())
        before = copy.deepcopy(spec)
        plan, text = self.export_both(spec)
        self.assertIn('Layered brown and caramel environment', text)
        self.assertIn('Keep the original blue colour.', text)
        self.assertNotIn(old['show'], text)
        self.assertNotIn(old['check'], text)
        self.assertNotIn('T02', text)
        self.assertEqual(plan['style']['primary']['snapshot'], card)
        self.assertEqual(library.card(card['id']), card)
        self.assertEqual(spec, before)
        for row in card['commitments']:
            if row['id'] != old['id']:
                self.assertIn(row, plan['commitments'])

    def test_explicit_replacement_is_not_an_append_and_omissions_are_recorded(self):
        baseline = library.prepare(self.spec())
        plan = library.prepare(self.spec(overrides=dict(commitments=[])))
        self.assertEqual(plan['commitments'], [])
        self.assertEqual(plan['commitments_skipped'],
                         [dict(id=row['id'], reason='explicit-override') for row in baseline['commitments']])
        self.assertNotIn('Commitment: ', library._visual().render(plan))
        self.assertIn('Commitment: ', library._visual().render(baseline))

    def test_replacement_still_obeys_model_locks_and_output_form(self):
        rows = [dict(id='chosen-' + axis, show='Selected ' + axis + ' treatment.', needs=[axis],
                     check='Review the chosen ' + axis + ' treatment.')
                for axis in ('lighting', 'expression', 'makeup', 'body')]
        for form, retained in [('human', ['lighting', 'body']), ('faceless', ['lighting', 'body']),
                               ('flat-lay', ['lighting']), ('hanger', ['lighting']), ('mannequin', ['lighting'])]:
            with self.subTest(form=form):
                model = dict(self.model, locked=['gentle smile'], styling_lock='full')
                plan = library.prepare(self.spec(output_form=form, model=model, overrides=dict(commitments=rows)))
                self.assertEqual([row['id'] for row in plan['commitments']], ['chosen-' + axis for axis in retained])
                self.assertNotIn('Selected expression treatment.', library._visual().render(plan))
                self.assertNotIn('Selected makeup treatment.', library._visual().render(plan))

    def test_malformed_replacements_are_rejected_before_filtering(self):
        row = dict(id='chosen-light', show='One soft key light.', needs=['lighting'], check='One lit side.')
        bad_values = [None, {}, [dict(row, needs=['gaze'])], [row, row],
                      [dict(row, show='')], [dict(row, unknown='field')],
                      [dict(row, needs=['makeup'], show='head direction changes')]]
        for value in bad_values:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'overrides.commitments'):
                library.prepare(self.spec(output_form='flat-lay', overrides=dict(commitments=value)))

    def test_culture_constraints_use_executable_fields_and_trace_stays_metadata(self):
        for entry, asset in [('qipao-urban', 'C11'), ('gongbu-dress', 'C19')]:
            with self.subTest(entry=entry):
                spec = self.with_shot(self.spec(entry))
                fact = 'Preserve the visible front closure and outer/inner layer relationship from the source.'
                limit = 'Do not add festival ornaments or garment components borrowed from other regions.'
                spec['garment']['keep'].append(fact)
                spec['culture_profile'] = dict(id=entry + '-current-form', version=1,
                                               form='Scope-only provenance, not an execution instruction.')
                spec['asset_trace'] = [dict(asset=asset, decision='translated',
                    affects='garment.keep, art.limits and shot_plan.looks[0].must_show',
                    check='Trace-only review: compare the closure, layers and supplied accessories.')]
                spec['overrides'] = dict(art=dict(limits=library.card(entry)['art']['limits'] + [limit]))
                plan, text = self.export_both(spec)
                self.assertIn(fact, text)
                self.assertIn(limit, text)
                self.assertIn('front closure', text)
                self.assertIn('visible layers', text)
                self.assertNotIn('Scope-only provenance', text)
                self.assertNotIn('Trace-only review', text)
                self.assertNotIn(asset, text)
                self.assertEqual(plan['asset_trace'], spec['asset_trace'])

    def test_supporting_style_only_changes_the_explicitly_resolved_fields(self):
        spec = self.with_shot(self.spec('gothic-editorial'))
        spec.update(supporting=['art-deco-set'], fusion_note='Only the set uses Art Deco geometry; retain the primary light.')
        spec['overrides'] = dict(photography=dict(scene='Stepped geometric panels with brushed metal edges in a stone lobby.'))
        plan = library.prepare(spec)
        text = library._visual().render(plan)
        self.assertIn(spec['overrides']['photography']['scene'], text)
        self.assertEqual(plan['photography']['lighting'], library.card('gothic-editorial')['photography']['lighting'])
        self.assertEqual(plan['style']['supporting'][0]['snapshot'], library.card('art-deco-set'))
        self.assertEqual(plan['commitments'], library.card('gothic-editorial')['commitments'])

    def test_subset_inherits_resolved_rules_without_reloading_card_defaults(self):
        spec = self.warm_spec(count=6)
        shots = sample_plan(count=6, back=False)
        shots['coverage'][0]['sha256'] = self.digest
        for look in shots['looks']:
            look['reference_sha256s'] = [self.digest]
        plan = library.prepare(dict(spec, shot_plan=shots))
        before = copy.deepcopy(plan)
        single = library._visual().subset(plan, 4)
        self.assertEqual(single['shots'], [plan['shots'][3]])
        self.assertEqual(single['commitments'], plan['commitments'])
        self.assertEqual(single['asset_trace'], plan['asset_trace'])
        self.assertIn('Layered brown and caramel environment', library._visual().render(single, 1))
        self.assertEqual(plan, before)

    def test_default_preparation_keeps_resolved_knowledge_apart_from_new_model_source_policy(self):
        relative = 'skills/threadtruth-studio/scripts/visual_library.py'
        source = subprocess.check_output(['git', 'show', '7f78875:' + relative], cwd=ROOT, text=True)
        namespace = dict(__file__=str(ROOT / relative), __name__='handoff_library')
        exec(compile(source, str(ROOT / relative), 'exec'), namespace)
        # Isolate the commitment change from later card-storage migrations.
        # Pre-migration frozen request bytes are covered by test_style_pose_pool.
        namespace['card'] = library.card
        for entry, form in [('korean-cold-editorial', 'human'), ('korean-cold-editorial', 'faceless'),
                            ('gongbu-dress', 'flat-lay')]:
            with self.subTest(entry=entry, form=form):
                spec = self.spec(entry, output_form=form)
                before = namespace['prepare'](spec)
                after = library.prepare(spec)
                # F6 adds an explicit source policy to newly prepared portraits.
                # Keep this test about unchanged knowledge/commitment resolution;
                # the new tail and frozen old bytes are tested in test_aesthetic_*.
                source_policy = after.pop('model_source_type', None)
                self.assertEqual(source_policy, spec['model']['source_type'] if form in ('human', 'faceless') else None)
                self.assertEqual(after, before)
                self.assertEqual(library._visual().render(after), namespace['_visual']().render(before))


if __name__ == '__main__':
    unittest.main()
