import copy
from pathlib import Path
import pytest
from runners.stage9.series_cases import construct_attempt, COHORTS
from runners.stage9.transfer_cases import eligibility, counterfactual
from runners.stage9.transfer_jobs import forecast_unit
from runners.stage9.mark_program import neutral_program
from runners.stage9.common import read
from runners.stage9.launch import handler_operation


@pytest.fixture(scope='module')
def actual():
    for i in range(30):
        c = construct_attempt(key='tool-transfer-fixture-'+str(i), cohort=COHORTS[i], role='pilot', dose=7)
        if c['realized'] and eligibility(c)[0]['eligible']:
            c['transfer'] = counterfactual(c)
            return c
    pytest.fail('fixed known-answer fixture did not supply an eligible tool-removal world')


def test_conditional_selection_and_new_future_ignore_original_unseen_outcomes(actual):
    changed = copy.deepcopy(actual)
    changed['target'] = 'unseen-target-changed'
    changed['source_worlds'][0]['trajectory']['steps'] = changed['source_worlds'][0]['trajectory']['steps'][:changed['requested_boundary']]
    assert eligibility(changed)[0] == eligibility(actual)[0]
    assert counterfactual(changed) == actual['transfer']
    assert all(not k.startswith('cite:') or p == 0 for k,p in actual['transfer']['oracle'].items())


def test_complete_tool_transfer_grid_and_resume_keep_future_outside_capsules(actual,tmp_path):
    p=neutral_program();q=copy.deepcopy(p);q['purpose']['cite']=2.
    package={'library':{'candidates':{'a':p,'b':q},'prior':{'a':.5,'b':.5},'shared_groups':{'a':'a','b':'b'}},
             'models':{'process_record':{'fixture':{'version':'s9-conditional-choice-v1','weights':{},'individual':False,'uniform_mixture':.01}}},
             'types':{'process_record':{t:1/8 for t in p['purpose']}}}
    result=forecast_unit(actual,package,{},tmp_path/'grid')
    assert len(result['costs'])==2 and all(c['accepted'] for c in result['costs'])
    assert result['truth']==actual['transfer']['target']
    for cost in result['costs']:
        visible=read(Path(cost['capsule'])/'evidence.json')
        assert not {'truth','transfer','oracle','source_worlds'}.intersection(visible)
    context=read(Path(result['costs'][1]['capsule'])/'evidence.json')
    assert context['evidence']==actual['views']['process_record']
    assert forecast_unit(actual,package,{},tmp_path/'grid',resume_only=True)==result
    bad=copy.deepcopy(actual);bad['transfer']['target']='changed'
    with pytest.raises(ValueError,match='future changed'):
        forecast_unit(bad,package,{},tmp_path/'grid',resume_only=True)
    assert handler_operation({'module':'runners.stage9.purpose_jobs','arguments':['--consumer','transfer']})[1]=='predict-transfer'


def test_source_preparation_retains_conditional_shortfall_and_checked_reentry(actual,tmp_path,monkeypatch):
    from runners.stage9 import transfer_cases
    from runners.stage9.common import write, closure, digest
    monkeypatch.setattr(transfer_cases,'ROOT',tmp_path)
    monkeypatch.setattr(transfer_cases,'inside',lambda p:Path(p).resolve())
    monkeypatch.setenv('S9_CELL_IDENTITY','a'*64)
    source=tmp_path/'source';identity={'per_cohort':2}
    write(source/'IDENTITY.json',identity);write(source/'CASES.json',[actual])
    write(source/'COMPLETE.json',{'accepted':True,'construction_only':True,'role':'pilot',
                                'identity_sha256':digest(identity),'outputs':closure([source/'CASES.json'])})
    out=tmp_path/'private/transfer-case-pilots/one-domain'
    result=transfer_cases.prepare(out,source,'pilot')
    assert result['scope']=='pilot' and result['role']=='pilot'
    assert result['requested_series']==2 and result['selected_series']==1
    assert result['accepted'] is False and result['disposition']=='IMPLEMENTATION INVALID'
    assert transfer_cases.prepare(out,source,'pilot')==result
