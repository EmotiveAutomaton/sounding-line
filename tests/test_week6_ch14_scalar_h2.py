"""Counted constructed-only qualification of an exact implementation successor."""
import importlib.util
import copy
import json
import math
from pathlib import Path
import numpy as np
import pytest
from runners.drive.cards import week6_ch14_scalar_h2 as fast
from runners.drive.cards import week6_ch14_replay_h2 as replay
from runners.drive.cards import week6_ch14_math_v3 as old
from runners.drive.cards import week6_ch_riders_fixture_v3 as fixture


@pytest.mark.parametrize('values', [[],[1.],[1e100,1.,-1e100],
    [1.,2**-53,2**-54],[1.,2**-53,-2**-54],[-1.,-2**-53,-2**-54],
    [1e-200,1e-200,-1e-200],[1.,-1.,3.,-2.,1e-30]])
def test_scalar_sum_preserves_cancellation(values):
    assert fast.scalar_sum(np.asarray(values,float)) == math.fsum(values)


def ragged(seed, columns):
    rng=np.random.default_rng(seed);lengths=np.asarray([2,3,5,2,4,7]*3)
    starts=np.r_[0,np.cumsum(lengths)[:-1]]
    return dict(x=rng.normal(size=(int(lengths.sum()),columns)),starts=starts,
        lengths=lengths,selected=starts+np.asarray([rng.integers(n) for n in lengths]),
        person=np.arange(len(starts))%3,week=np.zeros(len(starts),bool))


@pytest.mark.parametrize('columns',[1,2,3])
@pytest.mark.parametrize('hessian',[False,True])
@pytest.mark.parametrize('scale',[0.,.7,25.])
def test_ragged_scalar_likelihood_exact_oracle(columns,hessian,scale):
    data=ragged(39,columns);beta=np.arange(1,columns+1)*scale;weights=np.array([0.,2.,.5])
    answer=fast.likelihood(data,beta,weights,True,hessian)
    oracle=old.likelihood(data,beta,weights,True,hessian)
    for a,b in zip(answer,oracle):np.testing.assert_allclose(a,b,rtol=1e-12,atol=1e-12)


@pytest.mark.parametrize('world,expected', [('null',0.),('fixed_preference',0.),
    ('recency_at_bar',.54*math.log(.54/.5)+.46*math.log(.46/.5))])
def test_constructed_known_answers_and_unchanged_newton(world,expected):
    prepared=fixture.literal_menus(world,players=2);sets=old.model_sets(prepared)
    weights=np.asarray([1.,2.])
    a=fast.draw(prepared,sets,weights,True);b=old.draw(prepared,sets,weights,True)
    replay.base.parity.equivalent(a,b)
    assert a['gains']['hours']['point']==pytest.approx(expected,abs=1e-7)
    assert all(f['status']=='complete' for f in a['fits'].values())


@pytest.mark.parametrize('case',['zero_weight','singular','separated'])
def test_invalidity_and_unsupported_are_not_rescued(case):
    data=ragged(11,2);weights=np.ones(3)
    if case=='zero_weight':weights[:]=0
    if case=='singular':data['x'][:]=0
    if case=='separated':
        data['x'][:,0]=0.;data['x'][data['selected'],0]=1.
    a=fast.fit(data,weights,True);b=old.fit(data,weights,True)
    assert a['status']==b['status'] and a['status']!='complete'


def test_original_namespace_and_bytecode_preserved():
    assert old.fit.__globals__['likelihood'] is old.likelihood
    assert fast.fit.__code__ is old.fit.__code__
    assert fast.draw.__code__ is old.draw.__code__
    assert replay.reference_run.__code__ is replay.base.run.__code__
    assert replay.base.run.__globals__['ch14'] is old
    assert fast.scalar_kernel.targetoptions['fastmath'] is False
    assert not fast.scalar_kernel.targetoptions.get('parallel',False)


def test_fresh_complete_constructed_source_replay(tmp_path):
    path=Path(__file__).with_name('test_week6_ch_riders_v3.py')
    spec=importlib.util.spec_from_file_location('original_ch14_fixture',path)
    source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)
    inputs=source.constructed_source(tmp_path);config=dict(card='CH14',draws=3,constructed_fixture=True)
    output=tmp_path/'original';target=tmp_path/'reference'
    assert replay.base.execute(output,inputs,config)['status']=='complete'
    assert replay.reference_run(target,target,inputs,config,True)['status']=='complete'
    left=replay.read(output/'SCIENCE.json');right=replay.read(target/'SCIENCE.json')
    for value in (left,right):
        for fitted in value['fit'].values():
            fitted.pop('max_gradient',None);fitted.pop('minimum_information_eigenvalue',None)
    replay.base.parity.equivalent(left,right)
    assert len(replay.read(target/'RIDER_CHECKPOINT.json')['draws'])==3
    with pytest.raises(ValueError,match='starts fresh'):
        replay.reference_run(target,target,inputs,config,True)


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True),'utf8')


