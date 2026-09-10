import copy
import math
import pytest
from runners.stage9.cue_reader import forecast
from runners.stage9.program_inference import Budget
from runners.stage9.mark_program import neutral_program, policy
from runners.stage9.artifact_view import support
from runners.stage9.erased_inference import artifact_work
from runners.stage9.comparison_runtime import execute


def bundle():
    current={'context':{'topic':'fixture','audience':'peer','tools':{'library':True,'source_access':True},
                       'deadline':'loose','sections':[{'name':'a','slots':['x']},{'name':'b','slots':['x']}]},
             'marks':[],'events':[],'observed_stop':None}
    p=neutral_program();p['available_types']=['write','check'];p['action_noise']=0.
    p['stop']={'intercept':math.log(1/3),'progress':0.,'deadline':math.log(3.),'self':0.}
    return {'evidence':{'version':'s9-visible-artifact-v1','view':'process_record','current':current,
                       'earlier':[],'support':support(current,'process_record')},
            'candidates':{'a':p},'prior':{'a':1.},'shared_groups':{'a':'a'},
            'population_types':{t:1/8 for t in p['purpose']},
            'cue':{'kind':'section_checked','value':True,'section':'a','reliability':.9}}


def test_local_scope_and_reliability_have_independent_analytic_answers():
    b=bundle();original=copy.deepcopy(b);a=forecast(b,Budget(10000));p=a['predictions']['inferred_cued']
    assert b==original and p['stop']==pytest.approx(.25)
    # Four equally weighted write/check actions before the report; three after.
    assert p['check:a:x']==pytest.approx(.1*.75/4)
    assert p['check:b:x']==pytest.approx(.9*.75/3+.1*.75/4)
    wrong=copy.deepcopy(b);wrong['cue']['value']=False
    w=forecast(wrong,Budget(10000))
    assert w['predictions']['inferred_cued']['check:a:x']==pytest.approx(.9*.75/4)
    assert a['posterior']==w['posterior'] and a['historical_likelihood_receipts']==w['historical_likelihood_receipts']
    deadline=copy.deepcopy(b);deadline['cue']={'kind':'deadline','value':'tight','section':None,'reliability':.9}
    d=forecast(deadline,Budget(10000))
    assert d['predictions']['inferred_cued']['stop']==pytest.approx(.9*.5+.1*.25)
    for p in b['candidates'].values():p['action_noise']=.01
    direct=policy(b['candidates']['a'],artifact_work(b['evidence']['current']),believed_checked=('a',))
    assert direct['check:a:x']==pytest.approx(.01/len(direct))


def test_redundant_mark_and_irrelevant_local_operator_do_not_add_information():
    b=bundle();w=b['evidence']['current']
    w['marks']=['check:a:x'];w['events']=[{'i':0,'type':'check','section':'a','slot':'x','outcome':'done'}]
    b['evidence']['support']=support(w,'process_record')
    local=forecast(b,Budget(10000))
    redundant=copy.deepcopy(b);redundant['cue']={'kind':'past_mark','value':'check:a:x','section':None,'reliability':.9}
    repeated=forecast(redundant,Budget(10000))
    assert local['predictions']==repeated['predictions']
    assert repeated['predictions']['inferred_cued']==repeated['predictions']['inferred_uncued']
    assert repeated['distinct_earlier_works']==0 and repeated['reported_state_weights']=={}
    for mutate in (lambda d:d.update(truth='x'),lambda d:d['cue'].update(section='unknown'),
                   lambda d:d['cue'].update(reliability=float('nan'))):
        bad=copy.deepcopy(b);mutate(bad)
        with pytest.raises(ValueError):forecast(bad,Budget(10000))


def test_context_cue_actual_capsule_and_hidden_source_truth_refusal(tmp_path):
    b=bundle();expected=forecast(b,Budget(500000))
    result=execute(b,operation='context_cue',root=tmp_path/'caps')
    assert result['accepted'],result
    assert all(result['prediction'][k]==v for k,v in expected.items())
    assert not execute({**b,'source_is_true':True},operation='context_cue',root=tmp_path/'hidden')['accepted']
