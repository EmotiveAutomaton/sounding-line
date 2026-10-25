import copy
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from runners.drive.cards import week3_trust_analysis as w
from runners.drive.cards import week3_trust_learners as learners
from runners.drive.cards.timing_census import write


def window(drop):
    return dict(acceptance_before=.6+drop/2,acceptance_after=.6-drop/2,
                request_rate_before=1+drop/2,request_rate_after=1-drop/2)


def fixture(effect=.4):
    pairs=[];sessions=[]
    for i in range(24):
        writer='w'+str(i)
        for j,bin_ in enumerate(('short','short','long','long')):
            delta=effect if bin_=='long' else 0
            pairs.append(dict(writer=writer,run_bin=bin_,failure=dict(window=window(.1+delta),strict_retyped=True),
                              controls=[dict(window=window(.1))]))
            temp=.2+j*.2
            menu=[dict(handling='accept' if (k+j)%3 else 'dismiss',censored=False,temperature=temp,origin=k,resolution=k) for k in range(10)]
            sessions.append(dict(writer=writer,session=writer+':'+str(j),timestamp=j,menu=menu))
    return dict(pairs=pairs,sessions=sessions,run_median=2,summary=dict(support=True,constructed=True))


def test_matched_regression_cancels_and_direction_reverses():
    positive=w.compare(w.paired_rows(fixture()),np.random.default_rng(20261026),200,200)
    null=w.compare(w.paired_rows(fixture(0)),np.random.default_rng(20261026),200,200)
    reverse=w.compare(w.paired_rows(fixture(-.4)),np.random.default_rng(20261026),200,200)
    assert positive['ci95'][0]>0 and positive['reference']['one_sided_p']<.05
    assert null['ci95']==[0,0]
    assert reverse['ci95'][1]<0


def test_prospective_learners_predict_before_update_and_keep_all_runs():
    model=learners.ChangePoint(.1)
    assert model.predict()==.5
    model.update(1)
    assert model.predict()==pytest.approx(.1*.5+.9*2/3)
    for _ in range(20):model.update(0)
    assert len(model.weights)==22 and model.weights.sum()==pytest.approx(1)
    assert learners.score(learners.Adaptive(.05,.5),[1])==pytest.approx(np.log(.5))


def test_shifting_handling_rewards_online_learners_on_unseen_choices():
    result=learners.fit([0]*80+[1]*80,[1]*40)
    assert result['adaptive_log_likelihood']>result['fixed_log_likelihood']
    assert result['changepoint_log_likelihood']>result['fixed_log_likelihood']
    original=learners.fit([0]*80+[1]*80,[0]*40)
    assert original['frozen_training_selection']==result['frozen_training_selection']


def test_whole_session_holdout_and_missing_settings_are_explicit():
    data=fixture();fit=learners.by_writer(data['sessions'])
    assert len(fit['rows'])==24
    for row in fit['rows']:
        assert not set(row['training_sessions'])&set(row['heldout_sessions'])
        assert len(row['training_sessions'])==3 and len(row['heldout_sessions'])==1
    for session in data['sessions']:
        for m in session['menu']:m['temperature']=None
    assert w.temperature(data['sessions'],np.random.default_rng(1),20)['state']=='unsupported_missing_settings'


def test_complete_constructed_handler_and_fresh_native_replay(tmp_path):
    path=tmp_path/'fixture.json';write(path,fixture());inputs={'fixture':str(path)};output=tmp_path/'out'
    result=w.execute(output,inputs,w.CONSTRUCTED)
    assert result['state']=='positive' and result['constructed_only'] and not result['scientific_admission']
    manifest=tmp_path/'manifest.json';write(manifest,dict(output=str(output),inputs=inputs,config=w.CONSTRUCTED))
    script="import json,sys;from runners.drive.cards.week3_trust_analysis import verify;x=json.load(open(sys.argv[1]));assert verify(x['output'],x['inputs'],x['config'])['verified']"
    subprocess.run([sys.executable,'-X','utf8','-B','-c',script,str(manifest)],check=True,timeout=60)
    path.write_text(path.read_text()+' ',encoding='utf8')
    with pytest.raises(ValueError,match='replay differs'):w.verify(output,inputs,w.CONSTRUCTED)


def test_unsupported_is_not_null_and_partial_cannot_be_science(tmp_path):
    data=fixture();data['summary']['support']=False;path=tmp_path/'fixture.json';write(path,data)
    assert w.execute(tmp_path/'out',{'fixture':str(path)},w.CONSTRUCTED)['state']=='unsupported'
    with pytest.raises(ValueError,match='verified complete'):w.execute(tmp_path/'bad',{'fixture':str(path)},w.CONFIG)
