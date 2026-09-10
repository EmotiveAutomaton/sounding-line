"""Evaluator-side ArgRewrite cases and actual source/evidence separation.

DESIGN CHECK: H01/X01/X02/X05; LESSONS 3--5 and canonical-unit corrections.
NULL: future targets cannot choose a current span, private fields cannot enter
evidence, and connected sources cannot cross fitting/evaluation. ALTERNATIVE:
genuine earlier drafts and revision pairs form distinct explicit views, retaining
all canonical exclusions. The entire corpus was previously exposed: no reserve
or fresh confirmation is created. Annotation agreement is not maker intention.
"""
import argparse
from collections import Counter
from pathlib import Path
import time
from .argrewrite import CLASSES,visible,future_visible
from .common import REPO,ROOT,Units,closure,digest,file_hash,freeze,read
from .queue import inside,verify_sources,writer
from .split_guard import Separation,task_copies
from .training_jobs import cell_identity


def argrewrite_rows(essays):
    rows=[];excluded=[]
    if len({e['group'] for e in essays})!=len(essays):raise ValueError('duplicate essay lineage')
    for essay in essays:
        group=essay['group'];previous=[u['fine'] for u in essay['units'] if u['cycle']=='12' and u['usable']]
        for unit in essay['units']:
            if unit['group']!=group or unit['cycle'] not in ('12','23'):raise ValueError('revision belongs to a different lineage or cycle')
            if not unit['usable']:
                excluded.append({'source_unit':group,'task':'retrospective','key':unit['key'],'reason':unit['exclusion']});continue
            if unit['fine'] not in CLASSES:raise ValueError('unknown canonical purpose')
            pair=visible(unit,'pair')
            rows.append({'key':unit['key'],'unit':group,'source_group':'argrewrite:'+group,
                'task':'retrospective','cycle':unit['cycle'],'labels':[unit['fine']],
                'views':{'artifact':visible(unit,'artifact'),'pair':pair,
                    'record':{**pair,'earlier_labels':previous if unit['cycle']=='23' else []}},
                'annotation_scope':'canonical single-purpose units; excluded compound-purpose groups retained in ledger'})
        if not essay['future_usable']:
            excluded.append({'source_unit':group,'task':'future','reason':essay['future_exclusion']});continue
        later=[u['fine'] for u in essay['units'] if u['cycle']=='23' and u['usable']]
        if not later:
            excluded.append({'source_unit':group,'task':'future','reason':'no usable annotated next-cycle unit'});continue
        rows.append({'key':digest(['argrewrite-whole-next-cycle',group]),'unit':group,'source_group':'argrewrite:'+group,
            'task':'future','cycle':'23','labels':later,
            'views':{view:future_visible(essay,view) for view in ('artifact','record')},
            'annotation_scope':'one forecast scored against every canonical later-cycle annotation; no future-selected excerpt'})
    if len({r['key'] for r in rows})!=len(rows):raise ValueError('duplicate case identity')
    return rows,excluded


def separate(rows,allocation,separation,required_tasks=('retrospective','future')):
    if set(allocation)!={r['unit'] for r in rows}:raise ValueError('allocation omits or adds a source lineage')
    if set(allocation.values())!={'train','development','evaluation'}:raise ValueError('three explicit historical partitions required')
    lanes={lane:[r for r in rows if allocation[r['unit']]==lane] for lane in ('train','development','evaluation')}
    ledgers={}
    for lane,against in [('development',lanes['evaluation']),('train',lanes['development']+lanes['evaluation'])]:
        groups={r['source_group'] for r in lanes[lane]};targets={r['source_group'] for r in against}
        kept,source_receipt=separation.filter_fit(groups,targets)
        candidates=[r for r in lanes[lane] if r['source_group'] in kept];excluded_keys=set();copies=[]
        for task in ('retrospective','future'):
            selected=[r for r in candidates if r['task']==task];test=[r for r in against if r['task']==task]
            if not test:
                if task in required_tasks:raise ValueError('empty independent evaluation task')
                continue
            for view in sorted({v for r in test for v in r['views']}):
                def public(r):return {'key':r['key'],'unit':r['unit'],'evidence':{'task':task,'view':view,'input':r['views'][view]}}
                _,dropped=task_copies([public(r) for r in selected if view in r['views']],
                    [public(r) for r in test if view in r['views']])
                excluded_keys.update(r['key'] for r in dropped)
                copies.extend({'task':task,'view':view,**r} for r in dropped)
        lanes[lane]=[r for r in candidates if r['key'] not in excluded_keys]
        ledgers[lane]={'source_separation':source_receipt,'public_task_exclusions':copies,
            'assigned_records':len([r for r in rows if allocation[r['unit']]==lane]),'retained_records':len(lanes[lane]),
            'same_fitting_rows_for_all_views':True,'empty_public_artifacts_are_task_copies_not_asserted_author_aliases':True}
        for task in required_tasks:
            if not any(r['task']==task for r in lanes[lane]):raise ValueError('separation exhausted a required fitting/selection task')
    return lanes,ledgers


