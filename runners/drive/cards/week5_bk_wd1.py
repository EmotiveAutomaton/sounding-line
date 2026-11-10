"""Checkpointed WD1 corrected calibration, using the validated slower solver.

Only execution partitioning changes. Every original world, conditional
assignment, fit and summary is retained; no failed parity optimization is used.
"""
from pathlib import Path
import time
import numpy as np
from threadpoolctl import threadpool_limits
from . import week4_wd1_calibration_h2 as original
from . import week4_wd1_conditioned_support as support
from . import week3_sdt_newton as solver
from .week5_at_source import authenticate
from .week5_at_scoring import digest
from .timing_census import read, filehash
from .timing_p6 import gzread, gzip_equal, write_equal, progress


def roster():
    return [(family,ordinal,20261104+i*1000+ordinal) for i,family in enumerate(original.FAMILIES)
            for ordinal in range(10 if i<2 else 5)]


def make_world(family,ordinal,config=None):
    if (family,ordinal) not in {(f,o) for f,o,_ in roster()}:raise ValueError('Unknown frozen calibration world')
    seed=next(s for f,o,s in roster() if (f,o)==(family,ordinal));cfg=config or original.configuration('full')
    sessions,rows,scalar,embedding,truth=original.world(family,seed,cfg['writers'],cfg['decisions'])
    bank=support.bank(sessions,cfg['permutation_draws'],cfg['maximum_proposals'],seed)
    if not bank['complete']:raise ValueError('Complete conditional assignment bank unavailable')
    return dict(family=family,ordinal=ordinal,seed=seed,config=cfg,sessions=sessions,rows=rows,
                scalar=scalar.tolist(),embedding=embedding.tolist(),bank=bank,
                truth_sha256=digest(truth),solver_sha256=filehash(solver.__file__),
                original_calibration_sha256=filehash(original.__file__))


def fit_one(bundle,index):
    bank=bundle['bank'];count=1+len(bank['accepted'])
    if not 0<=index<count:raise ValueError('Assignment index outside complete bank')
    if filehash(solver.__file__)!=bundle['solver_sha256'] or filehash(original.__file__)!=bundle['original_calibration_sha256']:
        raise ValueError('Frozen validated solver changed')
    assignment={} if index==0 else bank['accepted'][index-1]['assignment']
    return solver.evaluate(bundle['sessions'],bundle['rows'],np.asarray(bundle['scalar']),np.asarray(bundle['embedding']),assignment,
                           dict(seed=bundle['seed'],pca_dimensions=bundle['config']['pca_dimensions']))


def world_result(bundle,blocks):
    binding=digest(bundle);records={}
    for block in blocks:
        if block['binding']!=binding:raise ValueError('Different world binding')
        for row in block['records']:
            index=row['index']
            if index in records:raise ValueError('Duplicated assignment index')
            records[index]=row
    required=1+bundle['config']['permutation_draws']
    if set(records)!=set(range(required)):raise ValueError('Missing complete reference fits')
    failed=[i for i,r in records.items() if r['status']!='complete']
    if failed:
        primary=dict(state='invalid',reason='Numerical reference fit failed',failed_assignments=failed)
    else:
        values=[records[i]['value'] for i in range(required)]
        primary=original.summarize(values[0],values[1:],bundle['config']['bootstrap_draws'],bundle['seed'])
    return dict(family=bundle['family'],ordinal=bundle['ordinal'],seed=bundle['seed'],primary=primary,
                config=bundle['config'],complete_assignment_fits=required,world_binding=binding,
                bank_sha256=digest(bundle['bank']),truth_sha256=bundle['truth_sha256'],
                fit_digests=[digest(records[i]) for i in range(required)],
                scientific_admission=False)


def campaign_result(results):
    if sorted((r['family'],r['ordinal'],r['seed']) for r in results)!=sorted(roster()):
        raise ValueError('All exact thirty worlds required')
    if any(r['config']!=original.configuration('full') or r['complete_assignment_fits']!=1001 for r in results):
        raise ValueError('Full original uncertainty and reference count required')
    results=sorted(results,key=lambda r:(original.FAMILIES.index(r['family']),r['ordinal']))
    return dict(card='BK-WD1-calibration',calibration=original.gate(results),worlds=30,results=results,
                original_solver=True,scientific_admission=False)


