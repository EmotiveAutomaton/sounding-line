"""Constructed native timing-ruler validation; no corpus outcomes."""
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from . import week4_timing_ruler as r
from .timing_p6 import write_equal
from .timing_census import read
CONFIG=dict(card='W4-timing-ruler-constructed',seed=r.SEED)
def compute(inputs,config):
    if inputs or config!=CONFIG:raise ValueError('Frozen constructed check required')
    with threadpool_limits(limits=1):
        m,a=r.writer_ruler(r.known_items());n,b=r.writer_ruler(r.known_items(13))
    pa=np.array([[x['fast'],x['hesitation'],x['slowest']] for x in a]);pb=np.array([[x['fast'],x['hesitation'],x['slowest']] for x in b])
    assert m['state']==n['state']=='fitted' and np.allclose(pa,pb,atol=1e-8)
    assert (pa[:240].argmax(1)==0).mean()>.98 and (pa[240:360].argmax(1)==1).mean()>.98 and (pa[360:].argmax(1)==2).mean()>.98
    assert not any(x['stop'] for x in a[:200]) and all(x['stop'] for x in a[360:])
    return dict(passes=True,model=m,scaled_model=n,posterior=pa.tolist(),scientific_admission=False)
def execute(output,inputs,config):write_equal(Path(output)/'RESULTS.json',compute(inputs,config));return dict(status='complete')
def verify(output,inputs,config):
    if read(Path(output)/'RESULTS.json')!=compute(inputs,config):raise ValueError('Native timing-ruler replay differs')
    return dict(verified=True,constructed_replay=True)
