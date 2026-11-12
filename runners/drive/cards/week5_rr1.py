"""RR1: actual-attempt bins of the unchanged qualified MD3 companion handler.

DESIGN CHECK: LESSONS 2-5; CONTROLS 6-7. The fixed cohort has completed actual
attempts 1, 2 and 3, never the first three saved arrays. This is a configured
re-read, not a new estimator; the packet explicitly requires no new fixture.
"""
from pathlib import Path
import hashlib
import json
import os
import time
for _key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '2'
import numpy as np
from . import week5_md3_bounded as study
from . import week5_md3 as history
from . import week5_md12_bounded as bounded
from . import week5_md_analysis as features
from . import week5_md_source_h1 as source
from . import week5_md as core
from . import week5_engine_export_io as sealed
from . import week5_qualification_io as io

MODULE = 'runners.drive.cards.week5_rr1'
REQUIRED_ATTEMPTS = (1, 2, 3)
BINS = ('1', '2', '3', '4+')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def dependencies():
    return {Path(m.__file__).as_posix(): io.sha(m.__file__) for m in
            (study, history, bounded, features, source, core, sealed, io)} | {
                Path(__file__).as_posix(): io.sha(__file__)}


def contract(config):
    allowed = {'phase', 'draws', 'max_new_draws', 'max_wall_seconds', 'participants'}
    if set(config) - allowed or config.get('phase') != 'RR1' or config.get('draws', 2000) != 2000:
        raise ValueError('RR1 uses the declared complete 2000-draw MD3 handler')
    if int(config.get('max_new_draws', 100)) <= 0 or float(config.get('max_wall_seconds', 900)) <= 0:
        raise ValueError('Positive operational bounds are required')
    sample = config.get('participants')
    if sample is not None and (type(sample) is not int or sample <= 0):
        raise ValueError('A prospectively frozen sample must be a positive whole-person count')
    return {'phase': 'RR1', 'draws': 2000, 'participants': sample,
            'cohort': 'completed actual attempts 1,2,3', 'bins': list(BINS),
            'references': ['play_start', 'best_observed_earlier_score']}


def authenticate(inputs):
    if set(inputs) != {'source_run', 'md3_run'}:
        raise ValueError('Exact repaired source and complete MD3 parent required')
    sr, _, _ = sealed.complete(inputs['source_run'], 'runners.drive.cards.week5_md_source_h1')
    mr, mp, _ = sealed.complete(inputs['md3_run'], 'runners.drive.cards.week5_md3_bounded')
    task = sr / 'output/task.npz'
    if Path(mp['inputs']['task']).resolve() != task.resolve():
        raise ValueError('RR1 and MD3 must use the same original repaired source')
    provenance = sealed.read(sr / 'output/SOURCE.json')
    if (provenance['version'] != 'MD-source.h1' or provenance['archive_sha256'] != source.ZIP_SHA
            or provenance['mat_sha256'] != source.MAT_SHA or provenance['task_sha256'] != io.sha(task)
            or sealed.read(sr / 'output/VERIFIED.json').get('verified') is not True):
        raise ValueError('Exact original source with complete every-array replay required')
    parent = sealed.read(mr / 'output/RESULT.json')
    if parent.get('complete_computation') is not True or parent['primary']['gamma'] != .65:
        raise ValueError('Completed MD3 with its frozen forgetting factor required')
    return task, parent, {'source_complete': io.sha(sr/'COMPLETE.json'),
        'md3_complete': io.sha(mr/'COMPLETE.json'), 'task': io.sha(task),
        'implementation': dependencies()}


