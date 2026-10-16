from runners.next_round.aries_reconcile import flags
from runners.stage12.aries import paragraph_text
import pytest


def test_canonical_filter_boundaries():
    assert not flags('a'*49, 'b'*50, [0])['canonical_min100']
    assert flags('a'*50, 'b'*50, [0])['canonical_min100']
    assert not flags('a'*100, 'a'*100, [0])['nonidentical']
    assert flags('', 'x'*100, [])['full_addition']
    assert not flags('', 'x'*100, [])['source_diff']


def test_body_and_backmatter_indices():
    doc = dict(pdf_parse=dict(body_text=[dict(text='body')], back_matter=[dict(text='back')]))
    assert paragraph_text(doc, [0,1]) == 'body\nback'
    with pytest.raises(ValueError):
        paragraph_text(doc, [-1])
    with pytest.raises(ValueError):
        paragraph_text(doc, [2])
