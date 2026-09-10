import copy
import math

import pytest

from runners.stage9 import familiarity_reader as reader, comparison_runtime
from runners.stage9.artifact_view import support
from runners.stage9.familiarity_cases import construct, choice_strata
from runners.stage9.mark_program import neutral_program
from runners.stage9.program_inference import Budget
from runners.stage9.series_cases import construct_attempt, COHORTS


def work(topic='current', marks=()):
    return {'context':{'topic':topic,'audience':'peer','tools':{'library':True,'source_access':True},
        'deadline':'loose','sections':[{'name':'s','slots':['a','b']}]}, 'marks':sorted(marks)}


def bundle(programs=None):
    current = work(marks=['write:s:a'])
    ev = {'version':'s9-visible-artifact-v1','view':'artifact','current':current,
        'earlier':[work('prior', ['write:s:a'])], 'support':support(current,'artifact')}
    programs = programs or {'a':neutral_program(),'b':neutral_program()}
    return {'evidences':{'q':ev},'maximum_actions':3,'candidates':programs,
            'prior':{c:1/len(programs) for c in programs},
            'shared_groups':{c:c for c in programs},'same_prior':.5,
            'population_types':{t:1/8 for t in neutral_program()['purpose']}}


def test_conditioned_first_action_mass_preserves_failed_observation_and_erasure():
    p = neutral_program(); p['available_types']=['write']; p['action_noise']=p['outcome_noise']=0.
    p['expertise']['success']['write']=.6
    initial = work(); total=0.; artifact_masses={():0.}
    for a in ('write:s:a','write:s:b'):
        for outcome, expected in (('done',.3),('failed',.2)):
            mark = [a] if outcome=='done' else []
            record = {**work(marks=mark),'events':[{'i':0,'type':'write','section':'s','slot':a.split(':')[-1],'outcome':outcome}],
                      'observed_stop':None}
            mass=math.exp(reader.first_action_likelihood(p,record,'process_record',Budget(100)))
            assert mass==pytest.approx(expected,abs=1e-14)
            total+=mass; artifact_masses[tuple(mark)]=artifact_masses.get(tuple(mark),0.)+mass
    assert total==pytest.approx(1.,abs=1e-14)
    for marks,mass in artifact_masses.items():
        assert math.exp(reader.first_action_likelihood(p,work(marks=marks),'artifact',Budget(100)))==pytest.approx(mass,abs=1e-14)
    p['stop']['intercept']=9.
    assert math.exp(reader.first_action_likelihood(p,initial,'artifact',Budget(100)))==pytest.approx(.4,abs=1e-12)


def test_identical_makers_leave_recognition_prior_and_forecasts_equal():
    b=bundle(); b['same_prior']=.3
    q=reader.forecast(b,Budget(1000))['queries']['q']
    assert q['recognition']==pytest.approx({'same':.3,'different':.7},abs=1e-14)
    for p in q['predictions'].values():
        assert p==pytest.approx(q['predictions']['program_prior'],abs=1e-14)
    with pytest.raises(ValueError,match='undeclared'): reader.forecast({**b,'true_maker':'a'},Budget(1000))
    with pytest.raises(ValueError,match='budget'): reader.forecast(b,Budget(1))
    bad=copy.deepcopy(b); bad['evidences']['q']['current']['marks'].append('write:s:b')
    bad['evidences']['q']['support']=support(bad['evidences']['q']['current'],'artifact')
    with pytest.raises(ValueError,match='exactly one'): reader.forecast(bad,Budget(1000))


