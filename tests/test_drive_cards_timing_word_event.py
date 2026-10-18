import pytest
from runners.drive.cards import timing_word_event as event


def test_boundary_denominator_and_casefold_alternative_paths():
    w=event.finite_witness()
    assert w['surface']['total']==pytest.approx(1)
    assert w['casefold']['total']==pytest.approx(1)
    assert w['trailing_only_total']==pytest.approx(.7)
    assert w['canonical_lowercase_only']==pytest.approx(.12/.7)
    assert w['actual_casefold_a']==pytest.approx((.12+.12+.1)/.7)
    assert w['actual_casefold_a']>w['surface']['events']['a']>w['canonical_lowercase_only']
    assert not w['native_gpt2_admitted']


def test_first_unmarked_word_uses_its_actual_start_set():
    tree={():{'a':.4,'Ba':.5,'EOS':.1},('a',):{'EOS':1.}}
    r=event.enumerate_events(tree,{'a':'a','Ba':'a'},{'a'},{'Ba'},'EOS')
    assert r['start_mass']==pytest.approx(.5) and r['events']['a']==pytest.approx(.8)


@pytest.mark.parametrize('probabilities,before,after',[([.1],0,1),([1.1],1,1),([.5],.1,1),([float('nan')],1,1)])
def test_invalid_probabilities_refuse(probabilities,before,after):
    with pytest.raises(ValueError):event.boundary_probability(probabilities,before,after)


def test_missing_paths_and_unfinished_words_refuse():
    with pytest.raises(ValueError,match='incomplete'):
        event.enumerate_events({():{'Ba':1.}},{'Ba':'a'},{'Ba'},{'Ba'},'EOS')
