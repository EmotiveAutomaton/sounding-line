"""D7.h1 full human consumer and generated-response cost admission.

DESIGN CHECK: LESSONS3-5/CONTROLS1-7 reread 2026-11-04. Known NULL,
nuisance and signed worlds reproduce the original calibration consumer exactly.
Missing/altered reference, failed calibration or incomplete fits refuse before
human fitting. Native/cost outputs never stand in for a human result.
"""
from pathlib import Path
from collections import Counter
import math
import time
import numpy as np
from threadpoolctl import threadpool_limits
from runners.stage14.common import read,filehash,atomic,digest
from . import week4_d7_calibration as c
from . import week4_d7_conditioned_support as h
from . import week3_d7_cost as cost
from .batch_runtime import check_files
from .timing_p6 import write_equal

SOURCE_KEYS={'source_complete','source_rows','source_landing'}


def configuration(mode):
    if mode not in ('constructed','cost','full'):raise ValueError('Unknown mode')
    return dict(card='D7.h1-human',mode=mode,seed=20261026,
        references=200 if mode=='full' else 2,bootstrap_draws=20 if mode=='constructed' else 2000)


def authenticated(path,module,config):
    root=Path(path).resolve().parent;completion=read(root/'COMPLETE.json');plan=read(root/'PLAN.json')
    if completion['status']!='COMPLETE' or not completion['fresh_process_verified']:
        raise ValueError('Dependency incomplete')
    if plan['module']!=module or plan['config']!=config:raise ValueError('Wrong dependency producer')
    check_files(plan['pins'])
    for name,sha in completion['outputs'].items():
        if filehash(root/name)!=sha:raise ValueError('Dependency output changed')
    return root,read(root/'output/SUMMARY.json')


def validate_bank(rows,bank):
    groups,excluded=c.support(rows);roster=sorted(groups)
    if excluded or not bank['complete'] or bank['draws']!=200 or len(bank['accepted'])!=200:
        raise ValueError('Incomplete conditional bank')
    if bank['metadata_sha256']!=digest(h.metadata(rows)) or bank['writers']!=roster:
        raise ValueError('Conditional bank binds different cohort')
    if bank['law']!='uniform-session-labels-within-prompt-conditional-on-original-support-h1':
        raise ValueError('Wrong conditional law')
    if bank['maximum_proposals']!=2000 or bank['seed']!=20261026:raise ValueError('Wrong proposal contract')
    # Rebuild the entire selection law from metadata; no trust in accepted-only output.
    if h.bank(rows)!=bank:raise ValueError('Conditional proposal law differs')
    return bank['accepted']


def generated(rows,seed):
    rng=np.random.default_rng(seed);result=[]
    for r in rows:
        accepted=bool(rng.integers(2))
        logtime=2+.3*accepted+.4*(r['mean_novelty']-.5)+rng.normal(0,.08)
        result.append(dict(r,accepted=accepted,dwell_seconds=math.expm1(max(0,logtime))))
    return result


def source(inputs,full=False):
    expected=SOURCE_KEYS|{'support_completion'}|({'calibration_completion','cost_completion'} if full else set())
    if set(inputs)!=expected:raise ValueError('Exact D7.h1 dependency bundle required')
    original={k:inputs[k] for k in SOURCE_KEYS};rows=cost.source(original)
    root,s=authenticated(inputs['support_completion'],h.__name__,h.configuration('full'))
    if read(root/'PLAN.json')['inputs']!=original:raise ValueError('Support used different source')
    if not s['bank_complete'] or not s['calibration_bank_parity'] or s['calibration_worlds']!=30:
        raise ValueError('Complete conditional support and parity required')
    groups,excluded=c.support(rows)
    if len(groups)!=38 or len(groups)+len(excluded)!=61:raise ValueError('Original population changed')
    cohort=[r for w in sorted(groups) for r in groups[w]]
    bank=read(root/'output/PRIVATE_CONDITIONAL_SUPPORT.json')['bank']
    assignments=validate_bank(cohort,bank)
    if full:
        _,cal=authenticated(inputs['calibration_completion'],c.__name__,c.configuration('calibration'))
        if not cal['calibration'].get('passes'):raise ValueError('Complete calibration did not pass')
        costroot,_=authenticated(inputs['cost_completion'],__name__,configuration('cost'))
        if read(costroot/'PLAN.json')['inputs']!={k:v for k,v in inputs.items() if k not in ('calibration_completion','cost_completion')}:
            raise ValueError('Cost used different source or support')
    return cohort,assignments,excluded


def cost_assignments(rows,assignments):
    counts=Counter(r['session'] for r in rows)
    def size(a):
        sums=Counter()
        for session,writer in a['assignment'].items():sums[writer]+=counts[session]
        return -max(sums.values()),a['draw']
    return sorted(assignments,key=size)[:2]


def forecast(times):
    setup=max(r['setup_cpu_seconds'] for r in times)
    unit=6*(setup+max(r['max_complete_writer_cpu_seconds'] for r in times)*38*401+60)
    whole=6*(setup+max(r['fitting_cpu_seconds'] for r in times)*(401/5))
    return dict(full_cpu_seconds=max(unit,whole),complete_writer_forecast=unit,
        whole_implementation_forecast=whole,writers=38,reference_arms=401,
        both_passes=True,safety_factor=3,human_scored=False)


