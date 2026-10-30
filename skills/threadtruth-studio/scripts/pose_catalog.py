"""Read local pose catalogs and validate declared execution sources.

No downloads, generation, license inference or image understanding. Declarations
must come from an actual rights/view review; a passing check is not legal proof.
The known ai-pose-gallery mirror is a research source, in every attachment role.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re

RESEARCH_SOURCE = 'anhao/ai-pose-gallery-zh'
RESEARCH_MARKERS = ('ai-pose-gallery-zh', 'ai-pose-gallery.pages.dev', 'ai-pose-gallery.anhao.app')
USAGES = {'owned', 'authorized', 'research-only'}
SOURCE_FIELDS = {'source_id', 'group_id', 'view', 'usage', 'note'}


def _text(value):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= 1200 and not any(ord(c) < 32 for c in value)


def _sha(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def _known_research(value):
    if isinstance(value, Path):value = str(value)
    return isinstance(value, str) and any(marker in value.lower().replace('\\', '/') for marker in RESEARCH_MARKERS)


def check_inventory(rows):
    """Reject declared/recognizable research sources before copying any role.

This cannot recognize an arbitrary renamed image with erased provenance. Keep
original source metadata; do not claim the path check is a content classifier.
"""
    for row in rows:
        check_source(row)
        if row.get('role') == 'pose-reference':
            validate_reference(row)
    return rows


def check_source(row):
    """Pre-copy source/path check; no image read or hash is required yet."""
    if not isinstance(row, dict):
        raise ValueError('Reference inventory rows must be objects')
    if any(_known_research(row.get(k, '')) for k in ('path', 'file', 'source_id', 'source_url')):
        raise ValueError('Known ai-pose-gallery material is research-only and cannot enter generation attachments')
    if isinstance(row.get('path'), (str, Path)):
        try:resolved = Path(row['path']).resolve()
        except (OSError, RuntimeError) as error:raise ValueError('Cannot resolve reference source path') from error
        if _known_research(resolved):
            raise ValueError('Resolved ai-pose-gallery source is research-only and cannot enter generation attachments')
    source = row.get('pose_source')
    if source is not None:
        if not isinstance(source, dict) or set(source) != SOURCE_FIELDS:
            raise ValueError('pose_source requires source_id, group_id, view, usage and review note')
        if source.get('usage') == 'research-only' or _known_research(source.get('source_id')):
            raise ValueError('Pose source is research-only; changing its attachment role does not authorize use')
        if any(not _text(source.get(k)) for k in SOURCE_FIELDS) or source['usage'] not in USAGES:
            raise ValueError('Declare the reviewed pose source and applicable owned/authorized usage')
        if row.get('role') != 'pose-reference':
            raise ValueError('Reviewed pose-source material must retain the pose-reference role')
    elif row.get('role') == 'pose-reference':
        raise ValueError('pose-reference requires a frozen pose_source review')
    return copy.deepcopy(source)


def validate_reference(row):
    check_source(row)
    source = row.get('pose_source') if isinstance(row, dict) else None
    if not isinstance(source, dict) or set(source) != SOURCE_FIELDS:
        raise ValueError('pose-reference requires a frozen pose_source review')
    if source.get('usage') == 'research-only' or _known_research(source.get('source_id')):
        raise ValueError('Pose source is research-only and cannot be used for generation')
    if row.get('role') != 'pose-reference' or not _sha(row.get('sha256')):
        raise ValueError('Pose image must bind its inventory hash and pose-reference role')
    if source.get('usage') not in {'owned', 'authorized'} or any(not _text(source.get(k)) for k in SOURCE_FIELDS):
        raise ValueError('Pose reference needs an actual source, group, view and rights/view review note')
    return copy.deepcopy(source)


def _local(base, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError('Catalog image paths must be relative to the catalog source root')
    resolved = (base / relative).resolve()
    if not resolved.is_relative_to(base.resolve()):
        raise ValueError('Catalog image path escapes its source root')
    return resolved


def load(path):
    """Load a reviewed small catalog, or inspect an unmodified gallery JSON.

