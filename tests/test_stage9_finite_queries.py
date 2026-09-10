import copy
from runners.stage9.finite_world import case,from_world
from runners.stage9.finite_queries import (validate_projection,projection,execute_rules,
    projected_case,group_cases,evaluate_unit)
from runners.stage9.common import digest


def test_compact_rules_match_both_real_constructor_domains_exhaustively():
    for domain in ('essay','workshop_doc'):
        original=case(0,domain)
        assert digest(from_world(original['world']))==digest(original)
        checked=validate_projection(original)
        assert checked['all_bounded_sequences_match'] and checked['sequences_checked']==11204
        rules=projection(original,'distinction_left')
        assert execute_rules(rules,[]) and execute_rules(rules,['stop'])
        assert not execute_rules(rules,['stop','stop'])


def test_source_names_cannot_inflate_projected_identity_space():
    world=case(0,'essay')['world'];changed=copy.deepcopy(world)
    changed['lid']='another-source';changed['doc']['topic']='An irrelevant new topic'
    assert projected_case(world)[-1]==projected_case(changed)[-1]
    rows=[{'unit':'first','source_worlds':[world]},{'unit':'second','source_worlds':[changed]}]
    kept,groups=group_cases(rows)
    assert len(kept)==len(groups)==1
    assert next(iter(groups.values()))['source_units']==['first','second']


def test_actual_queries_retain_longer_distinction_and_equivalent_histories():
    world=case(1,'workshop_doc')['world'];seen=[]
    def call(evidence,task,index):
        assert set(evidence)=={'prefix','options'} and set(evidence['options'])=={'yes','no'}
        assert task=={'operation':'choice'}
        assert not any(key in evidence['prefix'] for key in ('private_history_by_state','persistent_tendency','source_lineage'))
        seen.append(index)
        return {'accepted':True,'prediction':{'probs':{'yes':.5,'no':.5}}}
    result=evaluate_unit(world,call)
    assert len(seen)==len(set(seen))==len(result['queries'])==48
    truths={row['query']['query']:row['query']['truth'] for row in result['queries']}
    # Same seven one-symbol answers; opposite answers at the longer separator.
    for i in range(7):assert truths['distinction_left-'+str(i)]==truths['distinction_right-'+str(i)]
    assert truths['distinction_left-7']!=truths['distinction_right-7']
    for i in range(12):assert truths['compression_left-'+str(i)]==truths['compression_right-'+str(i)]
    assert set(truths.values())=={'yes','no'}
