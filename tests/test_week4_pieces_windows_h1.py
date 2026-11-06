import copy
import pytest
from runners.drive.cards import week4_pieces_windows_h1 as m
from runners.drive.cards import week3_insertion_provenance_h1 as source
from runners.drive.cards.timing_census import read
from tests.test_week3_pieces_effects_pilot import fixture,config
from tests.test_week3_pieces_input import fixture_events as legacy_events
from unittest.mock import patch


def canonical_fixture(root):
    def corrected():
        events,menus,selected=legacy_events()
        for e in events:
            if e['eventName']=='suggestion-open':e['currentSuggestions']=[dict(index=0,original='xyz',trimmed='xyz')]
            if e['eventName']=='suggestion-select':e['currentSuggestionIndex']=0
        canonical=source.replay(events)
        assert {r['ordinal'] for r in canonical['events'] if r['usable']}=={r['ordinal'] for r in menus}
        return events,menus,selected
    with patch('tests.test_week3_pieces_input.fixture_events',corrected):return fixture(root)


def cases():
    for kind in ('plain','newline','rewrite','repeated','unmatched','edited','deleted'):
        events,timeline=source.fixture(kind)
        for i in range(30):
            events.append(dict(eventName='idle',eventSource='user',eventTimestamp=20000+i*1000,
                               textDelta={'ops':[]} if i%2 else None))
        events.append(dict(eventName='idle',eventSource='user',eventTimestamp=180000))
        anchors=[dict(source_ordinal=i,seconds=e['eventTimestamp']/1000) for i,e in enumerate(events)]
        yield events,timeline,anchors


def test_all_original_windows_identical_on_every_anchor():
    for events,timeline,anchors in cases():assert m.effect_windows(events,timeline,anchors)==m.old.effect_windows(events,timeline,anchors)


def test_punctuation_delete_reinsert_unicode_and_retain_only():
    events,timeline=source.fixture('plain')
    events.extend([dict(eventName='text-insert',eventSource='user',eventTimestamp=20000,textDelta={'ops':[{'retain':5},{'insert':'.'}]}),
        dict(eventName='text-delete',eventSource='user',eventTimestamp=30000,textDelta={'ops':[{'retain':5},{'delete':1}]}),
        dict(eventName='text-insert',eventSource='user',eventTimestamp=40000,textDelta={'ops':[{'retain':5},{'insert':'!'}]}),
        dict(eventName='text-insert',eventSource='user',eventTimestamp=45000,textDelta={'ops':[{'retain':7}]}),
        dict(eventName='idle',eventSource='user',eventTimestamp=180000)])
    from runners.drive.timeline import rebuild
    canonical=source.replay(events)
    choices=[dict(key=str(r['ordinal']),ordinal=r['ordinal'],end_ordinal=len(events),handling=r['decision'],menu=r['options']) for r in canonical['events'] if r['usable']]
    timeline=rebuild(events,choices)
    anchors=[dict(source_ordinal=i,seconds=e['eventTimestamp']/1000) for i,e in enumerate(events)]
    assert m.effect_windows(events,timeline,anchors)==m.old.effect_windows(events,timeline,anchors)


def test_no_delta_events_do_not_reconvert_text(monkeypatch):
    events,timeline,anchors=next(cases());original=m.old.text_of;calls=[]
    def counted(doc):calls.append(1);return original(doc)
    monkeypatch.setattr(m.old,'text_of',counted)
    m.effect_windows(events,timeline,anchors)
    assert len(calls)==2+sum(bool(m.old.delta_ops(e.get('textDelta'))) for e in events)


def test_full_cost_work_matches_original_and_replays(tmp_path):
    inputs=canonical_fixture(tmp_path/'fixture');cfg=config()
    a=m.execute(tmp_path/'new',inputs,cfg);b=m.pilot.execute(tmp_path/'old',inputs,cfg)
    assert a['work']==b['work']
    assert m.verify(tmp_path/'new',inputs,cfg)['full_probe_replay']


def test_bad_anchor_and_source_still_refuse():
    events,timeline,anchors=next(cases());bad=copy.deepcopy(anchors);bad[0]['seconds']+=1
    with pytest.raises(ValueError,match='anchor differs'):m.effect_windows(events,timeline,bad)
    changed=dict(timeline,final_document='different')
    with pytest.raises(ValueError):m.effect_windows(events,changed,anchors)
