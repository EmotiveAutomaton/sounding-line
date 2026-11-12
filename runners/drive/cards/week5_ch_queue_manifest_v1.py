"""Authenticate complete N queues and retain the original collector contract."""
from pathlib import Path
import json
from .week5_ch_source import digest,write_json
from .week5_ch_pipeline_checkpoint import checked

MODULE='runners.drive.cards.week5_ch_queue_backhalf_v1'


def collection_manifest(completions,output,roster,nodes=1000000,expected_positions=None):
    if type(expected_positions) is not int or not 1<=expected_positions<=400000:
        raise ValueError('Complete declared roster denominator required')
    queues=[]
    for complete_spec in completions:
        path=checked(complete_spec);root=path.parent
        terminal=json.loads(path.read_text(encoding='utf8'))
        if terminal.get('status')!='COMPLETE' or not terminal.get('fresh_process_verified'):
            raise ValueError('Queue lacks complete counted native verification')
        for name in ('PLAN.json','output/QUEUE.json','output/QUEUE_BATCHES.json','output/QUEUE_VERIFIED.json'):
            if terminal['outputs'].get(name)!=digest(root/name):raise ValueError('Completed queue binding changed')
        plan=json.loads((root/'PLAN.json').read_text(encoding='utf8'))
        report=json.loads((root/'output/QUEUE.json').read_text(encoding='utf8'))
        proof=json.loads((root/'output/QUEUE_VERIFIED.json').read_text(encoding='utf8'))
        if (plan['module']!=MODULE or plan['inputs']['positions']!=roster or report['node_limit']!=nodes or
            report['expected_positions']!=expected_positions or not proof.get('every_score_covered') or
            not proof.get('all_closed_native_replays_authenticated') or not proof.get('original_roster_ordinals_verified')):
            raise ValueError('Different roster or incomplete queue replay')
        batches=json.loads((root/'output/QUEUE_BATCHES.json').read_text(encoding='utf8'))['batches']
        for batch in batches:
            seal_path=checked(batch['queue_unit_seal'])
            seal=json.loads(seal_path.read_text(encoding='utf8'))
            for name,sha in seal['files'].items():
                file=seal_path.parent/name
                if digest(file)!=sha:raise ValueError('Closed score or native proof changed')
            for name in ('verify','report','score_bindings'):checked(batch[name])
            batch['native_complete']=complete_spec
        queues.append((report['begin'],report['end'],batches))
    cursor=0;all_batches=[]
    for begin,end,batches in sorted(queues):
        if begin!=cursor or not begin<end<=expected_positions:
            raise ValueError('Missing, overlapping or out-of-frame queue interval')
        cursor=end;all_batches.extend(batches)
    if cursor!=expected_positions:
        raise ValueError('Complete original roster has not finished')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    write_json(output/'BATCHES.json',dict(batches=all_batches,population_complete=True,
        positions=expected_positions,roster_sha256=roster['sha256'],node_limit=nodes,
        source='Complete counted N queues with separate native replay for every score'))
    return len(all_batches)
