"""FIC1 gallery preparation and gallery-only nuisance projection; no human score.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 reread 2026-10-27.
Under NULL, an exactly linear length-only feature projects to zero; under an
ALTERNATIVE orthogonal to length, its residual remains. Probe values never fit
coefficients. Missing observations remain missing, a rank-exhausted fit remains
unsupported, and ties are not broken by identity. Every original writer stays
in the support census. No identification controls or scientific admission are
claimed by this component; permutations and independent donor folds must refit.
"""
from collections import Counter
from pathlib import Path
import math

import numpy as np
from threadpoolctl import threadpool_limits

from runners.stage14.common import read, filehash, freeze, atomic
from . import week3_fic1_features as features
from . import week3_fic1_prefixes as prefixes_source
from .timing_p6 import gzread, gzip_equal
from .timing_pmap_source import completed

CONFIG = dict(card='FIC1-galleries', schema=1, mode='full', sessions=990,
              writers=24, profiles=96, levels=['500','1000','2000','full'])
CONSTRUCTED = dict(CONFIG, mode='constructed', sessions=48, writers=6, profiles=24,
                   levels=['2','4','8','full'])
GENRES = ('creative','argumentative')


def json_array(x):
    x=np.asarray(x,float)
    if np.isinf(x).any(): raise ValueError('infinite feature or covariate')
    return [[float(v) if np.isfinite(v) else None for v in row] for row in x]


def adjust(a,b,qa,qb):
    """Fit each feature on gallery B only, apply to A and B without imputation."""
    a,b,qa,qb=(np.asarray(z,float) for z in (a,b,qa,qb))
    if a.ndim!=2 or a.shape!=b.shape or qa.ndim!=2 or qa.shape!=qb.shape or len(a)!=len(qa):
        raise ValueError('paired gallery/covariate dimensions differ')
    if any(np.isinf(z).any() for z in (a,b,qa,qb)): raise ValueError('infinite gallery value')
    da=np.column_stack([np.ones(len(a)),qa]);db=np.column_stack([np.ones(len(b)),qb])
    va=np.isfinite(da).all(1);vb=np.isfinite(db).all(1)
    aa=np.full_like(a,np.nan);bb=np.full_like(b,np.nan);fits=[]
    for j in range(a.shape[1]):
        use=vb & np.isfinite(b[:,j]);design=db[use];y=b[use,j]
        if not len(y):
            fits.append(dict(state='unsupported',reason='no finite gallery fit rows',n=0));continue
        coef,_,rank,_=np.linalg.lstsq(design,y,rcond=None)
        if len(y)<=rank:
            fits.append(dict(state='unsupported',reason='no residual degrees of freedom',n=len(y),rank=int(rank)));continue
        for raw,d,valid,out in ((a,da,va,aa),(b,db,vb,bb)):
            good=valid & np.isfinite(raw[:,j])
            out[good,j]=raw[good,j]-d[good]@coef
            out[np.isfinite(out[:,j]) & (np.abs(out[:,j])<1e-12),j]=0.
        fits.append(dict(state='fitted',coefficients=coef.tolist(),n=len(y),rank=int(rank),
                         residual_df=int(len(y)-rank),fit_half='gallery-B'))
    return dict(A=json_array(aa),B=json_array(bb),fits=fits)


def log_words(n):
    if type(n) is not int or n<0: raise ValueError('invalid word count')
    return math.log2(n) if n else None


def pooled_final(rows,dictionary):
    wc,pc=Counter(),Counter()
    for r in rows:
        wc.update(r['final_counts']['word_counts']);pc.update(r['final_counts']['punctuation_counts'])
    chars=sum(r['final_characters'] for r in rows)
    accepted=sum(r['final_accepted_characters'] for r in rows)
    if chars<0 or accepted<0 or accepted>chars: raise ValueError('invalid final provenance totals')
    words=sum(wc.values())
    if words!=sum(r['final_words'] for r in rows): raise ValueError('final word count differs')
    return dict(features=features.style(wc,pc,dictionary),words=words,
                log_words=log_words(words),accepted_share=accepted/chars if chars else None,
                characters=chars,accepted_characters=accepted)


