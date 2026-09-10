import copy,math
import pytest
from runners.stage9.local_repair import task_case,consequence
from runners.stage9.repair_analysis import row_for,control_answers,battery_identity,calibrate
from runners.stage9.repair_admission import disjoint
from runners.stage9.repair_jobs import records
from tests.test_stage9_prospective_choice import case


def test_exact_and_fluent_controls_use_real_execution_and_proper_scores():
    source=case();task=task_case(source,'artifact');prior={k:.25 for k in ('done','failed','illegal','stopped')}
    prospective,repair=control_answers(task,'exact',prior)
    exact=row_for(source,'artifact',prospective,repair,prior)
    assert exact['valid'] and exact['legal'] and exact['fixable'] and exact['goal_improving'] and not exact['collateral_damage']
    assert exact['consequence_difference']==pytest.approx(math.log(4))
    for kind in ('blind','story'):
        p,r=control_answers(task,kind,prior);row=row_for(source,'artifact',p,r,prior)
        assert row['valid'] and not row['goal_improving'] and row['consequence_difference']==0
    p,r=control_answers(task,'story',prior)
    assert not row_for(source,'artifact',p,r,prior)['legal']


def test_actual_zero_is_preserved_and_missing_label_cannot_score():
    source=case();task=task_case(source,'artifact');prior={k:.25 for k in ('done','failed','illegal','stopped')}
    p,r=control_answers(task,'exact',prior);truth=consequence(task)
    p['prediction']['probs']={k:0. if k==truth else 1/3 for k in prior}
    assert row_for(source,'artifact',p,r,prior)['consequence_difference']==-math.inf
    del p['prediction']['probs'][truth]
    with pytest.raises(ValueError,match='support'):row_for(source,'artifact',p,r,prior)


def test_battery_scope_and_insufficient_calibration_cannot_admit():
    a=battery_identity('artifact','essay','source-a')
    assert len({a,battery_identity('artifact','workshop_doc','source-a'),battery_identity('process_record','essay','source-a'),battery_identity('artifact','essay','source-b')})==4
    with pytest.raises(ValueError,match='complete independent'):calibrate([case()],{}, {})


def test_actual_evaluation_refuses_selection_sources_and_public_task_aliases():
    source=case();exposed=records([source]);empty={k:[] for k in exposed}
    with pytest.raises(ValueError,match='source'):disjoint([source],empty,exposed)
    copied=copy.deepcopy(exposed)
    for rows in copied.values():
        for row in rows:row['unit']='changed-path'
    with pytest.raises(ValueError,match='public task'):disjoint([source],empty,copied)
