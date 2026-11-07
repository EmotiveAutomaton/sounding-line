"""Independent Week 5 CPU policy; inherited campaigns retain their own clocks.

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
from .batch_runtime import REPO, read, resource_snapshot

OPEN = datetime.fromisoformat('2026-11-07T18:00:00+00:00')
FREEZE = datetime.fromisoformat('2026-11-16T04:00:00+00:00')
DRAIN = datetime.fromisoformat('2026-11-16T06:00:00+00:00')
ADDENDUM = datetime.fromisoformat('2026-11-16T07:00:00+00:00')
ROOT = REPO/'results/phase_2_4_stage_15/raw/drive-week5-20261107'
OLD_SLOTS = REPO/'results/.cpu-slots-20261017'
NEW_SLOTS = REPO/'results/.cpu-slots-20261107'
SHARED_LOCK = OLD_SLOTS/'tompathy-demo-prep.lock'
CEILING = 6_000_000.0
FAMILY_CEILINGS = dict(AT=750000, CH=2500000, IN=60000, SP=40000,
                       GO=600000, MD=34400, LA=450000, ID=40000, BK=1000000)

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
    if not Path(path).exists(): return dict(active=False,reason='absent')
    value=read(path)
    if not value.get('expires_at'): return dict(active=False,reason='missing_expiry',log_required=True)
    created, expires=instant(value['created_at']),instant(value['expires_at'])
    if created>at or expires<=created: raise ValueError('Invalid shared reservation clock')
    effective=min(expires,created+timedelta(hours=6),FREEZE)
    return dict(active=at<effective,reason='valid' if at<effective else 'expired',effective_expiry=effective.isoformat())

def charges(root=ROOT, exclude=None):
    """Count actual attempt CPU; unknown terminated attempts retain their full cap.

    Monitor progress is refreshed every two seconds. The additional two-second
    sampling envelope per active two-thread worker covers concurrent last ticks.
    """
    families={k:0.0 for k in FAMILY_CEILINGS}
    for path in Path(root).glob('*/PLAN.json'):
        if exclude and path.parent.resolve()==Path(exclude).resolve(): continue
        plan=read(path)
        if plan.get('campaign')!='S15-WEEK5': continue
        family=plan['family']
        if family not in families: raise ValueError('Unknown campaign family')
        terminals=[path.parent/n for n in ('COMPLETE.json','FAILED.json','PAUSED.json') if (path.parent/n).exists()]
        if len(terminals)>1: raise ValueError('Ambiguous terminal accounting')
        if terminals: charge=finite(read(terminals[0])['cpu_seconds'])
        elif not (path.parent/'ATTEMPT.claim').exists(): charge=0.0
        elif (path.parent/'BUDGET_PROGRESS.json').exists():
            progress=read(path.parent/'BUDGET_PROGRESS.json')
            age=(datetime.now(timezone.utc)-instant(progress['at'])).total_seconds()
            charge=finite(progress['cpu_seconds'])+4.0 if age<15 else finite(plan['max_cpu_seconds'])
        else: charge=finite(plan['max_cpu_seconds'])
        # Supervisor/launcher/replay coordination is charged conservatively.
        families[family]+=charge+(30 if (path.parent/'ATTEMPT.claim').exists() else 0)
    return families

def remaining(family, root=ROOT, exclude=None):
    used=charges(root,exclude)
    return max(0.0,min(FAMILY_CEILINGS[family]-used[family],CEILING-sum(used.values())))

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

def admission(plan, at=None, resources=None, lock_path=SHARED_LOCK,
              budget_root=ROOT, occupied=None, logical=None):
    at=at or datetime.now(timezone.utc)
    if at.tzinfo is None or not OPEN<=at<FREEZE: raise RuntimeError('Week 5 no-new-start boundary')
    if plan.get('campaign')!='S15-WEEK5' or plan.get('family') not in FAMILY_CEILINGS:
        raise ValueError('Explicit Week 5 campaign and family required')
    if plan.get('paid') or plan.get('gpu') or plan.get('ollama'):
        raise ValueError('Week 5 is CPU-only without paid or Ollama calls')
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
    needed=finite(plan['projected_peak_ram_GiB'],True)+memory_reserve(paths)
    if needed>snapshot['ram_available_GiB']-8: raise RuntimeError('Projected concurrent peak leaves less than eight GiB')
    room=remaining(plan['family'],budget_root,exclude=plan.get('attempt_root'))
    if room<=30: raise RuntimeError('Family or campaign CPU allowance exhausted')
    return dict(at=at.isoformat(),campaign='S15-WEEK5',resources=snapshot,slots=8-int(shared['active']),
                shared_reservation=shared,projected_peak_ram_GiB=plan['projected_peak_ram_GiB'],
                remaining_cpu_seconds=room-30,drain_utc=DRAIN.isoformat(),no_new_start_utc=FREEZE.isoformat())

def yield_reason(root,plan,resources=None):
    if datetime.now(timezone.utc)>=DRAIN: return 'week5_drain'
    if resources and any(resources[k]<v for k,v in [('ram_available_GiB',4),('commit_headroom_GiB',6),('disk_free_GiB',20)]):
        return 'resource_floor'
    if (Path(root)/'output/CANCEL_REQUEST.json').exists(): return 'owner_cancel'
    return None
