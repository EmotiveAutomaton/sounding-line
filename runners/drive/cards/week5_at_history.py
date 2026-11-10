"""AT1: donor sets redrawn inside the writer bootstrap, with equal budgets.

DESIGN CHECK: LESSONS3--5, 2026-11-07. Metadata matching precedes every fit;
null, personal and shared plants test all three bands. Prompt/future leakage,
unequal token/session budgets, undefined focal fits and exhausted support are
retained as invalid rather than silently replaced by successful-only draws.
"""
from collections import defaultdict
from pathlib import Path
import math,time
import numpy as np
from threadpoolctl import threadpool_limits

from .timing_d33 import cache,cache_probability,WEIGHTS
from .timing_d33_match import earlier,select_sessions,allocated_budgets,truncate_sequences,token_count
from .timing_d33_supported_stats import design,fit,basis
from .timing_stats import sufficient
from .timing_census import read,filehash
from .timing_p6 import gzread,write_equal,progress
from .week5_at_source import authenticate
from .week5_at_analysis import outcome
from .week5_at_scoring import SEED,digest


def equal_budget_history(by_writer,target,donors,genre,*,exclude_prompt=True,match='genre'):
    """Pool selected writers, then use D33's exact session/token matcher."""
    if target['writer'] in donors or len(set(donors))!=len(donors):
        raise ValueError('Donors must be distinct from recipient and each other')
    own=earlier(by_writer[target['writer']],target,exclude_prompt)
    if not own or not sum(map(token_count,own)):return None
    available=[s for w in donors for s in earlier(by_writer[w],target,exclude_prompt)
               if match=='random' or s['genre']==genre]
    if match=='same_prompt':
        selected=[]
        for prompt in sorted({s['prompt'] for s in own}):
            group=select_sessions([s for s in available if s['prompt']==prompt],
                                  [s for s in own if s['prompt']==prompt])
            if group is None:return None
            selected.extend(group['sessions'])
    else:
        group=select_sessions(available,own)
        if group is None:return None
        selected=group['sessions']
    budgets=allocated_budgets([token_count(s) for s in selected],sum(map(token_count,own)))
    trimmed=[dict(s,training_sequences=truncate_sequences(s['training_sequences'],n))
             for s,n in zip(selected,budgets)]
    if len(trimmed)!=len(own) or sum(map(token_count,trimmed))!=sum(map(token_count,own)):
        raise ValueError('Donor budget differs from own history')
    return cache(trimmed,target['timestamp'])


def probability(word,counts,population,mode='mixture'):
    if mode=='mixture':return cache_probability(word,counts,population)
    uni,bi,contexts,total=counts
    if mode=='vocabulary':return (uni[word['token']]+population)/(total+1)
    if mode=='bigram':
        previous=word['context'][-1] if word['context'] else '<s>'
        return (bi[(previous,word['token'])]+population)/(contexts[previous]+1)
    raise ValueError('Unknown history representation')


