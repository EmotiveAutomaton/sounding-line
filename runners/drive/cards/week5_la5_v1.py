"""LA5: qualified timing-table projection and subsequent talk-share comparison.

DESIGN CHECK: LESSONS2,3,5; CONTROLS6,7. Hand-computed shares, independent
source formulas, dense fixed-effect oracles and complete whole-meeting replay.
"""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import json
import os
import time
for _key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '2'
import numpy as np
from . import week5_la5_math_v1 as math
from . import week5_la_back_half_source_v2 as source
from . import week5_la_back_half as qualified
from . import week5_engine_export_io as seal
from . import week5_qualification_io as io
from . import timing_p6

MODULE = 'runners.drive.cards.week5_la5_v1'
BAR = .02


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def dependencies():
    modules = (math, source, qualified, seal, io, timing_p6)
    return {Path(m.__file__).as_posix(): io.sha(m.__file__) for m in modules} | {Path(__file__).as_posix(): io.sha(__file__)}


def settings(config):
    allowed = {'phase', 'draws', 'max_new_draws', 'max_wall_seconds'}
    if set(config)-allowed or config.get('phase') not in ('LA5-prepare', 'LA5') or config.get('draws', 2000) != 2000:
        raise ValueError('Exact LA5 preparation or complete 2000-draw analysis required')
    quantum = config.get('max_new_draws', 13 if config['phase'] == 'LA5-prepare' else 100)
    if type(quantum) is not int or quantum <= 0:
        raise ValueError('Positive whole-unit quantum required')
    seconds = float(config.get('max_wall_seconds', 900))
    if not np.isfinite(seconds) or seconds <= 0:
        raise ValueError('Positive bounded time required')
    return {'phase': config['phase'], 'draws': 2000, 'bar': BAR,
        'word_windows': 'start timestamps, left-closed right-open 60 seconds',
        'laugh_window': 'vocal onsets in [act end,act end+2]; two distinct other speakers',
        'join_window': '[first other onset-1, first other onset+3]',
        'model': 'global speaker and meeting effects, minute, act words, distinct other laughers',
        'eligible': 'global person available, both word denominators positive, both full windows within observed span'}


def load_source(inputs):
    if set(inputs) != {'source_run'}:
        raise ValueError('Complete qualified LA4 source-extension h1 required')
    root, plan, _ = seal.complete(inputs['source_run'], 'runners.drive.cards.week5_la_back_half_source_v2')
    if plan['config'].get('mode') != 'metadata' or plan['config'].get('constructed_fixture'):
        raise ValueError('Exact qualified complete metadata/speech extension required')
    original = Path(plan['inputs']['source'])
    pins = plan['config']['source_pins']
    for name in ('ACTS.json.gz', 'LAUGHS.json.gz', 'METADATA.json.gz'):
        if name not in pins or io.sha(original/name) != pins[name]:
            raise ValueError('Original qualified LA table changed')
    identity = {'source_complete': io.sha(root/'COMPLETE.json'), 'source_plan': io.sha(root/'PLAN.json'),
        'original_pins': pins, 'metadata': io.sha(root/'output/METADATA_EXT.json.gz'),
        'speech': io.sha(root/'output/SPEECH.json.gz'), 'implementation': dependencies(),
        'inherited_timing_support': seal.read(root/'output/SUMMARY.json')['speech_counts']}
    return (timing_p6.gzread(original/'ACTS.json.gz'), timing_p6.gzread(original/'LAUGHS.json.gz'),
            timing_p6.gzread(root/'output/SPEECH.json.gz'), timing_p6.gzread(root/'output/METADATA_EXT.json.gz'), identity)


def requested(output, began, seconds):
    return source.requested(Path(output)) or time.monotonic()-began >= seconds


