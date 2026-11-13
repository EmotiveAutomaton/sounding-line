"""CH7 snapshot reader repair; the v1 projection and population are preserved.

DESIGN CHECK: LESSONS 3-5 reread 2026-11-13. A stopped, authenticated,
checkpointed source must replay exactly without writes. Missing files, sidecars,
hash changes, incomplete sources and changed output rows must fail closed.
These are engineering gates, identical under a scientific null or alternative;
they guard evidence mutation and false qualification, not an effect direction.
Only the private output writer remains mutable. This adapter requires exclusive
ownership of stopped snapshots; immutable SQLite is not safe for a live source.
"""
from pathlib import Path
from contextlib import contextmanager
import hashlib
import json
import sqlite3

from . import week5_ch7_source_v1 as legacy
from . import week5_ch_history_index_bounded as base
from . import week5_ch_pipeline_checkpoint as ck
from .week5_ch_source import digest, write_json

MONTHS = legacy.MONTHS
projected = legacy.projected


def require_no_sidecars(path):
    for suffix in ('-wal', '-shm', '-journal'):
        if Path(str(path) + suffix).exists():
            raise ValueError('SQLite snapshot has a sidecar: ' + suffix)


@contextmanager
def readonly_snapshot(path):
    """Open an already stopped/checkpointed snapshot, never creating a file."""
    path = Path(path).resolve(strict=True)
    if not path.is_file():
        raise ValueError('SQLite snapshot must be an existing file')
    require_no_sidecars(path)
    con = sqlite3.connect(path.as_uri() + '?mode=ro&immutable=1', uri=True)
    try:
        con.execute('PRAGMA query_only=ON')
        require_no_sidecars(path)
        yield con
    finally:
        con.close()
        require_no_sidecars(path)


def source_info(inputs, config, check=None):
    source = ck.checked(inputs['histories'], check)
    with readonly_snapshot(source) as con:
        if config.get('constructed_fixture'):
            if con.execute("SELECT value FROM settings WHERE key='constructed_fixture'").fetchone() != ('true',):
                raise ValueError('Fixture requires constructed source')
        else:
            states = con.execute('SELECT complete FROM checkpoints').fetchall()
            if not states or not all(r[0] for r in states):
                raise ValueError('Incomplete source histories')
        months = tuple(r[0] for r in con.execute('SELECT DISTINCT month FROM histories ORDER BY month'))
        if months != MONTHS:
            raise ValueError('CH7 requires all three R2 source months')
        total = con.execute('SELECT count(*) FROM histories').fetchone()[0]
    return source, total


def source_rows(source, last=None):
    with readonly_snapshot(source) as con:
        query = 'SELECT month,ordinal,payload FROM histories'
        if last is not None:
            query += ' WHERE (month,ordinal)>(?,?)'
        query += ' ORDER BY month,ordinal'
        yield from con.execute(query, () if last is None else last)


def identity(inputs, config):
    if set(inputs) != {'histories'}:
        raise ValueError('Use sealed runtime continuation only')
    if set(config) - {'constructed_fixture', 'max_new_draws'}:
        raise ValueError('Unknown CH7 source configuration')
    return ck.binding(inputs, dict(config, months=list(MONTHS)), dict(
        adapter=digest(__file__), projection=digest(legacy.__file__),
        original_projection=digest(base.__file__)))


def contents_hash(database, control):
    h = hashlib.sha256()
    with readonly_snapshot(database) as con:
        for index, row in enumerate(con.execute('SELECT player,month,game,payload FROM player_history ORDER BY player,month,game')):
            if index % 1000 == 0 and ck.requested(control.root):
                return None
            h.update((json.dumps(row, separators=(',', ':')) + '\n').encode())
    return h.hexdigest()


