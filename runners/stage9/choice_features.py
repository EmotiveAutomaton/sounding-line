"""Sparse conditional-action features from validated visible artifacts only.

DESIGN CHECK: M01/C08/X02/X03/X05; LESSONS 3--5. NULL: hidden labels and
source IDs cannot affect features; same visible marks give identical artifact
features regardless of route. ALTERNATIVE: context, progress and permitted records
can change different action probabilities. Topic and cheap surface rivals remain
separate comparators. No external legality mask is learned competence.
"""
import math

from .artifact_view import TYPES, action_id, all_header_actions, type_counts, validate
from .program_inference import distribution, identity


def unique_earlier(evidence):
    unique = {}
    for work in evidence['earlier']:
        unique.setdefault(identity(work), work)
    return list(unique.values())


def action_features(evidence, action, individual=False):
    validate(evidence)
    if action not in evidence['support']:
        raise ValueError('action outside declared complete support')
    current, view = evidence['current'], evidence['view']
    context = current['context']
    section_names = [s['name'] for s in context['sections']]
    all_actions = all_header_actions(context)
    kind = 'stop' if action == 'stop' else all_actions[action]['type']
    counts = type_counts(current)
    total = len(current['marks'])
    global_features = {'bias': 1., 'mark_count': total/32, 'mark_fraction': total/max(1, len(all_actions)),
                       'section_count': len(section_names)/8,
                       'deadline_tight': float(context['deadline'] == 'tight'),
                       'audience:'+context['audience']: 1.,
                       **{'tool:'+k: float(v) for k, v in context['tools'].items()},
                       **{'current:'+k: counts[k]/max(1, total) for k in TYPES}}
    if view == 'process_record':
        events = current['events']
        previous = events[-1] if events else None
        global_features.update({'record_present': 1., 'attempt_count': len(events)/32,
                                'failed_count': sum(e['outcome'] == 'failed' for e in events)/16,
                                'previous:'+ (previous['type'] if previous else 'none'): 1.})
    else:
        previous = None
    if individual:
        earlier = unique_earlier(evidence)
        global_features['earlier_count'] = len(earlier)/7
        # Equal work weights, then equal type frequencies. A long work is not a
        # new maker and duplicated content does not increase this dose.
        for other_type in TYPES:
            global_features['history:'+other_type] = (math.fsum(
                type_counts(work)[other_type]/max(1, len(work['marks'])) for work in earlier)/len(earlier)
                if earlier else 0.)
    features = {kind+'|'+key: value for key, value in global_features.items()}
    if kind != 'stop':
        candidate = all_actions[action]
        section = candidate['section']
        same_section = [m for m in current['marks'] if m.split(':')[1] == section]
        slot = candidate['slot']
        matching_slot = {m.split(':')[0] for m in same_section if m.split(':')[2] == slot}
        features.update({kind+'|section_position': section_names.index(section)/max(1, len(section_names)-1),
                         kind+'|section_mark_count': len(same_section)/16,
                         **{kind+'|slot_has:'+t: float(t in matching_slot) for t in TYPES}})
        if previous:
            features[kind+'|same_previous_section'] = float(previous['section'] == section)
            features[kind+'|same_previous_slot'] = float(previous['section'] == section and previous['slot'] == slot)
    return features


def predict(evidence, parameters, offsets=None):
    if set(parameters) != {'version', 'weights', 'individual', 'uniform_mixture'} or parameters['version'] != 's9-conditional-choice-v1':
        raise ValueError('invalid conditional-choice parameters')
    if type(parameters['individual']) is not bool or any(not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v)
                                                       for v in parameters['weights'].values()):
        raise ValueError('invalid conditional-choice weights')
    epsilon = parameters['uniform_mixture']
    if not isinstance(epsilon, (int, float)) or isinstance(epsilon, bool) or not math.isfinite(epsilon) or not 0 <= epsilon < 1:
        raise ValueError('invalid declared forecast mixture')
    validate(evidence)
    offsets = offsets or {}
    if not set(offsets) <= set(TYPES) | {'stop'} or any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in offsets.values()):
        raise ValueError('invalid individual type adjustment')
    logits = {}
    for action in evidence['support']:
        features = action_features(evidence, action, parameters['individual'])
        logits[action] = math.fsum(value*parameters['weights'].get(key, 0.) for key, value in features.items())
        logits[action] += offsets.get(action.split(':')[0], 0.)
    peak = max(logits.values())
    weights = {a: math.exp(v-peak) for a, v in logits.items()}
    total = math.fsum(weights.values())
    return distribution({a: (1-epsilon)*w/total+epsilon/len(weights) for a, w in weights.items()})


def cheap_adaptation(evidence, population_types, strength=16.):
    """Smoothed bag-of-completed-types rival; no historical ordering inference.

    The population type reference and pseudocount strength are training/development
    artifacts. This is a heuristic frequency correction, not a maker posterior.
    """
    validate(evidence)
    distribution(population_types, TYPES)
    if any(p <= 0 for p in population_types.values()) or not math.isfinite(strength) or strength <= 0:
        raise ValueError('positive type reference and adaptation strength required')
    counts = {t: 0. for t in TYPES}
    for work in unique_earlier(evidence):
        c = type_counts(work)
        # Each work contributes one fixed mass, so work length does not invent dose.
        total = sum(c.values())
        if total:
            for t in TYPES:
                counts[t] += 8*c[t]/total
    total = sum(counts.values())
    return {t: math.log((strength*population_types[t]+counts[t])/(strength+total)/population_types[t]) for t in TYPES}
