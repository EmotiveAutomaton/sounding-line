"""CH8 packet formulas and independent cross-product implementation.

DESIGN CHECK: no between-player comparison substitutes for player fixed effects.
Whole-player resampling keeps all rows/acts; missing and singular draws stay
explicit. The result is descriptive and cannot identify an emotional channel.
"""
from collections import Counter
import math
import numpy as np
from .week5_ch_models import keep_columns,solve

NAMES=('favourite_minus_underdog','middle','games','form_before','losing_streak','sin_hour','cos_hour','tournament','rapid')


def eligible(r,controls):
    return (r['time_control'] in controls and not r['provisional_session'] and not r['censored']
            and r['E'] is not None and r['score'] is not None and math.isfinite(r['form_before']))


def choose(players,floor=3000):
    support={}
    for controls in [('blitz',),('blitz','rapid')]:
        supported=[]
        for name,rows in players.items():
            clean=[r for r in rows if eligible(r,controls)]
            sessions=len({r['session_id'] for r in clean})
            losses=sum(r['score']==0 for r in clean)
            if sessions>=5 and losses>=10:supported.append(name)
        support['+'.join(controls)]=len(supported)
        if len(supported)>=floor:return sorted(supported),controls,'case_met',support
    if supported:return sorted(supported),controls,'below floor, descriptive',support
    return sorted(n for n,rows in players.items() if any(eligible(r,controls) for r in rows)),controls,'below floor, descriptive',support


def nuisance(row):
    hour=row['start']/3600%24
    return [row['index_in_session'],row['form_before'],row['losing_streak'],
            math.sin(2*math.pi*hour/24),math.cos(2*math.pi*hour/24),
            float(row['tournament']),float(row['time_control']=='rapid')]


def design(rows,kind='primary'):
    y=[];x=[]
    for r in rows:
        if r['score']!=0:continue
        if kind=='previous_gap' and r['previous_start_gap'] is None:continue
        if kind=='points_and_forecast' and r['rating_change'] is None:continue
        head=[float(r['E']>=.65),float(.35<r['E']<.65)]
        if kind=='points_and_forecast':head=[r['E'],-r['rating_change']]
        value=(r['previous_start_gap'] if kind=='previous_gap' else r['remaining_games']
               if kind=='remaining_games' else float(r['stop']))
        y.append(value);x.append(head+nuisance(r))
    return np.asarray(y,float),np.asarray(x,float).reshape(-1,len(NAMES))


def block(y,x,reference=False):
    y,x=np.asarray(y,float),np.asarray(x,float)
    if not len(y):return np.zeros((x.shape[1],x.shape[1])),np.zeros(x.shape[1])
    if not np.isfinite(x).all() or not np.isfinite(y).all():raise ValueError('Nonfinite CH8 input')
    if reference:
        # Independent fixed-effect elimination from raw sums, not demeaned rows.
        sx=np.sum(x,axis=0);sy=float(np.sum(y));n=len(y)
        return x.T@x-np.outer(sx,sx)/n,x.T@y-sx*sy/n
    xc=x-x.mean(axis=0);yc=y-y.mean()
    return xc.T@xc,xc.T@yc


