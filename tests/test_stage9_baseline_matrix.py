import copy
from runners.stage9.baseline_matrix_runtime import execute
from runners.stage9.choice_features import predict,cheap_adaptation
from tests.test_stage9_comparison_runtime import bundle


def inputs():
    data=bundle()
    return {'evidences':data['evidences'],'models':{'first':data['population']},'population_types':data['population_types']}


def test_actual_all_candidate_baselines_equal_independent_execution(tmp_path):
    data=inputs();result=execute(data,root=tmp_path/'matrix')
    assert result['accepted'],result
    for name,evidence in data['evidences'].items():
        rows=result['prediction']['predictions'][name]
        assert len(rows)==5
        assert rows['first|population']==predict(evidence,data['models']['first'])
        for strength in (8.,16.,32.):
            assert rows['first|cheap-'+str(strength)]==predict(evidence,data['models']['first'],
                cheap_adaptation(evidence,data['population_types'],strength))


def test_repetition_does_not_invent_strength_and_private_input_refuses(tmp_path):
    data=inputs();data['evidences']['repeat']=copy.deepcopy(data['evidences']['one'])
    data['evidences']['repeat']['earlier']*=7
    result=execute(data,root=tmp_path/'repeat');assert result['accepted'],result
    assert result['prediction']['predictions']['one']==result['prediction']['predictions']['repeat']
    data['hidden_target']='stop'
    assert not execute(data,root=tmp_path/'hidden')['accepted']


def test_actual_source_boundary_and_budget_failure(tmp_path):
    path=tmp_path/'private.json';path.write_text('private fixture',encoding='utf-8')
    assert execute(None,task={'probe':True,'forbidden_paths':[str(path)],'other_port':65534},root=tmp_path/'probe')['accepted']
    assert not execute(inputs(),budget=1,root=tmp_path/'budget')['accepted']
