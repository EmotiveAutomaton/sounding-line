"""Pre-outcome secondary diagnostics; original forecasts remain the primary.

DESIGN CHECK: LESSONS3-5 and READER_HEURISTICS4/10. The four-action projection
has fixed .85/.05 confidence, independent of outcomes. Invalid attempts stay
invalid. Rule-collapse equality is a readout identity, not a reasoning ablation.
"""
from collections import Counter
from copy import deepcopy
from . import human_programs
from .contracts import canonical,parse_forecast

DEFINITION={'schema':'gear3.readouts.1','human_same_confidence':{'chosen':.85,'other':.05},
            'human_rule_mixture':'q(a)=0.05+0.80*f(a); fixed total lapse 0.15',
            'tie_rule':'fractional credit across all maximum-probability options',
            'role':'secondary, fixed before joined outcomes; original predictions remain primary'}


def same_confidence(task,status,forecast):
    if len(task.choices)!=4 or task.family!='coauthor-handling':
        raise ValueError('same-confidence readout is human four-class only')
    if status!='VALID':
        if forecast is not None:raise ValueError('invalid forecast substituted')
        return None
    original=parse_forecast(canonical(forecast),task)
    result=deepcopy(original)
    result['probabilities']={k:.85 if k==original['choice'] else .05 for k,_ in task.choices}
    return result


def human_diagnostic(task,candidates,forecast):
    executed=human_programs.evaluate(task,candidates)
    actions=[r['action'] for r in executed['executed'].values()];counts=Counter(actions)
    by_description={v:k for k,v in task.choices}
    formula={by_description[human_programs.DESCRIPTIONS[a]]:.05+.8*counts[a]/len(actions) for a in human_programs.ACTIONS}
    if any(abs(formula[k]-executed['probabilities'][k])>1e-12 for k in formula):
        raise ValueError('human rule-mixture identity failed')
    # Each conditional can be collapsed to the same realized constant vote on
    # this one task. This says nothing about the proposer's evidence processing.
    for candidate,action in zip(candidates,actions):
        constant={'feature':'constant','threshold':1,'below':action,'otherwise':action}
        if human_programs.execute(constant,executed['features'])!=human_programs.execute(candidate['program'],executed['features']):
            raise ValueError('single-task constant-collapse identity failed')
    maxima=[k for k,v in formula.items() if abs(v-max(formula.values()))<1e-12]
    return {'rule_count':len(actions),'vote_counts':dict(counts),'vote_concentration':max(counts.values())/len(actions),
            'constant_rule_share':sum(c['program']['feature']=='constant' or c['program']['below']==c['program']['otherwise'] for c in candidates)/len(actions),
            'generated_choice_in_mixture_argmax':forecast['choice'] in maxima if forecast else None,
            'mixture_argmax_options':maxima,'constant_collapse_identical':True,
            'scope':'single-task handling heuristic; proposer inference may affect its rule votes'}
