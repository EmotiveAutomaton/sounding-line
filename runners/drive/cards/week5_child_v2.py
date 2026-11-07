"""Native child boundary enforcing actual numerical pools after all imports.

DESIGN CHECK: LESSONS 3-5. Both execute and fresh replay have the same pins,
priority and pools. Imported legacy environment setters cannot silently win.
"""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import argparse,importlib,time
from pathlib import Path
import psutil
from threadpoolctl import threadpool_limits,threadpool_info
from .batch_runtime import read,freeze,check_files,now,native_identity

def run(root,operation):
    plan=read(root/'PLAN.json');check_files(plan['pins'])
    started=time.monotonic()
    freeze(root/(operation.upper()+'_NATIVE.json'),dict(at=now(),native=native_identity()))
    try:
        module=importlib.import_module(plan['module'])
        for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
            os.environ[key]='2'
        import sys
        if 'torch' in sys.modules:
            sys.modules['torch'].set_num_threads(2)
            sys.modules['torch'].set_num_interop_threads(1)
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        with threadpool_limits(limits=2):
            pools=threadpool_info()
            if any(x['num_threads']>2 for x in pools):raise RuntimeError('Numerical pool exceeds two threads')
            freeze(root/(operation.upper()+'_ENVIRONMENT.json'),dict(pools=pools,threads=2,cuda_visible=os.environ['CUDA_VISIBLE_DEVICES']))
            if operation=='execute':
                from .week5_resume import copy_checkpoint
                copy_checkpoint(root,plan)
            result=getattr(module,operation)(root/'output',plan['inputs'],plan['config'])
            if operation=='verify' and result.get('status')!='yielded' and result.get('verified') is not True:raise ValueError('Independent replay failed')
            freeze(root/('RESULT.json' if operation=='execute' else 'VERIFIED.json'),result)
        check_files(plan['pins'])
    finally:
        cpu=psutil.Process().cpu_times()
        freeze(root/(operation.upper()+'_USAGE.json'),dict(at=now(),cpu_seconds=cpu.user+cpu.system,wall_seconds=time.monotonic()-started))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=['execute','verify']);parser.add_argument('root',type=Path)
    args=parser.parse_args();run(args.root.resolve(),args.operation)
