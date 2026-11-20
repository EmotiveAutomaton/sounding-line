import copy

import numpy as np
import pytest
from scipy.special import expit

from runners.drive.cards import week6_lattice_diagnostics_v1 as d
from runners.drive.cards import week6_lattice_bindings_v1 as b
from runners.drive.cards.week6_lattice_diary_v1 import InvalidFit


def reference_design(ids, roles, events):
    x = np.column_stack([events[k] for k in b.STATUS])
    means = np.empty_like(x)
    for person in np.unique(ids):
        rows = ids == person
        means[rows] = x[rows].mean(axis=0)
    z = x - means
    z /= np.sqrt(np.mean(z * z, axis=0))
    below = np.isin(roles, [2, 7]).astype(float)
    above = (roles == 1).astype(float)
    return np.column_stack([np.ones(len(ids)), z, z[:, 1] * below,
                            z[:, 1] * above, below, above, means])


def fixture():
    rng = np.random.default_rng(20261120)
    ids = np.repeat(np.arange(90), 24)
    roles = np.tile([1, 2, 3], len(ids) // 3)
    x = 3 + rng.normal(0, .25, (90, 6))[ids] + rng.normal(0, .4, (len(ids), 6))
    events = dict(zip(b.STATUS, x.T))
    X = reference_design(ids, roles, events)
    outcomes = {}
    for name in d.OUTCOMES:
        coefficients = np.linspace(.01, .04, X.shape[1])
        coefficients[0] = -.5
        coefficients[7:9] = (.4, -.15) if name == 'angry' else (-.1, .2)
        outcomes[name] = 1 + rng.binomial(1, expit(X @ coefficients))
    keys = [str(k) for k in range(len(ids))]
    lead = np.where(roles == 2, 4.5, np.where(roles == 1, 2.5, 3.5))
    gate = d.review_role_metadata('a' * 64, keys, ids, np.ones(len(ids)), roles,
                                  events['criticised'], lead)
    payload = dict(source_sha256='a' * 64, row_keys=keys, events=events, outcomes=outcomes)
    return gate, payload


def revised_gate(gate, **changes):
    fields = {k: getattr(gate, k) for k in ('source_sha256', 'row_keys', 'people',
              'partner_count', 'role', 'criticised', 'leadership')}
    return d.review_role_metadata(**(fields | changes))


def no_outcomes():
    pytest.fail('Feeling outcomes were requested before the support/coding gate passed')


def test_insufficient_people_never_loads_feelings():
    gate, _ = fixture()
    gate = revised_gate(gate, people=gate.people % 39)
    result = d.analyse_roles(gate, no_outcomes)
    assert result['disposition'] == 'unsupported'
    assert not result['outcomes_read']
    assert result['support']['strata']['above']['people'] == 39


def test_fewer_than_sixty_criticisms_never_loads_feelings():
    gate, _ = fixture()
    crit = np.ones(len(gate.people))
    for role in (1, 2):
        rows = np.flatnonzero(gate.role == role)[::8][:59]
        crit[rows] = 2
    gate = revised_gate(gate, criticised=crit)
    out = d.analyse_roles(gate, no_outcomes)
    assert out['support']['strata']['below'] == dict(criticised_prompts=59, people=59)
    assert out['disposition'] == 'unsupported'


def test_coding_failure_never_loads_feelings():
    gate, _ = fixture()
    gate = revised_gate(gate, leadership=7-gate.leadership)
    out = d.analyse_roles(gate, no_outcomes)
    assert out['support']['support_passes']
    assert out['disposition'] == 'role_codes_do_not_carry_rank'


def test_review_copies_metadata_and_detects_later_mutation():
    gate, _ = fixture()
    lead = gate.leadership.copy()
    copied = revised_gate(gate, leadership=lead)
    lead[:] = 0
    assert copied.support()['coding_passes']
    copied.leadership.setflags(write=True)
    copied.leadership[0] += .1
    with pytest.raises(InvalidFit, match='metadata changed'):
        d.analyse_roles(copied, no_outcomes)


@pytest.mark.parametrize('change', ['source', 'order', 'criticism'])
def test_outcome_projection_must_match_reviewed_bytes_and_rows(change):
    gate, payload = fixture()
    if change == 'source':
        payload['source_sha256'] = 'b' * 64
    elif change == 'order':
        payload['row_keys'] = list(reversed(payload['row_keys']))
    else:
        payload['events']['criticised'] = payload['events']['criticised'] + .1
    with pytest.raises(InvalidFit, match='differs'):
        d.analyse_roles(gate, lambda: payload)


@pytest.mark.parametrize('field', ['events', 'outcomes'])
def test_no_covariate_or_comparison_feeling_can_be_dropped(field):
    gate, payload = fixture()
    payload[field].pop(next(iter(payload[field])))
    with pytest.raises(InvalidFit, match='All declared'):
        d.analyse_roles(gate, lambda: payload)


def test_missing_records_can_invalidate_support_after_the_outcome_read():
    gate, payload = fixture()
    payload['outcomes']['angry'] = payload['outcomes']['angry'].astype(float)
    payload['outcomes']['angry'][gate.people < 55] = np.nan
    out = d.analyse_roles(gate, lambda: payload)
    assert out['outcomes_read'] and 'fit' not in out
    assert out['disposition'] == 'unsupported_after_complete_cases'
    assert out['counts']['model_people'] == 35
    assert out['counts']['missing_model_rows'] == 55 * 24


def test_full_role_coefficients_agree_with_independent_model():
    import statsmodels.api as sm
    gate, payload = fixture()
    out = d.analyse_roles(gate, lambda: payload)
    X = reference_design(gate.people, gate.role, payload['events'])
    ref = {k: sm.Logit(y > 1, X).fit(disp=0).params for k, y in payload['outcomes'].items()}
    for name in d.OUTCOMES:
        np.testing.assert_allclose(out['fit']['coefficients'][name], ref[name], atol=1e-7)
        assert set(out['fit']['table'][name]['above']) == set(b.STATUS)
        assert out['fit']['table'][name]['above']['criticised'] == pytest.approx(ref[name][2]+ref[name][8])
    expected = ref['angry'][7] - ref['angry'][8] - np.mean([ref[k][7]-ref[k][8] for k in b.FEAR_LIKE])
    assert out['fit']['primary'] == pytest.approx(expected, abs=1e-7)
    assert expected > 0
    assert out['disposition'] == 'point_fit_only'


def test_weighted_person_fit_equals_literal_whole_person_replication():
    gate, p = fixture()
    counts = np.random.default_rng(55).integers(0, 4, 90)
    w = counts[gate.people]
    ix = np.repeat(np.arange(len(w)), w)
    weighted = d.role_fit(gate.people, gate.role, p['events'], p['outcomes'], w)
    repeated = d.role_fit(gate.people[ix], gate.role[ix], {k:v[ix] for k,v in p['events'].items()},
                          {k:v[ix] for k,v in p['outcomes'].items()})
    for name in d.OUTCOMES:
        np.testing.assert_allclose(weighted['coefficients'][name], repeated['coefficients'][name], atol=1e-7)


def test_reversing_roles_reverses_the_contrast():
    gate, p = fixture()
    forward = d.role_fit(gate.people, gate.role, p['events'], p['outcomes'])
    roles = np.where(gate.role == 1, 2, np.where(gate.role == 2, 1, gate.role))
    reverse = d.role_fit(gate.people, roles, p['events'], p['outcomes'])
    assert reverse['primary'] == pytest.approx(-forward['primary'], abs=1e-8)


def test_identical_feelings_give_zero_not_an_invalid_fit():
    gate, p = fixture()
    out = d.role_fit(gate.people, gate.role, p['events'], {k:p['outcomes']['angry'] for k in d.OUTCOMES})
    assert abs(out['primary']) < 1e-12


def test_other_roles_are_counted_but_unscored():
    gate, p = fixture()
    roles = gate.role.copy()
    roles[:96] = 4
    gate = revised_gate(gate, role=roles)
    out = d.analyse_roles(gate, lambda: p)
    assert out['support']['other_codes'] == {'4': 96}
    assert out['counts']['model_rows'] == len(roles)-96
    keep = roles != 4
    expected = d.role_fit(gate.people[keep], roles[keep],
                          {k:v[keep] for k,v in p['events'].items()},
                          {k:v[keep] for k,v in p['outcomes'].items()})
    assert out['fit']['primary'] == expected['primary']


def test_nonintegral_role_codes_and_duplicate_row_keys_refuse():
    gate, _ = fixture()
    with pytest.raises(InvalidFit, match='integral'):
        revised_gate(gate, role=gate.role + .5)
    with pytest.raises(InvalidFit, match='Unique ordered'):
        revised_gate(gate, row_keys=['same']*len(gate.people))


def test_absent_peer_reference_is_invalid_not_a_dropped_column():
    gate, p = fixture()
    keep = gate.role != 3
    with pytest.raises(InvalidFit):
        d.role_fit(gate.people[keep], gate.role[keep],
                    {k:v[keep] for k,v in p['events'].items()},
                    {k:v[keep] for k,v in p['outcomes'].items()})


def test_ld1_diagnostic_retains_model_with_explicit_group_labels():
    gate, p = fixture()
    context = (gate.role == 1).astype(float)
    feelings = dict(ashamed=p['outcomes']['ashamed'], sad=p['outcomes']['anxious'])
    out = d.context_diagnostic(gate.people, context, gate.criticised, feelings)
    expected = b.ld1(gate.people, context, gate.criticised, feelings)
    assert out['contrast'] == expected['primary']
    assert out['form_l'] == expected['form_l']
    assert out['feelings']['ashamed']['comparison'] == expected['feelings']['ashamed']['company']
    assert out['descriptive_only'] and 'primary' not in out
