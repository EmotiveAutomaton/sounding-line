"""Frozen constructed calibration of the unchanged TR3 recurrence consumer.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 6-7 reread 2026-10-27. NULL:
at most ten false positive/negative routes in 100 worlds. ALTERNATIVES:
at least eighteen correct routes in each twenty positive/negative worlds.
Incomplete worlds, undefined or wrong-direction routes do not earn a pass.
No failed gate is healed; no human data are consumed by this instrument.
"""
import json
from pathlib import Path
import time
from runners.stage14.common import read,filehash,freeze,atomic,canonical,digest
from . import week3_tr3_statistics as stats

WORLDS = [(0,20261026+i) for i in range(100)] + [(1,20261126+i) for i in range(20)] + [(-1,20261146+i) for i in range(20)]
CONFIGS = {m:dict(version=1,mode=m,worlds=[list(x) for x in (WORLDS[:1] if m=='timing' else WORLDS)],
    writers=20,sessions=4,permutations=200,bootstraps=2000) for m in ('timing','full')}


def summarize(cells, mode):
    expected=CONFIGS[mode]['worlds']
    if [[c['effect'],c['seed']] for c in cells]!=expected:
        raise ValueError('complete frozen world matrix required')
    bank={v:[] for v in (-1,0,1)}
    for c in cells:bank[c['effect']].append(c['result']['metrics']['primary']['route'])
    counts=dict(null_worlds=len(bank[0]),positive_worlds=len(bank[1]),negative_worlds=len(bank[-1]),
        false_routes=sum(r in ('positive','negative') for r in bank[0]),
        positive_routes=bank[1].count('positive'),negative_routes=bank[-1].count('negative'))
    passed=(counts['false_routes']<=10 and counts['positive_routes']>=18 and counts['negative_routes']>=18) if mode=='full' else None
    return dict(constructed=True,mode=mode,counts=counts,calibration_passed=passed,
        complete_calibration=mode=='full',human_statistic_computed=False,scientific_admission=False,
        scope='Constructed instrument calibration with original matching, rebuilt histories and unchanged routing rules')


def run(output,inputs,config,verification=False):
    mode=config.get('mode')
    if mode not in CONFIGS or config!=CONFIGS[mode]:raise ValueError('frozen constructed matrix required')
    required={'fixture_landing'}|({'timing_completion','timing_landing'} if mode=='full' else set())
    if set(inputs)!=required:raise ValueError('explicit calibration admission required')
    landing=read(inputs['fixture_landing'])
    if not landing['full_write_through'] or not landing['fixture_hold_cleared']:
        raise ValueError('corrected constructed fixture not admitted')
    if landing['implementation_sha256']!=filehash(Path(stats.__file__)):
        raise ValueError('estimator differs from corrected-fixture record')
    if mode=='full':
        gate=read(inputs['timing_landing'])
        if not gate['full_write_through'] or not gate['admitted'] or gate['completion_sha256']!=filehash(inputs['timing_completion']):
            raise ValueError('complete measured cost admission required')
        c=read(inputs['timing_completion'])
        if not c['fresh_process_verified']:raise ValueError('independent timing replay required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    binding=dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()})
    if (output/'BINDING.json').exists() and read(output/'BINDING.json')!=binding:
        raise ValueError('calibration binding changed')
    freeze(output/'BINDING.json',binding)
    cells=[];new_cpu=0;new_count=0
    for i,(effect,seed) in enumerate(config['worlds']):
        world=stats.world(seed,effect,writers=config['writers'],sessions=config['sessions'])
        path=output/'cells'/f'{i:03d}.json';path.parent.mkdir(exist_ok=True)
        if path.exists() and not verification:
            cell=read(path)
            if cell['world']!=world or cell['world_sha256']!=digest(world) or cell['effect']!=effect or cell['seed']!=seed:
                raise ValueError('retained world construction differs')
        else:
            start=time.process_time()
            result=stats.describe(stats.Study(**world),permutations=200,bootstraps=2000,seed=20261026)
            cell=json.loads(canonical(dict(effect=effect,seed=seed,world=world,world_sha256=digest(world),result=result)))
            if verification:
                if read(path)!=cell:raise ValueError('whole constructed consumer replay differs')
            else:
                freeze(path,cell);new_cpu+=time.process_time()-start;new_count+=1
        cells.append(cell)
        atomic(output/'PROGRESS.json',dict(phase='verify-worlds' if verification else 'worlds',done=i+1,total=len(config['worlds'])))
        if mode=='full' and not verification and new_count==14:
            freeze(output/'FIRST_TENTH.json',dict(new_worlds=new_count,measured_cpu_seconds=new_cpu,
                projected_cpu_seconds=2*new_cpu/new_count*len(config['worlds'])))
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():
            raise InterruptedError('calibration yields at complete world boundary')
    summary=summarize(cells,mode)
    if verification:
        if read(output/'SUMMARY.json')!=summary:raise ValueError('calibration summary replay differs')
        return dict(verified=True,complete_input_replay=True,all_worlds_recomputed=True)
    freeze(output/'SUMMARY.json',summary)
    return dict(status='complete',summary=summary)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
