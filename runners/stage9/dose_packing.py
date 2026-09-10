"""Second discarded dose packing: retain expert history labels, mask learner history.

DESIGN CHECK: C05. Reuse completed discarded Qwen collection with explicit lineage;
collect SmolLM2 under the same balanced dose design. Prior packing failure stays.
No scientific model, discovery target or reserve is consumed by this pilot.
"""
import argparse
from pathlib import Path
import time
import uuid
from runners.stage9.common import REPO,ROOT,Units,closure,digest,freeze,read
from runners.stage9.construction import register,rendered_prefix
from runners.stage9.dose_pilot import prepare
from runners.stage9.learner import collect_one
from runners.stage9.matching import earlier_context,mixture_keys,replay_row,target_positions,audit
from runners.stage9.mixed_recipes import build
from runners.stage9.runtime import execute
from runners.stage9.service_owner import resident
from runners.stage9.train import BASES,train


def run(family,loss_mode='full'):
    if loss_mode not in ('full','streamed'):raise ValueError('unregistered loss computation')
    lineage='pilot-dose-v3' if loss_mode=='streamed' else 'pilot-dose-v2'
    if loss_mode=='streamed':
        measured=read(ROOT/'pilot/STREAMED_LOSS.json')['families'][family]
        if not all(measured['checks'].values()):raise ValueError('actual-base loss checks did not pass')
    register();started=time.time();output=ROOT/'private'/lineage/family
    if (output/'COMPLETE.json').exists():return read(output/'COMPLETE.json')
    pool_root=ROOT/'private/pilot-dose/qwen' if family=='qwen' else output
    pool=prepare(family,pool_root)
    sources=closure([REPO/'runners/stage9'/n for n in ('dose_packing.py','dose_pilot.py','mixed_recipes.py',
        'learner.py','matching.py','recipes.py','construction.py','common.py','runtime.py','reader.py',
        'features.py','service_owner.py','model_service.py','generation_policy.py','neural.py','train.py')]
        +([REPO/'runners/stage9/streamed_loss.py'] if loss_mode=='streamed' else []))
    identity={'family':family,'pool_sha256':digest(pool),'sources':sources,
              'scope':'discarded balanced-dose packing pilot; not representative average runtime','loss_computation':loss_mode,
              'packing':'earlier correct expert labels preserved; actual learner history masked; two correct teacher continuations'}
    freeze(output/'IDENTITY.json',identity)
    if family=='qwen':
        collection_root=pool_root/'collection'
        records={r['key']:r['row'] for r in (read(p) for p in sorted((collection_root/'units').glob('*.json')))}
        if len(records)!=64 or any(not read(p)['graceful_shutdown'] for p in (pool_root/'services').glob('*/LIFECYCLE.json')):
            raise ValueError('prior Qwen collection is incomplete or service remains unresolved')
        freeze(output/'COLLECTION_SOURCE.json',{'root':str(collection_root),'identity_sha256':digest(read(collection_root/'IDENTITY.json')),
                                              'units_sha256':digest(records),'reused_discarded_collection':True})
    else:
        units=Units(output/'collection',identity)
        training=ROOT/'pilot/smollm-run1';complete=read(training/'COMPLETE.json');adapter=training/complete['selected_checkpoint']
        if complete['split']!='pilot' or closure([adapter])['sha256']!=complete['selected_checkpoint_sha256']:
            raise ValueError('discarded adapter identity changed')
        config={'family':family,'adapter':str(adapter),'adapter_sha256':closure([adapter])['sha256'],
                'precision':'float16','device':'cuda','batch_size':1,'max_context':4096,'max_support':128,'max_new_tokens':32}
        if len(units.all())<64:
            with resident(output/'services'/uuid.uuid4().hex[:12],config) as (ready,token):
                for source in pool['examples']:
                    key=source['key']
                    if units.get(key) is not None:continue
                    previous=earlier_context(source);with_goal=source['raw_record']['with_goal']
                    def render(world,events):return previous+rendered_prefix(world,events,with_goal=with_goal)
                    def predict(evidence,turn):
                        return execute(evidence,{'operation':'generate','identity':{**ready['identity'],'information_sha256':digest(evidence)},
                            'max_new_tokens':32,'seed':int(digest({'dose':key,'turn':turn})[:8],16)},
                            ready['endpoint'],token,root=output/'capsules',timeout=900)
                    unit_start=time.time()
                    row=collect_one(pool['worlds'][key],predict,maximum_actions=4,teacher_draws=2,render=render)
                    row.update(n_earlier=source['raw_record']['n_earlier'],unit_seconds=time.time()-unit_start)
                    units.put(key,row)
        records={u['key']:u['row'] for u in units.all()}
    if set(records)!={r['key'] for r in pool['examples']}:
        raise ValueError('collection sources differ from frozen dose pool')
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(BASES[family]['model'],revision=BASES[family]['revision'],local_files_only=True)
    selected=mixture_keys(pool['examples']);expert=[replay_row(r) for r in pool['examples']]
    budget=sum(len(target_positions(r)) for r in expert)
    mixed,matched=build(tok,pool['examples'],expert,{k:r for k,r in records.items() if k in selected},budget)
    comparison=audit({'expert':expert,'mixed':mixed})
    freeze(output/'PACKING.json',{'matching':matched,'comparison':comparison})
    validation=read(ROOT/'private/pilot-matched'/family/'expert.json')
    freeze(output/'mixed.json',{'split':'pilot','identity':identity,'examples':mixed,
           'validation':validation['validation'],'validation_choices':validation['validation_choices']})
    fit=train(output/'mixed.json',output/'training-v1',family,seed=996901,epochs=1,max_length=2048,
              checkpoint_every=2 if loss_mode=='streamed' else 8,loss_mode=loss_mode)
    result={'family':family,'identity_sha256':digest(identity),'comparison':comparison,'matching':matched,
            'training_active_seconds':fit['active_seconds'],'whole_this_attempt_seconds':time.time()-started,
            'collection_reused':family=='qwen','completed_at':time.time(),'scientific_launch_accepted':False}
    freeze(output/'COMPLETE.json',result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--family',choices=BASES,required=True)
    p.add_argument('--loss-mode',choices=['full','streamed'],default='full')
    args=p.parse_args();run(args.family,args.loss_mode)