@pytest.fixture
def transport(tmp_path,monkeypatch):
    from tests.test_week6_ch_riders_v3 import constructed_source
    monkeypatch.setattr(replay,'ROOT',tmp_path)
    monkeypatch.setattr(replay,'is_same_live_process',lambda n:False)
    inputs=constructed_source(tmp_path);config=dict(card='CH14',draws=3,constructed_fixture=True)
    oldroot=tmp_path/'old';output=oldroot/'output'
    assert replay.base.execute(output,inputs,config)['status']=='complete'
    write(output/'PILOT.json',dict(draws=3));write(output/'RECOVERY_ORIGIN.json',dict(constructed=True))
    prior=dict(module='runners.drive.cards.week6_ch14_wall_recovery_v1',inputs=inputs,config=config,
        campaign='S15-WEEK6',family='CH',budget_key='CH14',pins={x['path']:x['sha256'] for x in inputs.values()})
    write(oldroot/'PLAN.json',prior)
    for index,name in enumerate(('OWNER.json','EXECUTE_NATIVE.json','VERIFY_NATIVE.json')):
        write(oldroot/name,dict(native=dict(pid=987650+index),plan_sha256=replay.filehash(oldroot/'PLAN.json')))
    for name in ('EXECUTE_JOB_USAGE.json','VERIFY_JOB_USAGE.json'):
        write(oldroot/name,dict(cpu_seconds=1.,exit_code=0,includes_all_descendants_and_exited_processes=True))
    write(oldroot/'VERIFIED.json',dict(completed_draws=2,phase='source_setup_or_whole_player_refits',status='yielded',verification_prefix_credited=False))
    bank=replay.read(output/'RIDER_CHECKPOINT.json');bank['draws']=bank['draws'][:2]
    write(output/'independent-0001/RIDER_CHECKPOINT.json',bank)
    write(oldroot/'PAUSED.json',dict(status='PAUSED',paused_operation='verify',scientific_admission=False,
        cpu_seconds=2.,checkpoint_outputs=replay.output_manifest(output)))
    spec=dict(version=1,kind='CH14_VERIFY_SCALAR_H1',root=str(oldroot),
        receipts={n:replay.filehash(oldroot/n) for n in replay.RECEIPTS},output_manifest=replay.output_manifest(output))
    manifest=tmp_path/'replay.json';write(manifest,spec)
    plan=copy.deepcopy(prior);plan['module']=replay.__name__
    plan['inputs']['scalar_replay']=dict(path=str(manifest),sha256=replay.filehash(manifest))
    plan['pins'][str(manifest)]=replay.filehash(manifest)
    new=tmp_path/'new';write(new/'PLAN.json',plan)
    return dict(old=oldroot,new=new,spec=spec,plan=plan,manifest=manifest)


def invoke(t):return replay.execute(t['new']/'output',t['plan']['inputs'],t['plan']['config'])


def test_transport_full_replay_and_reentry_preserve_original(transport):
    t=transport;before=replay.output_manifest(t['old']/'output')
    assert invoke(t)['status']=='complete'
    assert invoke(t)['status']=='complete'
    assert replay.verify(t['new']/'output',t['plan']['inputs'],t['plan']['config'])['verified']
    assert replay.output_manifest(t['old']/'output')==before
    assert len(replay.read(t['new']/'output/independent-h2-0001/RIDER_CHECKPOINT.json')['draws'])==3
    assert not (t['new']/'output/YIELD_REQUEST.json').exists()


@pytest.mark.parametrize('name',sorted(replay.RECEIPTS))
def test_transport_changed_receipt_refuses(transport,name):
    t=transport
    with (t['old']/name).open('a') as f:f.write(' ')
    with pytest.raises(ValueError,match='Changed predecessor receipt'):invoke(t)


@pytest.mark.parametrize('pid',[987650,987651,987652])
def test_transport_each_live_identity_refuses(transport,monkeypatch,pid):
    monkeypatch.setattr(replay,'is_same_live_process',lambda n:n['pid']==pid)
    with pytest.raises(ValueError,match='still live'):invoke(transport)


@pytest.mark.parametrize('change',['source','manifest','output','extra','target','config','budget','pin',
                                  'ambiguous','cost','exit','partial'])
