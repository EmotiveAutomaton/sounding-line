"""Review-gated complete DC1 primary, prediction and secondary consumer.

DESIGN CHECK: LESSONS 2,3. The owner resolved the next-offer controls as explicit
future-offer adjustment for ratings and contemporaneous opportunity for choices.
These are conditional associations, not causal or rating-time forecasts. Primary and
both repeat references retain separate whole-person banks and unsupported
dispositions. The two primary parts are never replaced by their sum.
"""
from pathlib import Path
import time

import numpy as np

from . import week6_dc1_v2 as math
from . import week6_dc1_source_v1 as source
from . import week6_la6_source_v1 as common
from . import week5_engine_export_io as seal
from . import week5_qualification_io as io
from . import week5_rr3_v1 as compare

MODULE = 'runners.drive.cards.week6_dc1_runner_v2'
PANELS = ('primary_first_play', 'repeat_play_start', 'repeat_best_observed_earlier_score')
PARENT_PINS = {
    'TR1_complete': '8b5906f9723d08985e6bc8fac5bf5d682743082cc9e444f7b40d6a4398badb8e',
    'RR3_complete': '33f8667c70234391dacca838079637b4e85f7118f71756f0bfdc6570c4ddaa1b',
}
CONDITIONAL_SCOPE = ('paired rating/next-choice occasions in the fixed common prospective roster; '
    'running score displayed; conditional associations with future-offer nuisance adjustment for ratings; '
    'no causal effect or deployable rating-time forecast is claimed')


def review_contract(complete_hash):
    return {'admission': 'DC1-timing-and-statistic-v2', 'approved': True,
            'prepared_complete_sha256': complete_hash, 'timing': 'post_trial_k_to_next_choice_k_plus_1',
            'offer_controls': {name: {'rating_time_visibility': 'not asserted',
                                     'choice_time_role': 'known next-choice opportunity',
                                     'rating_model_role': 'explicit future-offer nuisance adjustment'} for name in math.TERMS[:3]},
            'parent_complete_sha256': PARENT_PINS,
            'first_play_primary': True, 'fixed_prospective_TR1_RR3_intersection': True,
            'identical_primary_rating_choice_occasions': True, 'history_through_completed_k_only': True,
            'causal_claim': False, 'deployable_rating_time_forecast': False,
            'math_sha256': io.sha(math.__file__), 'runner_sha256': io.sha(__file__),
            'source_adapter_sha256': io.sha(source.__file__),
            'prediction_convention': 'held-out people; training-only scales; unseen intercept population mean; C1 logistic choices; conditional comparison with eventual opportunity controls'}


def load(inputs):
    if set(inputs) != {'prepared_run', 'owner_review'}:
        raise ValueError('Exact DC1 source and owner timing review required')
    root, _, _ = seal.complete(inputs['prepared_run'], source.MODULE)
    expected = review_contract(io.sha(root / 'COMPLETE.json'))
    review = seal.read(inputs['owner_review'])
    if review != expected:
        raise ValueError('Owner conditional-opportunity review must bind the exact source and implementation')
    result = seal.read(root / 'output' / 'RESULT.json'); path = root / 'output' / 'TABLE.json'
    if result.get('complete_preparation') is not True or result['table_sha256'] != io.sha(path):
        raise ValueError('Complete timing table differs')
    table = seal.read(path)
    if table['timing'] != expected['timing']:
        raise ValueError('Reviewed rating/choice occasion mapping differs')
    if {name: table['source_identity'].get(name) for name in PARENT_PINS} != PARENT_PINS:
        raise ValueError('Exact reviewed TR1/RR3 source completions differ')
    if table['terms'] != list(math.TERMS):
        raise ValueError('All original RR3 terms must remain in the opportunity table')
    common_people = {r['person'] for r in table['person_source_arrays']}
    if len(common_people) != len(table['person_source_arrays']) or len(common_people) != table['roster']['common_people']:
        raise ValueError('Fixed common prospective roster coverage differs')
    if {r['person'] for r in table['rows']} != common_people:
        raise ValueError('Identical primary rating/choice occasions must cover every common person')
    keys = []
    for row in table['rows']:
        k = row['stored_rating_trial']; keys.append((row['person'], k))
        if (row['attempt'] != 1 or not 0 < k < 29 or row['next_choice_trial'] != k + 1
                or row['history_last_trial'] != k or row['controls_requiring_timing_review'] != list(math.TERMS[:3])):
            raise ValueError('Original first-play paired occasion or history boundary differs')
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate primary rating/next-choice occasion')
    return table, {'source_complete': expected['prepared_complete_sha256'], 'table_sha256': result['table_sha256'],
                   'owner_review': review}


def arrays(rows):
    return (np.asarray([r['x'] for r in rows], float), np.asarray([r['rating'] for r in rows], float),
            np.asarray([r['choice'] for r in rows], int), np.asarray([r['person'] for r in rows]))


