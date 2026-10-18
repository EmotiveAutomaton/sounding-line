import json
import math
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from runners.drive.cards import menus_crossed_stats as c
from runners.drive.cards import menus_d15 as d
from runners.drive.cards import menus_v3 as v
from runners.drive.cards.menus_io import read,write,sha256


def balanced(writers=24,repeat=3):
    combinations=np.array([(w,p,s,r) for w in range(writers) for p in range(3) for s in range(2) for r in range(repeat)])
    return [combinations[:,0],combinations[:,1],combinations[:,2],combinations[:,0]*3+combinations[:,1]]


def test_crossed_moments_match_independent_dense_projection():
    groups=balanced(4,2);a,_=c.components(groups);n=len(groups[0]);p=np.eye(n)-np.ones((n,n))/n
    kernels=[(g[:,None]==g[None,:]).astype(float) for g in groups]+[np.eye(n)]
    expected=np.array([[np.trace(p@x@p@y) for y in kernels] for x in kernels])
    assert np.allclose(a,expected,atol=1e-10)
    with pytest.raises(ValueError,match='aliased'):
        c.fit(np.arange(n),[groups[0],groups[1],groups[2],groups[0]],d.GROUPS)


def test_independent_noise_and_planted_variance_recovery():
    groups=balanced();rng=np.random.default_rng(187);noise=[];plant=[];variances=[]
    for _ in range(30):
        error=rng.normal(size=len(groups[0]));null=c.fit(error,groups,d.GROUPS)
        noise.append(null['unconstrained'][0,0])
        y=error.copy()
        for g,variance in zip(groups,[1.,.3,.2,.4]):y+=rng.normal(0,math.sqrt(variance),size=g.max()+1)[g]
        fit=c.fit(y,groups,d.GROUPS);plant.append(c.icc(fit)[0]);variances.append(fit['unconstrained'][0,0])
    assert abs(np.mean(noise))<.04
    assert abs(np.mean(variances)-1)<.2
    assert abs(np.mean(plant)-1/2.6)<.08
    assert c.decisions_for_reliability(.2)==pytest.approx(16)
    assert c.decisions_for_reliability(0) is None


def test_handling_icc_noise_and_planted_categorical_writer_signal():
    groups=balanced(32,6);rng=np.random.default_rng(119)
    noise=rng.integers(4,size=len(groups[0]));null=c.fit(np.eye(4)[noise],groups,d.GROUPS)
    assert c.icc(null)[0]<.08
    truth=np.array([w%4 if rng.random()<.9 else rng.choice([k for k in range(4) if k!=w%4]) for w in groups[0]])
    fit=c.fit(np.eye(4)[truth],groups,d.GROUPS)
    assert .6<c.icc(fit)[0]<.9
    blup=c.blup(np.eye(4)[truth],groups,fit)
    assert np.mean(np.argmax(blup['effects'][0],axis=1)==np.arange(32)%4)>.9


def test_pair_reliability_known_directions_and_duplicate_node_exclusion():
    rng=np.random.default_rng(71);halves=[dict(valid=True,profiles={}),dict(valid=True,profiles={})]
    for w in range(18):
        fine=rng.normal(size=6).tolist()
        for half in halves:half['profiles'][str(w)]=dict(fine=fine,coarse=rng.normal(size=4).tolist())
    config=d.CONFIG|dict(bootstrap=200)
    result=d.summarize_profiles(halves,config)
    assert result['primary']['state']=='positive' and result['fine_reliability']['effect']==pytest.approx(1)
    for half in halves:
        for profile in half['profiles'].values():profile['fine'],profile['coarse']=profile['coarse'],profile['fine']
    assert d.summarize_profiles(halves,config)['primary']['state']=='negative'
    for half in halves:
        for profile in half['profiles'].values():profile['fine']=profile['coarse']
    assert d.summarize_profiles(halves,config)['primary']['state']=='null'
    matrices=[np.array([[0.,1.,3.],[1.,0.,2.],[3.,2.,0.]])]*4
    assert d.distances_from_matrices(matrices,[0,0,1,2])==(0.,1.,1.)
    assert d.distances_from_matrices(matrices,[0,0,0,1])==(None,None,None)


