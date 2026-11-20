"""LD1 diagnostic comparisons and support-first LD2 role analysis.

DESIGN CHECK: LESSONS 3-5. The role check counts criticism and leadership
before calling an outcome loader. Both support and coding must pass. A zero
contrast, either sign, and a failed/singular fit remain distinct. Exact source,
row order, all six events and all four feelings are required. Known-answer
reference fits, whole-person replication and role reversal check the contrast.
No source is opened here and no scientific verdict is issued.
"""
from dataclasses import dataclass
import hashlib
import json
import re

import numpy as np

from . import week6_lattice_bindings_v1 as binding
from .week6_lattice_diary_v1 import InvalidFit, logit_fit, within

SCORED_ROLES = (1, 2, 3, 5, 6, 7, 9)
OUTCOMES = ('angry', *binding.FEAR_LIKE)


def context_diagnostic(people, comparison, failure, outcomes, weight=None):
    """Apply LD1's unchanged model to an explicitly bound binary comparison.

    Caller binds 1=comparison and 0=reference prospectively from the codebook.
    This helper does not guess communication or partner-count codes.
    """
    original = binding.ld1(people, comparison, failure, outcomes, weight)
    return dict(
        contrast=original['primary'], form_l=original['form_l'],
        feelings={name: dict(coefficients=row['coefficients'],
                            reference=row['alone'], comparison=row['company'],
                            ratio=row['ratio'])
                  for name, row in original['feelings'].items()},
        descriptive_only=True, limit=original['limit'])


@dataclass(frozen=True)
class RoleGate:
    source_sha256: str
    row_keys: tuple
    people: np.ndarray
    partner_count: np.ndarray
    role: np.ndarray
    criticised: np.ndarray
    leadership: np.ndarray
    binding_sha256: str

    def support(self):
        return binding.role_support(self.people, self.partner_count, self.role,
                                    self.criticised, self.leadership)


def review_role_metadata(source_sha256, row_keys, people, partner_count, role,
                         criticised, leadership):
    """Freeze outcome-free metadata; only positive integral role/count codes."""
    if not isinstance(source_sha256, str) or not re.fullmatch('[0-9a-f]{64}', source_sha256):
        raise InvalidFit('Exact source SHA256 required')
    ids, arrays = binding.aligned(people, partner_count, role, criticised, leadership)
    if any(a.ndim != 1 for a in arrays):
        raise InvalidFit('One metadata value per row required')
    keys = tuple(row_keys)
    if len(keys) != len(ids) or any(not isinstance(k, str) or not k for k in keys) or len(set(keys)) != len(keys):
        raise InvalidFit('Unique ordered row keys required')
    for a in arrays[:2]:
        if np.any(a < 1) or np.any(a != np.floor(a)):
            raise InvalidFit('Positive integral partner count and role codes required')
    # Own copies: the caller cannot change the reviewed arrays through an alias.
    frozen = [np.array(a, copy=True) for a in (ids, *arrays)]
    for a in frozen:
        a.setflags(write=False)
    manifest = dict(source_sha256=source_sha256, row_keys=keys,
                    metadata=[a.tolist() for a in frozen])
    pin = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()
    return RoleGate(source_sha256, keys, *frozen, pin)


