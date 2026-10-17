"""Storage-only recovery of the frozen, complete Phase 0 calibration grid.

DESIGN CHECK: LESSONS 3-5 reread 2026-10-16. NULL: changed, corrupt, incomplete
or out-of-order checkpoints refuse reuse; a live or unexpectedly failed prior
worker refuses preparation. ALTERNATIVE: byte-exact gzip round trips preserve
every field, and resumed scratch output equals the original complete pipeline.
The full fixed grid remains required. No scientific admission or new calls.
"""
import os
for _n in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_n] = '1'
import argparse
import gzip
import hashlib
import json
import threading
import time
import traceback
import uuid
from pathlib import Path
import numpy as np
from runners.stage14.common import REPO, read, freeze, atomic, pins, check_pins, filehash, now, limits, canonical
from runners.stage9.process_identity import native_identity
from runners.next_round.queue import resource_snapshot, require_resources
from . import v1_phase0_v2 as original

ROOT = REPO / 'results/phase_2_4_stage_15/raw/drive-v1-phase0-v3'
PRIOR = original.ROOT
FILES = ('CONSTRUCTION.json', 'PREDICTIONS.json', 'FITS.json', 'RESULT.json')
META_RESERVE = 16 * 1024**2
EXPECTED_PRIOR_PLAN = 'b70903aedbfbc9662030f6b841bf89671c8a88d7ce12c278c3966ff6bba24847'


def read_gzip(path):
    return json.loads(gzip.decompress(Path(path).read_bytes()).decode('utf-8'))


def retain_bytes(path, raw, root, ceiling):
    """Deterministic, atomic, lossless storage; never replace an existing record."""
    packed = gzip.compress(raw, compresslevel=6, mtime=0)
    if gzip.decompress(packed) != raw:
        raise ValueError('compression round trip')
    path = Path(path)
    if path.exists():
        if path.read_bytes() != packed:
            raise ValueError('immutable compressed record changed')
    else:
        used = sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
        if used + len(packed) + META_RESERVE > ceiling:
            raise RuntimeError('output byte ceiling')
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
        try:
            with temp.open('xb') as stream:
                stream.write(packed)
                stream.flush()
                os.fsync(stream.fileno())
            # Only this claimed worker writes here. Windows rename also refuses
            # an already existing destination rather than replacing evidence.
            temp.rename(path)
        finally:
            if temp.exists():
                temp.unlink()
    return dict(raw_sha256=hashlib.sha256(raw).hexdigest(), raw_bytes=len(raw),
                stored_sha256=filehash(path), stored_bytes=path.stat().st_size)


def retain_json(path, value, root, ceiling):
    return retain_bytes(path, (canonical(value) + '\n').encode('utf-8'), root, ceiling)


def prior_terminal(prior):
    owner = read(prior / 'OWNER.json')
    if native_identity(owner['native']['pid']) == owner['native']:
        raise ValueError('predecessor is live')
    if (prior / 'COMPLETE.json').exists() or (prior / 'MONITOR_FAILED.json').exists():
        raise ValueError('predecessor requires separate review')
    terminal = read(prior / 'FAILED.json')
    if terminal.get('status') != 'FAILED' or terminal.get('reason') != 'output byte ceiling':
        raise ValueError('unexpected predecessor terminal')
    return owner, terminal


def checkpoint_prefix(prior, grid):
    """Only a contiguous, complete prefix; never select by outcome or silently heal corruption."""
    prefix = []
    gap = False
    for i, cell in enumerate(grid):
        folder = prior / 'worlds' / f'{i:03d}'
        if not (folder / 'RESULT.json').exists():
            gap = True
            continue
        if gap:
            raise ValueError('noncontiguous completed worlds')
        if any(not (folder / name).is_file() for name in FILES):
            raise ValueError('incomplete completed checkpoint')
        if read(folder / 'RESULT.json').get('cell') != cell or read(folder / 'CONSTRUCTION.json').get('cell') != cell:
            raise ValueError('checkpoint cell identity')
        prefix.append(dict(world=i, files={name: filehash(folder / name) for name in FILES}))
    if not prefix or len(prefix) >= len(grid):
        raise ValueError('no partial complete prefix to recover')
    return prefix


