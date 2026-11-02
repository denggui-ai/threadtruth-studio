#!/usr/bin/env python3
"""Small owned pose library: inspect, select and freeze; no image/network calls."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'references/pose-library/catalog.json'
VOCABULARY = ROOT / 'references/pose-library/style-vocabulary.json'
DEFINITION_FIELDS = {'source_id', 'usage', 'group_id', 'view', 'title', 'family',
                     'body_action', 'hands', 'support', 'garment_views', 'avoid_when',
                     'review_note', 'sha256'}
OPTIONAL_DEFINITION_FIELDS = {'selection_policy'}
FAMILIES = {'stand', 'walk', 'sit', 'lean', 'turn', 'close', 'floor', 'kneel', 'squat', 'lie'}


def _catalog():
    spec = importlib.util.spec_from_file_location('owned_pose_catalog', Path(__file__).with_name('pose_catalog.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def freeze_vocabulary(ids, *, vocabulary_path=VOCABULARY, catalog_path=CATALOG):
    """Resolve a card's text pool once. Metadata only; never attach or read images."""
    if (not isinstance(ids, list) or not ids or len(ids) > 24
            or any(not isinstance(item, str) or not item.strip() for item in ids) or len(ids) != len(set(ids))):
        raise ValueError('pose_pool must contain distinct shared vocabulary ids')
    source = json.loads(Path(vocabulary_path).read_text(encoding='utf-8'))
    if (not isinstance(source, dict) or set(source) != {'version', 'entries'}
            or type(source['version']) is not int or source['version'] != 1 or not isinstance(source['entries'], list)):
        raise ValueError('Shared style vocabulary requires version=1 and entries')
    by_id = {}
    for row in source['entries']:
        if (not isinstance(row, dict) or not isinstance(row.get('id'), str)
                or not row['id'].strip() or row['id'] in by_id):
            raise ValueError('Shared vocabulary entries need unique ids')
        by_id[row['id']] = row
    catalog = None
    bindings = []
    for item in ids:
        if item not in by_id:
            raise ValueError('Unknown pose_pool vocabulary id: ' + item)
        row = copy.deepcopy(by_id[item])
        binding = dict(entry=row)
        if 'pose_id' in row:
            if catalog is None:
                catalog = _catalog().load(catalog_path)
            matches = _catalog().search(catalog, group_id=row['pose_id'], view=row.get('view'))
            if len(matches) != 1:
                raise ValueError('Shared vocabulary must select one existing pose/view: ' + item)
            selected = matches[0]
            definition = {k: copy.deepcopy(selected[k]) for k in DEFINITION_FIELDS}
            definition.update({k: copy.deepcopy(selected[k]) for k in OPTIONAL_DEFINITION_FIELDS if k in selected})
            binding['base'] = dict(version=1, definition=definition, definition_sha256=digest(definition),
                                   mode='text', origin='auto', adaptation_note='')
        bindings.append(binding)
    result = dict(version=1, entries=bindings)
    result['sha256'] = digest(result)
    resolve_vocabulary(result)
    return result


def resolve_vocabulary(frozen):
    """Project an already frozen pool to the legacy eight fields, without live reads."""
    if (not isinstance(frozen, dict) or set(frozen) != {'version', 'entries', 'sha256'}
            or type(frozen['version']) is not int or frozen['version'] != 1
            or not isinstance(frozen['entries'], list) or not 1 <= len(frozen['entries']) <= 24
            or frozen['sha256'] != digest(dict(version=frozen['version'], entries=frozen['entries']))):
        raise ValueError('Frozen pose pool version, entries or hash changed')
    rows = []
    fields = {'id', 'family', 'body', 'hands', 'support', 'views', 'avoid_when', 'check'}
    for binding in frozen['entries']:
        if not isinstance(binding, dict) or set(binding) not in ({'entry'}, {'entry', 'base'}):
            raise ValueError('Frozen pose pool bindings require an entry and optional base')
        entry = binding['entry']
        if not isinstance(entry, dict):
            raise ValueError('Frozen pose pool entry must be an object')
        if 'base' not in binding:
            if set(entry) != fields:
                raise ValueError('Text-only pool entry must retain the complete eight-field vocabulary')
            rows.append(copy.deepcopy(entry))
            continue
        if set(entry) != {'id', 'pose_id', 'view', 'context', 'avoid_when', 'check'}:
            raise ValueError('Geometry-backed vocabulary needs id, pose_id, view, context, avoid_when and check')
        if any(not _catalog()._text(value) for value in entry.values()):
            raise ValueError('Geometry-backed vocabulary fields must be nonempty single lines')
        base = _validate_snapshot(binding['base'])
        if (binding['base']['mode'] != 'text' or binding['base']['origin'] != 'auto'
                or binding['base']['adaptation_note'] or base.get('selection_policy')
                or (base['group_id'], base['view']) != (entry['pose_id'], entry['view'])):
            raise ValueError('Style pools require an unrestricted matching text definition; no image selection')
        avoid = base['avoid_when']
        if entry['avoid_when'] != 'none' and entry['avoid_when'] != avoid:
            avoid += ' ' + entry['avoid_when']
        rows.append(dict(id=entry['id'], family=base['family'], body=base['body_action'] + ' ' + entry['context'],
                         hands=base['hands'], support=base['support'], views=copy.deepcopy(base['garment_views']),
                         avoid_when=avoid, check=entry['check']))
    return rows


