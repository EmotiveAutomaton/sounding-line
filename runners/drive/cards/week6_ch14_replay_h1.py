"""Authenticated reuse of sealed execution; full fresh compiled scalar replay.

DESIGN CHECK: refuse changed/live predecessors and partial execution. No old
verification draw is credited. Isolated namespaces retain the frozen original
control flow without changing any historical module or source file.
"""
from pathlib import Path
import json
import shutil
import types
from .batch_runtime import read, freeze, filehash, check_files
from .week5_resume import output_manifest
from .week6_policy_v1 import ROOT
from .week6_ch14_wall_recovery_v1 import regular, require
from . import week6_ch_riders_v3 as base
from . import week6_ch14_scalar_h1 as scalar
from runners.stage9.process_identity import is_same_live_process

RECEIPTS = frozenset({'PLAN.json','PAUSED.json','OWNER.json','EXECUTE_NATIVE.json',
                     'VERIFY_NATIVE.json','EXECUTE_JOB_USAGE.json','VERIFY_JOB_USAGE.json'})
COPIES = frozenset({'SCIENCE.json','SOURCE_SEAL.json','RIDER_CHECKPOINT.json',
                   'PILOT.json','RECOVERY_ORIGIN.json'})


def identity(inputs, config):
    require(config.get('card') == 'CH14', 'CH14 only')
    return dict(original=base.identity(inputs, config),
                scalar_h1_sha256=filehash(scalar.__file__),
                replay_h1_sha256=filehash(__file__))


_scope = dict(vars(base), ch14=scalar, identity=identity)
reference_run = types.FunctionType(base.run.__code__, _scope, 'reference_run', base.run.__defaults__)


def authenticate(output, inputs, config):
    output = Path(output).resolve(); root = output.parent
    root.relative_to(Path(ROOT).resolve())
    require(output.name == 'output', 'Declared output directory required')
    manifest = inputs['scalar_replay']; path = Path(manifest['path'])
    regular(path)
    require(filehash(path) == manifest['sha256'], 'Changed replay manifest')
    spec = read(path); old = Path(spec['root']).resolve()
    old.relative_to(Path(ROOT).resolve())
    require(spec.get('kind') == 'CH14_VERIFY_SCALAR_H1' and spec.get('version') == 1,
            'Unknown replay contract')
    require(old != root and set(spec['receipts']) == RECEIPTS, 'Invalid predecessor')
    for name, digest in spec['receipts'].items():
        regular(old / name)
        require(filehash(old / name) == digest, 'Changed predecessor receipt: ' + name)
    prior = read(old / 'PLAN.json'); pause = read(old / 'PAUSED.json')
    require(pause.get('status') == 'PAUSED' and pause.get('paused_operation') == 'verify'
            and pause.get('scientific_admission') is False, 'Verification pause required')
    require(not any((old / n).exists() for n in ('COMPLETE.json','FAILED.json','VERIFIED.json')),
            'Ambiguous predecessor terminal')
    for name in ('OWNER.json','EXECUTE_NATIVE.json','VERIFY_NATIVE.json'):
        record = read(old / name)
        require(not is_same_live_process(record['native']), 'Predecessor still live')
    require(read(old/'OWNER.json')['plan_sha256'] == spec['receipts']['PLAN.json'], 'Owner binding mismatch')
    usage = [read(old/n) for n in ('EXECUTE_JOB_USAGE.json','VERIFY_JOB_USAGE.json')]
    require(all(u.get('includes_all_descendants_and_exited_processes') is True
                and u.get('exit_code') == 0 for u in usage), 'Unaccounted native exit')
    require(sum(u['cpu_seconds'] for u in usage) == pause['cpu_seconds'], 'Final cost mismatch')
    current = read(root/'PLAN.json')
    require(current['module'] == __name__ and prior['module'] ==
            'runners.drive.cards.week6_ch14_wall_recovery_v1', 'Wrong predecessor handler')
    require(current['inputs'] == inputs and current['config'] == config, 'Invocation mismatch')
    inherited = {k:v for k,v in inputs.items() if k != 'scalar_replay'}
    require(inherited == prior['inputs'] and config == prior['config'], 'Changed scientific inputs/configuration')
    require(prior['campaign'] == current['campaign'] == 'S15-WEEK6' and
            prior['family'] == current['family'] == 'CH' and
            prior['budget_key'] == current['budget_key'] == 'CH14', 'Changed accounting')
    require(all(current['pins'].get(p) == h for p,h in prior['pins'].items()), 'Dropped predecessor pin')
    require(current['pins'].get(str(path)) == manifest['sha256'], 'Unpinned replay manifest')
    check_files(prior['pins'])
    expected = spec['output_manifest']
    require(expected == pause['checkpoint_outputs'] and output_manifest(old/'output') == expected,
            'Changed checkpoint outputs')
    require(COPIES.issubset(expected), 'Incomplete execution')
    for name in expected: regular(old/'output'/name)
    scientific = {k:v for k,v in inherited.items() if k != 'wall_recovery'}
    binding = base.identity(scientific, config)
    saved = read(old/'output/RIDER_CHECKPOINT.json')
    require(saved['binding'] == binding and len(saved['draws']) == config.get('draws',2000),
            'Incomplete or changed execution draw bank')
    # Sealed SCIENCE is authenticated without interpreting its unfinished values.
    require(base.ck.sealed(old/'output',binding,lambda:None), 'Unsealed execution')
    origin = dict(adapter=__name__,manifest_sha256=manifest['sha256'],
                  predecessor_plan_sha256=spec['receipts']['PLAN.json'],
                  paused_sha256=spec['receipts']['PAUSED.json'],
                  copied={n:expected[n] for n in sorted(COPIES)},
                  old_verification_draws_credited=0)
    return scientific, old, current, origin


