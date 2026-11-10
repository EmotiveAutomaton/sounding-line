"""AT1 checkpointed successor; every frozen global donor RNG and fit unchanged."""
from pathlib import Path
import time
import numpy as np
from threadpoolctl import threadpool_limits
from . import week5_at_history as original
from .timing_census import read,filehash
from .timing_p6 import write_equal,progress


def run_block(output,inputs,config,verifying=False):
    start,count,total=config['draw_start'],config['draw_count'],config.get('draws',2000)
    if total not in (200,2000) or type(start) is not int or type(count) is not int or not 0<=start<total or not 1<=count<=100 or start+count>total:
        raise ValueError('Invalid fixed bootstrap block')
    science={k:v for k,v in config.items() if k not in ('draw_start','draw_count','max_wall_seconds')}
    if science.get('k',5) not in (1,3,5,20) or science.get('match','genre') not in ('genre','random','same_prompt'):
        raise ValueError('Unregistered AT1 block condition')
    quantum=float(config.get('max_wall_seconds',1200))
    if not 30<=quantum<=1500:raise ValueError('Bounded AT1 quantum required')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);began=time.monotonic()
    def paused():return (root/'YIELD_REQUEST.json').exists() or time.monotonic()-began>=quantum
    if paused():return dict(status='yielded',reason='resource request before history load',completed=0,total=count)
    bank=original.load(inputs,science)
    binding=original.digest(dict(inputs={k:filehash(Path(v)/'COMPLETE.json') if k.endswith('_root') else filehash(v) for k,v in inputs.items()},config=science))
    args=(science.get('k',5),science.get('match','genre'),not science.get('prompt_included',False),science.get('representation','mixture'))
    def sealed(path,expected_index,calculate):
        seal=path.with_suffix('.receipt.json')
        if path.exists() and not verifying:
            saved=read(path)
            if not seal.exists() or read(seal)['sha256']!=filehash(path):raise ValueError('Donor checkpoint seal differs')
        else:
            saved=dict(binding=binding,index=expected_index,value=calculate())
            if verifying:
                if not seal.exists() or read(seal)['sha256']!=filehash(path) or read(path)!=saved:
                    raise ValueError('Independent donor checkpoint replay differs')
            else:
                write_equal(path,saved);write_equal(seal,dict(sha256=filehash(path)))
        if saved['binding']!=binding or saved['index']!=expected_index:raise ValueError('Donor checkpoint binding or index differs')
        return saved['value']
    values=[];point=None
    with threadpool_limits(limits=2):
        if start==0:
            def point_fit():
                value,redraws,error=original.estimate(bank,np.random.default_rng(original.SEED),bank.writers,*args)
                return dict(effect=value,redraws=redraws,reason=error)
            point=sealed(root/'point.json','point',point_fit)
            if paused():return dict(status='yielded',reason='sealed donor point boundary',completed=0,total=count)
        for index in range(start,start+count):
            def draw_fit():
                rng=np.random.default_rng(np.random.SeedSequence([original.SEED,index,1]))
                chosen=rng.choice(bank.writers,size=len(bank.writers),replace=True).tolist()
                value,redraws,error=original.estimate(bank,rng,chosen,*args)
                return dict(index=index,effect=value,redraws=redraws,reason=error)
            values.append(sealed(root/f'draw-{index:04d}.json',index,draw_fit))
            progress(root/'PROGRESS.json',dict(phase='verify' if verifying else 'donor_refit',completed=len(values),total=count,global_index=index))
            if len(values)<count and paused():return dict(status='yielded',reason='sealed global donor draw boundary',completed=len(values),total=count)
    result=dict(binding=binding,science=science,total_draws=total,start=start,count=count,values=values,point=point,writers=len(bank.writers),scientific_admission=False)
    if verifying:
        if read(root/'BLOCK.json')!=result:raise ValueError('Independent donor block reduction differs')
        return dict(verified=True,complete_global_draw_refit=True,sealed_checkpoints=True)
    write_equal(root/'BLOCK.json',result);return dict(status='complete',scientific_admission=False,draw_start=start,draw_count=count)


def execute(output,inputs,config):
    if 'blocks' in inputs:return original.reduce_blocks(output,inputs,config)
    if 'draw_start' not in config:raise ValueError('Checkpointed successor requires explicit bounded blocks')
    return run_block(output,inputs,config)


def verify(output,inputs,config):
    if 'blocks' in inputs:return original.reduce_blocks(output,inputs,config,True)
    if 'draw_start' not in config:raise ValueError('Checkpointed successor requires explicit bounded blocks')
    return run_block(output,inputs,config,True)
