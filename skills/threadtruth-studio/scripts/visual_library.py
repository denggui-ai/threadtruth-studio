#!/usr/bin/env python3
"""Prepare frozen visual plans from selected runtime cards. No image/network calls."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import re
import sys
import unicodedata

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
INDEX = 'references/visual-library/index.json'


def _visual():
    spec = importlib.util.spec_from_file_location('library_visual_plan', Path(__file__).with_name('visual_plan.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read(root, relative):
    if (not isinstance(relative, str) or not relative or Path(relative).is_absolute()
            or '..' in Path(relative).parts):
        raise ValueError('Library paths must stay relative to the runtime root')
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('Library source is missing or outside the runtime root')
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('Library source must be a JSON object')
    return data


def index(root=ROOT):
    data = _read(root, INDEX)
    entries = data.get('entries')
    if not isinstance(entries, list) or not entries:
        raise ValueError('Execution index needs entries')
    ids = []
    for item in entries:
        if (not isinstance(item, dict) or not isinstance(item.get('id'), str)
                or not re.fullmatch(r'[a-z][a-z0-9-]{1,79}', item['id'])
                or not isinstance(item.get('name'), str) or not item['name'].strip()
                or not isinstance(item.get('card'), str)):
            raise ValueError('Execution entries require stable id, name and card path')
        ids.append(item['id'])
    if len(ids) != len(set(ids)):
        raise ValueError('Execution entry ids must be unique')
    return data


def card(entry_id, root=ROOT):
    found = [entry for entry in index(root)['entries'] if entry['id'] == entry_id]
    if len(found) != 1:
        raise ValueError('Choose an execution entry id from the index; knowledge names are not file paths')
    data = _read(root, found[0]['card'])
    if data.get('id') != entry_id or not data.get('version'):
        raise ValueError('Card identity/version does not match its execution entry')
    return data


def component(snapshot):
    visual = _visual()
    result = dict(id=snapshot['id'], version=snapshot['version'],
                  sha256=visual.object_hash(snapshot), snapshot=copy.deepcopy(snapshot))
    visual._component(result)
    return result


def route(query, root=ROOT):
    """Bounded explicit selection helper, not a general intent classifier.

    Keeps evidence spans and surfaces uncertain multi-style intent. The agent
    still reviews garment facts, cultural terms and contextual language.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError('Provide the actual user query')
    normalized = unicodedata.normalize('NFKC', query).casefold()
    data = index(root)
    occurrences = []
    for entry in data['entries']:
        for term in entry['aliases']:
            token = unicodedata.normalize('NFKC', term).casefold().strip()
            parts = [part for part in re.split(r'[\s_\-‐‑‒–—]+', token) if part]
            if not parts:
                continue
            pattern = r'[\s_\-‐‑‒–—]*'.join(re.escape(part) for part in parts)
            if re.match('[a-z0-9]', parts[0][0]):
                pattern = r'(?<![a-z0-9])' + pattern
            if re.match('[a-z0-9]', parts[-1][-1]):
                pattern += r'(?![a-z0-9])'
            for match in re.finditer(pattern, normalized):
                # A regional interior label is not an apparel choice.
                if token in ('美式', '美式复古') and re.match(r'(?:的)?(?:厨房|客厅|背景|布景|房间|公寓)', normalized[match.end():]):
                    continue
                occurrences.append(dict(id=entry['id'], term=term,
                                        start=match.start(), end=match.end()))
    matches = [item for item in occurrences if not any(
        other['start'] <= item['start'] and item['end'] <= other['end']
        and (other['end'] - other['start']) > (item['end'] - item['start'])
        for other in occurrences)]
    unique = {(item['id'], item['start'], item['end']): item for item in matches}
    matches = sorted(unique.values(), key=lambda item: (item['start'], item['end'], item['id']))
    excluded = []
    positive = []
    for item in matches:
        prefix = normalized[:item['start']]
        direct_negative = re.search(r'(?:不要|不用|不选|排除|别用|not|without|exclude)\s*(?:选择|采用|使用|走|use)?\s*$', prefix)
        coordinated_negative = excluded and re.fullmatch(
            r'\s*(?:和|及|、|或|and|or)\s*', normalized[excluded[-1]['end']:item['start']])
        # Explicit double negation needs human/agent interpretation, not a
        # guessed affirmative or a discarded direction.
        double_negative = direct_negative and re.search(r'(?:不是|并非|not)\s*$', prefix[:direct_negative.start()])
        if double_negative:
            return dict(decision='hold', entry_ids=sorted({m['id'] for m in matches}),
                        matches=matches, excluded=[], reason='Negation scope needs interpretation')
        (excluded if direct_negative or coordinated_negative else positive).append(item)
    positive = list({(item['id'], re.sub(r'[\s_\-‐‑‒–—]', '', unicodedata.normalize('NFKC', item['term']).casefold())): item
                     for item in reversed(positive)}.values())[::-1]
    ids = list(dict.fromkeys(item['id'] for item in positive))
    decision = 'none' if not ids else ('route' if len(ids) == 1 else 'hold')
    primary = ids[0] if len(ids) == 1 else None
    if len(ids) > 1:
        if re.search(r'比较|对比|区别|分别|各(?:出|做|生成)|\b(?:compare|versus)\b', normalized):
            decision = 'compare'
        else:
            primary_ids = {item['id'] for item in positive if
                           re.match(r'\s*(?:为主|作主风格|作为主风格)', normalized[item['end']:])
                           or re.search(r'(?:主风格|主要风格|primary)\s*[:：]?\s*$', normalized[:item['start']])}
            if len(primary_ids) == 1:
                primary = primary_ids.pop()
                decision = 'fusion'
    result = dict(decision=decision, entry_ids=ids, primary=primary,
                  matches=positive, excluded=excluded)
    navigation = []
    for item in data.get('navigation', []):
        label = unicodedata.normalize('NFKC', item['label']).casefold()
        for found in re.finditer(re.escape(label), normalized):
            covered = any(hit['start'] <= found.start() and found.end() <= hit['end'] for hit in matches)
            bare_tail = re.match(r'\s*(?:$|和|与|、|风格?$)', normalized[found.end():])
            negative = re.search(r'(?:不要|不用|不选|排除|别用)\s*$', normalized[:found.start()])
            if not covered and bare_tail and not negative:
                navigation.append(item)
                break
    if navigation:
        result.update(decision='hold', primary=None, navigation=navigation)
    return result


