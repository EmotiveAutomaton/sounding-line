import copy
from pathlib import Path
import pytest

from runners.stage9 import familiarity_cases
from runners.stage9.common import read,write,digest,closure
from runners.stage9.familiarity_jobs import forecast_unit
from runners.stage9.launch import handler_operation
from runners.stage9.mark_program import neutral_program
from tests.test_stage9_familiarity_reader import actual


def test_actual_complete_grid_keeps_distinct_targets_and_resumes(actual,tmp_path):
    cf=familiarity_cases.construct(actual);p=neutral_program()
    package={'library':{'candidates':{'a':p},'prior':{'a':1.},'shared_groups':{'a':'a'}},
        'models':{v:{'fixture':{'version':'s9-conditional-choice-v1','weights':{},'individual':False,'uniform_mixture':.01}}
                  for v in ('artifact','process_record')},
        'types':{v:{t:1/8 for t in p['purpose']} for v in ('artifact','process_record')}}
    case={**actual,'familiarity':cf}
    row=forecast_unit(case,package,{},tmp_path/'grid')
    assert len(row['costs'])==4 and all(c['accepted'] for c in row['costs'])
    assert len(row['questions'])==16 and len(row['metrics'])==8
    for q,cell in row['questions'].items():
        assert all(cell['validity'].values())
        assert len(cell['predictions'])==(5 if cell['kind']=='recognition' else 9)
        expected=cf['queries'][q.split('|')[0]][cell['kind']+'_target']
        assert cell['truth']==expected
    for cost in row['costs']:
        visible=read(Path(cost['capsule'])/'evidence.json')
        assert not {'target','oracle','future_event','source_worlds','queries','private_factors'} & set(visible)
    assert forecast_unit(case,package,{},tmp_path/'grid',resume_only=True)==row
    bad=copy.deepcopy(case);bad['familiarity']['outcomes']['expected']['target']='changed'
    with pytest.raises(ValueError,match='future changed'):forecast_unit(bad,package,{},tmp_path/'grid',resume_only=True)
    assert handler_operation({'module':'runners.stage9.purpose_jobs','arguments':['--consumer','familiarity']})[1]=='predict-familiarity'
    assert handler_operation({'module':'runners.stage9.familiarity_analysis','arguments':['--operation','evaluate']})[1]=='evaluate'
    with pytest.raises(ValueError,match='actual operation'):
        handler_operation({'module':'runners.stage9.familiarity_analysis','arguments':[]})


def test_fixed_source_shortfall_is_retained_with_stable_reentry(actual,tmp_path,monkeypatch):
    monkeypatch.setattr(familiarity_cases,'ROOT',tmp_path)
    monkeypatch.setattr(familiarity_cases,'inside',lambda p:Path(p).resolve())
    monkeypatch.setenv('S9_CELL_IDENTITY','b'*64)
    source=tmp_path/'source';own={'per_cohort':2}
    write(source/'IDENTITY.json',own);write(source/'CASES.json',[actual])
    write(source/'COMPLETE.json',{'accepted':True,'construction_only':True,'role':'pilot',
        'identity_sha256':digest(own),'outputs':closure([source/'CASES.json'])})
    out=tmp_path/'private/familiarity-case-pilots/small'
    done=familiarity_cases.prepare(out,source,'pilot')
    assert not done['accepted'] and done['selected_series']==done['assigned_series']==1
    assert done['requested_series']==2 and read(out/'REALIZATION.json')[0]['realized']
    assert familiarity_cases.prepare(out,source,'pilot')==done
    with pytest.raises(ValueError):familiarity_cases.prepare(out,source,'pilot',1)
