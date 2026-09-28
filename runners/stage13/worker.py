"""Native complete-block worker, immutable attempts and semantic replay.

DESIGN CHECK: LESSONS 3-5. NULL: unknown attempts, failed prerequisites, changed
sources, Gear 1 GPU work and expired blocks refuse. ALTERNATIVE: validated full
outputs re-enter without another model call; independent failures can continue.
"""
from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
import argparse
import json
import os
import time
from .common import RAW,REPO,read,freeze,atomic,filehash,now,bound,limit_process,check_pins
from runners.stage9.process_identity import native_identity


def verify(out):
    done=read(out/'COMPLETE.json')
    if done['status']!='complete':raise ValueError('not complete')
    for name,h in done['outputs'].items():
        if filehash(out/name)!=h:raise ValueError('completed output tampered: '+name)
    return done


def outputs(raw,ids,name='PREDICTIONS.json'):
    return [raw/'jobs'/i/name for i in ids]


def handle(card,out,raw,tick):
    action=card['action'];args=card.get('args',{})
    if action in ('qwen-development-repair','memory-development-admission','memory-development-batch'):
        from .development_repair import handle as repaired_handle
        return repaired_handle(card,out,raw,tick)
    if action=='schola-coupling':
        from .schola import run as schola_run
        return schola_run(read(raw/args['rows']),out,tick)
    if action.startswith('readout-'):
        from . import readouts
        if action=='readout-admission':return readouts.admission(out)
        if action=='readout-batch':return readouts.run(read(raw/args['rows']),out,tick)
        result=readouts.summarize([r for p in outputs(raw,args['blocks']) for r in read(p)['rows']]);freeze(out/'ANALYSIS.json',result);return result
    if action.startswith('legacy-'):
        from . import legacy
        return getattr(legacy,action.removeprefix('legacy-'))(out)
    if action=='detector-admission':
        from .detectors import admission
        return admission(args['arm'],out,raw)
    if action=='detector-batch':
        from .detectors import batch
        identity=read(raw/'jobs'/card['gates'][0]/'ADMISSION.json')['identity']
        return batch(args['arm'],read(raw/args['rows']),out,raw,tick,expected_identity=identity)
    if action=='located-fit':
        from .located import train_crossfit
        return train_crossfit(read(raw/args['rows']),out,tick)
    if action=='detector-select':
        from .detectors import merge_predictions,fit_and_select
        merged={part:merge_predictions(read(raw/path),outputs(raw,args['blocks'][part])) for part,path in args['sources'].items()}
        from .located import features
        located=read(raw/'jobs'/args['located']/'MODEL.json')
        merged={k:features(v,located,training=k=='train') for k,v in merged.items()}
        return fit_and_select(merged['train'],merged['development'],merged['calibration'],out)
    if action=='detector-evaluate':
        from .detectors import merge_predictions,evaluate
        rows=merge_predictions(read(raw/args['rows']),outputs(raw,args['blocks']))
        from . import located
        m=read(raw/'jobs'/args['located']/'MODEL.json');rows=located.features(rows,m)
        result=evaluate(read(raw/'jobs'/args['selection']/'SELECTION.json'),rows);result['locations']=located.evaluate(rows,m);freeze(out/'ANALYSIS.json',result);return result
    if action=='reconstruction-fit':
        from .reconstruction import model_fit
        result=model_fit(read(raw/args['rows']));freeze(out/'MODEL.json',result);return result
    if action=='reconstruction-batch':
        from .reconstruction import run_batch
        return run_batch(read(raw/args['rows']),read(raw/'jobs'/args['model']/'MODEL.json'),out,tick=tick)
    if action in ('reconstruction-summary','qwen-summary'):
        from .reconstruction import summarize
        records=[r for p in outputs(raw,args['blocks']) for r in read(p)['rows']]
        ineligible=[r for r in records if r.get('scores') is None]
        if ineligible:raise ValueError('ineligible main reader histories retained; complete-only comparison unavailable')
        result=summarize(records);freeze(out/'ANALYSIS.json',result);return result
    if action=='context-batch':
        from .context import run
        return run(read(raw/args['rows']),read(raw/args['training']),out,raw,tick=tick)
    if action=='context-summary':
        from .context import summarize
        from .calibration import fit,evaluate
        records=[r for p in outputs(raw,args['blocks']) for r in read(p)['rows']]
        result=summarize(records)
        if args.get('calibration'):
            cal=[r for p in outputs(raw,args['calibration']) for r in read(p)['rows']]
            result['calibration']={}
            for view,mode in sorted({(r['view'],r['mode']) for r in records if r.get('scores') is not None}):
                train=[r for r in cal if r['view']==view and r['mode']==mode];test=[r for r in records if r['view']==view and r['mode']==mode and r['partition']=='reserve']
                model=fit(train);result['calibration'][view+'/'+mode]=dict(fit=model,evaluation=evaluate(test,model))
        freeze(out/'ANALYSIS.json',result);return result
    if action=='roberta-evaluate':
        from .training import evaluate
        return evaluate(raw/'jobs'/args['training_job']/'best',{p:read(raw/x) for p,x in args['sources'].items()},out,tick,raw)
    if action=='roberta-training':
        from .training import train
        return train(read(raw/args['training']),read(raw/args['development']),out,tick,raw)
    if action in ('qwen-admission','qwen-batch'):
        from . import gpu
        from .reconstruction import score_prediction,predict
        rows=read(raw/args['rows']);records=[]
        model=read(raw/'jobs'/args['model']/'MODEL.json') if args.get('model') else None
        with gpu.service(out,raw) as state:
            for row in rows:
                for view in args.get('views',['C']):
                    for arm in args.get('arms',['direct','joint','without-goals','without-execution','equal-direct']):
                        tick();e=row['views'][view]
                        try:gpu.request(e,arm)
                        except ValueError as exc:
                            records.append(dict(key=row['key'],unit=row['unit'],partition=row['partition'],view=view,arm=arm,preflight_ineligible=str(exc),scores=None));continue
                        receipt=gpu.call(e,arm,out/'calls'/f"{row['key']}-{view}-{arm}",state,raw)
                        p=receipt['parsed']
                        if p is None:
                            from .reconstruction import SLOTS
                            p=dict(invalid=True,handling=None,facts=[dict(slot=s,exact_spans=[]) for s in SLOTS],attributes={})
                        record=dict(key=row['key'],unit=row['unit'],partition=row['partition'],admission_control=row.get('control'),view=view,arm=arm,prediction=p,metadata={},scores=score_prediction(row,p,{}),call=receipt)
                        records.append(record)
                        if arm=='joint' and receipt['parsed'] and model:
                            for coupling in ('joint-execution','without-goal-coupling','shuffled-goal-coupling'):
                                g=receipt['parsed']['goal_support'];compatibility=[g[0],g[1],g[2],g[2]]
                                pred,meta=predict(e,model,coupling,compatibility)
                                records.append(dict(key=row['key'],unit=row['unit'],partition=row['partition'],view=view,arm='reader-'+coupling,prediction=pred,metadata=meta,scores=score_prediction(row,pred,meta)))
        admitted=bool(records) and all(r.get('scores') and r.get('call',{}).get('parsed') is not None for r in records if not r['arm'].startswith('reader-'))
        if action=='qwen-admission':
            controls=[r for r in records if r.get('admission_control')=='observed-adoption']
            admitted=admitted and len(controls)==1 and controls[0]['scores']['handling']['correct']==1 and controls[0]['scores']['location']['strict']==1 and all(controls[0]['scores'][f]['correct']==1 for f in ('actor','operation','relation'))
        result=dict(rows=records,admitted=admitted,scope='literal schema and service-native token admission; scientific performance remains independently scored')
        freeze(out/'PREDICTIONS.json',result)
        if action=='qwen-admission':freeze(out/'ADMISSION.json',dict(admitted=admitted,rows=len(records)))
        return result
    raise ValueError('unimplemented action '+action)


