"""FIC1 sufficient-measure context construction; no identification scores.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 reread 2026-10-27.
NULL: identical prompt measures reconstruct identical pooled profiles. A
recipient's feature values cannot affect independent context. ALTERNATIVE:
person variation stays in observed profiles and cannot enter disjoint donor
pools. Missing fixed support remains unsupported, never dropped or redrawn.
Every rotation/control refits B-only nuisance coefficients. These construction
checks are not full scientific calibration; the handler is constructed-only.
"""
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
import math

import numpy as np
from threadpoolctl import threadpool_limits

from runners.stage14.common import read, filehash, freeze
from . import week3_fic1_reassignment as reconstruction
from . import week3_fic1_galleries as gallery
from .week3_identification_crossfit import writer_folds

CONFIG = dict(card='FIC1-context-native', schema=1, mode='constructed',
              writers=6, sessions=48, word_limits=[2,4,8], seed=20261026)


def weighted_median(values):
    mass=defaultdict(float)
    for value, weight in values:
        if not math.isfinite(value) or not math.isfinite(weight) or weight<=0:
            raise ValueError('invalid empirical timing mass')
        mass[float(value)]+=weight
    if not mass: return None
    seq=sorted(mass.items()); half=math.fsum(w for _,w in seq)/2
    total=0.
    for i,(value,weight) in enumerate(seq):
        total+=weight
        if math.isclose(total,half,rel_tol=1e-12,abs_tol=1e-15):
            return (value+seq[i+1][0])/2 if i+1<len(seq) else value
        if total>half: return value
    raise ValueError('timing mass accumulation failed')


def mean_measure(units, rows, final=False, quota=None):
    """Equal donor-session average of sufficient measures per word."""
    if not units: return None
    wc=defaultdict(float); pc=defaultdict(float); timing=defaultdict(list)
    for u in sorted(units,key=lambda x:x['session']):
        r=rows[u['session']]
        if quota is not None and (final or type(quota) is not int or quota<=0):
            raise ValueError('invalid donor prefix quota')
        if quota is not None and u['typed_words']<quota: return None
        n=r['final_words'] if final else (u['typed_words'] if quota is None else quota)
        if type(n) is not int or n<=0: return None
        factor=1/(len(units)*n)
        source=r['final_counts'] if final else (u['whole'] if quota is None else reconstruction.prefix.take(u,quota))
        if sum(source['word_counts'].values())!=n: raise ValueError('donor word denominator differs')
        for dest,key in ((wc,'word_counts'),(pc,'punctuation_counts')):
            for token,count in sorted(source[key].items()):
                if type(count) is not int or count<0: raise ValueError('invalid donor count')
                dest[token]+=count*factor
        if not final and source['tc_timing_mode']!='invalid':
            sequences={'within':source['within_intervals'],'onset':source['onset_intervals']}
            sequences.update({'bigram:'+k:v for k,v in source['bigram_intervals'].items()})
            for key,values in sorted(sequences.items()):
                for value in values:
                    if not math.isfinite(value) or value<0: raise ValueError('invalid donor timing')
                    timing[key].append((float(value),factor))
    return dict(words=dict(wc),punctuation=dict(pc),timing=dict(timing),donor_sessions=len(units))


def pool(measures, dictionary):
    """Pool expected sufficient mass before rates and timing medians."""
    if not measures or any(m is None for m,_ in measures): return None
    wc=defaultdict(float); pc=defaultdict(float); timing=defaultdict(list)
    for measure,n in measures:
        if type(n) is not int or n<=0: raise ValueError('invalid recipient quota')
        for dest,key in ((wc,'words'),(pc,'punctuation')):
            for token,value in sorted(measure[key].items()): dest[token]+=value*n
        for key,values in sorted(measure['timing'].items()):
            timing[key].extend((value,weight*n) for value,weight in values)
    keys=['within','onset']+['bigram:'+k for k in dictionary['character_bigrams']]
    return dict(style=gallery.features.style(wc,pc,dictionary),
                rhythm=[weighted_median(timing[k]) for k in keys])


