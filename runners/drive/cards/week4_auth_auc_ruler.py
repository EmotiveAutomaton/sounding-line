"""Constructed validation of a both-writer AUC uncertainty candidate.

DESIGN CHECK: LESSONS 3-5; CONTROLS 4-7; AUTH_AUC_RULER.md. Equal genre
mechanisms must control false alarms; planted signed differences must recover.
Exact ties must give exact zero difference. Unsupported/degenerate resampling
never licenses inference. No actual reader score is used in this runner.
"""
from pathlib import Path
import numpy as np
from runners.stage14.common import REPO, read, filehash
from .timing_p6 import write_equal

GENRES=('argumentative','creative')
FIELDS=('pair_id','block','genre','same_writer','left_writer','right_writer','left_session','right_session','left_prompt','right_prompt')


def configuration(mode):
    if mode not in ('constructed','timing','calibration'):
        raise ValueError('fixed ruler mode')
    return dict(mode=mode,seed=20261102,resamples=2000,
                worlds_per_regime={'constructed':1,'timing':2,'calibration':100}[mode])


def histories(rows):
    writers=sorted({r[k] for r in rows for k in ('left_writer','right_writer')})
    if len(writers)<4 or len({r['pair_id'] for r in rows})!=len(rows):
        raise ValueError('independent units or row uniqueness')
    ix={w:i for i,w in enumerate(writers)}
    pos=np.zeros((2,len(writers),10),dtype=np.int64)
    neg=np.zeros((2,len(writers),len(writers),10),dtype=np.int64)
    for r in rows:
        s=r['score'];i=ix[r['left_writer']];j=ix[r['right_writer']]
        if type(s) is not int or not 0<=s<=9 or type(r['same_writer']) is not bool:
            raise ValueError('score/truth schema')
        if r['same_writer']!=(i==j):raise ValueError('identity truth')
        g=GENRES.index(r['genre'])
        if r['same_writer']:pos[g,i,s]+=1
        else:neg[g,i,j,s]+=1
    if any(pos[g].sum()==0 or neg[g].sum()==0 for g in range(2)):
        raise ValueError('both truth classes required in both genres')
    return writers,pos,neg


def aucs(pos,neg,counts):
    counts=np.asarray(counts,dtype=np.float64)
    if counts.ndim!=2 or counts.shape[1]!=pos.shape[1] or not np.isfinite(counts).all() or (counts<0).any():
        raise ValueError('invalid writer weights')
    positive=np.einsum('bi,gis->bgs',counts,pos,optimize=True)
    negative=np.einsum('bi,gijs,bj->bgs',counts,neg,counts,optimize=True)
    below=np.cumsum(negative,axis=2)-negative
    numerator=np.sum(positive*(below+.5*negative),axis=2)
    denominator=np.sum(positive,axis=2)*np.sum(negative,axis=2)
    result=np.full(denominator.shape,np.nan)
    np.divide(numerator,denominator,out=result,where=denominator>0)
    return result


def evaluate(rows,seed=20261102,resamples=2000):
    writers,pos,neg=histories(rows);n=len(writers)
    rng=np.random.default_rng(seed)
    counts=rng.multinomial(n,np.full(n,1/n),size=resamples)
    point=aucs(pos,neg,np.ones((1,n)))[0]
    boot=aucs(pos,neg,counts);delta=boot[:,1]-boot[:,0]
    unsupported=int(np.count_nonzero(~np.isfinite(delta)))
    interval=None if unsupported else np.quantile(delta,[.025,.975],method='linear').tolist()
    degenerate=interval is not None and interval[0]==interval[1]
    return dict(argument_auc=float(point[0]),creative_auc=float(point[1]),difference=float(point[1]-point[0]),
                interval=interval,unsupported_draws=unsupported,degenerate_interval=degenerate,
                inference_valid=not unsupported and not degenerate,resamples=resamples,writers=n)


def fixture_geometry():
    rows=[]
    for genre in GENRES:
        for i in range(24):
            for block in range(3):
                left=f'{genre}-{i}-a{block}'
                for truth,j in ((True,i),(False,(i+block+1)%24)):
                    rows.append(dict(pair_id=f'{genre}-{i}-{block}-{truth}',block=f'{genre}-{i}-{block}',
                        genre=genre,same_writer=truth,left_writer=str(i),right_writer=str(j),
                        left_session=left,right_session=f'{genre}-{j}-b{block}',
                        left_prompt='a'+str(block),right_prompt='b'+str(block)))
    return rows


def geometry(inputs):
    if set(inputs)!={'collection_root','collection_landing'}:raise ValueError('fixed collection required')
    root=Path(inputs['collection_root']);landing=read(inputs['collection_landing'])
    expected=REPO/'results/phase_2_4_stage_15/raw/drive-week4-20261102/AUTH-collection'
    if root.resolve()!=expected.resolve():raise ValueError('original collection only')
    done=read(root/'COMPLETE.json')
    if not done['fresh_process_verified'] or not landing['full_write_through'] or landing['complete_sha256']!=filehash(root/'COMPLETE.json'):
        raise ValueError('unlanded collection')
    path=root/'output/PRIVATE_ROWS.json'
    if filehash(path)!=done['outputs']['output/PRIVATE_ROWS.json'] or filehash(path)!=landing['analysis_rows_sha256']:
        raise ValueError('collection changed')
    # Only structural metadata enters any constructed world. Never inspect scores.
    rows=[{k:r[k] for k in FIELDS} for r in read(path)]
    if len(rows)!=3800 or len({r['pair_id'] for r in rows})!=3800:raise ValueError('whole main geometry')
    return sorted(rows,key=lambda r:r['pair_id'])


