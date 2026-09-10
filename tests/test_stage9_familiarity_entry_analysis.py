import copy
import math
import pytest

from runners.stage9 import familiarity_entry_analysis as analysis
from runners.stage9.familiarity_cases import CONDITIONS
from runners.stage9.launch import handler_operation


def rows(units=('a','b')):
    result=[]
    for unit in units:
        conditions={}
        for condition in CONDITIONS:
            truth='stop' if condition.endswith('|expected') else 'write'
            grid={}
            for query in analysis.QUERIES:
                view,path,budget=query.split('|')
                forecasts={model:{k:p if k==truth else 1-p for k in ('stop','write')}
                    for model,p in (('program',.7),('strong',.8),('floor',.5))}
                grid[query]={'view':view,'path':path,'requested_budget':budget if budget=='stopped' else int(budget),
                    'preview_cost':3,'purchase_cost':1 if budget=='stopped' else int(budget),
                    'support':['stop','write'],'predictions':forecasts,'validity':dict.fromkeys(forecasts,True)}
            conditions[condition]={'unit':unit,'truth':truth,'rows':grid}
        result.append({'unit':unit,'domain':'fixture','purpose':'fixture','conditions':conditions})
    return result


def contrast(left='program',right='floor'):
    return {'id':'known','card':'T02',
        'left':{'conditions':list(CONDITIONS),'query':'artifact|future_prediction|1','model':left},
        'right':{'conditions':list(CONDITIONS),'query':'artifact|random|1','model':right},
        'threshold':.05,'strata':['domain'],'required_controls':['own-future','charged-pool'],
        'meaning':'paired quality and separate observation cost, averaged within each maker'}


def test_own_futures_equal_maker_weights_and_strong_independent_rival():
    data=rows();dev=rows(('dev-a','dev-b'));query='artifact|random|1'
    selected=analysis.select(dev,['dev-a','dev-b'],{'r':{'conditions':list(CONDITIONS),
        'query':query,'eligible':['floor','strong']}},'f'*64)
    assert selected['r']['selected']=='strong'
    c=contrast();c['right']={'conditions':list(CONDITIONS),'query':query,'selected_for':'r'}
    out=analysis.evaluate(data,['a','b'],c,selected,'f'*64,'pilot',draws=100)
    assert out['assigned_units']==out['scored_units']==2 and out['excluded_units']==0
    assert out['overall']['mean']==pytest.approx(math.log(.7/.8))
    assert out['purchase_saving']['mean']==0 and out['promotion_eligible'] is False
    selected['r']['units']=['a']
    with pytest.raises(ValueError,match='reused'):analysis.evaluate(data,['a','b'],c,selected,'f'*64,'pilot',draws=100)
    assert handler_operation({'module':'runners.stage9.familiarity_entry_analysis',
        'arguments':['--operation','evaluate']})[1]=='evaluate'


def test_equal_quality_and_purchase_saving_are_separate_with_strict_grid():
    data=rows();c=contrast('program','program')
    c['left']['query']='artifact|future-stop-0.05|stopped'
    c['right']['query']='artifact|future_prediction|3'
    out=analysis.evaluate(data,['a','b'],c,None,'f'*64,'pilot',draws=100)
    assert out['overall']['mean']==0 and out['purchase_saving']['mean']==2
    broken=copy.deepcopy(data);del broken[0]['conditions']['familiar|expected']['rows'][analysis.QUERIES[-1]]
    with pytest.raises(ValueError,match='complete query'):analysis.evaluate(broken,['a','b'],c,None,'f'*64,'pilot',draws=100)
    broken=copy.deepcopy(data);broken[0]['conditions']['familiar|expected']['truth']='write'
    with pytest.raises(ValueError,match='different actual futures'):analysis.evaluate(broken,['a','b'],c,None,'f'*64,'pilot',draws=100)
    broken=copy.deepcopy(data);broken[0]['conditions']['familiar|expected']['rows'][analysis.QUERIES[0]]['preview_cost']=0
    with pytest.raises(ValueError,match='observation cost'):analysis.evaluate(broken,['a','b'],c,None,'f'*64,'pilot',draws=100)
    with pytest.raises(ValueError,match='allocation'):analysis.evaluate(data,['a','b','missing'],c,None,'f'*64,'pilot',draws=100)


def test_invalid_assignments_and_infinite_loss_are_retained():
    data=rows();query='artifact|future_prediction|1'
    data[0]['conditions']['familiar|expected']['rows'][query]['validity']['program']=False
    out=analysis.evaluate(data,['a','b'],contrast(),None,'f'*64,'pilot',draws=100)
    assert out['disposition']=='IMPLEMENTATION INVALID' and out['scored_units']==out['excluded_units']==0
    data=rows();data[0]['conditions']['familiar|expected']['rows'][query]['predictions']['program']={'stop':0.,'write':1.}
    out=analysis.evaluate(data,['a','b'],contrast(),None,'f'*64,'pilot',draws=100)
    assert out['overall']['extended_mean']=='negative_infinity'
    assert out['scored_units']==2 and out['excluded_units']==0
    assert out['overall']['score_counts']['negative_infinity']==1
    assert out['purchase_saving']['mean']==0
