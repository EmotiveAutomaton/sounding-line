"""Manually reviewed finite dispatch list; source outcomes do not generate studies.

DESIGN CHECK: LESSONS 3-5. NULL: a gate file without a passing verdict cannot
activate a dependent job; duplicate produces and changed plans are rejected.
ALTERNATIVE: independent pilots/branches run serially after the existing owner,
while conditional extensions reserve later-branch budget and selection wakes.
"""
from pathlib import Path
from .common import PRIVATE,read,freeze,digest,canonical
from . import preflight,branch_runtime,continuation


def validate_task(task):
    from .models_v3 import request_for
    if task['kind']!='forecast':
        branch_runtime.auxiliary_request(task);return
    evidence=task['public'];possibilities=[evidence]
    if 'reveal' in task:possibilities=[dict(evidence,observation=o) for o in task['reveal']['observations'].values()]
    if 'history_ref' in task:possibilities=[dict(evidence,history_hypothesis={'reserved':'x'*3072})]
    for e in possibilities:
        for kind in branch_runtime.task_steps(task):
            retained={'reserved':'x'*3050} if kind in ('review','account_predict') else None
            request_for(e,kind,retained)


def setup(root=PRIVATE):
    items=[]
    def legacy(name,requires=(),reserve=0):
        path=root/'plans'/f'{name}.json';p=read(path)
        calls=sum(len(j['keys'])*len(j['views'])*sum(len(branch_runtime.base.chain(m)) for m in j['methods']) for j in p['jobs'])
        items.append(dict(id=name,runner='legacy',path=path.relative_to(root).as_posix(),digest=digest(p),calls=calls,
                          requires=list(requires),reserve_seconds=reserve,next_action=p['next_action']))
    def branch(name,requires=(),reserve=0):
        path=root/'branch_plans'/f'{name}.json'
        if not path.exists():return
        p=read(path)
        for t in p['tasks']:validate_task(t)
        items.append(dict(id=name,runner='branch',path=path.relative_to(root).as_posix(),digest=digest(p),calls=p['maximum_calls'],
                          requires=list(dict.fromkeys(p['requires']+list(requires))),reserve_seconds=reserve,next_action=p['next_action']))
    for method in ('review','account'):
        full=read(root/'plans'/f'S1-{method}-v3b.json')
        for job in full['jobs']:
            name=job['id']+'-only'
            freeze(root/'plans'/f'{name}.json',dict(full,id=name,jobs=[job]))
    legacy('review-pilot-v3b');legacy('account-pilot-v3b')
    legacy('S1-review-initial-v3b-only',['REVIEW_PILOT_PASSED-v3.json'])
    legacy('S1-account-initial-v3b-only',['ACCOUNT_PILOT_PASSED-v3.json'])
    branch('query-pilot-v1');branch('history-pilot-v1');branch('S4-history-v1',['DIRECT_PILOT_PASSED-v3.json'])
    branch('revision-pilot-v1');branch('S3-revision-v1')
    branch('S3-initial-direct-v1')
    branch('S1-account-interventions-v1')
    branch('llama-direct-pilot-v1');branch('llama-review-pilot-v1');branch('llama-account-pilot-v1')
    branch('S3-second-reader-direct-v1')
    legacy('S1-review-extension-v3b-only',['REVIEW_PILOT_PASSED-v3.json'],40000)
    legacy('S1-account-extension-v3b-only',['ACCOUNT_PILOT_PASSED-v3.json'],40000)
    # Validate every prepared candidate as well, even when selection has not yet
    # admitted it. A failed preparation is never silently queued.
    checked=0
    for path in (root/'branch_plans').glob('*.json'):
        for t in read(path)['tasks']:validate_task(t);checked+=1
    live=read(Path('.agent-state/stage11-1-direct-live.json'))
    manifest=dict(id='setup-v1',gear=2,wait_for=dict(native=live['native'],produce='plans/S1-direct-v3b-COMPLETE.json'),
                  items=items,next_action='Full S1 comparison and explicit activation of prepared S2/S3 candidates; Sunday packet remains open')
    continuation.validate_manifest(manifest)
    freeze(root/'continuation/QUEUE-v1.json',manifest)
    result=dict(status='PREPARED',queue_digest=digest(manifest),items=len(items),maximum_additional_calls=sum(i['calls'] for i in items),
                optional_extension_calls=sum(i['calls'] for i in items if i['reserve_seconds']),preflight_tasks=checked,
                sources=branch_runtime.sources(),no_new_model_calls=True,
                next_action=manifest['next_action'])
    freeze(root/'continuation/QUEUE-READY.json',result);return result


if __name__=='__main__':print(canonical(setup()))