def roster(data, sample=None):
    person = np.asarray(data['person']); counter = np.asarray(data['counter'])
    eligible = np.asarray(data['repeat_eligible'], bool)
    if not (len(person) == len(counter) == len(eligible)):
        raise ValueError('Repaired source support mask differs')
    if not np.isfinite(counter).all() or np.any(counter <= 0) or np.any(counter != np.floor(counter)):
        raise ValueError('Source attempted-play counters must be positive integers')
    order = np.lexsort((counter, person))
    starts = np.flatnonzero(np.r_[True, np.diff(person[order]) != 0]) if len(order) else []
    groups = np.split(order, starts[1:]) if len(order) else []
    counts = {'source_people': len(groups), 'source_saved_plays': len(person),
        'at_least_three_saved_people': 0, 'at_least_three_saved_plays': 0,
        'fewer_than_three_saved_people': 0, 'ambiguous_history_people_excluded': 0,
        'missing_required_actual_counter_people': 0,
        'missing_actual_attempt_people': {str(k): 0 for k in REQUIRED_ATTEMPTS}}
    accepted = []
    for ii in groups:
        if len(ii) < 3:
            counts['fewer_than_three_saved_people'] += 1
            continue
        counts['at_least_three_saved_people'] += 1
        counts['at_least_three_saved_plays'] += len(ii)
        missing = [k for k in REQUIRED_ATTEMPTS if k not in counter[ii]]
        for k in missing:
            counts['missing_actual_attempt_people'][str(k)] += 1
        counts['missing_required_actual_counter_people'] += bool(missing)
        ambiguous = not eligible[ii].all()
        counts['ambiguous_history_people_excluded'] += ambiguous
        if missing or ambiguous:
            continue
        if np.any(np.diff(counter[ii]) <= 0):
            raise ValueError('Qualified repeat source contains conflicting attempted-play counters')
        accepted.append(ii)
    counts['fixed_cohort_people_before_sample'] = len(accepted)
    if sample is not None and sample < len(accepted):
        selected = np.sort(np.random.default_rng(core.SEED).permutation(len(accepted))[:sample])
        accepted = [accepted[int(i)] for i in selected]
    indices = np.concatenate(accepted).astype(int) if accepted else np.array([], int)
    counts['fixed_cohort_people'] = len(accepted)
    counts['fixed_cohort_saved_plays'] = len(indices)
    counts['missing_later_attempt_records'] = sum(int(np.sum(np.diff(counter[ii])-1)) for ii in accepted)
    counts['four_plus_people'] = sum(bool(np.any(counter[ii] >= 4)) for ii in accepted)
    counts['four_plus_unobserved_people'] = len(accepted) - counts['four_plus_people']
    counts['exclusion_categories_may_overlap'] = True
    return indices, counts


def approximation(result, path, bar):
    if result.get('status') != 'ok':
        return result
    with np.load(path/'bootstrap.npz', allow_pickle=False) as saved:
        values = saved['values']
    if values.shape != (2000, 3) or not np.isfinite(values).all():
        raise ValueError('Every intended MD3 draw is required before interval reporting')
    se = values.std(axis=0, ddof=1)
    return {**result, 'bootstrap_SE_lower_upper_contrast': se.tolist(),
        'sees_lower_upper_contrast': (2.8*se).tolist(),
        'supports_at_lower_upper_contrast': (bar+2.8*se).tolist(),
        'limited_sensitivity_lower_upper_contrast': (2.8*se > bar).tolist(),
        'degenerate_bootstrap_lower_upper_contrast': (se == 0).tolist(),
        'normal_approximation_is_optimistic': True, 'inherited_MD3_bar': bar,
        'interpretation': 'descriptive configured re-read; no prior verdict changes'}


