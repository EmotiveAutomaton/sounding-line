import copy
import random

import pytest

from runners.stage9.common import digest
from runners.stage9.series_cases import (COHORTS, construct_attempt, dose_view,
    prepare_case, recorded_target, requested_boundary)


def test_prospective_cut_does_not_select_the_terminal_outcome():
    # Independent geometric stopping process: P(stop at every reached boundary)=.2.
    # A last-available-action cut would instead manufacture stop truth in every case.
    stops = reached = unreached = 0
    for i in range(6000):
        rng = random.Random(100000+i)
        steps = []
        for j in range(40):
            if rng.random() < .2:
                break
            steps.append({'type':'write','section':'s','slot':str(j)})
        trajectory = {'steps':steps,'stop_kind':'hazard' if len(steps)<40 else 'max_steps'}
        target, reason = recorded_target(trajectory,requested_boundary('independent-'+str(i)))
        if reason:
            unreached += 1
        else:
            reached += 1
            stops += target == 'stop'
    assert reached > 3500 and unreached > 500
    assert abs(stops/reached-.2) < .025
    assert recorded_target({'steps':[],'stop_kind':'max_steps'},0)[1] == 'right_censored_without_target'
    assert recorded_target({'steps':[],'stop_kind':'hazard'},1)[1] == 'terminated_before_requested_boundary'
    assert recorded_target({'steps':[],'stop_kind':'hazard'},40)[1] == 'outside_declared_query_window'


@pytest.fixture(scope='module')
def actual():
    rows = [construct_attempt(key='fixture-series-'+str(i),cohort=COHORTS[i],role='pilot',dose=3)
            for i in range(4)]
    return next(r for r in rows if r['realized'] and len(r['source_worlds'][0]['trajectory']['steps'])>r['requested_boundary']+2)


def test_real_series_preserves_factors_and_projects_only_observed_prefix(actual):
    worlds = actual['source_worlds']
    cut = actual['requested_boundary']
    changed = copy.deepcopy(worlds[0])
    changed['trajectory']['steps'] = changed['trajectory']['steps'][:cut+1]
    changed['trajectory']['stop_kind'] = 'max_steps'
    again = prepare_case(changed,worlds[1:],cut,'pilot')
    assert again['views'] == actual['views']
    assert again['target'] == actual['target']
    assert again['oracle'] == actual['oracle']
    assert actual['views']['process_record']['current']['observed_stop'] is None
    assert len(actual['views']['process_record']['current']['events']) == cut
    assert 'private_factors' not in actual['views']['artifact']
    assert digest(actual['views']['artifact']['current']) not in {
        digest(w) for w in actual['views']['artifact']['earlier']}


def test_doses_preserve_query_and_duplicate_control_is_explicit(actual):
    zero = dose_view(actual,0)
    three = dose_view(actual,3)
    repeated = dose_view(actual,3,repeat=True)
    assert not zero['earlier']
    assert len({digest(w) for w in three['earlier']}) == 3
    assert len({digest(w) for w in repeated['earlier']}) == 1
    assert zero['current'] == three['current'] == repeated['current']
    assert zero['support'] == three['support'] == repeated['support']
    with pytest.raises(ValueError,match='unavailable'):
        dose_view(actual,7)


def test_partition_wrong_maker_and_exact_copy_refuse(actual):
    current,*earlier = actual['source_worlds']
    with pytest.raises(ValueError,match='partition'):
        prepare_case(current,earlier,actual['requested_boundary'],'discovery')
    with pytest.raises(ValueError,match='duplicate world'):
        prepare_case(current,[current],actual['requested_boundary'],'pilot')
    changed = copy.deepcopy(earlier)
    changed[0]['state']['names']['law'] = 'editor2' if current['state']['names']['law'] != 'editor2' else 'novice'
    with pytest.raises(ValueError):
        prepare_case(current,changed,actual['requested_boundary'],'pilot')
def test_scientific_preparation_requires_an_actual_queue_identity(tmp_path,monkeypatch):
    from runners.stage9.series_jobs import prepare
    import pytest
    monkeypatch.delenv('S9_CELL_IDENTITY',raising=False)
    with pytest.raises(ValueError,match='queue cell identity'):
        prepare(tmp_path/'unstarted',role='discovery',key='guard')
    assert not (tmp_path/'unstarted').exists()
