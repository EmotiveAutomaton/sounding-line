"""Constructed rehearsal of both real telemetry writers and unchanged byte cap.

DESIGN CHECK: LESSONS 3-5 reread 2026-11-03. NULL: vanished recognized
telemetry temps are tolerated; ordinary missing data and I/O errors still fail.
ALTERNATIVE: all present bytes count; an oversized fixture must be stopped.
No participant data, API calls, scientific score or research change.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from runners.stage14.common import atomic,freeze,read
from .timing_p6 import progress
from .batch_runtime_v8 import output_bytes


def execute(output,inputs,config):
    if inputs or config not in ({'mode':'progress','writes':1000}, {'mode':'cap','writes':1000}):
        raise ValueError('Fixed constructed fixture only')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if config['mode']=='cap':
        if (output/'OVERSIZED.bin').read_bytes()!=b'x'*1024:
            raise ValueError('Expected byte-cap fixture absent')
        # Long enough for the supervisor's first check; negligible CPU.
        import time
        time.sleep(35)
        raise AssertionError('Supervisor did not enforce the byte cap')
    def write_telemetry():
        for i in range(config['writes']):
            progress(output/'PROGRESS.json',dict(index=i))
            atomic(output/'TELEMETRY.json',dict(index=i))
    scans=0
    with ThreadPoolExecutor(max_workers=1) as pool:
        writer=pool.submit(write_telemetry)
        while not writer.done():
            output_bytes(output);scans+=1
        writer.result()
    if scans<1:raise ValueError('Concurrent scan was not exercised')
    result=dict(constructed_fixture_only=True,writes=config['writes'],concurrent_scans=scans,scientific_admission=False)
    freeze(output/'SUMMARY.json',result)
    return result


def verify(output,inputs,config):
    output=Path(output)
    if inputs or config!={'mode':'progress','writes':1000}:raise ValueError('Fixed progress fixture required')
    for name in ('PROGRESS.json','TELEMETRY.json'):
        if read(output/name)!={'index':999}:raise ValueError('Telemetry incomplete')
    if read(output/'SUMMARY.json')['concurrent_scans']<1:raise ValueError('Concurrent scan absent')
    expected=sum((output/name).stat().st_size for name in ('PROGRESS.json','TELEMETRY.json','SUMMARY.json'))
    if output_bytes(output)!=expected:raise ValueError('Accounting differs from actual bytes')
    return dict(verified=True,constructed_fixture_only=True)
