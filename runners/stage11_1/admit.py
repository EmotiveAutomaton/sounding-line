"""Freeze the reviewed initial plans; later branches require their own admission.

DESIGN CHECK: LESSONS 2-5. NULL: a constructed interface pilot supplies no human
accuracy or independent confirmation. ALTERNATIVE: both exact-history twins realize
the common forms and the pre-audited fixed discovery sequence can proceed.
"""
from .common import PRIVATE,read,freeze,digest,allocation
from .models import VIEWS
from .targets import public,project
from .run import source_pin
from runners.stage11.run import fixture
from runners.stage11.replay import replay


def admit(root=PRIVATE):
    alloc=allocation(root);cohort=read(root/'COHORT.json');prepared=read(root/'PREPARED.json')
    if read(root/'TARGET_AUDIT.json')['status']!='PASS':raise ValueError('reviewed source audit required')
    pilot=[]
    for i in range(2):
        lines=fixture(i==0);e=replay(lines)['events'][0]
        pilot.append(dict(key=f'pilot{i}',writer=f'constructed{i}',session=f'constructed{i}',prompt='same',
            views={v:public(e,v) for v in VIEWS},target=project(e,lines),partition='discarded_constructed'))
    pilots=dict(pilot=pilot);freeze(root/'PILOT_COHORT.json',pilots)
    common=dict(threads=alloc['cpu_threads'],views=list(VIEWS),warrant='Descriptive exposed-record comparison; no fresh confirmation')
    pilot_job=dict(common,id='interface-pilot',branch='integration',partition='discarded_constructed',
        keys=[r['key'] for r in pilot],methods=['direct','review','account'],pilot=True,
        pursuit='Validate literal model interface for both endpoint-equivalent histories',
        next_action='S1 direct reference initial and frozen extension')
    pilot_plan=dict(id='interface-pilot',cohort_file='PILOT_COHORT.json',cohort_digest=digest(pilots),jobs=[pilot_job],
        next_action='S1 direct reference bank; retain all pilot costs')
    freeze(root/'plans/interface-pilot.json',pilot_plan)
    jobs=[]
    for tranche in ('initial','extension'):
        keys=[r['key'] for r in cohort['discovery'] if r['tranche']==tranche]
        jobs.append(dict(common,id=f'S1-direct-{tranche}',branch='S1',partition=f'discovery_{tranche}',keys=keys,
            methods=['direct'],requires_pilot=True,pursuit='Common-form direct reference on both blind evidence tiers',
            next_action=f'S1 budget-matched review and account-first on the identical {tranche} rows'))
    direct=dict(id='S1-direct',cohort_digest=digest(cohort),jobs=jobs,
        next_action='Land whole reference cells and launch the matched account/review blocks; campaign remains open')
    freeze(root/'plans/S1-direct.json',direct)
    matched=[]
    for j in jobs:
        matched.append(dict(j,id=j['id'].replace('direct','matched'),methods=['review','account'],
            pursuit='Sequential account versus equally budgeted direct review',
            next_action='S1 account intervention, S2 evidence dose, S3 breadth and S4 earlier-history contrasts'))
    freeze(root/'plans/S1-matched.json',dict(id='S1-matched',cohort_digest=digest(cohort),jobs=matched,
        next_action='Interpret complete contrasts and follow the authorized continuation tree'))
    return dict(status='ADMITTED',pilot_attempts=20,direct_attempts=2*len(cohort['discovery']),
        matched_attempts=8*len(cohort['discovery']),gear=alloc['gear'],sources=source_pin())


if __name__=='__main__':print(admit())