def statistics(players,names,controls,kind='primary',reference=False):
    xx=[];xy=[];counts=[]
    for name in names:
        rows=[r for r in players[name] if eligible(r,controls)]
        y,x=design(rows,kind)
        a,b=block(y,x,reference)
        xx.append(a);xy.append(b);counts.append(len(y))
    xx=np.asarray(xx,float);xy=np.asarray(xy,float)
    if not len(xx) or not sum(counts):raise ValueError('No CH8 outcome rows')
    total=xx.sum(axis=0)
    norms=np.sqrt(np.maximum(np.diag(total),0))
    denom=np.outer(norms,norms)
    correlation=np.divide(total,denom,out=np.zeros_like(total),where=denom>1e-20)
    eigen,vectors=np.linalg.eigh(correlation)
    root=np.sqrt(np.where(eigen>1e-12,eigen,0))[:,None]*vectors.T
    # Eigenvectors can put roundoff in exactly-zero original columns. Do not
    # normalize that numerical dust into an apparent unit nuisance vector.
    root[:,norms==0]=0
    required=2 if kind=='points_and_forecast' else 1
    # Redundant nuisance columns can drop only among themselves. Testing the
    # targets last prevents a missing underdog reference or a perfectly
    # confounded covariate from silently changing the registered contrast.
    nuisance=[required+j for j in keep_columns(root[:,required:],0)]
    order=nuisance+list(range(required))
    accepted=keep_columns(root[:,order],0)
    if any(len(nuisance)+j not in accepted for j in range(required)):
        raise ValueError('Primary target not identifiable conditional on registered controls')
    kept=list(range(required))+nuisance
    labels=list(NAMES)
    if kind=='points_and_forecast':labels[:2]=['expected_score','rating_points_lost']
    return dict(xx=xx[:,kept][:,:,kept],xy=xy[:,kept],kept=kept,
                names=[labels[k] for k in kept],rows=sum(counts),players_with_rows=sum(n>0 for n in counts))


def coefficients(s,weights=None,reference=False):
    weights=np.ones(len(s['xx'])) if weights is None else np.asarray(weights,float)
    xx=np.einsum('i,ijk->jk',weights,s['xx'])
    xy=weights@s['xy']
    if reference:
        scale=np.sqrt(np.diag(xx))
        if np.any(scale<=1e-12):raise ValueError('Reference no variation')
        a=xx/np.outer(scale,scale);b=xy/scale
        answer,_,rank,_=np.linalg.lstsq(a,b,rcond=1e-10)
        if rank!=len(scale):raise ValueError('Reference singular draw')
        return answer/scale
    return solve(xx,xy)


def summaries(players,names,controls):
    surprises=np.asarray([r['surprise'] for name in names for r in players[name]
                          if eligible(r,controls) and r['surprise'] is not None])
    edges=np.quantile(surprises,np.arange(1,10)/10).tolist() if len(surprises) else []
    # Per-player numerators/denominators support the same complete-cluster draws.
    acts=np.zeros((len(names),3,4));curve=np.zeros((len(names),10,2));losses=stops=0
    for index,name in enumerate(names):
        for r in players[name]:
            if not eligible(r,controls):continue
            if r['surprise'] is not None and edges:
                b=int(np.searchsorted(edges,r['surprise'],side='right'))
                curve[index,b]+=[float(r['stop']),1]
            if r['score']!=0:continue
            losses+=1;stops+=int(r['stop'])
            if not r['tournament']:
                b=0 if r['E']<=.35 else 2 if r['E']>=.65 else 1
                a=0 if r['stop'] else 1 if r['rematch'] else 2
                acts[index,b,a]+=1;acts[index,b,3]+=1
    return dict(acts=acts,curve=curve,surprise_edges=edges,losses=losses,stops=stops,
                overall_loss_stop=None if not losses else stops/losses)


def ratios(summary,weights=None):
    weights=np.ones(len(summary['acts'])) if weights is None else np.asarray(weights,float)
    acts=np.einsum('i,ijk->jk',weights,summary['acts'])
    curve=np.einsum('i,ijk->jk',weights,summary['curve'])
    def ratio(a,b):return None if b==0 else float(a/b)
    return dict(three_acts=[[ratio(a,n) for a in row[:3]] for row in acts for n in [row[3]]],
                stop_by_surprise_decile=[ratio(row[0],row[1]) for row in curve])


def estimate(players,floor=3000,reference=False):
    names,controls,status,support=choose(players,floor)
    stats={};points={}
    for kind in ['primary','previous_gap','points_and_forecast','remaining_games']:
        try:
            stats[kind]=statistics(players,names,controls,kind,reference)
            points[kind]=dict(coefficients=coefficients(stats[kind],reference=reference).tolist(),
                              rows=stats[kind]['rows'],kept=stats[kind]['kept'],columns=stats[kind]['names'],players=stats[kind]['players_with_rows'])
        except ValueError as exc:points[kind]=dict(unsupported=str(exc))
    summary=summaries(players,names,controls)
    return dict(names=names,controls=controls,status=status,support=support,
                statistics=stats,points=points,summary=summary)


