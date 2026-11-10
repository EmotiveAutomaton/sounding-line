"""Checkpointed LA1 preparation with the original eight-act rows and order.

DESIGN CHECK: this changes execution boundaries only. It never selects a
reader, truncates a context, selects a meeting sample or reads model scores.
Input-file decoding and one-meeting label construction remain atomic units
whose real timing/peak memory must be measured before source admission.
"""
from collections import Counter, defaultdict
from pathlib import Path
import math
import os
import time

from .week5_la import labelled_acts
from .week5_at_scoring import digest
from .timing_census import read, filehash
from .timing_p6 import gzread, gzip_equal, write_equal, progress

CORE = {
    'week5_la.py': '75072eeff47f0559edca1e63681b49feae58cb82502d6f8d4b457c9d52ecdca7',
    'week5_la_pipeline_v3.py': '624ffcd5b849c11d23763217790f0ead4c7db0c6d61e4e66090497902e7040fa',
    'week5_la_pipeline_v4.py': 'b360973f174d87a9f193881a72ff33779b57521f7e217557d71feea56f566b7f',
}
SCIENCE_KEYS = {'operation', 'card', 'corpus', 'history_acts', 'window', 'left',
                'label', 'laugh_scope', 'others_only'}
BOUND_KEYS = {'max_wall_seconds', 'max_new_blocks'}
COUNT_KEYS = {'acts', 'supported_history', 'insufficient_prior_history',
              'insufficient_completed_history'}


def require(value, message):
    if not value:
        raise ValueError(message)


def configuration(config):
    require(set(config) <= SCIENCE_KEYS | BOUND_KEYS, 'Unknown source-preparation configuration')
    require(config.get('card') == 'LA1' and config.get('operation', 'prepare') == 'prepare',
            'Only unchanged LA1 source preparation is supported')
    semantic = dict(card='LA1', corpus=config.get('corpus', 'both'),
                    history_acts=config.get('history_acts', 5), window=config.get('window', 2.),
                    left=config.get('left', 1.), label=config.get('label', 'vocal'),
                    laugh_scope=config.get('laugh_scope', 'others' if config.get('others_only', False) else 'all'))
    require(semantic['corpus'] in ('AMI', 'ICSI', 'both'), 'Unregistered corpus')
    require(semantic['history_acts'] in (3, 5, 10) and
            (semantic['left'], semantic['window']) in ((1., 1.), (1., 2.), (1., 3.), (5., 5.)),
            'Unregistered source history/window')
    require(semantic['label'] in ('vocal', 'vocal_and_speech') and
            semantic['laugh_scope'] in ('all', 'own', 'others'), 'Unregistered laugh support')
    wall, blocks = config.get('max_wall_seconds', 600), config.get('max_new_blocks', 32)
    require(type(wall) in (float, int) and math.isfinite(wall) and 0 < wall <= 1200,
            'Positive source quantum no greater than 1200 seconds required')
    require(type(blocks) is int and blocks > 0, 'Positive integral new-block bound required')
    return semantic, float(wall), blocks


def bound_source(inputs, semantic):
    require(set(inputs) == {'source_root'}, 'Only the original completed source is an input')
    source = Path(inputs['source_root']).resolve()
    done = read(source / 'COMPLETE.json')
    require(done.get('status') == 'COMPLETE' and done.get('fresh_process_verified') is True,
            'Completed independently verified source required')
    for name, expected in CORE.items():
        require(filehash(Path(__file__).parent / name) == expected, 'Original LA numerical/source code changed')
    for name in ('ACTS.json.gz', 'LAUGHS.json.gz', 'METADATA.json.gz'):
        require('output/' + name in done['outputs'], 'Source completion omits required data')
    binding = dict(source_root=str(source), source_complete_sha256=filehash(source / 'COMPLETE.json'),
                   semantic_config=semantic, original_core=CORE,
                   implementation_sha256=filehash(__file__))
    return source, done, binding


def initial_state():
    return dict(cursor=[0, 0], counts={}, buffer=[], batches=[])


def validate_state(state):
    require(set(state) == {'cursor', 'counts', 'buffer', 'batches'}, 'Checkpoint state shape changed')
    require(type(state['cursor']) is list and len(state['cursor']) == 2 and
            all(type(x) is int and x >= 0 for x in state['cursor']), 'Invalid source cursor')
    counts = state['counts']
    require(set(counts) <= COUNT_KEYS and all(type(v) is int and v >= 0 for v in counts.values()),
            'Invalid cumulative source counters')
    require(counts.get('acts', 0) == sum(v for k, v in counts.items() if k != 'acts'),
            'Source support counters do not partition processed acts')
    require(type(state['buffer']) is list and len(state['buffer']) < 8, 'Invalid partial source block')
    total = len(state['buffer'])
    for i, item in enumerate(state['batches']):
        require(set(item) == {'file', 'rows', 'sha256'} and
                item['file'] == f'batches/acts-{i:06d}.json.gz' and type(item['rows']) is int and
                0 < item['rows'] <= 8 and (i == len(state['batches']) - 1 or item['rows'] == 8),
                'Source block sequence or cardinality changed')
        total += item['rows']
    require(total == counts.get('supported_history', 0), 'Supported rows differ from checkpoint population')


