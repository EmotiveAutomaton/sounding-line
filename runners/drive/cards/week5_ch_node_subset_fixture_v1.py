"""Prepared exact original node-subset fixture; not run or scientifically admitted."""
from pathlib import Path
import gzip
import json
import os
import shutil

from . import week5_ch_batch_planner as original
from . import week5_ch_node_subset_bounded_v1 as bounded
from . import week5_ch_collection as collection
from . import week5_ch_pipeline_checkpoint as ck
from .week5_ch_source import digest,write_json


def spec(path):
    return dict(path=str(path),sha256=digest(path))


def snapshot(root):
    return {p.relative_to(root).as_posix():digest(p) for p in sorted(root.rglob('*')) if p.is_file()}


def clone(source,attempt):
    target = attempt/'output'
    shutil.copytree(source,target)
    write_json(attempt/'RESUMED_FROM.json',dict(constructed_handler_copy_only=True,copied=snapshot(target)))
    return target


def request(root):
    write_json(root/'YIELD_REQUEST.json',dict(reason='owner_cancel',at='2026-11-08T08:00:00Z',constructed_fixture=True))


def refuses(callback):
    try:
        callback()
    except ValueError:
        return
    raise AssertionError('Invalid subset input or output accepted')


def parity(left,right):
    for name in bounded.FILES:
        assert (left/name).read_bytes()==(right/name).read_bytes(),name


def run(root,owner):
    root.mkdir(parents=True,exist_ok=False)
    check = lambda: ck.require(owner)
    rows=[]
    for turn in range(6):
        for player in reversed(range(12)):
            if turn<2+player%5:
                rows.append(dict(player=f'constructed-node-player-{player}',ordinal=len(rows),
                                 round=turn,fen='constructed',uci='e2e4',nested=dict(values=[turn,True,None])))
    collection.write_rows(root/'parent.gz',rows)
    inputs=dict(positions=spec(root/'parent.gz'))
    config=dict(expected_positions=len(rows),maximum_positions=13,constructed_fixture=True)
    check()
    original.node_texture_roster(inputs['positions'],root/'original',13)
    assert bounded.execute(root/'bounded',inputs,config)['status']=='complete'
    parity(root/'original',root/'bounded')
    assert bounded.verify(root/'bounded',inputs,config)['verified']
    with gzip.open(root/'bounded/PRIVATE_POSITIONS.jsonl.gz','rt',encoding='utf8') as stream:
        chosen=[json.loads(line) for line in stream]
    assert len(chosen)<=13 and chosen
    for player in {row['player'] for row in chosen}:
        assert [r for r in chosen if r['player']==player]==[r for r in rows if r['player']==player]
    check()
    first=root/'execute_prefix'
    result=bounded.execute(first,inputs,dict(config,max_new_draws=3))
    assert result['status']=='yielded' and result['new_completed_units']==3
    before=snapshot(first)
    resumed=clone(first,root/'continued')
    assert bounded.execute(resumed,inputs,config)['status']=='complete'
    parity(root/'original',resumed)
    assert snapshot(first)==before
    result=bounded.verify(resumed,inputs,dict(config,max_new_draws=3))
    assert result['status']=='yielded' and result['new_completed_units']==3
    assert not result['verification_prefix_credited']
    assert bounded.verify(resumed,inputs,config)['verified']
    assert (resumed/'independent_subset-000002/SUBSET.json').exists()
    check()
    saved=bounded.Control.advance
    def interrupt(self,phase,done,total):
        saved(self,phase,done,total)
        if phase=='gzip_rows_restart_on_interrupt' and done==2:
            request(root/'gzip_pause')
    bounded.Control.advance=interrupt
    try:
        paused=bounded.execute(root/'gzip_pause',inputs,config)
    finally:
        bounded.Control.advance=saved
    assert paused['status']=='yielded' and paused['phase']=='gzip'
    old=snapshot(root/'gzip_pause')
    continuation=clone(root/'gzip_pause',root/'gzip_continued')
    assert bounded.execute(continuation,inputs,dict(config,max_new_draws=len(chosen)))['status']=='complete'
    parity(root/'original',continuation)
    assert snapshot(root/'gzip_pause')==old
    assert bounded.verify(continuation,inputs,config)['verified']
    check()
    original.node_texture_roster(inputs['positions'],root/'all_original',25000)
    assert bounded.execute(root/'all_bounded',inputs,dict(config,maximum_positions=25000))['status']=='complete'
    parity(root/'all_original',root/'all_bounded')
    refuses(lambda: bounded.execute(root/'none_fit',inputs,dict(config,maximum_positions=1)))
    refuses(lambda: bounded.execute(root/'wrong_count',inputs,dict(config,expected_positions=len(rows)+1)))
    refuses(lambda: bounded.execute(root/'changed_pin',dict(positions=dict(inputs['positions'],sha256='0'*64)),config))
    refuses(lambda: bounded.execute(root/'over_cap',inputs,dict(config,maximum_positions=25001)))
    altered=clone(first,root/'damaged_copy')
    with (altered/'PRIVATE_NODE_SUBSET.sqlite').open('ab') as stream:
        stream.write(b'constructed corruption')
    refuses(lambda: bounded.execute(altered,inputs,config))
    check()
    tampered=root/'false_seal'
    shutil.copytree(root/'bounded',tampered)
    changed=[dict(row) for row in chosen]
    changed[0]['ordinal']=-123
    collection.write_rows(tampered/'replacement.gz',changed)
    os.replace(tampered/'replacement.gz',tampered/'PRIVATE_POSITIONS.jsonl.gz')
    receipt=json.loads((tampered/'SUBSET.json').read_text(encoding='utf8'))
    receipt['positions_sha256']=digest(tampered/'PRIVATE_POSITIONS.jsonl.gz')
    write_json(tampered/'SUBSET.json',receipt,mutable=True)
    seal=json.loads((tampered/'SOURCE_SEAL.json').read_text(encoding='utf8'))
    seal['files']={name:digest(tampered/name) for name in seal['files']}
    write_json(tampered/'SOURCE_SEAL.json',seal,mutable=True)
    refuses(lambda: bounded.verify(tampered,inputs,config))
    proof=dict(constructed=True,original_two_file_byte_parity=True,
               whole_player_greedy_rule=True,original_per_player_row_order=True,
               execute_and_verify_actual_quantum=True,gzip_actual_owner_yield=True,
               fresh_parent_zero_replay=True,changed_predecessors=False,
               malformed_source_and_checkpoint_refusals=5,resealed_false_subset_refused=True,
               native_runtime_copy_exit_lease_watch_proof=False,scientific_admission=False)
    write_json(root/'FIXTURE.json',proof)
    return proof


def execute(output,inputs,config):
    if inputs or config!={'constructed_fixture':True}:
        raise ValueError('Exact source-free node-subset fixture required')
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    try:
        proof=run(output/'constructed_execution',output)
    except ck.YieldRequested:
        return dict(status='yielded',reason='Owner request; restart aggregate fixture in fresh output')
    return dict(status='complete',**proof)


def verify(output,inputs,config):
    if inputs or config!={'constructed_fixture':True}:
        raise ValueError('Exact source-free node-subset fixture required')
    output=Path(output)
    try:
        proof=run(output/'constructed_replay',output)
    except ck.YieldRequested:
        return dict(status='yielded',reason='Owner request; restart aggregate verification in fresh output')
    if proof!=json.loads((output/'constructed_execution/FIXTURE.json').read_text(encoding='utf8')):
        raise ValueError('Complete node-subset fixture replay differs')
    return dict(verified=True,complete_recalculation=True,scientific_admission=False)
