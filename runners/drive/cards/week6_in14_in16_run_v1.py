"""Sealed, resumable whole-writer draws for Week 6 IN14 and IN16.

DESIGN CHECK: LESSONS 2/3, CONTROLS 6/7. Every draw and failure retains its index;
partial execution/replay cannot emit a complete interval. No full-source outcome
has been computed during builder validation. Both source scopes stay distinct.
"""
from pathlib import Path
import hashlib
import json
import math
import os
import time
for _key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_key]='2'
import numpy as np
from . import week6_in14_math_v1 as in14
from . import week6_in16_math_v1 as in16
from . import week6_in14_in16_source_v1 as source
from . import week5_in12_v1 as common
from . import week5_in12_math_v1 as stats
from . import week5_engine_export_io as seal
from . import week5_qualification_io as io


def settings(card,config):
    if card not in ('IN14','IN16') or set(config)-{'source_scope','draws','max_new_draws','max_wall_seconds'}:
        raise ValueError('Undeclared card/settings')
    scope=config.get('source_scope')
    if scope not in source.SCOPES or config.get('draws',2000)!=2000:
        raise ValueError('Explicit source scope and full 2000 writer draws required')
    if type(config.get('max_new_draws',100)) is not int or config.get('max_new_draws',100)<1:
        raise ValueError('Positive whole-writer draw quantum required')
    if not np.isfinite(config.get('max_wall_seconds',900)) or config.get('max_wall_seconds',900)<=0:
        raise ValueError('Positive wall bound required')
    return {'card':card,'source_scope':scope,'draws':2000,'seed':20261107,
            'units':'rating points' if card=='IN14' else 'within-prompt ordinal-duration SD per raw N item point',
            'bar':.1,'source_scales':'fixed before resampling','interval':'whole-writer percentile 95%'}


def dependencies():
    modules=(in14,in16,source,common,stats,seal,io,source.original,source.duration)
    result={str(Path(m.__file__).resolve()):io.sha(m.__file__) for m in modules}|{str(Path(__file__).resolve()):io.sha(__file__),str(source.ELIGIBILITY):io.sha(source.ELIGIBILITY)}
    for name in ('week6_in14_v1.py','week6_in16_v1.py'):
        path=Path(__file__).with_name(name);result[str(path.resolve())]=io.sha(path)
    return result


def resample(keys,card,draw,panel=0):
    rng=np.random.default_rng(np.random.SeedSequence([20261107,int(card[2:]),draw,panel]))
    return dict(zip(keys,np.bincount(rng.integers(0,len(keys),len(keys)),minlength=len(keys)).tolist()))


def three_way(interval,bar=.1,direction=1):
    """Week 5 packet 0.6: direction-normalized, strict beyond-bar support."""
    low,high=map(float,interval)
    if direction not in (-1,1) or not math.isfinite(bar) or bar<=0 or not all(map(math.isfinite,(low,high))) or low>high:
        raise ValueError('Finite ordered interval, positive bar and signed direction required')
    if direction==-1:low,high=-high,-low
    if low>bar:return 'supports'
    if high<0 or (low>=-bar and high<=bar):return 'against'
    return 'inconclusive'


def summary(point,draws,writers,primary=False,reference=False,independent=False):
    bad=[i for i,v in enumerate(draws) if v is None]
    if point is None: return {'status':'unsupported','writers':writers,'failed_draws':bad}
    answer={'estimate':point,'writers':writers,'failed_draws':bad,'draws':len(draws)}
    if writers<2: return {**answer,'status':'unsupported','reason':'fewer than two independent writers'}
    if len(draws)!=2000: raise ValueError('Full bank required')
    if bad: return {**answer,'status':'invalid_uncertainty','reason':'failed draws retained without replacement'}
    interval,se=stats.interval_se(draws,independent)
    answer.update(status='complete' if writers>=20 else 'below floor, descriptive',interval=interval,bootstrap_SE=se)
    if primary:
        answer.update(bar=.1,sees=2.8*se,supports_at=.1+2.8*se,limited_sensitivity=2.8*se>.1,
                      sensitivity_approximation='normal approximation, slightly optimistic')
        if writers>=20 and not reference:
            # Both registered primaries have positive direction in their frozen units.
            answer['outcome']=three_way(interval,.1,1)
    return answer