def inputs(scope):
    """Reconstruct prepared-source cases and their exclusions without writing."""
    if scope not in ('pilot','scientific'):raise ValueError('revision preparation scope differs')
    prepared=ROOT/'private/prepared/argrewrite-v3';complete=read(prepared/'COMPLETE.json');identity0=read(prepared/'IDENTITY.json')
    if complete['identity_sha256']!=digest(identity0) or complete['historical_v4_exact'] is not True:raise ValueError('canonical preparation not verified')
    paths=sorted((prepared/'essays').glob('*.json'));essays=[read(p) for p in paths]
    original=read(ROOT/'private/pilot-baseline/argrewrite-v1/IDENTITY.json')
    if original['prepared_records']!=closure(paths) or original['prepared_identity']!=digest(identity0):raise ValueError('previous exposure or prepared bytes changed')
    if len(essays)!=86 or complete['reserve_groups']!=0:raise ValueError('historical exposure scope changed')
    old_fit=original['fit_groups'];evaluation=set(original['test_groups'])
    ordered=sorted(old_fit,key=lambda k:digest(['s9-arg-development-only',k]));cut=3*len(ordered)//4
    allocation={k:'train' for k in ordered[:cut]}|{k:'development' for k in ordered[cut:]}|{k:'evaluation' for k in evaluation}
    rows,excluded=argrewrite_rows(essays);cross=ROOT/'private/prepared/cross-source-v2'
    separation=Separation.verified(cross);lanes,ledger=separate(rows,allocation,separation)
    pilot_selected=None
    if scope=='pilot':
        pilot_selected={}
        for lane in ('development','evaluation'):
            chosen=[]
            for task in ('retrospective','future'):
                candidates=sorted([r for r in lanes[lane] if r['task']==task],key=lambda r:digest(['discarded-revision-pilot',r['key']]))
                groups=[]
                for row in candidates:
                    if row['unit'] not in groups:chosen.append(row);groups.append(row['unit'])
                    if len(groups)==2:break
                if len(groups)!=2:raise ValueError('pilot requires two distinct source groups per task')
            pilot_selected[lane]=[r['key'] for r in chosen];lanes[lane]=chosen
    metadata={
        'prepared_identity_sha256':digest(identity0),'prepared_records':closure(paths),
        'historical_allocation_sha256':digest(original),'cross_source_complete_sha256':file_hash(cross/'COMPLETE.json'),
        'classes':list(CLASSES),'allocation':allocation,'pilot_selected':pilot_selected,
        'data_scope':'previously exposed student essays; no reserve or new independent confirmation',
        'target':'canonical annotator-purpose agreement, or whole next-cycle annotation distribution'}
    return lanes,excluded,ledger,metadata


def run(directory,scope):
    start,cpu=time.monotonic(),time.process_time();cell=cell_identity();directory=inside(directory)
    prefix='revision-case-pilots' if scope=='pilot' else 'scientific-revision-case'
    if scope not in ('pilot','scientific') or not directory.is_relative_to(ROOT/'private'/prefix):raise ValueError('revision preparation scope differs')
    lanes,excluded,ledger,metadata=inputs(scope)
    source=closure([REPO/'runners/stage9',REPO/'runners/stage7',REPO/'runners/stage8',REPO/'soundingline',
        REPO/'runners/__init__.py',REPO/'runners/readout_repair.py',REPO/'runners/run_arg_replication.py',
        REPO/'runners/s3_lib.py',REPO/'runners/s4_lib.py',REPO/'runners/s5_lib.py'])
    identity={'cell_identity':cell,'operation':'argrewrite-actual-revision-cases-v1','scope':scope,'source':source,**metadata}
    with writer(directory):
        Units(directory,identity)
        if (directory/'COMPLETE.json').exists():
            done=read(directory/'COMPLETE.json')
            if done['identity_sha256']!=digest(identity) or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']:raise ValueError('completed revision cases changed')
            return done
        freeze(directory/'CASES.json',lanes);freeze(directory/'EXCLUSIONS.json',excluded);freeze(directory/'SEPARATION.json',ledger)
        verify_sources(source)
        done={'cell_identity':cell,'identity_sha256':digest(identity),'execution_complete':True,
            'counts':{lane:{task:sum(r['task']==task for r in own) for task in ('retrospective','future')} for lane,own in lanes.items()},
            'scope':scope,'reserve_groups':0,'scientific_admission':False,'wall_seconds':time.monotonic()-start,
            'parent_cpu_seconds':time.process_time()-cpu,'outputs':closure([directory/p for p in ('IDENTITY.json','CASES.json','EXCLUSIONS.json','SEPARATION.json')])}
        freeze(directory/'COMPLETE.json',done);return done


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--scope',choices=('pilot','scientific'),required=True)
    a=p.parse_args();run(a.output,a.scope)
