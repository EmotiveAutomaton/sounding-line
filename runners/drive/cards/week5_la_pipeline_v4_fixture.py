"""Constructed paired-reader completion reentry and mixed v3/v4 collection."""
from pathlib import Path
from types import FunctionType
import json
import shutil

from . import week5_la_pipeline_v3 as old
from . import week5_la_pipeline_v4 as new
from .week5_at_source import authenticate
from .week5_at_fixture import fixture_loader
from .week5_la_score_fixture import masked_loader
from .timing_census import read, filehash
from .timing_p6 import gzip_equal, gzread, write_equal


def causal_loader(manifest):
    model, tokenizer, torch = fixture_loader(manifest)
    return model.double(), tokenizer, torch


def old_score(output, inputs, config, verifying=False):
    fn = FunctionType(old.score.__code__, dict(old.score.__globals__,
        load_model=causal_loader, load_masked=masked_loader), old.score.__name__,
        old.score.__defaults__, old.score.__closure__)
    return fn(output, inputs, config, verifying)


def seal(root, module, inputs, config):
    if (root / 'COMPLETE.json').exists():
        return
    pins = {str(Path(new.__file__).parent / name): sha for name, sha in new.NUMERICAL_CORE.items()}
    if module.endswith('_v4'):
        pins[str(Path(new.__file__))] = filehash(new.__file__)
    for key, value in inputs.items():
        path = Path(value) / 'COMPLETE.json' if key.endswith('_root') else Path(value)
        if path.is_file():
            pins[str(path.resolve())] = filehash(path)
    write_equal(root / 'PLAN.json', dict(module=module, inputs=inputs, config=config, pins=pins))
    outputs = {p.relative_to(root).as_posix(): filehash(p) for p in root.rglob('*')
               if p.is_file() and p.name not in ('COMPLETE.json', 'PROGRESS.json')}
    write_equal(root / 'COMPLETE.json', dict(status='COMPLETE', fresh_process_verified=True,
        outputs=outputs, constructed_dependency_fixture=True, not_a_production_runtime_admission=True))


def refuse(call):
    try:
        call()
    except (ValueError, KeyError):
        return
    raise ValueError('Changed fixture condition was accepted')


def changed_copy(root, source, name, filename, transform):
    target = root / name
    if not target.exists():
        shutil.copytree(source, target)
        path = target / filename
        path.write_text(json.dumps(transform(read(path)), sort_keys=True) + '\n', encoding='utf8')
        done = read(target / 'COMPLETE.json')
        done['outputs'][filename] = filehash(path)
        (target / 'COMPLETE.json').write_text(json.dumps(done, sort_keys=True) + '\n', encoding='utf8')
    return target


