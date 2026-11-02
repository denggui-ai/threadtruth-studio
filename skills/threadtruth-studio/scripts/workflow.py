"""Versioned plan decisions, target QA and moderation scope. No I/O or generation."""
import copy
import hashlib
import json


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def text(value):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= 2400


def enabled(data):
    version = data.get('workflow_version', 0)
    if type(version) is not int or version not in (0, 1):
        raise ValueError('Unsupported workflow version')
    return version == 1


def shot(data, number, plan=None):
    plan = plan or data.get('shot_plan')
    if not isinstance(plan, dict) or plan.get('version') != 2:
        return None
    identifier = plan['selected_shot_ids'][number - 1]
    return next(item for item in plan['looks'] if item['shot_id'] == identifier)


def check_preparation(data):
    plan = data.get('shot_plan')
    if not isinstance(plan, dict) or plan.get('version') != 2:
        return
    active = [item for item in plan['looks'] if item['shot_id'] in plan['selected_shot_ids']]
    visual = {item.get('shot_id'): item for item in data.get('visual_plan', {}).get('shots', [])}
    for item in active:
        decision = item.get('pose_decision')
        selected = bool(item.get('pose_selection') or item.get('pose_id'))
        if selected and decision:
            raise ValueError('Choose a frozen library pose or a custom decision, not both: ' + item['shot_id'])
        if not selected:
            if (not isinstance(decision, dict) or set(decision) != {'kind', 'reason'}
                    or decision['kind'] not in ('custom', 'not-applicable') or not text(decision['reason'])):
                raise ValueError('Record the library selection or a specific custom pose decision for ' + item['shot_id'])
            if decision['kind'] == 'not-applicable' and item['framing'] != 'detail':
                raise ValueError('A body shot needs a library or custom action, not not-applicable')
        if item['framing'] == 'detail' and not visual.get(item['shot_id'], {}).get('garment_focus'):
            raise ValueError('Prepare a source-backed garment_focus for detail shot ' + item['shot_id'])


def confirmation(data, decision, fingerprint, at):
    if not enabled(data):
        raise ValueError('Plan confirmation applies to workflow version 1 tasks')
    if (not isinstance(decision, dict) or set(decision) != {'style', 'path', 'image_count', 'note'}
            or not text(decision['note']) or decision['style'] != data['context']['style']
            or type(decision['image_count']) is not int or decision['image_count'] != len(data['looks'])):
        raise ValueError('Confirm the actual style, current-stage image_count, path and user decision note')
    preview = data['context'].get('purpose') == 'preview-grid'
    allowed = {'preview'} if preview else ({'after-preview'} if data.get('preview_origin') else
                                          ({'single', 'direct'} if len(data['looks']) == 1 else {'direct'}))
    if decision['path'] not in allowed:
        raise ValueError('Confirm the actual preview/direct path; allowed: ' + ', '.join(sorted(allowed)))
    check_preparation(data)
    return dict(copy.deepcopy(decision), version=1, plan_sha256=fingerprint, at=at)


def validate(data):
    if not enabled(data):
        return
    current = data.get('plan_confirmation')
    if current is not None and (not isinstance(current, dict) or current.get('version') != 1
                               or digest(current) != data.get('plan_confirmation_sha256')):
        raise ValueError('Frozen plan confirmation changed')
    for previous in data.get('plan_confirmation_history', []):
        if digest(previous['decision']) != previous['sha256']:
            raise ValueError('Historical plan confirmation changed')


def require_confirmation(data, fingerprint):
    if not enabled(data):
        return
    validate(data)
    current = data.get('plan_confirmation')
    if current is None or current['plan_sha256'] != fingerprint:
        raise ValueError('Confirm the current plan and preview/direct route before reserving a request')
    check_preparation(data)


def store_confirmation(data, value):
    old = data.get('plan_confirmation')
    if old == value:
        return
    if old:
        data.setdefault('plan_confirmation_history', []).append(dict(decision=old, sha256=digest(old)))
    data.update(plan_confirmation=value, plan_confirmation_sha256=digest(value))


def rebind_confirmation(data, fingerprint, note, at):
    """An explicitly approved local revision keeps its already selected route."""
    if enabled(data) and data.get('plan_confirmation') and data['plan_confirmation']['plan_sha256'] != fingerprint:
        old = data['plan_confirmation']
        decision = {key: old[key] for key in ('style', 'path', 'image_count', 'note')}
        decision.update(image_count=len(data['looks']), note=note)
        if decision['path']=='single' and len(data['looks'])>1:decision['path']='direct'
        store_confirmation(data, confirmation(data, decision, fingerprint, at))


