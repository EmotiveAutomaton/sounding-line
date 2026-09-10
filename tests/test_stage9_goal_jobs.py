import copy
from pathlib import Path
import pytest
from runners.stage9.series_cases import construct_attempt, COHORTS
from runners.stage9.goal_cases import eligibility, counterfactual, GOALS
from runners.stage9.goal_jobs import forecast_unit
from runners.stage9.mark_program import neutral_program
from runners.stage9.common import read
from runners.stage9.launch import handler_operation


@pytest.fixture(scope='module')
def actual():
    for i,cohort in enumerate(COHORTS):
        c=construct_attempt(key='goal-transfer-fixture-'+str(i),cohort=cohort,role='pilot',dose=7)
        if c['realized'] and eligibility(c)[0]['eligible']:
            return c
    pytest.fail('fixed known-answer fixtures do not realize a goal-transfer case')


def test_goal_reversal_and_harder_control_preserve_skill_and_ignore_old_future(actual):
    check,goal,harder=eligibility(actual)
    assert check['eligible'] and goal.law==harder.law and goal.residue==harder.residue
    action=next(a for a in goal.pending if a['type']=='restructure')
    assert goal.apply(action,verify_outcome=False)['goal']==check['new_purpose']
    for condition in ('goal','harder'):
        target=counterfactual(actual,condition)
        bad=copy.deepcopy(actual);bad['target']='old unseen future changed'
        bad['source_worlds'][0]['trajectory']['steps']=bad['source_worlds'][0]['trajectory']['steps'][:bad['requested_boundary']]
        assert counterfactual(bad,condition)==target
    no_control=copy.deepcopy(actual)
    no_control['source_worlds'][0]['state']['external_context']['deadline']='tight'
    no_control['source_worlds'][0]['state']['belief_state']['believed_deadline']='tight'
    assert not eligibility(no_control)[0]['eligible']


def test_complete_paired_goal_grid_and_checked_reentry(actual,tmp_path):
    candidates={};purposes={}
    for i,purpose in enumerate(GOALS):
        p=neutral_program();p['purpose']['restructure']=float(i)
        candidates[purpose]=p;purposes[purpose]=purpose
    package={'library':{'candidates':candidates,'prior':{c:.25 for c in candidates},
                       'shared_groups':{c:'fixture-maker' for c in candidates}},
             'types':{'process_record':{t:1/8 for t in p['purpose']}}}
    evidence=[]
    for condition in ('goal','harder'):
        case={**actual,'goal_transfer':counterfactual(actual,condition)}
        out=tmp_path/condition;row=forecast_unit(case,package,purposes,out)
        assert row['truth']==case['goal_transfer']['target'] and row['costs'][0]['accepted']
        cell=row['rows']['process_record|'+condition]
        assert len(cell['predictions'])==6 and all(cell['validity'].values())
        visible=read(Path(row['costs'][0]['capsule'])/'evidence.json')
        assert not {'truth','oracle','goal_transfer','source_worlds'}.intersection(visible)
        evidence.append(visible['evidence'])
        assert forecast_unit(case,package,purposes,out,resume_only=True)==row
        bad=copy.deepcopy(case);bad['goal_transfer']['target']='changed'
        with pytest.raises(ValueError,match='future changed'):forecast_unit(bad,package,purposes,out,resume_only=True)
    assert evidence[0]==evidence[1]
    assert handler_operation({'module':'runners.stage9.purpose_jobs','arguments':['--consumer','goal']})[1]=='predict-goal'


def test_source_shortfall_and_condition_specific_identity(actual,tmp_path,monkeypatch):
    from runners.stage9 import goal_cases
    from runners.stage9.common import write, closure, digest
    monkeypatch.setattr(goal_cases,'ROOT',tmp_path)
    monkeypatch.setattr(goal_cases,'inside',lambda p:Path(p).resolve())
    monkeypatch.setenv('S9_CELL_IDENTITY','a'*64)
    source=tmp_path/'source';identity={'per_cohort':2}
    write(source/'IDENTITY.json',identity);write(source/'CASES.json',[actual])
    write(source/'COMPLETE.json',{'accepted':True,'construction_only':True,'role':'pilot',
                                'identity_sha256':digest(identity),'outputs':closure([source/'CASES.json'])})
    for condition in ('goal','harder'):
        out=tmp_path/'private/goal-case-pilots'/condition
        result=goal_cases.prepare(out,source,'pilot',condition)
        assert result['scope']=='pilot' and result['condition']==condition
        assert result['requested_series']==2 and result['selected_series']==1 and result['accepted'] is False
        assert goal_cases.prepare(out,source,'pilot',condition)==result
        other='goal' if condition=='harder' else 'harder'
        with pytest.raises(ValueError):goal_cases.prepare(out,source,'pilot',other)
