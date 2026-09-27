"""Immutable inputs and fixed campaign bounds.

DESIGN CHECK: LESSONS 3-5; CONTROLS 6. NULL: expired, changed, unowned or
unadmitted work refuses. ALTERNATIVE: an authorized complete block fits before
the reporting reserve. No silent retry or gear upgrade; all bands exhaustive.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import time
import uuid
from datetime import datetime, timezone, timedelta

REPO = Path(os.environ.get('SL_STAGE13_REPO', Path(__file__).resolve().parents[2])).resolve()
RAW = REPO / 'results/phase_2_4_stage_13/raw'
SEED = 130927
REPORTING = '2026-10-02T04:00:00+00:00'
DEADLINE = '2026-10-02T12:00:00+00:00'

def now(): return datetime.now(timezone.utc).isoformat()
def canonical(x): return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
def digest(x): return hashlib.sha256(canonical(x).encode('utf-8')).hexdigest()
def filehash(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def atomic(p, x):
    p=Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    tmp=p.with_name(p.name+'.'+uuid.uuid4().hex+'.tmp')
    tmp.write_text(canonical(x)+'\n', encoding='utf-8', newline='\n')
    for i in range(51):
        try: os.replace(tmp,p); return
        except PermissionError:
            if i==50: raise
            time.sleep(.1)
def freeze(p,x):
    if Path(p).exists():
        if canonical(read(p))!=canonical(x): raise ValueError('immutable record changed: '+str(p))
    else: atomic(p,x)
    return x
def limit_process():
    for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','TOKENIZERS_PARALLELISM'):
        os.environ[k]='false' if k=='TOKENIZERS_PARALLELISM' else '1'
    import psutil
    proc=psutil.Process()
    if os.name=='nt': proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    return proc
def check_pins(pins):
    for name,h in pins.items():
        if filehash(REPO/name)!=h: raise ValueError('source/input changed: '+name)
def bound(raw, card, at=None):
    contract=read(Path(raw)/'CONTRACT.json'); allocation=read(Path(raw)/'ALLOCATION.json')
    at=at or datetime.now(timezone.utc)
    if any((Path(raw)/n).exists() for n in ('PAUSE.json','STOP.json')): raise RuntimeError('owner pause/stop')
    end=datetime.fromisoformat(contract['reporting'])
    if at+timedelta(seconds=card['wall_seconds'])>=end: raise RuntimeError('whole block cannot fit before reporting reserve')
    if card['resource']=='gpu' and allocation['gear']!=2: raise RuntimeError('heavy GPU work held in Gear 1')
    if allocation['gear'] not in (1,2): raise RuntimeError('unknown gear')
    return contract
