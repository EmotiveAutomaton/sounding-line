"""Public-only rival preserves ambiguity and distinguishes net textual evidence."""
from runners.stage11_1 import cheap,models
from runners.stage11_1.targets import project,public
from runners.stage11.run import fixture
from runners.stage11.replay import replay
import json


def rows():
    out=[]
    for i in range(2):
        raw=fixture(i==0);e=replay(raw)['events'][0]
        out.append(dict(writer=str(i),target=project(e,raw),views={v:public(e,v) for v in models.VIEWS}))
    return out


def test_equifinal_history_forecasts_identical_and_valid():
    rs=rows();fit=cheap.fit(rs)
    a,detail=cheap.predict(rs[0]['views']['alternatives'],fit)
    b,_=cheap.predict(rs[1]['views']['alternatives'],fit)
    assert a==b and detail['signal']['literal_offer_retained']
    assert len(detail['compatible_histories'])==4 and all(0<w<1 for w in a['handling'])
    models.parse(dict(done=True,done_reason='stop',message=dict(content=json.dumps(a))),rs[0]['views']['alternatives'],'direct')


def test_private_truth_mutation_cannot_change_public_rival():
    rs=rows();fit=cheap.fit(rs);e=rs[0]['views']['alternatives'];a=cheap.predict(e,fit)
    rs[0]['target']['handling']='ignore'
    assert cheap.predict(e,fit)==a
    f,d=cheap.predict(rs[0]['views']['artifact'],fit)
    assert d['signal']=='artifact marginal only' and f['handling']==fit['handling']
