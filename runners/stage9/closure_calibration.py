"""B03 saved semantic reconstruction of actual-package numerical calibration.

DESIGN CHECK: B03/I03/X02/X06/X07/X12; LESSONS 3--5, CONTROLS 6--7.
NULL: substituted fixtures, fitting/package identities, omitted calls/variants or
changed thresholds cannot close. ALTERNATIVE: the original shared constructor,
all saved calls and the unchanged numerical comparison reproduce the recorded
decision. A failed tolerance remains failed. Bands: verified saved decision,
original failed/unrun disposition, or explicit integrity refusal. No model call,
writer, new reserve opening or scientific competence claim. Capsule isolation and
actual service-request accounting remain separate ledger components.
"""
from pathlib import Path

from . import package_calibration as calibration, calibration_check as consumer
from .common import REPO,closure,digest,file_hash,read
from .live_status import read as read_status
from .queue import inside,verify_committed,verify_disposition
from .train import BASES

MODULE='runners.stage9.package_calibration'
CONSUMER_MODULE='runners.stage9.calibration_check'


def inspect_consumer(job,plan,queue_path):
    """Rebuild the exact fixed or selected consumer decision from saved inputs.

    NULL: rehashed substitutions, non-boolean acceptance or incomplete output
    inventory refuse. ALTERNATIVE: both accepted and rejected numerical decisions
    reproduce unchanged. Target semantics and capsule isolation are checked by
    their separate final-ledger components; no competence is inferred here.
    """
    if job['module']!=CONSUMER_MODULE:raise ValueError('calibration consumer audit requires its original dispatcher')
    args=consumer.argument_parser().parse_args(job['arguments']);directory=inside(REPO/args.output)
    if (REPO/job['produces']).resolve()!=directory/'COMPLETE.json':
        raise ValueError('calibration consumer original output path differs')
    verify_committed(queue_path,job,plan,digest(plan));before=closure([directory])
    identity,decision=consumer.context(directory,args.calibration,args.target,args.scope,args.selected_calibrations,
        cell=digest({'manifest_sha256':digest(plan),'job':job}),source=plan['sources'])
    if digest(read(directory/'IDENTITY.json'))!=digest(identity) or digest(read(directory/'DECISION.json'))!=digest(decision):
        raise ValueError('calibration consumer original identity or saved decision differs')
    done=read(directory/'COMPLETE.json')
    expected={'cell_identity':identity['cell_identity'],'identity_sha256':digest(identity),'execution_complete':True,
        'instrument_accepted':decision['instrument_accepted'],'scientific_admission':False}
    if any(type(done.get(k)) is not type(v) or done[k]!=v for k,v in expected.items()):
        raise ValueError('calibration consumer completion substitutes its decision or scope')
    files=[directory/n for n in ('IDENTITY.json','DECISION.json')]
    inventory=files+[directory/'COMPLETE.json']
    lock=directory/'WRITER.lock'
    if lock.exists():
        # queue.writer leaves this empty coordination file after releasing its
        # OS lock. It is neither a result nor evidence of current ownership.
        if lock.read_bytes()!=b'':raise ValueError('calibration consumer writer lock contains unexpected data')
        inventory.append(lock)
    if done['outputs']!=closure(files) or before!=closure(inventory):
        raise ValueError('calibration consumer output inventory differs')
    if closure([directory])!=before:raise ValueError('read-only calibration consumer audit changed original evidence')
    return {'status':'RECONSTRUCTED','complete_sha256':file_hash(directory/'COMPLETE.json'),
        'decision_sha256':digest(decision),'target_complete_sha256':identity['target_complete_sha256'],
        'calibration_complete_sha256':identity['calibration_complete_sha256'],
        'selected_calibration':'selected_calibration' in identity,'instrument_accepted':decision['instrument_accepted'],
        'new_reader_calls':0,'new_reserve_openings':0,'scientific_admission':False,
        'scope':'Original exact-package consumer decision; target semantics/isolation and complete B03 remain separate'}


