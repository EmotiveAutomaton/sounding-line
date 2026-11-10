"""Complete-count D7 continuation proof; generated inputs only, no human data."""
from pathlib import Path
import copy
import json
import math
import time
import numpy as np
from threadpoolctl import threadpool_limits
from runners.stage14.common import read, filehash, atomic
from . import week5_bk_d7 as card
from .timing_p6 import write_equal


def refused(call):
    try:
        call()
    except (ValueError, KeyError):
        return
    raise ValueError('Deliberately invalid input was accepted')


def gate_worlds(name):
    """Known-answer gate logic, explicitly separate from fitted calibration."""
    worlds = []
    for regime, ordinal, seed in card.roster():
        signed = regime == 'signed'; dose = .8 if ordinal % 2 == 0 else -.8
        shared = dict(bootstrap_draws=2000, writers=12,
                      joint_permutation=dict(attempted=200, invalid=0, mean=0., one_sided_p=.005,
                                             two_sided_p=.005, positive_bias_flag=False, bias_flag=False),
                      fake_writer=dict(attempted=200, invalid=0, mean=0.))
        if name == 'D7.s':
            shared.update(gain=.1 if signed else 0., ci_low=.09 if signed else -.01,
                          ci_high=.11 if signed else .01, positive=signed,
                          mean_added_coefficient=dose if signed else 0.)
            value = dict(curve={key:copy.deepcopy(shared) for key in card.specification.KEYS})
        else:
            shared.update(delta=dose if signed else 0., directional_call=signed,
                          ci_low=dose-.01 if signed else -.01, ci_high=dose+.01 if signed else .01,
                          correlation=.9, correlation_interval=[.8, .95], correlation_undefined_resamples=0)
            value = dict(summary=shared)
        value.update(writers=12, observations=1440, joint_draws=200, conditional_draws=200,
                     fit_bank_sha256='constructed-gate-logic-only')
        worlds.append(card.world_record(name, regime, ordinal, value))
    return worlds


def sealing(root, cfg, result):
    root.mkdir(parents=True, exist_ok=True)
    write_equal(root/'output/RESULT.json', result)
    write_equal(root/'output/EXECUTE_COST.json', dict(process_cpu_seconds=1.))
    write_equal(root/'output/VERIFY_COST.json', dict(process_cpu_seconds=2.))
    write_equal(root/'PLAN.json', dict(module=card.__name__, config=cfg, inputs={}, pins={str(Path(card.__file__).resolve()):filehash(card.__file__)}))
    outputs={p.relative_to(root).as_posix():filehash(p) for p in (root/'output').glob('*.json')}
    write_equal(root/'COMPLETE.json', dict(status='COMPLETE', fresh_process_verified=True, outputs=outputs,
                                         constructed_fixture_only=True))


def gates(root, name, verifying):
    worlds=gate_worlds(name)
    result=card.campaign_result(name, worlds)
    if not result['calibration']['passes']:
        raise ValueError('Known passing complete calibration rejected')
    for changed in (worlds[:-1], worlds[:-1]+[worlds[0]]):
        refused(lambda:card.campaign_result(name, changed))
    for field,value in [('dose',17.),('bootstrap_draws',1999),('references',199),('writers',11),('producer_sha256','changed')]:
        changed=copy.deepcopy(worlds);changed[0][field]=value
        refused(lambda:card.campaign_result(name, changed))
    failed=copy.deepcopy(worlds)
    for world in failed:
        if world['regime']=='signed':
            if name=='D7.s':
                for value in world['analysis']['curve'].values():value['positive']=False
            else:world['analysis']['summary']['directional_call']=False
    if card.campaign_result(name, failed)['calibration']['passes']:
        raise ValueError('Known failed calibration admitted')
    paths=[]
    for index, world in enumerate(worlds):
        path=root/f'gate-dependency-{index:02d}'
        sealing(path,card.configuration(name,'world',world['regime'],world['ordinal']),world)
        paths.append(str(path))
    bank=root/'GATE_WORLD_LIST.json';write_equal(bank,paths)
    output=root/'gate-reduction'
    (card.verify if verifying else card.execute)(output,dict(worlds=str(bank)),card.configuration(name,'calibration_reduce'))
    if read(output/'RESULT.json')!=result:
        raise ValueError('Actual complete reduction differs from unchanged gate')
    pilot=root/'GATE_PILOT_LIST.json';write_equal(pilot,paths[:2])
    (card.verify if verifying else card.execute)(root/'pilot-reduction',dict(worlds=str(pilot)),card.configuration(name,'pilot_reduce'))
    estimate=read(root/'pilot-reduction/RESULT.json')
    if estimate['coverage']<.05 or estimate['calibration_forecast_cpu_seconds']!=360.:
        raise ValueError('Whole-world both-pass cost projection differs')
    calroot=root/'failed-calibration'
    sealing(calroot,card.configuration(name,'calibration_reduce'),card.campaign_result(name,failed))
    inputs={key:'never-read' for key in card.human.SOURCE_KEYS|{'support_completion','cost_completion'}}
    inputs['calibration_completion']=str(calroot/'COMPLETE.json')
    refused(lambda:card.human_source(inputs,name))


