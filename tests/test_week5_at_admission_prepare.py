"""Constructed metadata/refusal tests; no native or pretrained-model work."""
import json
from pathlib import Path
import pytest
from runners.drive.cards import week5_at_admission_prepare as driver


def write(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True)+'\n',encoding='utf8')


def reseal(root):
    done=driver.read(root/'COMPLETE.json')
    done['outputs']={p.relative_to(root).as_posix():driver.sha(p) for p in root.rglob('*')
                     if p.is_file() and p.name!='COMPLETE.json'}
    write(root/'COMPLETE.json',done)


def constructed_receipt(tmp_path, monkeypatch):
    monkeypatch.setattr(driver,'REPO',tmp_path)
    monkeypatch.setattr(driver,'BASE',tmp_path/'raw')
    root=tmp_path/'raw/AT2-constructed';root.mkdir(parents=True)
    dep=tmp_path/'constructed-kernel.txt';dep.write_text('fixture-only',encoding='utf8')
    write(root/'PLAN.json',dict(campaign='S15-WEEK5',family='AT',module='constructed-only',pins={str(dep):driver.sha(dep)}))
    write(root/'VERIFIED.json',dict(verified=True,fixture_only=True))
    for phase,cost in [('EXECUTE',2),('VERIFY',3)]:
        write(root/(phase+'_JOB_USAGE.json'),dict(cpu_seconds=cost,includes_all_descendants_and_exited_processes=True,exit_code=0,fixture_only=True))
    write(root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,cpu_seconds=5,outputs={},fixture_only=True))
    reseal(root)
    identities=[]
    monkeypatch.setattr(driver,'stopped_owner',lambda r,h:identities.append((r,h)))
    return root,identities


def test_completed_native_schema_requires_both_actual_phase_counts(tmp_path,monkeypatch):
    root,identities=constructed_receipt(tmp_path,monkeypatch)
    assert driver.complete(root,'constructed-only')[2]['cpu_seconds']==5
    assert len(identities)==1
    done=driver.read(root/'COMPLETE.json');done['cpu_seconds']=4
    write(root/'COMPLETE.json',done)
    with pytest.raises(driver.Refusal,match='undercounts'):
        driver.complete(root,'constructed-only')


def test_complete_label_cannot_replace_verified_or_descendant_accounting(tmp_path,monkeypatch):
    root,_=constructed_receipt(tmp_path,monkeypatch)
    write(root/'VERIFIED.json',dict(status='yielded',fixture_only=True));reseal(root)
    with pytest.raises(driver.Refusal,match='verified=True'):
        driver.complete(root)
    write(root/'VERIFIED.json',dict(verified=True,fixture_only=True))
    usage=driver.read(root/'VERIFY_JOB_USAGE.json');usage['includes_all_descendants_and_exited_processes']=False
    write(root/'VERIFY_JOB_USAGE.json',usage);reseal(root)
    with pytest.raises(driver.Refusal,match='descendant accounting'):
        driver.complete(root)


def test_failed_evidence_and_changed_pin_never_disappear(tmp_path,monkeypatch):
    root,_=constructed_receipt(tmp_path,monkeypatch)
    write(root/'FAILED.json',dict(fixture_only=True))
    with pytest.raises(driver.Refusal,match='Ambiguous'):
        driver.complete(root)
    # This deletion is confined to a disposable constructed test fixture.
    (root/'FAILED.json').unlink()
    Path(next(iter(driver.read(root/'PLAN.json')['pins']))).write_text('changed',encoding='utf8')
    with pytest.raises(driver.Refusal,match='Frozen dependency changed'):
        driver.complete(root)


def test_guard_measurement_uses_only_sealed_actual_phases(tmp_path):
    root=tmp_path/'constructed';root.mkdir()
    def receipt(phase,peak):
        return dict(status='returned',phase=phase,limits=driver.NATIVE_LIMITS,
                    initial=dict(commit_headroom_bytes=30*2**30,ram_available_bytes=30*2**30),
                    peak_working_set_bytes=peak,fixture_only=True)
    write(root/'output/GUARD_EXECUTE_fixture.json',receipt('execute',2**30))
    write(root/'output/GUARD_VERIFY_fixture.json',receipt('verify',2*2**30))
    write(root/'COMPLETE.json',dict(outputs={'output/GUARD_EXECUTE_fixture.json':'fixture','output/GUARD_VERIFY_fixture.json':'fixture'}))
    assert driver.guard_measurement(root)['peak_working_set_GiB']==2
    write(root/'output/GUARD_VERIFY_later.json',receipt('verify',99*2**30))
    assert driver.guard_measurement(root)['peak_working_set_GiB']==2
    value=receipt('verify',2*2**30);value['limits']=dict(driver.NATIVE_LIMITS,cooperative_grace_seconds=600)
    write(root/'output/GUARD_VERIFY_fixture.json',value)
    with pytest.raises(driver.Refusal,match='thresholds or grace'):
        driver.guard_measurement(root)


def test_full_pilot_requires_exact_coverage_and_no_duplicate_charge(monkeypatch):
    proposal=dict(model='constructed',model_manifest_sha256='fixture')
    with pytest.raises(driver.Refusal,match='all165'):
        driver.pilot_envelope([],proposal)
    def chunk(i,p):
        return dict(root=str(i),batch_ordinal=i,words=164 if i<164 else 111,
                    peak_working_set_GiB=2,chain=[dict(root='shared-attempt',cpu_seconds=1,supervisor_envelope_cpu_seconds=30)])
    # 164*164+111=27007 is the frozen work-count equality, not invented data.
    monkeypatch.setattr(driver,'measured_chunk',chunk)
    with pytest.raises(driver.Refusal,match='two chunks'):
        driver.pilot_envelope(list(range(165)),proposal)
    with pytest.raises(driver.Refusal,match='Duplicate/missing'):
        driver.pilot_envelope([0]*165,proposal)


@pytest.mark.parametrize('value',[None,True,-1,float('nan'),float('inf')])
def test_unmeasured_or_invalid_value_is_not_a_zero_cost(value):
    with pytest.raises(driver.Refusal):driver.finite(value)


def test_unknown_stage_and_missing_owner_review_refuse_before_git():
    with pytest.raises(driver.Refusal,match='Unknown explicit'):
        driver.prepare(dict(stage='launch_everything'))
    with pytest.raises(driver.Refusal,match='Explicit owner stage'):
        driver.design_review({},'guard_fixture','unused')
