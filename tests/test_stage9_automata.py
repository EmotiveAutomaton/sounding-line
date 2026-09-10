import itertools
import pytest
from runners.stage9.automata import accepts,shortest_separator,boundary,evaluate,threshold_language


def graph():
    return {'alphabet':['a','b'],'initial':'left','accepting':['left','right','l1','r1','end'],
            'transitions':{'left':{'a':'l1','b':'end'},'right':{'a':'r1','b':'end'},
                           'l1':{'a':'end'},'r1':{'b':'end'},'end':{}}}


def test_long_separator_matches_independent_exhaustive_language():
    g=graph();left=lambda s:accepts(g,'left',s);right=lambda s:accepts(g,'right',s)
    assert all(left((t,))==right((t,)) for t in g['alphabet'])
    answer=shortest_separator(g,'left','right');assert len(answer['suffix'])==2
    assert left(answer['suffix'])!=right(answer['suffix'])
    brute=[]
    for n in range(1,5):
        for s in itertools.product(g['alphabet'],repeat=n):
            if left(s) and not right(s) and all(left(s[:j]) and right(s[:j]) for j in range(1,n)):
                brute.append(s)
    assert boundary(left,right,g['alphabet'],4)['suffixes']==brute


def test_exact_reader_passes_but_constant_reader_cannot_distinguish():
    g=graph();left=lambda s:accepts(g,'left',s);right=lambda s:accepts(g,'right',s)
    exact=evaluate(left,right,left,right,g['alphabet'],4)
    assert exact['precision']==exact['recall']==1
    constant=lambda s:True
    assert evaluate(left,right,constant,constant,g['alphabet'],4)['recall']==0
    assert evaluate(left,left,left,right,g['alphabet'],4)['precision']==0
    assert shortest_separator(g,'left','left')['equivalent']
    with pytest.raises(ValueError,match='budget'):boundary(constant,constant,g['alphabet'],16,query_cap=10)


def test_recall_uses_language_difference_not_boundary_intersection():
    # Model separates at one token; truth only separates at two. Both accept the
    # true distinguishing suffix on the left, so boundary recall remains one.
    left=lambda s:s in [(),('a',),('a','a')]
    true_right=lambda s:s in [(),('a',)]
    model_right=lambda s:s==()
    result=evaluate(left,true_right,left,model_right,['a'],2)
    assert result['recall']==1 and result['precision']==0
    language=threshold_language(lambda s:{'a':.99,'b':.01},(),['a','b'],epsilon=.01)
    assert language(('a','a')) and not language(('a','b'))
    with pytest.raises(ValueError,match='full-support'):
        threshold_language(lambda s:{'a':1.},(),['a','b'])(('a',))
