"""Original paired LA numerics with immutable within-act masked checkpoints.

Only the separately reviewed native guard calls this producer. Completion is
not collector acceptance or human-bank admission. No selection is synthesized.
"""
from pathlib import Path
import math
import os
import time
import numpy as np

from . import week5_la_pipeline_v3 as original
from . import week5_la_pipeline_v4 as completion
from . import week5_la_mask_checkpoints as masked_checkpoints
from .week5_at_source import authenticate
from .week5_at_scoring import CausalScorer, digest
from .week5_at_scoring_v4 import NUMERICAL_SPEC
from .week5_at_selection import selected_reader
from .timing_census import read, filehash
from .timing_p6 import gzread, write_equal, progress

CORE = dict(completion.NUMERICAL_CORE, **{
    'week5_la_pipeline_v4.py': 'b360973f174d87a9f193881a72ff33779b57521f7e217557d71feea56f566b7f',
    'week5_la_mask_checkpoints.py': '689beea3b93c28e83ce4aec67ddcc050cadbad19a52c3685fc312b35450af322',
})
load_model = original.load_model
load_masked = original.load_masked


class PairedLoadYield(RuntimeError):
    """An actual load-stage resource refusal, never a scientific exclusion."""


def validate(inputs, config):
    if set(inputs) != {'rows', 'causal_manifest', 'masked_manifest', 'selection_root'}:
        raise ValueError('Exact LA paired inputs required')
    if set(config) - {'operation', 'max_new_mask_batches', 'max_wall_seconds'} or config.get('operation') != 'score':
        raise ValueError('Exact bounded paired score configuration required')
    batches, seconds = config.get('max_new_mask_batches', 32), config.get('max_wall_seconds', 600)
    if type(batches) is not int or not 1 <= batches <= 128:
        raise ValueError('Masked batch quantum must be between one and 128')
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or not 0 < seconds <= 1200:
        raise ValueError('Positive paired wall quantum at most 1200 seconds required')
    for name, sha in CORE.items():
        if filehash(Path(__file__).parent / name) != sha:
            raise ValueError('Frozen LA numerical/checkpoint source changed')
    return batches, float(seconds)


def sealed(path, expected):
    path = Path(path)
    seal = path.with_suffix('.seal.json')
    if not path.exists() and not seal.exists():
        return None
    if not path.is_file() or not seal.is_file():
        raise ValueError('Incomplete paired phase checkpoint; retain interrupted evidence')
    if read(seal) != dict(sha256=filehash(path), binding=expected):
        raise ValueError('Paired phase checkpoint seal or binding differs')
    value = read(path)
    if set(value) != {'binding', 'value'} or value['binding'] != expected:
        raise ValueError('Paired phase checkpoint semantic identity differs')
    return value['value']


def seal_value(path, expected, value):
    write_equal(path, dict(binding=expected, value=value))
    write_equal(Path(path).with_suffix('.seal.json'), dict(sha256=filehash(path), binding=expected))


def act_value(root, i, row, binding):
    path = root / f'act-{i:03d}.json'
    seal = path.with_suffix('.receipt.json')
    if not path.exists() and not seal.exists():
        return None
    if not path.is_file() or not seal.is_file() or read(seal) != dict(sha256=filehash(path)):
        raise ValueError('LA score checkpoint seal differs')
    value = read(path)
    if value.get('binding') != binding or value.get('id') != row['id']:
        raise ValueError('LA score identity differs')
    if value.get('status') not in ('supported', 'unsupported'):
        raise ValueError('Unknown paired support state')
    return value


def replay_binding(root, i, row, binding):
    path = root / f'act-{i:03d}.json'
    return dict(binding=binding, row_sha256=digest(row), act_sha256=filehash(path),
                producer_sha256=filehash(__file__), numerical_spec=NUMERICAL_SPEC)


def replay_evidence(root, i, value):
    if value['status'] == 'unsupported':
        return dict(status='unsupported', reason=value['reason'])
    directory = root / 'within_act' / f'act-{i:03d}'
    # The full original masked vectors and every execute/replay seal remain in
    # the terminal manifest. These additional hashes bind the completed phase.
    immutable = {p.relative_to(directory).as_posix(): filehash(p) for p in directory.rglob('*.json')
                 if 'invocation_costs' not in p.parts and p.name not in ('PROGRESS.json', 'YIELD_REQUEST.json')}
    return dict(status='supported', checkpoint_files=immutable,
                causal_verify_sha256=filehash(directory / 'causal-verify.json'),
                masked_verify_index_sha256=filehash(directory / 'masked/VERIFY_INDEX.json'),
                masked_execute_index_sha256=filehash(directory / 'masked/INDEX.json'),
                masked_result_sha256=filehash(directory / 'masked/RESULT.json'))


