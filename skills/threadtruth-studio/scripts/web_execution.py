"""Explicit, immutable web submission envelopes; no browser or generation calls."""
import hashlib
import json
from pathlib import Path


# Keep version-1 text stable: retained submissions bind these exact bytes.
BEGIN = b'[BEGIN FROZEN VISUAL REQUEST]\n'
END = b'\n[END FROZEN VISUAL REQUEST]\n'
PREFIX = (
    'WEB EXECUTION LIMIT — ONE IMAGE TOOL CALL MAXIMUM\n'
    'This message limits the already authorized current request; it grants no additional requests. '
    'Across this turn and any agents, invoke an image-generation or image-edit tool at most ONCE in total. '
    'A six-panel direction preview is one image made in that one call. Do not delegate generation, '
    'start parallel calls, make alternatives, refine, repair, regenerate or retry.\n'
    'Use the complete frozen visual request below and its ordered uploaded references. '
    'These execution limits do not change any garment, identity, pose, style, medium or canvas instruction.\n'
    'As soon as the first image tool call returns, END THIS TURN: return the original image on success; '
    'on failure or an unclear result, report that result and stop without another image tool call. '
    'If one call cannot complete the request, stop and explain. Visual QA belongs to the caller after '
    'the image is returned. Even visible mistakes do not authorize a correction; wait for a separate '
    'explicit user request before any further image tool call.\n\n'
).encode('utf-8') + BEGIN
SUFFIX = END + b'End the turn after the first result, failure or uncertainty. No automatic correction or retry.\n'
# V2 changes only the panel-neutral execution explanation. Never rewrite PREFIX:
# historical v1 packages bind it byte-for-byte, independently of newer plans.
PREFIX_V2 = PREFIX.replace(
    b'A six-panel direction preview is one image made in that one call.',
    b'A multi-panel direction preview, including a nine-panel 3x3 preview, is one image made in that one call.')


def version(data):
    plan=data.get('shot_plan')
    return 2 if isinstance(plan,dict) and plan.get('version')==2 else 1


def folder_name(data):
    return 'web-execution-v'+str(version(data))


def prefix(envelope_version):
    if type(envelope_version) is not int or envelope_version not in (1,2):
        raise ValueError('Unsupported web execution envelope version')
    return PREFIX_V2 if envelope_version==2 else PREFIX


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')


def safe(root,relative):
    path=Path(relative);resolved=(Path(root)/path).resolve()
    if path.is_absolute() or '..' in path.parts or not resolved.is_relative_to(Path(root).resolve()):
        raise ValueError('Web execution file escapes the task directory')
    return resolved


def artifact(root,path,expected=None):
    relative=str(Path(path).relative_to(root));raw=safe(root,relative).read_bytes()
    if expected is not None and raw!=expected:
        raise ValueError('Canonical handoff changed or is stale; do not rewrite its evidence')
    return dict(file=relative,sha256=sha(raw))


def material(root,data,row,out,refs,prompt,manifest):
    root=Path(root);out=Path(out)
    if data['route']!='chatgpt_web':raise ValueError('Execution envelope is for ChatGPT web only')
    canonical=prompt.encode('utf-8')
    if BEGIN in canonical or END in canonical:raise ValueError('Canonical request contains execution-envelope delimiters')
    prompt_record=artifact(root,out/'prompt.txt',canonical)
    manifest_record=None
    if manifest is not None:
        # export's existing manifest deliberately has no trailing newline.
        expected=json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8')
        manifest_record=artifact(root,out/'manifest.json',expected)
    attachments=[]
    for i,ref in enumerate(refs,1):
        item=artifact(root,out/f'{i:02d}-{ref["role"]}{Path(ref["file"]).suffix}')
        if item['sha256']!=ref['sha256']:raise ValueError('Exported web attachment changed')
        attachments.append(item)
    envelope_version=version(data);envelope_prefix=prefix(envelope_version)
    folder=out/folder_name(data)
    if folder.is_symlink():raise ValueError('Execution package must not be a symlink')
    message=envelope_prefix+canonical+SUFFIX
    metadata=dict(schema_version=envelope_version,route='chatgpt_web',image_tool_call_limit=1,
        task_created_at=data['created_at'],look=row['number'],attempt_number=row.get('attempt_number',1),
        plan_revision=row.get('plan_revision',0),current_plan_sha256=(manifest or {}).get('current_plan_sha256'),
        frozen_prompt_sha256=row['prompt_sha256'],canonical_prompt=prompt_record,
        canonical_manifest=manifest_record,attachments=attachments,
        envelope_sha256=sha(envelope_prefix+SUFFIX),
        submission=dict(file=str((folder/'submission.txt').relative_to(root)),sha256=sha(message)))
    return folder,message,metadata


