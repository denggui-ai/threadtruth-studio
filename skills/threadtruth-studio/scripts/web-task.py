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
_visual_plans = None
_web_execution = None
_pose_catalog = None


def pose_helper():
    global _pose_catalog
    if _pose_catalog is None:
        spec=importlib.util.spec_from_file_location('task_pose_catalog',Path(__file__).with_name('pose_catalog.py'))
        _pose_catalog=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_pose_catalog)
    return _pose_catalog


def v2(plan):
    return isinstance(plan,dict) and plan.get('version')==2


def inherit_framing_flag(plan,frozen):
    """WP-10a: a caller-supplied v2 plan that omits framing_guidance keeps the frozen task's flag; explicit values go to validation."""
    if v2(plan) and v2(frozen) and 'framing_guidance' not in plan and 'framing_guidance' in frozen:
        return dict(plan,framing_guidance=frozen['framing_guidance'])
    return plan


def selected_references(inventory,context,shot_plan,face_plan,look):
    """One ordered selection used by preparation, revisions and both exporters."""
    preview=context.get('purpose')=='preview-grid'
    if face_plan is not None:
        cells=face_plan['looks'] if preview else [face_plan['looks'][look-1]]
        ids=list(dict.fromkeys(h for cell in cells for h in cell['reference_sha256s']))
        by_hash={r['sha256']:r for r in inventory}
        rows=([r for r in inventory if r['sha256'] in ids] if preview
              else [by_hash[h] for h in ids])
    else:
        rows=list(inventory)
    if v2(shot_plan):
        cells=shot_helper().active_looks(shot_plan) if preview else [shot_helper().shot_at(shot_plan,look)]
        garments={h for cell in cells for h in cell['reference_sha256s']}
        aesthetics={h for cell in cells for h in cell.get('aesthetic_reference_sha256s',[])}
        poses=shot_helper().pose_selected(shot_plan,look,preview)
        selected=garments|aesthetics|poses
        # Face plans own original identity selection. Optional art/pose inputs
        # are selected by the same shot contract, never leaked across shots.
        rows=[r for r in rows if r['role'] in ('identity-reference','model-supplement') or r['sha256'] in selected]
        present={r['sha256'] for r in rows}
        rows += [r for r in inventory if r['sha256'] in selected-present]
    elif shot_plan is not None and face_plan is None:
        ids=shot_helper().selected(shot_plan,look,preview)
        rows=[r for r in rows if r['role']!='garment-source' or r['sha256'] in ids]
    return rows


def preflight_references(inventory,context,shot_plan,face_plan,count,identity,route):
    for number in range(1,count+1):
        rows=selected_references(inventory,context,shot_plan,face_plan,number)
        native_reference_check(rows,route,extra_anchor=int(identity and count>1 and number>1))


def preflight_series(inventory,context,plan,face_plan,identity,route):
    """Check known future requirements before charging for a preview or trial."""
    if not v2(plan) or plan['series_role']=='standalone':return
    full=copy.deepcopy(plan)
    full.update(series_role='series',selected_shot_ids=[s['shot_id'] for s in full['looks']])
    future_face=face_plan
    if face_plan is not None and len(face_plan['looks'])==1:
        # Only a lower bound is known for future real-face selections. Never
        # invent their face coverage/identity approval; continuation checks them.
        primary=face_plan['primary_identity_sha256']
        future_face=copy.deepcopy(face_plan)
        future_face['looks']=[face_plan['looks'][0]]+[
            dict(reference_sha256s=[primary]+s['reference_sha256s']) for s in full['looks'][1:]]
    preflight_references(inventory,dict(context,purpose='delivery'),full,future_face,len(full['looks']),identity,route)


def web_execution_helper():
    global _web_execution
    if _web_execution is None:
        spec=importlib.util.spec_from_file_location('task_web_execution',Path(__file__).with_name('web_execution.py'))
        _web_execution=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_web_execution)
    return _web_execution


def visual_helper():
    global _visual_plans
    if _visual_plans is None:
        spec=importlib.util.spec_from_file_location('task_visual_plan',Path(__file__).with_name('visual_plan.py'))
        _visual_plans=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_visual_plans)
    return _visual_plans

def shot_helper():
    global _shot_plans
    if _shot_plans is None:
        spec=importlib.util.spec_from_file_location('task_shot_plan',Path(__file__).with_name('shot_plan.py'))
        _shot_plans=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_shot_plans)
    return _shot_plans


def plan_fingerprint(data):
    frozen=dict(version=data.get('plan_version',0),context=data.get('context'),
                model=data.get('model'),shot_plan=data.get('shot_plan'))
    if 'visual_plan' in data:frozen['visual_plan']=data['visual_plan']
    if 'identity_instruction_version' in data:frozen['identity_instruction_version']=data['identity_instruction_version']
    return object_hash(frozen)



def prompt_contract(data,row=None):
    value=(row or {}).get('prompt_contract_version',data.get('prompt_contract_version',0))
    if type(value) is not int or value not in (0,1,2):
        raise ValueError('Unsupported prompt contract version')
    return value


def adopt_prompt_contract(data):
    # Explicit preparation adopts current semantics; historical bytes keep theirs.
    version=prompt_contract(data)
    wanted=2 if 'visual_plan' in data else 1
    if version==wanted:return
    for row in evidence_rows(data):
        row.setdefault('prompt_contract_version',version)
        for prior in row.get('prompt_history',[]):
            prior.setdefault('prompt_contract_version',row['prompt_contract_version'])
    data['prompt_contract_version']=wanted


def check_shot_plan(data):
    if 'shot_plan' not in data:
        if 'shot_plan_sha256' in data:raise ValueError('Missing frozen shot plan')
        return
    if data['schema_version']!=2 or object_hash(data['shot_plan'])!=data.get('shot_plan_sha256'):
        raise ValueError('Frozen shot plan changed')
    shot_helper().validate(data['shot_plan'],data['references'],context=data['context'],
        count=face_plan_count(data['context'],len(data['looks']),data.get('shot_plan')),identity=data['identity'],real_face_plan=data.get('real_face_plan'),
        strict_references=prompt_contract(data)>=1,model_source=(data.get('model') or {}).get('source_type'))
    history=data.get('shot_plan_history',[])
    if not isinstance(history,list):raise ValueError('Invalid shot plan history')
    for prior in history:
        if (not isinstance(prior,dict) or set(prior)!={'plan','sha256','note'}
                or object_hash(prior['plan'])!=prior['sha256'] or not prior['note'].strip()
                or (not (v2(data['shot_plan']) and data['shot_plan']['series_role']=='standalone')
                    and prior['plan']['looks'][0]!=data['shot_plan']['looks'][0])):
            raise ValueError('Historical first-shot plan changed')



def check_visual_plan(data):
    if 'visual_plan' not in data:
        if 'visual_plan_sha256' in data or prompt_contract(data)==2:
            raise ValueError('Prompt contract 2 requires a frozen visual plan')
        return
    if (data['schema_version']!=2 or prompt_contract(data)!=2
            or object_hash(data['visual_plan'])!=data.get('visual_plan_sha256')):
        raise ValueError('Frozen visual plan or prompt contract changed')
    visual_helper().validate(data['visual_plan'],data['references'],context=data['context'],
        count=face_plan_count(data['context'],len(data['looks']),data.get('shot_plan')),identity=data['identity'],shot_plan=data.get('shot_plan'))
    history=data.get('visual_plan_history',[])
    if not isinstance(history,list):raise ValueError('Invalid visual plan history')
    for prior in history:
        if (not isinstance(prior,dict) or set(prior)!={'plan','sha256','note'}
                or object_hash(prior['plan'])!=prior['sha256'] or not prior['note'].strip()
                or any(prior['plan'][k]!=data['visual_plan'].get(k) for k in prior['plan'] if k not in ('shots','persona','persona_model_sha256'))
                or (not (v2(data.get('shot_plan')) and data['shot_plan']['series_role']=='standalone')
                    and prior['plan']['shots'][0]!=data['visual_plan']['shots'][0])):
            raise ValueError('Historical approved visual plan changed')


def prompt_check(prompt,context,model=None,shot_plan=None,number=1,real_face_plan=None,visual_plan=None):
    photography_helper().apply(prompt,context.get('photography_targets'))
    if model is not None:models.apply_conditions(prompt,model,allow_child=True)
    if shot_plan is not None:
        shot_helper().apply(prompt,shot_plan,None if context.get('purpose')=='preview-grid' else number,real_face_plan)
    if visual_plan is not None:
        if visual_plan.get('persona') and model is not None and model.get('subject')=='child model':
            raise ValueError('Visual persona is not injected for child models; prepare the plan without a persona')
        if visual_plan.get('persona') and (model is None or object_hash(model)!=visual_plan.get('persona_model_sha256')):
            raise ValueError('Visual persona was resolved against a different model; prepare the plan again')
        look=None if context.get('purpose')=='preview-grid' else number
        if (visual_plan['output_form'] in ('human','faceless') and context['first_pose']!='custom'
                and context.get('purpose') not in ('model-check','correction-edit') and shot_plan is None):
            raise ValueError('Numbered human/faceless visual tasks require a reviewed source-backed shot_plan')
        if shot_plan is not None:
            usable={r['sha256'] for r in shot_plan['coverage'] if r['usable'] and r['same_sku']}
            if not set(visual_plan['garment']['source_sha256s'])<=usable:
                raise ValueError('Visual garment facts must use reviewed same-SKU usable shot sources')
        if real_face_plan is not None and visual_plan['output_form']=='faceless':
            cells=real_face_plan['looks'] if look is None else [real_face_plan['looks'][number-1]]
            if any(cell['face_visible'] for cell in cells):
                raise ValueError('Faceless visual output cannot override a conflicting visible real-face plan')
        blocks=[]
        if context.get('photography_targets'):blocks.append(photography_helper().render(context['photography_targets']))
        if model is not None:blocks.append(models.apply_conditions('',model,allow_child=True).strip())
        if shot_plan is not None:blocks.append(shot_helper().render(shot_plan,look,real_face_plan))
        visual_helper().check_prompt(prompt,visual_plan,look,managed_blocks=blocks)


