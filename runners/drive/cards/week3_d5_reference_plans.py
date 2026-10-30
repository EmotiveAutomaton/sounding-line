"""D5 supported-comparison reference plans; no identification outcomes.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 reread 2026-10-29.
NULL and ALTERNATIVE keep the fixed roster, prompt counts and source support.
Every shuffled profile is rebuilt; missing candidates invalidate that draw,
never a smaller successful-only bank. Role labels preserve donor disjointness;
share shuffles preserve each writer's full multiset. No score is computed.
"""
from collections import Counter, defaultdict
from pathlib import Path
import time
import numpy as np
from runners.stage14.common import read, filehash, freeze, atomic
from .timing_p6 import gzread, gzip_equal
from .timing_pmap_stats import split_sessions
from . import week3_d5_gallery_support as source

CHANNELS=('final','human32','human64','human128','human256','human512','human1024','selection','rhythm','process')
CONFIG=dict(card='D5-reference-plans',schema=1,mode='full',sessions=1399,writers=61,
            candidates=45,permutations=1000,share_permutations=200,seed=20261026)
CONSTRUCTED=dict(CONFIG,mode='constructed',sessions=48,writers=6,candidates=6,permutations=24,share_permutations=12)


def load(inputs,config):
    if config not in (CONFIG,CONSTRUCTED):raise ValueError('Frozen reference configuration required')
    if config==CONSTRUCTED:
        if set(inputs)!={'fixture'}:raise ValueError('Constructed fixture required')
        p=Path(inputs['fixture']);v=read(p)
        if v.get('constructed') is not True:raise ValueError('Constructed scope required')
        return v['rows'],v['writer_folds'],{str(p.resolve()):filehash(p)}
    if set(inputs)!={'support_complete'}:raise ValueError('Complete support source required')
    terminal=Path(inputs['support_complete']).resolve();root=terminal.parent;c=read(terminal);pins={str(terminal):filehash(terminal)}
    def artifact(name):
        p=(root/name).resolve();p.relative_to(root);h=filehash(p)
        if c.get('status')!='COMPLETE' or not c.get('fresh_process_verified') or c['outputs'].get(name)!=h:raise ValueError('Completed source bytes differ')
        pins[str(p)]=h;return gzread(p) if p.suffix=='.gz' else read(p)
    plan=artifact('PLAN.json')
    if plan['module']!=source.__name__ or plan['config']!=source.CONFIG:raise ValueError('Wrong support producer')
    detail=artifact('output/GALLERIES.json.gz');binding=artifact('output/BINDING.json')
    for p,h in binding['inputs'].items():
        if filehash(p)!=h:raise ValueError('Source binding changed')
        pins[p]=h
    return detail['rows'],detail['writer_folds'],pins


def layout(rows,roster,assignment=None):
    halves,excluded=split_sessions(rows,assignment);missing={};probes={}
    for channel in CHANNELS:
        components=source.COMPONENTS[channel];bad=[];counts=Counter();writers=Counter();varied=0
        for w in roster:
            parts=halves.get(w,[[],[]])
            if not all(all(any(r['support'][c] for r in part) for c in components) for part in parts):bad.append(w)
            eligible=[r for r in parts[0] if all(r['support'][c] for c in components)]
            counts.update(r['share_bin'] for r in eligible);bins={r['share_bin'] for r in eligible}
            writers.update(bins);varied+=len(bins-{'missing'})>=2
        missing[channel]=bad
        probes[channel]=dict(sessions=sum(counts.values()),bins=dict(sorted(counts.items())),writers_per_bin=dict(sorted(writers.items())),writers_with_multiple_bins=varied)
    return dict(missing_profile_writers=missing,probe_support=probes,split_excluded=excluded,
                halves={w:[[r['session'] for r in part] for part in halves.get(w,[[],[]])] for w in roster})


def label_draw(rows,folds,index,seed,roles):
    blocks=defaultdict(list)
    for i,r in enumerate(rows):blocks[(r['prompt'],folds[r['writer']] if roles else -1)].append(i)
    rng=np.random.default_rng(np.random.SeedSequence([seed,index,1 if roles else 0]));result={}
    for key,indices in sorted(blocks.items()):
        values=[rows[i]['writer'] for i in indices]
        for i,w in zip(indices,rng.permutation(values)):result[rows[i]['session']]=str(w)
    return result


