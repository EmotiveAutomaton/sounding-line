"""Gated corrected WD1 consumer with exact verified-profile reuse.

This implements the reuse explicitly permitted by WD1_SUPPORT_H2. All original
invalid evidence remains. No corrected inference precedes full calibration.
"""
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from . import week4_wd1_conditioned_support as support
from . import week4_wd1_calibration_h2 as calibration
from . import week3_sdt_newton as solver
from .week5_at_source import authenticate
from .week5_at_scoring import digest
from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal,progress


def source(inputs):
    if set(inputs)!={'original_completion','support_root','calibration_root'}:raise ValueError('Exact admitted WD1 source bundle required')
    cal=authenticate(inputs['calibration_root']);cp=read(cal/'PLAN.json');gate=read(cal/'output/RESULT.json')
    if cp['module']!='runners.drive.cards.week5_bk_wd1' or cp['config']!={'operation':'campaign_reduce'}:
        raise ValueError('Exact complete corrected calibration required')
    if gate['worlds']!=30 or not gate['calibration']['complete'] or not gate['calibration']['passes']:
        raise ValueError('Full corrected calibration did not pass')
    original,plan,done=support.authenticate(inputs['original_completion'])
    sr=authenticate(inputs['support_root']);sp=read(sr/'PLAN.json')
    if sp['module']!='runners.drive.cards.week4_wd1_conditioned_support' or sp['config']!=support.configuration('full'):
        raise ValueError('Exact complete conditional support source required')
    if Path(sp['inputs']['original_completion']).resolve()!=Path(inputs['original_completion']).resolve():
        raise ValueError('Support source references a different original')
    retained=read(sr/'output/PRIVATE_SUPPORT.json');bank=retained['bank']
    raw=read(plan['inputs']['sessions']);vectors=np.load(plan['inputs']['vectors'],mmap_mode='r',allow_pickle=False)
    sessions,rows,scalar,embedding=solver.population_features(raw,read(plan['inputs']['records']),vectors)
    replay=support.bank(sessions,1000,2000,20261026)
    if bank!=replay or not bank['complete']:raise ValueError('Complete support-conditioned bank changed')
    real=read(original/'output/REAL.json')
    if sorted(real['profiles'])!=bank['writers']:raise ValueError('Original supported roster differs')
    reused={};missing=[];audit={a['proposal']:a for a in retained['original_audit']}
    for number,item in enumerate(bank['accepted']):
        proposal=item['proposal']
        if solver.permute_sessions(sessions,20261026+proposal)!=item['assignment']:raise ValueError('Accepted assignment identity differs')
        if proposal<1000:
            path=original/'output/permutations'/f'{proposal:04d}.json'
            if filehash(path)!=audit[proposal]['original_profile_sha256']:raise ValueError('Reused profile seal differs')
            value=read(path)
            if sorted(value['profiles'])!=bank['writers']:raise ValueError('Reused profile has wrong support')
            reused[str(number)]=dict(value=value,proposal=proposal,original_sha256=filehash(path),assignment_sha256=digest(item['assignment']))
        else:missing.append(number)
    return dict(sessions=sessions,rows=rows,scalar=scalar.tolist(),embedding=embedding.tolist(),bank=bank,
                real=real,reused=reused,missing=missing,config=plan['config'],
                proof=dict(original_complete=filehash(inputs['original_completion']),support_complete=filehash(sr/'COMPLETE.json'),
                           calibration_complete=filehash(cal/'COMPLETE.json'),solver_sha256=filehash(solver.__file__)))


def reduce_values(bundle,blocks):
    binding=digest(bundle);values={int(k):v['value'] for k,v in bundle['reused'].items()};failed=[]
    seen=set()
    for block in blocks:
        if block['binding']!=binding:raise ValueError('Different corrected WD1 source')
        for r in block['records']:
            i=r['index']
            if i in seen or i in values:raise ValueError('Duplicate or overwritten reference')
            if i not in bundle['missing']:raise ValueError('Uncommissioned replacement of verified profile')
            seen.add(i)
            if r['status']=='complete':values[i]=r['value']
            else:failed.append(i)
    if seen!=set(bundle['missing']) or set(values)|set(failed)!=set(range(1000)):
        raise ValueError('Missing corrected reference profile')
    if failed:return dict(state='invalid',reason='Missing numerical certificate in new assignments',failed_assignments=failed)
    if any(sorted(v['profiles'])!=bundle['bank']['writers'] for v in values.values()):
        raise ValueError('Corrected profile support differs')
    return calibration.summarize(bundle['real'],[values[i] for i in range(1000)],2000,20261026)