def context_profiles(data, rebuilt, donors=None):
    """None selects literal leave-writer-out; a set selects independent donors."""
    units={u['session']:u for u in data['units']}; rows={r['session']:r for r in data['rows']}
    labels=rebuilt['labels']; dictionary=data['dictionary']; cache={}; out=[]
    if donors is not None and not set(donors)<=set(labels.values()): raise ValueError('unknown donor writer')
    for profile in rebuilt['profiles']:
        if donors is not None and profile['writer'] in donors: continue
        p=deepcopy(profile)
        if p['state']!='prepared': out.append(p); continue
        allowed=set(labels.values())-{p['writer']} if donors is None else set(donors)
        def measure(sid,final=False,quota=None):
            target=units[sid]; key=(target['genre'],target['prompt'],tuple(sorted(allowed)),final,quota)
            if key not in cache:
                uu=[u for u in units.values() if (u['genre'],u['prompt'])==key[:2] and labels[u['session']] in allowed]
                cache[key]=mean_measure(uu,rows,final,quota)
            return cache[key]
        for name,level in p['levels'].items():
            if level['state']!='prepared': continue
            value=pool([(measure(m['session'],quota=None if m['whole_session'] else m['typed_words']),m['typed_words']) for m in level['members']],dictionary)
            level['features']=value
            if value is None:
                level.update(state='unsupported',reason='missing complete context donor prompt')
        final_parts=[(measure(s,True),rows[s]['final_words']) for s in p['sessions']]
        final=pool(final_parts,dictionary) if all(n>0 for _,n in final_parts) else None
        p['final']['features']=final['style'] if final else [None]*(len(dictionary['words'])+len(dictionary['punctuation']))
        p['context_rule']='equal-session sufficient measure per word; pooled before rates and medians'
        out.append(p)
    return out


def vector(p,channel,level):
    if p is None or p['state']!='prepared': return None
    if channel=='final_style': return p['final']['features']
    z=p['levels'][level]
    return z['features'][channel] if z['state']=='prepared' else None


def support(profiles,levels):
    ix={(p['writer'],p['genre'],p.get('half')):p for p in profiles}
    if len(ix)!=len(profiles): raise ValueError('duplicate profile')
    writers=sorted({p['writer'] for p in profiles}); result={}
    for channel,level in [(c,l) for c in ('style','rhythm') for l in levels]+[('final_style','full')]:
        roster=[]
        for w in writers:
            values=[vector(ix.get((w,g,h)),channel,level) for g in gallery.GENRES for h in (0,1)]
            if all(v is not None and any(x is not None for x in v) for v in values): roster.append(w)
        result[channel+'.'+level]=roster
    return result


def matrices(profiles,rosters):
    ix={(p['writer'],p['genre'],p.get('half')):p for p in profiles}; result={}
    if len(ix)!=len(profiles): raise ValueError('duplicate profile')
    for name,roster in rosters.items():
        if roster!=sorted(set(roster)): raise ValueError('fixed canonical roster required')
        channel,level=name.split('.'); genres={}
        for genre in gallery.GENRES:
            aa=[[vector(ix.get((w,genre,h)),channel,level) for w in roster] for h in (0,1)]
            if len(roster)<3 or any(v is None or not any(x is not None for x in v) for a in aa for v in a):
                genres[genre]=dict(state='unsupported',writers=roster,reason='fixed gallery support absent');continue
            q=[[[ix[w,genre,h]['final']['log_words'] if channel=='final_style' else
                 gallery.log_words(ix[w,genre,h]['levels'][level]['selected_words'])] for w in roster] for h in (0,1)]
            g=dict(state='prepared',writers=roster,raw=dict(A=aa[0],B=aa[1]),covariates=dict(A=q[0],B=q[1]))
            if level=='full': g['length_adjusted']=gallery.adjust(*aa,*q)
            if channel=='final_style':
                aq=[[[v[0],ix[w,genre,h]['final']['accepted_share']] for w,v in zip(roster,q[h])] for h in (0,1)]
                g['length_and_ai_adjusted']=gallery.adjust(*aa,*aq)
            genres[genre]=g
        result[name]=genres
    return result


