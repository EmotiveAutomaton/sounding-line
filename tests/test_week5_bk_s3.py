from copy import deepcopy
import numpy as np
from runners.drive.cards import week5_bk_s3_source as source,week5_bk_s3_encode as encoder,week5_bk_s3_analysis as analysis
from runners.drive.cards.week5_bk_s3_fixture import events_fixture,world

def test_source_intime_context_and_exact_matching():
    events=events_fixture();rows,counts=source.materialize(events,source.prior.extract(events))
    pairs=source.match([dict(r,session='session',writer='writer') for r in rows])
    assert len(pairs)==1 and pairs[0][0]['size']==pairs[0][1]['size']==5
    for a,b in pairs:
        assert a['nonlocal_edit'] and not b['nonlocal_edit']
        assert all('Future words' not in t['rest_before'] for r in (a,b) for t in r['targets'])

def test_unicode_codepoint_size_and_both_replacement_orders():
    doc=source.units('Cat 😀 sits. More text.');ids=[('typed',0,i) for i in range(len(doc))]
    for ops in [[{'retain':4},{'insert':'fox'},{'delete':2}],[{'retain':4},{'delete':2},{'insert':'fox'}]]:
        after,_,bounds,size=source.transform(doc,ids,ops,1,True)
        assert source.text_of(after)=='Cat fox sits. More text.' and size==4
        assert source.text_of(after[bounds[4]:bounds[6]])=='fox'

def test_whole_sentence_delete_and_small_edits_counted():
    events=events_fixture();events=events[:3]+[dict(eventName='text-change',eventTimestamp=12000,eventSource='user',textDelta={'ops':[{'retain':21},{'delete':21}]})]+[events[-1]]
    rows,counts=source.materialize(events,source.prior.extract(events))
    assert counts.get('whole_sentence_deleted',0)>=1

def test_known_cosine_difference_and_missing_context():
    row=dict(targets=[dict(before='before',after='after',rest_before='context',next_paragraph='',prompt='context',rest_final='',position=.3)],session='s',ordinal=1)
    result=encoder.score([row],{'before':[1,0],'after':[0,1],'context':[0,1]})[0]
    assert result['scores']['primary']==1 and result['scores']['next_paragraph'] is None

def test_signed_null_and_below_floor():
    for sign in (-1,0,1):
        assert abs(analysis.fit(world(sign))['effect']-.4*sign)<1e-10
    rows=[r for r in world(1) if r['writer']=='constructed-0']
    result=analysis.analyse(rows,draws=20,permutations=20)
    assert result['direction']=='below floor, descriptive' and result['point']['effect']>.3

def test_unidentified_contrast_is_not_a_fitted_zero():
    rows=world(1)
    for r in rows:r['position']=int(r['nonlocal_edit']);r['remaining']=0
    assert analysis.fit(rows)['effect'] is None
    assert analysis.fit(rows[:2])['effect'] is None

def test_no_local_match_and_missing_context_are_explicit():
    rows=[r for r in world(1) if r['nonlocal_edit']]
    assert analysis.analyse(rows)['status']=='below floor, descriptive'
    rows=world(1)
    for r in rows:r['scores']['next_paragraph']=None
    assert analysis.analyse(rows,'next_paragraph')['point']['reason']=='no complete matched pairs'
