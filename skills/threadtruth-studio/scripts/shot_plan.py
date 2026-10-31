"""Source-backed garment routes and numbered shot plans. No image understanding or network."""
import copy
import importlib.util
from pathlib import Path
import re

BEGIN='[Task shot plan]'
END='[/Task shot plan]'
MASTERS=['SIDE_TURN_STANDING','SIDE_LEANING_WALL','UPRIGHT_SEATED','FRONT_LIGHT_STEP','SLIGHT_FORWARD_LEAN','BACK_TURN_GLANCE']
FRAMINGS=['full-body','full-body','half-body','full-body','knee-up','full-body']
# WP-6b/WP-20: breathing room. framing_guidance=1 renders the legacy head-height wording (frozen plans keep their bytes); 2 renders numeric coordinates (new plans).
FRAMING_GUIDANCE={
    'full-body':'Wide full-length shot from farther back: leave about one and a half head-heights of empty space above the hair and about one head-height of floor below the shoes, so the figure fills roughly three quarters of the frame height and never touches the top or bottom edge.',
    'knee-up':'Head to just below the knees, with about one head-height of empty space above the hair; the head never touches the top edge.',
    'half-body':'Head to waist or hips, with about one head-height of empty space above the hair; the head never touches the top edge.',
}
FRAMING_GUIDANCE_V2={
 'full-body':'Camera far back. Hair top at about y=20% of the frame height, shoe soles at about y=88%, so the person is only about two thirds of the frame height; empty background above the head; the head never touches the top edge. In a grid, apply this inside every cell.',
 'knee-up':'Hair top at about y=12% of the frame height; empty background above the head; the head never touches the top edge. In a grid, apply this inside every cell.',
 'half-body':'Hair top at about y=12% of the frame height; empty background above the head; the head never touches the top edge. In a grid, apply this inside every cell.',
}


def framing_line(plan,framing):
    text='Framing: '+framing+'.'
    g=plan.get('framing_guidance')
    table={1:FRAMING_GUIDANCE,2:FRAMING_GUIDANCE_V2}.get(g) if type(g) is int else None
    if table and framing in table:text+=' '+table[framing]
    return text
RELATIONS=[
    'Standing side turn with a natural shoulder/hip relationship and relaxed weight; not a frontal stand with only the head turned.',
    'Side leaning against a wall with credible contact and relaxed weight-bearing.',
    'Upright seated, relaxed arms and credible seat support; retain the classic half-body rhythm.',
    'A light frontal step, restrained natural movement; not a static stand or exaggerated runway stride.',
    'Standing with a subtle forward lean, arms hanging naturally, relaxed shoulders and neck; no hands braced on thighs, sitting or furniture support.',
    'Back-facing body with a natural over-shoulder relationship; only supported garment-back facts. Real face visibility follows original coverage.',
]
FRONT_RELATION='Frontal relaxed upright standing, both feet planted, arms relaxed; no step, lean, wall support or over-shoulder glance.'
VIEWS={'front','front-side','back','detail'}


def line(value):
    return isinstance(value,str) and bool(value.strip()) and len(value)<=600 and not any(ord(c)<32 for c in value)


def default_plan(sku,coverage):
    """Convenience template, not an assertion that anyone inspected these images."""
    back=any(r.get('usable') is True and r.get('same_sku') is True and 'back' in r.get('views',[]) for r in coverage)
    looks=[]
    for n,master in enumerate(MASTERS,1):
        views=['back'] if n==6 and back else ['front']
        refs=[r['sha256'] for r in coverage if r.get('usable') is True and r.get('same_sku') is True and set(views)<=set(r.get('views',[]))]
        looks.append(dict(pose=n,master='FRONT_RELAXED_STANDING' if n==6 and not back else master,
            framing=FRAMINGS[n-1],garment_views=views,reference_sha256s=refs))
    return dict(version=1,sku=sku,route='A' if back else 'B',preservation='classic',adaptation_note='',coverage=copy.deepcopy(coverage),looks=looks,framing_guidance=2)