def score(output, inputs, config, verifying=False, *, before_model_load=None):
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    wall, cpu, stamp = time.monotonic(), time.process_time(), time.time_ns()
    result = error = initial_cost = None
    loaded, new_batches, load_seconds = [], 0, 0.0
    try:
        batch_limit, wall_limit = validate(inputs, config)
        selection = authenticate(inputs['selection_root'])
        selected = read(selection / 'output/RESULT.json')
        causal, masked = read(inputs['causal_manifest']), read(inputs['masked_manifest'])
        if (selected.get('card') != 'AT2' or selected.get('selected_model') != causal['model'] or
                selected.get('screening_only') or not selected.get('selection_admissible')):
            raise ValueError('LA requires completed primary AT2 reader selection')
        reader_binding = selected_reader(inputs['selection_root'], causal)
        rows = gzread(inputs['rows'])
        if not rows or len({r['id'] for r in rows}) != len(rows):
            raise ValueError('Nonempty uniquely identified original act batch required')
        binding = digest(dict(inputs={k: filehash(Path(v) / 'COMPLETE.json') if k.endswith('_root') else filehash(v)
                                      for k, v in inputs.items()}, config=config, numerical_spec=NUMERICAL_SPEC))
        provenance = dict(binding=binding, implementation_sha256=filehash(__file__), core=CORE,
                          numerical_spec=NUMERICAL_SPEC, selected_reader_binding=reader_binding,
                          masked_precision='float32_original', collector_admission=False)
        write_equal(root / 'CHECKPOINT_PRODUCER.json', provenance)
        if (root / 'COST.json').exists():
            initial_cost = completion.retained_cost(root / 'COST.json')
            if any(not (root / n).is_file() for n in ('INDEX.json', 'SUMMARY.json')):
                raise ValueError('Completed LA cost exists without completed reduction')
        if verifying and any(not (root / n).is_file() for n in ('INDEX.json', 'SUMMARY.json', 'COST.json')):
            raise ValueError('Partial paired execution cannot enter independent verification')

        def stop(completed, reason):
            return dict(status='yielded', phase='verify' if verifying else 'execute', reason=reason,
                        completed=completed, total=len(rows), new_mask_batches=new_batches, model_loads=len(loaded))

        if (root / 'YIELD_REQUEST.json').exists():
            result = stop(0, 'resource request before loading')
            return result
        if before_model_load is None:
            raise ValueError('Paired native guard adapter required before either model load')
        try:
            before_model_load('causal')
            model, tok, torch = load_model(causal)
            loaded.append('causal')
            reader = CausalScorer(model, tok, torch, 1024)
            if (root / 'YIELD_REQUEST.json').exists() or time.monotonic() - wall >= wall_limit:
                result = stop(0, 'resource/wall request between paired loads')
                return result
            before_model_load('masked')
            masked_model, masked_tok, _ = load_masked(masked)
            loaded.append('masked')
        except PairedLoadYield:
            result = stop(0, 'paired native admission refused a model load')
            return result
        load_seconds = time.monotonic() - wall
        values = []
        for i, row in enumerate(rows):
            path = root / f'act-{i:03d}.json'
            saved = act_value(root, i, row, binding)
            if verifying and saved is None:
                raise ValueError('Paired verify lacks completed execution act')
            verified_path = root / 'verified_acts' / f'act-{i:03d}.json'
            verified = sealed(verified_path, replay_binding(root, i, row, binding)) if verifying else None
            if verified is not None and verified != replay_evidence(root, i, saved):
                raise ValueError('Completed paired independent replay evidence differs')
            if (saved is not None and not verifying) or verified is not None:
                value = saved
            else:
                if (root / 'YIELD_REQUEST.json').exists() or new_batches >= batch_limit or time.monotonic() - wall >= wall_limit:
                    result = stop(i, 'sealed paired work quantum')
                    return result
                resolution = None
                try:
                    # Warm the original prefix cache even after a partial act.
                    # Retain the first causal value, with unchanged fresh check
                    # on reentry; model arithmetic itself is never rewritten.
                    fresh_causal = reader.score(row['causal_prefix'], row['target'])
                    directory = root / 'within_act' / f'act-{i:03d}'
                    phase = 'verify' if verifying else 'execute'
                    causal_path = directory / f'causal-{phase}.json'
                    expected = dict(binding=binding, row_sha256=digest(row), phase=phase,
                                    causal_manifest_sha256=filehash(inputs['causal_manifest']))
                    s = sealed(causal_path, expected)
                    if s is None:
                        s = fresh_causal
                        seal_value(causal_path, expected, s)
                    else:
                        reader.direct_check(row['causal_prefix'], row['target'], s)
                    remaining = wall_limit - (time.monotonic() - wall)
                    if (root / 'YIELD_REQUEST.json').exists() or remaining <= 0:
                        result = stop(i, 'sealed causal checkpoint before masked work')
                        return result
                    if verifying and saved['status'] == 'unsupported':
                        # A support refusal has no completed masked RESULT to
                        # verify. Repeat the original refusal path, which for
                        # missing/too-long old support precedes any mask forward.
                        r = original.ResolutionScorer(masked_model, masked_tok, torch, mask_batch=8).score(
                            row['previous'], row['target'])
                    else:
                        resolution = masked_checkpoints.ResolutionScorer(masked_model, masked_tok, torch,
                            directory / 'masked', dict(source_row_sha256=digest(row),
                            masked_manifest_sha256=filehash(inputs['masked_manifest'])), verifying=verifying,
                            max_new_batches=batch_limit - new_batches, max_wall_seconds=remaining,
                            yield_request_path=root / 'YIELD_REQUEST.json')
                        r = resolution.score(row['previous'], row['target'])
                    value = dict(id=row['id'], binding=binding, status='supported', causal=s, resolution=r)
                except masked_checkpoints.MaskCheckpointYield as paused:
                    result = stop(i, 'sealed within-act masked checkpoint')
                    result['mask_checkpoint'] = paused.receipt
                    return result
                except ValueError as exc:
                    if not any(t in str(exc) for t in ('leaves no masked old support', 'Target loses its predictor', 'target exceeds')):
                        raise
                    value = dict(id=row['id'], binding=binding, status='unsupported', reason=str(exc))
                finally:
                    if resolution is not None:
                        new_batches += resolution.new_batches
                        if result and result.get('status') == 'yielded':
                            result['new_mask_batches'] = new_batches
                if verifying:
                    if saved['status'] != value['status'] or saved['id'] != value['id'] or saved['binding'] != binding:
                        raise ValueError('LA scoring support differs')
                    if value['status'] == 'supported':
                        old, new = saved['resolution'], value['resolution']
                        if any(old[k] != new[k] for k in ('old_tokens', 'old_tokens_dropped', 'current_tokens')) or any(
                                len(old[k]) != len(new[k]) or np.max(np.abs(np.asarray(old[k]) - np.asarray(new[k]))) > 1e-5
                                for k in ('before_logprobs', 'after_logprobs')):
                            raise ValueError('Masked paired score fresh-forward mismatch')
                        reader.direct_check(row['causal_prefix'], row['target'], saved['causal'])
                    value = saved
                    seal_value(verified_path, replay_binding(root, i, row, binding), replay_evidence(root, i, saved))
                else:
                    write_equal(path, value)
                    write_equal(path.with_suffix('.receipt.json'), dict(sha256=filehash(path)))
            values.append(dict(file=path.name, sha256=filehash(path), id=row['id'], status=value['status']))
            progress(root / 'PROGRESS.json', dict(phase='verify' if verifying else 'score', acts=i + 1,
                     total=len(rows), cold_load_seconds=load_seconds, new_mask_batches=new_batches))
        summary = dict(causal_model=causal['model'], causal_revision=causal['revision'], causal_manifest_sha256=digest(causal),
            masked_model=masked['model'], masked_revision=masked['revision'], masked_manifest_sha256=digest(masked),
            numerical_spec=NUMERICAL_SPEC, masked_precision='float32_original', selected_reader_binding=reader_binding,
            rows=len(rows), scientific_admission=False)
        if verifying:
            if read(root / 'INDEX.json') != values or read(root / 'SUMMARY.json') != summary:
                raise ValueError('LA scoring reduction differs')
            result = dict(verified=True, complete_paired_mask_reforward=True, immutable_within_act_replay=True)
        else:
            write_equal(root / 'INDEX.json', values)
            write_equal(root / 'SUMMARY.json', summary)
            if initial_cost is None:
                write_equal(root / 'COST.json', dict(elapsed_wall_seconds=time.monotonic() - wall,
                    process_cpu_seconds=time.process_time() - cpu, cold_load_seconds=load_seconds))
            result = dict(status='complete', scientific_admission=False, collector_admission=False)
        return result
    except BaseException as exc:
        error = type(exc).__name__
        raise
    finally:
        if initial_cost is not None and completion.retained_cost(root / 'COST.json') != initial_cost:
            raise ValueError('Original LA completed cost changed')
        write_equal(root / 'invocation_costs' / f'{os.getpid()}-{stamp}.json',
            dict(phase='verify' if verifying else 'execute', pid=os.getpid(), model_loads=loaded,
                 process_cpu_seconds=time.process_time() - cpu, wall_seconds=time.monotonic() - wall,
                 cold_load_seconds=load_seconds, new_mask_batches=new_batches,
                 status='exception' if error else ('verified' if result and result.get('verified') else (result or {}).get('status')),
                 error_class=error, retained_original_cost_sha256=initial_cost, producer_sha256=filehash(__file__),
                 runtime_all_attempt_cpu_including_startup_authoritative=True))


def execute(output, inputs, config):
    return score(output, inputs, config)


def verify(output, inputs, config):
    return score(output, inputs, config, True)
