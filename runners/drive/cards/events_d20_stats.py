"""Exact D20 donor expectation, cached overlap kernels, and paired controls.

DESIGN CHECK (LESSONS3-5, October18): the original equal-menu/session/writer
estimand and alternating-session Pearson reliability are unchanged. Null,
positive and reverse fixtures compare the fast reduction to the frozen code.
Within-writer outcome permutations preserve prompt/progress and every target;
singleton groups stay fixed. Identity controls permute complete even halves on
the fixed supported writer graph. Real writer nodes weight BOTH arms, including
their donor roles. Undefined draws are retained, never redrawn or set to zero.
"""
from collections import Counter, defaultdict
import hashlib
import json
import numpy as np
from . import menus_d12 as intervals

CHANNELS = ('lexical', 'embedding')


def kernel(rows, writers, channel):
    """One prompt/progress stratum; all dismissed windows are permutation units."""
    rows = sorted(rows, key=lambda r:r['key'])
    targets = [r for r in rows if r['handling']=='dismiss' and r['window'] is not None]
    wi = {w:i for i,w in enumerate(writers)}
    valid = [r for r in rows if any(r['options'])] if channel=='lexical' else [r for r in rows if r['vector'] is not None]
    sessions = sorted({r['session'] for r in valid}); si = {s:i for i,s in enumerate(sessions)}
    owners = {r['session']:wi[r['writer']] for r in valid}
    overlap = np.empty((len(targets), len(valid)))
    for i, target in enumerate(targets):
        if channel=='embedding':
            for j, donor in enumerate(valid):
                overlap[i,j] = float(np.dot(donor['vector'], target['window_vector']))
        else:
            window = set(target['window'])
            for j, donor in enumerate(valid):
                overlap[i,j] = float(np.mean([len(set(v)&window)/len(v) for v in donor['options'] if v]))
    by_session = np.zeros((len(targets),len(sessions)))
    for sid in sessions:
        by_session[:,si[sid]] = overlap[:,[j for j,r in enumerate(valid) if r['session']==sid]].mean(axis=1)
    sums = np.zeros((len(targets),len(writers))); counts = np.zeros(len(writers))
    for sid in sessions:
        sums[:,owners[sid]] += by_session[:,si[sid]]; counts[owners[sid]] += 1
    lookup = {r['key']:j for j,r in enumerate(valid)}
    own = np.zeros((len(targets),len(targets))); eligible=[]; excluded=Counter()
    for i,row in enumerate(targets):
        if row['key'] not in lookup:
            excluded['no supported offered option'] += 1
        elif len(sessions)<=1:
            excluded['no other-session donor in prompt/progress stratum'] += 1
        else:
            own[:,i] = overlap[:,lookup[row['key']]]; eligible.append(i)
    target_meta=[]
    for r in targets:
        signature=hashlib.sha256(json.dumps([r['window'],r['window_vector']],sort_keys=True).encode()).hexdigest()
        target_meta.append({k:r[k] for k in ('key','writer','session','half','prompt','progress_decile')}|dict(outcome_signature=signature))
    meta = dict(targets=target_meta,
                sessions=sessions, eligible=eligible, exclusions=dict(excluded), channel=channel, writers=writers)
    return meta, dict(own=own, sums=sums, counts=counts, session_overlap=by_session)


def comparisons(kernels, writers, mapping=None):
    wi = {w:i for i,w in enumerate(writers)}; result=[]; excluded=Counter()
    for meta, arrays in kernels:
        excluded.update(meta['exclusions']); targets=meta['targets']
        ti={r['key']:i for i,r in enumerate(targets)}; si={s:i for i,s in enumerate(meta['sessions'])}
        for i in meta['eligible']:
            r=targets[i]; j=i if mapping is None else ti[mapping[r['key']]]
            sums=arrays['sums'][j].copy(); counts=arrays['counts'].copy(); w=wi[r['writer']]
            sums[w]-=arrays['session_overlap'][j,si[r['session']]]; counts[w]-=1
            result.append({k:r[k] for k in ('key','writer','session','half')} | dict(
                observed=float(arrays['own'][j,i]),donor_sum=sums.tolist(),donor_sessions=counts.tolist()))
    return sorted(result,key=lambda r:r['key']),dict(excluded)


def outcome_groups(kernels):
    groups=defaultdict(list)
    for meta,_ in kernels:
        for r in meta['targets']:groups[(r['writer'],r['prompt'],r['progress_decile'])].append(r['key'])
    return [sorted(v) for _,v in sorted(groups.items())]


def permutation(groups, seed, draw):
    rng=np.random.default_rng(np.random.SeedSequence([seed,0,draw]))
    return {k:group[int(j)] for group in groups for k,j in zip(group,rng.permutation(len(group)))}