def validate(plan,inventory,*,context,count,identity=True,real_face_plan=None,strict_references=True,model_source=None):
    if is_v2(plan):
        return _validate_v2(plan,inventory,context=context,count=count,identity=identity,
                            real_face_plan=real_face_plan,strict_references=strict_references,model_source=model_source)
    fields={'version','sku','route','preservation','adaptation_note','coverage','looks'}
    if not isinstance(plan,dict) or set(plan)-{'framing_guidance'}!=fields or type(plan['version']) is not int or plan['version']!=1:
        raise ValueError('Shot plan requires version=1, sku, route, preservation, adaptation_note, coverage and looks')
    _check_framing_guidance(plan)
    if not identity or context.get('first_pose')=='custom' or context.get('purpose') in ('model-check','correction-edit'):
        raise ValueError('Shot plan applies to numbered human delivery or preview, not custom/diagnostic/non-human tasks')
    if not line(plan['sku']) or plan['route'] not in ('A','B') or plan['preservation'] not in ('classic','adapted'):
        raise ValueError('Declare one SKU, route A/B and classic/adapted preservation')
    if not isinstance(plan['adaptation_note'],str) or (plan['preservation']=='adapted' and not line(plan['adaptation_note'])):
        raise ValueError('An adapted shot plan requires the actual user-approved adaptation note')
    garments={r['sha256'] for r in inventory if r['role']=='garment-source'}
    coverage=plan['coverage'];seen=set();usable={}
    if not isinstance(coverage,list) or not coverage:raise ValueError('Review original garment coverage first')
    for ref in coverage:
        if (not isinstance(ref,dict) or set(ref)!={'sha256','views','usable','same_sku','note'}
                or not isinstance(ref['sha256'],str) or ref['sha256'] not in garments or ref['sha256'] in seen
                or type(ref['usable']) is not bool or type(ref['same_sku']) is not bool
                or not line(ref['note']) or not isinstance(ref['views'],list) or not ref['views']
                or any(not isinstance(v,str) or v not in VIEWS for v in ref['views'])
                or len(ref['views'])!=len(set(ref['views']))):
            raise ValueError('Garment coverage binds distinct original hashes, declared views, usability, same-SKU and review note')
        seen.add(ref['sha256'])
        if ref['usable'] and ref['same_sku']:usable[ref['sha256']]=set(ref['views'])
    supported=set().union(*usable.values()) if usable else set()
    if 'front' not in supported:raise ValueError('A usable same-SKU front is required before either garment route')
    expected='A' if 'back' in supported else 'B'
    if plan['route']!=expected:raise ValueError('Garment route must match usable same-SKU original back coverage')
    looks=plan['looks']
    if not isinstance(looks,list) or len(looks)!=count:raise ValueError('Shot plan look count must match the actual task/cells')
    head_gaze=any(isinstance(shot,dict) and ('head' in shot or 'gaze' in shot) for shot in looks)
    if head_gaze and (model_source not in ('ai','new') or real_face_plan is not None
                      or context.get('output_form')!='human'):
        raise ValueError('Shot head/gaze is only for visible AI/new portraits; real faces use reviewed real_face_plan')
    for i,shot in enumerate(looks,1):
        n=i if count==6 else context['first_pose']
        if (not isinstance(shot,dict) or set(shot)-{'arrangement','head','gaze'}!={'pose','master','framing','garment_views','reference_sha256s'}
                or type(shot['pose']) is not int or shot['pose']!=n):
            raise ValueError('Shot plan preserves numbered mothers in order')
        if head_gaze and (not line(shot.get('head')) or not line(shot.get('gaze'))):
            raise ValueError('Review both head orientation and eye gaze for every shot in this plan')
        master='FRONT_RELAXED_STANDING' if n==6 and expected=='B' else MASTERS[n-1]
        if shot['master']!=master:raise ValueError('Shot master conflicts with the garment route or numbered mother')
        if shot['framing'] not in ('full-body','half-body','knee-up'):
            raise ValueError('Unknown shot framing')
        if plan['preservation']=='classic' and (shot['framing']!=FRAMINGS[n-1] or 'arrangement' in shot):
            raise ValueError('Changing classic framing or relations requires explicit adapted preservation')
        if 'arrangement' in shot and not line(shot['arrangement']):raise ValueError('Adapted arrangement must be a short reviewed line')
        refs=shot['reference_sha256s'];views=shot['garment_views']
        if (not isinstance(refs,list) or not refs or any(not isinstance(h,str) or h not in usable for h in refs)
                or len(refs)!=len(set(refs)) or not isinstance(views,list) or not views
                or any(not isinstance(v,str) or v not in VIEWS for v in views) or len(views)!=len(set(views))):
            raise ValueError('Every shot needs distinct usable garment references and declared garment views')
        selected=set().union(*(usable[h] for h in refs))
        if not set(views)<=selected or ('back' in views and expected=='B') or (n==6 and expected=='A' and 'back' not in views):
            raise ValueError('Shot garment views require the selected original garment coverage')
        if (n<=5 or (n==6 and expected=='B')) and not {'front','front-side'} & set(views):
            raise ValueError('Frontal/front-side mothers need source-supported front or front-side garment views')
        if real_face_plan is not None:
            face=real_face_plan['looks'][i-1]
            if not set(refs)<=set(face['reference_sha256s']):raise ValueError('Garment shot references must be included in the real face look selection')
            actual_garments=set(face['reference_sha256s']) & garments
            if strict_references and not actual_garments<=set(usable):
                raise ValueError('Every real-selected garment, including optional detail, needs usable same-SKU coverage')
    return copy.deepcopy(plan)


