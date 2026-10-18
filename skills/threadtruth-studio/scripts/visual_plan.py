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
# Known bypasses of the existing identity/framing contracts; this is not a prose
# classifier. Semantic/source review remains necessary for natural-language facts.
OWNED = re.compile(r'\b(?:gaze|eyeline|off[- ](?:lens|camera|frame)|head (?:turn|direction|view)|near[- ]front'
                   r'|full[- ]body|half[- ]body|knee[- ]up|(?:change|replace|copy) (?:the )?(?:face|identity))\b'
                   r'|(?:全身|半身)(?:取景|构图)|(?:正脸)?直视镜头|替换身份|换脸', re.I)


def object_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _line(value, label, *, empty=False, owned=False):
    if (not isinstance(value, str) or (not empty and not value.strip()) or len(value) > 1200
            or any(ord(c) < 32 or ord(c) == 127 for c in value) or RESERVED.search(value)):
        raise ValueError(label + ' must be a short single-line visual statement without managed markers')
    if owned and OWNED.search(value):
        raise ValueError(label + ' cannot override identity, head/gaze or shot framing')


def _lines(value, label, *, required=False, owned=False):
    if not isinstance(value, list) or len(value) > 24 or (required and not value):
        raise ValueError(label + ' must be a list of visual statements')
    for item in value:
        _line(item, label, owned=owned)


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


def validate(plan, inventory, *, context, count, identity=True):
    """Validate resolved visual fields against original garment hashes and context."""
    if (not isinstance(plan, dict) or set(plan) - {'culture_profile'} != FIELDS
            or type(plan['version']) is not int or plan['version'] != 1):
        raise ValueError('Visual plan requires the complete version-1 structured fields')
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
    _line(style['fusion_note'], 'Fusion approval note', empty=not style['supporting'],owned=True)
    if not style['supporting'] and style['fusion_note']:
        raise ValueError('A fusion note requires explicitly selected supporting styles')
    if 'culture_profile' in plan:
        _component(plan['culture_profile'])
    garment = plan['garment']
    if not isinstance(garment, dict) or set(garment) != {'description', 'keep', 'source_sha256s'}:
        raise ValueError('Garment facts require description, keep and original source_sha256s')
    _line(garment['description'], 'Source-backed garment description')
    _lines(garment['keep'], 'Source-backed garment preservation', required=True)
    if not isinstance(inventory,list) or not inventory or any(not isinstance(r,dict) for r in inventory):
        raise ValueError('Visual preparation needs an explicit source inventory')
    originals = {r['sha256'] for r in inventory if r.get('role') == 'garment-source'}
    if any(not isinstance(h,str) or not re.fullmatch(r'[a-f0-9]{64}',h) for h in originals):
        raise ValueError('Original garment inventory requires exact lowercase SHA256 hashes')
    hashes = garment['source_sha256s']
    if (not isinstance(hashes, list) or not hashes or any(not isinstance(h, str) or h not in originals for h in hashes)
            or len(set(hashes)) != len(hashes)):
        raise ValueError('Visual garment facts must bind distinct original garment hashes')
    _lines(plan['styling'], 'Allowed styling', owned=True)
    photography = plan['photography']
    if not isinstance(photography, dict) or set(photography) != {'scene', 'lighting', 'composition', 'palette'}:
        raise ValueError('Visual photography requires scene, lighting, composition and palette')
    for key, value in photography.items():
        _line(value, 'Visual ' + key, owned=True)
    art = plan['art']
    if not isinstance(art, dict) or set(art) != {'direction', 'techniques', 'limits'}:
        raise ValueError('Art expression requires direction, techniques and limits')
    _line(art['direction'], 'Art direction', owned=True)
    _lines(art['techniques'], 'Art techniques', owned=True)
    _lines(art['limits'], 'Art limits', required=True, owned=True)
    _lines(plan['negatives'], 'Visual exclusions', owned=True)
    if type(count) is not int or count not in (1, 6) or not isinstance(plan['shots'], list) or len(plan['shots']) != count:
        raise ValueError('Visual shot count must match the task or six preview cells')
    if count==6 and context['first_pose']!=1:
        raise ValueError('Six visual presentations start from the actual first numbered presentation')
    for i, shot in enumerate(plan['shots'], 1):
        pose = i if count == 6 else context['first_pose']
        if (not isinstance(shot, dict) or set(shot) != {'slot', 'pose', 'scene', 'lighting', 'composition'}
                or type(shot['slot']) is not int or shot['slot'] != i
                or shot['pose'] != pose or type(shot['pose']) is not type(pose)):
            raise ValueError('Visual shots preserve actual numbered/custom presentation and consecutive slots')
        for key in ('scene', 'lighting', 'composition'):
            _line(shot[key], 'Per-shot ' + key, owned=True)
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
    cells = plan['shots'] if look is None else [plan['shots'][look - 1]]
    for shot in cells:
        rows += [f"Visual slot {shot['slot']} (presentation {shot['pose']}):",
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
    """Freeze one actual presentation from an accepted preview's six cells."""
    result = copy.deepcopy(plan)
    selected = [shot for shot in result['shots'] if shot['pose'] == pose]
    if len(selected) != 1:
        raise ValueError('Select one actual preview presentation')
    selected[0]['slot'] = 1
    result['shots'] = selected
    return result
