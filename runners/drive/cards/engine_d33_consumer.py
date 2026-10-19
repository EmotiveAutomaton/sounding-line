"""Authenticated EV input consumer; exact original D33 rows, no reader scores.

DESIGN CHECK: LESSONS sections 2-5 reread October 18. Under null and alternative,
original source identity, covariates and every support disposition must agree.
Changed or incomplete sources fail; missing survivors are never zero scores.
Known deleted/replaced words and complete serialized/native replay precede corpus.
The bounded first100 input cohort is not the final scientific population.
"""
from __future__ import annotations

from pathlib import Path
import time

from threadpoolctl import threadpool_limits

from runners.drive.engine_d33_join import join_rows
from runners.drive.engine_sources import Sources
from runners.stage14.common import atomic, read, filehash
from . import engine_input_pilot, timing_d33_pair_intake
from .timing_pmap_source import completed, bound_record
from .timing_p6 import write_equal, gzip_equal, gzread
from .timing_stats import bind, check_binding

CONFIG = dict(mode='source-pilot-consumer', cumulative_wall_seconds=1800)
INPUTS = timing_d33_pair_intake.INPUTS | {'source_completion'}


def validate(inputs, config):
    if config == CONFIG:
        if set(inputs) != INPUTS:
            raise ValueError('exact original D33 and source-pilot inputs required')
    elif config == dict(mode='constructed', cumulative_wall_seconds=120):
        if set(inputs) != {'source_completion', 'rows_fixture'}:
            raise ValueError('constructed input contract differs')
    else:
        raise ValueError('bounded consumer configuration required; full corpus unadmitted')


def input_records(complete_path, mode):
    """Authenticate the finished input producer before reading any occurrence."""
    root = Path(complete_path).resolve().parent
    completion = completed(complete_path, root/'PLAN.json')
    plan = read(root/'PLAN.json')
    if completion['outputs'].get('PLAN.json') != filehash(root/'PLAN.json'):
        raise ValueError('source producer plan changed')
    if plan['module'] != 'runners.drive.cards.engine_input_pilot':
        raise ValueError('wrong input producer')
    engine_input_pilot.validate(plan['config'])
    expected_mode = 'source-pilot' if mode == CONFIG['mode'] else 'constructed'
    if plan['config']['mode'] != expected_mode:
        raise ValueError('constructed and corpus input scopes differ')
    for path, digest in plan['pins'].items():
        if filehash(path) != digest:
            raise ValueError('input producer source pin changed')
    for relative in completion['outputs']:
        path = (root/relative).resolve()
        path.relative_to(root)
        completed(complete_path, path)
    output = root/'output'
    check_binding(output, plan['inputs'], plan['config'])
    sources, selected = engine_input_pilot.load(plan['inputs'], plan['config'])
    saved_inputs = read(output/'INPUTS.json')
    if saved_inputs != dict(config=plan['config'], inputs=sources.input_hashes,
                            repo_root=str(sources.root), selected_sessions=selected):
        raise ValueError('input producer population binding differs')
    index = read(output/'INDEX.json')
    if [r['session'] for r in index] != selected:
        raise ValueError('input cohort identity/order differs')
    records = [bound_record(output/'INDEX.json', r) for r in index]
    if any(r['document']['keys']['session'] != i['session'] or
           r['source_hashes'] != i['source_hashes'] for r, i in zip(records, index)):
        raise ValueError('indexed occurrence source differs')
    if ((output/'DOCUMENTS.jsonl').read_bytes() != engine_input_pilot.document_bytes(records)
            or read(output/'SUMMARY.json') != engine_input_pilot.summary(sources, records, plan['config'])):
        raise ValueError('completed document population differs')
    return sources, selected, records


def original_rows(inputs, config):
    if config['mode'] == 'constructed':
        return read(inputs['rows_fixture'])
    exact = {k: inputs[k] for k in timing_d33_pair_intake.INPUTS}
    saved, _, _, _, _ = timing_d33_pair_intake.load(exact, timing_d33_pair_intake.CONFIG)
    return saved['rows']


def run(output, inputs, config, operation):
    validate(inputs, config)
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    timing = output/'ACTIVE_TIME.json'
    previous = read(timing)['seconds'] if timing.exists() else 0.
    started = time.monotonic()
    def check():
        if previous + time.monotonic()-started > config['cumulative_wall_seconds']:
            raise TimeoutError('combined consumer execution/replay cap exceeded')
    try:
        with threadpool_limits(limits=1):
            if operation == 'verify':
                check_binding(output, inputs, config)
            sources, selected, records = input_records(inputs['source_completion'], config['mode'])
            check()
            rows = original_rows(inputs, config)
            check()
            if operation == 'verify':
                for sid, record in zip(selected, records):
                    if sources.session(sid) != record:
                        raise ValueError('fresh input reconstruction differs')
                    check()
            joined = join_rows(rows, records)
            summary = dict(card='EV-D33-input-consumer', status='complete',
                mode=config['mode'], support=joined['support'],
                source_selection='first100 sorted primary sessions' if config['mode']==CONFIG['mode'] else 'constructed source cohort',
                original_covariates_preserved=True, reader_executed=False,
                engine_word_join_complete=False, scientific_admission=False,
                scope='Authenticated input join only; outside-cohort rows remain in the original population')
            binding = dict(inputs={k:filehash(v) for k,v in sorted(inputs.items())}, config=config)
            if operation == 'execute':
                write_equal(output/'INPUTS.json', binding)
                gzip_equal(output/'JOINED.json.gz', joined)
                write_equal(output/'SUMMARY.json', summary)
                if (output/'TIMING_BINDINGS.json').exists():
                    check_binding(output, inputs, config)
                else:
                    bind(output, inputs, config, ['INPUTS.json','JOINED.json.gz','SUMMARY.json'])
            elif (read(output/'INPUTS.json') != binding or
                    gzread(output/'JOINED.json.gz') != joined or read(output/'SUMMARY.json') != summary):
                raise ValueError('consumer output does not reproduce')
            check()
            return summary if operation=='execute' else dict(verified=True, summary=summary,
                fresh_original_rows=True, fresh_input_documents=True)
    finally:
        atomic(timing, dict(seconds=previous + time.monotonic()-started))


def execute(output, inputs, config):
    return run(output, inputs, config, 'execute')


def verify(output, inputs, config):
    return run(output, inputs, config, 'verify')
