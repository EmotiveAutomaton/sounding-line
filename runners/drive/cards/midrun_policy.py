"""October 18 owner policy; does not select research or restart workers.

DESIGN CHECK: LESSONS 3-5 read 2026-10-18. NULL/ALTERNATIVE outcomes
cannot change resources, pins or eligibility. A forecast can yield only to a
fresh, owner-reviewed runnable successor; sub-two-hour projections continue.
Missing/stale waiting evidence never invents a successor. Safety yields remain.
Only documented environmental causes escape the single engineering retry.
"""
from __future__ import annotations

from datetime import datetime
import math

from .batch_runtime import read, filehash


def forecast_yield(projection, forecast, runnable_waiting):
    if not all(math.isfinite(x) and x > 0 for x in (projection, forecast)):
        raise ValueError('Invalid forecast or projection')
    return projection >= 7200 and projection > 2 * forecast and runnable_waiting


def reviewed_waiter(path, now):
    """A short owner-issued scheduling lease, bound to an executable plan."""
    if not path.exists():
        return False
    value = read(path)
    if datetime.fromisoformat(value['expires_at']) <= now:
        return False
    return (value.get('reviewed') is True and value.get('runnable') is True
            and value.get('waiting_for_slot') is True
            and filehash(value['plan_path']) == value['plan_sha256'])


def environmental_evidence(kind, evidence):
    if kind in {'memory_guard', 'temperature_guard'}:
        return isinstance(evidence.get('sample'), dict) and bool(evidence['sample'])
    if kind == 'os_refusal':
        return evidence.get('winerror') in {5, 32, 33} and bool(evidence.get('traceback_sha256'))
    if kind in {'sleep', 'power_loss', 'reboot', 'disk_exhaustion'}:
        return bool(evidence.get('system_receipt_sha256'))
    return False


def yield_reason(root, plan, resources=None):
    if resources is not None and (resources['ram_available_GiB'] < 4
            or resources['commit_headroom_GiB'] < 6 or resources['disk_free_GiB'] < 20):
        return 'resource_floor_yield'
    marker = root / 'output/FIRST_TENTH.json'
    if marker.exists() and not (root / 'FORECAST_YIELD_SATISFIED.json').exists():
        value = read(marker)
        projection = value.get('projected_cpu_seconds', value.get('projected_seconds'))
        if projection is None:
            raise ValueError('First-tenth projection missing')
        # P7-D33 has an explicit continuation exception in errata section 2.3.
        if plan.get('card') == 'P7-D33':
            return None
        from .batch_runtime import REPO
        waiting = reviewed_waiter(REPO / '.agent-state/drive-20261017/RUNNABLE_WAITING.json',
                                  datetime.now().astimezone())
        if forecast_yield(projection, plan['forecast_cpu_seconds'], waiting):
            return 'reviewed_runnable_successor_waiting'
    return None
