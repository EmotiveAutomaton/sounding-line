"""CH1 corpus-native mate-in-one ruler validation, not a human effect.

DESIGN CHECK: LESSONS 2-5. Apply the puzzle's opponent move first. The puzzle
must have exactly one legal mating reply independently of the engine. k50=1
then follows for its immediate-mate ruler. Never accept the theme label alone.
"""
from pathlib import Path
import argparse,csv,json
import chess
from .week5_ch_source import source_stream,write_json,digest
from .week5_ch_engine import Scorer,replay_scores

def choose(path,count=10):
    result=[];seen=0
    with source_stream(path) as f:
        for ordinal,row in enumerate(csv.DictReader(f)):
            if 'mateIn1' not in row['Themes'].split():continue
            seen+=1;board=chess.Board(row['FEN']);moves=row['Moves'].split()
            if len(moves)<2:continue
            first=chess.Move.from_uci(moves[0])
            if first not in board.legal_moves:raise ValueError('Puzzle opening move invalid')
            board.push(first);mating=[]
            for move in list(board.legal_moves):
                test=board.copy();test.push(move)
                if test.is_checkmate():mating.append(move)
            if len(mating)!=1:continue
            if mating[0].uci()!=moves[1]:raise ValueError('Puzzle solution is not unique immediate mate')
            result.append(dict(fen=board.fen(),uci=mating[0].uci(),source_ordinal=ordinal))
            if len(result)==count:break
    if len(result)!=count:raise ValueError('Not enough independently verified unique mate puzzles')
    return result,seen

def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);count=config.get('count',10)
    positions,seen=choose(inputs['puzzles']['path'],count);scorer=Scorer(inputs['engine']['path'],1000000)
    try:
        for i,row in enumerate(positions):
            result=scorer.score(row)
            if result['engine']['k50']!=1:raise ValueError('Unique mate in one has incorrect k50')
            write_json(output/'scores'/f'{i:03}.json',result)
    finally:scorer.close()
    write_json(output/'RULER.json',dict(puzzles=count,mateIn1_candidates=seen,unique_mates_independently_verified=True,
                                     all_k50_equal_one=True,puzzle_archive_sha256=inputs['puzzles']['sha256']))
    return dict(status='complete',scientific_effect_computed=False)

def verify(output,inputs,config):
    result=replay_scores(inputs['engine']['path'],sorted((Path(output)/'scores').glob('*.json')))
    write_json(Path(output)/'VERIFY.json',result);return dict(verified=True,**result)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--puzzles',required=True);p.add_argument('--engine',required=True);a=p.parse_args()
    inputs=dict(puzzles=dict(path=a.puzzles,sha256=digest(a.puzzles)),engine=dict(path=a.engine,sha256=digest(a.engine)))
    execute(a.output,inputs,{});proof=verify(a.output,inputs,{})
    write_json(Path(a.output)/'COMPLETE.json',dict(constructed_known_answers=True,inputs=inputs,proof=proof,module_sha256=digest(__file__)))
    print(json.dumps(proof))

if __name__=='__main__':main()
