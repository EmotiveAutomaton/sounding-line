"""Week 6 R18 extension v2 policy: explicit allowance modes with unchanged inclusive accounting.

DESIGN CHECK: LESSONS 3-5, 2026-11-07. Identical gates under scientific null
and alternative. Missing pins, unavailable capacity or budget refuse starts;
never reinterpret an operational failure as a scientific null. Unstarted
reservations do not consume CPU. Active measured use and all failed use do.
"""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import math
import os
import psutil
from .batch_runtime import REPO, read as raw_read, resource_snapshot
import time
import json
import stat
from . import week6_limits_extension_v2 as limits

OPEN = datetime.fromisoformat('2026-11-16T06:00:00+00:00')
FREEZE = datetime.fromisoformat('2026-11-23T04:00:00+00:00')
DRAIN = datetime.fromisoformat('2026-11-23T06:00:00+00:00')
ADDENDUM = datetime.fromisoformat('2026-11-23T07:00:00+00:00')
ROOT = REPO/'results/phase_2_4_stage_15/raw/drive-week6-20261115'
OLD_SLOTS = REPO/'results/.cpu-slots-20261017'
NEW_SLOTS = REPO/'results/.cpu-slots-20261107'
SHARED_LOCK = OLD_SLOTS/'tompathy-demo-prep.lock'
CEILING = 6_000_000.0
FAMILY_CEILINGS = dict(AT=750000, CH=2500000, IN=200000, SP=40000,
                       GO=600000, MD=120000, LA=450000, ID=40000, BK=1000000, EX=100000,
                       RF=40000, CP=60000, IS=40000, SV=60000, RW=20000,
                       KP=20000, ES=100000, MI=10000, IP=20000, EN=60000)

READ_DELAYS=(.01,.02,.04,.08,.16)

class AccountingReadError(RuntimeError):
    """Accounting is unavailable; no zero, cached value or permission bypass."""

def retry_read(call,path):
    for attempt in range(len(READ_DELAYS)+1):
        try:return call()
        except (PermissionError,FileNotFoundError,json.JSONDecodeError) as exc:
            if attempt==len(READ_DELAYS):
                raise AccountingReadError('Accounting read unavailable after six attempts: '+str(path)) from exc
            time.sleep(READ_DELAYS[attempt])

def read(path):return retry_read(lambda:raw_read(path),path)

def present(path):
    # Path.exists can hide some OS failures. Only actual absence is absence.
    def inspect():
        try:Path(path).stat();return True
        except FileNotFoundError:return False
    return retry_read(inspect,path)

def finite(value, positive=False):
    if type(value) not in (int,float) or not math.isfinite(value) or value < 0 or (positive and value == 0):
        raise ValueError('Invalid finite nonnegative accounting value')
    return float(value)

def instant(value):
    result = datetime.fromisoformat(value)
    if result.tzinfo is None: raise ValueError('Explicit timezone required')
    return result.astimezone(timezone.utc)

def shared_reservation(path=SHARED_LOCK, at=None):
    at = at or datetime.now(timezone.utc)
    if not present(path): return dict(active=False,reason='absent')
    value=read(path)
    if not value.get('expires_at'): return dict(active=False,reason='missing_expiry',log_required=True)
    created, expires=instant(value['created_at']),instant(value['expires_at'])
    if created>at or expires<=created: raise ValueError('Invalid shared reservation clock')
    effective=min(expires,created+timedelta(hours=6),FREEZE)
    return dict(active=at<effective,reason='valid' if at<effective else 'expired',effective_expiry=effective.isoformat())