def run(output, inputs, config):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    semantic = contract(config)
    task, parent, identity = authenticate(inputs)
    binding = digest({'semantic': semantic, 'source': identity})
    state = sealed.state(output/'PANELS.json', binding, {'panels': {}})
    if not (output/'PANELS.json').exists():
        sealed.checkpoint(output/'PANELS.json', state)
    data = features.load_verified(task)
    selected, census = roster(data, semantic['participants'])
    gamma = float(parent['primary']['gamma']); bar = float(parent['primary']['bar'])
    # Exactly the original repeat-companion scaling: global first-play covariates
    # and the original first-play common standing SD, never bin-specific scaling.
    raw_first = features.dynamic_features(data['first'], gamma)
    scale = raw_first.reshape(-1, 8).std(axis=0, ddof=1).clip(1e-10)
    scale[3:5] = parent['primary']['standing_sd']
    if not np.isfinite(scale).all() or np.any(scale <= 0):
        raise ValueError('Original MD3 reference scaling invalid')
    prior_indices, prior_scores, _ = history.repeat_roster(data)
    earlier = dict(zip(prior_indices.tolist(), prior_scores.tolist()))
    count = data['counter'][selected]
    for label in ('play_start', 'best_observed_earlier_score'):
        for number, bin_name in enumerate(BINS, 1):
            name = label + '-attempt-' + bin_name.replace('+', 'plus')
            if name in state['panels']:
                if state['panels'][name].get('status') == 'ok':
                    saved = output/name/'bootstrap.npz'
                    if io.sha(saved) != sealed.read(saved.with_suffix('.sha256.json'))['sha256']:
                        raise ValueError('Completed RR1 panel checkpoint changed')
                continue
            if bounded.wants_yield(study.CLOCK):
                raise bounded.YieldRequested({'status': 'yielded', 'phase': 'RR1_panels',
                    'completed': len(state['panels']), 'total': 8, 'verified': False})
            ii = selected[(count == number) if number < 4 else (count >= 4)]
            support = {'saved_plays': len(ii), 'people': int(len(np.unique(data['person'][ii])))}
            if label == 'best_observed_earlier_score' and number == 1:
                fitted = {'status': 'not_applicable', 'reason': 'no observed earlier play at actual attempt 1'}
            elif not len(ii):
                fitted = {'status': 'unsupported', 'reason': 'no eligible saved plays in this actual-attempt bin'}
            else:
                reference = np.zeros(len(ii)) if label == 'play_start' else np.array([earlier[int(i)] for i in ii])
                xx = features.dynamic_features(data['plays'][ii], gamma, reference) / scale
                fitted = study.bootstrap_panel(xx.reshape(-1, 8), data['plays'][ii, :, 6].ravel(),
                    np.repeat(data['person'][ii], 30), list(range(8)), output/name, 2000,
                    36 if label == 'play_start' else 37)
                fitted = approximation(fitted, output/name, bar)
            state['panels'][name] = {**fitted, **support, 'actual_attempt_bin': bin_name,
                'reference': label, 'below_floor_descriptive': (support['people'] < 20 or
                    fitted.get('informative_participants', support['people']) < 20)}
            sealed.checkpoint(output/'PANELS.json', state)
            io.write_json(output/'PROGRESS.json', {'phase': 'RR1_panels', 'completed': len(state['panels']), 'total': 8})
    result = {'card': 'RR1', 'record_kind': 'claim', 'theory_tags': ['H12-T6'],
        'by_construction': False, 'complete_computation': True, 'census': census,
        'configuration': semantic, 'gamma': gamma, 'standing_SD': float(scale[3]),
        'panels': state['panels'], 'cohort_constant_for_actual_attempts_1_2_3': True,
        'four_plus_scope': 'observed fourth-or-later attempts within the fixed cohort; not all cohort members return',
        'reference_scope': 'best observed earlier completed score; missing attempt scores remain unobserved',
        'scope': 'descriptive game-score re-read; not direct social security; no existing verdict changes',
        'controls': 'unchanged qualified MD3 handler and inherited calibration; no new fixture per packet',
        'binding': binding}
    io.write_json(output/'RESULT.json', result)
    return result


def execute(output, inputs, config):
    output = Path(output); contract(config); old_clock = study.CLOCK
    study.CLOCK = bounded.clock_state(output, dict(config, max_new_draws=config.get('max_new_draws', 100)))
    started = time.process_time()
    try:
        with io.publication([(core, 'save_json')]):
            try:
                result = run(output, inputs, config)
            except bounded.YieldRequested as pause:
                result = {**pause.receipt, 'verified': False}
        io.write_json(output/'COST.json', {'process_CPU_seconds': time.process_time()-started,
            'status': result.get('status', 'complete'), 'all_reentry_and_verification_costs_charge': True})
        return result
    finally:
        study.CLOCK = old_clock


def verify(output, inputs, config):
    output = Path(output)
    result = execute(output/'independent-replay', inputs, config)
    if result.get('status') == 'yielded':
        return {**result, 'verified': False}
    if result != sealed.read(output/'RESULT.json'):
        raise ValueError('RR1 complete independent configured replay differs')
    for path in sorted(output.glob('*/bootstrap.npz')):
        relative = path.relative_to(output)
        with np.load(path, allow_pickle=False) as a, np.load(output/'independent-replay'/relative, allow_pickle=False) as b:
            if set(a.files) != set(b.files):
                raise ValueError('RR1 independent checkpoint inventory differs')
            for key in a.files:
                equal = np.array_equal(a[key], b[key], equal_nan=True) if np.issubdtype(a[key].dtype, np.number) else np.array_equal(a[key], b[key])
                if not equal:
                    raise ValueError('RR1 every-draw independent replay differs')
    return {'verified': True, 'every_required_panel_and_draw_replayed': True,
            'missing_counter_exclusions_replayed': True}
