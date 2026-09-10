import copy
import itertools
import pytest
from runners.stage9.ambiguity_reader import forecast
from runners.stage9.program_inference import Budget
from runners.stage9.mark_program import neutral_program
from runners.stage9.artifact_view import support
from runners.stage9.comparison_runtime import execute


def bundle():
    marks=['consult:s:src','write:s:a','write:s:b']
    current={'context':{'topic':'fixture','audience':'peer','tools':{'library':False,'source_access':True},
                       'deadline':'loose','sections':[{'name':'s','slots':['a','b']}]},'marks':marks}
    histories={}
    for i,order in enumerate(itertools.permutations(marks)):
        histories['h'+str(i)]=[dict(zip(('type','section','slot'),a.split(':')),i=j,outcome='done') for j,a in enumerate(order)]
    p=neutral_program();p['stop']={'intercept':-3.,'progress':0.,'deadline':0.,'self':0.};p['action_noise']=0.
    return {'evidence':{'version':'s9-visible-artifact-v1','view':'artifact','current':current,'earlier':[],
                        'support':support(current,'artifact')},'histories':histories,'candidates':{'a':p},'prior':{'a':1.},'observed_future':None}


def test_equal_likelihood_histories_preserve_ambiguity_and_committed_ties():
    b=bundle();before=copy.deepcopy(b);r=forecast(b,Budget(10000))
    assert b==before
    assert r['history_predictions']['inferred']==pytest.approx({h:1/6 for h in b['histories']})
    assert len(r['selected_histories'])==6
    for future in r['future_predictions'].values():
        assert future['inferred']==future['committed']==future['population']


def test_later_observation_updates_history_without_leaking_into_a_future_score():
    b=bundle();p=copy.deepcopy(b['candidates']['a']);q=copy.deepcopy(p)
    p['expertise']['progress']['write>consult']=4.;q['purpose']['cite']=3.
    b.update(candidates={'a':p,'b':q},prior={'a':.5,'b':.5})
    initial=forecast(b,Budget(10000))
    after=forecast({**b,'observed_future':{'action':'cite:s:ref','outcome':'done'}},Budget(10000))
    assert after['future_predictions']=={} and after['later_observation_supplied']
    assert after['program_posterior']!=initial['program_posterior']
    assert after['history_predictions']['inferred']!=initial['history_predictions']['inferred']
    for mutate in (lambda d:d.update(true_history='h0'),lambda d:d['histories'].update(h0=d['histories']['h1']),
                   lambda d:d.update(observed_future={'action':'absent','outcome':'done'})):
        bad=copy.deepcopy(b);mutate(bad)
        with pytest.raises(ValueError):forecast(bad,Budget(10000))


def test_actual_offered_history_capsule_has_exact_same_readout(tmp_path):
    b=bundle();expected=forecast(b,Budget(500000));result=execute(b,operation='offered_history',root=tmp_path/'caps')
    assert result['accepted'],result
    assert all(result['prediction'][k]==v for k,v in expected.items())
    assert not execute({**b,'oracle_history':'h1'},operation='offered_history',root=tmp_path/'hidden')['accepted']


def test_explicit_process_record_identifies_history_only_in_its_own_diagnostic():
    b=bundle();before=forecast(b,Budget(10000))
    b['evidence']['view']='process_record'
    b['evidence']['current'].update(events=copy.deepcopy(b['histories']['h2']),observed_stop=None)
    record=forecast(b,Budget(10000))
    assert record['view']=='process_record' and record['history_predictions']['inferred']['h2']==1.
    assert before['history_predictions']['inferred']['h2']==pytest.approx(1/6)
    assert set(record['future_predictions'])=={'old','changed'}
