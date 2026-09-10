"""Actual sequential evidence purchases and pre-purchase predictions.

DESIGN CHECK: S02/S03/S04/X01/X02/X05/X06/X08/X11; LESSONS 3--5, CONTROLS 6--7.
NULL: hidden unbought outcomes cannot select an observation; duplicates cannot buy
confidence. ALTERNATIVE: different permitted entry rules change predictive quality
at equal budgets. Every path retains all steps and invalid calls; failed readers
never inherit a valid prior. All routes pay for the same seven initial previews.
Full-view means all unique purchases exhausted; canonical scan at a smaller
budget is explicitly a coverage baseline. The shared executor also serves the
separately constructed T02 entry cross; no S01 technique or recognition claim.
"""
from pathlib import Path
from . import baseline_matrix_runtime,comparison_runtime
from .artifact_comparisons import checkpoint_call
from .artifact_view import support
from .common import digest,distribution
from .selection_cases import construct
from .selection_reader import STRATEGIES

FIXED_BUDGETS=(0,1,3,7)
STOP_COSTS=(.05,.2)


def forecast_unit(case,package,purpose_groups,directory,*,resume_only=False):
    del purpose_groups
    cf=construct(case)
    if cf!=case['selection']:raise ValueError('selection source or future changed')
    return forecast_case(case,cf,package,directory,resume_only=resume_only)


