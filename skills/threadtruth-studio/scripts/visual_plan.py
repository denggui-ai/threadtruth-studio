"""Frozen visual decisions shared by native and web requests; no live-library reads.

Identity, body/head/gaze, garment coverage and numbered framing remain owned by
model_reference, real_face_plan and shot_plan. This module owns visual expression.
"""
import copy
import hashlib
import json
import re

BEGIN = '[Task visual plan]'
END = '[/Task visual plan]'
OBJECTIVES = ('product-display', 'styled-editorial', 'art-campaign')
MEDIA = ('photography', 'illustration', 'mixed-media')
OUTPUT_FORMS = ('human', 'faceless', 'flat-lay', 'hanger', 'mannequin')
FIELDS = {'version', 'objective', 'output_medium', 'output_form', 'style', 'garment', 'styling',
          'photography', 'art', 'negatives', 'shots'}
RESERVED = re.compile(r'\[(?:/?Task |/?Current model)|^\s*(?:POSE|Shot)\s+[1-6]\s*:', re.I)
V2_RESERVED = re.compile(r'^\s*(?:POSE|Shot)\s+[7-9]\s*:', re.I)
V2_BODY = re.compile(r'\b(?:body (?:action|pose|orientation)|hand (?:position|placement))\b', re.I)
# Known bypasses of the existing identity/framing contracts; this is not a prose
# classifier. Semantic/source review remains necessary for natural-language facts.
OWNED = re.compile(r'\b(?:gaze|eyeline|off[- ](?:lens|camera|frame)|head (?:turn|direction|view)|near[- ]front'
                   r'|full[- ]body|half[- ]body|knee[- ]up|(?:change|replace|copy) (?:the )?(?:face|identity))\b'
                   r'|(?:全身|半身)(?:取景|构图)|(?:正脸)?直视镜头|替换身份|换脸', re.I)


def object_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _got(value):
    """Describe an offending value briefly for validation messages (type or short repr)."""
    if value is None or isinstance(value,(bool,int,float)):return repr(value)
    if isinstance(value,str):return repr(value) if len(value)<=40 else repr(value[:37]+'...')
    name=type(value).__name__
    try:return f'{name} of {len(value)}'
    except TypeError:return name


def _line(value, label, *, empty=False, owned=False, v2=False):
    if (not isinstance(value, str) or (not empty and not value.strip()) or len(value) > 1200
            or any(ord(c) < 32 or ord(c) == 127 for c in value) or RESERVED.search(value)
            or (v2 and V2_RESERVED.search(value))):
        raise ValueError(label + ' must be a short single-line visual statement without managed markers')
    if owned and (OWNED.search(value) or (v2 and V2_BODY.search(value))):
        raise ValueError(label + ' cannot override identity, head/gaze or shot framing')


def _lines(value, label, *, required=False, owned=False, v2=False):
    if not isinstance(value, list) or len(value) > 24 or (required and not value):
        raise ValueError(label + ' must be a list of visual statements')
    for item in value:
        _line(item, label, owned=owned, v2=v2)


