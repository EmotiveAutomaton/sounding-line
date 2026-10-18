import functools
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest
from scipy.optimize import minimize
from scipy.special import expit
from runners.drive.cards import menus_d11 as d
from runners.drive.cards import menus_d11_stats as stats
from runners.drive.cards import menus_d11_sources as source
from runners.drive.cards.menus_io import read,write,sha256
from runners.drive.cards.timing_p6 import gzwrite


def synthetic_design(seed=84):
    rng=np.random.default_rng(seed);group=np.repeat(np.arange(10),40);own=rng.normal(size=len(group))
    x=np.c_[np.ones(len(group)),own,rng.normal(size=len(group))]
    y=(rng.random(len(group))<expit(1.7*own+.2*x[:,2])).astype(float)
    return x,y,group,own,np.ones(len(group))


def test_certified_fit_matches_independent_full_parameter_optimizer():
    x,y,g,own,w=synthetic_design();config=d.CONFIG
    fitted=stats.fit(x,y,g,own,w,config);q=x.shape[1];k=len(set(g))
    def objective(theta):
        beta=theta[:q];random=theta[q:].reshape(k,2);z=np.c_[np.ones(len(y)),own]
        eta=x@beta+np.sum(z*random[g],axis=1);res=expit(eta)-y
        fp=np.r_[0,np.full(q-1,config['fixed_ridge'])];rp=np.array([config['intercept_ridge'],config['slope_ridge']])
        value=np.sum(np.logaddexp(0,eta)-y*eta)+.5*np.sum(fp*beta*beta)+.5*np.sum(rp*random*random)
        gr=random*rp;np.add.at(gr,g,res[:,None]*z)
        return value,np.r_[x.T@res+fp*beta,gr.ravel()]
    independent=minimize(objective,np.zeros(q+2*k),jac=True,method='L-BFGS-B',options={'maxiter':3000,'ftol':1e-14,'gtol':1e-8})
    actual=np.r_[fitted['beta'],np.asarray(fitted['random']).ravel()]
    assert abs(objective(actual)[0]-independent.fun)<1e-8
    assert np.max(np.abs(actual-independent.x))<2e-4
    assert fitted['gradient_gap']<=config['gradient_tolerance']
    reversed_fit=stats.fit(x,1-y,g,own,w,config)
    assert np.allclose(reversed_fit['beta'],-np.array(fitted['beta']),atol=1e-8)


def test_resampled_writer_penalties_equal_explicit_clones():
    x,y,g,own,w=synthetic_design();copies=np.array([2,0,1,1,1,1,1,1,1,1]);order=np.repeat(np.arange(10),copies)
    result=stats.fit(x,y,g,own,w,d.CONFIG,copies)
    index=np.concatenate([np.flatnonzero(g==j) for j in order]);groups=np.repeat(np.arange(len(order)),40)
    explicit=stats.fit(x[index],y[index],groups,own[index],w[index],d.CONFIG)
    assert np.allclose(result['beta'],explicit['beta'],atol=2e-8)
    assert np.allclose(np.array(result['random'])[order],explicit['random'],atol=2e-8)
    with pytest.raises(ValueError,match='iteration cap'):stats.fit(x,y,g,own,w,d.CONFIG|dict(max_iterations=0))


def test_causal_word_window_and_complete_next_sentence():
    words=[dict(index=i,token='word',is_word=True,ordinal=i,completed_ordinal=i+1,
                sentence_start=i==56,previous_typed_token_index=i-1 if i else None) for i in range(60)]
    words.append(dict(index=60,token='.',is_word=False,ordinal=60,completed_ordinal=61,previous_typed_token_index=59))
    assert [w['index'] for w in source.prior_words(words,56)]==list(range(5,55))
    assert [w['index'] for w in source.next_sentence(words,55)]==list(range(56,61))
    words[58]['previous_typed_token_index']=None
    assert source.next_sentence(words,55) is None


@functools.lru_cache(None)
def basis():
    path=Path.cwd()/'results/phase_2_4_stage_15/raw/drive-content-features-v2/MODEL.json'
    from runners.drive.cards.events_p5 import Encoder
    text_a=' '.join(['apple']*50);text_b=' '.join(['telescope']*50);prompt='Write a short story.'
    vectors,_=Encoder(str(path),1,16).encode([text_a,text_b,prompt])
    return path,text_a,text_b,prompt,vectors