def analyze(output,label,rows,assignments,config,verifying=False):
    output=Path(output);groups,excluded=c.support(rows)
    if excluded or len(assignments)!=config['references']:raise ValueError('Fixed complete reference support required')
    for a in assignments:
        other,bad=c.support(c.reassigned(rows,a['assignment']))
        if bad or sorted(other)!=sorted(groups):raise ValueError('Reference roster changed before fits')
    worst=0.
    def fitted(name,g,reference=None):
        nonlocal worst
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():
            raise InterruptedError('D7.h1 fitted-arm boundary yield')
        path=output/(label+'-'+name+'.json')
        if path.exists() and not verifying:return read(path)
        value,t=c.fits(g,reference,config['seed']);worst=max(worst,t)
        if verifying:
            if read(path)!=value:raise ValueError('Complete fitted-arm replay differs')
        else:write_equal(path,value)
        return value
    real=fitted('real',groups);joint=[];fake=[]
    for index,a in enumerate(assignments):
        joint.append(fitted(f'joint-{index}',groups,index))
        other,_=c.support(c.reassigned(rows,a['assignment']))
        fake.append(fitted(f'fake-{index}',other))
        atomic(output/'PROGRESS.json',dict(phase='verify' if verifying else 'execute',label=label,
            references_done=index+1,references_total=len(assignments)))
    summary=c.summarize(real,joint,fake,config['bootstrap_draws'],config['seed'])
    return dict(summaries=summary,primary=c.PRIMARY,writers=len(groups),observations=len(rows),
        bootstrap_draws=config['bootstrap_draws'],joint_draws=len(joint),conditional_draws=len(fake),
        fit_bank_sha256=digest(dict(real=real,joint=joint,fake=fake)),causal_claim=False),worst


def calculate(output,inputs,config,verifying=False):
    if config!=configuration(config.get('mode')):raise ValueError('Frozen D7.h1 consumer contract required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);start=time.process_time()
    binding=dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()})
    if verifying:
        if read(output/'BINDING.json')!=binding:raise ValueError('Binding changed')
    else:write_equal(output/'BINDING.json',binding)
    mode=config['mode'];tasks=[];exclusions={}
    if mode=='constructed':
        if inputs:raise ValueError('No human inputs in native fixture')
        for regime in ('null','nuisance','signed'):
            rows,_=c.world(regime,config['seed'],6)
            assignments=h.bank(rows,draws=2)['accepted'];tasks.append((regime,rows,assignments))
    else:
        rows,assignments,exclusions=source(inputs,mode=='full')
        if mode=='cost':rows=generated(rows,config['seed']);assignments=cost_assignments(rows,assignments)
        tasks=[('human' if mode=='full' else 'generated',rows,assignments)]
    setup=time.process_time()-start;results={};worst=0.
    for label,rows,assignments in tasks:
        result,t=analyze(output,label,rows,assignments,config,verifying);worst=max(worst,t)
        if mode=='constructed':
            old,_=c.analyze(rows,dict(permutations=2,bootstrap_draws=20),config['seed'])
            if result['summaries']!=old['summaries'] or result['fit_bank_sha256']!=digest(old['private_fit_receipts']):
                raise ValueError('Original constructed consumer parity failed')
        results[label]=result
    path=output/'PRIVATE_ANALYSIS.json'
    record=dict(results=results,original_exclusions=exclusions)
    if verifying:
        if read(path)!=record:raise ValueError('Complete consumer replay differs')
    else:write_equal(path,record)
    summary=dict(card=config['card'],mode=mode,complete=True,primary=c.PRIMARY,
        human_scored=mode=='full',scientific_admission=mode=='full',
        native_consumer_parity=mode=='constructed',analysis_sha256=filehash(path),
        settings=6,bootstrap_draws=config['bootstrap_draws'],references_per_family=config['references'],
        conditional_law='D7.h1',scope='supported writers; completed duration only; descriptive')
    elapsed=time.process_time()-start
    timing=dict(cpu_seconds=elapsed,setup_cpu_seconds=setup,fitting_cpu_seconds=elapsed-setup,
                max_complete_writer_cpu_seconds=worst)
    write_equal(output/('VERIFY_TIMING.json' if verifying else 'EXECUTE_TIMING.json'),timing)
    if verifying:
        if read(output/'SUMMARY.json')!=summary:raise ValueError('Consumer summary differs')
        if mode=='cost':
            times=[read(output/n) for n in ('EXECUTE_TIMING.json','VERIFY_TIMING.json')]
            write_equal(output/'FORECAST.json',forecast(times))
        return dict(verified=True,full_fresh_fit_replay=True,complete_banks=mode=='full')
    write_equal(output/'SUMMARY.json',summary);return summary


def execute(output,inputs,config):
    with threadpool_limits(limits=2):return calculate(output,inputs,config)


def verify(output,inputs,config):
    with threadpool_limits(limits=2):return calculate(output,inputs,config,True)