def test_expected_signature_can_recognize_without_high_surprise(monkeypatch):
    p=neutral_program(); alt=copy.deepcopy(p); alt['purpose']['write']=99.
    b=bundle({'a':p,'b':alt})
    def likelihood(program,work,budget,maximum):
        return {'log_mass':math.log(.9 if program['purpose']['write']!=99. else .1)}
    monkeypatch.setattr(reader,'artifact_observation_likelihood',likelihood)
    def current(program,work,view,budget):
        expected = work['marks']==['write:s:a']
        usual=.9 if program['purpose']['write']!=99. else .1
        return math.log(usual if expected else 1-usual)
    monkeypatch.setattr(reader,'first_action_likelihood',current)
    expected=reader.forecast(b,Budget(1000))['queries']['q']
    # Archive posterior .9/.1; P(observation|same)=.82 vs independent=.5.
    assert expected['recognition']['same']==pytest.approx(.82/1.32,abs=1e-14)
    assert expected['raw_observation_surprise_nats']==pytest.approx(-math.log(.66),abs=1e-14)
    b['evidences']['q']['current']['marks']=['write:s:b']
    b['evidences']['q']['support']=support(b['evidences']['q']['current'],'artifact')
    unexpected=reader.forecast(b,Budget(1000))['queries']['q']
    assert unexpected['recognition']['same']==pytest.approx(.18/.68,abs=1e-14)
    assert expected['recognition']['same'] > unexpected['recognition']['same']
    assert expected['raw_observation_surprise_nats'] < unexpected['raw_observation_surprise_nats']


@pytest.fixture(scope='module')
def actual():
    case=construct_attempt(key='familiarity-source-fixture-v1',cohort=COHORTS[0],role='pilot',dose=7)
    assert case['realized']
    return case


def test_archive_purpose_does_not_become_the_new_works_purpose(monkeypatch):
    programs={}
    for i in range(4):
        p=neutral_program();p['purpose']['write']=float(i);programs[str(i)]=p
    b=bundle(programs);b['shared_groups']={'0':'A','1':'A','2':'B','3':'B'}
    def archive(program,work,budget,maximum):
        return {'log_mass':math.log(.9 if int(program['purpose']['write'])%2==0 else .1)}
    monkeypatch.setattr(reader,'artifact_observation_likelihood',archive)
    monkeypatch.setattr(reader,'first_action_likelihood',lambda *args:math.log(.4))
    out=reader.forecast(b,Budget(1000))['queries']['q']
    assert out['archive_maker_weights']==pytest.approx({'A':.5,'B':.5},abs=1e-14)
    assert out['current_program_weights_before']==pytest.approx(dict.fromkeys(programs,.25),abs=1e-14)
    assert out['weights']['assume_same']==pytest.approx(dict.fromkeys(programs,.25),abs=1e-14)


def test_actual_cross_preserves_current_futures_and_public_matching(actual):
    cf=construct(actual)
    assert len(cf['views'])==8
    assert min(cf['choice_strata']['expected'].values()) > max(cf['choice_strata']['unexpected'].values())
    for stratum in ('expected','unexpected'):
        names=[q for q,m in cf['queries'].items() if m['view']=='artifact' and m['condition'].endswith('|'+stratum)]
        a,b=(cf['views'][q] for q in names)
        assert a['current']==b['current'] and a['support']==b['support']
        assert cf['queries'][names[0]]['future_target']==cf['queries'][names[1]]['future_target']
        assert [w['context'] for w in a['earlier']]==[w['context'] for w in b['earlier']]
    changed=copy.deepcopy(actual); changed['target']='old future changed'
    for w in changed['source_worlds']: w['trajectory']={'steps':[],'changes':[{'unknown':'future'}]}
    assert construct(changed)==cf
    with pytest.raises(ValueError,match='distinct expected'): choice_strata({'a':.5,'b':.5,'stop':0.})


def test_actual_restricted_familiarity_execution_and_truth_refusal(actual,tmp_path):
    cf=construct(actual)
    b={'evidences':cf['views'],'maximum_actions':3,'candidates':{'one':neutral_program()},
       'prior':{'one':1.},'shared_groups':{'one':'one'},'same_prior':.5,
       'population_types':{t:1/8 for t in neutral_program()['purpose']}}
    result=comparison_runtime.execute(b,operation='maker_familiarity',budget=800000,root=tmp_path/'good')
    assert result['accepted'] and len(result['prediction']['queries'])==8
    for q in result['prediction']['queries'].values():
        assert q['recognition']==pytest.approx({'same':.5,'different':.5},abs=1e-12)
        assert q['exact_within_declared_model']
    denied=comparison_runtime.execute({**b,'queries':cf['queries']},operation='maker_familiarity',budget=800000,root=tmp_path/'bad')
    assert not denied['accepted']
