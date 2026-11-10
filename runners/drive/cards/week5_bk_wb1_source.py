"""Authenticated immutable WB1 source and first-tenth cost-work descriptors.

DESIGN CHECK: original source, candidate superset and seed-only sample remain.
No outcome is estimated; individual records and raw paths stay private.
"""
from pathlib import Path
import math
import os
import time
from runners.stage14.common import read, filehash, digest, atomic
from . import week3_pieces_effects_h1_pilot as pilot
from . import week3_pieces_coverage as coverage
from . import week3_pieces_stats as stats
from . import week3_pieces_effects_h1 as effects
from .timing_events import source_sessions
from .timing_p6 import gzread, gzip_equal, write_equal
from .week5_at_source import authenticate
from .batch_runtime import check_files


def configuration(mode='corpus',coarse=False):
    if mode not in ('corpus','constructed') or type(coarse) is not bool:
        raise ValueError('Exact WB1 source mode required')
    return dict(mode=mode,coarse=coarse,seed=stats.SEED,sample_denominator=10 if mode=='corpus' else 1,
                minimum_occurrences=30 if mode=='corpus' else 1,minimum_writers=10 if mode=='corpus' else 1)


def checked(path,value,verifying=False,gzip=False):
    if verifying:
        actual=gzread(path) if gzip else read(path)
        if actual!=value:raise ValueError('Fresh immutable WB1 record differs')
    elif gzip:gzip_equal(path,value)
    else:write_equal(path,value)


def completed(path,module=None):
    root=Path(path)
    if root.name=='COMPLETE.json':root=root.parent
    root=authenticate(root);plan=read(root/'PLAN.json');check_files(plan['pins'])
    if module is not None and plan['module']!=module:raise ValueError('Wrong WB1 dependency producer')
    return root,plan


def model(inputs,mode):
    if mode=='corpus':
        path=Path(inputs['content_model']).resolve();complete=Path(inputs['content_complete']).resolve()
        receipt=read(complete)
        if receipt.get('status')!='COMPLETE' or receipt['outputs'].get(path.relative_to(complete.parent).as_posix())!=filehash(path):
            raise ValueError('Original CONTENT_V2 model identity changed')
        effects.events_p5.model_identity(path)


def load(root):
    root,plan=completed(root,__name__)
    cfg=plan['config']
    if cfg!=configuration(cfg.get('mode'),cfg.get('coarse')):raise ValueError('Changed WB1 source configuration')
    manifest=read(root/'output/SOURCE.json')
    if manifest['config']!=cfg:raise ValueError('Source manifest configuration mismatch')
    rows=gzread(root/'output/COVERAGE_ROWS.json.gz')
    if digest(rows)!=manifest['rows_sha256']:raise ValueError('Source row bank changed')
    return root,manifest,rows


