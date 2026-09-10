"""Discarded collection and packing pilot spanning every scientific training dose.

DESIGN CHECK: C05/X01/X08. Fresh pilot instances, balanced across two domains and
zero through three earlier works. All attempts retained; only actual visited-state
teacher continuations are labels. This deliberately overweights long contexts for
capacity testing; its raw average is not the scientific population's runtime rate.
"""
import argparse
from collections import Counter
from pathlib import Path
import time
import uuid

from runners.stage9.common import REPO, ROOT, Units, closure, digest, freeze, read
from runners.stage9.construction import rendered_prefix, register
from runners.stage9.learner import collect_one
from runners.stage9.matching import earlier_context, learner_candidate, mixture_keys, replay_row, match_budget, audit, target_positions
from runners.stage9.recipes import training_record, POP
from runners.stage9.runtime import execute
from runners.stage9.service_owner import resident
from runners.stage9.train import BASES, train


def prepare(family, output):
    from transformers import AutoTokenizer
    path=output/'POOL.json'
    if path.exists():
        return read(path)
    started=time.time()
    tok=AutoTokenizer.from_pretrained(**{'pretrained_model_name_or_path':BASES[family]['model'],
        'revision':BASES[family]['revision'],'local_files_only':True,'trust_remote_code':False})
    examples=[]; worlds={}; attempted=Counter()
    for domain in POP.DOMAINS:
        counts=Counter()
        for i in range(3000):
            raw, linked=training_record(i,domain,9960000,'both')
            attempted[domain]+=1
            dose=raw['n_earlier']
            if counts[dose]>=8:
                continue
            ids=tok(raw['text']+tok.eos_token,add_special_tokens=True).input_ids[:1024]
            examples.append({'key':raw['lid'],'input_ids':ids,'raw_record':raw,'lineages':raw['lineages']})
            worlds.update({w['lid']:w for w in linked});counts[dose]+=1
            if sum(counts.values())==32:
                break
        if counts!={0:8,1:8,2:8,3:8}:
            raise ValueError('dose-stratified pilot failed its bounded construction')
    pool={'examples':examples,'worlds':worlds,'attempted':dict(attempted),
          'preparation_seconds':time.time()-started,'split':'pilot','band':9960000}
    freeze(path,pool)
    return pool


def run(family):
    register(); output=ROOT/'private/pilot-dose'/family
    if (output/'COMPLETE.json').exists():
        return read(output/'COMPLETE.json')
    pool=prepare(family,output)
    training=ROOT/'pilot'/('qwen-run2' if family=='qwen' else 'smollm-run1')
    fitted=read(training/'COMPLETE.json');adapter=training/fitted['selected_checkpoint']
    if fitted['split']!='pilot' or closure([adapter])['sha256']!=fitted['selected_checkpoint_sha256']:
        raise ValueError('discarded checkpoint mismatch')
    source_names=('dose_pilot.py','learner.py','matching.py','recipes.py','construction.py','common.py',
                  'runtime.py','reader.py','features.py','service_owner.py','model_service.py',
                  'generation_policy.py','neural.py','train.py')
    sources=closure([REPO/'runners/stage9'/n for n in source_names]+[
        REPO/'runners/stage7/constructor',REPO/'runners/stage7/reader',REPO/'runners/stage7/runtime.py',
        REPO/'runners/stage8/constructor',REPO/'runners/stage8/reader/logfmt.py',
        REPO/'runners/stage8/engines.py',REPO/'runners/readout_repair.py',REPO/'runners/s5_lib.py'])
    identity={'family':family,'pool_sha256':digest(pool),'sources':sources,
              'checkpoint':fitted['selected_checkpoint_sha256'],'teacher_draws':2,
              'maximum_training_tokens':2048,'scope':'discarded balanced-dose capacity pilot; not admission'}
    units=Units(output/'collection',identity)
    config={'family':family,'adapter':str(adapter),'adapter_sha256':closure([adapter])['sha256'],
            'precision':'float16','device':'cuda','batch_size':1,'max_context':4096,'max_support':128,'max_new_tokens':32}
    started=time.time()
    if len(units.all())<64:
        with resident(output/'services'/uuid.uuid4().hex[:12],config) as (ready,token):
            for source in pool['examples']:
                key=source['key']
                if units.get(key) is not None:
                    continue
                previous=earlier_context(source);with_goal=source['raw_record']['with_goal']
                def render(world, events):
                    return previous+rendered_prefix(world,events,with_goal=with_goal)
                def predict(evidence,turn):
                    return execute(evidence,{'operation':'generate','identity':{**ready['identity'],'information_sha256':digest(evidence)},
                        'max_new_tokens':32,'seed':int(digest({'dose':key,'turn':turn})[:8],16)},
                        ready['endpoint'],token,root=output/'capsules',timeout=900)
                unit_start=time.time()
                row=collect_one(pool['worlds'][key],predict,maximum_actions=4,teacher_draws=2,render=render)
                row.update(n_earlier=source['raw_record']['n_earlier'],unit_seconds=time.time()-unit_start)
                units.put(key,row)
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(BASES[family]['model'],revision=BASES[family]['revision'],local_files_only=True)
    records={u['key']:u['row'] for u in units.all()}
    if set(records)!={r['key'] for r in pool['examples']}:
        raise ValueError('incomplete actual collection')
    selected=mixture_keys([r|{'raw_record':r['raw_record']} for r in pool['examples']])
    expert=[replay_row(r) for r in pool['examples']]
    mixed=[learner_candidate(tok,r,records[r['key']],maximum_tokens=2048) if r['key'] in selected else replay_row(r) for r in pool['examples']]
    budget=sum(len(target_positions(r)) for r in expert)
    candidates={'expert_targets':budget,'mixed_available_targets':sum(len(target_positions(r)) for r in mixed),
                'maximum_mixed_input':max(len(r['input_ids']) for r in mixed),
                'collection_attempted':len(records),'actual_actions':sum(r['learner_actions_applied'] for r in records.values()),
                'per_dose':[{'dose':d,'sources':sum(r['n_earlier']==d for r in records.values()),
                             'unit_seconds':sum(r['unit_seconds'] for r in records.values() if r['n_earlier']==d)} for d in range(4)]}
    freeze(output/'CAPACITY.json',candidates)
    fixed={r['key'] for r in mixed if r['kind']!='learner_visited'}
    mixed=match_budget(mixed,budget,fixed_keys=fixed)
    comparison=audit({'expert':expert,'mixed':mixed})
    prior=read(ROOT/'private/pilot-matched'/family/'expert.json')
    freeze(output/'mixed.json',{'split':'pilot','identity':identity,'examples':mixed,
                              'validation':prior['validation'],'validation_choices':prior['validation_choices']})
    fit=train(output/'mixed.json',output/'training-v1',family,seed=996901,epochs=1,max_length=2048,checkpoint_every=8)
    result={'family':family,'identity_sha256':digest(identity),'capacity':candidates,'comparison':comparison,
            'training_active_seconds':fit['active_seconds'],'post_preparation_wall_seconds':time.time()-started,
            'completed_at':time.time(),'scientific_launch_accepted':False}
    freeze(output/'COMPLETE.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--family',choices=BASES,required=True)
    args=p.parse_args();run(args.family)
