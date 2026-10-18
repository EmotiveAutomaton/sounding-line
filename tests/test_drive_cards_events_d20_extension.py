import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest
from runners.drive.cards import events_d20_extension as d
from runners.drive.cards import events_d20_sources as source
from runners.drive.cards import events_d20_stats as stats
from runners.drive.cards import menus_d20 as old
from runners.drive.cards import menus_d20_recovery as recovery
from runners.drive.cards.menus_io import read,write,sha256,canonical,input_hashes
from runners.drive.cards.timing_p6 import gzwrite


def rows(world='positive'):
    result=[];words=['apple','orange','banana','pear','grape','melon','peach','berry']
    for w,word in enumerate(words):
        for h in range(2):
            level=7-w if world=='reverse' and h else w
            options=['shared'] if world=='null' else [word+' '+' '.join('filler'+str(j) for j in range(level))]
            vector=np.zeros(384);vector[w]=1/(level+1);vector[20]=np.sqrt(1-vector[w]**2)
            window=np.eye(384)[w]
            if world=='null':vector=window=np.eye(384)[0]
            result.append(dict(key=f'w{w}s{h}',writer=f'w{w}',session=f'w{w}s{h}',prompt='p',half=h,
                progress_decile=0,handling='dismiss',options=options,option_vectors=[vector.tolist()],
                window=' '.join(['shared' if world=='null' else word]*50),window_vector=window.tolist()))
    return result


def kernel_rows(raw,channel):
    lean=source.lean(raw);writers=sorted({r['writer'] for r in raw})
    groups={}
    for r in lean:groups.setdefault((r['prompt'],r['progress_decile']),[]).append(r)
    kernels=[stats.kernel(v,writers,channel) for _,v in sorted(groups.items())]
    comp,excluded=stats.comparisons(kernels,writers)
    return kernels,comp,writers,excluded


@pytest.mark.parametrize('world',['positive','reverse','null'])
def test_exact_kernel_and_bootstrap_reduction_matches_original(world):
    raw=rows(world)
    for channel in stats.CHANNELS:
        kernels,comp,writers,excluded=kernel_rows(raw,channel)
        original,ow,oe=old.comparisons(raw,channel)
        d.assert_comparisons(dict(rows=comp,writers=writers,exclusions=excluded),dict(rows=original,writers=ow,exclusions=oe))
        design=stats.Design(comp,writers)
        for weights in (np.ones(8),np.array([2,0,1,1,1,1,1,1]),np.array([8,0,0,0,0,0,0,0])):
            point,means,halves=design.values(weights);op,om,oh=old.estimates(original,writers,weights)
            assert point==pytest.approx(op,abs=1e-12)
            for w,v in om.items():
                assert means[writers.index(w)]==pytest.approx(v,abs=1e-12)
                assert halves[writers.index(w)]==pytest.approx(oh[w],abs=1e-12)
        point,_,halves=design.values(np.ones(8));corr=design.correlation(halves,np.ones(8))
        if world=='positive':assert corr==pytest.approx(1)
        if world=='reverse':assert corr<-.5
        if world=='null':assert point==pytest.approx(0,abs=1e-15) and corr is None


def test_within_writer_permutations_preserve_rows_and_match_slow_original():
    raw=rows();raw.append(raw[0]|dict(key='extra',session='extra',half=0,window=rows()[2]['window'],window_vector=rows()[2]['window_vector']))
    raw.append(raw[1]|dict(key='unsupported',session='unsupported',options=['the and'],option_vectors=[]))
    for channel in stats.CHANNELS:
        kernels,comp,writers,excluded=kernel_rows(raw,channel);groups=stats.outcome_groups(kernels)
        mapping=stats.permutation(groups,20261018,0);lookup={r['key']:r for r in raw};changed=[]
        for r in raw:
            donor=lookup[mapping[r['key']]]
            assert r['writer']==donor['writer'] and r['prompt']==donor['prompt']
            changed.append(r|dict(window=donor['window'],window_vector=donor['window_vector']))
        current,ex=stats.comparisons(kernels,writers,mapping);expected,ow,oe=old.comparisons(changed,channel)
        d.assert_comparisons(dict(rows=current,writers=writers,exclusions=ex),dict(rows=expected,writers=ow,exclusions=oe))
        assert [r['key'] for r in current]==[r['key'] for r in comp]


