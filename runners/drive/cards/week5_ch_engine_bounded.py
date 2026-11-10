"""Cooperative, resumable CH1 filler over the immutable fixed-node scorer.

DESIGN CHECK: LESSONS 3-5. Both directions retain identical source and engine
pins. An interrupted prefix is not a population result. Exact roster coverage,
fresh engine equality, and unchanged predecessor bytes are separate checks.
No copied verification checkpoint receives independent replay credit.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import time
import chess.engine
from . import week5_ch_engine as original
from .week5_ch_source import digest, write_json


class Scorer(original.Scorer):
    def __init__(self, path, nodes=1000000):
        # Each position has at most two searches. A nonresponsive search fails
        # within 20 seconds, leaving the runtime's 60-second yield grace intact.
        self.engine = chess.engine.SimpleEngine.popen_uci(str(path), timeout=20.)
        self.engine.configure({'Threads': 1, 'Hash': 64})
        self.nodes = nodes


def requested(output):
    output = Path(output)
    request = output / 'YIELD_REQUEST.json'
    if not request.exists():
        return False
    resume = output.parent / 'RESUMED_FROM.json'
    if resume.exists():
        copied = json.loads(resume.read_text(encoding='utf8'))['copied']
        # The sealed predecessor request is retained as evidence. Only its exact
        # hash is stale; a newly written supervisor request still interrupts.
        if copied.get('YIELD_REQUEST.json') == digest(request):
            return False
    return True


def bind(output, inputs, config):
    if set(inputs) != {'positions', 'engine'}:
        raise ValueError('Expected exact roster and engine inputs')
    for spec in inputs.values():
        if digest(spec['path']) != spec['sha256']:
            raise ValueError('CH1 input pin changed')
    allowed = {'offset', 'max_positions', 'nodes', 'wall_seconds',
               'max_new_draws', 'constructed_fixture'}
    if set(config) - allowed:
        raise ValueError('Unknown CH1 configuration')
    offset = config.get('offset', 0)
    maximum = config.get('max_positions', 1024)
    nodes = config.get('nodes', 1000000)
    quantum = config.get('max_new_draws', maximum)
    wall = config.get('wall_seconds', 600)
    if any(isinstance(x, bool) or not isinstance(x, int) for x in (offset, maximum, nodes, quantum)):
        raise ValueError('CH1 bounds must be integers')
    if offset < 0 or not 1 <= maximum <= 1024 or quantum < 1:
        raise ValueError('Invalid CH1 segment or quantum')
    if nodes not in (300000, 1000000, 3000000) or not 0 < wall <= 600:
        raise ValueError('Undeclared node count or wall bound')
    semantic = {k: v for k, v in config.items() if k != 'max_new_draws'}
    binding = dict(inputs=inputs, config=semantic, scorer_sha256=digest(original.__file__),
                   adapter_sha256=digest(__file__))
    write_json(Path(output) / 'BINDING.json', binding)
    rows = []
    for index, row in enumerate(original.iter_positions(inputs['positions']['path'])):
        if index < offset:
            continue
        if len(rows) == maximum:
            break
        rows.append(row)
    if len(rows) != maximum:
        raise ValueError('Segment extends outside frozen roster')
    keys = [original.score_key(row, nodes) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate position in segment')
    return rows, keys, offset, nodes, quantum, float(wall)


def prefix(output, rows, keys, nodes):
    directory = Path(output) / 'PRIVATE_SCORES'
    directory.mkdir(exist_ok=True)
    files = {p.stem: p for p in directory.glob('*.json')}
    if set(files) - set(keys):
        raise ValueError('Score outside declared segment')
    n = len(files)
    if set(files) != set(keys[:n]):
        raise ValueError('Nonconsecutive saved score prefix')
    for row, key in zip(rows[:n], keys[:n]):
        value = json.loads(files[key].read_text(encoding='utf8'))
        if (value['position'] != row or value['node_limit'] != nodes or
                value['threads'] != 1 or value['hash_mb'] != 64):
            raise ValueError('Saved score binding changed')
    return n


def paused(output, operation, completed, total, reason):
    write_json(Path(output) / (operation.upper() + '_CHECKPOINT.json'),
               dict(operation=operation, completed=completed, total=total,
                    reason=reason, population_complete=False), mutable=True)
    return dict(status='yielded', operation=operation, completed=completed,
                total=total, reason=reason, scientific_effect_computed=False)


def execute(output, inputs, config):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    rows, keys, offset, nodes, quantum, wall = bind(output, inputs, config)
    saved = prefix(output, rows, keys, nodes)
    if (output / 'BATCH.json').exists():
        report = json.loads((output / 'BATCH.json').read_text(encoding='utf8'))
        if report['visited_positions'] != saved or report['next_offset'] != offset + saved:
            raise ValueError('Sealed batch interval changed')
        return dict(status='complete', completed=saved, reused_positions=saved,
                    scientific_effect_computed=False)
    start = time.monotonic()
    count = saved
    engines = []
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            while count < len(rows):
                if requested(output):
                    return paused(output, 'execute', count, len(rows), 'owner requested yield')
                if count - saved >= quantum:
                    return paused(output, 'execute', count, len(rows), 'position checkpoint quantum')
                # Ordinary filler wall boundary seals the measured prefix; a
                # later disjoint batch starts at next_offset. Owner pauses instead
                # preserve this same segment for authenticated continuation.
                if time.monotonic() - start >= wall and count > 0:
                    break
                if not engines:
                    engines = [Scorer(inputs['engine']['path'], nodes) for _ in range(2)]
                stop = min(count + 2, len(rows), saved + quantum)
                futures = [pool.submit(engines[i].score, rows[j])
                           for i, j in enumerate(range(count, stop))]
                for j, future in zip(range(count, stop), futures):
                    write_json(output / 'PRIVATE_SCORES' / (keys[j] + '.json'), future.result())
                    count = j + 1
                write_json(output / 'EXECUTE_PROGRESS.json',
                           dict(completed=count, segment_total=len(rows),
                                newly_completed=count-saved, wall_seconds=time.monotonic()-start), mutable=True)
    finally:
        for engine in engines:
            engine.close()
    if not count:
        raise ValueError('Zero-progress engine batch cannot complete')
    report = dict(new_positions=count-saved, reused_positions=saved, visited_positions=count,
                  next_offset=offset+count, node_limit=nodes, population_complete=False,
                  segment_end=offset+len(rows), segment_complete=count == len(rows),
                  constructed_fixture=bool(config.get('constructed_fixture')))
    write_json(output / 'BATCH.json', report)
    return dict(status='complete', completed=count, new_positions=count-saved,
                reused_positions=saved, scientific_effect_computed=False)


def verify(output, inputs, config):
    output = Path(output)
    rows, keys, offset, nodes, _, _ = bind(output, inputs, config)
    count = prefix(output, rows, keys, nodes)
    report = json.loads((output / 'BATCH.json').read_text(encoding='utf8'))
    if report['visited_positions'] != count or report['next_offset'] != offset + count or count < 1:
        raise ValueError('Complete execute boundary required for replay')
    engines = []
    completed = 0
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            for begin in range(0, count, 2):
                if requested(output):
                    return paused(output, 'verify', completed, count, 'owner requested yield')
                if not engines:
                    engines = [Scorer(inputs['engine']['path'], nodes) for _ in range(2)]
                stop = min(begin+2, count)
                futures = [pool.submit(engines[i].score, rows[j])
                           for i, j in enumerate(range(begin, stop))]
                for j, future in zip(range(begin, stop), futures):
                    stored = json.loads((output / 'PRIVATE_SCORES' / (keys[j]+'.json')).read_text(encoding='utf8'))
                    if future.result() != stored:
                        raise ValueError('Fresh-process engine score disagreement')
                    completed += 1
                write_json(output / 'VERIFY_PROGRESS.json',
                           dict(verified_positions=completed, total=count, fresh_from_ordinal_zero=True), mutable=True)
    finally:
        for engine in engines:
            engine.close()
    result = dict(verified_positions=count, all_scores_equal=True,
                  fresh_from_ordinal_zero=True, complete_recalculation=True)
    write_json(output / 'VERIFY.json', result)
    return dict(verified=True, **result)
