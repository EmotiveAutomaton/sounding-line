"""0010 source adapter for repeated records of a single released trait."""
from pathlib import Path
import sys
import time
import numpy as np
import pandas as pd
from . import week7_trait_v1 as trait
from .week7_trait_v1 import old, binding, sources, evaluate
from .batch_runtime import atomic,filehash,freeze,now,read


def unique_traits(rows):
    if rows.id.isna().any(): raise ValueError('Missing person key in trait release')
    score=pd.to_numeric(rows.neuroticism,errors='raise')
    g=score.groupby(rows.id)
    if (g.nunique(dropna=True)>1).any():raise ValueError('Conflicting observed trait scores')
    return g.first().rename('neuroticism').reset_index()


def operate(output,inputs,config,replay):
    path,pin=binding(config['card'],config['member'],inputs['data_root'])
    _,static=sources(read(Path.cwd()/'.agent-state/data_collection_root.json'))
    if pin!=inputs['source_sha256'] or inputs['manifest_sha256']!=old.MANIFEST:raise ValueError('Different source')
    rows=pd.read_csv(static,sep='\t',usecols=['id','neuroticism'],dtype={'id':str})
    scores,panels,report=trait.parts(pd.read_csv(path,sep='\t',usecols=trait.COLUMNS,dtype={'id':str}),unique_traits(rows),replay)
    report.update(static_rows=len(rows),static_people=rows.id.nunique(),repeated_static_ids=int((rows.id.value_counts()>1).sum()))
    data=trait.core.Prepared(len(scores),report)
    data.panels['trait']=(scores,panels)
    data.specs={k:{} for k in [*trait.FEELINGS,*(a+'_minus_'+b for a,b in trait.combinations(trait.NEGATIVE,2))]}
    d=Path(output)/('verify' if replay else 'execute')
    start=time.monotonic()
    def guard():
        if time.monotonic()-start>=config['max_wall_seconds'] or any((Path(output)/k).exists() for k in ('YIELD_REQUEST.json','STOP_REQUEST.json')):
            raise trait.RequestedYield('runtime limit')
    def progress(n,t):atomic(d/'DRAW_PROGRESS.json',dict(at=now(),committed_draws=n,elapsed=t))
    try:
        result=trait.bank.run(d,sys.modules[__name__],data,member='0010',source_digest=pin,seed=202611190010,guard=guard,
            verify=replay,execute_dir=Path(output)/'execute',limit=config['max_new_draws'],progress=progress)
    except trait.RequestedYield as exc:return dict(status='yielded',verified=False,reason=str(exc))
    dest=d/'ENGINE_RESULT.json'
    if dest.exists():
        if read(dest)!=result:raise ValueError('Inconsistent completed result')
    else:freeze(dest,result)
    return dict(status='verified' if replay else 'computed',verified=replay,engine_sha256=filehash(dest),draw_count=2000)

def execute(output,inputs,config):return operate(output,inputs,config,False)
def verify(output,inputs,config):return operate(output,inputs,config,True)