def charges(root=ROOT, exclude=None, card_key=None):
    """Count actual attempt CPU; unknown terminated attempts retain their full cap.

    Monitor progress is refreshed every two seconds. The additional two-second
    sampling envelope per active two-thread worker covers concurrent last ticks.
    """
    families={k:0.0 for k in FAMILY_CEILINGS};pending=[]
    for key,row in limits.budgets(root).items():
        if row['family'] not in families: raise ValueError('Unknown preparation family')
        if card_key is None or key==card_key: families[row['family']]+=row['preparation_cpu_seconds']
    # Explicit listing propagates directory access failure instead of silently
    # turning a failed glob into an empty campaign.
    directories=retry_read(lambda:list(Path(root).iterdir()),root)
    for directory in directories:
        if not stat.S_ISDIR(retry_read(directory.stat,directory).st_mode):continue
        path=directory/'PLAN.json'
        if not present(path):continue
        if exclude and path.parent.resolve()==Path(exclude).resolve(): continue
        plan=read(path)
        if plan.get('campaign')!='S15-WEEK6': continue
        if card_key is not None and plan['budget_key']!=card_key: continue
        family=plan['family']
        if family not in families: raise ValueError('Unknown campaign family')
        terminals=[path.parent/n for n in ('COMPLETE.json','FAILED.json','PAUSED.json') if present(path.parent/n)]
        if len(terminals)>1: raise ValueError('Ambiguous terminal accounting')
        claimed=present(path.parent/'ATTEMPT.claim')
        if terminals: charge=finite(read(terminals[0])['cpu_seconds'])
        elif not claimed: charge=0.0
        elif present(path.parent/'BUDGET_PROGRESS.json'):
            progress=read(path.parent/'BUDGET_PROGRESS.json')
            pending.append((family,finite(progress['cpu_seconds']),instant(progress['at']),finite(plan['max_cpu_seconds'])))
            charge=0.0 # Replaced by the complete pending contribution below.
        else: charge=finite(plan['max_cpu_seconds'])
        # Supervisor/launcher/replay coordination is charged conservatively.
        families[family]+=charge+(30 if claimed else 0)
    at=datetime.now(timezone.utc)
    for family,measured,stamp,cap in pending:
        age=(at-stamp).total_seconds()
        if age<0:raise ValueError('Accounting progress clock is in the future')
        # Reconcile elapsed retry/listing time at the end of the complete
        # snapshot; retain the two-second, two-thread sampling envelope.
        families[family]+=measured+2*(age+2) if age<15 else max(cap,measured)
    return families

def remaining(family, root=ROOT, exclude=None):
    used=charges(root,exclude)
    return max(0.0,min(FAMILY_CEILINGS[family]-used[family],CEILING-sum(used.values())))

def available(plan, root=ROOT, exclude=None):
    budget=limits.plan_budget(plan,root)
    spent=sum(charges(root,exclude,card_key=plan['budget_key']).values())
    family_room=remaining(plan['family'],root,exclude)
    if budget['allowance_mode']=='lb_idle_family':
        return family_room
    card_room=budget['effective_ceiling_cpu_seconds']-budget['prior_campaign_cpu_seconds']-spent
    return max(0.0,min(card_room,family_room))


def lease_paths(old=OLD_SLOTS,new=NEW_SLOTS):
    return sorted(Path(old).glob('slot-*.json'))+sorted(Path(new).glob('slot-*.json'))

def memory_reserve(paths):
    extra=0.0
    for path in paths:
        lease=read(path)
        if 'projected_peak_ram_GiB' in lease:
            peak=finite(lease['projected_peak_ram_GiB'],True)
        else:
            # Older runtime lease: locate its actual frozen plan by card, never
            # assume zero peak merely because an old lease omitted the field.
            card=lease['card']; found=[]
            for campaign in ('drive-week4-20261102','theory-days-20261106','drive-week3-20261025'):
                p=REPO/'results/phase_2_4_stage_15/raw'/campaign/card/'PLAN.json'
                if p.exists(): found.append(read(p))
            if len(found)!=1: raise RuntimeError('Older lease peak needs explicit reconciliation')
            peak=finite(found[0]['projected_peak_ram_GiB'],True)
        native=lease['native']; pid=native.get('pid',native.get('windows_pid'))
        try:
            proc=psutil.Process(pid)
            from runners.stage9.process_identity import native_identity
            if native_identity(pid)!=native: raise RuntimeError('Lease process identity changed; reconcile before admission')
            used=sum(p.memory_info().rss for p in [proc,*proc.children(recursive=True)])/2**30
        except (psutil.NoSuchProcess,psutil.AccessDenied): used=0.0
        extra+=max(0,peak-used)
    return extra

