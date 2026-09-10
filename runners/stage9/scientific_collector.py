"""Collect from a declared training-only factorial fit on preassigned training sources.

DESIGN CHECK: C05/C07/X01/X08; LESSONS 3--5. Pilot weights cannot enter scientific collection. Its fixed
seed-9001 original-expert fit must match the prepared corpus hash. Both law arms
share the assigned half of source examples. Original goal and earlier-work context
remain visible, every attempt is retained, and only actual teacher continuations
become prospective training targets. This is fixed-policy collection, not DAgger.
NULL: pilot weights, changed sources or held-out combinations refuse scientific
collection. ALTERNATIVE: the entire preassigned training half completes. Explicit
discarded timing sources retain their actual parameter roles and cannot enter science.
"""
import argparse
from pathlib import Path
import time
import uuid
from collections import Counter

from runners.stage9.common import REPO,ROOT,Units,closure,digest,file_hash,freeze,read
from runners.stage9.construction import register,rendered_prefix
from runners.stage9.learner import MATCHED_TEACHER_DRAWS,collect_one
from runners.stage9.matching import earlier_context,mixture_keys
from runners.stage9.recipes import parameter_partition
from runners.stage9.runtime import execute
from runners.stage9.service_owner import resident


def collection_inputs(family,coverage,training,*,rehearsal=False):
    """Scientific and explicit discarded inputs converge on one real collection loop."""
    from runners.stage9.train import BASES
    training=Path(training).resolve()
    fitted=read(training/'IDENTITY.json');complete=read(training/'COMPLETE.json')
    if (fitted['family']!=family or fitted['base']!=BASES[family]
            or complete['identity_sha256']!=digest(fitted)):
        raise ValueError('collector model family, base or completion identity differs')
    if rehearsal:
        from runners.stage9.training_jobs import rehearsal_input
        source,_=rehearsal_input(family)
        dispatch=read(training.parent/'COMPLETE.json')
        if (not training.is_relative_to(ROOT/'private/training-handler-pilots') or coverage not in ('original','both')
            or fitted['split']!='pilot' or fitted['seed']!=997901 or fitted['corpus_sha256']!=file_hash(source)
            or dispatch.get('scope')!='discarded-rehearsal' or dispatch.get('operation')!='fit'
            or dispatch['training_complete_sha256']!=file_hash(training/'COMPLETE.json')):
            raise ValueError('discarded collection requires the actual completed isolated rehearsal fit')
        pool_root=ROOT/'private/pilot-dose/qwen' if family=='qwen' else ROOT/'private/pilot-dose-v3/smollm'
        old=read(pool_root/'POOL.json')
        if read(source)['identity']['pool_sha256']!=digest(old):
            raise ValueError('discarded source worlds differ from the audited fitting pool')
        pool={'candidate_examples':old['examples'],'private_worlds':old['worlds'],'split':'pilot',
            'original_pool_sha256':file_hash(pool_root/'POOL.json')}
        expected=32
        if coverage=='original':
            from runners.stage9.original_collection_pilot import original_pool,ASSIGNED
            pool=original_pool(pool);expected=ASSIGNED
    else:
        source=ROOT/'private/scientific-recipes'/family/'original_expert.json'
        if (fitted['split']!='training' or fitted['seed']!=9001 or fitted['corpus_sha256']!=file_hash(source)):
            raise ValueError('collector must be the declared seed-9001 original-expert scientific fit, never a discarded pilot')
        pool=read(ROOT/'private/training-pools'/family/(coverage+'.json'));expected=800
    if not rehearsal and any(parameter_partition(w)!='training' for w in pool['private_worlds'].values()):
        raise ValueError('held-out parameter entered collection')
    chosen=mixture_keys(pool['candidate_examples'])
    if len(chosen)!=expected:raise ValueError('assigned training source exposure differs')
    return fitted,complete,pool,chosen


