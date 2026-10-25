"""Week 3 admission, explicit CPU accounting and the shared ToMpathy lease.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 6-7 reread 2026-10-25. Scientific
nulls and alternatives have identical admission. Missing pins, ambiguous cost,
invalid clocks and resource shortages refuse; an expired reservation cannot
indefinitely idle the queue. No scientific result is inferred by this module.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import math

from .batch_runtime import REPO, read, resource_snapshot, slot_count

OPEN = datetime.fromisoformat('2026-10-25T19:35:00+00:00')
FREEZE = datetime.fromisoformat('2026-11-02T04:00:00+00:00')
DRAIN = datetime.fromisoformat('2026-11-02T06:00:00+00:00')
PAID_CUTOFF = datetime.fromisoformat('2026-10-31T00:00:00+00:00')
SHARED_LOCK = REPO/'results/.cpu-slots-20261017/tompathy-demo-prep.lock'


def instant(value):
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError('Explicit timezone required')
    return result.astimezone(timezone.utc)


def shared_reservation(path=SHARED_LOCK, at=None):
    at = datetime.now(timezone.utc) if at is None else at
    if at.tzinfo is None:
        raise ValueError('Explicit timezone required')
    if at >= FREEZE:
        return dict(active=False, reason='window_expired')
    if not Path(path).exists():
        return dict(active=False, reason='absent')
    value = read(path)
    if not value.get('expires_at'):
        return dict(active=False, reason='missing_expiry', log_required=True)
    created, expires = instant(value['created_at']), instant(value['expires_at'])
    if created > at or expires <= created:
        raise ValueError('Invalid shared reservation clock')
    effective = min(expires, created + timedelta(hours=6), FREEZE)
    return dict(active=at < effective, reason='valid' if at < effective else 'expired',
                effective_expiry=effective.isoformat(), log_required=at >= effective)


def costs(plan):
    keys = ('original_cpu_ceiling_seconds', 'prior_cpu_seconds_charged',
            'max_cpu_seconds', 'max_wall_seconds')
    values = [plan[k] for k in keys]
    if any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in values):
        raise ValueError('Invalid explicit CPU/wall accounting')
    original, charged, remaining, wall = values
    if min(original, remaining, wall) <= 0 or charged + remaining > 2*original:
        raise ValueError('One cumulative S4 doubling only, including verification')
    return dict(original_cpu_seconds=original, prior_cpu_seconds=charged,
                remaining_cpu_seconds=remaining, safety_wall_seconds=wall)


def admission(plan, at=None, resources=None, lock_path=SHARED_LOCK, logical=None):
    at = datetime.now(timezone.utc) if at is None else at
    if at.tzinfo is None or not OPEN <= at < FREEZE:
        raise RuntimeError('Week 3 no-new-start boundary')
    cost = costs(plan)
    if plan['forecast_cpu_seconds'] >= 7200 and not plan.get('pilot_verified'):
        raise RuntimeError('Separate measured pilot required for two-hour forecast')
    if plan.get('earliest_start_utc') and at < instant(plan['earliest_start_utc']):
        raise RuntimeError('Card earliest start has not arrived')
    snapshot = resource_snapshot() if resources is None else dict(resources)
    peak = plan['projected_peak_ram_GiB']
    if type(peak) not in (int, float) or not math.isfinite(peak) or peak <= 0:
        raise ValueError('Positive projected peak memory required')
    if snapshot['ram_available_GiB'] < 6 or snapshot['commit_headroom_GiB'] < 8 or snapshot['disk_free_GiB'] < 20:
        raise RuntimeError('CPU resource floor')
    shared = shared_reservation(lock_path, at)
    if shared['active'] and snapshot['ram_available_GiB'] - peak < 8:
        raise RuntimeError('ToMpathy needs eight GiB after this card peak')
    return dict(at=at.isoformat(), resources=snapshot, shared_reservation=shared,
                slots=slot_count(logical)-int(shared['active']),
                projected_peak_ram_GiB=peak, drain_utc=DRAIN.isoformat(),
                no_new_start_utc=FREEZE.isoformat(), **cost)


def yield_reason(root, plan, resources=None):
    if resources is not None and (resources['ram_available_GiB'] < 4 or resources['commit_headroom_GiB'] < 6 or resources['disk_free_GiB'] < 20):
        return 'resource_floor'
    if datetime.now(timezone.utc) >= DRAIN:
        return 'week_drain'
    marker = root/'output/FIRST_TENTH.json'
    if marker.exists():
        record = read(marker)
        projection = record.get('projected_cpu_seconds')
        if projection is not None:
            if not math.isfinite(projection) or projection <= 0:
                raise ValueError('Invalid CPU projection')
            if plan['prior_cpu_seconds_charged'] + projection > 2*plan['original_cpu_ceiling_seconds']:
                return 'cpu_projection_above_cumulative_S4_cap'
    return None
