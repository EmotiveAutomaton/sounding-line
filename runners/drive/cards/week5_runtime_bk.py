"""Week 5 backlog uses only the four original CPU leases.

DESIGN CHECK: LESSONS 3–5. Same containment and accounting as runtime v2.
No occupied lease is replaced and no extra-bank lease is claimed by BK.
"""
import argparse,json
from pathlib import Path
from . import week5_runtime_v2 as runtime

def claim(root,plan):
    if plan['family']!='BK':raise ValueError('Backlog family required')
    with runtime.kernel.admission_lock(runtime.policy.OLD_SLOTS):
        resources=runtime.policy.admission(dict(plan,attempt_root=str(root)))
        value=dict(native=runtime.native_identity(),card=plan['card'],family='BK',at=runtime.now(),
                   runtime='week5-bk',attempt_root=str(root),projected_peak_ram_GiB=plan['projected_peak_ram_GiB'])
        for index in range(4):
            path=runtime.policy.OLD_SLOTS/f'slot-{index}.json'
            try:
                with path.open('x',encoding='utf8',newline='\n') as f:json.dump(value,f)
                return (path,value),resources
            except FileExistsError:continue
        raise RuntimeError('Original four backlog slots occupied')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path)
    runtime.claim=claim
    runtime.run(parser.parse_args().root)
