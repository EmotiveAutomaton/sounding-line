"""CPU-only theory-days admission; no automatic scientific selection.

DESIGN CHECK: LESSONS 3-5. Null/alternative receive identical resource gates.
Missing accounting, invalid pins, overcommit or expired windows refuse, never
become scientific nulls. Campaign reservations include independent replay.
"""
from datetime import datetime, timezone
from pathlib import Path
import math
from runners.drive.cards import week4_policy as old
from runners.stage14.common import REPO, read

OPEN = datetime.fromisoformat('2026-11-06T15:00:00+00:00')
FREEZE = datetime.fromisoformat('2026-11-08T03:00:00+00:00')
DRAIN = datetime.fromisoformat('2026-11-08T15:00:00+00:00')
ROOT = REPO/'results/phase_2_4_stage_15/raw/theory-days-20261106'
CEILING = 54000.0
BUILD_RESERVE = 300.0


def campaign_charge(root=ROOT):
    """Reserve full caps for unfinished plans; never credit ambiguous exits."""
    total = BUILD_RESERVE
    for path in Path(root).glob('*/PLAN.json'):
        plan = read(path)
        cap = float(plan['max_cpu_seconds'])
        if not math.isfinite(cap) or cap <= 0:
            raise ValueError('Invalid reservation')
        terminals = [path.parent/name for name in ('COMPLETE.json','FAILED.json','PAUSED.json')
                     if (path.parent/name).exists()]
        if len(terminals) > 1:
            raise ValueError('Ambiguous terminal accounting')
        if terminals:
            value = read(terminals[0]).get('cpu_seconds')
            if type(value) not in (int,float) or not math.isfinite(value) or value < 0:
                raise ValueError('Missing terminal CPU charge')
            cap = value
        # Coordinator, source capsule and launcher CPU are conservatively reserved.
        total += cap + 30.0
    return total


def admission(plan, at=None, resources=None, lock_path=old.SHARED_LOCK,
              logical=None, budget_root=ROOT):
    at = datetime.now(timezone.utc) if at is None else at
    if at.tzinfo is None or not OPEN <= at < FREEZE:
        raise RuntimeError('Theory-days no-new-start boundary')
    if plan.get('campaign') != 'S15-THEORY-DAYS' or plan.get('numerical_threads') != 1:
        raise ValueError('Explicit CPU-only theory-days single-thread plan required')
    if plan.get('paid') or plan.get('gpu'):
        raise ValueError('No paid/GPU work in this campaign')
    adjusted = dict(plan, campaign='S15-WEEK4')
    # Reuse resource floors and the existing shared-machine reservation, with
    # only the original campaign's clock replaced by our narrower clock above.
    result = old.admission(adjusted, at=at, resources=resources,
                           lock_path=lock_path, logical=logical)
    charge = campaign_charge(budget_root)
    if charge > CEILING:
        raise RuntimeError('Theory-days total CPU reservations exceed 15 hours')
    if plan['forecast_cpu_seconds'] > plan['max_cpu_seconds']:
        raise ValueError('Forecast exceeds reserved complete execution/replay')
    return dict(result, drain_utc=DRAIN.isoformat(), no_new_start_utc=FREEZE.isoformat(),
                campaign_cpu_reserved_seconds=charge, campaign='S15-THEORY-DAYS')


def yield_reason(root, plan, resources=None):
    if datetime.now(timezone.utc) >= DRAIN:
        return 'theory_days_drain'
    return old.yield_reason(root, plan, resources)
