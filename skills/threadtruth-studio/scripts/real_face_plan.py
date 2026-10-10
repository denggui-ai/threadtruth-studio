"""Validate declared real-person view coverage and ordered per-image selections.

Coverage is a reviewed input declaration, not automatic face recognition or a
facial-fidelity guarantee. This helper does not generate, authorize or select
references on the caller's behalf.
"""
import copy
import re

VIEWS = {'front', 'near-front', 'left-three-quarter', 'right-three-quarter',
         'left-profile', 'right-profile', 'unknown'}
VIEW_TEXT = {'left-three-quarter': 'head facing image-left in a three-quarter view',
             'right-three-quarter': 'head facing image-right in a three-quarter view',
             'left-profile': 'head facing image-left in profile',
             'right-profile': 'head facing image-right in profile'}
LOOK_FIELDS = {'body_action', 'head_view', 'gaze', 'face_visible',
               'reference_sha256s', 'selection_note'}
FRONTAL = {'front', 'near-front'}
# Directional off-camera gaze; slight "past/beside the lens" stays allowed.
OFF_LENS = re.compile(r'\b(?:image[- ](?:left|right)|outside (?:of )?the (?:lens|frame|camera)|off[- ](?:lens|camera|frame)'
                      r'|away from (?:the )?(?:lens|camera)|(?:to|toward) the (?:left|right) of the (?:lens|camera)'
                      r'|sideways)\b', re.I)


def text(value):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= 1000


def sha(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def supports(views, target):
    return target in views or (target in {'front', 'near-front'} and
                               bool(set(views) & {'front', 'near-front'}))


def selected(plan, inventory, number):
    by_hash = {r['sha256']: r for r in inventory}
    return [by_hash[h] for h in plan['looks'][number - 1]['reference_sha256s']]


def validate(plan, inventory, *, schema_version, identity, model, context, count, route, strict_looks=()):
    """strict_looks: 1-based numbers of newly planned looks; frozen looks are never re-judged by newer rules."""
    if schema_version != 2 or not identity or not model or model['source_type'] != 'real':
        raise ValueError('real_face_plan applies only to an existing real-person identity task')
    if not isinstance(plan, dict) or set(plan) != {'primary_identity_sha256', 'coverage', 'looks'}:
        raise ValueError('Real face plan requires primary_identity_sha256, coverage and looks')
    if len({r['sha256'] for r in inventory}) != len(inventory):
        raise ValueError('Per-image selection requires unique inventory hashes and unambiguous roles')
    by_hash = {r['sha256']: r for r in inventory}
    primary = plan['primary_identity_sha256']
    if not sha(primary) or primary not in by_hash or by_hash[primary]['role'] != 'identity-reference':
        raise ValueError('The primary identity must be an original identity-reference, not a supplement')
    coverage = plan['coverage']
    if not isinstance(coverage, list) or not coverage:
        raise ValueError('Record reviewed coverage for original real-person images')
    reviewed = {}
    for row in coverage:
        if not isinstance(row, dict) or set(row) != {'sha256', 'views', 'note'}:
            raise ValueError('Coverage declares original sha256, views and a review note')
        h, views = row['sha256'], row['views']
        if (not sha(h) or h not in by_hash or by_hash[h]['role'] != 'identity-reference'
                or h in reviewed):
            raise ValueError('Coverage must bind distinct original identity references; AI supplements are not real angles')
        if (not isinstance(views, list) or not views or any(not isinstance(v, str) or v not in VIEWS for v in views)
                or len(set(views)) != len(views) or ('unknown' in views and len(views) != 1)
                or not text(row['note'])):
            raise ValueError('Declare clear supported views or unknown alone, plus a nonempty review note')
        reviewed[h] = views
    looks = plan['looks']
    if not isinstance(looks, list) or len(looks) != count or count not in (1, 6):
        raise ValueError('Provide one real face look per frozen single/six-image prompt')
    for number, look in enumerate(looks, 1):
        if not isinstance(look, dict) or set(look) != LOOK_FIELDS:
            raise ValueError('Each look separates body_action, head_view, gaze, face_visible and reference selection')
        if (any(not text(look[k]) for k in ('body_action', 'gaze', 'selection_note'))
                or type(look['face_visible']) is not bool):
            raise ValueError('Provide short nonempty planning/selection text and boolean face_visible')
        target = look['head_view']
        if ((look['face_visible'] and (not isinstance(target, str) or target not in VIEWS - {'unknown'}))
                or (not look['face_visible'] and target != 'hidden')):
            raise ValueError('Visible faces need a supported head_view; hidden faces use head_view=hidden')
        hashes = look['reference_sha256s']
        if (not isinstance(hashes, list) or not hashes or any(not sha(h) or h not in by_hash for h in hashes)
                or len(set(hashes)) != len(hashes)):
            raise ValueError('Select distinct frozen inventory hashes in actual attachment order')
        rows = selected(plan, inventory, number)
        if primary not in hashes or not any(r['role'] == 'garment-source' for r in rows):
            raise ValueError('Each image must retain the primary original identity and at least one garment source')
        if context.get('purpose') == 'correction-edit' and sum(r['role'] == 'edit-target' for r in rows) != 1:
            raise ValueError('A correction selection must retain its unique declared edit-target')
        if look['face_visible'] and not any(h in reviewed and supports(reviewed[h], target) for h in hashes):
            raise ValueError('Requested face direction lacks a selected clear original view; do not infer or mirror an unseen angle')
        covered = set().union(*(reviewed[h] for h in hashes if h in reviewed))
        if (number in strict_looks and look['face_visible'] and covered <= FRONTAL
                and OFF_LENS.search(look['gaze'])):
            raise ValueError('Frontal-only original coverage supports a camera or near-camera gaze; '
                             'directional off-lens eyes turn the head and drift identity')
        if route == 'codex_native' and len(rows) + int(number > 1) > 5:
            raise ValueError('Each native image permits five attachments, including the mandatory later first-image anchor; revise the explicit selection without silently dropping inputs')
    return copy.deepcopy(plan)


def prompt_lines(look):
    head=look['head_view']
    if head in VIEW_TEXT:head+=' ('+VIEW_TEXT[head]+')'
    lines = ['Real-person per-image plan: these body, head and eye directions override conflicting default pose/head/gaze text, not garment facts or original identity conditions.',
             'Body action: ' + look['body_action'] + '.',
             ('Head direction: ' + head + '.' if look['face_visible'] else
              'Face visibility: face is not visible; keep it naturally outside the frame or turned away, without a forced over-shoulder face.'),
             ('Eye gaze: ' + look['gaze'] + '.' if look['face_visible'] else
              'The eye direction is not exposed; do not force a visible camera gaze.'),
             'Keep natural neck support and distinct body action; generated supplements and the accepted first image do not establish unseen real-person angles.']
    return lines
