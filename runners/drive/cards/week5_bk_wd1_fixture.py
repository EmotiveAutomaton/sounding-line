"""Native original-solver block and complete-count signed summary checks."""
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from . import week5_bk_wd1 as card
from .timing_census import read
from .timing_p6 import write_equal,progress


def profiles(a,b,criterion=None):
    criterion=np.zeros(len(a)) if criterion is None else criterion
    return dict(profiles={str(i):dict(halves=[dict(sensitivity=float(a[i]),criterion=float(criterion[i])),
                                            dict(sensitivity=float(b[i]),criterion=float(criterion[i]))],
                                    thirds=[dict(sensitivity=float(a[i]),criterion=float(criterion[i])),
                                            dict(sensitivity=float(b[i]),criterion=float(criterion[i]))]) for i in range(len(a))},excluded={})


def signed_summaries():
    rng=np.random.default_rng(73);a=np.linspace(-1,1,12);b=np.sin(np.arange(12));b-=b.mean();b-=a*(a@b)/(a@a)
    controls=[profiles(rng.normal(size=12),rng.normal(size=12)) for _ in range(1000)]
    results={}
    for name,second,criterion in [('null',b,None),('criterion',b,a),('stable',a+.01*b,None),('reversed',-a+.01*b,None)]:
        results[name]=card.original.summarize(profiles(a,second,criterion),controls,2000,20261104)
    if any(results[k]['state']=='positive' for k in ('null','criterion')):raise ValueError('Known null acquired sensitivity recurrence')
    if results['stable']['state']!='positive' or results['reversed']['state']!='negative':raise ValueError('Signed recurrence not recovered')
    if results['criterion']['criterion_reliability_secondary']<.99999:raise ValueError('Criterion companion lost')
    if any(r['bootstrap_draws']!=2000 or r['permutation_draws']!=1000 for r in results.values()):raise ValueError('Full uncertainty coverage differs')
    return results


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Fixture takes no human input')
    root=Path(output);root.mkdir(parents=True,exist_ok=True)
    bundle=card.make_world('stable',0,card.original.configuration('constructed'));records=[]
    with threadpool_limits(limits=2):
        for index in range(5):
            value=card.fit_one(bundle,index);record=dict(index=index,status='complete',value=value,binding=card.digest(bundle))
            path=root/f'fit-{index:04d}.json'
            if verifying:
                if read(path)!=record:raise ValueError('Fresh actual slower-solver fit differs')
            else:write_equal(path,record)
            records.append(record);progress(root/'PROGRESS.json',dict(phase='verify' if verifying else 'execute',fits=index+1,total=5))
        a=card.world_result(bundle,[dict(binding=card.digest(bundle),records=records)])
        b=card.world_result(bundle,[dict(binding=card.digest(bundle),records=records[:2]),dict(binding=card.digest(bundle),records=records[2:])])
        if a!=b:raise ValueError('Block partition changed original statistic')
        summaries=signed_summaries()
    receipt=dict(fixture_only=True,actual_original_solver_fits=5,block_partition_invariant=True,
                 complete_signed_summary_draws=2000,complete_reference_profiles=1000,
                 generated_summary_controls_not_full_calibration=True,full_thirty_world_gate_still_required=True)
    for name,value in [('WORLD_RESULT.json',a),('SIGNED_SUMMARIES.json',summaries),('FIXTURE.json',receipt)]:
        if verifying:
            if read(root/name)!=value:raise ValueError('Complete fixture reduction differs')
        else:write_equal(root/name,value)
    return dict(verified=True,complete_native_handler_replay=True) if verifying else dict(status='complete',fixture_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)

if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