def world(base,regime,index,seed,deterministic=False):
    if regime not in ('null','positive','negative'):raise ValueError('unknown construction')
    rows=[]
    if deterministic:
        for r in base:
            active=(regime=='positive' and r['genre']=='creative') or (regime=='negative' and r['genre']=='argumentative')
            score=(9 if r['same_writer'] else 0) if active else 5
            rows.append(dict(r,score=score))
        return rows
    rng=np.random.default_rng(np.random.SeedSequence([seed,index,1907]))
    writers=sorted({r[k] for r in base for k in ('left_writer','right_writer')})
    wi={w:i for i,w in enumerate(writers)}
    # Stable writer ability plus genre-specific writer variation; negative
    # scores depend on BOTH writers. Prompt and session effects are shared
    # wherever the same source node appears. No human score parameter is fitted.
    ability=rng.normal(0,.8,len(writers))
    bias=rng.normal(0,.8,len(writers))
    variation=rng.normal(0,.7,(2,len(writers)))
    sessions=sorted({r[k] for r in base for k in ('left_session','right_session')})
    session={s:float(rng.normal(0,.4)) for s in sessions}
    prompts=sorted({(r['genre'],r[k]) for r in base for k in ('left_prompt','right_prompt')})
    prompt={p:float(rng.normal(0,.5)) for p in prompts}
    for r in sorted(base,key=lambda r:r['pair_id']):
        i,j=wi[r['left_writer']],wi[r['right_writer']];g=GENRES.index(r['genre'])
        shift=2.5 if (regime=='positive' and g==1) or (regime=='negative' and g==0) else 0
        signal=(1+ability[i]+variation[g,i]+shift) if r['same_writer'] else 0
        value=4+signal+(bias[i]+bias[j])/2+(session[r['left_session']]+session[r['right_session']])/2
        value+=(prompt[(r['genre'],r['left_prompt'])]+prompt[(r['genre'],r['right_prompt'])])/2+float(rng.normal(0,.8))
        rows.append(dict(r,score=int(np.clip(np.rint(value),0,9))))
    return rows


def run(output,inputs,config,verification=False):
    if config!=configuration(config['mode']):raise ValueError('fixed ruler configuration')
    mode=config['mode'];out=Path(output);out.mkdir(parents=True,exist_ok=True)
    if mode=='constructed' and inputs:raise ValueError('fixture has no human inputs')
    base=fixture_geometry() if mode=='constructed' else geometry(inputs)
    records=[]
    for regime in ('null','positive','negative'):
        for index in range(config['worlds_per_regime']):
            rows=world(base,regime,index,config['seed'],mode=='constructed')
            if verification:rows=list(reversed(rows))
            result=evaluate(rows,config['seed']+index,config['resamples'])
            record=dict(regime=regime,index=index,**result)
            name=f'world-{regime}-{index:03d}.json'
            if verification:
                if read(out/name)!=record:raise ValueError('fresh ruler replay differs')
            else:write_equal(out/name,record)
            records.append(record)
    if mode=='constructed':
        for r,target in zip(records,(0,.5,-.5)):
            if r['difference']!=target or r['unsupported_draws'] or r['interval']!=[target,target] or not r['degenerate_interval'] or r['inference_valid']:
                raise ValueError('deterministic arithmetic/null classification failed')
        passes=True
    else:
        by={g:[r for r in records if r['regime']==g] for g in ('null','positive','negative')}
        valid=all(r['inference_valid'] for r in records)
        false_alarms=sum(r['interval'] is not None and (r['interval'][0]>0 or r['interval'][1]<0) for r in by['null'])
        positive=sum(r['inference_valid'] and r['interval'][0]>0 for r in by['positive'])
        negative=sum(r['inference_valid'] and r['interval'][1]<0 for r in by['negative'])
        passes=mode=='calibration' and valid and false_alarms<=10 and positive>=80 and negative>=80
    summary=dict(mode=mode,worlds=len(records),geometry_pairs=len(base),resamples_per_world=config['resamples'],
                 passes=passes,scientific_admission=False,human_scores_used=False,context_control_admission=False)
    if mode!='constructed':summary.update(all_draws_supported_and_nondegenerate=valid,null_false_alarms=false_alarms,positive_recovered=positive,negative_recovered=negative)
    if verification:
        if read(out/'SUMMARY.json')!=summary:raise ValueError('summary replay differs')
    else:write_equal(out/'SUMMARY.json',summary)
    return dict(verified=True,complete_constructed_replay=True,scientific_admission=False)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