def delivery_retry_candidate(data,row,*,shot_plan=None,visual_plan=None,prompt=None):
    """Clarify one rejected non-anchor arrangement without replacing shared plans."""
    standalone=(v2(data.get('shot_plan')) and data['shot_plan']['series_role']=='standalone'
                and len(data['looks'])==1 and not data.get('model_confirmation'))
    if (data['schema_version']!=2 or is_preview(data) or row is None
            or (row['number']==1 and not standalone) or row['state']!='rejected'
            or any(x['state'] in ('reserved','unknown') for x in data['looks'])):
        raise ValueError('Revise only a rejected non-anchor delivery with no unresolved request')
    number=row['number'];index=number-1
    current_shot=data.get('shot_plan');current_visual=data.get('visual_plan')
    if current_shot is None or current_visual is None:
        raise ValueError('Structured delivery retry requires existing shot and visual plans')
    if v2(current_shot):
        shot=copy.deepcopy(current_shot if shot_plan is None else inherit_framing_flag(shot_plan,current_shot))
        visual=copy.deepcopy(current_visual if visual_plan is None else visual_plan)
        target=shot_helper().shot_at(current_shot,number)
        replacement=shot_helper().shot_at(shot,number)
        allowed=copy.deepcopy(current_shot)
        if any(replacement[k]!=target[k] for k in ('slot','shot_id')):
            raise ValueError('A retry retains the stable shot identity')
        allowed['looks'][target['slot']-1]=copy.deepcopy(replacement)
        allowed_visual=copy.deepcopy(current_visual)
        allowed_visual['shots'][index]=copy.deepcopy(visual['shots'][index])
        if shot!=allowed or visual!=allowed_visual:
            raise ValueError('Revise only the rejected shot, retaining all shared conditions and other shots')
        if shot==current_shot and visual==current_visual:
            raise ValueError('Structured retry requires an actual local plan change')
        face=copy.deepcopy(data.get('real_face_plan'))
        if face is not None:
            face=shot_helper().sync_real_face_plan(shot,face)
            garments={r['sha256'] for r in data['references'] if r['role']=='garment-source'}
            cell=face['looks'][index]
            cell['reference_sha256s']=[h for h in cell['reference_sha256s'] if h not in garments]+replacement['reference_sha256s']
            real_face_helper().validate(face,data['references'],schema_version=2,identity=data['identity'],
                model=data['model'],context=data['context'],count=len(data['looks']),route=data['route'],
                strict_looks=(number,),shot_plan=shot)
        shot_helper().validate(shot,data['references'],context=data['context'],count=len(data['looks']),
            identity=data['identity'],real_face_plan=face,model_source=data['model']['source_type'])
        visual_helper().validate(visual,data['references'],context=data['context'],count=len(data['looks']),
            identity=data['identity'],shot_plan=shot)
        preflight_references(data['references'],data['context'],shot,face,len(data['looks']),data['identity'],data['route'])
        compiled=visual_helper().compile_prompt(visual,number) if prompt is None else prompt
        prompt_check(compiled,data['context'],data['model'],shot,number,face,visual)
        result=dict(shot_plan=shot,visual_plan=visual,prompt=compiled)
        if face is not None:result['real_face_plan']=face
        return result
    shot=copy.deepcopy(current_shot if shot_plan is None else shot_plan)
    visual=copy.deepcopy(current_visual if visual_plan is None else visual_plan)
    shot_helper().validate(shot,data['references'],context=data['context'],
        count=face_plan_count(data['context'],len(data['looks']),data.get('shot_plan')),identity=data['identity'],
        real_face_plan=data.get('real_face_plan'),model_source=(data.get('model') or {}).get('source_type'))
    visual_helper().validate(visual,data['references'],context=data['context'],
        count=face_plan_count(data['context'],len(data['looks']),data.get('shot_plan')),identity=data['identity'],shot_plan=data.get('shot_plan'))
    allowed_shot=copy.deepcopy(current_shot)
    if 'arrangement' in shot['looks'][index]:
        allowed_shot['looks'][index]['arrangement']=shot['looks'][index]['arrangement']
    else:allowed_shot['looks'][index].pop('arrangement',None)
    allowed_visual=copy.deepcopy(current_visual)
    allowed_visual['shots'][index]['composition']=visual['shots'][index]['composition']
    if shot!=allowed_shot or visual!=allowed_visual:
        raise ValueError('Delivery retry changes only this rejected arrangement/composition; keep masters, framing, sources, head/gaze and other shots')
    if shot==current_shot and visual==current_visual:
        raise ValueError('Structured delivery retry requires an actual local plan change')
    compiled=visual_helper().compile_prompt(visual,number) if prompt is None else prompt
    prompt_check(compiled,data['context'],data.get('model'),shot,number,data.get('real_face_plan'),visual)
    return dict(shot_plan=shot,visual_plan=visual,prompt=compiled)


def persona_rebind_candidate(data,row,visual_plan,model):
    """Rebind a frozen persona to a revised, still unconfirmed first model; nothing else in the visual plan may change."""
    current=data.get('visual_plan')
    if (data['schema_version']!=2 or is_preview(data) or row is None or row['number']!=1
            or current is None or not current.get('persona') or not isinstance(visual_plan,dict)):
        raise ValueError('Persona rebinding applies only to the rejected first look of a structured delivery whose plan carries a persona')
    strip=lambda plan:{k:v for k,v in plan.items() if k not in ('persona','persona_model_sha256')}
    bound=visual_plan.get('persona')
    if (strip(visual_plan)!=strip(current)
            or (bound and visual_plan.get('persona_model_sha256')!=object_hash(model))
            or (not bound and ('persona' in visual_plan or 'persona_model_sha256' in visual_plan))):
        raise ValueError('Persona rebinding changes only the persona resolved against the revised model')
    visual_helper().validate(visual_plan,data['references'],context=data['context'],
        count=face_plan_count(data['context'],len(data['looks']),data.get('shot_plan')),identity=data['identity'],shot_plan=data.get('shot_plan'))
    return copy.deepcopy(visual_plan)


def preview_candidate(data, row, *, model=None, shot_plan=None, prompt=None, garment_references=None, real_face_plan=None, visual_plan=None, check_sources=True):
    shot_plan=inherit_framing_flag(shot_plan,data.get('shot_plan'))
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
            if (not isinstance(ref['path'],str) or not ref['path'].strip()
                    or not isinstance(ref['sha256'],str) or len(ref['sha256'])!=64
                    or any(c not in '0123456789abcdef' for c in ref['sha256'])):
                raise ValueError('Additional garment originals need an image path and SHA256')
            path=Path(ref['path']).resolve() if check_sources else Path(ref['path'])
            pose_helper().check_source(dict(path=str(path),role='garment-source'))
            if check_sources:
                models.validate_image(path)
                if digest(path)!=ref['sha256']:raise ValueError('Additional garment reference changed')
            if ref['sha256'] in hashes:
                raise ValueError('Additional garment reference duplicates frozen inventory')
            hashes.add(ref['sha256']);additions.append(dict(path=str(path),sha256=ref['sha256']))
            inventory.append(dict(sha256=ref['sha256'],role='garment-source'))
    planned=shot_plan if shot_plan is not None else effective_shot_plan(data)
    face_plan=copy.deepcopy(data.get('real_face_plan'))
    if face_plan is not None and v2(planned):
        face_plan=shot_helper().sync_real_face_plan(planned,face_plan)
        garments={r['sha256'] for r in inventory if r['role']=='garment-source'}
        for shot,cell in zip(shot_helper().active_looks(planned),face_plan['looks']):
            cell['reference_sha256s']=[h for h in cell['reference_sha256s'] if h not in garments]+shot['reference_sha256s']
        real_face_helper().validate(face_plan,inventory,schema_version=2,identity=data['identity'],model=changed,
            context=data['context'],count=face_plan_count(data['context'],1,planned),route=data['route'],shot_plan=planned)
    elif face_plan is not None and planned is not None:
        # Only garment selection and the declared sixth route may change here.
        # Original real coverage, identity and all other body/head/gaze values stay frozen.
        garment_hashes={r['sha256'] for r in inventory if r['role']=='garment-source'}
        usable_garments={r['sha256'] for r in planned['coverage'] if r.get('usable') is True and r.get('same_sku') is True}
        for i,shot in enumerate(planned['looks']):
            cell=face_plan['looks'][i]
            cell['reference_sha256s']=[h for h in cell['reference_sha256s'] if h not in garment_hashes or h in usable_garments]
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
        planned=shot_helper().validate(planned,inventory,context=data['context'],count=face_plan_count(data['context'],1,planned),
                                      identity=data['identity'],real_face_plan=face_plan,
                                      model_source=(changed or {}).get('source_type'))
    visual=visual_plan if visual_plan is not None else data.get('visual_plan')
    if visual is not None:
        visual=visual_helper().validate(visual,inventory,context=data['context'],count=face_plan_count(data['context'],1,planned),identity=data['identity'],shot_plan=planned)
        if prompt is None:prompt=visual_helper().compile_prompt(visual)
    if not isinstance(prompt,str) or not prompt.strip():raise ValueError('Provide a complete revised preview prompt')
    photography_helper().apply(prompt,data['context'].get('photography_targets'))
    if changed is not None:models.apply_conditions(prompt,changed,allow_child=True)
    if planned is not None:
        shot_helper().apply(prompt,planned,real_face_plan=face_plan)
        preflight_references(inventory,data['context'],planned,face_plan,1,data['identity'],data['route'])
        preflight_series(inventory,data['context'],planned,face_plan,data['identity'],data['route'])
    prompt_check(prompt,data['context'],changed,planned,1,face_plan,visual)
    result=dict(model=changed,shot_plan=planned,prompt=prompt)
    if visual is not None:result['visual_plan']=visual
    if additions:result['garment_references']=additions
    if face_plan is not None:result['real_face_plan']=face_plan
    return result


