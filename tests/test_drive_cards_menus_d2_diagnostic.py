"""Actual canonical inputs, original split parity and fitted known answers."""
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest

from runners.drive.cards import menus_d2_diagnostic as m
from runners.drive.cards import menus_d2_diagnostic_source as source
from runners.drive.cards import menus_d2_diagnostic_stats as stats
from runners.drive.cards.menus_io import read,write,sha256,assert_equal
from runners.stage14.common import digest


def fixture(root):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=False)
    base=root/'results/phase_2_4_stage_15/raw';audit=root/'audit';p8=root/'p8';content=root/'content'
    sessions=[];proofs=[];producer=[];sourcepins={};inputpins={};records=[];vectors=[];ledger=[]
    def embed(text,role,vector,truncated=False):
        index=len(vectors);vectors.append(vector);full=260 if truncated else len(text.split())
        ledger.append(dict(role=role,text_sha256=digest(text),full_tokens=full,used_tokens=min(full,254),
            first_native_token=max(0,full-254) if role=='context' else 0,truncated=truncated))
        return index
    for w in range(4):
        for h in range(5):
            sid=f'w{w}s{h}';start=w*10000+h*100;rows=[];events=[];rawsha=hashlib.sha256(sid.encode()).hexdigest()
            for i in range(20):
                key=f'{sid}i{i}';menu=['short phrase','longer option with much more detail']
                if i%2:menu.reverse()
                chosen=0;wrong=1;ids=[7,19];angle=.05+.55*(i%5)
                row=dict(key=key,writer=f'w{w}',session=sid,ordinal=i,open_at=start+i,handling='accept',
                    menu=menu,inserted=menu[wrong],document='prior source text')
                rows.append(row)
                events.append(dict(ordinal=i,decision='accept',usable=True,verified_insertion=True,
                    options=[dict(index=oid,original=text) for oid,text in zip(ids,menu)],matched_option_indices=[ids[chosen]],
                    selected_index=wrong,logged_index_agrees=False))
                proofs.append(dict(key=key,writer=row['writer'],session=sid,ordinal=i,open_at=row['open_at'],
                    canonical_handling='accept',prepared_handling='accept',canonical_positions=[chosen],prepared_positions=[wrong],
                    canonical_option_ids=ids,verified_insertion=True,canonical_usable=True,logged_selected_index=wrong,
                    logged_index_agrees=False,index_status='proven_disjoint_choice',raw_source_sha256=rawsha))
                context=embed(row['document'],'context',[0,0,1],i==0)
                options=[embed(menu[0],'suggestion',[1,0,0],i==1),embed(menu[1],'suggestion',[math.cos(angle),math.sin(angle),0])]
                records.append(dict(key=key,writer=row['writer'],session=sid,context=context,options=options))
                for j in range(2):producer.append(dict(key=key,writer=row['writer'],session=sid,ordinal=i,
                    position=j,suggestion_index=ids[j],logged_score=-4+j*81.54,source_sha256=rawsha,
                    decoding_numeric={k:float(z+1) for z,k in enumerate(stats.original.SETTINGS)}))
            path=root/'canonical'/(sid+'.json');write(path,dict(usable=True,reconstructed=True,events=events))
            sourcepins[path.relative_to(root).as_posix()]=sha256(path);inputpins[str(path)]=sha256(path)
            for proof in proofs[-len(rows):]:proof.update(canonical_path=str(path),canonical_sha256=sha256(path))
            sessions.append(dict(writer=f'w{w}',session=sid,timestamp=start,end_at=start+50,rows=rows))
    session_path=base/'phase0-v1/prepared/SESSIONS.json';source_path=session_path.with_name('SOURCE_PINS.json')
    write(session_path,sessions);write(source_path,sourcepins)
    foundation=base/'drive-foundation-v1';plan=foundation/'PLAN.json';complete=foundation/'COMPLETE.json'
    write(plan,dict(pins={p.relative_to(root).as_posix():sha256(p) for p in (session_path,source_path)},synthetic_fixture_only=True))
    write(complete,dict(status='COMPLETE',plan_sha256=sha256(plan),synthetic_fixture_only=True))
    for path in (session_path,source_path,plan,complete):inputpins[str(path)]=sha256(path)
    write(audit/'ROWS.json',proofs);write(audit/'INPUT_PINS.json',inputpins)
    origin=root/'audit_source.py';origin.write_text('# Synthetic audit fixture; no corpus evidence.\n',encoding='utf8')
    write(audit/'COMPLETE.json',dict(status='COMPLETE',schema_version=1,source_path=str(origin),source_sha256=sha256(origin),
        outputs={name:sha256(audit/name) for name in ('ROWS.json','INPUT_PINS.json')},no_fits=True,no_raw_replay=True,
        no_inference=True,no_repaired_scores=True,synthetic_fixture_only=True))
    p8.mkdir();(p8/'SUGGESTIONS.jsonl').write_text(''.join(json.dumps(p)+'\n' for p in producer),encoding='utf8')
    write(p8/'PLAN.json',dict(pins={str(session_path):sha256(session_path)},synthetic_fixture_only=True))
    write(p8/'COMPLETE.json',dict(status='COMPLETE',outputs={name:sha256(p8/name) for name in ('PLAN.json','SUGGESTIONS.jsonl')},synthetic_fixture_only=True))
    write(content/'RECORDS.json',records);write(content/'VISIBILITY.json',ledger);np.save(content/'VECTORS.npy',np.asarray(vectors))
    write(content/'COMPLETE.json',dict(status='COMPLETE',outputs={n:sha256(content/n) for n in ('RECORDS.json','VISIBILITY.json','VECTORS.npy')},synthetic_fixture_only=True))
    helper=Path(__file__).resolve().parents[1]/'.agent-state/drive-20261017/builder3/selected_source_audit_reader.py'
    inputs=dict(sessions=str(session_path),p8=str(p8/'SUGGESTIONS.jsonl'),p8_complete=str(p8/'COMPLETE.json'),
        content_complete=str(content/'COMPLETE.json'),records=str(content/'RECORDS.json'),vectors=str(content/'VECTORS.npy'),
        visibility=str(content/'VISIBILITY.json'),selection_reader=str(helper),selection_complete=str(audit/'COMPLETE.json'))
    # Authenticate exact original memberships with a deliberately marked metadata-only fixture.
    old=root/'original';case,excluded=stats.original.assemble(sessions,records,np.asarray(vectors),producer)
    splits,_=stats.original.chronological_partitions(sessions);hashes={}
    for writer in sorted(splits):
        split=stats.original.recipient_split(writer,splits)
        groups=[[case[r['key']] for s in split[name] for r in s['rows'] if r['key'] in case] for name in ('train','calibration','test')]
        value=dict(cutoff=split['cutoff'],test_cutoff=split['test_cutoff'],train_count=len(groups[0]),calibration_count=len(groups[1]),test_count=len(groups[2]),
            edges=np.quantile([c['dissimilarity'] for c in groups[0]],[.2,.4,.6,.8]).tolist(),
            arms=dict(primary=dict(predictions=[dict(key=c['key']) for c in groups[2]])))
        name='recipients/'+m.filename(writer);write(old/'output'/name,dict(result=value,synthetic_metadata_fixture_only=True));hashes[name]=sha256(old/'output'/name)
    write(old/'output/SUMMARY.json',dict(recipient_hashes=hashes,synthetic_metadata_fixture_only=True))
    basekeys=('sessions','records','vectors','p8','p8_complete','content_complete')
    pins={inputs[k]:sha256(inputs[k]) for k in basekeys}
    for module in (stats.original,source.partitions):pins[str(Path(module.__file__).resolve())]=sha256(module.__file__)
    write(old/'PLAN.json',dict(config=stats.original.CONFIG,inputs={k:inputs[k] for k in basekeys},pins=pins,synthetic_fixture_only=True))
    write(old/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,synthetic_metadata_fixture_only=True,
        outputs={p.relative_to(old).as_posix():sha256(p) for p in old.rglob('*') if p.is_file()}))
    inputs['original_complete']=str(old/'COMPLETE.json');return inputs


