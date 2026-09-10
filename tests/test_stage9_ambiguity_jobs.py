import copy
from pathlib import Path
import pytest
from runners.stage9.series_cases import construct_attempt,COHORTS
from runners.stage9.ambiguity_cases import inspect,construct,prepare
from runners.stage9.ambiguity_jobs import QUESTIONS,forecast_unit,targets
from runners.stage9.ambiguity_operations import inputs,evaluate_unit
from runners.stage9.mark_program import neutral_program
from runners.stage9.common import read,write,closure,digest


@pytest.fixture(scope='module')
def actual():
    for i,cohort in enumerate(COHORTS):
        c=construct_attempt(key='ambiguity-jobs-fixture-'+str(i),cohort=cohort,role='pilot',dose=0)
        if c['realized'] and inspect(c)[0]['eligible']:
            return {**c,'ambiguity':construct(c)}
    pytest.fail('fixed fixtures did not realize ambiguity')


def test_actual_three_caps_keep_six_targets_and_resume_exactly(actual,tmp_path):
    package={'library':{'candidates':{'p':neutral_program()},'prior':{'p':1.}}}
    row=forecast_unit(actual,package,{},tmp_path/'calls')
    assert len(row['costs'])==3 and all(c['accepted'] for c in row['costs'])
    assert set(row['questions'])==set(QUESTIONS)
    assert {q:r['truth'] for q,r in row['questions'].items()}==targets(actual)
    for c in row['costs']:
        evidence=read(Path(c['capsule'])/'evidence.json')
        assert set(evidence)=={'evidence','candidates','prior','histories','observed_future'}
        assert evidence['evidence']['view']==('process_record' if c['operation']=='record' else 'artifact')
    h=actual['ambiguity']['true_history']
    assert row['questions']['history_record']['predictions']['inferred'][h]==1.
    assert forecast_unit(actual,package,{},tmp_path/'calls',resume_only=True)==row
    bad=copy.deepcopy(actual);bad['ambiguity']['outcomes']['changed']['target']='invented'
    with pytest.raises(ValueError,match='changed'):forecast_unit(bad,package,{},tmp_path/'calls',resume_only=True)


def test_neural_inputs_obey_question_specific_information_boundary(actual):
    before=inputs(actual);bad=copy.deepcopy(actual)
    histories=sorted(bad['ambiguity']['offered_histories']);h=bad['ambiguity']['true_history']
    bad['ambiguity']['true_history']=histories[(histories.index(h)+1)%len(histories)]
    after=inputs(bad)
    assert {q for q in QUESTIONS if before[q]!=after[q]}=={'history_record','future_record'}
    bad=copy.deepcopy(actual)
    target=bad['ambiguity']['outcomes']['changed']['target']
    support=bad['ambiguity']['artifact']['support']
    bad['ambiguity']['outcomes']['changed']['target']=next(a for a in support if a!=target)
    assert {q for q in QUESTIONS if before[q]!=inputs(bad)[q]}=={'history_after'}
    calls=[]
    def call(e,args,index):
        calls.append((e,args,index));return {'accepted':True,'prediction':{'probs':{k:1/len(e['options']) for k in e['options']}}}
    result=evaluate_unit(actual,call)
    assert len(calls)==6 and set(result['questions'])==set(QUESTIONS)
    choices=before['history_artifact']['options'].values()
    assert len({tuple(sorted(c.strip().split(' -> '))) for c in choices})==1
    assert all('numeric source law' not in e['prefix'] for e,_,_ in calls)


def test_source_shortfall_is_retained_without_replacement_or_promotion(actual,tmp_path,monkeypatch):
    from runners.stage9 import common,queue
    monkeypatch.setattr(common,'ROOT',tmp_path)
    monkeypatch.setattr(queue,'inside',lambda p:Path(p).resolve())
    monkeypatch.setenv('S9_CELL_IDENTITY','a'*64)
    source=tmp_path/'source';identity={'per_cohort':2}
    write(source/'IDENTITY.json',identity);write(source/'CASES.json',[actual])
    write(source/'COMPLETE.json',{'accepted':True,'construction_only':True,'role':'pilot',
        'identity_sha256':digest(identity),'outputs':closure([source/'CASES.json'])})
    out=tmp_path/'private/ambiguity-case-pilots/fixture'
    result=prepare(out,source,'pilot')
    assert result['accepted'] is False and result['selected_series']==1 and result['requested_series']==2
    assert prepare(out,source,'pilot')==result
    with pytest.raises(ValueError):prepare(out,source,'pilot',1)
