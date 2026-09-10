import copy
from pathlib import Path
import pytest

from runners.stage9 import constraint_cases
from runners.stage9.common import read, write, digest, closure
from runners.stage9.constraint_jobs import forecast_unit
from runners.stage9.launch import handler_operation
from runners.stage9.mark_program import neutral_program
from tests.test_stage9_constraint_reader import actual


def test_actual_matched_reader_grid_reentry_and_source_truth_guard(actual,tmp_path):
    cf = constraint_cases.construct(actual); p = neutral_program()
    package = {'library':{'candidates':{'a':p},'prior':{'a':1.},'shared_groups':{'a':'a'}},
        'models':{v:{'fixture':{'version':'s9-conditional-choice-v1','weights':{},'individual':False,'uniform_mixture':.01}}
                  for v in ('artifact','process_record')},
        'types':{v:{t:1/8 for t in p['purpose']} for v in ('artifact','process_record')}}
    case = {**actual,'constraint_creation':cf}
    row = forecast_unit(case,package,{},tmp_path/'grid')
    assert len(row['costs']) == 4 and all(c['accepted'] for c in row['costs'])
    assert len(row['rows']) == 8 and row['truth'] == cf['target']
    for result in row['rows'].values():
        assert len(result['predictions']) == 8 and all(result['validity'].values())
        assert result['unique_prior_works'] == 1 and result['maximum_actions'] == 3
    for cost in row['costs']:
        visible = read(Path(cost['capsule'])/'evidence.json')
        assert not {'target','oracle','future_event','source_worlds','realization','private_factors'} & set(visible)
    assert forecast_unit(case,package,{},tmp_path/'grid',resume_only=True) == row
    bad = copy.deepcopy(case); bad['constraint_creation']['target'] = 'altered'
    with pytest.raises(ValueError,match='future changed'): forecast_unit(bad,package,{},tmp_path/'grid',resume_only=True)
    assert handler_operation({'module':'runners.stage9.purpose_jobs','arguments':['--consumer','constraint']})[1] == 'predict-constraint'


def test_assigned_source_shortfall_refuses_and_has_stable_reentry(actual,tmp_path,monkeypatch):
    monkeypatch.setattr(constraint_cases,'ROOT',tmp_path)
    monkeypatch.setattr(constraint_cases,'inside',lambda p:Path(p).resolve())
    monkeypatch.setenv('S9_CELL_IDENTITY','c'*64)
    source = tmp_path/'source'; own = {'per_cohort':2}
    write(source/'IDENTITY.json',own); write(source/'CASES.json',[actual])
    write(source/'COMPLETE.json',{'accepted':True,'construction_only':True,'role':'pilot',
        'identity_sha256':digest(own),'outputs':closure([source/'CASES.json'])})
    out = tmp_path/'private/constraint-case-pilots/small'
    done = constraint_cases.prepare(out,source,'pilot')
    assert done['accepted'] is False and done['assigned_series'] == 1 and done['selected_series'] == 1
    assert done['requested_series'] == 2 and read(out/'REALIZATION.json')[0]['realized']
    assert constraint_cases.prepare(out,source,'pilot') == done
    with pytest.raises(ValueError): constraint_cases.prepare(out,source,'pilot',1)
