"""WC2 fixed failed-means contrast, rival wording route and sensitivity checks.

DESIGN CHECK: LESSONS 3-5, CONTROLS 1-7 reread 2026-10-25. Equal own/context
vectors yield zero; topic-only signal cancels; independent directional signal
is positive and reversed signal negative. Phrase-route bands are exhaustive.
The band is fixed using only external context and support, before own outcomes.
Missing support is unsupported. A weak kept denominator never licenses a ratio.
Whole prompt halves and within-prompt label shuffles govern reliability only.
No choice of an embedding, window or band is made from its scientific score.
"""
from collections import defaultdict
import math
from pathlib import Path

import numpy as np

from .timing_census import read, filehash
from .timing_p6 import gzread, gzip_equal, write_equal
from .timing_pmap_source import completed
from .timing_text import tokens, WORD

CONFIG=dict(card='WC2',schema=1,mode='full',bootstrap_draws=2000,permutations=200,
            reliability_permutations=1000,seed=20261026,minimum_events=150,minimum_writers=25)
CONSTRUCTED=dict(CONFIG,mode='constructed',bootstrap_draws=200,permutations=32,
                 reliability_permutations=32,minimum_events=8,minimum_writers=4)
FUNCTION_WORDS=frozenset('a an the and or but if then because while as of to in on at by for from with without into through is are was were be been being have has had do does did not no this that these those it its i me my we us our you your he him his she her they them their who whom which what where when how why can could may might must shall should will would so than too very also only some any all each every both either neither such'.split())


def words(text):return [t for t in tokens(text) if WORD.fullmatch(t)]


def overlap(window,span,function=False):
    w,s=words(window),words(span)
    if function:w,s=[x for x in w if x in FUNCTION_WORDS],[x for x in s if x in FUNCTION_WORDS]
    found=total=0
    for size in (2,3):
        pool={tuple(s[i:i+size]) for i in range(len(s)-size+1)}
        values=[tuple(w[i:i+size]) for i in range(len(w)-size+1)]
        found+=sum(v in pool for v in values);total+=len(values)
    return found/total if total else None


def content_overlap(window,span):
    w=[x for x in words(window) if x not in FUNCTION_WORDS];s=set(words(span))-FUNCTION_WORDS
    return sum(x in s for x in w)/len(w) if w else None


def required(events):
    deleted=[e for e in events if e['kind']=='deleted' and e['window'] and e['context']]
    ids={e['id'] for e in deleted}|{e['kept_reference']['id'] for e in deleted if e['kept_reference']}
    selected=[e for e in events if e['id'] in ids]
    if len({e['id'] for e in events})!=len(events):raise ValueError('duplicate event identity')
    texts={t for e in selected for t in [e['span']['text'],*e['span']['unchosen'],e['window']['text'],
        *[w['text'] for w in e['context']],*([e['sensitivity']['text']] if e['sensitivity'] else []),
        *[w['text'] for w in e['sensitivity_context']]]}
    return selected,sorted(texts)


def score(window,span,other,vectors):
    if not other:raise ValueError('unchosen comparator absent')
    own=np.asarray(vectors[window],float);chosen=np.asarray(vectors[span],float)
    alternatives=np.asarray([vectors[t] for t in other],float)
    all_vectors=np.vstack([own,chosen,alternatives])
    if not np.isfinite(all_vectors).all() or not np.allclose(np.linalg.norm(all_vectors,axis=1),1,atol=1e-5):
        raise ValueError('nonfinite/nonunit embedding')
    return dict(embedding=float(own@chosen-np.mean(alternatives@own)),phrase=overlap(window,span),
        function_phrase=overlap(window,span,True),content=content_overlap(window,span))


def contrast(event,vectors,sensitivity=False):
    own=event['sensitivity'] if sensitivity else event['window']
    contexts=event['sensitivity_context'] if sensitivity else event['context']
    if own is None or not contexts:return None
    if any(w['writer']==event['writer'] or w['prompt']!=event['prompt'] for w in contexts):
        raise ValueError('own-writer or wrong-prompt context contamination')
    if len({w['writer'] for w in contexts})!=len(contexts):raise ValueError('repeated donor writer')
    a=score(own['text'],event['span']['text'],event['span']['unchosen'],vectors)
    bb=[score(w['text'],event['span']['text'],event['span']['unchosen'],vectors) for w in contexts]
    b={k:float(np.mean([x[k] for x in bb])) if all(x[k] is not None for x in bb) else None for k in a}
    d={k:a[k]-b[k] if a[k] is not None and b[k] is not None else None for k in a}
    return dict(own=a,context=b,difference=d,context_writers=len(contexts))


def writer_means(rows,key):
    grouped=defaultdict(list)
    for r in rows:
        v=r[key]
        if v is not None and math.isfinite(v):grouped[r['writer']].append(v)
    return {w:float(np.mean(x)) for w,x in sorted(grouped.items())}