def selected(plan,look,preview=False):
    cells=active_looks(plan) if preview else [shot_at(plan,look)]
    return {h for cell in cells for h in cell['reference_sha256s']}


def render(plan,look=None,real_face_plan=None):
    if is_v2(plan):
        return _render_v2(plan,look,real_face_plan)
    rows=[BEGIN,'Garment route: '+plan['route']+'; preservation: '+plan['preservation']+'.']
    if plan['preservation']=='adapted':rows.append('Agreed adaptation: '+plan['adaptation_note'])
    cells=list(enumerate(plan['looks'],1))
    if look is not None:cells=[cells[look-1]]
    for i,shot in cells:
        n=shot['pose'];relation=FRONT_RELATION if shot['master']=='FRONT_RELAXED_STANDING' else RELATIONS[n-1]
        rows.extend([f"Shot {n}: {shot['master']}. {framing_line(plan,shot['framing'])}",
                     shot.get('arrangement',relation),
                     'Supported garment views: '+', '.join(shot['garment_views'])+'.'])
        if 'head' in shot:
            rows.extend(['Head orientation: '+shot['head'], 'Eye gaze: '+shot['gaze']])
        if real_face_plan is not None:
            rows.append('Body arrangement and head/gaze are supplied by this shot\'s reviewed real_face_plan; keep natural support and the agreed classic/adapted relations. Do not infer another face view.')
    return '\n'.join(rows+[END])


def check_legacy_headers(prompt,plan,look=None,real_face_plan=None):
    """Restore known legacy syntax only when its explicit master/framing agrees.

    This is an export gate, not a retrospective evidence check or prose parser.
    """
    canonical=render(plan,look,real_face_plan)
    outside=prompt.replace(canonical,'',1)
    if is_v2(plan):
        if re.search(r'^\s*(?:POSE|Shot)\s+\d+\s*:',outside,re.I|re.M):
            raise ValueError('Legacy pose headers cannot override a version-2 shot plan')
        return
    shots=plan['looks'] if look is None else [plan['looks'][look-1]]
    expected={s['pose']:s for s in shots}
    headers=list(re.finditer(r'^\s*(?:POSE|Shot)\s+([1-6])\s*:\s*([A-Za-z_]+)',outside,re.I|re.M))
    if len(headers)!=len(re.findall(r'^\s*(?:POSE|Shot)\s+[1-6]\s*:',outside,re.I|re.M)):
        raise ValueError('Unrecognized legacy shot header requires explicit new preparation')
    for i,header in enumerate(headers):
        shot=expected.get(int(header[1]))
        section=outside[header.end():headers[i+1].start() if i+1<len(headers) else len(outside)]
        framings=re.findall(r'\bFraming:\s*(full-body|half-body|knee-up)\b',section,re.I)
        if shot is None or header[2].upper()!=shot['master'] or any(f.lower()!=shot['framing'] for f in framings):
            raise ValueError('Legacy shot header conflicts with the current plan; explicitly prepare a new prompt')


