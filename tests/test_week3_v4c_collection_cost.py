from pathlib import Path
import pytest
from runners.stage14.common import read
from runners.drive.cards import week3_v4c_collection_cost as m


def test_actual_compressed_boundary_replay_and_scope(tmp_path):
    out = tmp_path/'out'
    result = m.execute(out, {}, {'mode': 'constructed'})
    assert result['references_decoded'] == 796
    assert result['proof']['summary'] == dict(worlds=4, references_per_world=199)
    assert result['actual_scientific_summary_computed'] is False
    replay = m.verify(out, {}, {'mode': 'constructed'})
    assert replay['verified'] and replay['projected_collection_cpu_seconds'] > 0
    inputs = {f'shard{i}': str(out/f'fixture/{i}/COMPLETE.json') for i in range(4)}
    with pytest.raises(ValueError, match='scope mismatch'):
        m.measure(inputs)
    with pytest.raises(ValueError, match='four'):
        m.measure(dict(list(inputs.items())[:3]), True)
    target = next((out/'fixture/0').rglob('*.xz'))
    target.write_bytes(target.read_bytes() + b'corruption')
    with pytest.raises(ValueError, match='physical manifest'):
        m.measure(inputs, True)


def test_bad_mode_and_saved_proof_refuse(tmp_path):
    with pytest.raises(ValueError, match='Fixed'):
        m.execute(tmp_path, {}, {'mode': 'other'})
    with pytest.raises(ValueError, match='no source'):
        m.execute(tmp_path, {'source': 'x'}, {'mode': 'constructed'})
    m.execute(tmp_path, {}, {'mode': 'constructed'})
    import json
    path = tmp_path/'SUMMARY.json'
    result = read(path); result['references_decoded'] -= 1
    path.write_text(json.dumps(result), encoding='utf8')
    with pytest.raises(ValueError, match='replay differs'):
        m.verify(tmp_path, {}, {'mode': 'constructed'})
