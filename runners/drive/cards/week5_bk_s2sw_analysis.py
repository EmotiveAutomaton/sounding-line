"""Descriptive S2.sw released-change timing and later span overlap.

DESIGN CHECK: LESSONS 2-5, BK_S2SW.md. Never upgrade the absent physical
word-onset construct. Full cluster draws and within-segment references precede
reporting; no unidentified draw is dropped. Null and opposite-sign fixtures
exercise the same controlled contrast, including below-floor pooled output.
"""
from collections import Counter, defaultdict
from pathlib import Path
import math, time
import numpy as np
from threadpoolctl import threadpool_limits
from .week5_bk_s2sw_source import CONTROL_NAMES, SEED
from .week5_bk_klicke_intake import read, write, digest
from .timing_pmap_source import completed
from . import week5_bk_s2_analysis as numerical

CELLS = ('overlap','sentence_nonlocal','paragraph_nonlocal','within_two_minutes','later_than_two_minutes')


def source(inputs, mode):
    if set(inputs) != {'source_complete'}: raise ValueError('Exact completed source required')
    complete = Path(inputs['source_complete']); root = complete.parent; out = root/'output'
    for path in (root/'PLAN.json',root/'VERIFIED.json',out/'SUMMARY.json',out/'PRIVATE_SPANS.json.gz'): completed(complete,path)
    plan = read(root/'PLAN.json'); proof = read(root/'VERIFIED.json'); summary = read(out/'SUMMARY.json')
    if plan['module'] != 'runners.drive.cards.week5_bk_s2sw_source' or proof.get('complete_source_replay') is not True or proof.get('verified') is not True:
        raise ValueError('Whole source independent replay required')
    if plan['config']['mode'] != mode or summary['constructed'] != (mode=='constructed') or not summary['complete_population']:
        raise ValueError('Source mode or completeness changed')
    records = read(out/'PRIVATE_SPANS.json.gz')
    if len(records) != summary['census']['project_scoped_authors']: raise ValueError('Source author roster changed')
    if mode=='corpus' and (len(records) != 12 or summary['census']['rows'] != 61504): raise ValueError('Whole source population required')
    return records, summary, digest(complete)


def select(records, cell):
    rows = []; counts = Counter(); annotations = Counter()
    for author in records:
        for unit in author['units']:
            counts['production_spans'] += 1
            if unit['timing_state'] != 'eligible released-change proxy': counts['excluded_'+unit['timing_state']] += 1; continue
            if unit['class'] not in ('flow_proxy','hesitant_proxy'): counts['middle_or_tie'] += 1; continue
            if not unit['observed_later_rows']: counts['right_censored_no_later_row'] += 1; continue
            if cell in ('within_two_minutes','later_than_two_minutes') and unit['remaining_seconds'] < 120:
                counts['right_censored_before_two_minutes'] += 1; continue
            future = unit['later_edits']
            if cell=='sentence_nonlocal': future = [r for r in future if r['visible_sentence_nonlocal']]
            elif cell=='paragraph_nonlocal': future = [r for r in future if r['visible_paragraph_nonlocal']]
            elif cell=='within_two_minutes': future = [r for r in future if r['lag_seconds'] <= 120]
            elif cell=='later_than_two_minutes': future = [r for r in future if r['lag_seconds'] > 120]
            if set(unit['controls']) != set(CONTROL_NAMES) or not all(math.isfinite(v) for v in unit['controls'].values()):
                raise ValueError('Missing or nonfinite control')
            rows.append(dict(writer=author['author'],project=author['project'],session=unit['session'],
                flow=int(unit['class']=='flow_proxy'),outcome=int(bool(future)),controls=unit['controls'],
                events=[(unit['session'],r['ordinal']) for r in future]))
            annotations.update(r['label'] for r in future)
    counts['analytical_spans'] = len(rows); counts['source_authors'] = len(records)
    counts['distinct_later_edit_events'] = len({tuple(e) for r in rows for e in r['events']})
    return rows,dict(counts),dict(annotations)


