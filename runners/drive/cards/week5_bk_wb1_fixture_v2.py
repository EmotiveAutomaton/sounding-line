"""Complete-count WB1 raw, encoding, conditional-reference and reducer proof."""
from pathlib import Path
import copy
import json
import time
import shutil
from threadpoolctl import threadpool_limits
from runners.stage14.common import read,filehash,digest
from . import week5_bk_wb1_source as source
from . import week5_bk_wb1_encode_v2 as encode
from . import week5_bk_wb1_coverage as coverage
from . import week5_bk_wb1_reduce_v2 as reduce
from . import week5_bk_wb1_coverage_pilot as coverage_pilot
from . import week5_bk_wb1_pilot_forecast as pilot_forecast
from . import week3_pieces_coverage as old_coverage
from . import week3_pieces_effects_h1 as effects
from . import week4_pieces_windows_h1 as exact
from . import week3_pieces_stats as stats
from .timing_p6 import write_equal,gzread
from tests.test_week4_pieces_windows_h1 import canonical_fixture,cases
from tests.test_week3_pieces_effects import effect_records


def sealed(root,module,inputs,config):
    # These are explicitly constructed dependency receipts, not production
    # runtime admissions. Every component has executed and replayed before use;
    # the complete outer fixture is independently rerun in a fresh process.
    write_equal(root/'PLAN.json',dict(module=module.__name__,inputs=inputs,config=config,
                                    pins={str(Path(module.__file__).resolve()):filehash(module.__file__)}))
    outputs={p.relative_to(root).as_posix():filehash(p) for p in (root/'output').rglob('*')
             if p.is_file() and p.name not in ('PROGRESS.json','YIELD_REQUEST.json')}
    if not (root/'COMPLETE.json').exists():
        write_equal(root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,outputs=outputs,
            constructed_dependency_fixture=True,not_a_production_runtime_admission=True))


def stage(module,root,inputs,config,verifying=False):
    if verifying:
        target=root/'output'
        if module is encode:
            # Rehearse a truly fresh verification as well as continuation:
            # copy immutable execute bytes, preserving the original receipt,
            # but do not copy previous independent-verification proofs.
            target=root/'independent_replays'/str(time.time_ns())
            shutil.copytree(root/'output',target,ignore=shutil.ignore_patterns('*.verified.json'))
        value=module.verify(target,inputs,config)
        if value.get('verified') is not True:raise ValueError('Actual handler verifier contract missing')
    else:
        value=module.execute(root/'output',inputs,config)
        if value.get('status')!='complete':raise ValueError('Constructed stage did not complete')
        if module.verify(root/'output',inputs,config).get('verified') is not True:
            raise ValueError('Complete handler replay failed')
        sealed(root,module,inputs,config)
    return root


