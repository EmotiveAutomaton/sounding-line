import copy
import json
import math
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
from scipy.optimize import check_grad
from scipy.special import softmax

from runners.drive.cards import menus_d2 as d
from runners.drive.cards.menus_io import write, read, sha256


def fixture(tmp_path):
    sessions=[];records=[];vectors=[];producer=[]
    for w in range(4):
        for s in range(5):
            sid=f'w{w}s{s}'; start=w*10000+s*100
            session=dict(writer=f'w{w}',session=sid,timestamp=start,end_at=start+50,prompt='fixture',rows=[])
            for i in range(20):
                key=f'{sid}m{i}'; angle=.05+.55*(i%5)
                menu=['plain short option','longer alternative with additional detail']
                truth=i%2
                row=dict(key=key,session=sid,writer=f'w{w}',menu=menu,handling='accept',inserted=menu[truth],
                         document='prior plain text',ordinal=i,open_at=start+i,resolved_at=start+i+.5)
                session['rows'].append(row)
                context=len(vectors); vectors.append([0,0,1.])
                options=[len(vectors),len(vectors)+1];vectors.extend([[1.,0,0],[math.cos(angle),math.sin(angle),0]])
                records.append(dict(key=key,writer=f'w{w}',session=sid,context=context,options=options))
                for j in range(2):producer.append(dict(key=key,writer=f'w{w}',session=sid,ordinal=i,
                    position=j,suggestion_index=j+10,logged_score=1.2 if j else .3,
                    decoding_numeric={k:float(z+1) for z,k in enumerate(d.SETTINGS)}))
            sessions.append(session)
    source=tmp_path/'source';source.mkdir()
    write(source/'SESSIONS.json',sessions);write(source/'RECORDS.json',records)
    np.save(source/'VECTORS.npy',np.array(vectors))
    (source/'SUGGESTIONS.jsonl').write_text(''.join(json.dumps(p)+'\n' for p in producer),encoding='utf8')
    write(source/'CONTENT_COMPLETE.json',dict(status='COMPLETE',outputs={n:sha256(source/n) for n in ['RECORDS.json','VECTORS.npy']}))
    write(source/'PLAN.json',dict(pins={str((source/'SESSIONS.json').resolve()):sha256(source/'SESSIONS.json')}))
    write(source/'P8_COMPLETE.json',dict(status='COMPLETE',outputs={n:sha256(source/n) for n in ['SUGGESTIONS.jsonl','PLAN.json']}))
    inputs={k:str(source/n) for k,n in dict(sessions='SESSIONS.json',records='RECORDS.json',vectors='VECTORS.npy',
            p8='SUGGESTIONS.jsonl',content_complete='CONTENT_COMPLETE.json',p8_complete='P8_COMPLETE.json').items()}
    config=d.CONFIG|dict(bootstrap=100,pca_components=2,penalties=[.01,.1])
    return inputs,config


def test_gradient_and_probability_oracle():
    rng=np.random.default_rng(17); matrices=[rng.normal(size=(n,4)) for n in [2,5,3,4]]
    truths=[0,3,1,2];data=d.pack(matrices,truths);beta=rng.normal(size=4)
    assert check_grad(lambda b:d.objective(b,data,.1)[0],lambda b:d.objective(b,data,.1)[1],beta)<1e-6
    expected=[math.log(softmax(x@beta)[y]) for x,y in zip(matrices,truths)]
    assert np.allclose(d.log_scores(beta,matrices,truths),expected,atol=1e-14)


def test_null_and_planted_choice_rule():
    identical=[np.zeros((2,1))]*100
    beta,_=d.fit(d.pack(identical,[i%2 for i in range(100)]),.01)
    assert np.allclose(d.log_scores(beta,identical,[0]*100)+math.log(2),0,atol=1e-15)
    train=[np.array([[-a],[a]]) for a in np.tile([.01,.1,.5,1,2],40)]
    beta,_=d.fit(d.pack(train,[1]*len(train)),.01)
    small=d.log_scores(beta,[np.array([[-.01],[.01]])],[1])[0]+math.log(2)
    large=d.log_scores(beta,[np.array([[-2.],[2.]])],[1])[0]+math.log(2)
    assert large-small>.5


