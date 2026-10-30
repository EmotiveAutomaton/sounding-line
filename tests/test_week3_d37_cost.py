"""D37 production-source admission and full-unit cost boundary checks.

DESIGN CHECK: LESSONS 3-5. Same population under null/alternative; probe never
emits a partial effect. Complete known-answer units replay and changed source
or retained metadata refuses before a final receipt.
"""
from pathlib import Path
import numpy as np
import pytest
from runners.stage14.common import REPO
from runners.drive.cards import week3_d37_cost as cost
from runners.drive.cards import week3_d37_workload as work
from runners.drive.cards import week3_d37_readers as core
from runners.drive.cards.timing_census import read,filehash
from runners.drive.cards.timing_p6 import write_equal


def inputs():
    raw=REPO/'results/phase_2_4_stage_15/raw'
    return dict(source_complete=str(raw/'drive-week3-20261025/D37-inputs/COMPLETE.json'),
                source_landing=str(REPO/'.agent-state/drive-20261029/D37_INPUT_CORPUS_LANDED.json'),
                d15_complete=str(raw/'drive-wave-20261017-w1/D15/COMPLETE.json'),
                d15_landing=str(REPO/'results/phase_2_4_stage_15/DRIVE/D15.json'))


def test_actual_producer_consumer_admission_and_tamper(tmp_path):
    config=inputs(); rows,a,parts,y,excluded=work.source(config)
    assert len(rows)==16855 and len(parts)==41 and len(excluded)==20
    assert set(a)=={'page','process','embedding'} and len(y)==len(rows)
    original=read(config['source_landing']); changed=tmp_path/'changed.json'
    write_equal(changed,original|dict(completion_sha256='0'*64))
    with pytest.raises(ValueError,match='Unlanded'):work.source(config|dict(source_landing=str(changed)))


def test_frozen_world_laws_and_partitions():
    for n in (0,10,20):
        rows,a,parts,y,meta=work.world(n); truth=np.array(meta['truth'])
        assert len(rows)==768 and len(parts)==8 and len(set(y))==4
        assert np.allclose(truth.sum(1),1) and np.all(truth>=0)
        if n==0:assert np.array_equal(truth,np.full((768,4),.25))
        if n==10:assert np.array_equal(truth,.75*a['page']+.25/4)
        if n==20:
            person=np.eye(4)[[int(r['writer'][1:])%4 for r in rows]]
            assert np.array_equal(truth,(a['page']+a['process']+person)/3)
        for p in parts.values():core.partition_indices(rows,p)


def test_complete_forecast_counts_every_reference_and_replay():
    t=dict(human=dict(preprocess_max=2,fit_max=3,history_max=4,recipients=41),
           constructed=dict(preprocess_max=5,fit_max=6,history_max=7,recipients=8))
    f=cost.forecast(t)
    assert f['human_cpu_seconds']==6*(82+201*(4+3*41)+60)
    assert f['calibration_cpu_seconds']==6*(30*(40+201*(7+6*8))+60)
    assert f['full_cpu_seconds']==f['human_cpu_seconds']+f['calibration_cpu_seconds']


def test_cluster_summary_exact_identity_and_strong_known_gain():
    def predictions(gain):
        result=[]
        for w in range(4):
            for s in range(3):
                for j in range(s+1):
                    truth=np.eye(4)[j%4].tolist(); uniform=[.25]*4
                    result.append(dict(key=f'{w}-{s}-{j}',writer=str(w),session=f'{w}-{s}',truth=j%4,single=uniform,
                                       stack=truth if gain else uniform,entries=[uniform]*3))
        return result
    zero=work.summarize(predictions(False),np.zeros(200))
    assert zero['estimate']==0 and zero['interval95']==[0,0] and zero['state']=='null'
    positive=work.summarize(predictions(True),np.zeros(200))
    assert positive['estimate']==.375 and positive['useful_licensed_detection']
    with pytest.raises(ValueError,match='Incomplete'):work.summarize(predictions(True),np.zeros(199))


def fixture_loader(_):
    r,a,p,y,meta=work.world(20)
    return r,a,p,y,[]


def test_actual_cost_handler_fresh_replay_and_metadata_refusal(tmp_path):
    source=tmp_path/'fixture.json';write_equal(source,dict(constructed=True)); inp=dict(fixture=str(source)); out=tmp_path/'out'
    cost.one_pass(out,inp,cost.CONFIG,loader=fixture_loader)
    assert cost.one_pass(out,inp,cost.CONFIG,True,fixture_loader)['full_cost_unit_replay']
    assert read(out/'FORECAST.json')['permutations']==200
    probe=read(out/'PROBE.json'); (out/'PROBE.json').write_text('{}',encoding='utf8')
    with pytest.raises(ValueError,match='Fresh complete'):cost.one_pass(out,inp,cost.CONFIG,True,fixture_loader)
    assert probe['scientific_admission'] is False


def execute(output,inputs,config):
    if config!=cost.CONFIG or set(inputs)!={'fixture'} or read(inputs['fixture'])!={'constructed':True}:raise ValueError('Invalid fixture')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    return cost.one_pass(output,inputs,config,loader=fixture_loader)


def verify(output,inputs,config):
    return cost.one_pass(output,inputs,config,True,fixture_loader)
