import copy,math
import pytest
from runners.stage9.broll_jobs import select,evaluate,threshold,compare
from runners.stage9.broll_reader import ARMS


def grid(prefix):
    rows=[]
    for person in range(4):
        for script in ('one','two'):
            for view in ('same_person','other_person'):
                values={arm:[.5,.5] for arm in ARMS}
                values['budget_only']=[.7,.3];values['person_pos']=[.8,.2] if view=='same_person' else [.2,.8]
                values['person_word']=[.75,.25]
                rows.append({'key':str(person)+'-'+script,'unit':prefix+str(person),'script':script,
                    'goal':'informative','view':view,'labels':[1,0],'valid':True,'earlier_trial_count':3,'probabilities':values})
    return rows


def test_strongest_independent_rivals_and_two_dependence_axes():
    selection=select(grid('dev'));assert selection['personal']=='person_pos' and selection['cheap']=='budget_only'
    result=evaluate(grid('test'),selection,100);first,wrong,budget=result['contrasts']
    assert first['estimate']['mean']==pytest.approx(.05) and wrong['estimate']['mean']==pytest.approx(.6)
    assert all(r['participants']==4 and r['scripts']==2 and r['assigned_records']==8 for r in result['contrasts'])
    assert set(first['per_script'])==set(first['leave_one_script_out'])=={'one','two'}
    with pytest.raises(ValueError):evaluate(grid('dev'),selection,100)
    with pytest.raises(ValueError):select(grid('dev')+[grid('dev')[0]])


def test_null_missing_views_and_failed_attempts_are_retained():
    rows=grid('test');zero=compare(rows,'same_person','person_pos','same_person','person_pos',100)
    assert zero['estimate']['mean']==0 and zero['excluded_records']==0
    with pytest.raises(ValueError):compare(rows[1:],'same_person','person_pos','other_person','person_pos',100)
    broken=copy.deepcopy(rows);broken[0]['valid']=False
    result=evaluate(broken,select(grid('dev')),100)
    assert all(r['disposition']=='IMPLEMENTATION INVALID' and r['scored_records']==0 and r['assigned_records']==8 for r in result['contrasts'])
    assert all(len(records)==8 and sum(not r['valid'] for r in records)==1 for records in result['selection_overlap'].values())
    invalid_dev=grid('dev');invalid_dev[0]['valid']=False
    assert not select(invalid_dev)['accepted'] and evaluate(rows,select(invalid_dev),100)['disposition']=='NOT RUN WITH REASON'


def test_practical_scale_comes_from_a_fixed_known_answer_and_exact_null():
    r=threshold();p=r['known_truth_probability']
    assert r['expected_log_gain_nats']==pytest.approx(.05,abs=1e-12)
    expected=.25-(p*(1-p)**2+(1-p)*p**2)
    assert r['brier_gain']==pytest.approx(expected,abs=1e-12) and r['null_identical_forecasts_gain']==0.
    assert r['brier_gain']>0
