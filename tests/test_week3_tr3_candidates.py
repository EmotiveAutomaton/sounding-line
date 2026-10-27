import json
import pytest
from runners.drive.cards import week3_tr3_candidates as m


def fixture():
    rows=[dict(session='a',writer='d',prompt='p',half='discovery'),
          dict(session='b',writer='d',prompt='q',half='discovery'),
          dict(session='c',writer='t',prompt='p',half='test')]
    display=dict(ordinal=1,origin=1,reopened=False,options=['Perhaps it is. Perhaps it is!','Maybe.'])
    return dict(census=dict(roster=rows),split=dict(seed=20261026,writers={'d':'discovery','t':'test'},session_counts={'d':2,'t':1}),
        units={'a':dict(session='a',writer='d',prompt='p',displays=[display,dict(display,ordinal=2,reopened=True)]),
               'b':dict(session='b',writer='d',prompt='q',displays=[dict(ordinal=0,origin=None,reopened=True,options=[])])})


def test_exact_ngrams_and_punctuation_no_cross_sentence_adjacency():
    c=m.features('Perhaps it is. Perhaps it is!')
    assert c=={'p:!':1,'p:.':1,'w1:is':2,'w1:it':2,'w1:perhaps':2,
               'w2:it is':2,'w2:perhaps it':2,'w3:perhaps it is':2}


def test_unicode_symbols_gaps_and_apostrophes():
    c=m.features('Caf\u00e9 DON\u2019T \U0001f600 x_y; a\nb')
    assert c['w2:caf\u00e9 don\u2019t']==1 and c['w2:a b']==1
    assert c['p:\u2019']==1 and c['p:_']==1
    assert c['p:;']==1 and not any('\U0001f600' in k or 'x y' in k for k in c)
    assert 'w2:don\u2019t x' not in c
    assert m.features('')=={}
    with pytest.raises(UnicodeError):m.features('\ud800')


def test_reopen_counted_once_empty_orphan_retained():
    f=fixture();r=m.prepare(f['units']['a'],f['census']['roster'][0])
    assert r['menus']==1 and r['offers']==2 and r['feature_counts']['w1:perhaps']==2
    assert m.prepare(f['units']['b'],f['census']['roster'][1])['empty_displays']==1


@pytest.mark.parametrize('fault',['half','identity','reopen','duplicate','options'])
def test_invalid_unit_refused(fault):
    f=fixture();u=f['units']['a'];r=f['census']['roster'][0]
    if fault=='half':r['half']='test'
    elif fault=='identity':u['writer']='other'
    elif fault=='reopen':u['displays'][1]['options']=['changed']
    elif fault=='duplicate':u['displays'][1]['ordinal']=1
    else:u['displays'][0]['options']=[None]
    with pytest.raises(ValueError):m.prepare(u,r)


def test_changed_split_and_population_refused():
    f=fixture();c=f['census'];s=f['split']
    assert len(m.discovery_roster(c,s,False))==2
    with pytest.raises(ValueError):m.discovery_roster(c,s,True)
    s['session_counts']['d']=1
    with pytest.raises(ValueError):m.discovery_roster(c,s,False)
    s['session_counts']['d']=2;c['roster'][0]['half']='test'
    with pytest.raises(ValueError):m.discovery_roster(c,s,False)


def test_serialized_reentry_full_replay_and_test_units_not_read(tmp_path):
    f=tmp_path/'fixture.json';f.write_text(json.dumps(fixture()),encoding='utf8')
    config=dict(mode='constructed',seed=20261026);inputs=dict(fixture=str(f));out=tmp_path/'output'
    first=m.execute(out,inputs,config)
    assert first['summary']['sessions']==2 and first['summary']['test_units_read']==0
    assert m.execute(out,inputs,config)==first
    assert m.verify(out,inputs,config)['complete_candidate_replay']
    # No test source exists in the fixture: reading it would fail.
    candidate=out/'CANDIDATES.json';j=json.loads(candidate.read_text());j['counts']['w1:perhaps']+=1
    candidate.write_text(json.dumps(j))
    with pytest.raises(ValueError,match='aggregate'):m.verify(out,inputs,config)
