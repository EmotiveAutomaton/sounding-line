"""Known source transformations and indistinguishability gate the new targets."""
from runners.stage11.replay import replay
from runners.stage11.run import fixture
from runners.stage11_1.targets import project,public


def extract(rows):
    event=replay(rows)['events'][0]
    assert event['usable']
    return project(event,rows),event


def edit(*ops):
    return dict(eventName='text-insert',eventSource='user',textDelta={'ops':list(ops)})


def facts(target):return {f['slot']:f for f in target['facts']}


def test_same_all_blind_fields_distinct_executed_histories():
    a,ea=extract(fixture(True));b,eb=extract(fixture(False))
    for tier in ('artifact','alternatives'):assert public(ea,tier)==public(eb,tier)
    assert facts(a)['entry']['actor']=='model'
    assert facts(b)['entry']['operation']=='absent'
    assert facts(b)['continuation']['actor']=='human_writer'
    assert a['attributes']==b['attributes']==dict(reviewed='unknown',endorsed='unknown',understood='unknown')


def test_formatting_continuation_and_surrounding_separate():
    rows=fixture()+[edit({'retain':8},{'delete':1},{'insert':'L'}),
                    edit({'retain':13},{'insert':' afterward'}),edit({'insert':'Before '})]
    t,e=extract(rows);f=facts(t)
    assert e['end_document']=='Before A small Light afterward\n'
    assert f['change']['operation']=='format_edit'
    assert f['removal']['span_state']=='unlocated'
    assert f['continuation']['exact_spans']==[[20,30]]
    assert f['surrounding']['exact_spans']==[[0,7]]


def test_full_deletion_does_not_make_prior_document_continuation():
    t,e=extract(fixture()+[edit({'retain':7},{'delete':6}),edit({'insert':'New '})])
    f=facts(t)
    assert f['change']['operation']=='delete' and f['entry']['span_state']=='unlocated'
    assert f['surrounding']['operation']=='content_edit'
    assert f['continuation']['operation']=='absent'


def test_astral_character_positions_remain_codepoints():
    rows=fixture();rows[1]['currentSuggestions'][0].update(original=' 🌞 light',trimmed=' 🌞 light')
    rows[3]['textDelta']['ops'][1]['insert']=' 🌞 light'
    t,e=extract(rows+[edit({'insert':'🌍 '})]);f=facts(t)
    assert f['entry']['exact_spans']==[[9,17]]
    assert e['end_document'][9:17]==' 🌞 light'
