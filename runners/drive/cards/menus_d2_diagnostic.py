"""Separately commissioned canonical-source D2 diagnostics, with measured pilot.

DESIGN CHECK: LESSONS3-5. Pilot measures execution only and emits no primary.
Full admission requires its verified unchanged source/code/config and copies
sealed pilot fits exactly. Every completed comparison freshly refits all three
models and controls from canonical sources. Original D2 remains source-held.
"""
import hashlib
import math
from pathlib import Path
import time
from . import menus_d2_diagnostic_source as source
from . import menus_d2_diagnostic_stats as stats
from .menus_io import read,write,sha256,assert_equal,input_hashes

CONFIG=dict(mode='pilot',fit_config=stats.original.CONFIG,diagnostic_seed=20261018,bootstrap=2000)
EXTRA={'pilot_plan','pilot_complete','pilot_summary'}


def load(inputs,config):
    mode=config.get('mode')
    if mode not in ('pilot','full') or dict(config,mode='pilot')!=CONFIG:
        raise ValueError('diagnostic frozen configuration differs')
    if set(inputs)!=source.INPUTS|(EXTRA if mode=='full' else set()):
        raise ValueError('diagnostic admission inputs differ')
    scientific_inputs={k:inputs[k] for k in source.INPUTS}
    data=source.load(scientific_inputs)
    if not data['splits']:raise ValueError('no eligible canonical recipient')
    return data


def binding(data):
    return dict(inputs=data['identity'],scientific_config={k:v for k,v in CONFIG.items() if k!='mode'},
        code={str(Path(m.__file__).resolve()):sha256(m.__file__) for m in (source,stats)})


def filename(writer):return hashlib.sha256(writer.encode()).hexdigest()[:24]+'.json'


def unit(output,writer,split,data,bind):
    path=output/'recipients'/filename(writer);seal=path.with_suffix('.seal.json')
    if seal.exists():
        assert_equal(read(seal),dict(binding=bind,sha256=sha256(path)));return read(path)
    start=time.perf_counter();result=stats.fit_recipient(split,data['cases'])
    saved=dict(writer=writer,result=result,fit_seconds=time.perf_counter()-start)
    write(path,saved);write(seal,dict(binding=bind,sha256=sha256(path)));return saved


def work(data,writer):
    return sum(len(data['cases'][r['key']]['x']) for s in data['splits'][writer]['train'] for r in s['rows'] if r['key'] in data['cases'])


def pilot_report(data,saved,source_seconds):
    writer=sorted(data['splits'])[0];total=sum(work(data,w) for w in data['splits']);den=work(data,writer)
    # First eligible recipient is selected before outcomes. Use the larger of
    # equal-recipient and training-option work extrapolations, plus source cost.
    multiple=max(len(data['splits']),total/den)
    return dict(card='D2-diagnostics-pilot',status='complete',execution_only=True,primary=None,
        scientific_admission=False,writer=writer,eligible_recipients=len(data['splits']),
        fit_seconds=saved['fit_seconds'],source_seconds=source_seconds,
        pilot_training_options=den,total_training_options=total,
        projected_seconds=2*(source_seconds+saved['fit_seconds']*multiple),
        forecast_method='Twice source cost plus all three models/controls; first eligible recipient, larger of equal-recipient or training-option work extrapolation. Full fresh refit included. No outcome selection.',
        input_hashes=data['identity'],scientific_config={k:v for k,v in CONFIG.items() if k!='mode'},
        source_census=data['census'])


def reuse(output,inputs,data):
    plan,complete,summary=(read(inputs[k]) for k in ('pilot_plan','pilot_complete','pilot_summary'))
    root=Path(inputs['pilot_complete']).parent.resolve();old=Path(inputs['pilot_summary']).parent.resolve()
    if (old!=root/'output' or Path(inputs['pilot_plan']).resolve()!=root/'PLAN.json'
            or complete.get('status')!='COMPLETE' or not complete.get('fresh_process_verified')
            or plan['module']!='runners.drive.cards.menus_d2_diagnostic' or plan['config']!=CONFIG):
        raise ValueError('verified diagnostic pilot required')
    if plan['pins'].get(str(Path(__file__).resolve()))!=sha256(__file__):raise ValueError('pilot admission source changed')
    for key in ('pilot_plan','pilot_summary'):
        rel=Path(inputs[key]).resolve().relative_to(root).as_posix()
        if complete['outputs'].get(rel)!=sha256(inputs[key]):raise ValueError('pilot terminal artifact changed')
    assert_equal(summary['input_hashes'],data['identity'])
    assert_equal(summary['scientific_config'],{k:v for k,v in CONFIG.items() if k!='mode'})
    if not summary['execution_only'] or summary['primary'] is not None or summary['writer']!=sorted(data['splits'])[0]:
        raise ValueError('pilot selection or interpretation differs')
    names=['BINDING.json','SOURCE_AUDIT.json','PARTITIONS.json']+['recipients/'+filename(summary['writer']),
        'recipients/'+filename(summary['writer']).replace('.json','.seal.json')]
    assert_equal(read(old/'BINDING.json'),binding(data))
    for name in names:
        src=old/name;dest=output/name
        if complete['outputs'].get('output/'+name)!=sha256(src):raise ValueError('pilot retained artifact changed')
        if dest.exists():
            if sha256(dest)!=sha256(src):raise ValueError('existing full differs from pilot')
        else:
            dest.parent.mkdir(parents=True,exist_ok=True)
            with src.open('rb') as a,dest.open('xb') as b:
                for block in iter(lambda:a.read(1024*1024),b''):b.write(block)
    value=dict(inputs=input_hashes({k:inputs[k] for k in EXTRA}),copied=names,byte_exact=True)
    immutable(output/'PILOT_REUSE.json',value)


