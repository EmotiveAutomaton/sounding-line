"""Immutable LA completion reentry; original paired numerical code is unchanged."""
from pathlib import Path
from types import FunctionType
import math
import os
import time

from . import week5_la_pipeline_v3 as original
from .week5_at_source import authenticate
from .week5_at_scoring import digest
from .week5_at_scoring_v4 import NUMERICAL_SPEC
from .timing_census import read, filehash
from .timing_p6 import gzread, gzip_equal, write_equal
from .batch_runtime import check_files


PREDECESSOR_SHA256 = '624ffcd5b849c11d23763217790f0ead4c7db0c6d61e4e66090497902e7040fa'
NUMERICAL_CORE = {
    'week5_at_scoring.py': '2704c175e0ba4893dadb8df07e4b0550b0e1e1498383148afcb27ad9ad2fcf07',
    'week5_at_scoring_v4.py': '1759d0170c01376c0fcb74303b43c0977a0f47613becd15557698470273af420',
    'week5_la.py': '75072eeff47f0559edca1e63681b49feae58cb82502d6f8d4b457c9d52ecdca7',
    'week5_la_pipeline_v3.py': PREDECESSOR_SHA256,
}
PRODUCERS = {'runners.drive.cards.week5_la_pipeline_v3', 'runners.drive.cards.week5_la_pipeline_v4'}
load_model = original.load_model
load_masked = original.load_masked
progress = original.progress
prepare = original.prepare


def retained_cost(path):
    value = read(path)
    fields = {'elapsed_wall_seconds', 'process_cpu_seconds', 'cold_load_seconds'}
    if set(value) != fields:
        raise ValueError('Original LA completed cost shape changed')
    for key in fields:
        if isinstance(value[key], bool) or not isinstance(value[key], (int, float)) or not math.isfinite(value[key]) or value[key] < 0:
            raise ValueError('Invalid original LA completed cost quantity')
    return filehash(path)


def score(output, inputs, config, verifying=False):
    if filehash(original.__file__) != PREDECESSOR_SHA256:
        raise ValueError('Original paired scoring code changed')
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    began = time.process_time()
    wall = time.monotonic()
    stamp = time.time_ns()
    result = error = initial_sha = None
    cost_path = root / 'COST.json'
    try:
        if cost_path.exists():
            initial_sha = retained_cost(cost_path)
            if any(not (root / name).is_file() for name in ('INDEX.json', 'SUMMARY.json')):
                raise ValueError('Completed LA cost exists without completed reduction')
        def checked_write(destination, value):
            if Path(destination).resolve() == cost_path.resolve() and initial_sha is not None:
                if retained_cost(cost_path) != initial_sha:
                    raise ValueError('Original LA cost changed during reentry')
                return
            return write_equal(destination, value)
        fn = FunctionType(original.score.__code__, dict(original.score.__globals__,
            write_equal=checked_write, load_model=load_model, load_masked=load_masked, progress=progress),
            original.score.__name__, original.score.__defaults__, original.score.__closure__)
        fn.__kwdefaults__ = original.score.__kwdefaults__
        result = fn(root, inputs, config, verifying)
        if initial_sha is not None and retained_cost(cost_path) != initial_sha:
            raise ValueError('Original LA completed cost was overwritten')
        return result
    except BaseException as exc:
        error = type(exc).__name__
        raise
    finally:
        receipt = dict(process_cpu_seconds=time.process_time() - began, wall_seconds=time.monotonic() - wall,
                       phase='verify' if verifying else 'execute', pid=os.getpid(),
                       status='exception' if error else ('verified' if result and result.get('verified') else (result or {}).get('status')),
                       error_class=error, retained_original_cost_sha256=initial_sha,
                       source_code_sha256=filehash(original.__file__), numerical_spec=NUMERICAL_SPEC,
                       runtime_all_attempt_cpu_including_startup_authoritative=True)
        write_equal(root / 'invocation_costs' / f'{os.getpid()}-{stamp}.json', receipt)


def producer(root, plan):
    if plan.get('module') not in PRODUCERS:
        raise ValueError('Unknown LA numerical score producer')
    if read(root / 'COMPLETE.json')['outputs'].get('PLAN.json') != filehash(root / 'PLAN.json'):
        raise ValueError('LA producer plan is not authenticated')
    check_files(plan['pins'])
    pins = {}
    for name, sha in plan['pins'].items():
        key = str(Path(name).resolve()).casefold()
        if key in pins and pins[key] != sha:
            raise ValueError('Conflicting LA producer pin aliases')
        pins[key] = sha
    core = dict(NUMERICAL_CORE)
    if plan['module'].endswith('_v4'):
        core[Path(__file__).name] = filehash(__file__)
    for name, sha in core.items():
        path = Path(__file__).parent / name
        if filehash(path) != sha or pins.get(str(path.resolve()).casefold()) != sha:
            raise ValueError('Unreviewed or unpinned LA numerical producer')
    for name, value in plan['inputs'].items():
        path = Path(value) / 'COMPLETE.json' if name.endswith('_root') else Path(value)
        if pins.get(str(path.resolve()).casefold()) != filehash(path):
            raise ValueError('Unpinned LA score input')
    return dict(module=plan['module'], plan_sha256=filehash(root / 'PLAN.json'),
                complete_sha256=filehash(root / 'COMPLETE.json'), core=core)


