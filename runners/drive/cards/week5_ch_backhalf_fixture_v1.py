"""Constructed real-parser/reference fixture and native-queue input preparation.

The source handler runs only in a counted owner-admitted attempt. Preparing a
queue input is not admission and starts no engine. Native queue plans are run
one at a time by the owner, with execute and verifier pauses inspected separately.
"""
from collections import defaultdict
from pathlib import Path
import hashlib
import json
import sqlite3

from . import week5_ch_source as original
from . import week5_ch_backhalf_roster_v1 as roster
from . import week5_ch_merge_bounded as merge
from . import week5_ch_pipeline_checkpoint as ck
from .week5_ch_fixture import PGN


def spec(path):return dict(path=str(Path(path).resolve()),sha256=original.digest(path))


def reference_roster(database,players):
    """Small-fixture list oracle, independent of the disk-backed new selector."""
    con=sqlite3.connect(database)
    try:rows=con.execute('SELECT player,month,tc,band,n,rating_sum/n FROM frame WHERE n>=20').fetchall()
    finally:con.close()
    assigned={}
    for row in rows:
        rank=hashlib.sha256(f'{original.SEED}:eligibility:{row[0]}:{row[1]}:{row[2]}:{row[3]}'.encode()).hexdigest()
        if row[0] not in assigned or rank<assigned[row[0]][0]:assigned[row[0]]=(rank,row)
    cells=defaultdict(list)
    for _,row in assigned.values():cells[(row[2],row[1],row[3])].append(row)
    def apportion(counts,target):
        denominator=sum(counts.values());target=min(target,denominator)
        if not denominator:return {k:0 for k in counts}
        answer={k:target*n//denominator for k,n in counts.items()}
        order=sorted(counts,key=lambda k:(-(target*counts[k]%denominator),k))
        for key in order[:target-sum(answer.values())]:answer[key]+=1
        return answer
    quotas=apportion(roster.QUOTAS,players);selected=[]
    for tc in roster.QUOTAS:
        months={m:sum(len(v) for (t,n,b),v in cells.items() if t==tc and n==m) for m in roster.MONTHS}
        for month,n in apportion(months,quotas[tc]).items():
            bands={b:len(v) for (t,m,b),v in cells.items() if t==tc and m==month}
            for band,count in apportion(bands,n).items():
                ranked=sorted(cells[(tc,month,band)],key=lambda row:(hashlib.sha256(f'{original.SEED}:sample:{row[0]}'.encode()).hexdigest(),row[0]))
                for row in ranked[:count]:selected.append(dict(zip(('player','month','time_control','band','eligible_games','rating'),row)))
    return sorted(selected,key=lambda row:row['player'])


def source_fixture(output,inputs,config,request_root=None):
    if inputs or config!={'constructed_fixture':True}:
        raise ValueError('Only exact source-free constructed fixture accepted')
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    request_root=output if request_root is None else request_root
    salt=output/'CONSTRUCTED_SALT.bin';salt.write_bytes(b'constructed-three-month-frame-v1')
    frames={};sources=[]
    for month in roster.MONTHS:
        ck.require(request_root);texts=[]
        for pair in range(4):
            for tc in ('60+0','300+2','900+10','1800+0'):
                for game in range(24):
                    text=PGN.replace('fixture-white',f'constructed-white-{pair}').replace('fixture-black',f'constructed-black-{pair}')
                    text=text.replace('2017.04.01',month.replace('-','.')+'.01').replace('300+2',tc)
                    if game%5==0:text=text.replace(' { [%clk 0:04:58] }','')
                    if game%7==0:text=text.replace('0:04:57','0:05:00')
                    if game%11==0:text=text.replace('0:04:59','0:00:00')
                    texts.append(text)
        raw=output/(month+'.pgn');raw.write_text('\n'.join(texts),encoding='utf8',newline='\n')
        sources.append(dict(month=month,**spec(raw)))
        original.execute(output/('census-'+month),dict(source=spec(raw),salt=spec(salt)),dict(phase='census',month=month))
        frames['frame'+str(len(frames))]=spec(output/('census-'+month)/'PRIVATE_FRAME.sqlite')
    merge_inputs=dict(salt=spec(salt),**frames)
    merge.execute(output/'merge',merge_inputs,dict(phase='merge'))
    if not merge.verify(output/'merge',merge_inputs,dict(phase='merge'))['verified']:raise AssertionError('Constructed merge differs')
    frame=output/'merge/PRIVATE_FRAME.sqlite'
    selected,counts=roster.choose_players(frame,100,constructed=True)
    expected=reference_roster(frame,100)
    if selected!=expected:raise AssertionError('Independent proportional-roster oracle differs')
    reference=output/'REFERENCE_POSITIONS.jsonl.gz'
    reference_counts=original.collect_positions(sources,expected,salt.read_bytes(),reference)
    sample_inputs=dict(frame=spec(frame),salt=spec(salt))
    settings=dict(phase='sample',players=100,sources=sources,constructed_fixture=True)
    if roster.execute(output/'sample',sample_inputs,settings)['status']!='complete':raise AssertionError('Fixture sample incomplete')
    if not roster.verify(output/'sample',sample_inputs,settings)['verified']:raise AssertionError('Raw sample replay differs')
    if original.digest(reference)!=original.digest(output/'sample/PRIVATE_POSITIONS.jsonl.gz'):
        raise AssertionError('Original raw collector position order/value differs')
    native_counts=json.loads((output/'sample/SOURCE.json').read_text())
    if any(native_counts.get(k)!=v for k,v in reference_counts.items()):raise AssertionError('Original missingness/sample count differs')
    result=dict(verified=True,three_complete_months=True,unique_players=True,
        independent_roster_oracle=True,original_raw_collector_byte_parity=True,
        all_raw_sources_replayed=True,positions=reference_counts['sampled_positions'],
        selected_players=len(selected),constructed_fixture=True,scientific_admission=False)
    original.write_json(output/'FIXTURE.json',result)
    return result


def execute(output,inputs,config):
    # Runtime creates output first; keep the whole reference as one bounded child.
    return dict(status='complete',**source_fixture(Path(output)/'constructed',inputs,config,output))


def verify(output,inputs,config):
    first=json.loads((Path(output)/'constructed/FIXTURE.json').read_text())
    second=source_fixture(Path(output)/'independent',inputs,config,output)
    if first!=second:raise ValueError('Complete constructed source replay differs')
    return dict(verified=True,complete_recalculation=True,constructed_fixture=True)


def prepare_queue_inputs(root,engine):
    import chess
    from .week5_ch_collection import write_rows
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    one=chess.Board('8/8/8/8/8/1k6/r7/K7 w - - 0 1')
    mate=chess.Board('6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1')
    mating=[]
    for move in mate.legal_moves:
        trial=mate.copy();trial.push(move)
        if trial.is_checkmate():mating.append(move)
    if one.legal_moves.count()!=1 or len(mating)!=1:raise AssertionError('Known legal-move controls changed')
    boards=[(one,next(iter(one.legal_moves))),(mate,mating[0])]
    board=chess.Board()
    for san in ('e4','e5','Nf3','Nc6','Bb5','a6'):
        move=board.parse_san(san);boards.append((board.copy(),move));board.push(move)
    rows=[dict(fen=board.fen(),uci=move.uci(),ordinal=i,player=f'constructed-{i}',month=roster.MONTHS[i%3],rating=1600)
          for i,(board,move) in enumerate(boards)]
    write_rows(root/'PRIVATE_POSITIONS.jsonl.gz',rows)
    original.write_json(root/'KNOWN_ANSWERS.json',dict(single_legal_ordinal=0,unique_mate_ordinal=1,
        expected_positions=8,independent_native_replay_required=True,
        chain=[dict(stage='execute-pause',quantum=6,terminal='PAUSED',operation='execute'),
               dict(stage='final-verifier-pause',quantum=6,terminal='PAUSED',operation='verify'),
               dict(stage='complete',quantum=8,terminal='COMPLETE')]))
    return dict(positions=spec(root/'PRIVATE_POSITIONS.jsonl.gz'),engine=spec(engine))
