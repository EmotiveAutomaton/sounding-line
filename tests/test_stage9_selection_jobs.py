import copy
from pathlib import Path
import pytest
from runners.stage9 import selection_cases,selection_jobs
from runners.stage9.common import read,write,digest,closure
from runners.stage9.launch import handler_operation
from runners.stage9.mark_program import neutral_program
from tests.test_stage9_selection_reader import actual


def test_actual_sequential_purchase_paths_reenter_without_revealing_unbought(actual,tmp_path,monkeypatch):
    monkeypatch.setattr(selection_jobs,'STRATEGIES',('random','future_prediction'))
    cf=selection_cases.construct(actual);p=neutral_program()
    package={'library':{'candidates':{'a':p},'prior':{'a':1.},'shared_groups':{'a':'a'}},
        'models':{v:{'fixture':{'version':'s9-conditional-choice-v1','weights':{},'individual':False,'uniform_mixture':.01}}
                  for v in ('artifact','process_record')},
        'types':{v:{t:1/8 for t in p['purpose']} for v in ('artifact','process_record')}}
    case={**actual,'selection':cf};row=selection_jobs.forecast_unit(case,package,{},tmp_path/'grid')
    assert len(row['rows'])==20 and len(row['traces'])==8 and all(c['accepted'] for c in row['costs'])
    assert row['truth']==cf['target']
    for cell in row['rows'].values():
        assert all(cell['validity'].values()) and len(cell['predictions'])==6
        assert cell['preview_cost']==7
        if cell['requested_budget']==7:assert cell['full_view'] and cell['purchase_cost']==7
        if cell['requested_budget']=='stopped':assert cell['purchase_cost']==0
    for trace in row['traces'].values():
        for index,step in enumerate(trace['steps']):
            visible=read(Path(step['capsule'])/'evidence.json')
            assert set(visible['purchases'])==set(step['purchased']) and len(step['purchased'])==index
            assert not {'target','oracle','future_event','source_worlds','private_factors'} & set(visible)
            if index:assert trace['steps'][index-1]['output']['selected'] in visible['purchases']
    assert selection_jobs.forecast_unit(case,package,{},tmp_path/'grid',resume_only=True)==row
    bad=copy.deepcopy(case);bad['selection']['target']='changed'
    with pytest.raises(ValueError,match='future changed'):selection_jobs.forecast_unit(bad,package,{},tmp_path/'grid',resume_only=True)
    assert handler_operation({'module':'runners.stage9.purpose_jobs','arguments':['--consumer','selection']})[1]=='predict-selection'


def test_fixed_source_shortfall_retained(actual,tmp_path,monkeypatch):
    monkeypatch.setattr(selection_cases,'ROOT',tmp_path)
    monkeypatch.setattr(selection_cases,'inside',lambda p:Path(p).resolve())
    monkeypatch.setenv('S9_CELL_IDENTITY','b'*64)
    source=tmp_path/'source';own={'per_cohort':2}
    write(source/'IDENTITY.json',own);write(source/'CASES.json',[actual])
    write(source/'COMPLETE.json',{'accepted':True,'construction_only':True,'role':'pilot',
        'identity_sha256':digest(own),'outputs':closure([source/'CASES.json'])})
    out=tmp_path/'private/selection-case-pilots/small'
    done=selection_cases.prepare(out,source,'pilot')
    assert not done['accepted'] and done['selected_series']==done['assigned_series']==1
    assert done['requested_series']==2 and read(out/'REALIZATION.json')[0]['realized']
    assert selection_cases.prepare(out,source,'pilot')==done
    with pytest.raises(ValueError):selection_cases.prepare(out,source,'pilot',1)