Raw mirror rows always become research-only; inferred labels are not view review.
Images are read/hash-checked only when explicitly resolving an execution reference.
"""
    path = Path(path).resolve()
    doc = json.loads(path.read_text(encoding='utf-8'))
    if isinstance(doc, list):
        entries = []
        for row in doc:
            if not isinstance(row, dict):raise ValueError('Raw gallery records must be objects')
            match = re.fullmatch(r'((?:full_single|full_sexy|upper80v2|pair60)_P\d+)_(front|diag|side|high|low)', str(row.get('id', '')))
            if not match:
                raise ValueError('Unrecognized raw gallery record')
            entries.append(dict(group_id=match[1], view=match[2],
                                path=row.get('原图', row.get('原寸', '')),
                                title=row.get('姿势名称', row.get('ポーズ名', row['id'])),
                                category=row.get('分类', row.get('分類', '')),
                                body_action='', hands='', support='', occludes=[], suitable_for=[],
                                review_note=''))
        base = path.parent.parent if path.parent.name == 'data' else path.parent
        doc = dict(version=1, source_id=RESEARCH_SOURCE, usage='research-only',
                   note='Mirror source restrictions unresolved; labels are not reviewed body facts.', entries=entries)
    else:
        base = path.parent
        if (not isinstance(doc, dict) or set(doc) != {'version', 'source_id', 'usage', 'note', 'entries'}
                or type(doc['version']) is not int or doc['version'] != 1):
            raise ValueError('Catalog requires version=1, source_id, usage, note and entries')
    if not all(_text(doc.get(k)) for k in ('source_id', 'usage', 'note')) or doc['usage'] not in USAGES:
        raise ValueError('Catalog source and usage declaration required')
    if _known_research(doc['source_id']) or _known_research(str(path)):
        doc['usage'] = 'research-only'
    if not isinstance(doc['entries'], list):
        raise ValueError('Catalog entries must be a list')
    seen = set()
    for entry in doc['entries']:
        if not isinstance(entry, dict) or any(not _text(entry.get(k)) for k in ('group_id', 'view', 'path', 'title')):
            raise ValueError('Each catalog view needs group_id, view, path and title')
        key = (entry['group_id'], entry['view'])
        if key in seen:
            raise ValueError('Duplicate source/group/view in catalog')
        seen.add(key)
        _local(base, entry['path'])
        for key in ('occludes', 'suitable_for'):
            if not isinstance(entry.get(key, []), list) or any(not _text(v) for v in entry.get(key, [])):
                raise ValueError('Catalog occlusion and suitability labels must be text lists')
    doc['_base_dir'] = str(base)
    return doc


def search(catalog, *, query='', source_id=None, group_id=None, view=None):
    """Literal all-token search; actual selected views still need review."""
    if source_id is not None and source_id != catalog['source_id']:
        return []
    tokens = query.lower().split()
    result = []
    for row in catalog['entries']:
        if group_id is not None and row['group_id'] != group_id or view is not None and row['view'] != view:
            continue
        haystack = json.dumps(row, ensure_ascii=False).lower()
        if all(token in haystack for token in tokens):
            result.append(dict(copy.deepcopy(row), source_id=catalog['source_id'], usage=catalog['usage']))
    return result


def reference(catalog, group_id, view):
    """Resolve a reviewed owned/authorized image into the existing inventory."""
    if catalog['usage'] not in {'owned', 'authorized'} or _known_research(catalog['source_id']):
        raise ValueError('Catalog is research-only; no execution reference can be emitted')
    rows = search(catalog, group_id=group_id, view=view)
    if len(rows) != 1:
        raise ValueError('Select one unambiguous source/group/view')
    row = rows[0]
    if any(not _text(row.get(k)) for k in ('body_action', 'hands', 'support', 'review_note')):
        raise ValueError('Review the actual view: body, hands, support and review note are required')
    path = _local(Path(catalog['_base_dir']), row['path'])
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if not _sha(row.get('sha256')) or actual != row['sha256']:
        raise ValueError('Reviewed catalog image hash changed or is missing')
    source = dict(source_id=catalog['source_id'], group_id=group_id, view=view,
                  usage=catalog['usage'], note=catalog['note'] + ' View review: ' + row['review_note'])
    result = dict(path=str(path), sha256=actual, role='pose-reference', pose_source=source)
    check_inventory([result])
    return result


def main():
    parser = argparse.ArgumentParser(description='Read-only pose source/group/view catalog search; no generation.')
    parser.add_argument('catalog', type=Path)
    parser.add_argument('--query', default='')
    parser.add_argument('--source-id')
    parser.add_argument('--group-id')
    parser.add_argument('--view')
    parser.add_argument('--reference', action='store_true', help='Emit one reviewed owned/authorized execution reference')
    args = parser.parse_args()
    try:
        catalog = load(args.catalog)
        result = (reference(catalog, args.group_id, args.view) if args.reference else
                  search(catalog, query=args.query, source_id=args.source_id, group_id=args.group_id, view=args.view))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
