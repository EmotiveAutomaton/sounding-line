"""Whole-plan affordability and literal-pilot evidence admission.

DESIGN CHECK: LESSONS3-5. Both hypotheses use the same outcome-blind finite
prefix. Individual affordability never licenses an aggregate overrun. Pilot
admission binds actual reservations, device/raw outputs and producer sources;
a PASS boolean alone cannot authorize scientific dispatch.
"""
from copy import deepcopy
import hashlib,json,math,tempfile,zipfile
from pathlib import Path
from .gear3_campaign import CAMPAIGN,NODE_CENTS,CampaignLedger,capped_cost_cents
from .stage10.contracts import digest
from .stage10 import gear3_bundle,gear3_io,gear3_batch


def owned(repo,name):
    p=(repo/name).resolve()
    if not p.is_relative_to(repo.resolve()):raise ValueError('PLAN path escapes checkout')
    return p


def verify_invocation(repo,invocation,bundle,data,ghost_root):
    from .gear3_round1 import verify_completed_blocks
    rows=[r for r in data['runs'] if r.get('campaign_id')==CAMPAIGN and r.get('invocation_id')==invocation]
    if len(rows)!=1 or not rows[0].get('owner_ended') or rows[0]['status'] not in {'COMPLETE','FAILED'}:
        raise ValueError('invocation requires verified terminal ownership')
    row=rows[0];local=repo/'private/gear3/G3-S10-READER-1/invocations'/invocation
    reservation=json.loads((local/'RESERVATION.json').read_text())
    immutable=('campaign_id','invocation_id','node','command','profile','resources','duration_cap_seconds',
               'expires_at','ts','reserved_cents','overhead_cents','approval','campaign_authorization','recovery_of')
    if any(reservation[k]!=row[k] for k in immutable):raise ValueError('original reservation differs from ledger')
    if reservation.get('supplement_authorization') != row.get('supplement_authorization'):
        raise ValueError('supplement authorization differs from original reservation')
    job,checked=gear3_bundle.validate_input(bundle,repo,ghost_root)
    if checked['archive_sha256']!=row['command'][-1] or digest(job)!=row['profile']['job_sha256']:
        raise ValueError('producer input differs from reservation')
    terminal=json.loads((local/'REMOTE_TERMINAL.json').read_text())
    receipt=gear3_io.verify_archive(local/'OUTPUT.zip',local/'restored')
    if (receipt!=json.loads((local/'RETRIEVAL.json').read_text())
            or terminal!=json.loads((local/'restored/TERMINAL.json').read_text())
            or terminal['status']!=row['status'] or terminal.get('owner_ended') is not True
            or terminal['reservation_sha256']!=digest(reservation)
            or terminal['source_archive_sha256']!=checked['archive_sha256']
            or row['events'][-1]['evidence']['full_archive_sha256']!=receipt['archive_sha256']):
        raise ValueError('returned invocation evidence differs from original ownership')
    if row['status']=='COMPLETE':verify_completed_blocks(job,bundle,local/'restored',ghost_root)
    return row,job,terminal,receipt,local/'restored'


