import copy
import pytest
from runners.stage9.context_reader import forecast
from runners.stage9.program_inference import Budget
from runners.stage9.mark_program import neutral_program
from runners.stage9.artifact_view import support
from runners.stage9.comparison_runtime import execute


def bundle(available=True):
    current={'context':{'topic':'fixture','audience':'peer','tools':{'library':available,'source_access':True},
                        'deadline':'loose','sections':[{'name':'s','slots':['a','b']}]},
             'marks':['write:s:a'],'events':[{'i':0,'type':'write','section':'s','slot':'a','outcome':'done'}],
             'observed_stop':None}
    evidence={'version':'s9-visible-artifact-v1','view':'process_record','current':current,
              'earlier':[],'support':support(current,'process_record')}
    a=neutral_program();b=neutral_program();a['purpose']['write']=2.;b['purpose']['cite']=3.
    return {'evidence':evidence,'candidates':{'a':a,'b':b},'prior':{'a':.5,'b':.5},
            'shared_groups':{'a':'a','b':'b'},'announcement':'library_withdrawn'}


def test_observed_ban_changes_future_without_reinterpreting_past():
    data=bundle();original=copy.deepcopy(data)
    announced=forecast(data,Budget(10000));ordinary=forecast({**data,'announcement':'none'},Budget(10000))
    assert data==original
    assert announced['posterior']==ordinary['posterior']
    assert announced['historical_likelihood_receipts']==ordinary['historical_likelihood_receipts']
    assert announced['historical_input_sha256']==ordinary['historical_input_sha256']
    assert announced['future_input_sha256']!=ordinary['future_input_sha256']
    assert announced['predictions']['inferred_stale']==ordinary['predictions']['inferred_stale']
    p=announced['predictions']['inferred_announced']
    # The declared .01 model noise stays explicit; an external mask earns no legality claim.
    assert p['cite:s:ref']==pytest.approx(.01/len(p))
    assert p['cite:s:ref']<ordinary['predictions']['inferred_announced']['cite:s:ref']
    assert p['write:s:b']>ordinary['predictions']['inferred_announced']['write:s:b']


def test_irrelevant_announcement_null_and_unsupported_inputs_refuse():
    data=bundle(False)
    a=forecast(data,Budget(10000));b=forecast({**data,'announcement':'none'},Budget(10000))
    assert a['predictions']==b['predictions']
    for mutate in (lambda d:d.update(truth='a'),lambda d:d.update(announcement='new_goal'),
                   lambda d:d['evidence']['support'].pop()):
        bad=copy.deepcopy(data);mutate(bad)
        with pytest.raises(ValueError):forecast(bad,Budget(10000))


def test_actual_context_capsule_matches_independent_computation(tmp_path):
    data=bundle();result=execute(data,operation='context_transfer',root=tmp_path/'caps')
    assert result['accepted'],result
    expected=forecast(data,Budget(500000))
    assert all(result['prediction'][k]==v for k,v in expected.items())
    bad={**data,'hidden_future':'a'}
    assert not execute(bad,operation='context_transfer',root=tmp_path/'hidden')['accepted']
