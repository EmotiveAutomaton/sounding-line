"""Prepared final precision extension; selection waits for full branch landings.

DESIGN CHECK: LESSONS 3-5. NULL/ALTERNATIVE: new stochastic histories do not
create new policy laws. Only an explicitly selected complete branch may repeat;
the original ledger/deadline survives the new namespace. No automatic selection.
"""
import argparse
from datetime import datetime,timezone
from pathlib import Path
from .common import RAW,DEADLINE,MAX_GPU_SECONDS,charge_total,freeze,read,digest,source_pins
from .world import make_unit


def prepare(root=RAW):
    root=Path(root);sub=root/'seed-continuation-v1'
    for split in ['train','dev']:
        for suffix in ['public','evaluator']:freeze(sub/'fixture'/f'{split}-{suffix}.json',read(root/'fixture'/f'{split}-{suffix}.json'))
    pairs=[make_unit('test',i,seed=99112) for i in range(128)]
    for u,t in pairs:
        u['unit']='test-seed1-'+u['unit'].split('-')[-1];u['maker']='seed1-'+u['maker'];t['unit']=u['unit']
    freeze(sub/'fixture/test-public.json',[u for u,t in pairs]);freeze(sub/'fixture/test-evaluator.json',[t for u,t in pairs])
    return freeze(sub/'PLAN.json',dict(status='prepared, not selected',seed=99112,candidates=['M0','M3','M4'],units=128,
        prerequisites='all fourteen main jobs terminal and internally landed; select most decision-relevant complete branch; whole-block capacity',
        budget='all new calls and uncertainty charges go to original Stage 11.2 root; no new budget or clock',
        scope='independent generated histories under shared policy primitives, not new policy-law replication'))


def run(branch,root=RAW):
    from . import repair,local_reader,model_study
    from .consumer import run as audit
    from .views import install
    from .workflow import verify_admission,forecast
    root=Path(root);sub=root/'seed-continuation-v1'
    terminal=read(root/'queue/QUEUE-repair-v1/COMPLETE.json')
    if terminal['status']!='complete':raise ValueError('main explanatory continuations not terminal')
    main=read(root/'QUEUE-repair-v1.json')
    if terminal['manifest_sha256']!=digest(main):raise ValueError('main queue binding changed')
    if {d['id'] for d in terminal['dispositions']}!={j['id'] for j in main['jobs']} or any(d['status']!='complete' for d in terminal['dispositions']):
        raise ValueError('explanatory work remains unavailable; precision extension is premature')
    if not any(d['id']==branch+'-test' and d['status']=='complete' for d in terminal['dispositions']):raise ValueError('selected branch test unavailable')
    selection=read(sub/'SELECTION.json')
    if selection.get('branch')!=branch or selection.get('main_landings_complete') is not True:raise ValueError('explicit scientific selection and full internal landings required')
    if verify_admission(root)['admitted'] is not True:raise ValueError('gate failed')
    n=128*{'M0':24,'M3':12,'M4':7}[branch]
    rates=forecast(root,read(root/'QUEUE-repair-v1.json'))
    remaining=min(MAX_GPU_SECONDS-charge_total(root),(datetime.fromisoformat(DEADLINE)-datetime.now(timezone.utc)).total_seconds())
    if n*rates['p90']>remaining:raise ValueError('whole seed block exceeds remaining service/deadline capacity')
    prepare(root);freeze(sub/'SOURCE.json',source_pins())
    # Inherit the exact, independently replayed capability gate. It is not
    # described as a fresh admission run on the new histories.
    freeze(sub/'repair-v1/ollama-admission/COMPLETE.json',read(root/'repair-v1/ollama-admission/COMPLETE.json'))
    original=repair.call
    def charged_to_original(text,n,path,ignored_root):return original(text,n,path,root)
    repair.call=charged_to_original;install()
    try:
        repair.run(branch,'test',sub)
        result=audit(branch,'test',sub)
        return freeze(sub/'COMPLETE.json',dict(status='complete',branch=branch,audit_sha256=digest(result),selection_sha256=digest(selection),
            scope='new stochastic histories; same policy family and reused admission; original budget'))
    finally:repair.call=original


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--branch',choices=['M0','M3','M4']);a=p.parse_args()
    print(prepare()['status'] if a.prepare else run(a.branch)['status'])
