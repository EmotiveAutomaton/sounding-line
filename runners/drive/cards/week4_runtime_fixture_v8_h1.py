"""Exact accounting fixture with bounded Windows writer sharing retries.

DESIGN CHECK: LESSONS 3-5. The original native stress attempt is preserved:
its PID writer received PermissionError during concurrent scanning. Retry that
writer only, on PermissionError only, at most 50 calls, without skipping a value.
Permanent denial and other I/O errors fail. This is not a corpus-writer repair.
The scanner, bytes, both formats, native cap refusal and replay stay unchanged.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import time
from runners.stage14.common import atomic,freeze,read
from .timing_p6 import progress
from .batch_runtime_v8 import output_bytes


def pid_write(path,value):
    for attempt in range(50):
        try:
            progress(path,value)
            return attempt
        except PermissionError:
            if attempt==49:raise
            time.sleep(.01)


def execute(output,inputs,config):
    if inputs or config not in ({'mode':'progress','writes':1000}, {'mode':'cap','writes':1000}):
        raise ValueError('Fixed constructed fixture only')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if config['mode']=='cap':
        if (output/'OVERSIZED.bin').read_bytes()!=b'x'*1024:
            raise ValueError('Expected byte-cap fixture absent')
        time.sleep(35)
        raise AssertionError('Supervisor did not enforce the byte cap')
    def write_telemetry():
        retries=0
        for i in range(config['writes']):
            retries+=pid_write(output/'PROGRESS.json',dict(index=i))
            atomic(output/'TELEMETRY.json',dict(index=i))
        return retries
    scans=0
    with ThreadPoolExecutor(max_workers=1) as pool:
        writer=pool.submit(write_telemetry)
        while not writer.done():
            output_bytes(output);scans+=1
        retries=writer.result()
    if scans<1:raise ValueError('Concurrent scan was not exercised')
    result=dict(constructed_fixture_only=True,writes=config['writes'],concurrent_scans=scans,pid_writer_permission_retries=retries,scientific_admission=False)
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
