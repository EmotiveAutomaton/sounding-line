import copy
import json
from collections import Counter,defaultdict
import pytest
from runners.drive.cards import week3_fic1_prefixes as m
from runners.drive.cards.timing_text import replay_words
from runners.drive.cards.timing_revision_events import replay_revision_events
from tests.test_drive_engine_occurrences import event


def case(text='caf\u00e9 one extra. ',bulk=False,deleted=False):
    events=[event(0,doc='')]
    if bulk:events.append(event(100,[dict(insert=text)]))
    else:
        for i,c in enumerate(text):events.append(event((i+1)*10,[dict(retain=i),dict(insert=c)]))
    if deleted:events.append(event(1000,[dict(retain=9),dict(delete=5)]))
    replay=replay_words(events);audit=replay_revision_events(events)['revision_events']
    pairs=m.base.raw_pairs(events,replay,dict(events=[]));words=replay['words']
    wc,pc=m.features.counts(words)
    whole=dict(word_counts=wc,punctuation_counts=pc,bigram_counts=pairs['bigram_counts'],
        bigram_intervals=pairs['bigram_intervals'],tc_timing_mode='logged_delta',
        within_intervals=[v for w in words if w['is_word'] for v in w['within_intervals']],
        onset_intervals=[w['pause_seconds'] for w in words if w['is_word'] and w['pause_seconds'] is not None])
    pairs=dict(pairs,typed_atoms=[pairs['typed_atoms'][i] for i in range(len(pairs['typed_atoms']))])
    return dict(words=words,audit=audit,pairs=pairs,whole=whole)


def fixture():
    units=[];groups=defaultdict(list)
    for wi in range(3):
        for genre in m.source.GENRES:
            for si in range(4):
                meta=dict(session=f'w{wi}-{genre}-{si}',writer=f'w{wi}',genre=genre,
                          half=si%2,pair=si,prompt=f'{genre}-{si%2}',timestamp=float(si))
                c=case(deleted=si==2);units.append(dict(c,metadata=meta));groups[wi,genre,si%2].append(meta['session'])
    profiles=[dict(writer=f'w{w}',genre=g,half=h,sessions=ss,full_typed_words=6)
              for (w,g,h),ss in sorted(groups.items())]
    return dict(units=units,profiles=profiles,dictionary=dict(words=['caf\u00e9','extra'],punctuation=['.'],character_bigrams=['ca','at','t ']))


def built(c,metadata=None):
    return m.unit(metadata or dict(session='s',writer='w',genre='creative',half=0,pair=0,prompt='p',timestamp=0.),
                  c['words'],c['audit'],c['pairs'],c['whole'])


def test_exact_quotas_cross_sessions_and_keep_deleted_production():
    f=fixture();units=[built(c,c['metadata']) for c in f['units'][:4:2]];d=f['dictionary']
    a=m.profile(units,2,d);assert a['selected_words']==2 and a['features']['style']==[.5,0.,0.]
    b=m.profile(units,4,d);assert b['features']['style']==[.4,.2,.2]
    assert [r['typed_words'] for r in b['members']]==[3,1]
    full=m.profile(units,None,d);assert full['selected_words']==6 and full['features']['style']==[.25,.25,.25]
    assert m.profile(list(reversed(units)),4,d)==b
    assert m.profile(units,8,d)==dict(state='unsupported',requested_words=8,available_words=6,selected_words=0,members=[],features=None)


def test_same_delta_other_word_does_not_leak_into_prefix():
    u=built(case('cat dog ',bulk=True));a=m.take(u,1)
    assert a['word_counts']=={'cat':1} and a['timing_scope']['retained_token_atoms']==3
    assert a['timing_scope']['retained_pairs']==3
    assert a['within_intervals']==[] and a['bigram_intervals']=={}


def test_unicode_atoms_survive_json_round_trip():
    u=built(case('\U0001f642 caf\u00e9 cat ',bulk=True))
    assert m.take(u,1)==m.take(json.loads(json.dumps(u)),1)
    assert m.take(u,1)['word_counts']=={'caf\u00e9':1}


