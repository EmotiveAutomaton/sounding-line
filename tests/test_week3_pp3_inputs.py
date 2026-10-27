import json
from copy import deepcopy
import pytest
from runners.drive.cards import week3_pp3_inputs as m

def row(before,after,t=0,author=0,project=0,label='Text Production',category='IMPLEMENTATION'):
    return {'before text':before,'after text':after,'timestamp':t,'author':author,'project':project,'label':label,'high-level':category}

def test_complete_unicode_edit_envelopes():
    assert m.envelope('a😀z','aéz')==(1,1,1)
    assert m.envelope('ab','abc')==(2,0,1)
    assert m.envelope('abc','ab')==(2,1,0)
    assert m.envelope('abc','abc')==(3,0,0)

def test_timing_continuity_and_no_row_deletion():
    rows=[row('','a'),row('a','ab',1000),row('other','x',2000),row('x','xy',3000),row('xy','xyz',3000)]
    out,s=m.extract(rows)
    assert len(out)==5 and s['row_deletions']==0
    assert [r['pause_ms'] for r in out]==[None,1000,None,None,None]
    assert s['pause_observed']==1

def test_labels_cannot_change_features():
    rows=[row('a','ab'),row('ab','abc',1000)];other=deepcopy(rows)
    for r in other:r.update(label='Clarity',**{'high-level':'REVISION'})
    a,_=m.extract(rows);b,_=m.extract(other)
    assert [r['features'] for r in a]==[r['features'] for r in b]

def test_future_content_and_labels_cannot_change_previous_features():
    rows=[row('a','ab'),row('ab','abc',1000)];a,_=m.extract(rows)
    rows.append(row('abc','completely different',2000,label='Clarity',category='REVISION'))
    b,_=m.extract(rows)
    assert a==b[:2]

def test_history_is_project_and_author_scoped():
    rows=[row('','a'),row('a','ab',1000,project=1),row('a','ab',1000,author=1)]
    out,s=m.extract(rows)
    assert all(r['pause_ms'] is None for r in out)
    assert len({r['author'] for r in out})==3 and s['projects']==2

def test_structural_context_excludes_words():
    a=m.structural_context('\\section{hello}\\begin{figure}x')
    b=m.structural_context('\\section{world}\\begin{figure}y')
    assert a==b and sum(a)==2
    assert sum(m.structural_context('\\begin{figure}x\\end{figure}'))==0

def test_full_handler_replay_and_corruption_refusal(tmp_path):
    source=tmp_path/'fixture.json';source.write_text(json.dumps([row('','x'),row('x','xy',1000)]),encoding='utf8')
    out=tmp_path/'out';inputs={'fixture':str(source)}
    assert m.execute(out,inputs,m.FIXTURE)['rows']==2
    assert m.verify(out,inputs,m.FIXTURE)['verified']
    m.execute(out,inputs,m.FIXTURE)
    (out/'ROWS.jsonl.gz').write_bytes(b'bad')
    with pytest.raises(Exception):m.verify(out,inputs,m.FIXTURE)

def test_unknown_and_contradictory_labels_fail():
    with pytest.raises(ValueError):m.extract([row('','x',label='invented')])
    with pytest.raises(ValueError):m.extract([row('','x',category='REVISION')])
