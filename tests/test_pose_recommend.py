"""Goal/history ranking on real library metadata and synthetic existing task ledgers."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from tests import test_pose_history as fixtures

history, visual, task = fixtures.history, fixtures.library, fixtures.task
poses = fixtures.module('pose_library')


class PoseRecommendationTests(unittest.TestCase):
    setUp = fixtures.PoseHistoryTests.setUp
    image = fixtures.PoseHistoryTests.image
    spec = fixtures.PoseHistoryTests.spec
    create = fixtures.PoseHistoryTests.create
    returned = fixtures.PoseHistoryTests.returned
    prior = fixtures.PoseHistoryTests.prior

    def preparation(self, entry='nordic-minimal', goal='Visible garment panels.'):
        spec = self.spec(entry)
        spec['shot_plan']['looks'][0].update(display_goal=goal, must_show=[goal], framing='half-body',
                                           garment_views=['front', 'front-side', 'detail'])
        return spec

    def rank(self, spec, **kwargs):
        return poses.recommend(spec, 'garment-shot-1', limit=60, **kwargs)

    def candidate(self, report, pose_id):
        return next(row for row in report['candidates'] if row['pose_id'] == pose_id
                    or any(alt['pose_id'] == pose_id for alt in row['alternatives']))

    def test_must_show_vetoes_obstruction_without_turning_cautions_into_scores(self):
        spec = self.preparation(goal='领口清楚完整展示。')
        before = copy.deepcopy(spec)
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('Ranking must not read images')):
            collar = self.rank(spec)
        self.assertEqual(spec, before)
        self.assertEqual(collar['goal_terms'], ['collar'])
        self.assertNotIn('tt-close-collar-touch', {r['pose_id'] for r in collar['candidates']})
        self.assertGreater(collar['excluded']['must-show-occlusion'], 0)
        self.assertEqual(collar['ordering'][:2], ['current_style_first', 'body_relation_penalty'])
        # Emotion words mentioning a garment part do not create a must-show veto.
        spec['shot_plan']['looks'][0]['must_show'] = ['visible panels']
        emotional = self.rank(spec)
        self.assertIn('领口', self.candidate(emotional, 'tt-close-collar-touch')['review']['avoid_when'])
        spec['shot_plan']['looks'][0].update(display_goal='Show the garment hem and length.',
                                           must_show=['hem', 'garment length'])
        hem = self.rank(spec)
        self.assertNotEqual([r['pose_id'] for r in hem['candidates']], [r['pose_id'] for r in collar['candidates']])
        self.assertTrue(any(r['ranking_factors']['goal_clues'] for r in hem['candidates']))
        raised = self.candidate(hem, 'tt-stand-high-reach')
        self.assertTrue(raised['ranking_factors']['target_cautions'])
        self.assertIn('occludes', {f for c in raised['ranking_factors']['target_cautions'] for f in c['fields']})

    def test_empty_must_show_drops_occlusion_veto_and_keeps_display_goal_report_only(self):
        spec = self.preparation(goal='领口清楚完整展示。')
        vetoed = self.rank(spec)
        spec['shot_plan']['looks'][0]['must_show'] = []
        worn = self.rank(spec)
        self.assertNotIn('must-show-occlusion', worn['excluded'])
        self.assertIn('tt-close-collar-touch', {r['pose_id'] for r in worn['candidates']}
                      | {a['pose_id'] for r in worn['candidates'] for a in r['alternatives']})
        self.assertEqual(worn['goal_terms'], vetoed['goal_terms'])
        self.assertGreater(worn['eligible_actions'], vetoed['eligible_actions'])
        spec['shot_plan']['looks'][0].update(must_show=[], framing='detail')
        with self.assertRaisesRegex(ValueError, 'must_show'):
            self.rank(spec)

    def test_style_first_and_group_body_relations_precede_framing_and_history(self):
        spec = self.preparation('french-effortless')
        baseline = self.rank(spec)
        kinds = [row['kind'] for row in baseline['candidates']]
        self.assertEqual(kinds, sorted(kinds, key=lambda kind: kind != 'style'))
        chosen = baseline['candidates'][0]
        other = copy.deepcopy(spec['shot_plan']['looks'][0])
        other.update(shot_id='already-selected', slot=2,
                     **{key: chosen[key] for key in ('pose_id', 'body_action', 'hands', 'support')})
        spec['shot_plan']['looks'].append(other)
        ranked = self.rank(spec)
        repeated = self.candidate(ranked, chosen['pose_id'])
        self.assertEqual(repeated['ranking_factors']['body_variety']['penalty'], 2)
        distinct = [row for row in ranked['candidates'] if row['kind'] == 'style'
                    and row['ranking_factors']['body_variety']['penalty'] == 0]
        self.assertTrue(distinct)
        self.assertLess(distinct[0]['rank'], repeated['rank'])
        before = copy.deepcopy(repeated['ranking_factors']['body_variety'])
        other.update(head='Head turned left.', gaze='Look down.', hands='Hands touch the hair.',
                     scene='A different outdoor location.')
        after = self.candidate(self.rank(spec), chosen['pose_id'])['ranking_factors']['body_variety']
        self.assertEqual(before, after)

    def test_target_source_views_and_restricted_policy_are_hard_filters(self):
        spec = self.preparation()
        spec['shot_plan']['looks'][0]['garment_views'] = ['front']
        report = self.rank(spec)
        for row in report['candidates']:
            for candidate in [row, *row['alternatives']]:
                self.assertLessEqual(set(candidate['garment_views']), {'front', 'front-side'})
                self.assertNotEqual(candidate['pose_id'], 'tt-close-sleeve-push')
        self.assertEqual(report['excluded']['user-only'], 1)
        self.assertGreater(report['excluded']['needs-back'], 0)
        shallow = self.candidate(report, 'tt-turn-front-counter')
        self.assertIn('view_adaptation', shallow['review'])
        self.assertNotIn('tt-turn-back-still', {row['pose_id'] for row in report['candidates']})
        # Conditional skirt pressure stays reviewable, including front-facing kneeling.
        spec['shot_plan']['looks'][0]['must_show'] = ['hem']
        kneel = self.candidate(self.rank(spec), 'tt-kneel-tall')
        self.assertIn('膝下', kneel['review']['avoid_when'])
        spec['shot_plan']['looks'][0]['garment_views'] = ['front-side']
        spec['shot_plan']['coverage'][0]['views'] = ['front']
        with self.assertRaisesRegex(ValueError, 'own reference_sha256s'):
            self.rank(spec)
        # Another source's back evidence must not expand this shot's selected references.
        spec['inventory'].append(dict(sha256='b' * 64, role='garment-source'))
        spec['shot_plan']['coverage'].append(dict(sha256='b' * 64, views=['back'], usable=True,
                                                same_sku=True, note='Synthetic separate back evidence.'))
        spec['shot_plan']['looks'][0]['garment_views'] = ['back']
        with self.assertRaisesRegex(ValueError, 'own reference_sha256s'):
            self.rank(spec)
        spec['shot_plan']['looks'][0]['garment_views'] = ['front']
        spec['shot_plan']['coverage'][0]['usable'] = False
        with self.assertRaisesRegex(ValueError, 'usable same_sku'):
            self.rank(spec)

    def test_subject_scope_and_empty_candidates_never_relax_filters(self):
        male = self.preparation('korean-menswear')
        male['model']['subject'] = 'adult male model'
        report = self.rank(male)
        self.assertTrue(report['candidates'])
        self.assertEqual({r['kind'] for r in report['candidates']}, {'style'})
        self.assertGreater(report['excluded']['owned-subject-scope'], 0)
        for subject, source, form in [('child model', 'new', 'human'),
                                      ('adult female model', 'real', 'human'),
                                      ('adult female model', 'new', 'mannequin')]:
            with self.subTest(subject=subject, source=source, form=form):
                spec = self.preparation()
                spec['model'].update(subject=subject, source_type=source,
                                     consent_note='Synthetic consent fixture; no likeness image.')
                spec['output_form'] = form
                result = self.rank(spec)
                self.assertEqual(result['status'], 'unsupported-scope')
                self.assertEqual(result['candidates'], [])
        spec = self.preparation()
        spec['shot_plan']['looks'][0]['garment_views'] = ['detail']
        self.assertEqual(self.rank(spec)['status'], 'no-eligible-candidates')
        spec['shot_plan']['looks'][0]['garment_views'] = ['front']
        spec['output_form'] = 'faceless'
        spec['model'].update(source_type='real', consent_note='Synthetic consent fixture; no likeness image.')
        self.assertTrue(self.rank(spec)['candidates'])

    def test_exact_history_demotes_reuse_but_never_overrides_product_cautions(self):
        prior = self.prior()
        before = (prior / 'task.json').read_bytes()
        spec = self.preparation()
        baseline = self.rank(spec)
        spec['pose_history_tasks'] = [str(prior)]
        ranked = self.rank(spec)
        repeated = self.candidate(ranked, 'tt-stand-neutral')
        fresh = next(row for row in ranked['candidates'] if row['kind'] == repeated['kind']
                     and row['history']['tier'] < repeated['history']['tier']
                     and row['ranking_factors']['framing_penalty'] == repeated['ranking_factors']['framing_penalty'])
        self.assertGreater(repeated['rank'], self.candidate(baseline, 'tt-stand-neutral')['rank'])
        self.assertLess(fresh['rank'], repeated['rank'])
        self.assertEqual(repeated['history']['status'], 'exact-repeat')
        self.assertTrue(repeated['history']['requires_reuse_reason'])
        self.assertEqual(repeated['history']['matches'][0]['state'], 'rejected')
        self.assertEqual((prior / 'task.json').read_bytes(), before)
        spec['shot_plan']['looks'][0].update(display_goal='Show the collar clearly.', must_show=['collar'])
        product_first = self.rank(spec)
        self.candidate(product_first, 'tt-stand-neutral')
        self.assertNotIn('tt-close-collar-touch', {r['pose_id'] for r in product_first['candidates']})

    def test_near_results_frozen_v1_and_missing_history_keep_distinct_statuses(self):
        prior = self.prior(self.spec('athleisure', pose_id='al-zip-close'))
        frozen = history.freeze([prior])
        spec = self.preparation('old-money')
        near = self.candidate(self.rank(spec, history=frozen), 'om-cuff-close')
        self.assertEqual(near['history']['status'], 'near-repeat')
        self.assertEqual(near['history']['matches'][0]['basis'], ['near-body-hands-support'])
        legacy = copy.deepcopy(frozen)
        legacy['version'] = 1
        for entry in legacy['entries']:
            entry.pop('action_features')
        legacy['sha256'] = history.digest({k: v for k, v in legacy.items() if k != 'sha256'})
        old = self.candidate(self.rank(spec, history=legacy), 'om-cuff-close')
        self.assertEqual(old['history']['status'], 'no-exact-match-near-unchecked')
        none = self.rank(spec)
        self.assertIsNone(none['history_scope'])
        self.assertTrue(all(r['history']['status'] == 'not-provided' for r in none['candidates']))
        self.assertTrue(none['unrecognized_must_show'])
        draft = self.create(self.spec(), 'draft')
        missing = self.rank(spec, history=history.freeze([draft]))
        self.assertTrue(all(r['history']['status'] == 'no-comparable-history' for r in missing['candidates']))
        uncovered_spec = self.spec()
        uncovered_spec['shot_plan']['looks'][0].pop('pose_id')
        uncovered_spec['shot_plan']['looks'][0]['body_action'] = '自然站立，双脚分开，肩部放松。'
        uncovered = history.freeze([self.prior(uncovered_spec, 'uncovered-language')])
        gap = self.candidate(self.rank(spec, history=uncovered), 'om-cuff-close')
        self.assertEqual(gap['history']['status'], 'no-match-with-near-gaps')
        self.assertEqual(gap['history']['tier'], 1)
        broken = copy.deepcopy(frozen)
        broken['entries'][0]['state'] = 'accepted'
        with self.assertRaisesRegex(ValueError, 'hash changed'):
            self.rank(spec, history=broken)
        spec['pose_history_tasks'] = [str(prior)]
        with self.assertRaisesRegex(ValueError, 'not both'):
            self.rank(spec, history=frozen)

    def test_stable_order_groups_same_geometry_and_cli_is_read_only(self):
        spec = self.preparation()
        normal = self.rank(spec)
        grouped = self.candidate(normal, 'tt-turn-front-counter')
        variants = [row for row in [grouped, *grouped['alternatives']] if row['pose_id'] == 'tt-turn-front-counter']
        self.assertEqual({row['view'] for row in variants}, {'front', 'diag'})
        neutral = self.candidate(normal, 'tt-stand-neutral')
        self.assertIn('nm-open-stand', {r['pose_id'] for r in [neutral, *neutral['alternatives']]})
        self.assertEqual(len(normal['candidates']), normal['eligible_actions'])
        catalog = json.loads(poses.CATALOG.read_text())
        catalog['entries'].reverse()
        reversed_path = self.root / 'reversed-catalog.json'
        reversed_path.write_text(json.dumps(catalog))
        self.assertEqual(self.rank(spec, catalog_path=reversed_path), normal)
        path = self.root / 'ranking-spec.json'
        path.write_text(json.dumps(spec))
        before = path.read_bytes()
        existing = {p.name for p in self.root.iterdir()}
        run = subprocess.run([sys.executable, str(fixtures.SKILL / 'scripts/pose_library.py'), 'recommend',
            '--spec', str(path), '--shot-id', 'garment-shot-1', '--limit', '5'], capture_output=True, text=True, check=True)
        result = json.loads(run.stdout)
        self.assertEqual(result['candidates'], normal['candidates'][:5])
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual({p.name for p in self.root.iterdir()}, existing)

    def test_ranked_owned_choice_reaches_existing_prepare_and_both_exports(self):
        prior = self.prior()
        spec = self.preparation(goal='Show the garment silhouette.')
        spec['pose_history_tasks'] = [str(prior)]
        before = copy.deepcopy(spec)
        report = self.rank(spec)
        chosen = next(row for row in report['candidates'] if row['kind'] == 'owned'
                      and not row['history']['requires_reuse_reason'] and not row['ranking_factors']['target_cautions'])
        self.assertEqual(spec, before)
        spec['shot_plan'], ref = poses.apply(spec['shot_plan'], 'garment-shot-1', chosen['pose_id'], chosen['view'], origin='auto')
        self.assertIsNone(ref)
        for key in ('body_action', 'hands', 'support'):
            self.assertEqual(spec['shot_plan']['looks'][0][key], chosen[key])
        prepared = visual.prepare(spec)
        prompts = []
        for route in ('codex_native', 'chatgpt_web'):
            job = self.create(spec, route, route=route, visual=prepared)
            task.export(job)
            data = task.read(job)
            folder = task.handoff_directory(job, data, data['looks'][0])
            prompt = (folder / 'prompt.txt').read_bytes()
            prompts.append(prompt)
            manifest = json.loads((folder / 'manifest.json').read_text())
            self.assertEqual(manifest['shot_plan']['looks'][0], spec['shot_plan']['looks'][0])
            self.assertEqual(manifest['visual_plan']['pose_history'], prepared['pose_history'])
            self.assertEqual(data['attempts'], 0)
            self.assertIsNone(data['authorization'])
            for key in ('body_action', 'hands', 'support'):
                self.assertIn(chosen[key].encode(), prompt)
            self.assertNotIn(b'ranking_factors', prompt)
            if route == 'codex_native':
                self.assertEqual(json.loads((folder / 'request.json').read_text())['prompt'].encode(), prompt)
            else:
                packet = task.export_web_execution(job, 1)
                envelope = task.web_execution_helper()
                self.assertEqual(Path(packet['submission_file']).read_bytes(),
                                 envelope.prefix(envelope.version(data)) + prompt + envelope.SUFFIX)
        self.assertEqual(prompts[0], prompts[1])

    def test_ranked_style_reuse_still_requires_reason_and_old_cli_commands_work(self):
        prior = self.prior(self.spec('athleisure', pose_id='al-zip-close'))
        spec = self.preparation('old-money')
        spec['pose_history_tasks'] = [str(prior)]
        chosen = self.candidate(self.rank(spec), 'om-cuff-close')
        shot = spec['shot_plan']['looks'][0]
        shot.update({k: chosen[k] for k in ('pose_id', 'body_action', 'hands', 'support', 'garment_views')})
        with self.assertRaisesRegex(ValueError, 'Cross-group pose repeats'):
            visual.prepare(spec)
        shot['pose_reuse_reason'] = 'Use the same low-hand baseline to compare the source-backed cuff.'
        prepared = visual.prepare(spec)
        job = self.create(spec, 'style-choice', visual=prepared)
        task.export(job)
        self.assertEqual(task.read(job)['attempts'], 0)
        command = [sys.executable, str(fixtures.SKILL / 'scripts/pose_library.py')]
        search = subprocess.run([*command, 'search', '--query', 'tt-stand-neutral', '--garment-views', 'front'],
                                capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(search.stdout), poses.candidates(query='tt-stand-neutral', garment_views=['front']))
        source, output = self.root / 'apply-source.json', self.root / 'selection.json'
        source.write_text(json.dumps(self.preparation()['shot_plan']))
        subprocess.run([*command, 'apply', '--plan', str(source), '--shot-id', 'garment-shot-1',
                        '--pose-id', 'tt-stand-neutral', '--view', 'front', '--mode', 'text', '--origin', 'auto',
                        '--output', str(output)], capture_output=True, text=True, check=True)
        selected = json.loads(output.read_text())
        self.assertIsNone(selected['reference'])
        self.assertEqual(selected['shot_plan']['looks'][0]['pose_selection']['definition']['group_id'], 'tt-stand-neutral')


if __name__ == '__main__':
    unittest.main()