def candidates(*, query='', garment_views=None, include_restricted=False, catalog_path=CATALOG):
    helper = _catalog()
    rows = helper.search(helper.load(catalog_path), query=query)
    if not include_restricted:
        rows = [r for r in rows if 'selection_policy' not in r]
    if garment_views is not None:
        rows = [r for r in rows if set(r['garment_views']) <= set(garment_views)]
    return rows


def selection(pose_id, view, *, mode='text', origin='auto', catalog_path=CATALOG):
    helper = _catalog()
    catalog = helper.load(catalog_path)
    rows = helper.search(catalog, group_id=pose_id, view=view)
    if len(rows) != 1:
        raise ValueError('Select one unambiguous source/group/view')
    entry = rows[0]
    definition = {k: copy.deepcopy(entry[k]) for k in DEFINITION_FIELDS}
    definition.update({k: copy.deepcopy(entry[k]) for k in OPTIONAL_DEFINITION_FIELDS if k in entry})
    result = dict(version=1, definition=definition, definition_sha256=digest(definition),
                  mode=mode, origin=origin, adaptation_note='')
    _validate_snapshot(result)
    restricted = definition.get('selection_policy') == 'user-only'
    if restricted and mode == 'text':
        helper.checked_image(catalog, entry)
        ref = None
    else:
        ref = helper.reference(catalog, pose_id, view, allow_restricted=restricted and origin == 'user' and mode == 'image')
    return result, ref


def _validate_snapshot(value):
    fields = {'version', 'definition', 'definition_sha256', 'mode', 'origin', 'adaptation_note'}
    if not isinstance(value, dict) or set(value) != fields or type(value['version']) is not int or value['version'] != 1:
        raise ValueError('pose_selection requires a version-1 frozen definition, hash, mode, origin and adaptation_note')
    definition = value['definition']
    if (not isinstance(definition, dict) or not DEFINITION_FIELDS <= set(definition)
            or set(definition) - DEFINITION_FIELDS - OPTIONAL_DEFINITION_FIELDS
            or value['definition_sha256'] != digest(definition)):
        raise ValueError('Frozen pose definition changed')
    helper = _catalog()
    if any(not helper._text(definition[k]) for k in DEFINITION_FIELDS - {'garment_views'}):
        raise ValueError('Pose definition text must be nonempty single lines')
    if (definition['source_id'] != 'threadtruth-owned-poses-v1' or definition['usage'] != 'owned'
            or not helper._sha(definition['sha256']) or definition['family'] not in FAMILIES):
        raise ValueError('Unsupported owned pose definition')
    views = definition['garment_views']
    if (not isinstance(views, list) or not views or any(v not in {'front', 'front-side', 'back', 'detail'} for v in views)
            or len(views) != len(set(views))):
        raise ValueError('Pose definition needs distinct required garment views')
    if value['mode'] not in {'text', 'image'} or value['origin'] not in {'auto', 'user'}:
        raise ValueError('Pose selection mode is text/image and origin is auto/user')
    if 'selection_policy' in definition:
        if (not isinstance(definition['selection_policy'], str)
                or definition['selection_policy'] not in helper.SELECTION_POLICIES):
            raise ValueError('Unsupported pose selection policy')
        if value['origin'] != 'user':
            raise ValueError('Restricted pose is user-only; no automatic selection or image attachment')
    note = value['adaptation_note']
    if not isinstance(note, str) or (note and not helper._text(note)) or (note and value['mode'] == 'image'):
        raise ValueError('Only text selection may declare a garment-specific adaptation')
    return definition


def validate_scope(plan, model, output_form):
    if not isinstance(plan, dict) or not any('pose_selection' in s for s in plan.get('looks', []) if isinstance(s, dict)):
        return
    if not model or model.get('subject') not in {'adult model', 'adult female model'}:
        raise ValueError('Owned pose pilot is scoped to adult womenswear; child models are not supported')
    if output_form != 'faceless' and model.get('source_type') not in {'ai', 'new'}:
        raise ValueError('Owned pose pilot supports AI/new portraits or adult faceless delivery; real face angles need separate evidence')


