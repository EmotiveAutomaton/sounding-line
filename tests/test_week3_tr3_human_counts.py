import copy
import json
import runpy
from pathlib import Path

import pytest
from runners.stage9.coauthor import units, text_of, apply_delta
from runners.drive.cards import week3_tr3_human_counts as m
from runners.drive.cards.week3_tr3_candidates import features
from runners.drive.cards.week3_tr3_inputs import assemble


def make_unit(changes, initial='', session='s', writer='a'):
    doc=units(initial);owners=[None]*len(doc);edits=[];count=0
    for ordinal,(source,ops) in enumerate(changes,1):
        doc,owners,_=apply_delta(doc,owners,{'ops':ops},insertion_owner=ordinal)
        edits.append(dict(ordinal=ordinal,timestamp=ordinal,source=source,operations=ops))
        if source=='user':count+=sum(len(op['insert']) for op in ops if 'insert' in op)
    return dict(session=session,writer=writer,prompt='p',initial_document=initial,
        final_document=text_of(doc),edits=edits,user_inserted_characters=count)


def cases():
    return [
      make_unit([('user',[{'insert':"Alpha beta gamma. Don't élan! x_y U0001f600 z\n"}])]),
      make_unit([('user',[{'insert':'c'}]),('user',[{'retain':1},{'insert':'a'}]),
        ('user',[{'retain':2},{'insert':'t'}]),('user',[{'retain':3},{'insert':' '}])]),
      make_unit([('user',[{'insert':'gone '}]),('user',[{'delete':5}])]),
      make_unit([('api',[{'insert':'model '}]),('user',[{'retain':6},{'insert':'own words '}])]),
      make_unit([('user',[{'insert':'red X blue '}]),('api',[{'retain':4},{'delete':2}])]),
      make_unit([('user',[{'insert':'a b '}]),('user',[{'retain':2},{'insert':' '}])]),
      make_unit([],initial=''),
      make_unit([('user',[{'insert':'go go '}])])]


def fixture():
    prepared={};rows=[]
    for i,u in enumerate(cases()):
        sid=str(i);u=dict(u,session=sid);prepared[sid]=u
        rows.append(dict(session=sid,writer='a',prompt='p',start=i*100,end=i*100+50,
            displays=[],typed_inserted_characters=u['user_inserted_characters']))
    # The held-out payload is deliberately absent, while its census is retained.
    rows.append(dict(session='test',writer='b',prompt='p',start=0,end=50,displays=[],typed_inserted_characters=1))
    split=dict(seed=20261026,writers={'a':'discovery','b':'test'},session_counts={'a':len(prepared),'b':1})
    return dict(units=prepared,census=assemble(rows,split),split=split)


def count(unit):return m.production_counts(unit)['feature_counts']


def test_complete_paste_matches_independent_static_tokenizer():
    u=cases()[0]
    assert count(u)==features(u['final_document'])
    assert 'w2:x y' not in count(u)


def test_incremental_composition_does_not_count_prefixes():
    assert count(cases()[1])=={'w1:cat':1}


def test_finished_deleted_production_retained():
    assert count(cases()[2])=={'w1:gone':1}
    assert count(make_unit([('user',[{'insert':'gone'}]),('user',[{'delete':4}])]))=={}


def test_mixed_sources_never_supply_a_human_ngram():
    assert count(cases()[3])=={'w1:own':1,'w1:words':1,'w2:own words':1}


def test_machine_join_cannot_create_a_human_phrase():
    assert count(cases()[4])==features('red X blue ')


def test_human_edit_can_create_a_new_phrase():
    u=make_unit([('user',[{'insert':'red X blue '}]),('user',[{'retain':4},{'delete':2}])])
    expected=features('red X blue ');expected['w2:red blue']=1
    assert count(u)==expected


def test_whitespace_change_does_not_duplicate_lexical_occurrence():
    assert count(cases()[5])==features('a b ')


def test_empty_and_repeated_text():
    assert count(cases()[6])=={}
    assert count(cases()[7])=={'w1:go':2,'w2:go go':1}


def test_cursor_locations_use_real_document_context():
    u=make_unit([('user',[{'insert':'left '}]),('user',[{'retain':7},{'insert':'right '}])],initial='__\n')
    assert count(u)=={'w1:left':1,'w1:right':1}


def test_formatting_attributes_preserve_character_contract():
    u=make_unit([('user',[{'insert':'word ','attributes':{'bold':True}}]),
        ('user',[{'retain':5,'attributes':{'bold':False}}])])
    assert count(u)=={'w1:word':1}


def test_source_delimiter_cannot_join_two_typed_words():
    u=make_unit([('user',[{'insert':'one'}]),('api',[{'retain':3},{'insert':' '}]),
        ('user',[{'retain':4},{'insert':'two '}])])
    assert count(u)=={'w1:one':1,'w1:two':1}


def test_last_word_completed_at_session_end():
    assert count(make_unit([('user',[{'insert':'last word'}])]))==features('last word')


def test_existing_typing_producer_representation():
    from runners.drive.cards.week3_tr3_typing import prepare
    f=runpy.run_path(str(Path(__file__).with_name('test_week3_tr3_typing.py')))['fixture']()
    u=prepare(**f['sessions'][0])
    r=m.production_counts(u)
    assert r['typed_characters']==5 and r['edits']==4
    assert 'w1:api' not in r['feature_counts']


@pytest.mark.parametrize('fault',['final','count','clock','ordinal','surrogate','boundary'])
def test_invalid_input_refuses(fault):
    u=make_unit([('user',[{'insert':'U0001f600 word '}])])
    if fault=='final':u['final_document']='wrong'
    elif fault=='count':u['user_inserted_characters']+=1
    elif fault=='clock':u['edits'][0]['timestamp']=float('nan')
    elif fault=='ordinal':u['edits'][0]['ordinal']=-1
    elif fault=='surrogate':u['edits'].append(dict(ordinal=2,timestamp=2,source='user',operations=[{'retain':1},{'insert':'x'}]))
    else:u['edits'].append(dict(ordinal=2,timestamp=2,source='user',operations=[{'retain':100}]))
    with pytest.raises((ValueError,UnicodeError)):count(u)


def test_full_handler_reentry_replay_and_tamper(tmp_path):
    path=tmp_path/'fixture.json';path.write_text(json.dumps(fixture()),encoding='utf8')
    inputs=dict(fixture=str(path));config=dict(mode='constructed',seed=20261026);out=tmp_path/'output'
    m.execute(out,inputs,config)
    before={p.relative_to(out).as_posix():p.read_bytes() for p in out.rglob('*') if p.is_file() and p.name!='PROGRESS.json'}
    assert m.verify(out,inputs,config)['complete_human_counts_replay']
    m.execute(out,inputs,config)
    assert before=={p.relative_to(out).as_posix():p.read_bytes() for p in out.rglob('*') if p.is_file() and p.name!='PROGRESS.json'}
    assert json.loads((out/'SUMMARY.json').read_text())['test_payloads_read']==0
    (out/'COUNTS.json').write_text('{}')
    with pytest.raises(ValueError,match='aggregate replay'):m.verify(out,inputs,config)
