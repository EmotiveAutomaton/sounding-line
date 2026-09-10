"""Development-only selection of a complete three-seed recipe in each family.

DESIGN CHECK: C05/C06/C07/X01/X11/X12; LESSONS 3--5, CONTROLS 6.
NULL: one lucky seed cannot replace the recipe's mean, and missing/failed seeds
cannot disappear. ALTERNATIVE: one complete recipe per family is selected using
the same pre-existing development targets, retaining all seeds and failed fits.
Ranking is not an effect-size verdict or a competence gate. A family with no
complete eligible recipe gets no selection; independent CPU work stays eligible.
The actual two-fit pilot exercises source/queue/checkpoint consumption; full-grid
ranking and failure logic are also tested on independent known-answer fixtures.
"""
from .live_status import read as read_status
import argparse
from collections import defaultdict
import math
from pathlib import Path
import time
from runners.stage9.common import REPO,ROOT,Units,closure,digest,file_hash,freeze,read
from runners.stage9.neural_operations import training_package
from runners.stage9.queue import inside,verify_committed,verify_disposition,verify_sources,writer
from runners.stage9.training_jobs import FITS,cell_identity,training_root

PILOT_FITS=(('qwen','both_mixed',997901),('smollm','both_mixed',997901))


def choose(rows,scope):
    expected=FITS if scope=='scientific' else PILOT_FITS if scope=='pilot' else ()
    if not expected or len(rows)!=len(expected) or {(r['family'],r['recipe'],r['seed']) for r in rows}!=set(expected):
        raise ValueError('selection must retain every assigned family recipe and seed')
    if any(r['status'] not in ('COMPLETE','FAILED','NOT_RUN') for r in rows):
        raise ValueError('recipe selection cannot read an unfinished fitting grid')
    by_family={}
    for family in ('qwen','smollm'):
        own=[r for r in rows if r['family']==family];recipes={}
        valid=[r for r in own if r['status']=='COMPLETE']
        if valid and len({r['development_sha256'] for r in valid})!=1:
            raise ValueError('recipes used different validation questions or targets')
        for recipe in sorted({r['recipe'] for r in own}):
            cells=sorted([r for r in own if r['recipe']==recipe],key=lambda r:r['seed'])
            accepted=all(r['status']=='COMPLETE' for r in cells)
            if accepted and any(type(r['score']) not in (int,float) or not math.isfinite(r['score']) for r in cells):
                raise ValueError('nonfinite development selection score')
            recipes[recipe]={'complete_seed_set':accepted,'seeds':cells,
                'mean_development_log_score':math.fsum(r['score'] for r in cells)/len(cells) if accepted else None}
        eligible=[name for name,row in recipes.items() if row['complete_seed_set']]
        selected=min(eligible,key=lambda name:(-recipes[name]['mean_development_log_score'],name)) if eligible else None
        by_family[family]={'selected_recipe':selected,'selected_seeds':[r['seed'] for r in recipes[selected]['seeds']] if selected else [],
            'recipes':recipes,'selected':selected is not None,
            'disposition':'DESCRIPTIVE' if selected else 'NOT RUN WITH REASON',
            'reason':'maximum equal-seed mean on the common development questions; lexical recipe tie-break' if selected else 'no complete eligible seed set'}
    return {'families':by_family,'assigned_fits':len(rows),'scope':scope,
        'selection_rule':'one complete recipe per family; retain every seed, no best-seed substitution',
        'development_only':True,'scientific_admission':False,
        'limit':'training validation has original-law coverage and includes supplied-purpose renderings; selection does not establish broader or unaided competence'}


