"""Input equality, exact provenance, full handler replay and changed-source refusal."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from runners.drive.cards import week3_identification_inputs as card
from runners.drive.cards.timing_p6 import gzip_equal
from runners.drive.engine_habits_child import project


def fixture():
    rows=[]; hh=[]; docs=[]; genres=[]
    dictionary=dict(words=['word','other'],punctuation=['.'],character_bigrams=['wo'])
    for w in range(3):
        for s in range(8):
            g='creative' if s%2==0 else 'argumentative'
            keys=dict(session=f's{w}-{s}',writer=f'w{w}',prompt=f'{g}-{s//2}')
            row=dict(**keys,timestamp=float(s),word_counts={'word':w+1,'other':2},punctuation_counts={'.':1},
                     handling={'accept':w+1,'dismiss':1},revision={'content':1,'housekeeping':2},
                     accepted_characters=4,edited_accepted_characters=1,accepted_options=1,declined_options=1,
                     accepted_vector_sum=[0.]*384,declined_vector_sum=[0.]*384,requests=2,final_words=4,
                     tc_timing_mode='logged_delta',within_intervals=[1.,2.],onset_intervals=[3.],
                     bigram_intervals={'wo':[1.,2.]})
            rows.append(row)
            raw=dict(words=10,quotedWords=0,sentenceCount=2,sentenceMean=5.,sentenceSpread=1.,repeats={},
                     connectives={k:1 for k in card.habits.CONNECTIVES},punctuation={k:1 for k in card.habits.PUNCTUATION})
            v=project(raw,card.habits.CONNECTIVES);hh.append(dict(keys=keys,final=v,typed=copy.deepcopy(v)))
            text='word other.'
            docs.append(dict(keys=keys,text=text,textSha256=hashlib.sha256(text.encode()).hexdigest(),
                             provenance=[dict(start=0,end=4,source='accepted'),dict(start=4,end=len(text),source='typed')]))
            genres.append(dict(row,genre=g,pair=f'{w}-{s//2}',half=(s//2)%2))
    return rows,hh,docs,dictionary,genres,dictionary,dict(mode='primary',primary_population_supported=True)


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,sort_keys=True),encoding='utf8')


def seal(root):
    write(root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,
        outputs={p.relative_to(root).as_posix():card.filehash(p) for p in sorted(root.rglob('*')) if p.is_file() and p.name!='COMPLETE.json'}))
    return str(root/'COMPLETE.json')


def source_fixture(root):
    rr,hh,dd,d,gg,gd,gs=fixture()
    roots={k:root/k for k in card.INPUTS}
    modules={'pmap_completion':'timing_pmap_recovery','habit_completion':'engine_habits_input',
             'document_completion':'engine_input_full','genre_completion':'week_genre_features_resume'}
    for k,p in roots.items():write(p/'PLAN.json',dict(module='runners.drive.cards.'+modules[k]))
    p=roots['pmap_completion']
    for r in rr:gzip_equal(p/'output/sessions'/f"{r['session']}.json.gz",r)
    write(p/'output/STYLE_DICTIONARY.json',d)
    p=roots['habit_completion'];gzip_equal(p/'output/HABITS.json.gz',hh)
    write(p/'output/SUMMARY.json',dict(final_export_parity=True,documents=24))
    p=roots['document_completion'];(p/'output').mkdir()
    (p/'output/DOCUMENTS.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in dd),encoding='utf8')
    p=roots['genre_completion'];gzip_equal(p/'output/FEATURES.json.gz',gg)
    write(p/'output/DICTIONARY.json',gd);write(p/'output/SUMMARY.json',gs)
    return {k:seal(p) for k,p in roots.items()}


def test_preparation_preserves_population_original_profiles_and_session_units():
    args=fixture();v=card.prepare(*args)
    assert len(v['rows'])==len(v['genre_rows'])==24
    assert len(v['rows'][0]['features'])==9
    assert v['rows'][0]['accepted_share']==pytest.approx(4/11)
    assert v['rows'][0]['features']['PMAP.style']==pytest.approx([.25,.5,.25])
    assert v['legacy']['pmap']==card.pmap.profiles(args[0],args[3])[0]


def test_final_style_uses_full_text_and_unicode_provenance_is_codepoints():
    d=dict(text='\U0001f600 word.',textSha256=hashlib.sha256('\U0001f600 word.'.encode()).hexdigest(),
           provenance=[dict(start=0,end=1,source='accepted'),dict(start=1,end=7,source='typed')])
    assert card.accepted_share(d)==pytest.approx(1/7)
    assert card.final_style(d,dict(words=['word'],punctuation=['.']))==[.5,.5]
    d['provenance'][0]['end']=2
    with pytest.raises(ValueError,match='partition'):card.accepted_share(d)


def test_missing_cross_source_population_or_identity_refused():
    args=list(fixture());args[1]=args[1][1:]
    with pytest.raises(ValueError,match='populations'):card.prepare(*args)
    args=list(fixture());args[2][0]['keys']['prompt']='wrong'
    with pytest.raises(ValueError,match='identity'):card.prepare(*args)


def test_complete_input_handler_reentry_fresh_verify_and_mutation(tmp_path):
    config=card.CONSTRUCTED
    inputs=source_fixture(tmp_path/'source');output=tmp_path/'out'
    assert card.execute(output,inputs,config)['status']=='complete'
    before={p.name:p.read_bytes() for p in output.iterdir()}
    assert card.verify(output,inputs,config)['verified']
    card.execute(output,inputs,config)
    assert before=={p.name:p.read_bytes() for p in output.iterdir()}
    doc=Path(inputs['document_completion']).parent/'output/DOCUMENTS.jsonl'
    doc.write_text(doc.read_text()+'\n',encoding='utf8')
    with pytest.raises(ValueError,match='changed'):card.verify(output,inputs,config)
