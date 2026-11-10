from pathlib import Path
from datetime import datetime,timezone,timedelta
import json
import pytest
from runners.drive.cards import week5_policy_v2 as policy

def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value),encoding='utf8')

def attempt(root):
    folder=root/'job';folder.mkdir()
    save(folder/'PLAN.json',dict(campaign='S15-WEEK5',family='CH',max_cpu_seconds=100))
    (folder/'ATTEMPT.claim').touch()
    save(folder/'BUDGET_PROGRESS.json',dict(at=datetime.now(timezone.utc).isoformat(),cpu_seconds=7))
    return folder

def test_transient_read_recovers_without_losing_cpu(tmp_path,monkeypatch):
    attempt(tmp_path);original=policy.raw_read;calls=[]
    def intermittent(path):
        if Path(path).name=='BUDGET_PROGRESS.json' and len(calls)<2:
            calls.append(1);raise PermissionError('constructed sharing violation')
        return original(path)
    monkeypatch.setattr(policy,'raw_read',intermittent)
    value=policy.charges(tmp_path)['CH']
    assert len(calls)==2 and 41<=value<43

def test_repeated_denial_fails_closed(tmp_path,monkeypatch):
    attempt(tmp_path);original=policy.raw_read;calls=[]
    def denied(path):
        if Path(path).name=='BUDGET_PROGRESS.json':calls.append(1);raise PermissionError('constructed persistent denial')
        return original(path)
    monkeypatch.setattr(policy,'raw_read',denied)
    with pytest.raises(policy.AccountingReadError,match='six attempts'):policy.charges(tmp_path)
    assert len(calls)==6

def test_malformed_or_disappeared_accounting_never_becomes_zero(tmp_path):
    folder=attempt(tmp_path);(folder/'BUDGET_PROGRESS.json').write_text('{')
    with pytest.raises(policy.AccountingReadError):policy.charges(tmp_path)
    with pytest.raises(policy.AccountingReadError):policy.read(folder/'nonexistent.json')

def test_unknown_stale_and_unstarted_dispositions(tmp_path):
    folder=attempt(tmp_path)
    save(folder/'BUDGET_PROGRESS.json',dict(at=(datetime.now(timezone.utc)-timedelta(seconds=60)).isoformat(),cpu_seconds=7))
    assert policy.charges(tmp_path)['CH']==130
    (folder/'BUDGET_PROGRESS.json').unlink()
    assert policy.charges(tmp_path)['CH']==130
    (folder/'ATTEMPT.claim').unlink()
    assert policy.charges(tmp_path)['CH']==0

def test_terminal_failure_charge_and_ambiguity(tmp_path):
    folder=attempt(tmp_path);save(folder/'FAILED.json',dict(cpu_seconds=9))
    assert policy.charges(tmp_path)['CH']==39
    save(folder/'COMPLETE.json',dict(cpu_seconds=9))
    with pytest.raises(ValueError,match='Ambiguous'):policy.charges(tmp_path)

def test_future_progress_and_missing_budget_root_refuse(tmp_path):
    folder=attempt(tmp_path)
    save(folder/'BUDGET_PROGRESS.json',dict(at=(datetime.now(timezone.utc)+timedelta(days=1)).isoformat(),cpu_seconds=7))
    with pytest.raises(ValueError,match='future'):policy.charges(tmp_path)
    with pytest.raises(policy.AccountingReadError):policy.charges(tmp_path/'missing')

def test_started_child_missing_usage_never_becomes_zero(tmp_path):
    from runners.drive.cards.week5_runtime_v4 import failure_charge
    assert failure_charge(tmp_path,{'max_cpu_seconds':100},['execute'],0)==(100,True)
    assert failure_charge(tmp_path/'absent',{'max_cpu_seconds':100},['execute'],7)==(100,True)
    save(tmp_path/'EXECUTE_JOB_USAGE.json',dict(cpu_seconds=17))
    assert failure_charge(tmp_path,{'max_cpu_seconds':100},['execute'],0)==(17,False)
    assert failure_charge(tmp_path,{'max_cpu_seconds':100},[],0)==(0,False)

def test_inaccessible_attempt_directory_cannot_disappear_from_accounting(tmp_path,monkeypatch):
    folder=attempt(tmp_path);original=Path.stat
    def denied(path,*args,**kwargs):
        if path==folder:raise PermissionError('constructed directory denial')
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'stat',denied)
    with pytest.raises(policy.AccountingReadError):policy.charges(tmp_path)