def collect(output, inputs, config, verifying=False):
    if set(inputs) != {'prepared_root', 'score_bank'}:
        raise ValueError('Exact full laughter bank required')
    source = authenticate(inputs['prepared_root']) / 'output'
    bank = read(inputs['score_bank'])
    index = read(source / 'BATCHES.json')
    if set(bank) != set(x['file'] for x in index):
        raise ValueError('Incomplete laughter score bank')
    rows, unsupported, producers = [], [], []
    models, reader_banks = set(), set()
    for item in index:
        path = source / item['file']
        if filehash(path) != item['sha256']:
            raise ValueError('LA prepared source changed')
        score_root = authenticate(bank[item['file']])
        root = score_root / 'output'
        plan = read(score_root / 'PLAN.json')
        producers.append(producer(score_root, plan))
        summary = read(root / 'SUMMARY.json')
        if filehash(plan['inputs']['rows']) != filehash(path):
            raise ValueError('LA scorer/source binding differs')
        if summary.get('numerical_spec') != NUMERICAL_SPEC or summary.get('masked_precision') != 'float32_original':
            raise ValueError('Mixed LA reader numerical specification')
        reader_banks.add(digest({k: summary[k] for k in ('causal_manifest_sha256', 'masked_manifest_sha256', 'selected_reader_binding', 'numerical_spec')}))
        expected_binding = digest(dict(inputs={k: filehash(Path(v) / 'COMPLETE.json') if k.endswith('_root') else filehash(v)
                                               for k, v in plan['inputs'].items()}, config=plan['config'], numerical_spec=NUMERICAL_SPEC))
        values = read(root / 'INDEX.json')
        original_rows = gzread(path)
        if [r['id'] for r in original_rows] != [r['id'] for r in values]:
            raise ValueError('LA scored row population differs')
        models.add(summary['causal_model'])
        for row, value in zip(original_rows, values):
            score_path = root / value['file']
            if filehash(score_path) != value['sha256']:
                raise ValueError('LA scored act changed')
            scored = read(score_path)
            if scored['binding'] != expected_binding:
                raise ValueError('LA scored act numerical/input binding differs')
            if scored['status'] != 'supported':
                unsupported.append(dict(id=row['id'], reason=scored['reason']))
                continue
            projected = {k: v for k, v in row.items() if k not in ('text', 'previous', 'causal_prefix', 'target')}
            rows.append(dict(projected, resolution=scored['resolution']['resolution_nats_per_token'],
                             surprise=scored['causal']['surprisal_nats'] / row['word_count']))
    if len(models) != 1 or len(reader_banks) != 1:
        raise ValueError('Mixed selected causal/masked readers or numerical bindings')
    if len(unsupported) > max(0, (len(rows) + len(unsupported)) * .01):
        raise ValueError('Laughter score collection exceeds one-percent unsupported allowance')
    root = Path(output)
    summary = dict(supported=len(rows), unsupported=len(unsupported), model=next(iter(models)),
                   numerical_spec=NUMERICAL_SPEC, reader_bank_binding=next(iter(reader_banks)))
    for name, value in [('ROWS.json.gz', rows), ('UNSUPPORTED.json.gz', unsupported)]:
        if verifying:
            if gzread(root / name) != value:
                raise ValueError('LA complete bank projection differs')
        else:
            gzip_equal(root / name, value)
    if verifying:
        if read(root / 'SUMMARY.json') != summary or read(root / 'PRODUCER_BINDINGS.json') != producers:
            raise ValueError('LA complete bank reduction or provenance differs')
        return dict(verified=True, complete_bank_reduction=True)
    write_equal(root / 'SUMMARY.json', summary)
    write_equal(root / 'PRODUCER_BINDINGS.json', producers)
    return dict(status='complete', scientific_admission=False)


def execute(output, inputs, config):
    return {'prepare': prepare, 'score': score, 'collect': collect}[config.get('operation', 'prepare')](output, inputs, config)


def verify(output, inputs, config):
    return {'prepare': prepare, 'score': score, 'collect': collect}[config.get('operation', 'prepare')](output, inputs, config, True)
