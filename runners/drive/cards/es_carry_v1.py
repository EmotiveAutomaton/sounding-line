"""ES3 math on canonically scoped paired ratings; actual clock adapter held.

DESIGN CHECK: within-person carry, fixed strict boundaries, whole-person draws,
no shared-day-only contrast. Original item calibration sufficient statistics
are supplied separately so every draw recomputes pooled within-person scales.
No source units, waveform resets or eligible calibration rows are inferred here.
"""
import numpy as np
if __package__:
    from . import es_core_v1 as core
else:
    import es_core_v1 as core

BINS=((0.,45.,False,False),(45.,90.,True,False),(90.,150.,True,False),
      (150.,240.,True,True),(240.,np.inf,False,True))


def stats(people,outcomes):
    """Raw pair arrays plus reviewed original prompt-calibration moments.

    Person input: gap, x, ys NxK, calibration_n (one per item), calibration_ss
    (within-person residual sums of squares per item), original_interactions.
    The source caller must bind which eligible prompts supplied those moments.
    Items are antecedent angry, then the named consequent feelings.
    """
    core.need(tuple(outcomes) in (('angry',),('angry','sad','anxious')),'carry outcomes differ')
    prepared=[];counts={'source_people':len(people),'under_ten_interactions':0}
    for person in people:
        if person['original_interactions']<10:counts['under_ten_interactions']+=1;continue
        gap=core.finite_array(person['gap'],1);x=core.finite_array(person['x'],1);ys=core.finite_array(person['ys'],2)
        core.need(len(gap)==len(x)==len(ys) and ys.shape[1]==len(outcomes),'carry alignment differs')
        core.need(np.all(gap>0),'nonpositive gap')
        ns=core.finite_array(person['calibration_n'],1);ss=core.finite_array(person['calibration_ss'],1)
        core.need(len(ns)==len(ss)==1+len(outcomes) and np.all(ns>=2) and np.all(ns==np.floor(ns)) and np.all(ss>=0),
                  'original calibration moments invalid')
        rows=[]
        for lo,hi,include_lo,include_hi in BINS:
            mask=((gap>=lo) if include_lo else (gap>lo))&((gap<=hi) if include_hi else (gap<hi))
            values=np.column_stack((x[mask],ys[mask]));centered=values-values.mean(0) if len(values) else values
            rows.append({'n':len(values),'cov':centered.T@centered})
        # Primary short combines first TWO bins before centering. Summing their
        # separately-centered covariances would silently change its estimand.
        values=np.column_stack((x[gap<90],ys[gap<90]));centered=values-values.mean(0) if len(values) else values
        short={'n':len(values),'cov':centered.T@centered}
        prepared.append({'bins':rows,'short':short,'calibration_n':ns,'calibration_ss':ss})
    return {'people':prepared,'outcomes':tuple(outcomes),'counts':counts}


def estimates(stats,weights=None):
    w=core.weights_for(stats,weights)
    ss=sum(weight*p['calibration_ss'] for p,weight in zip(stats['people'],w))
    df=sum(weight*(p['calibration_n']-1) for p,weight in zip(stats['people'],w))
    if np.any(df<=0) or np.any(ss<=0):raise core.Unidentified('original carry calibration lacks variance')
    sd=np.sqrt(ss/df);nout=len(stats['outcomes'])
    def slope(which):
        cov=np.zeros((nout+1,nout+1));used=0;pairs=0
        for p,weight in zip(stats['people'],w):
            part=p['short'] if which=='short' else p['bins'][which]
            if part['n']<2 or part['cov'][0,0]<=0:continue
            cov+=weight*part['cov'];used+=int(weight);pairs+=int(weight)*part['n']
        if cov[0,0]<=0:return {'status':'UNSUPPORTED','slopes':None,'identified_people':used,'pairs':pairs}
        result=(cov[0,1:]/cov[0,0])*sd[0]/sd[1:]
        return {'status':'IDENTIFIED','slopes':result.tolist(),'identified_people':used,'pairs':pairs}
    bins=[slope(i) for i in range(5)];short=slope('short');long=bins[-1]
    primary=None if short['slopes'] is None or long['slopes'] is None else short['slopes'][0]-long['slopes'][0]
    return {'primary':primary,'short':short,'long':long,'five_bins':bins,'strict_primary_bounds':True,
            'outcomes':list(stats['outcomes']),'bar':.05}


def primary_statistic(stats,weights=None):
    value=estimates(stats,weights)['primary']
    if value is None:raise core.Unidentified('short or long carry unsupported')
    return value


def person_coupling(reactivity,carry,weights):
    """Descriptive full-person slopes; caller must freeze their source join."""
    a=np.asarray(reactivity,float);b=np.asarray(carry,float);w=np.asarray(weights,float)
    core.need(a.shape==b.shape==w.shape and a.ndim==1,'person slope alignment differs')
    keep=np.isfinite(a)&np.isfinite(b)
    return {'correlation':core.weighted_correlation(a[keep],b[keep],w[keep]),
            'identified_people':int(keep.sum()),'undefined_people':int((~keep).sum()),
            'descriptive_uncorrected_correlation':True}