def fixture(tmp_path,mode='positive'):
    model,text_a,text_b,prompt,vectors=basis();root=tmp_path/'source';root.mkdir()
    p2=root/'p2';p5=root/'p5';p6=root/'p6';content=root/'content'
    for directory in (p2,p5,p6,content):directory.mkdir()
    sessions=[];features=[];timeline_index=[];ledger_index=[];rng=np.random.default_rng(338)
    for writer in range(10):
        for number in range(4):
            sid=f'w{writer}s{number}';rows=[];decisions=[];words=[];ordinal=0;when=1000000+writer*100000+number*10000
            for j in range(8):
                high=bool(rng.integers(2));history=text_a if high else text_b
                start=len(words)
                for z,token in enumerate(history.split()+['.']):
                    words.append(dict(index=len(words),token=token,is_word=token!='.',ordinal=ordinal,completed_ordinal=ordinal,
                        sentence_start=z==0,previous_typed_token_index=len(words)-1 if z else None,revised=False));ordinal+=1
                opening=ordinal+1;ordinal+=4;prob=.9 if high else .1
                if mode=='null':prob=.5
                accepted=bool(rng.random()<prob)
                if mode=='reverse':accepted=not accepted
                action='accept' if accepted else 'dismiss';key=f'{sid}m{j}';time=when+j*100
                row=dict(key=key,writer=f'w{writer}',session=sid,prompt='p',ordinal=opening,handling=action,
                    menu=[text_a],inserted=text_a if accepted else '',open_at=time,resolved_at=time+10,session_time=when,
                    decision_index=j,document=prompt)
                rows.append(row);features.append(dict(key=key,writer=f'w{writer}',session=sid,options=[0],context=2,
                    cosine=[float(vectors[0]@vectors[2])],scalars=[[len(text_a),0.,0.,0.]]))
                decisions.append(dict(key=key,ordinal=opening,resolution_ordinal=opening+1,handling=action))
            sessions.append(dict(session=sid,writer=f'w{writer}',prompt='p',timestamp=when,end_at=when+1000,rows=rows))
            name=sid+'.json';write(p2/name,dict(session=sid,writer=f'w{writer}',prompt='p',initial_document=prompt,decisions=decisions))
            timeline_index.append(dict(session=sid,writer=f'w{writer}',file=name,sha256=sha256(p2/name)))
            name=sid+'.json.gz';gzwrite(p6/name,dict(session=sid,writer=f'w{writer}',prompt='p',words=words))
            ledger_index.append(dict(session=sid,writer=f'w{writer}',file=name,sha256=sha256(p6/name)))
    write(root/'SESSIONS.json',sessions);write(content/'RECORDS.json',features);np.save(content/'VECTORS.npy',vectors,allow_pickle=False)
    (content/'MODEL.json').write_bytes(model.read_bytes())
    write(content/'COMPLETE.json',dict(status='COMPLETE',outputs={n:sha256(content/n) for n in ('RECORDS.json','VECTORS.npy','MODEL.json')}))
    write(p2/'INDEX.json',timeline_index);write(p2/'COMPLETE.json',dict(status='COMPLETE',outputs={'INDEX.json':sha256(p2/'INDEX.json')}))
    write(p5/'INDEX.json',[dict(session=r['session']) for r in sessions])
    inputs=dict(sessions=str(root/'SESSIONS.json'),content_model=str(content/'MODEL.json'))
    write(p5/'INPUTS.json',dict(paths=inputs,sha256={k:sha256(v) for k,v in inputs.items()}))
    write(p5/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,outputs={n:sha256(p5/n) for n in ('INDEX.json','INPUTS.json')}))
    write(p6/'INDEX.json',ledger_index);write(p6/'PLAN.json',dict(inputs={'prepared_sessions':inputs['sessions']},pins={inputs['sessions']:sha256(inputs['sessions'])}))
    write(p6/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,outputs={n:sha256(p6/n) for n in ('INDEX.json','PLAN.json')}))
    inputs.update(content_records=str(content/'RECORDS.json'),content_vectors=str(content/'VECTORS.npy'),content_complete=str(content/'COMPLETE.json'),
        foundation_complete=str(p2/'COMPLETE.json'),session_index=str(p2/'INDEX.json'),p5_inputs=str(p5/'INPUTS.json'),p5_index=str(p5/'INDEX.json'),p5_completion=str(p5/'COMPLETE.json'),
        p6_index=str(p6/'INDEX.json'),p6_plan=str(p6/'PLAN.json'),p6_completion=str(p6/'COMPLETE.json'))
    return inputs,d.CONFIG|dict(bootstrap=30,checkpoint_draws=10,threads=1,batch_size=16,pca_dimensions=2)


def test_actual_positive_resume_certification_fresh_replay(tmp_path):
    inputs,config=fixture(tmp_path);output=tmp_path/'output';output.mkdir();write(output/'YIELD_REQUEST.json',{})
    assert d.execute(output,inputs,config)['status']=='yielded';(output/'YIELD_REQUEST.json').unlink()
    result=d.execute(output,inputs,config)
    assert result['primary']['state']=='positive'
    assert result['later_text']['writers']>=4
    before={str(p):sha256(p) for p in output.rglob('*') if p.is_file()}
    assert d.execute(output,inputs,config)==result
    assert before=={str(p):sha256(p) for p in output.rglob('*') if p.is_file()}
    request=tmp_path/'REQUEST.json';write(request,dict(output=str(output),inputs=inputs,config=config))
    code='import json,sys;from runners.drive.cards.menus_d11 import verify;r=json.load(open(sys.argv[1]));assert verify(**r)["point_certified"]'
    subprocess.run([sys.executable,'-B','-c',code,str(request)],check=True,timeout=60,env=os.environ|dict(PYTHONHASHSEED='421'))
    path=next((output/'draws').glob('*.json'));path.write_text(path.read_text(encoding='utf8')+' ',encoding='utf8')
    with pytest.raises(ValueError,match='changed'):d.verify(output,inputs,config)


@pytest.mark.parametrize('mode',['null','reverse'])
def test_full_pipeline_noise_and_reverse(mode,tmp_path):
    inputs,config=fixture(tmp_path,mode=mode);result=d.execute(tmp_path/'output',inputs,config)
    if mode=='reverse':assert result['primary']['state']=='negative'
    else:
        assert result['primary']['ci95'][0]<=0<=result['primary']['ci95'][1]
        assert abs(result['primary']['effect'])<1
    assert d.verify(tmp_path/'output',inputs,config)['point_certified']
