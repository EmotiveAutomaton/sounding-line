"""Prompt-block person-map profiles; fixed galleries, probe-cluster uncertainty.

DESIGN CHECK: LESSONS 3-5 read October 18. Identical profiles yield exact
fractional chance, unique duplicated fingerprints identify perfectly. A planted
style/lean reversal must reverse the primary. Fake session assignments preserve
session counts and never redraw or silently shrink the common probe/gallery.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import math
import numpy as np
from . import states_v2 as states
from .timing_pmap_source import ACTIONS

CHANNELS = ('lean','style','rhythm','revision','requests','length','content_taste')


def median(values):
    return float(np.median(values)) if len(values) else None


def split_sessions(rows, assignment=None):
    groups = defaultdict(list)
    for r in rows: groups[(assignment or {}).get(r['session'],r['writer'])].append(r)
    halves, excluded = {}, {}
    for writer, sessions in sorted(groups.items()):
        first = {}
        for r in sessions: first[r['prompt']] = min(first.get(r['prompt'],math.inf),r['timestamp'])
        if len(sessions) < 4 or len(first) < 2:
            excluded[writer] = dict(sessions=len(sessions),prompts=len(first)); continue
        order = {p:i%2 for i,p in enumerate(sorted(first,key=lambda p:(first[p],p)))}
        halves[writer] = [[r for r in sorted(sessions,key=lambda r:(r['timestamp'],r['session'])) if order[r['prompt']] == h] for h in (0,1)]
    return halves, excluded


def feature_names(dictionary):
    return dict(lean=list(ACTIONS),style=['word:'+w for w in dictionary['words']]+['punct:'+w for w in dictionary['punctuation']],
        rhythm=['within_word','word_onset']+['bigram:'+b for b in dictionary['character_bigrams']],
        revision=['content_per_100_words','housekeeping_per_100_words','accepted_original_characters_deleted_share'],
        requests=['requests_per_100_words'],length=['final_words_over_prompt_median'],
        content_taste=['MiniLM_'+str(k) for k in range(384)])


def profile(sessions, dictionary, prompt_medians):
    handling, words, punctuation, edits = (Counter() for _ in range(4))
    for r in sessions:
        handling.update(r['handling']); words.update(r['word_counts']); punctuation.update(r['punctuation_counts']); edits.update(r['revision'])
    nh, nw = sum(handling.values()),sum(words.values()); denominator = nw+sum(punctuation.values())
    accepted = sum(r['accepted_characters'] for r in sessions)
    na, nd = sum(r['accepted_options'] for r in sessions),sum(r['declined_options'] for r in sessions)
    a = sum((np.asarray(r['accepted_vector_sum']) for r in sessions),np.zeros(384))
    d = sum((np.asarray(r['declined_vector_sum']) for r in sessions),np.zeros(384))
    timing = [r for r in sessions if r['tc_timing_mode'] != 'invalid']
    return dict(lean=[handling[k]/nh if nh else None for k in ACTIONS],
        style=[words[k]/denominator if denominator else None for k in dictionary['words']]+[punctuation[k]/denominator if denominator else None for k in dictionary['punctuation']],
        rhythm=[median([x for r in timing for x in r['within_intervals']]),median([x for r in timing for x in r['onset_intervals']])]+[median([x for r in timing for x in r['bigram_intervals'].get(k,[])]) for k in dictionary['character_bigrams']],
        revision=[100*edits[k]/nw if nw else None for k in ('content','housekeeping')]+[sum(r['edited_accepted_characters'] for r in sessions)/accepted if accepted else None],
        requests=[100*sum(r['requests'] for r in sessions)/nw if nw else None],
        length=[float(np.mean([r['final_words']/prompt_medians[r['prompt']] for r in sessions if prompt_medians[r['prompt']] > 0])) if any(prompt_medians[r['prompt']] > 0 for r in sessions) else None],
        content_taste=(a/na-d/nd).tolist() if na and nd else [None]*384)


def profiles(rows, dictionary, assignment=None):
    lengths = defaultdict(list)
    for r in rows: lengths[r['prompt']].append(r['final_words'])
    pm = {p:median(v) for p,v in lengths.items()}
    halves, excluded = split_sessions(rows,assignment)
    values = {w:[profile(part,dictionary,pm) for part in parts] for w,parts in halves.items()}
    return values, excluded, {w:[[r['session'] for r in part] for part in parts] for w,parts in halves.items()}


def supported(profile, channel):
    return all(any(v is not None for v in part[channel]) for part in profile)


def identify(a,b):
    """B-only scaling/imputation. Full B gallery remains fixed in bootstrap.

    A wholly absent profile is refused. Partial missing cells receive B's
    observed-feature mean; features absent throughout B are omitted and counted.
    All-constant galleries legitimately tie at chance; no ID tie breaking.
    """
    a,b = np.asarray(a,float),np.asarray(b,float)
    if a.shape != b.shape or a.ndim != 2 or len(a) < 2 or np.any(~np.isfinite(a).any(1)) or np.any(~np.isfinite(b).any(1)):
        raise ValueError('absent channel or invalid paired gallery')
    have = np.isfinite(b).sum(0)
    mean = np.divide(np.nansum(b,axis=0),have,out=np.zeros(b.shape[1]),where=have>0)
    aa,bb = np.where(np.isfinite(a),a,mean),np.where(np.isfinite(b),b,mean)
    scale = bb.std(0); keep = (have>0)&(scale>1e-12)
    aa,bb = (aa[:,keep]-mean[keep])/scale[keep],(bb[:,keep]-mean[keep])/scale[keep]
    dist = np.sum((aa[:,None,:]-bb[None,:,:])**2,axis=2)
    nearest = np.isclose(dist,dist.min(1)[:,None],atol=1e-12,rtol=1e-12)
    scores = nearest.diagonal()/nearest.sum(1)
    return dict(scores=scores.tolist(),accuracy=float(scores.mean()),chance=1/len(a),writers=len(a),
        missing_A=int((~np.isfinite(a)).sum()),missing_B=int((~np.isfinite(b)).sum()),
        features=len(mean),used_features=int(keep.sum()),absent_B_features=int((have==0).sum()),
        constant_features=int(((have>0)&~keep).sum()),tied_probes=int((nearest.sum(1)>1).sum()),
        standardization='B-only observed means; partial missing cells imputed to B mean; B standard deviations; fixed gallery')


def reliability(a,b,names):
    out = []
    a,b = np.asarray(a,float),np.asarray(b,float)
    for j,name in enumerate(names):
        valid = np.isfinite(a[:,j])&np.isfinite(b[:,j]); x,y = a[valid,j],b[valid,j]
        r = float(np.corrcoef(x,y)[0,1]) if len(x)>=3 and np.std(x)>1e-12 and np.std(y)>1e-12 else None
        corrected = 2*r/(1+r) if r is not None and r > -1+1e-12 else None
        out.append(dict(feature=name,paired_writers=int(valid.sum()),missing_A=int((~np.isfinite(a[:,j])).sum()),
            missing_B=int((~np.isfinite(b[:,j])).sum()),pearson=r,spearman_brown=corrected,
            reason=None if corrected is not None else 'insufficient variation/support or r=-1'))
    return out


def channel_result(values, channel, writers, names):
    if len(writers)<3 or any(w not in values or not supported(values[w],channel) for w in writers):
        return dict(state='invalid',reason='fewer than three writers or absent channel on fixed support',writers=writers)
    a = [[np.nan if v is None else v for v in values[w][0][channel]] for w in writers]
    b = [[np.nan if v is None else v for v in values[w][1][channel]] for w in writers]
    return dict(state='descriptive',identification=identify(a,b),reliability=reliability(a,b,names),writers=writers)


def interval(scores,draws=2000,seed=20261018):
    x=np.asarray(scores,float)
    if len(x)<3 or not np.isfinite(x).all():return dict(state='invalid',reason='insufficient paired probes')
    rng=np.random.default_rng(seed); b=x[rng.integers(len(x),size=(draws,len(x)))].mean(1)
    effect=float(x.mean()); low,high=map(float,np.quantile(b,[.025,.975])); se=0. if np.ptp(b)==0 else float(b.std(ddof=1))
    return dict(effect=effect,ci_low=low,ci_high=high,bootstrap_se=se,z=effect/se if se else None,
        approximate_two_sided_wald_p=math.erfc(abs(effect/se)/math.sqrt(2)) if se else None,
        state=states.contrast_state(effect,low,high),writers=len(x),bootstrap_draws=draws,
        uncertainty='real probe-writer bootstrap; complete B gallery fixed; paired arms')


def distribution(values,observed=None):
    a=np.asarray(values,float)
    if not len(a):return dict(valid_draws=0)
    mean,sd=float(a.mean()),float(a.std(ddof=1)) if len(a)>1 else 0.
    low,high=map(float,np.quantile(a,[.025,.975]))
    return dict(valid_draws=len(a),mean=mean,sd=sd,q025=low,q975=high,
        one_sided_p=(1+int((a>=observed).sum()))/(len(a)+1) if observed is not None else None,
        bias_flag=bool(abs(mean)>.25*sd) if sd else bool(mean != 0))


def prepare(rows,dictionary):
    values,excluded,halves=profiles(rows,dictionary); names=feature_names(dictionary)
    common=sorted(w for w,v in values.items() if supported(v,'lean') and supported(v,'style'))
    rosters={c:common if c in ('lean','style') else sorted(w for w,v in values.items() if supported(v,c)) for c in CHANNELS}
    real={c:channel_result(values,c,rosters[c],names[c]) for c in CHANNELS}
    primary=interval(np.asarray(real['style']['identification']['scores'])-real['lean']['identification']['scores']) if all('identification' in real[c] for c in ('lean','style')) else dict(state='invalid',reason='primary common gallery unsupported')
    return dict(profiles=values,halves=halves,excluded=excluded,rosters=rosters,names=names,channels=real,
        primary=primary,extension_eligible=primary['state'] in ('positive','marginal'),
        channel_exclusions={c:sorted(set(values)-set(rosters[c])) for c in CHANNELS})


def fake_one(rows,dictionary,prepared,assignment):
    values,excluded,halves=profiles(rows,dictionary,assignment)
    channels={c:channel_result(values,c,prepared['rosters'][c],prepared['names'][c]) for c in CHANNELS}
    contrast=float(np.mean(np.asarray(channels['style']['identification']['scores'])-channels['lean']['identification']['scores'])) if all('identification' in channels[c] for c in ('lean','style')) else None
    return dict(channels=channels,primary=contrast,split_excluded=excluded,
        assignment=assignment,halves=halves)


def summarize(prepared,fakes):
    result={k:v for k,v in prepared.items() if k not in ('profiles','names')}
    result['permutations']=len(fakes); result['seed']=20261018
    result['primary_session_permutation_null']=distribution([f['primary'] for f in fakes if f['primary'] is not None],prepared['primary'].get('effect'))
    result['primary_session_permutation_null']['invalid_draws']=sum(f['primary'] is None for f in fakes)
    if result['primary_session_permutation_null']['invalid_draws']:
        result['primary_session_permutation_null']['one_sided_p']=None
        result['primary_session_permutation_null']['state']='invalid'
        result['primary_session_permutation_null']['reason']='fixed-support permutations incomplete; valid-draw distribution descriptive only; no successful-only p'
    else:result['primary_session_permutation_null']['state']='descriptive'
    result['fake_channels']={}
    for c in CHANNELS:
        real=prepared['channels'][c]; valid=[f['channels'][c] for f in fakes if 'identification' in f['channels'][c]]
        item=dict(attempted=len(fakes),invalid=len(fakes)-len(valid),accuracy=distribution([r['identification']['accuracy'] for r in valid]),
            reliability=[dict(feature=name,distribution=distribution([r['reliability'][j]['spearman_brown'] for r in valid if r['reliability'][j]['spearman_brown'] is not None])) for j,name in enumerate(prepared['names'][c])])
        if len(valid)==len(fakes) and valid and 'identification' in real:
            fake_scores=np.mean([r['identification']['scores'] for r in valid],axis=0)
            item['own_minus_fake']=interval(np.asarray(real['identification']['scores'])-fake_scores)
            item['fake_mean_probe_scores']=fake_scores.tolist()
        else:item['own_minus_fake']=dict(state='invalid',reason='fixed-gallery coverage missing; no redraw or successful-only inference')
        # Accuracy is not expected zero: report chance-centered fake bias separately.
        if valid:item['chance_centered']=distribution([r['identification']['accuracy']-r['identification']['chance'] for r in valid])
        result['fake_channels'][c]=item
    result['method']=dict(primary='style minus lean rank-one identification',extension='rhythm minus lean; separately gated',
        tie_policy='fractional 1/k among exactly tied nearest neighbors',split='whole prompts ordered by first start; alternate A/B',
        missing='wholly absent channels excluded before real fixed rosters; partial cells imputed to B feature mean with counts',
        fake='200 whole-session label permutations preserving counts; fixed real channel rosters; no redraw after coverage failure',
        reliability='Pearson half correlation, Spearman-Brown 2r/(1+r); no correlation for constants',
        revision_share='original canonical accepted codepoints deleted by user; internal additions separately counted',
        declined='canonical dismissed-menu mean vector; each dismissed menu equal weight; ignores and unselected options in accepted menus excluded; individual examination unknown',
        dictionary='full typed corpus transductive feature roster; no identity/outcome optimization')
    return result