def arithmetic(name, rows):
    module=card.CARDS[name];groups,_=card.calibration.support(rows)
    first=groups[sorted(groups)[0]];module.native_oracles(first)
    train,_,test=card.human.c.m.partition(first)[0]
    changed=copy.deepcopy(first)
    for i in test:changed[i]['dwell_seconds']*=3
    before=module.compare(first);after=module.compare(changed)
    if name=='D7.s':
        if any(before[key]['fits']!=after[key]['fits'] or before[key]['predictions']!=after[key]['predictions'] for key in before):
            raise ValueError('Later outcomes changed training fit or predictions')
    elif before['training_coefficients']!=after['training_coefficients'] or before['penalty']!=after['penalty']:
        raise ValueError('Later outcomes changed training fit or selection')
    constant=[dict(r,dwell_seconds=math.expm1(2.)) for r in first]
    value=module.compare(constant)
    if name=='D7.s':
        if any(v['gain']!=0. or v['fits'][1]['coefficients'][-1]!=0. for v in value.values()):
            raise ValueError('Constant responses acquired a novelty effect')
    elif value['delta']!=0. or value['earlier']!=0. or value['later']!=0.:
        raise ValueError('Constant responses acquired coefficient drift')


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('No human input in D7 fixture')
    root=Path(output);root.mkdir(parents=True,exist_ok=True)
    for name in card.CARDS:
        module=card.CARDS[name];base=root/name
        for regime,ordinal in [('null',0),('nuisance',0),('signed',0),('signed',1)]:
            cfg=card.configuration(name,'fixture_world',regime,ordinal);out=base/f'{regime}-{ordinal}'
            if not verifying:
                write_equal(out/'YIELD_REQUEST.json',dict(reason='constructed boundary test'))
                value=card.execute(out,{},cfg)
                if value.get('status')!='yielded':raise ValueError('Pre-fit yield ignored')
                (out/'YIELD_REQUEST.json').unlink()
            value=(card.verify if verifying else card.execute)(out,{},cfg)
            if verifying and value.get('verified') is not True:raise ValueError('Native verifier contract missing')
            rows,assignments,_=card.world_source(name,regime,ordinal,3)
            oldroot=base/f'original-{regime}-{ordinal}';oldroot.mkdir(parents=True,exist_ok=True)
            old,_=module.analyze(oldroot,'fixture',rows,assignments,
                                dict(references=200,bootstrap_draws=2000,seed=card.SEED+ordinal),verifying)
            got=read(out/'RESULT.json')['analysis']
            if got!=old:raise ValueError('Complete unchanged original analysis differs')
            arithmetic(name,rows)
            if regime=='signed':
                if name=='D7.s' and any(v['mean_added_coefficient']*(1 if ordinal==0 else -1)<=0 for v in got['curve'].values()):
                    raise ValueError('Signed novelty coefficient direction changed')
                if name=='D7.m' and got['summary']['delta']*(1 if ordinal==0 else -1)<=0:
                    raise ValueError('Signed later coefficient change lost')
            if regime=='null':
                seal=out/'arm-000.seal.json';saved=seal.read_bytes();seal.write_text('{}\n',encoding='utf8')
                try:refused(lambda:card.fitted_bank(out,name,rows,assignments,card.SEED,False))
                finally:seal.write_bytes(saved)
                refused(lambda:card.fitted_bank(out,name,rows,assignments[:-1],card.SEED,False))
                # A crash between atomic data and seal writes must recompute the
                # unsealed arm, never trust it or discard the original bytes.
                seal.unlink()
                try:
                    if card.fitted_bank(out,name,rows,assignments,card.SEED,False)!=got:
                        raise ValueError('Unsealed complete arm recovery changed the result')
                    if seal.read_bytes()!=saved:raise ValueError('Recovered seal changed')
                finally:
                    if not seal.exists():seal.write_bytes(saved)
        gates(base,name,verifying)
    if card.stability.correlation([1,2,3],[3,2,1])!=-1 or card.stability.correlation([1,2,3],[1,2,3])!=1:
        raise ValueError('Signed coefficient correlation became absolute')
    receipt=dict(fixture_only=True,actual_complete_handlers=8,original_estimator_exact_replay=True,
                 references_per_family=200,writer_bootstraps=2000,null_nuisance_positive_negative=True,
                 independent_augmented_least_squares=True,heldout_mutation_invariance=True,
                 exact_constant_response_zero=True,sealed_reentry_and_tamper_refusal=True,
                 partial_seal_recovery_recomputes_before_reuse=True,
                 complete_thirty_world_collection_gate=True,failed_calibration_refuses_human=True,
                 pilot_covers_two_of_thirty_worlds=True,gate_logic_is_constructed_not_full_calibration=True)
    card.record_equal(root/'FIXTURE.json',receipt,verifying)
    return dict(verified=True,complete_original_consumer_replay=True) if verifying else dict(status='complete',fixture_only=True)


def execute(output,inputs,config):
    with threadpool_limits(limits=2):return run(output,inputs,config)
def verify(output,inputs,config):
    with threadpool_limits(limits=2):return run(output,inputs,config,True)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('output');parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    began=time.process_time();value=(verify if args.verify else execute)(args.output,{},{})
    write_equal(Path(args.output)/('NATIVE_VERIFY_CPU.json' if args.verify else 'NATIVE_EXECUTE_CPU.json'),dict(cpu_seconds=time.process_time()-began))
    print(json.dumps(value))