def apply(prompt,plan,look=None,real_face_plan=None,*,strict=True):
    canonical=render(plan,look,real_face_plan)
    marked=BEGIN in prompt or END in prompt
    if marked:
        if prompt.count(BEGIN)!=1 or prompt.count(END)!=1 or canonical not in prompt:
            raise ValueError('Frozen shot plan block conflicts with the current plan')
    outside=prompt.replace(canonical,'',1) if marked else prompt
    pattern=r'^\s*(?:POSE|Shot)\s+\d+\s*:' if is_v2(plan) else r'^\s*(?:POSE|Shot)\s+[1-6]\s*:'
    if (strict or is_v2(plan)) and re.search(pattern,outside,re.I|re.M):
        raise ValueError('Remove legacy POSE/Shot blocks from prose; numbered arrangements come only from the current shot_plan')
    return prompt if marked else prompt.rstrip()+'\n'+canonical+'\n'


def _check_framing_guidance(plan):
    if 'framing_guidance' in plan and (type(plan['framing_guidance']) is not int or plan['framing_guidance'] not in (1,2)):
        raise ValueError('framing_guidance must be 1 or 2 when present')


def is_v2(plan):
    return isinstance(plan,dict) and type(plan.get('version')) is int and plan['version']==2


def active_looks(plan):
    """Execution order, retaining the full logical series in v2."""
    if not is_v2(plan):return plan['looks']
    by_id={item['shot_id']:item for item in plan['looks']}
    try:return [by_id[key] for key in plan['selected_shot_ids']]
    except (KeyError,TypeError) as error:raise ValueError('Unknown selected shot identity') from error


def shot_at(plan,look):
    rows=active_looks(plan)
    if type(look) is not int or not 1<=look<=len(rows):raise ValueError('Unknown active shot number')
    return rows[look-1]


def logical_count(plan):
    return len(plan['looks'])


def subset(plan,look,series_role='standalone'):
    """Select an existing active shot; never renumber it or discard its series."""
    result=copy.deepcopy(plan)
    selected_shot=copy.deepcopy(shot_at(plan,look))
    if is_v2(plan):
        if series_role not in {'standalone','series-first'}:raise ValueError('Choose a single-shot series role')
        if series_role=='series-first' and (selected_shot['slot']!=1 or logical_count(plan) not in (6,9)):
            raise ValueError('Only the actual first shot of a complete series can seed continuation')
        result['selected_shot_ids']=[selected_shot['shot_id']]
        result['series_role']=series_role
    else:
        result['looks']=[selected_shot]
    return result


def pose_selected(plan,look,preview=False):
    """The first-release preview uses reviewed text, not pose image attachments."""
    if not is_v2(plan) or preview:return set()
    ref=shot_at(plan,look).get('pose_reference')
    return {ref['sha256']} if ref else set()


def aesthetic_selected(plan,look,preview=False):
    if not is_v2(plan):return set()
    cells=active_looks(plan) if preview else [shot_at(plan,look)]
    return {h for cell in cells for h in cell.get('aesthetic_reference_sha256s',[])}


def body_text(shot):
    return shot['body_action']+' Hands: '+shot['hands']+' Support: '+shot['support']


def sync_real_face_plan(plan,face_plan):
    """Preparation helper only: caller freezes/reviews the resulting plan.

    Runtime validation checks equality and never silently repairs frozen content.
    """
    result=copy.deepcopy(face_plan)
    rows=active_looks(plan)
    if not is_v2(plan) or not isinstance(result,dict) or len(result.get('looks',[]))!=len(rows):
        raise ValueError('A v2 shot and real-face plan need matching active shots')
    for shot,face in zip(rows,result['looks']):face['body_action']=body_text(shot)
    return result


def _v2_line(value):
    return line(value) and not re.search(r'\[(?:/?Task |/?Current model)|(?:POSE|Shot)\s+\d+\s*:',value,re.I)