def fitting_rows(manifest_path,queue_root,scope):
    manifest_path=inside(manifest_path);queue_root=inside(queue_root)
    plan=read(manifest_path);status=read_status(queue_root/'STATUS.json');manifest_sha=digest(plan)
    if status['manifest_sha256']!=manifest_sha or plan['kind']!=('science' if scope=='scientific' else 'prelaunch_rehearsal'):
        raise ValueError('fitting source queue or scope differs')
    jobs=[j for j in plan['jobs'] if j['module']=='runners.stage9.training_jobs' and j['arguments'][0]=='fit']
    rows=[]
    for job in jobs:
        args=job['arguments'];arg=lambda key:args[args.index('--'+key)+1]
        family,recipe,seed=arg('family'),arg('recipe'),int(arg('seed'));current=status['jobs'][job['id']]
        row={'family':family,'recipe':recipe,'seed':seed,'status':current['status'],'job':job['id']}
        if current['status'] in ('FAILED','NOT_RUN'):
            verify_disposition(queue_root,job,current)
            record=read(queue_root/current['disposition_path'])
            if record['cell_identity']!=digest({'manifest_sha256':manifest_sha,'job':job}):raise ValueError('failed fitting identity differs')
            rows.append(row|{'reason':record['reason'],'disposition_sha256':current['disposition_sha256']});continue
        if current['status']!='COMPLETE':raise ValueError('fit grid still running')
        verify_committed(queue_root,job,plan,manifest_sha);produce=read(REPO/job['produces'])
        path=training_root(family,recipe,seed) if scope=='scientific' else ROOT/'private/training-handler-pilots/v2'/family/'fit'
        if (REPO/produce['training_root']).resolve()!=path:raise ValueError('selected fitting source is not the declared checkpoint root')
        adapter,adapter_sha,fit_sha=training_package(path,family,scope)
        if produce['training_complete_sha256']!=fit_sha or produce['selected_checkpoint_sha256']!=adapter_sha:
            raise ValueError('training wrapper differs from its actual complete fit')
        done=read(path/'COMPLETE.json');identity=read(path/'IDENTITY.json')
        corpus=(ROOT/'private/scientific-recipes'/family/(recipe+'.json') if scope=='scientific' else
                ROOT/'private/pilot-dose-v3'/family/'mixed.json')
        corpus_data=read(corpus)
        if identity['corpus_sha256']!=file_hash(corpus):raise ValueError('fitting development corpus changed')
        epochs=[read(path/f'EPOCH_{i}.json') for i in range(3 if scope=='scientific' else 1)]
        if epochs!=done['curve'] or any(e['n']!=(96 if scope=='scientific' else 80) for e in epochs):
            raise ValueError('complete epoch development measurements differ')
        best=max(epochs,key=lambda e:e['mean_next_action_log_score'])
        if best['checkpoint']!=done['selected_checkpoint'] or best['checkpoint_sha256']!=adapter_sha:
            raise ValueError('selected epoch differs from the original development rule')
        rows.append(row|{'score':best['mean_next_action_log_score'],'selected_checkpoint':best['checkpoint'],
            'adapter_sha256':adapter_sha,'complete_sha256':fit_sha,'validation_count':best['n'],
            'development_sha256':digest(corpus_data['validation_choices']),
            'epoch_records_sha256':digest(epochs),'fitting_produce_sha256':file_hash(REPO/job['produces'])})
    choose(rows,scope)  # Reject missing, extra, duplicated or differently assigned fits.
    return rows,manifest_sha


def run(directory,manifest,queue,scope):
    start,cpu=time.monotonic(),time.process_time();cell=cell_identity();directory=inside(directory)
    root_name='recipe-selection-pilots' if scope=='pilot' else 'scientific-recipe-selection'
    if scope not in ('pilot','scientific') or not directory.is_relative_to(ROOT/'private'/root_name):raise ValueError('recipe selection output scope differs')
    rows,manifest_sha=fitting_rows(manifest,queue,scope)
    source=closure([REPO/'runners/stage9',REPO/'runners/stage7',REPO/'runners/stage8',REPO/'soundingline',
        REPO/'runners/__init__.py',REPO/'runners/readout_repair.py',REPO/'runners/s3_lib.py',REPO/'runners/s4_lib.py',REPO/'runners/s5_lib.py'])
    identity={'cell_identity':cell,'operation':'development-recipe-selection-v1','scope':scope,'source':source,
        'fitting_manifest_sha256':manifest_sha,'fitting_rows_sha256':digest(rows)}
    with writer(directory):
        Units(directory,identity)
        if (directory/'COMPLETE.json').exists():
            done=read(directory/'COMPLETE.json')
            if done['identity_sha256']!=digest(identity) or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']:
                raise ValueError('completed recipe selection changed')
            return done
        result=choose(rows,scope);freeze(directory/'SELECTION.json',result);freeze(directory/'FITTING_ROWS.json',rows);verify_sources(source)
        done={'cell_identity':cell,'identity_sha256':digest(identity),'execution_complete':True,'development_only':True,
            'families':{family:{k:group[k] for k in ('selected','selected_recipe','selected_seeds','reason')} for family,group in result['families'].items()},
            'outputs':closure([directory/p for p in ('IDENTITY.json','SELECTION.json','FITTING_ROWS.json')]),
            'wall_seconds':time.monotonic()-start,'parent_cpu_seconds':time.process_time()-cpu,'scientific_admission':False}
        freeze(directory/'COMPLETE.json',done);return done


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('output','manifest','queue'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--scope',choices=('pilot','scientific'),required=True)
    a=p.parse_args();run(a.output,a.manifest,a.queue,a.scope)
