"""New-file, resumable, exact CH prefix representation migration.

DESIGN CHECK: CH_CENSUS_STORAGE_V1.md. Conversion is operational work charged
to CH, not new human-source admission. Both handlers stop at exact logical row
quanta; verification rereads the entire old immutable database from row zero.
"""
from pathlib import Path
import json
import sqlite3
import time
from . import week5_ch_source as original
from . import week5_ch_pipeline_checkpoint as ck
from . import week5_ch_storage_v1 as storage

TABLES = ('frame', 'openings', 'opening_positions', 'histories', 'checkpoints', 'settings')


def binding(inputs, config):
    if set(inputs) != {'frame'} or config.get('phase') != 'storage_migration':
        raise ValueError('One pinned standalone census database required')
    return ck.binding(inputs, config, dict(adapter=original.digest(__file__),
                                         codec=original.digest(storage.__file__),
                                         source=original.digest(original.__file__)))


def state_get(con, key):
    row = con.execute('SELECT value FROM _week5_storage_migration WHERE key=?', (key,)).fetchone()
    return json.loads(row[0]) if row else None


def state_put(con, key, value):
    con.execute('INSERT OR REPLACE INTO _week5_storage_migration VALUES(?,?)',
                (key, json.dumps(value, sort_keys=True)))


def rows(con, table, last=None):
    schema = con.execute('PRAGMA table_info('+table+')').fetchall()
    keys = [r[1] for r in sorted(schema, key=lambda r:r[5]) if r[5]]
    if not keys:
        raise ValueError('Original source primary key is missing')
    columns = [r[1] for r in schema]
    where = '' if last is None else ' WHERE ('+','.join(keys)+')>('+','.join('?' for _ in keys)+')'
    cursor = con.execute('SELECT * FROM '+table+where+' ORDER BY '+','.join(keys), () if last is None else last)
    for row in cursor:
        yield row, [row[columns.index(k)] for k in keys]


def inspect(con):
    if con.execute('PRAGMA quick_check').fetchone() != ('ok',):
        raise ValueError('Source checkpoint integrity failed')
    counts = {table:con.execute('SELECT count(*) FROM '+table).fetchone()[0] for table in TABLES}
    states = con.execute('SELECT month,ordinal,source,counts,complete FROM checkpoints').fetchall()
    if len(states) != 1:
        raise ValueError('Migration requires exactly one original month checkpoint')
    month, ordinal, source, raw_counts, complete = states[0]
    if json.loads(raw_counts).get('source_games') != ordinal+1:
        raise ValueError('Checkpoint ordinal and source denominator disagree')
    return counts, dict(month=month, ordinal=ordinal, source_sha256=source,
                        original_complete=complete, source_games=ordinal+1)


