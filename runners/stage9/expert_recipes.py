"""The two expert-prefix cells of the scientific training factorial.

DESIGN CHECK: C05/C07/X01. Preserve the original 1600 replay examples exactly;
match the broader arm's causal target-token total with disclosed correct-target
masking/supplementation. All source units stay in the training parameter partition.
Validation uses new instances in the development parameter partition, including
STOP on the complete objective support. No pilot adapter supplies scientific data.
"""
import argparse
import copy
from pathlib import Path
import random
import time

from runners.stage8.reader import logfmt as LF
from runners.stage9.common import REPO,ROOT,closure,digest,freeze,read
from runners.stage9.construction import Replay,rendered_prefix,register
from runners.stage9.matching import audit,match_budget,replay_row,target_positions
from runners.stage9.recipes import POP,sampled_world,parameter_partition
from runners.stage9.train import BASES


def render_tail(replay, seed):
    tail, stopped = replay.continue_teacher(seed)
    lines=[LF.event_line(e['i'],e['type'],e['section'],e['slot'],e['outcome']) for e in tail]
    if stopped:
        lines.append(LF.stop_line(len(replay.steps)))
    if not lines:
        raise ValueError('expert continuation has no supported target')
    return '\n'.join(lines)


def fit_expert_budget(tok, pool, budget):
    # These worlds were loaded from JSON, so no constructor has initialized the
    # reviewed purpose/secondary-law tables in this fresh preparation process.
    register()
    rows=[replay_row(r)|{'kind':'broader_expert_replay'} for r in pool['candidate_examples']]
    available=sum(len(target_positions(r)) for r in rows)
    receipt={'initial_target_tokens':available,'required_target_tokens':budget,
             'supplemented_sources':[],'target_tokens_masked':max(0,available-budget),
             'matching_rule':'retain original replay exactly; broad arm masks surplus or adds correct same-source expert continuations in fixed source-hash order'}
    if available>=budget:
        return match_budget(rows,budget),receipt
    remaining=budget-available
    for row in sorted(rows,key=lambda r:digest({'expert_supplement':r['key']})):
        world=pool['private_worlds'][row['key']]
        prefix=rendered_prefix(world,[])
        target=render_tail(Replay(world),int(digest({'expert_supplement_target':row['key']})[:12],16))
        prefix_ids=tok(prefix,add_special_tokens=True).input_ids
        target_ids=tok(target+tok.eos_token,add_special_tokens=False).input_ids
        if len(row['input_ids'])+len(prefix_ids)+len(target_ids)>2048:
            continue
        kept=min(remaining,len(target_ids))
        row['input_ids'].extend(prefix_ids+target_ids)
        row['labels'].extend([-100]*len(prefix_ids)+target_ids[:kept]+[-100]*(len(target_ids)-kept))
        receipt['supplemented_sources'].append({'key':row['key'],'correct_targets_supervised':kept,
                                                'additional_context_tokens':len(prefix_ids),
                                                'correct_targets_masked':len(target_ids)-kept})
        remaining-=kept
        if remaining==0:
            break
    if remaining:
        raise ValueError('bounded same-source supplementation cannot meet the target budget')
    return rows,receipt


