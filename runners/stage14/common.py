"""Source-bound local blocks.

DESIGN CHECK: LESSONS 2-5; CONTROLS 6. NULL: changed inputs, unknown attempts,
empty outputs and failed gates refuse. ALTERNATIVE: complete finite comparisons
replay without new calls. Failure never creates scientific admission.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import time
import uuid

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / 'results/phase_2_4_stage_14/raw'
CHECKPOINT = '2026-10-17T01:00:00+00:00'
REPORTING = '2026-10-16T17:00:00+00:00'
SEED = 141010

def now(): return datetime.now(timezone.utc).isoformat()
def canonical(x): return json.dumps(x, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
def digest(x): return hashlib.sha256(canonical(x).encode()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def filehash(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''): h.update(b)
    return h.hexdigest()
def atomic(p, x):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + '.' + uuid.uuid4().hex + '.tmp')
    tmp.write_text(canonical(x) + '\n', encoding='utf-8', newline='\n')
    for n in range(51):
        try: os.replace(tmp, p); return
        except PermissionError:
            if n == 50: raise
            time.sleep(.1)
def freeze(p, x):
    if Path(p).exists():
        if read(p) != x: raise ValueError('immutable record changed: ' + str(p))
    else: atomic(p, x)
    return x
def pins(paths): return {str(Path(p).relative_to(REPO)).replace('\\','/'):filehash(p) for p in paths}
def check_pins(values):
    for p,h in values.items():
        if filehash(REPO/p) != h: raise ValueError('binding changed: ' + p)
def limits():
    for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'): os.environ[k]='1'
    os.environ['TOKENIZERS_PARALLELISM']='false'
    import psutil
    proc=psutil.Process()
    if os.name=='nt': proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    return proc
def verify(out, card=None):
    out=Path(out); r=read(out/'COMPLETE.json')
    if r['status']!='complete' or not r['outputs']: raise ValueError('empty/nonterminal block')
    if card and r['card_sha256']!=filehash(card): raise ValueError('completed card changed')
    for p,h in r['outputs'].items():
        if filehash(out/p)!=h: raise ValueError('output changed: '+p)
    return r
