"""Constructed-only CP1 checks; no model or real corpus access."""
import json
import math
import numpy as np
import pytest
from runners.drive.cards import week5_cp_statistics_v2 as s
from runners.drive.cards import week5_cp_analysis_v2 as a
from runners.drive.cards import week5_cp_math_fixture_v2 as f
from runners.drive.cards import week5_rf_cp_source_v1 as source


def test_orthogonal_observed_size_and_direct_shuffle_oracle():
    groups=f.worlds(n=24);bank=f.banks(groups);point=s.evaluate(np.sum(bank,axis=0))
    assert point['observed']['assertion_to_deference']==pytest.approx(1/math.sqrt(626),abs=1e-10)
    assert point['observed']['assertion_to_assertion']==pytest.approx(0,abs=1e-10)
    assert point['observed']['warmth_to_warmth']==pytest.approx(1,abs=1e-10)
    assert point['primary']==pytest.approx(f.direct_primary(groups),abs=2e-10)
    a.compare_metrics(point,s.evaluate_reference(np.sum(bank,axis=0)))


def test_full_2000_draw_plants_reversal_null_and_sensitivity():
    receipt=f.mathematical_receipt(full_draws=True)
    for world in receipt['worlds'].values():assert world['all_global_indices']==list(range(2000))
    null=receipt['worlds']['identical']['uncertainty']['primary']
    assert null['interval']==[0,0] and null['sees']==0 and null['supports_at']==.02
    positive=receipt['worlds']['complementary']['uncertainty']['primary']
    assert positive['sees']==pytest.approx(2.8*positive['se'])


def test_whole_conversation_seed_and_global_index_are_stable():
    counts=s.draw_counts(80,731)
    assert counts.sum()==80 and np.array_equal(counts,s.draw_counts(80,731))
    assert not np.array_equal(counts,s.draw_counts(80,732))
    groups=f.worlds(n=24);banks=f.banks(groups)
    value=s.evaluate(np.einsum('c,crk->rk',s.draw_counts(24,7),banks,optimize=False))
    assert value['primary']==pytest.approx(f.direct_primary(groups,7),abs=2e-10)


def test_missing_variance_is_unsupported_and_below_floor_is_descriptive():
    groups=f.worlds(n=3)
    for _,rows in groups:
        for row in rows:row['parent_assertion']=1
    point=s.evaluate(np.sum(f.banks(groups),axis=0))
    assert point['primary'] is None
    out=s.uncertainty(point,[],below_floor=True)
    assert out['primary']['status']=='below_floor_descriptive' and out['primary']['interval'] is None
    with pytest.raises(ValueError):s.evaluate(np.zeros((200,34)))


def test_shuffled_complete_bundle_recomputes_edit_gap_and_oracle():
    rows=s.pair_array(f.worlds(n=1)[0][1]);order=np.array([3,2,1,0]);m=s.moment(rows,order)
    expected=((rows[order,6]-rows[:,2])/1e6).sum()
    assert m.reshape(-1)[2]==pytest.approx(expected)
    with pytest.raises(ValueError):s.moment(rows,[0,0,2,3])
    bank=f.banks(f.worlds(n=24));a.compare_metrics(s.evaluate(bank.sum(axis=0)),s.evaluate_reference(bank.sum(axis=0)))


def test_actual_qualified_boundary_pause_resume_full_replay_and_provenance(tmp_path):
    inputs,cfg=f.prepare_boundary(tmp_path/'boundary');output=tmp_path/'analysis'
    paused=a.execute(output,inputs,dict(cfg,max_new_draw_blocks=1))
    assert paused['status']=='yielded' and not (output/'RESULT.json').exists()
    first=source.sha(output/'draw-0000.json')
    assert a.execute(output,inputs,cfg)['status']=='complete'
    assert source.sha(output/'draw-0000.json')==first
    assert a.verify(output,inputs,cfg)['verified'] is True
    assert a.execute(output,inputs,cfg)['status']=='complete'
    result=json.loads((output/'RESULT.json').read_text('utf8'))
    assert result['bootstrap_draws']==2000 and result['selected_conversations']==20
    with pytest.raises(ValueError):a.execute(tmp_path/'bad',inputs,dict(cfg,constructed_fixture=False))
    bad=dict(cfg,instrument_native_complete_sha256='0'*64)
    with pytest.raises(ValueError):a.execute(tmp_path/'wrong-proof',inputs,bad)
    path=output/'draw-0000.json';path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(ValueError):a.execute(output,inputs,cfg)


def test_pair_collection_roles_exclusions_and_sample_authority():
    def row(key,parent,speaker,conv='c',tokens=10,admin=False):
        return {'id':key,'reply_to':parent,'speaker':speaker,'conversation':conv,'is_admin':admin,
            'edit_count':100,'markers':{'tokens':tokens,'counts':{'warmth':1,'deference':2,'assertion':3}}}
    rows={'a':row('a',None,'one',admin=True),'b':row('b','a','two'),'c':row('c','a','one'),
        'd':row('d','a','three',tokens=9),'e':row('e','missing','four')}
    groups,support=a.pairs_from_rows(rows,'admin-10')
    assert support['counts']['eligible_pairs']==1 and support['counts']['missing_parent']==1
    assert support['pair_collection_gate'] is False
    assert groups[0][1][0]['parent_assertion']==30
    with pytest.raises(ValueError):a.binding({}, {'whole_conversation_sample':{'size':20}},groups,support)


def test_cooperative_yield_and_unsealed_bank_refusal(tmp_path):
    output=tmp_path/'out';output.mkdir();(output/'YIELD_REQUEST.json').write_text('{}')
    assert a.execute(output,{}, {})['status']=='yielded'
    path=tmp_path/'bank.npy'
    with path.open('wb') as stream:np.save(stream,np.zeros((1,201,34)))
    with pytest.raises((ValueError,FileNotFoundError)):a.load_bank(path,{})


def test_exact_constant_gap_is_unsupported_in_every_global_draw():
    groups=f.worlds(n=24)
    for _,rows in groups:
        for row in rows:row['parent_edit_count']=100;row['reply_edit_count']=10
    bank=f.banks(groups)
    for index in (None,0,1,731,1999):
        weights=np.ones(len(groups)) if index is None else s.draw_counts(len(groups),index)
        total=np.einsum('c,crk->rk',weights,bank,optimize=False)
        point=s.evaluate(total);reference=s.evaluate_reference(total)
        assert point['graded_edit_gap'] is None and reference['graded_edit_gap'] is None
        assert point['primary'] is not None
        a.compare_metrics(point,reference)