def restore(root, phase, binding):
    directory = root / 'checkpoints' / phase
    seals = sorted(directory.glob('*.seal.json')) if directory.exists() else []
    if directory.exists():
        expected_data = {f'{i:06d}.json.gz' for i in range(len(seals))}
        actual_data = {p.name for p in directory.glob('*.json.gz')}
        require(expected_data <= actual_data and
                actual_data <= expected_data | {f'{len(seals):06d}.json.gz'},
                'Unexpected checkpoint data or a missing sealed state')
    previous_hash = None
    state = initial_state()
    for i, seal_path in enumerate(seals):
        require(seal_path.name == f'{i:06d}.seal.json', 'Checkpoint sequence has a gap')
        seal = read(seal_path)
        data_path = directory / f'{i:06d}.json.gz'
        require(seal == dict(file=data_path.name, sha256=filehash(data_path),
                             previous_seal_sha256=previous_hash, binding=digest(binding)),
                'Checkpoint data, source binding or chain changed')
        data = gzread(data_path)
        require(set(data) == {'binding', 'phase', 'state'} and data['binding'] == binding and data['phase'] == phase,
                'Checkpoint operation or semantic binding changed')
        current = data['state']
        validate_state(current)
        require(tuple(current['cursor']) >= tuple(state['cursor']) and
                current['batches'][:len(state['batches'])] == state['batches'] and
                all(current['counts'].get(k, 0) >= v for k, v in state['counts'].items()),
                'Checkpoint moved backward or replaced completed work')
        previous_hash, state = filehash(seal_path), current
    # Completed earlier blocks are immutable even when this invocation resumes
    # after them. Native checkpoint copies additionally authenticate every byte.
    for item in state['batches']:
        require(filehash(root / item['file']) == item['sha256'], 'Retained source block changed')
    return state, len(seals), previous_hash


def checkpoint(root, phase, binding, state, sequence, previous_hash):
    validate_state(state)
    directory = root / 'checkpoints' / phase
    data = directory / f'{sequence:06d}.json.gz'
    gzip_equal(data, dict(binding=binding, phase=phase, state=state))
    seal = directory / f'{sequence:06d}.seal.json'
    write_equal(seal, dict(file=data.name, sha256=filehash(data),
                           previous_seal_sha256=previous_hash, binding=digest(binding)))
    return sequence + 1, filehash(seal)


def interrupted(root, began, wall):
    return (root / 'YIELD_REQUEST.json').exists() or time.monotonic() - began >= wall


