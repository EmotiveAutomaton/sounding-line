"""Apply Week 7's process CPU and final-drain limits before reading a mounted source."""
from datetime import datetime, timezone
import os
import sys

CPU_LIMIT = 3600


def bounded(entry):
    """The file appended after the resource preamble is exactly the rehearsed entry."""
    prefix = f"""import os as _os
if _os.name == 'posix':
    import resource as _resource, signal as _signal, time as _time
    _hard = _resource.getrlimit(_resource.RLIMIT_CPU)[1]
    _cap = {CPU_LIMIT} if _hard == _resource.RLIM_INFINITY else min(_hard, {CPU_LIMIT})
    _resource.setrlimit(_resource.RLIMIT_CPU, (_cap, _cap))
    _left = int({int(datetime(2026,11,27,6,tzinfo=timezone.utc).timestamp())} - _time.time())
    if _left <= 0:
        raise SystemExit(20)
    _signal.alarm(min(21600, _left))
"""
    return prefix.encode('ascii') + entry
