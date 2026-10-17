#!/usr/bin/env python3
"""Local ChatGPT handoff/automation ledger. No network, browser or generation calls."""
import argparse
import copy
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import struct
import sys
import uuid
import zlib
from urllib.parse import urlparse

# Even --help must leave an installed/read-only runtime tree unchanged.
sys.dont_write_bytecode = True
_model_spec = importlib.util.spec_from_file_location('task_model_reference', Path(__file__).with_name('model_reference.py'))
models = importlib.util.module_from_spec(_model_spec)
_model_spec.loader.exec_module(models)
_face_plans = None
_photography_targets = None


def real_face_helper():
    # Old/default tasks and read-only --help retain their existing dependencies.
    global _face_plans
    if _face_plans is None:
        spec=importlib.util.spec_from_file_location('task_real_face_plan', Path(__file__).with_name('real_face_plan.py'))
        _face_plans=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_face_plans)
    return _face_plans


def photography_helper():
    global _photography_targets
    if _photography_targets is None:
        spec=importlib.util.spec_from_file_location('task_photography_targets', Path(__file__).with_name('photography_targets.py'))
        _photography_targets=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_photography_targets)
    return _photography_targets


_shot_plans = None

def shot_helper():
    global _shot_plans
    if _shot_plans is None:
        spec=importlib.util.spec_from_file_location('task_shot_plan',Path(__file__).with_name('shot_plan.py'))
        _shot_plans=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_shot_plans)
    return _shot_plans


def plan_fingerprint(data):
    return object_hash(dict(version=data.get('plan_version',0),context=data.get('context'),
                            model=data.get('model'),shot_plan=data.get('shot_plan')))


def check_shot_plan(data):
    if 'shot_plan' not in data:
        if 'shot_plan_sha256' in data:raise ValueError('Missing frozen shot plan')
        return
    if data['schema_version']!=2 or object_hash(data['shot_plan'])!=data.get('shot_plan_sha256'):
        raise ValueError('Frozen shot plan changed')
    shot_helper().validate(data['shot_plan'],data['references'],context=data['context'],
        count=face_plan_count(data['context'],len(data['looks'])),identity=data['identity'],real_face_plan=data.get('real_face_plan'))
    history=data.get('shot_plan_history',[])
    if not isinstance(history,list):raise ValueError('Invalid shot plan history')
    for prior in history:
        if (not isinstance(prior,dict) or set(prior)!={'plan','sha256','note'}
                or object_hash(prior['plan'])!=prior['sha256'] or not prior['note'].strip()
                or prior['plan']['looks'][0]!=data['shot_plan']['looks'][0]):
            raise ValueError('Historical first-shot plan changed')



def prompt_check(prompt,context,model=None,shot_plan=None,number=1,real_face_plan=None):
    photography_helper().apply(prompt,context.get('photography_targets'))
    if model is not None:models.apply_conditions(prompt,model,allow_child=True)
    if shot_plan is not None:
        shot_helper().apply(prompt,shot_plan,None if context.get('purpose')=='preview-grid' else number,real_face_plan)


def preview_candidate(data, row, *, model=None, shot_plan=None, prompt=None, garment_references=None, real_face_plan=None):
    changed=models.validate_model(model if model is not None else data['model'],allow_child=True) if data['identity'] else None
    if changed is not None and (any(changed[k]!=data['model'][k] for k in ('source_type','scope','subject'))
            or changed.get('consent_note','')!=data['model'].get('consent_note','')):
        raise ValueError('A preview styling revision cannot replace identity source, scope, subject or consent')
    additions=[];inventory=list(data['references']);hashes={r['sha256'] for r in inventory}
    if garment_references is not None:
        if not isinstance(garment_references,list) or not garment_references or shot_plan is None:
            raise ValueError('Additional garment originals require a revised shot plan')
        for ref in garment_references:
            if not isinstance(ref,dict) or set(ref)!={'path','sha256'}:
                raise ValueError('Additional garment originals declare path and exact sha256')
            path=Path(ref['path']).resolve();models.validate_image(path)
            if digest(path)!=ref['sha256'] or ref['sha256'] in hashes:
                raise ValueError('Additional garment reference changed or duplicates frozen inventory')
            hashes.add(ref['sha256']);additions.append(dict(path=str(path),sha256=ref['sha256']))
            inventory.append(dict(sha256=ref['sha256'],role='garment-source'))
    planned=shot_plan if shot_plan is not None else data.get('shot_plan')
    face_plan=copy.deepcopy(data.get('real_face_plan'))
    if face_plan is not None and planned is not None:
        # Only garment selection and the declared sixth route may change here.
        # Original real coverage, identity and all other body/head/gaze values stay frozen.
        garment_hashes={r['sha256'] for r in inventory if r['role']=='garment-source'}
        for i,shot in enumerate(planned['looks']):
            cell=face_plan['looks'][i]
            cell['reference_sha256s']=[h for h in cell['reference_sha256s'] if h not in garment_hashes or h in shot['reference_sha256s']]
            cell['reference_sha256s'] += [h for h in shot['reference_sha256s'] if h not in cell['reference_sha256s']]
        if data.get('shot_plan',{}).get('route')!=planned['route'] and data.get('shot_plan'):
            cell=face_plan['looks'][5]
            cell['body_action']=shot_helper().RELATIONS[5] if planned['route']=='A' else shot_helper().FRONT_RELATION
            if planned['route']=='A':
                cell.update(head_view='hidden',face_visible=False,gaze='not visible',
                    selection_note='Reviewed garment-route change: show supported back without inferring a new real face view')
        real_face_helper().validate(face_plan,inventory,schema_version=2,identity=data['identity'],
            model=changed,context=data['context'],count=6,route=data['route'])
    if real_face_plan is not None and real_face_plan!=face_plan:
        raise ValueError('Preview garment/styling revision cannot change original real face coverage or identity')
    if planned is not None:
        planned=shot_helper().validate(planned,inventory,context=data['context'],count=6,
                                      identity=data['identity'],real_face_plan=face_plan)
    if not isinstance(prompt,str) or not prompt.strip():raise ValueError('Provide a complete revised preview prompt')
    photography_helper().apply(prompt,data['context'].get('photography_targets'))
    if changed is not None:models.apply_conditions(prompt,changed,allow_child=True)
    if planned is not None:
        shot_helper().apply(prompt,planned,real_face_plan=face_plan)
        chosen=shot_helper().selected(planned,1,True)
        actual=[r for r in inventory if r['role']!='garment-source' or r['sha256'] in chosen]
        if face_plan:
            face_selected={h for cell in face_plan['looks'] for h in cell['reference_sha256s']}
            actual=[r for r in actual if r['sha256'] in face_selected]
        native_reference_check(actual,data['route'])
    result=dict(model=changed,shot_plan=planned,prompt=prompt)
    if additions:result['garment_references']=additions
    if face_plan is not None:result['real_face_plan']=face_plan
    return result


ROLE_TEXT = {
    'garment-source': 'garment source; authoritative product facts',
    'identity-reference': 'original model identity; ignore clothing, accessories, pose, backdrop and lighting',
    'aesthetic-reference': 'aesthetic only; do not copy identity or clothing',
    'edit-target': 'image to correct; supplies only the explicitly retained layout, pose and scene, not an accepted identity or authoritative garment facts; correct failed traits from the original identity and garment sources',
    'identity-only': 'current outfit accepted first-image identity; never override original identity or garment sources',
}


def native_reference_check(rows, route, extra_anchor=0):
    if route=='codex_native' and len(rows)+extra_anchor>5:
        raise ValueError('Native imagegen allows at most five references; select sufficient garment views before freezing, leaving room for original identity and the current first-image anchor; never silently drop inputs')


def is_preview(data):
    return data.get('schema_version') == 2 and data.get('context', {}).get('purpose') == 'preview-grid'


def face_plan_count(context, count):
    return 6 if (context or {}).get('purpose') == 'preview-grid' else count


def context_check(context, size):
    required = {'outfit', 'style', 'mode', 'output_form', 'size', 'first_pose'}
    if not isinstance(context, dict) or set(context) - {'purpose', 'pose_description', 'photography_targets', 'canvas_policy'} != required:
        raise ValueError('Declare outfit, style, mode, output_form, size and first_pose for the frozen task context')
    if any(not isinstance(context[k], str) or not context[k].strip() for k in required - {'size','first_pose'}):
        raise ValueError('Task context labels must be nonempty')
    if context['first_pose'] == 'custom':
        if not isinstance(context.get('pose_description'), str) or not context['pose_description'].strip():
            raise ValueError('A custom single-image presentation requires the explicit user pose/framing description')
    elif type(context['first_pose']) is not int or context['first_pose'] not in range(1,7):
        raise ValueError('Declare the actual first pose number or custom presentation')
    elif 'pose_description' in context:
        raise ValueError('pose_description is only for a custom body-action category; keep numbered-master framing/support/gaze choices in the frozen prompt')
    if context['mode'] not in ('B', 'C', 'D') or context['size'] != list(size):
        raise ValueError('Task mode/canvas does not match context')
    if context.get('purpose', 'delivery') not in ('delivery', 'model-check', 'correction-edit', 'preview-grid'):
        raise ValueError('Task purpose must be delivery, model-check, correction-edit or preview-grid')
    if context.get('canvas_policy', 'exact') not in ('exact', 'ratio-first'):
        raise ValueError('Canvas policy must be exact or ratio-first')
    result=copy.deepcopy(context)
    if 'photography_targets' in context:
        result['photography_targets']=photography_helper().validate(context['photography_targets'])
    return result


