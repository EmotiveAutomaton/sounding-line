"""WC2 null, topic, direction/wording routes and complete replay checks."""
import copy
import json

import numpy as np
import pytest

from runners.drive.cards import week3_failed_means as card


def payload(kind='new_means'):
    events=[];vectors={};basis=np.eye(3)
    for w in range(8):
        for s in range(4):
            chosen=f'old wording anchor w{w} p{s}';other=f'other option w{w} p{s}'
            context=f'neutral topic context w{w} p{s}';own=f'fresh means language w{w} p{s}'
            if kind=='wording':own=chosen
            vectors[chosen]=basis[0].tolist();vectors[other]=basis[1].tolist()
            vectors[context]=basis[2].tolist()
            vectors[own]=(basis[0] if kind in ('new_means','wording','topic') else basis[1] if kind=='reverse' else basis[2]).tolist()
            if kind=='topic':vectors[context]=basis[0].tolist()
            event=dict(id=f'w{w}s{s}',writer=f'w{w}',session=f'w{w}s{s}',prompt=f'p{s}',timestamp=s,
                kind='deleted',span=dict(text=chosen,unchosen=[other]),window=dict(text=own),
                context=[dict(text=context,writer='external',prompt=f'p{s}')],
                sensitivity=None,sensitivity_context=[],kept_reference=None)
            events.append(event)
    return dict(data=dict(events=events),vectors=vectors)


@pytest.mark.parametrize('kind,route',[('new_means','same end, new means'),('wording','lingering taste'),
                                     ('null','no direction'),('topic','no direction'),('reverse','moves away')])
def test_known_answer_routes(kind,route):
    p=payload(kind);r,d=card.analyze(p['data'],p['vectors'],card.CONSTRUCTED)
    assert r['route']==route and r['events']==32 and r['writers']==8
    assert r['persistence_ratio']['state']=='unresolved'


def test_positive_but_phrase_interval_crosses_band_is_unresolved():
    assert card.route(dict(interval=[.1,.2]),dict(interval=[-.2,.4]),.1)=='unresolved'
    assert card.route(dict(interval=[.1,.2]),dict(interval=[.1,.2]),.1)=='unresolved'
    assert card.route(dict(interval=[0,.2]),dict(interval=[0,0]),0)=='no direction'


def test_phrase_matches_occurrences_and_separates_wording_from_content():
    assert card.overlap('the cat ate the cat','the cat')==pytest.approx(2/7)
    assert card.content_overlap('cat under moon','moon and cat')==pytest.approx(2/3)
    assert card.overlap('cat moon','moon cat')==0


def test_band_uses_only_context_and_widens_at_low_writer_support():
    rows=[dict(writer=str(i),context_phrase=i/100) for i in range(25)]
    band=card.frozen_band(rows)
    assert band['widened'] and band['band']==band['projected_halfwidth90']
    assert not card.frozen_band([dict(writer=str(i),context_phrase=i/100) for i in range(100)])['widened']


def test_same_context_writer_or_repeated_donor_refuses():
    p=payload();e=p['data']['events'][0];e['context'][0]['writer']=e['writer']
    with pytest.raises(ValueError,match='contamination'):card.contrast(e,p['vectors'])
    p=payload();e=p['data']['events'][0];e['context']*=2
    with pytest.raises(ValueError,match='repeated'):card.contrast(e,p['vectors'])


def test_missing_support_is_not_zero_scored():
    p=payload();p['data']['events']=p['data']['events'][:2]
    result,detail=card.analyze(p['data'],{},card.CONSTRUCTED)
    assert result['state']=='unsupported' and not result['scientific_admission'] and detail['rows']==[]


def test_ratio_requires_paired_positive_denominator_and_uses_same_writers():
    p=payload();extra=[]
    for e in p['data']['events']:
        kept=copy.deepcopy(e);kept['id']+='-kept';kept['kind']='kept'
        e['kept_reference']=dict(id=kept['id']);extra.append(kept)
    p['data']['events']+=extra
    result,_=card.analyze(p['data'],p['vectors'],card.CONSTRUCTED)
    assert result['persistence_ratio']['estimate']==1
    assert result['persistence_ratio']['ci95']==[1,1]


def test_full_execute_reentry_fresh_verify_and_tamper(tmp_path):
    f=tmp_path/'fixture.json';f.write_text(json.dumps(payload()),encoding='utf8')
    out=tmp_path/'out';inputs={'fixture':str(f)}
    assert card.execute(out,inputs,card.CONSTRUCTED)['status']=='complete'
    assert card.execute(out,inputs,card.CONSTRUCTED)['status']=='complete'
    assert card.verify(out,inputs,card.CONSTRUCTED)['verified']
    p=json.loads((out/'SUMMARY.json').read_text());p['route']='wrong'
    (out/'SUMMARY.json').write_text(json.dumps(p),encoding='utf8')
    with pytest.raises(ValueError,match='replay differs'):card.verify(out,inputs,card.CONSTRUCTED)
