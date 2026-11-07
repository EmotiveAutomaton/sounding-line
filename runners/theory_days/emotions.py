"""TD4-TD6 exact-program consumers; committed designs precede real outcomes.

DESIGN CHECK: LESSONS 2-5, CONTROLS 6-7. Constructed order, disagreement and
language examples have exact answers; nulls must not become positive through
missing coverage or denominators. Scientific outcomes require full replay.
"""
from pathlib import Path
import io
import re
import zipfile
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from runners.stage14.common import freeze,read,filehash
from .intake import LABELS,read_goemotions

SCALES={
 'FEAR':('fear','uneasy worried anxious scared terrified'),
 'RAGE':('anger','annoyed frustrated mad angry furious rage'),
 'SEEKING':('anticipation','interested curious eager enthusiastic excited'),
 'PANIC/GRIEF':('sadness','sad lonely grief anguish heartbroken'),
 'CARE':('trust','tender fond protective devoted love'),
 'PLAY':('joy','amused silly giddy playful hilarious hysterical'),
 'LUST':(None,'desire passionate lust aroused'),
 'DISGUST':('disgust','dislike yucky disgusted gross loathe')}
CHANNELS=[['anger','annoyance'],['fear','nervousness'],['grief','sadness'],
 ['amusement','joy'],['curiosity','excitement'],['caring','love'],['desire'],['disgust']]
SUBJECTS={'he','she','they','people','someone','everyone','[name]'}
VERBS=set(('think thinks thought thinking believe believes believed believing want wants wanted wanting '
 'mean means meant intend intends intended intending know knows knew known knowing feel feels felt feeling '
 'care cares cared caring try tries tried trying wish wishes wished wishing expect expects expected expecting').split())


def scale_stats(intensities, arousal, dominance):
    values=np.asarray(intensities,dtype=float)
    result=dict(covered=len(values),inversions=None,spearman=None,off_line_ratio=None)
    if len(values)>=4 and np.ptp(values)>0:
        result.update(inversions=int((np.diff(values)<0).sum()),
                      spearman=float(spearmanr(np.arange(len(values)),values).statistic))
    x,a,d=map(lambda v:np.asarray(v,dtype=float),(intensities,arousal,dominance))
    mask=np.isfinite(x)&np.isfinite(a)&np.isfinite(d)
    result['joint_covered']=int(mask.sum())
    if mask.sum()>=4 and np.ptp(x[mask])>0 and np.std(a[mask])>0:
        design=np.column_stack([np.ones(mask.sum()),x[mask]])
        residual=d[mask]-design@np.linalg.lstsq(design,d[mask],rcond=None)[0]
        result['off_line_ratio']=float(np.std(residual)/np.std(a[mask]))
    inv,ratio=result['inversions'],result['off_line_ratio']
    if inv is None or ratio is None: verdict='design cannot test'
    elif inv>1 or ratio>1:verdict='against'
    elif inv==0 and ratio<.5:verdict='supports'
    else:verdict='inconclusive'
    result['verdict']=verdict
    return result


def td4(eil_path,vad_path):
    with zipfile.ZipFile(eil_path) as z:
        eil=pd.read_csv(io.BytesIO(z.read('NRC-Emotion-Intensity-Lexicon/NRC-Emotion-Intensity-Lexicon-v1.txt')),sep='\t')
    with zipfile.ZipFile(vad_path) as z:
        vad=pd.read_csv(io.BytesIO(z.read('NRC-VAD-Lexicon-v2.1/NRC-VAD-Lexicon-v2.1.txt')),sep='\t')
    if len(eil.columns)!=3 or len(vad.columns)!=4:raise ValueError('Lexicon schema')
    eil.columns=['word','emotion','intensity'];vad.columns=['word','valence','arousal','dominance']
    if eil.duplicated(['word','emotion']).any() or vad.word.duplicated().any():raise ValueError('Duplicate norm')
    e={(r.word,r.emotion):float(r.intensity) for r in eil.itertuples()}
    v={r.word:(float(r.arousal),float(r.dominance)) for r in vad.itertuples()}
    if not all(0<=x<=1 for x in e.values()) or not all(np.isfinite(x).all() for x in v.values()):raise ValueError('Invalid norm')
    result={}
    for name,(emotion,words) in SCALES.items():
        wordlist=words.split();covered=[w for w in wordlist if (w in v if emotion is None else (w,emotion) in e)]
        intensity=[v[w][0] if emotion is None else e[w,emotion] for w in covered]
        a=[v.get(w,(np.nan,np.nan))[0] for w in covered]
        d=[v.get(w,(np.nan,np.nan))[1] for w in covered]
        row=scale_stats(intensity,a,d)
        # Position masks correspond only to the curator's already-public word
        # lists; raw norm entries and wordwise scores are never emitted.
        row['intensity_coverage_mask']=[(w,emotion) in e if emotion else None for w in wordlist]
        row['vad_coverage_mask']=[w in v for w in wordlist]
        if name in ('SEEKING','CARE'):
            c=[w for w in wordlist if (w,'joy') in e]
            row['joy_companion']=scale_stats([e[w,'joy'] for w in c],
                [v.get(w,(np.nan,np.nan))[0] for w in c],[v.get(w,(np.nan,np.nan))[1] for w in c])
        result[name]=row
    return dict(scales=result,substrate='word norms',lexicon_entries_published=False)


