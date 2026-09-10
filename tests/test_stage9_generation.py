from runners.stage8.constructor import population as POP
from runners.stage8.reader import logfmt as LF
from runners.stage9.generation_evaluator import parse, original_broad_comparator


def test_actual_constructor_log_has_valid_strict_syntax():
    world = POP.sample_world(POP.pop_lid(7, 'essay', 9950000))
    lines = [LF.event_line(e['i'], e['type'], e['section'], e['slot'], e['outcome']) for e in world['trajectory']['steps']]
    if world['trajectory']['stop_kind'] == 'hazard':
        lines.append(LF.stop_line(len(lines)))
    result = parse('\n'.join(lines), max_lines=100)
    assert result['strict_syntax_valid']
    assert POP.feasible_visible(world, result['strict_events'])['all_feasible']


def test_legacy_and_strict_clock_preamble_and_outcome_semantics_stay_distinct():
    result = parse('A fluent story.\n99 write sec1 s1.1\n42 stop')
    assert result['legacy_stopped'] and len(result['legacy_events']) == 1
    assert result['legacy_events'][0]['outcome'] == 'done'
    assert not result['strict_syntax_valid']
    assert len(result['strict_errors']) == 4


def test_invalid_call_cannot_be_removed_to_obtain_broad_admission():
    good = {'valid_execution': True, 'legacy_feasible': True, 'strict_feasible': True, 'legacy_population_per_event': -.2}
    bad = {'valid_execution': False, 'legacy_feasible': False, 'strict_feasible': False, 'legacy_population_per_event': None}
    assert original_broad_comparator([good, good], [-1., -.5, -.3], 2)['historical_broad_pass']
    assert not original_broad_comparator([good, bad], [-1., -.5, -.3], 2)['historical_broad_pass']
