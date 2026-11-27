"""Count the 21 Week 8 rows against DH using the shared CPU-only slot banks.

DESIGN CHECK (LESSONS §§3–5). With no work the ledger starts at zero.
An active reservation counts in full across sources of the same row. Reject a
changed input, a foreign ledger, an exhausted allowance or a start at freeze.
"""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path

from . import batch_runtime_v8 as kernel
from . import week6_policy_services_v5 as resources
from .batch_runtime import REPO, filehash, freeze, native_identity, release_slot, resource_snapshot
from .week7_gear import read

CAMPAIGN = 'S15-WEEK8'
ROOT = REPO / 'results/phase_2_4_stage_15/raw/drive-week8-20261127'
AUTHORITY = REPO / 'docs/design/stage-15/week8/PACKET.md'
PACKET_SHA256 = '4e17127ff1b0dfac84289290356d4d72e2c22a3e7b9e5f43d73fe1c195025da3'
OPEN = datetime(2026, 11, 27, 14, 50, tzinfo=timezone.utc)
FREEZE = datetime(2026, 11, 29, 16, tzinfo=timezone.utc)
DRAIN = datetime(2026, 11, 29, 18, tzinfo=timezone.utc)
FINAL = datetime(2026, 11, 29, 19, tzinfo=timezone.utc)
CEILING = 2_000_000
SEALED_LIMIT = 30
CARDS = frozenset('TMP2 SLD5 SLD6 LKG1 LKG2 TMP3 LGH6 RML1 ACC1 ADP1 SLD7 SLD8 SLD9 MNG1 LGH7 ATL2 LAG2 TWO3 DRV1 ADM2 BMP1'.split())
ROW_LIMITS = dict.fromkeys(CARDS, 20_000)
ROW_LIMITS.update(LGH6=200_000, RML1=200_000, LAG2=60_000)


def shared_slot_limit(at=None, path=resources.SHARED_LOCK):
    at = at or datetime.now(timezone.utc)
    if not resources.present(path):
        return 8
    reservation = resources.read(path)
    if not reservation.get('expires_at'):
        return 8
    created = resources.instant(reservation['created_at'])
    expires = resources.instant(reservation['expires_at'])
    if created > at or expires <= created:
        raise ValueError('Invalid shared reservation clock')
    return 7 if at < min(created + timedelta(hours=6), expires) else 8


def balance(root=ROOT):
    total = 0.
    by_row = {}
    calls = 0
    for ref in root.glob('*/RESERVATION.json'):
        res = read(ref)
        if res['campaign'] != CAMPAIGN or res['card'] not in CARDS:
            raise ValueError('Foreign reservation on Week 8 ledger')
        charge = res['reserved_cpu_seconds']
        cost = ref.with_name('COST.json')
        settled = read(cost) if cost.is_file() else {}
        if settled:
            if settled['reservation_sha256'] != filehash(ref):
                raise ValueError('Mismatched cost receipt')
            charge = settled['charged_cpu_seconds']
        if not math.isfinite(charge) or not 0 <= charge <= res['reserved_cpu_seconds'] <= ROW_LIMITS[res['card']]:
            raise ValueError('Invalid Week 8 charge')
        if res['sealed'] and not settled.get('never_submitted'):
            calls += 1
        by_row[res['card']] = by_row.get(res['card'], 0.) + charge
        total += charge
    return total, by_row, calls


@contextmanager
def admit(directory, *, card, source, requested, peak, sealed, pins):
    if directory.parent != ROOT or card not in CARDS or not 0 < requested <= ROW_LIMITS[card]:
        raise ValueError('Invalid admission or row allowance')
    if not math.isfinite(peak) or peak <= 0 or pins.get(str(AUTHORITY)) != PACKET_SHA256:
        raise ValueError('Missing authority or resource inputs')
    owner = native_identity()
    lease = None
    try:
        with kernel.admission_lock(resources.OLD_SLOTS):
            now = datetime.now(timezone.utc)
            if not OPEN <= now < FREEZE:
                raise RuntimeError('Outside Week 8 start window')
            if directory.exists():
                raise FileExistsError(directory)
            for path, digest in pins.items():
                if filehash(path) != digest:
                    raise ValueError('Reviewed input changed: ' + str(path))
            total, rows, calls = balance()
            if total + requested > CEILING or rows.get(card, 0) + requested > ROW_LIMITS[card]:
                raise RuntimeError('Week 8 CPU allowance exhausted')
            if sealed and calls >= SEALED_LIMIT:
                raise RuntimeError('Week 8 sealed allowance exhausted')
            paths = resources.lease_paths()
            if len(paths) >= shared_slot_limit(now):
                raise RuntimeError('Shared slots occupied')
            snap = resource_snapshot()
            less = min(snap['ram_available_GiB'], snap['commit_headroom_GiB'])
            if (snap['ram_available_GiB'] < 6 or snap['disk_free_GiB'] < 20 or
                    resources.memory_reserve(paths) + peak > less - 8):
                raise RuntimeError('Shared resource headroom below start floors')
            record = dict(native=owner, card=card, family='W8', at=now.isoformat(), runtime='week8-gear2',
                          attempt_root=str(directory), projected_peak_ram_GiB=peak)
            for number in (4, 5, 6, 7, 0, 1, 2, 3):
                bank = resources.NEW_SLOTS if number >= 4 else resources.OLD_SLOTS
                bank.mkdir(exist_ok=True)
                slot = bank / f'slot-{number}.json'
                try:
                    with slot.open('x', encoding='utf8') as stream:
                        json.dump(record, stream)
                except FileExistsError:
                    continue
                lease = slot, record
                break
            if lease is None:
                raise RuntimeError('All slots claimed')
            resources.post_claim()
            if len(resources.lease_paths()) > shared_slot_limit():
                raise RuntimeError('Shared reservation changed during admission')
            directory.mkdir(parents=True, exist_ok=False)
            freeze(directory/'RESERVATION.json', dict(campaign=CAMPAIGN, card=card, source=source,
                   reserved_cpu_seconds=requested, row_cpu_limit=ROW_LIMITS[card], cap_cpu=CEILING,
                   sealed=sealed, slot=slot.name, native=owner, at=now.isoformat(), resources=snap,
                   pins=pins, threads=2))
        yield
    finally:
        if lease is not None:
            release_slot(*lease)


def settle(directory, charge, basis, never_submitted=False):
    with kernel.admission_lock(resources.OLD_SLOTS):
        ref = directory/'RESERVATION.json'
        res = read(ref)
        if directory.parent != ROOT or res['campaign'] != CAMPAIGN:
            raise ValueError('Foreign reservation')
        if not math.isfinite(charge) or not 0 <= charge <= res['reserved_cpu_seconds']:
            raise ValueError('Invalid cost')
        if never_submitted and (directory/'SUBMITTED.json').exists():
            raise ValueError('Submission already recorded')
        freeze(directory/'COST.json', dict(at=datetime.now(timezone.utc).isoformat(), reservation_sha256=filehash(ref),
               charged_cpu_seconds=charge, basis=basis, never_submitted=never_submitted))