def prepare(root, inputs, config, verifying=False):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    semantic, wall, block_limit = configuration(config)
    source, done, binding = bound_source(inputs, semantic)
    write_equal(root / 'PREPARATION_BINDING.json', binding)
    phase = 'verify' if verifying else 'execute'
    began = time.monotonic()
    state, sequence, previous_hash = restore(root, phase, binding)
    initial_acts, initial_blocks = state['counts'].get('acts', 0), len(state['batches'])

    def pause(where):
        nonlocal sequence, previous_hash
        sequence, previous_hash = checkpoint(root, phase, binding, state, sequence, previous_hash)
        progress(root / 'PROGRESS.json', dict(phase=phase, boundary=where, processed_acts=state['counts'].get('acts', 0),
                                            complete_blocks=len(state['batches']), pending_rows=len(state['buffer'])))
        return dict(status='yielded', reason='authenticated LA source quantum at ' + where,
                    phase=phase, new_processed_acts=state['counts'].get('acts', 0) - initial_acts,
                    new_complete_blocks=len(state['batches']) - initial_blocks)

    if interrupted(root, began, wall):
        return pause('before source authentication')
    for name, expected in done['outputs'].items():
        path = (source / name).resolve()
        path.relative_to(source)
        require(filehash(path) == expected, 'Source completed output changed')
        if interrupted(root, began, wall):
            return pause('source file authentication')
    loaded = {}
    for name in ('METADATA', 'LAUGHS', 'ACTS'):
        loaded[name] = gzread(source / 'output' / (name + '.json.gz'))
        if interrupted(root, began, wall):
            return pause('source file decoding')
    acts, laughs, metadata = loaded['ACTS'], loaded['LAUGHS'], loaded['METADATA']
    corpus, scope = semantic['corpus'], semantic['laugh_scope']
    if semantic['label'] == 'vocal':
        laughs = [e for e in laughs if e['label'] == 'vocal']
    if corpus != 'both':
        keep = {m for m, value in metadata.items() if value['corpus'] == corpus}
        acts = [a for a in acts if a['meeting'] in keep]
        laughs = [e for e in laughs if e['meeting'] in keep]
        metadata = {m: value for m, value in metadata.items() if m in keep}
    groups, events = defaultdict(list), defaultdict(list)
    for a in acts:
        groups[a['meeting']].append(a)
    for e in laughs:
        events[e['meeting']].append(e)
    meetings = sorted(groups)
    require(state['cursor'][0] <= len(meetings) and
            (state['cursor'][0] < len(meetings) or state['cursor'][1] == 0), 'Cursor exceeds source meetings')
    counts = Counter(state['counts'])

    def flush():
        rows = state['buffer']
        name = f'batches/acts-{len(state["batches"]):06d}.json.gz'
        if verifying:
            require(gzread(root / name) == rows, 'Independent original source-row replay differs')
        else:
            # A write interrupted before a checkpoint is adopted only if a
            # fresh reconstruction is byte/value equal; it is never deleted.
            gzip_equal(root / name, rows)
        state['batches'].append(dict(file=name, rows=len(rows), sha256=filehash(root / name)))
        state['buffer'] = []

    for ordinal in range(state['cursor'][0], len(meetings)):
        if interrupted(root, began, wall):
            state['counts'] = dict(counts)
            return pause('before meeting label construction')
        meeting = meetings[ordinal]
        labelled = labelled_acts(groups[meeting], events[meeting], semantic['window'], semantic['left'], scope == 'others')
        if scope == 'own':
            for act in labelled:
                act['laughed_after'] = act['own_laugh']
        start = state['cursor'][1] if ordinal == state['cursor'][0] else 0
        require(start < len(labelled), 'Cursor exceeds the current meeting')
        # Stable sorting inside the original label helper preserves exact
        # input order for ties. No completed act from another meeting enters.
        previous = labelled[:start]
        for position in range(start, len(labelled)):
            if interrupted(root, began, wall):
                state['counts'] = dict(counts)
                return pause('before next source act')
            act = labelled[position]
            counts['acts'] += 1
            if len(previous) >= semantic['history_acts']:
                completed = [p for p in previous if p['end'] <= act['start']]
                if len(completed) >= semantic['history_acts']:
                    state['buffer'].append(dict(act, previous=' '.join(p['text'] for p in completed[-semantic['history_acts']:]),
                                                causal_prefix=' '.join(p['text'] for p in completed) + ' ', target=act['text']))
                    counts['supported_history'] += 1
                    if len(state['buffer']) == 8:
                        flush()
                else:
                    counts['insufficient_completed_history'] += 1
            else:
                counts['insufficient_prior_history'] += 1
            previous.append(act)
            state['cursor'] = [ordinal, position + 1] if position + 1 < len(labelled) else [ordinal + 1, 0]
            state['counts'] = dict(counts)
            if len(state['batches']) - initial_blocks >= block_limit and state['cursor'][0] < len(meetings):
                return pause('sealed complete eight-act block')
    if state['buffer']:
        flush()
    summary = dict(card='LA1', corpus=corpus, history_acts=semantic['history_acts'],
                   window=semantic['window'], left=semantic['left'], counts=dict(counts),
                   meetings=len(metadata), source_sha256=filehash(source / 'COMPLETE.json'))
    if verifying:
        require(read(root / 'BATCHES.json') == state['batches'] and read(root / 'SUMMARY.json') == summary,
                'Independent complete source index or summary differs')
    else:
        write_equal(root / 'BATCHES.json', state['batches'])
        write_equal(root / 'SUMMARY.json', summary)
    # Extra/unindexed score inputs can never silently enlarge the source bank.
    require({p.name for p in (root / 'batches').glob('*.json.gz')} ==
            {Path(r['file']).name for r in state['batches']}, 'Unexpected or missing source batch')
    checkpoint(root, phase, binding, state, sequence, previous_hash)
    if verifying:
        return dict(verified=True, complete_source_projection=True, independent_checkpointed_replay=True,
                    newly_replayed_acts=counts.get('acts', 0) - initial_acts)
    return dict(status='complete', card='LA1', scientific_admission=False,
                new_processed_acts=counts.get('acts', 0) - initial_acts)


def call(output, inputs, config, verifying=False):
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    cpu, wall, stamp = time.process_time(), time.monotonic(), time.time_ns()
    result, error = None, None
    try:
        result = prepare(root, inputs, config, verifying)
        return result
    except BaseException as exc:
        error = type(exc).__name__
        raise
    finally:
        write_equal(root / 'invocation_costs' / f'{os.getpid()}-{stamp}.json',
                    dict(phase='verify' if verifying else 'execute', error_class=error,
                         process_cpu_seconds=time.process_time() - cpu, wall_seconds=time.monotonic() - wall,
                         result=result, native_all_attempt_accounting_authoritative=True))


def execute(output, inputs, config):
    return call(output, inputs, config)


def verify(output, inputs, config):
    return call(output, inputs, config, True)
