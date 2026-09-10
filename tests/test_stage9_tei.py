import pytest

from runners.stage9.tei import replacements, safe_parse


def surface(body):
    return ('<surface xmlns="http://www.tei-c.org/ns/1.0"><zone>' + body + '</zone></surface>').encode()


def test_real_mod_schema_preserves_local_replacement_and_hand():
    raw = surface('<line>to fin<mod><del>ed</del><add hand="#pbs">d</add></mod> a book</line>')
    cases, counts = replacements(raw, 'fixture')
    assert counts['mod_elements'] == counts['eligible_local_replacements'] == 1
    assert cases[0]['local_before'] == 'ed'
    assert cases[0]['local_after'] == 'd'
    assert cases[0]['hands'] == ['#pbs']
    assert 'global chronology' in cases[0]['order']


def test_unclear_and_cross_line_cancellation_are_not_clean_replacements():
    for raw in [surface('<line><mod><del>old</del><add><unclear>new</unclear></add></mod></line>'),
                surface('<line><delSpan spanTo="#end"/>earlier</line><line><mod><del>old</del><add>new</add></mod><anchor xml:id="end"/></line>')]:
        cases, counts = replacements(raw, 'fixture')
        assert not cases
        assert sum(counts['exclusions'].values()) == 1


def test_entity_and_external_schema_loading_are_not_executed():
    with pytest.raises(ValueError, match='DTD/entity'):
        safe_parse(b'<!DOCTYPE surface [<!ENTITY x SYSTEM "file:///truth">]><surface>&x;</surface>')
    with pytest.raises(ValueError, match='expected a released TEI surface'):
        safe_parse(b'<invented>draft markers</invented>')
