"""Frozen owner-defined secondary math; no source reads or result selection.

DESIGN CHECK: moderation includes every event interaction; no selected event or
median split. Raw floors precede transformations. Conditional-strength halves
may be undefined and are never zero-filled. Week2 endorsements are not event
counts. Source wave/day qualification remains separate from constructed math.
"""
import numpy as np
if __package__:
    from . import es_core_v1 as core
else:
    import es_core_v1 as core


def moderation_stats(people):
    stats=core.panel_stats(people,core.EVENTS,('ashamed',))
    means=[]
    for p in people:
        v=np.column_stack([p['ratings'][n] for n in core.EVENTS+('ashamed',)])
        keep=np.all(np.isfinite(v),axis=1)
        if keep.sum()>=10:means.append(float(np.mean(v[keep,3])))
    core.need(len(means)==len(stats['people']),'moderator population alignment differs')
    stats['usual_respected']=np.array(means)
    return stats


def moderation(stats,weights=None):
    sd,_,w=core.scale_and_sum(stats,weights);means=stats['usual_respected']
    if w.sum()<=1:raise core.Unidentified('moderator needs two people')
    centered=means-np.sum(w*means)/w.sum();variance=np.sum(w*centered**2)/(w.sum()-1)
    if variance<=0:raise core.Unidentified('usual respected does not vary')
    g=centered/np.sqrt(variance)
    gram=np.zeros((12,12));right=np.zeros(12)
    for p,weight,m in zip(stats['people'],w,g):
        xx=p['ss'][:6,:6]/sd[:6,None]/sd[None,:6]
        xy=p['ss'][:6,6]/sd[:6]/sd[6]
        gram+=weight*np.block([[xx,m*xx],[m*xx,m*m*xx]])
        right+=weight*np.concatenate((xy,m*xy))
    if np.linalg.matrix_rank(gram)<12:raise core.Unidentified('all-event moderation not identifiable')
    beta=np.linalg.solve(gram,right)
    return float(beta[7]-beta[8])


def _summary(x,y,days):
    finite=np.isfinite(y)&np.all(np.isfinite(x),axis=1)
    values=np.column_stack((x[finite],y[finite]));days=days[finite]
    centered=values-values.mean(0) if len(values) else values
    halves=[]
    for parity in (1,0):
        half=values[(days.astype(np.int64)%2)==parity]
        hc=half-half.mean(0) if len(half) else half
        halves.append((len(half),hc.T@hc))
    return {'n':len(values),'ss':centered.T@centered,'halves':halves}


def floor_stats(people,first,second,kind):
    core.need(kind in ('occurrence','strength'),'unknown floor panel')
    fields=core.NEGATIVE+tuple(first)+tuple(second);records=[]
    counts={'source_people':len(people),'missing_rows':0,'under_minimum_people':0,
            'original_complete_rows':0,'first_nonfloor_rows':0,'second_nonfloor_rows':0}
    for p in people:
        v=np.column_stack([p['ratings'][n] for n in fields]);days=np.asarray(p['days'],float)
        keep=np.all(np.isfinite(v),1)&np.isfinite(days);counts['missing_rows']+=int((~keep).sum())
        if keep.sum()<10:counts['under_minimum_people']+=1;continue
        v,days=v[keep],days[keep]
        core.need(np.all(days>=1)&np.all(days==np.floor(days)),'original day required')
        core.need(np.all((v>=1)&(v<=6)),'raw floor panel requires original six-point scale')
        counts['original_complete_rows']+=len(v)
        a=v[:,4:4+len(first)].mean(1);b=v[:,4+len(first):].mean(1)
        summaries=[]
        for label,mean in [('first',a),('second',b)]:
            above=mean>1;counts[label+'_nonfloor_rows']+=int(above.sum())
            response=above.astype(float) if kind=='occurrence' else np.where(above,mean-1,np.nan)
            summaries.append(_summary(v[:,:4],response,days))
        records.append(summaries)
    return {'people':records,'kind':kind,'counts':counts,'minimum_original_complete_prompts':10}


def floor_dial(stats,weights=None):
    w=core.weights_for(stats,weights);slopes=[]
    for side in (0,1):
        ss=sum(weight*p[side]['ss'] for p,weight in zip(stats['people'],w))
        df=sum(weight*max(0,p[side]['n']-1) for p,weight in zip(stats['people'],w))
        if df<=0 or np.any(np.diag(ss)<=0):raise core.Unidentified('floor panel pooled variance absent')
        sd=np.sqrt(np.diag(ss)/df);wx=1/sd[:4]/4
        values=np.full((len(stats['people']),2),np.nan)
        for i,p in enumerate(stats['people']):
            for half,(n,cov) in enumerate(p[side]['halves']):
                denominator=wx@cov[:4,:4]@wx
                if n>=2 and denominator>0:values[i,half]=(wx@cov[:4,4]/sd[4])/denominator
        slopes.append(values)
    return dial_from_slopes(*slopes,w)