def prepare(data,config):
    rows=data['rows'];groups=data['profiles'];pp=data['prefixes'];dictionary=data['dictionary']
    bysid={r['session']:r for r in rows}
    key=lambda p:(p['writer'],p['genre'],p['half'])
    pg={key(p):p for p in groups};pr={key(p):p for p in pp}
    writers=sorted({r['writer'] for r in rows})
    expected={(w,g,h) for w in writers for g in GENRES for h in (0,1)}
    if (len(bysid)!=len(rows) or len(rows)!=config['sessions'] or len(writers)!=config['writers']
        or len(groups)!=len(pg) or len(pp)!=len(pr) or len(pg)!=config['profiles']
        or set(pg)!=expected or set(pr)!=expected): raise ValueError('fixed complete population differs')
    seen=[];records={}
    for k in sorted(pg):
        group=pg[k];members=group['sessions']
        if not members or any(s not in bysid for s in members): raise ValueError('missing profile members')
        rr=[bysid[s] for s in members]
        if any(key(r)!=k for r in rr): raise ValueError('profile identity differs')
        if members!=[r['session'] for r in sorted(rr,key=lambda r:(r['timestamp'],r['session']))]: raise ValueError('profile chronology differs')
        if sum(r['typed_words'] for r in rr)!=group['full_typed_words']: raise ValueError('profile word count differs')
        level=pr[k]['levels']
        if set(level)!=set(config['levels']): raise ValueError('fixed word levels differ')
        for name,z in level.items():
            if z['state'] not in ('prepared','unsupported'): raise ValueError('unknown prefix support')
            if z['available_words']!=group['full_typed_words']: raise ValueError('prefix available words differ')
            if z['state']=='unsupported':
                if name=='full' or z['available_words']>=int(name) or z['features'] is not None: raise ValueError('invalid unsupported prefix')
            else:
                target=z['available_words'] if name=='full' else int(name)
                if z['selected_words']!=target or sum(m['typed_words'] for m in z['members'])!=target: raise ValueError('prefix quota differs')
                if any(m['session'] not in members for m in z['members']): raise ValueError('crossed prefix membership')
        seen.extend(members)
        records[k]=dict(levels=level,final=pooled_final(rr,dictionary),sessions=members)
    if Counter(seen)!=Counter(bysid.keys()): raise ValueError('profile session partition differs')
    for w in writers:
        for g in GENRES:
            a,b=(pg[w,g,h]['sessions'] for h in (0,1))
            if {bysid[s]['prompt'] for s in a}&{bysid[s]['prompt'] for s in b}: raise ValueError('prompt leakage')
    variants={};support={}
    names=[(c,l) for c in ('style','rhythm') for l in config['levels']]+[('final_style','full')]
    for channel,level in names:
        name=channel+'.'+level
        def vector(w,g,h):
            r=records[w,g,h]
            return r['final']['features'] if channel=='final_style' else r['levels'][level]['features'][channel] if r['levels'][level]['state']=='prepared' else None
        missing={w:[dict(genre=g,half=h) for g in GENRES for h in (0,1)
                    if vector(w,g,h) is None or not any(x is not None for x in vector(w,g,h))] for w in writers}
        roster=[w for w in writers if not missing[w]]
        support[name]=dict(original_writers=len(writers),supported_writers=len(roster),writers=roster,
                           unsupported=[dict(writer=w,missing=missing[w]) for w in writers if missing[w]])
        genres={}
        for genre in GENRES:
            arrays={h:[vector(w,genre,h) for w in roster] for h in (0,1)}
            if len(roster)<3:
                genres[genre]=dict(state='unsupported',reason='fewer than three paired writers');continue
            cov=[]
            for h in (0,1):
                cov.append([[records[w,genre,h]['final']['log_words']] if channel=='final_style' else
                            [log_words(records[w,genre,h]['levels'][level]['selected_words'])] for w in roster])
            result=dict(state='prepared',writers=roster,raw=dict(A=arrays[0],B=arrays[1]),
                        covariates=dict(names=['log2_words'],A=cov[0],B=cov[1]))
            # The full-word variant requests length adjustment. Equal-length arms
            # remain raw, so this preparation does not change their estimand.
            if level=='full': result['length_adjusted']=adjust(arrays[0],arrays[1],cov[0],cov[1])
            if channel=='final_style':
                ac=[[z[0],records[w,genre,0]['final']['accepted_share']] for w,z in zip(roster,cov[0])]
                bc=[[z[0],records[w,genre,1]['final']['accepted_share']] for w,z in zip(roster,cov[1])]
                result['length_and_ai_adjusted']=adjust(arrays[0],arrays[1],ac,bc)
                result['ai_covariates']=dict(names=['log2_words','accepted_character_share'],A=ac,B=bc)
            genres[genre]=result
        variants[name]=genres
    curve={c:sorted(set.intersection(*(set(support[c+'.'+l]['writers']) for l in config['levels']))) for c in ('style','rhythm')}
    return dict(variants=variants,support=support,length_curve_common_writers=curve,
                length_curve_population_rule='Scores uncomputed; all-length common support retained beside per-level support',
                fit_scope='Observed pooled B galleries only; every control and independent-donor rotation must refit on its own B',
                identification_computed=False,scientific_admission=False)


