"""Compare six acoustic features with independent facts on held-out laughs."""
from collections import Counter
import numpy as np
from sklearn.metrics import adjusted_rand_score
from sklearn.mixture import GaussianMixture

from runners.drive.cards.week7_lgh1_sound_v1 import measures
from runners.drive.cards.week7_phase1_operators import merge_components
from runners.drive.cards.week6_sealed_support_v1 import SealedFailure, write_tables
from runners.drive.cards.week6_la78_models_v1 import speaking_share
from runners.drive.cards.week6_la78_targets_v1 import SpeakerFloor, attribute


FEATURES=('duration_seconds','bursts','voiced_fraction','relative_pitch_semitones',
          'pitch_iqr_semitones','relative_level_db')
FACTS=('speaking','joined','target_share_change','partner_rating')


def heldout_facts(conversation,utterances,marks,start,end,partner_ratings,window=2.):
    actors=set(u['speaker'] for u in utterances)|set(l['speaker'] for l in marks)
    floors={p:SpeakerFloor([u for u in utterances if u['speaker']==p]) for p in actors}
    _,_,events=attribute(marks,floors,{p:'speaker' for p in actors},window)
    output=[]
    for actor,onset,targets,_ in events:
        others=[other for other in actors if other!=actor]
        row=dict(conversation=conversation,speaker=actor,
                 speaking=int(floors[actor].qualifying_end(onset,0.) is not None),
                 joined=int(any(other!=actor and onset<=other_onset<=onset+1
                                for other,other_onset,_,_ in events)),
                 overlap_other=int(any(floors[p].qualifying_end(onset,0.) is not None for p in others)),
                 partner_rating=partner_ratings.get(actor,np.nan))
        if len(targets)==1 and start<=onset-60 and onset+60<=end:
            target,=targets
            before=speaking_share(target,floors,onset-60,onset,'voiced')
            after=speaking_share(target,floors,onset,onset+60,'voiced')
            if before is not None and after is not None:
                row.update(target_share_change=after-before,target_share_before=before,target_share_after=after)
        output.append(row)
    return output


def sound(marked_laugh,reference_speech,sample_rate):
    item=measures(marked_laugh,reference_speech,sample_rate)
    return [item[key] for key in FEATURES]


def mixture(x):
    fits=[GaussianMixture(k,n_init=3,random_state=20261122,reg_covar=1e-5).fit(x)
          for k in range(1,min(6,len(x))+1)]
    return min(fits,key=lambda m:m.bic(x))


def between(values,group):
    total=np.sum((values-values.mean())**2)
    if total==0:return 0.
    return sum(np.sum(group==g)*(values[group==g].mean()-values.mean())**2
               for g in np.unique(group))/total


