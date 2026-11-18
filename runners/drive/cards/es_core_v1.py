"""Prospective openESM numerical core. Unrun; no source I/O or admission.

DESIGN CHECK: LESSONS 2, 3, 5 and the IN14 sampling-model correction. Person
offsets cannot create within-person effects. All six status predictors remain
joint. Cross-half reactivity is never replaced by same-prompt correlation.
Unsupported variance and invalid bootstrap draws stay explicit and unclipped.
Constructed known answers are required before this code sees human records.
"""
from itertools import combinations
import numpy as np

EVENTS = ('admired','criticised','ignored','respected','upstaged','sidelined')
FEELINGS = ('proud','success','superior','angry','excluded','envious','resentful',
            'ashamed','insecure','enthusiastic','relaxed','anxious','sad','lonely')
FAMILIES = {'anger':('angry','resentful'), 'fear':('anxious','insecure'),
            'ashamed':('ashamed',), 'sad':('sad','lonely','excluded')}
NEGATIVE = ('criticised','ignored','upstaged','sidelined')


class Unidentified(ValueError):
    pass


def need(value, message):
    if not value:
        raise ValueError(message)


def finite_array(value, ndim=None):
    result = np.asarray(value, dtype=np.float64)
    need(ndim is None or result.ndim == ndim, 'array dimension differs')
    need(np.all(np.isfinite(result)), 'nonfinite prepared array')
    return result


def panel_stats(people, xnames, ynames, minimum=10, require_days=False):
    """Common complete-case panel, then eligible people; retain all exclusions.

    A person record has integer `days` and a dictionary `ratings` of equal-length
    arrays. NaN means a source-allowed missing rating, never a zero rating.
    X/Y units are preserved in cached sums; pooled scaling is recomputed for
    each whole-person draw with denominator sum_i weight_i*(n_i-1).
    """
    xnames,ynames=tuple(xnames),tuple(ynames)
    need(type(minimum) is int and minimum>=2,'positive identifiable panel minimum required')
    need(len(set(xnames+ynames)) == len(xnames+ynames), 'duplicate panel field')
    fields = xnames+ynames
    kept, excluded = [], {'source_people':len(people), 'missing_rows':0,
                         'under_minimum_people':0, 'under_minimum_rows':0}
    for person in people:
        columns = [np.asarray(person['ratings'][n], dtype=np.float64) for n in fields]
        need(all(c.ndim == 1 and len(c) == len(person['days']) for c in columns),
             'column/day alignment differs')
        values = np.column_stack(columns)
        need(not np.any(np.isinf(values)), 'infinite rating')
        days=np.asarray(person['days'],dtype=np.float64)
        valid = np.all(np.isfinite(values), axis=1)
        if require_days:
            valid &= np.isfinite(days)
        excluded['missing_rows'] += int((~valid).sum())
        n = int(valid.sum())
        if n < minimum:
            excluded['under_minimum_people'] += 1
            excluded['under_minimum_rows'] += n
            continue
        v = values[valid]; days = days[valid]
        if require_days:
            need(np.all(np.isfinite(days)) and np.all(days == np.floor(days)) and np.all(days>=1),
                 'positive original study days required')
        centered = v-v.mean(axis=0)
        full = centered.T@centered
        halves=[]
        if require_days:
            for parity in (1,0):
                h = v[(days.astype(np.int64)%2)==parity]
                hc = h-h.mean(axis=0) if len(h) else h
                halves.append((len(h),hc.T@hc))
        kept.append({'n':n,'ss':full,'halves':halves})
    return {'people':kept,'xnames':tuple(xnames),'ynames':tuple(ynames),
            'excluded':excluded,'fields':tuple(fields),'minimum':minimum,
            'original_day_split':require_days}


def weights_for(stats, weights):
    n=len(stats['people'])
    if n==0: raise Unidentified('no supported people')
    w=np.ones(n,dtype=np.float64) if weights is None else finite_array(weights,1)
    need(len(w)==n and np.all(w>=0) and np.all(w==np.floor(w)) and w.sum()>0,
         'whole-person bootstrap frequencies required')
    return w


