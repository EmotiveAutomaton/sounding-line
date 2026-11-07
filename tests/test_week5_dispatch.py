import json
from pathlib import Path
import pytest
from runners.drive.week5_dispatch import candidates
from runners.stage14.common import filehash

def entry(base,name,priority):
    p=base/name;p.mkdir();(p/'PLAN.json').write_text('{}')
    return dict(root=str(p),priority=priority,plan_sha256=filehash(p/'PLAN.json'))

def test_priority_and_terminal_attempt_guards(tmp_path):
    a=entry(tmp_path,'late',9);b=entry(tmp_path,'first',1);c=entry(tmp_path,'completed',0)
    (Path(c['root'])/'COMPLETE.json').write_text('{}')
    assert candidates(dict(entries=[a,b,c]),tmp_path)==[b,a]
    (Path(b['root'])/'ATTEMPT.claim').write_text('owner')
    assert candidates(dict(entries=[a,b,c]),tmp_path)==[a]

def test_changed_plan_and_duplicate_identity_refuse(tmp_path):
    a=entry(tmp_path,'only',1)
    with pytest.raises(ValueError,match='Duplicate'):candidates(dict(entries=[a,a]),tmp_path)
    (Path(a['root'])/'PLAN.json').write_text('{"changed":true}')
    with pytest.raises(ValueError,match='changed'):candidates(dict(entries=[a]),tmp_path)
