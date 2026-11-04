"""Generated-choice fitting cost on the complete packed human feature support.

DESIGN CHECK: LESSONS 3-5 reread November 2. Human choices must not affect
generated labels or fit results under either law. Test this invariance and
impossible-padding refusal before native work. Cost is not recovery or power;
there is no scientific acceptance rule in this probe and no main admission.
"""
from pathlib import Path
import time
import numpy as np
from scipy.special import softmax
from . import week4_t4_inputs as source
from . import week4_t4_variable as model
from .timing_p6 import read,gzread,write_equal,progress
from .timing_pmap_source import completed


def configuration(mode):
    if mode not in ('constructed','cost'): raise ValueError('Unknown cost scope')
    return dict(card='T4-matched-cost',mode=mode,seeds=[20261102,20261103,20261104],
                refit_pairs=201,replay_factor=2,safety_factor=3)


def generated(packed,seed,individual):
    data=source.arrays(packed,'train'); writers=len(packed['writers'])
    # Remove the actual labels before computing even the generating probabilities.
    data['y']=np.zeros(len(data['w']),dtype=int)
    theta=np.r_[np.asarray([1.,-.5,.2,.1,.3,.3,-.2]),np.where((np.arange(writers)//2)%2,1.5,-1.5),
                np.where(np.arange(writers)%2,np.log(4.),np.log(.25)) if individual else np.zeros(writers)]
    probabilities=softmax(model.logits(theta,data,True),axis=1)
    rng=np.random.default_rng(seed)
    data['y']=(rng.random(len(data['w']))[:,None]>np.cumsum(probabilities,axis=1)).sum(axis=1)
    model.checked(data)
    return data


def known_answers():
    import copy
    p=source.assemble(source.fixture(),2,3);q=copy.deepcopy(p)
    q['train']['y']=[5]*len(q['train']['y'])
    for regime in (False,True):
        a=generated(p,20261102,regime);b=generated(q,20261102,regime)
        assert all(np.array_equal(a[k],b[k]) for k in a)
        assert model.checked(a)==3
    return dict(human_choice_invariance=True,generated_padding_refused=True,all_features_retained=True)


def load(inputs):
    if set(inputs)!={'inputs_completion','bank_completion'}: raise ValueError('Exact completed sources required')
    ic=Path(inputs['inputs_completion']);bc=Path(inputs['bank_completion'])
    for n in ('SUMMARY.json','PRIVATE_DATA.json.gz'):completed(ic,ic.parent/'output'/n)
    completed(bc,bc.parent/'output/SUMMARY.json')
    bank=read(bc.parent/'output/SUMMARY.json');meta=read(ic.parent/'output/SUMMARY.json')
    if not bank['complete_bank'] or not bank['bank_gate'] or bank['worlds']!=40:raise ValueError('Complete variable-menu validation required')
    if meta['mode']!='full' or not meta['support_pass']:raise ValueError('Complete supported input source required')
    data=gzread(ic.parent/'output/PRIVATE_DATA.json.gz')
    if len(data['writers'])<25:raise ValueError('Twenty-five writers required')
    return data


def run(output,inputs,config,verification=False):
    if config!=configuration(config['mode']):raise ValueError('Frozen cost configuration required')
    output=Path(output);start=time.process_time();checks=known_answers()
    if config['mode']=='constructed':
        if inputs:raise ValueError('Constructed inputs must be empty')
        packed=source.assemble(source.fixture(),2,3);seeds=config['seeds'][:1]
    else:packed=load(inputs);seeds=config['seeds']
    load_seconds=time.process_time()-start;receipts=[];durations=[]
    for seed in seeds:
        for individual in (False,True):
            begin=time.process_time();data=generated(packed,seed,individual)
            shared=model.fit(data,False);personal=model.fit(data,True)
            receipts.append(dict(seed=seed,regime='individual' if individual else 'shared',shared=shared,individual=personal))
            durations.append(time.process_time()-begin)
            progress(output/'PROGRESS.json',dict(phase='verify-cost' if verification else 'cost',done=len(receipts),total=2*len(seeds)))
    summary=dict(mode=config['mode'],generated_worlds=len(receipts),writers=len(packed['writers']),
                 training_menus=len(packed['train']['w']),human_choices_fitted=False,human_choices_scored=False,
                 checks=checks,bounded_fits=sum(r['individual']['boundary_coordinates']>0 for r in receipts),
                 scientific_admission=False)
    if verification:
        if read(output/'SUMMARY.json')!=summary or read(output/'PRIVATE_FITS.json')!=receipts:raise ValueError('Complete generated-fit replay differs')
        return dict(verified=True,complete_generated_fit_replay=True)
    write_equal(output/'PRIVATE_FITS.json',receipts);write_equal(output/'SUMMARY.json',summary)
    write_equal(output/'TIMING.json',dict(load_cpu_seconds=load_seconds,pair_cpu_seconds=durations,
        core_refit_forecast_cpu_seconds=config['replay_factor']*config['safety_factor']*(load_seconds+max(durations)*config['refit_pairs'])+20,
        scope='Core fitting only; scientific calibration, parameter uncertainty and joins not included; no main admission'))
    return dict(status='complete',scientific_admission=False)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
