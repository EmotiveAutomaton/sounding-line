import numpy as np
import pandas as pd
import pytest
from runners.drive.cards import week7_answered_v1 as paired


def clock():
    times = ['00:10','00:40','01:10','02:10','06:10','00:15']
    stamps = ['2026-01-'+('02' if i==5 else '01')+'T'+t+':00Z' for i,t in enumerate(times)]
    return pd.DataFrame(dict(id=['a']*6,day=[1]*5+[2],created_esm=stamps,ended_esm=stamps))


def test_clock_distribution():
    timestamps, report = paired.chronology(clock().sample(frac=1,random_state=1))
    assert report['all_pairs']==4 and report['short_pairs']==3
    assert report['gap_minutes']['median']==45 and report['cap_minutes']==90
    assert timestamps.gap.dropna().tolist()==[30,30,60,240]
    assert timestamps.block.tolist()==[0,0,0,0,1,0]
    assert np.isnan(timestamps.gap.iloc[-1])


@pytest.mark.parametrize(('field','value'),[
    ('created_esm',None),('ended_esm','broken'),('created_esm','2026-01-01T03:00:00Z'),
    ('ended_esm','2026-01-01T00:40:00Z'),('day',4)])
def test_invalid_clock_holds_whole_person(field,value):
    source=clock()
    source.loc[0,field]=value
    _,report=paired.chronology(source)
    assert report['all_pairs']==0 and report['clock_excluded_people']==1


@pytest.mark.parametrize(('m','s','expected'),[
    ((1,[.2,1.2]),(1,[0,2]),'undecided'),
    ((1,[-1,2]),(-1,[-2,1]),'undecided'),
    ((1,[.2,2]),(2,[1,3]),'consistent'),
    ((1,[.2,2]),(None,None),'undecided')])
def test_disagreement(m,s,expected):
    def metric(pair):
        return dict(estimate=pair[0],interval=pair[1])
    assert paired.reading(metric(m),metric(s))==expected


@pytest.mark.parametrize('card',paired.CARDS)
def test_paired_fit(card):
    rng=np.random.default_rng(22)
    source=pd.concat([clock().assign(id=str(i)) for i in range(100)],ignore_index=True)
    for col in sorted(set(paired.columns(card))-set(paired.CLOCKS)):
        source[col]=rng.integers(1,3 if col=='interaction' else 7,len(source))
    source.loc[0:1,'interaction']=np.nan
    timing,support=paired.chronology(source)
    def rows(replay):
        panel=paired.prepare(card,source,timing,support,replay)
        if card=='ISO1':
            assert panel.metadata['all']['model_pairs']==398
        return paired.evaluate(panel,None,lambda:None,verify=replay)
    a,b=rows(False),rows(True)
    assert a.keys()==b.keys() and any(v is not None for v in a.values())
    for k in a:
        if a[k] is None: assert b[k] is None
        else: assert a[k]==pytest.approx(b[k],abs=1e-10)
