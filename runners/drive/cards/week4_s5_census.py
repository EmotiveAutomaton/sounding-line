"""S5 complete descriptive census after an unsupported primary.

DESIGN CHECK: all 61,504 source rows and every excluded interval are retained
through the completed parent binding. No support threshold is relaxed and no
primary is fit. This completes a reporting omission in the original branch;
the empirical inability to test is not healed. Mixture failures stay explicit.
"""
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
from threadpoolctl import threadpool_limits
from .week4_s5_h1 import descriptive_mixtures
from .timing_p6 import write_equal,gzread
from .timing_census import read,filehash

CONFIG=dict(card='S5-descriptive-census',parent_state='design cannot test',expected_rows=61504)
def distribution(rows):
    values=[r['gap_seconds'] for r in rows]
    return dict(n=len(rows),authors=len({r['author'] for r in rows}),
        quantiles=np.quantile(values,[0,.25,.5,.75,1]).tolist() if values else None,
        mean_log_relative_gap=float(np.mean([r['log_relative_gap'] for r in rows])) if rows else None)

def summarize(rows):
    groups={}
    for key in ('category','label'):
        groups[key]={}
        for value in sorted({r[key] for r in rows}):
            sub=[r for r in rows if r[key]==value];start='high_start' if key=='category' else 'fine_start'
            groups[key][value]={name:distribution([r for r in sub if predicate(r)]) for name,predicate in [
                ('run_starts',lambda r:r[start] and not r['break_gap']),
                ('inside_runs',lambda r:not r[start] and not r['break_gap']),
                ('long_breaks',lambda r:r['break_gap'])]}
    with threadpool_limits(limits=1):mixtures=descriptive_mixtures(rows)
    aggregate={}
    for key in ('category','label'):
        aggregate[key]={}
        for value in groups[key]:
            means=[v['by_'+key][value]['posterior_means'] for v in mixtures.values() if
                v['state']=='fitted descriptive mixture' and value in v['by_'+key] and v['by_'+key][value]['n']]
            aggregate[key][value]=dict(author_ids=len(means),equal_author_posterior_mean=np.mean(means,axis=0).tolist() if means else None)
    return dict(distributions=groups,posteriors=aggregate,mixture_states=dict(Counter(v['state'] for v in mixtures.values())),
        primary='design cannot test; no relaxed floor or primary fit',descriptive_only=True),mixtures

def run(output,inputs,config,verification=False):
    if config!=CONFIG or set(inputs)!={'parent_completion'}:raise ValueError('Frozen census required')
    parent=Path(inputs['parent_completion']).parent;c=read(parent/'COMPLETE.json');s=read(parent/'output/SUMMARY.json')
    if not c['fresh_process_verified'] or s['state']!='design cannot test' or s['audit']['released_rows']!=61504:raise ValueError('Parent support state changed')
    for name,h in c['outputs'].items():
        if filehash(parent/name)!=h:raise ValueError('Parent bytes changed')
    rows=gzread(parent/'output/GAPS.json.gz');summary,private=summarize(rows)
    summary.update(parent_sha256=filehash(parent/'COMPLETE.json'),audit=s['audit'],qualifying_author_ids=s['qualifying_author_ids'])
    output=Path(output)
    if verification:
        if read(output/'SUMMARY.json')!=summary or read(output/'PRIVATE_MIXTURES.json')!=private:raise ValueError('Complete descriptive replay differs')
        return dict(verified=True,full_census_replay=True)
    write_equal(output/'SUMMARY.json',summary);write_equal(output/'PRIVATE_MIXTURES.json',private)
    return dict(status='complete',scientific_admission=False)
def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