def pilot_evidence(repo,invocation,bundle,data,ghost_root):
    row,job,terminal,receipt,restored=verify_invocation(repo,invocation,bundle,data,ghost_root)
    if row['node']!='P' or row['status']!='COMPLETE' or job['mode']!='science' or row['resources']['gpu']!='L40S':
        raise ValueError('complete literal GPU pilot required')
    device=json.loads((restored/'GPU_DEVICE.json').read_text())
    if device['returncode']!=0 or 'L40S' not in device['stdout'] or terminal['gpu_observation']['samples']<1:
        raise ValueError('actual L40S device evidence absent')
    loads=[]
    for path in sorted(restored.glob('load-*-memory.json')):
        value=json.loads(path.read_text());models=value.get('models',[])
        if (len(models)!=1 or models[0]['digest'] not in gear3_batch.PINS.values()
                or models[0].get('context_length')!=16384
                or type(models[0].get('size_vram')) is not int or models[0]['size_vram']<models[0]['size']):
            raise ValueError('pilot model/context does not fit fully on admitted GPU')
        loads.append(value)
    if {v['models'][0]['digest'] for v in loads}!=set(gear3_batch.PINS.values()):raise ValueError('pilot lacks both actual model loads')
    timings=[];valid=set();attempted=set()
    with zipfile.ZipFile(bundle) as z:
        for name in job['blocks']:
            m=json.loads(z.read(name))
            if m['node']!='P':raise ValueError('non-discarded source in pilot')
            tasks,_=gear3_batch.validate(m)
            for u in m['units']:
                route=restored/'blocks'/m['block_id']/'units'/digest(u)[:32]
                saved=json.loads((route/'UNIT.json').read_text())
                task,_=tasks[u['task_id']];key=(task.family,u['model'],u['arm'])
                attempted.add(key)
                if saved['result']['status']=='VALID':valid.add(key)
                calls=list((route/'route').rglob('ATTEMPT.json'))
                for call in calls:
                    raw=json.loads(call.with_name('RAW.json').read_text())
                    if raw.get('fixture') or raw.get('simulated') or raw.get('message',{}).get('thinking'):
                        raise ValueError('pilot contains constructed transport or unexpected thinking')
                if 'context-boundary' not in m['scope']:
                    timings.append({'family':key[0],'model':key[1],'arm':key[2],'seconds':saved['unit_wall_seconds']})
    # Protocol validity, not predictive accuracy, governs usable route admission.
    return {'schema':'gear3.pilot_admission.2','status':'PASS','invocation':invocation,
            'bundle':bundle.relative_to(repo).as_posix(),'bundle_sha256':row['command'][-1],
            'reservation_sha256':terminal['reservation_sha256'],'archive_sha256':receipt['archive_sha256'],
            'execution_sources':job['execution_source_hashes'],'profiles':job['profiles'],
            'device':device,'gpu_observation':terminal['gpu_observation'],'loads':loads,
            'route_timings':timings,'valid_routes':[list(k) for k in sorted(valid)],
            'unrealized_routes':[list(k) for k in sorted(attempted-valid)],
            'measurement_margin':1.25,'service_duration_seconds':terminal['duration_seconds'],
            'scope':'discarded interface/device/cost admission; no scientific scores'}


def validate_pilot(repo,path,data,ghost_root):
    saved=json.loads(path.read_text())
    if saved.get('schema')=='gear3.scoped_pilot_admission.1':
        from .gear3_scoped_pilot import compose
        rebuilt=compose(repo,owned(repo,saved['bundle']),owned(repo,saved['supplement']['bundle']),data,ghost_root)
        if rebuilt!=saved:raise ValueError('scoped pilot does not reproduce its original evidence')
        return saved
    if saved.get('schema')!='gear3.pilot_admission.2':raise ValueError('source-bound literal pilot required')
    rebuilt=pilot_evidence(repo,saved['invocation'],owned(repo,saved['bundle']),data,ghost_root)
    if rebuilt!=saved:raise ValueError('pilot admission does not reproduce actual evidence')
    return saved


def affordable_jobs(jobs,data,account):
    from .gear3_round1 import account_reservation_guard
    simulated=deepcopy(data);initial=CampaignLedger.totals(data)
    known={r.get('invocation_id'):r for r in data['runs'] if r.get('campaign_id')==CAMPAIGN}
    for job in jobs:
        if job['invocation'] in known:
            old=known[job['invocation']]
            if old['command'][-1]!=job['bundle_sha256'] or old['node']!=job['node']:
                raise ValueError('planned invocation differs from prior booking')
            continue
        amount=capped_cost_cents(job['seconds'],job['overhead_cents']);node=job['node']
        totals=CampaignLedger.totals(simulated)
        if (node not in {'A','B','C','D'} or totals[node]+amount>NODE_CENTS[node]
                or sum(totals.values())+amount>5000
                or sum(v for k,v in totals.items() if k!='Reserve')+amount>4000
                or (node=='A' and totals['P']+totals['A']+amount>2000)):
            raise ValueError('aggregate PLAN exceeds campaign/branch/initial allowance')
        account_reservation_guard(account,simulated,node,amount)
        simulated['runs'].append({'campaign_id':CAMPAIGN,'invocation_id':job['invocation'],'node':node,'booked_cents':amount})
    final=CampaignLedger.totals(simulated)
    return {'existing_booked_by_node':initial,'planned_total_by_node':final,
            'additional_cents':sum(final.values())-sum(initial.values()),
            'workspace_snapshot_sha256':digest(account),'basis':'whole plan including original pilot and unresolved costs; 1000-cent repair reserve retained'}


