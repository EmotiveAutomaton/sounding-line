"""WC4 reliability handler, full fresh reconstruction and first-tenth cost pilot.

DESIGN CHECK: LESSONS3-5, Week3 WC4 controls read 2026-10-25. One thousand
within-prompt writer-label permutations rebuild variance profiles. A pilot
never admits science; full plans refuse constructed or partial sources. Both
arms travel together through the real-writer bootstrap. Changed saved scores
must fail fresh replay. Model/source costs share the original3600CPU ceiling.
"""
from pathlib import Path
import time

from . import week3_stability_stats as stats
from .timing_census import read,filehash
from .timing_p6 import gzread,write_equal
from .timing_pmap_source import completed

CONFIG=dict(card='WC4',mode='full',seed=20261026,permutations=1000,bootstraps=2000)
PILOT=dict(CONFIG,mode='pilot',permutations=100)
CONSTRUCTED=dict(CONFIG,mode='constructed')


def load(inputs,config):
    if config not in (CONFIG,PILOT,CONSTRUCTED):raise ValueError('frozen WC4 analysis configuration required')
    if config==CONSTRUCTED:
        if set(inputs)!={'fixture'}:raise ValueError('WC4 constructed fixture required')
        return read(inputs['fixture'])
    if set(inputs)!={'source_completion'}:raise ValueError('WC4 complete source required')
    parent=Path(inputs['source_completion']).resolve().parent
    for name in ('WC4_INPUT_BINDING.json','EVENTS.json.gz','SUMMARY.json'):completed(inputs['source_completion'],parent/'output'/name)
    binding=read(parent/'output/WC4_INPUT_BINDING.json')
    if binding['config']['mode']!='full' or binding['config']['card']!='WC4-inputs' or binding['config']['expected_sessions']!=1399:
        raise ValueError('WC4 original complete source required')
    return gzread(parent/'output/EVENTS.json.gz')['sessions']


def run(output,inputs,config,verification=False):
    start=time.process_time();output=Path(output);output.mkdir(parents=True,exist_ok=True)
    rows=load(inputs,config);binding=dict(config=config,inputs={k:filehash(v) for k,v in sorted(inputs.items())})
    result=stats.analyze(rows,config)
    if config==PILOT:result=dict(card='WC4-cost-pilot',state='timing_only',scientific_admission=False)
    if verification:
        if read(output/'INPUT_BINDING.json')!=binding or read(output/'WC4_RESULT.json')!=result:raise ValueError('WC4 full statistical replay differs')
        return dict(verified=True,scientific_admission=False if config!=CONFIG else result['scientific_admission'])
    write_equal(output/'INPUT_BINDING.json',binding);write_equal(output/'WC4_RESULT.json',result)
    if not (output/'TIMING.json').exists():
        elapsed=time.process_time()-start
        write_equal(output/'TIMING.json',dict(cpu_seconds=elapsed,projected_full_analysis_and_replay_cpu_seconds=2*elapsed*(10 if config==PILOT else 1),
                                            excludes='all source, native and previous pilot charges; owner admission adds them'))
    return result


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