def _component(value):
    if not isinstance(value, dict) or set(value) != {'id', 'version', 'sha256', 'snapshot'}:
        raise ValueError('A visual component freezes id, version, sha256 and snapshot')
    _line(value['id'], 'Component id')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}',value['id']):
        raise ValueError('Visual component ids must be stable lowercase slugs')
    if not (type(value['version']) is int and value['version'] > 0 or
            isinstance(value['version'], str) and value['version'].strip()):
        raise ValueError('A visual component needs an explicit version')
    if not isinstance(value['snapshot'], dict) or not value['snapshot']:
        raise ValueError('A visual component requires the resolved source snapshot')
    try:
        encoded = json.dumps(value['snapshot'], ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValueError('Component snapshot must be finite JSON data') from error
    if len(encoded) > 100000 or object_hash(value['snapshot']) != value['sha256']:
        raise ValueError('Frozen visual component hash does not match its snapshot')
    if value['snapshot'].get('id', value['id']) != value['id']:
        raise ValueError('Visual component id conflicts with its frozen snapshot')
    if value['snapshot'].get('version',value['version']) != value['version']:
        raise ValueError('Visual component version conflicts with its frozen snapshot')


def shot_bindings(shot_plan):
    """Read stable active bindings; garment/body validation stays in shot_plan."""
    if not isinstance(shot_plan, dict) or shot_plan.get('version') != 2:
        raise ValueError('Stable visual bindings require a version-2 shot plan')
    looks = shot_plan.get('looks')
    selected = shot_plan.get('selected_shot_ids')
    if not isinstance(looks, list) or len(looks) not in (1, 6, 9):
        raise ValueError('A shot plan retains its complete logical series')
    bindings = []
    for slot, shot in enumerate(looks, 1):
        if (not isinstance(shot, dict) or shot.get('slot') != slot or type(shot.get('slot')) is not int
                or not isinstance(shot.get('shot_id'), str)
                or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}', shot['shot_id'])):
            raise ValueError('A shot binding needs its stable slot and shot_id')
        bindings.append(dict(slot=slot, shot_id=shot['shot_id']))
    ids = [shot['shot_id'] for shot in bindings]
    if (len(set(ids)) != len(ids) or not isinstance(selected, list)
            or len(selected) not in (1, len(ids))
            or any(not isinstance(identifier, str) or identifier not in ids for identifier in selected)
            or len(set(selected)) != len(selected)
            or (len(selected) > 1 and selected != ids)):
        raise ValueError('Active shots select one source shot or the ordered complete series')
    by_id = {shot['shot_id']: shot for shot in bindings}
    return [copy.deepcopy(by_id[identifier]) for identifier in selected]


def validate(plan, inventory, *, context, count, identity=True, shot_plan=None):
    """Validate resolved visual fields against original garment hashes and context."""
    if (not isinstance(plan, dict) or set(plan) - {'culture_profile', 'persona', 'persona_model_sha256'} != FIELDS
            or type(plan['version']) is not int or plan['version'] not in (1, 2)):
        raise ValueError('Visual plan requires complete version-1 or version-2 structured fields')
    v2 = plan['version'] == 2
    if plan['objective'] not in OBJECTIVES or plan['output_medium'] not in MEDIA:
        raise ValueError('Unknown visual objective or output medium')
    if plan['output_form'] not in OUTPUT_FORMS or plan['output_form'] != context['output_form']:
        raise ValueError('Visual output_form must match one of the five frozen task presentations')
    if bool(identity) != (plan['output_form'] in ('human', 'faceless')):
        raise ValueError('Human/faceless presentations retain identity gates; flat-lay/hanger/mannequin are non-portrait')
    style = plan['style']
    if not isinstance(style, dict) or set(style) != {'primary', 'supporting', 'fusion_note'}:
        raise ValueError('Style selection requires primary, supporting and fusion_note')
    _component(style['primary'])
    if style['primary']['id'] != context['style']:
        raise ValueError('Primary visual style must match the frozen task context')
    if not isinstance(style['supporting'], list) or len(style['supporting']) > 3:
        raise ValueError('At most three explicitly selected supporting styles are allowed')
    ids = {style['primary']['id']}
    for component in style['supporting']:
        _component(component)
        if component['id'] in ids:
            raise ValueError('Visual style components must be distinct')
        ids.add(component['id'])
    _line(style['fusion_note'], 'Fusion approval note', empty=not style['supporting'],owned=True,v2=v2)
    if not style['supporting'] and style['fusion_note']:
        raise ValueError('A fusion note requires explicitly selected supporting styles')
    if 'culture_profile' in plan:
        _component(plan['culture_profile'])
    if ('persona' in plan) != ('persona_model_sha256' in plan):
        raise ValueError('Style persona and its resolving model hash are frozen together')
    if 'persona' in plan:
        if not isinstance(plan['persona'], str) or not plan['persona'].strip():
            raise ValueError('Style persona must be a non-empty statement or omitted')
        if plan['output_form'] != 'human':
            raise ValueError('Style persona applies only to human presentations')
        if not isinstance(plan['persona_model_sha256'], str) or not re.fullmatch(r'[a-f0-9]{64}', plan['persona_model_sha256']):
            raise ValueError('Style persona requires the exact resolving model hash')
        _line(plan['persona'], 'Style persona', owned=True, v2=v2)
    garment = plan['garment']
    if not isinstance(garment, dict) or set(garment) != {'description', 'keep', 'source_sha256s'}:
        raise ValueError('Garment facts require description, keep and original source_sha256s')
    _line(garment['description'], 'Source-backed garment description', v2=v2)
    _lines(garment['keep'], 'Source-backed garment preservation', required=True, v2=v2)
    if not isinstance(inventory,list) or not inventory or any(not isinstance(r,dict) for r in inventory):
        raise ValueError('Visual preparation needs an explicit source inventory')
    originals = {r['sha256'] for r in inventory if r.get('role') == 'garment-source'}
    if any(not isinstance(h,str) or not re.fullmatch(r'[a-f0-9]{64}',h) for h in originals):
        raise ValueError('Original garment inventory requires exact lowercase SHA256 hashes')
    hashes = garment['source_sha256s']
    if (not isinstance(hashes, list) or not hashes or any(not isinstance(h, str) or h not in originals for h in hashes)
            or len(set(hashes)) != len(hashes)):
        raise ValueError('Visual garment facts must bind distinct original garment hashes')
    _lines(plan['styling'], 'Allowed styling', owned=True, v2=v2)
    photography = plan['photography']
    if not isinstance(photography, dict) or set(photography) != {'scene', 'lighting', 'composition', 'palette'}:
        raise ValueError('Visual photography requires scene, lighting, composition and palette')
    for key, value in photography.items():
        _line(value, 'Visual ' + key, owned=True, v2=v2)
    art = plan['art']
    if not isinstance(art, dict) or set(art) != {'direction', 'techniques', 'limits'}:
        raise ValueError('Art expression requires direction, techniques and limits')
    _line(art['direction'], 'Art direction', owned=True, v2=v2)
    _lines(art['techniques'], 'Art techniques', owned=True, v2=v2)
    _lines(art['limits'], 'Art limits', required=True, owned=True, v2=v2)
    _lines(plan['negatives'], 'Visual exclusions', owned=True, v2=v2)
    allowed_counts = (1, 6) if plan['version'] == 1 else (1, 6, 9)
    if type(count) is not int or count not in allowed_counts or not isinstance(plan['shots'], list) or len(plan['shots']) != count:
        raise ValueError('Visual shot count must match the task or declared preview cells')
    if plan['version'] == 1 and count==6 and context['first_pose']!=1:
        raise ValueError('Six visual presentations start from the actual first numbered presentation')
    if plan['version'] == 2 and not identity:
        raise ValueError('Version-2 garment-driven slots apply to human/faceless presentations')
    if plan['version'] == 2 and count > 1 and context['first_pose'] != 1:
        raise ValueError('A complete visual series starts with its stable first source slot')
    seen_ids = set()
    for i, shot in enumerate(plan['shots'], 1):
        if plan['version'] == 1:
            pose = i if count == 6 else context['first_pose']
            if (not isinstance(shot, dict) or set(shot) != {'slot', 'pose', 'scene', 'lighting', 'composition'}
                    or type(shot['slot']) is not int or shot['slot'] != i
                    or shot['pose'] != pose or type(shot['pose']) is not type(pose)):
                raise ValueError('Visual shots preserve actual numbered/custom presentation and consecutive slots')
        else:
            slot = i if count > 1 else context['first_pose']
            path = f'visual_plan.shots[{i - 1}]'
            required_shot = {'slot', 'shot_id', 'scene', 'lighting', 'composition'}
            hint = ('; every element needs exactly slot, shot_id, scene, lighting, composition. '
                    'visual_library prepare overrides.shots replaces ALL generated shots, so either omit overrides.shots '
                    'or give the complete list copied from a prepare run without it')
            if not isinstance(shot, dict):
                raise ValueError(path + ' must be an object (Visual v2 shots preserve stable source slots and distinct shot_id values); got '
                                 + _got(shot) + hint)
            if set(shot) != required_shot:
                raise ValueError(path + ' has the wrong keys (Visual v2 shots preserve stable source slots and distinct shot_id values); missing: '
                                 + (', '.join(sorted(required_shot - set(shot))) or 'none') + '; unexpected: '
                                 + (', '.join(sorted(set(shot) - required_shot)) or 'none') + hint)
            if type(shot['slot']) is not int or shot['slot'] != slot or slot not in range(1, 10):
                raise ValueError(path + '.slot must be ' + _got(slot) + ' (stable source slot in shot_plan order); got ' + _got(shot['slot']))
            if not isinstance(shot['shot_id'], str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}', shot['shot_id']):
                raise ValueError(path + '.shot_id must be 1-80 letters, digits, "_", "." or "-" starting with a letter or digit; got '
                                 + _got(shot['shot_id']))
            if shot['shot_id'] in seen_ids:
                raise ValueError(path + '.shot_id must be distinct; got duplicate ' + _got(shot['shot_id']))
            seen_ids.add(shot['shot_id'])
        for key in ('scene', 'lighting', 'composition'):
            _line(shot[key], 'Per-shot ' + key, owned=True, v2=v2)
    if shot_plan is not None:
        if not isinstance(shot_plan, dict) or shot_plan.get('version') not in (1, 2):
            raise ValueError('Visual binding requires a supported shot-plan version')
        if shot_plan['version'] != plan['version']:
            raise ValueError('Visual and garment shot-plan versions must agree')
    if shot_plan is not None and shot_plan['version'] == 2:
        actual = [dict(slot=s['slot'], shot_id=s['shot_id']) for s in plan['shots']]
        expected = shot_bindings(shot_plan)
        if actual != expected:
            at = next((k for k, (a, e) in enumerate(zip(actual, expected)) if a != e), min(len(actual), len(expected)))
            raise ValueError('visual_plan.shots[' + str(at) + '] must bind shot_plan selected shot '
                             + (json.dumps(expected[at], sort_keys=True) if at < len(expected) else 'none (too many shots)')
                             + ' (Visual and garment shot plans must bind the same active shot IDs and source slots); got '
                             + (json.dumps(actual[at], sort_keys=True) if at < len(actual) else 'none (missing shot)'))
    return copy.deepcopy(plan)


def render(plan, look=None):
    """Render only frozen resolved values. look is a task slot, None selects all."""
    if look is not None and (type(look) is not int or not 1<=look<=len(plan['shots'])):
        raise ValueError('Unknown visual presentation slot')
    style = plan['style']
    rows = [BEGIN, 'Visual objective: ' + plan['objective'] + '.',
            'Output medium: ' + plan['output_medium'] + '.',
            'Output presentation: ' + plan['output_form'] + '.',
            'Primary style: ' + style['primary']['id'] + '.',
            'Source-backed garment: ' + plan['garment']['description'],
            'Preserve original garment facts: ' + '; '.join(plan['garment']['keep']) + '.']
    if plan['output_form']=='faceless':
        rows.append('Keep the face outside the image or fully obscured; preserve supported body proportions and garment details. Do not introduce a visible face.')
    elif plan['output_form'] in ('flat-lay','hanger','mannequin'):
        rows.append('Non-portrait garment display: no live person, face, gaze or human pose instructions. Use garment arrangements for the numbered presentations.')
    if style['supporting']:
        rows += ['Supporting styles: ' + ', '.join(x['id'] for x in style['supporting']) + '.',
                 'Explicit fusion scope: ' + style['fusion_note']]
    if 'culture_profile' in plan:
        rows += ['Cultural form profile: ' + plan['culture_profile']['id'] + '.',
                 'Preserve source-supported garment form and construction; do not invent a dynasty, ritual meaning, pattern or accessory.']
    for item in plan['styling']:
        rows.append('Allowed styling: ' + item)
    for key in ('scene', 'lighting', 'composition', 'palette'):
        rows.append('Shared ' + key + ': ' + plan['photography'][key])
    rows += ['Art direction: ' + plan['art']['direction']]
    rows += ['Art technique: ' + item for item in plan['art']['techniques']]
    rows += ['Art limit: ' + item for item in plan['art']['limits']]
    if plan.get('persona'):
        rows.append('Style persona (yields to the declared model conditions): ' + plan['persona'])
    cells = plan['shots'] if look is None else [plan['shots'][look - 1]]
    for shot in cells:
        heading = (f"Visual slot {shot['slot']} (shot {shot['shot_id']}):" if plan['version'] == 2
                   else f"Visual slot {shot['slot']} (presentation {shot['pose']}):")
        rows += [heading,
                 'Scene: ' + shot['scene'], 'Lighting: ' + shot['lighting'],
                 'Composition: ' + shot['composition']]
    rows += ['Exclude: ' + item for item in plan['negatives']]
    rows += ['Garment facts, original identity, real-person view coverage and approved shot framing remain authoritative over visual expression.',
             'Create image artwork without added branding, poster copy, slogans, captions or extra text layouts. Preserve existing source garment marks and lettering; a direction preview may retain its required preview-only label.', END]
    return '\n'.join(rows)


def compile_prompt(plan, look=None):
    return render(plan, look) + '\n'


def apply(prompt, plan, look=None):
    canonical = render(plan, look)
    if BEGIN in prompt or END in prompt:
        if prompt.count(BEGIN) != 1 or prompt.count(END) != 1 or canonical not in prompt:
            raise ValueError('Frozen visual plan block conflicts with the current plan')
        return prompt
    return prompt.rstrip() + '\n' + canonical + '\n'


def check_prompt(prompt, plan, look=None, *, managed_blocks=()):
    """V2 frozen prose is compiled; legacy prose cannot smuggle stale visual rules."""
    canonical = render(plan, look)
    apply(prompt, plan, look)
    if prompt.count(canonical) != 1:
        raise ValueError('Visual-plan prompts must be compiled from the frozen structured plan')
    remainder = prompt.replace(canonical, '', 1)
    for block in managed_blocks:
        remainder = remainder.replace(block, '', 1)
    if remainder.strip():
        raise ValueError('Visual-plan prompts cannot contain ungoverned prose; update structured fields and recompile')


def subset(plan, pose):
    """Select a presentation without changing a v2 source slot or stable ID."""
    result = copy.deepcopy(plan)
    if plan['version'] == 2:
        selected = [shot for shot in result['shots'] if shot['slot'] == pose or shot['shot_id'] == pose]
    else:
        selected = [shot for shot in result['shots'] if shot['pose'] == pose]
    if len(selected) != 1:
        raise ValueError('Select one actual preview presentation')
    if plan['version'] == 1:
        selected[0]['slot'] = 1
    result['shots'] = selected
    return result


def bind_shots(plan, shot_plan):
    """Select already frozen photography by stable shot ID; never invent slots."""
    if plan.get('version') != 2:
        raise ValueError('Stable shot binding requires a version-2 visual plan')
    bindings = shot_bindings(shot_plan)
    by_id = {shot['shot_id']: shot for shot in plan['shots']}
    if len(by_id) != len(plan['shots']):
        raise ValueError('Duplicate visual shot IDs')
    result = copy.deepcopy(plan)
    result['shots'] = []
    for binding in bindings:
        shot = by_id.get(binding['shot_id'])
        if shot is None or shot['slot'] != binding['slot']:
            raise ValueError('No frozen photography exists for the selected source shot')
        result['shots'].append(copy.deepcopy(shot))
    return result
