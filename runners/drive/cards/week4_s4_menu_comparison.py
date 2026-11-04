"""S4(b) descriptive browsing reliability and chosen-option history similarity.

DESIGN CHECK: LESSONS 3-5, CONTROLS 1-3 reread November 3. Known equal,
positive and reversed writer contrasts must retain their answers. Unsupported
writers and undefined correlations remain explicit, never filled or rescued.
There is no scientific gate or causal/personal-mechanism admission here.
"""
from pathlib import Path
from collections import Counter, defaultdict
import math
import time
import numpy as np
from .timing_census import read, filehash
from .timing_p6 import gzread, gzip_equal, write_equal
from .timing_pmap_source import completed

ARMS=('pointer','keyboard','both','neither')


def configuration(mode):
    if mode not in ('constructed','full'):raise ValueError('Unknown comparison scope')
    return dict(card='S4-menu-comparison',mode=mode,seed=20261102,bootstrap=2000)


def correlation(x,y):
    if len(x)<3:return None
    a=np.asarray(x,float)-np.mean(x);b=np.asarray(y,float)-np.mean(y)
    den=float(np.linalg.norm(a)*np.linalg.norm(b))
    return float(np.dot(a,b)/den) if den>1e-15 else None


def estimate(rows,bootstrap=2000,seed=20261102):
    if not rows or len({r['key'] for r in rows})!=len(rows):raise ValueError('Empty or duplicate menu source')
    grouped=defaultdict(list)
    for r in rows:
        if r['navigation']['arm'] not in ARMS or r['half'] not in (0,1):raise ValueError('Unknown source arm or half')
        grouped[r['writer']].append(r)
    writers=[];effects=[];pairs=[]
    for writer,rs in sorted(grouped.items()):
        counts=Counter(r['navigation']['arm'] for r in rs)
        denominator=counts['pointer']+counts['keyboard']
        shares=[]
        for half in (0,1):
            c=Counter(r['navigation']['arm'] for r in rs if r['half']==half);n=c['pointer']+c['keyboard']
            shares.append(c['pointer']/n if n else None)
        chosen={arm:[] for arm in ARMS};missing=Counter()
        for r in rs:
            k=r['dismissal_index'];choice=r['canonical_choice'];v=r['option_own_cosines']
            if type(k)!=int or k<1 or choice is not None and (type(choice)!=int or not 0<=choice<=k):raise ValueError('Invalid canonical choice')
            accepted=r['handling'] in ('accept','edit')
            if accepted!=(choice is not None and choice<k):raise ValueError('Canonical choice/handling disagree')
            if v is not None and (len(v)!=k or not all(math.isfinite(x) and abs(x)<=1+1e-5 for x in v)):raise ValueError('Invalid option similarity')
            if not accepted:missing['not_a_chosen_option']+=1;continue
            if v is None:missing['no_earlier_history']+=1;continue
            chosen[r['navigation']['arm']].append(float(v[choice]))
        arm_means={arm:float(np.mean(v)) if v else None for arm,v in chosen.items()}
        difference=arm_means['pointer']-arm_means['keyboard'] if chosen['pointer'] and chosen['keyboard'] else None
        if difference is not None:effects.append(difference)
        if all(x is not None for x in shares):pairs.append(shares)
        writers.append(dict(writer=writer,counts={a:counts[a] for a in ARMS},pointer_share=counts['pointer']/denominator if denominator else None,
                            half_shares=shares,chosen_counts={a:len(chosen[a]) for a in ARMS},chosen_means=arm_means,difference=difference,excluded=dict(missing)))
    rng=np.random.default_rng(seed)
    bank=[]
    if len(effects)>=2:
        a=np.asarray(effects);bank=a[rng.integers(len(a),size=(bootstrap,len(a)))].mean(1).tolist()
    reliability=correlation(*np.asarray(pairs).T) if pairs else None
    rb=[]
    if reliability is not None:
        a=np.asarray(pairs)
        for ids in rng.integers(len(a),size=(bootstrap,len(a))):
            rb.append(correlation(a[ids,0],a[ids,1]))
    invalid=sum(x is None for x in rb)
    summary=dict(writers=len(writers),menus=len(rows),browsing_counts={a:sum(w['counts'][a] for w in writers) for a in ARMS},
        pointer_share_defined=sum(w['pointer_share'] is not None for w in writers),
        paired_effect_writers=len(effects),effect=float(np.mean(effects)) if bank else None,
        effect_ci95=np.quantile(bank,[.025,.975]).tolist() if bank else None,
        reliability_paired_writers=len(pairs),reliability=reliability,
        reliability_ci95=np.quantile(rb,[.025,.975]).tolist() if rb and not invalid else None,
        reliability_undefined_bootstraps=invalid,bootstrap=bootstrap,seed=seed,
        descriptive_only=True,p_value=None,scientific_promotion=False,
        undefined_effect_reason=None if bank else 'fewer than two writers with choices in both exclusive arms',
        undefined_reliability_reason=None if reliability is not None else 'fewer than three paired writers or zero share variance')
    return dict(summary=summary,writers=writers,effect_bootstraps=bank,reliability_bootstraps=rb)