def verify_checkpoint(folder, cell, sessions, base, covariates):
    """Rebuild construction and all saved statistics, without refitting or reporting scores."""
    generated, truth, trace = original.construct(sessions, base, covariates, **original.cell_without_replicate(cell))
    if read(folder / 'CONSTRUCTION.json') != dict(cell=cell, rows=trace):
        raise ValueError('construction replay mismatch')
    predictions = read(folder / 'PREDICTIONS.json')
    keys = [r['key'] for r in predictions]
    source = {r['key']: r for s in generated for r in s['rows']}
    if len(keys) != len(set(keys)) or set(keys) != set(source):
        raise ValueError('prediction support mismatch')
    for row in predictions:
        src = source[row['key']]
        if row['truth'] != src['handling'] or row['writer'] != src['writer']:
            raise ValueError('prediction construction mismatch')
        for prob in row['probabilities'].values():
            p = np.asarray(prob, float)
            if p.shape != (4,) or not np.isfinite(p).all() or (p < 0).any() or not np.isclose(p.sum(), 1, atol=1e-12, rtol=0):
                raise ValueError('invalid checkpoint probabilities')
    fits = read(folder / 'FITS.json')
    expected = [s['session'] for s in sorted(sessions, key=lambda s: (s['timestamp'], s['session'])) if s['rows']]
    if [f['session'] for f in fits] != expected:
        raise ValueError('fit session support mismatch')
    result = dict(cell=cell, **original.score_world(predictions, truth, base))
    if read(folder / 'RESULT.json') != result:
        raise ValueError('checkpoint score replay mismatch')
    return result


def prepare():
    if (ROOT / 'PLAN.json').exists() or (ROOT / 'ATTEMPT.claim').exists():
        raise ValueError('existing recovery attempt')
    owner, terminal = prior_terminal(PRIOR)
    old = read(PRIOR / 'PLAN.json')
    if filehash(PRIOR / 'PLAN.json') != EXPECTED_PRIOR_PLAN or owner['plan_sha256'] != EXPECTED_PRIOR_PLAN:
        raise ValueError('unreviewed predecessor plan')
    check_pins(old['pins'])
    if old['grid'] != original.GRID or old['runtime'] != original.runtime():
        raise ValueError('grid or runtime changed')
    from datetime import datetime
    # Charge the predecessor's entire lifetime against computation time. This
    # deliberately overcounts its waits; recovery cannot reset the 20-hour cap.
    elapsed = (datetime.fromisoformat(terminal['at']) - datetime.fromisoformat(owner['at'])).total_seconds()
    remaining = old['max_wall_seconds'] - max(0, elapsed)
    if remaining <= 0:
        raise ValueError('aggregate computation ceiling exhausted')
    prefix = checkpoint_prefix(PRIOR, old['grid'])
    paths = [REPO / p for p in old['pins']] + [PRIOR / n for n in ('PLAN.json', 'OWNER.json', 'FAILED.json')]
    paths += [REPO / p for p in ('runners/drive/v1_phase0_v3.py', 'tests/test_drive_v1_v3.py',
                                'docs/design/stage-15/drive/V1_PHASE0_V3.md')]
    for checkpoint in prefix:
        paths += [PRIOR / 'worlds' / f"{checkpoint['world']:03d}" / n for n in FILES]
    freeze(ROOT / 'PLAN.json', dict(at=now(), pins=pins(paths), grid=old['grid'], reuse=prefix,
        predecessor=PRIOR.relative_to(REPO).as_posix(), predecessor_lifetime_seconds=elapsed,
        max_wall_seconds=remaining, max_resource_wait_seconds=old['max_resource_wait_seconds'],
        max_output_bytes=old['max_output_bytes'], runtime=old['runtime'], compression='gzip-6-mtime0',
        model_calls=0, provider_calls=0, scientific_admission=False, whole_grid_required=True))


def compute(plan, guard, root=ROOT, prior=PRIOR, phase=original.PHASE):
    sessions = read(phase / 'prepared/SESSIONS.json')
    base = {r['key']: r['probabilities']['B-pop'] for r in read(phase / 'T0c/PREDICTIONS.json')}
    covariates = original.content_covariates(sessions)
    freeze(root / 'COVARIATES.json', covariates)
    inventory = {}
    results = []
    for i, cell in enumerate(plan['grid']):
        guard(dict(world=i, worlds=len(plan['grid']), phase='verify_reuse' if i < len(plan['reuse']) else 'construct'))
        folder = root / 'worlds' / f'{i:03d}'
        if i < len(plan['reuse']):
            checkpoint = plan['reuse'][i]
            if checkpoint['world'] != i:
                raise ValueError('reuse order changed')
            source = prior / 'worlds' / f'{i:03d}'
            for name in FILES:
                if filehash(source / name) != checkpoint['files'][name]:
                    raise ValueError('reused bytes changed')
            result = verify_checkpoint(source, cell, sessions, base, covariates)
            for name in FILES:
                raw = (source / name).read_bytes()
                if hashlib.sha256(raw).hexdigest() != checkpoint['files'][name]:
                    raise ValueError('reused bytes changed during retention')
                target = folder / (name + '.gz')
                inventory[target.relative_to(root).as_posix()] = retain_bytes(target, raw, root, plan['max_output_bytes'])
        else:
            generated, truth, trace = original.construct(sessions, base, covariates, **original.cell_without_replicate(cell))
            target = folder / 'CONSTRUCTION.json.gz'
            inventory[target.relative_to(root).as_posix()] = retain_json(target, dict(cell=cell, rows=trace), root, plan['max_output_bytes'])
            predictions, fits = original.fit_world(generated, lambda n, total: guard(dict(world=i, worlds=len(plan['grid']), sessions=n, total_sessions=total)))
            result = dict(cell=cell, **original.score_world(predictions, truth, base))
            for name, value in (('PREDICTIONS.json', predictions), ('FITS.json', fits), ('RESULT.json', result)):
                target = folder / (name + '.gz')
                inventory[target.relative_to(root).as_posix()] = retain_json(target, value, root, plan['max_output_bytes'])
        results.append(result)
    if len(results) != len(plan['grid']) or len(inventory) != 4 * len(plan['grid']):
        raise ValueError('incomplete grid')
    # Identical aggregation to v2.compute; scratch equivalence tests compare the
    # entire summary, predictions, fits and constructions, including reentry.
    recovery = []
    for effect in sorted({r['cell']['effect'] for r in results}):
        for delta in sorted({r['cell']['delta'] for r in results if r['cell']['effect'] == effect}):
            rr = [r for r in results if r['cell']['effect'] == effect and r['cell']['delta'] == delta]
            k = sum(r['recovered'] for r in rr)
            recovery.append(dict(effect=effect, delta=delta, recovered=k, worlds=len(rr), rate=k/len(rr), wilson95=original.wilson(k, len(rr)),
                conditional_interval_coverage=sum(r['interval_covers_conditional_target'] for r in rr)/len(rr),
                observed_minus_expected_quantiles=np.quantile([r['observed_minus_expected'] for r in rr], [.025, .5, .975]).tolist()))
    freeze(root / 'INVENTORY.json', inventory)
    freeze(root / 'SUMMARY.json', dict(curve=results, recovery=recovery, all_worlds_complete=True, other_V1_arms_run=False, scientific_admission=False))