def _execute(output, inputs, config):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    bound = binding(inputs, config)
    check = lambda:ck.require(output)
    source = ck.checked(inputs['frame'], check)
    if ck.sealed(output, bound, check):
        return dict(status='complete', sealed_output_reused=True)
    destination = output/'PRIVATE_FRAME.sqlite'
    if destination.resolve() == source.resolve():
        raise ValueError('Never replace original input')
    if destination.exists():
        ck.copied(destination, output, check)
    src = storage.connect(source)
    try:
        counts, checkpoint = inspect(src)
        total = sum(counts.values())
        with storage.bridge([original], output, [source]):
            target = original.open_database(destination)
        target.execute('CREATE TABLE IF NOT EXISTS _week5_storage_migration(key TEXT PRIMARY KEY,value TEXT)')
        prior = state_get(target, 'binding')
        if prior is not None and prior != bound:
            target.close()
            raise ValueError('Migration checkpoint changed inputs or contract')
        state = state_get(target, 'state') or dict(table=0, last=None, done=0)
        state_put(target, 'binding', bound)
        target.commit()
        quantum = config.get('max_new_draws')
        new = 0
        started = time.process_time()
        def progress():
            original.write_json(output/'PROGRESS.json', dict(operation='storage_migration_execute',
                                completed=state['done'], total=total, new_rows=new,
                                invocation_cpu_seconds=time.process_time()-started,
                                units='logical rows; not raw games, payload bytes or CPU fraction'), mutable=True)
        try:
            for index, table in enumerate(TABLES):
                if index < state['table']:
                    continue
                last = state['last'] if index == state['table'] else None
                iterator = iter(rows(src, table, last))
                sentinel = object()
                while True:
                    if state['done'] < total and (ck.requested(output) or (quantum is not None and new >= quantum)):
                        state_put(target, 'state', state)
                        target.commit()
                        progress()
                        return dict(status='yielded', reason='Exact source database row boundary',
                                    completed=state['done'], total=total, logical_row_units=True,
                                    scientific_admission=False)
                    entry = next(iterator, sentinel)
                    if entry is sentinel:
                        break
                    row, last = entry
                    target.execute('INSERT INTO '+table+' VALUES('+','.join('?' for _ in row)+')', row)
                    state.update(table=index, last=last, done=state['done']+1)
                    new += 1
                    if new % 100 == 0:
                        state_put(target, 'state', state)
                        target.commit()
                    if new % 10000 == 0:
                        progress()
                state.update(table=index+1, last=None)
                state_put(target, 'state', state)
                target.commit()
            progress()
        except BaseException:
            target.rollback()
            raise
        finally:
            target.execute('PRAGMA wal_checkpoint(TRUNCATE)')
            target.close()
    finally:
        src.close()
    # A complete copy is still not verified. This is representation telemetry.
    result = dict(format='SLCHZ1', source=inputs['frame'], rows=counts,
                  checkpoint=checkpoint, source_bytes=source.stat().st_size,
                  destination_bytes=destination.stat().st_size,
                  scientific_admission=False, fresh_source_replay_still_required=True)
    original.write_json(output/'STORAGE.json', result)
    ck.seal(output, bound, ['PRIVATE_FRAME.sqlite', 'STORAGE.json'], check)
    return dict(status='complete', **result)


def _verify(output, inputs, config):
    output = Path(output)
    bound = binding(inputs, config)
    check = lambda:ck.require(output)
    if not ck.sealed(output, bound, check):
        raise ValueError('Complete sealed migration required')
    source = ck.checked(inputs['frame'], check)
    target_path = output/'PRIVATE_FRAME.sqlite'
    src, target = storage.connect(source), storage.connect(target_path)
    done = 0
    quantum = config.get('max_new_draws')
    started = time.process_time()
    try:
        counts, checkpoint = inspect(src)
        total = sum(counts.values())
        for table in TABLES:
            if src.execute('PRAGMA table_info('+table+')').fetchall() != target.execute('PRAGMA table_info('+table+')').fetchall():
                raise ValueError('Storage migration changed schema')
            expected, actual = iter(rows(src, table)), iter(rows(target, table))
            sentinel = object()
            while True:
                if done < total and (ck.requested(output) or (quantum is not None and done >= quantum)):
                    return dict(status='yielded', reason='Fresh migration verification row boundary',
                                completed=done, total=total, verification_prefix_credited=False,
                                restart_verification_at_row_zero=True)
                a, b = next(expected, sentinel), next(actual, sentinel)
                if a is sentinel and b is sentinel:
                    break
                if a != b:
                    raise ValueError('Migration changed a logical source value')
                done += 1
                if done % 10000 == 0:
                    original.write_json(output/'VERIFY_PROGRESS.json', dict(completed=done,total=total,
                                        source_start_row=0,invocation_cpu_seconds=time.process_time()-started,
                                        units='logical rows; not raw games, payload bytes or CPU fraction'), mutable=True)
        if done != total:
            raise ValueError('Migration row denominator differs')
        expected_receipt = dict(format='SLCHZ1', source=inputs['frame'], rows=counts,
                                checkpoint=checkpoint, source_bytes=source.stat().st_size,
                                destination_bytes=target_path.stat().st_size,
                                scientific_admission=False, fresh_source_replay_still_required=True)
        if json.loads((output/'STORAGE.json').read_text('utf8')) != expected_receipt:
            raise ValueError('Migration telemetry changed')
    finally:
        src.close()
        target.close()
    return dict(verified=True, every_logical_value_compared=True, rows=done,
                source_start_row=0, compressed_source_is_not_scientific_replay=True,
                fresh_source_replay_still_required=True)


def execute(output, inputs, config):
    return ck.guarded(_execute, output, inputs, config)


def verify(output, inputs, config):
    return ck.guarded(_verify, output, inputs, config)