def forecast_case(case,cf,package,directory,*,resume_only=False,
                  operation='select_observation',fixed_budgets=FIXED_BUDGETS):
    """Shared acquisition executor; caller verifies its source construction first."""
    if operation not in ('select_observation','select_familiar_observation'):
        raise ValueError('undeclared selection operation')
    if (not fixed_budgets or fixed_budgets[0]!=0 or tuple(sorted(set(fixed_budgets)))!=tuple(fixed_budgets)
            or any(type(n) is not int or n<0 for n in fixed_budgets)):
        raise ValueError('explicit ordered observation budgets required')
    directory=Path(directory);rows,costs,traces={},[],{}
    for view in ('artifact','process_record'):
        public=cf['public'][view];queries={}
        if fixed_budgets[-1]!=len(public['pool']):raise ValueError('budget endpoint must cover the whole offered pool')
        paths=[(s,s,False,0.) for s in STRATEGIES]
        paths += [('future-stop-'+str(c),'future_prediction',True,c) for c in STOP_COSTS]
        for path,strategy,allow_stop,cost in paths:
            purchases={};steps=[];failed=False
            for step in range(len(public['pool'])+1):
                # Only the selected prefix of purchases enters this immutable call.
                bundle={**public,**package['library'],'purchases':dict(purchases),'strategy':strategy,
                    'allow_stop':allow_stop,'cost_nats':cost,
                    'seed':int(digest({'selection_random_v1':{'view':view,'current':public['current'],
                        'previews':sorted({digest(w) for w in public['pool'].values()})},
                        'bought':sorted(digest(public['pool'][k]) for k in purchases)})[:12],16)}
                result=checkpoint_call(directory/'calls'/(digest(bundle)+'.json'),bundle,
                    lambda:comparison_runtime.execute(bundle,operation=operation,budget=800000,
                        root=directory/'caps-selection'),resume_only=resume_only)
                costs.append({'operation':operation,'view':view,'path':path,'step':step,
                    'accepted':result['accepted'],'wall_seconds':result['wall_s'],'capsule':result['capsule']})
                accepted=result['accepted'] and result['prediction'].get('exact_within_declared_model') is True
                if accepted and result['prediction'].get('operation')!=operation:
                    raise ValueError('saved selection call uses another operation')
                output=result['prediction'] if accepted else None
                observed={**public,'purchases':dict(purchases)}
                trace={'step':step,'accepted':accepted,'input_sha256':digest(bundle),'observations_sha256':digest(observed),
                    'purchased':sorted(purchases),'output':output,'capsule':result['capsule']}
                steps.append(trace)
                if not accepted:failed=True;break
                if output['purchased_observations']!=len(purchases):raise ValueError('reader purchase cost mismatch')
                if output['stop']:break
                chosen=output['selected']
                if chosen not in public['pool'] or chosen in purchases:raise ValueError('reader selects unoffered or repeated purchase')
                # The evaluator reveal follows its saved selected decision.
                purchases[chosen]=cf['purchases'][view][chosen]
            else:raise ValueError('reader did not exhaust its bounded observation pool')
            traces[view+'|'+path]={'strategy':strategy,'allow_stop':allow_stop,'cost_nats':cost,
                'valid':not failed,'steps':steps,'preview_cost':len(public['pool']),
                'scope':'fixed shared-maker fitted model; each work has independently marginalized purpose'}
            for label in ('stopped',) if allow_stop else fixed_budgets:
                query=view+'|'+path+'|'+str(label)
                selected=steps[-1] if allow_stop else steps[min(label,len(steps)-1)]
                # A later failure does not erase a completed earlier-budget forecast.
                valid=selected['accepted'] and (allow_stop is False or not failed)
                n=selected['step'];visible_purchases={k:cf['purchases'][view][k] for k in selected['purchased']}
                canonical={}
                for k,w in sorted(public['pool'].items(),key=lambda item:(digest(item[1]),item[0])):
                    canonical.setdefault(digest(w),k)
                earlier=[visible_purchases.get(k,public['pool'][k]) for k in canonical.values()]
                evidence={'version':'s9-visible-artifact-v1','view':view,'current':public['current'],
                    'earlier':earlier,'support':support(public['current'],view)}
                queries[query]=evidence
                rows[query]={'predictions':{'program':selected['output']['prediction']} if valid else {},
                    'validity':{'program':valid},'model_input_sha256':{'program':selected['input_sha256']},
                    'support':evidence['support'],'evidence_sha256':digest(evidence),
                    'unique_prior_works':len({digest(w) for w in earlier}),
                    'preview_cost':len(public['pool']),'purchase_cost':n,'cost_nats':cost,
                    'full_view':valid and selected['output']['stop'] and not allow_stop,
                    'requested_budget':label,'path':path,'view':view}
                if operation=='select_familiar_observation':
                    cell=rows[query];cell['validity']['program_prior']=valid
                    cell['model_input_sha256']['program_prior']=selected['input_sha256']
                    if valid:cell['predictions']['program_prior']=selected['output']['current_only_prediction']
                    cell['recognition']=selected['output']['recognition'] if valid else None
                    traces[view+'|'+path]['scope']='inferred shared/independent current and archive makers; per-work purposes'
        baseline_input={'evidences':queries,'models':package['models'][view],'population_types':package['types'][view]}
        baseline=checkpoint_call(directory/(view+'-baselines.json'),baseline_input,
            lambda:baseline_matrix_runtime.execute(baseline_input,root=directory/'caps-baseline'),resume_only=resume_only)
        costs.append({'operation':'baselines','view':view,'accepted':baseline['accepted'],
            'wall_seconds':baseline['wall_s'],'capsule':baseline['capsule']})
        for query in queries:
            for model in package['models'][view]:
                for route in ('population','brief','cheap-8.0','cheap-16.0','cheap-32.0'):
                    key=model+'|'+route;rows[query]['validity'][key]=baseline['accepted']
                    rows[query]['model_input_sha256'][key]=digest(baseline_input)
                    if baseline['accepted']:rows[query]['predictions'][key]=baseline['prediction']['predictions'][query][key]
            for prediction in rows[query]['predictions'].values():
                distribution(prediction)
                if set(prediction)!=set(rows[query]['support']):raise ValueError('selection forecast support changed')
    # Multiple routes may share the same exact checkpoint; count actual calls once.
    unique={row['capsule']:row for row in costs}
    return {'unit':case['unit'],'role':case['role'],'truth':cf['target'],'rows':rows,'traces':traces,
        'costs':list(unique.values()),'domain':case['private_factors']['domain'],'purpose':case['private_factors']['purpose'],
        'case_sha256':digest(case),'source_template_sha256':cf['source_template_sha256'],
        'scope':'charged common previews; fixed budgets and costed future-gain stopping; no scientific promotion'}