def _execute(output, inputs, config):
    scientific, old, current, origin = authenticate(output,inputs,config)
    output = Path(output); marker = output/'SCALAR_REPLAY_ORIGIN.json'
    require(not current.get('resume'), 'This successor requires a fresh attempt')
    if marker.exists():
        require(read(marker) == origin, 'Changed replay origin')
        for name,digest in origin['copied'].items():
            require(filehash(output/name) == digest, 'Changed copied execution')
    else:
        require(not output.exists() or not any(output.iterdir()), 'Fresh target required')
        output.mkdir(parents=True,exist_ok=True)
        for name,digest in origin['copied'].items():
            shutil.copyfile(old/'output'/name,output/name)
            require(filehash(output/name) == digest, 'Execution copy mismatch')
        freeze(marker,origin)
    require(base.ck.sealed(output,base.identity(scientific,config),lambda:None), 'Copied seal mismatch')
    return dict(status='complete',sealed_execution_reused=True,scientific_admission=False)


def _verify(output, inputs, config):
    scientific, _, _, origin = authenticate(output,inputs,config)
    output = Path(output)
    require(read(output/'SCALAR_REPLAY_ORIGIN.json') == origin, 'Changed replay origin')
    for name,digest in origin['copied'].items():
        require(filehash(output/name) == digest, 'Changed copied execution')
    require(base.ck.sealed(output,base.identity(scientific,config),lambda:None), 'Copied seal mismatch')
    ordinal = 1
    while (output/f'independent-h1-{ordinal:04}').exists(): ordinal += 1
    target = output/f'independent-h1-{ordinal:04}'
    answer = reference_run(target,output,scientific,config,True)
    if answer['status'] != 'complete': return answer
    left = read(output/'SCIENCE.json'); right = read(target/'SCIENCE.json')
    for value in (left,right):
        for fitted in value.get('fit',{}).values():
            fitted.pop('max_gradient',None); fitted.pop('minimum_information_eigenvalue',None)
    base.parity.equivalent(left,right)
    return dict(verified=True,independent_formulas=True,compiled_scalar=True,
                all_whole_player_draws_recomputed=True,old_verification_draws_credited=0,
                raw_source_requalification=False)


def execute(output,inputs,config): return base.ck.guarded(_execute,output,inputs,config)
def verify(output,inputs,config): return base.ck.guarded(_verify,output,inputs,config)
