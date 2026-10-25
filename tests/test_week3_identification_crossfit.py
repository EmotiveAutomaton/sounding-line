"""Approved independent-writer context: donor separation and all-probe accounting."""
import copy
import json

import numpy as np
import pytest

from runners.drive.cards import week3_identification_crossfit as card
from runners.drive.cards import week3_identification_inputs as source
from tests.test_week3_identification import rows
from tests.test_week3_identification_inputs import fixture


def prepared_fixture():
    args=list(fixture());original=copy.deepcopy(args)
    for offset in range(1,4):
        for index in (0,1,2,4):
            for r in copy.deepcopy(original[index]):
                keys=r['keys'] if index in (1,2) else r
                keys['writer']='copy'+str(offset)+'-'+keys['writer']
                keys['session']='copy'+str(offset)+'-'+keys['session']
                if index==4:r['pair']='copy'+str(offset)+'-'+r['pair']
                args[index].append(r)
    return source.prepare(*args)


def test_crossfit_repairs_omission_fingerprint_and_preserves_every_probe():
    rr=rows('identity',writers=12)
    result,detail=card.analyze_group(rr,card.CONSTRUCTED)
    x=result['x'];assert x['real']['accuracy']==1
    assert x['context']['accuracy']==pytest.approx(1/8)
    assert x['pass_both'] and x['permutation']['one_sided_p']<.05
    probes=[]
    for fold in detail['folds']:
        donors=set(fold['donor_writers']);gallery=set(fold['gallery_writers']['x'])
        assert not donors&gallery
        assert set(fold['probe_writers']['x'])<=gallery
        probes+=fold['probe_writers']['x']
    assert sorted(probes)==sorted({r['writer'] for r in rr})
    assert x['fold_gallery_sizes']==[8,8,8]


@pytest.mark.parametrize('kind',['null','prompt'])
def test_null_and_prompt_only_cannot_pass_corrected_control(kind):
    result,_=card.analyze_group(rows(kind,writers=12),card.CONSTRUCTED)
    assert not result['x']['pass_both']
    assert result['x']['real_minus_context']['effect']==0


def test_fold_assignment_invariant_to_source_order_and_pinned():
    rr=rows('identity',writers=13)
    a=card.writer_folds(rr)
    assert a==card.writer_folds(list(reversed(rr)))
    assert sorted(list(a.values()).count(i) for i in range(3))==[4,4,5]


def test_shared_null_assignments_preserve_roles_and_agree_across_rotations():
    rr=rows('identity',writers=12);folds=card.writer_folds(rr)
    a=card.role_assignment(rr,folds,7,20261026)
    assert a==card.role_assignment(list(reversed(rr)),folds,7,20261026)
    assert all(folds[r['writer']]==folds[a[r['session']]] for r in rr)
    _,detail=card.analyze_group(rr,dict(card.CONSTRUCTED,permutations=3),folds=folds)
    first,second=detail['folds'][:2]
    for index in range(3):
        x=dict(zip(first['detail']['sessions'],first['detail']['assignments'][index]))
        y=dict(zip(second['detail']['sessions'],second['detail']['assignments'][index]))
        assert all(x[s]==y[s] for s in x.keys()&y.keys())


def test_unshared_context_does_not_drop_any_writer_or_create_badge():
    rr=rows('identity',writers=12)
    for r in rr:r['prompt']=r['writer']+'-'+r['prompt']
    result,detail=card.analyze_group(rr,card.CONSTRUCTED)
    assert result['x']['state']=='unsupported' and result['x']['writers']==12
    assert detail['variants']['x']['writers']==sorted({r['writer'] for r in rr})


def test_donor_provider_refuses_any_gallery_writer_and_own_feature_changes_cannot_change_context():
    rr=rows('identity',writers=12);folds=card.writer_folds(rr)
    donors=[r for r in rr if folds[r['writer']]==0];targets=[r for r in rr if folds[r['writer']]!=0]
    x,slices=card.base.feature_matrix(targets);provide=card.independent_context(donors,slices)
    assert np.array_equal(provide(targets,x,{}),provide(targets,x+10000,{}))
    with pytest.raises(ValueError,match='overlaps'):provide(donors,x,{})


def test_fast_genre_null_scorer_matches_primary_real_scores():
    rr=rows('identity',writers=12);folds=card.writer_folds(rr)
    result,detail=card.analyze_group(rr,card.CONSTRUCTED,folds=folds)
    fast=card.real_scores(rr,{'x':sorted(folds)},folds)
    assert fast['x']['scores']==detail['variants']['x']['real']['scores']
    assert fast['x']['accuracy']==result['x']['real']['accuracy']


def test_h1_full_native_handler_contract_fresh_replay_and_corruption(tmp_path):
    path=tmp_path/'fixture.json';path.write_text(json.dumps(prepared_fixture()),encoding='utf8')
    inputs={'fixture':str(path)};out=tmp_path/'out'
    assert card.execute(out,inputs,card.CONSTRUCTED)['status']=='complete'
    assert card.verify(out,inputs,card.CONSTRUCTED)['verified']
    result=card.read(out/'SUMMARY.json')
    assert result['card']=='WA0.h1' and len(result['channels'])==11
    assert set(result['genre_sensitivity'])=={'style','rhythm'}
    path.write_text(path.read_text()+' ',encoding='utf8')
    with pytest.raises(ValueError,match='changed'):card.verify(out,inputs,card.CONSTRUCTED)