def completed_pilot(root,inputs):
    report=m.execute(root/'output',inputs,m.CONFIG)
    write(root/'PLAN.json',dict(module='runners.drive.cards.menus_d2_diagnostic',config=m.CONFIG,
        pins={str(Path(m.__file__).resolve()):sha256(m.__file__)},synthetic_fixture_only=True))
    write(root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,synthetic_fixture_only=True,
        outputs={p.relative_to(root).as_posix():sha256(p) for p in root.rglob('*') if p.is_file()}))
    return inputs|dict(pilot_plan=str(root/'PLAN.json'),pilot_complete=str(root/'COMPLETE.json'),pilot_summary=str(root/'output/SUMMARY.json'))


def test_canonical_visibility_and_partition_bindings(tmp_path):
    inputs=fixture(tmp_path/'source');data=source.load(inputs)
    assert len(data['cases'])==400 and all(c['truth']==0 for c in data['cases'].values())
    assert data['census']['eligible_choice_changed']==400 and data['census']['menus_with_truncated_option']==20
    assert data['census']['filtered_options']==0 and len(data['splits'])==4
    values=read(inputs['visibility']);values[1]['text_sha256']='0'*64
    with pytest.raises(ValueError,match='visibility text'):
        source.visibility(read(inputs['sessions'])[0]['rows'][0],read(inputs['records'])[0],values)
    old=Path(inputs['original_complete']).parent/'output/recipients'/m.filename('w0')
    value=read(old);value['result']['train_count']+=1;old.write_text(json.dumps(value),encoding='utf8')
    with pytest.raises(ValueError,match='recipient identity'):source.load(inputs)


