"""Finite post-pilot dispatch, available only through runners/gear3.py.

DESIGN CHECK: LESSONS3-5. NULL and ALTERNATIVE use identical declared jobs.
Unknown owners stop dispatch; a failed domain retires without expanding others.
No job generation, inference from scores, automatic retry or new model wake.
"""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from .gear3_campaign import CampaignLedger,authoritative_ledger,atomic_json,CAMPAIGN
from .gear3_round1 import dispatch
from .stage10.contracts import digest
from .stage10.gear3_io import verify_archive


def run_plan(repo,plan_path,account_path):
    plan=json.loads(plan_path.read_text(encoding='utf8'))
    required={'schema','approval','pilot','pilot_sha256','allowed_bundle_sha256','jobs'}
    if set(plan)!=required or plan['schema']!='gear3.execution_plan.1':raise ValueError('exact frozen execution PLAN required')
    def owned(name):
        p=(repo/name).resolve()
        if not p.is_relative_to(repo.resolve()):raise ValueError('PLAN path escapes checkout')
        return p
    pilot=owned(plan['pilot']);admission=json.loads(pilot.read_text())
    if admission.get('status')!='PASS' or digest(admission)!=plan['pilot_sha256']:raise ValueError('passed pilot binding required')
    if not plan['approval'].strip() or not plan['jobs']:raise ValueError('empty execution PLAN')
    prior=set();phase=-1
    for job in plan['jobs']:
        if set(job)!={'invocation','node','bundle','bundle_sha256','seconds','startup_seconds','overhead_cents','dependencies','failure_domain'}:
            raise ValueError('unknown or missing planned job fields')
        identifier=job['invocation']
        if not identifier or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in identifier):raise ValueError('unsafe invocation')
        if job['node'] not in {'A','B','C','D'} or 'ABCD'.index(job['node'])<phase:raise ValueError('branch order differs')
        phase='ABCD'.index(job['node'])
        if identifier in prior or not set(job['dependencies'])<=prior or not job['failure_domain']:raise ValueError('unresolved dependency or duplicate job')
        prior.add(identifier)
        actual=hashlib.sha256(owned(job['bundle']).read_bytes()).hexdigest()
        if actual!=job['bundle_sha256'] or actual not in plan['allowed_bundle_sha256']:raise ValueError('planned input bytes changed')
    output=repo/'private/gear3/G3-S10-READER-1/sequences'/digest(plan)
    output.mkdir(parents=True,exist_ok=True)
    states={};retired=set();rows=[]
    ledger=CampaignLedger(authoritative_ledger(repo))
    try:
        for job in plan['jobs']:
            identifier=job['invocation'];domain=job['failure_domain']
            if domain in retired or any(states[d]!='COMPLETE' for d in job['dependencies']):
                states[identifier]='NOT_RUN';rows.append({'invocation':identifier,'status':'NOT_RUN','reason':'failed dependency or retired domain'})
                continue
            with ledger.transaction() as data:
                saved=[r for r in data['runs'] if r.get('campaign_id')==CAMPAIGN and r.get('invocation_id')==identifier]
            if saved:
                if len(saved)!=1 or not saved[0]['owner_ended'] or saved[0]['status'] not in {'COMPLETE','FAILED'}:
                    raise RuntimeError('prior owner needs inspection; no clock reset')
                if saved[0]['command'][-1]!=job['bundle_sha256']:raise ValueError('prior input binding differs')
                local=repo/'private/gear3/G3-S10-READER-1/invocations'/identifier
                receipt=verify_archive(local/'OUTPUT.zip')
                original=json.loads((local/'RETRIEVAL.json').read_text())
                terminal=json.loads((local/'REMOTE_TERMINAL.json').read_text())
                reservation=json.loads((local/'RESERVATION.json').read_text())
                row=saved[0]
                immutable=('campaign_id','invocation_id','node','command','profile','resources','duration_cap_seconds',
                           'expires_at','ts','reserved_cents','overhead_cents','approval','campaign_authorization','recovery_of')
                if any(reservation[k]!=row[k] for k in immutable):raise ValueError('prior reservation differs from ledger')
                import zipfile
                with zipfile.ZipFile(local/'OUTPUT.zip') as z:
                    embedded=json.loads(z.read('TERMINAL.json'))
                if (receipt!=original or terminal!=embedded or terminal['status']!=row['status']
                        or terminal['reservation_sha256']!=digest(reservation)
                        or terminal['source_archive_sha256']!=job['bundle_sha256']
                        or terminal.get('owner_ended') is not True):
                    raise ValueError('prior retrieval differs')
                evidence=row['events'][-1]['evidence']
                if evidence['full_archive_sha256']!=receipt['archive_sha256']:
                    raise ValueError('prior archive differs from terminal ledger evidence')
                status=terminal['status']
            else:
                args=SimpleNamespace(account=account_path,bundle=owned(job['bundle']),invocation=identifier,node=job['node'],
                    seconds=job['seconds'],startup_seconds=job['startup_seconds'],overhead_cents=job['overhead_cents'],
                    approval=plan['approval'],recovery_of=None,pilot=pilot,plan=plan_path)
                status=dispatch(repo,args)['status']
            if status not in {'COMPLETE','FAILED'}:raise RuntimeError('unresolved cloud owner')
            states[identifier]=status;rows.append({'invocation':identifier,'status':status})
            if status=='FAILED':retired.add(domain)
            atomic_json(output/'PROGRESS.json',{'plan_sha256':digest(plan),'jobs':rows})
        result={'status':'COMPLETE','plan_sha256':digest(plan),'jobs':rows,
            'scope':'finite execution exhausted with dispositions; scientific comparison pending'}
        atomic_json(output/'COMPLETE.json',result);return result
    except Exception as exc:
        atomic_json(output/'FAILED.json',{'status':'NEEDS_INSPECTION','plan_sha256':digest(plan),'jobs':rows,
            'error':repr(exc),'policy':'no automatic recovery or refreshed expiration'})
        raise
