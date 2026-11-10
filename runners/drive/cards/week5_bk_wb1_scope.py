"""Prospective whole-writer WB1 scope; no count or forecast is chosen here.

DESIGN CHECK: the original writer split, session rows, source bytes and random
reference indices survive projection. Candidate discovery is recomputed from
selected discovery writers only. Corpus scope requires a measured E decision.
"""
from pathlib import Path
from collections import Counter
import math
import time
import numpy as np

from . import week5_bk_wb1_source as original
from . import week5_bk_wb1_pilot_forecast as coverage_forecast
from . import week5_bk_wb1_reduce_v2 as effect_forecast
from . import week3_pieces_stats as stats
from . import week3_pieces_effects_h1_pilot as pilot
from .timing_census import read, filehash
from .timing_p6 import gzread
from runners.stage14.common import digest, atomic

SAMPLE_SEED = 20261102
CARD_CEILING = 260000
HISTORICAL_CHARGED_CPU = 24148.953125
completed = original.completed
checked = original.checked
session = original.session
model = original.model
timed = original.timed


def choose(rows, count):
    writers = sorted({r['writer'] for r in rows})
    if type(count) is not int or not 1 <= count <= len(writers):
        raise ValueError('Whole-writer count must be within the source population')
    # WB1 does not analyse genre; no new genre proxy or outcome stratum is added.
    return sorted(np.random.default_rng(SAMPLE_SEED).permutation(writers).tolist()[:count])


def positive(value, label, zero=False):
    if type(value) not in (float, int) or not math.isfinite(value) or value < 0 or (not zero and value == 0):
        raise ValueError('Invalid measured scope quantity: ' + label)
    return value


def budget(decision, coverage, effect):
    charged = positive(decision['charged_cpu_seconds'], 'prior charges', zero=True)
    if charged < HISTORICAL_CHARGED_CPU:
        raise ValueError('Historical WB1 charges cannot be reset by sampling')
    full = charged + positive(coverage, 'coverage forecast') + positive(effect, 'effects forecast')
    if decision['full_projected_cpu_seconds'] != full or full <= 2 * CARD_CEILING:
        raise ValueError('Verified combined forecast does not trigger amendment E')
    remaining = 2 * CARD_CEILING - charged
    estimate = positive(decision['projected_sample_cpu_seconds'], 'prospective sample estimate')
    if remaining <= 0 or decision['sample_budget_cpu_seconds'] != remaining or estimate > remaining:
        raise ValueError('Sample does not fit the frozen remaining doubled ceiling')
    if not isinstance(decision['sizing_note'], str) or not decision['sizing_note'].strip():
        raise ValueError('Prospective cost sizing rationale required')
    return full, remaining, estimate, charged