def validate_shot(shot, inventory, *, variety_checks):
    value = shot['pose_selection']
    definition = _validate_snapshot(value)
    if variety_checks != 2:
        raise ValueError('Owned pose selection requires variety_checks: 2; legacy plans are not migrated')
    if shot.get('pose_id') != definition['group_id']:
        raise ValueError('Selected pose_id differs from the frozen library definition')
    if not set(definition['garment_views']) <= set(shot['garment_views']):
        raise ValueError('Selected pose requires garment views backed by this shot: ' + ', '.join(definition['garment_views']))
    if not value['adaptation_note'] and any(shot[k] != definition[k] for k in ('body_action', 'hands', 'support')):
        raise ValueError('Selected body/hands/support changed; text adaptation must be explicit')
    ref = shot.get('pose_reference')
    if value['mode'] == 'text':
        if ref is not None:
            raise ValueError('Text pose selection cannot silently attach an image')
    else:
        if not isinstance(ref, dict) or ref.get('sha256') != definition['sha256']:
            raise ValueError('Image selection must retain its exact selected image hash')
        row = next((r for r in inventory if r.get('sha256') == definition['sha256']), None)
        source = _catalog().validate_reference(row or {})
        if any(source[k] != definition[k] for k in ('source_id', 'group_id', 'view', 'usage')):
            raise ValueError('Pose image source/group/view differs from the frozen selection')
    return definition


def apply(plan, shot_id, pose_id, view, *, mode='text', origin='auto', catalog_path=CATALOG):
    if plan.get('version') != 2:
        raise ValueError('Keep classic v1 plans unchanged; owned selection uses v2')
    result = copy.deepcopy(plan)
    matches = [s for s in result['looks'] if s['shot_id'] == shot_id]
    if len(matches) != 1:
        raise ValueError('Select exactly one existing stable shot_id')
    selected, ref = selection(pose_id, view, mode=mode, origin=origin, catalog_path=catalog_path)
    shot = matches[0]
    definition = selected['definition']
    if not set(definition['garment_views']) <= set(shot['garment_views']):
        raise ValueError('Selected pose is not supported by this shot garment views')
    shot.update({k: definition[k] for k in ('body_action', 'hands', 'support')})
    shot.update(pose_id=pose_id, pose_selection=selected)
    shot.pop('pose_reference', None)
    if mode == 'image':
        shot['pose_reference'] = dict(sha256=ref['sha256'], reason='Selected body, hand and support relations only; preserve the garment and identity references.')
    result['variety_checks'] = 2
    return result, ref if mode == 'image' else None


def recommend(spec, shot_id, *, history=None, limit=5, catalog_path=CATALOG):
    helper = importlib.util.spec_from_file_location('owned_pose_recommend', Path(__file__).with_name('pose_recommend.py'))
    module = importlib.util.module_from_spec(helper)
    helper.loader.exec_module(module)
    return module.recommend(spec, shot_id, history=history, limit=limit, catalog_path=catalog_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    find = sub.add_parser('search')
    find.add_argument('--query', default='')
    find.add_argument('--garment-views', nargs='+')
    find.add_argument('--include-restricted', action='store_true', help='Inspect restricted entries; selection limits still apply')
    rank = sub.add_parser('recommend', help='Read-only goal/history ordering; does not apply or attach a pose')
    rank.add_argument('--spec', type=Path, required=True, help='Existing visual preparation spec JSON')
    rank.add_argument('--shot-id', required=True)
    rank.add_argument('--history', type=Path, help='Optional frozen pose_history JSON or pose_history.py output')
    rank.add_argument('--limit', type=int, default=5)
    choose = sub.add_parser('apply')
    for key in ('plan', 'shot-id', 'pose-id', 'view', 'output'):
        choose.add_argument('--' + key, required=True)
    choose.add_argument('--mode', choices=('text', 'image'), default='text')
    choose.add_argument('--origin', choices=('auto', 'user'), default='user')
    args = parser.parse_args()
    if args.command == 'search':
        print(json.dumps(candidates(query=args.query, garment_views=args.garment_views,
                                    include_restricted=args.include_restricted), ensure_ascii=False, indent=2))
    elif args.command == 'recommend':
        frozen = json.loads(args.history.read_text()) if args.history else None
        if isinstance(frozen, dict) and 'pose_history' in frozen:
            frozen = frozen['pose_history']
        print(json.dumps(recommend(json.loads(args.spec.read_text()), args.shot_id,
                                   history=frozen, limit=args.limit), ensure_ascii=False, indent=2))
    else:
        plan, ref = apply(json.loads(Path(args.plan).read_text()), args.shot_id, args.pose_id, args.view, mode=args.mode, origin=args.origin)
        with Path(args.output).open('x') as output:
            json.dump(dict(shot_plan=plan, reference=ref), output, ensure_ascii=False, indent=2)
            output.write('\n')


if __name__ == '__main__':
    main()