class HistoryBank:
    def __init__(self,rows,records,roster):
        self.rows=defaultdict(list);self.records={r['session']:r for r in records}
        self.by_writer=defaultdict(list);self.roster=roster
        for r in rows:self.rows[r['writer']].append(r)
        for r in records:self.by_writer[r['writer']].append(r)
        self.writers=sorted(self.rows);self.own_cache={}

    def own(self,writer,exclude_prompt,mode):
        key=(writer,exclude_prompt,mode)
        if key in self.own_cache:return self.own_cache[key]
        calibration=self.roster['writers'][writer]['supported_sessions']['calibration']
        sessions=calibration+sorted({r['session'] for r in self.rows[writer]})
        histories={s:cache(earlier(self.by_writer[writer],self.records[s],exclude_prompt),
                           self.records[s]['timestamp']) for s in sessions}
        losses={a:[] for a in WEIGHTS}
        for sid in calibration:
            for word in self.records[sid]['words']:
                p=word['population_probability']
                if not word['is_word'] or p is None or p<=0:continue
                q=probability(word,histories[sid],p,mode)
                for a in WEIGHTS:losses[a].append(-math.log((1-a)*p+a*q))
        if not losses[0]:return None
        alpha=min(WEIGHTS,key=lambda a:(np.mean(losses[a]),a));values={}
        for row in self.rows[writer]:
            word=self.records[row['session']]['words'][row['index']];p=word['population_probability']
            q=(1-alpha)*p+alpha*probability(word,histories[row['session']],p,mode)
            values[(row['session'],row['index'])]=math.log(p/q)
        self.own_cache[key]=(values,alpha);return values,alpha

    def draw(self,writer,rng,k=5,match='genre',exclude_prompt=True,mode='mixture'):
        parts=self.roster['writers'][writer]
        calibration=parts['supported_sessions']['calibration']
        evaluation=sorted({r['session'] for r in self.rows[writer]})
        all_sessions=calibration+evaluation
        genres=sorted({self.records[s]['genre'] for s in all_sessions})
        # Fixed metadata pool, not selected from a fitted effect or p-value.
        pools={g:sorted(w for w,sessions in self.by_writer.items() if w!=writer and
                       any(s['genre']==g for s in sessions)) for g in genres}
        if match=='random':pools={g:sorted(w for w in self.by_writer if w!=writer) for g in genres}
        own=self.own(writer,exclude_prompt,mode)
        if own is None:return None,dict(redraws=0,reason='own calibration unsupported')
        own_values,own_alpha=own
        if any(len(pool)<k for pool in pools.values()):return None,dict(redraws=0,reason='fewer than k donor writers')
        for attempt in range(21):
            donors={g:rng.choice(pools[g],size=k,replace=False).tolist() for g in genres}
            histories={}
            for sid in all_sessions:
                target=self.records[sid];genre=target['genre']
                histories[sid]=equal_budget_history(self.by_writer,target,donors[genre],genre,
                                                    exclude_prompt=exclude_prompt,match=match)
                if histories[sid] is None:break
            if len(histories)!=len(set(all_sessions)) or any(v is None for v in histories.values()):continue
            losses={a:[] for a in WEIGHTS}
            for sid in calibration:
                for word in self.records[sid]['words']:
                    p=word['population_probability']
                    if not word['is_word'] or p is None or p<=0:continue
                    q=probability(word,histories[sid],p,mode)
                    for a in WEIGHTS:losses[a].append(-math.log((1-a)*p+a*q))
            if not losses[0]:continue
            alpha=min(WEIGHTS,key=lambda a:(np.mean(losses[a]),a))
            candidate=[]
            for row in self.rows[writer]:
                word=self.records[row['session']]['words'][row['index']];p=word['population_probability']
                q=(1-alpha)*p+alpha*probability(word,histories[row['session']],p,mode)
                candidate.append(dict(row,own_surprise=own_values[(row['session'],row['index'])],donor_surprise=math.log(p/q)))
            if np.std([r['donor_surprise'] for r in candidate])<=1e-12:continue
            return candidate,dict(redraws=attempt,alpha=float(alpha),own_alpha=float(own_alpha),donor_sets=donors)
        return None,dict(redraws=20,reason='donor set support exhausted')


def load(inputs,config=None):
    config=config or {}
    source=authenticate(inputs['d33_root']);p6=authenticate(inputs['p6_root'])
    rows=gzread(source/'output/DESIGN.json.gz');roster=read(source/'output/SUPPORTED_ROSTER.json')
    metadata={r['session']:r for r in read(inputs['timing_roster'])}
    records=[]
    for entry in read(p6/'output/P6_INDEX.json'):
        p=p6/'output'/entry['file']
        if filehash(p)!=entry['sha256']:raise ValueError('P6 history changed')
        record=gzread(p);record['genre']=metadata[record['session']]['genre'];records.append(record)
    if config.get('genre'):
        rows=[r for r in rows if metadata[r['session']]['genre']==config['genre']]
    outcome_name=config.get('outcome','log_pause')
    if outcome_name!='log_pause':
        if outcome_name not in ('hesitancy','stop') or 'timing_intervals' not in inputs:
            raise ValueError('Alternate pause outcome requires authenticated timing intervals')
        posterior=gzread(inputs['timing_intervals']);record_map={r['session']:r for r in records}
        for row in rows:
            ordinal=record_map[row['session']]['words'][row['index']]['ordinal']
            matched=[r for r in posterior[row['session']] if r['ordinal']==ordinal and r['onset']]
            if len(matched)!=1:raise ValueError('Alternate pause outcome lacks exact onset')
            row['log_pause']=1-matched[0]['fast'] if outcome_name=='hesitancy' else float(matched[0]['fast']<.5)
    return HistoryBank(rows,records,roster)