def person_secondary(table):
    rating_slopes, choice_slopes, excluded = [], [], []
    for row in table['person_source_arrays']:
        a, b = np.asarray(row['TR1_rating_x']), np.asarray(row['TR1_rating_y'])
        x, y = np.asarray(row['choice_x']), np.asarray(row['choice_y'])
        design = np.column_stack((np.ones(len(x)), x))
        if a.std() == 0 or y.std(ddof=1) == 0 or np.linalg.matrix_rank(design) != 10:
            excluded.append({'person': row['person'], 'reason': 'unsupported rating or full-control choice slope'})
            continue
        # TR1's exact original first-play rating slope; all its rating occasions.
        coefficient, _, valid = source.tr1.math.ols(a[None, :], b[None, :])
        if not valid[0]:
            excluded.append({'person': row['person'], 'reason': 'TR1 slope rank failure'}); continue
        beta = np.linalg.lstsq(design, (y - y.mean()) / y.std(ddof=1), rcond=None)[0]
        rating_slopes.append(float(coefficient[0, 1])); choice_slopes.append(float(beta[1 + math.RECENT]))
    admitted = table['source_identity'].get('TR1_primary_interpretable') is True
    primary = table['source_identity'].get('TR1_primary', {})
    stability = primary.get('estimate')
    if not admitted or stability is None or len(rating_slopes) < 3:
        result = {'status': 'unsupported', 'reason': 'TR1 stability gate or complete person-slope support failed'}
    else:
        result = math.corrected_person_correlation(rating_slopes, choice_slopes, stability)
    return {**result, 'supported_people': len(rating_slopes), 'excluded_people': excluded,
            'scope': 'descriptive; fixed parent TR1 correction; parent stability uncertainty not propagated'}


def settings(config):
    if set(config) - {'phase', 'draws', 'max_new_draws', 'max_wall_seconds'} or config.get('phase') != 'DC1' or config.get('draws', 2000) != 2000:
        raise ValueError('Exact complete DC1 two-thousand-draw configuration required')
    count, seconds = config.get('max_new_draws', 100), float(config.get('max_wall_seconds', 600))
    if type(count) is not int or count <= 0 or not np.isfinite(seconds) or not 0 < seconds <= 1200:
        raise ValueError('Positive bounded DC1 draw quantum required')
    return count, seconds


def operation(output, inputs, config):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    limit, seconds = settings(config); began = time.monotonic(); cpu = time.process_time()
    table, identity = load(inputs); binding = common.digest({'identity': identity, 'module': io.sha(__file__)})
    state = seal.state(output / 'PANELS.json', binding, {'panels': {}}); added = 0
    rows_by_panel = {'primary_first_play': table['rows'], 'repeat_play_start': table['repeat_rows']['play_start'],
                     'repeat_best_observed_earlier_score': table['repeat_rows']['best_observed_earlier_score']}
    for name in PANELS:
        if name in state['panels']:
            continue
        if added >= limit or common.requested(output, began, seconds):
            return {'status': 'yielded', 'verified': False, 'phase': 'DC1_panels', 'completed': len(state['panels']), 'total': 3}
        rows = rows_by_panel[name]; people = len({r['person'] for r in rows})
        if people < 2:
            state['panels'][name] = {'status': 'below floor, descriptive', 'people': people, 'reason': 'fewer than two paired people'}
            seal.checkpoint(output / 'PANELS.json', state); continue
        values = arrays(rows); stats = math.sufficient_statistics(*values)
        path = output / name / 'DRAWS.json'; bank = seal.state(path, binding, {'draws': []})
        if 'point' not in bank:
            try:
                bank['point'] = math.from_statistics(stats, np.ones(people))
            except (ValueError, np.linalg.LinAlgError) as error:
                state['panels'][name] = {'status': 'design cannot test', 'reason': str(error), 'people': people}
                seal.checkpoint(output / 'PANELS.json', state); continue
            seal.checkpoint(path, bank)
        while len(bank['draws']) < 2000:
            if added >= limit or common.requested(output, began, seconds):
                return {'status': 'yielded', 'verified': False, 'phase': 'DC1_' + name,
                        'completed': len(bank['draws']), 'total': 2000}
            bank['draws'].append(math.bootstrap_draw(stats, len(bank['draws'])))
            seal.checkpoint(path, bank); added += 1
        state['panels'][name] = math.summarize(bank['point'], bank['draws'], people)
        if name != 'primary_first_play':
            state['panels'][name]['scope'] = 'secondary repeat-play reference; never a second primary'
        seal.checkpoint(output / 'PANELS.json', state)
    if 'prediction' not in state:
        try:
            state['prediction'] = math.prediction_row(*arrays(table['rows']))
        except (ValueError, np.linalg.LinAlgError) as error:
            state['prediction'] = {'status': 'unsupported', 'reason': str(error)}
        state['person_secondary'] = person_secondary(table)
        seal.checkpoint(output / 'PANELS.json', state)
    result = {'card': 'DC1', 'complete_computation': True, 'complete_card': True,
              'record_kind': 'claim', 'theory_tags': ['H17-T1'], 'by_construction': False, 'activation': [],
              'primary': state['panels']['primary_first_play'],
              'repeat_references': {name: state['panels'][name] for name in PANELS[1:]},
              'prediction': state['prediction'], 'person_secondary': state['person_secondary'],
              'source_identity': identity, 'choice_half_is_RR3_replication': True,
              'scope': CONDITIONAL_SCOPE}
    io.write_json(output / 'RESULT.json', result)
    io.write_json(output / 'COST.json', {'process_CPU_seconds': time.process_time() - cpu,
                                       'scope': 'this invocation; full native, source and replay charge external'})
    return result


def execute(output, inputs, config):
    return operation(output, inputs, config)


def verify(output, inputs, config):
    output = Path(output); result = operation(output / 'independent-replay', inputs, config)
    if result.get('status') == 'yielded':
        return result
    compare.compare_record(seal.read(output / 'RESULT.json'), result)
    return {'verified': True, 'all_primary_repeat_prediction_person_fields_replayed': True,
            'replay_kind': 'fresh reconstruction; dense independent estimator oracle is in constructed tests'}