def development(tok):
    validation,choices,source_worlds=[],[],[]
    for domain in POP.DOMAINS:
        kept=0
        for i in range(3000):
            world=sampled_world(POP.pop_lid(i,domain,10100000),'original')
            if parameter_partition(world)!='development' or world['degenerate']:
                continue
            events=world['trajectory']['steps']
            cut=(0,min(2,len(events)),min(4,len(events)),len(events))[kept%4]
            replay=Replay(world,events[:cut])
            distribution=replay.probabilities()
            rng=random.Random(int(digest({'validation_target':world['lid']})[:12],16))
            u=rng.random();truth=sorted(distribution)[-1]
            for action,probability in sorted(distribution.items()):
                u-=probability
                if u<=0:
                    truth=action;break
            options={a:LF.stop_line(cut) if a=='stop' else LF.event_line(cut,*a.split(':')) for a in distribution}
            choices.append({'key':world['lid'],'prefix':rendered_prefix(world,replay.steps,with_goal=kept%2==0),
                            'options':options,'truth':truth,'private_exact_distribution':distribution,
                            'cut':cut,'domain':domain,'parameter_partition':'development'})
            text=POP.world_log(world,kept%2==0)
            ids=tok(text+tok.eos_token,add_special_tokens=True).input_ids
            if len(ids)>2048:
                raise ValueError('development target exceeds declared cap')
            validation.append({'key':world['lid'],'input_ids':ids})
            source_worlds.append(world)
            kept+=1
            if kept==48:
                break
        if kept!=48:
            raise ValueError('bounded search failed to realize 48 independent development worlds per domain')
    return validation,choices,source_worlds


def prepare(family):
    from transformers import AutoTokenizer
    started=time.time();base=BASES[family]
    tok=AutoTokenizer.from_pretrained(base['model'],revision=base['revision'],local_files_only=True,trust_remote_code=False)
    pools={coverage:read(ROOT/'private/training-pools'/family/(coverage+'.json')) for coverage in ('original','both')}
    for pool in pools.values():
        if len(pool['candidate_examples'])!=1600 or any(parameter_partition(w)!='training' for w in pool['private_worlds'].values()):
            raise ValueError('incomplete pool or held-out source exposure')
    original=[replay_row(r) for r in pools['original']['candidate_examples']]
    budget=sum(len(target_positions(r)) for r in original)
    broad,adjustment=fit_expert_budget(tok,pools['both'],budget)
    comparisons=audit({'original_expert':original,'both_expert':broad},pools['original']['private_worlds'].keys())
    if any(r['input_ids']!=s['input_ids'] or r['labels']!=s['input_ids'] for r,s in zip(original,pools['original']['candidate_examples'])):
        raise ValueError('original factorial replay changed')
    validation,choices,worlds=development(tok)
    if set(pools['original']['private_worlds']) & {w['lid'] for w in worlds}:
        raise ValueError('instance split overlap')
    sources=closure([REPO/'runners/stage9'/n for n in ('expert_recipes.py','matching.py','recipes.py','construction.py','train.py','common.py')]
                    +[REPO/'runners/stage7/constructor',REPO/'runners/stage8/constructor',REPO/'runners/stage8/reader/logfmt.py',REPO/'runners/stage8/engines.py'])
    identity={'family':family,'base':base,'sources':sources,'comparisons':comparisons,'broad_adjustment':adjustment,
              'pool_identities':{k:p['identity'] for k,p in pools.items()},'development_worlds_sha256':digest(worlds),
              'validation_selection':'same 96 original-law development-combination worlds; complete support including STOP; no training or pilot instance',
              'historical_limit':'original rendering and capped token arrays retained; parameter eligibility conditions the population and must not be called an unfiltered Stage 8 dataset',
              'matching_limit':'same target count, examples and source-lineage exposure; context tokens and supplemental target draws are explicitly different'}
    output=ROOT/'private/scientific-recipes'/family
    for name,examples in [('original_expert',original),('both_expert',broad)]:
        freeze(output/(name+'.json'),{'split':'training','identity':identity|{'cell':name},'examples':examples,
                                      'validation':validation,'validation_choices':choices})
    freeze(output/'DEVELOPMENT_WORLDS.json',worlds)
    receipt={'identity_sha256':digest(identity),'family':family,'comparison':comparisons,'broader_adjustment':adjustment,
             'validation_worlds':len(worlds),'validation_stop_targets':sum(c['truth']=='stop' for c in choices),
             'preparation_seconds':time.time()-started,'scientific_fit_launched':False,
             'remaining':'learner collection from training-only qualified collector, mixed cells, final manifest and launch acceptance'}
    freeze(output/'EXPERT_PREPARATION.json',receipt)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--family',required=True,choices=BASES)
    args=p.parse_args();prepare(args.family)
