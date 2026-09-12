"""Serial finite Ghost development producer chain, with terminal guards.

DESIGN CHECK: LESSONS2-5. Each NULL/ALTERNATIVE gets the same frozen public
cases; each child owns its actual GPU reservation. Completed outputs are reused,
source changes fail, and no evaluation answers are opened by the chain.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
from . import queue, deliberation, structured
from .contracts import digest
from .ollama import now,write_new


def run(prepared, public_root, output):
    sources={**structured.identity(),**deliberation.identity(),"runners/stage10/opportunity_chain.py":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    manifest={"at":now(),"sources":sources,"prepared_sha256":digest(queue.read(prepared/"FROZEN.json")),"envelopes_sha256":digest(queue.read(prepared/"development-envelopes.json")),"arms":["R0","R1","R2","R3"],"scope":"historically exposed V16 development; remaining strategies and evaluation pending"}
    if (output/"MANIFEST.json").exists():
        saved=queue.read(output/"MANIFEST.json")
        if any(saved[k]!=manifest[k] for k in manifest.keys()-{"at"}):
            raise ValueError("chain identity changed")
        manifest=saved
    else:
        write_new(output/"MANIFEST.json",manifest)
    results={}
    jobs=[("direct-example",lambda:queue.run(prepared,output/"direct-example",["R0","R1"])),
          ("deliberation",lambda:deliberation.run(prepared,output/"deliberation")),
          ("structured",lambda:structured.run(public_root,prepared/"development-envelopes.json",output/"structured"))]
    for name,work in jobs:
        for path,expected in sources.items():
            if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected:
                raise ValueError("chain source changed")
        queue.status(output/"STATUS.json",{"at":now(),"status":"RUNNING","active":name,"finished":list(results)})
        result=work();results[name]={"summary_sha256":digest(result),"status":result["status"]}
    summary={"at":now(),"status":"COMPLETE","manifest_sha256":digest(manifest),"producers":results,"scope":manifest["scope"]}
    if (output/"COMPLETE.json").exists():
        saved=queue.read(output/"COMPLETE.json")
        if any(saved[k]!=summary[k] for k in summary.keys()-{"at"}):
            raise ValueError("retained chain changed")
        summary=saved
    else:
        write_new(output/"COMPLETE.json",summary)
    queue.status(output/"STATUS.json",{"at":now(),"status":"COMPLETE","finished":list(results)})
    return summary


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--prepared",type=Path,required=True);p.add_argument("--public-root",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    try:run(a.prepared,a.public_root,a.output)
    except Exception as exc:
        if not (a.output/"FAILED.json").exists():write_new(a.output/"FAILED.json",{"at":now(),"error":repr(exc)})
        raise
