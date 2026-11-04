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
ORDER = ['current_style_first', 'body_relation_penalty', 'framing_penalty', 'history_tier',
         'stable_pose_id_and_view']

# Recommendation-only vocabulary; frozen shot-plan validation keeps its original words.
BACK_ACTION = re.compile(
    r'\b(?:turn(?:s|ed|ing)?|fac(?:e|es|ed|ing)|walk(?:s|ed|ing)?)\s+away\b'
    r'|\bback\s+to\s+(?:the\s+)?camera\b|\bover[- ](?:the[- ])?shoulder\b'
    r'|\bface\s+turn(?:s|ed|ing)?\s+back\b|\bthree[- ]quarter\s+away\b', re.I)


def _needs_back(row, back_words):
    """View labels cannot override explicit back-facing actions or evidence requirements."""
    action = ' '.join(row.get(key, '') for key in ('body', 'body_action', 'hands', 'support', 'head'))
    if back_words.search(action) or BACK_ACTION.search(action):
        return True
    limits = ' '.join(row.get(key, '') for key in ('avoid_when', 'check', 'review_note'))
    return bool(re.search(
        r'(?:后侧|后片|背面|背部)(?:商品)?(?:依据|参考|素材|源图)(?:不足|缺失|未知)'
        r'|(?:需|需要|缺少|缺乏)(?:同款|真实|可用)?(?:后侧|后片|背面|背部)(?:商品)?(?:依据|参考|素材|源图)'
        r'|背面未知却转出后片'
        r'|\b(?:needs?|requires?|missing|insufficient|no usable|lack of)\b[^.;。；]*\b(?:back|rear)\b[^.;。；]*\b(?:evidence|sources?|references?)\b'
        r'|\b(?:back|rear)\b[^.;。；]*\b(?:evidence|sources?|references?)\b[^.;。；]*\b(?:missing|insufficient|unavailable)\b',
        limits, re.I))


def _terms(text):
    return {name for name, pattern in GOALS.items() if re.search(pattern, text, re.I)}


def _evidence(targets, fields):
    return [dict(target=target, fields=[name for name, text in fields.items() if target in _terms(text)])
            for target in sorted(targets) if any(target in _terms(text) for text in fields.values())]


def _occlusion_conflicts(targets, review):
    """Veto declared obstruction, not every conditional mobility/pressure caution."""
    definite = [text for text in review['occludes']
                if not re.search(r'可能|风险|需核|影响|变化|\b(?:may|might|risk)\b', text, re.I)]
    # These catalog clauses explicitly say the touched part cannot be fully shown.
    # Other avoid_when text remains a review caution, including sitting/kneeling.
    blocked = [clause for clause in re.split(r'[；;。]', review['avoid_when'])
               if re.search(r'(?:必须|需)(?:完全)?无遮挡|手遮住|\b(?:obscures|occludes|covers)\b', clause, re.I)]
    return _evidence(targets, dict(occludes='; '.join(definite), avoid_when='; '.join(blocked)))


def _body_relation(row):
    """Limited body/support clues, deliberately excluding head, hands and scenery."""
    body = row.get('body_action', '')
    support = row.get('support', '').lower()
    height = next((name for name, pattern in (
        ('lying', r'\b(?:lying|lie|reclining on the (?:floor|ground))\b|侧卧'),
        ('floor-seated', r'\b(?:sitting|seated) on (?:the |a )?(?:floor|ground)\b|地坐'),
        ('squat', r'\b(?:squat|squatting)\b|蹲'),
        ('kneel', r'\b(?:kneel|kneeling)\b|跪'),
        ('seated', r'\b(?:sit|sitting|seated|perch|perching)\b|坐'),
        ('standing', r'\b(?:stand|standing|walk|walking|lean|leaning|stride)\b|站|走|倚'),
    ) if re.search(pattern, body, re.I)), None)
    if height is None:
        height = {'stand': 'standing', 'walk': 'standing', 'turn': 'standing', 'lean': 'standing',
                  'sit': 'seated', 'floor': 'floor-seated', 'kneel': 'kneel',
                  'squat': 'squat', 'lie': 'lying'}.get(row.get('family'))
    support = re.sub(r'\bno (?:external |hand, thigh or external )?support\b', '', support)
    supports = [name for name, pattern in (
        ('wall', r'wall|doorway|fence|墙|门框'),
        ('seat', r'bench|chair|seat|stool|ledge|sill|台沿|凳|椅'),
        ('rail', r'rail|栏杆'),
        ('floor-hand', r'(?:palm|hand|forearm).*(?:floor|ground)|(?:floor|ground).*(?:palm|hand|forearm)'),
        ('floor-knee', r'knees?.*(?:floor|ground)|(?:floor|ground).*knees?'),
    ) if re.search(pattern, support)]
    if not supports and re.search(r'feet|foot|leg|ground|floor|脚|足|腿', support):
        supports = ['feet']
    torso = ', '.join(part for part in re.split(r'[,;.]', body)
                      if not re.search(r'\b(?:head|chin|eyes?|gaze|glanc\w*|look\w*)\b', part, re.I))
    direction = next((name for name, pattern in (
        ('back', r'back to camera|facing away|背对'),
        ('quarter', r'three[- ]quarter|shallow turn|quarter[- ]turn|浅转|斜转'),
        ('side', r'(?:torso|body|shoulders?) (?:facing )?sideways|侧身'),
        ('front', r'frontal|(?:torso|body|chest|shoulders?) (?:kept |facing )?front|躯干正面'),
    ) if re.search(pattern, torso, re.I)), None)
    return dict(height=height, support=supports or None, torso=direction)