def run():
    limits()
    plan = read(ROOT / 'PLAN.json')
    check_pins(plan['pins'])
    prior_terminal(PRIOR)
    if original.runtime() != plan['runtime'] or plan['grid'] != original.GRID:
        raise ValueError('runtime or grid changed')
    require_resources(resource_snapshot())
    with (ROOT / 'ATTEMPT.claim').open('x', encoding='utf8') as f:
        f.write(now() + '\n')
    freeze(ROOT / 'OWNER.json', dict(at=now(), native=native_identity(), plan_sha256=filehash(ROOT / 'PLAN.json')))
    start = time.monotonic()
    stop = threading.Event()
    lease = REPO / 'results/.cpu.lock'
    token = f'{os.getpid()} drive-v1-phase0-v3'.encode()
    owned = False
    def hard():
        if stop.wait(plan['max_wall_seconds'] + plan['max_resource_wait_seconds'] + 90):
            return
        atomic(ROOT / 'FAILED.json', dict(status='FAILED', at=now(), reason='hard finite ceiling'))
        os._exit(124)
    threading.Thread(target=hard, daemon=True).start()
    try:
        while not (ROOT / 'MONITOR_READY.json').exists():
            if time.monotonic() - start > 90:
                raise TimeoutError('monitor handshake')
            time.sleep(.25)
        if read(ROOT / 'MONITOR_READY.json')['owner_sha256'] != filehash(ROOT / 'OWNER.json'):
            raise ValueError('monitor binding')
        while True:
            require_resources(resource_snapshot())
            try:
                fd = os.open(lease, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
                os.write(fd, token)
                os.close(fd)
                owned = True
                break
            except FileExistsError:
                pass
            atomic(ROOT / 'PROGRESS.json', dict(at=now(), task='WAITING_CPU_LEASE'))
            if time.monotonic() - start > plan['max_resource_wait_seconds']:
                raise TimeoutError('CPU resource wait')
            time.sleep(60)
        began = time.monotonic()
        def guard(progress):
            require_resources(resource_snapshot())
            if time.monotonic() - began > plan['max_wall_seconds']:
                raise TimeoutError('aggregate computation ceiling')
            atomic(ROOT / 'PROGRESS.json', dict(at=now(), task='plasmode_storage_recovery', progress=progress))
        compute(plan, guard, root=ROOT, prior=PRIOR, phase=original.PHASE)
        check_pins(plan['pins'])
        if sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file()) > plan['max_output_bytes']:
            raise RuntimeError('output byte ceiling')
        freeze(ROOT / 'COMPLETE.json', dict(status='COMPLETE', at=now(), outputs={p.relative_to(ROOT).as_posix(): filehash(p) for p in ROOT.rglob('*')
            if p.is_file() and (p.name.endswith('.json') or p.name.endswith('.json.gz')) and p.name not in ('PROGRESS.json', 'MONITOR_READY.json')},
            write_through_required=True, scientific_admission=False))
    except BaseException as exc:
        freeze(ROOT / 'FAILED.json', dict(status='FAILED', at=now(), reason=str(exc), traceback=traceback.format_exc()))
        raise
    finally:
        stop.set()
        if owned and lease.exists() and lease.read_bytes() == token:
            lease.unlink()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'run'])
    args = parser.parse_args()
    prepare() if args.action == 'prepare' else run()
