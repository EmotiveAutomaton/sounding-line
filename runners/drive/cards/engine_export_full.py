"""Complete EV reader continuation; authenticated pilot reuse, bounded batches.

DESIGN CHECK (2026-10-19)
LESSONS sections 3-5 read for this build. Under null and alternative, population,
source/reader identities and uncached batch replay must agree. Missing, changed,
truncated or substituted records fail; unsupported words remain explicit. Only
the completed pilot prefix is reused. Every new batch is scored again in a
fresh contained process. The single S4 ceiling includes all prior corpus work,
completed source preparation and both reader phases; it never doubles again.
Known-answer native replay, resume and corruption refusal precede corpus use.
No statistical result, badge or automatic successor is licensed by this export.
"""
from __future__ import annotations

from collections import Counter
import math
import os
from pathlib import Path
import shutil
import time

from threadpoolctl import threadpool_limits

from runners.stage14.common import atomic, read, filehash
from runners.drive.engine_export_join import digest, join_exports, typed_fragments
from . import engine_export_pilot as pilot, engine_export_support_pilot as support
from . import engine_input_full as full, engine_input_pilot as source_pilot
from . import engine_d33_consumer as consumer
from .timing_pmap_source import completed, bound_record
from .timing_p6 import write_equal, gzip_equal, gzread
from .timing_stats import bind, check_binding

EXTRA = {'full_source_completion', 'support_completion', 'cost_receipt'}
CONSTRUCTED = dict(mode='constructed', expected_sessions=2, reuse_sessions=1,
                   batch_size=1, cumulative_wall_seconds=180)


def remaining_cost(prior, source_seconds, pilot_seconds):
    if any(type(x) not in (int, float) or not math.isfinite(x) or x <= 0
           for x in (prior, source_seconds, pilot_seconds)):
        raise ValueError('invalid completed cumulative cost')
    charged = prior + source_seconds
    allowance = math.floor(28800 - charged)
    forecast = pilot_seconds * 1299 / 100
    if allowance <= 0 or forecast > allowance:
        raise ValueError('remaining reader reservation exceeds single combined ceiling')
    return dict(prior_wall_seconds_charged=charged, max_wall_seconds=allowance,
                projected_reader_seconds=forecast, combined_ceiling_seconds=28800)


def validate(inputs, config):
    if config == CONSTRUCTED:
        extra = EXTRA - {'cost_receipt'}
        underlying = {k:v for k,v in inputs.items() if k not in extra}
        pilot.validate(underlying, pilot.CONSTRUCTED)
    elif (set(config) == set(CONSTRUCTED) and config['mode'] == 'full-reader'
          and config['expected_sessions'] == 1399 and config['reuse_sessions'] == 100
          and config['batch_size'] == 100 and type(config['cumulative_wall_seconds']) is int
          and 0 < config['cumulative_wall_seconds'] < 28800):
        extra = EXTRA
        underlying = {k:v for k,v in inputs.items() if k not in extra}
        pilot.validate(underlying, pilot.PILOT)
    else:
        raise ValueError('fixed full-reader population, batches and cost required')
    if not extra <= set(inputs):
        raise ValueError('exact completed source and support inputs required')


def authenticate(complete_path, module):
    root = Path(complete_path).resolve().parent
    terminal = completed(complete_path, root/'PLAN.json')
    plan = read(root/'PLAN.json')
    if plan['module'] != module:
        raise ValueError('wrong completed producer')
    for path, sha in plan['pins'].items():
        if filehash(path) != sha:
            raise ValueError('completed producer source pin changed')
    for relative in terminal['outputs']:
        path = (root/relative).resolve(); path.relative_to(root)
        completed(complete_path, path)
    check_binding(root/'output', plan['inputs'], plan['config'])
    return root, plan


