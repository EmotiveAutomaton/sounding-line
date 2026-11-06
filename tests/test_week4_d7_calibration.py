import copy
from collections import Counter
import numpy as np
import pytest
from runners.drive.cards import week4_d7_calibration as c


def test_sessions_remain_whole_and_prompt_counts_preserved():
    rows,_=c.world('null',20261026,6);a=c.session_assignment(rows,0,20261026)
    assert a==c.session_assignment(rows[::-1],0,20261026)
    before={(r['session'],r['prompt'],r['writer']) for r in rows}
    after={(r['session'],r['prompt'],a[r['session']]) for r in rows}
    assert Counter((p,w) for s,p,w in before)==Counter((p,w) for s,p,w in after)
    assert c.audit_bank(rows,5,20261026)['valid']


def test_joint_reference_preserves_pairs_and_unobserved_rows():
    rows,_=c.world('signed',20261026,6);unit=c.m.writers(rows)['0'];unit[0]['dwell_observed']=False
    original=c.m.label_array(unit);changed=c.joint_labels(unit,1,20261026,0)
    assert np.array_equal(original[0],changed[0])
    assert sorted(map(tuple,original[1:]))==sorted(map(tuple,changed[1:]))


def test_complete_writer_bootstrap_equivalent_to_refitting_copies():
    rows,_=c.world('signed',20261026,6);groups,_=c.support(rows)
    values=[c.m.compare(groups[w],'duration','elapsed')['gain'] for w in sorted(groups)]
    ix=[0,2,2,5,1,0];refits=[]
    for j,i in enumerate(ix):
        copied=[dict(r,writer='copy'+str(j)) for r in groups[str(i)]]
        refits.append(c.m.compare(copied,'duration','elapsed')['gain'])
    assert refits==[values[i] for i in ix]


def test_support_change_stops_before_any_fit(monkeypatch):
    rows,_=c.world('null',20261026,6)
    monkeypatch.setattr(c,'audit_bank',lambda *a,**kw:dict(valid=False,draws=[{'same_supported_writers':False}]))
    monkeypatch.setattr(c,'fits',lambda *a,**kw:(_ for _ in ()).throw(AssertionError('must not fit')))
    result,_=c.analyze(rows,c.configuration('constructed'),20261026)
    assert result['state']=='invalid'


def test_exact_constant_null_is_not_positive():
    rows,_=c.world('null',20261026,6)
    for r in rows:r['dwell_seconds']=2.;r['accepted']=False
    result,_=c.analyze(rows,c.configuration('constructed'),20261026)
    s=result['summaries'][c.PRIMARY]
    assert s['gain']==s['ci_low']==s['ci_high']==0 and not s['positive']


def test_missing_reference_writer_refused():
    result={'a':{},'b':{},'c':{}}
    with pytest.raises(ValueError,match='fixed reference roster'):
        c.summarize(result,[{'a':{}}],[],20,7)


def test_signed_worlds_preserve_covariates():
    positive,dose=c.world('signed',20261026,6,0);negative,other=c.world('signed',20261026,6,1)
    assert dose==.8 and other==-.8
    for a,b in zip(positive,negative):
        assert {k:v for k,v in a.items() if k!='dwell_seconds'}=={k:v for k,v in b.items() if k!='dwell_seconds'}


def test_full_handler_replay_and_altered_checkpoint(tmp_path):
    cfg=c.configuration('constructed');c.execute(tmp_path,{},cfg)
    assert c.verify(tmp_path,{},cfg)['full_fresh_fit_replay']
    path=tmp_path/'null-20261026.json';original=c.read(path);original['dose']=1.
    c.atomic(path,original)
    with pytest.raises(ValueError,match='fitted world differs'):
        c.verify(tmp_path,{},cfg)
