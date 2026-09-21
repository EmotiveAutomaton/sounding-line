"""Private immutable records and the Stage 12 resource envelope.

DESIGN CHECK: LESSONS 3-5; CONTROLS 6-7. NULL: unchanged sources and budgets
permit reentry without new work. ALTERNATIVE: altered bindings, unknown charges,
expired clocks or exhausted budgets refuse dispatch. Failure cannot create a
scientific null or erase a cost. CPU and GPU totals are never interchanged.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import time
from datetime import datetime, timezone, timedelta
from runners.stage11_2.common import atomic

SOURCE = Path(__file__).resolve().parents[2]
REPO = Path(os.environ.get('SL_STAGE12_REPO', str(SOURCE))).resolve()
ROOT = REPO / 'results/phase_2_4_stage_12'
RAW = ROOT / 'raw'
SEED = 120921

def now():
    return datetime.now(timezone.utc).isoformat()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def filehash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def freeze(path, value):
    path = Path(path)
    if path.exists():
        if read(path) != value:
            raise ValueError('immutable record differs: '+str(path))
    else:
        atomic(path, value)
    return value

def pin(paths):
    return {str(Path(p).resolve().relative_to(REPO)):filehash(p) for p in sorted(paths)}

def check_pins(pins):
    for name, expected in pins.items():
        # Stage12 runs from its immutable capsule. Historical imports remain at
        # their native repository paths (their data roots are path-derived) and
        # must still match the archived source bytes before every new unit.
        path=SOURCE/name if (SOURCE/name).exists() else REPO/name
        if filehash(path) != expected:
            raise ValueError('source changed: '+name)

def charges(raw=RAW):
    totals = dict(cpu_seconds=0., gpu_seconds=0., diagnostic_gpu_seconds=0., host_cpu_seconds=0.)
    for p in (Path(raw)/'charges').glob('*.json'):
        r = read(p)
        for key in totals:
            # A live/interrupted reservation is charged until reconciled from
            # evidence. Missing completion can never refund the allowance.
            totals[key] += r.get(key, 0.)
    return totals

def admit(card, contract, raw=RAW):
    if (Path(raw)/'CANCEL.json').exists():
        raise RuntimeError('explicit stop requested')
    if datetime.now(timezone.utc) >= datetime.fromisoformat(contract['reporting']):
        raise RuntimeError('protected reporting window reached')
    if datetime.now(timezone.utc)+timedelta(seconds=card.get('wall_seconds',0))>datetime.fromisoformat(contract['reporting']):
        raise RuntimeError('complete unit cannot fit before protected reporting window')
    total = charges(raw)
    for key, limit in [('cpu_seconds','cpu_process_seconds'),('gpu_seconds','gpu_service_seconds'),
                       ('diagnostic_gpu_seconds','diagnostic_gpu_seconds')]:
        reserve = card.get(key, 0.)
        # Preserve four CPU process-hours and four GPU service-hours for replay
        # and bounded confirmation; reporting additionally has twelve wall hours.
        protected = 14400 if key in ('cpu_seconds','gpu_seconds') else 0
        if total[key]+reserve > contract[limit]-protected:
            raise RuntimeError('remaining '+key+' cannot close the complete unit')
    return total

def limit_process():
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        os.environ[key]='1'
    import psutil
    proc=psutil.Process()
    if os.name=='nt':
        proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    return proc

CHILD_CPU_UPPER_BOUND=0.

def native_command(command, *, cwd=REPO, timeout=60):
    """Synchronous leaf command, with a conservative child CPU upper bound.

    Only git read/init fixture commands and nvidia-smi use this wrapper. These
    handlers never launch scientific children. Python's run kills and reaps the
    direct leaf on timeout. Charging elapsed wall times all logical processors
    bounds its CPU even when exact native CPU timing is unavailable.
    """
    import subprocess
    global CHILD_CPU_UPPER_BOUND
    start=time.monotonic()
    try:
        return subprocess.run(command,cwd=cwd,timeout=timeout,capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0,check=True).stdout
    finally:
        CHILD_CPU_UPPER_BOUND+=(time.monotonic()-start)*(os.cpu_count() or 1)

def own_cpu():
    import psutil
    p=psutil.Process()
    c=p.cpu_times()
    # Stage workers may not launch detached children. Known native commands are
    # bounded synchronous calls, their CPU is accounted by the worker supervisor.
    return c.user+c.system+CHILD_CPU_UPPER_BOUND

def distribution(p, truth):
    """Finite label metrics; zero-support log loss stays infinite explicitly."""
    import math
    valid=(isinstance(p,list) and len(p)==len(truth) and
           all(type(v) in (int,float) and math.isfinite(v) and 0<=v<=1 for v in p)
           and abs(sum(p)-1)<1e-6)
    if not valid:
        return dict(valid=False, half_brier=1., accuracy=0., log_loss=None,
                    log_loss_infinite=True, invalid=True)
    zero=any(t>0 and v==0 for t,v in zip(truth,p))
    return dict(valid=True, half_brier=(1+sum(v*v for v in p)-2*sum(t*v for t,v in zip(truth,p)))/2,
                accuracy=float(max(range(len(p)),key=p.__getitem__)==max(range(len(truth)),key=truth.__getitem__)),
                log_loss=None if zero else -sum(t*math.log(v) for t,v in zip(truth,p) if t),
                log_loss_infinite=zero, invalid=False)