def prepare(spec, root=ROOT):
    """Resolve defaults once; the task subsequently uses only this frozen plan.

    Actual image decoding, inventory roles, consent and generation authority stay
    in the task ledger. This local preparation does not grant or consume a call.
    """
    allowed = {'entry_id', 'garment', 'inventory', 'count', 'first_pose', 'objective', 'output_form',
               'output_medium', 'supporting', 'fusion_note', 'overrides', 'culture_profile'}
    if not isinstance(spec, dict) or set(spec) - allowed:
        raise ValueError('Unknown visual preparation fields')
    primary = card(spec['entry_id'], root)
    objective = spec.get('objective', primary.get('default_objective',
                         'product-display' if spec['entry_id'] == 'ecommerce-studio' else 'styled-editorial'))
    support = primary.get('purpose_support', [])
    if objective not in support:
        raise ValueError('The selected entry does not declare this expression objective')
    medium = spec.get('output_medium', primary.get('medium', 'photography'))
    if medium != primary.get('medium', 'photography'):
        raise ValueError('Choose an entry for the requested medium instead of relabeling a photography card')
    supporting_ids = spec.get('supporting', [])
    if not isinstance(supporting_ids, list):
        raise ValueError('Supporting entries must be an explicit list')
    supporting = [component(card(entry_id, root)) for entry_id in supporting_ids]
    count = spec.get('count', 1)
    output_form = spec.get('output_form', 'human')
    pose = spec.get('first_pose', 1)
    photography = copy.deepcopy(primary['photography'])
    art = copy.deepcopy(primary['art'])
    overrides = spec.get('overrides', {})
    if not isinstance(overrides, dict) or set(overrides) - {'photography', 'art', 'styling', 'negatives', 'shots'}:
        raise ValueError('Resolve changes in photography/art/styling/negatives/shots only')
    for key, baseline in [('photography', photography), ('art', art)]:
        if key in overrides:
            if not isinstance(overrides[key], dict) or set(overrides[key]) - set(baseline):
                raise ValueError('Unknown ' + key + ' override')
            baseline.update(copy.deepcopy(overrides[key]))
    if type(count) is not int or count not in (1, 6):
        raise ValueError('Prepare one independent image or six preview/delivery presentations')
    shots = [dict(slot=i, pose=i if count == 6 else pose,
                  **{key: photography[key] for key in ('scene', 'lighting', 'composition')})
             for i in range(1, count + 1)]
    plan = dict(version=1, objective=objective, output_medium=medium, output_form=output_form,
                style=dict(primary=component(primary), supporting=supporting,
                           fusion_note=spec.get('fusion_note', '')),
                garment=copy.deepcopy(spec['garment']),
                styling=copy.deepcopy(overrides.get('styling', [])),
                photography=photography, art=art,
                negatives=copy.deepcopy(overrides.get('negatives', primary.get('negatives', []))),
                shots=copy.deepcopy(overrides.get('shots', shots)))
    if spec.get('culture_profile') is not None:
        plan['culture_profile'] = component(spec['culture_profile'])
    elif primary.get('culture_profile'):
        plan['culture_profile'] = component(primary['culture_profile'])
    return _visual().validate(plan, spec['inventory'],
                              context=dict(style=spec['entry_id'], first_pose=pose, output_form=output_form),
                              count=count, identity=output_form in ('human', 'faceless'))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('list', help='Read the execution index; no preparation or generation')
    show = sub.add_parser('show', help='Read one selected card')
    show.add_argument('entry_id')
    routing = sub.add_parser('route', help='Inspect explicit selection/comparison/fusion candidates; no generation')
    routing.add_argument('query')
    build = sub.add_parser('prepare', help='Freeze one actual garment/visual plan without generating')
    build.add_argument('--spec', required=True, type=Path)
    build.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == 'list':
            result = index()
        elif args.command == 'show':
            result = card(args.entry_id)
        elif args.command == 'route':
            result = route(args.query)
        else:
            result = prepare(json.loads(args.spec.read_text(encoding='utf-8')))
            # Never overwrite another frozen plan as a side effect of preparation.
            with args.output.open('x', encoding='utf-8') as handle:
                handle.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
            result = dict(status='prepared', path=str(args.output.resolve()),
                          visual_plan_sha256=_visual().object_hash(result), image_calls=0)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (KeyError, TypeError, ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
