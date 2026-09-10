"""Reader-side reuse of identical program/work evaluations across matched contrasts.

DESIGN CHECK: M01/M04/X05/X06; LESSONS 3--5. NULL: a repeated observation,
changed future, or a cached query from another view cannot add evidence. ALTERNATIVE:
each dose and hierarchy equals fresh standalone inference at the same seed/budget
envelope, while actual transitions are evaluated once per distinct program/work.
Bands: exact identity and complete support, or refusal; approximation stays explicit.
This object is invocation-local. It never reads evaluator files or accepts targets.
"""
import copy
import math

from .artifact_view import validate, validate_work
from .erased_inference import artifact_likelihood, artifact_work, process_likelihood
from .mark_program import policy, validate as validate_program
from .program_inference import (distribution, identity, log_probability, logsumexp,
                                normalize_logs, predictive_mixture)


class Table:
    def __init__(self, candidates, budget, *, exact_limit=8, permutations=16, seed=0):
        if not candidates or len(candidates)>64:
            raise ValueError('invalid candidate envelope')
        for program in candidates.values():
            validate_program(program)
        self.candidates = copy.deepcopy(candidates)
        self.budget = budget
        self.exact_limit, self.permutations, self.seed = exact_limit, permutations, seed
        self._likelihoods, self._forecasts = {}, {}
        self.cache_hits = 0

    def likelihood(self, cid, work, view):
        validate_work(work,view)
        key = (cid,view,identity(work))
        if key not in self._likelihoods:
            program = self.candidates[cid]
            self._likelihoods[key] = (process_likelihood(program,work,self.budget) if view=='process_record' else
                artifact_likelihood(program,work,self.budget,exact_limit=self.exact_limit,
                    permutations=self.permutations,seed=str(self.seed)+':'+identity(work)))
        else:
            self.cache_hits += 1
        return copy.deepcopy(self._likelihoods[key])

    def forecast(self, evidence, prior, *, shared_groups=None, current_purpose_weights=None):
        validate(evidence)
        distribution(prior,self.candidates)
        before = self.budget.used
        unique = {}
        current_key = identity(evidence['current'])
        for work in evidence['earlier']:
            key = identity(work)
            if key != current_key:
                unique.setdefault(key,work)
        works = [*unique.values(),evidence['current']]
        rows, forecasts = {}, {}
        for cid,program in self.candidates.items():
            rows[cid] = [self.likelihood(cid,w,evidence['view']) for w in works]
            state = artifact_work(evidence['current'])
            fkey = (cid,identity(state))
            if fkey not in self._forecasts:
                self.budget.charge()
                self._forecasts[fkey] = policy(program,state)
            forecasts[cid] = self._forecasts[fkey]
        posterior_groups = None
        if shared_groups is None:
            if current_purpose_weights is not None:
                raise ValueError('current purpose conditioning requires the per-work hierarchy')
            logs = {c:log_probability(prior[c])+math.fsum(r['log_mass'] for r in rows[c]) for c in rows}
        else:
            if set(shared_groups)!=set(self.candidates) or any(not isinstance(g,str) or not g for g in shared_groups.values()):
                raise ValueError('incomplete persistent grouping')
            groups = sorted(set(shared_groups.values()))
            members = {g:[c for c in rows if shared_groups[c]==g] for g in groups}
            masses = {g:math.fsum(prior[c] for c in members[g]) for g in groups}
            if any(m<=0 for m in masses.values()):
                raise ValueError('each maker group needs positive mass')
            conditional = {c:log_probability(prior[c]/masses[shared_groups[c]]) for c in rows}
            past = {g:log_probability(masses[g])+math.fsum(
                logsumexp([conditional[c]+rows[c][j]['log_mass'] for c in members[g]])
                for j in range(len(works)-1)) for g in groups}
            current = conditional
            if current_purpose_weights is not None:
                # Explicit diagnostic changes ONLY current-work purpose support.
                # It cannot retrospectively assert that every earlier work shared it.
                if set(current_purpose_weights)!=set(rows):
                    raise ValueError('incomplete current-purpose weights')
                for g in groups:
                    distribution({c:current_purpose_weights[c] for c in members[g]})
                current = {c:log_probability(current_purpose_weights[c]) for c in rows}
            logs = {c:past[shared_groups[c]]+current[c]+rows[c][-1]['log_mass'] for c in rows}
        weights,mass = normalize_logs(logs)
        if shared_groups is not None:
            posterior_groups = {g:math.fsum(weights[c] for c in members[g]) for g in groups}
        return {'prediction':predictive_mixture(weights,forecasts),'weights':weights,
            'persistent_weights':posterior_groups,'log_evidence':mass,'likelihood_receipts':rows,
            'distinct_earlier_works':len(unique),'duplicate_earlier_works_removed':len(evidence['earlier'])-len(unique),
            'new_evaluations':self.budget.used-before,'evaluations_used':self.budget.used,
            'exact_within_declared_model':all(r['exact'] for values in rows.values() for r in values),
            'current_purpose_assistance':current_purpose_weights is not None}


def approximation_comparison(first, second, *, maximum_tv=.01, maximum_log_difference=.01):
    """Declared apparatus envelope; independent seeds are supplied by the caller.

    Agreement is a reproducibility condition, not proof against a shared bias.
    The exact-small-case accuracy fixtures remain a separate prerequisite.
    """
    a,b = first['prediction'],second['prediction']
    distribution(a); distribution(b,a)
    if not 0 < maximum_tv < 1 or not 0 < maximum_log_difference < 1:
        raise ValueError('invalid predeclared approximation envelope')
    tv = .5*math.fsum(abs(a[k]-b[k]) for k in a)
    differences = [abs(math.log(a[k])-math.log(b[k])) if a[k]>0 and b[k]>0 else
                   (0. if a[k]==b[k] else math.inf) for k in a]
    largest = max(differences)
    return {'accepted':tv<=maximum_tv and largest<=maximum_log_difference,
            'total_variation':tv,'maximum_option_log_difference':largest,
            'maximum_tv':maximum_tv,'maximum_log_difference':maximum_log_difference,
            'meaning':'agreement of independently seeded approximations; shared bias not ruled out'}