def prepare(output, inputs, config, independent=False):
    output = Path(output); output.mkdir(parents=True, exist_ok=True); semantic = settings(config)
    acts, laughs, speech, metadata, identity = load_source(inputs)
    binding = digest({'semantic': semantic, 'source': identity, 'independent_formula': independent})
    groups = [defaultdict(list) for _ in range(3)]
    for rows, grouped in zip((acts, laughs, speech), groups, strict=True):
        for row in rows:
            if row['meeting'] not in metadata:
                raise ValueError('Prepared row has no qualified meeting metadata')
            grouped[row['meeting']].append(row)
    ordered = sorted(metadata); beginning = time.monotonic(); added = 0; complete_rows = []; totals = Counter()
    for ordinal, meeting in enumerate(ordered):
        path = output/'meetings'/f'{ordinal:04d}.json'
        path.parent.mkdir(exist_ok=True)
        if path.exists():
            block = seal.state(path, binding, {})
            if block['ordinal'] != ordinal or block['meeting'] != meeting:
                raise ValueError('Meeting checkpoint order changed')
        else:
            if added >= config.get('max_new_draws', 13) or requested(output, beginning, config.get('max_wall_seconds', 900)):
                return {'status': 'yielded', 'verified': False, 'phase': 'LA5_meetings', 'completed': ordinal, 'total': len(ordered)}
            began_cpu = time.process_time()
            rows, counts = math.events(groups[0][meeting], groups[1][meeting], groups[2][meeting], metadata[meeting], independent)
            block = {'binding': binding, 'ordinal': ordinal, 'meeting': meeting, 'rows': rows, 'counts': counts}
            seal.checkpoint(path, block); added += 1
            if not (output/'COST_PREFIX.json').exists():
                io.write_json(output/'COST_PREFIX.json', {'first_meeting_CPU_seconds': time.process_time()-began_cpu,
                    'excludes_upstream_IO_and_verification': True, 'meetings_total': len(ordered)})
        complete_rows.extend(block['rows'])
        totals.update({k: v for k, v in block['counts'].items() if type(v) is int})
        io.write_json(output/'PROGRESS.json', {'phase': 'LA5_meetings', 'completed': ordinal+1, 'total': len(ordered)})
    table = {'source_identity': identity, 'semantic': semantic, 'rows': complete_rows}
    seal.checkpoint(output/'EVENTS.json', table)
    result = {'card': 'LA5-source', 'record_kind': 'run', 'theory_tags': [], 'by_construction': False, 'activation': [],
        'complete_preparation': True, 'meetings': len(ordered), 'counts': dict(totals), 'exclusion_categories_may_overlap': True,
        'table_sha256': io.sha(output/'EVENTS.json'), 'source_identity': identity,
        'scope': 'Qualified observed timed words, vocal laugh onsets and acts; no new archive extraction or statistical fitting.'}
    io.write_json(output/'RESULT.json', result)
    return result


def load_prepared(inputs):
    if set(inputs) != {'prepared_run'}:
        raise ValueError('Complete independently replayed LA5 event table required')
    root, plan, _ = seal.complete(inputs['prepared_run'], MODULE)
    if plan['config'].get('phase') != 'LA5-prepare':
        raise ValueError('LA5 event-table phase differs')
    result = seal.read(root/'output/RESULT.json'); path = root/'output/EVENTS.json'
    if result.get('complete_preparation') is not True or result['table_sha256'] != io.sha(path):
        raise ValueError('LA5 complete event table differs')
    table = seal.read(path)
    return table['rows'], {'prepared_complete': io.sha(root/'COMPLETE.json'), 'table': io.sha(path),
                           'source_identity': table['source_identity'], 'implementation': dependencies()}


