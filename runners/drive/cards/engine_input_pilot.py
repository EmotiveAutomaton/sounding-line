"""Counted EV source pilot; final documents and exact occurrence ledgers only.

DESIGN CHECK: LESSONS2-5 read October18. Whole-handler constructed replay,
immutable reentry, saved-boundary resume and corrupted-source/output refusals
precede corpus use. Under either scientific null or alternative the source
ledger must reconstruct exactly; disagreement fails, never becomes zero support.
The first100 sorted primary sessions measure input preparation only. Reader,
D33/export joins, typed fragments and statistical admission remain separate.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

from threadpoolctl import threadpool_info, threadpool_limits

from runners.drive.engine_sources import Sources, INPUTS
from runners.stage14.common import atomic, read, filehash
from .timing_p6 import gzip_equal, gzread, write_equal
from .timing_stats import bind, check_binding

CONFIG = dict(mode='source-pilot', expected_sessions=1399, session_limit=100,
              cumulative_wall_seconds=1800)


def validate(config):
    if set(config) != set(CONFIG):
        raise ValueError('exact input-pilot configuration required')
    if config['mode'] == 'source-pilot':
        if config != CONFIG:
            raise ValueError('frozen first100 source pilot required')
    elif config['mode'] == 'constructed':
        if (type(config['expected_sessions']) is not int or not 1 <= config['expected_sessions'] <= 10
                or config['session_limit'] != config['expected_sessions']
                or config['cumulative_wall_seconds'] != 120):
            raise ValueError('bounded constructed validation required')
    else:
        raise ValueError('full corpus requires separate measured admission')


def load(inputs, config):
    validate(config)
    if set(inputs) != INPUTS:
        raise ValueError('exact source-pilot inputs required')
    sources = Sources(inputs, expected_sessions=config['expected_sessions'])
    selected = sources.population['primary_session_ids'][:config['session_limit']]
    return sources, selected


def relative(sid):
    return 'sessions/' + hashlib.sha256(sid.encode('utf8')).hexdigest() + '.json.gz'


def document_bytes(values):
    return ''.join(json.dumps(v['document'], ensure_ascii=False, sort_keys=True,
        allow_nan=False, separators=(',', ':'))+'\n' for v in values).encode('utf8')


def summary(sources, values, config):
    return dict(card='EV-input-source-pilot', status='complete', mode=config['mode'],
        primary_sessions=sources.population['primary_sessions'], completed_sessions=len(values),
        upstream_only_sessions=len(sources.population['upstream_only_session_ids']),
        selection='first100 sorted primary session IDs' if config['mode']=='source-pilot' else 'complete constructed cohort',
        counts={k:sum(v['support'][k] for v in values) for k in
            ('original_occurrences','intact_final_occurrences','original_words','intact_final_words')},
        reader_executed=False, d33_joined=False, scientific_admission=False,
        scope='Source preparation only; no exported feature, statistical result or full-corpus admission')


def _work(output, inputs, config, operation):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    validate(config)
    timing = output/'ACTIVE_TIME.json'
    previous = read(timing)['seconds'] if timing.exists() else 0.
    started = time.monotonic()
    def check_time():
        if previous + time.monotonic()-started > config['cumulative_wall_seconds']:
            raise TimeoutError('Combined source preparation/replay cap exceeded')
    try:
        if operation == 'verify':
            check_binding(output, inputs, config)
        sources, selected = load(inputs, config)
        binding = dict(config=config, inputs=sources.input_hashes, repo_root=str(sources.root),
                       selected_sessions=selected)
        if operation == 'execute':
            write_equal(output/'INPUTS.json', binding)
        elif read(output/'INPUTS.json') != binding:
            raise ValueError('input-pilot source binding changed')
        values, index = [], []
        for sid in selected:
            check_time()
            value = sources.session(sid)
            rel = relative(sid); target = output/rel
            if operation == 'execute':
                gzip_equal(target, value)
            elif gzread(target) != value:
                raise ValueError('fresh source replay differs')
            values.append(value)
            index.append(dict(session=sid, file=rel, sha256=filehash(target), source_hashes=value['source_hashes']))
            check_time()
            if operation == 'execute':
                atomic(output/'PROGRESS.json', dict(completed=len(values), total=len(selected), phase='source-replay'))
                if (len(values) == max(1,(len(selected)+9)//10)
                        and not (output/'FIRST_TENTH.json').exists()):
                    elapsed = previous + time.monotonic()-started
                    write_equal(output/'FIRST_TENTH.json', dict(completed=len(values), total=len(selected),
                        projected_seconds=2*elapsed*len(selected)/len(values),
                        projected_full_input_seconds=2*elapsed*config['expected_sessions']/len(values),
                        scope='Source-inclusive execution extrapolated and doubled for complete fresh replay; no reader cost'))
                if (output/'YIELD_REQUEST.json').exists():
                    return dict(status='yielded', completed=len(values), total=len(selected), scientific_admission=False)
        result = summary(sources, values, config)
        documents = document_bytes(values)
        if operation == 'execute':
            write_equal(output/'INDEX.json', index)
            write_equal(output/'SUMMARY.json', result)
            path = output/'DOCUMENTS.jsonl'
            if path.exists():
                if path.read_bytes() != documents:
                    raise ValueError('immutable exporter inputs changed')
            else:
                with path.open('xb') as stream:
                    stream.write(documents)
            artifacts=['INPUTS.json','INDEX.json','SUMMARY.json','DOCUMENTS.jsonl']+[r['file'] for r in index]
            if (output/'TIMING_BINDINGS.json').exists():
                check_binding(output, inputs, config)
            else:
                bind(output, inputs, config, artifacts)
        elif (read(output/'INDEX.json') != index or read(output/'SUMMARY.json') != result
                or (output/'DOCUMENTS.jsonl').read_bytes() != documents):
            raise ValueError('source-pilot final output differs')
        check_time()
        return result if operation=='execute' else dict(verified=True, summary=result,
            cumulative_seconds=previous+time.monotonic()-started)
    finally:
        atomic(timing,dict(seconds=previous+time.monotonic()-started))


def run(output, inputs, config, operation):
    with threadpool_limits(limits=1):
        pools=threadpool_info()
        if any(p['num_threads'] != 1 for p in pools):
            raise RuntimeError('numeric thread limit not applied')
        atomic(Path(output)/('THREADS_'+operation.upper()+'.json'),dict(numerical_threads=1,
            pools=[dict(api=p['user_api'],internal_api=p['internal_api'],num_threads=p['num_threads']) for p in pools]))
        return _work(output,inputs,config,operation)


def execute(output, inputs, config):
    return run(output,inputs,config,'execute')


def verify(output, inputs, config):
    return run(output,inputs,config,'verify')
