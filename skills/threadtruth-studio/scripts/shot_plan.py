"""Source-backed garment routes and numbered shot plans. No image understanding or network."""
import copy
import importlib.util
from pathlib import Path
import re

BEGIN='[Task shot plan]'
END='[/Task shot plan]'
MASTERS=['SIDE_TURN_STANDING','SIDE_LEANING_WALL','UPRIGHT_SEATED','FRONT_LIGHT_STEP','SLIGHT_FORWARD_LEAN','BACK_TURN_GLANCE']
FRAMINGS=['full-body','full-body','half-body','full-body','knee-up','full-body']
# WP-6b: breathing room. Rendered only when the plan carries framing_guidance=1 (new plans); frozen legacy plans keep their bytes.
FRAMING_GUIDANCE={
    'full-body':'Wide full-length shot from farther back: leave about one and a half head-heights of empty space above the hair and about one head-height of floor below the shoes, so the figure fills roughly three quarters of the frame height and never touches the top or bottom edge.',
    'knee-up':'Head to just below the knees, with about one head-height of empty space above the hair; the head never touches the top edge.',
    'half-body':'Head to waist or hips, with about one head-height of empty space above the hair; the head never touches the top edge.',
}


def framing_line(plan,framing):
    text='Framing: '+framing+'.'
    if plan.get('framing_guidance')==1 and framing in FRAMING_GUIDANCE:text+=' '+FRAMING_GUIDANCE[framing]
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
    return dict(version=1,sku=sku,route='A' if back else 'B',preservation='classic',adaptation_note='',coverage=copy.deepcopy(coverage),looks=looks,framing_guidance=1)


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
    if 'framing_guidance' in plan and (type(plan['framing_guidance']) is not int or plan['framing_guidance']!=1):
        raise ValueError('framing_guidance must be 1 when present')


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


