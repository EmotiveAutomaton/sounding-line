import json
from pathlib import Path
import subprocess
import sys

import pytest

from runners.drive.cards import engine_input_pilot as card
from runners.stage14.common import read, filehash
from tests.test_drive_engine_sources import fixture, save

CONFIG=dict(mode='constructed',expected_sessions=1,session_limit=1,cumulative_wall_seconds=120)


def test_complete_handler_fresh_process_and_immutable_reentry(tmp_path):
    inputs=fixture(tmp_path/'source');output=tmp_path/'output'
    result=card.execute(output,inputs,CONFIG)
    assert result['completed_sessions']==1 and not result['reader_executed']
    value=json.loads((output/'DOCUMENTS.jsonl').read_bytes())
    assert value['text']=='dog '
    assert [p['occurrenceId'] for p in value['provenance']]==['p6:1','source:3']
    manifest=tmp_path/'manifest.json';save(manifest,dict(inputs=inputs,config=CONFIG))
    code=('import json,sys;from pathlib import Path;from runners.drive.cards.engine_input_pilot import verify;'
        'p=json.load(open(sys.argv[1]));print(json.dumps(verify(Path(sys.argv[2]),p["inputs"],p["config"])))')
    check=json.loads(subprocess.check_output([sys.executable,'-B','-c',code,str(manifest),str(output)],text=True))
    assert check['verified'] and check['summary']==result
    bound=read(output/'TIMING_BINDINGS.json')['outputs']
    assert card.execute(output,inputs,CONFIG)==result
    assert {p:filehash(output/p) for p in bound}==bound
    assert read(output/'THREADS_VERIFY.json')['numerical_threads']==1


def test_saved_boundary_resume(tmp_path):
    inputs=fixture(tmp_path/'source');output=tmp_path/'output';output.mkdir()
    save(output/'YIELD_REQUEST.json',dict(reason='constructed boundary'))
    first=card.execute(output,inputs,CONFIG)
    assert first['status']=='yielded' and not (output/'SUMMARY.json').exists()
    saved=list((output/'sessions').glob('*.gz'));hashes={str(p):filehash(p) for p in saved}
    # Only remove the constructed fixture's own marker after its saved checkpoint.
    (output/'YIELD_REQUEST.json').unlink()
    result=card.execute(output,inputs,CONFIG)
    assert result['status']=='complete' and {str(p):filehash(p) for p in saved}==hashes
    assert card.verify(output,inputs,CONFIG)['verified']


def test_changed_raw_source_refuses_completed_reentry(tmp_path):
    inputs=fixture(tmp_path/'source');output=tmp_path/'output'
    card.execute(output,inputs,CONFIG)
    raw=Path(inputs['repo_root'])/'raw/s.jsonl'
    raw.write_bytes(raw.read_bytes().replace(b'cat',b'rat'))
    with pytest.raises(ValueError,match='raw EV source'):card.execute(output,inputs,CONFIG)


def test_changed_output_refuses_verification(tmp_path):
    inputs=fixture(tmp_path/'source');output=tmp_path/'output'
    card.execute(output,inputs,CONFIG)
    (output/'DOCUMENTS.jsonl').write_bytes(b'{}\n')
    with pytest.raises(ValueError,match='intermediate/output'):card.verify(output,inputs,CONFIG)


def test_full_corpus_and_changed_pilot_are_not_admitted():
    with pytest.raises(ValueError,match='separate measured'):card.validate(dict(card.CONFIG,mode='main'))
    with pytest.raises(ValueError,match='frozen first100'):card.validate(dict(card.CONFIG,session_limit=1399))
    with pytest.raises(ValueError,match='bounded constructed'):card.validate(dict(CONFIG,session_limit=2))
