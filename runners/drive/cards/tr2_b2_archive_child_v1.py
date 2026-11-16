"""Exact-Job handshake then one bounded extraction or replay quantum.

DESIGN CHECK: LESSONS 2-5. An unfinished independent replay returns yielded
with verified=false. Actual native identity, plan pins and two-thread pools
precede source work. The fixture branch is rejected by production admission.
"""
from pathlib import Path
import argparse
import importlib.util
import os
import sys
import time

REPO=next(p for p in Path(__file__).resolve().parents if (p/'runners/drive/native_job.py').is_file())
sys.path.insert(0,str(REPO))
os.environ['CUDA_VISIBLE_DEVICES']=''
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='2'
from runners.drive.cards.batch_runtime import read,freeze,filehash,check_files,now,native_identity
from runners.drive.cards.week5_at_queue_child_v2 import handshake


def run(root,operation):
    plan=read(root/'PLAN.json')
    if plan['phase']!=operation:raise ValueError('Child phase differs')
    check_files(plan['pins'])
    if plan.get('fixture_only') is True and plan.get('fixture_action')=='no_handshake':
        raise ValueError('constructed_missing_handshake_failure')
    native=handshake(root,operation)
    freeze(root/(operation.upper()+'_NATIVE.json'),dict(at=now(),native=native))
    import psutil
    from threadpoolctl import threadpool_limits,threadpool_info
    psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    if psutil.Process().nice()!=psutil.BELOW_NORMAL_PRIORITY_CLASS:
        raise ValueError('Below-normal child priority not applied')
    try:
        with threadpool_limits(limits=2):
            if plan.get('fixture_only') is True:
                action=plan['fixture_action']
                if action not in ('raise','hang','output','yield','complete'):
                    raise ValueError('Unknown constructed fixture action')
                freeze(root/(operation.upper()+'_ENVIRONMENT.json'),dict(threads=2,
                    pools=threadpool_info(),cuda_visible=os.environ['CUDA_VISIBLE_DEVICES']))
                if action=='raise':raise ValueError('constructed_child_failure')
                if action=='hang':
                    while True:time.sleep(.1)
                if action=='output':
                    (Path(plan['workspace'])/'oversized.bin').write_bytes(b'x'*131072)
                result=dict(status='yielded' if action=='yield' else 'complete',verified=operation=='verify' and action!='yield',
                    independent_complete_archive_replay=operation=='verify' and action!='yield',
                    original_census_reconciled=action!='yield',scientific_admission=False)
            else:
                handler=plan['handler']
                if filehash(handler['path'])!=handler['sha256']:raise ValueError('Source handler changed')
                spec=importlib.util.spec_from_file_location('frozen_original_b2_source',handler['path'])
                module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                # Imported legacy modules may load numerical libraries: enforce
                # the actual pools again after the complete source import.
                with threadpool_limits(limits=2):
                    pools=threadpool_info()
                    if any(p['num_threads']>2 for p in pools):raise ValueError('Actual pool exceeds two threads')
                    freeze(root/(operation.upper()+'_ENVIRONMENT.json'),dict(threads=2,pools=pools,cuda_visible=os.environ['CUDA_VISIBLE_DEVICES']))
                    result=module.run(Path(plan['workspace']),plan['inputs'],plan['config'],independent=operation=='verify')
                result=dict(result,verified=operation=='verify' and result.get('status')=='complete')
            if result.get('status')=='yielded' and result.get('verified') is True:
                raise ValueError('Incomplete replay cannot verify')
            freeze(root/('RESULT.json' if operation=='execute' else 'VERIFIED.json'),result)
        check_files(plan['pins'])
    finally:
        cpu=psutil.Process().cpu_times()
        freeze(root/(operation.upper()+'_USAGE.json'),dict(native=native,cpu_seconds=cpu.user+cpu.system))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=['execute','verify']);parser.add_argument('root',type=Path)
    args=parser.parse_args();run(args.root.resolve(),args.operation)
