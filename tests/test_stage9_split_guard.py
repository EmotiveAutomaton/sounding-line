import pytest
from runners.stage9.split_guard import Separation,task_copies,disjoint_factors


def test_complete_evidence_copy_is_removed_without_using_labels():
    fit=[{'key':'copy','unit':'a','evidence':{'text':'one  example'},'label':'unread'},
         {'key':'different','unit':'b','evidence':{'text':'one example','before':'different'}}]
    test=[{'key':'target','unit':'z','evidence':{'text':'one example'},'label':'other'}]
    kept,removed=task_copies(fit,test)
    assert [r['key'] for r in kept]==['different']
    assert [r['key'] for r in removed]==['copy']


def test_both_writer_and_prompt_must_be_disjoint():
    fit=[{'writer':'a','prompt':'common'}]
    test=[{'writer':'b','prompt':'common'}]
    with pytest.raises(ValueError,match='factor'):disjoint_factors(fit,test,['writer','prompt'])
    assert disjoint_factors(fit,[{'writer':'b','prompt':'new'}],['writer','prompt'])['writer']['shared_groups']==0


def fixture():
    groups={g:{'split':lane,'previously_exposed':False} for g,lane in [('a','train'),('b','discovery'),('c','reserve'),('d','train'),('e','reserve')]}
    edges=[{'groups':[a,b],'witnesses':[{'roles':['artifact']},{'roles':['artifact']}]} for a,b in [('a','b'),('b','c')]]
    return Separation(groups,{'long_overlap_edges':edges})


def test_transitive_copy_exposure_blocks_reserve_and_filters_whole_fit_group():
    guard=fixture()
    kept,receipt=guard.filter_fit(['a','d'],['c'])
    assert kept==['d'] and receipt['excluded_groups']==['a']
    with pytest.raises(ValueError,match='exposed'):guard.require_reserve(['c'])
    assert guard.require_reserve(['e'])['groups']==1
    with pytest.raises(ValueError,match='unknown'):guard.filter_fit(['a'],['missing'])


def test_unexamined_discovery_alias_must_be_reconciled_before_reserve_use():
    groups={g:{'split':s,'previously_exposed':False} for g,s in [('a','reserve'),('b','discovery')]}
    guard=Separation(groups,{'long_overlap_edges':[]},[['a','b']])
    with pytest.raises(ValueError,match='unreconciled'):guard.require_reserve(['a'])