def pair_sufficient(frame):
    """Exact cross-rater counts, with exclusivity eliminating self-pairs."""
    frame=frame.sort_values(['id','rater_id'])
    labels=frame[LABELS].to_numpy(dtype=np.int64)
    _,start,n=np.unique(frame.id.to_numpy(),return_index=True,return_counts=True)
    pairs=np.array([(i,j) for i in range(len(LABELS)) for j in range(i+1,len(LABELS))])
    count=np.add.reduceat(labels,start,axis=0)
    both=np.add.reduceat(labels[:,pairs[:,0]]*labels[:,pairs[:,1]],start,axis=0)
    a=count[:,pairs[:,0]]-both;b=count[:,pairs[:,1]]-both
    matrix=np.column_stack([a*b,a,b,n,n*(n-1)]).astype(float)
    return matrix,pairs,n


def lifts(sums,p):
    observed=sums[..., :p];a=sums[..., p:2*p];b=sums[..., 2*p:3*p]
    ratings=sums[..., -2,None];ordered=sums[..., -1,None]
    expected=ordered*a*b/(ratings*ratings)
    return np.divide(observed,expected,out=np.full_like(observed,np.nan),where=expected>0),expected


def interval(values):
    values=np.asarray(values)
    return [float(x) for x in np.quantile(values,[.025,.975])] if np.isfinite(values).all() else None


def pair_decision(estimate,ci):
    if ci is None:return 'invalid uncertainty'
    if ci[0]>0 and estimate>=.1:return 'win'
    if ci[1]<0 and estimate<=-.1:return 'loss'
    return 'inconclusive'


def disagreement(frame,draws=2000,seed=20261106):
    counts=frame.groupby('id').size(); frame=frame[frame.id.isin(counts[counts>=3].index)]
    matrix,pairs,n=pair_sufficient(frame);p=len(pairs)
    point,expected=lifts(matrix.sum(axis=0),p)
    rng=np.random.default_rng(seed); boot=np.empty((draws,p))
    # Batched exact multinomial comment resampling, single-thread BLAS.
    for begin in range(0,draws,16):
        size=min(16,draws-begin)
        w=rng.multinomial(len(n),np.full(len(n),1/len(n)),size=size).astype(float)
        boot[begin:begin+size]=lifts(w@matrix,p)[0]
    lookup={tuple(pair):k for k,pair in enumerate(pairs)}
    assignment={label:k for k,c in enumerate(CHANNELS) for label in c}
    results=[]
    for channel in CHANNELS[:6]:
        members=[LABELS.index(x) for x in channel];own=lookup[tuple(sorted(members))]
        row=dict(channel=channel,within_lift=float(point[own]),within_expected=float(expected[own]))
        for role in ('cross_channel','unassigned'):
            candidates=[]
            for k,(i,j) in enumerate(pairs):
                if not (i in members or j in members):continue
                other=j if i in members else i
                name=LABELS[other]
                eligible=(name in assignment and assignment[name]!=assignment[channel[0]]) if role=='cross_channel' else name not in assignment
                if eligible and expected[k]>=50 and np.isfinite(point[k]):candidates.append(k)
            if not candidates:
                row[role]=dict(status='unsupported competitor');continue
            best=max(candidates,key=lambda k:(point[k],-k))
            delta=float(point[own]-point[best]);fixed=interval(boot[:,own]-boot[:,best])
            reselection=interval(boot[:,own]-np.max(boot[:,candidates],axis=1))
            row[role]=dict(competitor=[LABELS[x] for x in pairs[best]],difference=delta,
                fixed_competitor_interval=fixed,reselected_interval=reselection,
                conditional_decision=pair_decision(delta,fixed),selection_aware_decision=pair_decision(delta,reselection))
        results.append(row)
    decision=[r['cross_channel'].get('conditional_decision') for r in results]
    verdict='against' if decision.count('loss')>=3 else 'supports' if decision.count('win')==6 else 'inconclusive'
    return dict(comments=len(n),ratings=len(frame),ordered_pairs=int((n*(n-1)).sum()),
                bootstrap_draws=draws,pairs=results,packet_verdict=verdict)


