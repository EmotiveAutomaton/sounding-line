import pyarrow as pa
from runners.theory_days.chess_source import features,prepare

def test_clock_sign_and_missingness(tmp_path):
    record=dict(headers=dict(WhiteElo='1500',BlackElo='1600',TimeControl='60+2'),moves='1. e4 {[%eval 0.2] [%clk 0:00:59]} e5 {[%eval 0.4] [%clk 0:01:00]} 2. Nf3 {[%eval 0.1] [%clk 0:00:57]} Nc6 {[%eval #-4] [%clk 0:00:58]} *')
    rows,c=features(record);assert len(rows)==2
    assert abs(rows[0][0]+20)<1e-9 and abs(rows[1][0]+30)<1e-9
    assert c['missing_eval_or_clock']==2
    text='[Event "constructed"]\n[WhiteElo "1500"]\n[BlackElo "1600"]\n[TimeControl "60+2"]\n\n'+record['moves']+'\n'
    p=tmp_path/'x.zst'
    with pa.CompressedOutputStream(str(p),'zstd') as f:f.write(text.encode())
    a=prepare(p,tmp_path/'a.gz',tmp_path/'a.npz',rate=1)
    assert a['source_games']==a['selected_games']==a['usable_games']==1 and a['moves']==2

def test_native_wrapper_creates_output_and_replays(tmp_path):
    from runners.theory_days.validate_chess_source import execute,verify
    output=tmp_path/'new-output';execute(output,{},{});assert verify(output,{}, {})['verified']