def dial_from_slopes(a,b,w):
    keep=np.all(np.isfinite(a),1)&np.all(np.isfinite(b),1)
    count={'eligible_people':len(keep),'identified_people':int(keep.sum()),'unidentified_people':int((~keep).sum())}
    a,b,w=a[keep],b[keep],w[keep]
    ra=core.weighted_correlation(a[:,0],a[:,1],w);rb=core.weighted_correlation(b[:,0],b[:,1],w)
    record=dict(count,half_reliability_first=ra,half_reliability_second=rb)
    if not core.reliabilities_supported(ra,rb):return dict(record,status='UNSUPPORTED',latent=None)
    cross=(core.weighted_correlation(a[:,0],b[:,1],w)+core.weighted_correlation(a[:,1],b[:,0],w))/2
    return dict(record,status='IDENTIFIED',latent=float(cross/np.sqrt(ra*rb)),correction_clipped=False)


def week_prediction_stats(people,family):
    """Caller already bound original day/wave identity; no modulo/reset here.

    Each person supplies answered_counts_by_day counted before any rating
    exclusion. Counts of endorsements use complete four-negative-item rows;
    missing-item rows are excluded and explicitly counted, never treated as zero.
    Original >=10 complete interaction eligibility precedes the two-week split.
    """
    fields=core.NEGATIVE+tuple(family);kept=[]
    counts={'source_people':len(people),'under_minimum_people':0,'missing_rating_rows':0,
            'week1_missing_family_rows':0,'week2_missing_negative_rows':0,
            'unidentified_week1_people':0,'missing_week2_people':0,'outside_day_1_to_14_rows':0}
    for p in people:
        core.need('answered_counts_by_day' in p,'source answered-prompt counts required')
        v=np.column_stack([p['ratings'][n] for n in fields]);d=np.asarray(p['days'],float)
        finite_day=np.isfinite(d)
        core.need(np.all(d[finite_day]==np.floor(d[finite_day])) and np.all(d[finite_day]>=1),'original study day required')
        week1=finite_day&(d>=1)&(d<=7);week2=finite_day&(d>=8)&(d<=14)
        negative_complete=np.all(np.isfinite(v[:,:4]),1)
        first=week1&negative_complete&np.all(np.isfinite(v[:,4:]),1)
        second=week2&negative_complete
        counts['missing_rating_rows']+=int(((week1|week2)&~(first|second)).sum())
        counts['week1_missing_family_rows']+=int((week1&negative_complete&~first).sum())
        counts['week2_missing_negative_rows']+=int((week2&~negative_complete).sum())
        counts['outside_day_1_to_14_rows']+=int((finite_day&~(week1|week2)).sum())
        if int(first.sum()+second.sum())<10:counts['under_minimum_people']+=1;continue
        if first.sum()<2:counts['unidentified_week1_people']+=1;continue
        if not second.any():counts['missing_week2_people']+=1;continue
        x=v[first,:4];y=v[first,4:];c=np.column_stack((x,y));c-=c.mean(0)
        answered=p['answered_counts_by_day']
        n1=sum(answered.get(i,0) for i in range(1,8));n2=sum(answered.get(i,0) for i in range(8,15))
        core.need(n1>=first.sum() and n2>=second.sum(),'answered prompt counts understate complete rows')
        kept.append({'n':int(first.sum()),'ss':c.T@c,'week1_endorsements':int((v[week1&negative_complete,:4]>1).sum()),
                     'week2_endorsements':int((v[second,:4]>1).sum()),'answered_week1':n1,'answered_week2':n2})
    return {'people':kept,'counts':counts,'family_items':tuple(family)}


def week_prediction(stats,weights=None):
    w=core.weights_for(stats,weights)
    ss=sum(weight*p['ss'] for p,weight in zip(stats['people'],w))
    df=sum(weight*(p['n']-1) for p,weight in zip(stats['people'],w))
    if df<=0 or np.any(np.diag(ss)<=0):raise core.Unidentified('first-week pooled item variance absent')
    sd=np.sqrt(np.diag(ss)/df);wx=1/sd[:4]/4;wy=1/sd[4:]/len(stats['family_items'])
    design=[];outcome=[];weights_kept=[];unidentified=0
    for p,weight in zip(stats['people'],w):
        denominator=wx@p['ss'][:4,:4]@wx
        if denominator<=0:unidentified+=1;continue
        slope=(wx@p['ss'][:4,4:]@wy)/denominator
        design.append([1.,slope,p['week1_endorsements'],p['answered_week1'],p['answered_week2']])
        outcome.append(p['week2_endorsements']);weights_kept.append(weight)
    x=np.asarray(design);y=np.asarray(outcome);wk=np.asarray(weights_kept)
    if len(x)<5:raise core.Unidentified('first-week design has fewer than five people')
    weighted=x*np.sqrt(wk[:,None]);rhs=y*np.sqrt(wk)
    if np.linalg.matrix_rank(weighted)<5:raise core.Unidentified('first-week controls not jointly identifiable')
    beta=np.linalg.lstsq(weighted,rhs,rcond=None)[0]
    return {'reactivity_coefficient':float(beta[1]),'identified_people':len(x),'unidentified_week1_slopes':unidentified,
            'response':'week2 negative-item endorsements above raw minimum','events_counted':False}