def draw(prepared,weights,reference=False):
    output={}
    for kind,stats in prepared['statistics'].items():
        try:output[kind]=coefficients(stats,weights,reference).tolist()
        except ValueError:output[kind]=None
    output.update(ratios(prepared['summary'],weights))
    return output


def interval(values):
    if not values or any(v is None or not math.isfinite(v) for v in values):return None
    return np.quantile(values,[.025,.975]).tolist()


def result(prepared,draws):
    point=prepared['points'];bar=None if prepared['summary']['overall_loss_stop'] is None else .1*prepared['summary']['overall_loss_stop']
    output={}
    for kind in point:
        if 'unsupported' in point[kind]:output[kind]=point[kind];continue
        width=len(point[kind]['coefficients'])
        values=[[None if d.get(kind) is None else d[kind][j] for d in draws] for j in range(width)]
        output[kind]=dict(point[kind],intervals=[interval(v) for v in values] if point[kind]['players']>=2 else [None]*width,
                          uncertainty_qualified=point[kind]['players']>=2,
                          invalid_draws=sum(d.get(kind) is None for d in draws))
        if kind=='primary':
            homogeneous=prepared['summary']['stops'] in (0,prepared['summary']['losses'])
            if homogeneous:
                output[kind]['intervals']=[None]*width
                output[kind]['uncertainty_qualified']=False
            ci=output[kind]['intervals'][0]
            se=None if ci is None else float(np.std(values[0],ddof=1))
            label='inconclusive'
            if ci is not None and bar is not None:
                label='more yielding after unexpected loss' if ci[0]>bar else 'more playing on after unexpected loss' if ci[1]<-bar else 'inside practical band' if ci[0]>=-bar and ci[1]<=bar else 'inconclusive'
            output[kind].update(bar=bar,sees=None if se is None else 2.8*se,
                               supports_at=None if se is None or bar is None else bar+2.8*se,
                               descriptive_pattern=label,causal_or_channel_verdict=False)
    ratio_point=ratios(prepared['summary'])
    act_people=(prepared['summary']['acts'][:,:,3]>0).sum(axis=0)
    curve_people=(prepared['summary']['curve'][:,:,1]>0).sum(axis=0)
    act_ci=[[interval([d['three_acts'][i][j] for d in draws]) if act_people[i]>=2 and ratio_point['three_acts'][i][j] not in (None,0.,1.) else None for j in range(3)] for i in range(3)]
    curve_ci=[interval([d['stop_by_surprise_decile'][i] for d in draws]) if curve_people[i]>=2 and ratio_point['stop_by_surprise_decile'][i] not in (None,0.,1.) else None for i in range(10)]
    return dict(card='CH8',status=prepared['status'],support=prepared['support'],controls=list(prepared['controls']),
        players=len(prepared['names']),loss_rows=prepared['summary']['losses'],estimates=output,
        three_acts=dict(point=ratio_point['three_acts'],intervals=act_ci,bins=['underdog','middle','favourite'],
                        acts=['stop','rematch','different_opponent'],non_tournament_only=True,people_per_bin=act_people.tolist()),
        surprise_curve=dict(point=ratio_point['stop_by_surprise_decile'],intervals=curve_ci,
                            cuts=prepared['summary']['surprise_edges'],all_results=True,people_per_bin=curve_people.tolist()),
        draws=len(draws),record_kind='claim',theory_tags=['H15-T1'],by_construction=False,
        activation=[dict(channel='SHAME',set_point='seen as competent, analogy only',
            moved='loss below forecast',could_do='stop, rematch or play somebody else',
            observed='complete descriptive STOP/REMATCH estimates',relation='behavioral analogy; channel identity untested')],
        limitations=['One-person and homogeneous binary cells have point/count diagnostics only, no population interval.','A public game rating is not standing in a room.','State confounding remains; this card is descriptive.',
                     'Favourite losses cost more rating points by construction.',
                     'The pre-pairing-gap falsification inherits residual session confounding when nonzero.'])