def test_content_exact_parity_and_future_label_invariance(tmp_path):
    data=source.load(fixture(tmp_path/'source'));split=data['splits']['w0']
    actual=stats.fit_recipient(split,data['cases'])
    assert_equal(actual['content'],stats.original.fit_recipient(split,data['cases'],stats.original.CONFIG))
    changed=copy.deepcopy(data['cases'])
    for session in split['test']:
        for row in session['rows']:changed[row['key']]['truth']=1-changed[row['key']]['truth']
    reverse=stats.fit_recipient(split,changed)
    for name in stats.MODELS:
        assert actual[name]['preprocessing']==reverse[name]['preprocessing']
        assert actual[name]['arms']['primary']['beta']==reverse[name]['arms']['primary']['beta']
        assert actual[name]['arms']['primary']['penalty']==reverse[name]['arms']['primary']['penalty']
    assert np.mean([r['gain'] for r in actual['position']['arms']['primary']['predictions']])>0
    assert np.mean([r['gain'] for r in reverse['position']['arms']['primary']['predictions']])<0


def test_null_length_planted_and_original_objective():
    cases=[dict(x=np.array([[math.log(2),0,1],[math.log(40),1,0]])) for _ in range(100)]
    matrices,scale=stats.baseline_transform(cases,[0]);beta,certificate=stats.original.fit(stats.original.pack(matrices,[1]*100),.01)
    assert certificate['gradient_max']<=1e-6
    assert np.mean(stats.original.log_scores(beta,matrices,[1]*100)+math.log(2))>.5
    assert np.mean(stats.original.log_scores(beta,matrices,[0]*100)+math.log(2))<0
    identical=[dict(x=np.ones((3,3)))]*60;zero,_=stats.baseline_transform(identical,[0])
    beta,_=stats.original.fit(stats.original.pack(zero,list(np.tile([0,1,2],20))),.01)
    assert np.allclose(stats.original.log_scores(beta,zero,[0]*60)+math.log(3),0,atol=1e-15)
    # Balanced identical menus have a zero-gradient population optimum through
    # the actual content PCA, calibration and all three fitting pipelines.
    pool={f'k{i}':dict(key=f'k{i}',writer='w',session=f's{i//8}',truth=i%2,
        x=np.array([[math.log(2),0.,1.],[math.log(40),1.,0.]]),
        embeddings=np.array([[1.,0.,0.],[0.,1.,0.]]),dissimilarity=1.) for i in range(16)}
    split=dict(cutoff=8,test_cutoff=12)
    for name,indices in (('train',range(8)),('calibration',range(8,12)),('test',range(12,16))):
        split[name]=[dict(rows=[dict(key=f'k{i}') for i in indices])]
    full=stats.fit_recipient(split,pool)
    for model in stats.MODELS:
        assert np.allclose([p['gain'] for p in full[model]['arms']['primary']['predictions']],0,atol=1e-15)


