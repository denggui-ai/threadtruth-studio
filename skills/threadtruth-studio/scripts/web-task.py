#!/usr/bin/env python3
"""Local ChatGPT handoff/automation ledger. No network, browser or generation calls."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import uuid
import zlib
from urllib.parse import urlparse


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
    if data.get('schema_version')!=1:raise ValueError('Unsupported task schema')
    return data


def create(root,refs,prompts,size,identity=True):
    root=Path(root)
    if len(prompts) not in (1,6) or not all(isinstance(p,str) and p.strip() for p in prompts):
        raise ValueError('Provide exactly one or six nonempty frozen prompts')
    if not refs or len(size)!=2 or any(type(v)!=int or v<=0 for v in size):
        raise ValueError('Real garment references and positive exact dimensions required')
    sources=[Path(p).resolve() for p in refs]
    if any(not p.is_file() or p.suffix.lower() not in ('.png','.jpg','.jpeg','.webp') for p in sources):
        raise ValueError('References must be existing image files')
    root.mkdir(parents=True,exist_ok=False);(root/'references').mkdir();frozen=[]
    for i,p in enumerate(sources,1):
        out=root/'references'/f'{i:02d}{p.suffix.lower()}';shutil.copyfile(p,out)
        frozen.append({'file':str(out.relative_to(root)),'sha256':digest(out),'role':'garment-source'})
    data={'schema_version':1,'created_at':stamp(),'route':'chatgpt_web','mode':'manual','model_verified':False,
          'size':list(size),'identity':bool(identity),'references':frozen,'authorization':None,'attempts':0,
          'complete':False,'delivery_status':'image-draft','events':[],
          'looks':[{'number':i,'prompt':p,'prompt_sha256':hashlib.sha256(p.encode()).hexdigest(),'state':'pending'} for i,p in enumerate(prompts,1)]}
    save(root,data);return data


def references(root,data,look):
    if not 1<=look<=len(data['looks']):raise ValueError('Unknown look number')
    row=data['looks'][look-1]
    if hashlib.sha256(row['prompt'].encode()).hexdigest()!=row['prompt_sha256']:raise ValueError('Frozen prompt changed')
    rows=list(data['references'])
    if data['identity'] and look>1:
        anchor=data['looks'][0]
        if anchor['state']!='accepted':raise ValueError('look-1 has not passed visual anchor QA')
        rows=rows+[dict(anchor['output'],role='identity-only')]
    for row in rows:
        if digest(Path(root)/row['file'])!=row['sha256']:raise ValueError('Frozen reference/anchor changed')
    return rows


def reference_hashes(root,look):
    return [r['sha256'] for r in references(root,read(root),look)]


def update(root,event,**kw):
    root=Path(root)
    with locked(root):
        d=read(root);n=kw.get('look');row=None
        for previous in d['looks']:
            if 'output' in previous and digest(root/previous['output']['file'])!=previous['output']['sha256']:raise ValueError('Previously imported output changed')
        if n is not None:
            if type(n)!=int or not 1<=n<=len(d['looks']):raise ValueError('Unknown look number')
            row=d['looks'][n-1]
        if event=='authorize':
            if d['authorization'] or d['attempts']:raise ValueError('Existing authorization/budget cannot be reset')
            limit=kw.get('limit');note=kw.get('note','').strip()
            if type(limit)!=int or not 1<=limit<=len(d['looks']) or not note:raise ValueError('Explicit ChatGPT upload and generation approval with limit required')
            d['authorization']={'destination':'ChatGPT','limit':limit,'note':note,'at':stamp()}
        elif event=='mode':
            if kw.get('mode') not in ('manual','automatic'):raise ValueError('Unknown mode')
            d['mode']=kw['mode']
        elif event=='reserve':
            auth=d['authorization']
            if not auth or d['attempts']>=auth['limit']:raise ValueError('No authorized request budget remains')
            if row is None or row['state']!='pending':raise ValueError('Submission already reserved or no pending look')
            if any(x['state']!='accepted' for x in d['looks'][:n-1]):raise ValueError('Earlier look is unresolved or not accepted')
            expected=[x['sha256'] for x in references(root,d,n)]
            if kw.get('refs')!=expected or kw.get('ready') is not True:raise ValueError('Check login, persistent chat, prompt and completed attachment order before reserving')
            url=kw.get('conversation','');u=urlparse(url)
            if u.scheme!='https' or u.hostname!='chatgpt.com' or not ((u.path.startswith('/c/') and u.path[3:]) or (u.path in ('','/') and kw.get('tab','').strip())):raise ValueError('Provide the observed persistent conversation, or a new-chat URL plus stable browser tab handle')
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
            if sha in [x.get('output',{}).get('sha256') for x in d['looks']]:raise ValueError('Duplicate output image')
            out=root/'outputs'/f'look-{n}.png';out.parent.mkdir(exist_ok=True)
            with out.open('xb') as f:f.write(source.read_bytes())
            row.update(state='returned',output={'file':str(out.relative_to(root)),'sha256':sha,'dimensions':dimensions})
        elif event=='accept':
            if row is None or row['state']!='returned':raise ValueError('No downloaded result for visual QA')
            if kw.get('qa') not in ('qa-pass','qa-user-review') or not kw.get('note','').strip():raise ValueError('Record actual visual QA and anchor suitability')
            if digest(root/row['output']['file'])!=row['output']['sha256']:raise ValueError('Output changed since import')
            row.update(state='accepted',qa=kw['qa'],qa_note=kw['note'])
        else:raise ValueError('Unknown event')
        d['complete']=all(x['state']=='accepted' for x in d['looks'])
        # Completeness never confers image-ready or user commercial acceptance.
        d['events'].append({'at':stamp(),'event':event,'look':n,'attempts':d['attempts']})
        save(root,d);return d


def export(root):
    root=Path(root)
    with locked(root):
        d=read(root);folder=root/'handoff';folder.mkdir(exist_ok=True);lines=['# ChatGPT 网页转交包','只用内置生图；不要选择其他插件。','参考图按编号上传，确认全部完成；使用新建持久对话。','提交前必须由 Codex 记录 reserve；本包不是新的生图授权。','点击网页原图下载，不使用截图；将原文件回传给 Codex。','尚未确认的请求先查原对话，不要再次发送。','']
        for row in d['looks']:
            n=row['number'];lines.append(f"- look-{n}: {row['state']}")
            if row['state']!='pending' or any(x['state']!='accepted' for x in d['looks'][:n-1]):continue
            refs=references(root,d,n);out=folder/f'look-{n}';out.mkdir(exist_ok=True)
            instruction=[]
            for i,r in enumerate(refs,1):
                src=root/r['file'];dst=out/f'{i:02d}-{r["role"]}{src.suffix}'
                if dst.exists() and digest(dst)!=r['sha256']:raise ValueError('Existing handoff attachment changed')
                shutil.copyfile(src,dst);instruction.append(f'Image {i}: '+('identity-only anchor; ignore its garment, lighting, pose and background' if r['role']=='identity-only' else 'garment source; authoritative product facts'))
            prompt='Only use built-in image generation, no other plugins. One standalone image.\n'+'\n'.join(instruction)+f'\nExact canvas: {d["size"][0]}x{d["size"][1]}.\n'+row['prompt']
            (out/'prompt.txt').write_text(prompt,encoding='utf-8')
        (folder/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');return str(folder)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['init','status','export','authorize','mode','reserve','bind','unknown','failed','returned','accept']);p.add_argument('--task',type=Path,required=True);p.add_argument('--spec',type=Path);p.add_argument('--look',type=int);p.add_argument('--note');p.add_argument('--limit',type=int);p.add_argument('--mode',choices=['manual','automatic']);p.add_argument('--ready',action='store_true');p.add_argument('--refs',nargs='*');p.add_argument('--conversation');p.add_argument('--tab');p.add_argument('--file',type=Path);p.add_argument('--qa',choices=['qa-pass','qa-user-review']);a=p.parse_args()
    try:
        if a.command=='init':
            spec=json.loads(a.spec.read_text());result=create(a.task,spec['references'],spec['prompts'],spec['size'],spec.get('identity',True))
        elif a.command=='status':result=read(a.task)
        elif a.command=='export':result=export(a.task)
        else:result=update(a.task,a.command,**{k:v for k,v in vars(a).items() if k not in ('command','task','spec') and v is not None})
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:p.exit(1,str(error)+'\n')

if __name__=='__main__':main()
