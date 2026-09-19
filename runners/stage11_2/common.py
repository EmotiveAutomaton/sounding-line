"""Immutable records and bounded accounting.

DESIGN CHECK: LESSONS 3–5, CONTROLS 6 read September 19.
NULL and ALTERNATIVE: altered inputs, unfinished reservations and exceeded bounds
must refuse dispatch. Every attempted service interval is charged, including failure.
Bands: admitted, blocked, failed, complete; no gate inferred from path existence.
"""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
import uuid

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / 'results/phase_2_4_stage_11_2'
RAW = ROOT / 'raw'
DEADLINE = '2026-09-20T15:00:00+00:00'
REPORTING = '2026-09-20T13:00:00+00:00'
MAX_GPU_SECONDS = 18 * 3600

def now():
    return datetime.now(timezone.utc).isoformat()

def canonical(obj):
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode()

def digest(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()

def filehash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda: stream.read(4*1024*1024), b''):
            h.update(data)
    return h.hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def freeze(path, obj):
    path = Path(path); data = canonical(obj)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f'immutable record differs: {path}')
    else:
        with path.open('xb') as stream:
            stream.write(data)
    return obj

def atomic(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    temp.write_bytes(canonical(obj))
    for i in range(30):
        try:
            os.replace(temp, path); return
        except PermissionError:
            if i == 29: raise
            time.sleep(.1)

def source_pins():
    paths = list((REPO/'runners/stage11_2').rglob('*.py'))
    paths += list((REPO/'runners/stage11_2/vendor').glob('LICENSE'))
    paths += list((REPO/'runners/stage11_2/vendor').glob('REVISION'))
    paths += [REPO/'runners/stage9/neural.py', REPO/'soundingline/probe/interventions.py',
              REPO/'soundingline/gpulock.py']
    return {p.relative_to(REPO).as_posix():filehash(p) for p in sorted(paths)}

def check_pins(pins):
    for name, expected in pins.items():
        if filehash(REPO/name) != expected: raise ValueError('source changed: '+name)

def charge_total(root):
    rows = [read(p) for p in (Path(root)/'charges').glob('*.json')]
    return sum(r.get('elapsed_seconds', r['reserved_seconds']) for r in rows)

@contextmanager
def gpu_service(root, name, reservation=600):
    """Serial caller owns GPU lock. Unfinished reservations remain charged at full bound."""
    root = Path(root)
    if datetime.now(timezone.utc).timestamp()+reservation > datetime.fromisoformat(DEADLINE).timestamp():
        raise RuntimeError('deadline cannot accommodate reserved service')
    if charge_total(root)+reservation > MAX_GPU_SECONDS:
        raise RuntimeError('cumulative GPU ceiling')
    ident = uuid.uuid4().hex
    path = root/'charges'/f'{ident}.json'
    start = time.monotonic()
    row = dict(id=ident, job=name, started=now(), reserved_seconds=reservation,
               state='reserved', pid=os.getpid())
    freeze(path,row)
    try:
        yield
    except BaseException as exc:
        row.update(state='failed', error=type(exc).__name__)
        raise
    else:
        row['state']='complete'
    finally:
        row.update(ended=now(), elapsed_seconds=time.monotonic()-start)
        atomic(path,row)

def contract(root=RAW):
    return freeze(Path(root)/'CONTRACT.json', dict(schema='stage11.2-v1',
        commissioned_at='2026-09-19T16:05:00+00:00', clock_basis='supplied-file receipt; fixed Sunday deadline governs',
        deadline=DEADLINE, reporting=REPORTING, gear=2, cpu_threads=4,
        cooling='existing boost-off / 90-percent maximum retained',
        maximum_gpu_seconds=MAX_GPU_SECONDS, paid_calls=0, delegation=False,
        capability_action=.70, capability_state=.80, maximum_capability_degradation=.05,
        train_units=96, dev_units=64, test_units=128, test_unit='maker/world construction',
        repair_limit_per_adapter_family=1, authority='supplied Stage 11.2 brief and explicit Gear 2 instruction'))
