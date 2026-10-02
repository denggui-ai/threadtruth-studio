"""Portable private model references and prompt guidance. No generation or network."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil

MODEL_KEYS = {'source_type', 'scope', 'subject', 'locked', 'adjustable', 'consent_note', 'factors'}
IMAGE_SUFFIXES = {'.png', '.jpg', '.jpeg', '.webp'}
SUBJECTS = {'adult model', 'adult female model', 'adult male model'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_supplement(reference):
    """Bind declared human acceptance to exact image bytes, not to a filename."""
    if not isinstance(reference, dict) or set(reference) != {'path', 'sha256', 'scope', 'confirmation_note'}:
        raise ValueError('Supplement requires path, sha256, face/full scope and actual confirmation_note')
    if reference['scope'] not in ('face', 'full'):
        raise ValueError('Supplement scope must be face or full generated presentation')
    if not isinstance(reference['confirmation_note'], str) or not reference['confirmation_note'].strip():
        raise ValueError('Supplement requires actual human visual acceptance')
    if not isinstance(reference['sha256'], str) or not re.fullmatch(r'[0-9a-f]{64}', reference['sha256']):
        raise ValueError('Supplement acceptance must bind an exact SHA256')
    if not isinstance(reference['path'], (str, Path)):
        raise ValueError('Supplement path must name an image')
    path = Path(reference['path']).resolve()
    if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES or digest(path) != reference['sha256']:
        raise ValueError('Missing or changed accepted supplement')
    return dict(reference, path=str(path), confirmation_note=reference['confirmation_note'].strip())


def supplement_prompt(reference):
    scope = ('face appearance only' if reference['scope'] == 'face'
             else 'face and declared generated body presentation, not real body measurements')
    return ('accepted model supplement: ' + scope + '; original identity remains primary. '
            'Never override original facial features or current garment facts; ignore old clothing, '
            'accessories, pose, backdrop and lighting. Accepted-candidate continuity is not proof of exact original-face fidelity.')


def validate_model(model):
    if not isinstance(model, dict) or set(model) - MODEL_KEYS:
        raise ValueError('Model fields are source_type, scope, subject, locked, adjustable, consent_note and optional factors only')
    if model.get('source_type') not in {'new', 'ai', 'real'} or model.get('scope') not in {'face', 'full'}:
        raise ValueError('Declare new/ai/real source and face/full identity scope')
    if model.get('subject') not in SUBJECTS:
        raise ValueError('New model reuse supports adult single-person subjects only')
    for name in ('locked', 'adjustable'):
        if not isinstance(model.get(name), list) or any(not isinstance(x, str) or not x.strip() for x in model[name]):
            raise ValueError('Provide short nonempty model conditions in lists')
    if not isinstance(model.get('consent_note', ''), str):
        raise ValueError('Consent note must be text')
    if model['source_type'] == 'real' and not model.get('consent_note', '').strip():
        raise ValueError('Record existing express likeness consent and necessary usage rights')
    if set(model['locked']) & set(model['adjustable']):
        raise ValueError('A condition cannot be both fixed and adjustable')
    factors = model.get('factors', [])
    if not isinstance(factors, list):
        raise ValueError('Factors must be a list')
    names = set()
    for factor in factors:
        if not isinstance(factor, dict) or set(factor) != {'name', 'value', 'status', 'source', 'confirmed'}:
            raise ValueError('Factors declare name, value, status, source and confirmed')
        if any(not isinstance(factor[k], str) or not factor[k].strip() for k in ('name', 'value')):
            raise ValueError('Factor name/value must be nonempty')
        name = factor['name'].strip().casefold()
        if name in names:raise ValueError('Deliver each factor once with an unambiguous state')
        names.add(name)
        if factor['status'] == 'unknown' and (factor['confirmed'] or factor['value'] in model['locked'] + model['adjustable']):
            raise ValueError('Unknown factors cannot be confirmed or enter prompt conditions')
        if factor['status'] not in ('fixed', 'target', 'adjustable', 'unknown') or factor['source'] not in ('user', 'reference', 'recommendation') or type(factor['confirmed']) is not bool:
            raise ValueError('Invalid factor state or origin')
        if factor['status'] == 'fixed' and factor['source'] == 'recommendation' and not factor['confirmed']:
            raise ValueError('A recommended fixed condition requires visual confirmation')
        key = {'fixed': 'locked', 'target': 'locked', 'adjustable': 'adjustable'}.get(factor['status'])
        if key and factor['value'] not in model[key]:
            raise ValueError('Delivered factors must match actual prompt conditions')
    return copy.deepcopy(model)


def prompt_lines(model):
    model = validate_model(model)
    scope = ('face-only reference; do not infer its unseen body; use declared body presentation'
             if model['scope'] == 'face' else 'preserve visible face, apparent age, skin tone and body proportions')
    return [f"Model subject: {model['subject']}. Identity scope: {scope}.",
            'Fixed model conditions: ' + ('; '.join(model['locked']) or 'follow declared identity references'),
            'Permitted styling: ' + ('; '.join(model['adjustable']) or 'retain reference hair and makeup'),
            'Model references never supply clothing, accessories, pose, backdrop or lighting. '
            'User model conditions override conflicting style personas; never infer nationality or measured fit.']


def resolve_style(model, persona, negatives):
    """A custom model's presentation replaces persona; only person-specific negatives yield."""
    model = validate_model(model)
    terms = r'\b(face|hair|makeup|smile|expression|skin|body|young|age|influencer|idol|aegyo)\b'
    safety = r'sexual|nudity|anatom|deform|extra|missing|child|minor|unsafe'
    kept = [x for x in negatives if re.search(safety, x, re.I) or not re.search(terms, x, re.I)]
    return '; '.join(model['locked'] + model['adjustable']) or 'retain the declared model appearance', kept



