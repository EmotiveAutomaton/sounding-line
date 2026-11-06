"""WD1.h2 outcome-blind support-conditioned reference, original retained.

DESIGN CHECK: LESSONS3-5 and CONTROLS1-7 reread 2026-11-04.
NULL and ALTERNATIVE use the identical support condition; it cannot read
responses, fitted slopes or correlations. Complete1000 accepted assignments
within2000 proposals or no inference. Finite-law checks validate allocation,
not human exchangeability or sensitivity. Complete calibration remains required.
"""
from pathlib import Path
from collections import Counter
from runners.stage14.common import read, filehash, digest, atomic
from . import week3_sdt_newton as original
from .timing_pmap_stats import split_sessions
from .timing_p6 import write_equal

FIELDS=('writer','session','prompt','timestamp')


def metadata(sessions):
    out=[]
    for s in sorted(sessions,key=lambda s:s['session']):
        count=len(s['rows']) if 'rows' in s else s['decisions']
        if not isinstance(count,int) or count<0:raise ValueError('Invalid decision count')
        out.append(dict({k:s[k] for k in FIELDS},decisions=count))
    if len({s['session'] for s in out})!=len(out):raise ValueError('Duplicate session')
    return out


def support(sessions,assignment=None):
    halves,excluded=split_sessions(metadata(sessions),assignment)
    roster=[]
    for w,parts in sorted(halves.items()):
        counts=[sum(s['decisions'] for s in part) for part in parts]
        if min(counts)<4:excluded[w]=dict(reason='fewer than four decisions in a prompt half',half_decisions=counts)
        else:roster.append(w)
    return roster,excluded


def bank(sessions,draws=1000,maximum=2000,seed=20261026,progress=lambda *a:None):
    if draws<1 or maximum<1:raise ValueError('Positive bank bounds required')
    sessions=metadata(sessions);roster,excluded=support(sessions)
    if len(roster)<2:raise ValueError('No supported comparison')
    accepted=[];proposals=[]
    for index in range(maximum):
        assignment=original.permute_sessions(sessions,seed+index)
        other,bad=support(sessions,assignment);valid=other==roster
        proposals.append(dict(proposal=index,assignment_sha256=digest(assignment),
            accepted=valid,excluded=bad,supported_writers=len(other)))
        if valid:accepted.append(dict(draw=len(accepted),proposal=index,assignment=assignment))
        progress(index+1,len(accepted))
        if len(accepted)==draws:break
    return dict(law='uniform-within-prompt-session-labels-conditional-on-exact-original-support-h2',
        seed=seed,draws=draws,maximum_proposals=maximum,metadata_sha256=digest(sessions),
        writers=roster,original_excluded=excluded,proposals=proposals,accepted=accepted,
        complete=len(accepted)==draws)


def fixture():
    # Both supported originally; within-prompt shuffles can collect the empty
    # sessions into one recipient and fail its decision floor.
    return [dict(writer=str(w),session=f'{w}:{p}:{i}',prompt=str(p),
        timestamp=100*p+10*i+w,decisions=4 if i==0 else 0)
        for w in range(2) for p in range(2) for i in range(2)]


def authenticate(completion):
    root=Path(completion).parent;c=read(completion);p=read(root/'PLAN.json')
    if c.get('status')!='COMPLETE' or not c.get('fresh_process_verified'):
        raise ValueError('Complete independently verified original required')
    if p['module']!='runners.drive.cards.week3_sdt_newton':raise ValueError('Wrong original')
    if p['config']!=dict(bootstrap_draws=2000,mode='full',pca_dimensions=16,permutation_draws=1000,seed=20261026):
        raise ValueError('Original configuration changed')
    for n,h in p['pins'].items():
        if filehash(n)!=h:raise ValueError('Original pin changed')
    for n,h in c['outputs'].items():
        if filehash(root/n)!=h:raise ValueError('Original output changed')
    if not read(root/'VERIFIED.json')['fresh_population_and_permutation_refit']:
        raise ValueError('Original full refit not verified')
    return root,p,c


def configuration(mode):
    if mode not in ('constructed','full'):raise ValueError('Unknown mode')
    return dict(card='WD1.h2-support',mode=mode,seed=20261026,
        draws=12 if mode=='constructed' else 1000,maximum_proposals=2000)


def calculate(output,inputs,config,saving):
    if config!=configuration(config.get('mode')):raise ValueError('Frozen configuration required')
    output=Path(output)
    if config['mode']=='constructed':
        if inputs:raise ValueError('No human inputs in fixture')
        sessions=fixture();root=None
    else:
        if set(inputs)!={'original_completion'}:raise ValueError('Exact original required')
        root,p,c=authenticate(inputs['original_completion'])
        sessions=metadata(read(p['inputs']['sessions']))
    def progress(done,accepted):
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():
            raise InterruptedError('WD1.h2 metadata boundary yield')
        atomic(output/'PROGRESS.json',dict(phase='conditional-support',proposals=done,accepted=accepted))
    result=bank(sessions,config['draws'],config['maximum_proposals'],config['seed'],progress)
    original_audit=[]
    if root is not None:
        if result['writers']!=sorted(read(root/'output/REAL.json')['profiles']):
            raise ValueError('Real support reconstruction differs')
        for index in range(1000):
            assignment=original.permute_sessions(sessions,config['seed']+index)
            roster,_=support(sessions,assignment)
            saved=read(root/'output/permutations'/f'{index:04}.json')
            if roster!=sorted(saved['profiles']):raise ValueError('Original reference support differs')
            original_audit.append(dict(proposal=index,original_profile_sha256=filehash(root/'output/permutations'/f'{index:04}.json'),
                supported_writers=len(roster),original_roster_matches=roster==result['writers']))
        if len(result['writers'])!=45 or len({s['writer'] for s in sessions})!=61:
            raise ValueError('Original population changed')
    private=dict(bank=result,original_audit=original_audit)
    path=output/'PRIVATE_SUPPORT.json'
    if saving:write_equal(path,private)
    elif read(path)!=private:raise ValueError('Full support replay differs')
    return dict(card=config['card'],mode=config['mode'],no_fits=True,scientific_admission=False,
        sessions=len(sessions),writers=len({s['writer'] for s in sessions}),supported_writers=len(result['writers']),
        accepted=len(result['accepted']),proposed=len(result['proposals']),
        rejected=sum(not p['accepted'] for p in result['proposals']),bank_complete=result['complete'],
        original_assignments_audited=len(original_audit),
        original_roster_failures=sum(not a['original_roster_matches'] for a in original_audit),
        original_reusable_assignments=sum(a['proposal']<1000 for a in result['accepted']) if root else 0,
        new_assignments_requiring_fit=sum(a['proposal']>=1000 for a in result['accepted']) if root else 0,
        private_sha256=filehash(path),input_hashes={k:filehash(v) for k,v in inputs.items()})


def execute(output,inputs,config):
    Path(output).mkdir(parents=True,exist_ok=True)
    result=calculate(output,inputs,config,True);write_equal(Path(output)/'SUMMARY.json',result);return result


def verify(output,inputs,config):
    result=calculate(output,inputs,config,False)
    if result!=read(Path(output)/'SUMMARY.json'):raise ValueError('Summary differs')
    return dict(verified=True,full_metadata_replay=True,no_fits=True)
