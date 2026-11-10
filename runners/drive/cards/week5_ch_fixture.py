"""Native CH0/CH1 known-answer gate; no corpus effect is computed.

DESIGN CHECK: LESSONS 2-5. Null/alternative clock arithmetic is exact; malformed
inputs refuse. Single legal move and unique immediate mate require k50=1.
Unchanged fresh-process replay must reproduce every returned engine field.
"""
from pathlib import Path
import argparse,gzip,json,subprocess,sys
import chess
from .week5_ch_source import decode_headers,parse_game,roundtrip,write_json,digest,execute as source_execute,verify as source_verify
from .week5_ch_engine import score_batch,replay_scores

PGN='''[Event "Rated Blitz game"]
[White "fixture-white"]
[Black "fixture-black"]
[WhiteElo "1600"]
[BlackElo "1800"]
[TimeControl "300+2"]
[Result "*"]
[UTCDate "2017.04.01"]
[UTCTime "12:00:00"]

1. e4 { [%clk 0:05:00] } e5 { [%clk 0:04:59] }
2. Nf3 { [%clk 0:04:58] } Nc6 { [%clk 0:04:57] }
3. Bb5 { [%clk 0:04:57] } a6 { [%clk 0:04:59] } *
'''

def run(output,engine):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    meta,_=decode_headers(PGN,b'fixture-salt-not-human-data-12345')
    for _ in range(1000):roundtrip(PGN,meta)
    rows,counts,_=parse_game(PGN,meta)
    assert rows[4]['think_time']==3 and rows[5]['think_time'] is None
    source=output/'SOURCE.pgn';source.write_text(PGN*24,encoding='utf8')
    salt=output/'salt.bin';salt.write_bytes(b'fixture-salt-not-human-data-12345')
    pins=dict(source=dict(path=str(source),sha256=digest(source)),salt=dict(path=str(salt),sha256=digest(salt)))
    settings=dict(phase='census',month='2017-04')
    source_execute(output/'census',pins,settings)
    source_proof=source_verify(output/'census',pins,settings)
    (output/'yield').mkdir(exist_ok=True);write_json(output/'yield'/'YIELD_REQUEST.json',{'reason':'native fixture boundary'})
    yielded=source_execute(output/'yield',pins,settings)
    assert yielded['status']=='yielded' and not(output/'yield'/'SOURCE.json').exists()
    resume_inputs=dict(pins,resume_frame={k:yielded['checkpoint'][k] for k in ('path','sha256')})
    source_execute(output/'resume',resume_inputs,settings)
    assert (output/'resume'/'SOURCE.json').read_bytes()==(output/'census'/'SOURCE.json').read_bytes()
    one=chess.Board('8/8/8/8/8/1k6/r7/K7 w - - 0 1')
    assert one.legal_moves.count()==1
    mate=chess.Board('6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1')
    mating=[]
    for move in mate.legal_moves:
        copy=mate.copy();copy.push(move)
        if copy.is_checkmate():mating.append(move)
    assert len(mating)==1
    positions=[dict(fen=one.fen(),uci=next(iter(one.legal_moves)).uci()),dict(fen=mate.fen(),uci=mating[0].uci())]
    path=output/'POSITIONS.jsonl.gz'
    with gzip.open(path,'wt',encoding='utf8') as f:
        for row in positions:f.write(json.dumps(row)+'\n')
    batch=score_batch(path,engine,output/'scores',nodes=1000000,max_positions=2)
    scores=[json.loads(p.read_text()) for p in sorted((output/'scores').glob('*.json'))]
    assert len(scores)==2 and all(row['engine']['k50']==1 for row in scores)
    child=subprocess.run([sys.executable,'-X','utf8','-B','-m','runners.drive.cards.week5_ch_fixture','--verify','--output',str(output),'--engine',str(engine)],capture_output=True,text=True)
    if child.returncode:raise RuntimeError('Fresh engine verification failed: '+child.stderr[-2000:])
    report=dict(constructed=True,roundtrip_games=1000,clock_arithmetic=True,single_legal_move=True,unique_mate_in_one=True,
                engine_sha256=digest(engine),chess_version=chess.__version__,engine_positions=2,fresh_replay=json.loads(child.stdout),
                source_sha256=digest(__file__),source_module_sha256=digest(Path(__file__).with_name('week5_ch_source.py')),
                engine_module_sha256=digest(Path(__file__).with_name('week5_ch_engine.py')),
                source_handler_replay=source_proof,cooperative_yield_and_new_attempt_resume=True,scientific_admission=False)
    write_json(output/'COMPLETE.json',report);return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--engine',required=True);p.add_argument('--verify',action='store_true');a=p.parse_args()
    if a.verify:result=replay_scores(a.engine,sorted((Path(a.output)/'scores').glob('*.json')))
    else:result=run(a.output,a.engine)
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
