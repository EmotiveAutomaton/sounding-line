"""Integrity and final-packet assembly; no inference and no new scientific verdict.

DESIGN CHECK: LESSONS 3-5. NULL: missing, failed, changed or held cells remain
explicit deficits. ALTERNATIVE: every claim points to a complete source-bound
consumer. A queue exit alone never implies scientific completion.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
from .common import RAW,read,freeze,atomic,filehash,now,canonical,check_pins
from .worker import verify



def semantic_replay(card,out,raw):
    from .scoring import proper_loss
    action=card['action']
    if action in ('reconstruction-batch','qwen-batch','qwen-admission','qwen-development-repair'):
        from .reconstruction import score_prediction
        original={r['key']:r for r in read(raw/card['args']['rows'])}
        for r in read(out/'PREDICTIONS.json')['rows']:
            if r.get('scores') is None:continue
            if score_prediction(original[r['key']],r['prediction'],r['metadata'])!=r['scores']:raise ValueError('contribution semantic replay differs')
    if action in ('context-batch','readout-batch','schola-coupling','memory-development-batch'):
        for r in read(out/'PREDICTIONS.json')['rows']:
            if r.get('scores') is None:continue
            n=r.get('n',len(r['probabilities']) if isinstance(r.get('probabilities'),list) else 4)
            if proper_loss(r['probabilities'],r['truth'],n)!=r['scores']:raise ValueError('proper-score replay differs')
    if action=='detector-batch':
        import math
        result=read(out/'PREDICTIONS.json')
        for r in result['rows']:
            f=r['features']
            if any(not math.isfinite(v) for k,v in f.items() if isinstance(v,(int,float))):raise ValueError('nonfinite detector output')
            if result['identity']['arm']=='e5' and abs(1/(1+math.exp(-f['e5_logit']))-f['e5_probability'])>1e-6:raise ValueError('e5 native logit/probability replay differs')

def snapshot(raw=RAW):
    jobs=[];failures=[];cost=Counter();consumers={};cards={}
    pin_union={};input_union={}
    for p in sorted((raw/'manifests').glob('*.json')):
        card=read(p);name=card['id'];cards[name]=filehash(p);out=raw/'jobs'/name
        for k,h in card['source_pins'].items():
            if k in pin_union and pin_union[k]!=h:raise ValueError('conflicting source pin')
            pin_union[k]=h
        input_union.update(card.get('input_pins',{}))
        if (out/'COMPLETE.json').exists():
            done=verify(out)
            if done['card_sha256']!=cards[name]:raise ValueError('terminal/card mismatch')
            semantic_replay(card,out,raw)
            jobs.append(dict(id=name,state='complete',kind=card['kind'],resource=card['resource'],terminal=filehash(out/'COMPLETE.json')))
            cost['completed_wall_seconds']+=done['wall_seconds'];cost['completed_cpu_seconds']+=done['cpu_seconds']
            if (out/'ANALYSIS.json').exists():consumers[name]=dict(path=str((out/'ANALYSIS.json').relative_to(raw)),sha256=filehash(out/'ANALYSIS.json'))
        elif (out/'FAILED.json').exists():
            failure=read(out/'FAILED.json');jobs.append(dict(id=name,state='failed',error=failure['error'],kind=card['kind'],resource=card['resource']))
            cost['failed_wall_seconds']+=failure.get('wall_seconds',0);cost['failed_cpu_seconds']+=failure.get('cpu_seconds',0);failures.append(name)
        elif card['resource']=='gpu' and read(raw/'ALLOCATION.json')['gear']==1:jobs.append(dict(id=name,state='held-gear1',kind=card['kind'],resource=card['resource']))
        elif (out/'DISPATCH.json').exists():jobs.append(dict(id=name,state='started-without-terminal',kind=card['kind'],resource=card['resource']))
        else:jobs.append(dict(id=name,state='unrun',kind=card['kind'],resource=card['resource']))
    check_pins(pin_union)
    for path,h in input_union.items():
        if filehash(raw/path)!=h:raise ValueError('frozen input changed')
    return dict(at=now(),status='inspection',verified_source_pins=len(pin_union),verified_input_pins=len(input_union),jobs=jobs,counts=dict(Counter(j['state'] for j in jobs)),costs=dict(cost),complete_consumers=consumers,contract=read(raw/'CONTRACT.json'),manifest_hashes=cards,
        scope='integrity inventory; only complete consumers can support the final scientific packet; generation stopped at fixed reporting boundary',
        required_deficits=['historically exposed human sources, one connected component per partition','CoAuthor has no independent mental-goal truth or naturally occurring public-context arm','DAMASHA exact forward unavailable after dependency admission failure','Ghost transfer conditional on an independently admitted native export','held GPU comparisons remain missing until explicit gear change and actual completion'])


def write_checkpoint(name,raw=RAW):
    receipt=snapshot(raw);freeze(raw/'checkpoints'/f'{name}-inventory.json',receipt)
    freeze(raw/'checkpoints'/f'{name}.json',dict(status='complete',at=now(),kind='predefined report checkpoint',inventory_sha256=filehash(raw/'checkpoints'/f'{name}-inventory.json'),scientific_verdict=False,
        action='Inspect full integrity, complete scientific write-through and one final curator packet; preserve all explicit deficits'))
    return receipt


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--name',required=True);a=p.parse_args();write_checkpoint(a.name)
