"""Predeclared Stage 12 diagnostics, recomputed without new model requests.

DESIGN CHECK: LESSONS 3-5. NULL: missing histories block paired contrasts and
unchanged/irrelevant movement subtracts generic revision drift. ALTERNATIVE:
request/edit and realization contrasts survive their source-specific rivals.
These are new descriptive analyses of exposed records, not new replications.
"""
from __future__ import annotations
from collections import defaultdict
from difflib import SequenceMatcher
import re
import numpy as np
from .common import REPO,read,filehash,freeze,digest
from .scoring import probabilities,proper_loss,interval

OLD=REPO/'results/phase_2_4_stage_12/raw/local-program-20260923-v2'


def retained(family,expected):
    records=[];pins={}
    for job in sorted((OLD/'jobs').glob(family+'-[0-9][0-9][0-9]-a2')):
        terminal=read(job/'COMPLETE.json')
        for name,h in terminal['output_files'].items():
            if filehash(job/name)!=h:raise ValueError('retained source changed')
        records.extend(read(job/'ROWS.json'));pins[str((job/'ROWS.json').relative_to(REPO))]=filehash(job/'ROWS.json')
    if len(records)!=expected or len({r['id'] for r in records})!=expected:raise ValueError('retained whole family incomplete')
    for r in records:
        if r['probabilities'] is not None and probabilities(r['probabilities'],r['n']) is None:raise ValueError('old probability schema cannot be silently repaired')
    return records,pins


def cosine(a,b):
    from collections import Counter
    a=Counter(re.findall(r'\w+',a.lower()));b=Counter(re.findall(r'\w+',b.lower()))
    denom=np.sqrt(sum(v*v for v in a.values())*sum(v*v for v in b.values()))
    return sum(v*b[k] for k,v in a.items())/denom if denom else 0.


def diff_features(c):
    before=c['before'];after=c['after'];request=c['review_request'];added=[];removed=[]
    for tag,i,j,k,l in SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
        if tag!='equal':added.append(after[k:l]);removed.append(before[i:j])
    return [cosine(request,' '.join(added)),cosine(request,' '.join(removed)),cosine(request,after),cosine(request,before),
        sum(map(len,added))/max(1,len(after)),sum(map(len,removed))/max(1,len(before))]


def aries(out):
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    rows,pins=retained('LP15',384);p=OLD/'inputs/ARIES-compile/SOURCE_ROWS.json';source={r['id']:r for r in read(p)};pins[str(p.relative_to(REPO))]=filehash(p)
    targets={r['unit']:r for r in rows};training=[r for r in targets.values() if not r['reserved']];testing=[r for r in targets.values() if r['reserved']]
    features={k:diff_features(r['public']) for k,r in source.items()}
    model=LogisticRegression(C=1,max_iter=1000,random_state=130927).fit([features[r['unit']] for r in training],[r['annotation'] for r in training])
    pmodel={r['unit']:float(model.predict_proba([features[r['unit']]])[0,1]) for r in testing}
    aggregates={}
    for direction in ('request','edit'):
        for view in ('pair','context','change'):
            for method in ('direct','account'):
                rs=[r for r in rows if r['reserved'] and r['direction']==direction and r['view']==view and r['method']==method]
                values=[proper_loss(r['probabilities'],r['annotation'],2)['brier'] for r in rs]
                rival=[proper_loss([1-pmodel[r['unit']],pmodel[r['unit']]],r['annotation'],2)['brier'] for r in rs]
                aggregates[direction+'/'+view+'/'+method]=dict(reader_loss=interval(values,[r['cluster'] for r in rs]),reader_minus_diff_rival=interval([a-b for a,b in zip(values,rival)],[r['cluster'] for r in rs]),
                    invalid=sum(r['probabilities'] is None for r in rs))
    result=dict(status='complete',comparisons=aggregates,source_pins=pins,training_papers=len({r['cluster'] for r in training}),reserved_papers=len({r['cluster'] for r in testing}),
        diff_rival=dict(features=['request-added cosine','request-removed cosine','request-after cosine','request-before cosine','added fraction','removed fraction'],coef=model.coef_[0].tolist(),intercept=model.intercept_.tolist(),auc=float(roc_auc_score([r['annotation'] for r in testing],[pmodel[r['unit']] for r in testing]))),
        scope='historically exposed ARIES pairs; former reserved-paper tag is an analysis stratum, not fresh confirmation; direction wording shares paired evidence')
    freeze(out/'ANALYSIS.json',result);return result


def revision(out):
    rows,pins=retained('LP21-revision',2688)
    # Retain the exact expected census; no silent complete-history selection.
    by={(r['unit'],r['method'],r['frame'],r['update'],r['mode']):r for r in rows};contrasts={}
    def penalty(unit,method,frame,update):
        a=by[unit,method,frame,update,'saved'];b=by[unit,method,frame,update,'fresh']
        return a['score']['half_brier']-b['score']['half_brier'],a['cluster']
    for control in ('unchanged','irrelevant'):
        values=[];units=[]
        for unit,method in sorted({(r['unit'],r['method']) for r in rows}):
            vals={}
            for frame in ('false','true'):
                d,cluster=penalty(unit,method,frame,'diagnostic');c,_=penalty(unit,method,frame,control);vals[frame]=d-c
            values.append(vals['false']-vals['true']);units.append(cluster)
        contrasts['diagnostic-minus-'+control]=interval(values,units)
    result=dict(status='complete',contrasts=contrasts,source_pins=pins,definition='false-minus-true saved-versus-fresh loss interaction, after subtracting matched unchanged/irrelevant interaction',scope='exposed retained histories, new descriptive difference-in-differences; old interaction retained')
    freeze(out/'ANALYSIS.json',result);return result


def realization(out):
    rows,pins=retained('LP18',384);results={}
    for sign in ('plus','minus'):
        for fulfilled in (False,True):
            rs=[r for r in rows if r['instruction_sign']==sign and r['fulfilled']==fulfilled]
            for view in ('artifact','instruction','trace'):
                for method in ('direct','account'):
                    selected=[r for r in rs if r['view']==view and r['method']==method]
                    if not selected:continue
                    for r in selected:
                        if r['target']!=[float(not r['fulfilled']),float(r['fulfilled'])] or r['exact_check']!=['exact',r['fulfilled']]:raise ValueError('realization source/checker disagree')
                    results[f'{sign}/{fulfilled}/{view}/{method}']=dict(loss=interval([proper_loss(r['probabilities'],int(fulfilled),2)['brier'] for r in selected],[r['cluster'] for r in selected]),
                        invalid=sum(r['probabilities'] is None for r in selected),attempts=len(selected))
    result=dict(status='complete',comparisons=results,source_pins=pins,scope='requested versus counterfactual feature, conditioned on actual exact realization; trace view supplies the checker answer; no claim of semantic goal realization')
    freeze(out/'ANALYSIS.json',result);return result
