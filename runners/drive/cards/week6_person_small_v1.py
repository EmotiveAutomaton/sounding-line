"""November 21 small diary rows. Operate on hash-verified workstation originals.

DESIGN CHECK. Paired outcomes share a mask, a roster and multiplicities. The
replay fits a separate solver. Neither missing inputs nor a singular fit are
converted into a zero. No participant identifier is written by this module.
"""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd

from . import week6_lb_bank_v1 as bank
from . import week6_ld12_common_v1 as core
from .batch_runtime import atomic, filehash, freeze, now, read
from .week6_es_v2 import preserve_inherited_yield
from .week6_ld_draws_v1 import RequestedYield

MANIFEST = 'cc63f8f6ffb5a47845b98b0d754b6412c18b0e6c79ea5badd8466d5589075f6d'
ROOT_NAME = 'DRT1-20261121'
EVENTS = tuple('status_'+k for k in ('admired','respected','criticised','ignored','upstaged','sidelined'))
LINEAR = {
    ('ANX1','0060'): ('anxious_schoolwork','afraid','sad','curious'),
    ('ANX1','0062'): ('worried','afraid','sad'),
    ('ANX1','0072'): ('parent_worried','parent_afraid','parent_sad'),
    ('PBK1','0072'): ('parenting_fun','parent_afraid','parent_sad'),
}
PAIRS = {('PRD1','0056'),('PRD1','0057')}
ERRORS = (core.fits.InvalidFit, np.linalg.LinAlgError)


def source_columns(card, member):
    if (card, member) in LINEAR:
        return ('id', *LINEAR[card,member])
    if (card, member) not in PAIRS:
        raise ValueError('No bound source row')
    keys = ('id','interaction','int_proud','int_enthusiastic',*EVENTS)
    return keys if member=='0056' else (*keys,'int_success','occup_success','occup_proud','occup_enthusiastic')


def binding(card, member, root):
    """Verify the local directory before opening the data table."""
    design_root = Path(root)
    if not design_root.is_absolute() or design_root.drive.casefold()!=os.environ['SystemDrive'].casefold() or design_root.name!=ROOT_NAME:
        raise ValueError('Expected the temporary workstation root')
    desc = design_root/'DRT1_MANIFEST.json'
    if filehash(desc)!=MANIFEST:
        raise ValueError('Changed temporary-root manifest')
    roster={row['path']:row for row in read(desc)['files']}
    prefix='open/openesm-'+member+'/'
    paths={}
    for name in ('SOURCE.json','DOCUMENTED_METADATA.json','SCHEMA.json','LICENCE_RECORD.json'):
        rel=prefix+name
        if filehash(design_root/rel)!=roster[rel]['sha256']:
            raise ValueError('Changed source metadata')
        paths[name]=design_root/rel
    source=read(paths['SOURCE.json'])
    items={x['name']:x for x in read(paths['DOCUMENTED_METADATA.json'])['features']}
    layout,= [f for f in read(paths['SCHEMA.json'])['files'] if f['file'].endswith('_ts.tsv')]
    rel=prefix+'raw/'+layout['file']
    required=set(source_columns(card,member))
    if not required<=items.keys() or not required<={x['name'] for x in layout['columns']}:
        raise ValueError('Missing declared items')
    if (source['slug']!='openesm-'+member or source['class'] not in ('open-clean','open-tests-only')
            or not source['licence']['name'] or layout['sha256']!=roster[rel]['sha256']
            or layout['bytes']!=roster[rel]['bytes'] or layout['malformed_row_count']):
        raise ValueError('Unbound diary source')
    path=design_root/rel
    if filehash(path)!=layout['sha256']: raise ValueError('Original source digest differs')
    return path,layout['sha256']


@dataclass
class Panel:
    ids: np.ndarray
    x: np.ndarray
    y: np.ndarray
    predictors: tuple
    outcomes: tuple
    context: object = None


def prepare(card,member,frame):
    keys=source_columns(card,member)
    source_count=len(frame)
    frame=frame.loc[~frame.id.isin(['','NA']),list(keys)].copy()
    people,ids=np.unique(frame.pop('id').to_numpy(str),return_inverse=True)
    for key in frame:
        column=pd.to_numeric(frame[key].replace({'':np.nan,'NA':np.nan}),errors='raise')
        if key=='interaction': low,high=1,2
        elif key=='anxious_schoolwork': low,high=0,1
        else: low,high=1,5 if member=='0060' else (6 if card=='PRD1' else 7)
        if ((column<low)|(column>high)|(column%1!=0)&column.notna()).any():
            raise ValueError('Source coding exceeds bound for '+key)
        frame[key]=column
    result=core.Prepared(len(people),dict(temporary_root=ROOT_NAME,manifest_sha256=MANIFEST,
                                         source_rows=source_count,missing_ids=source_count-len(frame),panels={}))
    def add(name,x,y,predictors,outcomes,mask,context=None):
        keep=mask & np.isfinite(x).all(axis=1) & np.isfinite(y).all(axis=1)
        group=ids[keep]
        result.panels[name]=Panel(group,x[keep],y[keep],predictors,outcomes,None if context is None else context[keep])
        denom=dict(rows=int(keep.sum()),people=len(np.unique(group)),eligible=int(mask.sum()))
        result.metadata['panels'][name]=denom
        for outcome in outcomes:
            for key in predictors: core.metric(result,f'{name}/{outcome}/{key}',f'{outcome} on {key}',denom)
        if card=='ANX1':
            for key in ('explained','residual'): core.metric(result,key,key+' share',denom)
        else:
            core.metric(result,name+'/contrast','paired slope difference',denom,role='registered' if name!='b' else 'table',
                        bar=.10 if card=='PRD1' and name=='a' else None)
    if card!='PRD1':
        y,*x=LINEAR[card,member]
        add('L',frame[x].to_numpy(float),frame[[y]].to_numpy(float),tuple(x),(y,),np.ones(len(frame),bool))
    else:
        ctx=frame.interaction.to_numpy()
        y=('int_proud','int_enthusiastic')
        add('a',frame[list(EVENTS)].to_numpy(float),frame[list(y)].to_numpy(float),EVENTS,y,ctx==1)
        if member=='0057':
            take=lambda k: np.where(ctx==1,frame['int_'+k],frame['occup_'+k])
            add('b',take('success')[:,None],np.column_stack([take('proud'),take('enthusiastic')]),
                ('success','company_times_success'),('proud','enthusiastic'),np.isin(ctx,[1,2]),(ctx==1).astype(float))
    return result


