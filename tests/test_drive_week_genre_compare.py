"""Known genre fingerprints, chance ties, invalid references and full replay."""
import copy
from pathlib import Path

import numpy as np
import pytest

from runners.drive.cards import week_genre_compare as stats, week_genre_features as features
from runners.drive.cards.timing_text import replay_words
from runners.drive.cards.timing_revision_events import replay_revision_events
from runners.drive.cards.timing_pmap_source import raw_features, dictionary
from runners.drive.cards.timing_p6 import gzip_equal
from runners.stage9.common import digest
from tests.test_drive_engine_occurrences import event
from tests.test_drive_week_genre_inputs import write


def completion(root):
    files = {p.relative_to(root).as_posix():features.filehash(p) for p in root.rglob('*')
             if p.is_file() and p.name != 'COMPLETE.json'}
    write(root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,outputs=files))
    return str(root/'COMPLETE.json')


def fixture(root):
    root = Path(root).resolve(); original=[]; raw_roster=[]; word_index=[]; revisions=[]; pins={}; pmap=[]; p2ix=[]
    for wi in range(15):
        for genre in stats.GENRES:
            for si in range(4):
                sid=f'w{wi:02}-{genre}-{si}'; meta=dict(session=sid,writer=f'w{wi:02}',prompt=f'{genre}-{si%2}',timestamp=si*1000.)
                text=('m'+chr(97+wi)+' ')*3 if genre=='creative' else 'common common common '
                events=[event(0,doc='')]; pos=0
                for char in text:
                    events.append(event((pos+1)*(wi+1 if genre=='creative' else 1)*10,[{'retain':pos},{'insert':char}]))
                    pos+=1
                replay=replay_words(events); audited=replay_revision_events(events)
                raw=root/'raw'/f'{sid}.jsonl'; raw.parent.mkdir(parents=True,exist_ok=True)
                import json
                raw.write_text('\n'.join(json.dumps(e) for e in events)+'\n',encoding='utf8',newline='\n')
                canonical=root/'results/phase_2_4_stage_9/private/prepared/coauthor-v2/sessions'/(digest({'coauthor-session':raw.stem})+'.json')
                write(canonical,dict(events=[]))
                timeline=dict(final_document=replay['final_document'],source_sha256=features.filehash(raw))
                p2=root/'p2'/f'{sid}.json'; write(p2,timeline)
                p2ix.append(dict(session=sid,file=p2.name,sha256=features.filehash(p2)))
                word=dict(**meta,words=replay['words']); path=root/'p6'/f'{sid}.json.gz'; gzip_equal(path,word)
                word_index.append(dict(session=sid,file=path.name,sha256=features.filehash(path)))
                sh=dict(raw=features.filehash(raw),p2=features.filehash(p2),p6=features.filehash(path),canonical=features.filehash(canonical))
                pair=features.raw_pairs(events,timeline,dict(events=[]))
                assert {k:v for k,v in pair.items() if k not in ('pairs','typed_atoms')}==raw_features(events,timeline,dict(events=[]))
                old=dict(**meta,source_hashes=sh,tc_timing_mode='logged_delta',
                    word_counts=dict(__import__('collections').Counter(w['token'] for w in replay['words'] if w['is_word'])),
                    punctuation_counts={},**{k:pair[k] for k in ('bigram_counts','bigram_intervals')})
                pmap.append(old); gzip_equal(root/'pmap/output/sessions'/f'{sid}.json.gz',old)
                rev=dict(**meta,source_hashes={k:sh[k] for k in ('raw','p2','p6')},revision_events=audited['revision_events'])
                revpath=root/'revision/output/sessions'/f'{sid}.json.gz'; gzip_equal(revpath,rev)
                revisions.append(dict(session=sid,file='sessions/'+revpath.name,sha256=features.filehash(revpath)))
                original.append(dict(word,genre=genre))
                raw_roster.append(dict(**meta,domain=genre,path=raw.relative_to(root).as_posix(),source_sha256=sh['raw']))
                pins[raw.relative_to(root).as_posix()]=sh['raw'];pins[canonical.relative_to(root).as_posix()]=sh['canonical']
    write(root/'ROSTER.json',raw_roster);write(root/'PINS.json',pins)
    write(root/'p6/INDEX.json',word_index);completion(root/'p6');write(root/'p2/INDEX.json',p2ix)
    write(root/'foundation/PLAN.json',dict(pins={'ROSTER.json':features.filehash(root/'ROSTER.json')}))
    write(root/'foundation/COMPLETE.json',dict(status='COMPLETE',plan_sha256=features.filehash(root/'foundation/PLAN.json')))
    inputs=dict(repo_root=str(root),raw_roster=str(root/'ROSTER.json'),source_pins=str(root/'PINS.json'),
        foundation_plan=str(root/'foundation/PLAN.json'),foundation_complete=str(root/'foundation/COMPLETE.json'),
        p6_completion=str(root/'p6/COMPLETE.json'),p6_index=str(root/'p6/INDEX.json'),session_index=str(root/'p2/INDEX.json'))
    write(root/'pmap/PLAN.json',dict(inputs=inputs));write(root/'pmap/output/PRIMARY.json',dict(source_audit=dict(sessions=len(original))))
    write(root/'pmap/output/STYLE_DICTIONARY.json',dictionary(pmap)); pc=completion(root/'pmap')
    write(root/'revision/PLAN.json',dict(inputs=inputs));write(root/'revision/output/INDEX.json',revisions); rc=completion(root/'revision')
    match_inputs=dict(pmap_completion=pc); matchroot=root/'matching'
    features.source.execute(matchroot/'output',match_inputs,features.source.CONFIG)
    write(matchroot/'PLAN.json',dict(inputs=match_inputs,config=features.source.CONFIG)); mc=completion(matchroot)
    return dict(matching_completion=mc,revision_completion=rc)


