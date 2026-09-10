"""Exact exposed Stage 8 generation battery, separate from new 96-world profiles.

DESIGN CHECK: I01/C02/C05/X01/X08/X11; LESSONS 3--5, CONTROLS 6.
NULL: changed old rows, missing worlds or a changed original reference refuse.
ALTERNATIVE: all forty archived worlds reproduce their full recorded continuation
and the original same-world reference. This is exposed historical diagnosis;
neither new labels nor new split names create an untouched confirmation sample.
The two-world pilot exercises the same loading path without replacing the full
historical sample. New Stage 9 scientific broad profiles still use 96 worlds.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import time

from runners.stage9.common import REPO,ROOT,closure,digest,file_hash,freeze,read
from runners.stage9.generation_pilot import original_world
from runners.stage9.queue import inside,verify_sources,writer
from runners.stage9.recipes import POP
from runners.stage9.series_cases import content_identity
from runners.stage9.training_jobs import cell_identity

ARCHIVE=REPO/'results/phase_2_4_stage_8'
PINS={'E04/cases.jsonl':'80690be78d0a7e8a780f27e8bef111bc86c7ffbe0c2e63f832f8606bd5be6892',
      'E04/metrics.json':'b2e18c20337397a6c8d02311d6fc6b60a33c319a2bd7fbcaf93f0e27ec286483'}


def archived_worlds():
    for name,sha in PINS.items():
        if file_hash(ARCHIVE/name)!=sha:raise ValueError('historical generation evidence changed')
    rows=[json.loads(line) for line in (ARCHIVE/'E04/cases.jsonl').read_text(encoding='utf-8').splitlines()]
    families={name:[r for r in rows if r['model_id']==name] for name in ('adapter:fm_qwen','adapter:fm_smollm')}
    lids={name:[r['lineage_id'].split('~')[0] for r in sub] for name,sub in families.items()}
    if (any(len(v)!=40 or len(set(v))!=40 for v in lids.values())
        or set(lids['adapter:fm_qwen'])!=set(lids['adapter:fm_smollm'])):
        raise ValueError('historical battery omits or repeats an original reader/world')
    worlds=[];files=[ARCHIVE/name for name in PINS]
    for row in families['adapter:fm_qwen']:
        # Archived absolute paths are provenance; derive a bounded local path
        # from the validated source lineage rather than following arbitrary paths.
        lid=row['lineage_id'].split('~')[0]
        path=ARCHIVE/'oracle/E04'/(lid.replace('|','-')+'~fm.json')
        if not path.resolve().is_relative_to(ARCHIVE/'oracle/E04'):
            raise ValueError('historical truth path escapes its archive')
        truth=read(path);world=original_world(lid);files.append(path)
        tail=[{k:e[k] for k in ('type','section','slot','outcome')}
              for e in world['trajectory']['steps'][world['cut']:]]
        if (truth['lid']!=lid or world['cut']!=truth['cut'] or world['state']['names']!=truth['state_names']
            or world['hidden']['next_action']!=truth['hidden']['next_action'] or tail!=truth['hidden']['tail']
            or world['degenerate'] or not POP.feasible_visible(world,world['trajectory']['steps'])['all_feasible']):
            raise ValueError('original world differs from its archived continuation or fails visible feasibility')
        worlds.append(world)
    if Counter(w['domain'] for w in worlds)!=dict.fromkeys(POP.DOMAINS,20):
        raise ValueError('original forty-world domain allocation changed')
    scores=[POP.marginal_log_likelihood(w)['per_event'] for w in worlds]
    metric=read(ARCHIVE/'E04/metrics.json')
    if (metric['n_real']!=40 or sorted(scores)[round(.2*(len(scores)-1))]!=metric['real_percentile_value']
        or any(v['n']!=40 for v in metric['readers'].values())):
        raise ValueError('original population reference does not reproduce')
    return worlds,scores,closure(files)


def world_plan(scope):
    if scope not in ('pilot','scientific'):raise ValueError('undeclared historical replay scope')
    worlds,scores,archive=archived_worlds()
    indices=(list(range(40)) if scope=='scientific' else
             [next(i for i,w in enumerate(worlds) if w['domain']==d) for d in POP.DOMAINS])
    selected=[worlds[i] for i in indices]
    return {'worlds':selected,'reference_scores':[scores[i] for i in indices],
        'original_archive':archive,'original_worlds':40,'original_reference_scores':scores,
        'selected_archive_indices':indices,'reference_policy':'same original worlds, computed before new predictions',
        'previously_exposed':True,'confirmation_eligible':False,'parameter_partition':'unfiltered archived sample; no new reserve access',
        'role':'pilot' if scope=='pilot' else 'historical_replay'}


def checked_inputs(directory,scope,population='historical_replay'):
    directory=inside(directory);done=read(directory/'COMPLETE.json');identity=read(directory/'IDENTITY.json')
    if (population!='historical_replay' or done.get('accepted') is not True or done.get('construction_only') is not True
        or identity['operation']!='historical-generation-replay-v1' or identity['scope']!=scope
        or done['identity_sha256']!=digest(identity)
        or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']):
        raise ValueError('historical replay identity or output closure differs')
    plan=read(directory/'WORLD_PLAN.json')
    if digest(plan)!=digest(world_plan(scope)):raise ValueError('historical source or reference changed')
    cases=[{'unit':content_identity(w),'role':plan['role'],'source_worlds':[w]} for w in plan['worlds']]
    if len({c['unit'] for c in cases})!=len(cases):raise ValueError('repeated historical source content')
    return cases,plan['role'],file_hash(directory/'COMPLETE.json'),plan


def prepare(directory,scope):
    cell=cell_identity();directory=inside(directory)
    source=closure([REPO/'runners/stage9',REPO/'runners/stage7',REPO/'runners/stage8',REPO/'soundingline',
        REPO/'runners/__init__.py',REPO/'runners/readout_repair.py',REPO/'runners/s3_lib.py',REPO/'runners/s4_lib.py',REPO/'runners/s5_lib.py'])
    identity={'cell_identity':cell,'operation':'historical-generation-replay-v1','scope':scope,'source':source,'pins':PINS}
    with writer(directory):
        freeze(directory/'IDENTITY.json',identity)
        if (directory/'COMPLETE.json').exists():
            checked_inputs(directory,scope)
            return read(directory/'COMPLETE.json')
        started,cpu=time.monotonic(),time.process_time();plan=world_plan(scope)
        freeze(directory/'WORLD_PLAN.json',plan);verify_sources(source)
        done={'cell_identity':cell,'identity_sha256':digest(identity),'accepted':True,'construction_only':True,
            'scope':scope,'role':plan['role'],'reader_worlds':len(plan['worlds']),
            'reference_worlds':len(plan['reference_scores']),'original_worlds':40,'previously_exposed':True,
            'confirmation_eligible':False,'scientific_admission':False,
            'wall_seconds':time.monotonic()-started,'parent_cpu_seconds':time.process_time()-cpu,
            'outputs':closure([directory/'IDENTITY.json',directory/'WORLD_PLAN.json'])}
        freeze(directory/'COMPLETE.json',done);return done


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--scope',choices=('pilot','scientific'),required=True)
    a=p.parse_args();prepare(a.output,a.scope)
