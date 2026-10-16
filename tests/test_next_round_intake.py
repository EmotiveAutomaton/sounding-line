import pytest
from runners.next_round import intake

class Response:
    def __init__(self,data,length):self.data=data;self.headers={'Content-Length':str(length)}
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def raise_for_status(self):pass
    def iter_content(self,n):yield self.data
class Session:
    def __init__(self,response):self.response=response
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def get(self,*args,**kwargs):return self.response

@pytest.mark.parametrize('payload,declared,limit,valid',[(b'ab',2,3,True),(b'ab',4,3,False),(b'abcd',0,3,False),(b'ab',3,4,False)])
def test_bounded_complete_download(tmp_path,monkeypatch,payload,declared,limit,valid):
    monkeypatch.setattr(intake.requests,'Session',lambda:Session(Response(payload,declared)))
    monkeypatch.setattr(intake,'ROOT',tmp_path)
    monkeypatch.setattr(intake,'resource_snapshot',lambda:dict(ram_available_GiB=10,commit_headroom_GiB=10,disk_free_GiB=30))
    path=tmp_path/'source.csv'
    if valid:
        result=intake.fetch('https://example.invalid/source',path,limit,'test')
        assert result['bytes']==len(payload) and path.read_bytes()==payload
    else:
        with pytest.raises(ValueError):intake.fetch('https://example.invalid/source',path,limit,'test')