def _body_variety(row, probe, selected, card, hist):
    relation = _body_relation(row)
    keys = set(hist.pose_keys(probe, card))
    comparisons = []
    for other in selected:
        previous = _body_relation(other)
        different = [axis for axis in relation if relation[axis] is not None
                     and previous[axis] is not None and relation[axis] != previous[axis]]
        same = bool(keys & set(hist.pose_keys(other, card)))
        complete = all(relation[k] is not None and previous[k] is not None for k in relation)
        penalty = 2 if same else 0 if different else 2 if complete else 1
        comparisons.append(dict(shot_id=other['shot_id'], penalty=penalty,
                                different_axes=different, same_pose=same))
    return dict(relation=relation, comparisons=comparisons,
                penalty=max((item['penalty'] for item in comparisons), default=0))


def _target(spec, shot_id, catalog):
    plan = spec.get('shot_plan')
    if not isinstance(plan, dict) or plan.get('version') != 2 or not isinstance(plan.get('looks'), list):
        raise ValueError('Pose recommendations require an existing v2 shot plan')
    shots = [s for s in plan['looks'] if isinstance(s, dict) and s.get('shot_id') == shot_id]
    if len(shots) != 1:
        raise ValueError('Select one unambiguous logical shot_id')
    shot = shots[0]
    if (not catalog._text(shot.get('display_goal')) or not isinstance(shot.get('must_show'), list)
            or (not shot['must_show'] and shot.get('framing') == 'detail')
            or any(not catalog._text(x) for x in shot['must_show'])
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
    back_words = _module('shot_plan').BACK_WORDS
    catalog = poses._catalog()
    target = _target(spec, shot_id, catalog)
    model = visual._models().validate_model(spec.get('model'), allow_child=True)
    form = spec.get('output_form', 'human')
    report = dict(version=2, rule='style-body-history-order-v2', shot_id=shot_id, ordering=ORDER[:],
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
    must_show = set().union(*(_terms(text) for text in target['must_show']))
    report['goal_terms'] = sorted(goals)
    report['unrecognized_must_show'] = [text for text in target['must_show'] if not _terms(text)]
    report['review_note'] = ('Keyword clues and declared limits only; verify the complete avoid_when, garment mobility, '
                             'support and identity evidence. No-match history is not proof of a new image pose.')
    card = visual.card(spec['entry_id'])
    selected = [s for s in spec['shot_plan']['looks'] if s.get('shot_id') != shot_id
                and s.get('framing') != 'detail' and (s.get('pose_id') or s.get('pose_selection')
                    or s.get('pose_decision', {}).get('kind') == 'custom')]
    owned_rows = poses.candidates(include_restricted=True, catalog_path=catalog_path or poses.CATALOG)
    owned_by_view = {(r['group_id'], r['view']): r for r in owned_rows}
    bases = {b['entry']['id']: b['base']['definition']
             for b in card.get('pose_pool_snapshot', {}).get('entries', []) if 'base' in b}
    candidates = []
    for row in card.get('pose_vocabulary', []):
        base = bases.get(row['id'], {})
        occludes = owned_by_view.get((base.get('group_id'), base.get('view')), {}).get('occludes', [])
        candidates.append(dict(kind='style', pose_id=row['id'], view=None, title=row['id'], family=row['family'],
            body_action=row['body'], hands=row['hands'], support=row['support'], garment_views=row['views'],
            _needs_back=_needs_back(row, back_words),
            review=dict(avoid_when=row['avoid_when'], check=row['check'], occludes=occludes, review_note='Current style text vocabulary.')))
    for row in owned_rows:
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
            _needs_back=_needs_back(row, back_words),
            review=dict(avoid_when=row['avoid_when'], check='', occludes=row.get('occludes', []), review_note=row['review_note'])))
    ranked = []
    for row in candidates:
        supported_views = set(target['garment_views'])
        if 'front' in supported_views:
            supported_views.add('front-side')
        needs_back = row.pop('_needs_back') or 'back' in row['garment_views']
        if needs_back and 'back' not in supported_views:
            report['excluded']['needs-back'] = report['excluded'].get('needs-back', 0) + 1
            continue
        if not set(row['garment_views']) <= supported_views:
            report['excluded']['target-garment-views'] = report['excluded'].get('target-garment-views', 0) + 1
            continue
        if 'front-side' in row['garment_views'] and 'front-side' not in target['garment_views']:
            row['review']['view_adaptation'] = ('Front-only evidence permits a shallow turn without revealing back structure. '
                'Adapt the text action to the supported front view; this recommendation does not establish side/back facts '
                'or authorize an unchanged pose image selection.')
        obstruction = _occlusion_conflicts(must_show, row['review'])
        if obstruction:
            report['excluded']['must-show-occlusion'] = report['excluded'].get('must-show-occlusion', 0) + 1
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
        variety = _body_variety(row, probe, selected, card, hist)
        row['ranking_factors'] = dict(target_cautions=cautions, goal_clues=clues,
                                     current_style=row['kind'] == 'style', body_variety=variety,
                                     framing_penalty=framing, history_tier=row['history']['tier'])
        row['_sort'] = (0 if row['kind'] == 'style' else 1, variety['penalty'], framing,
                        row['history']['tier'], row['pose_id'], row['view'] or '')
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
