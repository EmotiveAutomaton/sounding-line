"""Native descendant accounting and containment using stable identities."""
import json
import sys
import time
from runners.drive.native_job import ContainedProcess
from runners.drive.cards.batch_runtime_v5 import job_cpu
from runners.stage9.process_identity import native_identity


def test_descendant_cpu_and_exact_identity_exit(tmp_path):
    marker = tmp_path/'identities.json'
    descendant = 'import time;x=time.process_time();\nwhile time.process_time()-x<.3: pass\ntime.sleep(90)'
    code = ('import subprocess,sys,time,json;from pathlib import Path;'
            'from runners.stage9.process_identity import native_identity;'
            f'p=subprocess.Popen([sys.executable,"-c",{descendant!r}]);'
            f'Path({str(marker)!r}).write_text(json.dumps([native_identity(),native_identity(p.pid)]));time.sleep(90)')
    with ContainedProcess([sys.executable,'-B','-c',code], '.', tmp_path/'out', tmp_path/'err') as worker:
        deadline = time.monotonic()+20
        while not marker.exists() or job_cpu(worker)<.2:
            assert time.monotonic()<deadline
            time.sleep(.05)
        identities = json.loads(marker.read_text())
        assert job_cpu(worker) >= .2
    deadline = time.monotonic()+10
    for value in identities:
        while native_identity(value['pid']) == value:
            assert time.monotonic()<deadline
            time.sleep(.05)
    assert native_identity() is not None