def test_invalid_timing_stays_missing():
    u=built(case());u['whole']['tc_timing_mode']='invalid'
    assert m.profile([u],1,fixture()['dictionary'])['features']['rhythm']==[None]*5


@pytest.mark.parametrize('bad',['identity','pairs','counts','atoms'])
def test_occurrence_mismatches_refused(bad):
    c=case()
    if bad=='identity':c['audit'][0]['character_ids']=[0]
    elif bad=='pairs':c['whole']['bigram_counts']={}
    elif bad=='counts':c['whole']['word_counts']['extra']=0
    elif bad=='atoms':c['pairs']['typed_atoms']={'0':'x'}
    with pytest.raises(ValueError):built(c)


@pytest.mark.parametrize('quota',[0,-1,True,1.5,999])
def test_bad_session_quota_refused(quota):
    with pytest.raises(ValueError):m.take(built(case()),quota)


def test_full_handler_replay_reentry_and_missing_support(tmp_path):
    f=tmp_path/'fixture.json';m.freeze(f,fixture());inputs=dict(fixture=str(f));out=tmp_path/'out'
    m.execute(out,inputs,m.CONSTRUCTED)
    hashes={str(p.relative_to(out)):m.filehash(p) for p in out.rglob('*') if p.is_file()}
    assert m.verify(out,inputs,m.CONSTRUCTED)['all_prefixes_recomputed']
    m.execute(out,inputs,m.CONSTRUCTED)
    assert hashes=={str(p.relative_to(out)):m.filehash(p) for p in out.rglob('*') if p.is_file()}
    s=m.read(out/'SUMMARY.json');assert s['support']['8']==dict(prepared=0,unsupported=12)
    assert not s['identification_computed'] and not s['length_curve_scored']
    p=out/'PREFIX_FEATURES.json';v=m.read(p);v[0]['levels']['2']['selected_words']=3;m.atomic(p,v)
    with pytest.raises(ValueError,match='prefix replay differs'):m.verify(out,inputs,m.CONSTRUCTED)


@pytest.mark.parametrize('bad',['missing_profile','duplicate_profile','order','count','missing_unit'])
def test_wrong_complete_membership_refused(tmp_path,bad):
    f=fixture()
    if bad=='missing_profile':f['profiles'].pop()
    elif bad=='duplicate_profile':f['profiles'].append(copy.deepcopy(f['profiles'][0]))
    elif bad=='order':f['profiles'][0]['sessions'].reverse()
    elif bad=='count':f['profiles'][0]['full_typed_words']=100
    elif bad=='missing_unit':f['units'].pop()
    path=tmp_path/'fixture.json';m.freeze(path,f)
    with pytest.raises(ValueError):m.execute(tmp_path/'out',dict(fixture=str(path)),m.CONSTRUCTED)


def test_changed_source_and_unknown_config_refused(tmp_path):
    path=tmp_path/'fixture.json';m.freeze(path,fixture());inputs=dict(fixture=str(path));out=tmp_path/'out'
    m.execute(out,inputs,m.CONSTRUCTED)
    f=m.read(path);f['units'][0]['metadata']['timestamp']=100.;m.atomic(path,f)
    with pytest.raises(ValueError):m.verify(out,inputs,m.CONSTRUCTED)
    with pytest.raises(ValueError):m.execute(out,inputs,m.CONFIG)
    with pytest.raises(ValueError):m.execute(out,inputs,dict(m.CONSTRUCTED,word_limits=[1,2,3]))


def test_timing_quota_is_not_full_population_admission(tmp_path,monkeypatch):
    f=fixture()
    monkeypatch.setattr(m,'full_source',lambda inputs:((built(c,c['metadata']) for c in f['units']),f['profiles'],f['dictionary'],{}))
    out=tmp_path/'out';m.execute(out,{},m.TIMING)
    assert m.verify(out,{},m.TIMING)['all_timed_occurrences_recomputed']
    s=m.read(out/'SUMMARY.json');assert s['timing_sessions']==20 and not s['complete_population']
    assert not (out/'PREFIX_FEATURES.json').exists()
    before=m.filehash(out/'EXECUTE_COST.json');m.execute(out,{},m.TIMING)
    assert m.filehash(out/'EXECUTE_COST.json')==before
