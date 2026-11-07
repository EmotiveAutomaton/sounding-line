"""Native literal chess-source replay on a constructed known answer.

DESIGN CHECK: LESSONS 2-5. Sampling and annotation arithmetic run through the
actual consumer before month preparation. A fixture is not a population study.
"""
from pathlib import Path
import pyarrow as pa
from runners.stage14.common import read,freeze,filehash
from . import chess_source as c

def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);p=output/'fixture.zst'
    text='[Event "constructed"]\n[WhiteElo "1500"]\n[BlackElo "1600"]\n[TimeControl "60+2"]\n\n1. e4 {[%eval 0.2] [%clk 0:00:59]} e5 {[%eval 0.4] [%clk 0:01:00]} 2. Nf3 {[%eval 0.1] [%clk 0:00:57]} *\n'
    with pa.CompressedOutputStream(str(p),'zstd') as f:f.write(text.encode())
    inp=dict(source=dict(path=str(p),sha256=filehash(p)))
    c.execute(output/'consumer',inp,dict(sample_probability=1))
    s=read(output/'consumer/SOURCE.json');assert s['source_games']==1 and s['moves']==2
    freeze(output/'INPUTS.json',inp);return dict(constructed=True,actual_handler_executed=True)

def verify(output,inputs,config):
    output=Path(output);c.verify(output/'consumer',read(output/'INPUTS.json'),dict(sample_probability=1))
    return dict(verified=True,complete_handler_replay=True)
