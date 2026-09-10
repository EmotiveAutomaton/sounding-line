"""Bounded numerical synthesis from permitted artifacts and a declared library.

DESIGN CHECK: M02/X02/X06; LESSONS 3--5. NULL: no hidden inputs or duplicate
candidate multiplicity; an unknown proposal density never earns exact-posterior
language. ALTERNATIVE: observed unsupported operation types can open a candidate
whose executable support contains them. This is a heuristic proposal operation,
not an LLM call, an exact importance sampler, or an inferred true mental state.
"""
import copy
import math

from .artifact_view import TYPES, type_counts, validate
from .choice_features import unique_earlier
from .erased_inference import artifact_work
from .mark_program import policy, requirements, validate as validate_program
from .program_inference import identity, log_probability


def propose(evidence, library, budget, *, maximum=16, expand=False):
    validate(evidence)
    if type(maximum) is not int or not 1 <= maximum <= 64 or not library or len(library) > 64:
        raise ValueError('invalid numerical proposal envelope')
    if type(expand) is not bool or expand and maximum < 2:
        raise ValueError('expanded proposals require space for old and new candidates')
    original = {}
    for program in library:
        validate_program(program)
        original.setdefault(identity(program), copy.deepcopy(program))
    current = evidence['current']
    earlier = unique_earlier(evidence)
    all_works = [*earlier, current]
    scores = {}
    for key, program in original.items():
        score = 0.
        for work in all_works:
            budget.charge()
            forecast = policy(program, artifact_work(work, []))
            # Ranking surrogate only. The actual evaluator subsequently sums
            # stateful histories; this bag score is never its likelihood.
            if work['marks']:
                score += math.fsum(log_probability(forecast[a]) for a in work['marks'])/len(work['marks'])
        scores[key] = score
    ranked = sorted(original, key=lambda key: (-scores[key], key))
    candidates = dict(original)
    origins = {key: 'fixed_library' for key in candidates}
    if expand:
        current_counts = type_counts(current)
        earlier_counts = {t: math.fsum(type_counts(w)[t]/max(1, len(w['marks'])) for w in earlier) for t in TYPES}
        used_types = set(current_counts) | {t for t in TYPES if earlier_counts[t] > 0}
        for key in ranked[:max(1, maximum//2)]:
            budget.charge()  # each constructed proposal is an actual operation
            updated = copy.deepcopy(original[key])
            updated['available_types'] = sorted(set(updated['available_types']) | used_types)
            current_total = len(current['marks']) + len(TYPES)
            earlier_total = math.fsum(earlier_counts.values()) + len(TYPES)
            for t in TYPES:
                updated['purpose'][t] += math.log(len(TYPES)*(current_counts[t]+1)/current_total)
                updated['history'][t] += math.log(len(TYPES)*(earlier_counts[t]+1)/earlier_total)
            for t in used_types:
                for tool in requirements(t):
                    updated['context'][tool] = 'available'
            validate_program(updated)
            proposed_id = identity(updated)
            candidates.setdefault(proposed_id, updated)
            origins.setdefault(proposed_id, 'artifact_adapted_numeric_proposal')
        # Reserve half the finite width for new proposals where they exist; do not
        # silently lose all expanded hypotheses to the initial ranking surrogate.
        added = sorted(set(candidates)-set(original))
        take_added = added[:maximum//2]
        retained = ranked[:maximum-len(take_added)] + take_added
    else:
        retained = ranked[:maximum]
    selected = {key: candidates[key] for key in retained}
    fixed_complete = not expand and len(selected) == len(original)
    return {'candidates': selected, 'prior': {key: 1/len(selected) for key in selected},
            'origins': {key: origins[key] for key in selected}, 'library_sha256': identity(library),
            'distinct_library_candidates': len(original), 'selected_candidates': len(selected),
            'proposal_evaluations_used': budget.used, 'fixed_complete_catalogue': fixed_complete,
            'proposal_density_known': False, 'language_model_calls': 0,
            'meaning': ('uniform fixed finite library prior' if fixed_complete else
                        'data-dependent candidate search with uniform finite evaluation weights; no exact global posterior')}
