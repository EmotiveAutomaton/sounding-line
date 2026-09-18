"""Only the brief's predefined scientific coverage/reporting checkpoints.

DESIGN CHECK: LESSONS 5. NULL: elapsed time is never scientific success or new
authority; routine ETA checks are absent. ALTERNATIVE: each commissioned coverage
deadline emits one immutable operational event for the existing owner watcher.
Cancellation prevents subsequent events; original commissioning time never resets.
"""
from datetime import datetime,timezone,timedelta
import hashlib
import os
from pathlib import Path
import time
import traceback
from .common import PRIVATE,read,freeze
from runners.stage9.process_identity import native_identity


def schedule(contract):
    start=datetime.fromisoformat(contract['commissioned_at'])
    rows=[dict(id=f'coverage-{h}h',at=(start+timedelta(hours=h)).isoformat(),
               action='Inspect completed coverage, admitted work and branch dispositions; no unfinished scores') for h in contract['checkpoints_elapsed_hours']]
    rows += [dict(id='reporting-start',at=contract['reporting_starts'],action='Assemble the single final curator packet; finish only useful admitted small units'),
             dict(id='final-checkpoint',at=contract['checkpoint'],action='Complete the Sunday packet and record every branch/resource disposition')]
    return sorted(rows,key=lambda r:r['at'])


def due(rows,at):
    if at.tzinfo is None:raise ValueError('timezone-aware checkpoint clock required')
    return [r for r in rows if datetime.fromisoformat(r['at'])<=at]


def run(root=PRIVATE):
    import msvcrt
    directory=root/'continuation/checkpoints';directory.mkdir(parents=True,exist_ok=True)
    with (directory/'watch.lock').open('a+b') as lock:
        lock.write(b'1');lock.flush();lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        freeze(directory/f'OWNER-{os.getpid()}.json',dict(native=native_identity(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
        rows=schedule(read(root/'CONTRACT.json'));freeze(directory/'SCHEDULE.json',rows)
        while not (directory/'CANCEL').exists():
            for row in due(rows,datetime.now(timezone.utc)):
                freeze(directory/(row['id']+'.json'),dict(status='COMPLETE',kind='predefined operational checkpoint',
                    scientific_verdict=False,commissioned_due=row['at'],action=row['action']))
            if all((directory/(r['id']+'.json')).exists() for r in rows):break
            time.sleep(10)
        freeze(directory/f'EXIT-{os.getpid()}.json',dict(status='COMPLETE',scientific_verdict=False,
            disposition='cancelled' if (directory/'CANCEL').exists() else 'all predefined checkpoints emitted'))


if __name__=='__main__':
    try:run()
    except BaseException:
        freeze(PRIVATE/'continuation/checkpoints'/f'FAILED-{os.getpid()}.json',dict(status='FAILED',error=traceback.format_exc()))
        raise