def fixture(tmp_path):
    root=tmp_path/'source';root.mkdir();p2=root/'p2';p2.mkdir();sessions=[];producer=[];index=[]
    rng=np.random.default_rng(143)
    for w in range(16):
        for session_number in range(6):
            sid=f'w{w}s{session_number}';prompt=f'p{session_number//2}';rows=[];decisions=[]
            for i in range(18):
                key=f'{sid}m{i}';menu=['one','two'];ordinal=i*4
                probabilities=np.full(4,.08);probabilities[w%4]+=.5;probabilities[(w+session_number//2)%4]+=.18
                action=d.ACTIONS[int(rng.choice(4,p=probabilities))]
                rows.append(dict(key=key,writer=f'w{w}',session=sid,ordinal=ordinal,menu=menu,
                                 handling=action,inserted=menu[i%2],prompt=prompt))
                settings={k:float(i%2) for k in d.SETTINGS};settings[d.SETTINGS[-1]]=None if i%7==0 else float(i%2)
                for j in range(2):producer.append(dict(key=key,writer=f'w{w}',session=sid,ordinal=ordinal,
                    position=j,suggestion_index=j,logged_score=float(j-1),decoding_numeric=settings))
                decisions.append(dict(key=key,ordinal=ordinal,handling=action,latency_kind='observed_selection_or_close',
                    latency_seconds=float(rng.uniform(.1,5)*(w+1)),typed_since_previous_decision=int(rng.integers(1,20)),
                    interactions=[dict(event='suggestion-hover')]*(i%3)))
            sessions.append(dict(writer=f'w{w}',session=sid,timestamp=session_number,prompt=prompt,rows=rows))
            path=p2/(sid+'.json');write(path,dict(writer=f'w{w}',session=sid,prompt=prompt,decisions=decisions))
            index.append(dict(session=sid,writer=f'w{w}',file=path.name,sha256=sha256(path)))
    write(root/'SESSIONS.json',sessions)
    (root/'SUGGESTIONS.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in producer),encoding='utf8')
    write(root/'PLAN.json',dict(pins={str((root/'SESSIONS.json').resolve()):sha256(root/'SESSIONS.json')}))
    write(root/'COMPLETE.json',dict(status='COMPLETE',outputs={n:sha256(root/n) for n in ['PLAN.json','SUGGESTIONS.jsonl']}))
    write(p2/'INDEX.json',index)
    write(p2/'PLAN.json',dict(pins={(root/'SESSIONS.json').relative_to(tmp_path).as_posix():sha256(root/'SESSIONS.json')}))
    write(p2/'COMPLETE.json',dict(status='COMPLETE',plan_sha256=sha256(p2/'PLAN.json'),outputs={'INDEX.json':sha256(p2/'INDEX.json')}))
    return dict(sessions=str(root/'SESSIONS.json'),p8=str(root/'SUGGESTIONS.jsonl'),p8_complete=str(root/'COMPLETE.json'),
        foundation_complete=str(p2/'COMPLETE.json'),foundation_plan=str(p2/'PLAN.json'),session_index=str(p2/'INDEX.json'),
        repo_root=str(tmp_path)),d.CONFIG|dict(bootstrap=80)


def make_v3(tmp_path,inputs,config):
    root=tmp_path/'D15';output=root/'output';report=d.execute(output,inputs,config)
    write(root/'PLAN.json',dict(inputs=inputs,config=config))
    write(root/'COMPLETE.json',dict(status='COMPLETE',outputs={p.relative_to(root).as_posix():sha256(p) for p in root.rglob('*') if p.is_file()}))
    return dict(d15_complete=str(root/'COMPLETE.json'),d15_summary=str(output/'SUMMARY.json'),d15_plan=str(root/'PLAN.json')),report


def test_actual_d15_serialization_source_replay_and_wrong_tuple(tmp_path):
    inputs,config=fixture(tmp_path);out=tmp_path/'output';out.mkdir();write(out/'YIELD_REQUEST.json',{})
    assert d.execute(out,inputs,config)['status']=='yielded';(out/'YIELD_REQUEST.json').unlink()
    result=d.execute(out,inputs,config)
    assert result['support']['prompts']==['p0','p1','p2']
    assert result['support']['counts']['missing_setting_decisions']>0
    assert d.execute(out,inputs,config)==result and d.verify(out,inputs,config)['source_rows_replayed']
    request=tmp_path/'REQUEST.json';write(request,dict(output=str(out),inputs=inputs,config=config))
    code='import json,sys;from runners.drive.cards.menus_d15 import verify;r=json.load(open(sys.argv[1]));assert verify(**r)["verified"]'
    subprocess.run([sys.executable,'-B','-c',code,str(request)],check=True,timeout=30,env=os.environ|dict(PYTHONHASHSEED='971'))
    path=Path(inputs['session_index']);path.write_text(path.read_text()+' ',encoding='utf8')
    with pytest.raises(ValueError,match='saved primary recomputation differs'):d.verify(out,inputs,config)


def test_actual_v3_bootstrap_refit_fresh_verification_and_resume(tmp_path):
    inputs,config=fixture(tmp_path);vinputs,parent=make_v3(tmp_path,inputs,config)
    vconfig=v.CONFIG|dict(bootstrap=30,checkpoint_draws=10);out=tmp_path/'V3';out.mkdir();write(out/'YIELD_REQUEST.json',{})
    assert v.execute(out,vinputs,vconfig)['status']=='yielded';(out/'YIELD_REQUEST.json').unlink()
    result=v.execute(out,vinputs,vconfig)
    assert result['arms']['primary']['features']['handling']['effect']>.2
    assert result['primary']==result['arms']['primary']['features']['handling']
    before={str(p):sha256(p) for p in out.rglob('*') if p.is_file()}
    assert v.execute(out,vinputs,vconfig)==result
    assert before=={str(p):sha256(p) for p in out.rglob('*') if p.is_file()}
    request=tmp_path/'VREQUEST.json';write(request,dict(output=str(out),inputs=vinputs,config=vconfig))
    code='import json,sys;from runners.drive.cards.menus_v3 import verify;r=json.load(open(sys.argv[1]));assert verify(**r)["point_refitted"]'
    subprocess.run([sys.executable,'-B','-c',code,str(request)],check=True,timeout=30,env=os.environ|dict(PYTHONHASHSEED='973'))
    path=next((out/'draws').glob('*.json'));path.write_text(path.read_text()+' ',encoding='utf8')
    with pytest.raises(ValueError,match='changed'):v.verify(out,vinputs,vconfig)


def test_zero_icc_record_requirement_and_nonidentifiable_halves():
    config=v.CONFIG|dict(bootstrap=10)
    zero=dict(icc=[0.]*len(v.FEATURES),diagnostics={})
    result=v.summarize(zero,[zero]*10,config)['primary']
    assert result['state']=='null' and result['zero_icc_means_infinite_records']
    assert result['decisions_for_point_eight'] is None and result['unbounded_upper_records']
    assert d.summarize_profiles([dict(valid=False,reason='aliased'),dict(valid=False,reason='aliased')],d.CONFIG)['primary']['state']=='invalid'
