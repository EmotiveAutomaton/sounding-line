import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil
import pytest

from runners.drive.native_job import ContainedProcess

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='native Windows containment')


def await_file(path):
    deadline = time.monotonic()+15
    while not path.exists():
        assert time.monotonic() < deadline, str(path)
        time.sleep(.05)


def test_exact_command_logs_environment_and_priority(tmp_path):
    answer=tmp_path/'answer.json'
    code=('import os,json,psutil;from pathlib import Path;'
          f'Path({str(answer)!r}).write_text(json.dumps([os.environ["EV_TEST"],psutil.Process().nice()]));'
          'print("retained stdout")')
    with ContainedProcess([sys.executable,'-B','-c',code],tmp_path,tmp_path/'out',tmp_path/'err',
                          dict(os.environ,EV_TEST='only this child')) as child:
        await_file(answer)
        deadline=time.monotonic()+15
        while child.poll() is None:
            assert time.monotonic()<deadline
            time.sleep(.05)
        assert child.poll()==0
    assert json.loads(answer.read_text())==['only this child',psutil.BELOW_NORMAL_PRIORITY_CLASS]
    assert 'retained stdout' in (tmp_path/'out').read_text()


def test_close_terminates_child_and_descendant_only(tmp_path):
    marker=tmp_path/'identity.json'
    grandchild='import time;time.sleep(120)'
    code=('import subprocess,sys,time,json,os;from pathlib import Path;'
          f'p=subprocess.Popen([sys.executable,"-c",{grandchild!r}]);'
          f'Path({str(marker)!r}).write_text(json.dumps([os.getpid(),p.pid]));time.sleep(120)')
    with ContainedProcess([sys.executable,'-B','-c',code],tmp_path,tmp_path/'out',tmp_path/'err'):
        await_file(marker)
        identities=[(pid,psutil.Process(pid).create_time()) for pid in json.loads(marker.read_text())]
    deadline=time.monotonic()+10
    for pid,created in identities:
        while psutil.pid_exists(pid) and psutil.Process(pid).create_time()==created:
            assert time.monotonic()<deadline
            time.sleep(.05)
    assert psutil.Process(os.getpid()).is_running()


def test_invalid_executable_is_refused_before_work(tmp_path):
    with pytest.raises(OSError):
        ContainedProcess([str(tmp_path/'absent.exe')],tmp_path,tmp_path/'out',tmp_path/'err')


def test_abrupt_supervisor_exit_closes_owned_descendants(tmp_path):
    marker=tmp_path/'owned.json'
    child_code='import time;time.sleep(120)'
    code=('import sys,time,json,os;from pathlib import Path;'
          'from runners.drive.native_job import ContainedProcess;'
          f'p=ContainedProcess([sys.executable,"-c",{child_code!r}],{str(tmp_path)!r},{str(tmp_path/'out')!r},{str(tmp_path/'err')!r});'
          f'Path({str(marker)!r}).write_text(json.dumps([os.getpid(),p.pid]));time.sleep(120)')
    supervisor=subprocess.Popen([sys.executable,'-B','-c',code])
    try:
        await_file(marker)
        parent,child=json.loads(marker.read_text())
        created=psutil.Process(child).create_time()
        psutil.Process(parent).terminate()
        deadline=time.monotonic()+10
        while psutil.pid_exists(child) and psutil.Process(child).create_time()==created:
            assert time.monotonic()<deadline
            time.sleep(.05)
    finally:
        if supervisor.poll() is None:supervisor.terminate()
        supervisor.wait(timeout=10)


def test_safe_path_refuses_script_directory_stdlib_shadow(tmp_path):
    (tmp_path/'statistics.py').write_text('raise RuntimeError("shadowed")',encoding='utf8')
    script=tmp_path/'child.py';script.write_text('from statistics import mean;print(mean([2,4]))',encoding='utf8')
    with ContainedProcess([sys.executable,'-B',script],Path.cwd(),tmp_path/'out',tmp_path/'err',
                          dict(os.environ,PYTHONSAFEPATH='1')) as child:
        deadline=time.monotonic()+10
        while child.poll() is None:
            assert time.monotonic()<deadline
            time.sleep(.05)
        assert child.poll()==0
    assert (tmp_path/'out').read_text().strip()=='3'
