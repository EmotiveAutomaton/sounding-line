import json
from pathlib import Path
import numpy as np
import pytest
from runners.drive.cards import timing_d17 as original
from runners.drive.cards import timing_d17_recovery as repair
from runners.drive.cards.timing_census import read,write,filehash


def test_slow_overlapping_components_recover_known_boundary_with_same_tolerance():
    values=np.ones(100);means=np.array([0.,.001]);variances=np.ones(2);initial=np.array([.5,.5])
    with pytest.raises(ValueError,match='failed to converge'):
        original.session_weights(values,means,variances,initial)
    result=repair.session_weights(values,means,variances,initial)
    assert result[1]>1-1e-8
    check,_=repair.certificate(repair.density_matrix(values,means,variances),result)
    assert check['fixed_point_residual']<1e-8 and check['convex_duality_gap']<1e-8
    opposite=repair.accelerated_weights(-values,means,variances,initial)
    assert opposite[0]>1-1e-8


def test_already_convergent_fits_are_byte_identical():
    rng=np.random.default_rng(21);means=np.array([-1.,1.]);variances=np.array([.3,.4]);initial=np.array([.5,.5])
    values=np.r_[rng.normal(-1,.3,50),rng.normal(1,.3,50)]
    assert np.array_equal(original.session_weights(values,means,variances,initial),repair.session_weights(values,means,variances,initial))


def test_optimizer_success_without_certificate_is_refused(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(repair,'minimize',lambda *a,**k:SimpleNamespace(success=True,x=np.array([1.,0.])))
    with pytest.raises(ValueError,match='failed convergence certificate'):
        repair.accelerated_weights(np.ones(100),np.array([0.,.001]),np.ones(2),np.array([.5,.5]))


def test_nonfinite_density_and_bad_simplex_refused():
    with pytest.raises(ValueError):repair.density_matrix([np.nan],[0.],[1.])
    with pytest.raises(ValueError):repair.certificate(np.ones((2,2)),[1.,1.])


def test_actual_retained_nonconvergence_fixture_passes_certificate():
    path=Path('.agent-state/drive-20261017/D17_NONCONVERGENCE_FIXTURE.npz')
    if not path.exists():pytest.skip('private retained failure fixture not distributed')
    fixture=np.load(path)
    args=[fixture[n] for n in ('values','means','variances','initial')]
    with pytest.raises(ValueError,match='failed to converge'):original.session_weights(*args)
    result=repair.session_weights(*args)
    check,_=repair.certificate(repair.density_matrix(*args[:3]),result)
    assert check['fixed_point_residual']<1e-8 and check['convex_duality_gap']<1e-8


def recovery_inputs(tmp_path,monkeypatch):
    from tests.test_drive_cards_timing_d17 import serialized_inputs
    (tmp_path/'inputs').mkdir()
    original_inputs,config=serialized_inputs(tmp_path/'inputs')
    root=tmp_path/'original';out=root/'output'
    with monkeypatch.context() as m:
        def fail(*args):raise ValueError('session mixture weights failed to converge')
        m.setattr(original,'session_weights',fail)
        with pytest.raises(ValueError,match='failed to converge'):original.execute(out,original_inputs,config)
    write(root/'PLAN.json',dict(module='runners.drive.cards.timing_d17',inputs=original_inputs,config=config,pins={str(Path(original.__file__).resolve()):filehash(original.__file__)}))
    write(root/'FAILED.json',dict(status='FAILED',error='execute child exited 1'))
    inspection=dict(native_exit_verified=True,slot_released=True,primary_exists=False,failure_sha256=filehash(root/'FAILED.json'),plan_sha256=filehash(root/'PLAN.json'),prior_wall_seconds=10.)
    write(tmp_path/'inspection.json',inspection)
    files={p.relative_to(out).as_posix():filehash(p) for p in out.rglob('*') if p.is_file() and p.name!='D17_PROGRESS.json'}
    write(tmp_path/'retained.json',dict(files=files,failure_sha256=inspection['failure_sha256'],plan_sha256=inspection['plan_sha256']))
    return dict(original_plan=str(root/'PLAN.json'),original_failure=str(root/'FAILED.json'),inspection=str(tmp_path/'inspection.json'),retained=str(tmp_path/'retained.json'))


def test_actual_recovery_handler_reuses_bytes_fresh_verifies_and_reentry_is_immutable(tmp_path,monkeypatch):
    import subprocess,sys
    inputs=recovery_inputs(tmp_path,monkeypatch);output=tmp_path/'recovered'
    result=repair.execute(output,inputs,{})
    assert result['state']=='positive'
    binding=read(output/'RECOVERY_BINDING.json')
    assert all(filehash(output/name)==h for name,h in binding['files'].items())
    assert read(output/'D17_PROGRESS.json')['active_seconds']>=10
    write(tmp_path/'verify.json',dict(output=str(output),inputs=inputs))
    code="import json,sys;from pathlib import Path;from runners.drive.cards.timing_d17_recovery import verify;p=json.load(open(sys.argv[1]));print(json.dumps(verify(Path(p['output']),p['inputs'],{})))"
    done=subprocess.run([sys.executable,'-B','-c',code,str(tmp_path/'verify.json')],capture_output=True,text=True,check=True)
    assert json.loads(done.stdout)['verified']
    before={str(p):p.read_bytes() for p in output.rglob('*') if p.is_file()}
    assert repair.execute(output,inputs,{})==result
    assert before=={str(p):p.read_bytes() for p in output.rglob('*') if p.is_file()}


def test_changed_original_checkpoint_refuses_before_copying(tmp_path,monkeypatch):
    inputs=recovery_inputs(tmp_path,monkeypatch)
    path=Path(inputs['original_plan']).parent/'output/D17_MIXTURE_K1.json'
    path.write_text('{}')
    with pytest.raises(ValueError,match='retained checkpoint changed'):repair.execute(tmp_path/'recovered',inputs,{})
    assert not (tmp_path/'recovered').exists()


def test_unclosed_original_refuses_recovery(tmp_path,monkeypatch):
    inputs=recovery_inputs(tmp_path,monkeypatch)
    p=Path(inputs['inspection']);value=read(p);value['native_exit_verified']=False;p.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='did not close'):repair.execute(tmp_path/'recovered',inputs,{})
