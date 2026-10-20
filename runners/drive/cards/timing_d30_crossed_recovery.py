"""D30's single engineering retry, with immutable prefix and cumulative cost.

DESIGN CHECK: LESSONS 3-5. Preserve every row, seed, comparator and contrast.
Null and alternative receive the same certified numeric continuation. Changed
source/checkpoint bytes, mismatched failed attempt and a second failure refuse.
All retained fits must match fresh complete replay; no draw may be discarded.
"""
import math,time
from pathlib import Path
from datetime import datetime
from . import timing_d30_crossed_week as base
from . import crossed_reml_certified as solver
from .batch_runtime import read,filehash,check_files
from .timing_p6 import gzip_equal,gzread
from .timing_stats import bind,check_binding
from runners.stage14.common import freeze,atomic

CONFIG=base.CONFIG
CAP_SECONDS=base.CAP_SECONDS
DIAGNOSTIC_RESERVE=180.


def checked_fit(matrix):
    value=solver.fit(**matrix)
    if not value['converged'] or not math.isfinite(value['effect']):raise ValueError('uncertified fit')
    return value


def source(inputs,config):
    if set(inputs)!={'primary_completion','extension_completion','pilot_completion','failed_attempt'}:
        raise ValueError('exact single-retry inputs required')
    failed=Path(inputs['failed_attempt']);root=failed.parent;p=read(root/'PLAN.json');f=read(failed)
    original={k:v for k,v in inputs.items() if k!='failed_attempt'}
    if (f['status']!='FAILED' or p['module']!=base.__name__ or p['config']!=config or p['inputs']!=original
            or (root/'COMPLETE.json').exists()):raise ValueError('wrong failed attempt')
    check_files(p['pins'])
    wall=(datetime.fromisoformat(f['at'])-datetime.fromisoformat(read(root/'OWNER.json')['at'])).total_seconds()
    prior=p['prior_wall_seconds_charged']+wall+DIAGNOSTIC_RESERVE
    if wall<0 or prior>=CAP_SECONDS:raise ValueError('retry cumulative allowance unavailable')
    matrices,evidence=base.source(original,config)
    evidence.update(charged_pilot_seconds=prior,prior_main_seconds=wall,
                    diagnostic_reserve_seconds=DIAGNOSTIC_RESERVE,retry_number=1)
    binding=base.legacy.digest(dict(matrices=matrices,config=config))
    files=sorted((root/'output/bootstrap').glob('block-*.json'))
    files=[p for p in files if not p.name.endswith('.receipt.json')]
    for j,path in enumerate(files):
        item=read(path)
        if (item['binding']!=binding or item['start']!=25*j or item['stop']!=25*(j+1)
                or len(item['values'])!=25 or read(path.with_suffix('.receipt.json'))['sha256']!=filehash(path)):
            raise ValueError('retained retry checkpoint changed')
    if len(files)*25!=read(root/'output/PROGRESS.json')['done']:raise ValueError('retry prefix incomplete')
    evidence['retained_checkpoint_hashes']={p.name:filehash(p) for p in files}
    return matrices,evidence,files


def execute(output,inputs,config):
    output=Path(output);started=time.monotonic()
    if (output/'TIMING_BINDINGS.json').exists():return verify(output,inputs,config)['primary']
    freeze(output/'RUN_BINDINGS.json',dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()},source_sha256=filehash(__file__)))
    matrices,evidence,files=source(inputs,config)
    for path in files:
        for src in (path,path.with_suffix('.receipt.json')):
            dest=output/'bootstrap'/src.name;dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():
                if dest.read_bytes()!=src.read_bytes():raise ValueError('retry prefix reuse differs')
            else:
                with dest.open('xb') as stream:stream.write(src.read_bytes())
    prior=evidence['charged_pilot_seconds'];elapsed=lambda:prior+time.monotonic()-started
    setup=time.monotonic()-started;fit_started=time.monotonic();prefix=len(files)*25
    def checkpoint(phase,done,total):
        atomic(output/'PROGRESS.json',dict(phase=phase,done=done,total=total,cumulative_seconds=elapsed()))
        if (phase=='bootstrap' and done>prefix and done-prefix>=math.ceil((total-prefix)/10)
                and not (output/'FIRST_TENTH.json').exists()):
            active=sum(matrices[n] is not None for n in base.ARMS)
            fits=active*(2*total-prefix)+2*config['permutations']+2*active
            projection=2*setup+(time.monotonic()-fit_started)*fits/(active*(done-prefix))
            freeze(output/'FIRST_TENTH.json',dict(projected_seconds=projection,
                completed_new_draws_per_arm=done-prefix,retained_draws_per_arm=prefix,
                includes_all_controls_and_fresh_replay=True))
        if elapsed()>CAP_SECONDS:raise RuntimeError('retry cumulative ceiling exceeded')
        if (output/'YIELD_REQUEST.json').exists():raise base.Yield('saved complete recovery block')
    try:fitted=base.compute(matrices,config,output,checkpoint,fit_function=checked_fit)
    except base.Yield as exc:return dict(status='yielded',card=config['card'],reason=str(exc))
    if abs(fitted['points']['primary']['effect']-evidence['pilot_point']['effect'])>1e-6:raise ValueError('original point parity')
    result=base.summarize(matrices,evidence,fitted,config)
    gzip_equal(output/'DESIGNS.json.gz',dict(matrices=matrices,evidence=evidence))
    freeze(output/'FITS.json',fitted);freeze(output/'PRIMARY.json',result)
    freeze(output/'TIMING.json',dict(cumulative_seconds=elapsed(),prior_seconds_charged=prior,cap_seconds=CAP_SECONDS))
    bind(output,inputs,config,['DESIGNS.json.gz','FITS.json','PRIMARY.json','TIMING.json'])
    return result


def verify(output,inputs,config):
    output=Path(output);started=time.monotonic();check_binding(output,inputs,config)
    matrices,evidence,files=source(inputs,config)
    if gzread(output/'DESIGNS.json.gz')!=dict(matrices=matrices,evidence=evidence):raise ValueError('retry source replay')
    for path in files:
        if filehash(output/'bootstrap'/path.name)!=filehash(path):raise ValueError('retry prefix bytes differ')
    fitted=base.compute(matrices,config,fit_function=checked_fit)
    if fitted!=read(output/'FITS.json'):raise ValueError('retry uncached fit replay')
    result=base.summarize(matrices,evidence,fitted,config)
    if result!=read(output/'PRIMARY.json'):raise ValueError('retry report replay')
    if read(output/'TIMING.json')['cumulative_seconds']+time.monotonic()-started>CAP_SECONDS:raise RuntimeError('retry combined ceiling')
    return dict(verified=True,primary=result,full_uncached_replay=True,retained_prefix_exact=True,retry_number=1)