def arrays(rows):
    if not rows: raise ValueError('No analytical spans')
    writers = sorted({r['writer'] for r in rows}); lookup = {w:i for i,w in enumerate(writers)}
    x = np.array([[r['flow']]+[r['controls'][k] for k in CONTROL_NAMES] for r in rows],float)
    y = np.array([r['outcome'] for r in rows],float); g = np.array([lookup[r['writer']] for r in rows])
    means = np.array([x[g==i].mean(0) for i in range(len(writers))]); ym = np.array([y[g==i].mean() for i in range(len(writers))])
    xc=x-means[g];yc=y-ym[g]; scale=xc.std(0)
    if scale[0] <= 1e-12: raise ValueError('No within-author timing contrast')
    nuisance = xc[:,1:]; residual = xc[:,0]-nuisance@np.linalg.lstsq(nuisance,xc[:,0],rcond=1e-10)[0]
    if np.dot(residual,residual) <= 1e-10*np.dot(xc[:,0],xc[:,0]): raise ValueError('Timing contrast aliased with nuisance controls')
    keep=[0];rank=1
    for j in np.flatnonzero(scale>1e-12):
        if j==0: continue
        proposal=xc[:,keep+[j]]/scale[keep+[j]]; new=np.linalg.matrix_rank(proposal,tol=1e-9)
        if new>rank:keep.append(int(j));rank=new
    z=xc[:,keep]/scale[keep]
    stats=[dict(xx=z[g==i].T@z[g==i],xy=z[g==i].T@yc[g==i]) for i in range(len(writers))]
    return dict(x=x,y=y,g=g,xc=xc,yc=yc,z=z,means=means,ym=ym,scale=scale[keep],keep=keep,stats=stats,writers=writers)


def point(bundle):
    effect=numerical.coefficient(bundle)
    try:
        result=numerical.random_intercept_fit(bundle);result.pop('_design')
        result['nuisance_columns_dropped']=[CONTROL_NAMES[j-1] for j in range(1,len(CONTROL_NAMES)+1) if j not in bundle['keep']]
    except (ValueError, TypeError, np.linalg.LinAlgError):
        result=dict(effect=effect,random_intercept_state='unavailable or degenerate likelihood; exact within-author coefficient retained')
    return result


def initial(records,cell):
    rows,counts,annotations=select(records,cell)
    arms={str(arm):[r['outcome'] for r in rows if r['flow']==arm] for arm in (0,1)}
    pooled=(float(np.mean(arms['1'])-np.mean(arms['0'])) if all(arms.values()) else None)
    both={w for w in {r['writer'] for r in rows} if len({r['flow'] for r in rows if r['writer']==w})==2}
    counts['both_arm_authors']=len(both)
    summary=dict(card='BK-S2.sw',cell=cell,counts=counts,overlap_annotation_counts=annotations,
        annotation_count_unit='span-event links; one released edit can overlap several spans',
        pooled_unadjusted_risk_difference=pooled,pooled_arm_counts={k:len(v) for k,v in arms.items()},
        state='below floor, descriptive released-change proxy',physical_word_onset_flow_available=False,
        outcome_scope='Later released overlap inside exact contiguous editor segment; annotations do not define outcome',
        support_gate=False,global_people_count='not inferable from project-scoped authors',
        genre_texture='unavailable: no argumentative/creative source field',
        missing_controls=['physical word-onset/bigram timing','PP1 mechanical correction','whole-manuscript distance','genre'])
    kept=[r for r in rows if r['writer'] in both]
    try: bundle=arrays(kept)
    except ValueError as error:
        summary.update(conditional_estimate=None,reason=str(error));return rows,None,summary
    summary['conditional_estimate']=point(bundle)
    summary['counts']['within_author_spans']=len(kept)
    return kept,bundle,summary