def features_fixture(root):
    inputs=fixture(root/'source'); target=root/'features'
    features.execute(target/'output',inputs,features.CONFIG)
    features.verify(target/'output',inputs,features.CONFIG)
    return dict(features_completion=completion(target))


@pytest.mark.parametrize('ops',[
    [[{'insert':'cat dog '}]],
    [[{'insert':'😀 café ' }],[{'delete':2}]],
    [[{'insert':'cat '}],[{'delete':3},{'insert':'cat'}]],
    [[{'insert':'cat '}],[{'retain':1},{'insert':'h'}]],
    [[{'insert':'old '}],[{'retain':4},{'insert':'new '}],[{'delete':4}]],
])
def test_pair_replay_parity_and_occurrence_subset(ops):
    events=[event(0,doc='')]+[event((i+1)*100,op) for i,op in enumerate(ops)]
    replay=replay_words(events); audit=replay_revision_events(events)['revision_events']
    pairs=features.raw_pairs(events,replay,dict(events=[]))
    assert {k:v for k,v in pairs.items() if k not in ('pairs','typed_atoms')}==raw_features(events,replay,dict(events=[]))
    first=next(i for i,w in enumerate(replay['words']) if w['is_word'])
    match=dict(token_stop_exclusive=first+1,original_token_count=len(replay['words']),word_indices=[first],typed_words=1)
    row=features.subset(replay,match,audit,pairs)
    assert row['typed_words']==1 and sum(row['word_counts'].values())==1
    assert row['timing_scope']['retained_pairs']<=row['timing_scope']['source_pairs']


def population(mode='positive'):
    rows=[]; d=dict(words=['word'+str(i) for i in range(8)],punctuation=[],character_bigrams=[])
    for wi in range(8):
        for genre in stats.GENRES:
            for si in range(4):
                unique=(genre==('argumentative' if mode=='negative' else 'creative')) and mode!='null'
                rows.append(dict(session=f'{wi}-{genre}-{si}',writer=str(wi),genre=genre,pair=si,half=si%2,
                    prompt=genre+str(si%2),timestamp=si,typed_words=1,word_counts={('word'+str(wi)) if unique else 'word0':1},
                    punctuation_counts={},within_intervals=[wi+1 if unique else 1],onset_intervals=[1],
                    bigram_intervals={},tc_timing_mode='logged_delta'))
    return rows,d,dict(mode='primary',primary_population_supported=True)


@pytest.mark.parametrize('mode,expected',[('positive','positive'),('negative','negative'),('null','null')])
def test_signed_known_answers_with_complete_control_banks(mode,expected):
    rows,d,summary=population(mode)
    out,banks=stats.controlled(rows,d,summary)
    assert out['channels']['style']['state']==expected
    assert all(len(bank)==200 for bank in banks.values())
    if mode=='null':
        assert out['channels']['style']['observed']['by_genre']['creative']['accuracy']==1/8
        assert out['channels']['style']['primary']['effect']==0


def test_permutations_preserve_matched_exposure_and_fake_counts():
    rows,_,_=population(); rng=np.random.default_rng(41)
    for altered in (stats.permute_genres(rows,rng),stats.fake_writers(rows,rng)):
        assert sorted(r['session'] for r in rows)==sorted(r['session'] for r in altered)
        assert __import__('collections').Counter((r['writer'],r['genre']) for r in rows)==__import__('collections').Counter((r['writer'],r['genre']) for r in altered)


def test_missing_support_is_not_zero_or_redrawn():
    rows,d,summary=population()
    for r in rows:
        if r['writer']=='0' and r['genre']=='creative': r['tc_timing_mode']='invalid'
    out,banks=stats.controlled(rows,d,summary)
    assert out['common_writers']['rhythm']==7 and out['excluded_writers']['rhythm']==['0']
    assert len(banks['within_writer'])==200


def test_source_to_features_to_full_statistic_and_tamper(tmp_path):
    inputs=features_fixture(tmp_path); out=tmp_path/'out'
    stats.execute(out,inputs,stats.CONFIG);assert stats.verify(out,inputs,stats.CONFIG)['complete_controls']
    saved=stats.read(out/'PRIMARY.json');assert saved['channels']['style']['state']=='positive'
    saved['matched_writers']=0;write(out/'PRIMARY.json',saved)
    with pytest.raises(ValueError,match='replay differs'): stats.verify(out,inputs,stats.CONFIG)


def test_identity_mutation_and_partial_same_event_exclusion():
    events=[event(0,doc=''),event(100,[{'insert':'cat dog '}])]
    replay=replay_words(events); audit=replay_revision_events(events)['revision_events']
    pairs=features.raw_pairs(events,replay,dict(events=[]))
    match=dict(token_stop_exclusive=1,original_token_count=2,word_indices=[0],typed_words=1)
    out=features.subset(replay,match,audit,pairs)
    assert out['word_counts']=={'cat':1} and out['timing_scope']['retained_token_atoms']==3
    assert out['timing_scope']['retained_pairs']==3  # ca, at, t-space; never dog
    bad=copy.deepcopy(audit);bad[0]['character_ids']=[4,5,6]
    with pytest.raises(ValueError,match='identity or spelling'):features.subset(replay,match,bad,pairs)
