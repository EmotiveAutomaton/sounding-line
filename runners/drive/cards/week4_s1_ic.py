"""S1 planted-template calibration through exact histories and unchanged statistic.

DESIGN CHECK: LESSONS 3-5 and CONTROLS reread. Null identical/no-overlap
histories must return exact zero; planted signed template membership must keep
its sign. Stochastic nulls may reject, with finite count uncertainty retained.
The whole original positive gate is measured, never removed after a failed plant.
This construction validates template sensitivity, not psychological flow labels.
"""
from pathlib import Path
from collections import defaultdict
import time,json
import numpy as np
from threadpoolctl import threadpool_limits
from . import week4_s1_stats as stats
from .timing_census import read
from .timing_p6 import write_equal,gzip_equal,gzread,progress

DOSES=(0.,.01,.02,.05,.10,.20)
ALPHABET=tuple('token'+str(i) for i in range(150))

def configuration(mode):
    if mode not in ('constructed','timing','full'):raise ValueError('Unknown calibration scope')
    return dict(card='S1.ic',mode=mode,seed=20261102,doses=list(DOSES),seeds=20,
                writers=25,windows=80,permutations=200,bootstrap=2000)

def world(seed,dose,kind='stochastic'):
    if dose not in DOSES or kind not in ('stochastic','positive','negative','identical','empty'):raise ValueError('Unknown construction')
    rng=np.random.default_rng(seed);rows=[];proof=[];dictionary=set(ALPHABET)
    for w in range(25):
        sentences=[];seen=set()
        for i in range(80):
            for attempt in range(1000):
                sentence=rng.choice(ALPHABET,8).tolist();grams=[tuple(sentence[j:j+4]) for j in range(5)]
                if len(set(grams))==5 and not seen.intersection(grams):break
            else:raise ValueError('Unique constructed templates exhausted')
            seen.update(grams);sentences.append(sentence)
        label=np.tile([0,1],40);own_u=rng.random(80);donor_u=rng.random(80)
        own=own_u<(.4+dose*label);donor=donor_u<.4
        if kind=='positive':own=label==1;donor=np.zeros(80,bool)
        if kind=='negative':own=label==0;donor=np.zeros(80,bool)
        if kind=='identical':donor=own.copy()
        if kind=='empty':own=np.zeros(80,bool);donor=own.copy()
        filler=['outside']*8
        own_sessions=[sentences[i] if own[i] else filler for i in range(80)]
        donor_sessions=[sentences[i] if donor[i] else filler for i in range(80)]
        own_grams=stats.history_grams(own_sessions,dictionary);donor_grams=stats.history_grams(donor_sessions,dictionary)
        nuisance=rng.normal(size=(80,8))
        for i,sentence in enumerate(sentences):
            grams=[sentence[j:j+4] for j in range(5)];y=stats.recurrence(grams,own_grams,donor_grams)
            if y!=int(own[i])-int(donor[i]):raise ValueError('Unplanned template collision or membership error')
            rows.append(dict(writer=str(w),session=f'{w}-{i//40}',label=int(label[i]),nuisance=nuisance[i].tolist(),outcome=y))
        proof.append(dict(writer=str(w),own_words=sum(map(len,own_sessions)),donor_words=sum(map(len,donor_sessions)),unique_grams=len(seen),target_windows=80))
    return rows,proof

def checks():
    result={}
    for kind in ('positive','negative','identical','empty'):
        rows,proof=world(20261102,0.,kind);s,_=stats.analyze(rows)
        expected=1. if kind=='positive' else -1. if kind=='negative' else 0.
        assert abs(s['estimate']-expected)<1e-12
        if expected==0:assert s['state']=='null' and s['interval']==[0.,0.]
        if expected>0:assert s['positive_gate']
        if expected<0:assert s['interval'][1]<0 and not s['positive_gate']
        assert all(p['own_words']==p['donor_words']==640 and p['unique_grams']==400 for p in proof)
        result[kind]=True
    return result

def wilson(k,n):
    if not 0<=k<=n or n<1:raise ValueError('Invalid binomial counts')
    z=1.959963984540054;q=k/n;den=1+z*z/n
    center=(q+z*z/(2*n))/den;width=z*np.sqrt(q*(1-q)/n+z*z/(4*n*n))/den
    return [max(0.,float(center-width)),min(1.,float(center+width))]

def run(output,inputs,config,verification=False):
    if inputs or config!=configuration(config['mode']):raise ValueError('Frozen constructed scope required')
    start=time.process_time();output=Path(output)
    with threadpool_limits(limits=1):
        known=checks();records=[]
        grid=[] if config['mode']=='constructed' else [(0.,0),(.05,0),(.20,0)] if config['mode']=='timing' else [(d,j) for d in DOSES for j in range(20)]
        for index,(dose,j) in enumerate(grid):
            rows,proof=world(config['seed']+j,dose);s,private=stats.analyze(rows)
            if not s['scientific_effect_computed']:raise ValueError('Constructed support failed')
            record=dict(dose=dose,seed=config['seed']+j,summary=s,inference=private,source_proof=proof)
            path=output/'worlds'/f'd{DOSES.index(dose)}-s{j}.json.gz'
            if verification:
                if gzread(path)!=json.loads(json.dumps(record)):raise ValueError('Complete planted world replay differs')
            else:gzip_equal(path,record)
            records.append(record);progress(output/'PROGRESS.json',dict(done=index+1,total=len(grid),phase='verify' if verification else 'calibration'))
        curve=[]
        for dose in DOSES:
            rr=[r['summary'] for r in records if r['dose']==dose]
            if not rr:continue
            hits=sum(r['positive_gate'] for r in rr);cover=sum(r['interval'][0]<=dose<=r['interval'][1] for r in rr)
            curve.append(dict(dose=dose,worlds=len(rr),positive_gates=hits,positive_gate_fraction=hits/len(rr),positive_gate_count_interval=wilson(hits,len(rr)),interval_covers_truth=cover,
                 biased_references=sum(r['reference']['biased'] for r in rr),mean_estimate=float(np.mean([r['estimate'] for r in rr])),mean_error=float(np.mean([r['estimate']-dose for r in rr]))))
        summary=dict(known_checks=known,mode=config['mode'],worlds=len(records),curve=curve,scope='Constructed matched-length template histories and fixed complete statistical rule; no human psychological inference.',claim_upgrade=False,descendants=False)
    if verification:
        if read(output/'SUMMARY.json')!=summary:raise ValueError('Calibration summary replay differs')
    else:
        write_equal(output/'SUMMARY.json',summary)
        write_equal(output/'TIMING.json',dict(cpu_seconds=time.process_time()-start,full_forecast_cpu_seconds=3*(time.process_time()-start)*120/max(1,len(records))))
    return dict(verified=True,complete_source_replay=True,complete_statistical_replay=True) if verification else dict(status='complete')

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