def summarize(point, values, rows, meetings, *, secondary=False, independent=False):
    eligible = [r for r in rows if r['model_eligible']]
    counts = {'joined': sum(r['joined'] for r in eligible), 'not_joined': sum(not r['joined'] for r in eligible)}
    raw = {}
    for label, joined in [('joined', True), ('not_joined', False)]:
        measured = [r['outcome'] for r in rows if r['joined'] == joined and r['outcome'] is not None]
        raw[label] = {'events': len(measured), 'mean_share_change': float(np.mean(measured)) if measured else None}
    base = {'eligible_counts': counts, 'candidate_events': len(rows), 'meetings': meetings,
        'unadjusted_observed_description_all_nonempty_windows': raw, 'estimate': point, 'bar': BAR}
    if point is None:
        return {**base, 'status': 'design cannot test', 'reason': 'adjusted joined indicator has no identified residual variation', 'draws': 0}
    if meetings < 2:
        return {**base, 'status': 'below floor, descriptive', 'reason': 'one meeting cannot supply population uncertainty',
                'draws': 0, 'interval': None}
    if len(values) != 2000:
        raise ValueError('No interval from an unfinished LA5 bank')
    failed = [i for i, value in enumerate(values) if value is None]
    if failed:
        return {**base, 'status': 'invalid_uncertainty', 'failed_draws': failed, 'draws': 2000}
    interval, se = math.uncertainty(values, independent)
    floor = min(counts.values()) < 300 or meetings < 20
    result = {**base, 'status': 'ok', 'draws': 2000, 'interval': interval, 'bootstrap_SE': se,
        'sees': 2.8*se, 'supports_at': BAR+2.8*se, 'prediction_direction': 'negative',
        'limited_sensitivity': 2.8*se > BAR, 'degenerate_bootstrap': se == 0,
        'approximation': 'normal approximation; optimistic; supports_at is magnitude', 'below_floor_descriptive': floor,
        'interpretation': 'secondary descriptive comparison' if secondary else 'below floor, pooled description' if floor else 'primary adjusted comparison'}
    if not floor and not secondary:
        lo, hi = interval
        result['outcome'] = 'supports' if hi < -BAR else 'against' if lo > BAR else 'band-null' if lo >= -BAR and hi <= BAR else 'inconclusive'
    return result


def analysis(output, inputs, config, independent=False):
    output = Path(output); output.mkdir(parents=True, exist_ok=True); semantic = settings(config)
    rows, identity = load_prepared(inputs); binding = digest({'semantic': semantic, 'source': identity})
    roles = sorted({r['role'] for r in rows if r['corpus'] == 'AMI' and r.get('role')})
    panels = [('AMI', [r for r in rows if r['corpus'] == 'AMI'], False),
              ('ICSI', [r for r in rows if r['corpus'] == 'ICSI'], True)]
    panels += [('AMI-role-'+str(i), [r for r in rows if r['corpus'] == 'AMI' and r['role'] == role], True) for i, role in enumerate(roles)]
    state = seal.state(output/'PANELS.json', binding, {'panels': {}}); began = time.monotonic(); added = 0
    for name, selected, secondary in panels:
        prepared = math.arrays(selected)
        meetings = sorted({r['meeting'] for r in selected if r['model_eligible']})
        path = output/name/'DRAWS.json'; path.parent.mkdir(exist_ok=True)
        panel_binding = digest({'source_binding': binding, 'panel': name, 'rows': selected})
        bank = seal.state(path, panel_binding, {'draws': [], 'failures': {}})
        if 'point' not in bank:
            try:
                bank['point'] = math.estimate(prepared)
            except (np.linalg.LinAlgError, FloatingPointError) as exc:
                bank['point'] = None; bank['point_failure'] = type(exc).__name__
            seal.checkpoint(path, bank)
        if bank['point'] is not None and len(meetings) >= 2:
            while len(bank['draws']) < 2000:
                if added >= config.get('max_new_draws', 100) or requested(output, began, config.get('max_wall_seconds', 900)):
                    seal.checkpoint(path, bank)
                    return {'status': 'yielded', 'verified': False, 'phase': 'LA5_meeting_draws', 'completed': len(bank['draws']), 'total': 2000}
                ordinal = len(bank['draws']); rng = np.random.default_rng(np.random.SeedSequence([20261113, 5, ordinal]))
                weights = np.bincount(rng.integers(0, len(meetings), len(meetings)), minlength=len(meetings))
                cpu = time.process_time()
                try:
                    value = math.estimate(prepared, weights, meetings)
                    if value is None:
                        bank['failures'][str(ordinal)] = 'target absorbed or unsupported resampled variation'
                except (np.linalg.LinAlgError, FloatingPointError) as exc:
                    value = None; bank['failures'][str(ordinal)] = type(exc).__name__
                bank['draws'].append(value); added += 1
                if not (path.parent/'COST_PREFIX.json').exists():
                    io.write_json(path.parent/'COST_PREFIX.json', {'first_meeting_draw_CPU_seconds': time.process_time()-cpu,
                        'panels': len(panels), 'draws_per_supported_panel': 2000, 'excludes_source_and_replay': True})
                if len(bank['draws']) % 10 == 0:
                    seal.checkpoint(path, bank)
                    io.write_json(output/'PROGRESS.json', {'phase': 'LA5_meeting_draws', 'completed': len(bank['draws']), 'total': 2000})
        seal.checkpoint(path, bank)
        state['panels'][name] = summarize(bank['point'], bank['draws'], selected, len(meetings), secondary=secondary, independent=independent)
        if bank.get('point_failure'):
            state['panels'][name].update(status='invalid_computation', reason='numerical fixed-effect failure',
                                        failure=bank['point_failure'])
        seal.checkpoint(output/'PANELS.json', state)
    primary = state['panels']['AMI']
    relation = {'supports': 'with the proposed timing prediction', 'against': 'against the proposed timing prediction'}.get(primary.get('outcome'), 'says nothing decisive about the proposed mapping')
    result = {'card': 'LA5', 'record_kind': 'claim', 'theory_tags': ['H14-mockery'], 'by_construction': False,
        'activation': [{'channel': 'SHAME', 'signal_channel': 'PLAY', 'set_point': 'status, as proposed in the packet',
            'what_moved': 'at least two others laughed after the target act', 'available_action': 'join laughter or change subsequent speaking',
            'observed': primary, 'relation': relation, 'limit': 'Timing does not identify laughter at a person, a feeling, or a biological channel.'}],
        'complete_card': True, 'primary': primary, 'secondary': {k: v for k, v in state['panels'].items() if k != 'AMI'},
        'AMI_role_labels': roles, 'source_binding': binding, 'configuration': semantic,
        'limits': ['Laughter at a remark and at its speaker are not distinguished.', 'Not joining may mean holding the floor, predicting more talk.',
                   'Only qualified timed lexical words are observed; missing-timing counts remain inherited.',
                   'Full-window primary excludes edges of the observed annotation span; all nonempty edge shares remain unadjusted descriptions.',
                   'R13-R15 supporting handoffs absent at build; explicit packet definitions govern.']}
    io.write_json(output/'RESULT.json', result)
    return result


