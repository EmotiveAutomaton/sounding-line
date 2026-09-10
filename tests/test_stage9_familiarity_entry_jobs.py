import copy
from pathlib import Path
import pytest
from runners.stage9 import familiarity_entry_cases as sources,familiarity_entry_jobs as jobs,selection_jobs
from runners.stage9.common import read,write,digest,closure
from runners.stage9.launch import handler_operation
from runners.stage9.mark_program import neutral_program
from tests.test_stage9_familiarity_entry import case


def test_actual_entry_cross_keeps_complete_budgets_own_targets_and_selected_only_purchases(case,tmp_path,monkeypatch):
    monkeypatch.setattr(selection_jobs,'STRATEGIES',('random','future_prediction'))
    cf=sources.construct(case);p=neutral_program()
    package={'library':{'candidates':{'a':p},'prior':{'a':1.},'shared_groups':{'a':'a'}},
        'models':{v:{'fixture':{'version':'s9-conditional-choice-v1','weights':{},'individual':False,'uniform_mixture':.01}}
                  for v in ('artifact','process_record')},
        'types':{v:{t:1/8 for t in p['purpose']} for v in ('artifact','process_record')}}
    current={**case,'familiarity_entry':cf};row=jobs.forecast_unit(current,package,{},tmp_path/'grid')
    assert set(row['conditions'])==set(cf['conditions']) and all(c['accepted'] for c in row['costs'])
    for name,result in row['conditions'].items():
        assert result['truth']==cf['conditions'][name]['target'] and len(result['rows'])==16
        for cell in result['rows'].values():
            assert all(cell['validity'].values()) and len(cell['predictions'])==7
            assert cell['preview_cost']==3 and cell['recognition']==pytest.approx({'same':.5,'different':.5},abs=1e-14)
            if cell['requested_budget']==3:assert cell['full_view'] and cell['purchase_cost']==3
            if cell['requested_budget']=='stopped':assert cell['purchase_cost']==0
        for trace in result['traces'].values():
            for index,step in enumerate(trace['steps']):
                visible=read(Path(step['capsule'])/'evidence.json')
                assert len(visible['purchases'])==index and set(visible['purchases'])==set(step['purchased'])
                assert not {'target','oracle','recognition_target','condition','source_worlds','private_factors'}&set(visible)
                if index:assert trace['steps'][index-1]['output']['selected'] in visible['purchases']
    for stratum in ('expected','unexpected'):
        a,b=(row['conditions'][f+'|'+stratum] for f in ('familiar','unfamiliar'))
        for q in a['rows']:assert a['rows'][q]['predictions']['program_prior']==b['rows'][q]['predictions']['program_prior']
    assert jobs.forecast_unit(current,package,{},tmp_path/'grid',resume_only=True)==row
    changed=copy.deepcopy(current);changed['familiarity_entry']['conditions']['familiar|expected']['target']='changed'
    with pytest.raises(ValueError,match='future changed'):jobs.forecast_unit(changed,package,{},tmp_path/'grid',resume_only=True)
    assert handler_operation({'module':'runners.stage9.purpose_jobs','arguments':['--consumer','familiarity-entry']})[1]=='predict-familiarity-entry'


def test_entry_source_shortfall_is_retained_and_cannot_look_complete(case,tmp_path,monkeypatch):
    monkeypatch.setattr(sources,'ROOT',tmp_path);monkeypatch.setattr(sources,'inside',lambda p:Path(p).resolve())
    monkeypatch.setenv('S9_CELL_IDENTITY','b'*64)
    source=tmp_path/'source';own={'per_cohort':2}
    write(source/'IDENTITY.json',own);write(source/'CASES.json',[case])
    write(source/'COMPLETE.json',{'accepted':True,'construction_only':True,'role':'pilot',
        'identity_sha256':digest(own),'outputs':closure([source/'CASES.json'])})
    out=tmp_path/'private/familiarity-entry-case-pilots/small';done=sources.prepare(out,source,'pilot')
    assert not done['accepted'] and done['selected_series']==done['assigned_series']==1 and done['requested_series']==2
    assert read(out/'REALIZATION.json')[0]['realized'] and sources.prepare(out,source,'pilot')==done
    with pytest.raises(ValueError):sources.prepare(out,source,'pilot',1)