def run(output,inputs,config,verifying=False):
    root=Path(output);root.mkdir(parents=True,exist_ok=True);operation=config['operation']
    if operation=='source':
        if set(config)!={'operation'}:raise ValueError('Unchanged corrected source configuration required')
        bundle=source(inputs)
        if verifying:
            if gzread(root/'BUNDLE.json.gz')!=bundle:raise ValueError('Complete corrected source replay differs')
            return dict(verified=True,exact_original_profile_reuse=True,complete_source_replay=True)
        gzip_equal(root/'BUNDLE.json.gz',bundle);write_equal(root/'SUMMARY.json',dict(reused=len(bundle['reused']),missing_refits=len(bundle['missing']),scientific_admission=False))
        return dict(status='complete')
    source_root=authenticate(inputs['source_root'])/'output';bundle=gzread(source_root/'BUNDLE.json.gz');binding=digest(bundle)
    if filehash(solver.__file__)!=bundle['proof']['solver_sha256']:raise ValueError('Original solver changed')
    if operation=='reduce':
        if set(inputs)!={'source_root','blocks'} or set(config)!={'operation'}:raise ValueError('Exact corrected reference collection required')
        blocks=[read(authenticate(p)/'output/BLOCK.json') for p in read(inputs['blocks'])]
        primary=reduce_values(bundle,blocks)
        result=dict(card='BK-WD1-corrected',primary=primary,reused_verified_profiles=len(bundle['reused']),
                    freshly_refitted_profiles=len(bundle['missing']),scope=solver.SCOPE,
                    reference='original exact support-conditioned within-prompt assignment law',
                    calibration_passed=True,descriptive=True,supersedes_no_original_bytes=True)
        if verifying:
            if read(root/'RESULT.json')!=result:raise ValueError('Full corrected uncertainty replay differs')
            return dict(verified=True,complete_corrected_reference_reduction=True)
        write_equal(root/'RESULT.json',result);return dict(status='complete')
    if operation!='block' or set(inputs)!={'source_root'} or set(config)!={'operation','start','count'}:
        raise ValueError('Exact new-assignment block required')
    start=int(config['start']);count=int(config['count']);missing=bundle['missing']
    if not 0<=start<len(missing) or not 1<=count<=50 or start+count>len(missing):raise ValueError('Invalid missing-assignment range')
    records=[]
    with threadpool_limits(limits=2):
        for index in missing[start:start+count]:
            path=root/f'fit-{index:04d}.json'
            if path.exists() and not verifying:
                record=read(path)
                if read(path.with_suffix('.receipt.json'))['sha256']!=filehash(path):raise ValueError('Changed checkpoint')
            else:
                try:
                    value=solver.evaluate(bundle['sessions'],bundle['rows'],np.asarray(bundle['scalar']),np.asarray(bundle['embedding']),bundle['bank']['accepted'][index]['assignment'],bundle['config'])
                    record=dict(index=index,status='complete',value=value,binding=binding)
                except (ValueError,ArithmeticError) as error:record=dict(index=index,status='invalid',reason=str(error),binding=binding)
                if verifying:
                    if read(path)!=record:raise ValueError('Fresh new-assignment refit differs')
                else:
                    write_equal(path,record);write_equal(path.with_suffix('.receipt.json'),dict(sha256=filehash(path)))
            if record['binding']!=binding or record['index']!=index:raise ValueError('Wrong corrected checkpoint identity')
            records.append(record);progress(root/'PROGRESS.json',dict(phase='verify' if verifying else 'fit',missing_completed=len(records),missing_total=len(missing)))
            if (root/'YIELD_REQUEST.json').exists() and len(records)<count:return dict(status='yielded',reason='complete corrected fit boundary')
    block=dict(binding=binding,start=start,count=count,records=records)
    if verifying:
        if read(root/'BLOCK.json')!=block:raise ValueError('Block reduction differs')
        return dict(verified=True,full_new_assignment_refits=True)
    write_equal(root/'BLOCK.json',block);return dict(status='complete')

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
