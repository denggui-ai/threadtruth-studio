#!/usr/bin/env python3
"""Local ChatGPT handoff/automation ledger. No network, browser or generation calls."""
import argparse
import copy
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import uuid
import zlib
from urllib.parse import urlparse

_model_spec = importlib.util.spec_from_file_location('task_model_reference', Path(__file__).with_name('model_reference.py'))
models = importlib.util.module_from_spec(_model_spec)
_model_spec.loader.exec_module(models)
ROLE_TEXT = {
    'garment-source': 'garment source; authoritative product facts',
    'identity-reference': 'original model identity; ignore clothing, accessories, pose, backdrop and lighting',
    'aesthetic-reference': 'aesthetic only; do not copy identity or clothing',
    'identity-only': 'current outfit accepted first-image identity; never override original identity or garment sources',
}


def context_check(context, size):
    required = {'outfit', 'style', 'mode', 'output_form', 'size', 'first_pose'}
    if not isinstance(context, dict) or set(context) != required:
        raise ValueError('Declare outfit, style, mode, output_form, size and first_pose for the frozen task context')
    if any(not isinstance(context[k], str) or not context[k].strip() for k in required - {'size','first_pose'}):
        raise ValueError('Task context labels must be nonempty')
    if type(context['first_pose']) is not int or context['first_pose'] not in range(1,7):raise ValueError('Declare the actual first pose number')
    if context['mode'] not in ('B', 'C', 'D') or context['size'] != list(size):
        raise ValueError('Task mode/canvas does not match context')
    return copy.deepcopy(context)


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


def save(root,data):
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
    return data


def create(root,refs,prompts,size,identity=True,*,schema_version=2,model=None,context=None,route='chatgpt_web',model_package=None):
    root=Path(root)
    if model_package is not None:
        if schema_version!=2 or not identity or model is not None:raise ValueError('Package use requires a new portrait task and no conflicting inline model')
        card=models.load_package(model_package);model=card['model']
        refs=list(refs)+[dict(path=str(Path(model_package)/r['file']),role='identity-reference') for r in card['references']]
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
        if identity:
            model=models.validate_model(model or dict(source_type='new',scope='full',subject='adult model',locked=[],adjustable=[],consent_note=''))
        elif model is not None:raise ValueError('Non-portrait tasks cannot carry a model')
        items=[dict(path=p,role='garment-source') if isinstance(p,(str,Path)) else dict(p) for p in refs]
        if any(set(x)!={'path','role'} or x['role'] not in ('garment-source','identity-reference','aesthetic-reference') for x in items):
            raise ValueError('Declare an explicit reference role')
        if not any(x['role']=='garment-source' for x in items):raise ValueError('A model/photo/card is not a garment source')
        has_identity=any(x['role']=='identity-reference' for x in items)
        if not identity and any(x['role']!='garment-source' for x in items):raise ValueError('Non-portrait task cannot carry person references')
        if identity and (has_identity != (model['source_type'] in ('ai','real'))):raise ValueError('Existing models need original identity references; new models do not copy identity')
    sources=[Path(x['path']).resolve() for x in items]
    if any(not p.is_file() or p.suffix.lower() not in ('.png','.jpg','.jpeg','.webp') for p in sources):
        raise ValueError('References must be existing image files')
    root.mkdir(parents=True,exist_ok=False);(root/'references').mkdir();frozen=[]
    for i,(p,item) in enumerate(zip(sources,items),1):
        out=root/'references'/f'{i:02d}{p.suffix.lower()}';shutil.copyfile(p,out)
        frozen.append({'file':str(out.relative_to(root)),'sha256':digest(out),'role':item['role']})
    data={'schema_version':schema_version,'created_at':stamp(),'route':route,'mode':'manual','model_verified':False,
          'size':list(size),'identity':bool(identity),'references':frozen,'authorization':None,'attempts':0,
          'complete':False,'delivery_status':'image-draft','events':[],
          'looks':[{'number':i,'prompt':p,'prompt_sha256':hashlib.sha256(p.encode()).hexdigest(),'state':'pending'} for i,p in enumerate(prompts,1)]}
    if schema_version==2:
        data.update(context=context,context_sha256=object_hash(context),model=model,model_sha256=object_hash(model),model_confirmation=None)
    save(root,data);return data


