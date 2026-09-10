"""Separate original/expanded broad-generation and reference construction samples.

DESIGN CHECK: C02/C05/C06/C07/X01/X08/X11/X12; LESSONS 3--5.
NULL: repeated source content, crossed parameter partitions, incomplete cohorts,
invalid population logs or reader-dependent reference selection refuse. ALTERNATIVE:
the exact constructor's logs pass their own feasibility ruler and two complete,
disjoint samples freeze before any reader generates. Original means the historical
no-change constructor, under the declared Stage 9 held-out parameter partition;
that restricted population is disclosed, never retroactive Stage 8 admission.
The two-unit discarded route uses this same preparation and validation path.
"""
import argparse
from collections import Counter
from pathlib import Path
import time

from runners.stage9.common import REPO,ROOT,Units,closure,digest,file_hash,freeze,read
from runners.stage9.construction import Replay
from runners.stage9.generation_pilot import original_world
from runners.stage9.queue import inside,verify_sources,writer
from runners.stage9.recipes import POP,parameter_partition,sampled_world
from runners.stage9.series_cases import content_identity
from runners.stage9.training_jobs import cell_identity

POPULATIONS=('original','expanded')
ROLES=('pilot','development','discovery')


def make_attempt(index,domain,role,population,sample):
    if (population not in POPULATIONS or role not in ROLES or domain not in POP.DOMAINS
        or sample not in ('reader','reference') or type(index) is not int or index<0):
        raise ValueError('undeclared generation construction')
    lid=f'S9GEN|{domain}|{role}|{population}|{sample}|{index}'
    world=original_world(lid) if population=='original' else sampled_world(lid,'both')
    expected='training' if role=='pilot' else role
    if parameter_partition(world)!=expected:
        return {'selected':False,'reason':'outside declared parameter partition','lineage':lid}
    if world['degenerate']:
        return {'selected':False,'reason':'original constructor degeneracy','lineage':lid}
    # This is validation of the ruler, not a filter on the reader's result.
    actual=world['trajectory']['steps']
    if not POP.feasible_visible(world,actual)['all_feasible']:
        raise ValueError('population source log fails its own visible-feasibility ruler')
    replay=Replay(world,actual)
    # The original trace also stores policy likelihood and stopping diagnostics.
    # Replay returns executed events only; preserve all original diagnostics in
    # the source record and compare the complete explicit event schema here.
    fields=('i','type','section','slot','outcome','goal','goal_owner')
    if digest(replay.steps)!=digest([{k:event[k] for k in fields} for event in actual]):
        raise ValueError('population source log does not replay exactly')
    return {'selected':True,'world':world,'content_sha256':content_identity(world),'lineage':lid}


