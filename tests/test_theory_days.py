"""Meaningful fail-closed admission and source-projection checks."""
from datetime import timedelta
from pathlib import Path
import zipfile
import pytest
from runners.theory_days import policy,intake
from runners.stage14.common import freeze

def plan():
    return dict(campaign='S15-THEORY-DAYS',numerical_threads=1,
      original_cpu_ceiling_seconds=100,prior_cpu_seconds_charged=0,
      max_cpu_seconds=100,max_wall_seconds=200,forecast_cpu_seconds=80,
      projected_peak_ram_GiB=2,premortem=dict(case_and_check='constructed',smaller_route='none'))

def resources():
    return dict(ram_available_GiB=20,commit_headroom_GiB=20,disk_free_GiB=30)

def test_admission_boundaries(tmp_path):
    args=dict(resources=resources(),lock_path=tmp_path/'absent',budget_root=tmp_path)
    assert policy.admission(plan(),at=policy.OPEN,**args)['campaign']=='S15-THEORY-DAYS'
    for clock in (policy.OPEN-timedelta(seconds=1),policy.FREEZE):
        with pytest.raises(RuntimeError): policy.admission(plan(),at=clock,**args)
    for change in ({'gpu':True},{'paid':True},{'numerical_threads':2},{'forecast_cpu_seconds':101}):
        with pytest.raises(ValueError): policy.admission(dict(plan(),**change),at=policy.OPEN,**args)

def test_shared_budget_never_credits_unknown(tmp_path):
    freeze(tmp_path/'one/PLAN.json',dict(max_cpu_seconds=54000))
    with pytest.raises(RuntimeError):
        policy.admission(plan(),at=policy.OPEN,resources=resources(),lock_path=tmp_path/'absent',budget_root=tmp_path)
    freeze(tmp_path/'one/FAILED.json',dict(error='unknown'))
    with pytest.raises(ValueError):policy.campaign_charge(tmp_path)

def test_archive_traversal(tmp_path):
    path=tmp_path/'bad.zip'
    with zipfile.ZipFile(path,'w') as z:z.writestr('../escape','bad')
    with pytest.raises(ValueError):intake.archive_inventory(path)

def test_author_never_requested_and_duplicates_rejected(tmp_path,monkeypatch):
    import pyarrow as pa
    import pyarrow.parquet as pq
    values={c:([0,0,0] if c in intake.LABELS else ['x','x','x']) for c in intake.COLUMNS}
    values.update(rater_id=[1,2,3],example_very_unclear=[False,False,True],author=['NEVER READ']*3)
    path=tmp_path/'source.parquet';pq.write_table(pa.table(values),path)
    original=pq.read_table
    def guarded(*args,**kwargs):
        assert kwargs['columns']==intake.COLUMNS and 'author' not in kwargs['columns']
        return original(*args,**kwargs)
    monkeypatch.setattr(pq,'read_table',guarded)
    assert len(intake.read_goemotions(path))==3
    values['rater_id']=[1,1,3];pq.write_table(pa.table(values),path)
    with pytest.raises(ValueError,match='Duplicate'):intake.read_goemotions(path)

def test_intake_reentry_and_corruption(tmp_path,monkeypatch):
    from runners.stage14.common import filehash
    src=tmp_path/'source';src.write_bytes(b'known bytes')
    monkeypatch.setattr(intake,'SOURCES',[('fixture','https://invalid.example',filehash(src),'fixture','readme.md')])
    inputs={'fixture':dict(path=str(src),sha256=filehash(src))}
    output=tmp_path/'out'
    result=intake.execute(output,inputs,{})
    assert result==intake.execute(output,inputs,{})
    assert intake.verify(output,inputs,{})['verified']
    (output/'readme.md').write_bytes(b'changed')
    with pytest.raises(ValueError):intake.verify(output,inputs,{})
