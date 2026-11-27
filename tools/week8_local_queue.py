"""Start each reviewed local Week 8 unit when the existing Gear 2 admission permits."""
from datetime import datetime, timezone
import msvcrt
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runners.drive.cards import week8_gear as gear
from runners.stage14.common import atomic, now, read
from runners.stage9.process_identity import native_identity
from tools.week8_queue import ROWS, STATE

BASE=STATE/'local-queue'


def permits(q):
    leases=gear.resources.lease_paths()
    s=gear.resource_snapshot()
    available=min(s['ram_available_GiB'],s['commit_headroom_GiB'])
    if len(leases)>=gear.shared_slot_limit():return 'Shared slots occupied'
    if s['disk_free_GiB']<20 or s['ram_available_GiB']<6:return 'Disk or memory start floor'
    if gear.resources.memory_reserve(leases)+q['peak']+6>available-8:return 'Shared memory floor including companion headroom'
    total, by_row, _=gear.balance()
    if total+q['cap']>gear.CEILING or by_row.get(q['card'],0)+q['cap']>gear.ROW_LIMITS[q['card']]:
        return 'Campaign or row allowance'
    return None


def run():
    BASE.mkdir(exist_ok=True,parents=True)
    with (BASE/'owner.lock').open('a+b') as guard:
        if not guard.tell():guard.write(b'x');guard.flush()
        guard.seek(0);msvcrt.locking(guard.fileno(),msvcrt.LK_NBLCK,1)
        atomic(BASE/'OWNER.json',dict(native=native_identity(),at=now(),freeze=gear.FREEZE.isoformat()))
        children={}
        previous=None
        while datetime.now(timezone.utc)<gear.FREEZE:
            for unit,p in list(children.items()):
                if p.poll() is None:continue
                del children[unit]
                if (gear.ROOT/unit).exists() or p.returncode==0:continue
                tail=(BASE/(unit+'.log')).read_bytes()[-6000:].decode('utf8','replace')
                admission=('headroom','slots occupied','resource','companion handoff reserve','All slots claimed','Shared reservation changed','Post-claim')
                if not any(s in tail for s in admission):
                    atomic(BASE/(unit+'.hold.json'),dict(at=now(),reason='Unsubmitted local admission needs inspection'))
            units=[]
            for path in (STATE/'reviews').glob('*.json'):
                q=read(path);unit=q['unit']
                if ('operations' in q and q.get('fixture') and path.stem==unit
                        and unit not in children and not (gear.ROOT/unit).exists() and not (BASE/(unit+'.hold.json')).exists()):
                    units.append((list(ROWS).index(q['card']),0 if 'ICSI' in unit else 1,unit,q))
            waiting={}
            started=False
            for _,__,unit,q in sorted(units):
                why=permits(q)
                if why:
                    waiting[unit]=why
                    continue
                for tag in ('FAILED','COMPLETE'):
                    marker=(gear.ROOT/unit/(tag+'.json')).relative_to(ROOT).as_posix()
                    subprocess.run([sys.executable,'-B','tools/codex_watch.py','register',marker],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
                with (BASE/(unit+'.log')).open('ab') as file:
                    children[unit]=subprocess.Popen([sys.executable,'-B','tools/week8_run.py',q['card'],unit,'dispatch'],cwd=ROOT,stdout=file,
                                             stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                atomic(BASE/(unit+'.start.json'),dict(at=now(),pid=children[unit].pid,review='reviews/'+unit+'.json'))
                started=True
                break
            status=(tuple(sorted(waiting.items())),tuple(sorted(children)))
            if status!=previous:
                atomic(BASE/'STATUS.json',dict(at=now(),pending=waiting,launched=list(children)))
                previous=status
            # Give each child time to enter its atomic native admission before trying the next.
            time.sleep(4 if started else min(25,max(0,(gear.FREEZE-datetime.now(timezone.utc)).total_seconds())))
        atomic(BASE/'FROZEN.json',dict(at=now(),reason='Week 8 start freeze'))


if __name__=='__main__':
    run()