def test_known_null_signed_pairing_and_no_redraw():
    # Orthogonal halves give exact zero on a complete fixed graph; independent
    # duplicated profile is+1, reversed profile-1. No variance is undefined.
    x=np.array([-1,-1,1,1]); y=np.array([-1,1,-1,1])
    assert stats.weighted_correlations(x,np.array([y,x,-x]),np.ones(4))==pytest.approx([0,1,-1])
    assert stats.weighted_correlations(np.ones(4),np.array([y]),np.ones(4))==[None]
    report=stats.null_report(.4,[None,0,.1])
    assert not report['valid'] and report['p_one_sided'] is None and report['undefined_draws']==1
    assert stats.null_report(1,[-1,0,1])['p_one_sided']==.5
    kernels,comp,writers,_=kernel_rows(rows(),'lexical'); design=stats.Design(comp,writers)
    _,_,halves=design.values(np.ones(8));maps=stats.identity_maps(8,20261018,200)
    real=stats.identity_values(design,halves,np.ones(8),maps)
    assert real['own']==pytest.approx(1) and real['difference']>.9
    weights=np.array([2,0,1,1,1,1,1,1]);_,_,hs=design.values(weights)
    paired=stats.identity_values(design,hs,weights,maps)
    expanded=np.repeat(np.arange(8),weights);own=old.intervals.correlation(hs[expanded,0],hs[expanded,1])
    fake=np.mean([old.intervals.correlation(hs[expanded,0],hs[m[expanded],1]) for m in maps])
    assert paired['difference']==pytest.approx(own-fake)
    hs[maps[0,0],1]=np.nan
    bad=stats.identity_values(design,hs,np.ones(8),maps)
    assert bad['undefined']>0 and bad['difference'] is None
    sparse=stats.Design([dict(key='a',writer='a',session='a',half=0,observed=1,donor_sum=[0,0],donor_sessions=[0,1])],['a','b'])
    assert sparse.values(np.array([2,0]))[0] is None


