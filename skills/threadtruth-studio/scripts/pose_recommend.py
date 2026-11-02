"""Read-only, deterministic pose ordering from existing planning fields and history."""
import copy
import importlib.util
from pathlib import Path
import re


def _module(name):
    spec = importlib.util.spec_from_file_location('recommend_' + name, Path(__file__).with_name(name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


# Limited part/goal vocabulary for ranking clues, not garment facts or semantic QA.
GOALS = {
    'collar': r'\b(?:collars?|neckline)\b|领口|领缘|领型',
    'cuff': r'\bcuffs?\b|袖口',
    'sleeve': r'\bsleeves?\b|袖形|袖量|袖长|袖部|衣袖|袖子',
    'hem': r'\b(?:hem|hemline)\b|下摆|衣摆|后摆',
    'length': r'\blength\b|衣长|裤长|裙长',
    'waist': r'\b(?:waist|abdomen|abdominal)\b|腰|腹',
    'chest': r'\bchest\b|胸',
    'print': r'\b(?:print|printed|pattern|embroidery)\b|印花|图案|纹样|刺绣',
    'pocket': r'\bpockets?\b|口袋|胸袋|后袋',
    'closure': r'\b(?:closure|placket|zip|zipper|buttons?)\b|门襟|拉链|纽扣',
    'legs': r'\b(?:trouser|pant)s?\b|裤腿|裤管',
    'silhouette': r'\b(?:silhouette|outline)\b|轮廓|版型',
    'movement': r'\b(?:motion|movement|dynamic|stride)\b|动态|动感|步幅',
}
ORDER = ['target_caution_count', 'goal_clue_count_desc', 'framing_penalty', 'history_tier',
         'current_style_before_owned_on_tie', 'stable_pose_id_and_view']


def _terms(text):
    return {name for name, pattern in GOALS.items() if re.search(pattern, text, re.I)}


def _evidence(targets, fields):
    return [dict(target=target, fields=[name for name, text in fields.items() if target in _terms(text)])
            for target in sorted(targets) if any(target in _terms(text) for text in fields.values())]


def _target(spec, shot_id, catalog):
    plan = spec.get('shot_plan')
    if not isinstance(plan, dict) or plan.get('version') != 2 or not isinstance(plan.get('looks'), list):
        raise ValueError('Pose recommendations require an existing v2 shot plan')
    shots = [s for s in plan['looks'] if isinstance(s, dict) and s.get('shot_id') == shot_id]
    if len(shots) != 1:
        raise ValueError('Select one unambiguous logical shot_id')
    shot = shots[0]
    if (not catalog._text(shot.get('display_goal')) or not isinstance(shot.get('must_show'), list)
            or not shot['must_show'] or any(not catalog._text(x) for x in shot['must_show'])
            or shot.get('framing') not in ('full-body', 'half-body', 'knee-up', 'detail')):
        raise ValueError('Ranking needs display_goal, must_show and framing from the target shot')
    views = shot.get('garment_views')
    _module('shot_plan')._check_views('recommendation target garment_views', views)
    inventory = spec.get('inventory')
    if not isinstance(inventory, list):
        raise ValueError('Ranking needs the existing reference inventory')
    catalog.check_inventory(inventory)
    garments = {r.get('sha256') for r in inventory if r.get('role') == 'garment-source'}
    refs = shot.get('reference_sha256s')
    if (not isinstance(refs, list) or not refs or any(not catalog._sha(h) or h not in garments for h in refs)
            or len(set(refs)) != len(refs)):
        raise ValueError('Target references must be distinct garment-source hashes')
    coverage = plan.get('coverage')
    if not isinstance(coverage, list):
        raise ValueError('Ranking needs the existing reviewed garment coverage')
    supported = set()
    for sha in refs:
        rows = [r for r in coverage if isinstance(r, dict) and r.get('sha256') == sha]
        if len(rows) != 1 or rows[0].get('usable') is not True or rows[0].get('same_sku') is not True:
            raise ValueError('Target references require unambiguous usable same_sku coverage')
        _module('shot_plan')._check_views('recommendation source views', rows[0].get('views'))
        supported.update(rows[0]['views'])
    if not set(views) <= supported:
        raise ValueError('Target garment views lack evidence in its own reference_sha256s')
    return shot


def _history_result(history, probe, card, helper):
    if history is None:
        return dict(status='not-provided', tier=1, matches=[], requires_reuse_reason=False)
    plan = dict(version=2, series_role='standalone', selected_shot_ids=[probe['shot_id']], looks=[probe])
    report = helper.compare(history, plan, card)
    matches = [m for row in report['repeats'] for m in row['matches']]
    if matches:
        exact = any(any(b != 'near-body-hands-support' for b in m['basis']) for m in matches)
        status, tier = ('exact-repeat', 3) if exact else ('near-repeat', 2)
    elif report['status'] == 'no-comparable-history':
        status, tier = 'no-comparable-history', 1
    elif history['version'] == 1:
        status, tier = 'no-exact-match-near-unchecked', 1
    elif report['near_comparison']['unavailable_pairs']:
        status, tier = 'no-match-with-near-gaps', 1
    else:
        status, tier = 'no-match-in-covered-rules', 0
    result = dict(status=status, tier=tier, matches=matches, requires_reuse_reason=bool(matches))
    if 'near_comparison' in report:
        result['near_comparison'] = report['near_comparison']
    return result


def recommend(spec, shot_id, *, history=None, limit=5, catalog_path=None):
    """Rank one shot's options. Never mutate input, attach images or choose a pose."""
    if not isinstance(spec, dict) or type(limit) is not int or not 1 <= limit <= 60:
        raise ValueError('Recommendations need a preparation spec and limit between 1 and 60')
    poses, visual, hist = _module('pose_library'), _module('visual_library'), _module('pose_history')
    catalog = poses._catalog()
    target = _target(spec, shot_id, catalog)
    model = visual._models().validate_model(spec.get('model'), allow_child=True)
    form = spec.get('output_form', 'human')
    report = dict(version=1, rule='goal-history-order-v1', shot_id=shot_id, ordering=ORDER[:],
                  candidates=[], excluded={}, status='ranked')
    if (form not in ('human', 'faceless') or model['subject'] == 'child model'
            or (form == 'human' and model['source_type'] == 'real')):
        report.update(status='unsupported-scope', scope_note='Use the existing child, real-face or non-person planning path.')
        return report
    if history is not None and 'pose_history_tasks' in spec:
        raise ValueError('Choose frozen history or explicit task inputs, not both')
    if history is None and 'pose_history_tasks' in spec:
        history = hist.freeze(spec['pose_history_tasks'])
    if history is not None:
        hist.validate(history)
    report['history_scope'] = (dict(version=history['version'], sha256=history['sha256'],
                                   sources=len(history['sources']), returned_records=len(history['entries']))
                               if history is not None else None)
    goal_texts = [target['display_goal'], *target['must_show']]
    goals = set().union(*(_terms(text) for text in goal_texts))
    report['goal_terms'] = sorted(goals)
    report['unrecognized_must_show'] = [text for text in target['must_show'] if not _terms(text)]
    report['review_note'] = ('Keyword clues and declared limits only; verify the complete avoid_when, garment mobility, '
                             'support and identity evidence. No-match history is not proof of a new image pose.')
    card = visual.card(spec['entry_id'])
    candidates = []
    for row in card.get('pose_vocabulary', []):
        candidates.append(dict(kind='style', pose_id=row['id'], view=None, title=row['id'], family=row['family'],
            body_action=row['body'], hands=row['hands'], support=row['support'], garment_views=row['views'],
            review=dict(avoid_when=row['avoid_when'], check=row['check'], occludes=[], review_note='Current style text vocabulary.')))
    for row in poses.candidates(include_restricted=True, catalog_path=catalog_path or poses.CATALOG):
        if row.get('selection_policy'):
            report['excluded']['user-only'] = report['excluded'].get('user-only', 0) + 1
            continue
        if model['subject'] not in ('adult model', 'adult female model'):
            report['excluded']['owned-subject-scope'] = report['excluded'].get('owned-subject-scope', 0) + 1
            continue
        definition = {k: copy.deepcopy(row[k]) for k in poses.DEFINITION_FIELDS}
        selection = dict(version=1, definition=definition, definition_sha256=poses.digest(definition),
                         mode='text', origin='auto', adaptation_note='')
        poses._validate_snapshot(selection)
        candidates.append(dict(kind='owned', pose_id=row['group_id'], view=row['view'], title=row['title'],
            family=row['family'], body_action=row['body_action'], hands=row['hands'], support=row['support'],
            garment_views=row['garment_views'], _selection=selection,
            review=dict(avoid_when=row['avoid_when'], check='', occludes=row.get('occludes', []), review_note=row['review_note'])))
    ranked = []
    for row in candidates:
        if not set(row['garment_views']) <= set(target['garment_views']):
            report['excluded']['target-garment-views'] = report['excluded'].get('target-garment-views', 0) + 1
            continue
        probe = dict(shot_id=shot_id, pose_id=row['pose_id'],
                     **{k: row[k] for k in ('body_action', 'hands', 'support')})
        if '_selection' in row:
            probe['pose_selection'] = row.pop('_selection')
        keys = hist.pose_keys(probe, card)
        row['_group'] = next((key for key in keys if key.startswith('owned:')), 'text:' + hist.action_hash(probe))
        cautions = _evidence(goals, dict(avoid_when=row['review']['avoid_when'],
                                       occludes=' '.join(row['review']['occludes'])))
        clues = _evidence(goals - {x['target'] for x in cautions},
                          dict(title=row['title'] if row['kind'] == 'owned' else '',
                               body_action=row['body_action'], hands=row['hands'], check=row['review']['check']))
        framing = int((target['framing'] == 'detail' and row['family'] != 'close')
                      or (target['framing'] == 'full-body' and row['family'] == 'close'))
        row['history'] = _history_result(history, probe, card, hist)
        row['ranking_factors'] = dict(target_cautions=cautions, goal_clues=clues,
                                     framing_penalty=framing, history_tier=row['history']['tier'])
        row['_sort'] = (len(cautions), -len(clues), framing, row['history']['tier'],
                        0 if row['kind'] == 'style' else 1, row['pose_id'], row['view'] or '')
        ranked.append(row)
    groups = {}
    for row in sorted(ranked, key=lambda r: r['_sort']):
        key = row.pop('_group')
        row.pop('_sort')
        if key in groups:
            groups[key]['alternatives'].append({k: row[k] for k in ('kind', 'pose_id', 'view', 'garment_views')})
        else:
            row['alternatives'] = []
            groups[key] = row
    report['eligible_actions'] = len(groups)
    report['candidates'] = list(groups.values())[:limit]
    for number, row in enumerate(report['candidates'], 1):
        row['rank'] = number
    if not report['candidates']:
        report['status'] = 'no-eligible-candidates'
    return report
