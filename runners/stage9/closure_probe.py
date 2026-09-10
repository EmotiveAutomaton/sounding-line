"""Actual CPU denial probe for an exact queue-bound reader package.

DESIGN CHECK: B03/I03/X02; LESSONS 3--5, CONTROLS 6--7.
NULL: unknown runtime, changed materializer/copied source, absent native denials,
or altered sentinel cannot produce an isolation gate. ALTERNATIVE: the declared
runtime denies each forbidden action under its original copied package and a
completed reentry never executes another probe. CPU only; no model inference.
"""
import argparse
import hashlib
import importlib
from pathlib import Path
import time

from .common import REPO, ROOT, Units, digest, file_hash, freeze, read
from .queue import inside, verify_sources, writer
from .revision_predictions import finish, reentry, sources
from .training_jobs import cell_identity

# Explicitly reviewed materializers, never inferred from an output path or plugin.
RUNTIMES = {
    'reader': 'runners.stage9.runtime',
    'baseline_matrix': 'runners.stage9.baseline_matrix_runtime',
    'revision': 'runners.stage9.revision_runtime',
    'record': 'runners.stage9.record_runtime',
    'commit': 'runners.stage9.commit_runtime',
    'broll': 'runners.stage9.broll_runtime',
    'repair': 'runners.stage9.repair_runtime',
    'kernel': 'runners.stage9.kernel_runtime',
    'inference': 'runners.stage9.inference_runtime',
    'mark': 'runners.stage9.mark_runtime',
    'comparison': 'runners.stage9.comparison_runtime',
}


def bindings(runtime, source):
    if runtime not in RUNTIMES:
        raise ValueError('unreviewed capsule runtime')
    module = importlib.import_module(RUNTIMES[runtime])
    originals = (module.SOURCES if runtime != 'reader' else {
        'reader/worker.py': 'runners/stage9/reader.py', 'reader/readout.py': 'runners/readout_repair.py',
        'reader/features.py': 'runners/stage9/features.py'})
    host = RUNTIMES[runtime].replace('.', '/') + '.py'
    owner = 'runners/stage7/runtime.py'
    transport = 'runners/stage9/capsule_host.py'
    for path in set(originals.values()) | {host, owner, transport}:
        if source['files'].get(path) != file_hash(REPO / path):
            raise ValueError('runtime or original copied source differs from the manifest')
    from runners.stage7.runtime import BOOTSTRAP
    copied = {destination: source['files'][path] for destination, path in originals.items()}
    copied['bootstrap.py'] = hashlib.sha256(BOOTSTRAP.encode('utf-8')).hexdigest()
    copied['reader/__init__.py'] = hashlib.sha256(b'').hexdigest()
    return {'runtime': runtime, 'module': RUNTIMES[runtime], 'runtime_sha256': source['files'][host],
            'transport_sha256': source['files'][transport],
            'bootstrap_owner_sha256': source['files'][owner], 'original_paths': originals,
            'copied_sources': copied, 'copied_sources_sha256': digest(copied)}


def run(directory, manifest_path, runtime, scope):
    from .closure_capsules import denial_probe
    start, cpu = time.monotonic(), time.process_time()
    directory, manifest_path = map(inside, (directory, manifest_path))
    plan = read(manifest_path); verify_sources(plan['sources']); cell = cell_identity()
    own = [j for j in plan['jobs'] if digest({'manifest_sha256': digest(plan), 'job': j}) == cell]
    if (scope not in ('pilot', 'scientific') or not directory.is_relative_to(ROOT / 'private' / ('closure-probe-' + scope))
            or plan['kind'] != ('prelaunch_rehearsal' if scope == 'pilot' else 'science')
            or len(own) != 1 or own[0]['module'] != 'runners.stage9.closure_probe'
            or own[0]['resource'] != 'cpu' or own[0]['role'] != 'work'
            or (REPO / own[0]['produces']).resolve() != directory / 'COMPLETE.json'):
        raise ValueError('probe must belong to its actual CPU queue job and scope')
    binding = bindings(runtime, plan['sources'])
    identity = {'cell_identity': cell, 'operation': 'queue-bound-capsule-probe-v1', 'scope': scope,
                'source': sources(), 'manifest_sha256': digest(plan), 'binding_sha256': digest(binding)}
    with writer(directory):
        Units(directory, identity); prior = reentry(directory, identity)
        if prior is not None:
            denial_probe(read(directory / 'PROBE.json'), binding['copied_sources'])
            return prior
        freeze(directory / 'SENTINEL.json', {'purpose': 'existing-file isolation fixture; preserve bytes'})
        sentinel_sha = file_hash(directory / 'SENTINEL.json')
        task = {'probe': True, 'forbidden_paths': [str(directory / 'SENTINEL.json')], 'other_port': 65534}
        module = importlib.import_module(binding['module'])
        result = module.execute(None, task=task, root=directory / 'capsules')
        freeze(directory / 'PROBE.json', result)  # Failed probes are retained before validation.
        inspection = denial_probe(result, binding['copied_sources'])
        if file_hash(directory / 'SENTINEL.json') != sentinel_sha:
            raise ValueError('probe changed its forbidden existing file')
        freeze(directory / 'BINDING.json', binding)
        freeze(directory / 'INSPECTION.json', inspection)
        return finish(directory, identity, start, cpu,
                      ['SENTINEL.json', 'PROBE.json', 'BINDING.json', 'INSPECTION.json', 'capsules'],
                      isolation_probe_verified=True, denial_attempts=inspection['attempts'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for key in ('output', 'manifest'):
        parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--runtime', choices=tuple(RUNTIMES), required=True)
    parser.add_argument('--scope', choices=('pilot', 'scientific'), required=True)
    args = parser.parse_args()
    run(args.output, args.manifest, args.runtime, args.scope)
