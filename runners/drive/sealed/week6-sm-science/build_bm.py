"""Package three independent wave-two jobs with the reviewed numerical core."""
from hashlib import sha256
import json
from pathlib import Path
import sys
import build

HERE=Path(__file__).resolve().parent


def bm_sources():
    sources=build.modules()
    for key in ('bm_entry','independent_release'):
        sources[key]=(HERE/(key+'.py')).read_text('utf8')
    # Share the frozen point, family-draw and replay arithmetic verbatim. The
    # previous entry decides disclosure for its own outputs. The new entry
    # uses the joint row memberships and the same unmodified public gate.
    legacy=sources['engine']
    a=legacy.index('    estimates, unavailable, coverage = [], [], []')
    b=legacy.index('    counts_table = [',a)
    imports=legacy[:legacy.index('def study(')]
    sources['bm_numeric']=imports+'def numerical_outputs(results, families, replay_families):\n'+legacy[a:b]+"""
    return {k:v for k,v in (('estimates',estimates),('unidentified',unavailable),
                             ('interval_unavailable',coverage)) if v}
"""
    return sources


def build_jobs(destination):
    destination=Path(destination)
    destination.mkdir(parents=True,exist_ok=False)
    sources=bm_sources()
    source_map=json.loads((HERE/'source_map.json').read_text('utf8'))
    entries={}
    for job in ('main','nt1','d5'):
        directory=destination/job;directory.mkdir()
        code=build.single_file(sources,'from bm_entry import main\nraise SystemExit(main('+repr(source_map)+','+repr(job)+'))\n')
        (directory/'run.py').write_bytes(code)
        entries[job]=dict(bytes=len(code),sha256=sha256(code).hexdigest())
    manifest=dict(entries=entries,source_hashes={k:sha256(v.encode('utf8')).hexdigest() for k,v in sources.items()},
                  mounted_source='midus-m2-joined',real_runs_held=True)
    (destination/'MANIFEST.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n','utf8')


if __name__=='__main__':build_jobs(sys.argv[1])