def refused(call):
    try:call()
    except (ValueError,KeyError):return
    raise ValueError('Incomplete or changed native fixture input accepted')


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('WB1 fixture has no human input')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);inputfile=root/'INPUTS.json'
    if not inputfile.exists():write_equal(inputfile,canonical_fixture(root/'original-inputs'))
    original=read(inputfile);cfg=source.configuration('constructed')
    src=stage(source,root/'source',original,cfg,verifying);src_inputs=dict(source_root=str(src))
    _,manifest,rows=source.load(src)
    pilot=stage(coverage_pilot,root/'coverage-pilot',src_inputs,{},verifying)
    if read(pilot/'output/COVERAGE_PILOT.json')['work_fraction']!=.05:
        raise ValueError('Original five-percent reference pilot changed')
    stage(pilot_forecast,root/'coverage-pilot-forecast',dict(pilot_root=str(pilot)),{},verifying)
    for events,timeline,anchors in cases():
        if exact.effect_windows(events,timeline,anchors)!=effects.effect_windows(events,timeline,anchors):
            raise ValueError('Original physical-insertion windows changed')
    encpaths=[]
    for start in range(0,8,4):
        block=root/f'cost-block-{start}';blockcfg=dict(phase='cost',start=start,count=4)
        if not verifying:
            write_equal(block/'output/YIELD_REQUEST.json',dict(reason='constructed before-model yield'))
            if encode.execute(block/'output',src_inputs,blockcfg).get('status')!='yielded':raise ValueError('Encoding resource request ignored')
            (block/'output/YIELD_REQUEST.json').unlink()
        stage(encode,block,src_inputs,blockcfg,verifying);encpaths.append(str(block))
    bank=root/'COST_BANK.json';write_equal(bank,encpaths)
    cost=stage(reduce,root/'cost-reduce',dict(**src_inputs,blocks=str(bank)),dict(operation='cost_reduce'),verifying)
    old_cfg=dict(mode='constructed',seed=stats.SEED,sample_denominator=1,minimum_occurrences=1,
                 minimum_writers=1,permutation_draws=20,bootstrap_draws=2000,safety_multiplier=3)
    oracle_root=root/'original-cost';oracle_root.mkdir(parents=True,exist_ok=True)
    oracle,_=exact.measure(oracle_root,original,old_cfg)
    if read(cost/'output/WORK.json')!=oracle:raise ValueError('Complete original first-tenth work digest changed')
    pilot=root/'PILOT_BANK.json';write_equal(pilot,encpaths[:1])
    stage(reduce,root/'pilot-reduce',dict(**src_inputs,blocks=str(pilot)),dict(operation='pilot_reduce'),verifying)
    refused(lambda:encode.collect(src_inputs,'cost',encpaths[:1]))
    refused(lambda:encode.collect(src_inputs,'cost',encpaths+encpaths[:1]))
    _,_,entries,_,_,_,_=encode.collect(src_inputs,'cost',encpaths)
    if len(entries)!=8:raise ValueError('Original selected source count changed')
    reductions={};testlists={}
    for scope in ('whole','thirds'):
        paths=[]
        for start in range(0,200,10):
            block=root/f'{scope}-discovery-{start:03d}'
            stage(coverage,block,src_inputs,dict(operation='reference_block',scope=scope,side='discovery',start=start,count=10),verifying)
            paths.append(str(block))
        listing=root/(scope+'-DISCOVERY_BANK.json');write_equal(listing,paths)
        reductions[scope]=stage(coverage,root/(scope+'-discovery'),dict(**src_inputs,blocks=str(listing)),dict(operation='discovery_reduce',scope=scope),verifying)
        test_inputs=dict(**src_inputs,discovery_root=str(reductions[scope]));paths=[]
        for start in range(0,200,10):
            block=root/f'{scope}-test-{start:03d}'
            stage(coverage,block,test_inputs,dict(operation='reference_block',scope=scope,side='test',start=start,count=10),verifying)
            paths.append(str(block))
        listing=root/(scope+'-TEST_BANK.json');write_equal(listing,paths);testlists[scope]=str(listing)
    cov_inputs=dict(**src_inputs,whole_discovery=str(reductions['whole']),thirds_discovery=str(reductions['thirds']),
                    whole_blocks=testlists['whole'],thirds_blocks=testlists['thirds'])
    cov=stage(coverage,root/'coverage',cov_inputs,dict(operation='coverage_reduce'),verifying)
    old_cfg=dict(mode='constructed',coarse=False,seed=stats.SEED,surrogate_draws=200,bootstrap_draws=2000,minimum_occurrences=1,minimum_writers=1)
    old_out=root/'original-coverage';old_out.mkdir(parents=True,exist_ok=True)
    prep={k:original[k] for k in exact.pilot.PREP_KEYS}
    if verifying:old_coverage.verify(old_out,prep,old_cfg)
    else:old_coverage.execute(old_out,prep,old_cfg)
    actual=read(cov/'output/WB1_COVERAGE_RESULT.json')
    if actual!=read(old_out/'WB1_COVERAGE_RESULT.json'):raise ValueError('Complete original coverage changed')
    for scope in ('whole','thirds'):
        for draw in range(10):
            measured=read(pilot/'output'/f'{scope}-discovery-{draw:02d}.json')['values']
            if measured!=read(root/f'{scope}-discovery-000/output/draw-{draw:03d}.json')['values']:
                raise ValueError('Pilot changed original global conditional-reference draws')
    # Exercise nonempty effect encoding even when the tiny raw-source discovery
    # has no supra-first-order piece. This separate occurrence list is the old
    # raw-handler fixture, never represented as discovered human pieces.
    legacy_cov=Path(original['preparation_complete']).parent.parent/'coverage'
    effect_cov=root/'constructed-occurrence-coverage'
    observed=read(legacy_cov/'output/WB1_COVERAGE_RESULT.json')
    write_equal(effect_cov/'output/WB1_COVERAGE_RESULT.json',observed)
    sealed(effect_cov,coverage,dict(source_root=str(src)),dict(operation='coverage_reduce'))
    effect_inputs=dict(**src_inputs,coverage_root=str(effect_cov));paths=[]
    for start in range(0,8,4):
        block=root/f'effects-{start}';stage(encode,block,effect_inputs,dict(phase='effects',start=start,count=4),verifying);paths.append(str(block))
    bank=root/'EFFECT_BANK.json';write_equal(bank,paths)
    final=stage(reduce,root/'effects',dict(**effect_inputs,blocks=str(bank)),dict(operation='effects_reduce'),verifying)
    old_inputs=dict(coverage_complete=str(legacy_cov/'COMPLETE.json'),coverage_result=str(legacy_cov/'output/WB1_COVERAGE_RESULT.json'),
                    **{k:original[k] for k in ('source_inputs','content_model','content_complete')})
    old_effect=root/'original-effects';old_effect.mkdir(parents=True,exist_ok=True)
    old=effects.calculate(old_effect,old_inputs,dict(mode='constructed',permutation_draws=200,seed=stats.SEED),verifying)
    got=read(final/'output/WB1_RESULT.json')
    if any(got[k]!=v for k,v in old.items() if k!='bindings'):
        raise ValueError('Original complete effect definitions or statistics changed')
    if gzread(final/'output/WB1_EFFECT_ROWS.json.gz')!=read(old_effect/'WB1_EFFECT_ROWS.json'):
        raise ValueError('All actual raw occurrence and embedding values differ')
    known=effect_records();positive=effects.consistency(known,200,stats.SEED)
    if positive['net_characters']['variance_explained']!=1 or positive['net_characters']['permutation_p']>.05:
        raise ValueError('Known piece-dependent effects missed')
    classes=effects.classes(known,stats.SEED)
    for row in known:
        row['net_characters']=0.
        if row['side']=='test':row['sentence_completed']=123456.
    if effects.consistency(known,200,stats.SEED)['net_characters']['permutation_p']!=1:
        raise ValueError('Constant effects acquired a result')
    unchanged=effect_records()
    for row in unchanged:
        if row['side']=='test':row.update({key:123456. for key in effects.EFFECTS})
    if effects.classes(unchanged,stats.SEED)!=classes:raise ValueError('Held-out values changed discovered classes')
    expected=[dict(session=str(i),writer=str(i),events=100+i,real_covered=70,reference_covered=20) for i in range(10)]
    if stats.coverage_interval(expected,2000)['state']!='positive' or stats.coverage_interval([dict(r,real_covered=20) for r in expected],2000)['estimate']!=0 or stats.coverage_interval([dict(r,real_covered=0) for r in expected],2000)['state']!='negative':
        raise ValueError('Complete cluster interval sign controls failed')
    receipt=dict(fixture_only=True,actual_raw_sessions=8,all_seven_physical_insertion_cases=True,
                 original_cost_work_exact=True,all_four_reference_banks=200,whole_writer_bootstraps=2000,
                 original_full_coverage_exact=True,actual_source_and_embedding_replay=True,
                 original_effects_and_classes_exact=True,all_effect_references=200,
                 positive_null_negative_controls=True,discovery_isolated_from_test=True,
                 encoding_yield_complete_and_duplicate_bank_refusal=True,
                 exact_five_percent_coverage_pilot=True,independent_new_vector_verification=True,
                 constructed_dependency_receipts_not_production_admission=True)
    source.checked(root/'FIXTURE.json',receipt,verifying)
    return dict(verified=True,complete_raw_and_statistical_replay=True) if verifying else dict(status='complete',fixture_only=True)


def execute(output,inputs,config):
    with threadpool_limits(limits=2):return run(output,inputs,config)
def verify(output,inputs,config):
    with threadpool_limits(limits=2):return run(output,inputs,config,True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args()
    began=time.process_time();value=(verify if a.verify else execute)(a.output,{},{})
    write_equal(Path(a.output)/('NATIVE_VERIFY_CPU.json' if a.verify else 'NATIVE_EXECUTE_CPU.json'),dict(cpu_seconds=time.process_time()-began))
    print(json.dumps(value))
