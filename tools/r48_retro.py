"""Submit a reviewed retrospective job through the installed seal and count it separately."""
from contextlib import contextmanager
from datetime import datetime, timezone
import csv
import math
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import week8_sealed as spark, week8_spark_queue as queue
from runners.drive.cards import week8_gear as gear
from runners.stage14.common import filehash, freeze, now, read

LIMIT = 10
CAP = 1800
UNIT = 'D5s-argument-pooled-DN'
STATE = spark.STATE / 'retrospective'
RAW = gear.ROOT.parent / 'r48-backfill-20261127'
MARKERS = ('COMPLETE', 'FAILED')


def balance(root=RAW):
    reservations = 0
    for path in root.glob('*/RESERVATION.json'):
        item = read(path)
        if item['pool'] != 'R48-section-7' or item['ruling'] != gear.RULING_SHA256:
            raise ValueError('Incorrect retrospective ledger')
        settlement = path.with_name('COST.json')
        cost = read(settlement) if settlement.is_file() else None
        if cost:
            if cost['reservation'] != filehash(path) or not 0 <= cost['charged_cpu_seconds'] <= item['cap']:
                raise ValueError('Invalid retrospective settlement')
            if cost['never_submitted'] and path.with_name('SUBMITTED.json').exists():
                raise ValueError('Submission contradicts release of reservation')
        reservations += int(not (cost and cost['never_submitted']))
    if reservations > LIMIT:
        raise ValueError('Retrospective ceiling exceeded')
    return reservations


@contextmanager
def reservation(review):
    from runners.drive.cards import batch_runtime as runtime
    import json
    lease = None
    directory = RAW / UNIT
    try:
        with gear.kernel.admission_lock(gear.resources.OLD_SLOTS):
            current = datetime.now(timezone.utc)
            if not gear.OPEN <= current < gear.FREEZE or directory.exists() or balance() >= LIMIT:
                raise RuntimeError('Retrospective start unavailable')
            if queue.headroom():
                raise RuntimeError('Shared headroom unavailable')
            # Every weekly row could spend its entire allowance and every
            # retrospective call its bound without approaching the CPU ceiling.
            if sum(gear.ROW_LIMITS.values()) + LIMIT * CAP > gear.CEILING:
                raise ValueError('Combined CPU envelope needs a new accounting review')
            resource = gear.resource_snapshot()
            owner = runtime.native_identity()
            tag = dict(native=owner,card=UNIT,at=now(),projected_peak_ram_GiB=queue.SLOT_COST,
                       family='R48',attempt_root=str(directory))
            for index in (4,5,6,7,0,1,2,3):
                bank = gear.resources.NEW_SLOTS if index >= 4 else gear.resources.OLD_SLOTS
                bank.mkdir(exist_ok=True)
                slot = bank / f'slot-{index}.json'
                try:
                    with slot.open('x',encoding='utf8') as out:
                        json.dump(tag,out)
                except FileExistsError:
                    continue
                lease = slot, tag
                break
            if lease is None:
                raise RuntimeError('Shared headroom unavailable')
            gear.resources.post_claim()
            if len(gear.resources.lease_paths()) > gear.shared_slot_limit():
                raise RuntimeError('Shared headroom unavailable')
            directory.mkdir(parents=True,exist_ok=False)
            freeze(directory/'RESERVATION.json',dict(pool='R48-section-7',unit=UNIT,at=now(),
                   cap=CAP,ruling=gear.RULING_SHA256,native=owner,slot=slot.name,
                   review=filehash(review),resource=resource))
        yield directory
    finally:
        if lease:
            runtime.release_slot(*lease)