ROLE_TEXT = {
    'garment-source': 'garment source; authoritative product facts',
    'identity-reference': 'original model identity; ignore clothing, accessories, pose, backdrop and lighting',
    'aesthetic-reference': 'aesthetic only; do not copy identity or clothing',
    'pose-reference': 'body relationships only; never copy identity, body proportions, clothing, skin, line-art style or infer product/real-face evidence',
    'edit-target': 'image to correct; supplies only the explicitly retained layout, pose and scene, not an accepted identity or authoritative garment facts; correct failed traits from the original identity and garment sources',
    'identity-only': 'current outfit accepted first-image identity; never override original identity or garment sources',
}


def native_reference_check(rows, route, extra_anchor=0):
    if route=='codex_native' and len(rows)+extra_anchor>5:
        raise ValueError('Native imagegen allows at most five references; select sufficient garment views before freezing, leaving room for original identity and the current first-image anchor; never silently drop inputs')


def is_preview(data):
    return data.get('schema_version') == 2 and data.get('context', {}).get('purpose') == 'preview-grid'


def face_plan_count(context, count, shot_plan=None):
    if (context or {}).get('purpose') != 'preview-grid':return count
    return len(shot_helper().active_looks(shot_plan)) if v2(shot_plan) else 6


def context_check(context, size, shot_plan=None):
    required = {'outfit', 'style', 'mode', 'output_form', 'size', 'first_pose'}
    if not isinstance(context, dict) or set(context) - {'purpose', 'pose_description', 'photography_targets', 'canvas_policy'} != required:
        raise ValueError('Declare outfit, style, mode, output_form, size and first_pose for the frozen task context')
    if any(not isinstance(context[k], str) or not context[k].strip() for k in required - {'size','first_pose'}):
        raise ValueError('Task context labels must be nonempty')
    if context['first_pose'] == 'custom':
        if not isinstance(context.get('pose_description'), str) or not context['pose_description'].strip():
            raise ValueError('A custom single-image presentation requires the explicit user pose/framing description')
    elif type(context['first_pose']) is not int or context['first_pose'] not in range(1,10 if v2(shot_plan) else 7):
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


def presentation_check(context, refs, count, identity, model, shot_plan=None):
    if context.get('purpose') == 'preview-grid' and (count != 1 or context['first_pose'] != 1):
        raise ValueError('A preview-grid is one six-panel request with master numbering starting at 1')
    if context['first_pose'] == 'custom' and count != 1:
        raise ValueError('A custom presentation is a single-image task, not a default six-pose set')
    if count==9 and not v2(shot_plan):raise ValueError('Nine-image delivery requires a reviewed v2 shot plan')
    if any(r['role']=='pose-reference' for r in refs) and not v2(shot_plan):raise ValueError('Pose references require a v2 shot plan')
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


def create(root,refs,prompts,size,identity=True,*,schema_version=2,model=None,context=None,route=None,model_package=None,real_face_plan=None,shot_plan=None,visual_plan=None,count=None):
    root=Path(root)
    if route is None:route='chatgpt_web' if schema_version==1 else 'codex_native'
    if model_package is not None:
        if schema_version!=2 or not identity or model is not None:raise ValueError('Package use requires a new portrait task and no conflicting inline model')
        card=models.load_package(model_package);model=card['model']
        refs=list(refs)+[dict(path=str(Path(model_package)/r['file']),role='identity-reference') for r in card['references']]
        refs += [dict(path=str(Path(model_package)/r['file']), **{k:r[k] for k in ('role','sha256','scope','confirmation_note')})
                 for r in card.get('supplements', [])]
    if schema_version not in (1,2):raise ValueError('Unsupported task schema')
    if visual_plan is not None:
        if schema_version!=2:raise ValueError('Visual plans require schema 2')
        if prompts is None:
            requested=count if count is not None else (1 if (context or {}).get('purpose')=='preview-grid' else len(visual_plan.get('shots',[])))
            if type(requested) is not int or requested not in (1,6,9):raise ValueError('Compile one, six or nine visual prompts')
            prompts=[visual_helper().compile_prompt(visual_plan,None if (context or {}).get('purpose')=='preview-grid' else n) for n in range(1,requested+1)]
    if count is not None and (type(count) is not int or count not in (1,6,9) or prompts is None or count!=len(prompts)):
        raise ValueError('Declared count must match the actual prompts')
    if not isinstance(prompts,(list,tuple)):raise ValueError('Provide frozen prompts, or a visual plan for compilation')
    if len(prompts) not in (1,6,9) or not all(isinstance(p,str) and p.strip() for p in prompts):
        raise ValueError('Provide exactly one, six or nine nonempty frozen prompts')
    if not refs or len(size)!=2 or any(type(v)!=int or v<=0 for v in size):
        raise ValueError('Real garment references and positive exact dimensions required')
    if route not in ('chatgpt_web','codex_native'):raise ValueError('Unsupported native route')
    if schema_version==1:
        if len(prompts) not in (1,6):raise ValueError('Legacy tasks retain one or six images')
        if model is not None or context is not None or route!='chatgpt_web':raise ValueError('Legacy task interface is unchanged')
        items=[dict(path=p,role='garment-source') for p in refs]
    else:
        # WP-10a: a newly created garment-driven (v2) task gets the breathing-room flag by default. Only create() adds it;
        # frozen tasks keep their stored bytes, and later calls that omit the flag inherit it (inherit_framing_flag).
        if v2(shot_plan) and 'framing_guidance' not in shot_plan:shot_plan=dict(shot_plan,framing_guidance=1)
        context=context_check(context,size,shot_plan)
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
            elif item.get('role')=='pose-reference':
                if set(item)-{'sha256'}!={'path','role','pose_source'}:raise ValueError('Pose reference needs a path and reviewed source')
                pose_helper().check_source(item)
            elif set(item)!={'path','role'} or item['role'] not in ('garment-source','identity-reference','aesthetic-reference','edit-target'):
                raise ValueError('Declare an explicit reference role')
        for item in items:pose_helper().check_source(item)
        if not any(x['role']=='garment-source' for x in items):raise ValueError('A model/photo/card is not a garment source')
        has_identity=any(x['role']=='identity-reference' for x in items)
        if any(x['role']=='model-supplement' for x in items) and not has_identity:
            raise ValueError('An accepted supplement requires the original identity reference')
        if not identity and any(x['role']!='garment-source' for x in items):raise ValueError('Non-portrait task cannot carry person references')
        if identity and (has_identity != (model['source_type'] in ('ai','real'))):raise ValueError('Existing models need original identity references; new models do not copy identity')
        presentation_check(context, items, len(prompts), identity, model, shot_plan)
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
    inventory=[dict(sha256=digest(p),role=item['role'],**({'pose_source':copy.deepcopy(item['pose_source'])} if 'pose_source' in item else {})) for p,item in zip(sources,items)]
    for item,row in zip(items,inventory):
        if 'sha256' in item and item['sha256']!=row['sha256']:raise ValueError('Reference hash changed before import')
    if v2(shot_plan) and real_face_plan is not None:
        real_face_plan=shot_helper().sync_real_face_plan(shot_plan,real_face_plan)
    if visual_plan is not None:
        visual_plan=visual_helper().validate(visual_plan,inventory,context=context,
            count=face_plan_count(context,len(prompts),shot_plan),identity=identity,shot_plan=shot_plan)
    if schema_version==2 and context.get('purpose')=='preview-grid' and identity and model['source_type']=='real' and real_face_plan is None:
        raise ValueError('A real-person preview requires six declared cell plans and original view coverage')
    if real_face_plan is not None:
        plan_count=face_plan_count(context,len(prompts),shot_plan)
        real_face_plan=real_face_helper().validate(real_face_plan,inventory,schema_version=schema_version,identity=identity,
            model=model,context=context,count=plan_count,route=route,strict_looks=range(1,plan_count+1),shot_plan=shot_plan)
        if context.get('purpose')=='preview-grid':
            native_reference_check(selected_references(inventory,context,shot_plan,real_face_plan,1),route)
    elif shot_plan is None:
        native_reference_check(items,route,extra_anchor=int(identity and len(prompts)==6))
    if shot_plan is not None:
        if schema_version!=2:raise ValueError('Shot plans require schema 2')
        shot_plan=shot_helper().validate(shot_plan,inventory,context=context,
            count=face_plan_count(context,len(prompts),shot_plan),identity=identity,real_face_plan=real_face_plan,
            model_source=(model or {}).get('source_type'))
        preflight_references(inventory,context,shot_plan,real_face_plan,len(prompts),identity,route)
        preflight_series(inventory,context,shot_plan,real_face_plan,identity,route)
    if schema_version==2:
        for number,prompt in enumerate(prompts,1):prompt_check(prompt,context,model,shot_plan,number,real_face_plan,visual_plan)
    root.mkdir(parents=True,exist_ok=False)
    try:
        (root/'references').mkdir();frozen=[]
        for i,(p,item) in enumerate(zip(sources,items),1):
            out=root/'references'/f'{i:02d}{p.suffix.lower()}';shutil.copyfile(p,out)
            models.validate_image(out)
            frozen.append({'file':str(out.relative_to(root)),'sha256':digest(out),'role':item['role']})
            if 'pose_source' in item:frozen[-1]['pose_source']=copy.deepcopy(item['pose_source'])
            if item['role']=='model-supplement':
                if frozen[-1]['sha256']!=item['sha256']:raise ValueError('Accepted supplement changed during snapshot')
                frozen[-1].update(scope=item['scope'],confirmation_note=item['confirmation_note'])
        data={'schema_version':schema_version,'created_at':stamp(),'route':route,'mode':'manual','model_verified':False,
              'size':list(size),'identity':bool(identity),'references':frozen,'authorization':None,'attempts':0,
              'complete':False,'delivery_status':'prepared','events':[],
              'looks':[{'number':i,'prompt':p,'prompt_sha256':hashlib.sha256(p.encode()).hexdigest(),'state':'pending'} for i,p in enumerate(prompts,1)]}
        if schema_version==2:
            data.update(context=context,context_sha256=object_hash(context),model=model,model_sha256=object_hash(model),model_confirmation=None,
                        references_sha256=object_hash(frozen),failure_recovery_version=1,prompt_contract_version=1)
        if real_face_plan is not None:
            real_face_plan=real_face_helper().validate(real_face_plan,frozen,schema_version=schema_version,identity=identity,
                model=model,context=context,count=plan_count,route=route,strict_looks=range(1,plan_count+1),shot_plan=shot_plan)
            data.update(real_face_plan=real_face_plan,real_face_plan_sha256=object_hash(real_face_plan))
        if shot_plan is not None:
            data.update(shot_plan=shot_plan,shot_plan_sha256=object_hash(shot_plan),plan_version=0)
        if visual_plan is not None:
            data.update(visual_plan=visual_plan,visual_plan_sha256=object_hash(visual_plan),plan_version=0,prompt_contract_version=2)
        if schema_version==2 and v2(shot_plan) and identity:
            data['identity_instruction_version']=1
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
    rows=selected_references(data['references'],data.get('context',{}),data.get('shot_plan'),data.get('real_face_plan'),look)
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
        identity=data['identity'],model=data['model'],context=data['context'],count=face_plan_count(data['context'],len(data['looks']),data.get('shot_plan')),route=data['route'],shot_plan=data.get('shot_plan'))
    history=data.get('real_face_plan_history',[])
    if (not isinstance(history,list) or len(history)>1
            or (bool(data.get('continuation_authorization')) and len(history)!=1)):
        raise ValueError('Invalid real face plan extension history')
    for prior in history:
        if (not isinstance(prior,dict) or set(prior)!={'plan','sha256','note','at'}
                or not real_face_helper().text(prior['note']) or not real_face_helper().text(prior['at'])
                or object_hash(prior['plan'])!=prior['sha256']
                or len(data['looks']) not in (6,9) or not data.get('continuation_authorization')):
            raise ValueError('Frozen real face plan history changed')
        real_face_helper().validate(prior['plan'],data['references'],schema_version=2,identity=data['identity'],
            model=data['model'],context=data['context'],count=1,route=data['route'],
            shot_plan=shot_helper().subset(data['shot_plan'],1,series_role='series-first') if v2(data.get('shot_plan')) else None)
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
    pose_helper().check_inventory(data['references'])
    supplements=[r for r in data['references'] if r['role']=='model-supplement']
    poses=[r for r in data['references'] if r['role']=='pose-reference']
    if (supplements or poses or v2(data.get('shot_plan'))) and 'references_sha256' not in data:
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


