"""Package admitted program sources and public bindings in one sealed-run entry."""
from base64 import b85encode
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from runners.drive.cards import week8_gear as gear

LIB=gear.REPO/'runners/drive/sealed'
SUPPORT=gear.REPO/'runners/drive/cards/week6_sealed_support_v1.py'
RELEASE=LIB/'week6-sm-science/independent_release.py'


def package(study, modules, config, cpu_limit, fixture=False):
    if study not in modules or not 0<cpu_limit<=20000:
        raise ValueError('Missing entry or invalid CPU limit')
    contents={str(p.relative_to(gear.REPO)).replace('\\','/'):p.read_bytes() for p in modules}
    contents['runners/drive/cards/week6_sealed_support_v1.py']=SUPPORT.read_bytes()
    contents['independent_release.py']=RELEASE.read_bytes()
    contents['week6_sealed_support_v1.py']=b'from runners.drive.cards.week6_sealed_support_v1 import *\n'
    for name in list(contents):
        for parent in Path(name).parents:
            if parent!=Path('.'):
                contents.setdefault(parent.as_posix()+'/__init__.py',b'')
    buffer=BytesIO()
    with ZipFile(buffer,'w',compression=ZIP_DEFLATED) as archive:
        for name,data in sorted(contents.items()):
            archive.writestr(ZipInfo(name,(2026,11,27,0,0,0)),data,compress_type=ZIP_DEFLATED)
    blob=b85encode(buffer.getvalue()).decode('ascii')
    start=("root,out=map(Path,sys.argv[1:])" if fixture else
           "root,out=Path('/data'),Path('/out')\n"
           "flags=[l.split()[5].split(',') for l in Path('/proc/self/mountinfo').read_text().splitlines() if l.split()[4]=='/data']\n"
           "if len(flags)!=1 or 'ro' not in flags[0]: sys.exit(13)")
    text=f"""import base64,importlib,json,os,sys,tempfile,time
from pathlib import Path
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[name]='2'
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['TOKENIZERS_PARALLELISM']='false'
if os.name=='posix':
    import resource,signal
    hard=resource.getrlimit(resource.RLIMIT_CPU)[1]
    cap={cpu_limit} if hard==resource.RLIM_INFINITY else min(hard,{cpu_limit})
    resource.setrlimit(resource.RLIMIT_CPU,(cap,cap))
    seconds_left=int({int(gear.DRAIN.timestamp())}-time.time())
    if seconds_left<=0: sys.exit(20)
    signal.alarm(min(21600,seconds_left))
{start}
if {fixture!r} and os.name=='nt':
    import platform
    platform.uname()  # Cache local OS metadata needed by the Windows pandas import.
def offline(event,args):
    if event.startswith('socket.'): raise RuntimeError('Network access refused')
sys.addaudithook(offline)
with tempfile.TemporaryDirectory() as tmp:
    bundle=Path(tmp)/'program.zip'
    bundle.write_bytes(base64.b85decode({blob!r}))
    sys.path.insert(0,str(bundle))
    from runners.drive.cards.week6_sealed_support_v1 import SealedFailure
    try:
        module=importlib.import_module({'runners.drive.sealed.'+study.stem!r})
        module.run(root,out,json.loads({json.dumps(config,sort_keys=True)!r}))
    except SealedFailure as exc:
        sys.exit(exc.code)
    except Exception:
        if {fixture!r}:
            import traceback
            traceback.print_exc()
        sys.exit(14)
"""
    compile(text,'run.py','exec')
    return text.encode('utf8')
