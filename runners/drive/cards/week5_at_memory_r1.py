"""Prospective R1 memory envelope; no scientific scoring changes.

DESIGN CHECK: LESSONS 3-5. Completed native receipts, not forecasts or partial
chunks, establish peaks. Missing/tampered evidence refuses in either scientific
direction. Unobserved readers retain the six-GiB post-load commit floor.
"""
from pathlib import Path
import json, math, struct
from .timing_census import read, filehash
from .week5_at_precision_guard import LIMITS as ORIGINAL_LIMITS

GIB = 2**30


def positive(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError('Finite positive memory quantity required')
    return value


def envelope(float64_weight_bytes, private_peaks=(), working_set_peaks=(), legacy_start_GiB=26):
    positive(float64_weight_bytes)
    if legacy_start_GiB not in (26, 28):
        raise ValueError('Only the original reader start limits are admitted')
    private = [positive(x) for x in private_peaks]
    working = [positive(x) for x in working_set_peaks]
    if private:
        peak, factor, basis = max(private), 1.25, 'completed_private_commit'
    elif working:
        peak, factor, basis = max(working), 1.5, 'completed_working_set'
    else:
        peak, factor, basis = float64_weight_bytes, 2.5, 'unobserved_float64_weights'
    declared = math.ceil(factor * peak / (.5 * GIB)) * (.5 * GIB)
    start = declared + 7 * GIB
    if basis == 'unobserved_float64_weights':
        start = max(declared + 6 * GIB, min(start, legacy_start_GiB * GIB))
    limits = dict(ORIGINAL_LIMITS, start_commit_bytes=int(start), start_ram_bytes=int(declared + 8 * GIB))
    return dict(basis=basis, multiplier=factor, observed_peak_bytes=peak,
                declared_peak_bytes=int(declared), limits=limits)


def weight_bytes(manifest):
    """Count stored tensor elements from authenticated headers; never load weights."""
    total = 0
    files = [(Path(p), digest) for p, digest in manifest['files'].items() if p.endswith('.safetensors')]
    if not files:
        raise ValueError('Authenticated safetensors weights required')
    for path, digest in files:
        if filehash(path) != digest:
            raise ValueError('Model weight bytes changed')
        with path.open('rb') as stream:
            prefix = stream.read(8)
            if len(prefix) != 8:
                raise ValueError('Missing safetensors header')
            size = struct.unpack('<Q', prefix)[0]
            if not 0 < size <= 16 * 2**20:
                raise ValueError('Invalid safetensors header size')
            header = json.loads(stream.read(size))
        for key, value in header.items():
            if key == '__metadata__':
                continue
            shape = value['shape']
            if any(type(x) is not int or x < 0 for x in shape):
                raise ValueError('Invalid stored tensor shape')
            total += math.prod(shape) * 8
    return positive(total)


def profile(path, manifest_path, config):
    value = read(path)
    manifest_sha = filehash(manifest_path)
    if value.get('schema') != 'AT-R1-memory-v1' or value.get('model_manifest_sha256') != manifest_sha:
        raise ValueError('Memory profile model binding differs')
    context = dict(context=config.get('context', 'final'), context_length=config.get('context_length', 1024))
    if value.get('condition') != context:
        raise ValueError('Memory profile scoring condition differs')
    private, working, evidence = [], [], []
    seen = set()
    for item in value['completed_guard_receipts']:
        root = Path(item['root']).resolve()
        terminal = root / 'COMPLETE.json'
        if filehash(terminal) != item['complete_sha256']:
            raise ValueError('Completed memory evidence changed')
        done = read(terminal)
        if done.get('status') != 'COMPLETE' or done.get('fresh_process_verified') is not True:
            raise ValueError('Partial chunk cannot supply a completed memory peak')
        plan_path = root / 'PLAN.json'
        if done['outputs'].get('PLAN.json') != filehash(plan_path):
            raise ValueError('Memory evidence plan is not sealed')
        plan = read(plan_path)
        if filehash(plan['inputs']['model_manifest']) != manifest_sha:
            raise ValueError('Different reader in memory evidence')
        if {k: plan['config'].get(k, default) for k, default in [('context', 'final'), ('context_length', 1024)]} != context:
            raise ValueError('Different scoring condition in memory evidence')
        relative = item['guard_relative']
        guard = (root / relative).resolve(); guard.relative_to(root)
        if guard in seen or guard.parent != root / 'output' or not guard.name.startswith('GUARD_'):
            raise ValueError('Invalid or repeated native guard receipt')
        seen.add(guard)
        if done['outputs'].get(relative) != filehash(guard):
            raise ValueError('Memory guard receipt is not sealed')
        measured = read(guard)
        native = measured.get('identity', {})
        if measured.get('status') != 'returned' or measured.get('phase') not in ('execute', 'verify') or type(native.get('pid')) is not int or native['pid'] <= 0 or not native.get('creation_time') or not native.get('executable'):
            raise ValueError('Completed owned native guard evidence required')
        working.append(positive(measured['peak_working_set_bytes']))
        if 'peak_private_commit_bytes' in measured:
            private.append(positive(measured['peak_private_commit_bytes']))
        evidence.append(dict(complete_sha256=item['complete_sha256'], guard_sha256=filehash(guard), guard_relative=relative))
    manifest = read(manifest_path)
    # Exact original owner gate from week5_at_admission_prepare, not a guess
    # from a model's display name or its family.
    legacy = 28 if manifest['model'] == 'EleutherAI/pythia-1.4b-deduped' else 26
    result = envelope(weight_bytes(manifest), private, working, legacy)
    return dict(result, model_manifest_sha256=manifest_sha, profile_sha256=filehash(path), condition=context, evidence=evidence)