def interval(values,draws,seed,coverage=.95):
    x=np.asarray(values,float)
    if len(x)<2 or not np.isfinite(x).all():return dict(effect=None,interval=None,writers=len(x),state='unsupported')
    rng=np.random.default_rng(seed);means=x[rng.integers(len(x),size=(draws,len(x)))].mean(axis=1)
    low,high=np.quantile(means,[(1-coverage)/2,1-(1-coverage)/2]).tolist()
    return dict(effect=float(x.mean()),interval=[low,high],coverage=coverage,writers=len(x),
                state='positive' if low>0 else 'negative' if high<0 else 'not_detected')


def frozen_band(rows):
    context=writer_means(rows,'context_phrase');x=np.asarray(list(context.values()),float)
    if len(x)<2:return dict(band=None,reason='fewer than two context writers')
    sd=float(np.std(x,ddof=1));original=.25*sd;halfwidth=1.6448536269514722*sd/math.sqrt(len(x))
    return dict(band=max(original,halfwidth),original_band=original,context_writer_sd=sd,
        projected_halfwidth90=halfwidth,widened=halfwidth>original,writers=len(x),
        reason='context-only normal-reference halfwidth at fixed writer support; no own-window outcome used',
        timing='computed from context phrases before own embedding/phrase contrasts')


def route(embedding,phrase,band):
    if embedding['interval'] is None or phrase['interval'] is None or band is None:return 'unsupported'
    low,high=embedding['interval'];p,q=phrase['interval']
    if high<0:return 'moves away'
    if low<=0<=high:return 'no direction'
    if low<=0:raise ValueError('nonexhaustive embedding interval')
    if p>=-band and q<=band:return 'same end, new means'
    if p>band:return 'lingering taste'
    return 'unresolved'


def reliability(rows,config):
    writers=sorted({r['writer'] for r in rows});roster=[];halves={}
    for writer in writers:
        own=[r for r in rows if r['writer']==writer]
        prompts=sorted({r['prompt'] for r in own},key=lambda p:(min(r['timestamp'] for r in own if r['prompt']==p),p))
        if len({r['session'] for r in own})<4 or len(prompts)<2:continue
        roster.append(writer);halves[writer]={p:i%2 for i,p in enumerate(prompts)}
    def pair(labels):
        values=[]
        for w in roster:
            a=[[r['persist'] for r,label in zip(rows,labels) if label==w and halves[w].get(r['prompt'])==h] for h in (0,1)]
            if not all(a):return None
            values.append([float(np.mean(v)) for v in a])
        if len(values)<3:return None
        x=np.asarray(values)
        if np.std(x[:,0])==0 or np.std(x[:,1])==0:return None
        return float(np.corrcoef(x.T)[0,1])
    labels=[r['writer'] for r in rows];observed=pair(labels)
    if observed is None:return dict(state='unsupported',writers=len(roster),reason='insufficient fixed whole-prompt halves or zero between-writer variance')
    groups=defaultdict(list)
    for i,r in enumerate(rows):groups[r['prompt']].append(i)
    rng=np.random.default_rng(config['seed']);null=[]
    for _ in range(config['reliability_permutations']):
        perm=list(labels)
        for indices in groups.values():
            for i,label in zip(indices,rng.permutation([labels[j] for j in indices])):perm[i]=str(label)
        null.append(pair(perm))
    invalid=sum(x is None for x in null)
    return dict(state='invalid' if invalid else 'complete',writers=len(roster),correlation=observed,null=null,
        invalid_draws=invalid,p=(1+sum(x>=observed for x in null))/(1+len(null)) if not invalid else None,
        scope='persistence-rate whole-prompt split; fixed supported roster; no successful-only reference')


