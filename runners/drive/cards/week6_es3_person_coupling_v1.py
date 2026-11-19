"""Bounded source-consistent ES3 coupling; execute plus independent full replay.

DESIGN CHECK: original clocks/cohorts, approved short-minus-long scalar, exact
source/code/config pins, two threads, complete person draws and no premature
verified flag. Source admission and native containment/costs remain owner/runtime
obligations. No primary result or new scientific decision threshold is added.
"""
from pathlib import Path
import time
try:
    from . import es_core_v1 as core, es_source_v1 as source, es_carry_v1 as carry
    from . import es_handler_v1 as io, week6_es_v1 as base, es_clock_v1 as clock
    from . import es_population_guard_v1 as population, es3_person_coupling_v1 as coupling
except ImportError:
    import es_core_v1 as core
    import es_source_v1 as source
    import es_carry_v1 as carry
    import es_handler_v1 as io
    import week6_es_v1 as base
    import es_clock_v1 as clock
    import es_population_guard_v1 as population
    import es3_person_coupling_v1 as coupling


def load(inputs, config):
    intake, panel = base.load(inputs, config)
    core.need(set(panel) == {'member', 'card', 'panel', 'source_pin', 'draws', 'seed', 'calibration_scope',
                            'source_layout_review', 'missing_tokens', 'coupling_definition'}, 'coupling panel fields differ')
    core.need(panel['member'] in ('0056', '0057') and panel['card'] == 'ES3' and
              panel['panel'] == 'person_anger_short_minus_long', 'coupling source/panel differs')
    core.need(panel['source_pin'] == intake['members'][panel['member']]['raw_ts_pin_from_receipt_only'], 'coupling metadata source differs')
    review = io.read_json(inputs['source_admission_path'])
    core.need({'ES2', 'ES3'} <= set(review['cards']), 'both parent source scopes require admission')
    core.need(panel['coupling_definition'] == coupling.DEFINITION, 'approved coupling definition differs')
    core.need(panel['draws'] == 2000 and type(panel['seed']) is int and panel['seed'] >= 0, 'coupling draws differ')
    core.need(panel['source_layout_review']['status'] == 'OWNER_REVIEWED' and
              panel['source_layout_review']['clock_profile'] == clock.UTC_PROFILE, 'coupling clock review differs')
    core.need(panel['calibration_scope'] == clock.CALIBRATION, 'original context calibration differs')
    core.need(type(panel['missing_tokens']) is list and all(type(x) is str for x in panel['missing_tokens']), 'explicit missing tokens required')
    core.need(set(config) == {'panel_config', 'max_new_draws', 'max_wall_seconds'}, 'coupling operational fields differ')
    core.need(type(config['max_new_draws']) is int and 1 <= config['max_new_draws'] <= 2000, 'draw quantum differs')
    core.need(type(config['max_wall_seconds']) in (int, float) and 0 < config['max_wall_seconds'] <= 1500, 'cooperative wall cap differs')
    return intake, panel


def operation(output, inputs, config, phase):
    core.need(phase in ('execute', 'verify'), 'coupling phase differs')
    output = Path(output)
    if phase == 'verify':
        core.need((output/'execute/ENGINE_RESULT.json').is_file(), 'complete execute required before fresh replay')
    intake, panel = load(inputs, config)
    output.mkdir(parents=True, exist_ok=True)
    if phase == 'execute':
        base.preserve_inherited_yield(output)
    started = time.monotonic()
    root = output/phase
    root.mkdir(exist_ok=True)
    def guard():
        if (output/'YIELD_REQUEST.json').exists() or (output/'STOP_REQUEST.json').exists() or time.monotonic()-started >= config['max_wall_seconds']:
            raise io.Pause('coupling cooperative yield')
    modules = (core, source, carry, io, base, clock, population, coupling)
    files = [Path(m.__file__) for m in modules]+[Path(__file__)]
    binding = io.digest({'panel': panel, 'intake': intake, 'code': {p.name: source.sha256(p) for p in files}})
    io.exclusive_json(root/'BINDING.json', {'binding': binding, 'phase': phase})
    try:
        guard()
        prepared = coupling.prepare(inputs['source_path'], panel['source_pin'], panel['member'], panel['missing_tokens'], guard)
        scope = {'source': prepared['source_counts'], 'parent_join': prepared['coverage'],
                 'resampling_union_people': len(prepared['people']), 'definition': coupling.DEFINITION,
                 'identities_or_individual_slopes_exported': False, 'authenticated_source_passes': 2}
        point = None
        try:
            point = coupling.estimate(prepared)
        except core.Unidentified as exc:
            scope['global_identification_hold'] = str(exc)
            result = {'status': 'UNSUPPORTED_IDENTIFICATION', 'reason': str(exc), 'point': None,
                      'binding': binding, 'verified': False}
        else:
            scope['identified_parent_join'] = point['support']
            if point['status'] != 'IDENTIFIED':
                result = {'status': 'UNSUPPORTED_IDENTIFICATION', 'reason': point['reason'], 'point': point,
                          'binding': binding, 'verified': False}
            else:
                io.exclusive_json(root/'SCOPE.json', scope)
                population.require_population_interval(prepared)
                io.exclusive_json(root/'POINT.json', {'point': point})
                journal = io.DrawJournal(root/'draws', binding)
                calls = 0
                def progress(row):
                    nonlocal calls
                    journal.append(row)
                    calls += 1
                    guard()
                    if calls >= config['max_new_draws'] and row['draw'] < 1999:
                        raise io.Pause('coupling draw quantum')
                try:
                    boot = population.bootstrap(prepared, lambda w: coupling.statistic(prepared, w),
                                                panel['seed'], progress=progress, prior=journal.rows)
                finally:
                    journal.flush()
                core.need(len(journal.rows) == 2000, 'incomplete coupling draws')
                result = {'status': 'ENGINE_COMPLETE', 'binding': binding, 'point': point, 'draw_count': 2000,
                          'draw_sha256': io.digest(journal.rows), 'invalid_draws': boot['invalid_draws'],
                          'interval': boot['interval'], 'redraws': 0, 'valid_draw_only_interval': False,
                          'descriptive_uncorrected_correlation': True, 'reliability_correction': False,
                          'decision_bar': None, 'verified': False}
        io.exclusive_json(root/'SCOPE.json', scope)
        guard()
        io.exclusive_json(root/'ENGINE_RESULT.json', result)
    except io.Pause:
        return {'status': 'yielded', 'verified': False, 'operation': phase, 'scientific_result_complete': False}
    if phase == 'execute':
        return {'status': 'computed', 'verified': False, 'engine': result, 'requires_fresh_replay': True}
    proof = io.compare_fresh_phases(output/'execute', output/'verify')
    if result['status'] == 'ENGINE_COMPLETE':
        for child in ('execute', 'verify'):
            core.need(io.read_json(output/child/'POINT.json') == {'point': result['point']}, 'coupling point proof differs')
    return {'status': 'verified', 'verified': True, 'numerical_replay': proof, 'native_proof_required_from_runtime': True}


def execute(output, inputs, config):
    return operation(output, inputs, config, 'execute')


def verify(output, inputs, config):
    return operation(output, inputs, config, 'verify')
