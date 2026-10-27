import copy
import json

import pytest

from runners.drive.cards import week3_tr4_inputs as m
from runners.drive.cards.week3_tr3_inputs import assemble as exposure_census


def fixture():
    units = {}
    for writer, n in [('a', 12), ('b', 11)]:
        for i in range(n):
            sid = f'{writer}-{i:02d}'
            start = i*20
            displays = []
            for k, label in enumerate(m.CLASSES):
                displays.append(dict(ordinal=k, timestamp=start+k, origin=k,
                    reopened=False, options=[dict(index=3, original='x', trimmed='x')],
                    handling=label, handling_usable=True, handling_exclusion=None))
            displays.append(dict(displays[-1], ordinal=4, timestamp=start+4, reopened=True))
            displays.append(dict(ordinal=5, timestamp=start+5, origin=5,
                reopened=False, options=[], handling=None, handling_usable=False,
                handling_exclusion='no options', empty_display_event=True))
            units[sid] = dict(session=sid, writer=writer, prompt='p', start=start,
                end=start+10, displays=displays, typed_inserted_characters=0)
    # No observed choices is not four zero-valued observed shares.
    units['b-00']['displays'] = []
    # Touching sessions must not become strict history in either direction.
    units['a-00']['end'] = units['a-01']['start']
    split = dict(seed=m.SEED, writers={'a': 'discovery', 'b': 'test'}, session_counts={'a': 12, 'b': 11})
    census = exposure_census(list(units.values()), split)
    return dict(units=units, census=census, split=split)


def assembled(f):
    rows = [m.session_counts(f['units'][r['session']], r) for r in f['census']['roster']]
    return m.assemble(rows, f['census'], f['split'], False)


def test_four_classes_repeat_unknown_zero_and_threshold():
    result = assembled(fixture()); summary = result['summary']
    assert summary['sessions'] == 23 and summary['eligible_writers'] == 1
    assert summary['sessions_of_eligible_writers'] == 12
    assert summary['known_menus'] == 88 and summary['unknown_menus'] == 22
    assert summary['reopened_displays'] == 22
    assert summary['sessions_without_observed_choices'] == 1
    assert result['rows'][0]['counts'] == dict.fromkeys(m.CLASSES, 1)
    assert not summary['scientific_admission'] and not summary['forecasts_computed']


def test_strict_prior_never_invents_touching_order():
    rows = {r['session']: r for r in assembled(fixture())['rows']}
    assert rows['a-01']['strict_prior_sessions'] == []
    assert rows['a-01']['overlapping_or_touching_sessions'] == ['a-00']
    assert rows['a-02']['strict_prior_sessions'] == ['a-00', 'a-01']


def test_empty_reopen_keeps_canonical_label_but_no_extra_choice():
    f = fixture(); d = f['units']['a-00']['displays'][4]
    d.update(options=[], empty_display_event=True)
    assert assembled(f)['summary']['known_menus'] == 88


def test_orphan_empty_reopen_no_invented_menu():
    f = fixture(); u = f['units']['b-00']
    u['displays'] = [dict(ordinal=0, timestamp=0, origin=None, reopened=True,
        options=[], handling=None, handling_usable=False, handling_exclusion='no original',
        empty_display_event=True, unanchored_display_event=True)]
    f['census'] = exposure_census(list(f['units'].values()), f['split'])
    result = assembled(f)
    assert result['summary']['unanchored_reopens'] == 1
    assert result['summary']['original_menus'] == 110


@pytest.mark.parametrize('kind', ['unknown_label', 'reopen_label', 'option_schema', 'clock', 'ordinal', 'empty_usable'])
def test_bad_source_refuses(kind):
    f = fixture(); ds = f['units']['a-00']['displays']
    if kind == 'unknown_label': ds[0]['handling'] = 'acceptance'
    if kind == 'reopen_label': ds[4]['handling'] = 'accept'
    if kind == 'option_schema': ds[0]['options'] = ['x']
    if kind == 'clock': ds[2]['timestamp'] = -1
    if kind == 'ordinal': ds[2]['ordinal'] = 1
    if kind == 'empty_usable': ds[0]['options'] = []
    with pytest.raises(ValueError): assembled(f)


@pytest.mark.parametrize('kind', ['split', 'coverage', 'chronology', 'aggregate'])
def test_changed_census_refuses(kind):
    f = fixture()
    if kind == 'split': f['split']['session_counts']['a'] = 13
    if kind == 'coverage': f['census']['roster'].append(copy.deepcopy(f['census']['roster'][0]))
    if kind == 'chronology': f['census']['roster'][1]['strict_prior_sessions'] = ['a-00']
    if kind == 'aggregate': f['census']['summary']['unique_menus'] += 1
    with pytest.raises(ValueError): assembled(f)


def test_actual_producer_fixture_schema():
    import runpy
    from pathlib import Path
    source_fixture = runpy.run_path(str(Path(__file__).with_name('test_week3_tr3_inputs.py')))['fixture']
    from runners.drive.cards.week3_tr3_inputs import prepare
    f = source_fixture()
    rows = [prepare(**r) for r in f['sessions']]
    census = exposure_census(rows, f['split'])
    result = m.assemble([m.session_counts(u, r) for u, r in zip(rows, census['roster'])], census, f['split'], False)
    assert result['summary']['sessions'] == 4


def test_full_handler_replay_reentry_and_tamper(tmp_path):
    path = tmp_path/'fixture.json'; path.write_text(json.dumps(fixture()), encoding='utf8')
    inputs = {'fixture': str(path)}; config = dict(mode='constructed', seed=m.SEED)
    out = tmp_path/'new-output'
    m.execute(out, inputs, config)
    before = {p.name: p.read_bytes() for p in out.glob('*.json') if p.name != 'PROGRESS.json'}
    assert m.verify(out, inputs, config)['complete_input_replay']
    m.execute(out, inputs, config)
    assert before == {p.name: p.read_bytes() for p in out.glob('*.json') if p.name != 'PROGRESS.json'}
    data = json.loads((out/'CENSUS.json').read_text()); data['rows'][0]['counts']['accept'] += 1
    (out/'CENSUS.json').write_text(json.dumps(data), encoding='utf8')
    with pytest.raises(ValueError, match='replay differs'): m.verify(out, inputs, config)
