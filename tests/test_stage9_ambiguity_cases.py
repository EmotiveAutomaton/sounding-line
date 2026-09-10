import copy
import itertools
import math
import pytest
from runners.stage9.series_cases import construct_attempt,COHORTS
from runners.stage9.ambiguity_cases import inspect,construct,_draw


@pytest.fixture(scope='module')
def actual():
    for i,cohort in enumerate(COHORTS):
        c=construct_attempt(key='ambiguity-fixture-'+str(i),cohort=cohort,role='pilot',dose=0)
        if c['realized'] and inspect(c)[0]['eligible']:return c
    pytest.fail('fixed source fixtures cannot realize partial ambiguity')


def test_actual_source_has_identical_marks_partial_classes_and_exact_conditional_odds(actual):
    check,prepared=inspect(actual);result=construct(actual)
    assert check['completed_histories']==6 and check['old_predictive_classes']==1 and check['changed_predictive_classes']==2
    assert set(result['offered_histories'])==set(result['history_posterior_oracle'])
    assert all(set(':'.join(e[k] for k in ('type','section','slot')) for e in events)==set(result['artifact']['current']['marks'])
               for events in result['offered_histories'].values())
    for a,b in itertools.combinations(prepared['histories'],2):
        oracle=result['history_posterior_oracle']
        assert oracle[a]/oracle[b]==pytest.approx(math.exp(prepared['histories'][a]['log_mass']-prepared['histories'][b]['log_mass']))
        if result['history_classes'][a]['changed']==result['history_classes'][b]['changed']:
            after=result['history_posterior_after_oracle']
            assert after[a]*oracle[b]==pytest.approx(after[b]*oracle[a])
    for condition,outcome in result['outcomes'].items():
        assert outcome['target'] in result['artifact']['support']
        assert outcome['oracle_given_history']==result['history_future_oracles'][result['true_history']][condition]


def test_original_unseen_trajectory_and_target_cannot_change_new_history_or_future(actual):
    expected=construct(actual);bad=copy.deepcopy(actual)
    bad['target']='unseen changed';bad['source_worlds'][0]['trajectory']={'steps':[],'changes':[(0,'library_arrives')]}
    assert construct(bad)==expected
    dead=copy.deepcopy(actual);dead['source_worlds'][0]['state']['external_context']['tools']['source_access']=False
    assert inspect(dead)[0]['eligible'] is False
    with pytest.raises(ValueError):construct(dead)


def test_history_sampler_respects_nonuniform_probabilities_without_seed_search():
    draws=[_draw({'a':.1,'b':.9},i) for i in range(2000)]
    assert .07<draws.count('a')/len(draws)<.13
    assert _draw({'a':0.,'b':1.},20)=='b'
