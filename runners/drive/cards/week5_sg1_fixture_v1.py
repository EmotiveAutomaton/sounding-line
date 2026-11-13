"""Independent hand-written SG1 packet answers; constructed inputs only.

Input census construction uses the previously frozen parser, never SG1. Expected
answers below are literals/arithmetic from the stated moves and packet table,
not calls to the SG1 adapter. Production and replay sharing a bug must fail.
"""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sqlite3

from . import week5_ch_source as old
from . import week5_sg1_source_v1 as sg1
from . import week5_sg1_fields_v1 as fields

SALT = b'constructed-SG1-source-only-32byte'
NAME = 'Constructed Player'


def pgn(start, own, opponent, opponent_name, result, first=180,
        tournament=False, termination='Normal', black=False, moves=None):
    when = datetime.fromtimestamp(start, timezone.utc)
    names = [NAME, opponent_name]
    ratings = [own, opponent]
    changes = [-12 if result == '0-1' else 11 if result == '1-0' else 0, 12]
    if black:
        names.reverse()
        ratings.reverse()
        changes.reverse()
    headers = dict(Event='Rated Blitz tournament https://lichess.org/tournament/CONSTRUCTED' if tournament else 'Rated Blitz game',
                   White=names[0], Black=names[1], WhiteElo=ratings[0], BlackElo=ratings[1],
                   WhiteRatingDiff=changes[0], BlackRatingDiff=changes[1],
                   UTCDate=when.strftime('%Y.%m.%d'), UTCTime=when.strftime('%H:%M:%S'),
                   TimeControl='180+0', Result=result, Termination=termination)
    def clock(v):
        return f'{{[%clk 0:{v//60:02}:{v%60:02}]}}'
    if moves is None:
        a, b = (180, first) if black else (first, 180)
        moves = f'1. e4 {clock(a)} e5 {clock(b)} 2. Nf3 {clock(a-10)} Nc6 {clock(b-5)} 3. Bb5 {clock(a-20)} a6 {clock(b-15)}'
    return '\n'.join(f'[{k} "{v}"]' for k,v in headers.items()) + '\n\n' + moves + ' ' + result + '\n\n'


