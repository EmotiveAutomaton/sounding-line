import copy
import pytest
from runners.stage9.goal_reader import forecast
from runners.stage9.program_inference import Budget, identity, predictive_mixture
from runners.stage9.mark_program import neutral_program, policy
from runners.stage9.artifact_view import support
from runners.stage9.erased_inference import artifact_work
from runners.stage9.comparison_runtime import execute


def bundle():
    current={'context':{'topic':'fixture','audience':'peer','tools':{'library':True,'source_access':True},
                       'deadline':'loose','sections':[{'name':'s','slots':['a','b']}]},
             'marks':['write:s:a'],'events':[{'i':0,'type':'write','section':'s','slot':'a','outcome':'done'}],
             'observed_stop':None}
    candidates={};groups={};purposes={}
    for maker in ('a','b'):
        for purpose in ('old','new'):
            key=maker+'-'+purpose;p=neutral_program()
            p['purpose']['write' if purpose=='old' else 'restructure']=3.
            p['expertise']['cost']['write']=float(maker=='b')+float(purpose=='new')
            p['history']['check']=float(maker=='a')
            candidates[key]=p;groups[key]=maker;purposes[key]=purpose
    return {'evidence':{'version':'s9-visible-artifact-v1','view':'process_record','current':current,
                       'earlier':[],'support':support(current,'process_record')},
            'candidates':candidates,'prior':{c:.25 for c in candidates},'shared_groups':groups,'purpose_groups':purposes,
            'announced_purpose':'new','deadline':'unchanged','population_types':{t:1/8 for t in neutral_program()['purpose']}}


def test_goal_change_preserves_past_and_each_original_expertise():
    b=bundle();original=copy.deepcopy(b)
    changed=forecast(b,Budget(10000));old=forecast({**b,'announced_purpose':None},Budget(10000))
    assert b==original and changed['posterior']==old['posterior']
    assert changed['historical_likelihood_receipts']==old['historical_likelihood_receipts']
    programs=copy.deepcopy(b['candidates'])
    for key,p in programs.items():p['purpose']=copy.deepcopy(b['candidates'][b['shared_groups'][key]+'-new']['purpose'])
    assert identity(programs)==changed['future_programs_sha256']
    expected=predictive_mixture(changed['posterior'],{c:policy(p,artifact_work(b['evidence']['current'])) for c,p in programs.items()})
    assert changed['predictions']['inferred_changed']==expected
    assert expected['restructure:s:order']>old['predictions']['inferred_changed']['restructure:s:order']
    harder=forecast({**b,'announced_purpose':None,'deadline':'tight'},Budget(10000))
    assert harder['posterior']==old['posterior']
    assert harder['predictions']['inferred_changed']['stop']>old['predictions']['inferred_changed']['stop']


def test_goal_null_and_missing_destination_or_private_truth_refuse():
    b=bundle()
    for p in b['candidates'].values():p['purpose']={t:0. for t in p['purpose']}
    assert forecast(b,Budget(10000))['predictions']==forecast({**b,'announced_purpose':None},Budget(10000))['predictions']
    for mutate in (lambda d:d.update(truth='old'),lambda d:d.update(announced_purpose='absent'),
                   lambda d:d['purpose_groups'].update({'a-new':'old'})):
        bad=copy.deepcopy(b);mutate(bad)
        with pytest.raises(ValueError):forecast(bad,Budget(10000))


def test_goal_transfer_actual_capsule_matches_independent_execution(tmp_path):
    b=bundle();expected=forecast(b,Budget(500000))
    result=execute(b,operation='goal_transfer',root=tmp_path/'caps')
    assert result['accepted'],result
    assert all(result['prediction'][k]==v for k,v in expected.items())
    assert not execute({**b,'hidden_future':'x'},operation='goal_transfer',root=tmp_path/'hidden')['accepted']
