"""SL2 paired writer and crossed writer/prompt sensitivity, conditional on training.

DESIGN CHECK: LESSONS 3-5. NULL: zero paired differences give zero intervals;
replicating rows within one writer never creates writers. ALTERNATIVE: an effect
across writers survives dependence sensitivity. Wide bounds prohibit parity.
"""
from collections import defaultdict
import numpy as np
from .statistics_v2 import paired

def contrast(rows,left,right,draws=4000):
    base=paired(rows,left,right,draws)
    if base['writers']<2:return base|dict(left=left,right=right,prompts=len({r['prompt'] for r in rows}),crossed_writer_prompt_interval=None,writer_signflip_null_interval=None,dependence='A single writer cannot estimate writer population uncertainty.')
    writers=sorted({r['writer'] for r in rows}); prompts=sorted({r['prompt'] for r in rows})
    cells=defaultdict(list)
    for r in rows:cells[(r['writer'],r['prompt'])].append(r['scores'][left]['half_brier']-r['scores'][right]['half_brier'])
    value=np.zeros((len(writers),len(prompts)));count=np.zeros_like(value)
    for i,w in enumerate(writers):
        for j,p in enumerate(prompts):
            if cells[(w,p)]:value[i,j]=np.mean(cells[(w,p)]);count[i,j]=1
    rng=np.random.default_rng(141011);cross=[]
    for _ in range(draws):
        ww=rng.multinomial(len(writers),np.ones(len(writers))/len(writers))
        pw=rng.multinomial(len(prompts),np.ones(len(prompts))/len(prompts))
        denominator=count@pw;eligible=(denominator>0)&(ww>0)
        if eligible.any():cross.append(float(np.average((value@pw)[eligible]/denominator[eligible],weights=ww[eligible])))
    wd=np.array([np.mean([r['scores'][left]['half_brier']-r['scores'][right]['half_brier'] for r in rows if r['writer']==w]) for w in writers])
    signed=(rng.choice([-1,1],size=(draws,len(writers)))*wd).mean(axis=1)
    return base|dict(left=left,right=right,prompts=len(prompts),crossed_writer_prompt_interval=np.quantile(cross,[.025,.975]).tolist(),
        writer_signflip_null_interval=np.quantile(signed,[.025,.975]).tolist(),
        dependence='Intervals condition on fixed past-only training/donor roster; crossed prompt sensitivity resamples fixed stimuli, not a new-stimulus claim.')
