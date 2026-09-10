"""Explicit finite-support repair for development-only maker-series allocation.

DESIGN CHECK: I01/C05/M01/B01/X01/X08/X11; LESSONS3--5, CONTROLS6--7.
NULL: assigning any unit to an empty parameter set, hiding an available cohort,
changing marginals or substituting a source split refuses. ALTERNATIVE: the
declared allocation retains every feasible joint cohort and the original domain,
purpose, law-variant and residue marginals. Eight development joint cohorts remain
unavailable and are reported explicitly; they are not imputed or moved to another
partition. Discovery, reserve, training, reader criteria and effect scales stay
separate. Complete valid allocation or explicit refusal; no scientific score.
"""
from itertools import product
from .common import digest,read
from .recipes import W,POP,parameter_partition
from .series_cases import COHORTS

RULE='development-finite-support-fixed-marginals-v1'


def support_inventory():
    rows=[]
    for domain,law,residue,purpose in COHORTS:
        partitions={k:0 for k in ('training','development','discovery','reserve')}
        for belief,tendency,shape in product(W.BELIEFS,W.TENDENCIES[:2],POP.SHAPES):
            world={'state':{'names':{'law':law,'belief':belief,'residue':residue,'tendency':tendency}},
                'goal_name':purpose,'shape':shape}
            partitions[parameter_partition(world)]+=1
        rows.append({'cohort':list((domain,law,residue,purpose)),'parameter_counts':partitions})
    return rows


def declaration(per_cohort):
    if type(per_cohort) is not int or per_cohort<2 or per_cohort%2:
        raise ValueError('this balanced development repair requires a positive even original cohort count')
    rows=[];support=support_inventory()
    expected_empty={(domain,law,residue,purpose) for domain in POP.DOMAINS for law in ('novice','novice2')
        for residue,purpose in (('none','explore'),('habit_check','teach'))}
    if {tuple(r['cohort']) for r in support if not r['parameter_counts']['development']}!=expected_empty:
        raise ValueError('finite development support changed; allocation needs a new explicit review')
    for cohort in COHORTS:
        domain,law,residue,purpose=cohort;count=per_cohort
        absent_residue={'explore':'none','teach':'habit_check'}.get(purpose)
        if absent_residue is not None:
            if law in ('novice','novice2'):count=0 if residue==absent_residue else 2*per_cohort
            else:count=3*per_cohort//2 if residue==absent_residue else per_cohort//2
        rows.append({'cohort':list(cohort),'count':count})
    return {'version':1,'role':'development','rule':RULE,'original_per_cohort':per_cohort,
        'finite_support_sha256':digest(support),'counts':rows}


def validate(value,role,per_cohort):
    if role!='development':raise ValueError('finite-support repair is confined to development sources')
    expected=declaration(per_cohort)
    if not isinstance(value,dict) or digest(value)!=digest(expected):
        raise ValueError('development allocation differs from the exact reviewed support and marginals')
    return [row['count'] for row in expected['counts']]


def load(path,role,per_cohort):
    return validate(read(path),role,per_cohort)
