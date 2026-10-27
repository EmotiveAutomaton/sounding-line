import copy
import pytest
from tests.test_week3_tr3_inputs import fixture
from runners.drive.cards import week3_tr3_inputs_recovery as first
from runners.drive.cards import week3_tr3_inputs_recovery2 as second


def orphan_fixture():
    f=fixture()
    r=f['sessions'][0]
    r['events'].insert(1,dict(eventName='suggestion-reopen',eventTimestamp=r['meta']['timestamp']+.5,currentSuggestions=[]))
    r['canonical']['events'][0]['ordinal']+=1
    r['events'][3]['currentSuggestions']=[]
    return f


def test_orphan_is_retained_with_no_invented_origin_or_offer():
    r=orphan_fixture()['sessions'][0]
    with pytest.raises(ValueError):first.prepare(**r)
    out=second.prepare(**r)
    d=out['displays'][0]
    assert d['ordinal']==1 and d['origin'] is None and d['options']==[] and d['handling'] is None
    assert out['typed_inserted_characters']==2 and len(out['displays'])==3
    assert out['displays'][1]['origin']==2 and out['displays'][2]['options']==[]


def test_nonempty_orphan_still_fails():
    r=orphan_fixture()['sessions'][0];r['events'][1]['currentSuggestions']=r['canonical']['events'][0]['options']
    with pytest.raises(ValueError):second.prepare(**r)


def test_all_prior_representable_units_identical():
    for f in fixture()['sessions']:
        assert second.prepare(**f)==first.prepare(**f)
        f['events'][2]['currentSuggestions']=[]
        assert second.prepare(**f)==first.prepare(**f)