def references(root,data,look):
    if not 1<=look<=len(data['looks']):raise ValueError('Unknown look number')
    row=data['looks'][look-1]
    if hashlib.sha256(row['prompt'].encode()).hexdigest()!=row['prompt_sha256']:raise ValueError('Frozen prompt changed')
    rows=list(data['references'])
    if data['schema_version']==2 and data['identity'] and look>1 and not data['model_confirmation']:
        raise ValueError('First-image model has not been confirmed by the user')
    if data['identity'] and look>1:
        anchor=data['looks'][0]
        if anchor['state']!='accepted':raise ValueError('look-1 has not passed visual anchor QA')
        rows=rows+[dict(anchor['output'],role='identity-only')]
        if data['schema_version']==2:
            seen=set();unique=[]
            for ref in rows:
                key=(ref['sha256'], 'identity' if ref['role'] in ('identity-reference','identity-only') else ref['role'])
                if key not in seen:unique.append(ref);seen.add(key)
            rows=unique
    for row in rows:
        if digest(safe_file(Path(root),row['file']))!=row['sha256']:raise ValueError('Frozen reference/anchor changed')
    return rows


def reference_hashes(root,look):
    return [r['sha256'] for r in references(root,read(root),look)]


def evidence_rows(data):
    for row in data['looks']:
        yield from row.get('history', [])
        yield row


def check_evidence(root,data):
    if data['schema_version']==2:
        if object_hash(data['context'])!=data['context_sha256'] or object_hash(data['model'])!=data['model_sha256']:
            raise ValueError('Frozen context/model changed')
        context_check(data['context'],data['size'])
        if data['identity']:models.validate_model(data['model'])
    for row in evidence_rows(data):
        if hashlib.sha256(row['prompt'].encode()).hexdigest()!=row['prompt_sha256']:
            raise ValueError('Frozen prompt changed')
        if 'model' in row and object_hash(row['model'])!=row['model_sha256']:raise ValueError('Historical model conditions changed')
        if 'output' in row and digest(safe_file(root,row['output']['file']))!=row['output']['sha256']:
            raise ValueError('Previously imported output changed')
    for ref in data['references']:
        if digest(safe_file(root,ref['file']))!=ref['sha256']:raise ValueError('Frozen reference changed')


def safe_file(root,relative):
    path=Path(relative);resolved=(root/path).resolve()
    if path.is_absolute() or '..' in path.parts or not resolved.is_relative_to(root.resolve()):
        raise ValueError('Task file escapes private directory')
    return resolved


