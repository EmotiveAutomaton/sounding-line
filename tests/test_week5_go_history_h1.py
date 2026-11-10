import json,subprocess
from pathlib import Path
import pytest
from runners.drive.cards import week5_go_history_h1 as h
from runners.drive.cards import week5_go_history_bounded_h1 as bounded


def test_copy_creation_and_deletion_break_complete_projection(tmp_path,monkeypatch):
    salt=tmp_path/'salt';salt.write_bytes(b'a'*32);docs=tmp_path/'documents.json'
    h.core.write(docs,{'documents':[{'document':'fixture','repository':'eips','relative_path':'EIPS/eip-2.md'}]})
    raw='\n'.join(['COMMIT c5 5','M\tEIPS/eip-2.md','COMMIT c4 4','A\tEIPS/eip-2.md',
                   'COMMIT c3 3','D\tEIPS/eip-2.md','COMMIT c2 2','C053\tEIPS/eip-1.md\tEIPS/eip-2.md',
                   'COMMIT c1 1','A\tEIPS/eip-1.md'])
    calls=[]
    def git(repo,*args):
        if args[0]=='rev-parse':return h.core.PINS['eips']
        if args[0]=='log':return raw
        if args[0]=='diff-tree':return 'EIPS/eip-2.md'
        if args[0]=='show':
            calls.append(args[1]);assert args[1].split(':')[0] not in ('c1','c3')
            return '---\nauthor: Constructed\ntype: Standards Track\n---\n## Motivation\ncopy target goal\n## Specification\nconstructed body '+args[1].split(':')[0]
        raise AssertionError(args)
    monkeypatch.setattr(h.core,'git',git)
    inputs={'documents':str(docs),'salt':str(salt),'eips':str(tmp_path/'repo')};out=tmp_path/'run'
    result=bounded.execute(out,inputs,{'phase':'prepare'})
    assert result['counts']['copy_creation_boundaries']==1
    assert result['counts']['copy_origin_revisions_excluded']==1
    assert result['counts']['deletion_boundaries']==1
    assert result['first_draft_documents']==1
    assert bounded.verify(out,inputs,{'phase':'prepare'})['verified']
    part=out/'document-parts/000000/anchors.json';part.write_text('{}')
    with pytest.raises(ValueError,match='checkpoint changed'):bounded.execute(out,inputs,{'phase':'prepare'})


def test_actual_git_copy_history_boundary(tmp_path,monkeypatch):
    repo=tmp_path/'repo';repo.mkdir()
    def git(*args):
        p=subprocess.run(['git','-C',str(repo),*args],capture_output=True,text=True)
        assert p.returncode==0,p.stderr
        return p.stdout
    git('init','-q');git('config','user.name','Constructed Fixture');git('config','user.email','fixture@example.invalid')
    old=repo/'eip-1.md';old.write_bytes(('original proposal\n'*100).encode())
    git('add','eip-1.md');git('commit','-qm','constructed origin')
    new=repo/'eip-2.md';new.write_bytes(old.read_bytes());old.write_bytes(old.read_bytes()+b'original changed\n')
    git('add','eip-1.md','eip-2.md');git('commit','-qm','constructed copy')
    raw=git('log','--follow','--format=COMMIT %H %ct','--name-status','HEAD','--','eip-2.md')
    assert 'C100\teip-1.md\teip-2.md' in raw
    adapter=h.SourceCore();filtered=adapter.git(repo,'log','--follow','--format=COMMIT %H %ct','--name-status','HEAD','--','eip-2.md')
    assert filtered.count('COMMIT ')==1 and adapter.counts['copy_origin_revisions_excluded']==1
    assert adapter.git(repo,'show',git('rev-parse','HEAD').strip()+':eip-2.md')==new.read_text()


def test_missing_nondeleted_object_still_refuses(tmp_path):
    adapter=h.SourceCore()
    with pytest.raises(ValueError,match='unavailable'):adapter.git(tmp_path,'show','invalid:path')


def test_renamed_path_is_followed_to_copy_boundary(tmp_path,monkeypatch):
    raw='COMMIT new 3\nR100\told.md\tnew.md\nCOMMIT copy 2\nC053\torigin.md\told.md\nCOMMIT first 1\nA\torigin.md\n'
    monkeypatch.setattr(h.core,'git',lambda *args:raw)
    adapter=h.SourceCore();result=adapter.git(tmp_path,'log','--follow','--','new.md')
    assert 'COMMIT new' in result and 'COMMIT copy' in result and 'COMMIT first' not in result
    assert adapter.counts['copy_creation_boundaries']==1
