"""PP1.ic fixed constructed sensitivity calibration; no human data.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 6 read November 3. Known null has
zero latent boundary contrast; planted worlds raise middle probability.
Original interval above zero is positive, below zero negative, otherwise
not_detected. Numeric failure refuses the whole world, never drops a draw.
The six fixed worlds are conditional calibrations, not a power estimate.
"""
from pathlib import Path
import math
import time
import numpy as np
from threadpoolctl import threadpool_limits
from . import week3_pause_model as model
from .timing_p6 import write_equal, gzip_equal, gzread
from runners.stage14.common import atomic, read

SEEDS=(202611031,202611032)
DOSES=(0.,.1,.3)
CONFIG=dict(mode='calibration',bootstrap_draws=2000,seed=20261026)


def configuration(config):
    if set(config)!=set(CONFIG) or config['seed']!=20261026:
        raise ValueError('Frozen PP1.ic configuration required')
    expected={'calibration':2000,'cost':5,'validation':2}
    if config['mode'] not in expected or type(config['bootstrap_draws']) is not int or config['bootstrap_draws']!=expected[config['mode']]:
        raise ValueError('Complete draw count required for each mode')


def world(seed,dose):
    if seed not in SEEDS or dose not in DOSES:raise ValueError('Frozen world grid required')
    rng=np.random.default_rng(seed);rows=[];counts={loc:[0,0] for loc in model.LOCATIONS}
    for w in range(20):
        for p in range(4):
            intervals=[]
            for li,loc in enumerate(model.LOCATIONS):
                middle=(.08,.2,.2+dose,.75,.5)[li]
                for k in range(8):
                    u=float(rng.random());component=2 if u>=.95 else 1 if u< middle else 0
                    mechanical=bool(rng.random()<(.9 if loc=='before_sentence' else .25))
                    logtime=(-1.9,.5,3.2)[component]+rng.normal(0,.18)+.08*w+.03*p+.4*mechanical
                    ordinal=li*8+k
                    intervals.append(dict(ordinal=ordinal,previous_ordinal=ordinal-1,seconds=ordinal+float(rng.uniform(0,.9)),interval_seconds=math.exp(logtime),location=loc,next_upper_or_punctuation=mechanical,mechanical_training=loc in {'within_word','before_word'},target='deletion' if loc=='before_revision' else 'single_character_insert'))
                    counts[loc][0]+=int(component==1);counts[loc][1]+=1
            rows.append(dict(session=f'w{w}-p{p}',writer=f'w{w}',prompt=f'p{p}',timestamp=1000+p*100+w,genre='constructed',session_order=p,intervals=intervals,source_exclusions={},separator_intervals=0))
    truth=dict(seed=seed,dose=dose,writers=20,sessions=80,intervals=3200,latent_middle_counts=counts,realized_middle_contrast=counts['before_sentence'][0]/counts['before_sentence'][1]-counts['before_word'][0]/counts['before_word'][1])
    return rows,truth


def classify(lo,hi):
    return 'positive' if lo>0 else 'negative' if hi<0 else 'not_detected'


def compute(output,config):
    bank=[];timings=[];results=[]
    for seed in SEEDS:
        for dose in DOSES:
            rows,truth=world(seed,dose);t=time.process_time();observed=model.model(rows);times=[time.process_time()-t]
            rng=np.random.default_rng(config['seed']);draws=[]
            for index in range(config['bootstrap_draws']):
                selected=rng.integers(0,20,20);t=time.process_time()
                fitted=model.model(model.writer_resample(rows,selected));times.append(time.process_time()-t)
                draws.append(fitted['contrasts'])
                atomic(Path(output)/'PROGRESS.json',dict(seed=seed,dose=dose,done=index+1,total=config['bootstrap_draws']))
                if (Path(output).parent/'STOP').exists() or (Path(output)/'YIELD_REQUEST.json').exists():raise InterruptedError('PP1.ic yield at complete fit')
            timings.append(dict(seed=seed,dose=dose,fit_cpu_seconds=times))
            if config['mode']!='cost':
                lo,hi=np.quantile([d['sentence_minus_word'] for d in draws],[.025,.975])
                results.append(dict(**truth,effect=observed['contrasts']['sentence_minus_word'],ci_low=float(lo),ci_high=float(hi),state=classify(lo,hi),draws=len(draws)))
                bank.append(dict(seed=seed,dose=dose,draws=draws))
    if config['mode']=='cost':
        forecast=2*sum(max(t['fit_cpu_seconds'])*2001 for t in timings)+60
        return dict(card='PP1.ic-cost',scientific_admission=False,projected_execute_and_replay_cpu_seconds=forecast,timings=timings),None
    return dict(card='PP1.ic',scientific_admission=False,constructed=True,full_calibration=config['mode']=='calibration',worlds=results,scope='Six fixed constructed worlds; no population power or human sensitivity claim'),bank


def run(output,inputs,config,verification=False):
    configuration(config)
    if inputs:raise ValueError('Constructed PP1.ic accepts no external data')
    with threadpool_limits(limits=1):result,bank=compute(output,config)
    output=Path(output)
    if verification:
        if config['mode']=='cost':
            original=read(output/'RESULT.json')
            if original['card']!='PP1.ic-cost' or len(original['timings'])!=6 or original['projected_execute_and_replay_cpu_seconds']<=0:raise ValueError('Invalid cost receipt')
            atomic(output/'VERIFY_COST.json',result)
        elif read(output/'RESULT.json')!=result or gzread(output/'BOOTSTRAPS.json.gz')!=bank:raise ValueError('PP1.ic reconstruction differs')
        return dict(verified=True,full_replay=True,constructed=True)
    write_equal(output/'RESULT.json',result)
    if bank is not None:gzip_equal(output/'BOOTSTRAPS.json.gz',bank)
    return result


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
