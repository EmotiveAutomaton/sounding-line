"""Complete D37 calibration/human consumer with immutable arm checkpoints.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 read 2026-10-29. Common and page-only
worlds must not license complementary gain; the planted mixture must be seen.
All 200 reference refits, all recipients and all 30 worlds are required. Invalid
data, failed gates, missing draws or changed checkpoints refuse human inference.
Signed gain and negative controls remain separate; no partial scores reported.
"""
from pathlib import Path
import gzip,hashlib,json
import numpy as np
from scipy.stats import binomtest
from threadpoolctl import threadpool_limits
from . import week3_d37_workload as work
from . import week3_d37_readers as core
from .timing_census import read,filehash
from .timing_p6 import write_equal,progress

CONFIG=dict(card='D37-complete',schema=1,seed=work.SEED,permutations=work.PERMUTATIONS,
            bootstrap=work.BOOTSTRAP,worlds=work.WORLDS)


def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf8')


def digest(value):return hashlib.sha256(encoded(value)).hexdigest()


def slim(fit):
    return {k:dict(count=len(v),sha256=digest(v)) if k.endswith('_keys') else v for k,v in fit.items()}


def checkpoint(path,value=None):
    path=Path(path);seal=path.with_suffix('.seal.json')
    if value is None:
        if not path.exists() or not seal.exists() or filehash(path)!=read(seal)['sha256']:
            raise ValueError('Missing or changed complete arm checkpoint')
        value=json.loads(gzip.decompress(path.read_bytes()))
        if digest(value)!=read(seal)['content_sha256']:raise ValueError('Changed checkpoint contents')
        return value
    packed=gzip.compress(encoded(value),mtime=0)
    if path.exists():
        if checkpoint(path)!=value:raise ValueError('Fresh fitted arm differs')
        return value
    if seal.exists():raise ValueError('Orphan checkpoint seal')
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:stream.write(packed)
    write_equal(seal,dict(sha256=filehash(path),content_sha256=digest(value)))
    return value


def run_comparison(output,rows,arrays,parts,y,*,verifying=False,arms=201):
    """arms is internal; public execute always supplies the full fixed 201."""
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    binding=dict(rows_sha256=digest(rows),parts_sha256=digest(parts),targets_sha256=digest(np.asarray(y).tolist()),
                 arrays={k:hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest() for k,a in sorted(arrays.items())},
                 core_config=core.CONFIG,arms=arms)
    write_equal(output/'BINDING.json',binding)
    prepared={r:core.prepare(rows,arrays,parts[r]) for r in sorted(parts)}
    effects=[];primary=None;hashes={}
    for arm in range(arms):
        path=output/'arms'/f'{arm:04d}.json.gz'
        if path.exists() and not verifying:
            record=checkpoint(path)
            if record['binding']!=digest(binding) or record['arm']!=arm:raise ValueError('Retained arm identity differs')
        else:
            labels=y if arm==0 else core.permute_targets(rows,y,work.SEED+arm-1)
            history=core.prefix_counts(rows,labels);predictions=[];fits={}
            for recipient in sorted(parts):
                predicted,fit=core.fit_recipient(rows,labels,prepared[recipient],history)
                predictions.extend(predicted);fits[recipient]=slim(fit)
            record=dict(binding=digest(binding),arm=arm,predictions=predictions,fits=fits)
            if verifying and not path.exists():raise ValueError('Incomplete original arm bank')
            checkpoint(path,record)
        if arm==0:primary=record['predictions']
        else:
            if [r['key'] for r in record['predictions']]!=[r['key'] for r in primary]:raise ValueError('Reference scoring support differs')
            effects.append(work.effect(record['predictions']))
        hashes[str(arm)]=filehash(path)
        if arm%10==0 or arm==arms-1:progress(output/'PROGRESS.json',dict(phase='verify' if verifying else 'execute',complete_arms=arm+1,total_arms=arms))
    report=work.summarize(primary,effects) if arms==201 else dict(engineering_only=True,complete_arms=arms)
    report.update(arm_hashes=hashes,reference_values=effects,binding_sha256=filehash(output/'BINDING.json'))
    write_equal(output/'SUMMARY.json',report)
    return report