def run(card_path,raw=RAW):
    proc=limit_process();card_path=Path(card_path);card=read(card_path);out=raw/'jobs'/card['id']
    if not out.resolve().is_relative_to((raw/'jobs').resolve()):raise ValueError('output escaped stage')
    check_pins(card['source_pins'])
    for name,h in card.get('input_pins',{}).items():
        if filehash(raw/name)!=h:raise ValueError('input changed: '+name)
    if (out/'COMPLETE.json').exists():
        result=verify(out)
        if result['card_sha256']!=filehash(card_path):raise ValueError('card differs on reentry')
        return result
    if (out/'DISPATCH.json').exists() or (out/'FAILED.json').exists():raise RuntimeError('previous attempt requires reconciliation, no blind retry')
    bound(raw,card)
    if proc.memory_info().rss>2*1024**3:raise RuntimeError('unexpected worker footprint before model load')
    import psutil
    if psutil.virtual_memory().available<5*1024**3:raise RuntimeError('insufficient host memory; do not evict applications')
    for need in card.get('requires',[]):
        verify(raw/'jobs'/need)
    for gate in card.get('gates',[]):
        if read(raw/'jobs'/gate/'ADMISSION.json').get('admitted') is not True:raise RuntimeError('failed reader gate')
    start=time.monotonic();cpu0=sum(proc.cpu_times()[:2]);contract=read(raw/'CONTRACT.json')
    freeze(out/'DISPATCH.json',dict(at=now(),native=native_identity(),card_sha256=filehash(card_path),contract_sha256=filehash(raw/'CONTRACT.json')))
    def tick():
        if time.monotonic()-start>=card['wall_seconds']-15:raise TimeoutError('bounded complete-block timeout')
        if datetime.now(timezone.utc)>=datetime.fromisoformat(contract['reporting']):raise TimeoutError('reporting reserve reached')
        if any((raw/x).exists() for x in ('STOP.json','PAUSE.json')):raise RuntimeError('owner stop/pause')
        if card['resource']=='gpu' and read(raw/'ALLOCATION.json')['gear']!=2:raise RuntimeError('GPU reallocation requires natural stop')
    try:
        handle(card,out,raw,tick);tick()
        files={str(p.relative_to(out)):filehash(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name not in ('COMPLETE.json','PROGRESS.json') and not p.name.endswith('.tmp')}
        result=dict(status='complete',at=now(),id=card['id'],card_sha256=filehash(card_path),outputs=files,
            wall_seconds=time.monotonic()-start,cpu_seconds=sum(proc.cpu_times()[:2])-cpu0,resource=card['resource'],kind=card['kind'])
        freeze(out/'COMPLETE.json',result);return verify(out)
    except BaseException as exc:
        freeze(out/'FAILED.json',dict(status='failed',at=now(),error=type(exc).__name__+': '+str(exc),wall_seconds=time.monotonic()-start,cpu_seconds=sum(proc.cpu_times()[:2])-cpu0,card_sha256=filehash(card_path)))
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--card',type=Path,required=True);p.add_argument('--raw',type=Path,default=RAW);a=p.parse_args()
    try:run(a.card,a.raw)
    except BaseException as exc:
        out=a.raw/'jobs'/read(a.card)['id']
        if not (out/'COMPLETE.json').exists() and not (out/'FAILED.json').exists():freeze(out/'FAILED.json',dict(status='failed',at=now(),error=type(exc).__name__+': '+str(exc),phase='preflight',card_sha256=filehash(a.card)))
        raise
