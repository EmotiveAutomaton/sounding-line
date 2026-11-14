"""CH12 split-history indices and TR1 split-half reliability formula.

DESIGN CHECK: unreliable gain is not evidence of an unstable trait. Both half
variances must clear zero before interpreting stability. Ratios are unclipped;
undefined bootstrap draws are kept. Whole people, not games, are resampled.
"""
from datetime import datetime,timezone
import math
import numpy as np
from . import week5_tr1_math as tr1

SPLIT = datetime(2017,5,16,tzinfo=timezone.utc).timestamp()
INDEX_NAMES=('LEVEL','GAIN','FORECAST_GAIN')


def indices(rows,reference=False):
    wins=[r for r in rows if r['score']==1]
    losses=[r for r in rows if r['score']==0]
    favourite=[r for r in wins if r['E']>=.65]
    level=None if not favourite else sum(bool(r['stop']) for r in favourite)/len(favourite)
    gain=None if not wins or not losses else (sum(bool(r['stop']) for r in losses)/len(losses)-
                                              sum(bool(r['stop']) for r in wins)/len(wins))
    slope=None
    if len(losses)>=3:
        x=np.asarray([r['E'] for r in losses]);y=np.asarray([float(r['stop']) for r in losses])
        if np.ptp(x)>1e-12:
            if reference:
                design=np.column_stack((np.ones(len(x)),x))
                beta,_,rank,_=np.linalg.lstsq(design,y,rcond=1e-12)
                if rank==2:slope=float(beta[1])
            else:
                xc=x-x.mean();slope=float(xc@(y-y.mean())/(xc@xc))
    return [level,gain,slope]


def player(rows,reference=False):
    eligible=[r for r in rows if not r['censored'] and r['stop'] is not None and r['E'] is not None
              and r['score'] in (0.,.5,1.) and r['start'] is not None]
    counts=[];full=[];odd_even=[]
    for half in [0,1]:
        group=[r for r in eligible if int(r['start']>=SPLIT)==half]
        # Sessions are full source-defined units; do not recreate them from a
        # filtered outcome sequence, and never alternate individual games.
        starts={}
        for r in group:starts[r['session_id']]=min(starts.get(r['session_id'],float('inf')),r['start'])
        ordered=sorted(starts,key=lambda s:(starts[s],s));parity={s:i%2 for i,s in enumerate(ordered)}
        counts.append(dict(sessions=len(ordered),losses=sum(r['score']==0 for r in group),
                           wins=sum(r['score']==1 for r in group),rows=len(group)))
        full.append(indices(group,reference))
        odd_even.append([indices([r for r in group if parity[r['session_id']]==p],reference) for p in [0,1]])
    return dict(counts=counts,full=full,odd_even=odd_even,
                provisional_rows_retained=sum(r['provisional_session'] for r in eligible),
                all_time_controls=True)


def prepare(players,reference=False):
    names=[];entries=[]
    for name in sorted(players):
        names.append(name);entries.append(player(players[name],reference))
    def supported(sessions,losses):
        return [i for i,e in enumerate(entries) if all(c['sessions']>=sessions and c['losses']>=losses for c in e['counts'])]
    primary=supported(20,30);fallback=supported(10,15)
    chosen=primary if len(primary)>=1000 else fallback
    status='case_met' if len(primary)>=1000 else 'low reliability' if len(fallback)>=300 else 'below floor, descriptive'
    def number(v):return float('nan') if v is None else float(v)
    full=np.array([[[number(v) for v in half] for half in entries[i]['full']] for i in chosen]).reshape(-1,2,3)
    halves=np.array([[[[number(v) for v in parity] for parity in half] for half in entries[i]['odd_even']]
                     for i in chosen]).reshape(-1,2,2,3)
    return dict(names=[names[i] for i in chosen],full=full,halves=halves,status=status,
                support=dict(primary_players=len(primary),fallback_players=len(fallback),source_analysis_players=len(names)),
                provisional_rows_retained=sum(entries[i]['provisional_rows_retained'] for i in chosen),
                definition='All time controls; packet does not exclude provisional sessions for CH12; all missing indices remain explicit')


def moments(x,y,weights,reference=False):
    if not reference:return tr1.weighted_moments(x,y,weights)
    use=np.asarray(weights)>0;x=np.asarray(x)[use];y=np.asarray(y)[use];w=np.asarray(weights)[use]
    if len(x)<2 or not np.isfinite(x).all() or not np.isfinite(y).all() or w.sum()<=1:return None
    mx=np.average(x,weights=w);my=np.average(y,weights=w)
    vx=np.average((x-mx)**2,weights=w)*w.sum()/(w.sum()-1)
    vy=np.average((y-my)**2,weights=w)*w.sum()/(w.sum()-1)
    cov=np.average((x-mx)*(y-my),weights=w)*w.sum()/(w.sum()-1)
    if vx<=0 or vy<=0:return None
    return float(cov/math.sqrt(vx*vy)),float(vx),float(vy)