def fixture(tmp_path,world='positive'):
    """Actual serialized completed producer-shaped sources, no neural execution.

    The primary/recovery verifier genuinely runs on these synthetic rows before
    COMPLETE is written. The local model identity is read but never loaded.
    """
    root=Path(tmp_path)/'source';root.mkdir(parents=True);p2=root/'p2';p5=root/'p5';p6=root/'p6';content=root/'content'
    for folder in (p2,p5,p6,content):folder.mkdir()
    sessions=[];features=[];ledger=[];timelines=[];vectors=[];raw=rows(world)
    for i,row in enumerate(raw):
        sid=row['session'];menu=dict(key=row['key'],ordinal=0,handling='dismiss',menu=row['options'])
        sessions.append(dict(session=sid,writer=row['writer'],prompt='p',timestamp=row['half'],rows=[menu]))
        features.append(dict(key=row['key'],session=sid,writer=row['writer'],options=[i]));vectors.extend(row['option_vectors'])
        words=[dict(index=j,is_word=True,ordinal=j+2,completed_ordinal=j+3,token=t,revised=False) for j,t in enumerate(row['window'].split())]
        gzwrite(p6/(sid+'.json.gz'),dict(session=sid,writer=row['writer'],prompt='p',words=words))
        ledger.append(dict(session=sid,writer=row['writer'],file=sid+'.json.gz',sha256=sha256(p6/(sid+'.json.gz'))))
        write(p2/(sid+'.json'),dict(session=sid,writer=row['writer'],prompt='p',decisions=[dict(key=row['key'],ordinal=0,resolution_ordinal=1,handling='dismiss')]))
        timelines.append(dict(session=sid,writer=row['writer'],file=sid+'.json',sha256=sha256(p2/(sid+'.json'))))
    write(root/'SESSIONS.json',sessions);write(content/'RECORDS.json',features);np.save(content/'VECTORS.npy',np.asarray(vectors,np.float32),allow_pickle=False)
    model=Path.cwd()/'results/phase_2_4_stage_15/raw/drive-content-features-v2/MODEL.json'
    (content/'MODEL.json').write_bytes(model.read_bytes())
    write(content/'COMPLETE.json',dict(status='COMPLETE',outputs={n:sha256(content/n) for n in ('MODEL.json','VECTORS.npy','RECORDS.json')}))
    write(p2/'INDEX.json',timelines);write(p2/'COMPLETE.json',dict(status='COMPLETE',outputs={'INDEX.json':sha256(p2/'INDEX.json')}))
    write(p5/'INDEX.json',[dict(session=r['session']) for r in sessions]);paths=dict(sessions=str(root/'SESSIONS.json'),content_model=str(content/'MODEL.json'))
    write(p5/'INPUTS.json',dict(paths=paths,sha256=input_hashes(paths)))
    write(p5/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,outputs={n:sha256(p5/n) for n in ('INDEX.json','INPUTS.json')}))
    write(p6/'INDEX.json',ledger);write(p6/'PLAN.json',dict(inputs={'prepared_sessions':paths['sessions']},pins={paths['sessions']:sha256(paths['sessions'])}))
    write(p6/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,outputs={n:sha256(p6/n) for n in ('INDEX.json','PLAN.json')}))
    inputs=paths|dict(content_records=str(content/'RECORDS.json'),content_vectors=str(content/'VECTORS.npy'),content_complete=str(content/'COMPLETE.json'),
        foundation_complete=str(p2/'COMPLETE.json'),session_index=str(p2/'INDEX.json'),p5_inputs=str(p5/'INPUTS.json'),p5_index=str(p5/'INDEX.json'),
        p5_completion=str(p5/'COMPLETE.json'),p6_index=str(p6/'INDEX.json'),p6_plan=str(p6/'PLAN.json'),p6_completion=str(p6/'COMPLETE.json'))
    config=old.CONFIG|dict(bootstrap=40,threads=1);binding=dict(inputs=input_hashes(inputs),config=config)
    original=root/'original';output=original/'output';output.mkdir(parents=True);write(output/'BINDING.json',binding)
    data=old.source.load(inputs);bykey={r['key']:r for r in raw};inventory={}
    for sid in sorted(data['sessions']):
        batch,support,pins=old.source.session_rows(data,sid)
        for row in batch:row.update(window_vector=bykey[row['key']]['window_vector'],visibility=dict(synthetic=True))
        path=output/'sessions'/(sid+'.json');write(path,dict(binding=binding,rows=batch,support=support,source_pins=pins));write(path.with_suffix('.seal.json'),dict(sha256=sha256(path)))
        inventory[sid]=dict(sha256=sha256(path),seal_sha256=sha256(path.with_suffix('.seal.json')),bytes=path.stat().st_size)
    pins={str(Path(v).resolve()):sha256(v) for v in inputs.values()}
    for module in (old,old.source):pins[str(Path(module.__file__).resolve())]=sha256(module.__file__)
    write(original/'PLAN.json',dict(module='runners.drive.cards.menus_d20',card='D20',inputs=inputs,config=config,pins=pins,
        at='2026-10-18T00:00:00+00:00',max_wall_seconds=10800,max_output_bytes=536870912))
    write(original/'FAILED.json',dict(status='FAILED',error="RuntimeError('Frozen output byte cap exceeded')",engineering_retry_available=True,at='2026-10-18T00:00:10+00:00'))
    write(original/'INVENTORY.json',dict(original_plan_sha256=sha256(original/'PLAN.json'),original_failure_sha256=sha256(original/'FAILED.json'),sessions=inventory))
    inherited=inputs|dict(original_plan=str(original/'PLAN.json'),original_failure=str(original/'FAILED.json'),original_inventory=str(original/'INVENTORY.json'))
    recovered=root/'recovery';recovered.mkdir()
    write(recovered/'PLAN.json',dict(module='runners.drive.cards.menus_d20_recovery',inputs=inherited,config=config,
        pins={str(Path(v).resolve()):sha256(v) for v in inherited.values()},max_output_bytes=536870912,max_wall_seconds=10790))
    recovery.execute(recovered/'output',inherited,config)
    assert recovery.verify(recovered/'output',inherited,config)['verified']
    write(recovered/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,synthetic=True,
        outputs={p.relative_to(recovered).as_posix():sha256(p) for p in recovered.rglob('*') if p.is_file()}))
    return inherited|dict(primary_plan=str(recovered/'PLAN.json'),primary_complete=str(recovered/'COMPLETE.json'),
        primary_summary=str(recovered/'output'/'SUMMARY.json'),primary_comparisons=str(recovered/'output'/'COMPARISONS.json.gz')),d.CONFIG|dict(bootstrap=40,checkpoint_draws=20)