def _validate_v2(plan,inventory,*,context,count,identity,real_face_plan,strict_references,model_source):
    required={'version','sku','route','coverage','looks','selected_shot_ids','series_role'}
    if set(plan)-{'framing_guidance'}!=required or not _v2_line(plan['sku']) or plan['route'] not in ('A','B'):
        raise ValueError('Version-2 shot plan requires SKU, route, original coverage, complete looks, selected shot IDs and series role')
    _check_framing_guidance(plan)
    if (not identity or context.get('output_form') not in ('human','faceless')
            or context.get('first_pose')=='custom' or context.get('purpose') in ('model-check','correction-edit')):
        raise ValueError('Version-2 shot planning applies to human/faceless delivery and preview')
    if type(count) is not int or count not in (1,6,9):raise ValueError('One, six or nine active shots required')
    if not isinstance(inventory,list) or any(not isinstance(r,dict) or not isinstance(r.get('sha256'),str)
            or not re.fullmatch(r'[0-9a-f]{64}',r['sha256']) or not isinstance(r.get('role'),str) for r in inventory):
        raise ValueError('Reference inventory requires original hashes and roles')
    by_hash={r['sha256']:r for r in inventory}
    if len(by_hash)!=len(inventory):raise ValueError('Reference hashes and roles must be unambiguous')
    catalog=_pose_helper()
    catalog.check_inventory(inventory)
    garments={h for h,r in by_hash.items() if r['role']=='garment-source'}
    coverage=plan['coverage'];seen=set();usable={}
    if not isinstance(coverage,list) or not coverage:raise ValueError('Review original garment coverage first')
    for ref in coverage:
        if (not isinstance(ref,dict) or set(ref)!={'sha256','views','usable','same_sku','note'}
                or not isinstance(ref['sha256'],str) or ref['sha256'] not in garments or ref['sha256'] in seen
                or type(ref['usable']) is not bool or type(ref['same_sku']) is not bool
                or not _v2_line(ref['note']) or not isinstance(ref['views'],list) or not ref['views']
                or any(not isinstance(v,str) or v not in VIEWS for v in ref['views'])
                or len(ref['views'])!=len(set(ref['views']))):
            raise ValueError('Garment coverage binds distinct original hashes, reviewed views, usability and same-SKU evidence')
        seen.add(ref['sha256'])
        if ref['usable'] and ref['same_sku']:usable[ref['sha256']]=set(ref['views'])
    supported=set().union(*usable.values()) if usable else set()
    if 'front' not in supported:raise ValueError('A usable same-SKU front is required')
    if plan['route']!=('A' if 'back' in supported else 'B'):raise ValueError('Garment route must match original back coverage')
    looks=plan['looks']
    if not isinstance(looks,list) or len(looks) not in (1,6,9):raise ValueError('Keep the complete one, six or nine logical shots')
    fields={'slot','shot_id','display_goal','must_show','reason','body_action','hands','support','framing','garment_views','reference_sha256s'}
    optional={'head','gaze','pose_reference','aesthetic_reference_sha256s'}
    ids=[]
    head_gaze=any(isinstance(s,dict) and ('head' in s or 'gaze' in s) for s in looks)
    if head_gaze and (model_source not in ('ai','new') or real_face_plan is not None or context.get('output_form')!='human'):
        raise ValueError('AI/new visible portraits own shot head/gaze; real faces use reviewed real_face_plan')
    for slot,shot in enumerate(looks,1):
        if not isinstance(shot,dict) or set(shot)-optional!=fields or type(shot['slot']) is not int or shot['slot']!=slot:
            raise ValueError('Logical slots must be complete and ordered, independently of body actions')
        if (not isinstance(shot['shot_id'],str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}',shot['shot_id'])
                or shot['shot_id'] in ids):raise ValueError('Each logical shot needs a unique stable shot_id')
        ids.append(shot['shot_id'])
        if any(not _v2_line(shot[k]) for k in ('display_goal','reason','body_action','hands','support')):
            raise ValueError('Every shot needs reviewed display purpose, reason and actual body/hand/support relationships')
        if len(body_text(shot))>1000:raise ValueError('Combined body, hands and support must fit the real-face body contract')
        if (not isinstance(shot['must_show'],list) or not shot['must_show']
                or any(not _v2_line(v) for v in shot['must_show']) or len(shot['must_show'])!=len(set(shot['must_show']))):
            raise ValueError('Declare distinct visible garment features for the shot purpose')
        if shot['framing'] not in ('full-body','half-body','knee-up','detail'):raise ValueError('Unknown shot framing')
        if head_gaze and (not _v2_line(shot.get('head')) or not _v2_line(shot.get('gaze'))):
            raise ValueError('Declare both head orientation and eye gaze for every AI/new shot')
        refs=shot['reference_sha256s'];views=shot['garment_views']
        if (not isinstance(refs,list) or not refs or any(not isinstance(h,str) or h not in usable for h in refs)
                or len(refs)!=len(set(refs)) or not isinstance(views,list) or not views
                or any(not isinstance(v,str) or v not in VIEWS for v in views) or len(views)!=len(set(views))):
            raise ValueError('Every shot needs usable same-SKU garment references and declared coverage')
        selected_views=set().union(*(usable[h] for h in refs))
        if not set(views)<=selected_views:raise ValueError('Shot garment views require selected original garment coverage')
        if 'pose_reference' in shot:
            ref=shot['pose_reference']
            if (not isinstance(ref,dict) or set(ref)!={'sha256','reason'} or not _v2_line(ref['reason'])
                    or not isinstance(ref['sha256'],str) or ref['sha256'] not in by_hash
                    or by_hash[ref['sha256']]['role']!='pose-reference'):
                raise ValueError('A shot may select one reviewed pose-reference inventory hash with its reason')
            catalog.validate_reference(by_hash[ref['sha256']])
        aesthetic=shot.get('aesthetic_reference_sha256s',[])
        if (not isinstance(aesthetic,list) or any(not isinstance(h,str) or h not in by_hash or by_hash[h]['role']!='aesthetic-reference' for h in aesthetic)
                or len(aesthetic)!=len(set(aesthetic))):raise ValueError('Aesthetic selection binds distinct aesthetic-reference hashes only')
    selected_ids=plan['selected_shot_ids']
    if (not isinstance(selected_ids,list) or len(selected_ids)!=count or any(not isinstance(s,str) or s not in ids for s in selected_ids)
            or len(selected_ids)!=len(set(selected_ids))):raise ValueError('Selected shot identities must match the active execution count')
    role=plan['series_role']
    if role=='series':
        if len(looks) not in (6,9) or selected_ids!=ids:raise ValueError('Series execution selects every logical shot in order')
    elif role=='standalone':
        if len(selected_ids)!=1:raise ValueError('Standalone execution selects exactly one shot')
    elif role=='series-first':
        if len(looks) not in (6,9) or selected_ids!=ids[:1]:raise ValueError('Series-first selects the actual first shot of a complete six/nine plan')
    else:raise ValueError('Declare standalone, series-first or series execution')
    active=active_looks(plan)
    if context.get('first_pose')!=active[0]['slot']:raise ValueError('Task first slot must match its selected source shot')
    if context.get('purpose')=='preview-grid' and role!='series':raise ValueError('Preview must show the complete frozen series')
    if real_face_plan is not None:
        if len(real_face_plan.get('looks',[]))!=count:raise ValueError('Real face plan must align with active shot identities')
        for shot,face in zip(active,real_face_plan['looks']):
            if face.get('body_action')!=body_text(shot):raise ValueError('Real face body action must mirror the frozen shot body/hand/support plan')
            face_refs=set(face['reference_sha256s'])
            if not set(shot['reference_sha256s'])<=face_refs:raise ValueError('Real face selections must retain this shot garment references')
            if strict_references and not face_refs.intersection(garments)<=set(usable):
                raise ValueError('Every real-selected garment needs usable same-SKU coverage')
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
