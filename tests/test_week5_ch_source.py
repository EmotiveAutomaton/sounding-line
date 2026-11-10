import io,json,sqlite3
from pathlib import Path
import pytest
from runners.drive.cards import week5_ch_source as s

PGN='''[Event "Rated Blitz game"]
[White "constructed-white"]
[Black "constructed-black"]
[WhiteElo "1600"]
[BlackElo "1800"]
[TimeControl "300+2"]
[Result "1-0"]
[UTCDate "2017.04.01"]
[UTCTime "12:00:00"]
[WhiteRatingDiff "5"]
[BlackRatingDiff "-5"]

1. e4 { [%clk 0:05:00] } e5 { [%clk 0:04:59] }
2. Nf3 { [%clk 0:04:58] } Nc6 { [%clk 0:04:57] }
3. Bb5 { [%clk 0:04:57] } a6 { [%clk 0:04:59] }
4. Ba4 { [%clk 0:04:55] } Nf6 { [%clk 0:04:53] } 1-0
'''

def test_clock_provenance_zero_and_first_two_moves():
    meta,reason=s.decode_headers(PGN,b'a'*32); assert reason is None
    rows,counts,first=s.parse_game(PGN,meta)
    assert [r['think_time'] for r in rows]==[None,None,None,None,3.,None,4.,8.]
    assert counts=={'first_two_moves':4,'positive_think_time':3,'zero_think_time':1}
    assert rows[4]['clock_before']==298 and rows[4]['rating']==1600
    assert rows[5]['side']==1 and rows[5]['clock_before']==297
    assert first==[300,299] # ordinary thinking can make first clock < initial
    assert 'constructed-white' not in json.dumps(meta)

def test_roundtrip_retains_full_features():
    meta,_=s.decode_headers(PGN,b'a'*32);s.roundtrip(PGN,meta)

def test_missing_clock_is_not_spanned():
    changed=PGN.replace('Nc6 { [%clk 0:04:57] }','Nc6')
    rows,counts,_=s.parse_game(changed,s.decode_headers(changed,b'a'*32)[0])
    assert rows[5]['clock_before'] is None and rows[5]['think_time'] is None

def test_time_control_boundaries():
    assert [s.control(x,0) for x in (179,180,479,480,1499,1500)]==['bullet','blitz','blitz','rapid','rapid','classical']

def test_source_refuses_nonstandard_and_missing_ids():
    assert s.decode_headers(PGN+'[Variant "Chess960"]\n',b'a'*32)[1]=='variant'
    assert s.decode_headers(PGN.replace('constructed-white','Anonymous'),b'a'*32)[1]=='missing_identity'

def test_census_reentry_and_frame(tmp_path):
    source=tmp_path/'source.pgn';source.write_text(PGN*25,encoding='utf8');db=tmp_path/'frame.sqlite'
    first=s.census(source,s.digest(source),'2017-04',b'a'*32,db,checkpoint_games=5)
    second=s.census(source,s.digest(source),'2017-04',b'a'*32,db)
    assert first==second and first['source_games']==25 and first['roundtrip_games']==25
    selected,counts=s.choose_players(db,100)
    assert len(selected)==2 and len({r['player'] for r in selected})==2
    con=sqlite3.connect(db);assert con.execute('SELECT SUM(n) FROM frame').fetchone()[0]==50;con.close()

def test_incomplete_census_cannot_define_sampling_frame(tmp_path):
    source=tmp_path/'source.pgn';source.write_text(PGN*25,encoding='utf8');db=tmp_path/'frame.sqlite'
    s.census(source,s.digest(source),'2017-04',b'a'*32,db,max_games=5)
    with pytest.raises(ValueError,match='Incomplete'):s.choose_players(db)
    result=s.census(source,s.digest(source),'2017-04',b'a'*32,db)
    assert result['source_games']==25

def test_same_identity_is_sampled_once_across_months(tmp_path):
    source=tmp_path/'source.pgn';source.write_text(PGN*25,encoding='utf8');db=tmp_path/'frame.sqlite'
    for month in ('2017-04','2017-05','2026-07'):s.census(source,s.digest(source),month,b'a'*32,db)
    chosen,_=s.choose_players(db,10000);assert len(chosen)==2

def test_book_denominator_counts_games_not_repeated_positions(tmp_path):
    text=PGN.split('\n\n')[0]+'\n\n1. Nf3 Nf6 2. Ng1 Ng8 3. e4 e5 1-0\n'
    source=tmp_path/'loop.pgn';source.write_text(text,encoding='utf8');db=tmp_path/'frame.sqlite'
    s.census(source,s.digest(source),'2017-04',b'a'*32,db)
    con=sqlite3.connect(db)
    position='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -'
    assert con.execute('SELECT n FROM opening_positions WHERE position=?',(position,)).fetchone()[0]==1
    assert con.execute('SELECT SUM(n) FROM openings WHERE position=?',(position,)).fetchone()[0]==2
    con.close()

def test_supervisor_yield_and_authenticated_new_attempt_resume(tmp_path):
    source=tmp_path/'source.pgn';source.write_text(PGN*24,encoding='utf8');salt=tmp_path/'salt.bin';salt.write_bytes(b'a'*32)
    first=tmp_path/'first';first.mkdir();(first/'YIELD_REQUEST.json').write_text('{"reason":"fixture boundary"}')
    pins={'source':{'path':str(source),'sha256':s.digest(source)},'salt':{'path':str(salt),'sha256':s.digest(salt)}}
    result=s.execute(first,pins,{'phase':'census','month':'2017-04'})
    assert result['status']=='yielded' and not(first/'SOURCE.json').exists()
    later=tmp_path/'later';pins['resume_frame']={'path':result['checkpoint']['path'],'sha256':result['checkpoint']['sha256']}
    s.execute(later,pins,{'phase':'census','month':'2017-04'})
    assert json.loads((later/'SOURCE.json').read_text())['source_games']==24
    altered=tmp_path/'bad';salt.write_bytes(b'b'*32)
    with pytest.raises(ValueError,match='salt'):s.execute(altered,pins,{'phase':'census','month':'2017-04'})

