"""Known-answer and hostile branch checks for the P7 event enclosure."""
from fractions import Fraction
import pytest
from runners.drive.cards import timing_word_bounds as m


def test_casefold_alternate_paths_boundary_and_prefix_joint():
    pieces = {0:b' a', 1:b' A', 2:b' ', 3:b'a', 4:b'x', 5:b'!'}
    eos = 6
    tree = {():{0:.15,1:.15,2:.1,3:.2,4:.3,6:.1},
            (0,):{6:.8,4:.2}, (1,):{6:.8,4:.2},
            (2,):{3:1.}, (2,3):{6:1.}, (0,4):{6:1.}, (1,4):{6:1.}}
    def oracle(path):
        return {k:tree[path].get(k,0.) for k in range(7)}
    result=m.next_word_bounds(oracle,pieces,eos,b' ','a',max_nodes=30,max_depth=5)
    # Prefix mass .4; joint .15*.8 + .15*.8 + .1 = .34.
    exact=float(Fraction(17,20))
    assert result['conditional']['lower'] <= exact <= result['conditional']['upper']
    assert result['conditional']['point_score_admitted']
    assert not result['conditional']['scientific_admission']


@pytest.mark.parametrize(('data','target','final','expected'), [
    (b' hello', 'hello', False, m.PENDING),
    (b' hello', 'hello', True, m.ACCEPT),
    (b' hellos ', 'hello', False, m.REJECT),
    (b' hello!', 'hello', False, m.ACCEPT),
    (b" hello'", 'hello', False, m.PENDING),
    (b" hello' ", 'hello', False, m.ACCEPT),
    (b" hello's ", 'hello', False, m.REJECT),
    (b" hello's ", "hello's", False, m.ACCEPT),
    (' Stra\u00dfe!'.encode(), 'strasse', False, m.ACCEPT),
    (' \u0130!'.encode(), 'i\u0307', False, m.ACCEPT),
    (b' _\t a!', 'a', False, m.ACCEPT),
    (b'!a', 'a', False, m.REJECT),
    (b'!a', '!', False, m.ACCEPT),
    (b' a\xe2', 'a', False, m.PENDING),
    (b' a\xe2', 'a', True, m.ACCEPT),
    (' a\u2019b'.encode(), 'a', False, m.REJECT),
    (b' ___ ', 'a', True, m.REJECT),
])
def test_exact_regex_decisions(data,target,final,expected):
    assert m.word_state(data,b'',target,final)==expected


def test_infinite_separator_tail_is_not_zero():
    pieces={0:b' ',1:b'a!'}
    def oracle(path):return {0:.5,1:.4,2:.1}
    result=m.next_word_bounds(oracle,pieces,2,b'','a',max_nodes=3,max_depth=100)
    assert result['conditional']['lower'] <= .8 <= result['conditional']['upper']
    assert not result['conditional']['point_score_admitted']
    assert result['numerator']['unresolved_mass'] >= .125


def test_context_limit_retains_mass():
    result=m.next_word_bounds(lambda p:{0:.4,1:.6},{0:b'a'},1,b'','a',max_nodes=20,max_depth=1)
    assert result['numerator']['context_limited_nodes']==1
    assert result['conditional']['upper'] >= .4
    assert result['conditional']['lower']==0


def test_missing_token_and_impossible_conditioning_refuse():
    with pytest.raises(ValueError,match='incomplete'):
        m.next_word_bounds(lambda p:{0:1.},{0:b'a'},1,b'','a',max_nodes=1,max_depth=1)
    with pytest.raises(ValueError,match='impossible'):
        m.next_word_bounds(lambda p:{0:1.,1:0.},{0:b'a'},1,b'b','a',max_nodes=1,max_depth=1)


def test_prefix_can_end_inside_token_and_nothing_is_retokenized():
    result=m.next_word_bounds(lambda p:{0:.3,1:.7,2:0.},
        {0:b'old a!',1:b'old b!'},2,b'old ','a',max_nodes=2,max_depth=1)
    assert result['conditional']['lower'] <= .3 <= result['conditional']['upper']
    assert result['conditional']['point_score_admitted']


def test_merged_hidden_histories_are_not_assumed_equivalent():
    pieces={0:b'a',1:b'a',2:b'b',3:b'!'}
    def oracle(path):
        tree={():{0:.5,1:.5}, (0,):{3:1.}, (1,):{2:1.}}
        return {k:tree[path].get(k,0.) for k in range(5)}
    result=m.next_word_bounds(oracle,pieces,4,b'','a',max_nodes=3,max_depth=3)
    assert result['conditional']['lower'] <= .5 <= result['conditional']['upper']


def test_bounds_monotonically_tighten_with_work():
    def oracle(path):return {0:.4,1:.5,2:.1}
    results=[m.next_word_bounds(oracle,{0:b' ',1:b'a!'},2,b'','a',max_nodes=n,max_depth=10)['conditional'] for n in range(1,6)]
    for old,new in zip(results,results[1:]):
        assert new['lower']>=old['lower']
        assert new['upper']<=old['upper']
