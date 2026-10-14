import base64
import hashlib
import json
from pathlib import Path

import pytest
from runners.stage14 import public_sources as s


def github_blob(data):
    return dict(encoding='base64',content=base64.b64encode(data).decode(),
                sha=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest())


def revision(n,parent,text,date):
    return dict(revid=n,parentid=parent,timestamp=date,user='fixture',userid=1,
                sha1=hashlib.sha1(text.encode()).hexdigest(),
                slots=dict(main=dict(contentmodel='wikitext',content=text)))


def test_exact_byte_identity_and_corruption():
    data='naïve\r\n界'.encode()
    assert s.blob(github_blob(data))==data
    obj=github_blob(data);obj['sha']='0'*40
    with pytest.raises(s.SourceRefusal,match='identity'):s.blob(obj)
    obj=revision(2,1,data.decode(),'2026-09-02T00:00:00Z')
    assert s.revision(obj)==data
    obj['slots']['main']['content']+='changed'
    with pytest.raises(s.SourceRefusal,match='SHA1'):s.revision(obj)


def test_hidden_text_never_accepted():
    obj=revision(2,1,'fixture','2026-09-02T00:00:00Z');obj['texthidden']=True
    with pytest.raises(s.SourceRefusal,match='hidden'):s.revision(obj)


def test_real_wiki_handler_preserves_pair_but_refuses_science(tmp_path,monkeypatch):
    parent=revision(1,0,'before','2026-09-01T00:00:00Z')
    child=revision(2,1,'after','2026-09-02T00:00:00Z')
    replies=[{'query':{'rightsinfo':{'url':'https://creativecommons.org/licenses/by-sa/4.0/'}}},
             {'query':{'pages':[{'ns':0,'revisions':[child]}]}},
             {'query':{'users':[{'name':'fixture','groups':[]}]}},
             {'query':{'pages':[{'revisions':[parent,child]}]}}]
    class Fake:
        def __init__(self,*a):self.calls=0
        def get(self,*a):self.calls+=1;return replies.pop(0)
    monkeypatch.setattr(s,'Client',Fake)
    s.run(dict(policy_authorized=True,source='wikipedia',titles=['Fixture'],since='start',until='end',pairs_per_page=8),tmp_path,tmp_path,lambda _:None)
    assert (tmp_path/'texts/2/parent.txt').read_bytes()==b'before'
    assert json.loads((tmp_path/'SUMMARY.json').read_text())['pairs']==1
    assert json.loads((tmp_path/'ADMISSION.json').read_text())['admitted'] is False
    record=json.loads((tmp_path/'SOURCE_RECORDS.json').read_text())['pairs'][0]
    assert record['fresh_confirmation'] is False and record['revert_status'].startswith('unassessed')


def test_code_license_label_is_not_prose_grant(tmp_path):
    replies=[dict(private=False,fork=False,archived=False),[dict(sha='a'*40)],
             github_blob(b'Template licensed MIT; articles reserved'),
             github_blob(b'CC fixture')|dict(license=dict(spdx_id='CC-BY-4.0'))]
    class Fake:
        def get(self,*a):return replies.pop(0)
    result=s.github_run(dict(repositories=['fixture/blog'],until='2026-10-02',reviewed_grants={}),tmp_path,Fake())
    assert not result['pairs']
    assert 'prose rights' in result['exclusions'][0]['reason']
    assert not replies


def test_budget_refuses_before_network(tmp_path):
    client=s.Client(tmp_path,dict(request_limit=0,intake_seconds=100),lambda _:None)
    with pytest.raises(s.SourceRefusal,match='budget'):client.get('wiki',{})