def evaluate(features,metadata,out,*,shuffles=200,draws=2000):
    x=np.asarray(features,float)
    if x.shape!=(len(metadata),6):raise ValueError('six authorized sound features required')
    speakers=np.array([row['speaker'] for row in metadata])
    conv=np.array([row['conversation'] for row in metadata])
    if any(s in ('',None) for s in speakers) or any(c in ('',None) for c in conv):
        raise ValueError('missing membership')
    universe=frozenset(speakers)
    retained=np.flatnonzero(np.isfinite(x).all(axis=1))
    if len(retained)<24 or len(universe)<11:raise SealedFailure(12,'insufficient acoustic support')
    rng=np.random.default_rng(2026112205)
    shuffled=rng.permutation(retained)
    train,test=np.array_split(shuffled,2)
    spread=x[train].std(axis=0)
    if np.any(spread<=0):raise SealedFailure(12,'constant feature')
    z=(x-x[train].mean(axis=0))/spread
    model=mixture(z[train])
    _,dips=merge_components(model)
    group=model.predict(z[test])
    repeat=mixture(z[test])
    center=model.means_
    axis=np.linalg.svd(z[train],full_matrices=False)[2][0]
    axis*=1 if axis[np.argmax(np.abs(axis))]>=0 else -1
    position=z[test]@axis
    protected=[universe]
    def membership(mask):
        members=frozenset(speakers[test[mask]])
        if len(members)<11:return 0
        cells=Counter(tuple(p in branch for branch in (*protected,members)) for p in universe)
        if min(cells.values())<11:return 0
        if members not in protected:protected.append(members)
        return len(members)
    audible=frozenset(speakers[retained])
    if len(audible)<11 or 0<len(universe-audible)<11:
        raise SealedFailure(12,'acoustic roster disclosure')
    protected.append(audible)
    test_n=membership(np.ones(len(test),dtype=bool))
    if test_n<11:raise SealedFailure(12,'held-out roster disclosure')
    catalog={'mixture':[dict(components=model.n_components,dip_groups=dips,
        heldout_components=repeat.n_components,half_agreement=adjusted_rand_score(group,repeat.predict(z[test])),
        n=test_n)],'fractions':[],'facts':[],'within_groups':[],'target_minutes':[],
        'joined_acoustics':[],'overlap':[]}
    for value in (0,1):
        mask=np.array([metadata[i].get('overlap_other')==value for i in test],dtype=bool)
        n_overlap=membership(mask)
        if n_overlap:
            catalog['overlap'].append(dict(other_speaking=value,heldout_laughs=int(mask.sum()),n=n_overlap))
    sizes=np.bincount(group,minlength=model.n_components)
    largest=int(np.argmax(sizes))
    distance=np.linalg.norm(center-center[largest],axis=1)
    distance[largest]=np.inf
    nearest=int(np.argmin(distance)) if len(center)>1 else -1
    for g in np.unique(group):
        mask=group==g
        n=membership(mask)
        if n:
            catalog['fractions'].append(dict(component=int(g)+1,share=mask.mean(),largest=int(g==largest),
                                             nearest_to_largest=int(g==nearest),n=n))
        before=np.array([metadata[i].get('target_share_before',np.nan) for i in test],float)
        after=np.array([metadata[i].get('target_share_after',np.nan) for i in test],float)
        paired=mask & np.isfinite(before) & np.isfinite(after)
        n_target=membership(paired)
        if n_target:
            catalog['target_minutes'].append(dict(component=int(g)+1,share_before=before[paired].mean(),
                share_after=after[paired].mean(),share_change=(after[paired]-before[paired]).mean(),n=n_target))
    for fi,fact in enumerate(FACTS,1):
        y=np.array([metadata[i].get(fact,np.nan) for i in test],float)
        mask=np.isfinite(y)
        n=membership(mask)
        if not n:continue
        v=y[mask];g=group[mask]
        if len(np.unique(g))>=2:
            obs=between(v,g)
            null=[between(rng.permutation(v),g) for _ in range(shuffles)]
            catalog['facts'].append(dict(fact=fi,fraction_explained=obs,shuffle_95=np.quantile(null,.95),n=n))
        for label in np.unique(g):
            take=mask&(group==label)
            n_group=membership(take)
            if not n_group:continue
            axis_values=position[take]
            if np.var(axis_values)>0:
                slope=np.cov(axis_values,y[take],ddof=0)[0,1]/np.var(axis_values)
                catalog['within_groups'].append(dict(fact=fi,component=int(label)+1,mean=y[take].mean(),
                                                      axis_slope=slope,n=n_group))
    # Spontaneity proxy, with whole conversations resampled and zero-support
    # intervals withheld. The two joined groups also pass the membership check.
    joined=np.array([metadata[i].get('joined',np.nan) for i in test],float)
    yes,no=joined==1,joined==0
    if membership(yes) and membership(no):
        n=membership(yes|no)
        conversations,idx=np.unique(conv[test],return_inverse=True)
        if n:
            F=x[test][:,[2,3]]
            point=F[yes].mean(axis=0)-F[no].mean(axis=0)
            bank=[]
            for _ in range(draws):
                w=np.bincount(rng.integers(len(conversations),size=len(conversations)),
                              minlength=len(conversations))[idx]
                if not w[yes].sum() or not w[no].sum():break
                bank.append(np.average(F[yes],weights=w[yes],axis=0)-np.average(F[no],weights=w[no],axis=0))
            if len(bank)==draws:
                bounds=np.quantile(bank,[.025,.975],axis=0)
                for i in range(2):
                    catalog['joined_acoustics'].append(dict(measure=i+1,difference=point[i],
                        lower=bounds[0,i],upper=bounds[1,i],n=n))
    return write_tables(out,catalog)
