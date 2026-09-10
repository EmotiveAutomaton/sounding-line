"""Evaluator-only original broad-generation comparator and explicit Stage 9 parsing.

DESIGN CHECK: C02/C06. Preserve Stage 8's visible feasibility, extended-inventory score,
upper-median rule and twentieth-percentile reference. Report stricter syntax separately.
Invalid calls stay in the attempt denominator. No language-model output is executed.
NULL: plausible prose, repeated actions or unsupported outcomes cannot pass strict logs.
ALTERNATIVE: an actual constructor trajectory parses and satisfies its visible mechanics.
"""
from runners.stage8.constructor import population as POP
from runners.stage8.reader import logfmt as LF


def parse(text, max_lines=28):
    lines = text.split('\n')[:max_lines]
    legacy_events, legacy_stopped = [], False
    for line in lines:
        event = LF.parse_line(line)
        if event is None:
            if legacy_events:
                break
            continue
        if event.get('stop'):
            legacy_stopped = True
            break
        legacy_events.append({k: event[k] for k in ('type', 'section', 'slot')} | {'outcome': event.get('outcome', 'done')})
    strict_events, strict_stopped, errors = [], False, []
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        event = LF.parse_line(line)
        if strict_stopped:
            errors.append({'line': i, 'reason': 'nonempty output after STOP'})
            continue
        if event is None:
            errors.append({'line': i, 'reason': 'unparsed nonempty output'})
            continue
        if event['i'] != len(strict_events):
            errors.append({'line': i, 'reason': 'incorrect action clock'})
        if event.get('stop'):
            strict_stopped = True
            continue
        if event.get('outcome') not in ('done', 'failed'):
            errors.append({'line': i, 'reason': 'full log requires an explicit supported outcome'})
        strict_events.append(event)
    return {'legacy_events': legacy_events, 'legacy_stopped': legacy_stopped,
            'strict_events': strict_events, 'strict_stopped': strict_stopped, 'strict_errors': errors,
            'strict_syntax_valid': bool(strict_events) and not errors,
            'lines_outside_historical_cap': max(0, len(text.split('\n'))-max_lines),
            'historical_parse_rule': 'skip preamble; break after first unparsed post-event line; default omitted outcome to done; ignore printed clock',
            'strict_parse_rule': 'retain nonempty syntax errors, printed clock errors and missing/invalid outcomes; stopping reported separately'}


def score_attempt(world, prediction, max_lines=28):
    if not prediction.get('accepted'):
        return {'valid_execution': False, 'legacy_feasible': False, 'strict_feasible': False,
                'legacy_population_per_event': None, 'events': 0, 'stopped': False,
                'failure': 'invalid reader call retained in denominator'}
    parsed = parse(prediction['prediction']['text'], max_lines)
    events = parsed['legacy_events']
    visible = POP.feasible_visible(world, events)
    hidden = POP.feasible(world, events)
    population = POP.marginal_log_likelihood(world, events, extend=True) if visible['all_feasible'] else {'total': None, 'per_event': None}
    strict = parsed['strict_syntax_valid'] and POP.feasible_visible(world, parsed['strict_events'])['all_feasible']
    return {'valid_execution': True, 'legacy_feasible': visible['all_feasible'], 'strict_feasible': strict,
            'legacy_population_per_event': population['per_event'], 'legacy_population_total': population['total'],
            'events': len(events), 'stopped': parsed['legacy_stopped'], 'strict_stopped': parsed['strict_stopped'],
            'visible_feasibility': visible, 'hidden_inventory_feasibility': hidden, 'parse': parsed}


def original_broad_comparator(attempts, reference_scores, expected_attempts):
    if len(attempts) != expected_attempts or not reference_scores:
        raise ValueError('full attempts and a separately frozen reference population required')
    real = sorted(reference_scores)
    percentile = real[min(len(real)-1, max(0, int(round(.20*(len(real)-1)))))]
    values = sorted(r['legacy_population_per_event'] for r in attempts if r['legacy_population_per_event'] is not None)
    median = values[len(values)//2] if values else None
    feasibility = sum(r['valid_execution'] and r['legacy_feasible'] for r in attempts) / expected_attempts
    return {'n_attempts': expected_attempts, 'n_reference': len(real), 'reference_twentieth_percentile': percentile,
            'visible_feasibility': feasibility, 'strict_feasibility': sum(r['strict_feasible'] for r in attempts)/expected_attempts,
            'legacy_upper_median_per_event': median,
            'historical_broad_pass': feasibility == 1.0 and median is not None and median >= percentile,
            'scope': 'original-distribution comparator only; fitted adapters and expanded distributions require separate identities',
            'stopping_is_separate': True, 'invalid_calls_remain_in_denominator': True}
