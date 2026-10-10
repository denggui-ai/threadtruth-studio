"""Development-only per-shot photography choices; never a generation authority."""
import copy
import unicodedata

STUDIO = 'low-distraction white or light-gray studio background'
SPEC_FIELDS = {'mode', 'studio_prefix', 'shots'}
SHOT_FIELDS = {'pose', 'scene_index', 'framing', 'support', 'gaze'}
FRAMINGS = {'full-body', 'knee-up', 'half-body'}


def studio_scene(declared):
    # Retain the registered ecommerce pilot's explicit studio floor/wall/support
    # variants. Other pack locations cannot leak into a forced studio position.
    if declared.startswith(('seamless light-gray studio', 'same studio with ')):
        return declared
    return STUDIO


def _line(value, name):
    if (not isinstance(value, str) or not value.strip() or len(value.strip()) > 240
            or any(unicodedata.category(c).startswith('C') or c in '\u2028\u2029' for c in value)):
        raise ValueError(name + ' must be a nonempty single line of at most 240 characters')
    return value.strip()


def validate(value, default_mode):
    if value is None:
        value = {}
    if not isinstance(value, dict) or set(value) - SPEC_FIELDS:
        raise ValueError('photography spec permits only mode, studio_prefix and shots')
    mode = value.get('mode', default_mode)
    if not isinstance(mode, str) or mode not in {'B', 'C', 'D'}:
        raise ValueError('photography mode must be B, C or D')
    prefix = value.get('studio_prefix', 2) if mode == 'D' else 6 if mode == 'B' else 0
    if 'studio_prefix' in value and mode != 'D':
        raise ValueError('studio_prefix applies only to D mode')
    if mode == 'D' and (type(prefix) is not int or prefix not in {2, 3}):
        raise ValueError('D studio_prefix must be 2 or 3')
    shots = value.get('shots', [])
    if not isinstance(shots, list) or len(shots) > 6:
        raise ValueError('photography shots must be a list of at most six choices')
    normalized = {}
    for row in shots:
        if not isinstance(row, dict) or set(row) - SHOT_FIELDS:
            raise ValueError('photography shot contains unsupported fields')
        pose = row.get('pose')
        if type(pose) is not int or not 1 <= pose <= 6 or pose in normalized:
            raise ValueError('photography pose must be a distinct existing mother numbered 1-6')
        selected = copy.deepcopy(row)
        if 'scene_index' in row:
            if type(row['scene_index']) is not int or not 1 <= row['scene_index'] <= 6:
                raise ValueError('scene_index must be 1-6')
            if pose <= prefix:
                raise ValueError('studio positions cannot select a location scene')
        if 'framing' in row and (not isinstance(row['framing'], str) or row['framing'] not in FRAMINGS):
            raise ValueError('framing must be full-body, knee-up or half-body')
        for name in ('support', 'gaze'):
            if name in row:
                selected[name] = _line(row[name], name)
        normalized[pose] = selected
    return mode, prefix, normalized


def resolve(preview, value=None, *, real_face_plan=None, pose=1, action=2):
    """Resolve six unchanged mothers; a single real look binds only its selected mother.

    Caller validates the complete real plan against its original-reference inventory.
    Body/head/gaze are then taken only from that plan, never inferred from the spec.
    """
    mode, prefix, choices = validate(value, preview['mode'])
    result = copy.deepcopy(preview)
    scenes = result.get('scenes')
    if not isinstance(scenes, list) or len(scenes) != 6:
        raise ValueError('registered photography needs six declared scenes')
    real_looks = {}
    if real_face_plan is not None:
        looks = real_face_plan['looks']
        if len(looks) == 6:
            real_looks = dict(enumerate(looks, 1))
        elif len(looks) == 1 and action == 2:
            real_looks = {pose: looks[0]}
        else:
            raise ValueError('A real preview requires all six real_face_plan looks')
        unbound = [number for number, row in choices.items()
                   if number not in real_looks and ({'support', 'gaze'} & set(row))]
        if unbound:
            raise ValueError('photography support/gaze needs the corresponding real_face_plan look')
    resolved = []
    for template in result['poses']:
        number = template['ordinal']
        row = choices.get(number, {})
        look = real_looks.get(number)
        framing = row.get('framing', result['layout_contract']['framing'][number - 1])
        # A single real-person look has no accepted first-image anchor; a small full-body face
        # drifts toward a generic face, so its undeclared default is knee-up.
        if (look is not None and len(real_looks) == 1 and look['face_visible'] and 'framing' not in row
                and framing == 'full-body'):
            framing = 'knee-up'
        scene_index = None if number <= prefix else row.get('scene_index', number)
        scene = studio_scene(scenes[number - 1]) if scene_index is None else scenes[scene_index - 1]
        description = template['description']
        if template['master'] == 'UPRIGHT_SEATED':
            description = description.replace('端正半身坐姿', '端正坐姿')
        if look is not None:
            for name, authority in (('support', 'body_action'), ('gaze', 'gaze')):
                if name in row and row[name] != look[authority]:
                    raise ValueError('photography ' + name + ' conflicts with real_face_plan ' + authority)
        shot = dict(pose=number, master=template['master'],
                    body_action=look['body_action'] if look is not None else description,
                    head_view=look['head_view'] if look is not None else None,
                    face_visible=look['face_visible'] if look is not None else None,
                    gaze=look['gaze'] if look is not None else row.get('gaze'),
                    support=None if look is not None else row.get('support'),
                    scene_index=scene_index, scene=scene, framing=framing)
        if look is not None:
            shot['real_face_look'] = copy.deepcopy(look)
            if look['face_visible'] and framing == 'full-body':
                shot['identity_risk'] = ('full-body real face is small in frame; identity often drifts. Prefer a '
                                         'user-confirmed knee-up first image exported as an accepted supplement; '
                                         'review this face as qa-user-review.')
        template.update(description=description, scene=scene)
        result['layout_contract']['framing'][number - 1] = framing
        resolved.append(shot)
    result.update(mode=mode, studio_prefix=prefix, resolved_shots=resolved)
    return result
