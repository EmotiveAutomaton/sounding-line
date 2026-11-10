import json
from runners.drive.cards import week5_go_history as h
from runners.drive.cards import week5_go_history_bounded as bounded


def test_bounded_history_whole_replay_and_first_version(tmp_path,monkeypatch):
    salt=tmp_path/'salt';salt.write_bytes(b'x'*32)
    rows=[{'document':str(i),'repository':'eips','relative_path':f'EIPS/eip-{i}.md'} for i in range(2)]
    documents=tmp_path/'documents.json';h.core.write(documents,{'documents':rows})
    def git(repo,*args):
        if args[0]=='rev-parse':return h.core.PINS['eips']
        if args[0]=='log':return '\n'.join(f'COMMIT c{i} {i}' for i in reversed(range(9)))
        if args[0]=='diff-tree':return 'EIPS/eip-1.md'
        if args[0]=='show':
            i=int(args[1].split(':')[0][1:]);goal='forests and habitats' if i<4 else 'payment latency and transfers'
            return '---\nauthor: Constructed\ntype: Standards Track\n---\n## Motivation\n'+goal+'\n## Specification\n'+('old text ' if i<4 else 'new text ')*max(1,i+1)
        raise AssertionError(args)
    monkeypatch.setattr(h.core,'git',git)
    inputs={'documents':str(documents),'salt':str(salt),'eips':str(tmp_path/'history')}
    assert bounded.execute(tmp_path/'output',inputs,{'phase':'prepare','max_new_documents':1})['status']=='yielded'
    full=bounded.execute(tmp_path/'output',inputs,{'phase':'prepare'})
    assert full['first_draft_documents']==2 and full['three_each_anchors']==2
    assert bounded.verify(tmp_path/'output',inputs,{'phase':'prepare'})['verified']
    first=json.loads((tmp_path/'output/first-drafts.json').read_text())['documents']
    assert all(row['motivation']=='forests and habitats' for row in first)
    part=tmp_path/'output/document-parts/000000/anchors.json';part.write_text('{}')
    import pytest
    with pytest.raises(ValueError,match='checkpoint changed'):bounded.execute(tmp_path/'output',inputs,{'phase':'prepare'})
