import copy

import pytest

from runners.stage9.erased_inference import infer
from runners.stage9.artifact_view import support
from runners.stage9.likelihood_table import Table, approximation_comparison
from runners.stage9.program_inference import Budget
from tests.test_stage9_erased_inference import A,B,evidence,marked,program,recorded


def query_view(current,earlier,view):
    return {'version':'s9-visible-artifact-v1','view':view,'current':current,
            'earlier':earlier,'support':support(current,view)}


@pytest.mark.parametrize('view',['artifact','process_record'])
def test_reused_doses_and_hierarchy_match_fresh_inference(view):
    candidates = {k:program(p) for k,p in [('a1',.9),('a2',.1),('b1',.6),('b2',.4)]}
    prior = {k:.25 for k in candidates}
    groups = {k:k[0] for k in candidates}
    current = marked([], 'now') if view=='artifact' else recorded([])
    past = [marked([A],'one'),marked([B],'two'),marked([A,B],'three')]
    if view=='process_record':
        past = [recorded([A]),recorded([B]),recorded([A,B])]
    table = Table(candidates,Budget(10000),exact_limit=0,permutations=16,seed=99)
    fresh_cost = 0
    for n in (0,1,3):
        query = query_view(current,past[:n],view)
        for hierarchy in (None,groups):
            budget = Budget(10000)
            expected = infer(query,candidates,prior,budget,exact_limit=0,permutations=16,seed=99,shared_groups=hierarchy)
            actual = table.forecast(query,prior,shared_groups=hierarchy)
            for key in ('prediction','weights'):
                assert actual[key] == pytest.approx(expected[key],abs=1e-13)
            assert actual['likelihood_receipts'] == expected['likelihood_receipts']
            fresh_cost += budget.used
    assert table.budget.used < fresh_cost/2
    used = table.budget.used
    copy_query = query_view(current,past*2,view)
    repeated = table.forecast(copy_query,prior,shared_groups=groups)
    assert repeated['duplicate_earlier_works_removed']==3
    assert table.budget.used == used


def test_cache_separates_evidence_view_and_copies_candidate_parameters():
    p = {'a':program(.75),'b':program(.25)}
    table = Table(p,Budget(1000))
    query = evidence(marked([],'now'),[marked([A,B],'then')])
    before = table.forecast(query,{'a':.5,'b':.5})
    p['a']['purpose']['write'] = 30
    assert table.forecast(query,{'a':.5,'b':.5})['prediction'] == before['prediction']
    record_query = query_view(recorded([]),[recorded([A,B])],'process_record')
    after = table.forecast(record_query,{'a':.5,'b':.5})
    assert after['new_evaluations'] > 0
    assert after['likelihood_receipts']['a'][0]['algorithm'] == 'recorded event likelihood'


def test_current_purpose_does_not_assert_earlier_purpose():
    candidates = {k:program(p) for k,p in [('a1',.9),('a2',.1),('b1',.6),('b2',.4)]}
    groups = {k:k[0] for k in candidates}
    query = evidence(marked([],'future'),[marked([A],'past one'),marked([B],'past two')])
    result = Table(candidates,Budget(1000)).forecast(query,{k:.25 for k in candidates},shared_groups=groups,
        current_purpose_weights={'a1':1.,'a2':0.,'b1':1.,'b2':0.})
    assert result['persistent_weights'] == pytest.approx({'a':.5,'b':.5})
    assert result['weights'] == pytest.approx({'a1':.5,'a2':0.,'b1':.5,'b2':0.})
    assert result['prediction'][A] == pytest.approx(.75*(.9+.6)/2)


def test_approximation_envelope_can_reject_and_support_omission_refuses():
    first = {'prediction':{'a':.5,'b':.5}}
    assert approximation_comparison(first,first)['accepted']
    assert not approximation_comparison(first,{'prediction':{'a':.51,'b':.49}})['accepted']
    with pytest.raises(ValueError,match='distribution'):
        approximation_comparison(first,{'prediction':{'a':1.}})