def build(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    salt_path = root / 'PRIVATE_CONSTRUCTED_SALT.bin'
    salt_path.write_bytes(SALT)
    april = datetime(2017, 4, 1, tzinfo=timezone.utc).timestamp()
    may = datetime(2017, 5, 1, tzinfo=timezone.utc).timestamp()
    june = datetime(2017, 6, 1, tzinfo=timezone.utc).timestamp()
    raw = [
        [pgn(april+s, own, opp, name, result, first, tour)
         for s,own,opp,name,result,first,tour in
         [(0,1500,1400,'A','0-1',180,False),
          (400,1488,1412,'A','1-0',180,False),
          (900,1499,1700,'B','0-1',180,False),
          (2760,1495,1300,'C','1-0',90,True),
          (3100,1498,1500,'D','1/2-1/2',180,True)]],
        [pgn(may,1500,1400,'E','1-0',termination='Time forfeit',black=True)],
        [pgn(june,1500,1500,'F','0-1',termination='Unspecified constructed reason',
             moves='1. f3 {[%clk 0:03:00]} e5 {[%clk 0:03:00]} 2. g4 {[%clk 0:02:50]} Qh4# {[%clk 0:02:55]}')]]
    inputs = {'salt': dict(path=str(salt_path), sha256=old.digest(salt_path))}
    database = root / 'PRIVATE_CONSTRUCTED_CENSUS.sqlite'
    con = old.open_database(database)
    player = old.pseudonym(NAME, SALT)
    con.executemany('INSERT INTO settings VALUES(?,?)', [('salt_sha256',old.digest(salt_path)),('constructed_fixture','true')])
    for month, key, texts in zip(sg1.MONTHS, sg1.RAW_KEYS, raw):
        path = root / (month + '.pgn')
        path.write_text(''.join(texts), encoding='utf8', newline='\n')
        pin = old.digest(path)
        inputs[key] = dict(path=str(path), sha256=pin)
        for ordinal,text in enumerate(texts):
            meta,reason = old.decode_headers(text,SALT)
            assert reason is None
            rows,dispositions,first = old.parse_game(text,meta)
            payload = dict(game=hashlib.sha256((pin+':'+str(ordinal)).encode()).hexdigest(),
                meta=meta, rows=[r for r in rows if r['player']==player],
                dispositions=dispositions, first_clocks=first)
            con.execute('INSERT INTO histories VALUES(?,?,?)', (month,ordinal,json.dumps(payload,sort_keys=True)))
        con.execute('INSERT INTO checkpoints VALUES(?,?,?,?,?)',
                    (month,len(texts)-1,pin,json.dumps(dict(source_games=len(texts),parse_failure=0)),1))
    con.commit()
    con.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    con.close()
    inputs['histories'] = dict(path=str(database),sha256=old.digest(database))
    return inputs, player


def oracle(output, player):
    with sg1.HistoryStore(Path(output)/'PRIVATE_PLAYER_HISTORY.sqlite', True) as store:
        rows = sorted(store[player], key=lambda r:(r['month'],r['source_ordinal']))
    april = datetime(2017,4,1,tzinfo=timezone.utc).timestamp()
    expected = [
        (0,1500,1400,-1,0.,180,False,True,False,False,1,False,35.),
        (400,1488,1412,1,1.,180,False,False,False,False,2,False,35.),
        (900,1499,1700,-1,0.,180,False,False,True,False,3,False,35.),
        (2760,1495,1300,1,1.,90,True,False,False,False,1,True,35.),
        (3100,1498,1500,0,.5,180,True,None,None,True,2,False,35.)]
    keys = ['start','rating','opponent_rating','result','score','first_clock','tournament',
            'rematch','stop','censored','index_in_session','berserk_candidate','duration_est']
    for index, (row, answer) in enumerate(zip(rows[:5],expected)):
        answer = (answer[0]+april,)+answer[1:]
        assert tuple(row[k] for k in keys) == answer, 'Independent SG1 packet answers differ'
        assert row['source_ordinal'] == index and row['colour']=='white'
        assert row['own_first_move']=='e2e4' and row['opponent_first_move'] is None
        assert row['final_material_balance']==0 and not row['last_move_checkmate']
        assert row['rows']==[dict(ply=1,clock_before=None,think_time=None),
                             dict(ply=3,clock_before=row['first_clock'],think_time=None),
                             dict(ply=5,clock_before=row['first_clock']-10,think_time=10.)]
        assert row['own_last_clock']==row['first_clock']-20 and row['opponent_last_clock']==165
    assert len(rows)==7
    assert rows[0]['session_id']==rows[1]['session_id']==rows[2]['session_id']
    assert rows[3]['session_id']==rows[4]['session_id']!=rows[0]['session_id']
    assert [r['seconds_to_next'] for r in rows[:5]] == [400.,500.,1860.,340.,None]
    assert rows[5]['colour']=='black' and rows[5]['own_first_move']=='e7e5'
    assert rows[5]['opponent_first_move']=='e2e4'
    assert rows[5]['duration_est']==200. and rows[5]['termination']=='Time forfeit'
    assert rows[6]['last_move_checkmate'] and rows[6]['duration_est']==15.
    assert rows[6]['termination']=='Unspecified constructed reason'
    assert rows[5]['censored'] and rows[6]['censored']
    return rows


def source_case(root):
    root = Path(root)
    inputs, player = build(root)
    output = root/'output'
    before = {key:old.digest(value['path']) for key,value in inputs.items()}
    assert sg1.execute(output,inputs,dict(constructed_fixture=True))['status']=='complete'
    assert sg1.verify(output,inputs,dict(constructed_fixture=True))['verified']
    rows = oracle(output,player)
    assert {key:old.digest(value['path']) for key,value in inputs.items()}==before
    assert not list(root.rglob('*-wal')) and not list(root.rglob('*-shm'))
    old.write_json(root/'FIXTURE.json',dict(passed=True, source_games=7, player_games=7,
        expected_values_independent=True, source_preserved=True,
        full_raw_replay=True, unknown_termination_retained=True,
        constructed_only=True, packet_table_checked=True))
    return inputs,player,rows


def execute(output,inputs,config):
    if inputs or config:
        raise ValueError('Constructed fixture takes no corpus/config')
    source_case(Path(output)/'case')
    return dict(status='complete',constructed_fixture=True)


def verify(output,inputs,config):
    execute(Path(output)/'independent',inputs,config)
    return dict(verified=True,complete_recalculation=True,constructed_fixture=True)
