"""Literal constructed durations and exact source/replay refusal cases.

DESIGN CHECK: arithmetic known answers and support/invalid-source dispositions
are fixed before original-source access; there is no effect-direction gate.
"""
from pathlib import Path
import copy,json,os
import pytest
from runners.drive.cards import week6_es_duration_v1 as adapter


def write(p, x):
    p.write_text(json.dumps(x), encoding='utf8')


def setup(tmp_path, rows=None):
    raw=tmp_path/'constructed.tsv'
    raw.write_text('id\tday\tbeep\temotion_chronometry\tunused_group\n'+(rows or
        'a\t1\t1\t0\tx\na\t1\t2\t10\tx\nb\t2\t1\t30\ty\nb\t3\t1\t120\ty\nNA\t2\t1\t90\tz\na\t2\t2\tNA\tx\n'),encoding='utf8')
    pin={'bytes':raw.stat().st_size,'sha256':adapter.source.sha256(raw)}
    panel={'member':'0045','card':'ES3','panel':'duration_minutes','source_pin':pin,
           'missing_tokens':['','NA'],'source_layout_review':copy.deepcopy(adapter.LAYOUT)}
    metadata=tmp_path/'metadata.json';admission=tmp_path/'admission.json'
    write(metadata,{'members':{'0045':{'raw_ts_pin_from_receipt_only':pin,'classification':'open-tests-only',
        'licence':{'name':'CC-BY-NC-4.0','attribution':'constructed fixture; no human source'}}}})
    review={'schema':'ES_OWNER_SOURCE_ADMISSION_V1','status':'OWNER_ADMITTED','member':'0045','cards':['ES3'],
        'source_pin':pin,'metadata_sha256':adapter.source.sha256(metadata),'missing_tokens':['','NA'],
        'source_layout_review':copy.deepcopy(adapter.LAYOUT)}
    write(admission,review)
    inputs={'source_path':str(raw),'metadata_path':str(metadata),'metadata_sha256':adapter.source.sha256(metadata),
        'source_admission_path':str(admission),'source_admission_sha256':adapter.source.sha256(admission)}
    return tmp_path/'output',inputs,{'panel_config':panel,'max_wall_seconds':30}


def test_literal_untrimmed_minutes_and_complete_replay(tmp_path):
    out,inputs,config=setup(tmp_path)
    first=adapter.execute(out,inputs,config)
    assert first['status']=='computed' and first['verified'] is False
    s=first['engine']['summary']
    assert s==dict(status='DESCRIPTIVE_ONLY',unit='self-estimated current-state minutes',eligible_rows=4,people=2,
        minimum=0.,q25=7.5,median=20.,q75=52.5,maximum=120.,mean=40.,outlier_trimming=False,
        diagnostic_groups_read=False,source_rows=6,missing_id_rows=1,missing_duration_rows=1)
    assert adapter.verify(out,inputs,config)['verified'] is True


def test_no_recorded_duration_is_explicitly_unsupported(tmp_path):
    out,inputs,config=setup(tmp_path,'a\t1\t1\tNA\tx\n')
    assert adapter.execute(out,inputs,config)['engine']['status']=='UNSUPPORTED_NO_RECORDED_DURATION'
    assert adapter.verify(out,inputs,config)['verified'] is True


@pytest.mark.parametrize('value',['-1','NaN','inf','unknown'])
def test_invalid_duration_refuses_without_complete(tmp_path,value):
    out,inputs,config=setup(tmp_path,f'a\t1\t1\t{value}\tx\n')
    with pytest.raises(ValueError):adapter.execute(out,inputs,config)
    assert not (out/'execute/ENGINE_RESULT.json').exists()


@pytest.mark.parametrize('fault',['metadata_pin','admission_pin','member','panel','unit','extra_field','wall'])
def test_metadata_and_measure_mutations_refuse_before_rows(tmp_path,monkeypatch,fault):
    out,inputs,config=setup(tmp_path)
    if fault=='metadata_pin':inputs['metadata_sha256']='0'*64
    elif fault=='admission_pin':inputs['source_admission_sha256']='0'*64
    elif fault=='member':config['panel_config']['member']='0057'
    elif fault=='panel':config['panel_config']['panel']='group_comparison'
    elif fault=='unit':config['panel_config']['source_layout_review']['duration_unit']='hours'
    elif fault=='extra_field':config['panel_config']['trim_outliers']=True
    elif fault=='wall':config['max_wall_seconds']=1501
    def forbidden(*args,**kwargs):raise AssertionError('source opened before metadata rejection')
    monkeypatch.setattr(adapter.clock,'selected_frames',forbidden)
    with pytest.raises(ValueError):adapter.execute(out,inputs,config)


def test_replay_requires_complete_execution(tmp_path):
    out,inputs,config=setup(tmp_path)
    with pytest.raises(ValueError):adapter.verify(out,inputs,config)


def test_source_changed_between_phases_refuses(tmp_path):
    out,inputs,config=setup(tmp_path);adapter.execute(out,inputs,config)
    with Path(inputs['source_path']).open('a') as stream:stream.write('a\t3\t3\t1\tx\n')
    with pytest.raises(ValueError):adapter.verify(out,inputs,config)


def test_changed_summary_refuses(tmp_path):
    out,inputs,config=setup(tmp_path);adapter.execute(out,inputs,config)
    write(out/'execute/SUMMARY.json',{'status':'changed'})
    with pytest.raises(ValueError):adapter.verify(out,inputs,config)


def test_requested_yield_cannot_complete(tmp_path):
    out,inputs,config=setup(tmp_path);out.mkdir();write(out/'YIELD_REQUEST.json',{})
    assert adapter.execute(out,inputs,config)['status']=='yielded'
    assert not (out/'execute/ENGINE_RESULT.json').exists()


def test_unknown_phase_refuses(tmp_path):
    out,inputs,config=setup(tmp_path)
    with pytest.raises(ValueError):adapter.operation(out,inputs,config,'unknown')


def test_exact_columns_selected_before_materialization(tmp_path,monkeypatch):
    out,inputs,config=setup(tmp_path);original=adapter.clock.pd.read_csv;seen=[]
    def observed(*args,**kwargs):
        seen.append(tuple(kwargs['usecols']))
        assert kwargs['usecols']==['id','day','beep','emotion_chronometry']
        return original(*args,**kwargs)
    monkeypatch.setattr(adapter.clock.pd,'read_csv',observed)
    adapter.execute(out,inputs,config)
    assert seen==[('id','day','beep','emotion_chronometry')]


def test_actual_loaded_modules_and_numerical_pools():
    from threadpoolctl import threadpool_info
    plan_path=Path(os.environ['ES_DURATION_QUAL_PLAN']);plan=json.loads(plan_path.read_text('utf8'))
    modules=[adapter,adapter.core,adapter.source,adapter.clock,adapter.io,adapter.base,adapter.clock.carry]
    witness={}
    for module in modules:
        path=Path(module.__file__).resolve();digest=adapter.source.sha256(path)
        assert plan['source_pins'][str(path)]==digest
        witness[module.__name__]={'path':str(path),'sha256':digest}
    pools=threadpool_info()
    assert pools and all(1<=pool['num_threads']<=2 for pool in pools)
    for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        assert os.environ[key] in ('1','2')
    write(plan_path.parent/'MODULE_WITNESS.json',{'modules':witness,'pools':pools,'source_records':'constructed only'})