def effective_shot_plan(data):
    edits=data['looks'][0].get('local_edits',[]) if is_preview(data) else []
    return edits[-1]['shot_plan'] if edits else data.get('shot_plan')


def composite_pixels(base_path,donor_path,rectangle):
    from PIL import Image
    size=png_size(base_path)
    if png_size(donor_path)!=size:raise ValueError('Local preview donor must have the original canvas; no resizing')
    if (not isinstance(rectangle,list) or len(rectangle)!=4 or any(type(v) is not int for v in rectangle)
            or not 0<=rectangle[0]<rectangle[2]<=size[0] or not 0<=rectangle[1]<rectangle[3]<=size[1]):
        raise ValueError('Declare one nonempty integer rectangle inside the original preview')
    with Image.open(base_path) as source,Image.open(donor_path) as donor:
        if source.mode not in ('RGB','RGBA'):raise ValueError('Local preview composition requires RGB/RGBA originals')
        result=source.copy();result.paste(donor.convert(source.mode).crop(rectangle),rectangle[:2])
        return result


def check_local_edits(root,data,row):
    if 'local_edits' not in row:return
    edits=row['local_edits']
    if not is_preview(data) or not isinstance(edits,list) or not edits:
        raise ValueError('Local image revisions belong to an existing preview only')
    previous=None
    for edit in edits:
        if (set(edit)!={'base_output','donor','output','rectangle','shot_plan','prior_review','note','at','generation_calls','sha256'}
                or object_hash({k:v for k,v in edit.items() if k!='sha256'})!=edit['sha256']
                or type(edit['generation_calls']) is not int or edit['generation_calls']!=0
                or not edit['note'].strip() or not edit['at'].strip()
                or (previous is not None and edit['base_output']!=previous)):
            raise ValueError('Local preview revision changed or broke its original-image chain')
        for key in ('base_output','donor','output'):
            artifact=edit[key];file=safe_file(root,artifact['file'])
            if digest(file)!=artifact['sha256'] or png_size(file)!=artifact['dimensions']:
                raise ValueError('Frozen local preview source or result changed')
        review=edit['prior_review']
        if review.get('state') not in ('accepted','rejected') or review.get('qa') not in ('qa-pass','qa-user-review','qa-retry') or not review.get('qa_note','').strip():
            raise ValueError('Local preview correction must preserve its prior visual review')
        planned=edit['shot_plan']
        if planned is not None:
            shot_helper().validate(planned,data['references'],context=data['context'],count=face_plan_count(data['context'],1,planned),
                identity=data['identity'],real_face_plan=row.get('real_face_plan',data.get('real_face_plan')),
                model_source=(row.get('model',data['model']) or {}).get('source_type'))
        expected=composite_pixels(safe_file(root,edit['base_output']['file']),safe_file(root,edit['donor']['file']),edit['rectangle'])
        from PIL import Image
        with Image.open(safe_file(root,edit['output']['file'])) as actual:
            if actual.mode!=expected.mode or actual.tobytes()!=expected.tobytes():
                raise ValueError('Local preview result changed protected pixels or does not match its donor rectangle')
        previous=edit['output']
    if row.get('output')!=previous:raise ValueError('Current preview does not bind its latest local correction')


def compose_preview(root,data,row,**kw):
    root=Path(root).resolve()
    note=kw.get('note','').strip()
    if (data['schema_version']!=2 or not is_preview(data) or row is None or row['number']!=1
            or row['state'] not in ('accepted','rejected') or data.get('preview_revision') or not note
            or kw.get('expected_output_sha256')!=row['output']['sha256']):
        raise ValueError('Compose only an exact reviewed, open preview with explicit local-edit scope')
    donor=Path(kw['file']);donor_hash=digest(donor)
    if donor_hash!=kw.get('expected_donor_sha256'):raise ValueError('Local preview donor changed')
    planned=copy.deepcopy(inherit_framing_flag(kw.get('shot_plan',effective_shot_plan(data)),effective_shot_plan(data)))
    if planned is None and effective_shot_plan(data) is not None:
        raise ValueError('Local composition cannot discard the current reviewed shot plan')
    if planned is not None:
        shot_helper().validate(planned,data['references'],context=data['context'],count=face_plan_count(data['context'],1,planned),
            identity=data['identity'],real_face_plan=data.get('real_face_plan'),model_source=(data['model'] or {}).get('source_type'))
        original=effective_shot_plan(data)
        if original and any(planned[k]!=original[k] for k in ('version','sku','route','coverage')):
            raise ValueError('Local composition retains the same SKU and original garment coverage')
        preflight_references(data['references'],data['context'],planned,data.get('real_face_plan'),1,data['identity'],data['route'])
        preflight_series(data['references'],data['context'],planned,data.get('real_face_plan'),data['identity'],data['route'])
    result=composite_pixels(safe_file(root,row['output']['file']),donor,kw.get('rectangle'))
    sequence=len(row.get('local_edits',[]))+1
    name=f"look-1-attempt-{row.get('attempt_number',1)}-local-{sequence}"
    source=safe_file(root,'local-edits/'+name+'-donor.png');out=safe_file(root,'outputs/'+name+'.png')
    source.parent.mkdir(exist_ok=True);out.parent.mkdir(exist_ok=True)
    # Exclusive files preserve the actual provider result, every donor and each local revision.
    with source.open('xb') as f:f.write(donor.read_bytes())
    if digest(source)!=donor_hash:raise ValueError('Local preview donor changed while retaining it')
    with out.open('xb') as f:result.save(f,format='PNG',icc_profile=result.info.get('icc_profile'))
    artifact=dict(file=str(out.relative_to(root)),sha256=digest(out),dimensions=png_size(out))
    edit=dict(base_output=copy.deepcopy(row['output']),
        donor=dict(file=str(source.relative_to(root)),sha256=donor_hash,dimensions=png_size(source)),
        output=artifact,rectangle=kw['rectangle'],shot_plan=planned,
        prior_review={k:copy.deepcopy(row[k]) for k in ('state','qa','qa_note','qa_history') if k in row},
        note=note,at=stamp(),generation_calls=0)
    edit['sha256']=object_hash(edit)
    row.setdefault('local_edits',[]).append(edit)
    row.update(state='returned',output=artifact)
    for key in ('qa','qa_note','qa_history'):row.pop(key,None)
    check_local_edits(root,data,row)


