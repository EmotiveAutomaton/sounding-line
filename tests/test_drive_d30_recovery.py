"""Certified numerical continuation, frozen successful fits and retained replay."""
import json,copy
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from runners.drive.cards import crossed_reml_certified as solver
from runners.drive.cards import timing_d30_crossed_recovery as recovery
from runners.drive.cards.timing_census import read,write,filehash
from runners.drive.cards.timing_p6 import gzread
from tests.test_drive_d30_crossed_week import constructed,supported_sources,SMALL


def test_successful_fits_are_exact_and_variance_failures_still_refuse():
    for signal in (0,1,-1):
        matrix=constructed(signal)
        assert solver.fit(**matrix)==solver.old.fit(**matrix)
    matrix=constructed(0);matrix['y']=[0.]*len(matrix['y'])
    with pytest.raises(ValueError,match='residual variance'):solver.fit(**matrix)


def test_certified_continuation_uses_original_tolerances_and_refuses_bad_cases():
    def good(x):return dict(objective=100+float(np.dot(x-1,x-1))),2*(x-1)
    result=SimpleNamespace(success=False,status=2,message='ABNORMAL: ',x=np.array([1+4e-6,1+2e-6]),nit=7)
    x,cert=solver.polish(good,result,10)
    assert max(abs(x-1))<1e-12 and cert['projected_gradient_max']<=1e-6
    assert cert['function_tolerance']==1e-10 and cert['positive_curvature_verified']
    with pytest.raises(ValueError,match='only abnormal'):
        solver.polish(good,SimpleNamespace(**dict(result.__dict__,status=1)),10)
    with pytest.raises(ValueError,match='iteration limit'):
        solver.polish(good,SimpleNamespace(**dict(result.__dict__,nit=200)),10)
    def saddle(x):return dict(objective=float(x[0]**2-x[1]**2)),np.array([2*x[0],-2*x[1]])
    with pytest.raises(ValueError,match='curvature'):solver.polish(saddle,result,10)
    far=SimpleNamespace(**dict(result.__dict__,x=np.array([2.,2.])))
    with pytest.raises(ValueError,match='cannot improve|iteration limit'):solver.polish(good,far,10)


def test_original_variance_ceiling_still_refuses(monkeypatch):
    monkeypatch.setattr(solver.old.original,'MAX_RATIO',.001)
    with pytest.raises(ValueError,match='variance ceiling'):solver.fit(**constructed())


def test_retained_actual_failure_is_strictly_certified():
    path=Path('.agent-state/drive-20261018-week/D30_FAILED_MATRIX.json.gz')
    if not path.exists():pytest.skip('private retained failure fixture')
    matrix=gzread(path)
    with pytest.raises(ValueError,match='ABNORMAL'):solver.old.fit(**matrix)
    answer=solver.fit(**matrix)
    cert=answer['numerical_certificate']
    assert answer['converged'] and cert['projected_gradient_max']<1e-6
    assert cert['newton_steps']==1 and answer['iterations']<=200
    assert solver.fit(**matrix)==answer


def native_inputs(root):
    root=Path(root);inputs=supported_sources(root/'source')
    base=recovery.base;base.CONFIG=SMALL
    output=root/'failed/output';write(output/'YIELD_REQUEST.json',{})
    assert base.execute(output,inputs,SMALL)['status']=='yielded'
    failed=output.parent
    write(failed/'OWNER.json',dict(at='2026-10-19T00:00:00+00:00'))
    write(failed/'PLAN.json',dict(module=base.__name__,config=SMALL,inputs=inputs,
          pins={str(Path(base.__file__).resolve()):filehash(base.__file__)},prior_wall_seconds_charged=20.))
    write(failed/'FAILED.json',dict(status='FAILED',at='2026-10-19T00:00:10+00:00'))
    return dict(inputs,failed_attempt=str(failed/'FAILED.json'))


def execute(output,inputs,config):
    assert config==SMALL;recovery.base.CONFIG=SMALL
    report=recovery.execute(output,inputs,config)
    assert report['state']=='positive'
    return report


def verify(output,inputs,config):
    assert config==SMALL;recovery.base.CONFIG=SMALL
    result=recovery.verify(output,inputs,config)
    result['actual_failure_certificate_passed']=True
    test_retained_actual_failure_is_strictly_certified()
    return result


def test_full_handler_reuses_exact_prefix_and_rejects_mutation(tmp_path,monkeypatch):
    monkeypatch.setattr(recovery.base,'CONFIG',SMALL)
    inputs=native_inputs(tmp_path/'source');output=tmp_path/'retry'
    original=Path(inputs['failed_attempt']).parent/'output/bootstrap/block-00000.json'
    before=original.read_bytes();result=recovery.execute(output,inputs,SMALL)
    assert (output/'bootstrap/block-00000.json').read_bytes()==before==original.read_bytes()
    assert recovery.verify(output,inputs,SMALL)['primary']==result
    assert read(output/'TIMING.json')['prior_seconds_charged']==210
    assert recovery.execute(output,inputs,SMALL)==result
    original.write_bytes(before+b' ')
    with pytest.raises(ValueError,match='checkpoint changed'):recovery.source(inputs,SMALL)
