"""Actual constructed prepare/readback path normalization regression."""
from runners.drive.cards import week5_go3_collection_counted_fixture_v2 as driver


def test_prepare_tree_matches_canonical_readback(tmp_path, monkeypatch):
    monkeypatch.setattr(driver, 'PRIVATE', tmp_path)
    monkeypatch.setattr(driver, 'INPUTS', tmp_path / 'inputs')
    driver.prepare()
    saved = driver.read(tmp_path / 'go3-collection-fixture-input-tree.json')
    assert saved['files'] == driver.all_bytes(driver.INPUTS)
    assert all('\\' not in name for name in saved['files'])
    assert any('/' in name for name in saved['files'])
    assert saved['constructed_only'] is True
    assert saved['source_envelopes_are_not_native_results'] is True