def update(root,event,**kw):
    root=Path(root)
    with locked(root):
        d=read(root);n=kw.get('look');row=None
        check_evidence(root,d)
        if n is not None:
            if type(n)!=int or not 1<=n<=len(d['looks']):raise ValueError('Unknown look number')
            row=d['looks'][n-1]
        if event=='authorize':
            if d['authorization'] or d['attempts']:raise ValueError('Existing authorization/budget cannot be reset')
            limit=kw.get('limit');note=kw.get('note','').strip()
            if type(limit)!=int or not 1<=limit<=len(d['looks']) or not note:raise ValueError('Explicit ChatGPT upload and generation approval with limit required')
            d['authorization']={'destination':('ChatGPT' if d['schema_version']==1 else d['route']),'limit':limit,'note':note,'at':stamp()}
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
            if d['identity'] and not d['model_confirmation']:raise ValueError('User must confirm the model first')
            if d['context']['first_pose']!=1:raise ValueError('Only an actual pose-1 trial can become look-1 of the six-pose set')
            if kw.get('context')!=d['context']:raise ValueError('Continuation must keep outfit, style, mode, output form and canvas')
            if not note or not approval or any(x['approval_id']==approval for x in d.get('retry_authorizations',[])):
                raise ValueError('Explicit five-image approval and a fresh ID required')
            if not isinstance(prompts,list) or len(prompts)!=5 or any(not isinstance(p,str) or not p.strip() for p in prompts):
                raise ValueError('Provide exactly five continuation prompts')
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
        elif event=='retry-authorize':
            # One explicit grant replaces one rejected attempt, never resets the task.
            note=kw.get('note','').strip();approval=kw.get('approval_id','').strip();prompt=kw.get('prompt','')
            grants=d.get('retry_authorizations',[])
            if row is None or row['state']!='rejected' or not d['authorization']:raise ValueError('Only a visually rejected downloaded attempt can be retried')
            attempt=row.get('attempt_number',1)
            if type(kw.get('expected_attempt'))!=int or kw['expected_attempt']!=attempt:raise ValueError('Approval must target the current rejected attempt')
            if not note or not approval or not isinstance(prompt,str) or not prompt.strip():raise ValueError('Explicit retry approval, unique approval ID and corrected prompt required')
            if any(g['approval_id']==approval for g in grants) or d.get('continuation_authorization',{}).get('approval_id')==approval:raise ValueError('Retry approval already used')
            if any(x['state']!='pending' for x in d['looks'][n:]):raise ValueError('Cannot replace an anchor with existing downstream work')
            history=copy.deepcopy(row.get('history',[]));old=copy.deepcopy(row);old.pop('history',None)
            if d['schema_version']==2 and d['model']:
                old.update(model=copy.deepcopy(d['model']),model_sha256=d['model_sha256'])
            if kw.get('model') is not None:
                if d['schema_version']!=2 or n!=1 or not row.get('model_rejected') or d['model_confirmation']:raise ValueError('Model revision requires explicit unconfirmed-first-model rejection')
                changed=models.validate_model(kw['model'])
                if any(changed[k]!=d['model'][k] for k in ('source_type','scope','subject')):raise ValueError('A different identity/source/scope requires a new declared model version, not replacement of original references')
                d.update(model=changed,model_sha256=object_hash(changed))
            history.append(old)
            grant={'approval_id':approval,'look':n,'rejected_attempt':attempt,'additional_requests':1,'note':note,'at':stamp(),'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest()}
            row.clear();row.update(number=n,state='pending',attempt_number=attempt+1,prompt=prompt,prompt_sha256=grant['prompt_sha256'],history=history)
            d.setdefault('retry_authorizations',[]).append(grant)
        elif event=='mode':
            if kw.get('mode') not in ('manual','automatic'):raise ValueError('Unknown mode')
            d['mode']=kw['mode']
        elif event=='reserve':
            auth=d['authorization']
            if not auth or d['attempts']>=auth['limit']+len(d.get('retry_authorizations',[]))+d.get('continuation_authorization',{}).get('additional_requests',0):raise ValueError('No authorized request budget remains')
            if row is None or row['state']!='pending':raise ValueError('Submission already reserved or no pending look')
            if any(x['state']!='accepted' for x in d['looks'][:n-1]):raise ValueError('Earlier look is unresolved or not accepted')
            expected=[x['sha256'] for x in references(root,d,n)]
            if kw.get('refs')!=expected or kw.get('ready') is not True:raise ValueError('Check login, persistent chat, prompt and completed attachment order before reserving')
            url=kw.get('conversation','');u=urlparse(url)
            if d['route']=='chatgpt_web' and (u.scheme!='https' or u.hostname!='chatgpt.com' or not ((u.path.startswith('/c/') and u.path[3:]) or (u.path in ('','/') and kw.get('tab','').strip()))):raise ValueError('Provide the observed persistent conversation, or a new-chat URL plus stable browser tab handle')
            row.update(state='reserved',conversation=url,tab=kw.get('tab'),submitted_at=stamp(),reference_hashes=expected)
            d['attempts']+=1
        elif event=='bind':
            u=urlparse(kw.get('conversation',''))
            if row is None or row['state'] not in ('reserved','unknown') or u.scheme!='https' or u.hostname!='chatgpt.com' or not u.path.startswith('/c/') or not u.path[3:]:raise ValueError('Bind only an observed persistent URL to the existing reserved request')
            row['conversation']=kw['conversation']
        elif event in ('unknown','failed'):
            if row is None or row['state'] not in ('reserved','unknown'):raise ValueError('No pending submitted request')
            row['state']=event
        elif event=='returned':
            if row is None or row['state'] not in ('reserved','unknown'):raise ValueError('No reserved result to recover')
            source=Path(kw['file']);dimensions=png_size(source);sha=digest(source)
            if dimensions!=d['size']:raise ValueError('Wrong canvas: stop without another generation call')
            if sha in [x.get('output',{}).get('sha256') for x in evidence_rows(d)]:raise ValueError('Duplicate output image')
            suffix=f"-attempt-{row['attempt_number']}" if row.get('attempt_number',1)>1 else '';out=root/'outputs'/f'look-{n}{suffix}.png';out.parent.mkdir(exist_ok=True)
            with out.open('xb') as f:f.write(source.read_bytes())
            row.update(state='returned',output={'file':str(out.relative_to(root)),'sha256':sha,'dimensions':dimensions})
        elif event=='accept':
            if row is None or row['state']!='returned':raise ValueError('No downloaded result for visual QA')
            if kw.get('qa') not in ('qa-pass','qa-user-review') or not kw.get('note','').strip():raise ValueError('Record actual visual QA and anchor suitability')
            if digest(root/row['output']['file'])!=row['output']['sha256']:raise ValueError('Output changed since import')
            row.update(state='accepted',qa=kw['qa'],qa_note=kw['note'])
        else:raise ValueError('Unknown event')
        d['complete']=all(x['state']=='accepted' for x in d['looks']) and (d['schema_version']==1 or not d['identity'] or bool(d['model_confirmation']))
        # Completeness never confers image-ready or user commercial acceptance.
        d['events'].append({'at':stamp(),'event':event,'look':n,'attempts':d['attempts']})
        save(root,d);return d


def export(root):
    root=Path(root)
    with locked(root):
        d=read(root);check_evidence(root,d);folder=root/'handoff';folder.mkdir(exist_ok=True);lines=['# ChatGPT 网页转交包','只用内置生图；不要选择其他插件。','参考图按编号上传，确认全部完成；使用新建持久对话。','提交前必须由 Codex 记录 reserve；本包不是新的生图授权。','点击网页原图下载，不使用截图；将原文件回传给 Codex。','尚未确认的请求先查原对话，不要再次发送。','']
        if d['route']=='codex_native':
            lines=['# Codex 原生生成执行包','参考图按编号作为实际工具附件传入；只用原生生图。','调用前记录 reserve；本包不是新的生图授权。','原图返回后落盘、读取元数据并记录 QA。','未决调用先检查原结果，不自动追加调用。','']
        for row in d['looks']:
            n=row['number'];lines.append(f"- look-{n}: {row['state']}")
            if row['state']!='pending' or any(x['state']!='accepted' for x in d['looks'][:n-1]):continue
            if d['schema_version']==2 and d['identity'] and n>1 and not d['model_confirmation']:continue
            refs=references(root,d,n);suffix=f"-attempt-{row['attempt_number']}" if row.get('attempt_number',1)>1 else '';out=folder/f'look-{n}{suffix}';out.mkdir(exist_ok=True);lines.append(f'  Current handoff: {out.name}; earlier attempt folders are evidence only, never resubmit them.')
            instruction=[]
            for i,r in enumerate(refs,1):
                src=root/r['file'];dst=out/f'{i:02d}-{r["role"]}{src.suffix}'
                if dst.exists() and digest(dst)!=r['sha256']:raise ValueError('Existing handoff attachment changed')
                shutil.copyfile(src,dst);instruction.append(f'Image {i}: '+ROLE_TEXT[r['role']])
            if d['schema_version']==2 and d['model']:instruction.extend(models.prompt_lines(d['model']))
            prompt='Only use built-in image generation, no other plugins. One standalone image.\n'+'\n'.join(instruction)+f'\nExact canvas: {d["size"][0]}x{d["size"][1]}.\n'+row['prompt']
            (out/'prompt.txt').write_text(prompt,encoding='utf-8')
        (folder/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');return str(folder)


def export_model(root, destination, name):
    root=Path(root)
    with locked(root):
        d=read(root);check_evidence(root,d)
        if d['schema_version']!=2 or not d['identity'] or not d['model_confirmation'] or d['looks'][0]['state']!='accepted':
            raise ValueError('Export only a technically accepted and human-confirmed first-image model')
        refs=[root/r['file'] for r in d['references'] if r['role']=='identity-reference']
        if d['model']['source_type']=='new':refs=[root/d['looks'][0]['output']['file']]
        return models.export_package(destination,d['model'],refs,name,d['model_confirmation']['note'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['init','status','export','authorize','mode','reserve','bind','unknown','failed','returned','accept','reject','retry-authorize','confirm-model','reject-model','continue-authorize','export-model']);p.add_argument('--task',type=Path,required=True);p.add_argument('--spec',type=Path);p.add_argument('--destination',type=Path);p.add_argument('--name');p.add_argument('--look',type=int);p.add_argument('--note');p.add_argument('--limit',type=int);p.add_argument('--mode',choices=['manual','automatic']);p.add_argument('--ready',action='store_true');p.add_argument('--refs',nargs='*');p.add_argument('--conversation');p.add_argument('--tab');p.add_argument('--file',type=Path);p.add_argument('--qa',choices=['qa-pass','qa-user-review']);p.add_argument('--expected-attempt',type=int);p.add_argument('--approval-id');p.add_argument('--prompt-file',type=Path);p.add_argument('--model-spec',type=Path);a=p.parse_args()
    try:
        if a.command=='init':
            spec=json.loads(a.spec.read_text());result=create(a.task,spec['references'],spec['prompts'],spec['size'],spec.get('identity',True),schema_version=spec.get('schema_version',2),model=spec.get('model'),context=spec.get('context'),route=spec.get('route','chatgpt_web'),model_package=spec.get('model_package'))
        elif a.command=='status':result=read(a.task)
        elif a.command=='export':result=export(a.task)
        elif a.command=='export-model':result=export_model(a.task,a.destination,a.name)
        else:
            args={k:v for k,v in vars(a).items() if k not in ('command','task','spec','prompt_file','destination','name','model_spec') and v is not None}
            if a.model_spec:
                if a.command!='retry-authorize':raise ValueError('Model revision is only accepted with explicit first-image retry authority')
                args['model']=json.loads(a.model_spec.read_text(encoding='utf-8'))['model']
            if a.prompt_file:args['prompt']=a.prompt_file.read_text(encoding='utf-8')
            if a.command=='continue-authorize':
                spec=json.loads(a.spec.read_text(encoding='utf-8'));args.update(context=spec['context'],prompts=spec['prompts'])
            result=update(a.task,a.command,**args)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:p.exit(1,str(error)+'\n')

if __name__=='__main__':main()