def checked_inputs(directory,scope,population):
    directory=inside(directory);complete=read(directory/'COMPLETE.json');identity=read(directory/'IDENTITY.json')
    if (complete.get('accepted') is not True or complete.get('construction_only') is not True
        or identity['operation']!='broad-generation-preparation-v1' or identity['population']!=population
        or complete['identity_sha256']!=digest(identity)
        or closure([REPO/p for p in complete['outputs']['files']])!=complete['outputs']):
        raise ValueError('generation construction identity or output closure differs')
    role=identity['role'];expected=2 if scope=='pilot' else 96
    if (scope not in ('pilot','scientific') or role not in (('pilot',) if scope=='pilot' else ('development','discovery'))
        or identity['count_per_sample']!=expected):
        raise ValueError('generation cohort cannot borrow pilot or change declared count')
    plan=read(directory/'WORLD_PLAN.json');seen=set();input_seen=set()
    for sample in ('reader','reference'):
        rows=plan[sample]
        if len(rows)!=expected or Counter(r['world']['domain'] for r in rows)!=dict.fromkeys(POP.DOMAINS,expected//2):
            raise ValueError('incomplete or unbalanced generation population')
        for row in rows:
            actual=make_attempt(row['index'],row['world']['domain'],role,population,sample)
            if digest(actual)!=digest(row['source']):raise ValueError('generation source world differs from constructor')
            if digest(row['world'])!=digest(actual['world']):raise ValueError('generation world differs from source')
            key=content_identity(row['world'])
            if key in seen:raise ValueError('generation/reference source content repeats')
            seen.add(key)
            # Header-identical tasks remain distinct stochastic worlds but are
            # recorded explicitly; no claim of independent prompt identities.
            from runners.stage9.construction import rendered_prefix
            input_seen.add(digest(rendered_prefix(row['world'],[])))
    values=[POP.marginal_log_likelihood(row['world'])['per_event'] for row in plan['reference']]
    if values!=plan['reference_scores']:raise ValueError('frozen reference calculation changed')
    if len(input_seen)!=plan['distinct_headers_across_samples']:
        raise ValueError('generation input identity count changed')
    cases=[{'unit':r['source']['content_sha256'],'role':role,'source_worlds':[r['world']]} for r in plan['reader']]
    return cases,role,file_hash(directory/'COMPLETE.json'),plan


def prepare(directory,*,role,population):
    cell=cell_identity();directory=inside(directory)
    if role not in ROLES or population not in POPULATIONS:raise ValueError('undeclared generation population or role')
    count=2 if role=='pilot' else 96
    source=closure([REPO/'runners/stage9',REPO/'runners/stage7',REPO/'runners/stage8',REPO/'soundingline',
        REPO/'runners/__init__.py',REPO/'runners/readout_repair.py',REPO/'runners/s3_lib.py',REPO/'runners/s4_lib.py',REPO/'runners/s5_lib.py'])
    identity={'cell_identity':cell,'operation':'broad-generation-preparation-v1','population':population,
        'role':role,'count_per_sample':count,'maximum_attempts_per_domain':4000,'source':source,
        'parameter_partition':'training' if role=='pilot' else role,
        'selection':'first nondegenerate source worlds in each domain and assigned parameter partition; independent reader/reference streams',
        'original_scope':'historical no-change construction restricted to this Stage 9 parameter split; no retrospective admission'}
    with writer(directory):
        units=Units(directory,identity)
        if (directory/'COMPLETE.json').exists():
            checked_inputs(directory,'pilot' if role=='pilot' else 'scientific',population)
            return read(directory/'COMPLETE.json')
        started,cpu=time.monotonic(),time.process_time();plan={'reader':[],'reference':[]};attempts=[];seen=set()
        for sample in ('reader','reference'):
            for domain in POP.DOMAINS:
                selected=0
                for index in range(4000):
                    key={'sample':sample,'domain':domain,'index':index}
                    row=units.get(key)
                    if row is None:
                        row=make_attempt(index,domain,role,population,sample);units.put(key,row)
                    attempts.append({**key,'selected':row['selected'],'reason':row.get('reason')})
                    if row['selected']:
                        if row['content_sha256'] in seen:raise ValueError('repeated whole generation source')
                        seen.add(row['content_sha256'])
                        plan[sample].append({'index':index,'world':row['world'],'source':row});selected+=1
                    if selected==count//2:break
                if selected!=count//2:raise ValueError('bounded generation construction exhausted before complete cohort')
        plan['reference_scores']=[POP.marginal_log_likelihood(row['world'])['per_event'] for row in plan['reference']]
        if any(v is None for v in plan['reference_scores']):raise ValueError('missing broad reference score')
        from runners.stage9.construction import rendered_prefix
        plan['distinct_headers_across_samples']=len({digest(rendered_prefix(r['world'],[])) for k in ('reader','reference') for r in plan[k]})
        freeze(directory/'WORLD_PLAN.json',plan);freeze(directory/'ATTEMPTS.json',attempts);verify_sources(source)
        complete={'cell_identity':cell,'identity_sha256':digest(identity),'accepted':True,'construction_only':True,
            'role':role,'population':population,'reader_worlds':count,'reference_worlds':count,'construction_attempts':len(attempts),
            'distinct_source_worlds':len(seen),'distinct_headers_across_samples':plan['distinct_headers_across_samples'],
            'wall_seconds':time.monotonic()-started,'parent_cpu_seconds':time.process_time()-cpu,
            'outputs':closure([directory/p for p in ('IDENTITY.json','WORLD_PLAN.json','ATTEMPTS.json','units')]),
            'scientific_admission':False,'disposition':'DESCRIPTIVE'}
        freeze(directory/'COMPLETE.json',complete)
        return complete


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--role',choices=ROLES,required=True);p.add_argument('--population',choices=POPULATIONS,required=True)
    a=p.parse_args();prepare(a.output,role=a.role,population=a.population)