def check_evidence(root,data):
    prompt_contract(data)
    check_shot_plan(data)
    check_visual_plan(data)
    check_preview_origin(root,data)
    check_model_confirmation(data)
    check_reference_metadata(root,data)
    if data['schema_version']==2:
        if object_hash(data['context'])!=data['context_sha256'] or object_hash(data['model'])!=data['model_sha256']:
            raise ValueError('Frozen context/model changed')
        context_check(data['context'],data['size'],data.get('shot_plan'))
        if data['identity']:models.validate_model(data['model'],allow_child=True)
        presentation_check(data['context'], data['references'], len(data['looks']), data['identity'], data['model'],data.get('shot_plan'))
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
        checked=preview_candidate(data,row,check_sources=False,**candidate['candidate'])
        if checked!=candidate['candidate']:raise ValueError('Invalid preview candidate')
    for row in evidence_rows(data):
        if 'web_execution' in row:
            web_execution_helper().check_retained(root,row)
        check_local_edits(root,data,row)
        if hashlib.sha256(row['prompt'].encode()).hexdigest()!=row['prompt_sha256']:
            raise ValueError('Frozen prompt changed')
        photography_helper().apply(row['prompt'], data['context'].get('photography_targets') if data['schema_version']==2 else None)
        contract=prompt_contract(data,row)
        if row in data['looks'] and 'visual_plan' in data and contract!=2:
            raise ValueError('Current visual-plan prompts cannot downgrade their contract')
        if contract>=1 and data['schema_version']==2 and data['identity']:
            models.apply_conditions(row['prompt'],row.get('model',data['model']),allow_child=True)
        if row in data['looks'] and 'shot_plan' in data:
            shot_helper().apply(row['prompt'],data['shot_plan'],None if is_preview(data) else row['number'],data.get('real_face_plan'),strict=contract>=1)
        if contract==2:
            visual=row.get('visual_plan',data.get('visual_plan'))
            if visual is None:raise ValueError('Historical contract 2 requires its visual plan')
            prompt_check(row['prompt'],data['context'],row.get('model',data['model']),
                row.get('shot_plan',data.get('shot_plan')),row['number'],
                row.get('real_face_plan',data.get('real_face_plan')),visual)
        history=row.get('prompt_history',[])
        revision=row.get('plan_revision',0)
        if type(revision) is not int or revision<0 or not isinstance(history,list) or len(history)!=revision:
            raise ValueError('Invalid pending-prompt revision history')
        for i,prior in enumerate(history):
            if (prior.get('revision')!=i or not prior.get('note','').strip()
                    or hashlib.sha256(prior['prompt'].encode()).hexdigest()!=prior['prompt_sha256']):
                raise ValueError('Historical prompt revision changed')
            photography_helper().apply(prior['prompt'], data['context'].get('photography_targets') if data['schema_version']==2 else None)
            if prompt_contract(data,prior)>=1 and data['schema_version']==2 and data['identity']:
                models.apply_conditions(prior['prompt'],row.get('model',data['model']),allow_child=True)
            if prompt_contract(data,prior)==2:
                prompt_check(prior['prompt'],data['context'],row.get('model',data['model']),
                    row.get('shot_plan',data.get('shot_plan')),row['number'],
                    row.get('real_face_plan',data.get('real_face_plan')),row.get('visual_plan',data.get('visual_plan')))
        if 'real_face_plan' in row and object_hash(row['real_face_plan'])!=row.get('real_face_plan_sha256'):
            raise ValueError('Historical real face plan changed')
        if 'shot_plan' in row and object_hash(row['shot_plan'])!=row.get('shot_plan_sha256'):
            raise ValueError('Historical shot plan changed')
        if 'visual_plan' in row and object_hash(row['visual_plan'])!=row.get('visual_plan_sha256'):
            raise ValueError('Historical visual plan changed')
        if 'visual_plan' in row:
            if contract!=2:raise ValueError('Historical visual plan requires its original contract 2')
            visual_helper().validate(row['visual_plan'],data['references'],context=data['context'],
                count=len(row['visual_plan']['shots']),identity=data['identity'],shot_plan=row.get('shot_plan'))
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


def continue_v2(data,kw):
    """Continue a declared series-first trial; never expand an arbitrary single."""
    prior=data['shot_plan'];note=kw.get('note','').strip();approval=kw.get('approval_id','').strip()
    if (prior['series_role']!='series-first' or len(data['looks'])!=1
            or data['looks'][0]['state']!='accepted' or not data['authorization']
            or data['context'].get('purpose','delivery')!='delivery'):
        raise ValueError('Continue only an accepted explicitly declared series-first trial')
    if data['identity'] and not data['model_confirmation']:raise ValueError('Confirm the actual first-image model before continuation')
    if kw.get('context')!=data['context'] or not note or not approval:
        raise ValueError('Continuation retains context and requires explicit remaining-image approval')
    if data.get('continuation_authorization') or any(g['approval_id']==approval for g in data.get('retry_authorizations',[])):
        raise ValueError('Continuation approval already used')
    full=copy.deepcopy(prior);full['selected_shot_ids']=[s['shot_id'] for s in full['looks']];full['series_role']='series'
    if kw.get('shot_plan') is not None and inherit_framing_flag(kw['shot_plan'],prior)!=full:
        raise ValueError('Continue the complete frozen series without re-planning its shots')
    count=len(full['looks']);face=copy.deepcopy(data.get('real_face_plan'))
    if face is not None:
        extra=kw.get('real_face_looks')
        if not isinstance(extra,list) or len(extra)!=count-1:raise ValueError('Declare every remaining real-face look')
        face['looks'].extend(copy.deepcopy(extra));face=shot_helper().sync_real_face_plan(full,face)
        real_face_helper().validate(face,data['references'],schema_version=2,identity=data['identity'],model=data['model'],
            context=data['context'],count=count,route=data['route'],strict_looks=range(2,count+1),shot_plan=full)
    elif kw.get('real_face_looks') is not None:raise ValueError('Cannot retrofit real identity coverage during continuation')
    shot_helper().validate(full,data['references'],context=data['context'],count=count,identity=data['identity'],
        real_face_plan=face,model_source=data['model']['source_type'])
    visual=None;prompts=kw.get('prompts')
    if 'visual_plan' in data:
        visual=visual_helper().validate(kw.get('visual_plan'),data['references'],context=data['context'],count=count,
            identity=data['identity'],shot_plan=full)
        old=data['visual_plan']
        if any(visual[k]!=old[k] for k in old if k!='shots') or visual['shots'][0]!=old['shots'][0]:
            raise ValueError('Continuation keeps shared photography and the accepted first shot')
        if prompts is None:prompts=[visual_helper().compile_prompt(visual,n) for n in range(2,count+1)]
    elif kw.get('visual_plan') is not None:raise ValueError('Do not retrofit a visual plan onto the accepted first image')
    if not isinstance(prompts,list) or len(prompts)!=count-1 or any(not isinstance(p,str) or not p.strip() for p in prompts):
        raise ValueError('Provide exactly the remaining series prompts')
    preflight_references(data['references'],data['context'],full,face,count,data['identity'],data['route'])
    for number,prompt in enumerate(prompts,2):prompt_check(prompt,data['context'],data['model'],full,number,face,visual)
    data.setdefault('shot_plan_history',[]).append(dict(plan=copy.deepcopy(prior),sha256=object_hash(prior),note=note))
    data.update(shot_plan=full,shot_plan_sha256=object_hash(full),plan_version=data.get('plan_version',0)+1)
    if face is not None:
        data['real_face_plan_history']=[dict(plan=copy.deepcopy(data['real_face_plan']),sha256=data['real_face_plan_sha256'],note=note,at=stamp())]
        data.update(real_face_plan=face,real_face_plan_sha256=object_hash(face))
    if visual is not None:
        data.setdefault('visual_plan_history',[]).append(dict(plan=copy.deepcopy(data['visual_plan']),sha256=data['visual_plan_sha256'],note=note))
        data.update(visual_plan=visual,visual_plan_sha256=object_hash(visual))
    data['continuation_authorization']=dict(approval_id=approval,additional_requests=count-1,note=note,at=stamp())
    data['looks'].extend(dict(number=n,prompt=p,prompt_sha256=hashlib.sha256(p.encode()).hexdigest(),state='pending') for n,p in enumerate(prompts,2))