def run(output,inputs,config,verification=False):
    if set(config) != {'card','cell','mode','max_new_draws'} or config['card'] != 'BK-S2.sw' or config['cell'] not in CELLS or config['mode'] not in ('corpus','constructed') or type(config['max_new_draws']) is not int or config['max_new_draws']<1:
        raise ValueError('Frozen S2.sw analysis configuration required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);start=time.process_time()
    records,source_summary,source_hash=source(inputs,config['mode']);cell=config['cell'];draws=2000 if cell=='overlap' else 200
    binding=dict(source_complete_sha256=source_hash,cell=cell,mode=config['mode'])
    if (output/'BINDING.json').exists() and read(output/'BINDING.json') != binding:raise ValueError('Analysis checkpoint changed inputs')
    with threadpool_limits(limits=1):
        rows,bundle,summary=initial(records,cell);bank=[];null=[];new=0
        if bundle is not None and len(bundle['writers'])>=2:
            rng=np.random.default_rng(SEED);sessions=defaultdict(list)
            for i,r in enumerate(rows):sessions[r['session']].append(i)
            for i in range(draws+200):
                if i<draws:
                    ix=rng.integers(len(bundle['writers']),size=len(bundle['writers']));kind='bootstrap'
                else:
                    labels=np.array([r['flow'] for r in rows]);kind='permutation'
                    for indices in sessions.values():labels[indices]=rng.permutation(labels[indices])
                dest=output/'draws'/f'{i:05d}.json'
                if verification or not dest.exists():
                    try:
                        value=numerical.coefficient(bundle,ix) if kind=='bootstrap' else numerical.coefficient(arrays([dict(r,flow=int(v)) for r,v in zip(rows,labels)]))
                        record=dict(kind=kind,value=value,status='identified')
                    except (ValueError,np.linalg.LinAlgError) as error:record=dict(kind=kind,value=None,status='unidentified',reason=str(error))
                    new+=1
                    if verification:
                        if read(dest)!=record:raise ValueError('Fresh full draw differs')
                    else:write(dest,record)
                else:record=read(dest)
                (bank if kind=='bootstrap' else null).append(record)
                if not verification and new==max(1,(draws+200)//20) and not (output/'PILOT.json').exists():
                    write(output/'PILOT.json',dict(new_draws=new,total_draws=draws+200,cpu_seconds=time.process_time()-start,
                        projected_execute_verify_cpu=2*(time.process_time()-start)*(draws+200)/new))
                if (output/'YIELD_REQUEST.json').exists() or (not verification and new>=config['max_new_draws'] and i+1<draws+200):
                    write(output/'BINDING.json',binding)
                    return dict(status='yielded',reason='complete numerical draw boundary; verification restarts all draws',completed_units=i+1,new_draws=new)
            valid=all(r['status']=='identified' for r in bank+null)
            summary['draws']=dict(bootstrap=len(bank),permutation=len(null),unidentified=sum(r['status']!='identified' for r in bank+null))
            if valid:
                values=[r['value'] for r in bank];refs=[r['value'] for r in null]
                summary['interval']=np.quantile(values,[.025,.975]).tolist()
                summary['reference']=dict(mean=float(np.mean(refs)),interval=np.quantile(refs,[.025,.975]).tolist(),scope='within-segment label diagnostic; no exchangeability guarantee')
                summary['uncertainty']='degenerate empirical bootstrap; no population uncertainty claim' if np.ptp(values)<=1e-12 else 'descriptive whole project-author bootstrap; few clusters, cross-project identity unverified'
            else:summary['uncertainty']='unidentified allocation retained; no interval computed from surviving draws'
        else:summary['uncertainty']='fewer than two estimable author clusters; pooled descriptive estimate only'
        summary['constructed']=config['mode']=='constructed';summary['source_census']=source_summary['census']
    for name,value in [('BINDING.json',binding),('SUMMARY.json',summary),('PRIVATE_DRAWS.json.gz',dict(bootstrap=bank,permutation=null))]:
        if verification:
            if read(output/name)!=value:raise ValueError('Complete numerical summary changed')
        else:write(output/name,value)
    return dict(verified=True,all_draws_recomputed=True,new_draws=new) if verification else dict(status='complete',new_draws=new)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