def scalar_check(rows,value):
    expected=[]
    for w in value['writers']:
        rs=[r for r in rows if r['writer']==w['writer']]
        a=[];b=[]
        for r in rs:
            if r['handling'] in ('accept','edit') and r['option_own_cosines'] is not None:
                if r['navigation']['arm']=='pointer':a.append(r['option_own_cosines'][r['canonical_choice']])
                elif r['navigation']['arm']=='keyboard':b.append(r['option_own_cosines'][r['canonical_choice']])
        d=sum(a)/len(a)-sum(b)/len(b) if a and b else None
        assert (d is None)==(w['difference'] is None)
        if d is not None:assert abs(d-w['difference'])<1e-12;expected.append(d)
    if len(expected)>=2:assert abs(sum(expected)/len(expected)-value['summary']['effect'])<1e-12


def fixture(delta=.25,writers=61,per_half=140):
    rows=[]
    for w in range(writers):
        for half in (0,1):
            for i in range(per_half):
                arm='pointer' if i<(w%50+20) else 'keyboard'
                rows.append(dict(key=f'{w}:{half}:{i}',writer=str(w),half=half,navigation=dict(arm=arm),handling='accept',
                                 canonical_choice=1,dismissal_index=2,option_own_cosines=[-.5,.25+(delta if arm=='pointer' else 0.)]))
    return rows


def constructed(config):
    result={}
    for name,delta in (('positive',.25),('equal',0.),('reversed',-.25)):
        rows=fixture(delta);v=estimate(rows,config['bootstrap'],config['seed']);scalar_check(rows,v)
        assert v['summary']['effect']==delta and v['summary']['effect_ci95']==[delta,delta]
        assert abs(v['summary']['reliability']-1)<1e-12
        result[name]=v
    return result


def run(output,inputs,config,verification=False):
    if config!=configuration(config['mode']):raise ValueError('Frozen comparison configuration required')
    started=time.process_time();output=Path(output)
    if config['mode']=='constructed':
        if inputs:raise ValueError('No human inputs in constructed run')
        values=constructed(config)
        summary=dict(mode='constructed',cases=list(values),writers_per_case=61,menus_per_case=17080,bootstrap=2000,
                     equal_positive_reversed=True,known_reliability=True,human_result_computed=False)
    else:
        if set(inputs)!={'source_completion'}:raise ValueError('Exact full source required')
        c=Path(inputs['source_completion']);source=c.parent/'output'
        for n in ('SUMMARY.json','PRIVATE_ROWS.json.gz'):completed(c,source/n)
        s=read(source/'SUMMARY.json')
        if s['mode']!='full' or not s['complete_population']:raise ValueError('Full population source required')
        rows=gzread(source/'PRIVATE_ROWS.json.gz')
        if len(rows)!=s['menus'] or s['menus']>17080 or s['writers']>61:raise ValueError('Measured workload envelope exceeded')
        values=estimate(rows,config['bootstrap'],config['seed']);scalar_check(rows,values)
        summary=dict(values['summary'],mode='full',source_completion_sha256=filehash(c),source_summary=s)
    if verification:
        if read(output/'SUMMARY.json')!=summary or gzread(output/'PRIVATE_BANKS.json.gz')!=values:raise ValueError('Complete statistic replay differs')
        return dict(verified=True,complete_statistic_replay=True,scalar_writer_check=True)
    write_equal(output/'SUMMARY.json',summary);gzip_equal(output/'PRIVATE_BANKS.json.gz',values)
    write_equal(output/'TIMING.json',dict(cpu_seconds=time.process_time()-started))
    return dict(status='complete',descriptive_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
