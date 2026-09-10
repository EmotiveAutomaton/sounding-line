import copy
from pathlib import Path
import pytest
from runners.stage9.series_cases import construct_attempt,COHORTS
from runners.stage9.cue_cases import eligibility,counterfactual
from runners.stage9.cue_jobs import forecast_unit
from runners.stage9.mark_program import neutral_program
from runners.stage9.common import read
from runners.stage9.launch import handler_operation


@pytest.fixture(scope='module')
def actual():
    for i,cohort in enumerate(COHORTS):
        c=construct_attempt(key='context-cue-fixture-'+str(i),cohort=cohort,role='pilot',dose=7)
        if c['realized'] and eligibility(c)[0]['eligible']:return c
    pytest.fail('fixed context fixtures did not realize both interventions')


def test_context_scope_and_futures_do_not_depend_on_old_unseen_outcomes(actual):
    check,global_change,local_change=eligibility(actual)
    assert check['eligible'] and global_change.law==local_change.law and global_change.residue==local_change.residue
    for condition in ('global','local'):
        future=counterfactual(actual,condition)
        bad=copy.deepcopy(actual);bad['target']='changed unseen target'
        bad['source_worlds'][0]['trajectory']['steps']=bad['source_worlds'][0]['trajectory']['steps'][:bad['requested_boundary']]
        assert counterfactual(bad,condition)==future
    empty=copy.deepcopy(actual);empty['views']['process_record']['current']['marks']=[]
    assert not eligibility(empty)[0]['eligible']


def test_full_context_report_grid_is_matched_and_keeps_truth_labels_private(actual,tmp_path):
    p=neutral_program()
    package={'library':{'candidates':{'a':p},'prior':{'a':1.},'shared_groups':{'a':'a'}},
             'types':{'process_record':{t:1/8 for t in p['purpose']}}}
    previous=None
    for condition in ('global','local'):
        case={**actual,'context_cue':counterfactual(actual,condition)};out=tmp_path/condition
        row=forecast_unit(case,package,{},out)
        assert row['truth']==case['context_cue']['target'] and len(row['costs'])==3
        assert set(row['rows'])=={'process_record|'+t for t in ('true','false','redundant')}
        for cost in row['costs']:
            assert cost['accepted']
            visible=read(Path(cost['capsule'])/'evidence.json')
            assert not {'truth','treatment','source_is_true','oracle','source_worlds','context_cue'}.intersection(visible)
            if previous is not None:assert visible['evidence']==previous
            previous=visible['evidence']
        redundant=row['rows']['process_record|redundant']['predictions']
        assert redundant['inferred_cued']==redundant['inferred_uncued']
        assert forecast_unit(case,package,{},out,resume_only=True)==row
        bad=copy.deepcopy(case);bad['context_cue']['target']='changed'
        with pytest.raises(ValueError,match='future changed'):forecast_unit(bad,package,{},out,resume_only=True)
    assert handler_operation({'module':'runners.stage9.purpose_jobs','arguments':['--consumer','cue']})[1]=='predict-cue'


def test_context_source_shortfall_and_changed_condition_refuse(actual,tmp_path,monkeypatch):
    from runners.stage9 import cue_cases
    from runners.stage9.common import write,closure,digest
    monkeypatch.setattr(cue_cases,'ROOT',tmp_path);monkeypatch.setattr(cue_cases,'inside',lambda p:Path(p).resolve())
    monkeypatch.setenv('S9_CELL_IDENTITY','a'*64)
    source=tmp_path/'source';identity={'per_cohort':2}
    write(source/'IDENTITY.json',identity);write(source/'CASES.json',[actual])
    write(source/'COMPLETE.json',{'accepted':True,'construction_only':True,'role':'pilot',
                                'identity_sha256':digest(identity),'outputs':closure([source/'CASES.json'])})
    for condition in ('global','local'):
        out=tmp_path/'private/cue-case-pilots'/condition
        result=cue_cases.prepare(out,source,'pilot',condition)
        assert result['scope']=='pilot' and result['condition']==condition
        assert result['selected_series']==1 and result['requested_series']==2 and result['accepted'] is False
        assert cue_cases.prepare(out,source,'pilot',condition)==result
        with pytest.raises(ValueError):cue_cases.prepare(out,source,'pilot','local' if condition=='global' else 'global')
