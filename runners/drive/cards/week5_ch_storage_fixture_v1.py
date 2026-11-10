"""Constructed native fixture preparation for explicit CH history compression.

This is a counted-runtime execute/verify handler, not a launcher. No source,
engine or test executes on import. Owner qualification must additionally drive
the separate migration and census handlers through real native pause/copy/replay.
"""
from pathlib import Path
from types import SimpleNamespace
import json
import shutil
import sqlite3
import struct
from . import week5_ch_source as original
from . import week5_ch_census_replay as old_replay
from . import week5_ch_storage_v1 as storage
from . import week5_ch_storage_migrate_v1 as migration
from . import week5_ch_census_storage_v1 as census
from . import week5_ch_storage_consumers_v1 as consumers
from . import week5_ch_merge_bounded as merge
from . import week5_ch_sample_bounded as sample
from . import week5_ch_history_index_bounded as history
from .week5_ch_fixture import PGN


def pin(path):
    return dict(path=str(Path(path).resolve()), sha256=original.digest(path))


def refuse(call):
    try:
        call()
    except (ValueError, OSError, sqlite3.Error, UnicodeError):
        return True
    raise AssertionError('Required storage refusal did not occur')


def codec_checks():
    values = ['', 'ordinary short text', '雪🙂\n\x00'*1000,
              json.dumps(dict(value=-0.0, missing=None, array=[1,1.25,True]), sort_keys=True)*1000]
    for value in values:
        assert storage.decode(storage.encode(value)) == value
    packed = storage.encode('long known-answer payload '*1000)
    assert isinstance(packed, bytes)
    refuse(lambda:storage.decode(packed[:-1]))
    refuse(lambda:storage.decode(packed+b'extra trailing stream'))
    refuse(lambda:storage.decode(packed[:len(storage.MAGIC)+8]+b'x'*32+packed[len(storage.MAGIC)+40:]))
    refuse(lambda:storage.decode(storage.MAGIC+struct.pack('>Q',storage.MAX_PAYLOAD_BYTES+1)+b'0'*40))
    refuse(lambda:storage.decode(b'unknown codec'))
    refuse(lambda:storage.parameters('UPDATE histories SET payload=?', ('changed',)))
    refuse(lambda:storage.parameters('ATTACH DATABASE ? AS prior', ('unreviewed',)))
    return dict(exact_unicode_and_short_text=True, corrupt_truncated_trailing_oversize_refused=True,
                unreviewed_mutations_refused=True)


