"""Choose one additional observation before its outcome crosses the boundary.

DESIGN CHECK: S02/S03/S04/T02/X02/X05/X06/X08; LESSONS 3--5, CONTROLS 6--7.
NULL: identical future policies have zero consequential information even when the
observation is noisy; repeated preview content never creates independent evidence.
ALTERNATIVE: a purchased observation can change a persistent-maker posterior and
its separate future forecast. Purchases contain only already revealed outcomes.
Initial current/preview works show one executed action conditional on execution.
A purchase observes the next decision (stop or one action), with failures and stop
erased together in the artifact view. Per-work purposes remain independent given
the persistent maker. This is exact within the fitted approximate mark process,
not the actual constructor's full historical process or an unknown true utility.
Affordance is the fitted current-purpose utility of visible operation types; it
is not an independently measured useful-technique outcome for S01.
The separate familiarity entry operation uses equal prior mass on a shared maker
and independently drawn current/archive makers. Purchases update both that link
and each maker; information entropy refers to this joint hypothesis. Independently
drawn fitted components may coincide and are not literal historical identity.
"""
import math
import random

from .artifact_view import action_id,support,validate_work
from .erased_inference import artifact_work
from .familiarity_reader import first_action_likelihood
from .information_selection import acquisition,entropy
from .mark_program import policy,success_probabilities,validate as validate_program
from .program_inference import distribution,identity,log_probability,logsumexp,normalize_logs,predictive_mixture

STRATEGIES=('anomaly','signature','affordance','random','full_scan','entropy','model_information','future_prediction')


def observation_distribution(program,preview,view,budget):
    validate_work(preview,view);current=artifact_work(preview)
    budget.charge();p=policy(program,current);success=success_probabilities(program,current)
    if view=='process_record':
        result={'stop':p['stop']}
        for a in success:
            result['done|'+a]=p[a]*success[a];result['failed|'+a]=p[a]*(1-success[a])
    else:
        result={'unchanged':p['stop']+math.fsum(p[a]*(1-success[a]) for a in success)}
        result.update({'mark|'+a:p[a]*success[a] for a in success})
    return distribution(result)


def purchased_symbol(preview,purchase,view):
    validate_work(preview,view);validate_work(purchase,view)
    if preview['context']!=purchase['context']:
        raise ValueError('purchase changes the preview context')
    if view=='process_record':
        if (len(preview['events'])!=1 or preview['observed_stop'] is not None
                or purchase['events'][:1]!=preview['events']):
            raise ValueError('purchase changes the observed first action')
        n=len(purchase['events'])
        if n==1 and purchase['observed_stop'] is True:return 'stop'
        if n==2 and purchase['observed_stop'] is None:
            event=purchase['events'][-1];return event['outcome']+'|'+action_id(event)
        raise ValueError('purchase must reveal one next decision or its stop')
    new=set(purchase['marks'])-set(preview['marks'])
    if not set(preview['marks'])<=set(purchase['marks']) or len(new)>1:
        raise ValueError('purchase changes old marks or reveals multiple new actions')
    return 'mark|'+next(iter(new)) if new else 'unchanged'


