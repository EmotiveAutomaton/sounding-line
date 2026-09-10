import copy
import math
import pytest

from runners.stage9 import familiarity_analysis as analysis


def rows(units=('a','b')):
    result=[]
    for unit in units:
        cells={}
        for i in range(8):
            familiar=i%4<2;condition=('familiar' if familiar else 'unfamiliar')+'|'+('expected' if i%2==0 else 'unexpected')
            for kind in ('recognition','future'):
                truth=('same' if familiar else 'different') if kind=='recognition' else ('stop' if i%2==0 else 'write')
                support=['same','different'] if kind=='recognition' else ['stop','write']
                predictions={'good':{k:.8 if k==truth else .2 for k in support},'floor':dict.fromkeys(support,.5),
                    'always':{k:.9 if k==support[0] else .1 for k in support}}
                cells['q'+str(i)+'|'+kind]={'kind':kind,'view':'artifact' if i<4 else 'process_record','condition':condition,
                    'truth':truth,'support':support,'predictions':predictions,'validity':dict.fromkeys(predictions,True)}
        result.append({'unit':unit,'questions':cells,'domain':'fixture','purpose':'fixture'})
    return result


def contrast(left='good',right='floor',questions=None):
    questions=questions or ['q0|recognition','q2|recognition']
    return {'id':'known','card':'T02','left':{'questions':questions,'model':left},
        'right':{'questions':questions,'model':right},'threshold':.05,'strata':['domain'],
        'required_controls':['balanced-truth'],'meaning':'known balanced conditional recognition gain'}


def test_balanced_identity_beats_constant_and_has_one_unit_per_maker():
    data=rows();qs=['q0|recognition','q2|recognition']
    selected=analysis.select(data,['a','b'],{'r':{'questions':qs,'eligible':['good','always','floor']}},'f'*64)['r']
    assert selected['selected']=='good' and selected['scores']['always'] < selected['scores']['floor']
    result=analysis.evaluate(data,['a','b'],contrast(),None,'f'*64,'pilot',draws=100)
    assert result['assigned_units']==result['scored_units']==2
    assert result['overall']['mean']==pytest.approx(math.log(.8/.5),abs=1e-14)
    zero=analysis.evaluate(data,['a','b'],contrast('good','good'),None,'f'*64,'pilot',draws=100)
    assert zero['overall']['mean']==0
    with pytest.raises(ValueError,match='balanced'):analysis.cells(data[0],['q0|recognition'])
    with pytest.raises(ValueError,match='different outcomes'):analysis.cells(data[0],['q0|recognition','q0|future'])


def test_own_future_truth_and_independent_development_selection():
    qs=['q0|future','q1|future'];development=rows(('dev-a','dev-b'));data=rows()
    selected=analysis.select(development,['dev-a','dev-b'],{'f':{'questions':qs,'eligible':['good','floor']}},'f'*64)
    c=contrast('good','floor',qs);c['right']={'questions':qs,'selected_for':'f'}
    result=analysis.evaluate(data,['a','b'],c,selected,'f'*64,'pilot',draws=100)
    assert result['overall']['mean']==0  # both actual futures use their own truth
    selected['f']['units']=['a']
    with pytest.raises(ValueError,match='reused'):analysis.evaluate(data,['a','b'],c,selected,'f'*64,'pilot',draws=100)


def test_invalid_and_zero_components_never_make_a_valid_subset():
    data=rows();data[0]['questions']['q2|recognition']['validity']['good']=False
    out=analysis.evaluate(data,['a','b'],contrast(),None,'f'*64,'pilot',draws=100)
    assert out['disposition']=='IMPLEMENTATION INVALID' and out['scored_units']==0 and out['excluded_units']==0
    data=rows();data[0]['questions']['q2|recognition']['predictions']['good']={'same':1.,'different':0.}
    out=analysis.evaluate(data,['a','b'],contrast(),None,'f'*64,'pilot',draws=100)
    assert out['disposition']=='DESCRIPTIVE' and out['scored_units']==2 and out['excluded_units']==0
    assert out['overall']['mean'] is None
    assert out['overall']['extended_mean']=='negative_infinity'
    assert out['overall']['score_counts']['negative_infinity']==1
    broken=copy.deepcopy(data);del broken[0]['questions']['q7|future']
    with pytest.raises(ValueError,match='incomplete'):analysis.evaluate(broken,['a','b'],contrast(),None,'f'*64,'pilot',draws=100)