def role_fit(people, role, events, outcomes, weight=None):
    """Pooled Form O with role-specific criticism slopes and peer reference.

    All six events and their person means enter jointly. The supplied role
    fixture's two criticism products and role indicators remain explicit.
    The caller has already applied the observed support/coding gate; bootstrap
    draws refit this function without selecting draws by support or direction.
    """
    ids, (roles,) = binding.aligned(people, role)
    if roles.ndim != 1 or not np.isin(roles, SCORED_ROLES).all():
        raise InvalidFit('Only the declared single-partner role groups may be modelled')
    x = binding.named_matrix(events, binding.STATUS, len(ids))
    if set(outcomes) != set(OUTCOMES):
        raise InvalidFit('Angry and all three fear-like feelings are required')
    z, means, _ = within(x, ids, weight)
    below = np.isin(roles, (2, 7)).astype(float)
    above = (roles == 1).astype(float)
    ci = binding.STATUS.index('criticised')
    X = np.column_stack((np.ones(len(ids)), z, z[:, ci] * below,
                         z[:, ci] * above, below, above, means))
    b_index, a_index = 7, 8
    fits, table = {}, {}
    for name in OUTCOMES:
        _, (y,) = binding.aligned(ids, outcomes[name])
        if y.ndim != 1:
            raise InvalidFit('One feeling rating per row required')
        fit = logit_fit(X, y > 1, weight)
        fits[name] = fit
        table[name] = {}
        for group, offset in (('peers', 0.), ('below', fit[b_index]), ('above', fit[a_index])):
            slopes = fit[1:7].copy()
            slopes[ci] += offset
            table[name][group] = dict(zip(binding.STATUS, map(float, slopes)))
    gaps = {group: table['angry'][group]['criticised'] -
            float(np.mean([table[k][group]['criticised'] for k in binding.FEAR_LIKE]))
            for group in ('peers', 'below', 'above')}
    return dict(primary=float(gaps['below'] - gaps['above']), bar=.40,
                coefficients=fits, table=table, anger_minus_fear=gaps,
                column_names=['intercept', *binding.STATUS, 'criticised_x_below',
                              'criticised_x_above', 'below', 'above',
                              *['mean_' + k for k in binding.STATUS]],
                limit='Role is rank in one relationship; conduct and feeling share one prompt.')


def analyse_roles(gate, load_outcomes):
    """Read feelings only after metadata passes; authenticate the second read.

    The loader returns source_sha256, ordered row_keys, events and outcomes.
    Real adapters must authenticate the same original source before and after
    each projection. This API alone is not permission to open participant data.
    """
    # Rebuild the metadata pin, detecting even deliberate write-enable mutation.
    checked = review_role_metadata(gate.source_sha256, gate.row_keys, gate.people,
                                  gate.partner_count, gate.role, gate.criticised,
                                  gate.leadership)
    if checked.binding_sha256 != gate.binding_sha256:
        raise InvalidFit('Reviewed metadata changed')
    support = gate.support()
    result = dict(support=support, binding_sha256=gate.binding_sha256,
                  outcomes_read=False, descriptive_only=True)
    if not support['support_passes']:
        return dict(result, disposition='unsupported')
    if not support['coding_passes']:
        return dict(result, disposition='role_codes_do_not_carry_rank')
    payload = load_outcomes()
    result['outcomes_read'] = True
    if payload.get('source_sha256') != gate.source_sha256 or tuple(payload.get('row_keys', ())) != gate.row_keys:
        raise InvalidFit('Outcome source or row order differs from reviewed metadata')
    if set(payload['events']) != set(binding.STATUS) or set(payload['outcomes']) != set(OUTCOMES):
        raise InvalidFit('All declared events and feelings must be present')
    events = {k: np.asarray(payload['events'][k], float) for k in binding.STATUS}
    outcomes = {k: np.asarray(payload['outcomes'][k], float) for k in OUTCOMES}
    arrays = [*events.values(), *outcomes.values()]
    if any(a.shape != (len(gate.people),) or np.isinf(a).any() for a in arrays):
        raise InvalidFit('Aligned ratings required; infinities are not missing records')
    if not np.array_equal(events['criticised'], gate.criticised):
        raise InvalidFit('Criticism differs between support and outcome projections')
    eligible = (gate.partner_count == 1) & np.isin(gate.role, SCORED_ROLES)
    complete = np.all(np.isfinite(np.column_stack(arrays)), axis=1)
    keep = eligible & complete
    result['counts'] = dict(metadata_rows=len(gate.people), eligible_rows=int(eligible.sum()),
                            missing_model_rows=int((eligible & ~complete).sum()),
                            model_rows=int(keep.sum()), model_people=int(len(np.unique(gate.people[keep]))))
    if not keep.any():
        return dict(result, disposition='unsupported_after_complete_cases')
    after = binding.role_support(gate.people[keep], gate.partner_count[keep], gate.role[keep],
                                 gate.criticised[keep], gate.leadership[keep])
    result['support_after_complete_cases'] = after
    if not after['support_passes']:
        return dict(result, disposition='unsupported_after_complete_cases')
    if not after['coding_passes']:
        return dict(result, disposition='role_codes_do_not_carry_rank_after_complete_cases')
    result['fit'] = role_fit(gate.people[keep], gate.role[keep],
                             {k: v[keep] for k, v in events.items()},
                             {k: v[keep] for k, v in outcomes.items()})
    return dict(result, disposition='point_fit_only', descriptive_only=False)
