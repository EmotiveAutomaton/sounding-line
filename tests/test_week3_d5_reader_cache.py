"""Exact reader algebra and actual completed producer boundaries."""
from copy import deepcopy
import gzip
from pathlib import Path

import numpy as np
import pytest

from runners.stage14.common import freeze,read
from runners.drive.cards import week3_d5_reader_cache as card


def fixture():
    rows=[];characters=[];process=[]
    for w in range(4):
        for p in range(4):
            meta=dict(session=f'w{w}p{p}',writer=f'w{w}',prompt=f'p{p}',timestamp=float(p),
                model_share=p/4,model_share_missing_reason=None)
            text=('alpha beta '+chr(97+w)+' ') * (8*(p+1))
            u=dict(**meta,end_at=float(p+1),codepoints_by_origin={'typed':len(text)},
                final_document=text,final_typed_groups=[{'text':text}])
            characters.append(card.chars.prepare(u));rows.append(meta)
            process.append(dict(selection=[.5,.25,.25,0.],rhythm=[float(w+1),None,float(p+1)]))
    return dict(constructed=True,rows=rows,characters=characters,process=process)


def dense_oracle(values):
    keys=sorted({(n,s) for v in values if v.get('supported',True) for n in ('2','3','4') for s in v['counts'][n]})
    rows=[]
    for v in values:
        if not v.get('supported',True) or min(v['opportunities'].values())==0:rows.append([0.]*len(keys))
        else:rows.append([v['counts'][n].get(s,0)/v['opportunities'][n]/np.sqrt(3) for n,s in keys])
    return np.asarray(rows)


def test_sparse_kernel_equals_independent_explicit_coordinate_oracle():
    values=[card.chars.counts([s]) for s in ['ab\u00e9! abcd','x\U0001f642xx!','ab\u00e9! abcd']]+[dict(supported=False)]
    k,valid,stats=card.kernel(values);x=dense_oracle(values)
    assert np.allclose(k,x@x.T,atol=1e-12,rtol=1e-12)
    assert valid.tolist()==[True,True,True,False] and stats['coordinates']==x.shape[1]
    kk,vv,_=card.kernel(list(reversed(values)))
    assert np.array_equal(kk,k[::-1,::-1]) and np.array_equal(vv,valid[::-1])


def test_profile_reader_dense_parity_identity_ties_and_reversal():
    rng=np.random.default_rng(13);x=rng.uniform(size=(12,9));a=rng.uniform(size=(4,12));b=rng.uniform(size=(4,12));truth=np.arange(4)
    aa=a@x;bb=b@x;sim=aa@bb.T/np.sqrt(np.sum(aa**2,1)[:,None]*np.sum(bb**2,1)[None,:]);ties=np.isclose(sim,sim.max(1)[:,None],atol=1e-12,rtol=1e-12)
    expected=ties[np.arange(4),truth]/ties.sum(1)
    assert np.array_equal(card.cosine_scores(x@x.T,np.ones(12,bool),a,b,truth),expected)
    eye=np.eye(4);valid=np.ones(4,bool)
    assert np.array_equal(card.cosine_scores(eye,valid,eye,eye,truth),np.ones(4))
    assert np.array_equal(card.cosine_scores(eye,valid,eye,eye,(truth+1)%4),np.zeros(4))
    assert np.array_equal(card.cosine_scores(np.ones((4,4)),valid,eye,eye,truth),np.full(4,.25))


def test_missing_invalid_and_zero_norm_are_refused():
    eye=np.eye(3);truth=np.arange(3)
    with pytest.raises(ValueError,match='Missing evidence'):card.cosine_scores(eye,[True,False,True],eye,eye,truth)
    with pytest.raises(ValueError,match='Zero-norm'):card.cosine_scores(np.zeros((3,3)),[True]*3,eye,eye,truth)
    with pytest.raises(ValueError,match='Invalid kernel'):card.cosine_scores(np.full((3,3),np.nan),[True]*3,eye,eye,truth)
    values=[card.chars.counts(['abcdef'])];values[0]['opportunities']['2']+=1
    with pytest.raises(ValueError,match='conserve'):card.kernel(values)


def test_full_constructed_handler_reentry_and_fresh_replay(tmp_path):
    path=tmp_path/'fixture.json';freeze(path,fixture());inputs=dict(fixture=str(path));out=tmp_path/'output'
    assert card.execute(out,inputs,card.CONSTRUCTED)['status']=='complete'
    names=[p for p in out.iterdir() if p.name!='PROGRESS.json'];before={p.name:p.read_bytes() for p in names}
    assert card.verify(out,inputs,card.CONSTRUCTED)['full_fresh_cache_replay']
    card.execute(out,inputs,card.CONSTRUCTED)
    assert before=={p.name:p.read_bytes() for p in names}
    summary=read(out/'SUMMARY.json');assert summary['sessions']==16 and not summary['effect_computed'] and not summary['scientific_admission']
    assert summary['channels']['human1024']['unsupported_sessions']==16


def test_changed_identity_and_saved_array_fail(tmp_path):
    f=fixture();f['characters'][0]['writer']='wrong';path=tmp_path/'bad-fixture.json';freeze(path,f)
    with pytest.raises(ValueError,match='identity'):card.execute(tmp_path/'bad',dict(fixture=str(path)),card.CONSTRUCTED)
    path=tmp_path/'fixture.json';freeze(path,fixture());out=tmp_path/'output';inputs=dict(fixture=str(path));card.execute(out,inputs,card.CONSTRUCTED)
    p=out/'final.npy.gz';p.write_bytes(gzip.compress(b'wrong array',mtime=0))
    with pytest.raises(ValueError,match='kernel replay'):card.verify(out,inputs,card.CONSTRUCTED)


def test_actual_producer_boundary_and_dense_oracle(tmp_path):
    repo=Path(__file__).resolve().parents[1];terminal=repo/'results/phase_2_4_stage_15/raw/drive-week3-20261025/D5-gallery-support/COMPLETE.json'
    rows,characters,process,pins=card.load(dict(support_complete=str(terminal)),card.CONFIG)
    assert len(rows)==len(characters)==len(process)==1399 and len(pins)>2800
    values=[card.representation(c,'human128') for c in characters[:4]]
    k,_,_=card.kernel(values);x=dense_oracle(values);assert np.allclose(k,x@x.T,atol=1e-12,rtol=1e-12)
    plan=read(terminal.parent/'PLAN.json');plan['module']='wrong'
    freeze(tmp_path/'PLAN.json',plan);freeze(tmp_path/'COMPLETE.json',read(terminal))
    with pytest.raises(ValueError,match='source bytes'):card.load(dict(support_complete=str(tmp_path/'COMPLETE.json')),card.CONFIG)