def immutable(path,value):
    if path.exists():assert_equal(read(path),value)
    else:write(path,value)


def result(data,units):
    return dict(card='D2-diagnostics-canonical',status='complete',descriptive=True,scientific_admission=False,
        original_D2_unchanged_and_held=True,original_attempt_retry=False,extension_computed=False,
        input_hashes=data['identity'],source_census=data['census'],source_scope=data['scope'],
        exclusions=data['exclusions'],scientific_config={k:v for k,v in CONFIG.items() if k!='mode'},
        **stats.summarize({w:r['result'] for w,r in units.items()}))


def execute(output:Path,inputs:dict,config:dict)->dict:
    output=Path(output);output.mkdir(parents=True,exist_ok=True);start=time.perf_counter()
    data=load(inputs,config);source_seconds=time.perf_counter()-start;bind=binding(data)
    if config['mode']=='full':reuse(output,inputs,data)
    immutable(output/'BINDING.json',bind)
    immutable(output/'SOURCE_AUDIT.json',dict(rows=data['rows'],census=data['census'],scope=data['scope']))
    immutable(output/'PARTITIONS.json',data['partitions'])
    writers=sorted(data['splits']);requested=writers[:1] if config['mode']=='pilot' else writers;units={}
    for number,writer in enumerate(requested,1):
        if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',completed_recipients=len(units))
        units[writer]=unit(output,writer,data['splits'][writer],data,bind)
        if config['mode']=='full' and number>=max(1,math.ceil(.1*len(writers))) and not (output/'FIRST_TENTH.json').exists():
            write(output/'FIRST_TENTH.json',dict(completed_recipients=number,total_recipients=len(writers),
                projected_seconds=2*(source_seconds+sum(u['fit_seconds'] for u in units.values())*len(writers)/number),
                includes_fresh_refit=True))
    if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',completed_recipients=len(units))
    if config['mode']=='pilot':
        # Preserve original measured source timing on immutable reentry.
        if (output/'SUMMARY.json').exists():source_seconds=read(output/'SUMMARY.json')['source_seconds']
        report=pilot_report(data,units[writers[0]],source_seconds)
    else:report=result(data,units)
    report['recipient_hashes']={'recipients/'+filename(w):sha256(output/'recipients'/filename(w)) for w in units}
    immutable(output/'SUMMARY.json',report);return report


def verify(output:Path,inputs:dict,config:dict)->dict:
    output=Path(output);data=load(inputs,config);bind=binding(data);report=read(output/'SUMMARY.json')
    if config['mode']=='full':reuse(output,inputs,data)
    assert_equal(read(output/'BINDING.json'),bind)
    assert_equal(read(output/'SOURCE_AUDIT.json'),dict(rows=data['rows'],census=data['census'],scope=data['scope']))
    assert_equal(read(output/'PARTITIONS.json'),data['partitions'])
    writers=sorted(data['splits']);requested=writers[:1] if config['mode']=='pilot' else writers;units={}
    for writer in requested:
        path=output/'recipients'/filename(writer);saved=read(path)
        assert_equal(read(path.with_suffix('.seal.json')),dict(binding=bind,sha256=sha256(path)))
        if saved['writer']!=writer or not math.isfinite(saved['fit_seconds']) or saved['fit_seconds']<0:raise ValueError('invalid saved recipient')
        assert_equal(saved['result'],stats.fit_recipient(data['splits'][writer],data['cases']))
        units[writer]=saved
    actual=pilot_report(data,units[writers[0]],report['source_seconds']) if config['mode']=='pilot' else result(data,units)
    actual['recipient_hashes']={'recipients/'+filename(w):sha256(output/'recipients'/filename(w)) for w in units}
    assert_equal(report,actual)
    return dict(verified=True,canonical_source_replayed=True,fresh_refit_models=3,fresh_refit_controls=3,
        recipients=len(units),primary_recomputed=actual.get('primary'))
