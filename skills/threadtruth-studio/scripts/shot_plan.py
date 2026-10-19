"""Source-backed garment routes and numbered shot plans. No image understanding or network."""
import copy
import re

BEGIN='[Task shot plan]'
END='[/Task shot plan]'
MASTERS=['SIDE_TURN_STANDING','SIDE_LEANING_WALL','UPRIGHT_SEATED','FRONT_LIGHT_STEP','SLIGHT_FORWARD_LEAN','BACK_TURN_GLANCE']
FRAMINGS=['full-body','full-body','half-body','full-body','knee-up','full-body']
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
    return dict(version=1,sku=sku,route='A' if back else 'B',preservation='classic',adaptation_note='',coverage=copy.deepcopy(coverage),looks=looks)


def validate(plan,inventory,*,context,count,identity=True,real_face_plan=None,strict_references=True,model_source=None):
    fields={'version','sku','route','preservation','adaptation_note','coverage','looks'}
    if not isinstance(plan,dict) or set(plan)!=fields or type(plan['version']) is not int or plan['version']!=1:
        raise ValueError('Shot plan requires version=1, sku, route, preservation, adaptation_note, coverage and looks')
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
    cells=plan['looks'] if preview else [plan['looks'][look-1]]
    return {h for cell in cells for h in cell['reference_sha256s']}


def render(plan,look=None,real_face_plan=None):
    rows=[BEGIN,'Garment route: '+plan['route']+'; preservation: '+plan['preservation']+'.']
    if plan['preservation']=='adapted':rows.append('Agreed adaptation: '+plan['adaptation_note'])
    cells=list(enumerate(plan['looks'],1))
    if look is not None:cells=[cells[look-1]]
    for i,shot in cells:
        n=shot['pose'];relation=FRONT_RELATION if shot['master']=='FRONT_RELAXED_STANDING' else RELATIONS[n-1]
        rows.extend([f"Shot {n}: {shot['master']}. Framing: {shot['framing']}.",
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
    if strict and re.search(r'^\s*(?:POSE|Shot)\s+[1-6]\s*:',outside,re.I|re.M):
        raise ValueError('Remove legacy POSE/Shot blocks from prose; numbered arrangements come only from the current shot_plan')
    return prompt if marked else prompt.rstrip()+'\n'+canonical+'\n'
