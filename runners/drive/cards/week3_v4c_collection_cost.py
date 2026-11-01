"""Complete collection I/O timing, with scientific aggregation kept uncomputed.

DESIGN CHECK: LESSONS 3-5 reread 2026-11-01. Under NULL and ALTERNATIVE,
all shard identities, physical hashes and every reference must verify. Missing,
mixed or altered inputs refuse. Timing does not admit science or enlarge a cap.
The unchanged summary algorithm is timed on constructed known answers only.
Fresh-process verification repeats the whole workload, not a sampled fraction.
"""
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
import time

from runners.stage14.common import read, freeze, filehash
from . import week3_v4c_mc_collect_compressed as collector
from . import week3_v4c_mc_compressed as full
from . import week3_v4c_storage as storage


def fixture(root):
    """Four complete tiny shards exercise actual compressed I/O and refusals."""
    root = Path(root)
    cells = full.source.roster()[:4]
    inputs = {}
    for i, cell in enumerate(cells):
        r = root / str(i)
        config = dict(full.CONFIG, shard_index=i)
        freeze(r/'PLAN.json', dict(module=full.__name__, config=config,
                                   inputs={'constructed': 'fixed'}))
        freeze(r/'VERIFIED.json', dict(full_fresh_generation_and_refit=True))
        freeze(r/'output/BINDING.json', dict(code={'constructed': 'fixed'}))
        freeze(r/'output/STORAGE_BINDING.json', full.storage_binding())
        world = dict(cell=cell, reference_count=199, probability=1., detected=False)
        base = r/'output/worlds'/full.source.world_name(cell)
        freeze(base/'OBSERVED.json', dict(likelihood_ratio=0.))
        freeze(base/'RESULT.json', world)
        for j in range(199):
            storage.freeze(base/f'null-{j:03d}.json',
                           dict(statistic={'likelihood_ratio': 0.}))
        freeze(r/'output/SUMMARY.json', dict(config=config, worlds=[world]))
        freeze(r/'output/XZ_MANIFEST.json', full.physical_manifest(r/'output'))
        outputs = {p.relative_to(r).as_posix(): filehash(p)
                   for p in sorted(r.rglob('*.json')) if p.name != 'COMPLETE.json'}
        freeze(r/'COMPLETE.json', dict(status='COMPLETE', fresh_process_verified=True,
                                      synthetic_fixture_only=True, outputs=outputs))
        inputs[f'shard{i}'] = str(r/'COMPLETE.json')
    return inputs, cells


def measure(inputs, constructed=False):
    if set(inputs) != {f'shard{i}' for i in range(4)}:
        raise ValueError('All four shards required')
    for p in inputs.values():
        if bool(read(p).get('synthetic_fixture_only', False)) != constructed:
            raise ValueError('Constructed/source scope mismatch')
    actual_roster = full.source.roster()
    expected = 4 if constructed else 110
    reads = 0
    original_read = storage.read

    def counted_read(path):
        nonlocal reads
        value = original_read(path)
        if storage.reference(path):
            reads += 1
        return value

    def coverage_only(worlds):
        if len(worlds) != expected:
            raise ValueError('Incomplete collection coverage')
        # This callback deliberately never accesses probabilities or detections.
        return dict(worlds=len(worlds), references_per_world=199)

    started = time.process_time()
    with ExitStack() as stack:
        if constructed:
            stack.enter_context(patch.object(full.source, 'roster', lambda: actual_roster[:4]))
        stack.enter_context(patch.object(storage, 'read', counted_read))
        stack.enter_context(patch.object(full, 'full_summary', coverage_only))
        proof = collector.gather(inputs, collector.CONFIG)
    io_cpu = time.process_time() - started
    if reads != expected * 199:
        raise ValueError('Complete reference decoding required')
    # Conservative summary allowance: run all three fixed known-answer patterns,
    # including both gate states, rather than summarize actual shard outcomes.
    started = time.process_time()
    for pattern in range(3):
        worlds = []
        for i, cell in enumerate(actual_roster):
            hit = pattern == 1 or (pattern == 2 and i % 2 == 0)
            worlds.append(dict(cell=cell, reference_count=199,
                               probability=.005 if hit else 1., detected=hit))
        full.full_summary(worlds)
    summary_cpu = time.process_time() - started
    return dict(proof=proof, references_decoded=reads, constructed=constructed,
                io_cpu_seconds=io_cpu, constructed_summary_cpu_seconds=summary_cpu,
                measured_pass_cpu_seconds=io_cpu+summary_cpu,
                includes_full_physical_hashing=True, actual_scientific_summary_computed=False)


def run(output, inputs, config):
    if config not in ({'mode': 'constructed'}, {'mode': 'cost'}):
        raise ValueError('Fixed cost or constructed mode required')
    constructed = config['mode'] == 'constructed'
    if constructed:
        if inputs:
            raise ValueError('Constructed mode has no source inputs')
        inputs, _ = fixture(Path(output)/'fixture')
    return measure(inputs, constructed)


def execute(output, inputs, config):
    result = run(output, inputs, config)
    freeze(Path(output)/'SUMMARY.json', result)
    return result


def verify(output, inputs, config):
    result = run(output, inputs, config)
    saved = read(Path(output)/'SUMMARY.json')
    for key in ('proof', 'references_decoded', 'constructed',
                'includes_full_physical_hashing', 'actual_scientific_summary_computed'):
        if result[key] != saved[key]:
            raise ValueError('Fresh full cost replay differs: '+key)
    freeze(Path(output)/'REPLAY_COST.json', result)
    return dict(verified=True, cost_only=True,
                full_physical_hashing_and_decoding_replayed=True,
                actual_scientific_summary_computed=False,
                projected_collection_cpu_seconds=1.5*(saved['measured_pass_cpu_seconds']+
                                                       result['measured_pass_cpu_seconds']+10))
