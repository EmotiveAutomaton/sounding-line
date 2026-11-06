"""Outcome-free D7 fixed-cohort reference support audit.

DESIGN CHECK: LESSONS 2-5 reread 2026-11-04. NULL and ALTERNATIVE use
identical observed-duration support and full chronological partitions. Audit
all200 frozen whole-session assignments before fitting; every invalid draw
remains. No coefficients, loss, prediction, bootstrap or p-value is computed.
"""
from pathlib import Path
from collections import Counter
from runners.stage14.common import read,filehash
from . import week4_d7_calibration as calibration
from . import week3_d7_cost as cost
from .timing_p6 import write_equal


def configuration(mode):
    if mode not in ('constructed','full'):raise ValueError('Unknown mode')
    return dict(card='D7-reference-support',mode=mode,seed=20261026,assignments=200)


def calculate(output,inputs,config,saving):
    if config!=configuration(config.get('mode')):raise ValueError('Frozen support contract required')
    if config['mode']=='constructed':
        if inputs:raise ValueError('No human data in fixture')
        rows,_=calibration.world('null',20261026,6)
    else:rows=cost.source(inputs)
    groups,excluded=calibration.support(rows)
    if config['mode']=='full' and len(groups)!=38:raise ValueError('Original supported population differs')
    # The diagnostic population is the primary's complete supported writers.
    # Unsupported original writers remain in the census, never enter fits.
    cohort=[r for w in sorted(groups) for r in groups[w]]
    audit=calibration.audit_bank(cohort,config['assignments'],config['seed'])
    path=Path(output)/'PRIVATE_REFERENCE_SUPPORT.json'
    value=dict(original_exclusions=excluded,reference=audit,
               original_rows=len(rows),analysis_rows=len(cohort))
    if saving:write_equal(path,value)
    elif read(path)!=value:raise ValueError('Complete support replay differs')
    return dict(card=config['card'],mode=config['mode'],original_writers=len(groups)+len(excluded),
        original_rows=len(rows),analysis_rows=len(cohort),supported_writers=len(groups),
        excluded_writers=len(excluded),exclusion_reasons=dict(sorted(Counter(excluded.values()).items())),
        attempted=config['assignments'],invalid=sum(not r['same_supported_writers'] for r in audit['draws']),
        support_invariant=audit['valid'],no_fits=True,scientific_admission=False,
        private_support_sha256=filehash(path),input_hashes={k:filehash(v) for k,v in inputs.items()})


def execute(output,inputs,config):
    Path(output).mkdir(parents=True,exist_ok=True)
    result=calculate(output,inputs,config,True);write_equal(Path(output)/'SUMMARY.json',result);return result


def verify(output,inputs,config):
    result=calculate(output,inputs,config,False)
    if read(Path(output)/'SUMMARY.json')!=result:raise ValueError('Support summary differs')
    return dict(verified=True,full_fresh_support_replay=True,no_fits=True)
