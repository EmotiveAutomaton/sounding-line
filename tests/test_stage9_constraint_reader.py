import copy
import itertools
import math
from pathlib import Path

import pytest

from runners.stage9 import constraint_reader as reader, comparison_runtime
from runners.stage9.artifact_view import support
from runners.stage9.common import read
from runners.stage9.constraint_cases import construct, CONDITIONS
from runners.stage9.mark_program import neutral_program
from runners.stage9.program_inference import Budget
from runners.stage9.series_cases import construct_attempt, COHORTS


def work(topic='earlier', marks=()):
    return {'context': {'topic': topic, 'audience': 'peer',
        'tools': {'library': True, 'source_access': True}, 'deadline': 'loose',
        'sections': [{'name': 's', 'slots': ['a', 'b']}]}, 'marks': sorted(marks)}


def test_complete_known_budget_distribution_preserves_failure_and_stopping(monkeypatch):
    hazard, success_rate = .25, 1.
    def policy(program, current):
        available = sorted({'write:s:a', 'write:s:b'} - set(current['marks']))
        return {'stop': 1.} if not available else {'stop': hazard, **{a:(1-hazard)/len(available) for a in available}}
    def success(program, current):
        return {a:success_rate for a in policy(program, current) if a != 'stop'}
    monkeypatch.setattr(reader, 'policy', policy); monkeypatch.setattr(reader, 'success_probabilities', success)
    p = neutral_program()
    expected = {():.25, ('write:s:a',):.09375, ('write:s:b',):.09375, ('write:s:a','write:s:b'):.5625}
    actual = {marks:math.exp(reader.artifact_observation_likelihood(p,work(marks=marks),Budget(100),2)['log_mass']) for marks in expected}
    assert actual == pytest.approx(expected,abs=1e-14) and sum(actual.values()) == pytest.approx(1.,abs=1e-14)
    success_rate = .5
    assert math.exp(reader.artifact_observation_likelihood(p,work(),Budget(100),1)['log_mass']) == pytest.approx(.625,abs=1e-14)
    success_rate, hazard = 1., .75
    assert math.exp(reader.artifact_observation_likelihood(p,work(),Budget(100),2)['log_mass']) > .7


def test_artifact_mass_equals_sum_of_all_actual_records():
    p = neutral_program(); p['available_types'] = ['write']; p['action_noise'] = 0.
    p['outcome_noise'] = 0.; p['expertise']['success']['write'] = .6
    initial = work(); masses = {}
    def enumerate_records(current, events, mass):
        choices = reader.policy(p, current); successes = reader.success_probabilities(p, current)
        if len(events) == 2:
            record = {**current, 'events':events, 'observed_stop':None}
            assert math.exp(reader.record_observation_likelihood(p,record,Budget(100),2)['log_mass']) == pytest.approx(mass,abs=1e-14)
            key = tuple(current['marks']); masses[key] = masses.get(key,0.) + mass
            return
        record = {**current, 'events':events, 'observed_stop':True}
        stopped = math.exp(reader.record_observation_likelihood(p,record,Budget(100),2)['log_mass'])
        assert stopped == pytest.approx(mass*choices['stop'],abs=1e-14)
        key = tuple(current['marks']); masses[key] = masses.get(key,0.) + stopped
        for action, probability in choices.items():
            if action == 'stop' or not probability: continue
            kind, section, slot = action.split(':')
            for outcome, q in (('done',successes[action]),('failed',1-successes[action])):
                if not q: continue
                event = {'i':len(events),'type':kind,'section':section,'slot':slot,'outcome':outcome}
                changed = {**current,'marks':sorted([*current['marks'],action]) if outcome=='done' else current['marks']}
                enumerate_records(changed,[*events,event],mass*probability*q)
    enumerate_records(initial,[],1.)
    assert sum(masses.values()) == pytest.approx(1.,abs=1e-12)
    for marks, mass in masses.items():
        assert math.exp(reader.artifact_observation_likelihood(p,work(marks=marks),Budget(1000),2)['log_mass']) == pytest.approx(mass,abs=1e-12)