def calculate(card,frame,identity,output,config,independent=False):
    semantic=settings(card,config);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if card=='IN14':
        rows,counts=in14.pairs(frame,identity['eligible_rounds']);prepared=in14.prepare(rows)
        keys=sorted(rows.prolific_id.unique()) if not rows.empty else []
        support={'pair_dispositions':counts,'rated_feelings':list(in14.FEELINGS),'explicit_session_ID_available':False}
        evaluate=in14.evaluate
    else:
        prepared=in16.prepare(frame);keys=prepared['keys'];support=prepared['support'];evaluate=in16.evaluate
    result={'card':card,'record_kind':'claim','theory_tags':['H18-G3','H17-BOUND'] if card=='IN14' else ['H18-SURPRISE-3'],
            'by_construction':identity.get('constructed',False),'activation':[], 'semantic':semantic,
            'source_identity':identity,'support':support,'scope':'adult recalled events under assigned prompts; lowercase evidence',
            'all_report_reference':config['source_scope']=='all-report-reference'}
    if len(keys)<2: return {**result,'status':'unsupported','complete_card':True,'reason':'fewer than two eligible writers'}
    binding=common.digest({'identity':identity,'semantic':semantic,'dependencies':dependencies(),'frame':frame.to_json(orient='split'),'independent':independent})
    saved=seal.state(output/'DRAWS.json',binding,{'point':None,'draws':[]})
    if saved['point'] is None:
        saved['point']=evaluate(prepared,dict.fromkeys(keys,1),independent);seal.checkpoint(output/'DRAWS.json',saved)
    start=time.monotonic();added=0
    while len(saved['draws'])<2000:
        if common.should_yield(output,start,config,added):
            seal.checkpoint(output/'DRAWS.json',saved)
            return {'status':'yielded','verified':False,'phase':card+'_writer_draws','completed':len(saved['draws']),'total':2000}
        weights=resample(keys,card,len(saved['draws']))
        if card=='IN16':
            weights={name:resample(prepared[part]['keys'],card,len(saved['draws']),i+1) if prepared[part] else {}
                     for i,(name,part) in enumerate([('clearing','clearing'),('writer_share','share')])}
        saved['draws'].append(evaluate(prepared,weights,independent));added+=1
        if len(saved['draws'])%10==0:
            seal.checkpoint(output/'DRAWS.json',saved);io.write_json(output/'PROGRESS.json',{'completed':len(saved['draws']),'total':2000})
    seal.checkpoint(output/'DRAWS.json',saved);point=saved['point']['value'];reference=result['all_report_reference']
    if card=='IN14':
        panels={}
        for name,value in point.items():
            panel=prepared[name];n=len(panel['keys']) if panel else 0;panels[name]={}
            terms=('increase',) if name=='same_valence_reach' else ('prompt','same_valence','shape_minus_mood')
            for term in terms:
                panels[name][term]=summary(value[term] if value else None,
                    [d['value'][name][term] if d['value'][name] else None for d in saved['draws']],n,name=='under10' and term=='prompt',reference,independent)
        people=in14.person_preparation(rows,independent)
        seal.checkpoint(output/'PERSON_PREPARATION_PRIVATE.json',{'writers':people})
        under10=panels.pop('under10');panels['under10_shape_and_mood']={k:v for k,v in under10.items() if k!='prompt'}
        result.update(primary=under10['prompt'],secondary=panels,
            person_preparation={'writers_with_four_pairs':len(people),'halves_sharing_survey':sum(r['halves_share_survey'] for r in people),
                'corrected_reliability_computed':False},
            held_secondaries={'person':'TR1 corrected split-half and trait relation require calibrated noise/dependence mapping for overlapping survey pairs'})
    else:
        panels={name:summary(value,[d['value'][name] for d in saved['draws']],
                    len(prepared['share' if name=='writer_share' else 'clearing']['keys']) if prepared['share' if name=='writer_share' else 'clearing'] else 0,
                    name=='clearing',reference,independent) for name,value in point.items()}
        result.update(primary=panels.pop('clearing'),secondary=panels,scales=prepared['scales'],N_writer_SD=prepared['N_writer_SD'],
                      writer_share_method='conditional random intercept REML; tau2/(tau2+sigma2)')
    result.update(status='complete',complete_card=True,failed_draws_never_removed=True)
    return result


def execute(card,output,inputs,config):
    semantic=settings(card,config);frame,identity=source.load(inputs,card,semantic['source_scope'])
    answer=calculate(card,frame,identity,output,config)
    if answer.get('status')!='yielded':io.write_json(Path(output)/'RESULT.json',answer)
    return answer


def verify(card,output,inputs,config):
    semantic=settings(card,config);output=Path(output);frame,identity=source.load(inputs,card,semantic['source_scope'])
    replay=output/'independent-replay';answer=calculate(card,frame,identity,replay,config,True)
    if answer.get('status')=='yielded': return {**answer,'verified':False}
    common.compare(seal.read(output/'RESULT.json'),answer)
    if (output/'PERSON_PREPARATION_PRIVATE.json').exists():
        common.compare(seal.read(output/'PERSON_PREPARATION_PRIVATE.json'),seal.read(replay/'PERSON_PREPARATION_PRIVATE.json'))
    if (output/'DRAWS.json').exists():
        left=seal.read(output/'DRAWS.json');right=seal.read(replay/'DRAWS.json')
        common.compare(left['point'],right['point']);common.compare(left['draws'],right['draws'])
    io.write_json(replay/'RESULT.json',answer)
    return {'verified':True,'all_draws_replayed':True,'no_demographic_columns_read':True}
