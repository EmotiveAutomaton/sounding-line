import json
from pathlib import Path
import pytest
from runners.drive.cards import timing_revision_input as card
from runners.drive.cards.timing_p6 import gzread,gzip_equal
from tests.test_drive_cards_timing_revision_source import fixture

CONFIG=dict(mode='constructed',expected_sessions=1,session_limit=1,cumulative_wall_seconds=120)

def test_complete_source_handler_reentry_and_fresh_replay(tmp_path):
    inputs=fixture(tmp_path/'source');out=tmp_path/'output'
    first=card.execute(out,inputs,CONFIG)
    assert first['original_occurrences']==2 and first['retained_changes']==1
    assert not first['classification_performed'] and not first['scientific_admission']
    before={p.name:p.read_bytes() for p in (out/'sessions').glob('*.gz')}
    assert card.execute(out,inputs,CONFIG)==first
    assert before=={p.name:p.read_bytes() for p in (out/'sessions').glob('*.gz')}
    assert card.verify(out,inputs,CONFIG)['summary']==first

def test_resume_retains_exact_prefix_and_source_guard(tmp_path):
    inputs=fixture(tmp_path/'source');out=tmp_path/'output';out.mkdir();(out/'YIELD_REQUEST.json').write_text('{}')
    assert card.execute(out,inputs,CONFIG)['status']=='yielded'
    saved=next((out/'sessions').glob('*.gz'));original=saved.read_bytes();(out/'YIELD_REQUEST.json').unlink()
    card.execute(out,inputs,CONFIG);assert saved.read_bytes()==original
    raw=Path(inputs['repo_root'])/'raw/s.jsonl';raw.write_bytes(raw.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='raw revision source'):card.verify(out,inputs,CONFIG)

def test_tampered_output_and_wrong_scope_refused(tmp_path):
    inputs=fixture(tmp_path/'source');out=tmp_path/'output';card.execute(out,inputs,CONFIG)
    path=next((out/'sessions').glob('*.gz'));path.write_bytes(b'forged')
    with pytest.raises(ValueError):card.verify(out,inputs,CONFIG)
    with pytest.raises(ValueError):card.execute(tmp_path/'wrong',inputs,dict(CONFIG,mode='pilot'))

def execute(output,inputs,config):
    value=card.execute(output,inputs,config)
    assert value['original_occurrences']==2 and value['retained_changes']==1 and value['upstream_only_sessions']==1
    return value

def verify(output,inputs,config):return card.verify(output,inputs,config)
