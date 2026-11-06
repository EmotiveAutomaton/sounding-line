"""D7.h1 support-conditioned diagnostic, retaining the invalid original.

DESIGN CHECK: LESSONS3-5 and CONTROLS1-7 reread 2026-11-04.
NULL/ALTERNATIVE share the same outcome-blind conditioning rule. Exactly200
accepted assignments or no fit; all rejected proposals remain. Constructed
complete-bank parity is not itself scientific calibration. No fitting here.
"""
from collections import Counter
from pathlib import Path
from runners.stage14.common import read, filehash, digest, atomic
from . import week4_d7_calibration as c
from . import week3_d7_cost as cost
from .timing_p6 import write_equal

FIELDS=('key','writer','session','prompt','session_start','session_end','open_at','dwell_observed')


def metadata(rows):
    return [{k:r[k] for k in FIELDS} for r in rows]


def bank(rows,draws=200,maximum=2000,seed=20261026,progress=lambda *args:None):
    if draws<1 or maximum<1:raise ValueError('Positive bank bounds required')
    rows=metadata(rows);groups,excluded=c.support(rows);roster=sorted(groups)
    if excluded or not roster:raise ValueError('Complete supported cohort required')
    proposals=[];accepted=[]
    for index in range(maximum):
        assignment=c.session_assignment(rows,index,seed)
        other,bad=c.support(c.reassigned(rows,assignment));valid=sorted(other)==roster
        proposals.append(dict(proposal=index,assignment_sha256=digest(assignment),
            accepted=valid,exclusions=bad,supported_writers=len(other)))
        if valid:accepted.append(dict(draw=len(accepted),proposal=index,assignment=assignment))
        progress(len(proposals),len(accepted))
        if len(accepted)==draws:break
    return dict(law='uniform-session-labels-within-prompt-conditional-on-original-support-h1',
        metadata_sha256=digest(rows),writers=roster,draws=draws,maximum_proposals=maximum,
        seed=seed,proposals=proposals,accepted=accepted,complete=len(accepted)==draws)


def calibration_parity(progress=lambda *args:None):
    checks=[]
    for regime in ('null','nuisance','signed'):
        for ordinal in range(10):
            seed=20261026+ordinal;rows,_=c.world(regime,seed,12,ordinal)
            result=bank(rows,seed=seed)
            same=(result['complete'] and len(result['proposals'])==200 and
                  [a['proposal'] for a in result['accepted']]==list(range(200)))
            checks.append(dict(regime=regime,seed=seed,identical_original_bank=same,
                metadata_sha256=result['metadata_sha256'],bank_sha256=digest(result)))
            progress(len(checks),30)
    return dict(worlds=checks,complete=len(checks)==30,identical=all(r['identical_original_bank'] for r in checks))


def configuration(mode):
    if mode not in ('constructed','full'):raise ValueError('Unknown mode')
    return dict(card='D7.h1-reference-support',mode=mode,seed=20261026,
        assignments=12 if mode=='constructed' else 200,maximum_proposals=2000)


def calculate(output,inputs,config,saving):
    if config!=configuration(config.get('mode')):raise ValueError('Frozen conditional-support contract required')
    output=Path(output)
    if config['mode']=='constructed':
        if inputs:raise ValueError('No human data in fixture')
        rows,_=c.world('null',config['seed'],6)
    else:rows=cost.source(inputs)
    groups,excluded=c.support(rows)
    if config['mode']=='full' and len(groups)!=38:raise ValueError('Original supported population differs')
    cohort=[r for w in sorted(groups) for r in groups[w]]
    def progress(phase,done,total):
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():
            raise InterruptedError('D7.h1 metadata boundary yield')
        atomic(output/'PROGRESS.json',dict(phase=phase,done=done,total=total))
    result=bank(cohort,config['assignments'],config['maximum_proposals'],config['seed'],
                lambda attempted,accepted:progress('conditional-bank',attempted,config['maximum_proposals']))
    parity=calibration_parity(lambda done,total:progress('calibration-bank-parity',done,total)) if config['mode']=='full' else None
    private=dict(original_exclusions=excluded,bank=result,calibration_parity=parity)
    path=output/'PRIVATE_CONDITIONAL_SUPPORT.json'
    if saving:write_equal(path,private)
    elif read(path)!=private:raise ValueError('Complete conditional-support replay differs')
    summary=dict(card=config['card'],mode=config['mode'],source_rows=len(rows),analysis_rows=len(cohort),
        original_writers=len(groups)+len(excluded),supported_writers=len(groups),
        exclusion_reasons=dict(sorted(Counter(excluded.values()).items())),
        proposed=len(result['proposals']),accepted=len(result['accepted']),
        rejected=sum(not r['accepted'] for r in result['proposals']),bank_complete=result['complete'],
        calibration_bank_parity=None if parity is None else parity['identical'],
        calibration_worlds=0 if parity is None else len(parity['worlds']),no_fits=True,
        scientific_admission=False,private_support_sha256=filehash(path),
        input_hashes={k:filehash(v) for k,v in inputs.items()})
    return summary


def execute(output,inputs,config):
    Path(output).mkdir(parents=True,exist_ok=True)
    result=calculate(output,inputs,config,True);write_equal(Path(output)/'SUMMARY.json',result);return result


def verify(output,inputs,config):
    result=calculate(output,inputs,config,False)
    if read(Path(output)/'SUMMARY.json')!=result:raise ValueError('Conditional support summary differs')
    return dict(verified=True,full_fresh_support_replay=True,no_fits=True)