def test_transport_corruption_and_semantic_refusals(transport,change):
    t=transport;p=t['plan'];oldroot=t['old']
    if change in ('source','manifest','output','extra','target'):
        path={'source':Path(p['inputs']['histories']['path']),'manifest':t['manifest'],
              'output':oldroot/'output/SCIENCE.json','extra':oldroot/'output/extra.txt',
              'target':t['new']/'output/extra.txt'}[change]
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('ab') as f:f.write(b' ')
    elif change=='config':p['config']['draws']=4
    elif change=='budget':p['budget_key']='CH13'
    elif change=='pin':p['pins'].pop(p['inputs']['histories']['path'])
    elif change=='ambiguous':write(oldroot/'COMPLETE.json',{})
    else:
        name='VERIFY_JOB_USAGE.json' if change=='exit' else 'PAUSED.json'
        value=replay.read(oldroot/name)
        if change=='cost':value['cpu_seconds']=3.
        elif change=='exit':value['exit_code']=1
        else:value['paused_operation']='execute'
        write(oldroot/name,value);t['spec']['receipts'][name]=replay.filehash(oldroot/name)
        write(t['manifest'],t['spec']);p['inputs']['scalar_replay']['sha256']=replay.filehash(t['manifest'])
        p['pins'][str(t['manifest'])]=replay.filehash(t['manifest'])
    write(t['new']/'PLAN.json',p)
    with pytest.raises((ValueError,RuntimeError)):invoke(t)


def test_transport_copy_corruption_refuses(transport,monkeypatch):
    monkeypatch.setattr(replay.shutil,'copyfile',lambda a,b:Path(b).write_bytes(b'bad'))
    with pytest.raises(ValueError,match='copy mismatch'):invoke(transport)


@pytest.mark.parametrize('change',['complete','empty','credited','wrong_count','extra','boolean_count'])
def test_exact_yielded_schema_refuses_other_receipts(transport,change):
    t=transport;path=t['old']/'VERIFIED.json';value=replay.read(path)
    if change=='complete':value={'verified':True}
    elif change=='empty':value={}
    elif change=='credited':value['verification_prefix_credited']=True
    elif change=='wrong_count':value['completed_draws']=1
    elif change=='extra':value['verified']=True
    else:value['completed_draws']=True
    write(path,value);t['spec']['receipts']['VERIFIED.json']=replay.filehash(path)
    write(t['manifest'],t['spec']);t['plan']['inputs']['scalar_replay']['sha256']=replay.filehash(t['manifest'])
    t['plan']['pins'][str(t['manifest'])]=replay.filehash(t['manifest']);write(t['new']/'PLAN.json',t['plan'])
    with pytest.raises(ValueError):invoke(t)


def test_original_adapter_refuses_the_real_yielded_filename(transport,monkeypatch):
    from runners.drive.cards import week6_ch14_replay_h1 as failed
    t=transport;monkeypatch.setattr(failed,'ROOT',t['old'].parent)
    monkeypatch.setattr(failed,'is_same_live_process',lambda n:False)
    t['spec']['receipts'].pop('VERIFIED.json');write(t['manifest'],t['spec'])
    t['plan']['inputs']['scalar_replay']['sha256']=replay.filehash(t['manifest'])
    with pytest.raises(ValueError,match='Ambiguous predecessor terminal'):
        failed.authenticate(t['new']/'output',t['plan']['inputs'],t['plan']['config'])


def test_reused_workspace_matches_previous_kernel_bitwise():
    from runners.drive.cards import week6_ch14_scalar_h1 as previous
    for seed in range(7):
        for columns in (1,2,3):
            data=ragged(seed,columns);beta=np.arange(columns)*.7;weights=np.array([0.,2.,.5])
            for hessian in (False,True):
                for a,b in zip(fast.likelihood(data,beta,weights,True,hessian), previous.likelihood(data,beta,weights,True,hessian)):
                    np.testing.assert_array_equal(a,b)


def test_constructed_large_menu_timing():
    import os,time,statistics
    from runners.drive.cards import week6_ch14_scalar_h1 as previous
    rng=np.random.default_rng(20261119);lengths=rng.integers(2,15,size=20000);starts=np.r_[0,np.cumsum(lengths)[:-1]]
    data=dict(x=rng.normal(size=(int(lengths.sum()),3)),starts=starts,selected=starts,person=np.arange(len(starts))%200)
    beta=np.array([.1,-.3,.7]);weights=np.ones(200)
    for a,b in zip(fast.likelihood(data,beta,weights,True,True),previous.likelihood(data,beta,weights,True,True)):
        np.testing.assert_array_equal(a,b)
    timings={}
    for name,implementation in [('previous',previous),('candidate',fast)]:
        times=[]
        for repeat in range(7):
            start=time.process_time();implementation.likelihood(data,beta,weights,True,True);times.append(time.process_time()-start)
        timings[name]=times
    report=dict(constructed_only=True,choices=20000,options=int(lengths.sum()),seed=20261119,cpu_seconds=timings,
                median_speed_ratio=statistics.median(timings['previous'])/statistics.median(timings['candidate']),scientific_admission=False)
    Path(os.environ['CH14_BENCHMARK_PATH']).write_text(json.dumps(report,sort_keys=True),'utf8')