def execute(output, inputs, config):
    if inputs or config.get('phase') != 'constructed_storage_fixture':
        raise ValueError('This fixture takes no participant source')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if (output/'FIXTURE_INPUTS.json').exists():
        raise ValueError('Fixture execution is a new bounded attempt only')
    checks = codec_checks()
    real_shutil = storage.shutil
    try:
        storage.shutil = SimpleNamespace(disk_usage=lambda path:SimpleNamespace(free=0))
        refuse(lambda:storage.connect(output/'disk_refusal.sqlite', writable=True))
    finally:
        storage.shutil = real_shutil
    checks['disk_floor_refused_without_cleanup'] = True
    salt = output/'fixture_salt.bin'
    salt.write_bytes(b'fixture-salt-not-human-data-12345')
    for index in range(2000):
        pgn = PGN.replace('fixture-white', 'constructed-history-'+str(index))
        metadata, _ = original.decode_headers(pgn, salt.read_bytes())
        if any(original.selected_history(player) for player in metadata['players']):
            break
    else:
        raise AssertionError('Constructed history support missing')
    source = output/'constructed.pgn'
    source.write_text(pgn*48, encoding='utf8', newline='\n')
    pins = dict(source=pin(source), salt=pin(salt))
    cfg = dict(phase='census', month='2017-04', expected_games=48)
    original.execute(output/'old_prefix', pins, dict(cfg,max_games=24))
    original.execute(output/'old_full', pins, cfg)
    prefix = output/'old_prefix'/'PRIVATE_FRAME.sqlite'
    old_hash = original.digest(prefix)
    migration_inputs = dict(frame=pin(prefix))
    migration_config = dict(phase='storage_migration')
    migration.execute(output/'migration', migration_inputs, migration_config)
    converted = output/'migration'/'PRIVATE_FRAME.sqlite'
    storage.compare(prefix, converted, migration.TABLES)
    assert original.digest(prefix) == old_hash
    refuse(lambda:storage.connect(prefix, writable=True))
    refuse(lambda:storage.connect(output/'missing.sqlite'))
    with storage.bridge([original], output/'scope', [prefix]):
        refuse(lambda:original.sqlite3.connect(output/'outside.sqlite'))
    migrated = dict(pins, resume_frame=pin(converted))
    census.execute(output/'new_full', migrated, cfg)
    storage.compare(output/'old_full'/'PRIVATE_FRAME.sqlite', output/'new_full'/'PRIVATE_FRAME.sqlite', migration.TABLES)
    # An authenticated but false copied prefix must be rejected by raw replay.
    bad = output/'falsified_prefix.sqlite'
    shutil.copyfile(converted, bad)
    con = sqlite3.connect(bad)
    con.execute('UPDATE frame SET rating_sum=rating_sum+1')
    con.commit()
    con.close()
    bad_inputs = dict(pins, resume_frame=pin(bad))
    census.execute(output/'false_full', bad_inputs, cfg)
    routes = {}
    for label, source_db in [('plain', output/'old_full'/'PRIVATE_FRAME.sqlite'),
                              ('packed', output/'new_full'/'PRIVATE_FRAME.sqlite')]:
        root = output/label
        merge_inputs = dict(frame0=pin(source_db), salt=pin(salt))
        merge_cfg = dict(phase='merge')
        (merge if label=='plain' else consumers).execute(root/'merge', merge_inputs, merge_cfg)
        frame = root/'merge'/'PRIVATE_FRAME.sqlite'
        sample_inputs = dict(frame=pin(frame), salt=pin(salt))
        sample_cfg = dict(phase='sample', players=10000,
                          sources=[dict(pins['source'], month='2017-04')])
        (sample if label=='plain' else consumers).execute(root/'sample', sample_inputs, sample_cfg)
        history_inputs = dict(histories=pin(frame))
        history_cfg = dict(phase='history_index')
        (history if label=='plain' else consumers).execute(root/'history', history_inputs, history_cfg)
        routes[label] = dict(merge_inputs=merge_inputs, merge_config=merge_cfg,
                             sample_inputs=sample_inputs, sample_config=sample_cfg,
                             history_inputs=history_inputs, history_config=history_cfg)
    parity(output)
    raw = sqlite3.connect(output/'new_full'/'PRIVATE_FRAME.sqlite')
    try:
        encoded = raw.execute("SELECT count(*) FROM histories WHERE typeof(payload)='blob'").fetchone()[0]
        assert encoded > 0
        physical = raw.execute("SELECT payload FROM histories WHERE typeof(payload)='blob' LIMIT 1").fetchone()[0]
        refuse(lambda:json.loads(physical))
    finally:
        raw.close()
    result = dict(constructed=True, scientific_admission=False, checks=checks,
                  compressed_history_rows=encoded, original_prefix_unchanged=True)
    original.write_json(output/'FIXTURE_INPUTS.json', dict(original=pins, migrated=migrated,
                         bad=bad_inputs, config=cfg, migration_inputs=migration_inputs,
                         migration_config=migration_config, routes=routes))
    original.write_json(output/'FIXTURE_EXECUTE.json', result)
    return dict(status='complete', **result)


def parity(output):
    output = Path(output)
    storage.compare(output/'plain'/'merge'/'PRIVATE_FRAME.sqlite',
                    output/'packed'/'merge'/'PRIVATE_FRAME.sqlite', migration.TABLES)
    storage.compare(output/'plain'/'history'/'PRIVATE_PLAYER_HISTORY.sqlite',
                    output/'packed'/'history'/'PRIVATE_PLAYER_HISTORY.sqlite', ('player_history',))
    for name in ('PRIVATE_SELECTED_PLAYERS.json', 'PRIVATE_POSITIONS.jsonl.gz', 'SOURCE.json'):
        assert (output/'plain'/'sample'/name).read_bytes() == (output/'packed'/'sample'/name).read_bytes()
    a = json.loads((output/'plain'/'history'/'INDEX.json').read_text('utf8'))
    b = json.loads((output/'packed'/'history'/'INDEX.json').read_text('utf8'))
    # Physical source identity necessarily changes with representation. It must
    # be recorded, not falsified to manufacture byte-identical provenance.
    assert a.pop('source_sha256') != b.pop('source_sha256')
    assert a == b


def verify(output, inputs, config):
    if inputs or config.get('phase') != 'constructed_storage_fixture':
        raise ValueError('Constructed fixture identity changed')
    output = Path(output)
    saved = json.loads((output/'FIXTURE_INPUTS.json').read_text('utf8'))
    assert migration.verify(output/'migration', saved['migration_inputs'], saved['migration_config'])['verified']
    assert old_replay.verify(output/'old_full', saved['original'], saved['config'])['verified']
    assert census.verify(output/'new_full', saved['migrated'], saved['config'])['verified']
    refuse(lambda:census.verify(output/'false_full', saved['bad'], saved['config']))
    for label, settings in saved['routes'].items():
        for route, handler in [('merge',merge),('sample',sample),('history',history)]:
            module = handler if label=='plain' else consumers
            proof = module.verify(output/label/route, settings[route+'_inputs'], settings[route+'_config'])
            assert proof['verified']
    parity(output)
    return dict(verified=True, complete_recalculation=True, constructed=True,
                original_full_reference=True, fresh_full_raw_replay=True,
                false_rehashed_prefix_refused=True, complete_consumer_value_parity=True,
                scientific_admission=False, real_pause_copy_native_exit_proof_separate=True)