def evaluate(prepared,weights=None,reference=False):
    n=len(prepared['names']);weights=np.ones(n) if weights is None else np.asarray(weights,float)
    answer={}
    for column,name in enumerate(INDEX_NAMES):
        full=prepared['full'][:,:,column];halves=prepared['halves'][:,:,:,column]
        supported=np.isfinite(full).all(axis=1)&np.isfinite(halves).all(axis=(1,2))
        use=supported&(weights>0);w=weights[use]
        report=dict(supported_players=int(supported.sum()),undefined_players=int((~supported).sum()),
                    raw_correlation=None,reliabilities=None,true_variances=None,
                    minimum_true_variance=None,stability=None)
        paired=moments(full[use,0],full[use,1],w,reference)
        if paired is None:
            answer[name]=dict(report,status='unsupported');continue
        raw,vl,vr=paired;reliabilities=[]
        for side in [0,1]:
            m=moments(halves[use,side,0],halves[use,side,1],w,reference)
            reliabilities.append(None if m is None or m[0]<=-1 else 2*m[0]/(1+m[0]))
        report.update(raw_correlation=raw,reliabilities=reliabilities)
        if any(r is None for r in reliabilities):
            answer[name]=dict(report,status='undefined_reliability');continue
        true=[vl*reliabilities[0],vr*reliabilities[1]]
        report.update(true_variances=true,minimum_true_variance=min(true))
        if min(reliabilities)<=0:
            answer[name]=dict(report,status='nonpositive_reliability');continue
        answer[name]=dict(report,status='complete',stability=raw/math.sqrt(np.prod(reliabilities)))
    # Standard attenuation correction for LEVEL/GAIN is reported separately in
    # each half; their overlapping win-stop component is an explicit rival.
    correlation=[]
    for half in [0,1]:
        both=np.isfinite(prepared['full'][:,half,:2]).all(axis=1)&np.isfinite(prepared['halves'][:,half,:,:2]).all(axis=(1,2))
        use=both&(weights>0);w=weights[use]
        m=moments(prepared['full'][use,half,0],prepared['full'][use,half,1],w,reference)
        reliabilities=[]
        for column in [0,1]:
            h=moments(prepared['halves'][use,half,0,column],prepared['halves'][use,half,1,column],w,reference)
            reliabilities.append(None if h is None or h[0]<=-1 else 2*h[0]/(1+h[0]))
        corrected=None if m is None or any(v is None or v<=0 for v in reliabilities) else m[0]/math.sqrt(np.prod(reliabilities))
        correlation.append(corrected)
    answer['LEVEL_GAIN_corrected_correlations']=correlation
    return answer


def ci(values):
    if not values or any(v is None or not math.isfinite(v) for v in values):return None
    return np.quantile(values,[.025,.975]).tolist()


def result(prepared,draws,reference=False):
    point=evaluate(prepared,reference=reference);result={}
    for name in INDEX_NAMES:
        values=[d[name]['stability'] for d in draws]
        variances=[d[name]['minimum_true_variance'] for d in draws]
        interval=ci(values);variance_interval=ci(variances)
        variance_pass=variance_interval is not None and variance_interval[0]>0
        verdict='inconclusive'
        if variance_pass and interval is not None and prepared['status']!='below floor, descriptive' and point[name]['supported_players']>=300:
            verdict='stable' if interval[0]>.5 else 'not stable' if interval[1]<.2 else 'partly stable' if interval[0]>=.2 and interval[1]<=.5 else 'inconclusive'
        se=None if interval is None else float(np.std(values,ddof=1))
        result[name]=dict(point=point[name],interval=interval,true_variance_interval=variance_interval,
            variance_gate_pass=variance_pass,verdict=verdict,bar=.5,lower_band=.2,
            sees=None if se is None else 2.8*se,supports_at=None if se is None else .5+2.8*se,
            invalid_draws=sum(v is None for v in values))
    return dict(card='CH12',status=prepared['status'],support=prepared['support'],players=len(prepared['names']),
        indices=result,LEVEL_GAIN_corrected_correlations=dict(point=point['LEVEL_GAIN_corrected_correlations'],
            intervals=[ci([d['LEVEL_GAIN_corrected_correlations'][half] for d in draws]) for half in [0,1]]),
        provisional_rows_retained=prepared['provisional_rows_retained'],draws=len(draws),
        record_kind='claim',theory_tags=['H15-T11','H12-T7'],by_construction=False,
        activation=[],limitations=['A public game rating is not standing in a room.',
         'All time controls are included; changing composition between halves is a rival.',
         'LEVEL and GAIN share the win-stop term; simple reliability correction does not remove correlated measurement error.',
         'Reliability uses odd/even whole sessions; unsupported index values are not zero.',
         'The packet support floor is separate from the positive-true-variance gate.'])


def constructed_controls(people=2000,seed=20261112):
    """TR1's 1/.5/0 stability worlds re-pointed to bounded behavioral indices."""
    rng=np.random.default_rng(seed);worlds={}
    for rho in [1.,.5,0.]:
        a=rng.normal(size=(people,3));b=rng.normal(size=(people,3))
        a-=a.mean(axis=0);a/=a.std(axis=0,ddof=1)
        b-=b.mean(axis=0);b-=a*(np.sum(a*b,axis=0)/np.sum(a*a,axis=0));b/=b.std(axis=0,ddof=1)
        second=rho*a+math.sqrt(1-rho*rho)*b
        # Common positive scale preserves the exact generating correlations and
        # keeps LEVEL/GAIN away from impossible probability differences.
        scale=.08/max(np.max(abs(a)),np.max(abs(second)))
        latent=np.stack((a,second),axis=1)*scale+np.array([.25,.1,.05])
        noisy=latent[:,:,None,:]+rng.normal(0,scale/2,(people,2,2,3))
        full=noisy.mean(axis=2)
        prepared=dict(names=[str(i) for i in range(people)],full=full,halves=noisy,
            status='case_met',support={},provisional_rows_retained=0)
        worlds[str(rho)]=dict(expected=rho,prepared=prepared,estimate=evaluate(prepared))
    return worlds
