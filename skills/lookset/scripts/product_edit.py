"""Source-bound single-image product editing. No image, network or generation calls."""
import re


FORMS = ('human', 'faceless', 'flat-lay', 'hanger', 'mannequin', 'ghost-mannequin')
FIELDS = {'version', 'operation', 'source_form', 'edit_target_sha256', 'display_mode',
          'items', 'background', 'structure_evidence', 'unresolved_parts'}


def line(value):
    return (isinstance(value, str) and 0 < len(value.strip()) <= 600
            and not any(ord(c) < 32 or ord(c) == 127 for c in value)
            and '[' not in value and ']' not in value)


def sources(value, originals):
    return (isinstance(value, list) and bool(value)
            and all(isinstance(h, str) and h in originals for h in value)
            and len(set(value)) == len(value))


def validate(edit, inventory, *, output_form):
    if not isinstance(edit, dict) or set(edit) - {'correction'} != FIELDS or type(edit['version']) is not int or edit['version'] != 1:
        raise ValueError('product_edit requires the complete version-1 product specification')
    if 'correction' in edit and not line(edit['correction']):
        raise ValueError('Product correction must describe the actual local repair without changing the product contract')
    if edit['operation'] not in ('background-cleanup', 'reconstruction') or edit['source_form'] not in FORMS:
        raise ValueError('Declare background-cleanup or reconstruction and the actual source_form')
    if output_form not in FORMS:
        raise ValueError('Unknown product presentation')
    if edit['operation'] == 'background-cleanup' and edit['source_form'] != output_form:
        raise ValueError('Background cleanup retains the source presentation; removing a person is reconstruction')
    if edit['operation'] == 'reconstruction' and output_form in ('human', 'faceless'):
        raise ValueError('Product reconstruction is non-portrait; use the existing person workflow for a new pose')
    originals = {r['sha256'] for r in inventory if r.get('role') == 'garment-source'}
    target = [r['sha256'] for r in inventory if r.get('role') == 'edit-target']
    if (not originals or any(not isinstance(h, str) or not re.fullmatch(r'[a-f0-9]{64}', h) for h in originals)
            or len(target) != 1 or target[0] != edit['edit_target_sha256']):
        raise ValueError('Bind one edit-target hash and retain original garment-source facts separately')
    items = edit['items']
    if (not isinstance(items, list) or not 1 <= len(items) <= 12
            or edit['display_mode'] not in ('single', 'outfit')
            or (len(items) == 1) != (edit['display_mode'] == 'single')):
        raise ValueError('Single mode has one garment; outfit mode declares every selected item')
    names = set()
    for item in items:
        if (not isinstance(item, dict) or set(item) != {'name', 'kind', 'source_sha256s'}
                or not line(item['name']) or item['name'] in names or item['kind'] not in ('garment', 'accessory')
                or not sources(item['source_sha256s'], originals)):
            raise ValueError('Each distinct product item needs its name, garment/accessory kind and original source hashes')
        names.add(item['name'])
    if not any(item['kind'] == 'garment' for item in items):
        raise ValueError('This branch serves clothing and its selected outfit accessories, not accessory-only catalogs')
    selected_sources = {h for item in items for h in item['source_sha256s']}
    if originals != selected_sources:
        raise ValueError('Keep only selected product sources in the garment-source inventory; remove unselected SKU references before preparation')
    bg = edit['background']
    if (not isinstance(bg, dict) or set(bg) != {'color', 'shadow'}
            or bg['color'] not in ('#FFFFFF', '#F2F2F2') or bg['shadow'] not in ('none', 'soft-contact')):
        raise ValueError('Freeze a pure white or light gray background and none/soft-contact shadow')
    if edit['unresolved_parts'] != []:
        raise ValueError('Resolve required hidden/cropped structures with same-product sources or narrow the view before preparation')
    evidence = edit['structure_evidence']
    if not isinstance(evidence, list) or len(evidence) > 24:
        raise ValueError('structure_evidence lists the visible interior/opening parts and their original sources')
    parts = set()
    for entry in evidence:
        if (not isinstance(entry, dict) or set(entry) != {'part', 'source_sha256s'}
                or not line(entry['part']) or entry['part'] in parts
                or not sources(entry['source_sha256s'], selected_sources)):
            raise ValueError('Interior structure evidence must bind distinct visible parts to original product sources')
        parts.add(entry['part'])
    if output_form == 'ghost-mannequin' and not evidence:
        raise ValueError('Ghost mannequin requires source evidence for the openings/interiors actually shown')