def measured_decision(inputs, config, parent, population):
    decision = read(inputs['scope_decision'])
    required = {'schema', 'owner_reviewed', 'source_complete_sha256', 'writers', 'seed',
                'card_ceiling_cpu_seconds', 'charged_cpu_seconds', 'sample_budget_cpu_seconds',
                'full_projected_cpu_seconds', 'projected_sample_cpu_seconds', 'sizing_note',
                'coverage_forecast_complete_sha256', 'effects_cost_complete_sha256'}
    if set(decision) != required or decision['schema'] != 'WB1-WHOLE-WRITER-SCOPE-1' or decision['owner_reviewed'] is not True:
        raise ValueError('Frozen owner-reviewed scope decision required')
    if (decision['writers'] != config['writers'] or decision['seed'] != SAMPLE_SEED or
            decision['card_ceiling_cpu_seconds'] != CARD_CEILING or
            decision['source_complete_sha256'] != filehash(parent / 'COMPLETE.json')):
        raise ValueError('Sample decision source, size, seed or ceiling differs')
    if not 20 <= config['writers'] < population:
        raise ValueError('Corpus E sample must retain at least twenty whole writers and be smaller than the population')
    cov, covplan = completed(inputs['coverage_forecast_root'], coverage_forecast.__name__)
    eff, effplan = completed(inputs['effects_cost_root'], effect_forecast.__name__)
    if decision['coverage_forecast_complete_sha256'] != filehash(cov / 'COMPLETE.json') or decision['effects_cost_complete_sha256'] != filehash(eff / 'COMPLETE.json'):
        raise ValueError('Frozen measured forecast receipts differ')
    pilot_root, pilot_plan = completed(covplan['inputs']['pilot_root'])
    if (pilot_plan['module'] != 'runners.drive.cards.week5_bk_wb1_coverage_pilot' or
            Path(pilot_plan['inputs']['source_root']).resolve() != parent.resolve() or
            effplan['config'] != {'operation': 'cost_reduce'} or
            Path(effplan['inputs']['source_root']).resolve() != parent.resolve()):
        raise ValueError('Measured forecasts refer to a different full population')
    coverage = positive(read(cov / 'output/FORECAST.json')['projected_full_coverage_cpu_seconds'], 'coverage forecast')
    effect = max(positive(read(eff / 'output' / (phase + '_FORECAST.json'))['projected_missing_effect_work_cpu_seconds'],
                          'effects forecast') for phase in ('EXECUTE', 'VERIFY'))
    full, remaining, estimate, charged = budget(decision, coverage, effect)
    return dict(decision_sha256=filehash(inputs['scope_decision']), coverage_forecast_complete_sha256=filehash(cov / 'COMPLETE.json'),
                effects_cost_complete_sha256=filehash(eff / 'COMPLETE.json'), full_projected_cpu_seconds=full,
                projected_sample_cpu_seconds=estimate, sample_budget_cpu_seconds=remaining,
                charged_cpu_seconds=charged, sizing_note=decision['sizing_note'],
                sample_estimate_is_prospective_not_a_new_measurement=True)


def projection(inputs, config):
    if set(config) != {'writers', 'seed', 'trigger'} or type(config['seed']) is not int or config['seed'] != SAMPLE_SEED:
        raise ValueError('Exact frozen whole-writer configuration required')
    parent, manifest, rows = original.load(inputs['source_root'])
    population = len({r['writer'] for r in rows})
    expected = {'source_root'}
    if manifest['config']['mode'] == 'corpus':
        expected |= {'scope_decision', 'coverage_forecast_root', 'effects_cost_root'}
        if config['trigger'] != 'measured_E':
            raise ValueError('Human sample scope requires the measured E trigger')
    elif config['trigger'] != 'constructed_fixture':
        raise ValueError('Constructed validation must be explicit')
    if set(inputs) != expected:
        raise ValueError('Exact full-source and scope-decision inputs required')
    chosen = choose(rows, config['writers'])
    selected = [r for r in rows if r['writer'] in set(chosen)]
    if len({r['session'] for r in rows}) != len(rows):
        raise ValueError('Duplicate original session identity')
    sides = {}
    for row in rows:
        if row['side'] not in ('discovery', 'test') or sides.setdefault(row['writer'], row['side']) != row['side']:
            raise ValueError('Original writer partition is inconsistent')
    decision = measured_decision(inputs, config, parent, population) if manifest['config']['mode'] == 'corpus' else None
    scope = dict(unit='whole_writer', seed=SAMPLE_SEED, selected_writers=chosen, writers=len(chosen),
                 population_writers=population, population_share=len(chosen) / population,
                 sessions=len(selected), population_sessions=len(rows), sample_scoped=len(chosen) < population,
                 writer_side_counts=dict(Counter(sides[w] for w in chosen)),
                 source_complete_sha256=filehash(parent / 'COMPLETE.json'), trigger=config['trigger'],
                 scope='sample-scoped' if len(chosen) < population else 'full population',
                 scientific_admission=False, decision=decision)
    binding = digest(dict(parent_binding=manifest['binding'], scope=scope, config=config))
    return parent, manifest, selected, scope, binding