def _pose_helper():
    spec=importlib.util.spec_from_file_location('shot_plan_pose_catalog',Path(__file__).with_name('pose_catalog.py'))
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    return helper


def _got(value):
    """Describe an offending value briefly for validation messages (type or short repr)."""
    if value is None or isinstance(value,(bool,int,float)):return repr(value)
    if isinstance(value,str):return repr(value) if len(value)<=40 else repr(value[:37]+'...')
    name=type(value).__name__
    try:return f'{name} of {len(value)}'
    except TypeError:return name


def _check_views(path,views):
    if not isinstance(views,list) or not views:
        raise ValueError(path+' must be a nonempty list drawn from front, front-side, back, detail; got '+_got(views))
    bad=[v for v in views if not isinstance(v,str) or v not in VIEWS]
    if bad:raise ValueError(path+' must only contain front, front-side, back, detail; got '+_got(bad[0]))
    if len(views)!=len(set(views)):raise ValueError(path+' must not repeat a view; got '+_got(views))


BACK_WORDS=re.compile(r'back to (?:the )?camera|over[- ](?:the[- ])?shoulder|turned away|facing away|walking away|from behind|背对|回头|背影',re.I)


def _validate_v2(plan,inventory,*,context,count,identity,real_face_plan,strict_references,model_source):
    required={'version','sku','route','coverage','looks','selected_shot_ids','series_role'}
    keys=set(plan)-{'framing_guidance','variety_checks'}
    if keys!=required:
        raise ValueError('shot_plan must have exactly the keys '+', '.join(sorted(required))+' (optional: framing_guidance, variety_checks); missing: '
                         +(', '.join(sorted(required-keys)) or 'none')+'; unexpected: '+(', '.join(sorted(keys-required)) or 'none'))
    if not _v2_line(plan['sku']):raise ValueError('shot_plan.sku must be a nonempty single line; got '+_got(plan['sku']))
    if plan['route'] not in ('A','B'):raise ValueError('shot_plan.route must be "A" or "B"; got '+_got(plan['route']))
    _check_framing_guidance(plan)
    if 'variety_checks' in plan and (type(plan['variety_checks']) is not int or plan['variety_checks']!=1):
        raise ValueError('variety_checks must be 1 when present')
    variety=plan.get('variety_checks')==1
    if (not identity or context.get('output_form') not in ('human','faceless')
            or context.get('first_pose')=='custom' or context.get('purpose') in ('model-check','correction-edit')):
        raise ValueError('Version-2 shot planning applies to human/faceless delivery and preview only; got identity='+_got(identity)
                         +', output_form='+_got(context.get('output_form'))+', first_pose='+_got(context.get('first_pose'))
                         +', purpose='+_got(context.get('purpose')))
    if type(count) is not int or count not in (1,6,9):raise ValueError('count must be 1, 6 or 9 active shots; got '+_got(count))
    if not isinstance(inventory,list) or any(not isinstance(r,dict) or not isinstance(r.get('sha256'),str)
            or not re.fullmatch(r'[0-9a-f]{64}',r['sha256']) or not isinstance(r.get('role'),str) for r in inventory):
        raise ValueError('references must be a list of {sha256: 64 lowercase hex chars, role: string}; got '+_got(inventory))
    by_hash={r['sha256']:r for r in inventory}
    if len(by_hash)!=len(inventory):
        raise ValueError('references must not repeat a sha256; got '+str(len(inventory)-len(by_hash))+' duplicate(s)')
    catalog=_pose_helper()
    catalog.check_inventory(inventory)
    garments={h for h,r in by_hash.items() if r['role']=='garment-source'}
    coverage=plan['coverage'];seen=set();usable={}
    if not isinstance(coverage,list) or not coverage:
        raise ValueError('shot_plan.coverage must be a nonempty list of reviewed garment-source entries; got '+_got(coverage))
    for i,ref in enumerate(coverage):
        path=f'shot_plan.coverage[{i}]'
        if not isinstance(ref,dict):raise ValueError(path+' must be an object; got '+_got(ref))
        if set(ref)!={'sha256','views','usable','same_sku','note'}:
            raise ValueError(path+' must have exactly the keys note, same_sku, sha256, usable, views; got '+(', '.join(sorted(ref)) or 'none'))
        if not isinstance(ref['sha256'],str) or ref['sha256'] not in garments:
            raise ValueError(path+'.sha256 must be the sha256 of a garment-source reference; got '+_got(ref['sha256']))
        if ref['sha256'] in seen:raise ValueError(path+'.sha256 repeats an earlier coverage entry: '+ref['sha256'])
        if type(ref['usable']) is not bool:raise ValueError(path+'.usable must be true or false; got '+_got(ref['usable']))
        if type(ref['same_sku']) is not bool:raise ValueError(path+'.same_sku must be true or false; got '+_got(ref['same_sku']))
        if not _v2_line(ref['note']):raise ValueError(path+'.note must be a nonempty single line of review notes; got '+_got(ref['note']))
        _check_views(path+'.views',ref['views'])
        seen.add(ref['sha256'])
        if ref['usable'] and ref['same_sku']:usable[ref['sha256']]=set(ref['views'])
    supported=set().union(*usable.values()) if usable else set()
    if 'front' not in supported:
        raise ValueError('shot_plan.coverage must include a usable same_sku entry whose views contain "front"; usable views: '
                         +(', '.join(sorted(supported)) or 'none'))
    expected_route='A' if 'back' in supported else 'B'
    if plan['route']!=expected_route:
        raise ValueError(f'shot_plan.route must be "{expected_route}" because usable same_sku back coverage is '
                         +('present' if 'back' in supported else 'absent')+'; got '+_got(plan['route']))
    looks=plan['looks']
    if not isinstance(looks,list) or len(looks) not in (1,6,9):
        raise ValueError('shot_plan.looks must be a list of 1, 6 or 9 logical shots; got '+_got(looks))
    fields={'slot','shot_id','display_goal','must_show','reason','body_action','hands','support','framing','garment_views','reference_sha256s'}
    optional={'head','gaze','pose_reference','aesthetic_reference_sha256s','scene','lighting','camera'}
    ids=[];action_keys={}
    head_gaze=any(isinstance(s,dict) and ('head' in s or 'gaze' in s) for s in looks)
    if head_gaze and (model_source not in ('ai','new') or real_face_plan is not None or context.get('output_form')!='human'):
        raise ValueError('looks[*].head/gaze are only for AI/new visible portraits; real faces use the reviewed real_face_plan; got model_source='
                         +_got(model_source)+', output_form='+_got(context.get('output_form')))
    for slot,shot in enumerate(looks,1):
        path=f'shot_plan.looks[{slot-1}]'
        if not isinstance(shot,dict):raise ValueError(path+' must be an object; got '+_got(shot))
        keys=set(shot)-optional
        if keys!=fields:
            raise ValueError(path+' must have exactly the keys '+', '.join(sorted(fields))+' (optional: '+', '.join(sorted(optional))
                             +'); missing: '+(', '.join(sorted(fields-keys)) or 'none')+'; unexpected: '+(', '.join(sorted(keys-fields)) or 'none'))
        if type(shot['slot']) is not int or shot['slot']!=slot:
            raise ValueError(path+f'.slot must be {slot} (logical slots stay complete and ordered); got '+_got(shot['slot']))
        if not isinstance(shot['shot_id'],str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}',shot['shot_id']):
            raise ValueError(path+'.shot_id must be 1-80 letters, digits, "_" or "-" starting with a letter or digit; got '+_got(shot['shot_id']))
        if shot['shot_id'] in ids:raise ValueError(path+'.shot_id must be unique; "'+shot['shot_id']+'" is already used by an earlier shot')
        ids.append(shot['shot_id'])
        for k in ('display_goal','reason','body_action','hands','support'):
            if not _v2_line(shot[k]):raise ValueError(path+'.'+k+' must be a nonempty single line without POSE/Shot headers; got '+_got(shot[k]))
        if len(body_text(shot))>1000:
            raise ValueError(path+'.body_action + hands + support must total at most 1000 characters; got '+str(len(body_text(shot))))
        must=shot['must_show']
        if not isinstance(must,list) or not must:
            raise ValueError(path+'.must_show must be a nonempty list of distinct strings, e.g. ["collar", "hem"]; got '+_got(must))
        bad=[v for v in must if not _v2_line(v)]
        if bad:raise ValueError(path+'.must_show items must be nonempty single lines; got '+_got(bad[0]))
        if len(must)!=len(set(must)):raise ValueError(path+'.must_show must not repeat an item; got '+_got(must))
        if shot['framing'] not in ('full-body','half-body','knee-up','detail'):
            raise ValueError(path+'.framing must be one of full-body, half-body, knee-up, detail; got '+_got(shot['framing']))
        if head_gaze:
            for k in ('head','gaze'):
                if not _v2_line(shot.get(k)):
                    raise ValueError(path+'.'+k+' must be a nonempty single line on every shot once any shot declares head/gaze; got '+_got(shot.get(k)))
        refs=shot['reference_sha256s']
        if not isinstance(refs,list) or not refs:
            raise ValueError(path+'.reference_sha256s must be a nonempty list of usable same_sku garment-source hashes; got '+_got(refs))
        for h in refs:
            if not isinstance(h,str) or h not in usable:
                raise ValueError(path+'.reference_sha256s must only name usable same_sku coverage hashes; got '+_got(h)
                                 +'; usable: '+(', '.join(sorted(usable)) or 'none'))
        if len(refs)!=len(set(refs)):raise ValueError(path+'.reference_sha256s must not repeat a hash; got '+_got(refs))
        views=shot['garment_views']
        _check_views(path+'.garment_views',views)
        selected_views=set().union(*(usable[h] for h in refs))
        if not set(views)<=selected_views:
            raise ValueError(path+'.garment_views must be covered by its reference_sha256s coverage; not covered: '
                             +', '.join(sorted(set(views)-selected_views))+' (covered: '+(', '.join(sorted(selected_views)) or 'none')+')')
        for k in ('scene','lighting','camera'):
            if k in shot and not _v2_line(shot[k]):
                raise ValueError(path+'.'+k+' must be a nonempty single line when given (it overrides the style card for this shot); got '+_got(shot[k]))
        if variety and 'back' not in views and (m:=BACK_WORDS.search(shot['body_action']+' '+(shot.get('head') or ''))):
            raise ValueError(path+'.body_action/head must not turn away from the camera ("'+m.group(0)+'") when garment_views has no "back"; add back coverage or change the action')
        key=(shot['framing'],' '.join(re.sub(r'[\W_]+',' ',shot['body_action'].casefold()).split()))
        if variety and key in action_keys:
            raise ValueError(path+'.body_action repeats shot_plan.looks['+str(action_keys[key])+'] with the same framing; give each shot a different body action or framing')
        action_keys[key]=slot-1
        if 'pose_reference' in shot:
            ref=shot['pose_reference']
            if (not isinstance(ref,dict) or set(ref)!={'sha256','reason'} or not _v2_line(ref['reason'])
                    or not isinstance(ref['sha256'],str) or ref['sha256'] not in by_hash
                    or by_hash[ref['sha256']]['role']!='pose-reference'):
                raise ValueError(path+'.pose_reference must be {sha256: <one pose-reference inventory hash>, reason: <single line>}; got '+_got(ref))
            catalog.validate_reference(by_hash[ref['sha256']])
        aesthetic=shot.get('aesthetic_reference_sha256s',[])
        if (not isinstance(aesthetic,list) or any(not isinstance(h,str) or h not in by_hash or by_hash[h]['role']!='aesthetic-reference' for h in aesthetic)
                or len(aesthetic)!=len(set(aesthetic))):
            raise ValueError(path+'.aesthetic_reference_sha256s must be a list of distinct aesthetic-reference hashes; got '+_got(aesthetic))
    selected_ids=plan['selected_shot_ids']
    if not isinstance(selected_ids,list) or any(not isinstance(s,str) for s in selected_ids):
        raise ValueError('shot_plan.selected_shot_ids must be a list of shot_id strings; got '+_got(selected_ids))
    if len(selected_ids)!=count:
        raise ValueError(f'shot_plan.selected_shot_ids must have exactly {count} entries (the active execution count); got {len(selected_ids)}')
    unknown=[s for s in selected_ids if s not in ids]
    if unknown:raise ValueError('shot_plan.selected_shot_ids must only name looks[*].shot_id values; unknown: '+', '.join(unknown))
    if len(selected_ids)!=len(set(selected_ids)):
        raise ValueError('shot_plan.selected_shot_ids must not repeat a shot_id; got '+_got(selected_ids))
    role=plan['series_role']
    if role=='series':
        if len(looks) not in (6,9) or selected_ids!=ids:
            raise ValueError('series_role "series" requires a complete six/nine plan with selected_shot_ids equal to every looks[*].shot_id in order; got '
                             +str(len(looks))+' looks, selected '+_got(selected_ids))
    elif role=='standalone':
        if len(selected_ids)!=1:raise ValueError('series_role "standalone" requires exactly one selected_shot_id; got '+str(len(selected_ids)))
    elif role=='series-first':
        if len(looks) not in (6,9) or selected_ids!=ids[:1]:
            raise ValueError('series_role "series-first" requires a complete six/nine plan with selected_shot_ids equal to the actual first shot_id only; got '
                             +str(len(looks))+' looks, selected '+_got(selected_ids))
    else:raise ValueError('shot_plan.series_role must be "standalone", "series-first" or "series"; got '+_got(role))
    active=active_looks(plan)
    if context.get('first_pose')!=active[0]['slot']:
        raise ValueError(f'context.first_pose must equal the first selected shot slot {active[0]["slot"]}; got '+_got(context.get('first_pose')))
    if context.get('purpose')=='preview-grid' and role!='series':
        raise ValueError('Preview must show the complete frozen series: series_role must be "series" when purpose is preview-grid; got '+_got(role))
    if real_face_plan is not None:
        if len(real_face_plan.get('looks',[]))!=count:
            raise ValueError(f'real_face_plan.looks must have exactly {count} entries matching the active shots; got '+str(len(real_face_plan.get('looks',[]))))
        for i,(shot,face) in enumerate(zip(active,real_face_plan['looks'])):
            if face.get('body_action')!=body_text(shot):
                raise ValueError(f'real_face_plan.looks[{i}].body_action must mirror the frozen shot body/hand/support text (Real face body action must mirror the shot plan); got '+_got(face.get('body_action')))
            face_refs=set(face['reference_sha256s'])
            if not set(shot['reference_sha256s'])<=face_refs:
                raise ValueError(f'real_face_plan.looks[{i}].reference_sha256s must retain this shot garment references; missing: '
                                 +', '.join(sorted(set(shot['reference_sha256s'])-face_refs)))
            if strict_references and not face_refs.intersection(garments)<=set(usable):
                raise ValueError(f'real_face_plan.looks[{i}].reference_sha256s garments must all have usable same-SKU coverage; not usable: '
                                 +', '.join(sorted(face_refs.intersection(garments)-set(usable))))
    return copy.deepcopy(plan)

def _render_v2(plan,look,real_face_plan):
    rows=[BEGIN,'Garment route: '+plan['route']+'; garment-driven shot plan v2.',
          'Logical series: '+str(logical_count(plan))+'.']
    cells=active_looks(plan) if look is None else [shot_at(plan,look)]
    for shot in cells:
        rows.extend([f"Shot {shot['slot']}: {shot['shot_id']}. {framing_line(plan,shot['framing'])}",
                     'Display purpose: '+shot['display_goal'], 'Must show: '+', '.join(shot['must_show'])+'.',
                     'Selection reason: '+shot['reason'], body_text(shot),
                     'Supported garment views: '+', '.join(shot['garment_views'])+'.'])
        if 'head' in shot:rows.extend(['Head orientation: '+shot['head'],'Eye gaze: '+shot['gaze']])
        if 'pose_reference' in shot:
            rows.append('Optional body-only reference reason: '+shot['pose_reference']['reason']+' Copy no identity, body proportions, clothing or illustration style; preview uses the described action only.')
        if real_face_plan is not None:
            rows.append('The reviewed real-face plan mirrors this body action and supplies supported head/gaze; it cannot establish another real face angle.')
    return '\n'.join(rows+[END])
