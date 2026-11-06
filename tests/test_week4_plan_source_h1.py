import pytest
from runners.drive.cards import week4_plan_source_h1 as h
from runners.drive.cards import week4_plan_source as original
from runners.stage9 import coauthor
from runners.drive.cards.week3_insertion_provenance_h1 import fixture as insertion_fixture
from tests import test_week4_plan_source as base_tests


@pytest.mark.parametrize('text', ['', 'ascii\n', 'A\U0001f600B\n', '\u00e9\u6f22\U0001d11e'])
def test_conversion_equals_original(text):
    assert h.units(text) == coauthor.units(text)
    assert h.text_of(h.units(text)) == coauthor.text_of(coauthor.units(text)) == text


@pytest.mark.parametrize('kind', ['plain','newline','rewrite','repeated','unmatched','edited','deleted'])
def test_complete_canonical_parity(kind):
    events, _ = insertion_fixture(kind)
    assert h.replay(events) == coauthor.replay(events)


def test_full_source_parity():
    args = original.fixture()
    assert h.source_session(*args) == original.source_session(*args)
    with pytest.raises(UnicodeError): h.text_of([0xd83d])
    assert h.apply_delta.__kwdefaults__ == coauthor.apply_delta.__kwdefaults__


@pytest.mark.parametrize('name', [n for n in dir(base_tests) if n.startswith('test_')])
def test_original_source_contract(name, monkeypatch, tmp_path):
    # Exercise original cases against the new replay and actual successor handler.
    proxy = type('Proxy', (), {})()
    for key in ('fixture','byte_delta'): setattr(proxy, key, getattr(original, key))
    for key in ('source_session','configuration','execute','verify'): setattr(proxy, key, getattr(h, key))
    monkeypatch.setattr(base_tests, 'p', proxy)
    fn = getattr(base_tests, name)
    if name == 'test_reentry_and_full_output_mutation': fn(tmp_path)
    else: fn()