def analyze(data,vectors,config):
    if config not in (CONFIG,CONSTRUCTED):raise ValueError('fixed WC2 analysis design required')
    selected,_=required(data['events']);targets=[e for e in selected if e['kind']=='deleted']
    count=len(targets);writers=len({e['writer'] for e in targets})
    if count<config['minimum_events'] or writers<config['minimum_writers']:
        return dict(card='WC2',state='unsupported',events=count,writers=writers,scientific_admission=False),dict(rows=[])
    # Freeze context-only phrase dispersion before evaluating any own outcome.
    bandrows=[dict(writer=e['writer'],context_phrase=float(np.mean([overlap(w['text'],e['span']['text']) for w in e['context']]))) for e in targets]
    band=frozen_band(bandrows)
    scored={e['id']:contrast(e,vectors) for e in selected};rows=[]
    for e in targets:
        d=scored[e['id']];kept=scored[e['kept_reference']['id']] if e['kept_reference'] else None
        sensitivity=contrast(e,vectors,True)
        rows.append(dict(id=e['id'],writer=e['writer'],session=e['session'],prompt=e['prompt'],timestamp=e['timestamp'],
            **d['difference'],context_phrase=d['context']['phrase'],own=d['own'],context=d['context'],
            persist=int(d['difference']['embedding']>0),kept=kept['difference']['embedding'] if kept else None,
            paired_numerator=d['difference']['embedding'] if kept else None,
            sensitivity=sensitivity['difference']['embedding'] if sensitivity else None))
    means={k:writer_means(rows,k) for k in ('embedding','phrase','function_phrase','content','kept','paired_numerator','sensitivity')}
    summary={k:interval(list(v.values()),config['bootstrap_draws'],config['seed'],.90 if k=='phrase' else .95) for k,v in means.items()}
    # The paired kept denominator is assessed on exactly the numerator's writers.
    if set(means['kept'])!=set(means['paired_numerator']):raise ValueError('ratio paired writer population differs')
    ratio=dict(state='unresolved',reason='kept-reference denominator lower bound is below0.01 or unsupported')
    if summary['kept']['interval'] is not None and summary['kept']['interval'][0]>=.01:
        order=sorted(means['kept']);a=np.array([means['paired_numerator'][w] for w in order]);b=np.array([means['kept'][w] for w in order])
        ix=np.random.default_rng(config['seed']).integers(len(order),size=(config['bootstrap_draws'],len(order)))
        denominators=b[ix].mean(axis=1)
        if np.any(denominators<=0):ratio=dict(state='unresolved',reason='nonpositive denominator in paired ratio bootstrap')
        else:ratio=dict(state='complete',estimate=float(a.mean()/b.mean()),ci95=np.quantile(a[ix].mean(axis=1)/denominators,[.025,.975]).tolist(),writers=len(order))
    # Repeated within-writer own/context swaps are a diagnostic exchangeability reference.
    rng=np.random.default_rng(config['seed']);null=[]
    for _ in range(config['permutations']):
        swapped=[dict(writer=r['writer'],x=r['embedding']*int(rng.choice([-1,1]))) for r in rows]
        null.append(float(np.mean(list(writer_means(swapped,'x').values()))))
    result=dict(card='WC2',state='complete',events=count,writers=writers,contrasts=summary,phrase_band=band,
        route=route(summary['embedding'],summary['phrase'],band['band']),persistence_ratio=ratio,
        null_reference=dict(draws=len(null),values=null,one_sided_p=(1+sum(v>=summary['embedding']['effect'] for v in null))/(len(null)+1),
                            scope='diagnostic eventwise own/context swaps within writer; observational exchangeability is not guaranteed'),
        reliability=reliability(rows,config),writer_profiles={w:dict(events=len([r for r in rows if r['writer']==w]),
            persist_share=float(np.mean([r['persist'] for r in rows if r['writer']==w])),
            drop_share=float(np.mean([1-r['persist'] for r in rows if r['writer']==w]))) for w in sorted({r['writer'] for r in rows})},
        estimand='equal-writer mean of equal-event own-minus-equal-donor-writer context advantages',
        scope='observational CoAuthor outcome blocks; no causal hidden-goal inference',scientific_admission=True)
    return result,dict(rows=rows,writer_means=means)


def load(inputs,config):
    if config==CONSTRUCTED:
        if set(inputs)!={'fixture'}:raise ValueError('constructed payload required')
        f=read(inputs['fixture']);return f['data'],f['vectors']
    if config!=CONFIG or set(inputs)!={'feature_completion'}:raise ValueError('verified feature completion required')
    parent=Path(inputs['feature_completion']).parent
    for name in ('EVENTS.json.gz','VECTORS.json.gz','SUMMARY.json'):
        completed(inputs['feature_completion'],parent/'output'/name)
    if read(parent/'output/SUMMARY.json').get('analysis_ready') is not True:raise ValueError('partial/constructed feature pass cannot feed corpus analysis')
    return gzread(parent/'output/EVENTS.json.gz'),gzread(parent/'output/VECTORS.json.gz')


def run(output,inputs,config,verification=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    data,vectors=load(inputs,config);summary,details=analyze(data,vectors,config)
    binding=dict(config=config,inputs={k:filehash(v) for k,v in sorted(inputs.items())})
    if verification:
        if read(output/'BINDING.json')!=binding or read(output/'SUMMARY.json')!=summary or gzread(output/'DETAILS.json.gz')!=details:
            raise ValueError('fresh WC2 replay differs')
        return dict(verified=True,full_statistic_replay=True)
    write_equal(output/'BINDING.json',binding);write_equal(output/'SUMMARY.json',summary);gzip_equal(output/'DETAILS.json.gz',details)
    return dict(status='complete',state=summary['state'])


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
