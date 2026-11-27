"""Dispatch reviewed Week 8 Spark jobs as soon as the shared Gear 2 floors allow."""
from datetime import datetime,timezone
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runners.drive.cards import week8_gear as gear
from runners.stage14.common import atomic, now, read
from runners.stage9.process_identity import native_identity
from tools.week8_queue import STATE,ROWS

TRAITS=('agreeableness','neuroticism','extraversion','conscientiousness','openness')
CONTROL='SLD6-wave2-shuffle'
SLOT_COST=.5  # Workstation launcher only. The installed Spark job has its own CPU and memory limits.
SHARED=STATE/'spark-queue'


def when():
    return datetime.now(timezone.utc)


def headroom():
    leases=gear.resources.lease_paths()
    s=gear.resource_snapshot()
    projected=gear.resources.memory_reserve(leases)+SLOT_COST+6
    available=min(s['ram_available_GiB'],s['commit_headroom_GiB'])
    if len(leases)>=gear.shared_slot_limit():return 'Shared slots occupied'
    if s['ram_available_GiB']<6 or s['disk_free_GiB']<20:return 'Host start floor'
    if projected>available-8:return 'Shared memory floor including companion headroom'
    return None


def native_code(unit):
    """Read only the previously submitted job's authenticated status fields."""
    job=gear.ROOT/unit
    submitted=read(job/'SUBMITTED.json')
    name=submitted['job']
    if not re.fullmatch(r'w8-[a-z0-9-]+',name) or name!='w8-'+unit.lower():
        raise ValueError('Submitted name changed')
    rec=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','spark',
         "grep -F 'name="+name+" ' /var/log/sealed-runs.log | cut -d' ' -f1-5,7"],capture_output=True,text=True)
    evidence=rec.stdout.strip()
    match=re.fullmatch(r'\S+ name='+re.escape(name)+r' source=\S+ job='+re.escape(submitted['entry'][:16])+r' exit=(\d+) gate=(\w+)',evidence)
    if rec.returncode or not match:return None
    out=dict(native=int(match[1]),gate=match[2],receipt=evidence)
    atomic(SHARED/(unit+'.native.json'),out)
    return out['native']


def ordered():
    rows=[]
    for p in (STATE/'reviews').glob('*.json'):
        q=read(p)
        if 'tables' not in q or not q.get('fixture_gate_passed') or q['unit']!=p.stem:continue
        rows.append((p.stem,q))
    def key(item):
        unit,q=item
        tail=unit.removeprefix('SLD6-wave2-')
        rank=TRAITS.index(tail) if tail in TRAITS else 10
        return (list(ROWS).index(q['card']),rank,unit)
    return sorted(rows,key=key)


def next_job():
    for unit,q in ordered():
        d=gear.ROOT/unit
        if d.exists() or (SHARED/(unit+'.hold.json')).exists():continue
        if q.get('not_before') and when()<datetime.fromisoformat(q['not_before']):continue
        if q['card']=='SLD6' and unit.startswith('SLD6-wave2-') and unit!='SLD6-wave2-structure':
            stopped=False
            for t in TRAITS:
                previous='SLD6-wave2-'+t
                failed=gear.ROOT/previous/'FAILED.json'
                if not failed.exists():continue
                proof=SHARED/(previous+'.native.json')
                if not proof.exists() or read(proof)['native']!=12:stopped=True
            if stopped:continue
            if unit==CONTROL and not any((gear.ROOT/('SLD6-wave2-'+t)/'COMPLETE.json').is_file() for t in TRAITS):
                continue
        return unit
    return None


def run():
    import msvcrt
    SHARED.mkdir(parents=True,exist_ok=True)
    with (SHARED/'owner.lock').open('a+b') as guard:
        if not guard.tell():guard.write(b'x');guard.flush()
        guard.seek(0);msvcrt.locking(guard.fileno(),msvcrt.LK_NBLCK,1)
        atomic(SHARED/'OWNER.json',dict(at=now(),native=native_identity(),freeze=gear.FREEZE.isoformat()))
        shell=shutil.which('pwsh')
        if not shell:raise RuntimeError('PowerShell unavailable')
        last=None
        while when()<gear.FREEZE:
            unit=next_job()
            reason=headroom() if unit else 'No reviewed unsubmitted unit'
            status=(unit,reason)
            if status!=last:
                atomic(SHARED/'STATUS.json',dict(at=now(),unit=unit,reason=reason))
                last=status
            if reason:
                time.sleep(min(30,max(0,(gear.FREEZE-when()).total_seconds())))
                continue
            logfile=SHARED/(unit+'.log')
            with logfile.open('ab') as out:
                rc=subprocess.run([shell,'-NoProfile','-File',str(ROOT/'tools/week8_spark.ps1'),'-Unit',unit],
                                  cwd=ROOT,stdout=out,stderr=subprocess.STDOUT).returncode
            job=gear.ROOT/unit
            if (job/'FAILED.json').exists():
                if (job/'SUBMITTED.json').exists():native_code(unit)
            elif rc and not (job/'RESERVATION.json').exists():
                tail=logfile.read_bytes()[-6500:].decode('utf8','replace')
                recoverable=any(s in tail for s in ('companion handoff reserve','headroom','slots occupied',
                     'shared lane','Post-claim counted capacity','Shared reservation changed','All slots claimed'))
                if not recoverable:
                    atomic(SHARED/(unit+'.hold.json'),dict(at=now(),reason='Unsubmitted admission needs owner inspection'))
                time.sleep(30)
            last=None
        atomic(SHARED/'FROZEN.json',dict(at=now(),reason='Week 8 start freeze'))


if __name__=='__main__':
    run()