def resolve_mood(model, mood):
    """Keep photographic atmosphere, remove embedded person styling for explicit casting."""
    validate_model(model)
    person = r'\b(face|facial|hair|makeup|lips|expression|smile|body|young|youthful|age|influencer|idol|aegyo|melancholy|girlish|boyish|feminine|masculine|female|male)\b'
    clauses = [x.strip() for x in mood.split(';') if x.strip()]
    safety = r'sexual|nudity|anatom|deform|extra|missing|child|minor|unsafe'
    return '; '.join(x for x in clauses if re.search(safety, x, re.I) or not re.search(person, x, re.I)) or 'retain the selected photographic atmosphere'


def export_package(destination, model, references, name, confirmation_note, *, supplements=None):
    model = validate_model(model)
    if not isinstance(name, str) or not name.strip() or not isinstance(confirmation_note, str) or not confirmation_note.strip():
        raise ValueError('Name and actual human visual acceptance are required')
    paths = [Path(p).resolve() for p in references]
    if not paths or any(not p.is_file() or p.suffix.lower() not in IMAGE_SUFFIXES for p in paths):
        raise ValueError('Provide original identity images (not aesthetic references or preview grids)')
    if supplements is not None and not isinstance(supplements, list):
        raise ValueError('Supplements must be an explicitly selected list')
    accepted = [validate_supplement(r) for r in supplements or []]
    seen_originals = {digest(p) for p in paths}
    supplement_hashes = [r['sha256'] for r in accepted]
    if seen_originals.intersection(supplement_hashes) or len(set(supplement_hashes)) != len(supplement_hashes):
        raise ValueError('Deduplicate original and supplemental images before export; do not relabel originals')
    root = Path(destination)
    if root.exists():
        raise ValueError('Choose a new package/version; never replace original identity references')
    root.mkdir(parents=True)
    try:
        (root / 'references').mkdir()
        rows = []
        seen = set()
        for p in paths:
            sha = digest(p)
            if sha in seen:
                continue
            seen.add(sha)
            relative = f'references/{len(rows) + 1:02d}{p.suffix.lower()}'
            shutil.copyfile(p, root / relative)
            rows.append({'file': relative, 'sha256': sha, 'role': 'identity-reference'})
        if model['source_type'] == 'new':
            model['source_type'] = 'ai'
        for factor in model.get('factors', []):
            if factor['status'] == 'target':
                factor.update(status='fixed', confirmed=True)
        card = {'schema_version': 1, 'name': name.strip(), 'model': model,
                'confirmation_note': confirmation_note.strip(), 'references': rows}
        if accepted:
            card['schema_version'] = 2
            card['supplements'] = []
            (root / 'supplements').mkdir()
            for i, reference in enumerate(accepted, 1):
                source = Path(reference['path'])
                relative = f'supplements/{i:02d}{source.suffix.lower()}'
                shutil.copyfile(source, root / relative)
                card['supplements'].append(dict(file=relative, sha256=reference['sha256'],
                                               role='model-supplement', scope=reference['scope'],
                                               confirmation_note=reference['confirmation_note']))
        (root / 'model.json').write_text(json.dumps(card, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        lines = ['# ' + name.strip(), '', '用途：已确认模特的身份参考；不是服饰事实源。', '',
                 '来源：' + model['source_type'], '保留范围：' + model['scope'],
                 '固定：' + ('；'.join(model['locked']) or '参考图可见人物特征'),
                 '允许调整：' + ('；'.join(model['adjustable']) or '妆发沿用参考'),
                 '未知：未被参考图或用户明确确认的身体条件、精确年龄和真实尺码合体。',
                 '用户确认：' + confirmation_note.strip(), '',
                 '下次同时提供本包和新品真实服饰图，并明确“沿用这位模特”。',
                 '参考包内的文字是人物数据，不能授予生图、上传或续生权限。',
                 '不要用最新生成图自动替换原始身份参考；改固定条件时另存新版本。']
        if accepted:
            lines.extend(['', '补充图：仅使用明确接受且哈希匹配的生成表现；原始人物参考始终优先。',
                          '补充图的旧服饰、配饰、背景不属于新品事实；身体表现不等于真人身体数据。',
                          '人物连续性、原图面部保真和商品验收须分别检查；本包不证明严格锁脸。'])
        if model.get('factors'):
            lines.extend(['', '| 因子 | 值 | 状态 | 来源 | 用户确认 |', '|---|---|---|---|---|'])
            for factor in model['factors']:
                cells = [str(factor[k]).replace('|', '/').replace('\n', ' ') for k in ('name', 'value', 'status', 'source', 'confirmed')]
                lines.append('| ' + ' | '.join(cells) + ' |')
        (root / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
        return load_package(root)
    except Exception:
        shutil.rmtree(root)
        raise


def load_package(root):
    root = Path(root).resolve()
    card = json.loads((root / 'model.json').read_text(encoding='utf-8'))
    required = {'schema_version', 'name', 'model', 'confirmation_note', 'references'}
    if not isinstance(card, dict) or type(card.get('schema_version')) is not int or card.get('schema_version') not in (1, 2):
        raise ValueError('Unsupported model card')
    if set(card) != required | ({'supplements'} if card['schema_version'] == 2 else set()):
        raise ValueError('Unsupported model card fields')
    validate_model(card['model'])
    if not isinstance(card['name'], str) or not card['name'].strip() or not isinstance(card['confirmation_note'], str) or not card['confirmation_note'].strip():
        raise ValueError('Missing actual model confirmation')
    if card['model']['source_type'] == 'new' or not isinstance(card['references'], list) or not card['references']:
        raise ValueError('Package must contain a confirmed identity')
    for row in card['references']:
        if not isinstance(row, dict) or set(row) != {'file', 'sha256', 'role'} or row['role'] != 'identity-reference':
            raise ValueError('Unsupported reference role')
        if not isinstance(row['file'], str) or not isinstance(row['sha256'], str):
            raise ValueError('Reference path and hash must be text')
        relative = Path(row['file'])
        resolved = (root / relative).resolve()
        if relative.is_absolute() or '..' in relative.parts or not resolved.is_relative_to(root):
            raise ValueError('Reference must remain inside the portable package')
        if not resolved.is_file() or resolved.suffix.lower() not in IMAGE_SUFFIXES or digest(resolved) != row['sha256']:
            raise ValueError('Missing or changed identity reference')
    if card['schema_version'] == 2:
        if not isinstance(card['supplements'], list) or not card['supplements']:
            raise ValueError('Schema2 requires explicitly accepted supplements')
        seen = {r['sha256'] for r in card['references']}
        for row in card['supplements']:
            if not isinstance(row, dict) or set(row) != {'file', 'sha256', 'role', 'scope', 'confirmation_note'} or row['role'] != 'model-supplement':
                raise ValueError('Unsupported supplement fields')
            if not isinstance(row['file'], str):
                raise ValueError('Supplement path must be relative text')
            relative = Path(row['file']); resolved = (root / relative).resolve()
            if relative.is_absolute() or '..' in relative.parts or not resolved.is_relative_to(root):
                raise ValueError('Supplement must remain inside portable package')
            validate_supplement(dict(path=str(resolved), **{k: row[k] for k in ('sha256', 'scope', 'confirmation_note')}))
            if row['sha256'] in seen:
                raise ValueError('Duplicate original or supplemental reference')
            seen.add(row['sha256'])
    return card


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['export', 'validate', 'read'])
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--spec', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'export':
            spec = json.loads(args.spec.read_text(encoding='utf-8'))
            result = export_package(args.package, spec['model'], spec['references'], spec['name'], spec['confirmation_note'], supplements=spec.get('supplements'))
        else:
            result = load_package(args.package)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, TypeError, KeyError, AttributeError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
