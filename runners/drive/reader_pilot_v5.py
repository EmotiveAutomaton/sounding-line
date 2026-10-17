"""Finite no-cache float32 recovery; original attempts remain immutable.

DESIGN CHECK: LESSONS 3-5 reread October 17. NULL: output/source drift,
misalignment, nonfinite losses, disagreement or resource loss stops admission.
ALTERNATIVE: every fixed pilot item agrees and fits the frozen smaller budget.
No scientific effect selection, full-corpus dispatch or automatic retry.
"""
import os
for _key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '1'
import argparse
import gc
import hashlib
import importlib.metadata
import json
import shutil
import threading
import time
import traceback
from pathlib import Path
from runners.stage14.common import REPO, read, freeze, atomic, pins, check_pins, filehash, now, limits
from runners.stage9.process_identity import native_identity
from runners.next_round.queue import require_resources, resource_snapshot
from .readers import verify_model, contexts, pack
from .readers_low_memory import score_menu, token_losses
from .reader_precision import discrepancy
from .reader_pilot_v4 import gpu, direct_loss

ROOT = REPO / 'results/phase_2_4_stage_15/raw/drive-reader-pilot-v5'
PRIOR = REPO / 'results/phase_2_4_stage_15/raw/drive-reader-pilot-v4'
AUDIT = REPO / '.agent-state/drive-20261016/READER_V4_FAILURE_INSPECTION.json'
PUBLIC = REPO / 'results/phase_2_4_stage_15/DRIVE/READER_PILOT_V4.json'
ORDER = ('pythia410', 'pythia1000', 'pythia1400')
VERSIONS = ('torch', 'transformers', 'tokenizers', 'safetensors')


def compare_scores(reference, actual, tolerance):
    if len(reference) != len(actual):
        raise ValueError('menu coverage changed')
    errors = []
    for old, new in zip(reference, actual):
        if old['eligible'] != new['eligible']:
            raise ValueError('eligibility changed')
        if not old['eligible']:
            if old != new: raise ValueError('exclusion changed')
            continue
        for key in ('native_token_ids', 'codepoint_offsets', 'prefix_tokens', 'target_tokens', 'utf8_bytes'):
            # JSON round trips normalize tuples to lists.
            if json.dumps(old[key]) != json.dumps(new[key]):
                raise ValueError('token/byte alignment changed: ' + key)
        error = discrepancy(old['native_token_nll'], new['native_token_nll'])
        if error > tolerance:
            raise ValueError('retained/direct token-loss disagreement')
        errors.append(error)
    return errors


def prepare():
    limits(); require_resources(resource_snapshot())
    if ROOT.exists(): raise ValueError('attempt directory already exists')
    public = read(PUBLIC)
    if filehash(AUDIT) != public['inspection_sha256']:
        raise ValueError('prior independent inspection changed')
    audit = read(AUDIT)
    if hashlib.sha256(json.dumps(audit['retained'], sort_keys=True).encode()).hexdigest() != public['retained_hash_manifest_sha256']:
        raise ValueError('retained manifest changed')
    if filehash(PRIOR / 'FAILED.json') != public['terminal_sha256'] or not public['native_exit_verified']:
        raise ValueError('original terminal binding')
    old_plan = read(PRIOR / 'PLAN.json'); check_pins(old_plan['pins'])
    versions = {n: importlib.metadata.version(n) for n in VERSIONS}
    if versions != old_plan['versions']: raise ValueError('comparison runtime drift')
    source_paths = [PRIOR / 'PLAN.json', PRIOR / 'FAILED.json', PUBLIC, AUDIT]
    for model, record in audit['retained'].items():
        for filename, sha in record['hashes'].items():
            path = PRIOR / model / filename
            if filehash(path) != sha: raise ValueError('retained output changed')
            source_paths.append(path)
    models = read(PRIOR / 'MODELS.json')
    for entry in models.values(): verify_model(entry)
    for filename in ('CASES.json', 'MODELS.json'):
        freeze(ROOT / filename, read(PRIOR / filename)); source_paths.append(PRIOR / filename)
    for model in ('smol360', 'qwen500'):
        for filename in ('SCORES.json', 'TELEMETRY.json'):
            dest = ROOT / model / filename; dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PRIOR / model / filename, dest)
            if filehash(dest) != filehash(PRIOR / model / filename): raise ValueError('reuse bytes differ')
    source_paths += [REPO / p for p in (
        'runners/drive/reader_pilot_v5.py', 'runners/drive/readers_low_memory.py',
        'runners/drive/reader_pilot_v4.py', 'runners/drive/readers.py',
        'runners/drive/reader_precision.py', 'runners/stage14/common.py',
        'runners/stage9/process_identity.py', 'runners/next_round/queue.py',
        'tests/test_drive_reader_memory.py', 'docs/design/stage-15/drive/READER_PILOT_V5.md')]
    source_paths += [ROOT / 'CASES.json', ROOT / 'MODELS.json']
    binding = pins(source_paths); binding.update(old_plan['pins'])
    freeze(ROOT / 'PLAN.json', dict(at=now(), pins=binding, order=list(ORDER),
        reused_completed=['smol360', 'qwen500'], reused_runtime_versions_not_frozen=True,
        versions=versions, cases=len(read(ROOT/'CASES.json')), common_window=2048,
        dtype='float32', block_tokens=32, cache=False, allocator_cap_MiB=5888,
        cold_free_floor_MiB=7424, initialized_empty_free_floor_MiB=7168,
        working_free_floor_MiB=1024, maximum_temperature_C=78, tolerance=.02,
        max_resource_wait_seconds=7200, max_compute_seconds=3600,
        hard_wall_seconds=10800, target_yield_seconds=.05,
        scientific_admission=False, full_corpus_dispatch=False, original_failure_preserved=True))
    print('Finite memory-recovery pilot frozen; no inference yet.')