def test_serialized_yield_resume_fresh_process_and_mutation_refusal(tmp_path):
    inputs,config=fixture(tmp_path);output=tmp_path/'output';output.mkdir();write(output/'YIELD_REQUEST.json',{})
    assert d.execute(output,inputs,config)['status']=='yielded'
    assert len(list((output/'sources').glob('*.gz')))==1
    (output/'YIELD_REQUEST.json').unlink();report=d.execute(output,inputs,config)
    assert report['primary']['state']=='positive'
    assert report['arms']['lexical']['identity']['own_minus_fake']['state']=='positive'
    assert report['arms']['lexical']['outcome_permutation']['reliability']['draws']==200
    before={str(p):sha256(p) for p in output.rglob('*') if p.is_file()}
    assert d.execute(output,inputs,config)==report
    assert before=={str(p):sha256(p) for p in output.rglob('*') if p.is_file()}
    request=tmp_path/'REQUEST.json';write(request,dict(output=str(output),inputs=inputs,config=config))
    code='import json,sys;from runners.drive.cards.events_d20_extension import verify;r=json.load(open(sys.argv[1]));assert verify(**r)["all_draws_recomputed"]'
    subprocess.run([sys.executable,'-B','-c',code,str(request)],check=True,timeout=90,env=os.environ|dict(PYTHONHASHSEED='319'))
    path=next((output/'draws').glob('bootstrap-*.json'));path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(ValueError,match='changed'):d.verify(output,inputs,config)


def test_changed_source_and_closed_gate_refuse(tmp_path):
    inputs,config=fixture(tmp_path)
    path=Path(inputs['sessions']);path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(ValueError,match='pin changed'):source.context(inputs)
    null_inputs,_=fixture(tmp_path/'null',world='null')
    with pytest.raises(ValueError,match='gate is closed'):source.context(null_inputs)


def test_reliability_original_seed_draws_and_singleton_support():
    _,comp,writers,_=kernel_rows(rows(),'lexical');config=old.CONFIG|dict(bootstrap=40)
    expected=old.summarize(comp,writers,config,reliability=True)['split_half_reliability']
    design=stats.Design(comp,writers);rng=np.random.default_rng(config['seed']);draws=[]
    for _ in range(config['bootstrap']):
        weights=np.bincount(rng.integers(8,size=8),minlength=8);_,_,halves=design.values(weights)
        draws.append(design.correlation(halves,weights))
    point=design.correlation(design.values(np.ones(8))[2],np.ones(8),4)
    actual=old.intervals.interval(point,draws,config)
    assert actual['effect']==pytest.approx(expected['effect']);assert actual['ci95']==pytest.approx(expected['ci95'])
    assert actual['undefined_draws']==expected['undefined_draws']
    assert stats.permutation([['a'],['b']],20261018,19)=={'a':'a','b':'b'}