def update(root,event,**kw):
    root=Path(root)
    if event!='reserve' and any(kw.get(k) is not None for k in ('execution_manifest','expected_submission_sha256')):
        raise ValueError('Web execution binding is only accepted with reserve')
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
            candidate=preview_candidate(d,row,model=kw.get('model'),shot_plan=kw.get('shot_plan'),prompt=kw.get('prompt'),garment_references=kw.get('garment_references'),visual_plan=kw.get('visual_plan'))
            if d.get('preview_revision'):d.setdefault('preview_revision_history',[]).append(d['preview_revision'])
            d['preview_revision']=dict(candidate=candidate,candidate_sha256=object_hash(candidate),
                base_plan_sha256=plan_fingerprint(d),output_sha256=row['output']['sha256'],note=note,at=stamp())
        elif event=='cancel-preview-revision':
            proposal=d.get('preview_revision');note=kw.get('note','').strip()
            if (not is_preview(d) or n!=1 or not proposal or row['state'] not in ('accepted','rejected')
                    or not note or kw.get('expected_candidate_sha256')!=proposal['candidate_sha256']
                    or kw.get('expected_output_sha256')!=proposal['output_sha256']):
                raise ValueError('Cancel the exact current preview candidate/output with an actual withdrawal note')
            d.setdefault('preview_revision_history',[]).append(dict(copy.deepcopy(proposal),
                disposition='cancelled',disposition_note=note,disposition_at=stamp()))
            d.pop('preview_revision')
        elif event=='compose-preview':
            compose_preview(root,d,row,**kw)
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
        elif event=='continue-authorize' and v2(d.get('shot_plan')):
            continue_v2(d,kw)
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
            continuation_visual=None
            if 'visual_plan' in d:
                continuation_visual=visual_helper().validate(kw.get('visual_plan'),d['references'],
                    context=d['context'],count=6,identity=d['identity'])
                prior=d['visual_plan']
                if (any(continuation_visual[k]!=prior[k] for k in prior if k!='shots')
                        or continuation_visual['shots'][0]!=prior['shots'][0]):
                    raise ValueError('Continuation cannot replace approved shared visual decisions or first shot')
                if prompts is None:
                    prompts=[visual_helper().compile_prompt(continuation_visual,i) for i in range(2,7)]
            elif kw.get('visual_plan') is not None:
                raise ValueError('A continuation cannot retrofit a visual plan onto an approved legacy first image')
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
                    identity=d['identity'],real_face_plan=continuation_plan,
                    model_source=(d.get('model') or {}).get('source_type'))
                prior=d['shot_plan']
                if (any(full[k]!=prior[k] for k in ('sku','coverage','route','preservation','adaptation_note')) or full['looks'][0]!=prior['looks'][0]
                        or full.get('framing_guidance')!=prior.get('framing_guidance')):
                    raise ValueError('Continuation cannot replace the approved first shot, original garment coverage or framing guidance')
                for i,prompt in enumerate(prompts,2):
                    prompt_check(prompt,d['context'],d['model'],full,i,continuation_plan)
                    chosen=shot_helper().selected(full,i)
                    actual=[r for r in d['references'] if r['role']!='garment-source' or r['sha256'] in chosen]
                    if continuation_plan is not None:
                        actual=[r for r in d['references'] if r['sha256'] in continuation_plan['looks'][i-1]['reference_sha256s']]
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
            if continuation_visual is not None:
                prior=d['visual_plan']
                d['visual_plan_history']=[dict(plan=copy.deepcopy(prior),sha256=object_hash(prior),note=note)]
                d.update(visual_plan=continuation_visual,visual_plan_sha256=object_hash(continuation_visual))
                if 'shot_plan' not in d:d['plan_version']=d.get('plan_version',0)+1
            for i,prompt in enumerate(prompts,2):prompt_check(prompt,d['context'],d['model'],d.get('shot_plan'),i,continuation_plan,d.get('visual_plan'))
            adopt_prompt_contract(d)
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
            prompt_check(prompt,d['context'],d['model'],d.get('shot_plan'),n,d.get('real_face_plan'),d.get('visual_plan'))
            adopt_prompt_contract(d)
            revision=row.get('plan_revision',0)
            row.setdefault('prompt_history',[]).append(dict(prompt=row['prompt'],
                prompt_sha256=row['prompt_sha256'],revision=revision,note=note,at=stamp(),
                prompt_contract_version=prompt_contract(d,row)))
            row.update(prompt=prompt,prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),plan_revision=revision+1,prompt_contract_version=prompt_contract(d))
        elif event=='retry-authorize':
            if is_preview(d) and len(d.get('retry_authorizations',[]))>=3:
                raise ValueError('Preview correction limit reached: three additional requests maximum')
            # One explicit grant replaces one rejected/reconciled failed attempt, never resets the task.
            proposal=d.get('preview_revision') if is_preview(d) else None
            delivery_revision=None;persona_rebind=None
            if (not is_preview(d) and kw.get('model') is not None and kw.get('visual_plan') is not None and kw.get('shot_plan') is None
                    and n==1 and (d.get('visual_plan') or {}).get('persona')):
                persona_rebind=persona_rebind_candidate(d,row,kw['visual_plan'],models.validate_model(kw['model'],allow_child=True))
            elif not is_preview(d) and (kw.get('shot_plan') is not None or kw.get('visual_plan') is not None):
                delivery_revision=delivery_retry_candidate(d,row,shot_plan=kw.get('shot_plan'),
                    visual_plan=kw.get('visual_plan'),prompt=kw.get('prompt'))
            if is_preview(d) and not proposal and effective_shot_plan(d)!=d.get('shot_plan'):
                raise ValueError('Retain the locally corrected shot plan through a reviewed preview revision before retry')
            note=kw.get('note','').strip();approval=kw.get('approval_id','').strip()
            if delivery_revision:prompt=delivery_revision['prompt']
            elif persona_rebind is not None:prompt=kw.get('prompt') or visual_helper().compile_prompt(persona_rebind,1)
            else:prompt=kw.get('prompt',proposal['candidate']['prompt'] if proposal else '')
            if proposal:
                if kw.get('shot_plan') is not None:kw['shot_plan']=inherit_framing_flag(kw['shot_plan'],proposal['candidate'].get('shot_plan'))
                for key in ('model','shot_plan','visual_plan','prompt','garment_references'):
                    if key in kw and kw[key]!=proposal['candidate'].get(key):
                        raise ValueError('Retry must use the reviewed preview revision candidate')
            grants=d.get('retry_authorizations',[])
            failed_ready=(row is not None and row['state']=='failed' and failure_recovery(d) and row.get('failure_reconciliation'))
            if row is None or (row['state']!='rejected' and not failed_ready and not (proposal and row['state']=='accepted')) or not d['authorization']:
                raise ValueError('Retry only a visually rejected result or a reconciled failure with retained evidence; recover unknown requests first; got '
                                 +('no --look' if row is None else 'look '+str(n)+' state '+repr(row['state']))
                                 +('' if d['authorization'] else ', task has no authorize record'))
            attempt=row.get('attempt_number',1)
            if type(kw.get('expected_attempt'))!=int or kw['expected_attempt']!=attempt:
                raise ValueError('Approval must target the current rejected/failed attempt: pass --expected-attempt '+str(attempt)+'; got '+repr(kw.get('expected_attempt')))
            if not note or not approval or not isinstance(prompt,str) or not prompt.strip():
                missing=[];via_revise=is_preview(d) and row['state'] in ('accepted','rejected')
                if not note:missing.append('--note "<the user\'s own words granting this one extra request>"')
                if not approval:missing.append('--approval-id <a new ID you choose, unique within this task, e.g. retry-look'+str(n)+'-attempt'+str(attempt+1)+'>')
                if not isinstance(prompt,str) or not prompt.strip():
                    missing.append('a corrected prompt: first run revise-preview --task <task> --look '+str(n)
                        +' --expected-output-sha256 '+row.get('output',{}).get('sha256','<current output sha256>')
                        +' --spec revision.json --note "<user feedback>" (revision.json holds the complete new "prompt"), then repeat this command'
                        if via_revise else '--prompt-file <file holding the complete corrected prompt>')
                raise ValueError('Explicit retry approval, unique approval ID and corrected prompt required; missing: '+'; '.join(missing)
                    +'. Full form: retry-authorize --task <task> --look '+str(n)+' --expected-attempt '+str(attempt)
                    +' --approval-id <unique ID> --note "<user words>"'+('' if via_revise else ' --prompt-file <file>'))
            photography_helper().apply(prompt,d['context'].get('photography_targets') if d['schema_version']==2 else None)
            if any(g['approval_id']==approval for g in grants) or d.get('continuation_authorization',{}).get('approval_id')==approval:raise ValueError('Retry approval already used')
            if (d['schema_version']==1 or n==1) and any(x['state']!='pending' for x in d['looks'][n:]):raise ValueError('Cannot replace an anchor with existing downstream work')
            if d['schema_version']==2:adopt_prompt_contract(d)
            history=copy.deepcopy(row.get('history',[]));old=copy.deepcopy(row);old.pop('history',None)
            if d['schema_version']==2:old['prompt_contract_version']=prompt_contract(d,row)
            if d['schema_version']==2 and d['model']:
                old.update(model=copy.deepcopy(d['model']),model_sha256=d['model_sha256'])
            if 'shot_plan' in d:
                old.update(shot_plan=copy.deepcopy(d['shot_plan']),shot_plan_sha256=d['shot_plan_sha256'])
            if 'visual_plan' in d:
                old.update(visual_plan=copy.deepcopy(d['visual_plan']),visual_plan_sha256=d['visual_plan_sha256'])
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
                if 'visual_plan' in candidate:
                    d.update(visual_plan=copy.deepcopy(candidate['visual_plan']),visual_plan_sha256=object_hash(candidate['visual_plan']),prompt_contract_version=2)
                if 'real_face_plan' in candidate:
                    old.update(real_face_plan=copy.deepcopy(d['real_face_plan']),real_face_plan_sha256=d['real_face_plan_sha256'])
                    d.update(real_face_plan=copy.deepcopy(candidate['real_face_plan']),real_face_plan_sha256=object_hash(candidate['real_face_plan']))
                old['preview_revision']=copy.deepcopy(proposal)
                d.pop('preview_revision')
            elif delivery_revision:
                if 'real_face_plan' in delivery_revision:
                    old.update(real_face_plan=copy.deepcopy(d['real_face_plan']),real_face_plan_sha256=d['real_face_plan_sha256'])
                    d.update(real_face_plan=copy.deepcopy(delivery_revision['real_face_plan']),real_face_plan_sha256=object_hash(delivery_revision['real_face_plan']))
                for field in ('shot_plan','visual_plan'):
                    previous=d[field];changed=delivery_revision[field]
                    if changed!=previous:
                        d.setdefault(field+'_history',[]).append(dict(plan=copy.deepcopy(previous),sha256=object_hash(previous),note=note))
                        d.update({field:copy.deepcopy(changed),field+'_sha256':object_hash(changed)})
                d['plan_version']=d.get('plan_version',0)+1
            elif persona_rebind is not None:
                previous=d['visual_plan']
                d.setdefault('visual_plan_history',[]).append(dict(plan=copy.deepcopy(previous),sha256=object_hash(previous),note=note))
                d.update(visual_plan=persona_rebind,visual_plan_sha256=object_hash(persona_rebind),plan_version=d.get('plan_version',0)+1)
                # Looks 2..n are unsubmitted drafts (the anchor guard above rejects downstream work); swap their frozen visual block in place.
                for other in d['looks'][1:]:
                    stale=visual_helper().render(previous,other['number']);fresh=visual_helper().render(persona_rebind,other['number'])
                    if stale==fresh:continue
                    if other['state']!='pending' or other['prompt'].count(stale)!=1:
                        raise ValueError('Pending downstream prompts must carry exactly one frozen visual block to rebind the persona')
                    other['prompt']=other['prompt'].replace(stale,fresh,1);other['prompt_sha256']=hashlib.sha256(other['prompt'].encode()).hexdigest()
            elif kw.get('shot_plan') is not None or kw.get('visual_plan') is not None:
                raise ValueError('Change shot/visual plans through a reviewed preview revision')
            if kw.get('model') is not None and not proposal:
                if d['schema_version']!=2 or n!=1 or not row.get('model_rejected') or d['model_confirmation']:raise ValueError('Model revision requires explicit unconfirmed-first-model rejection')
                changed=models.validate_model(kw['model'],allow_child=True)
                if any(changed[k]!=d['model'][k] for k in ('source_type','scope','subject')):raise ValueError('A different identity/source/scope requires a new declared model version, not replacement of original references')
                d.update(model=changed,model_sha256=object_hash(changed))
            if d['schema_version']==2 and n==1 and d['model_confirmation']:
                old['model_confirmation']=copy.deepcopy(d['model_confirmation'])
                d['model_confirmation']=None
            if d['schema_version']==2:prompt_check(prompt,d['context'],d['model'],d.get('shot_plan'),n,d.get('real_face_plan'),d.get('visual_plan'))
            history.append(old)
            grant={'approval_id':approval,'look':n,'rejected_attempt':attempt,'additional_requests':1,'note':note,'at':stamp(),'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest()}
            if failed_ready:
                grant.pop('rejected_attempt')
                grant.update(source_state='failed',failed_attempt=attempt)
            row.clear();row.update(number=n,state='pending',attempt_number=attempt+1,prompt=prompt,prompt_sha256=grant['prompt_sha256'],history=history,
                **({'prompt_contract_version':prompt_contract(d)} if d['schema_version']==2 else {}))
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
            execution=None
            if kw.get('execution_manifest') is not None:
                selected=references(root,d,n);canonical=handoff_prompt(d,row,selected)
                execution=web_execution_helper().validate_current(root,d,row,handoff_directory(root,d,row),
                    selected,canonical,handoff_manifest(d,row,selected,canonical),
                    kw['execution_manifest'],kw.get('expected_submission_sha256'))
            elif kw.get('expected_submission_sha256') is not None:
                raise ValueError('Expected submission hash requires the web execution manifest')
            elif d['route']=='chatgpt_web' and (handoff_directory(root,d,row)/web_execution_helper().folder_name(d)).exists():
                raise ValueError('Prepared web execution requires its manifest and submission hash binding')
            row.update(state='reserved',conversation=url,tab=kw.get('tab'),submitted_at=stamp(),reference_hashes=expected)
            if execution is not None:row['web_execution']=execution
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


def handoff_directory(root,data,row):
    suffix=f"-attempt-{row['attempt_number']}" if row.get('attempt_number',1)>1 else ''
    if row.get('plan_revision',0):suffix+=f"-plan-{row['plan_revision']}"
    if 'plan_version' in data:suffix+=f"-v{data['plan_version']}"
    return Path(root)/'handoff'/f"look-{row['number']}{suffix}"


def handoff_prompt(d,row,refs):
    """Render the existing canonical request; execution policy lives separately."""
    n=row['number'];instruction=[]
    for i,r in enumerate(refs,1):
        instruction.append(f'Image {i}: '+(models.supplement_prompt(r) if r['role']=='model-supplement' else ROLE_TEXT[r['role']]))
    if d['schema_version']==2 and d['model'] and prompt_contract(d,row)==0:
        instruction.extend(models.prompt_lines(d['model'],allow_child=True))
    if d['schema_version']==2 and d['context']['first_pose']=='custom':
        instruction.append('Explicit user presentation: '+d['context']['pose_description']+
                           ' This overrides conflicting default pose/framing, not garment facts or original model conditions.')
    if d['schema_version']==2 and d['context'].get('purpose')=='correction-edit':
        instruction.append('Operation: correct the declared edit target using the original person and garment sources; '
                           'retain only the requested picture elements. Native editing is soft conditioning, not pixel protection or guaranteed facial fidelity.')
    form=('One '+('nine-panel 3x3' if v2(d.get('shot_plan')) and face_plan_count(d['context'],1,d['shot_plan'])==9 else 'six-panel')+' direction preview, not standalone delivery. Include the small single-line label '
          '方向预览·非成片 / PREVIEW ONLY — NOT FINAL.' if is_preview(d) else 'One standalone image.')
    prompt='Only use built-in image generation, no other plugins. '+form+'\n'+'\n'.join(instruction)+'\n'+canvas_instruction(d)+'\n'+row['prompt']
    if 'real_face_plan' in d:
        cells=enumerate(d['real_face_plan']['looks'],1) if is_preview(d) else [(n,d['real_face_plan']['looks'][n-1])]
        for number,cell in cells:
            prompt+='\n'+(f'Preview cell {number}:\n' if is_preview(d) else '')+'\n'.join(real_face_helper().prompt_lines(cell))
            if is_preview(d):
                positions={r['sha256']:i for i,r in enumerate(refs,1)}
                hashes=cell['reference_sha256s']
                if v2(d.get('shot_plan')):
                    per_cell=selected_references(d['references'],dict(d['context'],purpose='delivery'),d['shot_plan'],d['real_face_plan'],number)
                    hashes=[r['sha256'] for r in per_cell]
                selected=', '.join(f'Image {positions[h]}' for h in hashes if h in positions)
                prompt+='\nCell reference images: '+selected+'. Use only these references for this cell, retaining their declared garment/identity roles; do not mix product facts from other cells. Selection note: '+cell['selection_note']
    elif is_preview(d) and v2(d.get('shot_plan')):
        positions={r['sha256']:i for i,r in enumerate(refs,1)}
        for number,shot in enumerate(shot_helper().active_looks(d['shot_plan']),1):
            cell_refs=selected_references(d['references'],dict(d['context'],purpose='delivery'),d['shot_plan'],None,number)
            selected=', '.join(f"Image {positions[r['sha256']]}" for r in cell_refs if r['sha256'] in positions)
            prompt+=f"\nPreview cell {number}:\nShot identity: {shot['shot_id']}.\nCell reference images: "+selected+'. Use only these references for this cell, retaining each declared role; do not borrow another cell\'s product or aesthetic input.'
    if d['schema_version']==2 and d['model'] and prompt_contract(d,row)>=1:
        prompt=models.apply_conditions(prompt,d['model'],allow_child=True)
    if d.get('identity_instruction_version') == 1 and d.get('model'):
        anchor = any(r['role'] == 'identity-only' for r in refs)
        if d['model']['source_type'] == 'new':
            original = ('Identity scope: face-only reference; do not infer its unseen body; use declared body presentation.'
                        if d['model']['scope'] == 'face' else
                        'Identity scope: preserve visible face, apparent age, skin tone and body proportions.')
            if anchor:
                scope = 'Identity scope: preserve the accepted first-image identity; do not copy its pose, hands, support, clothing or background. Execute the current shot plan.'
            else:
                scope = 'Identity scope: create a new fictional person distinct from any person in garment-source images; use those images only for garment facts. Do not copy their face, hair, expression or identity.'
            prompt = prompt.replace(original, scope, 1)
            if not d['model']['locked']:
                prompt = prompt.replace('Fixed model conditions: follow declared identity references',
                                        'Fixed model conditions: follow declared casting requirements', 1)
        if anchor:
            prompt += '\nUse the first-image anchor only for identity; do not copy its pose, hands, support or framing. Follow this shot’s body action and hand positions.\n'
        elif any(r['role'] == 'identity-reference' for r in refs):
            prompt += '\nUse identity references only for the declared person; do not copy their pose, hands, support or framing. Follow this shot’s body action and hand positions.\n'
    if 'shot_plan' in d:
        shot_look=None if is_preview(d) else n
        if prompt_contract(d,row)==0:
            shot_helper().check_legacy_headers(row['prompt'],d['shot_plan'],shot_look,d.get('real_face_plan'))
        prompt=shot_helper().apply(prompt,d['shot_plan'],shot_look,d.get('real_face_plan'),strict=prompt_contract(d,row)>=1)
    prompt=photography_helper().apply(prompt,d['context'].get('photography_targets') if d['schema_version']==2 else None)
    if 'visual_plan' in d:
        prompt=visual_helper().apply(prompt,d['visual_plan'],None if is_preview(d) else n)
    return prompt


def handoff_manifest(d,row,refs,prompt):
    if d['schema_version']!=2:return None
    n=row['number']
    manifest=dict(look=n,attempt_number=row.get('attempt_number',1),plan_revision=row.get('plan_revision',0),
        frozen_prompt_sha256=row['prompt_sha256'],tool_prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
        reference_hashes=[r['sha256'] for r in refs])
    manifest.update(current_plan_sha256=plan_fingerprint(d),current_plan_version=d.get('plan_version',0))
    if 'visual_plan' in d:
        manifest.update(visual_plan=copy.deepcopy(d['visual_plan']),visual_plan_sha256=d['visual_plan_sha256'],
            prompt_contract_version=2)
    if 'shot_plan' in d:
        manifest.update(shot_plan=d['shot_plan'],shot_plan_sha256=d['shot_plan_sha256'],
            omitted_reference_sha256s=[r['sha256'] for r in d['references'] if r['sha256'] not in {x['sha256'] for x in refs}])
        if v2(d['shot_plan']):
            shots=shot_helper().active_looks(d['shot_plan']) if is_preview(d) else [shot_helper().shot_at(d['shot_plan'],n)]
            manifest['shot_bindings']=[dict(shot_id=s['shot_id'],slot=s['slot'],decision_sha256=object_hash(s)) for s in shots]
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
    if v2(d.get('shot_plan')):
        chosen={r['sha256'] for r in refs}
        manifest['omitted_reference_sha256s']=[r['sha256'] for r in d['references'] if r['sha256'] not in chosen]
    return manifest


def export_web_execution(root,look):
    """Explicitly add a one-call web envelope to an unchanged current export."""
    root=Path(root)
    with locked(root):
        d=read(root);check_evidence(root,d)
        if type(look) is not int or not 1<=look<=len(d['looks']):raise ValueError('Select one current look')
        row=d['looks'][look-1]
        if row['state']!='pending':raise ValueError('Prepare execution only for an unsubmitted pending look')
        blocked=progression_error(d,look)
        if blocked:raise ValueError(blocked)
        refs=references(root,d,look);prompt=handoff_prompt(d,row,refs)
        return web_execution_helper().prepare(root,d,row,handoff_directory(root,d,row),refs,prompt,
                                               handoff_manifest(d,row,refs,prompt))


def export(root):
    root=Path(root)
    with locked(root):
        d=read(root);check_evidence(root,d);folder=root/'handoff';folder.mkdir(exist_ok=True);lines=['# ChatGPT 网页转交包','只用内置生图；不要选择其他插件。','参考图按编号上传，确认全部完成；使用新建持久对话。','提交前必须由 Codex 记录 reserve；本包不是新的生图授权。','点击网页原图下载，不使用截图；将原文件回传给 Codex。','尚未确认的请求先查原对话，不要再次发送。','']
        if d['route']=='codex_native':
            lines=['# Codex 原生生成执行包','参考图按编号作为实际工具附件传入；只用原生生图。','调用前记录 reserve；本包不是新的生图授权。','原图返回后落盘、读取元数据并记录 QA。','未决调用先检查原结果，不自动追加调用。','']
        for row in d['looks']:
            n=row['number'];lines.append(f"- look-{n}: {row['state']}")
            if row['state']!='pending' or progression_error(d,n):continue
            refs=references(root,d,n);out=handoff_directory(root,d,row)
            out.mkdir(exist_ok=True);lines.append(f'  Current handoff: {out.name}; earlier attempt/plan folders are evidence only, never resubmit them.')
            for i,r in enumerate(refs,1):
                src=root/r['file'];dst=out/f'{i:02d}-{r["role"]}{src.suffix}'
                if dst.exists() and digest(dst)!=r['sha256']:raise ValueError('Existing handoff attachment changed')
                shutil.copyfile(src,dst)
            prompt=handoff_prompt(d,row,refs)
            (out/'prompt.txt').write_text(prompt,encoding='utf-8')
            if d['route']=='codex_native':
                request=dict(prompt=prompt,
                             referenced_image_paths=[str((out/f'{i:02d}-{r["role"]}{Path(r["file"]).suffix}').resolve()) for i,r in enumerate(refs,1)],
                             transparent_background=False)
                (out/'request.json').write_text(json.dumps(request,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            if d['schema_version']==2:
                manifest=handoff_manifest(d,row,refs,prompt)
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
        if not isinstance(spec,dict) or set(spec)-{'context','size','prompts','count','real_face_plan','garment_sha256s','series_role'}:
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
        if 'real_face_plan' in d and not v2(d.get('shot_plan')):
            planned=spec.get('real_face_plan',{})
            if any(planned.get(k)!=d['real_face_plan'][k] for k in ('coverage','primary_identity_sha256')):
                raise ValueError('Keep original reviewed real coverage; preview faces supply no new authentic view')
        refs=[dict(path=str(safe_file(parent,r['file'])),**{k:v for k,v in r.items() if k!='file'}) for r in d['references']
              if r['role']!='garment-source' or selected is None or r['sha256'] in selected]
        # create accepts hashes only on model supplements; original rows are rehashed.
        for ref in refs:
            if ref['role']!='model-supplement':ref.pop('sha256')
        prompts=spec.get('prompts')
        requested=len(prompts) if prompts is not None else spec.get('count',shot_helper().logical_count(effective_shot_plan(d)) if v2(effective_shot_plan(d)) else 1)
        if type(requested) is not int or requested not in (1,6,9):raise ValueError('Prepare one, six or nine delivery images')
        planned=copy.deepcopy(effective_shot_plan(d))
        if planned is not None:
            if selected is not None and not {r['sha256'] for r in planned['coverage']}<=set(selected):
                raise ValueError('Garment selection cannot drop frozen shot coverage; prepare an explicit plan revision first')
            if v2(planned):
                if requested==1:
                    number=context.get('first_pose')
                    if type(number) is not int or not 1<=number<=len(planned['looks']):raise ValueError('Select an original logical shot')
                    planned=shot_helper().subset(planned,number,series_role=spec.get('series_role','standalone'))
                elif requested!=shot_helper().logical_count(planned) or spec.get('series_role','series')!='series':
                    raise ValueError('A series delivery retains the complete preview plan')
            elif requested==1:
                if type(context.get('first_pose')) is not int or context['first_pose'] not in range(1,7):raise ValueError('Select a numbered shot for a planned single delivery')
                planned['looks']=[planned['looks'][context['first_pose']-1]]
        visual=copy.deepcopy(d.get('visual_plan'))
        if visual is not None and v2(planned):visual=visual_helper().bind_shots(visual,planned)
        elif visual is not None and requested==1:visual=visual_helper().subset(visual,context.get('first_pose'))
        face=spec.get('real_face_plan')
        if v2(planned) and 'real_face_plan' in d:
            expected_face=copy.deepcopy(d['real_face_plan'])
            expected_face['looks']=[copy.deepcopy(d['real_face_plan']['looks'][s['slot']-1]) for s in shot_helper().active_looks(planned)]
            if face is not None and face!=expected_face:
                raise ValueError('Delivery retains the reviewed real-person cell plan; revise the preview explicitly first')
            face=expected_face
        child=create(root,refs,prompts,spec['size'],d['identity'],model=d['model'],
                     context=context,route=d['route'],real_face_plan=face,shot_plan=planned,
                     visual_plan=visual,count=requested)
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
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['init','status','export','export-web-execution','authorize','mode','reserve','bind','unknown','failed','returned','accept','reject','audit-reject','review-output','revise-pending','retry-authorize','confirm-model','reject-model','continue-authorize','export-model','enable-failure-recovery','reconcile-failure','finish-preview','prepare-delivery','revise-preview','cancel-preview-revision','compose-preview']);p.add_argument('--task',type=Path,required=True);p.add_argument('--spec',type=Path);p.add_argument('--destination',type=Path);p.add_argument('--preview-task',type=Path);p.add_argument('--decision',choices=['stop','direction-confirmed']);p.add_argument('--name');p.add_argument('--look',type=int);p.add_argument('--note');p.add_argument('--limit',type=int);p.add_argument('--mode',choices=['manual','automatic']);p.add_argument('--ready',action='store_true');p.add_argument('--refs',nargs='*');p.add_argument('--conversation');p.add_argument('--tab');p.add_argument('--file',type=Path);p.add_argument('--failure-receipt',type=Path);p.add_argument('--reason');p.add_argument('--request-check-completed',action='store_true');p.add_argument('--qa',choices=['qa-pass','qa-user-review','qa-retry']);p.add_argument('--execution-manifest',type=Path);p.add_argument('--expected-submission-sha256');p.add_argument('--expected-output-sha256');p.add_argument('--expected-donor-sha256');p.add_argument('--rectangle',nargs=4,type=int);p.add_argument('--expected-prompt-sha256');p.add_argument('--expected-plan-sha256');p.add_argument('--expected-candidate-sha256');p.add_argument('--expected-attempt',type=int);p.add_argument('--approval-id');p.add_argument('--prompt-file',type=Path);p.add_argument('--model-spec',type=Path);p.add_argument('--include-accepted-reference',action='store_true');p.add_argument('--accepted-scope',choices=['face','full']);a=p.parse_args()
    try:
        if a.command!='export-model' and (a.include_accepted_reference or a.accepted_scope is not None):
            raise ValueError('Accepted-reference options are only for export-model')
        if a.accepted_scope is not None and not a.include_accepted_reference:
            raise ValueError('Declare --include-accepted-reference before choosing its scope')
        if a.command=='init':
            spec=json.loads(a.spec.read_text());result=create(a.task,spec['references'],spec.get('prompts'),spec['size'],spec.get('identity',True),schema_version=spec.get('schema_version',2),model=spec.get('model'),context=spec.get('context'),route=spec.get('route'),model_package=spec.get('model_package'),real_face_plan=spec.get('real_face_plan'),shot_plan=spec.get('shot_plan'),visual_plan=spec.get('visual_plan'),count=spec.get('count'))
        elif a.command=='prepare-delivery':
            result=create_from_preview(a.task,a.preview_task,json.loads(a.spec.read_text()),note=a.note)
        elif a.command=='status':result=read(a.task)
        elif a.command=='export':result=export(a.task)
        elif a.command=='export-web-execution':result=export_web_execution(a.task,a.look)
        elif a.command=='export-model':result=export_model(a.task,a.destination,a.name,include_accepted=a.include_accepted_reference,accepted_scope=a.accepted_scope or 'face')
        else:
            args={k:v for k,v in vars(a).items() if k not in ('command','task','spec','prompt_file','destination','preview_task','name','model_spec','include_accepted_reference','accepted_scope') and v is not None}
            if a.model_spec:
                if a.command not in ('retry-authorize','revise-preview'):raise ValueError('Model revision is only accepted with explicit first-image retry authority')
                args['model']=json.loads(a.model_spec.read_text(encoding='utf-8'))['model']
            if a.prompt_file:args['prompt']=a.prompt_file.read_text(encoding='utf-8')
            if a.command=='revise-preview' and a.spec:
                revision=json.loads(a.spec.read_text(encoding='utf-8'))
                if not isinstance(revision,dict) or set(revision)-{'model','shot_plan','visual_plan','prompt','garment_references'}:raise ValueError('Preview revision spec contains only model, shot_plan, visual_plan, prompt and garment_references')
                args.update(revision)
            if a.command=='retry-authorize' and a.spec:
                revision=json.loads(a.spec.read_text(encoding='utf-8'))
                if not isinstance(revision,dict) or not revision or set(revision)-{'shot_plan','visual_plan','prompt'}:
                    raise ValueError('Delivery retry spec contains only shot_plan, visual_plan and optional compiled prompt')
                args.update(revision)
            if a.command=='compose-preview' and a.spec:
                local=json.loads(a.spec.read_text(encoding='utf-8'))
                if not isinstance(local,dict) or set(local)!={'shot_plan'}:raise ValueError('Local composition spec contains only the reviewed shot_plan')
                args.update(local)
            if a.command=='continue-authorize':
                spec=json.loads(a.spec.read_text(encoding='utf-8'));args.update(context=spec['context'],prompts=spec.get('prompts'))
                if 'real_face_looks' in spec:args['real_face_looks']=spec['real_face_looks']
                if 'shot_plan' in spec:args['shot_plan']=spec['shot_plan']
                if 'visual_plan' in spec:args['visual_plan']=spec['visual_plan']
            result=update(a.task,a.command,**args)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:p.exit(1,str(error)+'\n')

if __name__=='__main__':main()