def test_all_contrast_directions_and_population_guard():
    config=d.CONFIG|dict(bootstrap=100)
    rows=[dict(writer=str(w),quintile=q,gain=v) for w in range(5) for q,v in [(0,0.),(4,.3+w/100)]]
    assert d.summarize(rows,config)['state']=='positive'
    assert d.summarize([r|dict(gain=-r['gain']) for r in rows],config)['state']=='negative'
    assert d.summarize([r|dict(gain=0.) for r in rows],config)['state']=='null'
    with pytest.raises(ValueError,match='insufficient writers'):
        d.summarize([r for r in rows if r['writer']=='0'],config)


def test_coverage_and_option_identity_fail_closed(tmp_path):
    inputs,config=fixture(tmp_path);cases,splits,excluded=d.load(inputs)
    assert len(cases)==400
    producer=[json.loads(l) for l in Path(inputs['p8']).read_text().splitlines()]
    producer[0]['position']=1
    with pytest.raises(ValueError,match='coverage'):
        d.assemble(read(inputs['sessions']),read(inputs['records']),np.load(inputs['vectors']),producer)
    changed=read(inputs['sessions']);changed[0]['rows'][0]['inserted']='unshown'
    producer=[json.loads(l) for l in Path(inputs['p8']).read_text().splitlines()]
    selected,excluded=d.assemble(changed,read(inputs['records']),np.load(inputs['vectors']),producer)
    assert len(selected)==399 and excluded['ambiguous_or_absent_selected_text']==1


def test_chronology_test_labels_do_not_change_model(tmp_path):
    inputs,config=fixture(tmp_path);cases,splits,_=d.load(inputs)
    split=d.recipient_split('w0',splits)
    assert all(s['end_at']<split['cutoff'] for s in split['train'])
    assert not any(s['writer']=='w1' for s in split['train'])
    a=d.fit_recipient(split,cases,config);changed=copy.deepcopy(cases)
    for session in split['test']:
        for row in session['rows']:changed[row['key']]['truth']=1-changed[row['key']]['truth']
    b=d.fit_recipient(split,changed,config)
    assert a['preprocessing']==b['preprocessing'] and a['edges']==b['edges']
    assert a['arms']['primary']['beta']==b['arms']['primary']['beta']
    assert a['arms']['primary']['penalty']==b['arms']['primary']['penalty']


def test_actual_serialization_reentry_fresh_process_and_tamper(tmp_path):
    inputs,config=fixture(tmp_path);out=tmp_path/'output'
    result=d.execute(out,inputs,config)
    assert result['writers']==4 and result['extension_computed'] is False
    before={str(p):sha256(p) for p in out.rglob('*') if p.is_file()}
    assert d.execute(out,inputs,config)==result
    assert before=={str(p):sha256(p) for p in out.rglob('*') if p.is_file()}
    request=tmp_path/'REQUEST.json';write(request,dict(output=str(out),inputs=inputs,config=config))
    code='import json,sys; from runners.drive.cards.menus_d2 import verify; r=json.load(open(sys.argv[1])); assert verify(**r)["verified"]'
    env=os.environ.copy();env.update(PYTHONHASHSEED='719',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
    subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(request)],env=env,check=True,timeout=45)
    checkpoint=next((out/'recipients').glob('*.json'))
    checkpoint.write_text(checkpoint.read_text()+' ',encoding='utf8')
    with pytest.raises(ValueError,match='changed saved recipient'): d.verify(out,inputs,config)


def test_yield_and_changed_dependency_refusal(tmp_path):
    inputs,config=fixture(tmp_path);out=tmp_path/'output';out.mkdir()
    write(out/'YIELD_REQUEST.json',{'reason':'fixture'})
    assert d.execute(out,inputs,config)['status']=='yielded'
    (out/'YIELD_REQUEST.json').unlink()
    assert d.execute(out,inputs,config)['writers']==4
    with Path(inputs['p8']).open('a',encoding='utf8') as stream:stream.write('\n')
    with pytest.raises(ValueError): d.verify(out,inputs,config)


def test_uniform_control_is_canonical_and_within_each_offer_set():
    cases=[dict(key=f'k{i}',x=np.zeros((2+i%4,1)),truth=0) for i in range(400)]
    a=d.labels(cases,'uniform_control',17);b=d.labels(cases[::-1],'uniform_control',17)
    assert a==b[::-1] and all(0<=y<len(c['x']) for y,c in zip(a,cases))
    assert .4<np.mean(np.array(a)[::4]==0)<.6
