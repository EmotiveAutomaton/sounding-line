import chess,chess.engine
import numpy as np
import pytest
from runners.drive.cards import week5_ch_engine as e

def info(uci,cp,turn=chess.WHITE):
    return dict(pv=[chess.Move.from_uci(uci)],score=chess.engine.PovScore(chess.engine.Cp(cp),turn),nodes=100)

def test_closeness_boundaries_and_played_outside_top():
    rows=[info('e2e4',100),info('d2d4',50),info('g1f3',49)]
    result=e.summarize(rows,True,'b1c3',info('b1c3',-20))
    assert result['k50']==2 and result['k100']==3 and result['centipawn_loss']==120

def test_black_perspective_is_not_white_score():
    r=e.summarize([info('e7e5',-10),info('d7d5',-90)],False,'e7e5')
    assert r['top'][0]['move']=='d7d5' and r['centipawn_loss']==80

def test_unique_mate_is_distinct_from_longer_mates():
    assert e.cp_value(chess.engine.Mate(1))-e.cp_value(chess.engine.Mate(2))>50
    assert e.cp_value(chess.engine.Mate(-1))<e.cp_value(chess.engine.Cp(-10000))

def test_entropy_and_temperature():
    assert e.policy_entropy([0,0,0],100)==pytest.approx(np.log(3))
    assert e.policy_entropy([10000,0],100)<1e-10
    low=e.fit_temperature([[0,-100]]*50,[0]*50)
    high=e.fit_temperature([[0,-100]]*50,[0,1]*25)
    assert low['temperature']<high['temperature']