def test_known_null_and_present_signal_and_horizon_refusals():
    p = neutral_program(); target = work('future'); earlier = work()
    evidence = {'version':'s9-visible-artifact-v1','view':'artifact','current':target,'earlier':[earlier],'support':support(target,'artifact')}
    bundle = {'evidences':{'artifact':evidence},'maximum_actions':3,'candidates':{'a':p,'b':copy.deepcopy(p)},'prior':{'a':.3,'b':.7},'shared_groups':{'a':'a','b':'b'}}
    result = reader.forecast(bundle,Budget(1000))['queries']['artifact']
    assert result['weights']['program_mixture'] == pytest.approx(bundle['prior'],abs=1e-14)
    assert result['predictions']['differentiated_maker'] == pytest.approx(result['predictions']['program_prior'],abs=1e-14)
    bundle['candidates']['a']['stop']['intercept'] = 2.
    bundle['candidates']['a']['purpose']['write'] = 3.
    result = reader.forecast(bundle,Budget(1000))['queries']['artifact']
    assert result['weights']['program_mixture']['a'] > .7
    assert max(abs(result['predictions']['program_mixture'][k]-result['predictions']['program_prior'][k]) for k in evidence['support']) > .05
    bad = {**earlier,'events':[],'observed_stop':None}
    with pytest.raises(ValueError,match='record must end'): reader.record_observation_likelihood(p,bad,Budget(100),3)
    with pytest.raises(ValueError,match='undeclared'): reader.forecast({**bundle,'true_maker':'a'},Budget(1000))
    with pytest.raises(ValueError,match='observation budget'): reader.forecast({**bundle,'maximum_actions':4},Budget(1000))
    same_header = copy.deepcopy(bundle); same_header['evidences']['artifact']['current'] = earlier
    same = reader.forecast(same_header,Budget(1000))['queries']['artifact']
    assert same['weights'] == result['weights']  # bounded empty earlier work still informs


@pytest.fixture(scope='module')
def actual():
    case = construct_attempt(key='bounded-creation-fixture',cohort=COHORTS[0],role='pilot',dose=7)
    assert case['realized']
    return case


def test_creation_cross_retains_stops_and_ignores_old_unseen_trajectories(actual):
    result = construct(actual)
    assert result['freedom_realized'] and all(v['realized'] for v in result['pressure_checks'].values())
    assert set(result['views']) == {v+'|'+c for v in ('artifact','process_record') for c in CONDITIONS}
    for c in CONDITIONS:
        a, b = result['views']['artifact|'+c],result['views']['process_record|'+c]
        assert a['current']['marks'] == b['current']['marks'] == []
        assert a['earlier'][0]['marks'] == b['earlier'][0]['marks']
        assert (b['earlier'][0]['observed_stop'] is True) == (len(b['earlier'][0]['events']) < 3)
    changed = copy.deepcopy(actual); changed['target'] = 'not the new target'
    for w in changed['source_worlds']: w['trajectory'] = {'steps':[],'changes':[{'unseen':'mutated'}]}
    assert construct(changed) == result


def test_actual_restricted_creation_reader_and_hidden_field_refusal(actual,tmp_path):
    c = construct(actual); p = neutral_program()
    bundle = {'evidences':c['views'],'maximum_actions':c['maximum_actions'],
              'candidates':{'a':p},'prior':{'a':1.},'shared_groups':{'a':'a'}}
    out = comparison_runtime.execute(bundle,operation='bounded_creation',budget=800000,root=tmp_path/'good')
    assert out['accepted'] and len(out['prediction']['queries']) == 8
    assert read(Path(out['capsule'])/'evidence.json') == bundle
    assert 'reader/constraint_reader.py' in out['copied_sources']['files']
    for q in out['prediction']['queries'].values():
        assert q['exact_within_declared_model'] and q['distinct_earlier_works'] == 1
        assert q['predictions']['program_mixture'] == q['predictions']['program_prior']
    bad = comparison_runtime.execute({**bundle,'target':c['target']},operation='bounded_creation',budget=800000,root=tmp_path/'bad')
    assert not bad['accepted']
