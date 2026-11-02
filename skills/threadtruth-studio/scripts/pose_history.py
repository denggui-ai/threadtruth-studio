#!/usr/bin/env python3
"""Compare selected task records with a new pose plan; no database or image reads."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import unicodedata

sys.dont_write_bytecode = True


def _module(name):
    spec = importlib.util.spec_from_file_location('history_' + name, Path(__file__).with_name(name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _sha(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def _line(value):
    return isinstance(value, str) and bool(value.strip()) and not any(ord(c) < 32 for c in value)


def action_hash(shot):
    parts = []
    for field in ('body_action', 'hands', 'support'):
        value = shot.get(field)
        if not _line(value):
            raise ValueError('History comparison requires body_action, hands and support')
        parts.append(' '.join(re.sub(r'[\W_]+', ' ', unicodedata.normalize('NFKC', value).casefold()).split()))
    return digest(parts)


def pose_keys(shot, card=None):
    """Use frozen identifiers, never infer old geometry from a live library."""
    result = []
    pose_id = shot.get('pose_id')
    if pose_id is not None:
        if not _line(pose_id):
            raise ValueError('Historical pose_id must be a nonempty single line')
        result.append('id:' + pose_id)
    base = None
    if 'pose_selection' in shot:
        base = _module('pose_library')._validate_snapshot(shot['pose_selection'])
        if pose_id != base['group_id']:
            raise ValueError('Historical pose_id differs from its frozen selection')
    elif card and 'pose_pool_snapshot' in card:
        for binding in card['pose_pool_snapshot']['entries']:
            if binding['entry']['id'] == pose_id and 'base' in binding:
                base = binding['base']['definition']
                break
    if base is not None:
        result.append('owned:' + base['source_id'] + ':' + base['group_id'])
    return result


def _card(holder):
    visual = holder.get('visual_plan')
    if visual is None:
        return None
    if digest(visual) != holder.get('visual_plan_sha256'):
        raise ValueError('Historical visual plan hash changed')
    component = visual['style']['primary']
    _module('visual_plan')._component(component)
    return component['snapshot']


def _plan(holder):
    plan = holder.get('shot_plan')
    if plan is not None and digest(plan) != holder.get('shot_plan_sha256'):
        raise ValueError('Historical shot plan hash changed')
    if not isinstance(plan, dict) or plan.get('version') != 2:
        return None
    looks, selected = plan.get('looks'), plan.get('selected_shot_ids')
    if (not isinstance(looks, list) or not looks or not isinstance(selected, list) or not selected
            or any(not isinstance(s, dict) or not _line(s.get('shot_id')) for s in looks)
            or any(not isinstance(s, str) for s in selected)):
        raise ValueError('Historical v2 plan needs logical shots and selected_shot_ids')
    ids = [s['shot_id'] for s in looks]
    if len(ids) != len(set(ids)) or len(selected) != len(set(selected)) or not set(selected) <= set(ids):
        raise ValueError('Historical shot selection is ambiguous')
    return plan


def freeze(tasks):
    """Read only the explicit task JSONs. Returned/rejected plans are not visual proof."""
    if (not isinstance(tasks, list) or not tasks
            or any(not isinstance(p, (str, Path)) or not str(p).strip() for p in tasks)):
        raise ValueError('pose_history_tasks must list selected task directories or task JSON files')
    sources, entries, seen = [], [], set()
    for path in tasks:
        path = Path(path)
        if path.is_dir():
            path = path / 'task.json'
        raw = path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        if sha in seen:
            continue
        seen.add(sha)
        data = json.loads(raw)
        if not isinstance(data, dict) or data.get('schema_version') not in (1, 2):
            raise ValueError('History input must be an existing schema-1/2 task record')
        source = dict(id='history-' + str(len(sources) + 1), task_sha256=sha, skipped={})
        sources.append(source)
        rows = data.get('looks')
        if not isinstance(rows, list) or not rows:
            raise ValueError('History task must contain look records')
        _plan(data)
        _card(data)
        purpose = data.get('context', {}).get('purpose', 'delivery')
        if purpose not in ('delivery', 'preview-grid'):
            source['skipped']['unsupported-purpose'] = len(rows)
            continue
        for row in rows:
            if (not isinstance(row, dict) or not isinstance(row.get('history', []), list)
                    or any(not isinstance(item, dict) for item in row.get('history', []))):
                raise ValueError('Historical look and retry records must be objects')
            retained = [(item, item) for item in row.get('history', [])] + [(row, data)]
            for attempt, holder in retained:
                if attempt.get('state') not in ('returned', 'accepted', 'rejected') or not attempt.get('output'):
                    reason = 'not-returned'
                else:
                    plan = _plan(holder)
                    reason = 'unsupported-or-missing-plan' if plan is None else None
                if reason:
                    source['skipped'][reason] = source['skipped'].get(reason, 0) + 1
                    continue
                card = _card(holder)
                if not isinstance(attempt['output'], dict):
                    raise ValueError('Historical output must contain a SHA256')
                output = attempt['output'].get('sha256')
                number = attempt.get('number')
                if (not _sha(output) or type(number) is not int or number < 1
                        or type(attempt.get('attempt_number', 1)) is not int or attempt.get('attempt_number', 1) < 1):
                    raise ValueError('Returned history requires output hash and valid look/attempt numbers')
                selected = plan['selected_shot_ids']
                if purpose == 'preview-grid':
                    if number != 1:
                        raise ValueError('Preview history has one grid record')
                    ids = selected
                else:
                    if number > len(selected):
                        raise ValueError('Historical look number is outside its selected shots')
                    ids = [selected[number - 1]]
                for shot in plan['looks']:
                    if shot['shot_id'] in ids:
                        entries.append(dict(source=source['id'], shot_id=shot['shot_id'],
                            pose_keys=pose_keys(shot, card), action_sha256=action_hash(shot),
                            plan_sha256=holder['shot_plan_sha256'], output_sha256=output,
                            attempt=attempt.get('attempt_number', 1), state=attempt['state'], purpose=purpose))
    result = dict(version=1, sources=sources, entries=entries)
    result['sha256'] = digest(result)
    validate(result)
    return result


def validate(history):
    if (not isinstance(history, dict) or set(history) != {'version', 'sources', 'entries', 'sha256'}
            or type(history['version']) is not int or history['version'] != 1
            or history['sha256'] != digest({k: v for k, v in history.items() if k != 'sha256'})
            or not isinstance(history['sources'], list) or not history['sources']
            or not isinstance(history['entries'], list)):
        raise ValueError('Frozen pose history version, sources, entries or hash changed')
    ids = set()
    for source in history['sources']:
        if (not isinstance(source, dict) or set(source) != {'id', 'task_sha256', 'skipped'}
                or not _line(source['id']) or source['id'] in ids or not _sha(source['task_sha256'])
                or not isinstance(source['skipped'], dict)
                or any(k not in {'not-returned', 'unsupported-or-missing-plan', 'unsupported-purpose'}
                       or type(v) is not int or v < 1 for k, v in source['skipped'].items())):
            raise ValueError('Invalid frozen pose history source')
        ids.add(source['id'])
    for entry in history['entries']:
        fields = {'source', 'shot_id', 'pose_keys', 'action_sha256', 'plan_sha256', 'output_sha256', 'attempt', 'state', 'purpose'}
        if (not isinstance(entry, dict) or set(entry) != fields or entry['source'] not in ids
                or not _line(entry['shot_id']) or not isinstance(entry['pose_keys'], list)
                or any(not _line(k) or not k.startswith(('id:', 'owned:')) for k in entry['pose_keys'])
                or len(entry['pose_keys']) != len(set(entry['pose_keys']))
                or any(not _sha(entry[k]) for k in ('action_sha256', 'plan_sha256', 'output_sha256'))
                or type(entry['attempt']) is not int or entry['attempt'] < 1
                or entry['state'] not in ('returned', 'accepted', 'rejected')
                or entry['purpose'] not in ('delivery', 'preview-grid')):
            raise ValueError('Invalid frozen pose history entry')
    return history


def compare(history, plan, card=None):
    validate(history)
    if not isinstance(plan, dict) or plan.get('version') != 2:
        raise ValueError('Cross-group pose checks require a v2 plan; keep classic tasks unchanged')
    results = []
    for shot in plan['looks']:
        if plan['series_role'] == 'standalone' and shot['shot_id'] not in plan['selected_shot_ids']:
            continue
        keys, action = set(pose_keys(shot, card)), action_hash(shot)
        matches = []
        for entry in history['entries']:
            common = keys & set(entry['pose_keys'])
            basis = (['pose-id'] if any(k.startswith('id:') for k in common) else [])
            if any(k.startswith('owned:') for k in common):
                basis.append('shared-geometry')
            if action == entry['action_sha256']:
                basis.append('body-hands-support')
            if basis:
                matches.append(dict(source=entry['source'], shot_id=entry['shot_id'],
                    attempt=entry['attempt'], state=entry['state'], purpose=entry['purpose'], basis=basis))
        if matches:
            reason = shot.get('pose_reuse_reason', '')
            if 'pose_reuse_reason' in shot and not _line(reason):
                raise ValueError('pose_reuse_reason must be a nonempty single line')
            results.append(dict(shot_id=shot['shot_id'], matches=matches, reuse_reason=reason))
    return dict(status='no-comparable-history' if not history['entries'] else
                ('repeats' if results else 'no-exact-repeat'), sources=copy.deepcopy(history['sources']),
                compared_records=len(history['entries']), repeats=results)


def enforce(history, plan, card=None):
    report = compare(history, plan, card)
    unresolved = [row['shot_id'] for row in report['repeats'] if not row['reuse_reason'].strip()]
    if unresolved:
        raise ValueError('Cross-group pose repeats: ' + ', '.join(unresolved)
                         + '; choose another supported action or give each shot a concrete pose_reuse_reason')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', action='append', required=True, help='Explicit task directory or task JSON; repeat for another group')
    parser.add_argument('--plan', type=Path, help='Optional proposed shot_plan JSON')
    parser.add_argument('--entry-id', help='Current style entry, for shared geometry aliases')
    args = parser.parse_args(argv)
    try:
        frozen = freeze(args.task)
        result = dict(pose_history=frozen)
        if args.plan:
            card = _module('visual_library').card(args.entry_id) if args.entry_id else None
            result['comparison'] = compare(frozen, json.loads(args.plan.read_text()), card)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, KeyError, TypeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
