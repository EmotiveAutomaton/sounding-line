import copy
import pytest
from runners.stage9.repair_case_jobs import public_keys,eligibility
from runners.stage9.repair_admission import disjoint
from runners.stage9.repair_analysis import row_for,control_answers
from runners.stage9.repair_jobs import VIEWS
from runners.stage9.local_repair import task_case
from tests.test_stage9_prospective_choice import case


def test_projected_source_renaming_cannot_create_an_independent_local_question():
    a=case();b=copy.deepcopy(a);b['unit']='new-source-name';b['target']='different-private-target'
    b['private_factors']['law']='private-label';assert public_keys(a)==public_keys(b)
    empty={v:set() for v in VIEWS};seen={v:{key} for v,key in public_keys(a).items()}
    assert eligibility(b,empty,seen)[1]=='repeated_public_local_task'
    assert eligibility(b,seen,empty)[1]=='exposed_public_local_task'
    assert eligibility(b,empty,empty)[0]


def test_future_truth_cannot_select_a_local_task_and_aliases_cluster_together():
    a=case();b=copy.deepcopy(a);cut=b['requested_boundary'];b['source_worlds'][0]['trajectory']['steps']=b['source_worlds'][0]['trajectory']['steps'][:cut]+[{'future':'CANARY'}]
    b['source_worlds'][0]['trajectory']['changes']=[(30,'private future')]
    assert public_keys(a)==public_keys(b)
    b=copy.deepcopy(a);b['unit']='renamed'
    prior={k:.25 for k in ('done','failed','illegal','stopped')};p,r=control_answers(task_case(a,'artifact'),'exact',prior)
    left,right=row_for(a,'artifact',p,r,prior),row_for(b,'artifact',p,r,prior)
    assert left['unit']==right['unit'] and left['attempt_id']!=right['attempt_id']


def test_repeated_current_questions_refuse_before_any_comparison():
    a=case();b=copy.deepcopy(a);b['unit']='different-whole-source'
    empty={v:[] for v in VIEWS}
    with pytest.raises(ValueError,match='within its own cohort'):disjoint([a,b],empty,empty)
