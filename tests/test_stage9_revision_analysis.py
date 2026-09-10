import copy,math
import pytest
from runners.stage9.revision_analysis import select,evaluate,comparison,scores


def grid(prefix,lexical=.7):
    rows=[]
    for task,views in [('retrospective',('artifact','pair','record')),('future',('artifact','record'))]:
        for i in range(4):
            for view in views:
                probabilities={k:{'a':p,'b':1-p} for k,p in [('lexical_delta',lexical),('surface_delta',.8),('class_prior',.6),('majority',.1)]}
                if view=='record':probabilities['previous_cycle']={'a':.7,'b':.3}
                rows.append({'key':task+'-'+str(i),'unit':prefix+str(i),'task':task,'view':view,
                    'labels':['a'],'valid':True,'probabilities':probabilities})
    return rows


def test_strongest_independent_rival_and_zero_view_contrast():
    dev=grid('dev',.9);selected=select(dev)
    assert all(v['selected']=='surface_delta' for task in selected.values() for v in task.values())
    rows=grid('test',.7);result=evaluate(rows,selected,draws=100)
    assert len(result['contrasts'])==8 and result['confirmation_eligible'] is False
    for item in result['contrasts']:
        expected=math.log(.7/.8) if item['left']['view']==item['right']['view'] else 0.
        assert item['estimate']['mean']==pytest.approx(expected)
        assert item['estimate']['n_units']==4 and item['disposition']=='DESCRIPTIVE'
    with pytest.raises(ValueError):evaluate(dev,selected,draws=100)
    with pytest.raises(ValueError):select(dev+[dev[0]])
    broken=copy.deepcopy(dev);del broken[0]['probabilities']['majority']
    with pytest.raises(ValueError):select(broken)
    # A whole future cycle receives one distribution, with every target included.
    future=next(r for r in rows if r['task']=='future');future['labels']=['a','a','b']
    assert scores(future,'lexical_delta')==pytest.approx((2*math.log(.7)+math.log(.3))/3)


def test_source_clustering_invalid_attempts_and_zero_forecasts_retained():
    rows=grid('test');original=comparison(rows,'retrospective','artifact','lexical_delta','artifact','surface_delta',100)
    duplicates=[]
    for row in rows:
        new=copy.deepcopy(row);new['key']+='-another-target';duplicates.append(new)
    repeated=comparison(rows+duplicates,'retrospective','artifact','lexical_delta','artifact','surface_delta',100)
    assert repeated['estimate']['n_units']==original['estimate']['n_units']==4
    assert repeated['estimate']['mean']==original['estimate']['mean'] and repeated['assigned_records']==8
    invalid=copy.deepcopy(rows);invalid[0]['valid']=False
    refused=comparison(invalid,'retrospective','artifact','lexical_delta','artifact','surface_delta',100)
    assert refused['disposition']=='IMPLEMENTATION INVALID' and refused['scored_records']==0 and refused['excluded_records']==0
    assert refused['assigned_records']==4
    zero=copy.deepcopy(rows)
    for row in zero:row['probabilities']['lexical_delta']={'a':0.,'b':1.}
    result=comparison(zero,'retrospective','artifact','lexical_delta','artifact','surface_delta',100)
    assert result['scored_records']==4 and result['excluded_records']==0
    assert result['estimate']['finite_estimate'] is False and result['disposition']=='DESCRIPTIVE'