def scale_and_sum(stats, weights=None):
    w=weights_for(stats,weights)
    ss=np.einsum('p,pij->ij',w,np.array([p['ss'] for p in stats['people']]))
    df=sum(weight*(p['n']-1) for weight,p in zip(w,stats['people']))
    variance=np.diag(ss)/df
    if np.any(variance<=0): raise Unidentified('zero pooled within-person variance')
    return np.sqrt(variance),ss,w


def joint_fit(stats, weights=None):
    sd,ss,w=scale_and_sum(stats,weights)
    nx=len(stats['xnames']);xx=ss[:nx,:nx]
    if np.linalg.matrix_rank(xx)<nx: raise Unidentified('joint predictors not identifiable')
    beta=np.linalg.solve(xx,ss[:nx,nx:]) * sd[:nx,None] / sd[None,nx:]
    need(np.all(np.isfinite(beta)), 'nonfinite joint fit')
    return beta.T


def es1_contrasts(beta, outcomes):
    b={name:beta[i] for i,name in enumerate(outcomes)}
    x={name:i for i,name in enumerate(EVENTS)}
    result={}
    if 'ashamed' in b:result['a']=float(b['ashamed'][x['criticised']]-b['ashamed'][x['ignored']])
    if 'lonely' in b:result['b']=float(b['lonely'][x['ignored']]-b['lonely'][x['criticised']])
    if 'angry' in b:result['c']=float(b['angry'][x['criticised']]-(b['angry'][x['ignored']]+b['angry'][x['sidelined']])/2)
    if 'proud' in b and 'relaxed' in b:result['d']=float(b['proud'][x['admired']]-b['relaxed'][x['admired']])
    # Packet e specifies the conditional upstaged coefficient, not a second event contrast.
    if 'envious' in b:result['e']=float(b['envious'][x['upstaged']])
    return result


def weighted_correlation(a,b,w):
    a=finite_array(a,1);b=finite_array(b,1);w=finite_array(w,1)
    need(a.shape==b.shape==w.shape and np.all(w>=0),'correlation alignment differs')
    if w.sum()<=1: raise Unidentified('correlation requires at least two people')
    da=a-np.sum(w*a)/w.sum();db=b-np.sum(w*b)/w.sum()
    aa=np.sum(w*da*da);bb=np.sum(w*db*db)
    if aa<=0 or bb<=0: raise Unidentified('constant between-person slopes')
    return float(np.sum(w*da*db)/np.sqrt(aa*bb))


def reactivities(stats, family_items, weights=None):
    """Graded slopes, using each half's own intercept; no binary-event proxy."""
    need(stats['original_day_split'] is True,'original odd/even day split required')
    sd,_,w=scale_and_sum(stats,weights);nx=len(stats['xnames'])
    wx=1/sd[:nx]/nx
    wy=np.zeros(len(stats['ynames']),dtype=np.float64)
    for item in family_items:
        wy[stats['ynames'].index(item)]=1/sd[nx+stats['ynames'].index(item)]/len(family_items)
    slopes=np.full((len(stats['people']),2),np.nan)
    for p,person in enumerate(stats['people']):
        for half,(n,ss) in enumerate(person['halves']):
            denominator=wx@ss[:nx,:nx]@wx
            if n>=2 and denominator>0:
                slopes[p,half]=(wx@ss[:nx,nx:]@wy)/denominator
    return slopes,w


def dial(stats, first, second, weights=None):
    a,w=reactivities(stats,first,weights);f,_=reactivities(stats,second,weights)
    valid=np.all(np.isfinite(a),axis=1)&np.all(np.isfinite(f),axis=1)
    # Algebraically undefined slopes are excluded and counted, not replaced or regularized.
    support={'eligible_people':len(valid),'identified_people':int(valid.sum()),
             'unidentified_people':int((~valid).sum())}
    a,f,w=a[valid],f[valid],w[valid]
    ra=weighted_correlation(a[:,0],a[:,1],w);rf=weighted_correlation(f[:,0],f[:,1],w)
    record=dict(support,half_reliability_first=ra,half_reliability_second=rf)
    if not reliabilities_supported(ra,rf):return dict(record,status='UNSUPPORTED',latent=None,reason='odd_even_reliability_below_0.15')
    cross=(weighted_correlation(a[:,0],f[:,1],w)+weighted_correlation(a[:,1],f[:,0],w))/2
    same=(weighted_correlation(a[:,0],f[:,0],w)+weighted_correlation(a[:,1],f[:,1],w))/2
    denominator=np.sqrt(ra*rf)
    return dict(record,status='IDENTIFIED',latent=float(cross/denominator),cross_half_raw=cross,
                same_prompt_trap=float(same/denominator),correction_clipped=False)