def run(family,coverage,training,output,*,rehearsal=False):
    started=time.time()
    register()
    training,output=Path(training).resolve(),Path(output).resolve()
    from runners.stage9.training_jobs import cell_identity
    cell=cell_identity()
    if rehearsal and (not output.is_relative_to(ROOT/'private/collection-handler-pilots')
        or output==ROOT/'private/collection-handler-pilots'):
        raise ValueError('discarded collection output must stay in its explicit pilot namespace')
    if not rehearsal and output!=ROOT/'private/scientific-collection'/family/coverage:
        raise ValueError('scientific collection output differs from the declared factorial')
    fitted,complete,pool,chosen=collection_inputs(family,coverage,training,rehearsal=rehearsal)
    adapter=training/complete['selected_checkpoint']
    if closure([adapter])['sha256']!=complete['selected_checkpoint_sha256']:
        raise ValueError('collector checkpoint changed')
    sources=closure([REPO/'runners/stage9'/n for n in ('scientific_collector.py','learner.py','matching.py',
        'recipes.py','construction.py','common.py','runtime.py','reader.py','features.py','service_owner.py',
        'model_service.py','generation_policy.py','neural.py','train.py')]
        +([REPO/'runners/stage9/original_collection_pilot.py'] if rehearsal and coverage=='original' else [])
        +[REPO/'runners/stage7/constructor',
        REPO/'runners/stage7/reader',REPO/'runners/stage8/constructor',REPO/'runners/stage8/reader/logfmt.py',
        REPO/'runners/stage8/engines.py',REPO/'runners/readout_repair.py',REPO/'runners/stage7/runtime.py'])
    identity={'family':family,'coverage':coverage,'cell_identity':cell,'discarded_rehearsal':rehearsal,
              'collector_fit':fitted,'selected_checkpoint':complete['selected_checkpoint_sha256'],
              'pool_sha256':digest(pool),'assigned_keys':sorted(chosen),'sources':sources,
              'parameter_roles':dict(Counter(parameter_partition(w) for w in pool['private_worlds'].values())),
              'actions_per_source':4,'teacher_draws_per_state':MATCHED_TEACHER_DRAWS,'precision':'float16','decoding':'greedy first-line free proposal',
              'evidence':'same original goal-presence and complete earlier-work text as the paired expert example',
              'scope':('discarded rehearsal; scientific use forbidden' if rehearsal else 'training-only fixed-policy collection; no admission from collection success')}
    units=Units(output,identity)
    if (output/'COMPLETE.json').exists():
        done=read(output/'COMPLETE.json')
        if done['identity_sha256']!=digest(identity) or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']:
            raise ValueError('completed collection closure changed')
        return done
    config={'family':family,'adapter':str(adapter),'adapter_sha256':closure([adapter])['sha256'],
            'precision':'float16','device':'cuda','batch_size':1,'max_context':4096,'max_support':128,'max_new_tokens':32}
    with resident(output/'services'/uuid.uuid4().hex[:12],config) as (ready,token):
        for source_row in pool['candidate_examples']:
            key=source_row['key']
            if key not in chosen or units.get(key) is not None:
                continue
            world=pool['private_worlds'][key]
            previous=earlier_context(source_row)
            with_goal=source_row['raw_record']['with_goal']
            def render(current,events):
                return previous+rendered_prefix(current,events,with_goal=with_goal)
            def predict(evidence,turn):
                return execute(evidence,{'operation':'generate','identity':{**ready['identity'],'information_sha256':digest(evidence)},
                                         'max_new_tokens':32,'seed':int(digest({'collection':key,'turn':turn})[:8],16)},
                               ready['endpoint'],token,root=output/'capsules',timeout=900)
            row=collect_one(world,predict,maximum_actions=4,teacher_draws=MATCHED_TEACHER_DRAWS,render=render)
            row.update(training_source_lineages=source_row['lineages'],with_goal=with_goal,
                       earlier_context_sha256=digest(previous),parameter_partition=parameter_partition(world),
                       source_parameter_roles={lid:parameter_partition(pool['private_worlds'][lid]) for lid in source_row['lineages']})
            units.put(key,row)
    records=units.all()
    if {r['key'] for r in records}!=chosen:
        raise ValueError('collection has absent or extraneous assigned source units')
    receipt={'identity_sha256':digest(identity),'cell_identity':cell,'discarded_rehearsal':rehearsal,
             'sources_attempted':len(records),'completed_at':time.time(),
             'actual_learner_actions':sum(r['row']['learner_actions_applied'] for r in records),
             'sources_with_actual_visits':sum(r['row']['learner_actions_applied']>0 for r in records),
             'domains':dict(Counter(r['row']['domain'] for r in records)),
             'wall_seconds':time.time()-started,'scientific_admission':False,
             'outputs':closure([output/'units',output/'capsules',output/'services']),
             'failure_rule':'invalid or stopped proposals retain their assignment; never replace a failed source with a new one'}
    freeze(output/'COMPLETE.json',receipt)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--family',required=True,choices=['qwen','smollm'])
    p.add_argument('--coverage',required=True,choices=['original','both'])
    p.add_argument('--training',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    args=p.parse_args();run(args.family,args.coverage,args.training,args.output)