class Design:
    """Vectorized version of frozen estimates, retaining the session hierarchy."""
    def __init__(self,rows,writers):
        self.rows=rows; self.writers=writers; self.n=len(writers); wi={w:i for i,w in enumerate(writers)}
        self.owners=np.array([wi[r['writer']] for r in rows],int)
        self.sums=np.asarray([r['donor_sum'] for r in rows],float).reshape(len(rows),self.n)
        self.counts=np.asarray([r['donor_sessions'] for r in rows],float).reshape(len(rows),self.n)
        self.observed=np.array([r['observed'] for r in rows],float)
        sessions=sorted({(r['writer'],r['half'],r['session']) for r in rows}); lookup={s:i for i,s in enumerate(sessions)}
        self.row_session=np.array([lookup[(r['writer'],r['half'],r['session'])] for r in rows],int)
        self.session_sizes=np.bincount(self.row_session,minlength=len(sessions))
        self.session_owner=np.array([wi[w] for w,h,s in sessions],int)
        self.session_half=np.array([2*wi[w]+h for w,h,s in sessions],int)
        self.writer_sessions=np.bincount(self.session_owner,minlength=self.n)
        self.half_sessions=np.bincount(self.session_half,minlength=2*self.n)
        self.eligible=np.flatnonzero((self.half_sessions.reshape(self.n,2)>0).all(axis=1))

    def values(self,weights):
        denominator=self.counts@weights; bad=denominator<=0
        effects=np.zeros(len(self.rows)); good=~bad
        effects[good]=self.observed[good]-(self.sums[good]@weights)/denominator[good]
        session_means=np.bincount(self.row_session,weights=effects,minlength=len(self.session_sizes))/self.session_sizes
        invalid_session=np.bincount(self.row_session,weights=bad.astype(int),minlength=len(self.session_sizes))>0
        invalid_writer=np.bincount(self.session_owner,weights=invalid_session.astype(int),minlength=self.n)>0
        means=np.divide(np.bincount(self.session_owner,weights=session_means,minlength=self.n),self.writer_sessions,
                        out=np.full(self.n,np.nan),where=self.writer_sessions>0)
        halves=np.divide(np.bincount(self.session_half,weights=session_means,minlength=2*self.n),self.half_sessions,
                         out=np.full(2*self.n,np.nan),where=self.half_sessions>0).reshape(self.n,2)
        means[invalid_writer]=np.nan; halves[invalid_writer]=np.nan
        selected=(weights>0)&(self.writer_sessions>0)
        point=None if not selected.any() or np.any(invalid_writer&selected) else float(np.average(means[selected],weights=weights[selected]))
        # Frozen estimates aborts the entire draw if any sampled target lacks
        # donor support, including a writer absent from the two-half subset.
        if np.any(invalid_writer&selected):halves[:]=np.nan
        return point,means,halves

    def correlation(self,halves,weights,minimum=3):
        chosen=self.eligible[weights[self.eligible]>0]
        if len(chosen)<minimum:return None
        return weighted_correlations(halves[chosen,0],halves[chosen,1][None,:],weights[chosen])[0]


def weighted_correlations(x,ys,weights):
    """Each row of ys is one paired arm; weights are real writer multiplicity."""
    weights=np.asarray(weights,float); x=np.asarray(x,float);ys=np.asarray(ys,float)
    if weights.sum()<=0:return [None]*len(ys)
    x=x-np.average(x,weights=weights);y=ys-np.average(ys,axis=1,weights=weights)[:,None]
    den=np.sqrt(np.sum(weights*x*x)*np.sum(weights*y*y,axis=1))
    numer=np.sum(weights*x*y,axis=1)
    return [float(np.clip(a/b,-1,1)) if np.isfinite(b) and b>1e-14 else None for a,b in zip(numer,den)]


def identity_maps(n,seed,count):
    rng=np.random.default_rng(np.random.SeedSequence([seed,1]))
    return np.asarray([rng.permutation(n) for _ in range(count)],int).reshape(count,n)


def identity_values(design,halves,weights,maps,minimum=3):
    e=design.eligible; chosen=np.flatnonzero(weights[e]>0)
    if len(chosen)<minimum:return dict(own=None,fake_mean=None,difference=None,undefined=len(maps))
    # All even-half rows are kept intact. Their donor baseline is rebuilt with
    # the SAME real writer weights even if that even-half owner was not sampled.
    x=halves[e[chosen],0]; ys=halves[e[maps[:,chosen]],1]
    own=weighted_correlations(x,halves[e[chosen],1][None,:],weights[e[chosen]])[0]
    fake=weighted_correlations(x,ys,weights[e[chosen]])
    invalid=sum(v is None for v in fake)
    mean=float(np.mean(fake)) if not invalid else None
    return dict(own=own,fake_mean=mean,difference=None if own is None or mean is None else own-mean,
                undefined=invalid)


def null_report(point,draws):
    valid=[v for v in draws if v is not None]; bad=len(draws)-len(valid)
    # No conditional p-value obtained by dropping unsupported permutations.
    mean=float(np.mean(valid)) if valid else None
    sd=float(np.std(valid,ddof=1)) if len(valid)>1 else None
    return dict(draws=len(draws),undefined_draws=bad,valid=bad==0 and point is not None,
                p_one_sided=(1+sum(v>=point for v in valid))/(1+len(draws)) if bad==0 and point is not None else None,
                mean=mean,sd=sd,quantiles95=np.quantile(valid,[.025,.975]).tolist() if valid else [None,None],
                bias_flag=None if mean is None or sd is None else abs(mean)>.25*sd,
                moments_scope='all draws' if bad==0 else 'finite draws only; p invalid, no redraw')
