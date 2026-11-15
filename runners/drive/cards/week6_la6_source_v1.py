"""LA6 all-utterance source adapter, preserving the qualified original parser.

DESIGN CHECK: LESSONS 2,3. Reuse the pinned laugh-label rule, not LA1's
history-truncated scoring population. Early utterances survive with empty
history. Every source byte and every reconstructed meeting is replayed.
"""
from collections import defaultdict
from pathlib import Path
import hashlib
import json
import time

from . import week5_la_prepare_v1 as original
from . import week5_la as labels
from . import week5_engine_export_io as seal
from . import week5_qualification_io as io
from . import timing_p6
from . import week6_la6_v1 as math

MODULE = 'runners.drive.cards.week6_la6_source_v1'
SEMANTIC = {'card': 'LA6', 'all_original_utterances': True, 'corpus': 'both',
            'label': 'vocal', 'laugh_scope': 'all', 'window': 2., 'left': 1.,
            'matching_seconds': 30., 'control_replacement': True}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def load_source(inputs):
    source, complete, inherited = original.bound_source(inputs, SEMANTIC)
    pins = {}
    for name in ('ACTS', 'LAUGHS', 'METADATA'):
        relative = 'output/' + name + '.json.gz'
        path = source / relative
        path.resolve().relative_to(source)
        expected = complete['outputs'][relative]
        if path.is_symlink() or io.sha(path) != expected:
            raise ValueError('Original qualified source table changed')
        pins[name] = expected
    loaded = {name: timing_p6.gzread(source / 'output' / (name + '.json.gz')) for name in pins}
    identity = {'inherited_source': inherited, 'table_pins': pins,
                'module_sha256': io.sha(__file__), 'math_sha256': io.sha(math.__file__)}
    return loaded['ACTS'], loaded['LAUGHS'], loaded['METADATA'], identity


def project_meeting(acts, laughs):
    """No history-count filter: even a first utterance with an empty text survives."""
    events = [event for event in laughs if event['label'] == 'vocal']
    rows = labels.labelled_acts(acts, events, window=2., left=1., others_only=False)
    table, audit = math.matched_table(rows, events)
    features = math.feature_rows(rows, events)
    if len(features) != len(acts):
        raise ValueError('All original utterances must survive feature preparation')
    return {'table': table, 'audit': audit, 'all_utterance_features': list(features.values()),
            'source_utterances': len(acts), 'source_vocal_events': len(events)}


def settings(config):
    if set(config) - {'phase', 'max_new_meetings', 'max_wall_seconds'} or config.get('phase') != 'LA6-prepare':
        raise ValueError('Exact all-utterance LA6 preparation configuration required')
    count, seconds = config.get('max_new_meetings', 8), config.get('max_wall_seconds', 600)
    if type(count) is not int or count <= 0 or not 0 < float(seconds) <= 1200:
        raise ValueError('Positive bounded preparation quantum required')
    return count, float(seconds)


def requested(output, began, seconds):
    return time.monotonic() - began >= seconds or any((p / 'YIELD_REQUEST.json').exists() for p in [output, *output.parents[:3]])


def operation(output, inputs, config, independent=False):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    limit, seconds = settings(config); began = time.monotonic(); cpu = time.process_time()
    acts, laughs, metadata, identity = load_source(inputs)
    groups, events = defaultdict(list), defaultdict(list)
    for act in acts:
        if act['meeting'] not in metadata:
            raise ValueError('Original utterance has no meeting metadata')
        groups[act['meeting']].append(act)
    for event in laughs:
        events[event['meeting']].append(event)
    binding = digest({'semantic': SEMANTIC, 'source': identity})
    state = seal.state(output / 'STATE.json', binding, {'meetings': []})
    meetings = sorted(groups); added = 0
    if state['meetings'] != meetings[:len(state['meetings'])]:
        raise ValueError('Meeting checkpoint order differs')
    for ordinal, meeting in enumerate(meetings):
        path = output / 'meetings' / f'{ordinal:05d}.json'
        if ordinal < len(state['meetings']):
            seal.state(path, binding, {})
            continue
        if added >= limit or requested(output, began, seconds):
            return {'status': 'yielded', 'verified': False, 'phase': 'LA6_all_utterance_preparation',
                    'completed': ordinal, 'total': len(meetings)}
        block = {'binding': binding, 'meeting': meeting, **project_meeting(groups[meeting], events[meeting])}
        seal.checkpoint(path, block)
        state['meetings'].append(meeting); seal.checkpoint(output / 'STATE.json', state); added += 1
    rows, audit, total = [], [], 0
    for ordinal, meeting in enumerate(meetings):
        block = seal.state(output / 'meetings' / f'{ordinal:05d}.json', binding, {})
        if block['meeting'] != meeting:
            raise ValueError('Meeting checkpoint identity differs')
        rows.extend(block['table']); audit.append({'meeting': meeting, **block['audit']})
        total += block['source_utterances']
    if total != len(acts):
        raise ValueError('Source population does not reconcile')
    table = {'rows': rows, 'audit': audit, 'source_identity': identity, 'semantic': SEMANTIC}
    seal.checkpoint(output / 'TABLE.json', table)
    result = {'card': 'LA6-source', 'record_kind': 'run', 'theory_tags': [], 'by_construction': False,
              'activation': [], 'complete_preparation': True, 'all_original_utterances': total,
              'meetings': len(meetings), 'matched_pairs': len(rows) // 2,
              'table_sha256': io.sha(output / 'TABLE.json'), 'source_identity': identity,
              'scientific_admission': False}
    io.write_json(output / 'RESULT.json', result)
    io.write_json(output / 'COST.json', {'process_CPU_seconds': time.process_time() - cpu,
                                       'scope': 'this invocation; source IO and replay charged externally'})
    return result


def execute(output, inputs, config):
    return operation(output, inputs, config)


def verify(output, inputs, config):
    output = Path(output)
    result = operation(output / 'independent-replay', inputs, config, True)
    if result.get('status') == 'yielded':
        return result
    for name in ('TABLE.json', 'RESULT.json'):
        if seal.read(output / name) != seal.read(output / 'independent-replay' / name):
            raise ValueError('Complete all-utterance source replay differs')
    return {'verified': True, 'complete_original_utterance_replay': True, 'human_outcomes_fitted': False}