def package_paths(root,folder):
    return (safe(root,str((folder/'submission.txt').relative_to(root))),
            safe(root,str((folder/'execution.json').relative_to(root))))


def check_package(root,folder,message,metadata):
    submission,path=package_paths(root,folder)
    if submission.read_bytes()!=message or path.read_bytes()!=encode(metadata):
        raise ValueError('Frozen web execution package changed; never overwrite it')
    return dict(file=str(path.relative_to(Path(root).resolve())),sha256=sha(path.read_bytes()))


def prepare(root,data,row,out,refs,prompt,manifest):
    folder,message,metadata=material(root,data,row,out,refs,prompt,manifest)
    submission,path=package_paths(root,folder)
    if folder.exists():
        check_package(root,folder,message,metadata)
    else:
        folder.mkdir()
        # Exclusive creation retains partial files after an interrupted write for reconciliation.
        with submission.open('xb') as stream:stream.write(message)
        with path.open('xb') as stream:stream.write(encode(metadata))
    return dict(execution_manifest=str(path),submission_file=str(submission),
        submission_sha256=metadata['submission']['sha256'],envelope_sha256=metadata['envelope_sha256'],
        canonical_prompt_sha256=metadata['canonical_prompt']['sha256'])


def validate_current(root,data,row,out,refs,prompt,manifest,path,expected_submission_sha256):
    folder,message,metadata=material(root,data,row,out,refs,prompt,manifest)
    _,expected_path=package_paths(root,folder)
    if Path(path).resolve()!=expected_path or expected_submission_sha256!=metadata['submission']['sha256']:
        raise ValueError('Reserve the exact current web execution manifest and submission hash')
    return check_package(root,folder,message,metadata)


def check_retained(root,row):
    """Verify a reserved/historical binding without rebuilding it from newer plans."""
    record=row['web_execution']
    if not isinstance(record,dict) or set(record)!={'file','sha256'}:
        raise ValueError('Invalid retained web execution binding')
    raw=safe(root,record['file']).read_bytes()
    if sha(raw)!=record['sha256']:raise ValueError('Retained web execution manifest changed')
    meta=json.loads(raw)
    envelope_prefix=prefix(meta.get('schema_version'))
    if (meta.get('route')!='chatgpt_web' or type(meta.get('image_tool_call_limit')) is not int
            or meta['image_tool_call_limit']!=1 or meta.get('look')!=row['number']
            or meta.get('attempt_number')!=row.get('attempt_number',1)
            or meta.get('frozen_prompt_sha256')!=row['prompt_sha256']
            or meta.get('envelope_sha256')!=sha(envelope_prefix+SUFFIX)):
        raise ValueError('Retained web execution no longer binds this attempt')
    records=[meta['canonical_prompt'],meta['submission']]+meta['attachments']
    if meta['canonical_manifest'] is not None:records.append(meta['canonical_manifest'])
    for item in records:
        if sha(safe(root,item['file']).read_bytes())!=item['sha256']:
            raise ValueError('Retained web execution artifact changed')
    canonical=safe(root,meta['canonical_prompt']['file']).read_bytes()
    if (safe(root,meta['submission']['file']).read_bytes()!=envelope_prefix+canonical+SUFFIX
            or [item['sha256'] for item in meta['attachments']]!=row['reference_hashes']):
        raise ValueError('Retained web submission or ordered attachments changed')
