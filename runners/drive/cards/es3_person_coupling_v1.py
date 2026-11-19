"""Approved anger reactivity versus short-minus-long carry, exact person join.

DESIGN CHECK: LESSONS 2/3/5; packet ES2/ES3 and curator scalar ruling.
NULL: equal short/long day-floor carry cancels; an unrelated contrast yields
zero coupling, while undefined slopes stay unsupported. ALTERNATIVE: coupled
literal person slopes recover their signed correlation. Parent cohorts and
original context calibration precede the join. No new bar or correction.
"""
import numpy as np
try:
    from . import es_core_v1 as core, es_source_v1 as source, es_clock_v1 as clock, es_carry_v1 as carry
except ImportError:
    import es_core_v1 as core
    import es_source_v1 as source
    import es_clock_v1 as clock
    import es_carry_v1 as carry

DEFINITION = {
    'schema': 'ES3_PERSON_ANGER_SHORT_MINUS_LONG_V1',
    'reactivity': 'full_prompt_slope_mean_scaled_angry_resentful_on_mean_four_scaled_negative_events',
    'carry': 'per_person_angry_slope_gap_lt90_minus_gap_gt240',
    'calibration': 'separate_original_parent_cohorts_before_exact_person_join',
    'uncertainty': '2000_shared_whole_person_draws_over_union_of_parent_eligible_rosters',
    'scales_in_each_draw': 'recompute_original_parent_pooled_within_person_sample_scales',
    'association': 'descriptive_uncorrected_person_correlation_no_decision_bar',
    'invalid_draw_policy': 'retain_all_no_redraw_no_selective_interval',
}
FIELDS = core.NEGATIVE + core.FAMILIES['anger']


def prepare_reactivity(frames, member, missing_tokens, guard=lambda: None):
    """Full anger-family panel independent of carry clock/activity exclusions.

    Each interaction is decoded with the original rating/day rules. The original
    common complete-case panel and ten-prompt eligibility apply to this secondary
    family. Raw rows/identities stay private. Returning sufficient statistics
    releases the interaction arrays before the independent carry source pass.
    """
    core.need(member in ('0056', '0057'), 'coupling source member differs')
    grouped = {}
    counts = dict(source_rows=0, missing_id_rows=0, missing_interaction_rows=0,
                  noninteraction_rows=0, interaction_rows=0, source_people=0,
                  missing_rows=0, under_minimum_people=0, under_minimum_rows=0)
    for frame in frames:
        guard()
        core.need(set(frame.columns) == set(clock.whitelist(member, 'carry')), 'coupling whitelist differs')
        for row in frame.to_dict('records'):
            counts['source_rows'] += 1
            if row['id'] in missing_tokens:
                counts['missing_id_rows'] += 1
                continue
            day = source.study_day(row['day'], missing_tokens)
            context = row['interaction']
            if context in missing_tokens:
                counts['missing_interaction_rows'] += 1
                continue
            try:
                context = float(context)
            except (TypeError, ValueError):
                raise ValueError('unknown interaction code') from None
            core.need(context in (1., 2.), 'unknown interaction code')
            if context == 2.:
                counts['noninteraction_rows'] += 1
                continue
            counts['interaction_rows'] += 1
            person = grouped.setdefault((member, row['id']), {'days': [], 'ratings': {n: [] for n in FIELDS}})
            person['days'].append(day)
            for name in FIELDS:
                prefix = 'status_' if name in core.NEGATIVE else 'int_'
                person['ratings'][name].append(source.rating(row[prefix+name], 6, missing_tokens))
    counts['source_people'] = len(grouped)
    people, keys = [], []
    for key, person in sorted(grouped.items()):
        guard()
        one = core.panel_stats([person], core.NEGATIVE, core.FAMILIES['anger'], minimum=10, require_days=True)
        for name in ('missing_rows', 'under_minimum_people', 'under_minimum_rows'):
            counts[name] += one['excluded'][name]
        if one['people']:
            people.append(one['people'][0])
            keys.append(key)
    stats = dict(people=people, xnames=core.NEGATIVE, ynames=core.FAMILIES['anger'],
                 fields=FIELDS, minimum=10, original_day_split=True, excluded=counts)
    return dict(stats=stats, private_keys=keys, source_counts=counts)


