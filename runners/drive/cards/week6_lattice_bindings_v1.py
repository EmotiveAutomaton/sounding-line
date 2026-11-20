"""Array bindings for LD1, LD2 and LD3; no source reads or result claims.

DESIGN CHECK: LESSONS 3-5. Inputs are frozen, complete-case arrays. LD1 matches
the supplied occurrence design exactly; LD2 keeps all six status events and
the declared moderator. LD3 jointly fits all eight activity ratings. Whole-person
weights rebuild scales in every draw. Missing columns, support failures and
singular fits are explicit; they cannot become a zero or a new contrast.
"""
import numpy as np
from .week6_lattice_diary_v1 import InvalidFit, within, logit_fit, linear_fit

STATUS = ('admired','criticised','ignored','respected','upstaged','sidelined')
ACTIVITY = ('pleasant','fun','done','intellectual','overwhelmed','bored','concentrated','motivated')
FEAR_LIKE = ('anxious','ashamed','insecure')

def aligned(people, *values):
    ids=np.asarray(people)
    if ids.ndim!=1 or len(ids)==0:
        raise InvalidFit('Nonempty person roster required')
    arrays=[np.asarray(x,float) for x in values]
    if any(a.ndim not in (1,2) or len(a)!=len(ids) or not np.isfinite(a).all() for a in arrays):
        raise InvalidFit('Frozen finite aligned complete-case arrays required')
    return ids,arrays

def named_matrix(values, names, n):
    if set(values)!=set(names):
        raise InvalidFit('The entire declared predictor set is required')
    a=np.column_stack([values[name] for name in names])
    if a.shape!=(n,len(names)) or not np.isfinite(a).all():
        raise InvalidFit('Finite declared predictor columns required')
    return a

def form_l(people, predictors, outcomes, weight=None):
    ids,[x]=aligned(people,predictors)
    x,_,_=within(x,ids,weight)
    result={}
    for name,values in outcomes.items():
        _,[y]=aligned(ids,values)
        y,_,_=within(y,ids,weight)
        result[name]=linear_fit(x,y[:,0],weight)
    return result

def ld1(people, company, failure, outcomes, weight=None, *, floor=1):
    ids,(ctx,f)=aligned(people,company,failure)
    if ctx.ndim!=1 or not np.isin(ctx,[0,1]).all() or len(np.unique(ctx))!=2:
        raise InvalidFit('Both contexts with company=1, alone=0 required')
    if not {'ashamed','sad'}<=set(outcomes):
        raise InvalidFit('Ashamed and sad cannot be substituted')
    fw,fm,_=within(f,ids,weight);fw,fm=fw[:,0],fm[:,0]
    X=np.column_stack((np.ones(len(ids)),ctx,fw,fw*ctx,fm))
    fits={}
    for name,values in outcomes.items():
        _,[y]=aligned(ids,values)
        b=logit_fit(X,y>floor,weight)
        alone,company=float(b[2]),float(b[2]+b[3])
        fits[name]=dict(coefficients=b,alone=alone,company=company,
            ratio=company/alone if abs(alone)>1e-12 else None,
            ratio_interpretation='signed descriptive ratio; undefined at zero denominator')
    # The secondary raw-rating difference uses each context's own within-person
    # scales, exactly as the supplied preflight reference does.
    raw={}
    for context in (0,1):
        keep=ctx==context
        raw[context]=form_l(ids[keep],f[keep,None],
            {name:np.asarray(y)[keep] for name,y in outcomes.items()},
            None if weight is None else np.asarray(weight)[keep])
    secondary=float(raw[1]['ashamed'][0]-raw[0]['ashamed'][0]-raw[1]['sad'][0]+raw[0]['sad'][0])
    return dict(primary=float(fits['ashamed']['coefficients'][3]-fits['sad']['coefficients'][3]),
        form_l=secondary,feelings=fits,bar=.10,
        limit='A context difference in answer noise can produce this contrast; self-report in one sitting.')

def ld2_product(people, events, moderator, outcomes, weight=None, *, floor=1):
    ids=np.asarray(people)
    x=named_matrix(events,STATUS,len(ids))
    ids,[z]=aligned(ids,np.column_stack((x,moderator)))
    if set(outcomes)!={'angry',*FEAR_LIKE}:
        raise InvalidFit('Angry and all three fear-like feelings are required')
    z,means,_=within(z,ids,weight)
    product=z[:,STATUS.index('criticised')]*z[:,-1]
    X=np.column_stack((np.ones(len(ids)),z,product,means))
    product_index=1+z.shape[1]
    fits={}
    for name,values in outcomes.items():
        _,[y]=aligned(ids,values)
        fits[name]=logit_fit(X,y>floor,weight)
    contrast=float(fits['angry'][product_index]-np.mean([fits[k][product_index] for k in FEAR_LIKE]))
    # Exact same standardised predictor/product rows, with within-person outcome
    # standardisation, furnish the labelled linear diagnostic.
    raw_X=np.column_stack((z,product))
    raw={}
    for name,values in outcomes.items():
        yw,_,_=within(values,ids,weight)
        raw[name]=linear_fit(raw_X,yw[:,0],weight)
    secondary=float(raw['angry'][-1]-np.mean([raw[k][-1] for k in FEAR_LIKE]))
    return dict(primary=contrast,form_l=secondary,coefficients=fits,product_index=product_index,bar=.05,
        limit='Conduct and feeling share one prompt; changes in answer noise remain a rival.')

def role_support(people, partner_count, role, criticised, leadership, *, floor=1):
    """This API cannot receive feeling outcomes: the support check runs first."""
    ids,(count,role,crit,lead)=aligned(people,partner_count,role,criticised,leadership)
    below=(count==1)&np.isin(role,[2,7]);above=(count==1)&(role==1)
    strata={}
    for name,m in (('below',below),('above',above)):
        selected=m&(crit>floor)
        strata[name]=dict(criticised_prompts=int(selected.sum()),people=int(len(np.unique(ids[selected]))))
    enough=all(v['criticised_prompts']>=60 and v['people']>=40 for v in strata.values())
    check=float(lead[below].mean()-lead[above].mean()) if below.any() and above.any() else None
    return dict(strata=strata,support_passes=enough,lead_below_minus_above=check,
        coding_passes=check is not None and check>0,
        inferentially_eligible=enough and check is not None and check>0,
        other_codes={str(int(c)):int(((count==1)&(role==c)).sum()) for c in np.unique(role)
                     if c not in (1,2,3,5,6,7,9)})

def ld3(people, activity, feelings, weight=None):
    x=named_matrix(activity,ACTIVITY,len(people))
    if not {'enthusiastic','relaxed','anxious','angry'}<=set(feelings):
        raise InvalidFit('The two registered feeling contrasts cannot be substituted')
    table=form_l(people,x,feelings,weight)
    return dict(table=table,intellectual=float(table['enthusiastic'][3]-table['relaxed'][3]),
        overwhelmed=float(table['anxious'][4]-table['angry'][4]),bar=.05,
        limit='All activity ratings are jointly held; a single prompt carries both activity and feeling reports.')
