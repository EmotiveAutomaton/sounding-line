"""Native stopped-owner/immutable-copy proof for scoped resume quanta only."""
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys
from . import week5_resume_v4 as adapter, week5_policy as policy
from .batch_runtime import freeze, filehash, read, native_identity


def child(root, operation):
    root = Path(root).resolve()
    # Isolate constructed evidence under private storage. This changes no real
    # campaign plan, lease, environment policy or human source.
    policy.ROOT = root
    if operation == 'produce':
        for number, (module, bounds) in enumerate(adapter.MODULE_KEYS.items()):
            old = root / str(number) / 'old'
            old.mkdir(parents=True)
            pinned = old / 'source.bin'; pinned.write_bytes(b'constructed-only immutable source\n')
            config = {'phase':'prepare', **{k:1 for k in bounds}}
            plan = dict(module=module, inputs={'source':str(pinned)}, family='FIXTURE', campaign='S15-WEEK5',
                        config=config, pins={str(pinned):filehash(pinned), str(Path(adapter.__file__).resolve()):filehash(adapter.__file__)})
            freeze(old / 'PLAN.json', plan)
            freeze(old / 'OWNER.json', dict(native=native_identity(), plan_sha256=filehash(old / 'PLAN.json')))
            freeze(old / 'output/checkpoint.json', {'constructed':True, 'prefix':[1,2,3]})
            freeze(old / 'output/independent-replay/checkpoint.json', {'constructed':True, 'prefix':[1]})
            freeze(old / 'output/YIELD_REQUEST.json', {'reason':'fixture quantum'})
            freeze(old / 'PAUSED.json', dict(status='PAUSED', checkpoint_validation_required=True,
                checkpoint_outputs=adapter.output_manifest(old / 'output')))
        return
    if operation == 'copy':
        records=[]
        for number, (module, bounds) in enumerate(adapter.MODULE_KEYS.items()):
            old, new = root / str(number) / 'old', root / str(number) / 'new'
            plan = read(old / 'PLAN.json')
            before = {str(p.relative_to(old)):filehash(p) for p in old.rglob('*') if p.is_file()}
            plan['config'] = {**plan['config'], **{k:10 for k in bounds}}
            plan['resume'] = dict(root=str(old), plan_sha256=filehash(old / 'PLAN.json'), paused_sha256=filehash(old / 'PAUSED.json'))
            new.mkdir(parents=True)
            freeze(new / 'PLAN.json', plan)
            receipt = adapter.copy_checkpoint(new, plan)
            after = {str(p.relative_to(old)):filehash(p) for p in old.rglob('*') if p.is_file()}
            assert before == after
            assert not (new / 'output/YIELD_REQUEST.json').exists()
            records.append(dict(module=module, copied_files=len(receipt['copied']), predecessor_unchanged=True,
                old_owner_stopped=not adapter.is_same_live_process(read(old / 'OWNER.json')['native'])))
        freeze(root / 'COPIED.json', dict(native=native_identity(), records=records))
        return
    if operation == 'verify':
        checks=[]
        for number, module in enumerate(adapter.MODULE_KEYS):
            old, new = root / str(number) / 'old', root / str(number) / 'new'
            receipt=read(new / 'RESUMED_FROM.json')
            expected=read(old / 'PAUSED.json')['checkpoint_outputs']
            assert adapter.output_manifest(old / 'output') == adapter.output_manifest(new / 'output') == expected == receipt['copied']
            assert filehash(old / 'PLAN.json') == receipt['plan_sha256']
            assert filehash(old / 'PAUSED.json') == receipt['paused_sha256']
            checks.append(dict(module=module, verified=True))
        freeze(root / 'FRESH_VERIFIED.json', dict(native=native_identity(), checks=checks, verified=True))
        return
    raise ValueError(operation)


def main(output):
    output=Path(output).resolve(); output.mkdir(parents=True,exist_ok=False)
    env=dict(os.environ, OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', NUMEXPR_NUM_THREADS='2', CUDA_VISIBLE_DEVICES='')
    for operation in ('produce','copy','verify'):
        with (output / (operation+'.stdout.log')).open('wb') as stdout, (output / (operation+'.stderr.log')).open('wb') as stderr:
            subprocess.run([sys.executable,'-X','utf8','-B','-m',__spec__.name,str(output),'--operation',operation],
                           check=True,env=env,stdout=stdout,stderr=stderr)
    value=dict(verified=True, constructed_only=True, no_human_source=True,
        modules=list(adapter.MODULE_KEYS), native_stopped_owner_copy_and_fresh_verify=True,
        proofs={name:filehash(output/name) for name in ('COPIED.json','FRESH_VERIFIED.json')},
        source_sha256=filehash(adapter.__file__))
    freeze(output/'FIXTURE.json',value)
    print(json.dumps(value))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path)
    parser.add_argument('--operation',choices=['produce','copy','verify'])
    args=parser.parse_args()
    child(args.output,args.operation) if args.operation else main(args.output)