def forecast(bundle,budget,*,same_prior=None):
    # The ordinary S02 source guarantees a shared maker. T02 must instead infer
    # shared versus independent current/archive makers without seeing that truth.
    if same_prior is not None and (isinstance(same_prior,bool) or not isinstance(same_prior,(int,float))
            or not math.isfinite(same_prior) or not 0<=same_prior<=1):
        raise ValueError('invalid shared-maker prior')
    fields={'view','current','pool','purchases','candidates','prior','shared_groups','strategy','cost_nats','allow_stop','seed'}
    if set(bundle)!=fields:raise ValueError('undeclared acquisition input or hidden outcome')
    view=bundle['view'];current=bundle['current'];pool=bundle['pool'];purchases=bundle['purchases']
    candidates,prior,groups=(bundle[k] for k in ('candidates','prior','shared_groups'))
    strategy,cost,allow_stop=bundle['strategy'],bundle['cost_nats'],bundle['allow_stop']
    if (strategy not in STRATEGIES or type(allow_stop) is not bool or type(bundle['seed']) is not int
            or isinstance(cost,bool) or not isinstance(cost,(int,float)) or not math.isfinite(cost) or cost<0):
        raise ValueError('invalid selection strategy, seed or observation cost')
    if allow_stop and strategy not in ('entropy','model_information','future_prediction'):
        raise ValueError('costed stopping requires a commensurate information criterion')
    if (not isinstance(pool,dict) or not 1<=len(pool)<=7 or not isinstance(purchases,dict)
            or set(purchases)-set(pool) or not candidates or len(candidates)>64):
        raise ValueError('invalid permitted preview pool or purchased subset')
    validate_work(current,view);distribution(prior,candidates)
    for p in candidates.values():validate_program(p)
    if set(groups)!=set(candidates) or any(not isinstance(g,str) or not g for g in groups.values()):
        raise ValueError('incomplete persistent maker grouping')
    members={g:[c for c in candidates if groups[c]==g] for g in sorted(set(groups.values()))}
    masses={g:math.fsum(prior[c] for c in cs) for g,cs in members.items()}
    if any(m<=0 for m in masses.values()):raise ValueError('zero-mass maker group')
    conditional={c:log_probability(prior[c]/masses[groups[c]]) for c in candidates}
    current_logs={c:first_action_likelihood(p,current,view,budget) for c,p in candidates.items()}
    current_group={g:logsumexp([conditional[c]+current_logs[c] for c in cs]) for g,cs in members.items()}
    target_only,_=normalize_logs({g:log_probability(masses[g])+current_group[g] for g in members})
    def purpose_posterior(g,logs):
        values={c:conditional[c]+logs[c] for c in members[g]}
        # A group contradicted by this work later has zero persistent mass. Its
        # undefined within-group conditional can use its prior without affecting
        # any observable marginal; it must not invalidate compatible groups.
        return ({c:prior[c]/masses[g] for c in members[g]} if logsumexp(list(values.values()))==-math.inf
                else normalize_logs(values)[0])
    target_purpose={g:purpose_posterior(g,current_logs) for g in members}
    target_predictions={}
    for c,p in candidates.items():budget.charge();target_predictions[c]=policy(p,artifact_work(current))
    target_by_group={g:predictive_mixture(target_purpose[g],{c:target_predictions[c] for c in cs}) for g,cs in members.items()}
    current_only_prediction=predictive_mixture(target_only,target_by_group)
    ids={name:identity(validate_work(w,view)) for name,w in pool.items()}
    canonical={};aliases={}
    for name in sorted(pool,key=lambda n:(ids[n],n)):
        if ids[name] in canonical:aliases[name]=canonical[ids[name]]
        else:canonical[ids[name]]=name
    # Exact repeats do not become fresh likelihood factors. Only a canonical
    # representative can be bought, so aliases cannot buy a second hidden outcome.
    if set(purchases)&set(aliases):raise ValueError('duplicate preview alias cannot supply another purchase')
    joint={g:log_probability(masses[g])+current_group[g] for g in members}
    archive_logs={g:0. for g in members}
    offers={};preview_receipts={}
    for name in canonical.values():
        preview=pool[name]
        likelihoods={c:first_action_likelihood(p,preview,view,budget) for c,p in candidates.items()}
        marginal={g:logsumexp([conditional[c]+likelihoods[c] for c in cs]) for g,cs in members.items()}
        within={g:purpose_posterior(g,likelihoods) for g in members}
        kernels={c:observation_distribution(p,preview,view,budget) for c,p in candidates.items()}
        observed={g:predictive_mixture(within[g],{c:kernels[c] for c in cs}) for g,cs in members.items()}
        for g in joint:
            joint[g]+=marginal[g];archive_logs[g]+=marginal[g]
        if name in purchases:
            symbol=purchased_symbol(preview,purchases[name],view)
            if any(symbol not in p for p in observed.values()):raise ValueError('purchase outside offered support')
            for g in joint:
                joint[g]+=log_probability(observed[g][symbol])
                archive_logs[g]+=log_probability(observed[g][symbol])
        else:offers[name]=observed
        # Entry cues are fixed from current-work information before observing
        # the archive previews; they do not score a preview after fitting to it.
        conditioned=logsumexp([log_probability(target_only[g])+marginal[g] for g in members])
        population=logsumexp([log_probability(masses[g])+marginal[g] for g in members])
        kinds=[a.split(':')[0] for a in preview['marks']]
        affordance=math.fsum(target_only[g]*target_purpose[g][c]*
            math.fsum(candidates[c]['purpose'][k] for k in kinds)/len(kinds)
            for g,cs in members.items() for c in cs) if kinds else 0.
        preview_receipts[name]={'anomaly':-conditioned,'signature':conditioned-population,
                                'affordance':affordance,'content_id':ids[name]}
    states=None
    if same_prior is not None:
        states={};linked_joint={};linked_future={}
        for current_g in members:
            if same_prior>0:
                h=identity(['same',current_g]);states[h]=('same',current_g,current_g)
                linked_joint[h]=log_probability(same_prior)+joint[current_g]
            if same_prior<1:
                for archive_g in members:
                    h=identity(['independent',current_g,archive_g])
                    states[h]=('different',current_g,archive_g)
                    linked_joint[h]=(log_probability(1-same_prior)+log_probability(masses[current_g])
                        +current_group[current_g]+log_probability(masses[archive_g])+archive_logs[archive_g])
        # Within the independent branch, two draws may select the same fitted
        # group; equality of coarse components is not actual maker identity.
        linked_future={h:target_by_group[c] for h,(_,c,_) in states.items()}
        offers={n:{h:p[a] for h,(_,_,a) in states.items()} for n,p in offers.items()}
        joint=linked_joint;target_by_group=linked_future
    weights,_=normalize_logs(joint)
    future=predictive_mixture(weights,target_by_group)
    calculations={}
    for name,likelihoods in offers.items():
        value=acquisition(weights,likelihoods,target_by_group,budget,
            conditional_independence='observation_and_future_given_hypothesis')
        calculations[name]={k:value[k] for k in ('observation_entropy_nats','expected_model_information_nats','expected_future_log_gain_nats')}
        # Algebraic identity cases have exactly zero information. Avoid turning
        # roundoff in repeated mixtures into a positive zero-cost buying signal.
        if all(p==next(iter(likelihoods.values())) for p in likelihoods.values()):
            calculations[name]['expected_model_information_nats']=0.
            calculations[name]['expected_future_log_gain_nats']=0.
        if all(p==next(iter(target_by_group.values())) for p in target_by_group.values()):
            calculations[name]['expected_future_log_gain_nats']=0.
        if same_prior==0:
            calculations[name]['expected_future_log_gain_nats']=0.
    field={'entropy':'observation_entropy_nats','model_information':'expected_model_information_nats',
           'future_prediction':'expected_future_log_gain_nats'}.get(strategy)
    ordered=sorted(offers,key=lambda n:ids[n]);scores={};selected=None
    if ordered:
        if strategy=='random':selected=random.Random(bundle['seed']).choice(ordered)
        elif strategy=='full_scan':selected=ordered[0]
        else:
            scores={n:calculations[n][field]-cost if field else preview_receipts[n][strategy] for n in ordered}
            selected=min(ordered,key=lambda n:(-scores[n],ids[n]))
            if allow_stop and scores[selected]<=0:selected=None
    result={'prediction':future,'persistent_weights':weights,'model_entropy_nats':entropy(weights),
        'selected':selected,'selected_content_id':ids[selected] if selected is not None else None,
        'stop':selected is None,'strategy':strategy,'scores':scores,'calculations':calculations,
        'entry_cues':preview_receipts,'duplicate_aliases':aliases,'unique_previews':len(canonical),
        'purchased_observations':len(purchases),'cost_nats_per_purchase':cost,
        'preview_cost_scope':'all offered previews already observed and counted equally in every route',
        'evaluations_used':budget.used,'information_sha256':identity(bundle),'exact_within_declared_model':True,
        'scope':'next-observation selection before purchase; fitted approximate process with per-work purpose'}
    if states is not None:
        result.update(recognition={r:math.fsum(weights[h] for h,s in states.items() if s[0]==r)
                                   for r in ('same','different')},
            current_maker_weights={g:math.fsum(weights[h] for h,s in states.items() if s[1]==g) for g in members},
            archive_maker_weights={g:math.fsum(weights[h] for h,s in states.items() if s[2]==g) for g in members},
            same_maker_prior=same_prior,entropy_model='relationship_and_current_archive_maker',
            current_only_prediction=current_only_prediction,
            scope='shared versus independent maker selection; fitted approximate process with per-work purpose')
    return result


def familiarity_forecast(bundle,budget):
    """T02 uses a fixed equal shared/independent prior, never the source label."""
    return forecast(bundle,budget,same_prior=.5)
