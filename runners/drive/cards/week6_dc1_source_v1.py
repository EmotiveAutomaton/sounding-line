"""DC1 parent-authenticated, bounded timing-table preparation without fitting.

DESIGN CHECK: LESSONS 2,3. Authenticate both complete parents, their common raw
source, frozen person rosters and RR3 scales. Persist every rating disposition
and unknown offer-control availability. No outcome regression occurs here.
"""
from pathlib import Path
import time

import numpy as np

from . import week5_tr1 as tr1
from . import week5_rr3_v1 as rr3
from . import week5_engine_export_io as seal
from . import week5_qualification_io as io
from . import week6_dc1_v1 as math
from . import week6_la6_source_v1 as common

MODULE = 'runners.drive.cards.week6_dc1_source_v1'
BLOCK = 128


def supported_tr1_people(data):
    """Reconstruct only the frozen parent full/half-fit membership decision.

    Source-eligible repeat people are not automatically supported TR1 people.
    The original gate has no bridge over an unsupported consecutive pair.
    """
    selected, compact, census = tr1.roster(data)
    x, y, _ = tr1.math.recent_luck(data['plays'][selected])
    _, _, valid = tr1.math.ols(x, y)
    halves = np.stack([tr1.math.ols(x[:, section], y[:, section])[0]
                       for section in (slice(0, 6), slice(6, 12))], axis=1)
    left, right, support = tr1.supported_pairs({'person': compact, 'counter': data['counter'][selected]},
                                               {'valid': valid, 'half': halves})
    members = np.unique(data['person'][selected[np.r_[left, right]]])
    return members, {'source_eligible': census, 'supported_analysis': support}


def tr1_membership(data):
    """Prospective roster stays fixed; realized fit support is a separate fact."""
    selected, _, _ = tr1.roster(data)
    fixed = np.unique(data['person'][selected])
    supported, audit = supported_tr1_people(data)
    return fixed, supported, audit


def load_parents(inputs):
    if set(inputs) != {'tr1_run', 'rr3_run'}:
        raise ValueError('Exact complete TR1 and RR3 parents required')
    tr, tp, _ = seal.complete(inputs['tr1_run'], tr1.MODULE)
    rr, rp, _ = seal.complete(inputs['rr3_run'], rr3.MODULE)
    tresult, rresult = seal.read(tr / 'output' / 'RESULT.json'), seal.read(rr / 'output' / 'RESULT.json')
    if (tresult.get('card') != 'TR1' or rresult.get('card') != 'RR3'
            or tresult.get('complete_computation') is not True or rresult.get('complete_computation') is not True):
        raise ValueError('Both human parent computations must be complete and verified')
    if tp['config'].get('phase') != 'TR1':
        raise ValueError('Frozen TR1 parent phase differs')
    rr3.settings(rp['config'])
    task, tr_identity = tr1.authenticate(tp['inputs'])
    data, rr_selected, census, standing, rr_identity = rr3.load(rp['inputs'])
    if io.sha(task) != rr_identity['upstream']['task']:
        raise ValueError('TR1 and RR3 raw source tasks differ')
    tr_people, tr_supported, tr_audit = tr1_membership(data)
    if tr_audit['supported_analysis'] != tresult['support']:
        raise ValueError('Frozen TR1 supported-pair membership no longer reproduces')
    rr_people = np.unique(data['person'][rr_selected])
    people, roster = math.common_roster(tr_people, rr_people, data['person'])
    # Authenticate the inherited feature scales by their original preparation.
    rebuilt = rr3.prepare(data, np.asarray([], int), census, standing)
    scales = rresult['reference_scales']
    if not np.array_equal(np.asarray(scales), np.asarray(rebuilt['scales'])):
        raise ValueError('Frozen RR3 scales do not reproduce from the same source')
    identity = {'TR1_complete': io.sha(tr / 'COMPLETE.json'), 'RR3_complete': io.sha(rr / 'COMPLETE.json'),
                'TR1_identity': tr_identity, 'RR3_identity': rr_identity,
                'TR1_roster_support': tr_audit, 'RR3_roster_support': census,
                'source_task_sha256': io.sha(task), 'TR1_primary': tresult['primary'],
                'TR1_primary_interpretable': tresult.get('primary_interpretable', False),
                'module_sha256': io.sha(__file__), 'math_sha256': io.sha(math.__file__)}
    prior_indices, prior_scores, excluded = rr3.previous.history.repeat_roster(data)
    data['_dc1_earlier_reference'] = dict(zip(prior_indices.tolist(), prior_scores.tolist()))
    data['_dc1_TR1_supported_people'] = set(tr_supported.tolist())
    identity['repeat_reference_excluded_people'] = excluded
    identity['RR3_parent_informative_participants'] = rresult['primary_panel'].get('informative_participants')
    return data, people, roster, scales, identity


