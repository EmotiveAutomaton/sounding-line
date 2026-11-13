"""CH7 source fixture with independently specified answers; v1 is retained.

DESIGN CHECK: LESSONS 3-5 reread 2026-11-13. Four declared result types
cover both sides: win/loss, loss/win, draw/draw and unknown/unknown. Exact
expected records are authored here without invoking the projection under test.
A damaged projection must fail even when execute and replay share that defect.
This source gate applies under both scientific null and alternative. The full
numerical qualification below is prepared, not implied by the source-only check.
"""
from pathlib import Path
import json
import sqlite3
from . import week5_ch7_fixture_v1 as numerical
from . import week5_ch7_source_v2 as source
from .week5_ch_source import digest, write_json


def source_case(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    raw = output / 'PRIVATE_CONSTRUCTED_RAW.sqlite'
    con = sqlite3.connect(raw)
    expected = []
    # These answers are specified independently of source.projected.
    cases = [('2017-04', '1-0', (1, -1)), ('2017-05', '0-1', (-1, 1)),
             ('2017-06', '1/2-1/2', (0, 0)), ('2017-06', '*', (None, None))]
    try:
        con.executescript('CREATE TABLE histories(month TEXT,ordinal INTEGER,payload TEXT,PRIMARY KEY(month,ordinal));CREATE TABLE settings(key TEXT PRIMARY KEY,value TEXT);')
        con.execute("INSERT INTO settings VALUES('constructed_fixture','true')")
        for i, (month, result, answers) in enumerate(cases):
            payload = dict(game=f'constructed-source-{i}', meta=dict(
                players=['constructed-one', 'constructed-two'], ratings=[1500, 1450],
                start=1500000000, end=None, initial=300, increment=2,
                time_control='blitz', rating_changes=[5, -5], result=result),
                first_clocks=[299, 298], rows=[
                    dict(player='constructed-one', ply=1, clock_before=299, think_time=3),
                    dict(player='constructed-two', ply=2, clock_before=298, think_time=4)])
            con.execute('INSERT INTO histories VALUES(?,?,?)', (month, i, json.dumps(payload, sort_keys=True)))
            for player, rating, opponent, change, clock, ply, think, answer in [
                ('constructed-one', 1500, 1450, 5, 299, 1, 3, answers[0]),
                ('constructed-two', 1450, 1500, -5, 298, 2, 4, answers[1]),
            ]:
                value = dict(game=f'constructed-source-{i}', month=month,
                    start=1500000000, end=None, initial=300, increment=2,
                    time_control='blitz', rating_change=change, result=answer,
                    first_clock=clock, rows=[dict(ply=ply, clock_before=clock, think_time=think)],
                    rating=rating, opponent_rating=opponent, source_ordinal=i)
                expected.append((player, month, f'constructed-source-{i}', json.dumps(value, sort_keys=True, separators=(',', ':'))))
        con.commit()
    finally:
        con.close()
    before = digest(raw)
    inputs = dict(histories=dict(path=str(raw), sha256=before))
    config = dict(constructed_fixture=True)
    target = output / 'projection'
    if source.execute(target, inputs, config)['status'] != 'complete':
        raise AssertionError('Source fixture did not finish')
    if not source.verify(target, inputs, config).get('verified'):
        raise AssertionError('Full raw source replay failed')
    with source.readonly_snapshot(target / 'PRIVATE_PLAYER_HISTORY.sqlite') as con:
        actual = con.execute('SELECT player,month,game,payload FROM player_history ORDER BY player,month,game').fetchall()
    if actual != sorted(expected):
        raise AssertionError('Independent constructed source answers differ')
    if digest(raw) != before:
        raise AssertionError('Source bytes changed')
    source.require_no_sidecars(raw)
    write_json(output / 'SOURCE_FIXTURE.json', dict(passed=True, source_games=4,
        player_games=8, result_cases=['white_win', 'black_win', 'draw', 'unknown'],
        independent_expected_rows=True, source_bytes_unchanged=True, full_raw_replay=True,
        contents_sha256=json.loads((target / 'INDEX.json').read_text())['contents_sha256']))


def execute(output, inputs, config):
    if inputs or config != {'constructed_fixture': True}:
        raise ValueError('Exact source-free fixture required')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    source_case(output / 'source')
    numerical.execute(output / 'numerical', inputs, config)
    for case, expected in [('null', 'mixed'), ('floor', 'floor'), ('ladder', 'ladder')]:
        result = json.loads((output / 'numerical' / case / 'analysis/SCIENCE.json').read_text())
        if result['pattern'] != expected:
            raise AssertionError(f'Constructed {case} joint shape rule failed')
        if case == 'null' and result['verdict'] != 'against':
            raise AssertionError('Null world did not return inside-band primary')
    write_json(output / 'QUALIFICATION.json', dict(passed=True, constructed_only=True,
        source_full_replay=True, full_numerical_cases=3, bootstrap_draws=2000,
        null_histories=20, scientific_admission=False))
    return dict(status='complete', constructed_fixture=True)


def verify(output, inputs, config):
    output = Path(output)
    fresh = output / 'independent_native'
    execute(fresh, inputs, config)
    for case in ('null', 'floor', 'ladder'):
        if digest(output / 'numerical' / case / 'analysis/SCIENCE.json') != digest(fresh / 'numerical' / case / 'analysis/SCIENCE.json'):
            raise ValueError('Fresh complete native numerical outputs differ')
    for relative in ('source/SOURCE_FIXTURE.json', 'QUALIFICATION.json'):
        if digest(output / relative) != digest(fresh / relative):
            raise ValueError('Fresh complete native source proof differs')
    return dict(verified=True, complete_raw_and_numerical_replay=True)