def load(inputs, config):
    validate(inputs, config)
    root, plan = authenticate(inputs['full_source_completion'], 'runners.drive.cards.engine_input_full')
    full.validate(plan['inputs'], plan['config'])
    expected_mode = 'constructed' if config == CONSTRUCTED else 'full-source'
    if (plan['config']['mode'] != expected_mode
            or plan['config']['expected_sessions'] != config['expected_sessions']
            or plan['config']['reuse_sessions'] != config['reuse_sessions']
            or Path(plan['inputs']['source_completion']).resolve() != Path(inputs['source_completion']).resolve()):
        raise ValueError('full-source population or prior identity differs')
    sources, reuse = full.load(plan['inputs'], plan['config'])
    selected = sources.population['primary_session_ids']
    out = root/'output'; index = read(out/'INDEX.json')
    if [r['session'] for r in index] != selected:
        raise ValueError('full-source session order differs')
    records = [bound_record(out/'INDEX.json', r) for r in index]
    for sid, value, row in zip(selected, records, index):
        if (value['document']['keys']['session'] != sid or value['source_hashes'] != row['source_hashes']
                or row['reused'] != (sid in reuse) or sid in reuse and value != reuse[sid]):
            raise ValueError('full-source record identity differs')
    expected_inputs = dict(config=plan['config'], inputs=sources.input_hashes,
        selected_sessions=selected, source_completion_sha256=filehash(inputs['source_completion']))
    if read(out/'INPUTS.json') != expected_inputs or (out/'DOCUMENTS.jsonl').read_bytes() != source_pilot.document_bytes(records):
        raise ValueError('full-source document binding differs')
    parent, parent_plan = authenticate(inputs['support_completion'], 'runners.drive.cards.engine_export_support_pilot')
    support.validate(parent_plan['inputs'], parent_plan['config'])
    expected_support = support.CONSTRUCTED if config == CONSTRUCTED else support.CONFIG
    if parent_plan['config'] != expected_support:
        raise ValueError('support pilot scope differs')
    underlying = {k:v for k,v in inputs.items() if k not in EXTRA}
    if {k:str(Path(v).resolve()) for k,v in underlying.items()} != {k:str(Path(v).resolve()) for k,v in parent_plan['inputs'].items()}:
        raise ValueError('original rows, sources or reader changed since support pilot')
    identity = read(parent/'output/IDENTITY.json')
    if identity['selected_sessions'] != selected[:config['reuse_sessions']]:
        raise ValueError('reused export is not exact completed prefix')
    mode = 'constructed' if config == CONSTRUCTED else 'reader-pilot'
    documents = [r['document'] for r in records[:config['reuse_sessions']]]
    values, manifest = pilot.authenticated_export(parent/'output/execute/FEATURES.jsonl', documents,
        inputs, mode, identity['lease_sha256'])
    other, other_manifest = pilot.authenticated_export(parent/'output/verify/FEATURES.jsonl', documents,
        inputs, mode, identity['lease_sha256'])
    if values != other or manifest != other_manifest or identity['manifest_sha256'] != digest(manifest):
        raise ValueError('completed pilot uncached replay differs')
    cost = None
    if config != CONSTRUCTED:
        receipt = read(inputs['cost_receipt'])
        if (Path(plan['inputs']['support_completion']).resolve() != parent/'COMPLETE.json'
                or Path(plan['inputs']['cost_receipt']).resolve() != Path(inputs['cost_receipt']).resolve()
                or plan['prior_wall_seconds_charged'] != receipt['total_charged_wall_seconds']):
            raise ValueError('full-source cumulative charge identity differs')
        cost = remaining_cost(receipt['total_charged_wall_seconds'],
            read(root/'output/ACTIVE_TIME.json')['seconds'], receipt['active_wall_seconds'])
        if config['cumulative_wall_seconds'] != cost['max_wall_seconds']:
            raise ValueError('reader allowance does not equal actual remaining cost')
    return records, parent, values, cost


def seal_batch(folder, documents, inputs, mode):
    path = folder/'FEATURES.jsonl'
    manifest = read(str(path)+'.manifest.json')
    values, _ = pilot.authenticated_export(path, documents, inputs, mode, manifest['slotLeaseSha256'])
    files = {p.name:filehash(p) for p in sorted(folder.iterdir())
             if p.is_file() and p.suffix in ('.json', '.jsonl') and p.name != 'SEALED.json'}
    write_equal(folder/'SEALED.json', dict(documents_sha256=digest(documents), files=files))
    return values


def saved_batch(folder, documents, inputs, mode):
    seal = read(folder/'SEALED.json')
    files = {p.name:filehash(p) for p in sorted(folder.iterdir())
             if p.is_file() and p.suffix in ('.json', '.jsonl') and p.name != 'SEALED.json'}
    if seal != dict(documents_sha256=digest(documents), files=files):
        raise ValueError('changed or incomplete reader checkpoint')
    return pilot.authenticated_export(folder/'FEATURES.jsonl', documents, inputs, mode,
        read(str(folder/'FEATURES.jsonl')+'.manifest.json')['slotLeaseSha256'])[0]


