"""Counted CA5.r.h1 preference comparison, cost pilot and native validation.

DESIGN CHECK: LESSONS 3-5 / CONTROLS 1-7. Exact sparse additive null, signed
known-answer worlds, real-mask planted validation and immutable text freeze
precede unknown scores. Pilot emits timing/admission only, never a verdict.
Full item/person banks and the entire approved population cannot be reduced.
"""
from pathlib import Path
import time
import numpy as np
from . import week3_jester_preference as m
from . import week3_jester_topics_h1 as topics
from .timing_census import read, filehash
from .timing_p6 import write_equal
from .menus_io import assert_equal
from .batch_runtime import atomic


def load(inputs, config):
    if set(config) != {'mode'} or config['mode'] not in {'constructed','pilot','main'}:
        raise ValueError('frozen comparison mode required')
    if set(inputs) != m.support.INPUTS | {'topics_complete','topics_plan','topics'}:
        raise ValueError('exact authenticated comparison inputs required')
    root=Path(inputs['topics_complete']).resolve().parent
    c,p=read(inputs['topics_complete']),read(inputs['topics_plan'])
    if (Path(inputs['topics_plan']).resolve()!=root/'PLAN.json'
            or Path(inputs['topics']).resolve()!=root/'output/TOPICS.json'
            or c.get('status')!='COMPLETE' or not c.get('fresh_process_verified')
            or p.get('module')!='runners.drive.cards.week3_jester_topics_h1'
            or Path(p['inputs']['jester_texts']).resolve()!=Path(inputs['jester_texts']).resolve()):
        raise ValueError('unadmitted/mixed topic source')
    for path,h in p['pins'].items():
        if filehash(path)!=h:raise ValueError('topic input changed')
    for path,h in c['outputs'].items():
        if filehash(m.support.checked_path(root,path))!=h:raise ValueError('topic output changed')
    if c['outputs'].get('output/TOPICS.json')!=filehash(inputs['topics']):
        raise ValueError('unsealed topic features')
    features=read(inputs['topics'])
    if features != topics.build(p['inputs'],p['config']):
        raise ValueError('full text-only reconstruction differs')
    mode='constructed' if config['mode']=='constructed' else 'corpus'
    source=read(Path(inputs['source_complete']).parent/'output/RATINGS_INDEX.json')
    y,summary,bindings=m.load_ratings(inputs,dict(mode=mode,expected_rows=source['rows'] if mode=='constructed' else 50691))
    return y,np.asarray(features['weights']),summary,bindings


def known_answers():
    records={}
    for name,effect,reverse in [('positive',4.,False),('reversed',4.,True),('noise',0.,False)]:
        y,w=m.planted_world(effect=effect,reverse=reverse)
        result=m.calculate(y,w)
        records[name]=result
    if records['positive']['item']['paired_interval'][0] <= .5:
        raise ValueError('stable preference known answer failed')
    if records['reversed']['item']['paired_interval'][1] >= -.5:
        raise ValueError('reversed preference known answer failed')
    if records['noise']['state'] in {'positive','negative'}:
        raise ValueError('noise known answer false alarm')
    return records


def mask_calibration(mask, weights):
    """Only actual exposure and text coordinates; no rating values enter."""
    halves=[m.Half(mask[:,h::2],weights[h::2]) for h in (0,1)]
    rng=np.random.default_rng(m.SEED+300000)
    person=rng.uniform(-2,2,size=(len(mask),1));item=rng.uniform(-2,2,size=(1,mask.shape[1]))
    additive=person+item
    zero=[a.residuals(np.where(mask[:,h::2],additive[:,h::2],np.nan)) for h,a in enumerate(halves)]
    if any(np.count_nonzero(e) for e in zero):raise ValueError('actual-mask additive null failed')
    results={}
    for name,scale,reverse in [('stable',4.,False),('reversed',4.,True)]:
        taste=rng.normal(size=(len(mask),8)) @ weights.T
        if reverse:taste[:,1::2]*=-1
        noise=rng.normal(size=mask.shape)*np.exp(rng.uniform(-1,1,size=(len(mask),1)))
        y=np.where(mask,additive+scale*taste+.08*noise,np.nan)
        profiles=[a.profiles(a.residuals(y[:,h::2])) for h,a in enumerate(halves)]
        r,z=m.correlations(*profiles)
        results[name]=dict(mean=float(r.mean()),constant=int(z.sum()))
    # Twenty independent noise worlds: the zero expectation is an ensemble
    # property, not an arbitrary demand that one small fixture be within .03.
    noise_means=[]
    for i in range(20):
        rng=np.random.default_rng(m.SEED+400000+i)
        noise=rng.normal(size=mask.shape)*np.exp(rng.uniform(-1,1,size=(len(mask),1)))
        profiles=[a.profiles(a.residuals(np.where(mask[:,h::2],noise[:,h::2],np.nan))) for h,a in enumerate(halves)]
        noise_means.append(float(m.correlations(*profiles)[0].mean()))
    results['noise']=dict(mean=float(np.mean(noise_means)),world_means=noise_means,worlds=20)
    if results['stable']['mean']<=.10 or results['reversed']['mean']>=-.10 or abs(results['noise']['mean'])>=.03:
        raise ValueError('mask/feature known-answer sensitivity or null failed')
    return dict(exact_additive_zero=True,persons=len(mask),worlds=results,
        scope='Known constructed ratings on fixed actual exposure; not an exposure-bias correction.')


def run(output,inputs,config,verification=False):
    y,w,source,bindings=load(inputs,config)
    # Known worlds, including the actual exposure pattern, precede real scores.
    controls=known_answers() if config['mode']=='constructed' else None
    mask_controls=mask_calibration(np.isfinite(y),w)
    if not verification:
        atomic(Path(output)/'PROGRESS.json',dict(phase='controls_complete',mode=config['mode']))
    start=time.process_time()
    counts=(100,20,2000) if config['mode']=='pilot' else (1000,200,2000)
    result=m.calculate(y,w,*counts)
    elapsed=time.process_time()-start
    if config['mode']=='pilot':
        # Result deliberately discarded. Only a complete pilot's cost is exportable.
        public=dict(card='CA5.r.h1-preference-cost',persons=len(y),item_draws=100,person_draws=20,
            bootstrap_draws=2000,full_item_draws=1000,full_person_draws=200,
            scientific_admission=False,partial_scores_released=False)
        if not verification:
            write_equal(Path(output)/'COST.json',dict(measured_comparison_cpu_seconds=elapsed,
                conservative_full_execution_and_replay_cpu_seconds=24*elapsed,
                scope='10x reference work, 2x fresh replay, 20 percent margin; source/controls charged separately'))
    else:
        public=dict(card='CA5.r.h1-preference',mode=config['mode'],result=result,
            scientific_admission=config['mode']=='main',
            scope='Conditional observed-population lexical preference recurrence; no demographic-relative harm or value inference.')
    payloads={'RESULT.json':public,'MASK_CALIBRATION.json':mask_controls,
        'SOURCE_SUPPORT.json':source,'SOURCE_BINDINGS.json':bindings}
    if controls is not None:payloads['KNOWN_ANSWERS.json']=controls
    for name,obj in payloads.items():
        if verification:assert_equal(obj,read(Path(output)/name))
        else:write_equal(Path(output)/name,obj)
    return dict(verified=verification,full_source_and_statistic_replay=True,
        mode=config['mode'],persons=len(y),scientific_admission=config['mode']=='main')


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
