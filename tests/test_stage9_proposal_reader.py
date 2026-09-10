import copy
import pytest

from runners.stage9.artifact_view import support
from runners.stage9.program_inference import Budget
from runners.stage9.proposal_reader import forecast
from runners.stage9.comparison_runtime import execute
from tests.test_stage9_erased_inference import A,B,program,recorded


def bundle(evaluator='stateful'):
    current=recorded([])
    return {'evidence':{'version':'s9-visible-artifact-v1','view':'process_record','current':current,
                       'earlier':[recorded([A],['failed'])],'support':support(current,'process_record')},
            'candidates':{'reliable':program(.9,.9),'fallible':program(.1,.1)},
            'prior':{'reliable':.5,'fallible':.5},'evaluator':evaluator}


def test_same_pool_and_observations_separate_scoring_from_proposals():
    data=bundle();stateful=forecast(data,Budget(1000));bag=forecast({**data,'evaluator':'bag'},Budget(1000))
    # Pr(action A, failure): .75*.9*.1 == .75*.1*.9, an exact ambiguity.
    assert stateful['forecast']['weights']==pytest.approx({'reliable':.5,'fallible':.5})
    assert bag['forecast']['weights']==pytest.approx({'reliable':.5,'fallible':.5})
    data['evidence']['earlier']=[recorded([A],['done'])]
    stateful=forecast(data,Budget(1000));bag=forecast({**data,'evaluator':'bag'},Budget(1000))
    assert stateful['pool_sha256']==bag['pool_sha256'] and stateful['evidence_sha256']==bag['evidence_sha256']
    assert stateful['forecast']['weights']['reliable']==pytest.approx(.81/(.81+.01))
    assert bag['forecast']['weights']['reliable']==pytest.approx(.9)
    repeated=copy.deepcopy(data);repeated['evidence']['earlier']*=5
    assert forecast(repeated,Budget(1000))['forecast']['prediction']==stateful['forecast']['prediction']


def test_equal_program_null_and_actual_copied_evaluators(tmp_path):
    for evaluator in ('stateful','bag'):
        data=bundle(evaluator);data['candidates']['fallible']=copy.deepcopy(data['candidates']['reliable'])
        expected=forecast(data,Budget(500000))
        assert expected['forecast']['weights']==pytest.approx(data['prior'])
        actual=execute(data,operation='proposal_evaluation',root=tmp_path/evaluator)
        assert actual['accepted'],actual
        assert actual['prediction']['forecast']==expected['forecast']
        assert actual['prediction']['exact_global_posterior'] is False
    data=bundle();data['hidden_future']='write'
    assert not execute(data,operation='proposal_evaluation',root=tmp_path/'hidden')['accepted']
