import copy
import json

import pytest
from runners.drive.cards import week3_tr3_outcome_inputs as m


def unit(session='a', writer='writer-a'):
    first = [dict(index=17, original='Alpha alpha', trimmed='Alpha alpha'),
             dict(index=3, original='Beta', trimmed='Beta')]
    second = [dict(index=9, original='Alpha beta', trimmed='Alpha beta')]
    rows = [dict(ordinal=1, options=first, usable=True, decision='accept', selected_index=17,
                 matched_option_indices=[3], verified_insertion=True, exclusion=None),
            dict(ordinal=2, options=second, usable=True, decision='dismiss', selected_index=None,
                 matched_option_indices=[], verified_insertion=False, exclusion=None)]
    displays = [dict(ordinal=r['ordinal'],origin=r['ordinal'],reopened=False, options=r['options'],
                     handling=r['decision'], handling_usable=r['usable']) for r in rows]
    displays.append(dict(ordinal=3,origin=2,reopened=True,options=second))
    exposure = dict(session=session,writer=writer,prompt='p',start=0,end=10,displays=displays)
    typing = dict(session=session,writer=writer,prompt='p',initial_document='',final_document='Alpha ',
        user_inserted_characters=6,edits=[dict(ordinal=1,timestamp=1,source='user',operations=[dict(insert='Alpha ')])])
    human = dict(session=session,writer=writer,prompt='p',typed_characters=6,feature_counts={'w1:alpha':1})
    canonical = dict(usable=True,reconstructed=True,errors=[],events=rows)
    return dict(exposure=exposure,typing=typing,human=human,canonical=canonical)


def fixture():
    units = {'a':unit(), 'b':unit('b','writer-b')}
    roster = [dict(session=sid,writer=u['exposure']['writer'],prompt='p',half='discovery' if sid=='a' else 'test',
                   start=0,end=10,typed_inserted_characters=6) for sid,u in units.items()]
    return dict(units=units,census=dict(roster=roster),
        split=dict(seed=20261026,writers={'writer-a':'discovery','writer-b':'test'},session_counts={'writer-a':1,'writer-b':1}),
        selection=dict(features=[dict(feature='w1:alpha'),dict(feature='w1:beta')]))


def test_actual_insertion_wins_over_wrong_logged_index_and_reopens():
    u=unit(); result=m.offer_counts(u['exposure'],u['canonical'],{'w1:alpha','w1:beta'})
    assert result['counts']=={'w1:alpha':{'shown':2,'other':1,'dismissed':1},
                              'w1:beta':{'shown':2,'accepted':1,'dismissed':1}}
    assert result['support']==dict(menus=2,empty_menus=0,reopens=1,alternatives=3)


def test_unknown_and_empty_retained():
    u=unit(); row=u['canonical']['events'][0]; row['usable']=False
    u['exposure']['displays'][0].update(handling_usable=False,handling=None)
    result=m.offer_counts(u['exposure'],u['canonical'],{'w1:alpha'})
    assert result['counts']['w1:alpha']==dict(shown=2,unknown=1,dismissed=1)
    for row in u['canonical']['events']:row.update(options=[],usable=False)
    for display in u['exposure']['displays'][:2]:display.update(options=[],handling=None,handling_usable=False)
    assert m.offer_counts(u['exposure'],u['canonical'],{'w1:alpha'})['counts']=={}


@pytest.mark.parametrize('fault',['duplicate','missing','options','handling','accepted','verified'])
def test_changed_canonical_source_refuses(fault):
    u=unit()
    if fault=='duplicate':u['canonical']['events'].append(u['canonical']['events'][0])
    elif fault=='missing':u['exposure']['displays']=u['exposure']['displays'][1:]
    elif fault=='options':u['exposure']['displays'][0]['options']=[]
    elif fault=='handling':u['exposure']['displays'][0]['handling']='ignore'
    elif fault=='accepted':u['canonical']['events'][0]['matched_option_indices']=[999]
    else:u['canonical']['events'][0]['verified_insertion']=False
    with pytest.raises(ValueError):m.offer_counts(u['exposure'],u['canonical'],{'w1:alpha'})


def test_identity_denominator_and_selected_filter():
    f=fixture();r=f['census']['roster'][0];u=f['units']['a']
    out=m.prepare(r,u['exposure'],u['human'],u['canonical'],{'w1:beta'})
    assert out['human_counts']=={} and set(out['offers'])=={'w1:beta'}
    u['human']['typed_characters']=7
    with pytest.raises(ValueError,match='denominator'):m.prepare(r,u['exposure'],u['human'],u['canonical'],set())
    u['human']['writer']='wrong'
    with pytest.raises(ValueError,match='identity'):m.prepare(r,u['exposure'],u['human'],u['canonical'],set())


def test_full_handler_reuses_discovery_and_replays_test_typing(tmp_path):
    f=fixture();del f['units']['a']['typing'];del f['units']['b']['human']
    path=tmp_path/'fixture.json';path.write_text(json.dumps(f),encoding='utf8')
    out=tmp_path/'output';inputs=dict(fixture=str(path));config=dict(mode='constructed',seed=20261026)
    m.execute(out,inputs,config)
    before={p.relative_to(out).as_posix():p.read_bytes() for p in out.rglob('*') if p.is_file() and p.name!='PROGRESS.json'}
    assert m.verify(out,inputs,config)['complete_outcome_input_replay']
    m.execute(out,inputs,config)
    assert before=={p.relative_to(out).as_posix():p.read_bytes() for p in out.rglob('*') if p.is_file() and p.name!='PROGRESS.json'}
    s=json.loads((out/'SUMMARY.json').read_text());assert s['test_counts_computed']==s['discovery_counts_reused']==1
    (out/'SUMMARY.json').write_text('{}')
    with pytest.raises(ValueError,match='aggregate replay'):m.verify(out,inputs,config)