def evaluate(data,weights,guard,*,verify=False):
    mass=core.multiplicities(data.people,weights)
    if mass.sum()!=data.people: raise ValueError('Incomplete whole-person draw')
    within,logit,linear=core.arithmetic(verify)
    result=dict.fromkeys(data.specs)
    for name,p in data.panels.items():
        guard()
        if not len(p.ids): continue
        w=mass[p.ids]
        if not w.sum(): continue
        try:
            z,means,_=within(p.x,p.ids,w)
            if name=='L':
                y=within(p.y,p.ids,w)[0][:,0]
                coefs=linear(z,y,w)
                for key,coef in zip(p.predictors,coefs): result[f'L/{p.outcomes[0]}/{key}']=float(coef)
                if 'explained' in result:
                    residual=float(np.average((y-z@coefs)**2,weights=w)/np.average(y**2,weights=w))
                    result.update(explained=1-residual,residual=residual)
                else: result['L/contrast']=float(coefs[0]-coefs[1])
                continue
            if name=='a': design=np.column_stack((np.ones(len(w)),z,means))
            else: design=np.column_stack((np.ones(len(w)),p.context,z,p.context*z[:,0],means))
            for idx,outcome in enumerate(p.outcomes):
                try: beta=logit(design,p.y[:,idx]>1,w)
                except ERRORS: continue
                selected=beta[1:1+len(EVENTS)] if name=='a' else beta[2:4]
                for key,coef in zip(p.predictors,selected): result[f'{name}/{outcome}/{key}']=float(coef)
            key=p.predictors[0] if name=='a' else p.predictors[1]
            result[name+'/contrast']=core.contrast(result[f'{name}/{p.outcomes[0]}/{key}'],result[f'{name}/{p.outcomes[1]}/{key}'])
        except ERRORS:
            continue
    core.record_point_dispositions(data,result,weights)
    return result


def operate(output,inputs,config,verify):
    card,member=config['card'],config['member']
    root=Path(inputs['data_root'])
    path,digest=binding(card,member,root)
    if inputs['manifest_sha256']!=MANIFEST or inputs['source_sha256']!=digest: raise ValueError('Changed plan source')
    output=Path(output)
    phase='verify' if verify else 'execute'
    if not verify: preserve_inherited_yield(output)
    started=time.monotonic()
    def guard():
        if time.monotonic()-started>=config['max_wall_seconds'] or any((output/n).exists() for n in ('YIELD_REQUEST.json','STOP_REQUEST.json')):
            raise RequestedYield('wall or runtime control')
    def progress(count,elapsed):
        atomic(output/phase/'DRAW_PROGRESS.json',dict(at=now(),card=card,member=member,phase=phase,committed_draws=count,
               temporary_root=ROOT_NAME,manifest_sha256=MANIFEST,elapsed=elapsed))
    try:
        guard()
        frame=pd.read_csv(path,sep='\t',dtype=str,usecols=source_columns(card,member),keep_default_na=False,na_filter=False)
        data=prepare(card,member,frame)
        result=bank.run(output/phase,sys.modules[__name__],data,member=member,source_digest=digest,
                        seed=202611190000+int(member),guard=guard,verify=verify,execute_dir=output/'execute',
                        limit=config['max_new_draws'],progress=progress)
    except RequestedYield as exc:
        return dict(status='yielded',verified=False,operation=phase,reason=str(exc),scientific_result_complete=False)
    result.update(card=card,temporary_root=ROOT_NAME,manifest_sha256=MANIFEST)
    dest=output/phase/'ENGINE_RESULT.json'
    if dest.exists():
        if read(dest)!=result: raise ValueError('Conflicting completed bank')
    else: freeze(dest,result)
    return dict(status='verified' if verify else 'computed',verified=verify,requires_fresh_replay=not verify,
                scientific_result_complete=verify,engine_sha256=filehash(dest),draw_count=2000)


def execute(output,inputs,config): return operate(output,inputs,config,False)


def verify(output,inputs,config): return operate(output,inputs,config,True)

