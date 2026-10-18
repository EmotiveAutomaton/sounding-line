"""Prospective October18-25 CPU admission; never mutates a live old plan.

DESIGN CHECK: LESSONS3-5. Null/alternative outcomes cannot affect dispatch.
Exact cutoffs, invalid cost units, unknown peaks and changed completion evidence
fail closed. A yield is operational, not a null. Costs may double once only.
"""
from datetime import datetime, timezone
import math
from pathlib import Path

from .batch_runtime import REPO, read, filehash, resource_snapshot, slot_count


def instant(value):
    return datetime.fromisoformat(value).astimezone(timezone.utc)


OPEN = instant('2026-10-18T00:00:00-07:00')
FREEZE = instant('2026-10-21T06:00:00-07:00')
DRAIN = instant('2026-10-21T12:00:00-07:00')
REOPEN = instant('2026-10-22T07:00:00-07:00')
FINAL_FREEZE = instant('2026-10-25T20:00:00-07:00')
FINAL_DRAIN = instant('2026-10-25T22:00:00-07:00')
DEMO_END = instant('2026-10-20T20:00:00-07:00')


def window(at):
    if at.tzinfo is None:
        raise ValueError('Explicit timezone required')
    if OPEN <= at < FREEZE:
        return 'pre-talk', FREEZE, DRAIN
    if REOPEN <= at < FINAL_FREEZE:
        return 'post-talk', FINAL_FREEZE, FINAL_DRAIN
    raise RuntimeError('Week no-new-start boundary')


def demo_reserved(plan, at):
    if at >= DEMO_END:
        return False
    receipt = plan.get('demo_completion_receipt')
    if receipt:
        expected = plan['pins'].get(str(Path(receipt)))
        if not expected or filehash(receipt) != expected:
            raise ValueError('Demo completion receipt is not pinned')
        if read(receipt).get('availableModulesComplete') is True:
            return False
    # Missing shared handoff lock is not evidence that the reservation ended.
    return True


def cost(plan):
    original = plan['original_wall_ceiling_seconds']
    charged = plan.get('prior_wall_seconds_charged', 0)
    allowance = plan['max_wall_seconds']
    if any(not math.isfinite(x) for x in (original, charged, allowance)) or original <= 0 or charged < 0 or allowance <= 0:
        raise ValueError('Invalid original/charged/remaining wall cost')
    if charged + allowance > 2 * original:
        raise ValueError('S4 original ceiling may double only once, including replay and prior work')
    return original, charged, allowance


def admission(plan, at=None, resources=None):
    at = datetime.now(timezone.utc) if at is None else at
    name, freeze, drain = window(at)
    original, charged, allowance = cost(plan)
    if plan['forecast_cpu_seconds'] >= 7200 and not plan.get('pilot_verified'):
        raise RuntimeError('Separate measured pilot required')
    if plan.get('week_window', name) != name:
        raise RuntimeError('Card is outside its registered week window')
    if plan.get('earliest_start_utc') and at < instant(plan['earliest_start_utc']):
        raise RuntimeError('Card earliest start has not arrived')
    snapshot = resource_snapshot() if resources is None else dict(resources)
    if snapshot['ram_available_GiB'] < 6 or snapshot['commit_headroom_GiB'] < 8 or snapshot['disk_free_GiB'] < 20:
        raise RuntimeError('New CPU start below RAM/commit/disk floor')
    reserved = demo_reserved(plan, at)
    peak = 4.0
    if plan.get('peak_memory_receipt'):
        path = plan['peak_memory_receipt']
        if plan['pins'].get(str(Path(path))) != filehash(path):
            raise ValueError('Measured memory receipt is not pinned')
        peak = read(path)['peak_ram_GiB']
        if not math.isfinite(peak) or peak <= 0:
            raise ValueError('Invalid measured peak')
    if reserved and snapshot['ram_available_GiB'] - peak < 8:
        raise RuntimeError('Demo preparation needs 8GiB RAM after the card peak')
    return dict(resources=snapshot, week_window=name, no_new_start_utc=freeze.isoformat(),
                drain_utc=drain.isoformat(), reserved_demo_slot=reserved,
                slots=slot_count()-int(reserved), peak_ram_GiB=peak,
                original_wall_ceiling_seconds=original, prior_wall_seconds_charged=charged,
                remaining_wall_seconds=min(allowance,(drain-at).total_seconds()))


def yield_reason(root, plan, resources=None):
    if resources is not None and (resources['ram_available_GiB'] < 4 or resources['commit_headroom_GiB'] < 6 or resources['disk_free_GiB'] < 20):
        return 'resource_floor_yield'
    admitted = read(root/'ADMISSION.json')
    if datetime.now(timezone.utc) >= instant(admitted['drain_utc']):
        return 'week_drain_boundary'
    marker = root/'output/FIRST_TENTH.json'
    if marker.exists():
        value = read(marker)
        # Never compare CPU-seconds to a wall-seconds ceiling without a declared conversion.
        projection = value.get('projected_seconds')
        if projection is not None:
            if not math.isfinite(projection) or projection <= 0:
                raise ValueError('Invalid measured wall projection')
            original, charged, _ = cost(plan)
            if charged + projection > 2*original:
                return 'projected_wall_cost_above_twice_original_ceiling'
    return None