def reliabilities_supported(first,second):
    need(np.isfinite(first) and np.isfinite(second),'nonfinite half reliability')
    return first>=.15 and second>=.15


def dial_reading(lower,upper):
    need(np.isfinite(lower) and np.isfinite(upper) and lower<=upper,'invalid full-draw interval')
    if lower>=0.90:return 'ONE_DIAL'
    if upper<=0.85:return 'MORE_THAN_ONE'
    return 'UNRESOLVED'


def bootstrap(stats, statistic, seed, draws=2000, progress=lambda row:None, prior=()):
    """Exact whole-person resampling. Preserve every invalid draw, never redraw.

    Each draw has its own deterministic SeedSequence, so a retained prefix can
    resume without replaying fits. Caller authenticates source/config/code and
    every prior draw receipt before providing `prior`.
    """
    need(type(draws) is int and draws==2000,'packet requires 2000 whole-person draws')
    n=len(stats['people']);need(n>0,'empty bootstrap population')
    result=[dict(row) for row in prior]
    need([r['draw'] for r in result]==list(range(len(result))) and len(result)<=draws,
         'noncontiguous bootstrap checkpoint')
    for draw in range(len(result),draws):
        rng=np.random.default_rng(np.random.SeedSequence([seed,draw]))
        weights=np.bincount(rng.integers(n,size=n),minlength=n)
        try:
            value=statistic(weights)
            if isinstance(value,dict):
                if value.get('status')!='IDENTIFIED':
                    raise Unidentified('draw does not identify corrected correlation')
                value=value['latent']
            values=finite_array(np.atleast_1d(value),1)
            record={'draw':draw,'status':'VALID','value':values.tolist()}
        except (Unidentified,np.linalg.LinAlgError) as exc:
            record={'draw':draw,'status':'INVALID','reason':str(exc)}
        result.append(record);progress(record)
    invalid=sum(r['status']!='VALID' for r in result)
    interval=None
    if invalid==0:
        interval=np.quantile(np.array([r['value'] for r in result]),[.025,.975],axis=0).T.tolist()
    return {'draws':result,'invalid_draws':invalid,'interval':interval,
            'status':'INTERVAL_UNAVAILABLE' if invalid else 'COMPLETE',
            'redraws':0,'valid_draw_only_interval':False}


def primary_gap(gap):
    need(np.isfinite(gap) and gap>0,'positive finite prompt gap required')
    return 'short' if gap<90 else 'long' if gap>240 else 'middle'


def five_gap_bins(gap):
    need(np.isfinite(gap) and gap>0,'positive finite prompt gap required')
    return 0 if gap<45 else 1 if gap<90 else 2 if gap<150 else 3 if gap<=240 else 4


def carry_slope(people, lower, upper, include_lower, include_upper):
    """Within-person pair slope in an explicitly bounded gap panel.

    Caller supplies canonical already-scaled antecedent/consequent arrays; this
    function subtracts each person's within-panel means, with no pooled-person
    substitute. Timestamp construction is the separately held source adapter.
    """
    xx=xy=0.;used=0;rows=0
    for person in people:
        gap=finite_array(person['gap'],1);x=finite_array(person['x'],1);y=finite_array(person['y'],1)
        need(gap.shape==x.shape==y.shape,'carry pair alignment differs')
        keep=((gap>=lower) if include_lower else (gap>lower))&((gap<=upper) if include_upper else (gap<upper))
        a=x[keep];b=y[keep]
        if len(a)<2:continue
        a=a-a.mean();b=b-b.mean();v=float(a@a)
        if v==0:continue
        xx+=v;xy+=float(a@b);used+=1;rows+=len(a)
    if xx<=0:raise Unidentified('no identifiable within-person carry slope')
    return {'slope':xy/xx,'identified_people':used,'identified_pairs':rows}


def carry_primary(people):
    short=carry_slope(people,0,90,False,False)
    long=carry_slope(people,240,np.inf,False,True)
    return {'short':short,'long':long,'contrast':short['slope']-long['slope'],
            'bar':0.05,'strict_primary_bounds':True}