def presentation_check(context, refs, count, identity, model):
    if context.get('purpose') == 'preview-grid' and (count != 1 or context['first_pose'] != 1):
        raise ValueError('A preview-grid is one six-panel request with master numbering starting at 1')
    if context['first_pose'] == 'custom' and count != 1:
        raise ValueError('A custom presentation is a single-image task, not a default six-pose set')
    targets = sum(r['role'] == 'edit-target' for r in refs)
    if context.get('purpose') == 'correction-edit':
        if (count != 1 or not identity or not model or model['source_type'] not in ('ai', 'real')
                or not any(r['role'] == 'identity-reference' for r in refs) or targets != 1):
            raise ValueError('Correction edit requires one image, one edit target and an existing original person reference')
    elif targets:
        raise ValueError('An edit target is only valid for an explicitly requested correction-edit')


def object_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def png_size(path):
    path=Path(path)
    if path.stat().st_size>100_000_000:raise ValueError('PNG exceeds supported download size')
    data=path.read_bytes()
    if data[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('Expected original PNG')
    at=8;idat=bytearray();header=None;ended=False
    while at<len(data):
        if at+12>len(data):raise ValueError('Truncated PNG chunk')
        size=struct.unpack('>I',data[at:at+4])[0];kind=data[at+4:at+8];end=at+12+size
        if end>len(data):raise ValueError('Truncated PNG data')
        payload=data[at+8:at+8+size];crc=struct.unpack('>I',data[at+8+size:end])[0]
        if zlib.crc32(kind+payload)&0xffffffff!=crc:raise ValueError('PNG checksum mismatch')
        if header is None and kind!=b'IHDR':raise ValueError('Missing PNG header')
        if kind==b'IHDR':
            if header is not None or size!=13:raise ValueError('Invalid PNG header')
            header=struct.unpack('>IIBBBBB',payload)
        elif kind==b'IDAT':idat.extend(payload)
        elif kind==b'IEND':
            if size or end!=len(data):raise ValueError('Invalid PNG ending')
            ended=True;break
        at=end
    if not ended or not header or not idat:raise ValueError('Incomplete PNG download')
    w,h,depth,color,compression,filter_method,interlace=header
    channels={0:1,2:3,3:1,4:2,6:4}.get(color)
    allowed={0:(1,2,4,8,16),2:(8,16),3:(1,2,4,8),4:(8,16),6:(8,16)}
    if not w or not h or not channels or depth not in allowed[color] or compression or filter_method or interlace not in (0,1):raise ValueError('Unsupported PNG encoding')
    passes=[(0,0,1,1)] if not interlace else [(0,0,8,8),(4,0,8,8),(0,4,4,8),(2,0,4,4),(0,2,2,4),(1,0,2,2),(0,1,1,2)]
    lengths=[]
    for x,y,dx,dy in passes:
        pw=max(0,(w-x+dx-1)//dx);ph=max(0,(h-y+dy-1)//dy)
        if pw and ph:lengths.append(((pw*channels*depth+7)//8+1,ph))
    expected=sum(length*rows for length,rows in lengths)
    if expected>256_000_000:raise ValueError('PNG decoded size exceeds limit')
    try:
        decoder=zlib.decompressobj();raw=decoder.decompress(idat,expected+1)
    except zlib.error as exc:raise ValueError('Invalid compressed PNG') from exc
    if len(raw)!=expected or not decoder.eof or decoder.unused_data:raise ValueError('Incomplete or oversized PNG pixel stream')
    at=0
    for length,rows in lengths:
        for row in range(rows):
            if raw[at]>4:raise ValueError('Invalid PNG row filter')
            at+=length
    return [w,h]


def stamp():
    return datetime.now(timezone.utc).isoformat()


def refresh_delivery_status(data):
    # Retried images remain evidence even after the current row returns to pending.
    has_output=any(row.get('output') for row in evidence_rows(data))
    data['delivery_status']=('preview-grid' if is_preview(data) else 'image-draft') if has_output else 'prepared'
    if is_preview(data) or 'preview_origin' in data:
        data['total_attempts']=data['attempts']+data.get('preview_origin', {}).get('attempts', 0)


def save(root,data):
    refresh_delivery_status(data)
    temp=root/('.task-'+uuid.uuid4().hex+'.tmp')
    with temp.open('x',encoding='utf-8') as f:
        json.dump(data,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
    temp.replace(root/'task.json')
    if os.name=='posix':
        fd=os.open(root,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)


@contextmanager
def locked(root):
    lock=root/'.writer-lock'
    try:lock.mkdir()
    except FileExistsError:raise ValueError('Task is locked; inspect the existing writer before recovery')
    try:yield
    finally:lock.rmdir()


def read(root):
    root=Path(root);data=json.loads((root/'task.json').read_text())
    if data.get('schema_version') not in (1,2):raise ValueError('Unsupported task schema')
    if 'failure_recovery_version' in data and (data['schema_version']!=2 or type(data['failure_recovery_version']) is not int or data['failure_recovery_version']!=1):
        raise ValueError('Unsupported failure recovery version')
    # Normalize legacy records in memory; reading must not rewrite evidence.
    check_preview_origin(root,data)
    refresh_delivery_status(data)
    return data


def failure_recovery(data):
    return data['schema_version']==2 and data.get('failure_recovery_version')==1


def retain_failure(root,row,source,kind,reason):
    """Keep the exact local receipt/result, including invalid image bytes."""
    source=Path(source)
    if not source.is_file() or (kind=='provider' and not source.stat().st_size):
        raise ValueError('A nonempty local terminal failure receipt is required')
    out=root/'failures'/f"look-{row['number']}-attempt-{row.get('attempt_number',1)}-{kind}{source.suffix or '.bin'}"
    out.parent.mkdir(exist_ok=True)
    if out.exists():
        if digest(out)!=digest(source):raise ValueError('Existing failure evidence differs; reconcile the original file without overwriting it')
    else:
        with source.open('rb') as src,out.open('xb') as dst:
            shutil.copyfileobj(src,dst);dst.flush();os.fsync(dst.fileno())
    return dict(kind=kind,reason=reason,evidence=dict(file=str(out.relative_to(root)),sha256=digest(out)),at=stamp())


def create(root,refs,prompts,size,identity=True,*,schema_version=2,model=None,context=None,route=None,model_package=None,real_face_plan=None,shot_plan=None):
    root=Path(root)
    if route is None:route='chatgpt_web' if schema_version==1 else 'codex_native'
    if model_package is not None:
        if schema_version!=2 or not identity or model is not None:raise ValueError('Package use requires a new portrait task and no conflicting inline model')
        card=models.load_package(model_package);model=card['model']
        refs=list(refs)+[dict(path=str(Path(model_package)/r['file']),role='identity-reference') for r in card['references']]
        refs += [dict(path=str(Path(model_package)/r['file']), **{k:r[k] for k in ('role','sha256','scope','confirmation_note')})
                 for r in card.get('supplements', [])]
    if schema_version not in (1,2):raise ValueError('Unsupported task schema')
    if len(prompts) not in (1,6) or not all(isinstance(p,str) and p.strip() for p in prompts):
        raise ValueError('Provide exactly one or six nonempty frozen prompts')
    if not refs or len(size)!=2 or any(type(v)!=int or v<=0 for v in size):
        raise ValueError('Real garment references and positive exact dimensions required')
    if route not in ('chatgpt_web','codex_native'):raise ValueError('Unsupported native route')
    if schema_version==1:
        if model is not None or context is not None or route!='chatgpt_web':raise ValueError('Legacy task interface is unchanged')
        items=[dict(path=p,role='garment-source') for p in refs]
    else:
        context=context_check(context,size)
        if 'photography_targets' in context:photography_helper().strict_check(context['photography_targets'])
        if context.get('purpose')=='model-check' and (not identity or len(prompts)!=1):
            raise ValueError('model-check is a single portrait diagnostic, not a six-pose delivery')
        if identity:
            model=models.validate_model(model or dict(source_type='new',scope='full',subject='adult model',locked=[],adjustable=[],consent_note=''),allow_child=True)
        elif model is not None:raise ValueError('Non-portrait tasks cannot carry a model')
        items=[dict(path=p,role='garment-source') if isinstance(p,(str,Path)) else dict(p) for p in refs]
        for i,item in enumerate(items):
            if item.get('role')=='model-supplement':
                items[i]=dict(models.validate_supplement({k:v for k,v in item.items() if k!='role'}),role='model-supplement')
            elif set(item)!={'path','role'} or item['role'] not in ('garment-source','identity-reference','aesthetic-reference','edit-target'):
                raise ValueError('Declare an explicit reference role')
        if not any(x['role']=='garment-source' for x in items):raise ValueError('A model/photo/card is not a garment source')
        has_identity=any(x['role']=='identity-reference' for x in items)
        if any(x['role']=='model-supplement' for x in items) and not has_identity:
            raise ValueError('An accepted supplement requires the original identity reference')
        if not identity and any(x['role']!='garment-source' for x in items):raise ValueError('Non-portrait task cannot carry person references')
        if identity and (has_identity != (model['source_type'] in ('ai','real'))):raise ValueError('Existing models need original identity references; new models do not copy identity')
        presentation_check(context, items, len(prompts), identity, model)
    for prompt in prompts:
        photography_helper().apply(prompt, context.get('photography_targets') if schema_version==2 else None)
    sources=[Path(x['path']).resolve() for x in items]
    if any(not p.is_file() or p.suffix.lower() not in ('.png','.jpg','.jpeg','.webp') for p in sources):
        raise ValueError('References must be existing image files')
    for source in sources:models.validate_image(source)
    if schema_version==2:
        identities=[digest(p) for p,item in zip(sources,items) if item['role'] in ('identity-reference','model-supplement')]
        if len(identities)!=len(set(identities)):
            raise ValueError('Deduplicate identical identity references before task initialization and prompt numbering')
    inventory=[dict(sha256=digest(p),role=item['role']) for p,item in zip(sources,items)]
    if schema_version==2 and context.get('purpose')=='preview-grid' and identity and model['source_type']=='real' and real_face_plan is None:
        raise ValueError('A real-person preview requires six declared cell plans and original view coverage')
    if real_face_plan is not None:
        plan_count=face_plan_count(context,len(prompts))
        real_face_plan=real_face_helper().validate(real_face_plan,inventory,schema_version=schema_version,identity=identity,
            model=model,context=context,count=plan_count,route=route,strict_looks=range(1,plan_count+1))
        if context.get('purpose')=='preview-grid':
            selected={h for look in real_face_plan['looks'] for h in look['reference_sha256s']}
            native_reference_check([r for r in inventory if r['sha256'] in selected],route)
    elif shot_plan is None:
        native_reference_check(items,route,extra_anchor=int(identity and len(prompts)==6))
    if shot_plan is not None:
        if schema_version!=2:raise ValueError('Shot plans require schema 2')
        shot_plan=shot_helper().validate(shot_plan,inventory,context=context,
            count=face_plan_count(context,len(prompts)),identity=identity,real_face_plan=real_face_plan)
        for number,prompt in enumerate(prompts,1):
            chosen=shot_helper().selected(shot_plan,number,context.get('purpose')=='preview-grid')
            actual=[r for r in inventory if r['role']!='garment-source' or r['sha256'] in chosen]
            if real_face_plan is not None:
                face_rows=real_face_plan['looks'] if context.get('purpose')=='preview-grid' else [real_face_plan['looks'][number-1]]
                face_selected={h for cell in face_rows for h in cell['reference_sha256s']}
                actual=[r for r in actual if r['sha256'] in face_selected]
            native_reference_check(actual,route,extra_anchor=int(identity and len(prompts)==6 and number>1))
            shot_helper().apply(prompt,shot_plan,None if context.get('purpose')=='preview-grid' else number,real_face_plan)
    if schema_version==2:
        for number,prompt in enumerate(prompts,1):prompt_check(prompt,context,model,shot_plan,number,real_face_plan)
    root.mkdir(parents=True,exist_ok=False)
    try:
        (root/'references').mkdir();frozen=[]
        for i,(p,item) in enumerate(zip(sources,items),1):
            out=root/'references'/f'{i:02d}{p.suffix.lower()}';shutil.copyfile(p,out)
            models.validate_image(out)
            frozen.append({'file':str(out.relative_to(root)),'sha256':digest(out),'role':item['role']})
            if item['role']=='model-supplement':
                if frozen[-1]['sha256']!=item['sha256']:raise ValueError('Accepted supplement changed during snapshot')
                frozen[-1].update(scope=item['scope'],confirmation_note=item['confirmation_note'])
        data={'schema_version':schema_version,'created_at':stamp(),'route':route,'mode':'manual','model_verified':False,
              'size':list(size),'identity':bool(identity),'references':frozen,'authorization':None,'attempts':0,
              'complete':False,'delivery_status':'prepared','events':[],
              'looks':[{'number':i,'prompt':p,'prompt_sha256':hashlib.sha256(p.encode()).hexdigest(),'state':'pending'} for i,p in enumerate(prompts,1)]}
        if schema_version==2:
            data.update(context=context,context_sha256=object_hash(context),model=model,model_sha256=object_hash(model),model_confirmation=None,
                        references_sha256=object_hash(frozen),failure_recovery_version=1)
        if real_face_plan is not None:
            real_face_plan=real_face_helper().validate(real_face_plan,frozen,schema_version=schema_version,identity=identity,
                model=model,context=context,count=plan_count,route=route,strict_looks=range(1,plan_count+1))
            data.update(real_face_plan=real_face_plan,real_face_plan_sha256=object_hash(real_face_plan))
        if shot_plan is not None:
            data.update(shot_plan=shot_plan,shot_plan_sha256=object_hash(shot_plan),plan_version=0)
        save(root,data);return data
    except Exception:
        shutil.rmtree(root)
        raise


def references(root,data,look):
    check_model_confirmation(data)
    check_reference_metadata(root,data)
    if not 1<=look<=len(data['looks']):raise ValueError('Unknown look number')
    row=data['looks'][look-1]
    if hashlib.sha256(row['prompt'].encode()).hexdigest()!=row['prompt_sha256']:raise ValueError('Frozen prompt changed')
    if is_preview(data) and 'real_face_plan' in data:
        selected={h for cell in data['real_face_plan']['looks'] for h in cell['reference_sha256s']}
        rows=[r for r in data['references'] if r['sha256'] in selected]
    else:
        rows=(real_face_helper().selected(data['real_face_plan'],data['references'],look)
              if 'real_face_plan' in data else list(data['references']))
    if 'shot_plan' in data:
        selected=shot_helper().selected(data['shot_plan'],look,is_preview(data))
        rows=[r for r in rows if r['role']!='garment-source' or r['sha256'] in selected]
    if data['schema_version']==2 and data['identity'] and look>1 and not data['model_confirmation']:
        raise ValueError('First-image model has not been confirmed by the user')
    if data['identity'] and look>1:
        anchor=data['looks'][0]
        if anchor['state']!='accepted':raise ValueError('look-1 has not passed visual anchor QA')
        rows=rows+[dict(anchor['output'],role='identity-only')]
        if data['schema_version']==2 and 'real_face_plan' not in data:
            seen=set();unique=[]
            for ref in rows:
                key=(ref['sha256'], 'identity' if ref['role'] in ('identity-reference','model-supplement','identity-only') else ref['role'])
                if key not in seen:unique.append(ref);seen.add(key)
            rows=unique
    for row in rows:
        if digest(safe_file(Path(root),row['file']))!=row['sha256']:raise ValueError('Frozen reference/anchor changed')
        models.validate_image(safe_file(Path(root),row['file']))
    native_reference_check(rows,data['route'])
    return rows


def reference_hashes(root,look):
    return [r['sha256'] for r in references(root,read(root),look)]


def progression_error(data, look):
    """Shared export/reserve gate: resolved non-anchor visual rejects are local.

    Original requests, invalid canvases/provider failures and the first anchor
    remain blocking. A visual rejection is never promoted to acceptance here.
    Schema 1 retains its existing strict order.
    """
    if is_preview(data) and data.get('preview_decision'):
        return 'Preview task is closed; no further preview submissions'
    if data['schema_version']==1:
        return 'Earlier look is unresolved or not accepted' if any(
            x['state']!='accepted' for x in data['looks'][:look-1]) else None
    if any(x['state'] in ('reserved','unknown') for x in data['looks']):
        return 'Recover the existing unresolved request before another submission'
    if any(x['state']=='failed' for x in data['looks']):
        return 'Resolve the retained provider/canvas failure before another submission'
    if data['identity'] and look>1:
        if data['looks'][0]['state']!='accepted':
            return 'look-1 has not passed visual anchor QA'
        if not data['model_confirmation']:
            return 'First-image model has not been confirmed by the user'
    for prior in data['looks'][:look-1]:
        if prior['state']=='accepted':
            continue
        if (prior['number']>1 and prior['state']=='rejected' and prior.get('output')
                and prior.get('qa')=='qa-retry' and not prior.get('model_rejected')):
            continue
        return 'Earlier look is pending, unreviewed or an invalid first image'
    return None


def evidence_rows(data):
    for row in data['looks']:
        yield from row.get('history', [])
        yield row


def canvas_baseline(data):
    """Derive from retained first-look evidence, including rejected/retried outputs."""
    if data.get('context', {}).get('canvas_policy', 'exact') == 'exact':
        return data['size']
    first=data['looks'][0]
    for row in [*first.get('history', []), first]:
        if 'output' in row:return row['output']['dimensions']
    return None


def canvas_matches(data, dimensions):
    w,h=data['size']
    baseline=canvas_baseline(data)
    return dimensions[0]*h==dimensions[1]*w and (baseline is None or dimensions==baseline)


def canvas_instruction(data):
    baseline=canvas_baseline(data)
    if baseline is not None:return f'Exact canvas: {baseline[0]}x{baseline[1]}.'
    w,h=data['size'];divisor=math.gcd(w,h)
    return f'Canvas aspect ratio: {w//divisor}:{h//divisor}. First compliant original establishes the exact pixel baseline for this task.'


def check_model_confirmation(data):
    if data['schema_version']==2 and data.get('model_confirmation'):
        confirmation=data['model_confirmation']
        if (not isinstance(confirmation,dict) or not isinstance(confirmation.get('note'),str)
                or not confirmation['note'].strip()
                or confirmation.get('output_sha256')!=data['looks'][0].get('output',{}).get('sha256')):
            raise ValueError('Model confirmation does not bind the current first-image output')


def check_real_face_plan(root,data):
    fields={'real_face_plan','real_face_plan_sha256','real_face_plan_history'} & set(data)
    if not fields:return
    if not {'real_face_plan','real_face_plan_sha256'} <= fields:
        raise ValueError('Real face plan requires its frozen metadata hash')
    if 'references_sha256' not in data or object_hash(data['references'])!=data['references_sha256']:
        raise ValueError('Real face plan requires the frozen full-inventory role/acceptance hash')
    if object_hash(data['real_face_plan'])!=data['real_face_plan_sha256']:
        raise ValueError('Frozen real face plan changed')
    if (data['schema_version']!=2 or object_hash(data['model'])!=data['model_sha256']
            or object_hash(data['context'])!=data['context_sha256']):
        raise ValueError('Frozen real-person source/context changed')
    real_face_helper().validate(data['real_face_plan'],data['references'],schema_version=data['schema_version'],
        identity=data['identity'],model=data['model'],context=data['context'],count=face_plan_count(data['context'],len(data['looks'])),route=data['route'])
    history=data.get('real_face_plan_history',[])
    if (not isinstance(history,list) or len(history)>1
            or (bool(data.get('continuation_authorization')) and len(history)!=1)):
        raise ValueError('Invalid real face plan extension history')
    for prior in history:
        if (not isinstance(prior,dict) or set(prior)!={'plan','sha256','note','at'}
                or not real_face_helper().text(prior['note']) or not real_face_helper().text(prior['at'])
                or object_hash(prior['plan'])!=prior['sha256']
                or len(data['looks'])!=6 or not data.get('continuation_authorization')):
            raise ValueError('Frozen real face plan history changed')
        real_face_helper().validate(prior['plan'],data['references'],schema_version=2,identity=data['identity'],
            model=data['model'],context=data['context'],count=1,route=data['route'])
        current=data['real_face_plan']
        if (prior['plan']['primary_identity_sha256']!=current['primary_identity_sha256']
                or prior['plan']['coverage']!=current['coverage']
                or prior['plan']['looks'][0]!=current['looks'][0]):
            raise ValueError('Continuation cannot replace original face coverage or first-look plan')
    for ref in data['references']:
        file=safe_file(Path(root),ref['file'])
        if digest(file)!=ref['sha256']:raise ValueError('Frozen inventory changed, including unselected references')
        models.validate_image(file)


def check_reference_metadata(root,data):
    check_real_face_plan(root,data)
    if data['schema_version']!=2:return
    supplements=[r for r in data['references'] if r['role']=='model-supplement']
    if supplements and 'references_sha256' not in data:
        raise ValueError('Supplemental reference acceptance requires its frozen metadata hash')
    if 'references_sha256' in data and object_hash(data['references'])!=data['references_sha256']:
        raise ValueError('Frozen reference roles/acceptance changed')
    if supplements and (not data['identity'] or data['model']['source_type'] not in ('ai','real')
                        or not any(r['role']=='identity-reference' for r in data['references'])):
        raise ValueError('Supplement requires an existing original identity')
    for row in supplements:
        if set(row)!={'file','sha256','role','scope','confirmation_note'}:
            raise ValueError('Unsupported frozen supplement fields')
        models.validate_supplement(dict(path=str(safe_file(Path(root),row['file'])),
                                        **{k:row[k] for k in ('sha256','scope','confirmation_note')}))


def check_preview_origin(root,data):
    if 'preview_origin' in data:
        origin=data['preview_origin']
        snapshot=safe_file(root,'provenance/preview-task.json')
        if digest(snapshot)!=origin['snapshot_sha256']:
            raise ValueError('Preview provenance snapshot changed')
        prior=json.loads(snapshot.read_text())
        if (not is_preview(prior) or not prior.get('preview_decision') or prior['looks'][0]['state']!='accepted'
                or origin['attempts']!=prior['attempts'] or is_preview(data)
                or digest(safe_file(root,'provenance/preview.png'))!=prior['looks'][0]['output']['sha256']):
            raise ValueError('Invalid preview provenance or cumulative request count')


def check_evidence(root,data):
    check_shot_plan(data)
    check_preview_origin(root,data)
    check_model_confirmation(data)
    check_reference_metadata(root,data)
    if data['schema_version']==2:
        if object_hash(data['context'])!=data['context_sha256'] or object_hash(data['model'])!=data['model_sha256']:
            raise ValueError('Frozen context/model changed')
        context_check(data['context'],data['size'])
        if data['identity']:models.validate_model(data['model'],allow_child=True)
        presentation_check(data['context'], data['references'], len(data['looks']), data['identity'], data['model'])
        if is_preview(data) and (data.get('model_confirmation') or len(data.get('retry_authorizations',[]))>3):
            raise ValueError('A preview cannot confirm identity or exceed three correction requests')
    if 'plan_version' in data and (type(data['plan_version']) is not int or data['plan_version']<0):
        raise ValueError('Invalid current plan version')
    candidate=data.get('preview_revision')
    if candidate:
        row=data['looks'][0]
        if (not is_preview(data) or candidate.get('output_sha256')!=row.get('output',{}).get('sha256')
                or candidate.get('base_plan_sha256')!=plan_fingerprint(data)
                or object_hash(candidate['candidate'])!=candidate.get('candidate_sha256')
                or not candidate.get('note','').strip()):
            raise ValueError('Preview revision no longer binds the reviewed output/current plan')
        checked=preview_candidate(data,row,**candidate['candidate'])
        if checked!=candidate['candidate']:raise ValueError('Invalid preview candidate')
    for row in evidence_rows(data):
        if hashlib.sha256(row['prompt'].encode()).hexdigest()!=row['prompt_sha256']:
            raise ValueError('Frozen prompt changed')
        photography_helper().apply(row['prompt'], data['context'].get('photography_targets') if data['schema_version']==2 else None)
        if data['schema_version']==2 and data['identity']:
            models.apply_conditions(row['prompt'],row.get('model',data['model']),allow_child=True)
        if row in data['looks'] and 'shot_plan' in data:
            shot_helper().apply(row['prompt'],data['shot_plan'],None if is_preview(data) else row['number'],data.get('real_face_plan'))
        history=row.get('prompt_history',[])
        revision=row.get('plan_revision',0)
        if type(revision) is not int or revision<0 or not isinstance(history,list) or len(history)!=revision:
            raise ValueError('Invalid pending-prompt revision history')
        for i,prior in enumerate(history):
            if (prior.get('revision')!=i or not prior.get('note','').strip()
                    or hashlib.sha256(prior['prompt'].encode()).hexdigest()!=prior['prompt_sha256']):
                raise ValueError('Historical prompt revision changed')
            photography_helper().apply(prior['prompt'], data['context'].get('photography_targets') if data['schema_version']==2 else None)
        if 'real_face_plan' in row and object_hash(row['real_face_plan'])!=row.get('real_face_plan_sha256'):
            raise ValueError('Historical real face plan changed')
        if 'shot_plan' in row and object_hash(row['shot_plan'])!=row.get('shot_plan_sha256'):
            raise ValueError('Historical shot plan changed')
        if 'model' in row and object_hash(row['model'])!=row['model_sha256']:raise ValueError('Historical model conditions changed')
        if 'output' in row and digest(safe_file(root,row['output']['file']))!=row['output']['sha256']:
            raise ValueError('Previously imported output changed')
        if data['schema_version']==2 and 'output' in row:
            actual=png_size(safe_file(root,row['output']['file']))
            if not canvas_matches(data,actual) or actual!=row['output']['dimensions']:
                raise ValueError('Previously imported output has wrong canvas')
        reviews=row.get('qa_history',[])
        if not isinstance(reviews,list):raise ValueError('Invalid QA review history')
        for review in reviews:
            if (not isinstance(review,dict) or review.get('qa') not in ('qa-pass','qa-user-review','qa-retry')
                    or review.get('state') not in ('accepted','rejected')
                    or any(not isinstance(review.get(k),str) or not review[k].strip() for k in ('qa_note','at'))):
                raise ValueError('Invalid QA review history record')
            # Older audit-reject records predate output hash binding.
            if 'output_sha256' in review and review['output_sha256']!=row.get('output',{}).get('sha256'):
                raise ValueError('Historical QA review does not bind this output')
        if 'failure' in row:
            failure=row['failure'];evidence=failure['evidence']
            if not failure_recovery(data) or failure['kind'] not in ('provider','invalid-result') or not failure['reason'].strip():
                raise ValueError('Invalid retained failure record')
            if digest(safe_file(root,evidence['file']))!=evidence['sha256']:
                raise ValueError('Retained failure evidence changed')
        if 'failure_reconciliation' in row:
            checked=row['failure_reconciliation']
            if (not checked['note'].strip() or checked.get('request_check_completed') is not True
                    or checked['attempt_number']!=row.get('attempt_number',1)
                    or checked['failure_sha256']!=object_hash(row.get('failure'))):
                raise ValueError('Failure reconciliation no longer binds this failed attempt')
    for ref in data['references']:
        if digest(safe_file(root,ref['file']))!=ref['sha256']:raise ValueError('Frozen reference changed')
        models.validate_image(safe_file(root,ref['file']))


def safe_file(root,relative):
    path=Path(relative);resolved=(root/path).resolve()
    if path.is_absolute() or '..' in path.parts or not resolved.is_relative_to(root.resolve()):
        raise ValueError('Task file escapes private directory')
    return resolved


def update(root,event,**kw):
    root=Path(root)
    with locked(root):
        d=read(root);n=kw.get('look');row=None;stop_error=None
        check_evidence(root,d)
        if is_preview(d) and d.get('preview_decision'):
            raise ValueError('Preview task is closed; create a linked independent delivery instead')
        if is_preview(d) and event in ('confirm-model','reject-model','continue-authorize'):
            raise ValueError('A preview is not an accepted identity or delivery look-1')
        if kw.get('real_face_looks') is not None and event!='continue-authorize':
            raise ValueError('real_face_looks is only accepted for explicit continuation')
        if n is not None:
            if type(n)!=int or not 1<=n<=len(d['looks']):raise ValueError('Unknown look number')
            row=d['looks'][n-1]
        if event=='revise-preview':
            note=kw.get('note','').strip()
            if (not is_preview(d) or n!=1 or row['state'] not in ('accepted','rejected')
                    or not note or kw.get('expected_output_sha256')!=row.get('output',{}).get('sha256')):
                raise ValueError('Revise only an exact reviewed, open preview output with actual user feedback')
            candidate=preview_candidate(d,row,model=kw.get('model'),shot_plan=kw.get('shot_plan'),prompt=kw.get('prompt'),garment_references=kw.get('garment_references'))
            if d.get('preview_revision'):d.setdefault('preview_revision_history',[]).append(d['preview_revision'])
            d['preview_revision']=dict(candidate=candidate,candidate_sha256=object_hash(candidate),
                base_plan_sha256=plan_fingerprint(d),output_sha256=row['output']['sha256'],note=note,at=stamp())
        elif event=='finish-preview':
            decision=kw.get('decision');note=kw.get('note','').strip()
            if not is_preview(d) or n is not None or not note or decision not in ('stop','direction-confirmed'):
                raise ValueError('Record a task-level preview stop or actual direction confirmation')
            state=d['looks'][0]['state']
            if state in ('reserved','unknown') or (state=='failed' and not d['looks'][0].get('failure_reconciliation')):
                raise ValueError('Resolve the original preview request before closing it')
            if decision=='direction-confirmed' and (state!='accepted' or d.get('preview_revision')):
                raise ValueError('Confirm direction only after preview review')
            if state=='returned':raise ValueError('Review the returned preview before closing')
            d['preview_decision']=dict(decision=decision,note=note,at=stamp())
        elif event=='authorize':
            if d['authorization'] or d['attempts']:raise ValueError('Existing authorization/budget cannot be reset')
            limit=kw.get('limit');note=kw.get('note','').strip()
            if type(limit)!=int or not 1<=limit<=len(d['looks']) or not note:raise ValueError('Explicit ChatGPT upload and generation approval with limit required')
            d['authorization']={'destination':('ChatGPT' if d['schema_version']==1 else d['route']),'limit':limit,'note':note,'at':stamp()}
        elif event=='enable-failure-recovery':
            note=kw.get('note','').strip()
            if d['schema_version']!=2 or 'failure_recovery_version' in d or not note or n is not None:
                raise ValueError('Explicit task-level adoption note required for a legacy schema-2 task only')
            d.update(failure_recovery_version=1,failure_recovery_adoption=dict(note=note,at=stamp()))
        elif event=='reconcile-failure':
            note=kw.get('note','').strip()
            if not failure_recovery(d) or row is None or row['state']!='failed' or 'failure' not in row:
                raise ValueError('Reconcile only a retained, explicit failure under recovery v1; recover unknown requests first')
            if (type(kw.get('expected_attempt')) is not int or kw['expected_attempt']!=row.get('attempt_number',1)
                    or kw.get('request_check_completed') is not True or not note):
                raise ValueError('Match the failed attempt and record the completed original-request check')
            if row.get('failure_reconciliation'):raise ValueError('Failure already reconciled; additional calls still need explicit retry approval')
            row['failure_reconciliation']=dict(attempt_number=row.get('attempt_number',1),failure_sha256=object_hash(row['failure']),
                                                request_check_completed=True,note=note,at=stamp())
        elif event=='confirm-model':
            note=kw.get('note','').strip()
            if d['schema_version']!=2 or not d['identity'] or n!=1 or row['state']!='accepted' or not note:
                raise ValueError('Confirm only a QA-accepted first image with actual human visual approval')
            if d['model_confirmation']:raise ValueError('Model confirmation already recorded')
            d['model_confirmation']={'note':note,'output_sha256':row['output']['sha256'],'at':stamp()}
        elif event=='continue-authorize':
            note=kw.get('note','').strip();approval=kw.get('approval_id','').strip();prompts=kw.get('prompts')
            if d['schema_version']!=2 or len(d['looks'])!=1 or d['looks'][0]['state']!='accepted' or not d['authorization']:
                raise ValueError('Continue only the same accepted one-image task')
            if d['context'].get('purpose') in ('model-check', 'correction-edit'):
                raise ValueError(d['context']['purpose']+' cannot become look-1 of a production six-pose set')
            if d['identity'] and not d['model_confirmation']:raise ValueError('User must confirm the model first')
            if d['context']['first_pose']!=1:raise ValueError('Only an actual pose-1 trial can become look-1 of the six-pose set')
            if kw.get('context')!=d['context']:raise ValueError('Continuation must keep outfit, style, mode, output form and canvas')
            if not note or not approval or any(x['approval_id']==approval for x in d.get('retry_authorizations',[])):
                raise ValueError('Explicit five-image approval and a fresh ID required')
            if not isinstance(prompts,list) or len(prompts)!=5 or any(not isinstance(p,str) or not p.strip() for p in prompts):
                raise ValueError('Provide exactly five continuation prompts')
            for prompt in prompts:
                photography_helper().apply(prompt,d['context'].get('photography_targets'))
            continuation_plan=None
            if 'real_face_plan' in d:
                extra=kw.get('real_face_looks')
                if not isinstance(extra,list) or len(extra)!=5:
                    raise ValueError('Continue a planned real task with five explicit real_face_looks')
                continuation_plan=copy.deepcopy(d['real_face_plan'])
                continuation_plan['looks'].extend(copy.deepcopy(extra))
                real_face_helper().validate(continuation_plan,d['references'],schema_version=2,identity=d['identity'],
                    model=d['model'],context=d['context'],count=6,route=d['route'],strict_looks=range(2,7))
            elif kw.get('real_face_looks') is not None:
                raise ValueError('real_face_looks only extends an existing real_face_plan; do not retrofit old or AI tasks')
            elif 'shot_plan' not in d:
                future=list(d['references'])
                anchor=d['looks'][0]['output']
                if d['identity'] and not any(r['role'] in ('identity-reference','model-supplement') and r['sha256']==anchor['sha256'] for r in future):
                    future.append(dict(anchor,role='identity-only'))
                native_reference_check(future,d['route'])
            if 'shot_plan' in d:
                full=shot_helper().validate(kw.get('shot_plan'),d['references'],context=d['context'],count=6,
                    identity=d['identity'],real_face_plan=continuation_plan)
                prior=d['shot_plan']
                if any(full[k]!=prior[k] for k in ('sku','coverage','route','preservation','adaptation_note')) or full['looks'][0]!=prior['looks'][0]:
                    raise ValueError('Continuation cannot replace the approved first shot or original garment coverage')
                for i,prompt in enumerate(prompts,2):
                    prompt_check(prompt,d['context'],d['model'],full,i,continuation_plan)
                    chosen=shot_helper().selected(full,i)
                    actual=[r for r in d['references'] if r['role']!='garment-source' or r['sha256'] in chosen]
                    if continuation_plan is not None:
                        actual=[r for r in actual if r['sha256'] in continuation_plan['looks'][i-1]['reference_sha256s']]
                    anchor=d['looks'][0]['output']
                    if d['identity'] and not any(r['role'] in ('identity-reference','model-supplement') and r['sha256']==anchor['sha256'] for r in actual):
                        actual.append(dict(anchor,role='identity-only'))
                    native_reference_check(actual,d['route'])
                d['shot_plan_history']=[dict(plan=copy.deepcopy(prior),sha256=object_hash(prior),note=note)]
                d.update(shot_plan=full,shot_plan_sha256=object_hash(full),plan_version=d.get('plan_version',0)+1)
            if continuation_plan is not None:
                d['real_face_plan_history']=[dict(plan=copy.deepcopy(d['real_face_plan']),
                    sha256=d['real_face_plan_sha256'],note=note,at=stamp())]
                d.update(real_face_plan=continuation_plan,real_face_plan_sha256=object_hash(continuation_plan))
            for i,prompt in enumerate(prompts,2):prompt_check(prompt,d['context'],d['model'],d.get('shot_plan'),i,continuation_plan)
            d['continuation_authorization']={'approval_id':approval,'additional_requests':5,'note':note,'at':stamp()}
            d['looks'].extend({'number':i,'prompt':p,'prompt_sha256':hashlib.sha256(p.encode()).hexdigest(),'state':'pending'} for i,p in enumerate(prompts,2))
        elif event=='reject-model':
            note=kw.get('note','').strip()
            if d['schema_version']!=2 or not d['identity'] or n!=1 or row['state']!='accepted' or d['model_confirmation'] or not note or any(x['state']!='pending' for x in d['looks'][1:]):
                raise ValueError('Reject a model only before first-image human confirmation and downstream work')
            row.update(state='rejected',model_rejected=True,model_rejection_note=note)
        elif event=='reject':
            note=kw.get('note','').strip()
            if row is None or row['state']!='returned' or not note:raise ValueError('Reject only a downloaded result with actual visual QA reasons')
            row.update(state='rejected',qa='qa-retry',qa_note=note)
        elif event=='audit-reject':
            note=kw.get('note','').strip()
            if d['schema_version']!=2 or row is None or row['state']!='accepted' or not note:
                raise ValueError('Record a late source/identity QA rejection only for an accepted schema-2 output')
            row.setdefault('qa_history',[]).append(dict(qa=row['qa'],qa_note=row['qa_note'],state=row['state'],at=stamp()))
            row.update(state='rejected',qa='qa-retry',qa_note=note)
        elif event=='review-output':
            note=kw.get('note','').strip();qa=kw.get('qa')
            if (d['schema_version']!=2 or row is None or n==1
                    or row['state'] not in ('accepted','rejected') or not row.get('output')
                    or row.get('model_rejected') or not note or qa not in ('qa-pass','qa-user-review','qa-retry')):
                raise ValueError('Re-review only a returned, already reviewed non-anchor schema-2 image with actual QA reasons')
            if kw.get('expected_output_sha256')!=row['output']['sha256']:
                raise ValueError('Re-review must target the exact existing output hash')
            row.setdefault('qa_history',[]).append(dict(qa=row['qa'],qa_note=row['qa_note'],
                state=row['state'],output_sha256=row['output']['sha256'],at=stamp()))
            row.update(state='rejected' if qa=='qa-retry' else 'accepted',qa=qa,qa_note=note)
        elif event=='revise-pending':
            note=kw.get('note','').strip();prompt=kw.get('prompt','')
            if (d['schema_version']!=2 or row is None or row['state']!='pending'
                    or row.get('history') or row.get('output') or row.get('submitted_at')
                    or row.get('attempt_number',1)!=1 or not note
                    or not isinstance(prompt,str) or not prompt.strip() or prompt==row['prompt']):
                raise ValueError('Revise only a never-submitted schema-2 look with a changed prompt and actual user plan approval')
            if any(x['state'] in ('reserved','unknown') for x in d['looks']):
                raise ValueError('Resolve the existing request before changing pending plans')
            if kw.get('expected_prompt_sha256')!=row['prompt_sha256']:
                raise ValueError('Pending revision must target the current frozen prompt hash')
            prompt_check(prompt,d['context'],d['model'],d.get('shot_plan'),n,d.get('real_face_plan'))
            revision=row.get('plan_revision',0)
            row.setdefault('prompt_history',[]).append(dict(prompt=row['prompt'],
                prompt_sha256=row['prompt_sha256'],revision=revision,note=note,at=stamp()))
            row.update(prompt=prompt,prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),plan_revision=revision+1)
        elif event=='retry-authorize':
            if is_preview(d) and len(d.get('retry_authorizations',[]))>=3:
                raise ValueError('Preview correction limit reached: three additional requests maximum')
            # One explicit grant replaces one rejected/reconciled failed attempt, never resets the task.
            proposal=d.get('preview_revision') if is_preview(d) else None
            note=kw.get('note','').strip();approval=kw.get('approval_id','').strip()
            prompt=kw.get('prompt',proposal['candidate']['prompt'] if proposal else '')
            if proposal:
                for key in ('model','shot_plan','prompt','garment_references'):
                    if key in kw and kw[key]!=proposal['candidate'].get(key):
                        raise ValueError('Retry must use the reviewed preview revision candidate')
            grants=d.get('retry_authorizations',[])
            failed_ready=(row is not None and row['state']=='failed' and failure_recovery(d) and row.get('failure_reconciliation'))
            if row is None or (row['state']!='rejected' and not failed_ready and not (proposal and row['state']=='accepted')) or not d['authorization']:
                raise ValueError('Retry only a visually rejected result or a reconciled failure with retained evidence; recover unknown requests first')
            attempt=row.get('attempt_number',1)
            if type(kw.get('expected_attempt'))!=int or kw['expected_attempt']!=attempt:raise ValueError('Approval must target the current rejected/failed attempt')
            if not note or not approval or not isinstance(prompt,str) or not prompt.strip():raise ValueError('Explicit retry approval, unique approval ID and corrected prompt required')
            photography_helper().apply(prompt,d['context'].get('photography_targets') if d['schema_version']==2 else None)
            if any(g['approval_id']==approval for g in grants) or d.get('continuation_authorization',{}).get('approval_id')==approval:raise ValueError('Retry approval already used')
            if (d['schema_version']==1 or n==1) and any(x['state']!='pending' for x in d['looks'][n:]):raise ValueError('Cannot replace an anchor with existing downstream work')
            history=copy.deepcopy(row.get('history',[]));old=copy.deepcopy(row);old.pop('history',None)
            if d['schema_version']==2 and d['model']:
                old.update(model=copy.deepcopy(d['model']),model_sha256=d['model_sha256'])
            if 'shot_plan' in d:
                old.update(shot_plan=copy.deepcopy(d['shot_plan']),shot_plan_sha256=d['shot_plan_sha256'])
            if proposal:
                candidate=preview_candidate(d,row,**proposal['candidate'])
                for ref in candidate.get('garment_references',[]):
                    path=Path(ref['path']);out=root/'references'/('added-'+ref['sha256']+path.suffix.lower())
                    if out.exists() and digest(out)!=ref['sha256']:raise ValueError('Existing added garment file changed')
                    if not out.exists():shutil.copyfile(path,out)
                    if digest(out)!=ref['sha256']:raise ValueError('Additional garment source changed during snapshot')
                    d['references'].append(dict(file=str(out.relative_to(root)),sha256=ref['sha256'],role='garment-source'))
                d['references_sha256']=object_hash(d['references'])
                d.update(model=copy.deepcopy(candidate['model']),model_sha256=object_hash(candidate['model']),
                         plan_version=d.get('plan_version',0)+1)
                if candidate['shot_plan'] is not None:
                    d.update(shot_plan=copy.deepcopy(candidate['shot_plan']),shot_plan_sha256=object_hash(candidate['shot_plan']))
                if 'real_face_plan' in candidate:
                    old.update(real_face_plan=copy.deepcopy(d['real_face_plan']),real_face_plan_sha256=d['real_face_plan_sha256'])
                    d.update(real_face_plan=copy.deepcopy(candidate['real_face_plan']),real_face_plan_sha256=object_hash(candidate['real_face_plan']))
                old['preview_revision']=copy.deepcopy(proposal)
                d.pop('preview_revision')
            elif kw.get('shot_plan') is not None:
                raise ValueError('Change shot plans through a reviewed preview revision')
            if kw.get('model') is not None and not proposal:
                if d['schema_version']!=2 or n!=1 or not row.get('model_rejected') or d['model_confirmation']:raise ValueError('Model revision requires explicit unconfirmed-first-model rejection')
                changed=models.validate_model(kw['model'],allow_child=True)
                if any(changed[k]!=d['model'][k] for k in ('source_type','scope','subject')):raise ValueError('A different identity/source/scope requires a new declared model version, not replacement of original references')
                d.update(model=changed,model_sha256=object_hash(changed))
            if d['schema_version']==2 and n==1 and d['model_confirmation']:
                old['model_confirmation']=copy.deepcopy(d['model_confirmation'])
                d['model_confirmation']=None
            if d['schema_version']==2:prompt_check(prompt,d['context'],d['model'],d.get('shot_plan'),n,d.get('real_face_plan'))
            history.append(old)
            grant={'approval_id':approval,'look':n,'rejected_attempt':attempt,'additional_requests':1,'note':note,'at':stamp(),'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest()}
            if failed_ready:
                grant.pop('rejected_attempt')
                grant.update(source_state='failed',failed_attempt=attempt)
            row.clear();row.update(number=n,state='pending',attempt_number=attempt+1,prompt=prompt,prompt_sha256=grant['prompt_sha256'],history=history)
            d.setdefault('retry_authorizations',[]).append(grant)
        elif event=='mode':
            if kw.get('mode') not in ('manual','automatic'):raise ValueError('Unknown mode')
            d['mode']=kw['mode']
        elif event=='reserve':
            auth=d['authorization']
            if not auth or d['attempts']>=auth['limit']+len(d.get('retry_authorizations',[]))+d.get('continuation_authorization',{}).get('additional_requests',0):raise ValueError('No authorized request budget remains')
            if row is None or row['state']!='pending':raise ValueError('Submission already reserved or no pending look')
            if ('plan_version' in d or kw.get('expected_plan_sha256') is not None) and kw.get('expected_plan_sha256')!=plan_fingerprint(d):
                raise ValueError('Reserve the current plan fingerprint; stale handoffs cannot be submitted')
            blocked=progression_error(d,n)
            if blocked:raise ValueError(blocked)
            if ((row.get('plan_revision',0)>0 or kw.get('expected_prompt_sha256') is not None)
                    and kw.get('expected_prompt_sha256')!=row['prompt_sha256']):
                raise ValueError('Reserve the current revised prompt; stale handoffs must not be submitted')
            expected=[x['sha256'] for x in references(root,d,n)]
            if kw.get('refs')!=expected or kw.get('ready') is not True:raise ValueError('Check login, persistent chat, prompt and completed attachment order before reserving')
            url=kw.get('conversation','');u=urlparse(url)
            if d['route']=='chatgpt_web' and (u.scheme!='https' or u.hostname!='chatgpt.com' or not ((u.path.startswith('/c/') and u.path[3:]) or (u.path in ('','/') and kw.get('tab','').strip()))):raise ValueError('Provide the observed persistent conversation, or a new-chat URL plus stable browser tab handle')
            row.update(state='reserved',conversation=url,tab=kw.get('tab'),submitted_at=stamp(),reference_hashes=expected)
            if d['schema_version']==2:row['submitted_prompt_sha256']=row['prompt_sha256']
            d['attempts']+=1
        elif event=='bind':
            u=urlparse(kw.get('conversation',''))
            if row is None or row['state'] not in ('reserved','unknown') or u.scheme!='https' or u.hostname!='chatgpt.com' or not u.path.startswith('/c/') or not u.path[3:]:raise ValueError('Bind only an observed persistent URL to the existing reserved request')
            row['conversation']=kw['conversation']
        elif event=='failed' and failure_recovery(d):
            if row is None or (row['state'] not in ('reserved','unknown') and not (row['state']=='failed' and 'failure' not in row)):
                raise ValueError('No submitted request needing a terminal failure receipt')
            reason=kw.get('reason','').strip();receipt=kw.get('failure_receipt')
            if not reason or receipt is None:raise ValueError('Explicit terminal failure reason and a local failure receipt required')
            row.update(state='failed',failure=retain_failure(root,row,receipt,'provider',reason))
        elif event in ('unknown','failed'):
            if row is None or row['state'] not in ('reserved','unknown'):raise ValueError('No pending submitted request')
            row['state']=event
        elif event=='returned':
            if row is None or row['state'] not in ('reserved','unknown'):raise ValueError('No reserved result to recover')
            source=Path(kw['file'])
            try:
                dimensions=png_size(source);sha=digest(source)
                if not canvas_matches(d,dimensions):raise ValueError('Wrong canvas: stop without another generation call')
                if sha in [x.get('output',{}).get('sha256') for x in evidence_rows(d)]:raise ValueError('Duplicate output image')
            except ValueError as error:
                if not failure_recovery(d):raise
                row.update(state='failed',failure=retain_failure(root,row,source,'invalid-result',str(error)))
                stop_error=ValueError(str(error)+'; exact original retained as failed; reconcile before any explicit retry')
            if stop_error is None:
                suffix=f"-attempt-{row['attempt_number']}" if row.get('attempt_number',1)>1 else '';out=root/'outputs'/f'look-{n}{suffix}.png';out.parent.mkdir(exist_ok=True)
                with out.open('xb') as f:f.write(source.read_bytes())
                row.update(state='returned',output={'file':str(out.relative_to(root)),'sha256':sha,'dimensions':dimensions})
        elif event=='accept':
            if row is None or row['state']!='returned':raise ValueError('No downloaded result for visual QA')
            if kw.get('qa') not in ('qa-pass','qa-user-review') or not kw.get('note','').strip():raise ValueError('Record actual visual QA and anchor suitability')
            if digest(root/row['output']['file'])!=row['output']['sha256']:raise ValueError('Output changed since import')
            row.update(state='accepted',qa=kw['qa'],qa_note=kw['note'])
        else:raise ValueError('Unknown event')
        d['complete']=(bool(d.get('preview_decision')) if is_preview(d) else
            all(x['state']=='accepted' for x in d['looks']) and (d['schema_version']==1 or not d['identity'] or bool(d['model_confirmation'])))
        # Completeness never confers image-ready or user commercial acceptance.
        d['events'].append({'at':stamp(),'event':event,'look':n,'attempts':d['attempts']})
        save(root,d)
        if stop_error is not None:raise stop_error
        return d


def export(root):
    root=Path(root)
    with locked(root):
        d=read(root);check_evidence(root,d);folder=root/'handoff';folder.mkdir(exist_ok=True);lines=['# ChatGPT 网页转交包','只用内置生图；不要选择其他插件。','参考图按编号上传，确认全部完成；使用新建持久对话。','提交前必须由 Codex 记录 reserve；本包不是新的生图授权。','点击网页原图下载，不使用截图；将原文件回传给 Codex。','尚未确认的请求先查原对话，不要再次发送。','']
        if d['route']=='codex_native':
            lines=['# Codex 原生生成执行包','参考图按编号作为实际工具附件传入；只用原生生图。','调用前记录 reserve；本包不是新的生图授权。','原图返回后落盘、读取元数据并记录 QA。','未决调用先检查原结果，不自动追加调用。','']
        for row in d['looks']:
            n=row['number'];lines.append(f"- look-{n}: {row['state']}")
            if row['state']!='pending' or progression_error(d,n):continue
            refs=references(root,d,n);suffix=f"-attempt-{row['attempt_number']}" if row.get('attempt_number',1)>1 else ''
            if row.get('plan_revision',0):suffix+=f"-plan-{row['plan_revision']}"
            if 'plan_version' in d:suffix+=f"-v{d['plan_version']}"
            out=folder/f'look-{n}{suffix}';out.mkdir(exist_ok=True);lines.append(f'  Current handoff: {out.name}; earlier attempt/plan folders are evidence only, never resubmit them.')
            instruction=[]
            for i,r in enumerate(refs,1):
                src=root/r['file'];dst=out/f'{i:02d}-{r["role"]}{src.suffix}'
                if dst.exists() and digest(dst)!=r['sha256']:raise ValueError('Existing handoff attachment changed')
                shutil.copyfile(src,dst)
                instruction.append(f'Image {i}: '+(models.supplement_prompt(r) if r['role']=='model-supplement' else ROLE_TEXT[r['role']]))
            # Current model is rendered once after the frozen prose, never as a second source.
            if d['schema_version']==2 and d['context']['first_pose']=='custom':
                instruction.append('Explicit user presentation: '+d['context']['pose_description']+
                                   ' This overrides conflicting default pose/framing, not garment facts or original model conditions.')
            if d['schema_version']==2 and d['context'].get('purpose')=='correction-edit':
                instruction.append('Operation: correct the declared edit target using the original person and garment sources; '
                                   'retain only the requested picture elements. Native editing is soft conditioning, not pixel protection or guaranteed facial fidelity.')
            form=('One six-panel direction preview, not standalone delivery. Include the small single-line label '
                  '方向预览·非成片 / PREVIEW ONLY — NOT FINAL.' if is_preview(d) else 'One standalone image.')
            prompt='Only use built-in image generation, no other plugins. '+form+'\n'+'\n'.join(instruction)+'\n'+canvas_instruction(d)+'\n'+row['prompt']
            if 'real_face_plan' in d:
                cells=enumerate(d['real_face_plan']['looks'],1) if is_preview(d) else [(n,d['real_face_plan']['looks'][n-1])]
                for number,cell in cells:
                    prompt+='\n'+(f'Preview cell {number}:\n' if is_preview(d) else '')+'\n'.join(real_face_helper().prompt_lines(cell))
                    if is_preview(d):
                        positions={r['sha256']:i for i,r in enumerate(refs,1)}
                        selected=', '.join(f'Image {positions[h]}' for h in cell['reference_sha256s'])
                        prompt+='\nCell reference images: '+selected+'. Use only these references for this cell, retaining their declared garment/identity roles; do not mix product facts from other cells. Selection note: '+cell['selection_note']
            if d['schema_version']==2 and d['model']:
                prompt=models.apply_conditions(prompt,d['model'],allow_child=True)
            if 'shot_plan' in d:
                prompt=shot_helper().apply(prompt,d['shot_plan'],None if is_preview(d) else n,d.get('real_face_plan'))
            prompt=photography_helper().apply(prompt,d['context'].get('photography_targets') if d['schema_version']==2 else None)
            (out/'prompt.txt').write_text(prompt,encoding='utf-8')
            if d['route']=='codex_native':
                request=dict(prompt=prompt,
                             referenced_image_paths=[str((out/f'{i:02d}-{r["role"]}{Path(r["file"]).suffix}').resolve()) for i,r in enumerate(refs,1)],
                             transparent_background=False)
                (out/'request.json').write_text(json.dumps(request,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            if d['schema_version']==2:
                manifest=dict(look=n,attempt_number=row.get('attempt_number',1),plan_revision=row.get('plan_revision',0),
                    frozen_prompt_sha256=row['prompt_sha256'],tool_prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
                    reference_hashes=[r['sha256'] for r in refs])
                manifest.update(current_plan_sha256=plan_fingerprint(d),current_plan_version=d.get('plan_version',0))
                if 'shot_plan' in d:
                    manifest.update(shot_plan=d['shot_plan'],shot_plan_sha256=d['shot_plan_sha256'],
                        omitted_reference_sha256s=[r['sha256'] for r in d['references'] if r['sha256'] not in {x['sha256'] for x in refs}])
                if 'real_face_plan' in d:
                    manifest.update(real_face_plan=copy.deepcopy(d['real_face_plan']),
                        real_face_plan_sha256=d['real_face_plan_sha256'])
                    if is_preview(d):
                        manifest['preview_cell_plans']=copy.deepcopy(d['real_face_plan']['looks'])
                        chosen={r['sha256'] for r in refs}
                    else:
                        manifest['real_face_look']=copy.deepcopy(d['real_face_plan']['looks'][n-1])
                        chosen=set(manifest['real_face_look']['reference_sha256s'])
                    manifest['omitted_reference_sha256s']=[r['sha256'] for r in d['references'] if r['sha256'] not in chosen]
                (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        (folder/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');return str(folder)


def create_from_preview(root, preview_root, spec, *, note):
    """Prepare one linked delivery, without inheriting preview pixels or authority."""
    root=Path(root).resolve();parent=Path(preview_root).resolve()
    if root==parent or root.is_relative_to(parent) or parent.is_relative_to(root):
        raise ValueError('Delivery and preview must have separate task directories')
    with locked(parent):
        d=read(parent);check_evidence(parent,d)
        if (not is_preview(d) or not d.get('preview_decision') or d.get('delivery_task')
                or d['looks'][0]['state']!='accepted' or d.get('preview_revision') or not isinstance(note,str) or not note.strip()):
            raise ValueError('Prepare delivery only from a closed, reviewed preview with an actual user request and no prior delivery link')
        if not isinstance(spec,dict) or set(spec)-{'context','size','prompts','real_face_plan','garment_sha256s'}:
            raise ValueError('Delivery spec contains only context, size, prompts, optional real_face_plan and garment selection')
        context=spec['context']
        garments={r['sha256'] for r in d['references'] if r['role']=='garment-source'}
        selected=spec.get('garment_sha256s')
        if selected is not None and (not isinstance(selected,list) or not selected
                or any(not isinstance(h,str) or h not in garments for h in selected) or len(set(selected))!=len(selected)):
            raise ValueError('Select distinct original garment hashes for the requested outfit')
        if context.get('purpose','delivery')!='delivery' or any(
                context.get(k)!=d['context'][k] for k in ('style','mode','output_form')) or (
                context.get('outfit')!=d['context']['outfit'] and (selected is None or set(selected)==garments)):
            raise ValueError('A preview handoff retains outfit, style, mode and output form; changes are a separate task')
        if 'real_face_plan' in d:
            planned=spec.get('real_face_plan',{})
            if any(planned.get(k)!=d['real_face_plan'][k] for k in ('coverage','primary_identity_sha256')):
                raise ValueError('Keep original reviewed real coverage; preview faces supply no new authentic view')
        refs=[dict(path=str(safe_file(parent,r['file'])),**{k:v for k,v in r.items() if k!='file'}) for r in d['references']
              if r['role']!='garment-source' or selected is None or r['sha256'] in selected]
        # create accepts hashes only on model supplements; original rows are rehashed.
        for ref in refs:
            if ref['role']!='model-supplement':ref.pop('sha256')
        planned=copy.deepcopy(d.get('shot_plan'))
        if planned is not None:
            if selected is not None and not {r['sha256'] for r in planned['coverage']}<=set(selected):
                raise ValueError('Garment selection cannot drop frozen shot coverage; prepare an explicit plan revision first')
            if len(spec['prompts'])==1:
                if type(context.get('first_pose')) is not int or context['first_pose'] not in range(1,7):raise ValueError('Select a numbered shot for a planned single delivery')
                planned['looks']=[planned['looks'][context['first_pose']-1]]
        child=create(root,refs,spec['prompts'],spec['size'],d['identity'],model=d['model'],
                     context=context,route=d['route'],real_face_plan=spec.get('real_face_plan'),shot_plan=planned)
        try:
            provenance=root/'provenance';provenance.mkdir()
            snapshot=provenance/'preview-task.json'
            snapshot.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
            shutil.copyfile(safe_file(parent,d['looks'][0]['output']['file']),provenance/'preview.png')
            child['preview_origin']=dict(task=str(parent),snapshot_sha256=digest(snapshot),attempts=d['attempts'],note=note)
            check_evidence(root,child);save(root,child)
            d['delivery_task']=dict(task=str(root),note=note,at=stamp())
            save(parent,d)
        except Exception:
            shutil.rmtree(root)
            raise
        return child


def export_model(root, destination, name, *, include_accepted=False, accepted_scope='face'):
    root=Path(root)
    with locked(root):
        d=read(root);check_evidence(root,d)
        if is_preview(d) or d['schema_version']!=2 or not d['identity'] or not d['model_confirmation'] or d['looks'][0]['state']!='accepted':
            raise ValueError('Export only a technically accepted and human-confirmed first-image model')
        refs=[root/r['file'] for r in d['references'] if r['role']=='identity-reference']
        if d['model']['source_type']=='new':refs=[root/d['looks'][0]['output']['file']]
        if type(include_accepted) is not bool or accepted_scope not in ('face','full'):
            raise ValueError('Explicit accepted-reference opt-in and face/full scope required')
        supplements=[dict(path=str(safe_file(root,r['file'])), **{k:r[k] for k in ('sha256','scope','confirmation_note')})
                     for r in d['references'] if r['role']=='model-supplement']
        if include_accepted and d['model']['source_type']!='new':
            first=d['looks'][0]['output']
            supplements.append(dict(path=str(safe_file(root,first['file'])),sha256=first['sha256'],
                                    scope=accepted_scope,confirmation_note=d['model_confirmation']['note']))
        return models.export_package(destination,d['model'],refs,name,d['model_confirmation']['note'],supplements=supplements)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['init','status','export','authorize','mode','reserve','bind','unknown','failed','returned','accept','reject','audit-reject','review-output','revise-pending','retry-authorize','confirm-model','reject-model','continue-authorize','export-model','enable-failure-recovery','reconcile-failure','finish-preview','prepare-delivery','revise-preview']);p.add_argument('--task',type=Path,required=True);p.add_argument('--spec',type=Path);p.add_argument('--destination',type=Path);p.add_argument('--preview-task',type=Path);p.add_argument('--decision',choices=['stop','direction-confirmed']);p.add_argument('--name');p.add_argument('--look',type=int);p.add_argument('--note');p.add_argument('--limit',type=int);p.add_argument('--mode',choices=['manual','automatic']);p.add_argument('--ready',action='store_true');p.add_argument('--refs',nargs='*');p.add_argument('--conversation');p.add_argument('--tab');p.add_argument('--file',type=Path);p.add_argument('--failure-receipt',type=Path);p.add_argument('--reason');p.add_argument('--request-check-completed',action='store_true');p.add_argument('--qa',choices=['qa-pass','qa-user-review','qa-retry']);p.add_argument('--expected-output-sha256');p.add_argument('--expected-prompt-sha256');p.add_argument('--expected-plan-sha256');p.add_argument('--expected-attempt',type=int);p.add_argument('--approval-id');p.add_argument('--prompt-file',type=Path);p.add_argument('--model-spec',type=Path);p.add_argument('--include-accepted-reference',action='store_true');p.add_argument('--accepted-scope',choices=['face','full']);a=p.parse_args()
    try:
        if a.command!='export-model' and (a.include_accepted_reference or a.accepted_scope is not None):
            raise ValueError('Accepted-reference options are only for export-model')
        if a.accepted_scope is not None and not a.include_accepted_reference:
            raise ValueError('Declare --include-accepted-reference before choosing its scope')
        if a.command=='init':
            spec=json.loads(a.spec.read_text());result=create(a.task,spec['references'],spec['prompts'],spec['size'],spec.get('identity',True),schema_version=spec.get('schema_version',2),model=spec.get('model'),context=spec.get('context'),route=spec.get('route'),model_package=spec.get('model_package'),real_face_plan=spec.get('real_face_plan'),shot_plan=spec.get('shot_plan'))
        elif a.command=='prepare-delivery':
            result=create_from_preview(a.task,a.preview_task,json.loads(a.spec.read_text()),note=a.note)
        elif a.command=='status':result=read(a.task)
        elif a.command=='export':result=export(a.task)
        elif a.command=='export-model':result=export_model(a.task,a.destination,a.name,include_accepted=a.include_accepted_reference,accepted_scope=a.accepted_scope or 'face')
        else:
            args={k:v for k,v in vars(a).items() if k not in ('command','task','spec','prompt_file','destination','preview_task','name','model_spec','include_accepted_reference','accepted_scope') and v is not None}
            if a.model_spec:
                if a.command not in ('retry-authorize','revise-preview'):raise ValueError('Model revision is only accepted with explicit first-image retry authority')
                args['model']=json.loads(a.model_spec.read_text(encoding='utf-8'))['model']
            if a.prompt_file:args['prompt']=a.prompt_file.read_text(encoding='utf-8')
            if a.command=='revise-preview' and a.spec:
                revision=json.loads(a.spec.read_text(encoding='utf-8'))
                if not isinstance(revision,dict) or set(revision)-{'model','shot_plan','prompt','garment_references'}:raise ValueError('Preview revision spec contains only model, shot_plan and prompt')
                args.update(revision)
            if a.command=='continue-authorize':
                spec=json.loads(a.spec.read_text(encoding='utf-8'));args.update(context=spec['context'],prompts=spec['prompts'])
                if 'real_face_looks' in spec:args['real_face_looks']=spec['real_face_looks']
                if 'shot_plan' in spec:args['shot_plan']=spec['shot_plan']
            result=update(a.task,a.command,**args)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:p.exit(1,str(error)+'\n')

if __name__=='__main__':main()