def calibration_gate(results):
    if len(results)!=30 or [r['world'] for r in results]!=list(range(30)):
        raise ValueError('Incomplete calibration matrix')
    counts={};intervals={}
    for kind,start in (('common',0),('page_only',10),('complementary',20)):
        group=results[start:start+10]
        if any(r['kind']!=kind for r in group):raise ValueError('Wrong calibration world type')
        field='useful_licensed_detection' if kind=='complementary' else 'licensed_positive'
        n=sum(r['result'][field] for r in group);counts[kind]=n
        ci=binomtest(n,10).proportion_ci(confidence_level=.95,method='exact')
        intervals[kind]=[float(ci.low),float(ci.high)]
    return dict(passes=counts['common']<=2 and counts['page_only']<=2 and counts['complementary']>=8,
                counts=counts,denominator_per_kind=10,binomial_interval95=intervals,
                scope='finite constructed validation of this law and sample, not universal error control')


def admission(inputs,config):
    if config not in (CONFIG|dict(mode='calibration'),CONFIG|dict(mode='human')):raise ValueError('Frozen full configuration required')
    expected={'cost_landing'} if config['mode']=='calibration' else {'cost_landing','calibration_landing',
              'source_complete','source_landing','d15_complete','d15_landing'}
    if set(inputs)!=expected:raise ValueError('Exact full-run admission inputs required')
    cost=read(inputs['cost_landing']);root=Path(cost['completion']).parent
    if not cost.get('full_write_through') or filehash(root/'COMPLETE.json')!=cost['completion_sha256']:
        raise ValueError('Unlanded cost result')
    if filehash(root/'output/FORECAST.json')!=cost['forecast_sha256'] or read(root/'output/FORECAST.json')!=cost['forecast']:
        raise ValueError('Changed measured forecast')
    if config['mode']=='human':
        landed=read(inputs['calibration_landing']);calroot=Path(landed['completion']).parent
        if not landed.get('full_write_through') or filehash(calroot/'COMPLETE.json')!=landed['completion_sha256']:
            raise ValueError('Unlanded calibration')
        summary=read(calroot/'output/SUMMARY.json')
        if filehash(calroot/'output/SUMMARY.json')!=landed['summary_sha256'] or summary['config']!=CONFIG|dict(mode='calibration'):
            raise ValueError('Changed calibration result')
        if not summary['calibration']['passes']:raise ValueError('Failed full calibration gate')
        source_keys={'source_complete','source_landing','d15_complete','d15_landing'}
        original=read(root/'output/BINDING.json')['inputs']
        if {k:filehash(inputs[k]) for k in source_keys}!={k:original[k] for k in source_keys}:
            raise ValueError('Cost/human sources differ')
    return cost


def one_pass(output,inputs,config,verifying=False):
    admission(inputs,config);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    binding=dict(inputs={k:filehash(v) for k,v in inputs.items()},config=config)
    write_equal(output/'BINDING.json',binding)
    if config['mode']=='calibration':
        results=[]
        for number in range(30):
            rows,arrays,parts,y,meta=work.world(number)
            progress(output/'PROGRESS.json',dict(phase='verify-world' if verifying else 'world',completed_worlds=number,total_worlds=30))
            result=run_comparison(output/'worlds'/f'{number:02d}',rows,arrays,parts,y,verifying=verifying)
            results.append(dict(world=number,kind=meta['kind'],result={k:v for k,v in result.items() if k not in ('arm_hashes','reference_values')},summary_sha256=filehash(output/'worlds'/f'{number:02d}'/'SUMMARY.json')))
        summary=dict(config=config,constructed=True,results=results,calibration=calibration_gate(results),scientific_admission=False)
    else:
        data=work.source({k:v for k,v in inputs.items() if k not in ('cost_landing','calibration_landing')})
        rows,arrays,parts,y,excluded=data
        result=run_comparison(output/'human',rows,arrays,parts,y,verifying=verifying)
        summary=dict(config=config,constructed=False,result=result,excluded_recipients=len(excluded),all_prepared_rows=len(rows),
                     descriptive=True,scientific_admission=False,uncertainty='writer-cluster bootstrap conditional on fitted forecasts; historical exposed corpus')
    write_equal(output/'SUMMARY.json',summary)
    return dict(verified=True,full_fitted_reference_replay=True) if verifying else dict(status='complete',mode=config['mode'])


def execute(output,inputs,config):
    with threadpool_limits(limits=2):return one_pass(output,inputs,config)


def verify(output,inputs,config):
    with threadpool_limits(limits=2):return one_pass(output,inputs,config,True)
