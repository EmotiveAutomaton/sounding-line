"""R2 three-month unique-player quotas; no clocks or outcomes read.

DESIGN CHECK: complete source support, outcome-blind salted priority, exact
largest remainders, and honest shortfall accounting precede the raw sampler.
Temporary SQLite bounds candidate memory; only the final <=10,000 roster is
materialized. The original source and transactional sampler remain unchanged.
"""
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
import hashlib
import sqlite3

from . import week5_ch_source as source
from . import week5_ch_sample_bounded as sample
from . import week5_ch_pipeline_checkpoint as ck

MONTHS = ('2017-04', '2017-05', '2017-06')
QUOTAS = {'blitz': 7000, 'bullet': 1000, 'rapid': 1000, 'classical': 1000}


def allocate(counts, target):
    """Integer largest remainder, deterministic ties, no float round-off."""
    if type(target) is not int or target < 0 or any(type(n) is not int or n < 0 for n in counts.values()):
        raise ValueError('Nonnegative integer support required')
    total = sum(counts.values())
    target = min(target, total)
    if not total:
        return {key: 0 for key in counts}
    result = {key: target * count // total for key, count in counts.items()}
    remainder = target - sum(result.values())
    for key in sorted(counts, key=lambda key: (-(target * counts[key] % total), key))[:remainder]:
        result[key] += 1
    return result


def choose_players(database, players=10000, *, constructed=False, check=lambda: None):
    if type(players) is not int or not 1 <= players <= 10000 or (players != 10000 and not constructed):
        raise ValueError('Production retains the complete 10,000-player target')
    con = sqlite3.connect(f'file:{Path(database).resolve().as_posix()}?mode=ro', uri=True)
    # An empty SQLite filename is a private disk-backed temporary database.
    # Its candidate rows never become committed project output.
    unique = sqlite3.connect('')
    appearances = Counter()
    try:
        stamps = con.execute('SELECT month,complete FROM checkpoints ORDER BY month').fetchall()
        if stamps != [(month, 1) for month in MONTHS]:
            raise ValueError('Exactly three complete April/May/June 2017 sources required')
        unique.execute('PRAGMA temp_store=FILE')
        unique.execute('PRAGMA cache_size=-8192')
        unique.execute('CREATE TABLE chosen(player TEXT PRIMARY KEY,priority TEXT,month TEXT,tc TEXT,band INTEGER,n INTEGER,rating REAL,sample_rank TEXT)')
        unique.execute('CREATE INDEX sample_cell ON chosen(tc,month,band,sample_rank,player)')
        for index, row in enumerate(con.execute('SELECT player,month,tc,band,n,rating_sum/n FROM frame WHERE n>=20')):
            if index % 1000 == 0:
                check()
            player, month, tc, band, n, rating = row
            if month not in MONTHS or tc not in QUOTAS:
                raise ValueError('Unexpected eligible source stratum')
            appearances[(tc, month)] += 1
            priority = hashlib.sha256(f'{source.SEED}:eligibility:{player}:{month}:{tc}:{band}'.encode()).hexdigest()
            rank = hashlib.sha256(f'{source.SEED}:sample:{player}'.encode()).hexdigest()
            unique.execute('INSERT INTO chosen VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(player) DO UPDATE SET '
                           'priority=excluded.priority,month=excluded.month,tc=excluded.tc,band=excluded.band,'
                           'n=excluded.n,rating=excluded.rating,sample_rank=excluded.sample_rank '
                           'WHERE excluded.priority < chosen.priority',
                           (player, priority, month, tc, band, n, rating, rank))
        unique.commit()
        quotas = QUOTAS if players == 10000 else allocate(QUOTAS, players)
        selected, counts = [], {}
        for tc in QUOTAS:
            check()
            month_counts = {month: unique.execute('SELECT COUNT(*) FROM chosen WHERE tc=? AND month=?', (tc, month)).fetchone()[0]
                            for month in MONTHS}
            months = allocate(month_counts, quotas[tc])
            by_month = {}
            for month in MONTHS:
                bands = dict(unique.execute('SELECT band,COUNT(*) FROM chosen WHERE tc=? AND month=? GROUP BY band', (tc, month)))
                band_quota = allocate(bands, months[month])
                for band in sorted(bands):
                    for row in unique.execute('SELECT player,month,tc,band,n,rating FROM chosen WHERE tc=? AND month=? AND band=? '
                                              'ORDER BY sample_rank,player LIMIT ?', (tc, month, band, band_quota[band])):
                        selected.append(dict(zip(('player','month','time_control','band','eligible_games','rating'), row)))
                by_month[month] = dict(eligible_appearances=appearances[(tc,month)],
                                      assigned_unique_eligible=month_counts[month], selected=months[month],
                                      bands={str(b): dict(eligible=bands[b],selected=band_quota[b]) for b in sorted(bands)})
            counts[tc] = dict(target=quotas[tc],eligible=sum(month_counts.values()),selected=sum(months.values()),
                              shortfall=quotas[tc]-sum(months.values()),months=by_month)
        if len({r['player'] for r in selected}) != len(selected):
            raise AssertionError('Player assigned more than once')
        return sorted(selected,key=lambda row:row['player']), counts
    finally:
        con.close()
        unique.close()


@contextmanager
def selector(output, config):
    saved = source.choose_players
    source.choose_players = lambda database, players=10000: choose_players(
        database, players, constructed=bool(config.get('constructed_fixture')), check=lambda: ck.require(output))
    try:
        yield
    finally:
        source.choose_players = saved


def configured(config):
    allowed = {'phase','sources','players','max_new_draws','constructed_fixture'}
    if set(config)-allowed or config.get('phase') != 'sample':
        raise ValueError('Unexpected three-month sample configuration')
    if [row['month'] for row in config['sources']] != list(MONTHS):
        raise ValueError('Raw sources must be the complete ordered three-month frame')
    return dict(config, back_half_roster_sha256=source.digest(__file__),
                back_half_scope='R2:2017-04,2017-05,2017-06')


def execute(output, inputs, config):
    with selector(output, config):
        return sample.execute(output, inputs, configured(config))


def verify(output, inputs, config):
    with selector(output, config):
        return sample.verify(output, inputs, configured(config))