def load(inputs,config):
    if config==CONSTRUCTED:
        if set(inputs)!={'fixture'}: raise ValueError('explicit constructed fixture required')
        return read(inputs['fixture']),{str(Path(inputs['fixture']).resolve()):filehash(inputs['fixture'])}
    if config!=CONFIG or set(inputs)!={'prefix_completion','feature_completion'}: raise ValueError('fixed completed predecessors required')
    bindings={}
    def artifact(which,rel):
        terminal=Path(inputs[which]).resolve();path=terminal.parent/rel
        completed(terminal,path);bindings[str(terminal)]=filehash(terminal);bindings[str(path)]=filehash(path)
        return gzread(path) if path.suffix=='.gz' else read(path)
    pp=artifact('prefix_completion','PLAN.json');fp=artifact('feature_completion','PLAN.json')
    if pp['module']!='runners.drive.cards.week3_fic1_prefixes' or pp['config']!=prefixes_source.CONFIG or fp['module']!='runners.drive.cards.week3_fic1_features' or fp['config']!=features.CONFIG:
        raise ValueError('unexpected gallery predecessor')
    if Path(pp['inputs']['feature_completion']).resolve()!=Path(inputs['feature_completion']).resolve(): raise ValueError('prefix/feature lineage differs')
    psummary=artifact('prefix_completion','output/SUMMARY.json')
    if not psummary['exact_occurrence_replay'] or psummary['identification_computed']: raise ValueError('unexpected prefix scope')
    index=artifact('feature_completion','output/SESSION_INDEX.json');rows=[]
    for item in index:
        r=artifact('feature_completion','output/'+item['file'])
        if r['session']!=item['session'] or filehash(Path(inputs['feature_completion']).parent/'output'/item['file'])!=item['sha256']: raise ValueError('feature session binding differs')
        rows.append(r)
    groups=artifact('prefix_completion','output/PROFILES.json')
    if groups!=artifact('feature_completion','output/PROFILES.json'): raise ValueError('predecessor memberships differ')
    dictionary=artifact('prefix_completion','output/DICTIONARY.json')
    if dictionary!=artifact('feature_completion','output/DICTIONARY.json'): raise ValueError('predecessor dictionaries differ')
    return dict(rows=rows,profiles=groups,prefixes=artifact('prefix_completion','output/PREFIX_FEATURES.json'),dictionary=dictionary),bindings


def run(output,inputs,config,verification=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    with threadpool_limits(limits=1):
        data,bindings=load(inputs,config);result=prepare(data,config)
    summary=dict(card=CONFIG['card'],constructed=config['mode']=='constructed',sessions=len(data['rows']),
                 profiles=len(data['profiles']),writers=config['writers'],all_profiles_retained=True,
                 support={k:dict(supported_writers=v['supported_writers'],unsupported_writers=len(v['unsupported'])) for k,v in result['support'].items()},
                 length_curve_common_writers={k:len(v) for k,v in result['length_curve_common_writers'].items()},
                 length_covariate_fitted=True,identification_computed=False,controls_computed=False,
                 full_calibration_complete=False,scientific_admission=False,auth_requests_prepared=False)
    for name,value in [('GALLERIES.json',result),('SUMMARY.json',summary),('BINDING.json',dict(config=config,inputs=bindings))]:
        path=output/name
        if verification:
            if read(path)!=value: raise ValueError('full gallery replay differs: '+name)
        else: freeze(path,value)
    if verification: return dict(verified=True,complete_input_replay=True,all_galleries_recomputed=True)
    return dict(status='complete',scientific_admission=False)


def execute(output,inputs,config): return run(output,inputs,config)
def verify(output,inputs,config): return run(output,inputs,config,True)
