"""Full EV source continuation with authenticated, byte-identical pilot reuse.

DESIGN CHECK: LESSONS 2-5 reread October18 for this build. Null and alternative
worlds require identical source identities, complete population and exact replay.
Missing, corrupted or re-sealed false records fail; they are never zero support.
Known-answer whole-handler replay, resume and mutation refusals precede corpus.
Only the already verified pilot prefix is reused without new source replay;
every newly constructed session is independently replayed before COMPLETE.
The fixed source cap reserves the measured remaining reader cost under the
single eight-hour S4 export ceiling, including all earlier charged work.
"""
from __future__ import annotations

from pathlib import Path
import math
import shutil
import time

from threadpoolctl import threadpool_limits

from runners.stage14.common import atomic, read, filehash
from . import engine_input_pilot as pilot
from .engine_d33_consumer import input_records, CONFIG as CONSUMER
from .timing_p6 import write_equal, gzip_equal, gzread
from .timing_pmap_source import completed
from .timing_stats import bind, check_binding

CONFIG = dict(mode='full-source', expected_sessions=1399, reuse_sessions=100,
              cumulative_wall_seconds=13500)
INPUTS = {'source_completion', 'support_completion', 'cost_receipt'}


def reserve_cost(prior, active, receipt, allowance):
    if any(not math.isfinite(x) or x <= 0 for x in (prior, active, allowance)):
        raise ValueError('invalid cumulative cost')
    charged = prior + active
    if active != receipt['active_wall_seconds'] or charged != receipt['total_charged_wall_seconds']:
        raise ValueError('cumulative cost receipt differs')
    reader_reserve = active * (1399-100)/100
    if charged + allowance + reader_reserve > 28800:
        raise ValueError('source allowance consumes remaining reader reservation')
    return dict(charged=charged, source_allowance=allowance, reader_reserve=reader_reserve,
                remaining_after_source=28800-charged-allowance)


def validate(inputs, config):
    if config == CONFIG:
        if set(inputs) != INPUTS:
            raise ValueError('exact complete source/support/cost inputs required')
    elif (set(config) == set(CONFIG) and config['mode'] == 'constructed'
          and type(config['expected_sessions']) is int
          and 1 <= config['expected_sessions'] <= 10
          and type(config['reuse_sessions']) is int
          and 0 <= config['reuse_sessions'] < config['expected_sessions']
          and config['cumulative_wall_seconds'] == 120):
        if set(inputs) != {'source_completion'}:
            raise ValueError('constructed input scope differs')
    else:
        raise ValueError('frozen full-source or bounded constructed scope required')


def load(inputs, config):
    validate(inputs, config)
    sources, selected, records = input_records(inputs['source_completion'],
        CONSUMER['mode'] if config['mode'] == 'full-source' else 'constructed')
    if sources.population['primary_sessions'] != config['expected_sessions']:
        raise ValueError('full-source population differs')
    count = config['reuse_sessions']
    if len(records) < count or selected[:count] != sources.population['primary_session_ids'][:count]:
        raise ValueError('reuse is not the verified consecutive prefix')
    if config['mode'] == 'full-source':
        root = Path(inputs['support_completion']).resolve().parent
        terminal = completed(inputs['support_completion'], root/'PLAN.json')
        plan = read(root/'PLAN.json'); receipt = read(inputs['cost_receipt'])
        if (plan['module'] != 'runners.drive.cards.engine_export_support_pilot'
                or Path(plan['inputs']['source_completion']).resolve() != Path(inputs['source_completion']).resolve()
                or receipt['complete_sha256'] != filehash(inputs['support_completion'])
                or receipt['plan_sha256'] != filehash(root/'PLAN.json')
                or not receipt['verified'] or not receipt['uncached_replay_exact']
                or not receipt['ev2_support_floor_passed']):
            raise ValueError('completed support/cost identity differs')
        for path, digest in plan['pins'].items():
            if filehash(path) != digest:
                raise ValueError('support source pin changed')
        for relative in terminal['outputs']:
            target = (root/relative).resolve(); target.relative_to(root)
            completed(inputs['support_completion'], target)
        reserve_cost(plan['prior_wall_seconds_charged'], read(root/'output/ACTIVE_TIME.json')['seconds'],
                     receipt, config['cumulative_wall_seconds'])
    return sources, dict(zip(selected[:count], records[:count]))