def estimate(bank,rng,writer_sample,k,match,exclude_prompt,mode='mixture'):
    groups=[];redraws=0
    for writer in writer_sample:
        rows,audit=bank.draw(writer,rng,k,match,exclude_prompt,mode);redraws+=audit['redraws']
        if rows is None:return None,redraws,audit['reason']
        # Each sampled copy is a separate random-intercept group, including
        # duplicate recipients drawn by the cluster bootstrap.
        x,y,w=design(rows);groups.extend(sufficient(x,y,w))
    try:
        if len(bank.writers)<20:
            keep,_=basis(groups);xx=sum(g['xx'] for g in groups);xy=sum(g['xy'] for g in groups)
            beta=np.linalg.solve(xx[np.ix_(keep,keep)],xy[keep])
            if 0 not in keep or 1 not in keep:raise ValueError('Pooled focal contrast unsupported')
            effect=float(beta[keep.index(0)]-beta[keep.index(1)])
        else:effect=fit(groups)['own_minus_donor']
        return effect,redraws,None
    except ValueError as error:return None,redraws,str(error)


def run(output,inputs,config,verifying=False):
    if config.get('k',5) not in (1,3,5,20) or config.get('match','genre') not in ('genre','random','same_prompt'):
        raise ValueError('Unregistered AT1 matching condition')
    draws=config.get('draws',2000)
    if draws not in (200,2000):raise ValueError('Unregistered uncertainty count')
    if config.get('representation','mixture') not in ('mixture','vocabulary','bigram'):raise ValueError('Unknown cache representation')
    started=time.monotonic();root=Path(output);root.mkdir(parents=True,exist_ok=True);bank=load(inputs,config)
    binding=digest(dict(inputs={k:filehash(Path(v)/'COMPLETE.json') if k.endswith('_root') else filehash(v)
                               for k,v in inputs.items()},config=config))
    args=(config.get('k',5),config.get('match','genre'),not config.get('prompt_included',False),config.get('representation','mixture'))
    with threadpool_limits(limits=2):
        point,redraws,reason=estimate(bank,np.random.default_rng(SEED),bank.writers,*args)
        if point is None:
            result=dict(card='AT1',state='unsupported',reason=reason,donor_redraws=redraws,
                        writers=len(bank.writers),scientific_effect=None)
        else:
            samples=[];failed=[];total_redraws=redraws
            for b in range(draws):
                rng=np.random.default_rng(np.random.SeedSequence([SEED,b,1]))
                chosen=rng.choice(bank.writers,size=len(bank.writers),replace=True).tolist()
                dest=root/f'draw-{b:04d}.json'
                if dest.exists() and not verifying:
                    saved=read(dest)
                    if saved['binding']!=binding or read(dest.with_suffix('.receipt.json'))['sha256']!=filehash(dest):
                        raise ValueError('AT1 checkpoint binding/seal changed')
                else:
                    value,nredraw,error=estimate(bank,rng,chosen,*args)
                    saved=dict(binding=binding,index=b,effect=value,redraws=nredraw,reason=error)
                    if verifying:
                        if read(dest)!=saved:raise ValueError('Complete donor/bootstrap replay differs')
                    else:
                        write_equal(dest,saved);write_equal(dest.with_suffix('.receipt.json'),dict(sha256=filehash(dest)))
                samples.append(saved['effect']);total_redraws+=saved['redraws']
                if saved['effect'] is None:failed.append(b)
                if b%10==0:progress(root/'PROGRESS.json',dict(phase='verify' if verifying else 'bootstrap',draws=b+1,total=draws))
                if not verifying and time.monotonic()-started>config.get('max_wall_seconds',1200) and b+1<draws:
                    return dict(status='yielded',reason='complete donor bootstrap checkpoint',completed=b+1,total=draws)
            result=dict(card='AT1',writers=len(bank.writers),primary=outcome(point,samples,.01) if not failed else
                        dict(state='invalid',reason='Undefined bootstrap fits retained',failed_draws=len(failed)),
                        point=point,donor_redraws=total_redraws,failed_draws=failed,
                        scope='below floor, descriptive' if len(bank.writers)<20 else 'descriptive',
                        k=args[0],match=args[1],prompt_excluded=args[2],representation=args[3],
                        estimator='pooled descriptive fallback' if len(bank.writers)<20 else 'writer random intercept')
    if verifying:
        if read(root/'RESULT.json')!=result:raise ValueError('AT1 reduction replay differs')
        return dict(verified=True,complete_donor_redraw_refit=True)
    write_equal(root/'BINDING.json',dict(sha256=binding));write_equal(root/'RESULT.json',result)
    return dict(status='complete',card='AT1')


