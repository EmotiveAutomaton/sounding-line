"""Whole-writer sample view of the unchanged S1 nuisance consumer.

DESIGN CHECK: Week4 amendments E/G; LESSONS3-5, especially source support,
canonical random ordering and full admission, reread in this build.
NULL/ALTERNATIVE: selection never reads outcomes or changes nuisance values.
Constructed checks preserve whole writers, proportional genre allocation,
source order invariance and an independently reconstructed manifest. Changed
membership refuses. Full source/histories remain intact; scope is sample only.
"""
from collections import Counter,defaultdict
from pathlib import Path
from types import FunctionType
import numpy as np
from . import week4_s1_nuisance as original
from . import week4_s1_nuisance_v2 as corrected
from .timing_census import read
from .timing_p6 import write_equal

configuration=original.configuration
SEED=20261102

def writer_frame(records):
    genres=defaultdict(Counter)
    for row in records:genres[row['writer']][row['genre']]+=1
    return [dict(writer=w,genre=sorted(g,key=lambda k:(-g[k],k))[0]) for w,g in sorted(genres.items())]

def select_writers(frame,size):
    if not isinstance(size,int) or isinstance(size,bool) or not 1<=size<=len(frame):
        raise ValueError('Invalid whole-writer sample size')
    if len({r['writer'] for r in frame})!=len(frame):raise ValueError('Duplicate sampling identity')
    groups=defaultdict(list)
    for row in sorted(frame,key=lambda r:r['writer']):groups[row['genre']].append(row['writer'])
    quotas={g:size*len(v)//len(frame) for g,v in groups.items()}
    remainder=sorted(groups,key=lambda g:(-(size*len(groups[g])%len(frame)),g))
    for g in remainder[:size-sum(quotas.values())]:quotas[g]+=1
    rng=np.random.default_rng(SEED);selected=[]
    for g in sorted(groups):selected.extend(rng.permutation(groups[g]).tolist()[:quotas[g]])
    return sorted(selected)

def validate_sample(records,manifest):
    frame=writer_frame(records)
    if manifest.get('seed')!=SEED or manifest.get('frame')!=frame:
        raise ValueError('Sample source frame changed')
    selected=select_writers(frame,manifest['sample_size'])
    if manifest.get('selected_writers')!=selected:raise ValueError('Frozen sample membership differs')
    return selected

def sampled_view(values,manifest):
    records,windows,intervals,by_writer,medians=values
    selected=set(validate_sample(records,manifest))
    return (records,[w for w in windows if w['writer'] in selected],intervals,by_writer,medians)

def known_checks():
    frame=[dict(writer=str(i),genre='a' if i<6 else 'b') for i in range(12)]
    chosen=select_writers(frame,6)
    assert len(chosen)==len(set(chosen))==6
    assert sum(int(w)<6 for w in chosen)==3
    assert chosen==select_writers(list(reversed(frame)),6)
    assert select_writers(frame,12)==sorted(r['writer'] for r in frame)
    return dict(proportional_genre_sample=True,whole_writer_unique=True,canonical_input_order=True,full_frame_preserved=True)

def run(output,inputs,config,verification=False):
    scope={}
    def load(source):
        if set(source)!={'histories_completion','typing_completion','pmap_completion','sample_manifest'}:
            raise ValueError('Exact sample inputs required')
        values=original.load({k:v for k,v in source.items() if k!='sample_manifest'})
        records,windows,intervals,by_writer,medians=values
        manifest=read(source['sample_manifest']);selected=set(validate_sample(records,manifest))
        scope.update(seed=SEED,population_writers=len(manifest['frame']),sample_writers=len(selected),
            selected_writers=sorted(selected),source_sessions=len(windows),
            sampled_sessions=sum(w['writer'] in selected for w in windows),
            scope='Whole-writer sample; original full-population source and history matches preserved.')
        return sampled_view(values,manifest)
    def checks():return dict(corrected.known_check(),**known_checks())
    runner=FunctionType(original.run.__code__,dict(original.run.__globals__,load=load,
        features=corrected.features,known_check=checks),original.run.__name__,
        original.run.__defaults__,original.run.__closure__)
    result=runner(output,inputs,config,verification)
    value=scope or dict(scope='Constructed sample interface; no corpus accessed.',checks=known_checks())
    path=Path(output)/'SAMPLE_SCOPE.json'
    if verification:
        if read(path)!=value:raise ValueError('Sample scope replay differs')
    else:write_equal(path,value)
    return result

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
