import copy
import json
import pytest
from runners.drive.cards import week4_auth_source as a


def test_exact_unicode_spacing_seams_and_exclusions():
    first,empty,long=a.fixtures();v=a.project(first)
    assert v['text']=='I  care \U0001f600!\n\nTail.' and v['payload_words']==4 and v['seams']==1
    assert [x['text'] for x in v['typed_chunks']]==['I  care \U0001f600!','Tail.']
    assert a.project(empty)['text']=='' and a.project(empty)['payload_words']==0
    assert a.project(long)['text']=='  '+('word\t'*399)+'word'
    assert a.project(long)['payload_words']==400 and a.project(long)['full_typed_words']==401
    for t in a.fixtures():assert a.project(t)==a.project(t,True)


def test_invalid_unicode_and_provenance_refused():
    for independent in (False,True):
        t=a.fixtures()[0];t['final_spans'][1]['end_utf16']-=1
        with pytest.raises(ValueError):a.project(t,independent)
        t=a.fixtures()[0];t['final_document']+='missing'
        with pytest.raises(ValueError):a.project(t,independent)
        t=a.fixtures()[0];t['final_spans'][0]['origin']='foreign'
        with pytest.raises(ValueError):a.project(t,independent)


def test_whole_handlers_reentry_and_mutation(tmp_path):
    c=a.configuration('constructed');a.execute(tmp_path,{},c)
    assert a.verify(tmp_path,{},c)['independent_codepoint_replay']
    before={str(p.relative_to(tmp_path)):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file() and p.name!='PROGRESS.json'}
    a.verify(tmp_path,{},c)
    assert before=={str(p.relative_to(tmp_path)):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file() and p.name!='PROGRESS.json'}
    p=tmp_path/'SUMMARY.json';p.write_text('{}',encoding='utf8')
    with pytest.raises(ValueError):a.verify(tmp_path,{},c)


def test_frozen_configuration_and_sources(tmp_path):
    c=a.configuration('constructed');c['max_words']=401
    with pytest.raises(ValueError):a.execute(tmp_path,{},c)
    with pytest.raises(ValueError):a.execute(tmp_path,{'secret':'source'},a.configuration('constructed'))
    with pytest.raises(ValueError):a.cohort({})


@pytest.fixture
def sealed_cohort(tmp_path):
    root=tmp_path/'fic1';out=root/'output';out.mkdir(parents=True)
    def put(path,value):path.write_text(json.dumps(value),encoding='utf8')
    put(root/'PLAN.json',{});index=[];rows=[];hashes={'PLAN.json':a.filehash(root/'PLAN.json')}
    for i in range(990):
        v=dict(session=f'{i:04}',writer=str(i%24),genre='fixture',prompt=str(i%7),half=i%2,final_document=dict(text='typed'))
        p=out/(v['session']+'.json');put(p,v);h=a.filehash(p)
        index.append(dict(session=v['session'],file=p.name,sha256=h));hashes['output/'+p.name]=h;rows.append(v)
    put(out/'SESSION_INDEX.json',index);hashes['output/SESSION_INDEX.json']=a.filehash(out/'SESSION_INDEX.json')
    put(root/'COMPLETE.json',dict(fresh_process_verified=True,outputs=hashes))
    landing=tmp_path/'landing.json';put(landing,dict(full_write_through=True,completion_sha256=a.filehash(root/'COMPLETE.json')))
    return dict(fic1_root=str(root),fic1_landing=str(landing),r2_root='unused',r2_landing='unused'),rows


def test_sealed_cohort_requires_exact_landing_and_payloads(sealed_cohort):
    inputs,rows=sealed_cohort
    assert len(a.cohort(inputs))==990
    p=a.Path(inputs['fic1_landing']);original=p.read_bytes();p.write_text('{}',encoding='utf8')
    with pytest.raises((KeyError,ValueError)):a.cohort(inputs)
    p.write_bytes(original)
    (a.Path(inputs['fic1_root'])/'output/0000.json').write_text('{}',encoding='utf8')
    with pytest.raises(ValueError):a.cohort(inputs)


def test_cross_source_join_refuses_identity_or_text_changes(sealed_cohort,monkeypatch):
    inputs,old=sealed_cohort
    row=dict(session='0000',writer=old[0]['writer'],genre='fixture',record=dict(exact=True,timeline=dict(final_document='typed')))
    monkeypatch.setattr(a,'r2_source',lambda inputs,n:iter([row]))
    assert list(a.source(inputs,1))[0]['prompt']==old[0]['prompt']
    row['writer']='another'
    with pytest.raises(ValueError):list(a.source(inputs,1))
    row['writer']=old[0]['writer'];row['record']['timeline']['final_document']='different'
    with pytest.raises(ValueError):list(a.source(inputs,1))
    row['record']['exact']=False
    assert not list(a.source(inputs,1))[0]['record']['exact']
    monkeypatch.setattr(a,'r2_source',lambda inputs,n:iter([]))
    with pytest.raises(ValueError):list(a.source(inputs,1))
