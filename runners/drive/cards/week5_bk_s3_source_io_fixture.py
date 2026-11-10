"""Native S3 telemetry recovery, exact source parity and fresh replay.

DESIGN CHECK: LESSONS 3-5. An actual Windows reader handle must reproduce
the old failure and permit bounded recovery after release. Changed source
outputs must still fail. No model scoring or human data enters this fixture.
"""
from pathlib import Path
import argparse, ctypes, json, os, subprocess, sys, threading, time
from . import week5_bk_s3_source as original
from . import week5_bk_s3_source_io as fixed
from .week5_bk_s3_fixture import events_fixture
from .timing_p6 import write_equal, gzread
from .timing_census import filehash, read


def held_status(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"last_good":true}\n', encoding='utf8')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,
                                ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p]
    kernel.CreateFileW.restype=ctypes.c_void_p
    kernel.CloseHandle.argtypes=[ctypes.c_void_p]
    handle=kernel.CreateFileW(str(path.resolve()),0x80000000,1,None,3,0,None)
    if handle in (None,ctypes.c_void_p(-1).value):raise ctypes.WinError(ctypes.get_last_error())
    def release():
        time.sleep(.25)
        if not kernel.CloseHandle(handle):raise ctypes.WinError(ctypes.get_last_error())
    worker=threading.Thread(target=release);worker.start();return worker


def run(output, verify=False):
    if os.name!='nt':raise RuntimeError('Actual Windows proof required')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    inputs=dict(constructed_source=str(output/'SOURCE_FIXTURE.json'))
    config=dict(card='BK-S3-source',mode='constructed')
    target=output/'recovered'
    if verify:
        hold=held_status(target/'PROGRESS.json')
        try:proof=fixed.verify(target,inputs,config)
        finally:hold.join()
        if proof!={'verified':True,'complete_source_replay':True}:raise ValueError('Incomplete replay')
        # A telemetry repair cannot grant acceptance to changed source output.
        bad=output/'tampered';bad.mkdir()
        for name in ('PRIVATE_EVENTS.json.gz','SUMMARY.json'):(bad/name).write_bytes((target/name).read_bytes())
        changed=read(bad/'SUMMARY.json');changed['sessions']+=1
        (bad/'SUMMARY.json').write_text(json.dumps(changed),encoding='utf8')
        try:fixed.verify(bad,inputs,config)
        except ValueError:pass
        else:raise AssertionError('Changed summary passed verification')
        return dict(verified=True,actual_sharing_retry=True,tamper_refused=True,process_cpu_seconds=time.process_time())
    events=events_fixture()
    write_equal(output/'SOURCE_FIXTURE.json',dict(constructed=True,events=events,reference=original.prior.extract(events)))
    blocked=output/'original-refusal';hold=held_status(blocked/'PROGRESS.json')
    try:
        try:original.execute(blocked,inputs,config)
        except PermissionError:pass
        else:raise AssertionError('Original did not reproduce sharing failure')
    finally:hold.join()
    baseline=output/'baseline';original.execute(baseline,inputs,config)
    hold=held_status(target/'PROGRESS.json')
    try:result=fixed.execute(target,inputs,config)
    finally:hold.join()
    assert result=={'status':'complete','scientific_effect_computed':False}
    assert fixed.run.__code__ is original.run.__code__
    assert {k for k,v in original.run.__globals__.items() if fixed.run.__globals__[k] is not v}=={'progress'}
    assert read(baseline/'SUMMARY.json')==read(target/'SUMMARY.json')
    assert gzread(baseline/'PRIVATE_EVENTS.json.gz')==gzread(target/'PRIVATE_EVENTS.json.gz')
    child=subprocess.run([sys.executable,'-X','utf8','-B','-m',__name__ if __name__!='__main__' else 'runners.drive.cards.week5_bk_s3_source_io_fixture','--output',str(output),'--verify'],capture_output=True,text=True,timeout=120)
    (output/'verify.stdout.log').write_text(child.stdout,encoding='utf8')
    (output/'verify.stderr.log').write_text(child.stderr,encoding='utf8')
    if child.returncode:raise RuntimeError(child.stderr)
    proof=json.loads(child.stdout)
    receipt=dict(passed=True,constructed=True,original_failure_reproduced=True,unchanged_source_function=True,
                 exact_source_rows_and_summary=True,fresh_process=proof,
                 process_cpu_seconds=time.process_time(),source_sha256={str(Path(m.__file__).name):filehash(m.__file__) for m in (original,fixed)},
                 fixture_sha256=filehash(__file__))
    write_equal(output/'FIXTURE.json',receipt);return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps(run(a.output,a.verify)))