def run(output,inputs,config,verifying=False):
    root=Path(output);root.mkdir(parents=True,exist_ok=True);operation=config['operation'];began=time.process_time()
    if operation=='world_source':
        if inputs or set(config)!={'operation','family','ordinal'}:raise ValueError('Exact generated-world configuration required')
        bundle=make_world(config['family'],int(config['ordinal']))
        if verifying:
            if gzread(root/'WORLD.json.gz')!=bundle:raise ValueError('Full world and bank replay differs')
            return dict(verified=True,complete_generated_world_replay=True)
        gzip_equal(root/'WORLD.json.gz',bundle);write_equal(root/'SUMMARY.json',dict(family=bundle['family'],seed=bundle['seed'],assignments=1001,scientific_admission=False))
        return dict(status='complete')
    if operation=='campaign_reduce':
        if set(inputs)!={'worlds'} or set(config)!={'operation'}:raise ValueError('Exact complete world bank required')
        result=campaign_result([read(authenticate(p)/'output/RESULT.json') for p in read(inputs['worlds'])])
        if verifying:
            if read(root/'RESULT.json')!=result:raise ValueError('Full campaign reduction differs')
            return dict(verified=True,complete_calibration_reduction=True)
        write_equal(root/'RESULT.json',result);return dict(status='complete',calibration_passes=result['calibration']['passes'])
    source=authenticate(inputs['source_root'])/'output';bundle=gzread(source/'WORLD.json.gz')
    if bundle['config']!=original.configuration('full'):raise ValueError('Complete original design required')
    if operation=='world_reduce':
        if set(inputs)!={'source_root','blocks'} or set(config)!={'operation'}:raise ValueError('Exact complete block bank required')
        blocks=[read(authenticate(p)/'output/BLOCK.json') for p in read(inputs['blocks'])]
        result=world_result(bundle,blocks)
        if verifying:
            if read(root/'RESULT.json')!=result:raise ValueError('Complete world reduction differs')
            return dict(verified=True,all_1000_references_and_2000_writer_draws_replayed=True)
        write_equal(root/'RESULT.json',result);return dict(status='complete',scientific_admission=False)
    if operation!='block' or set(inputs)!={'source_root'} or set(config)!={'operation','start','count'}:
        raise ValueError('Exact fit block contract required')
    start=int(config['start']);count=int(config['count'])
    if not 0<=start<1001 or not 1<=count<=100 or start+count>1001:raise ValueError('Invalid global assignment range')
    binding=digest(bundle);records=[]
    with threadpool_limits(limits=2):
        for index in range(start,start+count):
            path=root/f'fit-{index:04d}.json'
            if path.exists() and not verifying:
                record=read(path)
                if read(path.with_suffix('.receipt.json'))['sha256']!=filehash(path):raise ValueError('Changed fit checkpoint')
            else:
                try:record=dict(index=index,status='complete',value=fit_one(bundle,index),binding=binding)
                except (ValueError,ArithmeticError) as error:record=dict(index=index,status='invalid',reason=str(error),binding=binding)
                if verifying:
                    if read(path)!=record:raise ValueError('Independent full reference fit differs')
                else:
                    write_equal(path,record);write_equal(path.with_suffix('.receipt.json'),dict(sha256=filehash(path)))
            if record['binding']!=binding or record['index']!=index:raise ValueError('Wrong fit checkpoint identity')
            records.append(record);progress(root/'PROGRESS.json',dict(phase='verify' if verifying else 'fit',index=index,total=1001))
            if (root/'YIELD_REQUEST.json').exists() and index+1<start+count:
                return dict(status='yielded',reason='certified original-solver fit boundary',completed=len(records))
    block=dict(binding=binding,start=start,count=count,records=records)
    if verifying:
        if read(root/'BLOCK.json')!=block:raise ValueError('Full block reduction differs')
        return dict(verified=True,complete_original_solver_refit=True)
    write_equal(root/'BLOCK.json',block);write_equal(root/'COST.json',dict(process_cpu_seconds=time.process_time()-began,complete_fits=count,includes_native_verify=False))
    return dict(status='complete',invalid=sum(r['status']!='complete' for r in records))


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
