import json
import numpy as np
import pytest
from runners.drive.cards import week5_go1_pipeline as g


def test_rationale_removed_structurally_and_99_never_falls_back(tmp_path,monkeypatch):
    text='---\nauthor: Example\ntype: Standards Track\n---\n## Motivation\ngoal\n## Rationale\nSECRET\n### Detail\nNESTED\n## Specification\nvisible'
    row,_=g.core.parse_document(text,'eips',b'x'*32)
    rows=[{**row,'document':str(i),'relative_path':f'EIPS/eip-{i}.md','head':g.core.PINS['eips'],'type':'A' if i<50 else 'B'} for i in range(110)]
    file=tmp_path/'documents.json';g.core.write(file,{'documents':rows})
    monkeypatch.setattr(g.core,'git',lambda *args:text)
    prepared,roster=g.prepared_rows({'documents':str(file),'eips':str(tmp_path)}, {'field':'rationale'})
    assert roster and all('SECRET' not in r['rest'] and 'NESTED' not in r['rest'] and 'goal' in r['rest'] for r in prepared)
    assert not g.prepared_rows({'documents':str(file)}, {'distractors':99,'strict_stratum':True})[1]


def test_vector_seal_pause_resume_and_tamper(tmp_path,monkeypatch):
    manifest=tmp_path/'manifest';manifest.write_text('constructed')
    def embeddings(texts,path,cache,on_vector):
        cache=dict(cache)
        for i,text in enumerate(texts):
            if text not in cache:
                v=np.zeros(384,np.float32);v[i]=1;cache[text]=v;on_vector(text,v)
        return np.asarray([cache[t] for t in texts])
    monkeypatch.setattr(g.readers,'embeddings',embeddings)
    with pytest.raises(g.Paused):g.vector_bank(['a','b'],manifest,tmp_path/'bank',{'max_new_texts':1})
    vectors=g.vector_bank(['a','b'],manifest,tmp_path/'bank',{})
    assert vectors.shape==(2,384)
    path=next(p for p in (tmp_path/'bank').glob('*.json') if not p.name.endswith('seal.json') and p.name!='PROGRESS.json')
    data=json.loads(path.read_text());data['vector'][0]=.5;g.core.write(path,data)
    with pytest.raises(ValueError,match='seal changed'):g.vector_bank(['a','b'],manifest,tmp_path/'bank',{})


def test_all_declared_grid_source_and_score_consumers(tmp_path,monkeypatch):
    rows=[]
    for repository in ['peps','eips']:
        for i in range(110):
            rows.append({'repository':repository,'type':'Standards Track','category':'Core','author':str(i),
                         'document':repository+str(i),'relative_path':f'{i}.md','head':g.core.PINS[repository],
                         'motivation':f'goal token{i}','rest':f'goal token{i}','specification':f'goal token{i}','rationale':f'reason token{i}'})
    docs=tmp_path/'documents.json';first=tmp_path/'first.json';g.core.write(docs,{'documents':rows});g.core.write(first,{'documents':rows})
    def raw(repo,*args):
        index=args[-1].split(':')[-1].split('.')[0]
        return f'---\nauthor: Constructed\n---\n## Motivation\ngoal token{index}\n## Rationale\nreason token{index}\n## Specification\ntoken{index}'
    monkeypatch.setattr(g.core,'git',raw)
    inputs={'documents':str(docs),'first_drafts':str(first),'peps':str(tmp_path),'eips':str(tmp_path)}
    for cell in g.grid():
        cfg={**cell,'phase':'GO1-score','reader':'tfidf'};out=tmp_path/cell['cell']
        result=g.execute(out,inputs,cfg);assert result['rows']>0 and result['candidate_count']==cfg.get('distractors',49)+1
        assert g.verify(out,inputs,cfg)['verified']
