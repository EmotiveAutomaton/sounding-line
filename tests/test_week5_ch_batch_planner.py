import json
from pathlib import Path
import pytest
from runners.drive.cards import week5_ch_batch_planner as p
from runners.drive.cards.week5_ch_collection import write_rows
from runners.drive.cards.week5_ch_engine import score_key,iter_positions
from runners.drive.cards.week5_ch_source import digest,write_json


def roster(tmp_path):
    rows=[dict(player=str(i//4),ordinal=i,fen='constructed',uci='e2e4') for i in range(12)];path=tmp_path/'roster.gz';write_rows(path,rows)
    return rows,dict(path=str(path),sha256=digest(path))


def completed(root,source,rows,offset):
    write_json(root/'PLAN.json',dict(module='runners.drive.cards.week5_ch_engine',inputs=dict(positions=source),config=dict(offset=offset)))
    write_json(root/'output/BATCH.json',dict(node_limit=1000000,visited_positions=len(rows),new_positions=len(rows),reused_positions=0,next_offset=offset+len(rows)))
    write_json(root/'output/VERIFY.json',dict(all_scores_equal=True,verified_positions=len(rows)))
    for row in rows:write_json(root/'output/PRIVATE_SCORES'/(score_key(row,1000000)+'.json'),dict(position=row,node_limit=1000000,engine={}))
    outputs={path.relative_to(root).as_posix():digest(path) for path in root.rglob('*') if path.is_file()}
    write_json(root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,outputs=outputs,constructed_fixture=True))
    return dict(path=str(root/'COMPLETE.json'),sha256=digest(root/'COMPLETE.json'))


def test_segments_cover_roster_once_and_resume_exact_interval(tmp_path):
    rows,source=roster(tmp_path);segments=p.segments(source,segment_positions=5)
    assert [(r['begin'],r['end']) for r in segments]==[(0,5),(5,10),(10,12)]
    first=completed(tmp_path/'batch0',source,rows[:2],0);next_=p.continuation(segments[0],[first]);assert next_['next_offset']==2 and next_['config']['max_positions']==3
    second=completed(tmp_path/'batch1',source,rows[2:5],2);assert p.continuation(segments[0],[second,first])['segment_complete']
    with pytest.raises(ValueError,match='Overlapping'):p.continuation(segments[0],[first,first])
    p.collection_manifest([first,second],tmp_path/'manifest');assert (tmp_path/'manifest/BATCHES.json').exists()


def test_node_texture_selects_whole_players_same_roster(tmp_path):
    rows,source=roster(tmp_path);result=p.node_texture_roster(source,tmp_path/'texture',maximum_positions=9)
    assert result==dict(positions=8,players=2)
    selected=list(iter_positions(tmp_path/'texture/PRIVATE_POSITIONS.jsonl.gz'))
    assert all(sum(r['player']==player for r in selected)==4 for player in {r['player'] for r in selected})
    with pytest.raises(ValueError,match='cap'):p.node_texture_roster(source,tmp_path/'over',25001)
