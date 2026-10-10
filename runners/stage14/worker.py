"""One finite local card, immutable completion and independently visible failures.

DESIGN CHECK: LESSONS 3-5. NULL: changed pins, duplicate/unknown attempt, missing
outputs or failed dependency refuse. ALTERNATIVE: valid reentry performs no calls.
Every outcome is complete, failed, blocked, or an explicit resource hold.
"""
import argparse
import importlib
from pathlib import Path
import time
import traceback
from .common import RAW, REPO, limits, now, read, atomic, freeze, filehash, check_pins, verify
from runners.stage9.process_identity import native_identity

def run(card_path,raw=RAW):
    raw=Path(raw); card_path=Path(card_path); card=read(card_path); out=raw/'jobs'/card['id']
    if (out/'COMPLETE.json').exists(): return verify(out,card_path)
    if (out/'DISPATCH.json').exists(): raise RuntimeError('unknown attempt; inspect before any restart')
    limits(); check_pins(card['source_pins']); check_pins(card.get('input_pins',{}))
    for dependency in card.get('requires',[]): verify(raw/'jobs'/dependency,raw/'cards'/f'{dependency}.json')
    for gate in card.get('gates',[]):
        if read(raw/'jobs'/gate/'ADMISSION.json').get('admitted') is not True: raise RuntimeError('scientific gate refused')
    if any((raw/x).exists() for x in ('PAUSE.json','STOP.json')): raise RuntimeError('owner pause')
    start=time.monotonic(); cpu=time.process_time()
    freeze(out/'DISPATCH.json',dict(status='running',at=now(),native=native_identity(),card_sha256=filehash(card_path)))
    def tick(progress): atomic(out/'PROGRESS.json',dict(at=now(),elapsed_seconds=time.monotonic()-start,progress=progress))
    try:
        module=importlib.import_module('runners.stage14.'+card['handler'])
        module.run(card,out,raw,tick)
        check_pins(card['source_pins']); check_pins(card.get('input_pins',{}))
        for p in card['produces']:
            if not (out/p).is_file() or (out/p).stat().st_size==0: raise ValueError('missing declared output: '+p)
        files={str(p.relative_to(out)).replace('\\','/'):filehash(p) for p in out.rglob('*') if p.is_file() and p.name not in ('PROGRESS.json','COMPLETE.json')}
        receipt=dict(status='complete',at=now(),card_sha256=filehash(card_path),outputs=files,
                     wall_seconds=time.monotonic()-start,cpu_seconds=time.process_time()-cpu,scientific_verdict=False)
        freeze(out/'COMPLETE.json',receipt);return receipt
    except BaseException as exc:
        freeze(out/'FAILED.json',dict(status='failed',at=now(),error=repr(exc),traceback=traceback.format_exc(),
            wall_seconds=time.monotonic()-start,cpu_seconds=time.process_time()-cpu,card_sha256=filehash(card_path)))
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--card',type=Path,required=True);p.add_argument('--raw',type=Path,default=RAW)
    a=p.parse_args();run(a.card,a.raw)
