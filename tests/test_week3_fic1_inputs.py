import copy
import hashlib
import json
import pytest
from runners.drive.cards import week3_fic1_inputs as m


def fixture():
    words=[]; documents=[]; matches=[]
    for n in range(13):
        writer='w'+str(n//4); genre=m.GENRES[(n//2)%2]; half=n%2
        sid='s'+str(n); prompt=genre+'-'+str(half); timestamp=float(n)
        tokens=['caf\u00e9','one','.','extra','\U0001f642']
        ww=[dict(index=i,token=t,is_word=i in (0,1,3),ordinal=i,
                 completed_ordinal=i,seconds=float(i)) for i,t in enumerate(tokens)]
        row=dict(session=sid,writer=writer,prompt=prompt,timestamp=timestamp,genre=genre,words=ww)
        words.append(row)
        text='P AI caf\u00e9.'
        documents.append(dict(keys={k:row[k] for k in m.IDENTITY},text=text,
            textSha256=hashlib.sha256(text.encode()).hexdigest(),
            provenance=[dict(start=0,end=2,source='prompt'),dict(start=2,end=4,source='accepted'),
                        dict(start=4,end=len(text),source='typed')]))
        if n<12:
            matches.append(dict(**{k:row[k] for k in (*m.IDENTITY,'genre','timestamp')},half=half,pair=n//2,
                typed_words=2,original_typed_words=3,original_token_count=5,word_indices=[0,1],
                token_stop_exclusive=2,boundary_completed_ordinal=1))
    return dict(words=words,documents=documents,matches=matches)


def prepare(f): return m.prepare(f['words'],f['documents'],f['matches'],m.CONSTRUCTED)


def test_restores_full_production_preserves_original_cohort_and_final_provenance():
    f=fixture(); units,profiles,summary,extra=prepare(f)
    assert len(units)==len(profiles)==12 and summary['writers']==3
    assert summary['matched_typed_words']==24 and summary['full_typed_words']==36
    assert summary['restored_typed_words']==12 and extra==['s12']
    assert units[0]['typed_production'][-1]['token']=='\U0001f642'
    assert units[0]['typed_production'][3]['token']=='extra'  # Later deletion absent in final text stays.
    assert 'extra' not in units[0]['final_document']['text']
    assert units[0]['final_accepted_characters']==2
    assert not summary['identification_computed'] and not summary['auth_requests_prepared']
    for rows in f.values(): rows.reverse()
    assert prepare(f)==(units,profiles,summary,extra)


@pytest.mark.parametrize('bad',['duplicate_words','missing_document','duplicate_match','missing_match','writer',
    'prefix','count','half','token','document_hash','provenance'])
def test_invalid_sources_fail_closed(bad):
    f=fixture()
    if bad=='duplicate_words':f['words'].append(copy.deepcopy(f['words'][0]))
    elif bad=='missing_document':f['documents'].pop()
    elif bad=='duplicate_match':f['matches'].append(copy.deepcopy(f['matches'][0]))
    elif bad=='missing_match':f['matches'].pop()
    elif bad=='writer':f['documents'][0]['keys']['writer']='wrong'
    elif bad=='prefix':f['matches'][0]['word_indices']=[0,3]
    elif bad=='count':f['matches'][0]['original_typed_words']=4
    elif bad=='half':f['matches'][0]['half']=True
    elif bad=='token':f['words'][0]['words'][0]['token']=''
    elif bad=='document_hash':f['documents'][0]['text']+='x'
    elif bad=='provenance':f['documents'][0]['provenance'][1]['start']=1
    with pytest.raises(ValueError):prepare(f)


def test_same_prompt_cannot_cross_halves():
    f=fixture()
    f['words'][1]['prompt']=f['matches'][1]['prompt']=f['documents'][1]['keys']['prompt']=f['words'][0]['prompt']
    with pytest.raises(ValueError,match='halves overlap'):prepare(f)


def test_full_handler_reentry_complete_replay_and_mutation_refusal(tmp_path):
    fixture_path=tmp_path/'fixture.json';m.freeze(fixture_path,fixture())
    inputs=dict(fixture=str(fixture_path));out=tmp_path/'out'
    m.execute(out,inputs,m.CONSTRUCTED)
    hashes={str(p.relative_to(out)):m.filehash(p) for p in out.rglob('*.json')}
    assert m.verify(out,inputs,m.CONSTRUCTED)['all_sessions_recomputed']
    m.execute(out,inputs,m.CONSTRUCTED)
    assert hashes=={str(p.relative_to(out)):m.filehash(p) for p in out.rglob('*.json')}
    path=out/'PROFILES.json'; profiles=m.read(path);profiles[0]['full_typed_words']=0
    m.atomic(path,profiles)
    with pytest.raises(ValueError,match='replay differs'):m.verify(out,inputs,m.CONSTRUCTED)


def test_changed_source_refuses_existing_checkpoint(tmp_path):
    path=tmp_path/'fixture.json';m.freeze(path,fixture()); inputs=dict(fixture=str(path));out=tmp_path/'out'
    m.execute(out,inputs,m.CONSTRUCTED)
    f=m.read(path);f['words'][0]['words'][0]['token']='changed';m.atomic(path,f)
    with pytest.raises(ValueError,match='replay differs'):m.verify(out,inputs,m.CONSTRUCTED)


def test_unknown_input_config_and_no_silent_fixture_fallback(tmp_path):
    with pytest.raises(ValueError):m.load(dict(fixture='absent'),m.CONFIG)
    with pytest.raises(ValueError):m.load({},m.CONSTRUCTED)
    with pytest.raises(ValueError):m.load({},dict(m.CONFIG,writers=23))


def test_corpus_adapter_requires_exact_completed_producer_seals(tmp_path,monkeypatch):
    f=fixture(); monkeypatch.setattr(m,'word_source',lambda inputs:(f['words'],{},dict(primary_sessions=1399)))
    genre=tmp_path/'genre'; docs=tmp_path/'docs'; genre.mkdir();docs.mkdir()
    def seal(root,module):
        m.freeze(root/'PLAN.json',dict(module=module))
        m.freeze(root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,
            outputs={'PLAN.json':m.filehash(root/'PLAN.json')}))
    seal(genre,'wrong-producer');seal(docs,'runners.drive.cards.engine_input_full')
    inputs=dict(pmap_completion='mocked',genre_completion=str(genre/'COMPLETE.json'),document_completion=str(docs/'COMPLETE.json'))
    with pytest.raises(ValueError,match='unexpected predecessor'):m.load(inputs,m.CONFIG)
    m.atomic(genre/'PLAN.json',dict(module='runners.drive.cards.week_genre_inputs_recovery'))
    with pytest.raises(ValueError,match='dependency changed'):m.load(inputs,m.CONFIG)
