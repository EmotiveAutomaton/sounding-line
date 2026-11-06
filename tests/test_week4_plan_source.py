from copy import deepcopy
import gzip
import json
import pytest
from runners.drive.cards import week4_plan_source as p
from runners.stage9.coauthor import replay


def test_midpoint_unicode_and_display_projection():
    e, c, m = p.fixture()
    r = p.source_session(e, c, m)
    assert r['cut'] == 8
    assert r['provider_text_only'] == dict(midpoint_text='A\U0001f600C\n', later_options=[['left','right']]*4)
    assert r['counts'] == dict(raw_later_openings=4, usable_later_openings=4, later_choices=4, midpoint_nonempty=True)
    assert all(x['choice'] == 2 for x in r['private_choices'])
    assert set(r['provider_text_only']) == {'midpoint_text','later_options'}


def test_future_edit_cannot_rewrite_midpoint():
    e, c, m = p.fixture()
    original = p.source_session(e, c, m)
    # Same number of events and same opening boundary; only future document changes.
    e[-1]['textDelta'] = {'ops':[{'delete':5}, {'insert':'future replacement\n'}]}
    c = replay(e)
    changed = p.source_session(e, c, m)
    assert changed['provider_text_only'] == original['provider_text_only']


def test_open_before_boundary_excluded_even_when_later_dismissed():
    e, c, m = p.fixture()
    e[7], e[8] = e[8], e[7]
    c = replay(e)
    m[0]['ordinal'] = 7
    r = p.source_session(e, c, m)
    assert r['counts']['usable_later_openings'] == 3


def test_ignore_is_not_dismissal():
    e, c, m = p.fixture()
    e[-1]['eventName'] = 'cursor'
    c = replay(e)
    m[-1].update(choice=None, handling='ignore')
    r = p.source_session(e, c, m)
    assert r['counts']['usable_later_openings'] == 4
    assert r['counts']['later_choices'] == 3


def test_inserted_choice_overrules_logged_selection():
    e, c, m = p.fixture()
    e[9] = dict(eventName='suggestion-select', currentSuggestionIndex=7,
                eventSource='api', textDelta={'ops':[{'retain':4}, {'insert':'\nright'}]})
    c = replay(e)
    assert c['events'][0]['logged_index_agrees'] is False
    m[0].update(choice=1, handling='accept')
    r = p.source_session(e, c, m)
    assert r['private_choices'][0]['choice'] == 1
    m[0]['choice'] = 0
    with pytest.raises(ValueError, match='choice binding'):
        p.source_session(e, c, m)


def test_unseen_option_and_duplicate_menu_refuse():
    e, c, m = p.fixture()
    bad = deepcopy(m)
    bad[0]['options'][0] = 'not shown'
    with pytest.raises(ValueError, match='Unseen'):
        p.source_session(e, c, bad)
    with pytest.raises(ValueError, match='Duplicate'):
        p.source_session(e, c, m+[m[0]])


def test_changed_canonical_and_malformed_source_refuse():
    e, c, m = p.fixture()
    bad = deepcopy(c)
    bad['final_document'] = 'changed'
    with pytest.raises(ValueError, match='Frozen canonical'):
        p.source_session(e, bad, m)
    e[1]['textDelta'] = {'ops':[{'retain':1000}]}
    with pytest.raises(ValueError, match='boundary'):
        p.source_session(e, c, m)


def test_utf16_surrogate_and_boolean_boundaries_refuse():
    b = 'A\U0001f600B\n'.encode('utf-16-le')
    with pytest.raises(UnicodeError):
        p.byte_delta(b, {'ops':[{'retain':1}, {'delete':1}]})
    with pytest.raises(ValueError):
        p.byte_delta(b, {'ops':[{'retain':True}]})
    assert p.byte_delta(b, {'ops':[{'retain':1}, {'delete':2}, {'insert':'x'}]}).decode('utf-16-le') == 'AxB\n'


def test_reentry_and_full_output_mutation(tmp_path):
    config = p.configuration('constructed')
    p.execute(tmp_path, {}, config)
    before = (tmp_path/'PRIVATE_SESSIONS.json.gz').read_bytes()
    assert p.verify(tmp_path, {}, config)['complete_source_replay']
    assert before == (tmp_path/'PRIVATE_SESSIONS.json.gz').read_bytes()
    rows = json.loads(gzip.decompress(before))
    rows[0]['provider_text_only']['midpoint_text'] = 'forged'
    (tmp_path/'PRIVATE_SESSIONS.json.gz').write_bytes(gzip.compress(json.dumps(rows).encode()))
    with pytest.raises(ValueError, match='Complete private'):
        p.verify(tmp_path, {}, config)
