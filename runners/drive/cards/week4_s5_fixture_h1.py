"""Native S5 known-answer rehearsal; constructed values only.

DESIGN CHECK: zero, positive and reversed planted coefficients must reproduce
through the certified random-intercept fit and whole-author bootstrap. No
unknown corpus comparison or new claim is admitted by this fixture.
"""
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from . import week4_s5_h1 as s
from .timing_p6 import write_equal
from .timing_census import read

CONFIG=dict(card='S5-constructed',bootstrap=25,permutations=20)
def compute(inputs,config):
    if inputs or config!=CONFIG:raise ValueError('Fixed constructed S5 pass required')
    with threadpool_limits(limits=1):
        rows=[s.fit_arrays(*s.known_arrays(effect),bootstrap=25,permutations=20) for effect in (0.,.7,-.7)]
    if not np.allclose([r['estimate'] for r in rows],[0,.7,-.7],atol=1e-8):raise ValueError('Constructed effect not recovered')
    if [s.result_state(r['estimate'],r['interval']) for r in rows]!=['null','positive','negative']:
        raise ValueError('Known-answer classification failed')
    return dict(known_answers_pass=True,rows=rows,scientific_admission=False)
def execute(output,inputs,config):
    write_equal(Path(output)/'RESULTS.json',compute(inputs,config));return dict(status='complete',scientific_admission=False)
def verify(output,inputs,config):
    if read(Path(output)/'RESULTS.json')!=compute(inputs,config):raise ValueError('Fresh constructed replay differs')
    return dict(verified=True,scientific_admission=False)