def photography(edit):
    cleanup = edit['operation'] == 'background-cleanup'
    return dict(
        scene='Seamless uniform ' + edit['background']['color'] + ' studio background, without props.',
        lighting=('Retain the source subject lighting and texture; change only its background.' if cleanup else
                  'Soft even neutral studio lighting, accurate garment colors and visible fabric texture.'),
        composition=('Retain every subject, pose, silhouette and relative position in the edit target; only pad the canvas if needed.' if cleanup else
                     'One centered complete product arrangement, source-supported view, natural proportions and clear margins.'),
        palette='Original garment colors; background ' + edit['background']['color'] + '.')


def same_contract(before, after):
    return (isinstance(before, dict) and isinstance(after, dict)
            and {k: v for k, v in before.items() if k != 'correction'} ==
            {k: v for k, v in after.items() if k != 'correction'})


def requirements(edit, form):
    """Expectations are frozen with the plan; QA must report each actual result."""
    bg = edit['background']
    items = '; '.join(i['name'] for i in edit['items'])
    scope = ('Keep the declared ' + edit['display_mode'] + ' sales items unchanged: ' + items
             + '; retain all other existing foreground subjects, clothing and accessories from the edit target, without treating them as sale items or adding products.'
             if edit['operation'] == 'background-cleanup' else
             'Exactly the declared ' + edit['display_mode'] + ' items: ' + items + '; no additions, omissions or substitutions.')
    result = {
        'product_scope': scope,
        'background': 'Uniform ' + bg['color'] + ' background; shadow=' + bg['shadow'] + '; verify background pixels outside the declared shadow and subject.',
        'edges': 'No background residue or halos; preserve thin edges, lace, mesh, transparency and original lining.',
        'edit_scope': ('Keep all original subjects, pose, silhouette, visible folds and product details; only replace background.'
                       if edit['operation'] == 'background-cleanup' else
                       'Reconstruct only the selected source-backed garments; no invented hidden design, changed proportions or new marks.'),
    }
    if form == 'ghost-mannequin':
        result.update(
            no_body_support='No body parts, skin, anatomy, transparent bodies, human reflections/shadows, mannequin, hanger, stand or support.',
            volume='Natural three-dimensional garment volume, gravity, folds and thickness; not flat-lay, hanger or visible mannequin.',
            openings='Hollow natural openings with original lining and construction preserved; source-backed parts: ' + '; '.join(e['part'] for e in edit['structure_evidence']) + '.')
    if any(i['kind'] == 'accessory' for i in edit['items']) and edit['operation'] == 'reconstruction':
        result['accessories'] = 'Selected shoes, bags and jewelry are independent products, with no feet, shoulders or wearing body; preserve source pairing and design.'
    return result


def render(edit, form):
    rows = ['Product operation: ' + edit['operation'] + ' via native AI image editing; not a deterministic cutout or pixel-preservation guarantee.',
            'Use the edit target for retained presentation only. Original garment-source images alone establish product facts; derived outputs never prove unseen design.',
            'Product constraints take precedence over style defaults. One independent image, no collage, extra view, caption or new logo.']
    rows += ['Product requirement ' + key + ': ' + value for key, value in requirements(edit, form).items()]
    if form == 'ghost-mannequin':
        rows += ['Sleeves and trouser legs remain natural hollow tubes; no arms or legs. Necklines contain no head or neck; skirts contain no legs; shoes contain no feet.',
                 'Hollow does not mean holes, removed lining or invented transparency. Preserve original multilayer sheer fabric, construction and fit. Never synthesize anatomy to support the garment.']
    if edit['operation'] == 'reconstruction':
        rows.append('Remove the source person completely. Keep only the declared product inventory and source-supported structure; no speculative reverse view or hidden design.')
    if edit.get('correction'):
        rows.append('Correct the reviewed local defect, retaining every product constraint above: ' + edit['correction'])
    return '\n'.join(rows)
