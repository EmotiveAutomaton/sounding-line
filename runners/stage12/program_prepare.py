"""Manual translation of the curator-approved 22 cards, not a research generator.

DESIGN CHECK: LESSONS 3-5. NULL: missing sources stay blocked and duplicate
exposure is not fresh evidence. ALTERNATIVE: all prospective rosters, reserved
replications and fixed contrasts bind before dispatch. No cloud, fit, outcome
selection or reset of the original week's clocks/charges is permitted.
"""
import argparse
from collections import defaultdict
from copy import deepcopy
import itertools
from pathlib import Path
import time
from .common import REPO,RAW,read,freeze,digest,filehash,charges,own_cpu,limit_process
from . import program_world as W, program_queries as Q, program_sources as S
from .canary import PROFILE,compile_inputs
from .output_interface import VERSION,adapt
from .local_api import request

NAME='local-program-20260923-v2'
PROGRAM=RAW/NAME
ORDER=['LP01','LP02','LP04','LP06','LP15','LP05','LP07','LP08','LP09','LP10','LP11','LP12','LP13','LP14','LP16','LP17','LP18','LP20-Qwen','LP20-Smol','LP21-revision','LP21-query']
CAPS={'LP01':384,'LP02':768,'LP04':2688,'LP05':1152,'LP06':640,'LP07':1408,'LP08':768,'LP09':864,'LP10':1664,'LP11':1536,'LP12':768,'LP13':768,'LP14':256,'LP15':384,'LP16':1440,'LP17':2000,'LP18':384,'LP20-Qwen':432,'LP20-Smol':432,'LP21-revision':2688,'LP21-query':1408}


def hf_source(name):
    cache=Path.home()/'.cache/huggingface/hub'/('models--'+name.replace('/','--'))
    revision=(cache/'refs/main').read_text().strip();root=cache/'snapshots'/revision
    if not root.is_dir():raise ValueError('cached model snapshot absent')
    paths=[p for p in root.iterdir() if p.is_file() and p.suffix in ('.json','.safetensors','.model','.txt')]
    if not any(p.suffix=='.safetensors' for p in paths):raise ValueError('complete local weights absent')
    return dict(hf_model=name,model_path=str(root),model_revision=revision,model_files={str(p):filehash(p) for p in paths})