def test_pilot_full_resume_and_fresh_process(tmp_path):
    inputs=fixture(tmp_path/'source');pilot=tmp_path/'pilot';fullinputs=completed_pilot(pilot,inputs)
    report=read(pilot/'output/SUMMARY.json');assert report['primary'] is None and report['execution_only']
    assert m.verify(pilot/'output',inputs,m.CONFIG)['fresh_refit_models']==3
    out=tmp_path/'full';out.mkdir();write(out/'YIELD_REQUEST.json',dict(reason='fixture'))
    config=m.CONFIG|dict(mode='full');assert m.execute(out,fullinputs,config)['status']=='yielded'
    (out/'YIELD_REQUEST.json').unlink();result=m.execute(out,fullinputs,config)
    assert result['primary']['state']=='positive' and result['all_three_against_uniform']['position']['primary']['state']=='positive'
    assert sha256(out/'recipients'/m.filename('w0'))==sha256(pilot/'output/recipients'/m.filename('w0'))
    before={p.relative_to(out).as_posix():sha256(p) for p in out.rglob('*') if p.is_file()}
    assert m.execute(out,fullinputs,config)==result
    assert before=={p.relative_to(out).as_posix():sha256(p) for p in out.rglob('*') if p.is_file()}
    request=tmp_path/'REQUEST.json';write(request,dict(output=str(out),inputs=fullinputs,config=config))
    code='import json,sys;from runners.drive.cards.menus_d2_diagnostic import verify;r=json.load(open(sys.argv[1]));assert verify(**r)["verified"]'
    env=os.environ.copy();env.update(PYTHONHASHSEED='719',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(request)],env=env,check=True,timeout=40)
    changed=read(fullinputs['pilot_complete']);changed['status']='FAILED';Path(fullinputs['pilot_complete']).write_text(json.dumps(changed),encoding='utf8')
    with pytest.raises(ValueError,match='verified diagnostic pilot'):m.execute(out,fullinputs,config)


def test_paired_bootstrap_exact_difference_and_refusal():
    units={}
    for w in range(4):
        models={}
        for model,offset in (('content',.4),('position',.1),('length',0)):
            models[model]=dict(arms={arm:dict(predictions=[dict(key=f'w{w}m{q}',writer=f'w{w}',session=f'w{w}s',
                truth=0,size=2,quintile=q,gain=w*.01+offset) for q in (0,4)]) for arm in stats.ARMS})
        units[f'w{w}']=models
    result=stats.summarize(units);paired=result['paired_model_differences']['content_minus_position']
    assert paired['effect']==pytest.approx(.3) and paired['ci95']==pytest.approx([.3,.3])
    units['w0']['position']['arms']['primary']['predictions'][0]['key']='different'
    with pytest.raises((ValueError,AssertionError)):stats.summarize(units)