def run(output, inputs, config, operation):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    os.environ['PYTHONSAFEPATH'] = '1'
    timing = output/'ACTIVE_TIME.json'
    previous = read(timing)['seconds'] if timing.exists() else 0.
    start = time.monotonic()
    def check():
        if previous + time.monotonic()-start > config['cumulative_wall_seconds']:
            raise TimeoutError('single combined reader execution/replay allowance exceeded')
        if (output.parent/'STOP').exists():
            raise RuntimeError('owner stop requested')
    try:
        validate(inputs, config)
        if operation == 'verify' or (output/'TIMING_BINDINGS.json').exists():
            check_binding(output, inputs, config)
        records, parent, values, cost = load(inputs, config)
        mode = 'constructed' if config == CONSTRUCTED else 'reader-pilot'
        reuse = output/'reuse'; reuse.mkdir(exist_ok=True)
        for path in sorted((parent/'output/execute').iterdir()):
            if path.suffix not in ('.json','.jsonl'): continue
            target = reuse/path.name
            if not target.exists() and operation == 'execute': shutil.copyfile(path, target)
            if target.read_bytes() != path.read_bytes(): raise ValueError('reused export bytes differ')
        binding = dict(config=config, inputs={k:filehash(v) for k,v in inputs.items()},
                       selected_sessions=[r['document']['keys']['session'] for r in records], cost=cost)
        write_equal(output/'INPUTS.json', binding)
        (output/operation).mkdir(exist_ok=True)
        for number, offset in enumerate(range(config['reuse_sessions'], len(records), config['batch_size'])):
            check()
            documents = [r['document'] for r in records[offset:offset+config['batch_size']]]
            relative = operation+'/batch-'+str(number).zfill(3); folder = output/relative
            if folder.exists():
                # Partial batches are retained and refused, never silently overwritten.
                batch = saved_batch(folder, documents, inputs, mode)
            else:
                pilot.export(output, documents, inputs, dict(mode=mode), relative, check)
                batch = seal_batch(folder, documents, inputs, mode)
            if operation == 'verify':
                original = saved_batch(output/'execute'/folder.name, documents, inputs, mode)
                if batch != original:
                    raise ValueError('fresh uncached batch does not reproduce')
            values.extend(batch)
            atomic(output/'PROGRESS.json', dict(phase=operation, completed=len(values), total=len(records)))
            check()
        original_rows = consumer.original_rows(inputs, dict(mode='constructed') if mode=='constructed' else consumer.CONFIG)
        joined = join_exports(original_rows, records, values)
        fragments = [typed_fragments(r) for r in records]
        summary = dict(card='EV-export-full', status='complete', mode=config['mode'],
            documents=len(records), reused_documents=config['reuse_sessions'],
            newly_exported_documents=len(records)-config['reuse_sessions'],
            original_rows_preserved=True, support=joined['support'],
            fragment_dispositions=dict(Counter(r['status'] for r in fragments)),
            real_reader_executed=mode=='reader-pilot', typed_fragments_reader_scored=False,
            scientific_admission=False, source_replay='Authenticated completed full-source producer',
            reader_replay='Authenticated completed prefix; fresh uncached remaining batches')
        if operation == 'execute':
            gzip_equal(output/'FEATURES.json.gz', values); gzip_equal(output/'JOINED.json.gz', joined)
            gzip_equal(output/'FRAGMENTS.json.gz', fragments); write_equal(output/'SUMMARY.json', summary)
            if not (output/'TIMING_BINDINGS.json').exists():
                artifacts = ['INPUTS.json','FEATURES.json.gz','JOINED.json.gz','FRAGMENTS.json.gz','SUMMARY.json']
                artifacts += [p.relative_to(output).as_posix() for folder in (output/'execute',reuse)
                    for p in sorted(folder.rglob('*')) if p.is_file() and p.suffix in ('.json','.jsonl')]
                bind(output, inputs, config, artifacts)
        elif (values != gzread(output/'FEATURES.json.gz') or joined != gzread(output/'JOINED.json.gz')
              or fragments != gzread(output/'FRAGMENTS.json.gz') or summary != read(output/'SUMMARY.json')):
            raise ValueError('full reader population or original-row join does not reproduce')
        check()
        return summary if operation=='execute' else dict(verified=True, summary=summary,
            fresh_uncached_replay_documents=len(records)-config['reuse_sessions'],
            authenticated_prior_replay_documents=config['reuse_sessions'])
    finally:
        atomic(timing, dict(seconds=previous+time.monotonic()-start))


def execute(output, inputs, config):
    with threadpool_limits(limits=1): return run(output, inputs, config, 'execute')


def verify(output, inputs, config):
    with threadpool_limits(limits=1): return run(output, inputs, config, 'verify')