def mind_counts(text):
    tokens=re.findall(r'\[name\]|[a-z]+',text.lower())
    hits=sum(t in SUBJECTS and any(v in VERBS for v in tokens[k+1:k+4]) for k,t in enumerate(tokens))
    return hits,len(tokens),bool(set(tokens)&{'he','she','they'})


def matched_pairs(frame,threshold,seed=20261106):
    aggregate=frame.groupby('id',sort=True).agg(text=('text','first'),subreddit=('subreddit','first'),
                                              disgust=('disgust','sum'),anger=('anger','sum'))
    aggregate['arm']=np.where((aggregate.disgust>=threshold)&(aggregate.anger==0),1,
                            np.where((aggregate.anger>=threshold)&(aggregate.disgust==0),0,-1))
    candidates=aggregate[aggregate.arm>=0].copy()
    candidates['length']=candidates.text.str.split().str.len()
    candidates['decile']=pd.qcut(candidates.length,10,labels=False,duplicates='drop').fillna(0).astype(int)
    rng=np.random.default_rng(seed);matched=[]
    for (subreddit,decile),part in candidates.groupby(['subreddit','decile'],sort=True):
        a=part.index[part.arm==1].to_numpy();b=part.index[part.arm==0].to_numpy()
        rng.shuffle(a);rng.shuffle(b)
        for ia,ib in zip(a,b):
            ah,an,ap=mind_counts(part.loc[ia,'text']);bh,bn,bp=mind_counts(part.loc[ib,'text'])
            matched.append((subreddit,ah,an,bh,bn,ap,bp))
    return matched,dict(disgust_candidates=int((candidates.arm==1).sum()),
                       anger_candidates=int((candidates.arm==0).sum()),matched_pairs=len(matched),threshold=threshold)


def mind_contrast(pairs,draws=2000,seed=20261106):
    if not pairs:return dict(status='unsupported',pairs=0)
    strata={}
    for row in pairs:strata.setdefault(row[0],[]).append(row[1:5])
    arrays=[np.asarray(v,dtype=float) for v in strata.values()]
    total=sum((a.sum(axis=0) for a in arrays),np.zeros(4))
    def contrast(v):
        a,n,b,m=v
        return (a/n-b/m)/(b/m) if n>0 and m>0 and b>0 else np.nan
    rng=np.random.default_rng(seed);boot=np.empty(draws)
    for i in range(draws):
        values=sum((a[rng.integers(len(a),size=len(a))].sum(axis=0) for a in arrays),np.zeros(4))
        boot[i]=contrast(values)
    ci=interval(boot);point=contrast(total)
    verdict='inconclusive' if ci is None else 'supports' if ci[1]<-.1 else 'against' if ci[0]>-.1 else 'inconclusive'
    return dict(pairs=len(pairs),disgust_hits=int(total[0]),disgust_tokens=int(total[1]),
                anger_hits=int(total[2]),anger_tokens=int(total[3]),
                relative_difference=float(point) if np.isfinite(point) else None,interval=ci,
                undefined_draws=int((~np.isfinite(boot)).sum()),verdict=verdict)


def td6(frame,draws=2000):
    pairs,strict=matched_pairs(frame,2)
    if len(pairs)<300:pairs,support=matched_pairs(frame,1)
    else:support=strict
    if len(pairs)<300:return dict(status='design cannot test',strict=strict,used=support)
    primary=mind_contrast(pairs,draws)
    # Preserve original matching in the person-targeted sensitivity.
    person=[r for r in pairs if r[5] and r[6]]
    return dict(strict=strict,used=support,primary=primary,person_targeted=mind_contrast(person,draws))


def calculate(inputs,config):
    for value in inputs.values():
        if filehash(Path(value['path']))!=value['sha256']:raise ValueError('Scientific input mutation')
    card=config['card']
    if card=='TD4':return td4(inputs['eil']['path'],inputs['vad']['path'])
    frame=read_goemotions(inputs['go_emotions']['path'])
    frame=frame.loc[~frame.example_very_unclear]
    if card=='TD5':
        counts=frame.groupby('id').size();subset=frame[frame.id.isin(counts[counts==3].index)]
        return dict(primary=disagreement(frame,config['draws']),exactly_three=disagreement(subset,config['draws']))
    if card=='TD6':return td6(frame,config['draws'])
    raise ValueError('Unregistered consumer')


def execute(output,inputs,config):
    result=calculate(inputs,config);freeze(Path(output)/'SCIENCE.json',result);return result


def verify(output,inputs,config):
    result=calculate(inputs,config)
    if read(Path(output)/'SCIENCE.json')!=result:raise ValueError('Complete independent replay differs')
    return dict(verified=True,complete_recalculation=True)