NEW_FAMILIES = frozenset({'KP','ES','MI','IP','EN'})

def runtime_contract(plan):
    if plan.get('accounting_runtime') != 'week6-extension-v2':
        raise ValueError('Explicit reviewed Week6 R18 extension accounting runtime required')


def sealed_fixture_contract(plan):
    if plan.get('family') != 'MI':
        return
    if not (plan.get('fixture_only') is True and plan.get('data_access') == 'constructed-fixture-only'):
        raise ValueError('MI admits constructed fixture work only; no MIDUS rows')
    spec = plan['sealed_fixture_manifest']; path = Path(spec['path']).resolve()
    from .batch_runtime import filehash
    if filehash(path) != spec['sha256'] or plan['pins'].get(str(path)) != spec['sha256']:
        raise ValueError('MI fixture manifest must be exactly pinned')
    manifest = read(path)
    if not (manifest.get('kind') == 'MIDUS_CONSTRUCTED_FIXTURE_V1'
            and manifest.get('no_real_rows') is True and manifest.get('mr1_refused') is True
            and manifest.get('inputs') == plan['inputs'] and manifest.get('module') == plan['module']):
        raise ValueError('MI sealed fixture/source contract differs')

def require_new_family_transition(plan, root=ROOT):
    """Old policy readers reject unknown families, even unclaimed plans.

    Call BEFORE writing a new-family PLAN and again under the admission mutex.
    Never treat a missing receipt, inaccessible identity, or unexplained dead
    legacy attempt as permission to proceed. All old code remains immutable.
    """
    runtime_contract(plan)
    from .week6_transition_services_v2 import require_transition
    path = str(Path(plan['migration_review']).resolve())
    digest = plan['migration_review_sha256']
    if plan['pins'].get(path) != digest:
        raise ValueError('Exact R18 migration review must be pinned')
    review = require_transition(path, digest, root)
    # Legacy readers prevent posting new-family fixture receipts early. Once
    # migrated, every already-incurred pending charge must enter the ledger
    # before any extension-runtime study can start.
    latest = limits.budgets(root)
    for key, pending in review['pending_preparation'].items():
        row = latest[key]
        if row['family'] != pending['family'] or row['preparation_cpu_seconds'] < finite(pending['minimum_cpu_seconds']):
            raise ValueError('Pending preparation charges not fully posted')
        if any(row['evidence_pins'].get(p) != h for p,h in pending['evidence_pins'].items()):
            raise ValueError('Pending preparation evidence omitted')
    return review