def combine(reactivity, carry_prepared, member):
    """Freeze both original parent rosters before joining; no nearest-key match."""
    first = list(reactivity['private_keys'])
    second = list(carry_prepared['private_keys'])
    core.need(len(first) == len(reactivity['stats']['people']) and
              len(second) == len(carry_prepared['stats']['people']), 'parent key/stat alignment differs')
    core.need(len(first) == len(set(first)) and len(second) == len(set(second)), 'duplicate exact person key')
    core.need(member in ('0056', '0057') and all(type(k) is tuple and len(k) == 2 and
              k[0] == member and type(k[1]) is str for k in first+second), 'mixed or malformed source person identity')
    core.need(tuple(reactivity['stats']['xnames']) == core.NEGATIVE and
              tuple(reactivity['stats']['ynames']) == core.FAMILIES['anger'], 'reactivity parent items differ')
    core.need(tuple(carry_prepared['stats']['outcomes']) == ('angry',), 'carry parent outcome differs')
    union = sorted(set(first) | set(second))
    positions = {key: i for i, key in enumerate(union)}
    common = sorted(set(first) & set(second))
    first_index = {key: i for i, key in enumerate(first)}
    second_index = {key: i for i, key in enumerate(second)}
    return dict(people=[{} for _ in union], reactivity=reactivity['stats'], carry=carry_prepared['stats'],
                private_union_keys=union, first_positions=[positions[k] for k in first],
                second_positions=[positions[k] for k in second], common_positions=[positions[k] for k in common],
                common_first=[first_index[k] for k in common], common_second=[second_index[k] for k in common],
                coverage=dict(first_people=len(first), second_people=len(second), common_people=len(common),
                              first_only_people=len(set(first)-set(second)), second_only_people=len(set(second)-set(first))),
                source_counts=dict(reactivity=reactivity['source_counts'], carry=carry_prepared['source_counts']))


def prepare(path, pin, member, missing_tokens, guard=lambda: None):
    """Two authenticated whitelist passes, no raw-frame duplication or export."""
    first = prepare_reactivity(clock.selected_frames(path, pin, member, 'carry', guard), member, missing_tokens, guard)
    second = clock.prepare_carry(clock.selected_frames(path, pin, member, 'carry', guard), member, ('angry',),
                                 missing_tokens, clock.UTC_PROFILE, clock.CALIBRATION, guard)
    return combine(first, second, member)


def _reactivity_slopes(stats, weights):
    sd, _, _ = core.scale_and_sum(stats, weights)
    moments = np.asarray([p['ss'] for p in stats['people']], dtype=np.float64)
    wx = 1 / sd[:4] / 4
    wy = 1 / sd[4:] / 2
    denominator = np.einsum('i,pij,j->p', wx, moments[:, :4, :4], wx)
    numerator = np.einsum('i,pij,j->p', wx, moments[:, :4, 4:], wy)
    slopes = np.full(len(moments), np.nan)
    good = denominator > 0
    slopes[good] = numerator[good] / denominator[good]
    return slopes


def _carry_slopes(stats, weights):
    w = core.weights_for(stats, weights)
    ss = sum(weight*p['calibration_ss'] for p, weight in zip(stats['people'], w))
    df = sum(weight*(p['calibration_n']-1) for p, weight in zip(stats['people'], w))
    if np.any(df <= 0) or np.any(ss <= 0):
        raise core.Unidentified('original carry calibration lacks variance')
    sd = np.sqrt(ss/df)
    values = np.full(len(w), np.nan)
    reasons = {'short_unsupported_people': 0, 'long_unsupported_people': 0}
    for i, person in enumerate(stats['people']):
        short, long = person['short'], person['bins'][4]
        good_short = short['n'] >= 2 and short['cov'][0, 0] > 0
        good_long = long['n'] >= 2 and long['cov'][0, 0] > 0
        reasons['short_unsupported_people'] += int(not good_short)
        reasons['long_unsupported_people'] += int(not good_long)
        if good_short and good_long:
            values[i] = (short['cov'][0, 1]/short['cov'][0, 0] -
                         long['cov'][0, 1]/long['cov'][0, 0])*sd[0]/sd[1]
    return values, reasons


def estimate(stats, weights=None):
    w = core.weights_for(stats, weights)
    first = _reactivity_slopes(stats['reactivity'], w[stats['first_positions']])
    second, reasons = _carry_slopes(stats['carry'], w[stats['second_positions']])
    a, b = first[stats['common_first']], second[stats['common_second']]
    valid = np.isfinite(a) & np.isfinite(b)
    support = dict(stats['coverage'], union_people=len(stats['people']),
                   identified_people=int(valid.sum()), undefined_common_people=int((~valid).sum()),
                   undefined_reactivity_people=int((~np.isfinite(first)).sum()),
                   undefined_carry_people=int((~np.isfinite(second)).sum()), **reasons)
    if int(valid.sum()) < 2:
        return dict(status='UNSUPPORTED_IDENTIFICATION', correlation=None, support=support,
                    reason='population coupling needs at least two independent identified people')
    try:
        result = carry.person_coupling(a, b, w[stats['common_positions']])
    except core.Unidentified as exc:
        return dict(status='UNSUPPORTED_IDENTIFICATION', correlation=None, support=support, reason=str(exc))
    return dict(status='IDENTIFIED', correlation=result['correlation'], support=support,
                descriptive_uncorrected_correlation=True, reliability_correction=False, decision_bar=None)


def statistic(stats, weights=None):
    result = estimate(stats, weights)
    if result['status'] != 'IDENTIFIED':
        raise core.Unidentified(result['reason'])
    return result['correlation']
