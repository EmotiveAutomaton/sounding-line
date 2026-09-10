"""Stage 9 host for the inherited isolated reader, with a hidden Windows child.

DESIGN CHECK: I03/X02/X06; LESSONS 3--5. NULL: hiding a window must not
change arguments, scrubbed environment, timeouts, output collection or access
denials. ALTERNATIVE: actual complete predictions and boundary probes behave
identically through a no-console launch. This owns only Stage 9 host execution;
the inherited bootstrap and closed Stage 7 implementation remain unchanged.
"""
from pathlib import Path
import subprocess,time
from runners.stage7.runtime import BASE_PY,scrubbed_env
from .common import read


def run_capsule(cap:Path,endpoint:str,token:str,model:str,timeout_s:float=1800.):
    start=time.time()
    command=[str(BASE_PY),'-I','-S','-E','-B','-X','utf8','bootstrap.py']
    try:
        result=subprocess.run(command,cwd=str(cap),env=scrubbed_env(cap,endpoint,token,model),
            capture_output=True,text=True,timeout=timeout_s,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        rc,error=result.returncode,result.stderr[-2000:]
    except subprocess.TimeoutExpired as exc:
        rc,error=124,f'timeout after {timeout_s}s: {str(exc)[-500:]}'
    output={'rc':rc,'wall_s':round(time.time()-start,3),'stderr_tail':error,'capsule':str(cap)}
    for name in ('prediction','receipt','error','access'):
        path=cap/'out'/(name+'.json');output[name]=read(path) if path.exists() else None
    return output
