"""EV2 counted handler with explicit owner-stop/resource-yield boundaries.

DESIGN CHECK: LESSONS3-5 read 2026-10-19. Scientific null/alternative and all
controls are unchanged from engine_signatures. Resource/owner stops fail closed
before loading, after loading and every ten reassignments; never become a null.
Original validated handler/source remain immutable. Complete fresh replay and
binding checks are mandatory under both hypotheses.
"""
from pathlib import Path
from threadpoolctl import threadpool_limits
from runners.stage14.common import read,atomic
from .engine_signatures import CONFIG,CONSTRUCTED,load,analyze
from .timing_p6 import write_equal,gzip_equal,gzread
from .timing_stats import bind,check_binding


def boundary(output):
    output=Path(output)
    if (output.parent/'STOP').exists():raise RuntimeError('Owner stop requested')
    if (output/'YIELD_REQUEST.json').exists():
        raise RuntimeError('Resource or runtime boundary: '+str(read(output/'YIELD_REQUEST.json')))


def run(output,inputs,config,operation):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);boundary(output)
    if operation=='verify' or (output/'TIMING_BINDINGS.json').exists():check_binding(output,inputs,config)
    def progress(p):
        boundary(output);atomic(output/'PROGRESS.json',p)
    with threadpool_limits(limits=1):
        rows=load(inputs,config);boundary(output)
        summary,detail=analyze(rows,config,progress);boundary(output)
    if operation=='execute':
        write_equal(output/'SUMMARY.json',summary);gzip_equal(output/'DETAIL.json.gz',detail)
        if not (output/'TIMING_BINDINGS.json').exists():bind(output,inputs,config,['SUMMARY.json','DETAIL.json.gz'])
        return summary
    if summary!=read(output/'SUMMARY.json') or detail!=gzread(output/'DETAIL.json.gz'):
        raise ValueError('fresh source/statistic/control reconstruction differs')
    return dict(verified=True,summary=summary,fresh_source_authentication=True,
                full_statistic_replay=True,full_control_replay=True)


def execute(output,inputs,config):return run(output,inputs,config,'execute')
def verify(output,inputs,config):return run(output,inputs,config,'verify')
