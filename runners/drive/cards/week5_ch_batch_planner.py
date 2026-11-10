"""Immutable CH1 segment planning and authenticated completed-batch collection.

This prepares data only. It never starts workers, creates leases or expands a
scientific roster. Root wraps each emitted configuration in a counted plan.
"""
from collections import defaultdict
from pathlib import Path
import hashlib,json
from .week5_ch_collection import verified_spec,write_rows
from .week5_ch_engine import iter_positions,score_key
from .week5_ch_source import write_json,digest


def segments(positions,nodes=1000000,segment_positions=1024):
    if segment_positions<1:raise ValueError('Positive segment size required')
    path=verified_spec(positions);keys=set();count=0
    for row in iter_positions(path):
        key=score_key(row,nodes)
        if key in keys:raise ValueError('Duplicate position in roster')
        keys.add(key);count+=1
    if not count:raise ValueError('Empty roster')
    return [dict(segment=i,begin=start,end=min(count,start+segment_positions),roster=positions,node_limit=nodes,
                 config=dict(offset=start,max_positions=min(segment_positions,count-start),nodes=nodes,wall_seconds=600),
                 combined_execute_replay_wall_seconds=1800,projected_peak_ram_GiB=.5)
            for i,start in enumerate(range(0,count,segment_positions))]


def authenticated_batch(completion):
    file=verified_spec(completion);root=file.parent;receipt=json.loads(file.read_text())
    if receipt.get('status')!='COMPLETE' or not receipt.get('fresh_process_verified'):raise ValueError('Batch lacks complete native replay')
    outputs=receipt['outputs']
    needed=['PLAN.json','output/BATCH.json','output/VERIFY.json']
    score_names=sorted(name for name in outputs if name.startswith('output/PRIVATE_SCORES/') and name.endswith('.json'))
    for name in needed+score_names:
        if name not in outputs or digest(root/name)!=outputs[name]:raise ValueError('Completed batch binding changed')
    plan=json.loads((root/'PLAN.json').read_text());report=json.loads((root/'output/BATCH.json').read_text());proof=json.loads((root/'output/VERIFY.json').read_text())
    if plan['module']!='runners.drive.cards.week5_ch_engine':raise ValueError('Not a CH engine batch')
    if not proof.get('all_scores_equal') or proof['verified_positions']!=len(score_names):raise ValueError('Replay denominator mismatch')
    if report['visited_positions']!=len(score_names) or report['next_offset']!=plan['config'].get('offset',0)+len(score_names):raise ValueError('Batch interval mismatch')
    actual=set(p.name for p in (root/'output/PRIVATE_SCORES').glob('*.json'))
    if actual!={Path(n).name for n in score_names}:raise ValueError('Unbound score file')
    return root,plan,report,{Path(name).name:outputs[name] for name in score_names}


def continuation(segment,completions):
    intervals=[]
    for complete in completions:
        root,plan,report,bindings=authenticated_batch(complete)
        if plan['inputs']['positions']!=segment['roster'] or report['node_limit']!=segment['node_limit']:raise ValueError('Batch belongs to different roster or node limit')
        begin=plan['config'].get('offset',0);end=report['next_offset']
        if begin<segment['begin'] or end>segment['end'] or end<=begin:raise ValueError('Batch outside segment or made no progress')
        intervals.append((begin,end))
    offset=segment['begin']
    for begin,end in sorted(intervals):
        if begin!=offset:raise ValueError('Overlapping or gapped batch continuation')
        offset=end
    if offset==segment['end']:return dict(segment_complete=True,next_offset=offset)
    return dict(segment_complete=False,next_offset=offset,config=dict(offset=offset,max_positions=segment['end']-offset,nodes=segment['node_limit'],wall_seconds=600))


def collection_manifest(completions,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);batches=[]
    for i,complete in enumerate(completions):
        root,plan,report,bindings=authenticated_batch(complete);path=output/f'SCORE_BINDINGS_{i:06}.json';write_json(path,bindings)
        def spec(p):return dict(path=str(p),sha256=digest(p))
        batches.append(dict(path=str(root/'output/PRIVATE_SCORES'),verify=spec(root/'output/VERIFY.json'),report=spec(root/'output/BATCH.json'),score_bindings=spec(path),native_complete=complete))
    write_json(output/'BATCHES.json',dict(batches=batches,population_complete=False));return len(batches)


def node_texture_roster(positions,output,maximum_positions=25000):
    if maximum_positions>25000:raise ValueError('Packet node-texture position cap')
    source=verified_spec(positions);players=defaultdict(list)
    for row in iter_positions(source):players[row['player']].append(row)
    selected=[];count=0
    for player in sorted(players,key=lambda p:hashlib.sha256(('20261107:CH-node-texture:'+p).encode()).hexdigest()):
        if count+len(players[player])>maximum_positions:continue
        selected.extend(players[player]);count+=len(players[player])
    if not selected:raise ValueError('No whole player fits node-texture subset')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);write_rows(output/'PRIVATE_POSITIONS.jsonl.gz',selected)
    write_json(output/'SUBSET.json',dict(parent_roster_sha256=positions['sha256'],selected_positions=len(selected),selected_players=len({r['player'] for r in selected}),maximum_positions=maximum_positions,selection='whole players by seeded player hash, before engine readout; shared by both node counts',texture_only=True,positions_sha256=digest(output/'PRIVATE_POSITIONS.jsonl.gz')))
    return dict(positions=len(selected),players=len({r['player'] for r in selected}))
