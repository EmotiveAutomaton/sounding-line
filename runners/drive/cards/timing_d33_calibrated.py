"""Separately labelled calibration-supported D33 pair under week S1.

DESIGN CHECK: LESSONS 3-5 read October19. Selection reads calibration support,
never pauses, fitted effects, or evaluation losses. Under NULL and ALTERNATIVE
the same keys survive. Every original key has one disposition. Empty support,
changed authenticated intermediates or undefined focal fits refuse; no imputation.
Original joint estimator, signed bands, paired writer draws and two permutation
families remain unchanged. A smaller supported population leaves the original
question open. No P7 event, new model, paid computation or causal claim is added.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import time

from . import timing_d33_supported as original
from . import timing_d33_supported_source as sources
from . import timing_d33_supported_counts as counts
from .timing_census import read, filehash
from .timing_p6 import write_equal, gzip_equal, gzread, progress
from .timing_stats import bind, check_binding
from .batch_runtime import check_files

CONFIG = dict(original.configuration('pair'), card='D33.pair-calibration-supported',
              population='matched history and nonempty original supported calibration')
INPUTS = {'prior_completion', 'prior_receipt'}


def select_population(roster, saved):
    """Partition original evaluation keys using only pre-fit support facts."""
    result = deepcopy(roster)
    owners = {(r['session'], r['index']): r['writer'] for r in saved['rows']}
    old_kept = [tuple(k) for k in roster['retained_keys']]
    old_missing = [tuple(k) for k in roster['unsupported_keys']]
    if (len(owners) != len(saved['rows']) or len(old_kept + old_missing) != len(owners)
            or len(set(old_kept + old_missing)) != len(owners)
            or set(old_kept + old_missing) != set(owners)):
        raise ValueError('original evaluation roster is not an exact partition')
    supported = {w for w, v in roster['writers'].items() if v['calibration_keys']}
    kept = [k for k in old_kept if owners[k] in supported]
    dropped = [k for k in old_kept if owners[k] not in supported]
    result['retained_keys'] = [list(k) for k in kept]
    result['unsupported_keys'] = [list(k) for k in old_missing + dropped]
    result['calibration_unsupported_keys'] = [list(k) for k in dropped]
    result['original_supported_coverage'] = deepcopy(roster['coverage'])
    for writer, part in result['writers'].items():
        count = sum(owners[k] == writer for k in dropped)
        part['excluded_for_missing_calibration_words'] = count
        part['retained_evaluation_words'] -= count
        part['unsupported_evaluation_words'] += count
        if writer not in supported:
            part['unsupported_sessions']['evaluation'] += part['supported_sessions']['evaluation']
            part['supported_sessions']['evaluation'] = []
    result['coverage'].update(
        retained_words=len(kept), unsupported_words=len(old_missing) + len(dropped),
        calibration_unsupported_words=len(dropped),
        calibration_unsupported_writers=len({owners[k] for k in dropped}),
        retained_writers=len({owners[k] for k in kept}),
        wholly_unsupported_writers=sum(v['retained_evaluation_words'] == 0 for v in result['writers'].values()),
        writers_with_any_unsupported_words=sum(v['unsupported_evaluation_words'] > 0 for v in result['writers'].values()),
        retained_sessions={split: sum(len(v['supported_sessions'][split]) for v in result['writers'].values()) for split in ('calibration', 'evaluation')},
        unsupported_sessions={split: sum(len(v['unsupported_sessions'][split]) for v in result['writers'].values()) for split in ('calibration', 'evaluation')})
    result['selection'] = 'Nonempty supported calibration keys only; original chronological split and all donor matches unchanged'
    return result


def load_source(inputs, config):
    if set(inputs) != INPUTS or config != CONFIG:
        raise ValueError('exact calibration-supported inputs/config required')
    root = Path(inputs['prior_completion']).resolve().parent
    done, plan, receipt = read(inputs['prior_completion']), read(root/'PLAN.json'), read(inputs['prior_receipt'])
    if (done['status'] != 'COMPLETE' or not done['fresh_process_verified']
            or plan['module'] != counts.__name__ or plan['config'] != original.configuration('pair')
            or filehash(root/'COMPLETE.json') != receipt['complete_sha256']
            or filehash(root/'PLAN.json') != receipt['plan_sha256']
            or not receipt['full_fresh_source_verification'] or receipt['state'] != 'invalid'
            or receipt['reason'] != 'retained evaluation writers have no supported calibration words'):
        raise ValueError('prior complete source or invalid disposition changed')
    check_files(plan['pins'])
    for name, expected in done['outputs'].items():
        if filehash(root/name) != expected:
            raise ValueError('prior completed output changed: '+name)
    # Rebuild original source/matches with the already validated exact counter.
    source = object.__new__(sources.Sources)
    counts.source_constructor(source, {k: plan['inputs'][k] for k in original.INPUTS})
    old_roster = source.roster_for('pair')
    if old_roster != read(root/'output/SUPPORTED_ROSTER.json'):
        raise ValueError('original supported roster differs on reconstruction')
    return source, old_roster, root


def prepared(output, inputs, config, verifying=False):
    source, old_roster, root = load_source(inputs, config)
    roster = select_population(old_roster, source.saved)
    # This artifact is frozen before calibration or access to inference outputs.
    if verifying:
        if read(output/'SUPPORTED_ROSTER.json') != roster:
            raise ValueError('calibration-supported roster changed')
    else:
        write_equal(output/'SUPPORTED_ROSTER.json', roster)
    tuning = sources.calibrate(old_roster, source.units['pair'], source.lookup)
    if tuning != read(root/'output/CALIBRATION.json'):
        raise ValueError('original chronological calibration changed')
    covariates = {sid: gzread(root/'output/sessions'/(sid+'.json.gz'))
                  for sid in sorted({sid for sid, _ in roster['retained_keys']})}
    rows = sources.scientific_rows(source.saved, roster, source.units['pair'], source.lookup, tuning, covariates)
    return rows, roster, tuning, covariates


def result(statistics, roster, tuning, covariates):
    value = original.result(statistics, roster, tuning, covariates, 'pair')
    value.update(card=CONFIG['card'], population=CONFIG['population'],
                 source_replay='Original matching and calibration rebuilt; authenticated complete raw covariates reused unchanged',
                 original_supported_attempt='Retained invalid; no scientific fit was run in it')
    return value


def execute(output, inputs, config):
    started = time.monotonic(); output = Path(output)
    write_equal(output/'INPUTS.json', original.binding(inputs, config))
    rows, roster, tuning, covariates = prepared(output, inputs, config)
    write_equal(output/'CALIBRATION.json', tuning)
    gzip_equal(output/'DESIGN.json.gz', rows)
    source_seconds = time.monotonic() - started

    def checkpoint(item):
        progress(output/'PROGRESS.json', dict(phase='joint-inference', **item))
        if item['blocks'] == 1 and not (output/'FIRST_TENTH.json').exists():
            write_equal(output/'FIRST_TENTH.json', dict(
                projected_seconds=2*(source_seconds+10*item['measured_block_seconds']),
                method='Both full inference arms plus both control families; source and fresh replay included; prior costs held by supervisor'))
        return (output/'YIELD_REQUEST.json').exists()

    statistics = original.run(rows, draws=config['bootstrap_draws'], permutations=config['permutations'],
                              seed=config['seed'], checkpoint=output/'inference', checkpoint_callback=checkpoint)
    if statistics.get('status') == 'yielded':
        return statistics
    value = result(statistics, roster, tuning, covariates)
    write_equal(output/'PRIMARY.json', value)
    artifacts = ['INPUTS.json', 'SUPPORTED_ROSTER.json', 'CALIBRATION.json', 'DESIGN.json.gz', 'PRIMARY.json']
    artifacts += [p.relative_to(output).as_posix() for p in sorted((output/'inference').glob('*.json'))]
    if (output/'FIRST_TENTH.json').exists(): artifacts.append('FIRST_TENTH.json')
    if (output/'TIMING_BINDINGS.json').exists(): check_binding(output, inputs, config)
    else: bind(output, inputs, config, artifacts)
    progress(output/'PROGRESS.json', dict(phase='complete', seconds=time.monotonic()-started))
    return value


def verify(output, inputs, config):
    output = Path(output); check_binding(output, inputs, config)
    if read(output/'INPUTS.json') != original.binding(inputs, config):
        raise ValueError('new source binding changed')
    rows, roster, tuning, covariates = prepared(output, inputs, config, True)
    if rows != gzread(output/'DESIGN.json.gz') or tuning != read(output/'CALIBRATION.json'):
        raise ValueError('supported design or calibration changed')
    # Fresh process, no saved inference blocks: complete statistical replay.
    statistics = original.run(rows, draws=config['bootstrap_draws'], permutations=config['permutations'], seed=config['seed'])
    value = result(statistics, roster, tuning, covariates)
    if value != read(output/'PRIMARY.json'):
        raise ValueError('fresh full inference differs')
    return dict(verified=True, original_question_open=True, coverage=roster['coverage'],
                full_matching_calibration_and_statistical_replay=True, authenticated_covariate_reuse=True)