def run(output,inputs,config,verifying=False):
    if config!=configuration(config.get('mode'),config.get('coarse')):raise ValueError('Frozen WB1 source contract required')
    extra={'prior_wb1_complete','prior_wb1_result'} if config['coarse'] and config['mode']=='corpus' else set()
    if set(inputs)!=pilot.PREP_KEYS|{'source_inputs','content_model','content_complete'}|extra:
        raise ValueError('Exact original source bundle required')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);began=time.monotonic()
    prep={k:inputs[k] for k in pilot.PREP_KEYS|extra}
    rows=coverage.load(prep,dict(mode=config['mode'],coarse=config['coarse']))
    sources=read(inputs['source_inputs'])
    expected={'repo_root','session_index','foundation_complete','foundation_plan','raw_roster','prepared_sessions'}
    if set(sources)!=expected:raise ValueError('Original source bundle shape changed')
    bound=read(inputs['preparation_result'])['source_bindings']
    for key,path in sources.items():
        if key!='repo_root' and bound.get(str(Path(path).resolve()))!=filehash(path):
            raise ValueError('Effect source differs from canonical preparation')
    model(inputs,config['mode'])
    candidates=stats.candidates([r for r in rows if r['side']=='discovery'],config['minimum_occurrences'],config['minimum_writers'])
    selected=pilot.selection(rows,config['sample_denominator']);by_session={r['session']:r for r in rows}
    binding=digest(dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()}))
    checked(root/'BINDING.json',dict(binding=binding),verifying)
    descriptors=[];counts={};seen=set()
    for index,(source_row,timeline,meta) in enumerate(source_sessions(sources,'raw_roster')):
        if (root/'YIELD_REQUEST.json').exists() or time.monotonic()-began>=1200:
            return dict(status='yielded',reason='authenticated complete source-session boundary')
        session=source_row['session'];row=by_session[session]
        if row['writer']!=source_row['writer']:raise ValueError('Prepared writer mismatch')
        occurrences=list(pilot.occurrences(row,candidates));counts[session]=len(occurrences)
        raw=(Path(sources['repo_root'])/meta['path']).resolve()
        timeline_path=(Path(sources['session_index']).resolve().parent/source_row['file']).resolve()
        value=dict(index=index,session=session,writer=row['writer'],side=row['side'],
                   raw_path=str(raw),raw_sha256=filehash(raw),timeline_path=str(timeline_path),
                   timeline_sha256=filehash(timeline_path),cost_selected=session in selected,
                   candidate_occurrences=occurrences if session in selected else [],binding=binding)
        name=f'sessions/session-{index:04d}.json.gz'
        checked(root/name,value,verifying,True)
        descriptors.append(dict(index=index,session=session,file=name,sha256=filehash(root/name),
                                cost_selected=session in selected,candidate_occurrences=counts[session]))
        seen.add(session)
        atomic(root/'PROGRESS.json',dict(phase='verify' if verifying else 'source',sessions=len(seen),total=len(rows)))
    if seen!=set(by_session) or len(descriptors)!=len(rows):raise ValueError('Original full source census changed')
    checked(root/'COVERAGE_ROWS.json.gz',rows,verifying,True)
    manifest=dict(config=config,binding=binding,rows_sha256=digest(rows),sessions=descriptors,
                  candidates=[dict(symbols=list(k),**v) for k,v in sorted(candidates.items())],
                  counts=counts,selected_sessions=sorted(selected),writers=len({r['writer'] for r in rows}),
                  inputs=inputs,scientific_admission=False,source_only=True)
    checked(root/'SOURCE.json',manifest,verifying)
    return dict(verified=True,complete_original_source_replay=True) if verifying else dict(status='complete',source_only=True)


def session(root,manifest,entry):
    path=Path(root)/'output'/entry['file']
    if filehash(path)!=entry['sha256']:raise ValueError('Session descriptor changed')
    value=gzread(path)
    if value['binding']!=manifest['binding'] or value['session']!=entry['session'] or value['index']!=entry['index']:
        raise ValueError('Session identity changed')
    for path_key,sha_key in [('raw_path','raw_sha256'),('timeline_path','timeline_sha256')]:
        if filehash(value[path_key])!=value[sha_key]:raise ValueError('Original session source changed')
    return value


def timed(function,output,inputs,config,verifying):
    root=Path(output);phase='VERIFY' if verifying else 'EXECUTE';began=time.process_time();stamp=time.time_ns();value=None
    try:
        value=function(output,inputs,config,verifying)
        return value
    finally:
        ledger=root/'cost_ledger';ledger.mkdir(parents=True,exist_ok=True)
        write_equal(ledger/f'{phase}-{os.getpid()}-{stamp}.json',dict(process_cpu_seconds=time.process_time()-began,
                    outcome='exception' if value is None else value.get('status','verified')))
        done=value is not None and (value.get('verified') is True or value.get('status')=='complete')
        path=root/(phase+'_COST.json')
        if done and not path.exists():write_equal(path,dict(process_cpu_seconds=sum(read(p)['process_cpu_seconds'] for p in ledger.glob(phase+'-*.json')),
                                                          startup_and_prior_attempts_additional=True))


def execute(output,inputs,config):return timed(run,output,inputs,config,False)
def verify(output,inputs,config):return timed(run,output,inputs,config,True)