def _execute(output, inputs, config):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    bound = identity(inputs, config)
    control = ck.Control(output, output, config, 'execute')
    check = lambda: ck.require(output)
    if ck.sealed(output, bound, check):
        return dict(status='complete', sealed_output_reused=True)
    source, total = source_info(inputs, config, check)
    database = output / 'PRIVATE_PLAYER_HISTORY.sqlite'
    if database.exists():
        ck.copied(database, output, check)
    # This connection owns only the new output, not an evidence snapshot.
    con = sqlite3.connect(database)
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA synchronous=FULL')
    con.executescript('CREATE TABLE IF NOT EXISTS player_history(player TEXT,month TEXT,game TEXT,payload TEXT,PRIMARY KEY(player,month,game)) WITHOUT ROWID;CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);')
    state = ck.initialize(con, bound, dict(last=None, source_records=0, player_games=0, moves=0))
    con.executemany('INSERT OR IGNORE INTO settings VALUES(?,?)', [('source_sha256', inputs['histories']['sha256']), ('constructed_fixture', json.dumps(bool(config.get('constructed_fixture')))), ('complete', 'false')])
    con.commit()
    since = 0

    def save(complete=False):
        nonlocal since
        ck.put(con, 'state', state)
        con.executemany('INSERT OR REPLACE INTO settings VALUES(?,?)', [('complete', json.dumps(complete)), ('player_games', str(state['player_games'])), ('moves', str(state['moves']))])
        con.commit()
        control.tick(since, state['source_records'], total)
        since = 0

    try:
        for month, ordinal, payload in source_rows(source, state['last']):
            if control.stop():
                save()
                return control.yielded(state['source_records'], total)
            for player, game in projected(month, ordinal, payload):
                con.execute('INSERT INTO player_history VALUES(?,?,?,?)', (player, month, game['game'], json.dumps(game, sort_keys=True, separators=(',', ':'))))
                state['player_games'] += 1
                state['moves'] += len(game['rows'])
            state['last'] = [month, ordinal]
            state['source_records'] += 1
            since += 1
            if since >= 500:
                save()
        save(True)
        players = con.execute('SELECT count(DISTINCT player) FROM player_history').fetchone()[0]
    except BaseException:
        con.rollback()
        raise
    finally:
        con.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        con.close()
    digest_ = contents_hash(database, control)
    if digest_ is None:
        return control.yielded(state['source_records'], total)
    result = dict(player_games=state['player_games'], moves=state['moves'], players=players, complete=True,
                  constructed_fixture=bool(config.get('constructed_fixture')), source_sha256=inputs['histories']['sha256'], contents_sha256=digest_)
    write_json(output / 'INDEX.json', result)
    ck.seal(output, bound, ['PRIVATE_PLAYER_HISTORY.sqlite', 'INDEX.json'], check)
    return dict(status='complete', **result)


def _verify(output, inputs, config):
    output = Path(output)
    control = ck.Control(output / 'verification', output, config, 'verify')
    done = games = moves = 0
    check = lambda: ck.require(output)
    if not ck.sealed(output, identity(inputs, config), check):
        raise ValueError('Complete projected history required')
    source, total = source_info(inputs, config, check)
    with readonly_snapshot(output / 'PRIVATE_PLAYER_HISTORY.sqlite') as target:
        for month, ordinal, payload in source_rows(source):
            if done % 500 == 0 and control.stop():
                return control.yielded(done, total)
            for player, game in projected(month, ordinal, payload):
                row = target.execute('SELECT payload FROM player_history WHERE player=? AND month=? AND game=?', (player, month, game['game'])).fetchone()
                if row != (json.dumps(game, sort_keys=True, separators=(',', ':')),):
                    raise ValueError('Full independent projected row differs')
                games += 1
                moves += len(game['rows'])
            done += 1
            if done % 500 == 0:
                control.tick(500, done, total)
        if target.execute('SELECT count(*) FROM player_history').fetchone()[0] != games:
            raise ValueError('Extra projected rows')
        players = target.execute('SELECT count(DISTINCT player) FROM player_history').fetchone()[0]
        expected_settings = dict(source_sha256=inputs['histories']['sha256'], constructed_fixture=json.dumps(bool(config.get('constructed_fixture'))), complete='true', player_games=str(games), moves=str(moves))
        if dict(target.execute('SELECT key,value FROM settings')) != expected_settings:
            raise ValueError('Projection settings changed')
    content = contents_hash(output / 'PRIVATE_PLAYER_HISTORY.sqlite', control)
    if content is None:
        return control.yielded(done, total)
    expected = dict(player_games=games, moves=moves, players=players, complete=True, constructed_fixture=bool(config.get('constructed_fixture')), source_sha256=inputs['histories']['sha256'], contents_sha256=content)
    if json.loads((output / 'INDEX.json').read_text(encoding='utf8')) != expected:
        raise ValueError('Index receipt differs')
    return dict(verified=True, complete_recalculation=True, source_start_ordinal=0, source_records=done, every_player_game_compared=games)


def execute(output, inputs, config):
    return ck.guarded(_execute, output, inputs, config)


def verify(output, inputs, config):
    return ck.guarded(_verify, output, inputs, config)