def _run(output, inputs, config, operation):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    validate(inputs, config)
    timing = output/'ACTIVE_TIME.json'
    previous = read(timing)['seconds'] if timing.exists() else 0.
    start = time.monotonic()
    def check():
        if previous + time.monotonic()-start > config['cumulative_wall_seconds']:
            raise TimeoutError('combined full-source construction/replay cap exceeded')
    try:
        if (output/'TIMING_BINDINGS.json').exists():
            check_binding(output, inputs, config)
        sources, reuse = load(inputs, config)
        selected = sources.population['primary_session_ids']
        binding = dict(config=config, inputs=sources.input_hashes, selected_sessions=selected,
                       source_completion_sha256=filehash(inputs['source_completion']))
        write_equal(output/'INPUTS.json', binding)
        values, index = [], []
        new_done = 0
        for sid in selected:
            check()
            rel = pilot.relative(sid); path = output/rel
            seal = path.with_suffix('.sha256.json')
            if sid in reuse:
                original = Path(inputs['source_completion']).parent/'output'/rel
                if operation == 'execute' and not path.exists():
                    path.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(original, path)
                if not path.exists() or path.read_bytes() != original.read_bytes():
                    raise ValueError('reused pilot bytes differ')
                value = gzread(path)
                if value != reuse[sid]:
                    raise ValueError('reused pilot record differs')
            elif operation == 'verify':
                value = sources.session(sid)
                if gzread(path) != value:
                    raise ValueError('fresh full-source replay differs')
            elif path.exists():
                if not seal.exists() or read(seal) != {'sha256': filehash(path)}:
                    raise ValueError('unsealed or changed source checkpoint')
                value = gzread(path)
            else:
                value = sources.session(sid); gzip_equal(path, value)
                new_done += 1
            if value['document']['keys']['session'] != sid:
                raise ValueError('checkpoint session identity differs')
            write_equal(seal, dict(sha256=filehash(path)))
            values.append(value)
            index.append(dict(session=sid, file=rel, sha256=filehash(path),
                              source_hashes=value['source_hashes'], reused=sid in reuse))
            check()
            atomic(output/'PROGRESS.json', dict(completed=len(values), total=len(selected), phase=operation))
            if (operation == 'execute' and new_done == max(1, (len(selected)-len(reuse)+9)//10)
                    and not (output/'FIRST_TENTH.json').exists()):
                projection = 2*(time.monotonic()-start)*(len(selected)-len(reuse))/new_done
                write_equal(output/'FIRST_TENTH.json', dict(new_completed=new_done,
                    projected_seconds=projection, scope='Remaining source construction plus full new-session replay; reader reserved separately'))
                if projection > config['cumulative_wall_seconds']:
                    atomic(output/'YIELD_REQUEST.json', dict(reason='source forecast exceeds fixed allowance that reserves remaining reader cost'))
            if operation == 'execute' and (output/'YIELD_REQUEST.json').exists():
                return dict(status='yielded', completed=len(values), total=len(selected), scientific_admission=False)
        result = dict(card='EV-full-source', status='complete', mode=config['mode'],
            primary_sessions=len(selected), reused_sessions=len(reuse), new_sessions=len(selected)-len(reuse),
            upstream_only_sessions=len(sources.population['upstream_only_session_ids']),
            counts={k:sum(v['support'][k] for v in values) for k in
                ('original_occurrences','intact_final_occurrences','original_words','intact_final_words')},
            reader_executed=False, scientific_admission=False,
            scope='Full source preparation only; reader continuation and scientific comparisons remain separately admitted')
        documents = pilot.document_bytes(values)
        if operation == 'execute':
            write_equal(output/'INDEX.json', index); write_equal(output/'SUMMARY.json', result)
            target = output/'DOCUMENTS.jsonl'
            if target.exists():
                if target.read_bytes() != documents:
                    raise ValueError('immutable full documents changed')
            else:
                with target.open('xb') as stream: stream.write(documents)
            if not (output/'TIMING_BINDINGS.json').exists():
                bind(output, inputs, config, ['INPUTS.json','INDEX.json','SUMMARY.json','DOCUMENTS.jsonl']
                     + [r['file'] for r in index]
                     + [str(Path(r['file']).with_suffix('.sha256.json')).replace('\\','/') for r in index])
        elif (read(output/'INDEX.json') != index or read(output/'SUMMARY.json') != result
              or (output/'DOCUMENTS.jsonl').read_bytes() != documents):
            raise ValueError('full-source aggregate replay differs')
        check()
        return result if operation == 'execute' else dict(verified=True, summary=result,
            fresh_source_replay_sessions=len(selected)-len(reuse), authenticated_prior_replay_sessions=len(reuse))
    finally:
        atomic(timing, dict(seconds=previous+time.monotonic()-start))


def execute(output, inputs, config):
    with threadpool_limits(limits=1): return _run(output, inputs, config, 'execute')


def verify(output, inputs, config):
    with threadpool_limits(limits=1): return _run(output, inputs, config, 'verify')