def run(output, inputs, config, verifying=False):
    if set(inputs) != {'constructed_root'} or config:
        raise ValueError('Completed constructed AT collection proof only')
    prior = authenticate(inputs['constructed_root'])
    if read(prior / 'PLAN.json').get('module') != 'runners.drive.cards.week5_at_collect_v4_fixture':
        raise ValueError('Human inputs are excluded')
    if not read(prior / 'output/FIXTURE.json').get('constructed_receipts_not_production_admission'):
        raise ValueError('Missing constructed-only declaration')
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    if (root / 'YIELD_REQUEST.json').exists():
        return dict(status='yielded', reason='before bounded constructed paired scoring')
    selection = prior / 'output/selection'
    model = read(selection / 'output/RESULT.json')['selected_model']
    source_bank = read(prior / 'output/BANK.json')
    model_plan = read(Path(next(iter(source_bank[model].values()))) / 'PLAN.json')
    causal_manifest = Path(model_plan['inputs']['model_manifest'])
    masked_manifest = root / 'masked.json'
    write_equal(masked_manifest, dict(model='constructed-masked', revision='fixture'))
    prepared = root / 'prepared'
    batches = []
    for j in range(2):
        path = prepared / 'output/batches' / f'acts-{j:06d}.json.gz'
        gzip_equal(path, [dict(id=f'constructed-{j}-{i}', causal_prefix='a ' * (i + 1), target='b',
                             previous='old text', word_count=1, meeting='constructed') for i in range(2)])
        batches.append(dict(file=path.relative_to(prepared / 'output').as_posix(), sha256=filehash(path), rows=2))
    write_equal(prepared / 'output/BATCHES.json', batches)
    seal(prepared, 'constructed_prepared_source', {}, {})
    score_config = dict(operation='score')
    saved = new.load_model, new.load_masked, new.progress
    new.load_model, new.load_masked = causal_loader, masked_loader
    bank, oracle_bank = {}, {}
    try:
        for j, batch in enumerate(batches):
            if (root / 'YIELD_REQUEST.json').exists():
                return dict(status='yielded', reason='sealed constructed paired-score batch')
            args = dict(rows=str(prepared / 'output' / batch['file']), causal_manifest=str(causal_manifest),
                        masked_manifest=str(masked_manifest), selection_root=str(selection))
            target = root / f'score-{j}'
            if j == 0:
                marker = target / 'output/YIELD_REQUEST.json'
                if not verifying and not (target / 'output/COST.json').exists():
                    def interrupt(path, value):
                        saved[2](path, value)
                        if value['acts'] == 1:
                            write_equal(marker, dict(reason='constructed partial-act pause'))
                    new.progress = interrupt
                    result = new.score(target / 'output', args, score_config)
                    new.progress = saved[2]
                    if result.get('status') != 'yielded' or result.get('completed') != 1:
                        raise ValueError('Paired act checkpoint did not yield')
                    first_sha = filehash(target / 'output/act-000.json')
                    marker.unlink()
                    new.score(target / 'output', args, score_config)
                    if filehash(target / 'output/act-000.json') != first_sha:
                        raise ValueError('Completed act changed during continuation')
                if not verifying:
                    cost = filehash(target / 'output/COST.json')
                    numeric = {p.name: filehash(p) for p in (target / 'output').glob('act-*.json')}
                    write_equal(marker, dict(reason='constructed pause after execute before verify'))
                    if new.score(target / 'output', args, score_config, True).get('status') != 'yielded':
                        raise ValueError('Completed execute did not preserve pre-verification pause')
                    marker.unlink()
                    if new.score(target / 'output', args, score_config).get('status') != 'complete':
                        raise ValueError('Completed execute reentry failed')
                    if filehash(target / 'output/COST.json') != cost or numeric != {
                            p.name: filehash(p) for p in (target / 'output').glob('act-*.json')}:
                        raise ValueError('Completed numerical bytes or original cost changed')
                if new.score(target / 'output', args, score_config, True).get('verified') is not True:
                    raise ValueError('Paired numerical replay did not verify')
                seal(target, new.__name__, args, score_config)
                oracle = root / 'same-input-v3'
                old_score(oracle / 'output', args, score_config, verifying or (oracle / 'COMPLETE.json').exists())
                seal(oracle, old.__name__, args, score_config)
                for item in read(target / 'output/INDEX.json'):
                    if filehash(target / 'output' / item['file']) != filehash(oracle / 'output' / item['file']):
                        raise ValueError('v3/v4 paired numerical bytes differ')
                oracle_bank[batch['file']] = str(oracle)
            else:
                old_score(target / 'output', args, score_config, verifying or (target / 'COMPLETE.json').exists())
                seal(target, old.__name__, args, score_config)
                oracle_bank[batch['file']] = str(target)
            bank[batch['file']] = str(target)
    finally:
        new.load_model, new.load_masked, new.progress = saved
    write_equal(root / 'BANK.json', bank)
    write_equal(root / 'ORACLE_BANK.json', oracle_bank)
    collection_inputs = dict(prepared_root=str(prepared), score_bank=str(root / 'BANK.json'))
    (new.verify if verifying else new.execute)(root / 'collection', collection_inputs, dict(operation='collect'))
    (old.verify if verifying else old.execute)(root / 'original-collection',
        dict(prepared_root=str(prepared), score_bank=str(root / 'ORACLE_BANK.json')), dict(operation='collect'))
    for name in ('ROWS.json.gz', 'UNSUPPORTED.json.gz'):
        if gzread(root / 'collection' / name) != gzread(root / 'original-collection' / name):
            raise ValueError('LA collection numerical rows changed')
    if read(root / 'collection/SUMMARY.json') != read(root / 'original-collection/SUMMARY.json'):
        raise ValueError('LA collection summary changed')
    source = root / 'score-0'
    bad_module = changed_copy(root, source, 'unknown-producer', 'PLAN.json', lambda p: dict(p, module='unknown'))
    refuse(lambda: new.producer(bad_module, read(bad_module / 'PLAN.json')))
    missing = changed_copy(root, source, 'missing-pin', 'PLAN.json',
        lambda p: dict(p, pins={k: v for k, v in p['pins'].items() if not k.endswith('week5_la_pipeline_v4.py')}))
    refuse(lambda: new.producer(missing, read(missing / 'PLAN.json')))
    bad_cost = changed_copy(root, source, 'invalid-cost', 'output/COST.json', lambda c: dict(c, process_cpu_seconds=-1))
    refuse(lambda: new.retained_cost(bad_cost / 'output/COST.json'))
    costs = [read(p) for p in (source / 'output/invocation_costs').glob('*.json')]
    if len(costs) < 5 or not {'yielded', 'complete', 'verified'} <= {c['status'] for c in costs}:
        raise ValueError('Complete lifecycle invocation costs are missing')
    if any(c['process_cpu_seconds'] < 0 or not c['runtime_all_attempt_cpu_including_startup_authoritative']
           or c['source_code_sha256'] != new.PREDECESSOR_SHA256 for c in costs):
        raise ValueError('Invocation cost scope or producer changed')
    result = dict(fixture_only=True, no_human_input=True, prior_complete_sha256=filehash(prior / 'COMPLETE.json'),
                  actual_constructed_causal_fp64_masked_fp32=True, partial_act_yield_and_continue=True,
                  complete_execute_pause_before_verify_reentry=True, original_cost_and_numeric_bytes_preserved=True,
                  every_invocation_cost_retained=True, v3_v4_numeric_bytes_equal=True,
                  mixed_exact_producer_collection_equals_original=True, unknown_producer_missing_pin_bad_cost_refused=True)
    if verifying:
        if read(root / 'FIXTURE.json') != result:
            raise ValueError('Paired completion lifecycle replay differs')
        return dict(verified=True, complete_paired_checkpoint_lifecycle=True)
    write_equal(root / 'FIXTURE.json', result)
    return dict(status='complete', fixture_only=True)


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, True)
