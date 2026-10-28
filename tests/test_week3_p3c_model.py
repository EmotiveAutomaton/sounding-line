import hashlib
import json
import sys
import types
import pytest
from runners.drive.cards import week3_p3c_model as m


def fixture(tmp_path):
    files={n:('test-'+n).encode() for n in m.FILES};rows=[]
    for n,b in files.items():
        row=dict(rfilename=n,size=len(b),blobId=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest())
        if n=='pytorch_model.bin':row['lfs']=dict(size=len(b),sha256=hashlib.sha256(b).hexdigest())
        rows.append(row)
    meta=dict(id=m.MODEL,sha=m.REVISION,private=False,gated=False,siblings=rows)
    inputs={}
    for k,v in dict(metadata=json.dumps(meta),official_license='Apache License Version 2.0',official_readme=m.MODEL,
        source_gate=json.dumps(dict(full_write_through=True)),agent_labels=json.dumps(dict(agent_made=True,predictions_seen=False))).items():
        p=tmp_path/(k+'.json');p.write_text(v,encoding='utf8');inputs[k]=str(p)
    return files,meta,inputs


def test_actual_handler_with_fake_transport_reentry_verify_mutation(tmp_path,monkeypatch):
    files,meta,inputs=fixture(tmp_path);calls=[]
    def download(**kw):
        calls.append(kw)
        assert kw['token'] is False and kw['revision']==m.REVISION and set(kw['allow_patterns'])==set(m.FILES)
        kw['local_dir'].mkdir(parents=True)
        for n,b in files.items():(kw['local_dir']/n).write_bytes(b)
    monkeypatch.setitem(sys.modules,'huggingface_hub',types.SimpleNamespace(snapshot_download=download))
    out=tmp_path/'out';m.execute(out,inputs,{'version':1});m.execute(out,inputs,{'version':1})
    assert len(calls)==1 and m.verify(out,inputs,{'version':1})['full_download_byte_inventory']
    p=out/'model/pytorch_model.bin';b=p.read_bytes();p.write_bytes(b'x'+b[1:])
    with pytest.raises(ValueError,match='LFS hash'):m.verify(out,inputs,{'version':1})


@pytest.mark.parametrize('bad',['gated','revision','missing','oversize'])
def test_metadata_refusals(tmp_path,bad):
    _,meta,_=fixture(tmp_path)
    if bad=='gated':meta['gated']='manual'
    elif bad=='revision':meta['sha']='unknown'
    elif bad=='missing':meta['siblings'].pop()
    else:meta['siblings'][0]['size']=3*1024**3
    with pytest.raises(ValueError):m.expected(meta)


def test_small_file_blob_refusal(tmp_path):
    files,meta,_=fixture(tmp_path)
    for n,b in files.items():(tmp_path/n).write_bytes(b)
    p=tmp_path/'config.json';b=p.read_bytes();p.write_bytes(b'x'+b[1:])
    with pytest.raises(ValueError,match='Git blob'):m.inventory(tmp_path,meta)
