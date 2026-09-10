from pathlib import Path
from copy import deepcopy
import math
import pytest
from runners.stage9.baseline_predictions import discovery_forecasts,unit_result
from runners.stage9.baseline_matrix_runtime import execute
from runners.stage9.common import read
from runners.stage9.choice_features import predict
from runners.stage9.confirmation_freeze import paired_rows
from tests.test_stage9_artifact_comparisons import actual_case
from tests.test_stage9_comparison_runtime import bundle


def layout(query):
    return {'unit':['unit'],'target':['target'],'truth':['truth'],
            'probabilities':['forecasts',query,'model|population','probabilities'],
            'valid':['forecasts',query,'model|population','valid']}


def test_real_baseline_capsules_need_no_program_library_and_keep_exact_inputs(tmp_path):
    case=actual_case();data=bundle()
    package={'models':{v:{'model':data['population']} for v in ('artifact','process_record')},
             'types':{v:data['population_types'] for v in ('artifact','process_record')}}
    calls=[]
    def call(bundle,view):
        result=execute(bundle,root=tmp_path/view);assert result['accepted']
        calls.append((bundle,result))
        return result
    row=unit_result(case,package,call,(0,1))
    assert len(calls)==2 and len(row['rows'])==6 and len(row['costs'])==2
    for inputs,result in calls:
        assert read(Path(result['capsule'])/'evidence.json')==inputs
        assert set(inputs)=={'evidences','models','population_types'}
        for query,evidence in inputs['evidences'].items():
            assert result['prediction']['predictions'][query]['model|population']==predict(evidence,data['population'])
    assert row['truth']==case['target']
    for cell in row['rows'].values():
        assert len(cell['predictions'])==5 and all(cell['validity'].values())
        assert 'program_mixture' not in cell['predictions']
    forecasts=discovery_forecasts([case],[row],package,(0,1))
    paired=paired_rows(forecasts,forecasts,layout('process_record|dose0'),layout('artifact|dose0'),None)
    expected=math.log(row['rows']['process_record|dose0']['predictions']['model|population'][case['target']])
    expected-=math.log(row['rows']['artifact|dose0']['predictions']['model|population'][case['target']])
    assert paired==[{'unit':case['unit'],'target':'next_recorded_event','seed':None,'difference':expected}]
    assert set(forecasts[0]['forecasts'])==set(row['rows'])


@pytest.fixture
def failed_baseline():
    case=actual_case();data=bundle()
    package={'models':{v:{'model':data['population']} for v in ('artifact','process_record')},
             'types':{v:data['population_types'] for v in ('artifact','process_record')}}
    def fail(inputs,view):
        return {'accepted':False,'wall_s':0,'capsule':'failed-'+view}
    return case,unit_result(case,package,fail,(0,1)),package


def test_export_preserves_every_failed_call_and_b01_refuses_it(failed_baseline):
    case,row,package=failed_baseline
    original=deepcopy(row)
    forecasts=discovery_forecasts([case],[row],package,(0,1))
    assert row==original and len(forecasts)==1 and len(forecasts[0]['forecasts'])==6
    assert all(cell=={'valid':False,'probabilities':None}
               for query in forecasts[0]['forecasts'].values() for cell in query.values())
    with pytest.raises(ValueError,match='failed assigned forecast'):
        paired_rows(forecasts,forecasts,layout('process_record|dose0'),layout('artifact|dose0'),None)


@pytest.mark.parametrize('change',[
    'missing_unit','extra_unit','duplicate_unit','duplicate_case','truth','role',
    'missing_query','missing_model','nonboolean_validity','evidence','support','invalid_prediction'])
def test_export_rejects_incomplete_or_substituted_grid(failed_baseline,change):
    case,row,package=failed_baseline
    cases=[case];rows=[row];cell=row['rows']['artifact|dose0']
    if change=='missing_unit':rows=[]
    elif change=='extra_unit':rows.append({**deepcopy(row),'unit':'extra'})
    elif change=='duplicate_unit':rows.append(deepcopy(row))
    elif change=='duplicate_case':cases.append(deepcopy(case))
    elif change=='truth':row['truth']='changed'
    elif change=='role':row['role']='reserve'
    elif change=='missing_query':row['rows'].pop('process_record|repeat7')
    elif change=='missing_model':cell['validity'].pop('model|population')
    elif change=='nonboolean_validity':cell['validity']['model|population']=0
    elif change=='evidence':cell['evidence_sha256']='0'*64
    elif change=='support':cell['support']=[]
    elif change=='invalid_prediction':cell['predictions']['model|population']={}
    with pytest.raises(ValueError):discovery_forecasts(cases,rows,package,(0,1))


@pytest.mark.parametrize('probabilities',[{'unknown':1.0},{'unknown':float('nan')}])
def test_export_rejects_changed_or_nonfinite_probability_support(failed_baseline,probabilities):
    case,row,package=failed_baseline
    cell=row['rows']['artifact|dose0']
    cell['validity']['model|population']=True
    cell['predictions']['model|population']=probabilities
    with pytest.raises(ValueError):discovery_forecasts([case],[row],package,(0,1))
