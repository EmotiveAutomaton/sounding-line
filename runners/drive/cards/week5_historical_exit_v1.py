"""Read-only pre-reboot exit evidence for authenticated historical attempts.

DESIGN CHECK: LESSONS 3-5. Access denial alone never proves exit. A retained
creation time and terminal time both preceding an independently corroborated
kernel boot establish that the old process cannot be the current PID holder.
Unknown, conflicting or current-boot identities refuse. No process is touched.
"""
from datetime import datetime, timezone
from functools import lru_cache
import subprocess
import psutil
from runners.stage9.process_identity import is_same_live_process

EPOCH = 11644473600
PROOFS = {}

def preboot(record, terminal_at, os_boot_ticks, kernel_boot_epoch, current_epoch):
    if type(record.get('pid')) is not int or type(record.get('created_ticks')) is not int:
        raise ValueError('Malformed retained native identity')
    created=record['created_ticks']/10_000_000-EPOCH
    boot=os_boot_ticks/10_000_000-EPOCH
    terminal=datetime.fromisoformat(terminal_at)
    if terminal.tzinfo is None:
        raise ValueError('Terminal time needs a timezone')
    ended=terminal.timestamp()
    if not (abs(boot-kernel_boot_epoch)<10 and 0<created<=ended<boot-60 and boot<current_epoch):
        raise ValueError('Independent boot evidence does not establish historical exit')
    return dict(native=record,terminal_at=terminal_at,os_boot_ticks=os_boot_ticks,
                kernel_boot_epoch=kernel_boot_epoch,inspected_at=datetime.fromtimestamp(current_epoch,timezone.utc).isoformat(),
                basis='Authenticated attempt creation and terminal precede independently agreeing OS and kernel boot times; no identity is inferred for the current PID holder')

@lru_cache(maxsize=1)
def boot_pair():
    command='(Get-CimInstance Win32_OperatingSystem -ErrorAction Stop).LastBootUpTime.ToUniversalTime().ToFileTimeUtc()'
    value=subprocess.run(['powershell','-NoProfile','-Command',command],capture_output=True,text=True,check=True,timeout=30)
    return int(value.stdout.strip()),psutil.boot_time()

def stopped(record, terminal_at):
    try: return not is_same_live_process(record)
    except OSError as exc:
        if exc.errno != 5: raise
        os_boot,kernel_boot=boot_pair()
        proof=preboot(record,terminal_at,os_boot,kernel_boot,datetime.now(timezone.utc).timestamp())
        PROOFS[(record['pid'],record['created_ticks'])]=proof
        return True
