import json
import shutil
from pathlib import Path
import pytest
from runners.drive.cards import week5_ch_engine_bounded as b
from runners.drive.cards import week5_ch_batch_planner_v2 as planner
from runners.drive.cards.week5_ch_collection import write_rows
from runners.drive.cards.week5_ch_source import digest, write_json


class FakeScorer:
    calls = []
    def __init__(self, path, nodes): self.nodes = nodes
    def score(self, row):
        self.calls.append(row['ordinal'])
        return dict(position=row, node_limit=self.nodes, threads=1, hash_mb=64, engine={'k50':1})
    def close(self): pass


def fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(b, 'Scorer', FakeScorer)
    FakeScorer.calls = []
    rows = [dict(ordinal=i, fen='constructed', uci='e2e4') for i in range(4)]
    source = tmp_path/'positions.gz'
    write_rows(source, rows)
    engine = tmp_path/'engine'
    engine.write_bytes(b'constructed')
    inputs = {k:dict(path=str(p), sha256=digest(p)) for k,p in [('positions',source),('engine',engine)]}
    return inputs, dict(offset=0, max_positions=4, nodes=1000000, max_new_draws=2)


def test_pause_resume_fresh_replay_and_immutable_reentry(tmp_path, monkeypatch):
    inputs, config = fixture(tmp_path, monkeypatch)
    old = tmp_path/'old'/'output'
    assert b.execute(old, inputs, config)['status'] == 'yielded'
    old_bytes = {p.relative_to(old):p.read_bytes() for p in old.rglob('*') if p.is_file()}
    new = tmp_path/'new'/'output'
    shutil.copytree(old, new)
    done = b.execute(new, inputs, {**config, 'max_new_draws':4})
    assert done['new_positions'] == 2 and done['reused_positions'] == 2
    FakeScorer.calls = []
    assert b.verify(new, inputs, config)['verified_positions'] == 4
    assert sorted(FakeScorer.calls) == [0,1,2,3]
    report = (new/'BATCH.json').read_bytes()
    b.execute(new, inputs, config)
    b.verify(new, inputs, config)
    assert (new/'BATCH.json').read_bytes() == report
    assert old_bytes == {p.relative_to(old):p.read_bytes() for p in old.rglob('*') if p.is_file()}


def test_owner_request_and_exact_copied_request(tmp_path, monkeypatch):
    inputs, config = fixture(tmp_path, monkeypatch)
    output = tmp_path/'run'/'output'
    write_json(output/'YIELD_REQUEST.json', {'reason':'old owner request'})
    assert b.execute(output, inputs, config)['status'] == 'yielded'
    assert FakeScorer.calls == []
    write_json(output.parent/'RESUMED_FROM.json', {'copied':{'YIELD_REQUEST.json':digest(output/'YIELD_REQUEST.json')}})
    assert b.execute(output, inputs, {**config,'max_new_draws':4})['status'] == 'complete'
    assert b.verify(output, inputs, config)['verified']
    write_json(output/'YIELD_REQUEST.json', {'reason':'new owner request'}, mutable=True)
    assert b.verify(output, inputs, config)['status'] == 'yielded'


def test_gaps_damaged_scores_and_changed_input_refuse(tmp_path, monkeypatch):
    inputs, config = fixture(tmp_path, monkeypatch)
    output = tmp_path/'output'
    b.execute(output, inputs, {**config,'max_new_draws':4})
    file = next((output/'PRIVATE_SCORES').glob('*.json'))
    saved = file.read_bytes()
    value = json.loads(saved); value['engine']['k50'] = 9
    file.write_text(json.dumps(value))
    with pytest.raises(ValueError, match='disagreement'): b.verify(output, inputs, config)
    file.write_bytes(saved)
    file.unlink()
    with pytest.raises(ValueError, match='prefix|interval'): b.execute(output, inputs, config)
    Path(inputs['engine']['path']).write_bytes(b'changed')
    with pytest.raises(ValueError, match='pin'): b.execute(output, inputs, config)


def test_bad_quanta_segments_and_node_counts_refuse(tmp_path, monkeypatch):
    inputs, config = fixture(tmp_path, monkeypatch)
    for i, change in enumerate([{'max_positions':0},{'max_positions':1025},{'nodes':42},
                                {'max_new_draws':0},{'offset':True},{'max_positions':5}]):
        with pytest.raises(ValueError): b.execute(tmp_path/str(i), inputs, {**config,**change})


def test_actual_adapter_contract(tmp_path, monkeypatch):
    inputs, config = fixture(tmp_path, monkeypatch)
    config['max_new_draws'] = 4
    root = tmp_path/'run'
    b.execute(root/'output', inputs, config); b.verify(root/'output', inputs, config)
    write_json(root/'PLAN.json', dict(module=planner.MODULE, inputs=inputs, config=config))
    outputs = {p.relative_to(root).as_posix():digest(p) for p in root.rglob('*') if p.is_file()}
    write_json(root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,outputs=outputs))
    spec = dict(path=str(root/'COMPLETE.json'),sha256=digest(root/'COMPLETE.json'))
    segment = planner.segments(inputs['positions'], segment_positions=4)[0]
    assert planner.continuation(segment,[spec])['segment_complete']
    planner.collection_manifest([spec],tmp_path/'collection')
    with pytest.raises(ValueError, match='Overlapping'): planner.continuation(segment,[spec,spec])
    (root/'output/PRIVATE_SCORES'/'extra.txt').write_text('unbound')
    with pytest.raises(ValueError, match='Unbound'): planner.authenticated_batch(spec)
