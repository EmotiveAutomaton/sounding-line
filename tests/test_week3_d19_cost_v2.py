"""D19 source, numerical, full-handler and immutable replay checks."""
from pathlib import Path
import copy
import numpy as np
import pytest
from runners.drive.cards import week3_d19_cost_v2 as d
from runners.stage14.common import read,freeze,filehash


def rows():
    out=[]
    for i in range(60):
        a=np.zeros(384);a[i%15]=1
        out.append(dict(writer=str(i%15),session=str(i),handling=dict(accept=2,dismiss=1),revision=dict(content=1,housekeeping=2),typed_words=100,final_words=100,requests=3,edited_accepted_characters=1,accepted_characters=20,within_intervals=[.1,.2],onset_intervals=[1,2],tc_timing_mode='valid',accepted_options=2,declined_options=1,accepted_vector_sum=(2*a).tolist(),declined_vector_sum=(-a).tolist()))
    return out


def known():
    x=np.tile(np.eye(3),(10,1));w,h,r=d.fit(x,3)
    assert r['relative_error']<1e-10
    return r


def test_known_and_rejection():
    known()
    for a in (np.array([[-1.]]),np.array([[np.nan]])):
        with pytest.raises(ValueError):d.fit(a,1)


def test_missing_signed_and_normalization():
    r=rows();r[0]['accepted_options']=0;r[0]['accepted_vector_sum']=[0.]*384;r[0]['within_intervals']=[]
    x,meta=d.matrix(r)
    assert meta['rows']==60 and meta['missing_cells']==2 and meta['block_widths']==[26,1536]
    assert np.all(x>=0) and np.isfinite(x).all()
    assert x[0,24]>0 and x[0,26:26+768].sum()==0 # missing flag is present; accepted vector is absent
    assert x[0,26+768:26+1152].sum()==0 # negative declined vector has no positive mass
    bad=copy.deepcopy(r);bad[0]['accepted_vector_sum'][0]=1
    with pytest.raises(ValueError):d.matrix(bad)


def test_whole_writer_sampling():
    r=rows();ids=d.bootstrap(r,17);assert len(ids)==60
    counts={w:sum(r[i]['writer']==w for i in ids) for w in {a['writer'] for a in r}}
    assert all(n%4==0 for n in counts.values()) and ids.tolist()==d.bootstrap(r,17).tolist()


def execute(output,inputs,config):
    result=d.run(output,inputs,config,loader=lambda _:rows());freeze(Path(output)/'KNOWN.json',known());return result


def verify(output,inputs,config):
    if read(Path(output)/'KNOWN.json')!=known():raise ValueError('Known-answer replay differs')
    return d.run(output,inputs,config,True,loader=lambda _:rows())


def test_complete_handler(tmp_path):
    execute(tmp_path,{},d.CONFIG);saved=filehash(tmp_path/'05-real.npz')
    assert verify(tmp_path,{},d.CONFIG)['full_fresh_fit_replay']
    assert filehash(tmp_path/'05-real.npz')==saved
    (tmp_path/'05-real.json').write_text('{}')
    with pytest.raises(ValueError):verify(tmp_path,{},d.CONFIG)


def test_config_and_yield(tmp_path):
    with pytest.raises(ValueError):execute(tmp_path,{},dict(d.CONFIG,ranks=[5]))
    (tmp_path/'YIELD_REQUEST.json').write_text('{}')
    with pytest.raises(InterruptedError):execute(tmp_path,{},d.CONFIG)
