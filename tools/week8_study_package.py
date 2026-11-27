"""Package an offline Week 8 study for the existing sealed runner and its native fixture."""
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runners.drive.cards import week8_gear as gear
from runners.drive.sealed import week7_sld3_build as original
from runners.stage14.common import filehash,freeze,read
from tools.week8_sealed import GATE,HOST,STATE


def entry(sources, module, config, cap, fixture):
    guard=f"""import os,sys
from pathlib import Path
if os.name=='posix':
    import resource,signal,time
    hard=resource.getrlimit(resource.RLIMIT_CPU)[1]
    limit={cap} if hard==resource.RLIM_INFINITY else min(hard,{cap})
    resource.setrlimit(resource.RLIMIT_CPU,(limit,limit))
    remaining=int({int(gear.DRAIN.timestamp())}-time.time())
    if remaining<=0:sys.exit(20)
    signal.alarm(min(21600,remaining))
"""
    if fixture:
        guard+="if os.name=='nt':\n    import platform\n    platform.uname()\n"
        locations='Path(sys.argv[1]),Path(sys.argv[2])'
    else:
        guard+="flags=[r.split()[5].split(',') for r in Path('/proc/self/mountinfo').read_text().splitlines() if r.split()[4]=='/data']\nif len(flags)!=1 or 'ro' not in flags[0]:sys.exit(13)\n"
        locations="Path('/data'),Path('/out')"
    guard+="def offline(event,args):\n    if event.startswith('socket.'):raise RuntimeError('Network refused')\nsys.addaudithook(offline)\n"
    call=f"from week6_sealed_support_v1 import SealedFailure\nfrom {module} import run\ntry:\n    run({locations},{config!r})\nexcept SealedFailure as exc:\n    sys.exit(exc.code)\n"
    if not fixture:
        call+="except Exception:\n    sys.exit(14)\n"
    return guard.encode()+original.build.single_file(sources,call)


def gate(out):
    if filehash(GATE)!=read(HOST)['installed_gate_sha256']:
        raise ValueError('Installed gate pin differs')
    if subprocess.check_output([sys.executable,'-I','-B',str(GATE),str(out)],text=True).strip()!='gate passed':
        raise ValueError('Native fixture failed the installed gate')


def admit(unit,card,source,cap,tables,program,fixture,pins,not_before=None):
    path=STATE/'sealed'/unit/'run.py'
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.read_bytes()!=program:
        raise ValueError('Sealed entry already exists with other bytes')
    if not path.exists():
        path.write_bytes(program)
    evidence=[Path(p) for p in pins]+[path,fixture,gear.AUTHORITY,Path(gear.__file__),Path(__file__),
              Path(original.build.__file__),ROOT/'tools/week8_spark.ps1',ROOT/'tools/week8_sealed.py',HOST,GATE]
    review=dict(unit=unit,card=card,source=source,cap=cap,tables=tables,fixture_gate_passed=True,
                fixture_sha256=filehash(fixture),pins={str(p):filehash(p) for p in evidence})
    if not_before:
        review['not_before']=not_before
    dest=STATE/'reviews'/(unit+'.json')
    freeze(dest,review)
    return filehash(dest)