def submit():
    review = STATE/'REVIEW.json'
    q = read(review)
    entry = STATE/'run.py'
    if q['unit'] != UNIT or q['cap'] != CAP or q['source'] != 'midus-m2-joined':
        raise ValueError('Unexpected retrospective candidate')
    for path, expected in q['pins'].items():
        if filehash(Path(path)) != expected:
            raise ValueError('Changed reviewed input '+Path(path).name)
    if q['pins'].get(str(entry)) != filehash(entry) or q['ruling'] != gear.RULING_SHA256:
        raise ValueError('Missing scientific binding')
    rehearsal = Path(q['rehearsal'])
    if str(rehearsal) not in q['pins'] or read(rehearsal)['forms'] != ['fine','coarse','summary']:
        raise ValueError('Missing constructed rehearsal')
    host = read(spark.HOST)
    observed = spark.remote('sha256sum /usr/local/bin/sealed-run /usr/local/lib/sealed-gate.py').splitlines()
    if [r.split()[0] for r in observed] != [host['installed_runner_sha256'],host['installed_gate_sha256']]:
        raise ValueError('Installed route changed')
    if filehash(spark.GATE) != host['installed_gate_sha256'] or host['image_digest'] not in spark.remote('cat /srv/open/pins/sl-tabular-2026-11-16.txt').splitlines():
        raise ValueError('Image or rehearsal gate changed')
    alias = q['source']
    job = 'r48-'+UNIT.lower()
    with reservation(review) as d:
        try:
            dest='/home/agent/sealed-jobs/'+job
            spark.remote('mkdir '+dest)
            spark.exec_ok(['scp',*spark.SSH,str(entry),'spark:'+dest+'/run.py'])
            if spark.remote('sha256sum '+dest+'/run.py').split()[0] != filehash(entry):
                raise ValueError('Remote entry differs')
            freeze(d/'SUBMITTED.json',dict(at=now(),source=alias,job=job,entry=filehash(entry)))
            call=subprocess.run(['ssh',*spark.SSH,'spark','sudo -n sealed-run '+job+' '+alias],
                                capture_output=True,text=True)
            freeze(d/'EXIT.json',dict(at=now(),wrapper_exit=call.returncode))
            if call.returncode:
                raise RuntimeError('Installed runner exit '+str(call.returncode))
            match=re.search(r'(/home/agent/sealed-totals/'+re.escape(job)+r'-[0-9]{8}T[0-9]{6})\s*$',call.stdout)
            if not match or spark.remote('ls -1 '+match[1]).splitlines()!=['argument.csv']:
                raise ValueError('Unexpected gated table')
            base=match[1]+'/argument.csv'
            out=d/'gated-return'
            out.mkdir()
            path=out/'argument.csv'
            pin=spark.remote('sha256sum '+base).split()[0]
            spark.exec_ok(['scp',*spark.SSH,'spark:'+base,str(path)])
            if filehash(path)!=pin or spark.exec_ok([sys.executable,'-B','-I',str(spark.GATE),str(out)])!='gate passed':
                raise ValueError('Gated replay differs')
            with path.open(newline='') as stream:
                table=csv.DictReader(stream)
                required={'comparison','n','resampling','valid_draws','estimate','lower','upper'}
                if set(table.fieldnames or ())!=required:
                    raise ValueError('Unexpected columns')
                rows=list(table)
                if not rows or any(int(r['n'])<11 or not all(math.isfinite(float(v)) for v in r.values()) for r in rows):
                    raise ValueError('Invalid released rows')
            terminal='COMPLETE'
            record=dict(at=now(),unit=UNIT,aggregate_sha256=pin)
        except Exception as exc:
            terminal='FAILED'
            record=dict(at=now(),unit=UNIT,reason=str(exc) if isinstance(exc,ValueError) else type(exc).__name__)
        submitted=(d/'SUBMITTED.json').exists()
        freeze(d/'COST.json',dict(at=now(),reservation=filehash(d/'RESERVATION.json'),
               never_submitted=not submitted,charged_cpu_seconds=CAP if submitted else 0))
        freeze(d/(terminal+'.json'),record)
        if terminal!='COMPLETE':
            raise RuntimeError('Retrospective job needs disposition')


if __name__=='__main__':
    if sys.argv[1:]==['balance']:
        print(balance())
    elif sys.argv[1:]==['eligible']:
        # Weekly starts have first use of this serial Spark lane.
        ok = not (RAW/UNIT).exists() and balance()<LIMIT and not queue.headroom() and queue.next_job() is None
        sys.exit(0 if ok else 3)
    elif sys.argv[1:]==['submit']:
        submit()
    else:
        raise SystemExit('Expected balance, eligible or submit')
