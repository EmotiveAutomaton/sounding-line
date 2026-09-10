import copy
import pytest

from runners.stage9.comparison_runtime import execute
from runners.stage9.program_inference import Budget
from runners.stage9.erased_inference import infer
from tests.test_stage9_erased_inference import A,evidence,marked,program


def bundle():
    return {'evidences':{'zero':evidence(marked([],'current')),
                        'one':evidence(marked([],'current'),[marked([A],'past')])},
        'candidates':{'a':program(.75),'b':program(.25)},'prior':{'a':.5,'b':.5},
        'shared_groups':{'a':'a','b':'b'},'population':{'version':'s9-conditional-choice-v1',
            'weights':{},'individual':False,'uniform_mixture':.01},
        'population_types':{t:1/8 for t in program()['purpose']}}


@pytest.mark.parametrize('estimator',['uniform','grouped','particles'])
def test_actual_matrix_capsule_uses_same_input_and_matches_independent_route(tmp_path,estimator):
    data = bundle()
    actual = execute(data,estimator=estimator,root=tmp_path/'matrix')
    assert actual['accepted'],actual
    assert actual['inputs_and_sources_unchanged']
    for name,query in data['evidences'].items():
        expected = infer(query,data['candidates'],data['prior'],Budget(100))
        assert actual['prediction']['predictions'][name]['program_mixture']['prediction']==expected['prediction']
    assert actual['prediction']['cache_hits'] > 0


def test_hidden_fields_and_exhausted_budget_invalidate_whole_matrix(tmp_path):
    data = bundle();data['hidden_target']='write'
    assert not execute(data,root=tmp_path/'hidden')['accepted']
    assert not execute(bundle(),budget=1,root=tmp_path/'budget')['accepted']
    assert not execute(bundle(),budget=8000001,root=tmp_path/'over')['accepted']
    assert execute(bundle(),budget=8000000,root=tmp_path/'limit')['accepted']


def test_actual_private_file_access_probe(tmp_path):
    forbidden = tmp_path/'truth.json';forbidden.write_text('secret fixture',encoding='utf-8')
    result = execute(None,task={'probe':True,'forbidden_paths':[str(forbidden)],'other_port':65534},root=tmp_path/'access')
    assert result['accepted'],result
