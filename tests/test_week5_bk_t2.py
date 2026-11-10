from pathlib import Path
import copy
import numpy as np
from runners.drive.cards import week5_bk_t2_source as source,week5_bk_t2_features as features,week5_bk_t2_analysis as analysis
from runners.drive.cards.week5_bk_t2_fixture import source_fixture,world


def test_lineage_initial_typed_mixed_deleted_and_accepted():
    rows,census=source.materialize(**source_fixture())
    mixed=[r for r in rows if r['origin']=='mixed'];accepted=[r for r in rows if r['origin']=='accepted'];typed=[r for r in rows if r['origin']=='typed']
    assert len(mixed)==1 and mixed[0]['labels']=={'a':0,'b':1,'c':None}
    assert len(accepted)==1 and accepted[0]['labels']=={'a':None,'b':None,'c':1}
    assert len(typed)==2 and all(r['labels']['c']==0 for r in typed)
    assert census['initial_units_without_final_feature']==1


def test_merged_split_and_both_replacement_orders():
    rows,c=source.materialize(**source_fixture(merge=True));assert c['ancestor_count_2']==1
    assert all(r['labels']['a'] is None and r['labels']['b'] is None for r in rows if r['ancestry']=='multiple')
    rows,c=source.materialize(**source_fixture(split=True));assert c['initial_units_split_across_final_sentences']==1
    for order in ('delete-first','insert-first'):
        rows,c=source.materialize(**source_fixture(order));assert rows[0]['ancestry']=='unique' and rows[0]['labels']['b']==1


def test_provenance_and_ancestor_corruption_refused():
    data=source_fixture();data['first_units'][0]['text']='wrong'
    import pytest
    with pytest.raises(ValueError,match='ancestry'):source.materialize(**data)
    data=source_fixture();data['timeline']['final_spans'][0]['origin']='prompt'
    with pytest.raises(ValueError,match='typed provenance'):source.materialize(**data)


def test_full_document_acceptance_and_valid_class_without_nuisances():
    data=source_fixture(full_append=True);data['first_units'][0]['timing_state']='missing_population_frequency'
    rows,census=source.materialize(**data)
    assert rows[0]['labels']['a']==0
    accepted=[r for r in rows if r['origin']=='accepted']
    assert len(accepted)==1 and accepted[0]['ancestor_indices']==[] and accepted[0]['labels']=={'a':None,'b':None,'c':1}
    for span in data['timeline']['final_spans']:
        if span['origin']=='accepted':span['origin']='accepted_edited'
    rows,_=source.materialize(**data);assert [r['labels']['c'] for r in rows if r['origin']=='accepted']==[1]


def test_final_features_ignore_process_metadata_and_keep_content_placeholder():
    row={'text':'The bright bird sings.','position':.5,'labels':{'a':0},'revision':False}
    a=features.lexical(row['text'],row['position'],{'the'});row.update(labels={'a':1},revision=True,writer='different',hesitancy=.9)
    assert a==features.lexical(row['text'],row['position'],{'the'})
    assert a[0]==[22.,4.,.5] and sum(a[1][15:])==3.


def test_auc_exact_ties_weights_and_single_class():
    assert analysis.auc([0,1],[0,1])==1
    assert analysis.auc([0,1],[1,0])==0
    assert analysis.auc([0,1],[1,1])==.5
    assert analysis.auc([0,0],[0,1]) is None
    assert analysis.auc([0,1,0],[0,1,.5],[2,1,3])==1


def test_writer_folds_and_three_known_worlds():
    rows=world('signal');writers=[r['writer'] for r in rows];folds=analysis.folds(writers)
    assert len(set(folds))==5 and all(len(set(folds[np.array(writers)==w]))==1 for w in set(writers))
    for name,expected in [('signal',.5),('null',0.),('baseline_only',0.)]:
        point,_=analysis.point(world(name),'a','primary');assert abs(point['gain']-expected)<1e-12 and point['scope']=='held-out writers'


def test_pooled_oneclass_and_interleaved_real_cost_prefix():
    p,_=analysis.point(world('signal')[:16],'a','primary');assert p['scope']=='below floor, descriptive'
    rows=world('signal')
    for row in rows:row['labels']['a']=0
    p,_=analysis.point(rows,'a','primary');assert p['auc'] is None and p['reason']=='one-class/empty target'
    tasks=analysis.work_units(2000,200);assert len(tasks)==2200 and sum(k=='permutation' for k,i in tasks[:110])==10
