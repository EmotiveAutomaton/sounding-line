"""One-work descriptive bounds, copied-text rival and future-evidence refusal."""
import copy
import pytest
from runners.stage9.genetic_cases import offered,validate
from runners.stage9.genetic_jobs import controls,summarize
from runners.stage9.features import copy_probabilities


def case(key='a',before='old local words',after='new local words'):
    return {'key':key,'work':'one work','local_before':before,'local_after':after,'hands':[],
            'hand_status':'unspecified in local markup'}


def test_offered_replacement_uses_current_text_and_content_order():
    own=case();pool=[own,case('b',after='other local words'),case('c',after='three simple words'),case('d',after='last sample words')]
    task=offered(own,pool);validate([task])
    assert task['evidence']==offered(own|{'key':'renamed'},list(reversed(pool)))['evidence']
    assert task['evidence']['options'][task['truth']]==own['local_after']
    assert own['local_after'] not in task['evidence']['prefix']
    bad=copy.deepcopy(task);bad['evidence']['future_label']=bad['truth']
    with pytest.raises(ValueError):validate([bad])
    bad=copy.deepcopy(task);bad['truth']='missing'
    with pytest.raises(ValueError):validate([bad])
    bad=copy.deepcopy(task);bad['evidence']['prefix']+=own['local_after']
    with pytest.raises(ValueError):validate([bad])


def forecasts():
    options={'a':'old local words','b':'new local words','c':'other simple words','d':'far distant things'}
    rivals=controls('old local words',options,copy_probabilities('old local words',options))
    base={'key':'a','unit':'one work','truth':'a','public_input_sha256':'same','valid':True}
    return [base|{'probabilities':{'neural':dict(rivals['uniform'])}}],[base|{'probabilities':rivals}]


def test_one_work_has_no_population_interval_and_copy_can_win():
    neural,rivals=forecasts();profile=summarize(neural,rivals)
    assert not profile['scientific_admission'] and not profile['confirmation_eligible']
    assert all(r['estimate']['ci'] is None and r['independent_works']==1 for r in profile['contrasts'])
    assert profile['contrasts'][0]['estimate']['mean']<0 and profile['contrasts'][1]['estimate']['mean']==0
    assert all(r['disposition']=='DESCRIPTIVE' for r in profile['contrasts'])
    with pytest.raises(ValueError):controls('old',{'a':'old','b':'new'},{'a':.5,'b':.5})


def test_missing_invalid_and_nonfinite_genetic_predictions_remain_visible():
    neural,rivals=forecasts()
    with pytest.raises(ValueError):summarize(neural,[])
    bad=copy.deepcopy(rivals);bad[0]['public_input_sha256']='different'
    with pytest.raises(ValueError):summarize(neural,bad)
    bad=copy.deepcopy(neural);bad[0].update(valid=False,probabilities=None)
    result=summarize(bad,rivals)
    assert all(r['disposition']=='IMPLEMENTATION INVALID' and r['assigned']==1 and r['excluded']==0 and r['scored']==0 for r in result['contrasts'])
    for row in neural+rivals:
        for name in row['probabilities']:row['probabilities'][name]={'a':0.,'b':1.,'c':0.,'d':0.}
    result=summarize(neural,rivals)
    assert all(r['estimate']['finite_estimate'] is False for r in result['contrasts'])


def test_genetic_dispatcher_distinguishes_operations_and_actual_packages():
    from runners.stage9.launch import handler_operation
    def job(*args):return {'module':'runners.stage9.genetic_jobs','arguments':list(args)}
    signatures=[handler_operation(job(op)) for op in ('prepare','controls','evaluate')]
    signatures += [handler_operation(job('neural','--family',family,'--package-kind',kind)) for family in ('qwen','smollm') for kind in ('base','archive','fitted')]
    assert len(set(signatures))==9
    for args in [('neural',),('neural','--family','other'),('neural','--family','qwen','--package-kind','unknown')]:
        with pytest.raises(ValueError):handler_operation(job(*args))