def role_assignment(units,folds,index,seed):
    if set(folds)!={u['writer'] for u in units}: raise ValueError('role population differs')
    rng=np.random.default_rng(np.random.SeedSequence([seed,index])); groups=defaultdict(list); labels={}
    for u in units: groups[u['genre'],u['prompt'],folds[u['writer']]].append(u)
    for _,part in sorted(groups.items()):
        part=sorted(part,key=lambda u:u['session'])
        labels.update((u['session'],str(w)) for u,w in zip(part,rng.permutation([u['writer'] for u in part])))
    return labels


def prepare(data,config,labels=None):
    units=data['units']; folds=writer_folds(units,config['seed'])
    labels=labels or {u['session']:u['writer'] for u in units}
    if set(labels)!={u['session'] for u in units}: raise ValueError('assignment population differs')
    if any(labels[u['session']] not in folds or folds[labels[u['session']]]!=folds[u['writer']] for u in units):
        raise ValueError('assignment crosses frozen writer roles')
    rebuilt=reconstruction.rebuild(units,data['rows'],data['dictionary'],config['word_limits'],labels)
    levels=[str(n) for n in config['word_limits']]+['full']
    # The roster is fixed from original support, never from a passing control draw.
    observed=reconstruction.rebuild(units,data['rows'],data['dictionary'],config['word_limits'])
    rosters=support(observed['profiles'],levels)
    literal=context_profiles(data,rebuilt); rotations=[]
    for f in range(3):
        donors=sorted(w for w in folds if folds[w]==f)
        rr={name:[w for w in roster if folds[w]!=f] for name,roster in rosters.items()}
        probes={name:[w for w in roster if folds[w]==(f+1)%3] for name,roster in rosters.items()}
        actual=[p for p in rebuilt['profiles'] if p['writer'] not in donors]
        context=context_profiles(data,rebuilt,set(donors))
        rotations.append(dict(donor_fold=f,donors=donors,probes=probes,galleries=rr,
            observed=matrices(actual,rr),context=matrices(context,rr),context_profiles=context))
    for name,roster in rosters.items():
        if Counter(w for r in rotations for w in r['probes'][name])!=Counter(roster): raise ValueError('probe coverage differs')
    return dict(rosters=rosters,writer_folds=folds,rotations=rotations,
        literal_leave_writer_out=matrices(literal,rosters),literal_licenses_claim=False,
        identification_computed=False,full_calibration_complete=False,scientific_admission=False)


def run(output,inputs,config,verification=False):
    if config!=CONFIG or set(inputs)!={'fixture'}: raise ValueError('constructed context fixture only')
    fp=Path(inputs['fixture']); data=read(fp)
    if len(data['units'])!=config['sessions'] or len({u['writer'] for u in data['units']})!=config['writers']:
        raise ValueError('constructed population differs')
    with threadpool_limits(limits=1): result=prepare(data,config)
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    summary=dict(card=config['card'],constructed=True,context_construction_replayed=True,
        rotations=3,identification_computed=False,full_calibration_complete=False,scientific_admission=False)
    for name,value in [('CONTEXT.json',result),('SUMMARY.json',summary),('BINDING.json',dict(config=config,fixture_sha256=filehash(fp)))]:
        path=output/name
        if verification:
            if read(path)!=value: raise ValueError('context replay differs: '+name)
        else: freeze(path,value)
    if verification: return dict(verified=True,all_context_reconstructed=True,constructed=True)
    return dict(status='complete',scientific_admission=False)


def execute(output,inputs,config): return run(output,inputs,config)
def verify(output,inputs,config): return run(output,inputs,config,True)