def validate_plan(repo,plan,account,data,ghost_root):
    required={'schema','approval','pilot','pilot_sha256','allowed_bundle_sha256','jobs','analysis','analysis_sha256','affordability'}
    if set(plan)!=required or plan['schema']!='gear3.execution_plan.2' or not plan['jobs'] or not plan['approval'].strip():
        raise ValueError('complete frozen execution/analysis PLAN required')
    pilot=validate_pilot(repo,owned(repo,plan['pilot']),data,ghost_root)
    if digest(pilot)!=plan['pilot_sha256']:raise ValueError('PLAN pilot binding differs')
    analysis=json.loads(owned(repo,plan['analysis']).read_text())
    from .stage10.gear3_consumer import validate_analysis
    validate_analysis(analysis,plan)
    if digest(analysis)!=plan['analysis_sha256']:raise ValueError('frozen local evaluator/consumer plan differs')
    expected={(b['invocation'],b['block_id']):b for b in analysis['blocks']};observed=set();writers={};history={}
    prior=set();phase=-1;seen=set();a={};valid={tuple(k) for k in pilot['valid_routes']}
    for job in plan['jobs']:
        if set(job)!={'invocation','node','bundle','bundle_sha256','seconds','startup_seconds','overhead_cents','dependencies','failure_domain'}:
            raise ValueError('unknown planned job fields')
        identifier=job['invocation'];node=job['node']
        if (not identifier or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in identifier)
                or node not in {'A','B','C','D'} or 'ABCD'.index(node)<phase or identifier in prior
                or not set(job['dependencies'])<=prior or not job['failure_domain']):raise ValueError('invalid finite job/dependency order')
        phase='ABCD'.index(node);prior.add(identifier)
        payload,checked=gear3_bundle.validate_input(owned(repo,job['bundle']),repo,ghost_root)
        if checked['archive_sha256']!=job['bundle_sha256'] or job['bundle_sha256'] not in plan['allowed_bundle_sha256']:
            raise ValueError('planned bundle bytes differ')
        if payload['execution_source_hashes']!=pilot['execution_sources'] or payload['profiles']!=pilot['profiles']:
            raise ValueError('scientific source/model differs from literal pilot')
        if type(job['startup_seconds']) is not int or not 1<=job['startup_seconds']<=job['seconds']:
            raise ValueError('bounded planned startup required')
        with zipfile.ZipFile(owned(repo,job['bundle'])) as z:
            for name in payload['blocks']:
                block=json.loads(z.read(name));tasks,_=gear3_batch.validate(block)
                if block['node']!=node:raise ValueError('block branch differs')
                key=(identifier,block['block_id']);binding=expected.get(key);observed.add(key)
                if binding is None or binding['manifest_sha256']!=digest(block) or binding['task_ids']!=list(tasks):
                    raise ValueError('scientific block differs from frozen analysis')
                condition='other-writer' if 'other-writer' in block['scope'] else 'artifact-only' if 'artifact-only' in block['scope'] else 'ordinary'
                for tid,(task,row) in tasks.items():
                    key=(node,condition,tid)
                    if key in seen:raise ValueError('duplicated planned opportunity')
                    seen.add(key)
                    if any((task.family,u['model'],u['arm']) not in valid for u in block['units'] if u['task_id']==tid):
                        raise ValueError('planned route lacks valid literal pilot example')
                    if node=='A':
                        a[tid]=identifier
                        if task.family=='coauthor-handling':writers.setdefault(row['group'],set()).add(tid)
                    if node=='B':history.setdefault(condition,{}).setdefault(row['group'],set()).add(tid)
                    if node in {'B','C'} and (tid not in a or a[tid] not in job['dependencies']):
                        raise ValueError('B/C needs actual admitted A counterpart dependency')
                    if node=='D' and tid in a:raise ValueError('D repeats earlier task')
    if observed!=set(expected):raise ValueError('analysis has unplanned blocks')
    if any(len(v)>8 for v in writers.values()) or any(len(v)>2 for groups in history.values() for v in groups.values()):raise ValueError('writer event cap exceeded')
    if history and (set(history)!={'other-writer','artifact-only'} or history['other-writer']!=history['artifact-only']):raise ValueError('history conditions need identical admitted targets')
    affordable=affordable_jobs(plan['jobs'],data,account)
    # Frozen evidence is retained; a refreshed current guard may reduce headroom,
    # but cannot make an originally unaffordable plan acceptable retroactively.
    if plan['affordability']['additional_cents'] < affordable['additional_cents']:
        raise ValueError('PLAN cost is understated')
    return pilot,analysis,affordable
