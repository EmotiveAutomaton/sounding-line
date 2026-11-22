"""Shared Windows admission for Week 7. Costs and terminals belong to Week 7 only."""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import json
import math
import time

from . import batch_runtime_v8 as kernel
from . import week6_policy_services_v5 as resources
from .batch_runtime import REPO, filehash, freeze, native_identity, release_slot, resource_snapshot


ROOT = REPO / 'results/phase_2_4_stage_15/raw/drive-week7-20261122'
AUTHORITY = REPO / 'docs/design/stage-15/week7/CK_EARLY_OPEN.md'
OPEN = datetime(2026, 11, 22, 23, 30, tzinfo=timezone.utc)
FREEZE = datetime(2026, 11, 27, 4, tzinfo=timezone.utc)
DRAIN = datetime(2026, 11, 27, 6, tzinfo=timezone.utc)
CEILING = 6_000_000
SEALED_LIMIT = 30


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def balance(root=ROOT):
    total = 0.
    by_row = {}
    invocations = 0
    for directory in root.iterdir() if root.exists() else ():
        reference = directory / 'RESERVATION.json'
        if not reference.is_file():
            continue
        reservation = read(reference)
        if reservation['campaign'] != 'S15-WEEK7':
            raise ValueError('Foreign reservation on Week 7 ledger')
        charge = reservation['reserved_cpu_seconds']
        terminal = directory / 'COST.json'
        if terminal.is_file():
            settled = read(terminal)
            if settled['reservation_sha256'] != filehash(reference):
                raise ValueError('Mismatched cost receipt')
            charge = settled['charged_cpu_seconds']
        if not math.isfinite(charge) or not 0 <= charge <= reservation['reserved_cpu_seconds']:
            raise ValueError('Invalid CPU charge')
        key = (reservation['card'], reservation['source'])
        by_row[key] = by_row.get(key, 0.) + charge
        total += charge
        # Reserve an invocation until the client proves it stopped before submitting.
        if reservation['sealed'] and not (terminal.is_file() and settled.get('never_submitted')):
            invocations += 1
    return total, by_row, invocations


@contextmanager
def admit(directory, *, card, source, requested, row_limit, peak, sealed, pins):
    if directory.parent != ROOT or row_limit != (200000 if card in {'LGH1','CRV1'} else 20000):
        raise ValueError('Wrong Week 7 directory or row allowance')
    if not 0 < requested <= row_limit or not 0 < peak or not pins or str(AUTHORITY) not in pins:
        raise ValueError('Missing admission inputs')
    owner = native_identity()
    lease = None
    try:
        with kernel.admission_lock(resources.OLD_SLOTS):
            now = datetime.now(timezone.utc)
            if not OPEN <= now < FREEZE:
                raise RuntimeError('Outside the Week 7 start window')
            for path, digest in pins.items():
                if filehash(path) != digest:
                    raise ValueError('Reviewed input changed: '+str(path))
            used, rows, calls = balance()
            if used+requested > CEILING or rows.get((card, source), 0)+requested > row_limit:
                raise RuntimeError('Week 7 CPU allowance exhausted')
            if sealed and calls >= SEALED_LIMIT:
                raise RuntimeError('Week 7 sealed allowance exhausted')
            paths = resources.lease_paths()
            snapshot = resource_snapshot()
            if len(paths) >= 8-int(resources.shared_reservation()['active']):
                raise RuntimeError('Shared slots occupied')
            if (snapshot['ram_available_GiB'] < 6 or snapshot['commit_headroom_GiB'] < 8
                    or snapshot['disk_free_GiB'] < 20 or resources.memory_reserve(paths)+peak >
                    min(snapshot['ram_available_GiB'],snapshot['commit_headroom_GiB'])-8):
                raise RuntimeError('Shared resource headroom below start floors')
            directory.mkdir(parents=True,exist_ok=False)
            stamp = now.isoformat()
            record = dict(native=owner,card=card,family='W7',at=stamp,runtime='week7-gear2',
                          attempt_root=str(directory),projected_peak_ram_GiB=peak)
            for number in (4,5,6,7,0,1,2,3):
                bank = resources.NEW_SLOTS if number >= 4 else resources.OLD_SLOTS
                bank.mkdir(exist_ok=True)
                slot = bank/f'slot-{number}.json'
                try:
                    with slot.open('x',encoding='utf8') as stream:
                        json.dump(record, stream)
                except FileExistsError:
                    continue
                lease = slot, record
                break
            if lease is None:
                raise RuntimeError('All slots claimed')
            resources.post_claim()
            freeze(directory/'RESERVATION.json',dict(campaign='S15-WEEK7',card=card,source=source,
                reserved_cpu_seconds=requested,row_cpu_limit=row_limit,cap_cpu=CEILING,sealed=sealed,
                ordinal=calls+1 if sealed else None,slot=slot.name,native=owner,at=stamp,resources=snapshot,
                threads=2,pins=pins))
        yield
    finally:
        if lease is not None:
            release_slot(*lease)


def settle(directory, charge, basis, never_submitted=False):
    with kernel.admission_lock(resources.OLD_SLOTS):
        reservation=directory/'RESERVATION.json'
        if not math.isfinite(charge) or not 0 <= charge <= read(reservation)['reserved_cpu_seconds']:
            raise ValueError('Charge outside reservation')
        if never_submitted and (directory/'SUBMITTED.json').exists():
            raise ValueError('Submission already recorded')
        freeze(directory/'COST.json',dict(at=datetime.now(timezone.utc).isoformat(),
            reservation_sha256=filehash(reservation),charged_cpu_seconds=charge,
            basis=basis,never_submitted=never_submitted))