def goal(data, row):
    if row.get('adopted_revision'):
        return row['adopted_revision']['goal']
    if data.get('revision_origin'):
        return data['revision_origin']['goal']
    item = shot(data, row['number'], row.get('shot_plan'))
    if item:
        return item['display_goal']
    visual = data.get('visual_plan', {})
    if visual.get('shots'):
        return visual['shots'][row['number'] - 1]['composition']
    return data.get('context', {}).get('pose_description', 'Show the declared source garment and presentation')


def review_result(data, row, review):
    required = {'goal', 'garment', 'photography'}
    identity = row.get('adopted_revision', {}).get('identity', data['identity'])
    if identity:
        required |= {'identity', 'anatomy'}
    if not isinstance(review, dict) or set(review) != required:
        raise ValueError('QA records expected, observed and result for: ' + ', '.join(sorted(required)))
    for key, item in review.items():
        if (not isinstance(item, dict) or set(item) != {'expected', 'observed', 'result'}
                or not text(item['expected']) or not text(item['observed'])
                or item['result'] not in ('met', 'unmet', 'unknown')):
            raise ValueError('Each QA item needs its actual expectation, observation and met/unmet/unknown result')
    if review['goal']['expected'] != goal(data, row):
        raise ValueError('QA must assess the frozen display goal, not a substituted target')
    if any(item['result'] == 'unmet' for key, item in review.items() if key != 'photography'):
        return 'qa-retry'
    if any(item['result'] != 'met' for item in review.values()):
        return 'qa-user-review'
    return 'qa-pass'


def record_review(data, row, review, requested):
    if not enabled(data) and review is None:
        return
    result = review_result(data, row, review)
    if requested != result:
        raise ValueError('QA result for the actual requirements is ' + result + '; cannot record ' + str(requested))
    row['review'] = copy.deepcopy(review)
    row['review_sha256'] = digest(review)


def validate_review(data, row):
    if enabled(data) and row.get('state')=='accepted' and 'review' not in row:
        raise ValueError('An accepted workflow-1 image needs recorded target QA')
    if 'review' in row:
        if digest(row['review']) != row.get('review_sha256'):
            raise ValueError('Recorded target QA changed')
        result = review_result(data, row, row['review'])
        # Later audit rejection can tighten the result without falsifying the original observations.
        if row.get('qa') not in (result, 'qa-retry'):
            raise ValueError('QA status contradicts recorded target observations')
    if 'retained_by_user' in row:
        kept = row['retained_by_user']
        if not text(kept.get('note')) or kept.get('output_sha256') != row.get('output', {}).get('sha256'):
            raise ValueError('User retention must bind the actual image without erasing QA')
    for earlier in row.get('qa_history',[]):
        if isinstance(earlier,dict) and 'review' in earlier and digest(earlier['review'])!=earlier.get('review_sha256'):
            raise ValueError('Historical target QA changed')


def group(data, number, plan=None):
    item = shot(data, number, plan)
    framing = item['framing'] if item else data.get('revision_origin', {}).get('framing', 'presentation')
    form = data.get('context', {}).get('output_form')
    return ('person' if form in ('human', 'faceless') else form, 'detail' if framing == 'detail' else 'body')


def moderation_sources(data):
    if not enabled(data):
        return []
    result = []
    for current in data['looks']:
        for row in [*current.get('history', []), current]:
            failure = row.get('failure', {})
            if failure.get('code') == 'moderation_blocked':
                result.append(dict(sha256=digest(failure), group=group(data, current['number'], row.get('shot_plan'))))
    return result


def hold_sources(data, look, related=()):
    if not enabled(data):
        return []
    row = data['looks'][look - 1]
    checked = {entry['failure_sha256'] for entry in row.get('moderation_reviews', [])}
    key = group(data, look)
    return list(dict.fromkeys(item['sha256'] for item in [*moderation_sources(data), *related]
                              if tuple(item['group']) == key and item['sha256'] not in checked))


def hold_error(data, look, related=()):
    if hold_sources(data, look, related):
        return 'Similar moderation request is on hold; review its original goal and recovery plan first'
    return None


def acknowledge(data, look, failure_sha256, note, at, related=()):
    if not text(note) or failure_sha256 not in hold_sources(data, look, related):
        raise ValueError('Review the exact current moderation hold with a concrete decision note')
    data['looks'][look - 1].setdefault('moderation_reviews', []).append(
        dict(failure_sha256=failure_sha256, note=note, at=at))
