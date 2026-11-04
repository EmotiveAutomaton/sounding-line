import hashlib
import json
import pytest
from runners.drive.cards import week4_s1_gram_recurrence as g
from runners.drive.cards import week4_s1_stats as s
from runners.drive.cards.timing_p6 import gzread


def test_matching_three_word_membership_and_occurrences():
    a = ('a', '<content>', '<content>'); b = ('the', '<content>', '<content>')
    assert g.checked_recurrence([a, a, b], {a}, {b}) == 1 / 3
    assert g.checked_recurrence([a], {a}, {a}) == 0
    for targets, own, donor in (([a + ('x',)], {a}, {b}), ([a], {a + ('x',)}, {b}), ([a], {a}, {b + ('x',)})):
        with pytest.raises(ValueError, match='Matching'): g.checked_recurrence(targets, own, donor)


def test_three_word_boundaries_do_not_change_original_default():
    seq = [['a', 'b', '.', 'the', 'c', 'd'], ['a', 'e']]
    assert s.history_grams(seq, {'a', 'the'}, n=3) == {('the', '<content>', '<content>')}
    assert s.history_grams(seq, {'a', 'the'}) == set()
    assert not s.history_grams([['b', 'c', 'd']], {'a'}, n=3)


def test_full_source_joins_and_mismatch_refusal(tmp_path):
    inputs = g.constructed_sources(tmp_path)
    rows, census, _ = g.rows_from_sources(tmp_path / 'scored', inputs, False)
    assert [r['outcome'] for r in rows] == [1, -1, 1 / 3, 0]
    assert census == dict(included_windows=4, history_supported_sessions=1, history_or_window_unsupported_sessions=1398)
    assert g.rows_from_sources(tmp_path / 'scored', inputs, True)[0] == rows
    wp = tmp_path / 'constructed_sources/windows/PLAN.json'
    wp.write_text(json.dumps(dict(config=dict(gram_words=4))))
    with pytest.raises(ValueError, match='Frozen source'): g.rows_from_sources(tmp_path / 'refused', inputs, False)


def test_full_source_target_length_tamper_refused(tmp_path):
    import gzip
    inputs = g.constructed_sources(tmp_path)
    root = tmp_path / 'constructed_sources/windows'
    windows = root / 'output/WINDOWS.json.gz'
    value = gzread(windows); value[1]['windows'][0]['grams'][0].append('<content>')
    with gzip.open(windows, 'wt', encoding='utf8') as f: json.dump(value, f)
    receipt = json.loads((root / 'COMPLETE.json').read_text())
    receipt['outputs'][windows.relative_to(root).as_posix()] = hashlib.sha256(windows.read_bytes()).hexdigest()
    (root / 'COMPLETE.json').write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match='length'): g.rows_from_sources(tmp_path / 'refused', inputs, False)


def test_complete_native_replay_and_output_tamper(tmp_path):
    config = g.configuration('constructed')
    g.execute(tmp_path, {}, config)
    assert g.verify(tmp_path, {}, config)['complete_statistical_replay']
    summary = json.loads((tmp_path / 'SUMMARY.json').read_text())
    assert all(summary['known_checks'].values()) and not summary['scientific_effect_computed']
    (tmp_path / 'SUMMARY.json').write_text('{}')
    with pytest.raises(ValueError, match='replay'): g.verify(tmp_path, {}, config)


def test_configuration_and_human_input_refusal(tmp_path):
    with pytest.raises(ValueError): g.configuration('other')
    with pytest.raises(ValueError, match='Frozen'): g.execute(tmp_path, {}, dict(g.configuration('constructed'), gram_words=4))
    with pytest.raises(ValueError, match='No human'): g.execute(tmp_path, {'nuisance_completion': 'unused'}, g.configuration('constructed'))
