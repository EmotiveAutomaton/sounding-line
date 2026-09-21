"""Cheap, bounded resource wait inside the existing owned queue.

DESIGN CHECK: LESSONS 3-5. NULL: occupied hardware performs no inference and
produces no readiness marker. ALTERNATIVE: two actual ready inspections permit
one downstream admission attempt. The worker's cancellation, CPU and elapsed
limits continue during sleep. No process termination, allocation or LLM wake.
"""
import time
from .common import freeze,atomic,filehash,now,REPO
from .local_api import readiness


def run(out,card,pulse,raw):
    interval=card['poll_seconds']
    if interval != 300:
        raise ValueError('unreviewed capacity polling interval')
    consecutive=0;checks=0
    while True:
        pulse(phase='waiting-for-local-capacity',checks=checks)
        if (REPO/'results/.gpu.lock').exists():
            state=dict(ready=False,reason='existing GPU owner; no lock stealing',at=now())
        else:
            state=readiness(card['profile'])
        checks+=1
        consecutive=consecutive+1 if state['ready'] else 0
        atomic(out/'LATEST_CAPACITY.json',dict(state,checks=checks,consecutive_ready=consecutive))
        if consecutive>=2:
            freeze(out/'RESOURCE_READY.json',dict(status='complete',profile=card['profile'],inspection=state,checks=checks))
            return dict(status='complete',kind='infrastructure',checks=checks,
                controls=dict(no_inference=True,two_ready_samples=True,no_lock_stealing=True),
                files={'RESOURCE_READY.json':filehash(out/'RESOURCE_READY.json')})
        # Cheap local sleeping; the agent itself never waits in a polling loop.
        for _ in range(interval//10):
            time.sleep(10)
            pulse(phase='waiting-for-local-capacity',checks=checks,ready=state['ready'],reason=state['reason'])