def admission(plan, at=None, resources=None, lock_path=SHARED_LOCK,
              budget_root=ROOT, occupied=None, logical=None):
    runtime_contract(plan)
    require_new_family_transition(plan, budget_root)
    sealed_fixture_contract(plan)
    if plan.get('operating_gear') != 2: raise ValueError('Explicit CPU-only Gear 2 required')
    at=at or datetime.now(timezone.utc)
    if at.tzinfo is None or not OPEN<=at<FREEZE: raise RuntimeError('Week 6 no-new-start boundary')
    limits.require_predecessor_drain(plan,at,lease_paths())
    if plan.get('campaign')!='S15-WEEK6' or plan.get('family') not in FAMILY_CEILINGS:
        raise ValueError('Explicit Week 6 campaign and family required')
    if plan.get('paid') or plan.get('gpu') or plan.get('ollama'):
        raise ValueError('Week 6 is CPU-only without paid or Ollama calls')
    if plan.get('numerical_threads') not in (1,2): raise ValueError('At most two numerical threads')
    if (os.cpu_count() if logical is None else logical)<24: raise RuntimeError('Eight-slot allocation requires the declared host capacity')
    for key in ('case_and_check','smaller_route'):
        if not plan.get('premortem',{}).get(key): raise ValueError('Two-line pre-mortem required')
    for key in ('max_cpu_seconds','max_wall_seconds','projected_peak_ram_GiB'):
        finite(plan[key],True)
    if plan.get('forecast_cpu_seconds',0)>7200 and plan.get('pilot_fraction')!=0.05:
        raise ValueError('Checkpointed first-five-percent in-slot pilot required')
    if not plan.get('fixture_passed') or not plan.get('reviewed_design_commit'):
        raise ValueError('Reviewed committed design and passed native fixture required')
    snapshot=resource_snapshot() if resources is None else dict(resources)
    if any(snapshot[k]<v for k,v in [('ram_available_GiB',6),('commit_headroom_GiB',8),('disk_free_GiB',20)]):
        raise RuntimeError('CPU resource floor')
    paths=lease_paths() if occupied is None else occupied
    shared=shared_reservation(lock_path,at)
    if len(paths)>=8-int(shared['active']): raise RuntimeError('Counted CPU slots occupied')
    needed=finite(plan['projected_peak_ram_GiB'],True)+memory_reserve(paths)+6.0 # reserve one reviewed companion handoff peak
    if needed>min(snapshot['ram_available_GiB'],snapshot['commit_headroom_GiB'])-8: raise RuntimeError('Projected concurrent peak leaves less than eight GiB')
    room=available(plan,budget_root,exclude=plan.get('attempt_root'))
    if room<=30: raise RuntimeError('Family or campaign CPU allowance exhausted')
    budget=limits.plan_budget(plan,budget_root)
    current=sum(charges(budget_root,exclude=plan.get('attempt_root'),card_key=plan['budget_key']).values())
    return dict(at=at.isoformat(),campaign='S15-WEEK6',resources=snapshot,slots=8-int(shared['active']),
                allowance_mode=budget['allowance_mode'],budget_receipt=budget['bound_receipt'],
                budget_receipt_sha256=budget['bound_receipt_sha256'],budget_revision=budget['bound_revision'],
                original_ceiling_cpu_seconds=budget['ceiling_cpu_seconds'],
                effective_ceiling_cpu_seconds=budget['effective_ceiling_cpu_seconds'],
                prior_campaign_cpu_seconds=budget['prior_campaign_cpu_seconds'],
                current_campaign_card_cpu_seconds=current,
                cumulative_card_cpu_seconds=budget['prior_campaign_cpu_seconds']+current,
                cumulative_preparation_cpu_seconds=budget['preparation_cpu_seconds'],
                idle_slots_before_claim=8-int(shared['active'])-len(paths),
                shared_reservation=shared,projected_peak_ram_GiB=plan['projected_peak_ram_GiB'],
                remaining_cpu_seconds=room-30,drain_utc=DRAIN.isoformat(),no_new_start_utc=FREEZE.isoformat())

def yield_reason(root,plan,resources=None):
    if datetime.now(timezone.utc)>=DRAIN: return 'week6_drain'
    if resources and any(resources[k]<v for k,v in [('ram_available_GiB',4),('commit_headroom_GiB',6),('disk_free_GiB',20)]):
        return 'resource_floor'
    if (Path(root)/'output/CANCEL_REQUEST.json').exists(): return 'owner_cancel'
    return None


def post_claim():
    """Close the race with the companion's exclusive-file, post-count protocol."""
    paths=lease_paths(); shared=shared_reservation()
    if len(paths)>8-int(shared['active']): raise RuntimeError('Post-claim counted capacity exceeded')
    snapshot=resource_snapshot()
    needed=memory_reserve(paths)+6.0
    if needed>min(snapshot['ram_available_GiB'],snapshot['commit_headroom_GiB'])-8:
        raise RuntimeError('Post-claim projected memory or companion handoff reserve')
    if snapshot['disk_free_GiB']<20: raise RuntimeError('Post-claim disk floor')
    return snapshot
