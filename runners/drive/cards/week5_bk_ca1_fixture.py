"""Constructed source and complete native CA1/V1 proofs, never human scores."""
from pathlib import Path
import gzip,hashlib,json,sys,time,shutil,subprocess
import numpy as np
from . import week5_bk_ca1_features as features
from . import week5_bk_v1 as analysis
from . import week5_go as core


def completed(root):
    core.write(root/'COMPLETE.json',{'status':'COMPLETE','fresh_process_verified':True,
        'outputs':{'output/'+p.name:core.sha(p) for p in (root/'output').iterdir() if p.is_file()}})


def make_source(root,people=12):
    out=root/'output';out.mkdir(parents=True,exist_ok=True);rng=np.random.default_rng(712)
    texts=[f'Constructed statement {i}: a person chooses an answer about topic {i%17}.' for i in range(600)]
    rows=[];membership={'mandatory':[f'w{i:03}' for i in range(people//2)],'random':[f'w{i:03}' for i in range(people//2,people)]}
    for i in range(people):
        for j in range(24):
            rows.append({'writer':f'w{i:03}','country':'country-a','conversation':f'c{i:03}-{j:03}',
                         'turn':1,'prompt':f'p{j%50:03}','candidates':[4*j+k for k in range(4)],'choice':int(rng.integers(4))})
    splits={'writer_splits':{w:{} for w in membership['mandatory']+membership['random']},
            'prompt_text_indices':{f'p{i:03}':550+i for i in range(50)}}
    with gzip.open(out/'COMPARISONS.jsonl.gz','wt',encoding='utf8') as f:
        for r in rows:f.write(json.dumps(r)+'\n')
    with gzip.open(out/'TEXTS.jsonl.gz','wt',encoding='utf8') as f:
        for i,t in enumerate(texts):f.write(json.dumps({'index':i,'text':t,'sha256':hashlib.sha256(t.encode()).hexdigest()})+'\n')
    core.write(out/'SPLITS.json',splits);core.write(out/'PRIVATE_SAMPLE.json',membership)
    report={'card':'CA1-inputs','variant':'CA1.s1','state':'inputs_ready','sample_scope':True,
            'permutation_route':'within_country_and_50_prompt_clusters','output_hashes':{n:core.sha(out/n) for n in
                 ('COMPARISONS.jsonl.gz','TEXTS.jsonl.gz','SPLITS.json','PRIVATE_SAMPLE.json')}}
    core.write(out/'SUMMARY.json',report);completed(root)
    return rows,membership,splits


def analysis_source(root,kind):
    sr=root/'source';rows,membership,splits=make_source(sr);out=sr/'output';rng=np.random.default_rng(771)
    # Full-rank, common repeated choice sets make known-direction recovery clear.
    vectors=rng.normal(size=(600,384));vectors/=np.linalg.norm(vectors,axis=1)[:,None]
    x,_=analysis.old.candidate_features(rows,vectors,list(range(600)),seed=analysis.old.SEED)
    people,halves,details=analysis.allocation(rows,{p:0 for p in splits['prompt_text_indices']},membership)
    signs={w:(1 if i%2 else -1) for i,w in enumerate(people)}
    for i,r in enumerate(rows):
        sign=1 if kind=='null' else signs[r['writer']]*(1 if kind=='positive' or halves[i]==0 else -1)
        r['choice']=int(np.argmax(sign*x[i,:,0]))
    # Every half sees exactly the same trial roster: reorder conversations using
    # the consumer's own choice-blind assignment, then pair their candidate sets.
    for w in people:
        sides=[[i for i,r in enumerate(rows) if r['writer']==w and halves[i]==h] for h in (0,1)]
        for j,(a,b) in enumerate(zip(*sides)):
            rows[a]['candidates']=[4*j+k for k in range(4)]
            rows[b]['candidates']=rows[a]['candidates'][:]
    x,_=analysis.old.candidate_features(rows,vectors,list(range(600)),seed=analysis.old.SEED)
    for i,r in enumerate(rows):
        sign=1 if kind=='null' else signs[r['writer']]*(1 if kind=='positive' or halves[i]==0 else -1)
        r['choice']=int(np.argmax(sign*x[i,:,0]))
    with gzip.open(out/'COMPARISONS.jsonl.gz','wt',encoding='utf8') as f:
        for r in rows:f.write(json.dumps(r)+'\n')
    report=json.loads((out/'SUMMARY.json').read_text('utf8'));report['output_hashes']['COMPARISONS.jsonl.gz']=core.sha(out/'COMPARISONS.jsonl.gz');core.write(out/'SUMMARY.json',report);completed(sr)
    fr=root/'features';fo=fr/'output';fo.mkdir(parents=True);np.save(fo/'EMBEDDINGS.npy',vectors.astype(np.float32))
    core.write(fo/'INDEX.json',{'comparison_indices':list(range(len(rows))),'text_indices':list(range(600)),
                              'prompt_clusters':{p:0 for p in splits['prompt_text_indices']}})
    core.write(fo/'SUMMARY.json',{'card':'CA1-features','mode':'full','execution_only':False,
                                'input_hashes':{'prepared_summary':core.sha(out/'SUMMARY.json')},
                                'output_hashes':{n:core.sha(fo/n) for n in ('EMBEDDINGS.npy','INDEX.json')}});completed(fr)
    return {'prepared_summary':str(out/'SUMMARY.json'),'prepared_complete':str(sr/'COMPLETE.json'),
            'features_summary':str(fo/'SUMMARY.json'),'features_complete':str(fr/'COMPLETE.json')}


def run(root,phase):
    root=Path(root);root.mkdir(parents=True,exist_ok=True);start=time.process_time()
    if phase=='v1-replay-child':
        bundle=json.loads((root/'INPUTS.json').read_text('utf8'))
        result=analysis.verify(root/'run',bundle['inputs'],bundle['config'])
        core.write(root/'FRESH_VERIFICATION.json',{**result,'cpu_seconds':time.process_time()-start});return
    if phase in ('encoder-fresh','encoder-replay-child'):
        out=root/'source/output';model=Path('results/phase_2_4_stage_15/raw/drive-week3-20261025/CA1-model')
        inputs={'prepared_summary':str(out/'SUMMARY.json'),'prepared_complete':str(root/'source/COMPLETE.json'),
                'model_summary':str(model/'output/SUMMARY.json'),'model_complete':str(model/'COMPLETE.json')}
        config={'fixture':True,'actual_encoder':True,'max_new_chunks':1,'max_wall_seconds':900};dest=root/'fresh-native'
        if phase=='encoder-replay-child':
            result=features.verify(dest,inputs,config);core.write(root/'CHILD_VERIFICATION.json',result);return
        shutil.copytree(root/'run',dest,ignore=shutil.ignore_patterns('independent-replay'))
        for i in range(2):
            child=subprocess.run([sys.executable,'-X','utf8','-B','-m',__spec__.name,str(root),'encoder-replay-child'],capture_output=True,text=True)
            (root/f'fresh-{i}.stderr.log').write_text(child.stderr,encoding='utf8')
            if child.returncode:raise ValueError('fresh native encoder replay failed')
            result=json.loads((root/'CHILD_VERIFICATION.json').read_text('utf8'))
            assert result['verified']==(i==1)
        core.write(root/'FRESH_PROCESS.json',{'verified':True,'fresh_process_replay_with_resume':True,
                    'feature_module_sha256':core.sha(features.__file__),'vectors_sha256':core.sha(dest/'EMBEDDINGS.npy')})
        print(json.dumps({'verified':True,'receipt':str(root/'FRESH_PROCESS.json')}));return
    if phase=='encoder':
        rows,_,_=make_source(root/'source')
        # Include 550 candidate indices so the real encoder exercises two chunks.
        out=root/'source/output';splits=json.loads((out/'SPLITS.json').read_text('utf8'))
        splits['prompt_text_indices']={f'p{i:03}':i for i in range(600)};core.write(out/'SPLITS.json',splits)
        report=json.loads((out/'SUMMARY.json').read_text('utf8'));report['output_hashes']['SPLITS.json']=core.sha(out/'SPLITS.json');core.write(out/'SUMMARY.json',report);completed(root/'source')
        model=Path('results/phase_2_4_stage_15/raw/drive-week3-20261025/CA1-model')
        inputs={'prepared_summary':str(out/'SUMMARY.json'),'prepared_complete':str(root/'source/COMPLETE.json'),
                'model_summary':str(model/'output/SUMMARY.json'),'model_complete':str(model/'COMPLETE.json')}
        config={'fixture':True,'actual_encoder':True,'max_new_chunks':1,'max_wall_seconds':900}
        dest=root/'run';assert features.execute(dest,inputs,config)['status']=='yielded'
        assert not (dest/'SUMMARY.json').exists()
        result=features.execute(dest,inputs,config)
        assert result['texts']==600
        assert features.verify(dest,inputs,config)['verified'] is False
        assert features.verify(dest,inputs,config)['verified'] is True
        # Compare directly to the unchanged old encoder at the same batch layout.
        encode=features.old.encoder(inputs,{'mode':'full'})
        texts=[f'Constructed statement {i}: a person chooses an answer about topic {i%17}.' for i in range(600)]
        original=np.concatenate([encode(texts[i:i+512]) for i in range(0,600,512)])
        assert np.array_equal(original,np.load(dest/'EMBEDDINGS.npy'))
        proof={'actual_original_encoder':True,'all_600_vectors_bitwise_equal':True,'pause_resume_and_independent_replay':True}
    elif phase=='v1':
        results={}
        for kind in ('positive','negative','null'):
            inputs=analysis_source(root/kind,kind);dest=root/kind/'run'
            config={'fixture':True,'permutations':200,'draws':2000,'max_new_fits':1,'max_wall_seconds':900}
            assert analysis.execute(dest,inputs,config)['status']=='yielded';assert not (dest/'RESULT.json').exists()
            config['max_new_fits']=10**9
            result=analysis.execute(dest,inputs,config)
            assert result.get('status')!='yielded'
            core.write(root/kind/'INPUTS.json',{'inputs':inputs,'config':config})
            child=subprocess.run([sys.executable,'-X','utf8','-B','-m',__spec__.name,str(root/kind),'v1-replay-child'],capture_output=True,text=True)
            (root/kind/'verify.stderr.log').write_text(child.stderr,encoding='utf8')
            if child.returncode:raise ValueError('fresh V1 native replay failed')
            assert json.loads((root/kind/'FRESH_VERIFICATION.json').read_text('utf8'))['verified']
            values=[r['mean_cosine_excess'] for r in result['groups'].values()]
            if kind=='positive':assert min(values)>.1
            if kind=='negative':assert max(values)<-.1
            if kind=='null':
                # Common choices can differ modestly because each person sees
                # a different exact set; the independent exact-profile null
                # below additionally requires exact zero classification.
                assert max(abs(v) for v in values)<.1
            results[kind]=result['groups']
        detail={f'w{i}':{'group':'random','country':'a','cluster':0} for i in range(30)}
        profiles={w:[[1.,2.],[1.,2.]] for w in detail};exact=analysis.contrast(profiles,detail)
        null=analysis.summary(exact,[exact]*200)
        assert null['random']['mean_cosine_excess']==0 and null['random']['state']=='inconclusive' and not null['random']['control_pass']
        proof={'whole_signed_worlds':results,'complete_200_permutations_and_2000_bootstraps':True,'exact_profile_null':null['random'],
               'fresh_native_verifier_cpu_seconds':sum(json.loads((root/k/'FRESH_VERIFICATION.json').read_text('utf8'))['cpu_seconds'] for k in results)}
    else:raise ValueError('unknown fixture phase')
    receipt={'verified':True,'constructed_only':True,'cpu_seconds':time.process_time()-start,
             'modules':{Path(m.__file__).name:core.sha(m.__file__) for m in (features,analysis)},**proof}
    core.write(root/'FIXTURE.json',receipt);print(json.dumps({'verified':True,'phase':phase,'receipt':str(root/'FIXTURE.json'),'cpu_seconds':receipt['cpu_seconds']}))


if __name__=='__main__':run(Path(sys.argv[1]),sys.argv[2])