def hf_rows(family,units):
    rows=[]
    for i in range(48):
        label=i%4;u=dict(unit=family+'-admit-'+str(i),cluster=family+'-admit-'+str(i))
        order=[2,0,3,1] if i%2 else list(range(4));q=[float(j==label) for j in range(4)]
        text='Known-answer interface admission. The verified answer is '+W.W.LETTERS[label]+'. No other label is possible. Return probabilities in order '+','.join(W.W.LETTERS[j] for j in order)+'.'
        rows.append(W.row(family,u,'admission',text,q,'account' if i//4%2 else 'direct',development=True,label_order=order))
    for u in units:
        before=W.target(u,u['history'][:1]);after=W.target(u,u['history'][:8]);initial=None
        for condition in ('canonical','inverted','fresh','saved','duplicate','independent'):
            q=before;order=[2,0,3,1] if condition=='inverted' else list(range(4))
            text=W.question(u)+'\nCopy this supplied initial answer exactly: '+str([before[j] for j in order])+'. Output order '+','.join(W.W.LETTERS[j] for j in order)+'.'
            if condition in ('fresh','saved'):text=W.question(u)+'\nHistory:\n'+W.evidence(u['history'][:8]);q=after
            if condition=='duplicate':text=W.question(u)+'\n'+W.evidence(u['history'][:1])+'\nDuplicate report of the SAME event:\n'+W.evidence(u['history'][:1])
            if condition=='independent':text=W.question(u)+'\n'+W.evidence(u['history'][:2]);q=W.target(u,u['history'][:2])
            r=W.row(family,u,condition,text,q,label_order=order,saved_reply=initial if condition=='saved' else None)
            if condition=='canonical':initial=r['id']
            rows.append(r)
    return rows


def compile_all(raw=PROGRAM):
    raw=Path(raw);limit_process();start=own_cpu()
    # Freeze reserves before exploration and explicitly share discovery parents.
    pool=W.roster(20000,64);donors=W.roster(50000,64,excluded=[u['cluster'] for u in pool])
    reserve_revision=W.roster(60000,64,excluded=[u['cluster'] for u in pool+donors])
    reserve_query=W.roster(70000,64,excluded=[u['cluster'] for u in pool+donors+reserve_revision])
    freeze(raw/'inputs/MAKER_ROSTERS.json',dict(discovery=pool,donors=donors,reserved_revision=reserve_revision,reserved_query=reserve_query))
    studies={};metadata={}
    for f,n in [('LP01',64),('LP02',64),('LP04',64),('LP05',32),('LP06',64),('LP09',48),('LP10',64),('LP11',64),('LP12',64)]:
        studies[f]=W.static_rows(f,pool[:n],donors=donors)
    studies['LP07']=Q.slots('LP07',pool);studies['LP08']=Q.stopping(pool)
    studies['LP13']=W.twin_rows(W.twins())
    studies['LP14'],metadata['native']=S.native(RAW/'inputs/ghost-source-v1')
    studies['LP15'],metadata['ARIES']=S.aries(RAW/'inputs/aries-v1',raw/'inputs/ARIES-compile')
    studies['LP16'],metadata['CoAuthor']=S.coauthor()
    studies['LP17'],metadata['ScholaWrite']=S.scholawrite()
    studies['LP18'],metadata['realization']=S.realization()
    models={}
    for family,name in [('LP20-Qwen','Qwen/Qwen2.5-1.5B-Instruct'),('LP20-Smol','HuggingFaceTB/SmolLM2-1.7B-Instruct')]:
        models[family]=hf_source(name);studies[family]=hf_rows(family,pool)
    studies['LP21-revision']=W.static_rows('LP21-revision',reserve_revision)
    studies['LP21-query']=Q.slots('LP21-query',reserve_query)
    for family,rows in studies.items():
        W.validate_rows(rows)
        if len(rows)>CAPS[family]:raise ValueError('approved family call cap exceeded')
        for r in rows:
            if not r.get('dynamic'):adapt(request(r['text'],r['n'],r['call_class']),VERSION)
        freeze(raw/'inputs'/(family+'.json'),rows)
    counts={f:len(rows) for f,rows in studies.items()}
    if sum(counts.values())>23600-768:raise ValueError('whole program cap exceeded')
    source_paths=[REPO/'docs/design/STAGE12_LOCAL_RESEARCH_PROGRAM.md',REPO/'docs/design/STAGE12_LOCAL_RESEARCH_SOURCES.md',RAW/'jobs/S12-population-v1/POPULATION.json',RAW/'jobs/S12-population-v1/SOURCE_METADATA.json',REPO/'corpora/g159_rebuild/realization_audit.json']
    source_pins={str(p):filehash(p) for p in source_paths}
    manifest=dict(status='complete',kind='infrastructure',counts=counts,calls=sum(counts.values()),approved_cap=23600,conditional_unavailable_calls=768,models=models,metadata=metadata,source_pins=source_pins,
        shared_discovery_histories=64,reserved_histories=128,new_fits=0,paid_calls=0,controls=dict(reserved_before_outcomes=True,source_bound=True,no_replacement_native_mechanism=True,private_evaluators=True))
    freeze(raw/'inputs/CENSUS.json',manifest)
    freeze(raw/'charges/source-compilation.json',dict(cpu_seconds=own_cpu()-start,gpu_seconds=0,diagnostic_gpu_seconds=0,state='complete'))
    return manifest


def build(raw=PROGRAM):
    from .freeze_plan import build as freeze_plan
    raw=Path(raw);census=read(raw/'inputs/CENSUS.json');profile=dict(PROFILE,output=2048)
    # Explicit later commission, not a reset of the old week ledger.
    freeze(raw/'CONTRACT.json',dict(T0='2026-09-24T03:50:00+00:00',reporting='2026-09-26T03:50:00+00:00',deadline='2026-09-26T03:50:00+00:00',
        authority='September 23 approval of all local program proposals in Gear 2 for two days, includes setup',gear=2,
        gpu_service_seconds=172800,cpu_process_seconds=129600,diagnostic_gpu_seconds=14400,paid_dispatch_dollars=0,new_fits=0,delegation=False,
        original_week_contract_sha256=filehash(RAW/'CONTRACT.json'),original_week_charges_at_freeze=charges(RAW),
        accounting='separate newly commissioned local envelope; four CPU/GPU hours protected by unchanged common admission; original week unchanged; diagnostic time is included in GPU total'))
    freeze(raw/'charges/operator-setup-bound.json',dict(cpu_seconds=1800,gpu_seconds=0,diagnostic_gpu_seconds=0,state='complete',basis='conservative bound for preliminary compiler/ruler inspections including two stopped redundant source scans; not measured service'))
    canary='LP-reader-admission';card=dict(id=canary,handler='local-canary',resource='gpu',question='Admit current constructed reader interface',wall_seconds=3570,cpu_seconds=1800,gpu_seconds=3570,diagnostic_gpu_seconds=3570,profile=profile,output_interface=VERSION,requests_digest=digest(compile_inputs(VERSION)),needs=[],inputs={})
    implementation=REPO/'docs/design/STAGE12_LOCAL_PROGRAM_IMPLEMENTATION.md'
    bound_inputs={str(raw/'inputs/CENSUS.json'):filehash(raw/'inputs/CENSUS.json'),str(implementation):filehash(implementation)}
    card['inputs'].update(bound_inputs)
    cards=[card];gate=str(raw/'jobs'/canary/'ADMISSION.json');ready=str((raw/'jobs'/canary/'READER_READY.json').relative_to(REPO));families={}
    for family in ORDER:
        rows=read(raw/'inputs'/(family+'.json'));hf=census['models'].get(family);dev=[r for r in rows if r.get('development')];main=[r for r in rows if not r.get('development')]
        jobs=[];extra_needs=[]
        def add(identifier,selected,admission=False):
            path=raw/'inputs/blocks'/(identifier+'.json');freeze(path,selected)
            wall=max(1800,len(selected)*45+480)
            c=dict(id=identifier,handler='program-run',resource='gpu',question='Approved '+family+' complete paired block',family=family,wall_seconds=wall,cpu_seconds=wall*(2 if hf else 1),
                gpu_seconds=wall,diagnostic_gpu_seconds=wall if admission else 0,diagnostic=admission,calls=len(selected),rows_path=str(path),rows_digest=digest(selected),
                inputs={**bound_inputs,str(path):filehash(path)},needs=([ready] if not hf else [])+list(extra_needs),admission_path=gate,profile=profile,output_interface=VERSION,admission=admission)
            if hf:c.update(hf)
            cards.append(c);jobs.append(identifier)
        if dev:
            ident=family+'-admission';add(ident,dev,True);extra_needs=[str((raw/'jobs'/ident/'READY.json').relative_to(REPO))]
        by=defaultdict(list)
        for r in main:by[r['unit']].append(r)
        batch=[];i=0
        for unit,values in by.items():
            if batch and (len(batch)+len(values)>180 or family in ('LP07','LP10','LP21-query')):
                add(family+'-'+str(i).zfill(3),batch);batch=[];i+=1
            batch.extend(values)
        if batch:add(family+'-'+str(i).zfill(3),batch)
        families[family]=jobs
        cards.append(dict(id=family+'-summary',handler='program-consume',resource='cpu',question='Whole roster analysis '+family,family=family,source_jobs=jobs,calls=len(rows),
            needs=[str((raw/'jobs'/j/'COMPLETE.json').relative_to(REPO)) for j in jobs],wall_seconds=900,cpu_seconds=900,gpu_seconds=0,inputs=dict(bound_inputs)))
    freeze(raw/'FAMILY_JOBS.json',families)
    plan=freeze_plan(NAME,cards,'queue',raw)
    return dict(plan=str(plan),cards=len(cards),calls=sum(c['calls'] for c in cards if c['handler']=='program-run'),canary_calls=11,
        study_families=list(families),conditional_native='LP19 blocked, source receipt in CENSUS.json')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['compile','freeze']);p.add_argument('--raw',type=Path,default=PROGRAM);a=p.parse_args()
    print(compile_all(a.raw) if a.action=='compile' else build(a.raw))
