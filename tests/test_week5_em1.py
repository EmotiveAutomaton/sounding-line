import json
import pytest
from runners.drive.cards import week5_em1 as study
from runners.drive.cards import week5_em1_hashes as hashes
from runners.drive.cards import week5_em1_fixture as fixture


def test_pan_hashes_cover_three_levels_without_text():
    original = b'First paragraph\nSecond paragraph'
    a = hashes.pan_fingerprint(original, {'changes': [0]}, 'source/a')
    b = hashes.pan_fingerprint(original, {'changes': [1]}, 'source/b')
    overlap = hashes.pan_overlap([a], [b])
    assert overlap['document']['shared_occurrences'] == 1
    assert overlap['paragraph']['shared_occurrences'] == 2
    assert overlap['pair']['shared_occurrences'] == 1
    assert 'First paragraph' not in json.dumps(a)
    assert a['document_key_sha256'] != b['document_key_sha256']


def test_pair_delimiter_ambiguity_does_not_merge_canonical_hashes():
    a = hashes.pan_fingerprint(b'a|P|b\nc', {'changes': [0]}, 'a')
    b = hashes.pan_fingerprint(b'a\nb|P|c', {'changes': [0]}, 'b')
    assert a['pair_hashes'][0]['legacy_md5'] == b['pair_hashes'][0]['legacy_md5']
    assert a['pair_hashes'][0]['sha256'] != b['pair_hashes'][0]['sha256']


def test_alignment_failures_count_but_cannot_supply_pairs():
    row = hashes.pan_fingerprint(b'a\nb', {'changes': [0, 1]}, 'a')
    assert row['valid_pair_alignment'] is False and row['pair_hashes'] == []
    assert row['paragraphs'] == 2 and row['declared_pairs'] == 2


def test_fold_population_matches_original_union_and_project_order():
    records = [hashes.schola_fingerprint({'project': project, 'before text': 'shared beginning ' + split}, split, i, 6)
               for i, project in enumerate((1, 2)) for split in ('train', 'test')]
    order = [hashes.text_hash(json.dumps(i)) for i in (1, 2)]
    table = hashes.schola_tables(records, order)
    assert table['overall']['shared_unique_prefixes'] == 1
    assert all(row['test_rows'] == 2 and row['train_rows'] == 2 for row in table['folds'])
    assert table['folds'][0]['held_project_sha256'] == order[0]


def test_undocumented_prefix_never_gets_a_default():
    with pytest.raises(ValueError):
        hashes.schola_fingerprint({'project': 1, 'before text': 'x'}, 'test', 0, None)


def test_complete_materials_and_independent_replay(tmp_path, monkeypatch):
    root, result, proof, terminals = fixture.chain(tmp_path, monkeypatch)
    assert result['complete_materials'] is True and proof['verified'] is True
    assert sum(row.get('status') == 'yielded' for row in terminals) == 2
    assert result['historical_prefix_definition_recovered'] is False
    for path in (root / 'bundle').rglob('*.json'):
        text = path.read_text()
        assert 'First constructed paragraph' not in text and 'prefix-0' not in text
    assert 'does not claim to reproduce' in (root / 'bundle/scholawrite/README.md').read_text()


def test_changed_member_and_extra_member_refuse(tmp_path):
    path, _, _ = fixture.prepare(tmp_path)
    manifest = study.capsule(path)
    root = tmp_path / 'train_2023'
    (root / 'unlisted.txt').write_text('changed')
    with pytest.raises(ValueError, match='Unpinned'):
        study.capsule(path)


def test_prefix_receipt_must_agree(tmp_path):
    path, _, _ = fixture.prepare(tmp_path)
    manifest = json.loads(path.read_text()); manifest['prefix_rule']['characters'] = 999
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='disagree'):
        study.capsule(path)