def run():
    limits(); plan = read(ROOT/'PLAN.json'); check_pins(plan['pins'])
    require_resources(resource_snapshot())
    if {n: importlib.metadata.version(n) for n in VERSIONS} != plan['versions']:
        raise ValueError('runtime drift')
    with (ROOT/'ATTEMPT.claim').open('x', encoding='utf8') as f: f.write(now()+'\n')
    freeze(ROOT/'OWNER.json', dict(at=now(), native=native_identity(), plan_sha256=filehash(ROOT/'PLAN.json')))
    started = time.monotonic(); waited = 0.; stop = threading.Event()
    lock = REPO/'results/.gpu.lock'; token = f'{os.getpid()} drive-reader-pilot-v5'.encode()
    owned = False; model = None; torch = None

    def deadline():
        if not stop.wait(plan['hard_wall_seconds']):
            atomic(ROOT/'FAILED.json', dict(status='FAILED', at=now(), reason='hard wall ceiling; lease retained'))
            os._exit(124)

    threading.Thread(target=deadline, daemon=True).start()
    try:
        while not (ROOT/'MONITOR_READY.json').exists():
            if time.monotonic()-started > 90: raise TimeoutError('monitor handshake')
            time.sleep(.25)
        if read(ROOT/'MONITOR_READY.json')['owner_sha256'] != filehash(ROOT/'OWNER.json'):
            raise ValueError('monitor binding')

        def wait_for(floor, task, acquire=False):
            nonlocal waited, owned
            wait_start = time.monotonic()
            while True:
                snap = gpu(); require_resources(resource_snapshot())
                if snap['free_MiB'] >= floor and snap['temperature_C'] <= plan['maximum_temperature_C']:
                    if not acquire: break
                    try:
                        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                        try: os.write(fd, token)
                        finally: os.close(fd)
                        owned = True; break
                    except FileExistsError: pass
                atomic(ROOT/'PROGRESS.json', dict(at=now(), task='WAITING_RESOURCE', next=task,
                    gpu=snap, required_free_MiB=floor, lease_owned=owned))
                if waited + time.monotonic()-wait_start > plan['max_resource_wait_seconds']:
                    raise TimeoutError('finite resource allowance exhausted')
                time.sleep(30)
            waited += time.monotonic()-wait_start

        wait_for(plan['cold_free_floor_MiB'], 'CUDA initialization', acquire=True)
        import torch as torch_module
        torch = torch_module
        from transformers import AutoTokenizer, AutoModelForCausalLM
        torch.set_num_threads(1)
        torch.cuda.set_per_process_memory_fraction(plan['allocator_cap_MiB']*2**20 / torch.cuda.get_device_properties(0).total_memory)
        cases = read(ROOT/'CASES.json'); models = read(ROOT/'MODELS.json')
        summaries = {n: read(ROOT/n/'TELEMETRY.json') for n in plan['reused_completed']}
        all_snapshots = []

        def guard():
            snap = gpu(); all_snapshots.append(snap); require_resources(resource_snapshot())
            if snap['free_MiB'] < plan['working_free_floor_MiB'] or snap['temperature_C'] > plan['maximum_temperature_C']:
                raise RuntimeError('working GPU resource floor lost')
            if time.monotonic()-started-waited > plan['max_compute_seconds']:
                raise TimeoutError('finite compute allowance exhausted')
            time.sleep(plan['target_yield_seconds'])

        for name in ORDER:
            check_pins(plan['pins'])
            gc.collect(); torch.cuda.empty_cache()
            if torch.cuda.memory_allocated() or torch.cuda.memory_reserved():
                raise ValueError('prior model allocator not empty')
            wait_for(plan['initialized_empty_free_floor_MiB'], name)
            path = verify_model(models[name])
            tok = AutoTokenizer.from_pretrained(path, local_files_only=True, trust_remote_code=False, use_fast=True)
            atomic(ROOT/'PROGRESS.json', dict(at=now(), task='LOADING', model=name, gpu=gpu()))
            model = AutoModelForCausalLM.from_pretrained(path, local_files_only=True, trust_remote_code=False,
                torch_dtype=torch.float32).to('cuda').eval()
            if model.config._attn_implementation != 'sdpa' or any(p.device.type != 'cuda' or p.dtype != torch.float32 for p in model.parameters()):
                raise ValueError('actual precision/residency/attention changed')
            guard(); torch.cuda.reset_peak_memory_stats(); began = time.monotonic()
            outputs = []; errors = []; comparisons = []; snapshot_start = len(all_snapshots)
            if name == 'pythia1400':
                # Full declared window; no natural input or score selects this stress case.
                synthetic = dict(eligible=True, prefix=[0]+[1]*2015, target=[1]*32)
                guard(); memory_values = token_losses(model, synthetic, torch, block_tokens=plan['block_tokens']); guard()
                freeze(ROOT/name/'MEMORY_PROBE.json', dict(at=now(), window_tokens=2048,
                    finite=all(__import__('math').isfinite(v) for v in memory_values),
                    target_tokens=len(memory_values), max_allocated_bytes=torch.cuda.max_memory_allocated(),
                    max_reserved_bytes=torch.cuda.max_memory_reserved(), gpu=gpu(), scientific=False))
            saved = read(PRIOR/name/'SCORES.json') if name != 'pythia1400' else None
            for i, case in enumerate(cases):
                atomic(ROOT/'PROGRESS.json', dict(at=now(), task='SCORING', model=name, menu=i,
                    total=len(cases), gpu=gpu()))
                for condition, context in contexts(tok, case['brief'], case['document']).items():
                    scores = score_menu(model, tok, context, case['menu'], torch,
                        block_tokens=plan['block_tokens'], check=guard)
                    if saved is not None:
                        old = saved[len(outputs)]
                        if (old['key'], old['condition']) != (case['key'], condition): raise ValueError('roster order changed')
                        errors.extend(compare_scores(old['scores'], scores, plan['tolerance']))
                        comparisons.append(dict(key=case['key'], condition=condition,
                            reference=old['scores'], actual=scores))
                    elif i == 0:
                        for j, (target, scored) in enumerate(zip(case['menu'], scores)):
                            if not scored['eligible']: continue
                            guard(); reference = direct_loss(model, torch, pack(tok, context, target)); guard()
                            error = discrepancy(reference, scored['native_token_nll'])
                            freeze(ROOT/name/f'check-{condition}-{j:03d}.json', dict(direct=reference,
                                blocked=scored['native_token_nll'], max_abs_error=error, tolerance=plan['tolerance']))
                            if error > plan['tolerance']: raise ValueError('ordinary/blocked direct disagreement')
                            errors.append(error)
                    outputs.append(dict(key=case['key'], condition=condition, scores=scores))
            if saved is not None and len(outputs) != len(saved): raise ValueError('incomplete retained coverage')
            if not errors: raise ValueError('empty equivalence gate')
            elapsed = time.monotonic()-began
            target_tokens = sum(s.get('target_tokens', 0) for row in outputs for s in row['scores'] if s['eligible'])
            summaries[name] = dict(items=sum(len(r['scores']) for r in outputs), target_tokens=target_tokens,
                seconds=elapsed, target_tokens_per_second=target_tokens/elapsed,
                numerical_max_abs=max(errors), numerical_comparisons=len(errors), tolerance=plan['tolerance'],
                max_allocated_bytes=torch.cuda.max_memory_allocated(), max_reserved_bytes=torch.cuda.max_memory_reserved(),
                minimum_observed_free_MiB=min(s['free_MiB'] for s in all_snapshots[snapshot_start:]),
                dtype='float32', versions=plan['versions'], attention=model.config._attn_implementation,
                all_parameters_cuda=True, context_window=2048, cache=False, block_tokens=plan['block_tokens'],
                allocator_cap_MiB=plan['allocator_cap_MiB'])
            freeze(ROOT/name/'SCORES.json', outputs)
            freeze(ROOT/name/'TELEMETRY.json', summaries[name])
            if comparisons: freeze(ROOT/name/'EQUIVALENCE.json', comparisons)
            del model; model = None; gc.collect(); torch.cuda.empty_cache()
        check_pins(plan['pins'])
        freeze(ROOT/'SUMMARY.json', summaries)
        freeze(ROOT/'COMPLETE.json', dict(status='COMPLETE', at=now(),
            outputs={p.relative_to(ROOT).as_posix():filehash(p) for p in ROOT.rglob('*.json')
                     if p.name not in ('PROGRESS.json', 'MONITOR_READY.json')},
            scientific_admission=False, full_corpus_dispatch=False, write_through_required=True))
    except BaseException as exc:
        freeze(ROOT/'FAILED.json', dict(status='FAILED', at=now(), reason=str(exc), traceback=traceback.format_exc()))
        raise
    finally:
        stop.set()
        model = None; gc.collect()
        if torch is not None and torch.cuda.is_initialized(): torch.cuda.empty_cache()
        if owned and lock.exists() and lock.read_bytes() == token: lock.unlink()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['prepare', 'run'])
    prepare() if parser.parse_args().action == 'prepare' else run()
