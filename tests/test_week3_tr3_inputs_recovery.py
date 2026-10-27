import copy
import pytest
from tests.test_week3_tr3_inputs import fixture
from runners.drive.cards import week3_tr3_inputs as original
from runners.drive.cards import week3_tr3_inputs_recovery as recovery


def test_valid_units_identical():
    for f in fixture()['sessions']:assert recovery.prepare(**f)==original.prepare(**f)


def test_empty_reopen_retained_without_offer():
    f=fixture()['sessions'][0];f['events'][2]['currentSuggestions']=[]
    with pytest.raises(ValueError):original.prepare(**f)
    r=recovery.prepare(**f)
    assert len(r['displays'])==2
    assert r['displays'][1]['options']==[] and r['displays'][1]['empty_display_event']
    assert r['typed_inserted_characters']==2
    assert r['displays'][0]['options']==f['canonical']['events'][0]['options']


def test_empty_open_retained_only_with_explicit_canonical_exclusion():
    f=fixture()['sessions'][0]
    for i in [1,2]:f['events'][i]['currentSuggestions']=[]
    f['canonical']['events'][0]['options']=[]
    r=recovery.prepare(**f)
    assert all(d['options']==[] for d in r['displays'])
    f['canonical']['events'][0]['usable']=True
    with pytest.raises(ValueError):recovery.prepare(**f)


def test_malformed_reopen_not_silently_emptied():
    f=fixture()['sessions'][0];f['events'][2]['currentSuggestions']=None
    with pytest.raises(ValueError):recovery.prepare(**f)
