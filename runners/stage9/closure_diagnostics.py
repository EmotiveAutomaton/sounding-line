"""B03 reconstruction of saved operation diagnostics using their original inputs.

DESIGN CHECK: B03/C01/C02/C04/C06/C08/X01/X06/X08/X11/X12;
LESSONS 3--5, CONTROLS 6--7. NULL: a rehashed summary, changed cohort, package,
assistance condition or boolean cannot pass as the original calculation.
ALTERNATIVE: complete saved units and unchanged formulas reproduce the summary,
including invalid, unscored and descriptive outcomes. Bands: exact reconstruction,
original FAILED/NOT_RUN disposition, or integrity refusal. No reader invocation,
writer, reserve opening, new competence verdict or complete B03 acceptance.
Original neural semantics and capsule isolation have separate ledger components.
"""
from . import operation_analysis as analysis
from .common import REPO,closure,digest,file_hash,read
from .live_status import read as read_status
from .queue import inside,verify_committed,verify_disposition
from .scoring import score_json

MODULE='runners.stage9.operation_analysis'


def inspect_completed(job,plan,queue_path):
    if job['module']!=MODULE:raise ValueError('diagnostic audit requires its original dispatcher')
    args=analysis.argument_parser().parse_args(job['arguments']);directory=inside(REPO/args.output)
    if (REPO/job['produces']).resolve()!=directory/'COMPLETE.json':
        raise ValueError('diagnostic audit differs from its original output')
    verify_committed(queue_path,job,plan,digest(plan));before=closure([directory])
    inputs=[inside(args.cases),inside(args.plan)]
    inputs.extend(inside(p) for p in read(inside(args.plan))['inputs'].values())
    input_before=closure(inputs)
    identity,cases,rows=analysis.context(directory,args.cases,args.plan,args.scope,
        cell=digest({'manifest_sha256':digest(plan),'job':job}),source=plan['sources'])
    expected_profile=score_json(analysis.summarize(identity['kind'],cases,rows))
    if (digest(read(directory/'IDENTITY.json'))!=digest(identity)
            or digest(read(directory/'PROFILE.json'))!=digest(expected_profile)):
        raise ValueError('diagnostic original identity or recalculated profile differs')
    done=read(directory/'COMPLETE.json')
    expected={'cell_identity':identity['cell_identity'],'identity_sha256':digest(identity),
        'execution_complete':True,'scientific_admission':False}
    if any(type(done.get(k)) is not type(v) or done[k]!=v for k,v in expected.items()):
        raise ValueError('diagnostic completion substitutes its execution or scope')
    files=[directory/n for n in ('IDENTITY.json','PROFILE.json')]
    inventory=files+[directory/'COMPLETE.json'];lock=directory/'WRITER.lock'
    if lock.exists():
        if lock.read_bytes()!=b'':raise ValueError('diagnostic writer lock contains unexpected data')
        inventory.append(lock)
    if done['outputs']!=closure(files) or before!=closure(inventory):
        raise ValueError('diagnostic output inventory differs')
    if closure([directory])!=before or closure(inputs)!=input_before:
        raise ValueError('read-only diagnostic audit changed original evidence')
    return {'status':'RECONSTRUCTED','kind':identity['kind'],
        'complete_sha256':file_hash(directory/'COMPLETE.json'),'profile_sha256':digest(expected_profile),
        'source_cases':len(cases),'operation_units':{name:len(value) for name,value in rows.items()},
        'input_files':len(input_before['files']),'input_sha256':input_before['sha256'],
        'new_reader_calls':0,'new_reserve_openings':0,'scientific_admission':False,
        'scope':'Original diagnostic calculations; neural semantics/isolation and complete B03 remain separate'}


def queue_audits(plan,queue_path,prior):
    state=read_status(queue_path/'STATUS.json');result={}
    for key,job in prior.items():
        if job['module']!=MODULE:continue
        current=state['jobs'][key]
        if current['status']=='COMPLETE':result[key]=inspect_completed(job,plan,queue_path)
        elif current['status'] in ('FAILED','NOT_RUN'):
            verify_disposition(queue_path,job,current)
            result[key]={k:current[k] for k in ('status','reason','disposition_sha256')}
        else:raise ValueError('diagnostic audit requires terminal producer jobs')
    return {'jobs':result,'scientific_admission':False}