def inspect_completed(job,plan,queue_path):
    if job['module']!=MODULE:raise ValueError('calibration audit requires the original dispatcher')
    args=calibration.argument_parser().parse_args(job['arguments']);directory=inside(REPO/args.output)
    if (REPO/job['produces']).resolve()!=directory/'COMPLETE.json':
        raise ValueError('calibration audit differs from its original producer')
    verify_committed(queue_path,job,plan,digest(plan));before=closure([directory])
    saved_identity=read(directory/'IDENTITY.json')
    identity,_,inputs=calibration.context(directory,args.family,args.package_kind,args.training,args.scope,
        cell=digest({'manifest_sha256':digest(plan),'job':job}),source=plan['sources'],
        version=saved_identity['operation'])
    if digest(identity)!=digest(saved_identity) or read(directory/'INPUTS.json')!=inputs:
        raise ValueError('calibration fixtures, fitting or original source identity differ')
    packages=read(directory/'PACKAGES.json');expected_calls=set();expected_units=set();capsules={}
    if set(packages)!={'-'.join(map(str,v)) for v in calibration.VARIANTS}:
        raise ValueError('calibration requires every original precision variant')
    for precision,device,batch in calibration.VARIANTS:
        key=f'{precision}-{device}-{batch}';package=packages[key];base=BASES[args.family]
        expected={'model':base['model'],'revision':base['revision'],'adapter_sha256':identity['adapter_sha256'],
            'precision':precision,'device':device,'batch_size':batch,'max_context':4096,'max_support':128,'max_new_tokens':32}
        scorer=package['scorer_sources']
        if (any(type(package.get(k)) is not type(v) or package[k]!=v for k,v in expected.items())
                or not scorer['files'] or scorer['sha256']!=digest(scorer['files'])
                or package['scorer_sha256']!=scorer['sha256']
                or any(plan['sources']['files'].get(p)!=sha for p,sha in scorer['files'].items())):
            raise ValueError('calibration package differs from original family, adapter or scorer')
        original=inputs['distinct-maximum-support']
        cases={**inputs,'permutation':{'prefix':original['prefix'],'options':dict(reversed(list(original['options'].items())))}}
        for name,evidence in cases.items():
            path=directory/'calls'/key/(name+'.json');cached=read(path)
            task=calibration.call_task(package,evidence,identity['operation'])
            if set(cached)!={'input_sha256','result'} or cached['input_sha256']!=digest({'evidence':evidence,'task':task}):
                raise ValueError('calibration call differs from its reconstructed input')
            result=cached['result'];cap=Path(result['capsule']).resolve()
            if not cap.is_relative_to(directory/'capsules') or cap in capsules:
                raise ValueError('calibration call substitutes or reuses its capsule')
            if (result.get('accepted') is not True or read(cap/'evidence.json')!=evidence or read(cap/'task.json')!=task
                    or any(read(cap/'out'/(n+'.json'))!=result.get(n) for n in ('prediction','receipt','access'))):
                raise ValueError('completed calibration lacks its actual valid capsule outputs')
            calibration.audit_execution(result);expected_calls.add(path);capsules[cap]=path
        expected_units.add(directory/'units'/(digest(key)+'.json'))
    if (set((directory/'calls').rglob('*.json'))!=expected_calls
            or set((directory/'units').glob('*.json'))!=expected_units):
        raise ValueError('calibration contains missing or extra calls or variants')
    decision=calibration.checked_calibration(directory,packages['float16-cuda-4'])
    done=read(directory/'COMPLETE.json')
    expected={'execution_complete':True,'instrument_only':True,'family':args.family,'package_kind':args.package_kind,
        'adapter_sha256':identity['adapter_sha256'],'data_role':'pilot','scientific_admission':False,
        'instrument_accepted':decision['instrument_accepted'],'old_1e_minus6_pass':decision['old_1e_minus6_pass']}
    if any(type(done.get(k)) is not type(v) or done[k]!=v for k,v in expected.items()):
        raise ValueError('calibration completion substitutes its actual decision or scope')
    if closure([directory])!=before:raise ValueError('read-only calibration audit changed original evidence')
    return {'status':'RECONSTRUCTED','variants':len(expected_units),'calls':len(expected_calls),
        'complete_sha256':file_hash(directory/'COMPLETE.json'),'inputs_sha256':digest(inputs),
        'calculation_sha256':file_hash(directory/'CALIBRATION.json'),
        'instrument_accepted':decision['instrument_accepted'],'old_1e_minus6_pass':decision['old_1e_minus6_pass'],
        'new_reader_calls':0,'new_reserve_openings':0,'scientific_admission':False,
        'scope':'Original numerical calibration from discarded fixtures; not scientific competence or complete B03'}


def queue_audits(plan,queue_path,prior):
    state=read_status(queue_path/'STATUS.json');result={}
    for key,job in prior.items():
        if job['module'] not in (MODULE,CONSUMER_MODULE):continue
        current=state['jobs'][key]
        if current['status']=='COMPLETE':
            inspect=inspect_completed if job['module']==MODULE else inspect_consumer
            result[key]=inspect(job,plan,queue_path)
        elif current['status'] in ('FAILED','NOT_RUN'):
            verify_disposition(queue_path,job,current)
            result[key]={k:current[k] for k in ('status','reason','disposition_sha256')}
        else:raise ValueError('calibration audit requires terminal producer jobs')
    return {'jobs':result,'scientific_admission':False}