def share_draw(rows,index,seed):
    blocks=defaultdict(list)
    for i,r in enumerate(rows):blocks[r['writer']].append(i)
    result=[None]*len(rows);rng=np.random.default_rng(np.random.SeedSequence([seed,index,2]))
    for w,indices in sorted(blocks.items()):
        for i,b in zip(indices,rng.permutation([rows[i]['share_bin'] for i in indices])):result[i]=str(b)
    return result


def compute(output,inputs,config,verification=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);start=time.process_time()
    rows,folds,pins=load(inputs,config);rows=sorted(rows,key=lambda r:r['session']);writers=sorted({r['writer'] for r in rows})
    if len(rows)!=config['sessions'] or len({r['session'] for r in rows})!=len(rows) or len(writers)!=config['writers']:raise ValueError('Complete source census differs')
    if set(folds)!=set(writers) or set(folds.values())!={0,1,2}:raise ValueError('Complete frozen donor roles required')
    for r in rows:
        if source.share_bin(r['model_share'])!=r['share_bin'] or any(type(v) is not bool for v in r['support'].values()):raise ValueError('Invalid source support')
    halves,_=split_sessions(rows);roster=sorted(halves)
    if len(roster)!=config['candidates']:raise ValueError('Fixed candidate roster differs')
    real=layout(rows,roster);total=2*config['permutations']+config['share_permutations'];done=0;invalid={};windex={w:i for i,w in enumerate(writers)}
    def retain(name,value):
        p=output/name
        if verification:
            if (gzread(p) if p.suffix=='.gz' else read(p))!=value:raise ValueError('Fresh reference-plan replay differs')
        elif p.suffix=='.gz':gzip_equal(p,value)
        else:freeze(p,value)
    retain('BINDING.json',dict(config=config,inputs=pins))
    retain('SOURCE.json.gz',dict(rows=rows,writer_folds=folds,original_writers=writers,candidates=roster))
    retain('REAL_SUPPORT.json',real)
    def checkpoint():
        nonlocal done
        done+=1
        if done%12==0 or done==total:atomic(output/'PROGRESS.json',dict(phase='verify' if verification else 'execute',done=done,total=total))
        if (output/'YIELD_REQUEST.json').exists() or (output.parent/'STOP').exists():raise InterruptedError('Reference-plan boundary yield')
        tenth=max(1,config['permutations']//10)
        if not verification and done==tenth and not (output/'FIRST_TENTH.json').exists():
            freeze(output/'FIRST_TENTH.json',dict(projected_cpu_seconds=max(.001,4*(time.process_time()-start)*total/done),scope='Both complete reference-plan passes times two; not scientific-scoring admission'))
    for roles,name in [(False,'literal'),(True,'independent')]:
        counts={ch:0 for ch in CHANNELS};assignments=[];missing=[]
        for i in range(config['permutations']):
            assignment=label_draw(rows,folds,i,config['seed'],roles);state=layout(rows,roster,assignment)
            bad={ch:state['missing_profile_writers'][ch] for ch in CHANNELS if state['missing_profile_writers'][ch]}
            for ch in bad:counts[ch]+=1
            assignments.append([windex[assignment[r['session']]] for r in rows]);missing.append(bad);checkpoint()
        retain(name+'-BANK.json.gz',dict(writer_order=writers,sessions=[r['session'] for r in rows],assignments=assignments,missing_profile_writers=missing))
        invalid[name]=counts
    shares=[]
    for i in range(config['share_permutations']):shares.append(share_draw(rows,i,config['seed']));checkpoint()
    retain('SHARE_BANK.json.gz',dict(sessions=[r['session'] for r in rows],bins=shares))
    retain('SUMMARY.json',dict(sessions=len(rows),writers=len(writers),candidate_writers=len(roster),all_sessions_retained=True,source_only=True,effect_computed=False,scientific_admission=False,
        invalid_reference_draws=invalid,permutations_per_label_bank=config['permutations'],within_writer_share_permutations=config['share_permutations'],real_profile_missing={ch:len(v) for ch,v in real['missing_profile_writers'].items()},
        primary='human128; prospectively selected by full fixed-roster profile support',scope='Necessary fixed-gallery reference support only; no identification or slope computed'))
    return dict(verified=True,full_fresh_reference_replay=True,source_only=True) if verification else dict(status='complete',source_only=True)


def execute(output,inputs,config):
    try:return compute(output,inputs,config)
    except InterruptedError:return dict(status='yielded',source_only=True)
def verify(output,inputs,config):return compute(output,inputs,config,True)