def run(output, inputs, config, verifying=False):
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    began = time.monotonic()
    if (root / 'YIELD_REQUEST.json').exists():
        return dict(status='yielded', reason='before whole-writer projection')
    parent, full, rows, scope, binding = projection(inputs, config)
    cfg = full['config']
    candidates = stats.candidates([r for r in rows if r['side'] == 'discovery'], cfg['minimum_occurrences'], cfg['minimum_writers'])
    selected_cost = pilot.selection(rows, cfg['sample_denominator'])
    by_session = {r['session']: r for r in rows}
    entries, counts = [], {}
    checked(root / 'BINDING.json', dict(binding=binding), verifying)
    for entry in full['sessions']:
        if entry['session'] not in by_session:
            continue
        if (root / 'YIELD_REQUEST.json').exists() or time.monotonic() - began >= 1200:
            return dict(status='yielded', reason='whole source-session projection boundary')
        descriptor = original.session(parent, full, entry)
        row = by_session[entry['session']]
        if descriptor['writer'] != row['writer'] or descriptor['side'] != row['side']:
            raise ValueError('Original raw writer/side differs from projected row')
        occurrences = list(pilot.occurrences(row, candidates))
        counts[entry['session']] = len(occurrences)
        value = dict(descriptor, binding=binding, cost_selected=entry['session'] in selected_cost,
                     candidate_occurrences=occurrences if entry['session'] in selected_cost else [])
        checked(root / entry['file'], value, verifying, True)
        entries.append(dict(entry, sha256=filehash(root / entry['file']), cost_selected=value['cost_selected'],
                            candidate_occurrences=len(occurrences)))
        atomic(root / 'PROGRESS.json', dict(phase='verify' if verifying else 'scope', sessions=len(entries), total=len(rows)))
    if {r['session'] for r in entries} != set(by_session):
        raise ValueError('Whole-writer projection lost a session')
    checked(root / 'COVERAGE_ROWS.json.gz', rows, verifying, True)
    manifest = dict(config=cfg, binding=binding, rows_sha256=digest(rows), sessions=entries,
                    candidates=[dict(symbols=list(k), **v) for k, v in sorted(candidates.items())],
                    counts=counts, selected_sessions=sorted(selected_cost), writers=scope['writers'],
                    inputs=full['inputs'], scientific_admission=False, source_only=True, sample_scope=scope)
    checked(root / 'SOURCE.json', manifest, verifying)
    write_scope(root, manifest, verifying)
    return dict(verified=True, complete_whole_writer_projection=True) if verifying else dict(status='complete', source_only=True)


def load(path):
    root, plan = completed(path, __name__)
    _, parent, expected_rows, scope, binding = projection(plan['inputs'], plan['config'])
    manifest = read(root / 'output/SOURCE.json')
    rows = gzread(root / 'output/COVERAGE_ROWS.json.gz')
    if (rows != expected_rows or digest(rows) != manifest['rows_sha256'] or manifest['binding'] != binding or
            manifest['sample_scope'] != scope or manifest['config'] != parent['config'] or
            manifest['inputs'] != parent['inputs'] or manifest['writers'] != scope['writers']):
        raise ValueError('Sample source population, binding or configuration changed')
    chosen_sessions = {r['session'] for r in rows}
    expected_sessions = [(r['session'], r['index'], r['file']) for r in parent['sessions'] if r['session'] in chosen_sessions]
    if [(r['session'], r['index'], r['file']) for r in manifest['sessions']] != expected_sessions:
        raise ValueError('Sample descriptor order or original identity changed')
    if manifest['selected_sessions'] != sorted(pilot.selection(rows, parent['config']['sample_denominator'])):
        raise ValueError('Original within-sample cost selection changed')
    write_scope(root / 'output', manifest, True)
    return root, manifest, rows


def write_scope(output, manifest, verifying=False):
    # Identities stay in the private source manifest, not the aggregate sidecar.
    value = {k: v for k, v in manifest['sample_scope'].items() if k != 'selected_writers'}
    checked(Path(output) / 'SAMPLE_SCOPE.json', value, verifying)


def execute(output, inputs, config):
    return timed(run, output, inputs, config, False)


def verify(output, inputs, config):
    return timed(run, output, inputs, config, True)