def run_block(output,inputs,config,verifying=False):
    """Fixed global bootstrap indices, independently re-created in each block."""
    start,count,total=config['draw_start'],config['draw_count'],config.get('draws',2000)
    if total not in (200,2000) or type(start) is not int or type(count) is not int or not 0<=start<total or not 1<=count<=100 or start+count>total:
        raise ValueError('Invalid fixed bootstrap block')
    science={k:v for k,v in config.items() if k not in ('draw_start','draw_count','max_wall_seconds')}
    if science.get('k',5) not in (1,3,5,20) or science.get('match','genre') not in ('genre','random','same_prompt'):
        raise ValueError('Unregistered AT1 block condition')
    bank=load(inputs,science);root=Path(output);root.mkdir(parents=True,exist_ok=True)
    binding=digest(dict(inputs={k:filehash(Path(v)/'COMPLETE.json') if k.endswith('_root') else filehash(v)
                               for k,v in inputs.items()},config=science))
    args=(science.get('k',5),science.get('match','genre'),not science.get('prompt_included',False),science.get('representation','mixture'))
    values=[];point=None
    with threadpool_limits(limits=2):
        if start==0:
            value,redraws,error=estimate(bank,np.random.default_rng(SEED),bank.writers,*args)
            point=dict(effect=value,redraws=redraws,reason=error)
        for b in range(start,start+count):
            rng=np.random.default_rng(np.random.SeedSequence([SEED,b,1]))
            chosen=rng.choice(bank.writers,size=len(bank.writers),replace=True).tolist()
            value,redraws,error=estimate(bank,rng,chosen,*args)
            values.append(dict(index=b,effect=value,redraws=redraws,reason=error))
            progress(root/'PROGRESS.json',dict(phase='verify' if verifying else 'donor_refit',completed=b-start+1,total=count))
    result=dict(binding=binding,science=science,total_draws=total,start=start,count=count,values=values,
                point=point,writers=len(bank.writers),scientific_admission=False)
    if verifying:
        if read(root/'BLOCK.json')!=result:raise ValueError('Independent donor block replay differs')
        return dict(verified=True,complete_global_draw_refit=True)
    write_equal(root/'BLOCK.json',result);return dict(status='complete',scientific_admission=False,draw_start=start,draw_count=count)


def reduce_blocks(output,inputs,config,verifying=False):
    if set(inputs)!={'blocks'} or config!={}:raise ValueError('Exact AT1 reduction inputs required')
    paths=read(inputs['blocks']);blocks=[]
    for path in paths:
        source=authenticate(path);blocks.append(read(source/'output/BLOCK.json'))
    result=reduce_values(blocks)
    root=Path(output)
    if verifying:
        if read(root/'RESULT.json')!=result:raise ValueError('Complete donor reduction replay differs')
        return dict(verified=True,complete_verified_block_reduction=True)
    write_equal(root/'RESULT.json',result);return dict(status='complete',card='AT1')


def reduce_values(blocks):
    """Pure exact reduction, also exercised by the native constructed fixture."""
    if not blocks:raise ValueError('No donor refit blocks')
    first=blocks[0]
    if any(any(b[k]!=first[k] for k in ('binding','science','total_draws','writers')) for b in blocks):
        raise ValueError('Mixed donor refit estimands')
    samples=sorted([r for b in blocks for r in b['values']],key=lambda r:r['index'])
    if [r['index'] for r in samples]!=list(range(first['total_draws'])):raise ValueError('Incomplete or duplicate donor uncertainty')
    points=[b['point'] for b in blocks if b['point'] is not None]
    if len(points)!=1:raise ValueError('Donor point estimate must appear exactly once')
    point=points[0];failed=[r['index'] for r in samples if r['effect'] is None]
    if point['effect'] is None:
        primary=dict(state='unsupported',reason=point['reason'])
    elif failed:primary=dict(state='invalid',reason='Undefined donor resamples retained',failed_draws=len(failed))
    else:primary=outcome(point['effect'],[r['effect'] for r in samples],.01)
    result=dict(card='AT1',primary=primary,point=point['effect'],writers=first['writers'],
                donor_redraws=point['redraws']+sum(r['redraws'] for r in samples),failed_draws=failed,
                estimator='pooled descriptive fallback' if first['writers']<20 else 'writer random intercept',
                config=first['science'],complete_draws=len(samples),descriptive=True,
                screening_only=first['total_draws']==200)
    return result


def execute(output,inputs,config):
    if 'blocks' in inputs:return reduce_blocks(output,inputs,config)
    if 'draw_start' in config:return run_block(output,inputs,config)
    return run(output,inputs,config)
def verify(output,inputs,config):
    if 'blocks' in inputs:return reduce_blocks(output,inputs,config,True)
    if 'draw_start' in config:return run_block(output,inputs,config,True)
    return run(output,inputs,config,True)