def execute(output, inputs, config):
    settings(config)
    return prepare(output, inputs, config) if config['phase'] == 'LA5-prepare' else analysis(output, inputs, config)


def compare(left, right):
    if isinstance(left, dict):
        if not isinstance(right, dict) or set(left) != set(right):
            raise ValueError('LA5 independent record fields differ')
        for key in left:
            compare(left[key], right[key])
    elif isinstance(left, list):
        if not isinstance(right, list) or len(left) != len(right):
            raise ValueError('LA5 independent vector differs')
        for a, b in zip(left, right, strict=True):
            compare(a, b)
    elif type(left) in (float, int) and type(right) in (float, int):
        if not np.isclose(left, right, atol=1e-9, rtol=0):
            raise ValueError('LA5 independent number differs')
    elif left != right:
        raise ValueError('LA5 independent value differs')


def verify(output, inputs, config):
    output = Path(output); settings(config); path = output/'independent-replay'
    replay = prepare(path, inputs, config, True) if config['phase'] == 'LA5-prepare' else analysis(path, inputs, config, True)
    if replay.get('status') == 'yielded':
        return {**replay, 'verified': False}
    original = seal.read(output/'RESULT.json')
    if config['phase'] == 'LA5-prepare':
        compare(seal.read(output/'EVENTS.json'), seal.read(path/'EVENTS.json'))
        compare(original, replay)
        return {'verified': True, 'all_events_words_windows_and_exclusions_replayed': True, 'independent_interval_count_formula': True}
    compare(original, replay)
    for bank in output.glob('*/DRAWS.json'):
        other = path/bank.relative_to(output)
        compare(seal.read(bank), seal.read(other))
    return {'verified': True, 'all_supported_panels_and_2000_meeting_draws_replayed': True,
            'independent_summary_formula': True, 'qualified_speaker_and_meeting_estimator_reused': True}
