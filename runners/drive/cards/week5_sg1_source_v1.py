"""SG1: one complete raw-month traversal per execute and fresh verification.

DESIGN CHECK: exact original 2% histories, CH7-column parity and full raw replay.
Only the new private output database is writable. Existing snapshot sidecars
are refused. Work is checkpointed by selected source games, then whole players;
a 5% row prefix is not a 5% CPU claim. No engine or scoring is used.
"""
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
import hashlib
import json
import sqlite3

from . import week5_ch_source as source
from . import week5_ch7_source_v2 as snapshots
from . import week5_sg1_fields_v1 as fields
from . import week5_ch_pipeline_checkpoint as ck

MONTHS = ('2017-04', '2017-05', '2017-06')
RAW_KEYS = ('raw_april', 'raw_may', 'raw_june')


def dumps(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def identity(inputs, config):
    if set(inputs) != {'histories', 'salt', *RAW_KEYS}:
        raise ValueError('SG1 needs exact complete history, salt and three raw month pins')
    if set(config) - {'constructed_fixture', 'max_new_draws'}:
        raise ValueError('Unknown SG1 configuration')
    return ck.binding(inputs, config, dict(adapter=source.digest(__file__),
        fields=source.digest(fields.__file__), parser=source.digest(source.__file__),
        snapshot=source.digest(snapshots.__file__), legacy_projection=source.digest(fields.ch7.__file__)))


def authenticate(inputs, config, root):
    paths = {key: ck.checked(value, lambda: ck.require(root)) for key, value in inputs.items()}
    salt = paths['salt'].read_bytes()
    with snapshots.readonly_snapshot(paths['histories']) as con:
        settings = dict(con.execute('SELECT key,value FROM settings'))
        if settings.get('salt_sha256') != hashlib.sha256(salt).hexdigest():
            raise ValueError('History and salt differ')
        if config.get('constructed_fixture') and settings.get('constructed_fixture') != 'true':
            raise ValueError('Constructed fixture source required')
        census = list(con.execute('SELECT month,ordinal,source,counts,complete FROM checkpoints ORDER BY month'))
        if tuple(r[0] for r in census) != MONTHS or not all(r[4] == 1 for r in census):
            raise ValueError('All three completed original months required')
        for row, key in zip(census, RAW_KEYS):
            if row[2] != inputs[key]['sha256']:
                raise ValueError('Raw month differs from completed census')
        total = con.execute('SELECT count(*) FROM histories').fetchone()[0]
        if total < 1:
            raise ValueError('Empty history source')
    return paths, salt, census, total


def original_games(paths, census, root, after=None):
    """Original membership, original ordinals; stream unused games without parsing."""
    with snapshots.readonly_snapshot(paths['histories']) as con:
        for (month, last_raw, raw_sha, _, _), key in zip(census, RAW_KEYS):
            if after is not None and month < after[0]:
                continue
            minimum = after[1] if after is not None and month == after[0] else -1
            cursor = con.execute('SELECT ordinal,payload FROM histories WHERE month=? AND ordinal>? ORDER BY ordinal',
                                 (month, minimum))
            wanted = next(cursor, None)
            last_seen = -1
            with source.source_stream(paths[key]) as stream:
                for ordinal, text in enumerate(source.records(stream)):
                    last_seen = ordinal
                    if ordinal % 100 == 0:
                        ck.require(root)
                    if wanted is not None and ordinal == wanted[0]:
                        expected_game = hashlib.sha256((raw_sha + ':' + str(ordinal)).encode()).hexdigest()
                        if json.loads(wanted[1])['game'] != expected_game:
                            raise ValueError('Original game identity differs from raw source ordinal')
                        yield month, ordinal, text, wanted[1]
                        wanted = next(cursor, None)
            if wanted is not None or last_seen != last_raw:
                raise ValueError('Raw traversal coverage differs from completed census')


def open_output(path):
    con = sqlite3.connect(path)
    con.executescript('PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL;'
        'CREATE TABLE IF NOT EXISTS player_history(player TEXT,month TEXT,game TEXT,payload TEXT,'
        'PRIMARY KEY(player,month,game)) WITHOUT ROWID;'
        'CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);')
    return con


def settings_put(con, values):
    con.executemany('INSERT OR REPLACE INTO settings VALUES(?,?)', list(values.items()))


def content_hash(path, root):
    h = hashlib.sha256()
    with snapshots.readonly_snapshot(path) as con:
        for ordinal, row in enumerate(con.execute('SELECT player,month,game,payload FROM player_history ORDER BY player,month,game')):
            if ordinal % 500 == 0:
                ck.require(root)
            h.update((dumps(list(row)) + '\n').encode())
    return h.hexdigest()


def histogram_add(total, more):
    for group in more:
        for key, value in more[group].items():
            if key == 'bins':
                total[group][key] = [a+b for a,b in zip(total[group][key], value)]
            else:
                total[group][key] += value


def _execute(output, inputs, config):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    bound = identity(inputs, config)
    if ck.sealed(output, bound, lambda: ck.require(output)):
        return dict(status='complete', sealed_output_reused=True)
    paths, salt, census, total = authenticate(inputs, config, output)
    database = output / 'PRIVATE_PLAYER_HISTORY.sqlite'
    if database.exists():
        ck.copied(database, output, lambda: ck.require(output))
    con = open_output(database)
    state = ck.initialize(con, bound, dict(phase='source', last=None, source_records=0,
        player_games=0, moves=0, source_failures=0, last_player=None, players_done=0,
        histogram=fields.histogram([]), dispositions={}))
    settings_put(con, dict(complete='false', constructed_fixture=json.dumps(bool(config.get('constructed_fixture'))),
                          source_sha256=inputs['histories']['sha256'], adapter_sha256=source.digest(__file__)))
    con.commit()
    control = ck.Control(output, output, config, 'execute')
    since = 0

    def save():
        nonlocal since
        ck.put(con, 'state', state)
        con.commit()
        denominator = total if state['phase'] == 'source' else max(state.get('players_total', 0), 1)
        done = state['source_records'] if state['phase'] == 'source' else state['players_done']
        control.tick(since, done, denominator)
        since = 0

    try:
        if state['phase'] == 'source':
            for month, ordinal, text, prior in original_games(paths, census, output, state['last']):
                if control.stop():
                    save()
                    return control.yielded(state['source_records'], total)
                try:
                    emitted = list(fields.project(text, month, ordinal, prior, salt))
                except (ValueError, KeyError, IndexError):
                    state['source_failures'] += 1
                    save()
                    source.write_json(output / 'SOURCE_FAILURE.json',
                        dict(reason='Selected history failed raw reconstruction; no partial population admitted',
                             source_failures=state['source_failures']))
                    raise ValueError('Selected source failed reconstruction; aggregate failure receipt retained') from None
                for player, row in emitted:
                    con.execute('INSERT INTO player_history VALUES(?,?,?,?)',
                                (player, month, row['game'], dumps(row)))
                    state['player_games'] += 1
                    state['moves'] += len(row['rows'])
                    counts = Counter(state['dispositions'])
                    counts['duration:' + row['duration_status']] += 1
                    counts['missing_tournament_id'] += int(row['tournament'] and row['tournament_id'] is None)
                    counts['unknown_termination'] += int(row['termination'] not in ('Normal', 'Time forfeit'))
                    state['dispositions'] = dict(counts)
                state['last'] = [month, ordinal]
                state['source_records'] += 1
                since += 1
                if since >= 100:
                    save()
            if state['source_records'] != total:
                raise ValueError('Original history coverage incomplete')
            save()
            state['phase'] = 'sessions'
            state['players_total'] = con.execute('SELECT count(DISTINCT player) FROM player_history').fetchone()[0]
            save()
        if state['phase'] == 'sessions':
            players = con.execute('SELECT DISTINCT player FROM player_history WHERE player>? ORDER BY player',
                                  (state['last_player'] or '',)).fetchall()
            for (player,) in players:
                if control.stop():
                    save()
                    return control.yielded(state['players_done'], state['players_total'])
                games = [json.loads(r[0]) for r in con.execute('SELECT payload FROM player_history WHERE player=? ORDER BY month,game', (player,))]
                extended = fields.session_rows(games)
                for row in extended:
                    con.execute('UPDATE player_history SET payload=? WHERE player=? AND month=? AND game=?',
                                (dumps(row), player, row['month'], row['game']))
                histogram_add(state['histogram'], fields.histogram(extended))
                state['last_player'] = player
                state['players_done'] += 1
                since += 1
                save()
            state['phase'] = 'complete'
            save()
        settings_put(con, dict(complete='true', player_games=str(state['player_games']), moves=str(state['moves'])))
        con.commit()
    except BaseException:
        con.rollback()
        raise
    finally:
        con.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        con.close()
    result = dict(complete=True, constructed_fixture=bool(config.get('constructed_fixture')),
        source_sha256=inputs['histories']['sha256'], source_records=state['source_records'],
        player_games=state['player_games'], players=state['players_done'], moves=state['moves'],
        source_failures=state['source_failures'], dispositions=state['dispositions'],
        inherited_source_dispositions={r[0]: json.loads(r[3]) for r in census},
        contents_sha256=content_hash(database, output),
        sg1v=dict(histogram=state['histogram'], flag_admitted=False,
                  status='Histogram produced; owner review of two modes and non-tournament rate required'),
        record_kind='run', theory_tags=['H15-T1', 'H15-T2'], by_construction=True,
        activation=[], interpretation='Source preparation only; no channel or behavioral inference.')
    source.write_json(output / 'INDEX.json', result)
    ck.seal(output, bound, ['PRIVATE_PLAYER_HISTORY.sqlite', 'INDEX.json'], lambda: ck.require(output))
    return dict(status='complete', source_records=state['source_records'], player_games=state['player_games'])


def _verify(output, inputs, config):
    output = Path(output)
    if not ck.sealed(output, identity(inputs, config), lambda: ck.require(output)):
        raise ValueError('Complete SG1 output required')
    paths, salt, census, total = authenticate(inputs, config, output)
    index = json.loads((output / 'INDEX.json').read_text(encoding='utf8'))
    games = moves = records = 0
    hist = fields.histogram([])
    dispositions = Counter()
    database = output / 'PRIVATE_PLAYER_HISTORY.sqlite'
    with snapshots.readonly_snapshot(database) as con:
        for month, ordinal, text, prior in original_games(paths, census, output):
            for player, row in fields.project(text, month, ordinal, prior, salt):
                found = con.execute('SELECT payload FROM player_history WHERE player=? AND month=? AND game=?',
                                    (player, month, row['game'])).fetchone()
                if found is None:
                    raise ValueError('SG1 replay missing original player-game')
                actual = json.loads(found[0])
                if {k:v for k,v in actual.items() if k not in fields.SESSION_COLUMNS} != row:
                    raise ValueError('SG1 full raw projection replay differs')
                games += 1
                moves += len(row['rows'])
                dispositions['duration:' + row['duration_status']] += 1
                dispositions['missing_tournament_id'] += int(row['tournament'] and row['tournament_id'] is None)
                dispositions['unknown_termination'] += int(row['termination'] not in ('Normal', 'Time forfeit'))
            records += 1
        if con.execute('SELECT count(*) FROM player_history').fetchone()[0] != games:
            raise ValueError('SG1 has extra player-game rows')
        players = 0
        for (player,) in con.execute('SELECT DISTINCT player FROM player_history ORDER BY player'):
            ck.require(output)
            stored = [json.loads(r[0]) for r in con.execute('SELECT payload FROM player_history WHERE player=? ORDER BY month,game', (player,))]
            raw = [{k:v for k,v in r.items() if k not in fields.SESSION_COLUMNS} for r in stored]
            expected = fields.session_rows(raw)
            if stored != expected:
                raise ValueError('SG1 chronological session replay differs')
            histogram_add(hist, fields.histogram(expected))
            players += 1
        settings = dict(con.execute('SELECT key,value FROM settings'))
        if settings != dict(complete='true', constructed_fixture=json.dumps(bool(config.get('constructed_fixture'))),
                            source_sha256=inputs['histories']['sha256'], adapter_sha256=source.digest(__file__),
                            player_games=str(games), moves=str(moves)):
            raise ValueError('SG1 source settings differ')
    if (records != total or index['source_records'] != records or index['player_games'] != games or
            index['moves'] != moves or index['players'] != players or
            index['dispositions'] != dict(dispositions) or index['sg1v']['histogram'] != hist or
            index['contents_sha256'] != content_hash(database, output)):
        raise ValueError('SG1 aggregate replay differs')
    return dict(verified=True, complete_recalculation=True, source_start_ordinal=0,
                raw_months_retraversed=3, source_records=records, player_games=games,
                full_session_recalculation=True, no_duplicate_full_database=True)


def execute(output, inputs, config):
    return ck.guarded(_execute, output, inputs, config)


def verify(output, inputs, config):
    # A yield during verification restarts this bounded raw stream from zero in
    # the next counted attempt. No verified prefix is credited as whole replay.
    return ck.guarded(_verify, output, inputs, config)


class HistoryStore(Mapping):
    """CH6/CH7-compatible source interface, immutable for its whole lifetime."""
    def __init__(self, path, constructed=False):
        self.manager = snapshots.readonly_snapshot(path)
        self.con = self.manager.__enter__()
        try:
            settings = dict(self.con.execute('SELECT key,value FROM settings'))
            if settings.get('complete') != 'true' or settings.get('constructed_fixture') != json.dumps(constructed):
                raise ValueError('Complete SG1 source of the declared kind required')
            if settings.get('adapter_sha256') != source.digest(__file__):
                raise ValueError('Different SG1 adapter')
        except BaseException:
            self.manager.__exit__(None, None, None)
            raise
    def __iter__(self):
        return (r[0] for r in self.con.execute('SELECT DISTINCT player FROM player_history ORDER BY player'))
    def __len__(self):
        return self.con.execute('SELECT count(DISTINCT player) FROM player_history').fetchone()[0]
    def __getitem__(self, player):
        values = [json.loads(r[0]) for r in self.con.execute('SELECT payload FROM player_history WHERE player=? ORDER BY month,game', (player,))]
        if not values:
            raise KeyError(player)
        return values
    def close(self):
        self.manager.__exit__(None, None, None)
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()


def authenticate_consumer(inputs, config, root):
    required = {'histories'} if config.get('constructed_fixture') else {'histories', 'index', 'source_seal', 'source_complete', 'source_verified'}
    if set(inputs) != required:
        raise ValueError('SG1 complete, independent replay and sealed table inputs required')
    paths = {key: ck.checked(value, lambda: ck.require(root)) for key, value in inputs.items()}
    if not config.get('constructed_fixture'):
        index = json.loads(paths['index'].read_text(encoding='utf8'))
        seal = json.loads(paths['source_seal'].read_text(encoding='utf8'))
        if (not index.get('complete') or index.get('constructed_fixture') or
                seal['files'].get('PRIVATE_PLAYER_HISTORY.sqlite') != inputs['histories']['sha256'] or
                seal['files'].get('INDEX.json') != inputs['index']['sha256'] or
                seal['binding']['implementation'].get('adapter') != source.digest(__file__)):
            raise ValueError('Unqualified SG1 projection')
        # Runtime receipt schemas and native identities are owner admission
        # obligations. Their exact immutable bytes are required and pinned here.
        if not paths['source_complete'].stat().st_size or not paths['source_verified'].stat().st_size:
            raise ValueError('Empty runtime qualification receipt')
    return paths['histories']
