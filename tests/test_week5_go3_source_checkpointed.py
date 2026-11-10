from pathlib import Path
import json,math
import pytest
from runners.drive.cards import week5_go3_source_checkpointed as s


@pytest.mark.parametrize('read_size,resume_size',[(1,1),(7,7),(64,64),(4096,4096),(1,7),(7,1),(64,7)])
def test_exact_byte_pilot_and_partial_utf8_row_resume(tmp_path,monkeypatch,read_size,resume_size):
    monkeypatch.setattr(s,'READ_BYTES',read_size)
    folder=tmp_path/'xml';folder.mkdir()
    posts='<posts><row Id="1" OwnerUserId="a" /></posts>'.encode()
    history='<posthistory><row Id="1" PostId="1" PostHistoryTypeId="2" CreationDate="0" UserId="a" Text="café &amp; old"/><row Id="2" PostId="1" PostHistoryTypeId="5" CreationDate="1" UserId="b" Comment="fix grammar" Text="café &amp; new"/></posthistory>'.encode()
    for name,raw in zip(s.integrity.TARGETS,(posts,history)):(folder/name).write_bytes(raw)
    sizes=[len(posts),len(history)];binding={'fixture':True};db,state=s.open_state(tmp_path,binding)
    with pytest.raises(s.Pause,match='exact first-five-percent'):
        s.ingest(db,state,tmp_path,b'x'*32,'writers',sizes,lambda:False)
    assert sum(state['bytes'])==math.ceil(.05*sum(sizes))
    db.close();s.seal(tmp_path,state)
    monkeypatch.setattr(s,'READ_BYTES',resume_size)
    db,state=s.open_state(tmp_path,binding)
    s.ingest(db,state,tmp_path,b'x'*32,'writers',sizes,lambda:False)
    assert state['bytes']==sizes and state['records']==[1,2]
    assert db.execute('SELECT body FROM history ORDER BY ordinal').fetchall()==[('café & old',),('café & new',)]
    assert state['counts']=={'posts':1,'history_rows':2}
    db.close()


def test_changed_checkpoint_binding_refuses(tmp_path):
    db,state=s.open_state(tmp_path,{'fixture':1});db.close();s.seal(tmp_path,state)
    with pytest.raises(ValueError,match='binding differs'):s.open_state(tmp_path,{'fixture':2})