def project_block(data, keys, scales):
    """Prepare every approved primary/repeat occasion and per-person source arrays."""
    selected = np.flatnonzero(np.isin(data['person'], keys) & (data['counter'] == 1))
    rows, audit = math.timing_table(data['plays'][selected], data['person'][selected],
                                   data['counter'][selected], keys, keys, scales)
    tr_x, tr_y, _ = tr1.math.recent_luck(data['plays'][selected])
    choice_x = np.concatenate((math.history.dynamic_features(data['plays'][selected], .65),
                               math.rr3.recent(data['plays'][selected])[:, :, None]), axis=2) / np.asarray(scales)
    persons = [{'person': int(data['person'][index]), 'TR1_rating_x': tr_x[j].tolist(),
                'TR1_rating_y': tr_y[j].tolist(), 'choice_x': choice_x[j, 1:].tolist(),
                'choice_y': data['plays'][index, 1:, 6].tolist(),
                'TR1_parent_supported_pair': int(data['person'][index]) in data.get('_dc1_TR1_supported_people', set())}
               for j, index in enumerate(selected)]
    repeats = {'play_start': [], 'best_observed_earlier_score': []}; dispositions = []
    indices = np.flatnonzero(np.isin(data['person'], keys) & (data['counter'] > 1))
    earlier = data.get('_dc1_earlier_reference', {})
    if any(int(i) not in earlier for i in indices):
        raise ValueError('Common-roster repeat is absent from the frozen earlier-score mapping')
    for attempt in sorted(set(data['counter'][indices].tolist())):
        ii = indices[data['counter'][indices] == attempt]; people = data['person'][ii]
        for name in repeats:
            reference = np.zeros(len(ii)) if name == 'play_start' else np.asarray([earlier[int(i)] for i in ii])
            rr, aa = math.timing_table(data['plays'][ii], people, np.ones(len(ii), int), people, people, scales, reference)
            for row in rr:
                row.update(attempt=int(attempt), reference=name)
            repeats[name].extend(rr)
            dispositions.extend({**row, 'attempt': int(attempt), 'reference': name} for row in aa['dispositions'])
    return {'rows': rows, 'dispositions': audit['dispositions'], 'person_source_arrays': persons,
            'repeat_rows': repeats, 'repeat_dispositions': dispositions}


def settings(config):
    if set(config) - {'phase', 'max_new_blocks', 'max_wall_seconds'} or config.get('phase') != 'DC1-prepare':
        raise ValueError('Exact DC1 timing preparation required')
    limit, seconds = config.get('max_new_blocks', 4), float(config.get('max_wall_seconds', 600))
    if type(limit) is not int or limit <= 0 or not np.isfinite(seconds) or not 0 < seconds <= 1200:
        raise ValueError('Positive bounded source quantum required')
    return limit, seconds


def operation(output, inputs, config):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    limit, seconds = settings(config); began = time.monotonic(); cpu = time.process_time()
    data, people, roster, scales, identity = load_parents(inputs)
    binding = common.digest({'source': identity, 'people': list(map(int, people)), 'scales': scales,
                             'timing': 'post_trial_k_to_next_choice_k_plus_1'})
    state = seal.state(output / 'STATE.json', binding, {'blocks': 0})
    blocks = (len(people) + BLOCK - 1) // BLOCK; added = 0
    for ordinal in range(state['blocks'], blocks):
        if added >= limit or common.requested(output, began, seconds):
            return {'status': 'yielded', 'verified': False, 'phase': 'DC1_timing_projection',
                    'completed': ordinal, 'total': blocks}
        keys = people[ordinal * BLOCK:(ordinal + 1) * BLOCK]
        block = {'binding': binding, 'ordinal': ordinal, 'people': list(map(int, keys)),
                 **project_block(data, keys, scales)}
        seal.checkpoint(output / 'blocks' / f'{ordinal:05d}.json', block)
        state['blocks'] = ordinal + 1; seal.checkpoint(output / 'STATE.json', state); added += 1
    rows, dispositions, person_arrays, repeat_dispositions = [], [], [], []
    repeats = {'play_start': [], 'best_observed_earlier_score': []}
    for ordinal in range(blocks):
        block = seal.state(output / 'blocks' / f'{ordinal:05d}.json', binding, {})
        if block['ordinal'] != ordinal:
            raise ValueError('Timing block ordinal changed')
        rows.extend(block['rows']); dispositions.extend(block['dispositions'])
        person_arrays.extend(block['person_source_arrays']); repeat_dispositions.extend(block['repeat_dispositions'])
        for name in repeats:
            repeats[name].extend(block['repeat_rows'][name])
    table = {'rows': rows, 'dispositions': dispositions, 'roster': roster, 'source_identity': identity,
             'scales': scales, 'terms': list(math.TERMS), 'timing': 'post_trial_k_to_next_choice_k_plus_1',
             'offer_control_availability': {name: 'unknown_at_rating_time' for name in math.TERMS[:3]},
             'person_source_arrays': person_arrays, 'repeat_rows': repeats, 'repeat_dispositions': repeat_dispositions,
             'production_admitted': False, 'hold': math.TIMING_HOLD}
    seal.checkpoint(output / 'TABLE.json', table)
    result = {'card': 'DC1-source', 'record_kind': 'run', 'theory_tags': [], 'by_construction': False,
              'activation': [], 'complete_preparation': True, 'primary_people': len(people),
              'paired_occasions': len(rows), 'all_rating_dispositions': len(dispositions),
              'table_sha256': io.sha(output / 'TABLE.json'), 'source_identity': identity,
              'human_outcome_fit': False, 'production_admitted': False, 'hold': math.TIMING_HOLD}
    io.write_json(output / 'RESULT.json', result)
    io.write_json(output / 'COST.json', {'process_CPU_seconds': time.process_time() - cpu,
                                       'scope': 'this invocation; full native/source/replay charge external'})
    return result


def execute(output, inputs, config):
    return operation(output, inputs, config)


def verify(output, inputs, config):
    output = Path(output); result = operation(output / 'independent-replay', inputs, config)
    if result.get('status') == 'yielded':
        return result
    for name in ('TABLE.json', 'RESULT.json'):
        if seal.read(output / name) != seal.read(output / 'independent-replay' / name):
            raise ValueError('Complete common-roster timing replay differs')
    return {'verified': True, 'all_primary_occasions_and_exclusions_replayed': True,
            'offer_control_availability_remains_held': True, 'human_outcome_fit': False}
