"""Complete D7 core fixtures and native replay; no human data."""
import copy
from pathlib import Path
import numpy as np
import pytest
from runners.drive.cards import week3_d7_models as m
from runners.stage14.common import read,freeze,filehash


def check_core():
    results={}
    for dose in (-.8,0.,.8):
        groups=m.writers(m.world(writers=4,dose=dose))
        values=[m.compare(rows,'duration','elapsed') for rows in groups.values()]
        if dose:assert np.mean([v['gain'] for v in values])>.025
        results[str(dose)]=values
    for rows in m.writers(m.world(writers=2)).values():
        y=m.label_array(rows);y[:,0]=2.;y[:,1]=1.
        for response in m.RESPONSES:
            for cost in m.COSTS:
                v=m.compare(rows,response,cost,y)
                assert v['gain']==0. and v['predictions'][0]==v['predictions'][1]
    return results


def test_known_answers():check_core()


@pytest.mark.parametrize('response',m.RESPONSES)
def test_no_test_response_leak(response):
    rows=m.world(writers=1);groups,_=m.partition(rows);labels=m.label_array(rows)
    before=m.compare(rows,response,'elapsed',labels)
    labels[groups[2],m.RESPONSES.index(response)]=3. if response=='duration' else 1-labels[groups[2],1]
    after=m.compare(rows,response,'elapsed',labels)
    assert before['fits']==after['fits'] and before['predictions']==after['predictions']


def test_binary_half_brier_and_session_weights():
    rows=m.world(writers=1);v=m.compare(rows,'acceptance','elapsed')
    p=np.array(v['predictions'][0]);y=np.array(v['test_truth']);w=np.array(v['weight'])
    assert v['losses'][0]==pytest.approx(w@(.5*((p-y)**2+((1-p)-(1-y))**2)))
    bykey={r['key']:r for r in rows};sums={}
    for k,weight in zip(v['test_keys'],w):
        s=bykey[k]['session'];sums[s]=sums.get(s,0)+weight
    assert max(sums.values())-min(sums.values())<1e-12


def test_censoring_and_bad_support():
    rows=m.world(writers=1);rows[0]['dwell_observed']=False
    g,r=m.partition(rows);assert r is None and 0 not in g[0]
    assert m.partition(m.world(writers=1,sessions=4))[1]=='session_support'
    for row in rows:
        if row['session']=='0:5':row['session_end']=9999999
    assert m.partition(rows)[1]=='overlapping_time_ranges'
    with pytest.raises(ValueError):m.partition(rows+[rows[0]])


def test_training_transform_and_constant_unknown_prompt():
    rows=m.world(writers=1);g,_=m.partition(rows);labels=m.label_array(rows)
    x=m.features(rows,g[0],'duration','elapsed',True,labels)
    changed=copy.deepcopy(rows)
    for i in g[2]:changed[i]['prompt']='unseen';changed[i]['mean_novelty']=999.
    z=m.features(changed,g[0],'duration','elapsed',True,labels)
    assert np.array_equal(x[g[0]],z[g[0]])
    assert np.isfinite(z).all()


def execute(output,inputs,config):
    if config!={'card':'D7-models-constructed','schema':1}:raise ValueError('Config changed')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    result=check_core();freeze(output/'RESULT.json',result)
    return dict(status='complete',constructed=True)


def verify(output,inputs,config):
    if config!={'card':'D7-models-constructed','schema':1}:raise ValueError('Config changed')
    if read(Path(output)/'RESULT.json')!=check_core():raise ValueError('Fresh fitting replay differs')
    return dict(verified=True,constructed=True,full_fresh_fit_replay=True)


def test_actual_handler_reentry_and_tamper(tmp_path):
    cfg={'card':'D7-models-constructed','schema':1}
    execute(tmp_path,{},cfg);first=filehash(tmp_path/'RESULT.json')
    execute(tmp_path,{},cfg);assert first==filehash(tmp_path/'RESULT.json')
    assert verify(tmp_path,{},cfg)['full_fresh_fit_replay']
    (tmp_path/'RESULT.json').write_text('{}')
    with pytest.raises(ValueError):verify(tmp_path,{},cfg)
