"""Predeclared S4 texture grid; never upgrades the unsupported parent.

DESIGN CHECK: Week4 amendments F/G, S4 grid and LESSONS2-5 reviewed
2026-11-02. NULL: exact equal rates remain null; absent support has no effect.
ALTERNATIVE: signed differences survive the unchanged comparison. Changing
threshold/window requires full raw replay; old 30-second outcomes are not reused.
Each cell is descriptive, receives no descendants and keeps the parent gap.
"""
from pathlib import Path
import hashlib,json,time
from .week4_cursor import extract,assemble
from .week4_cursor_source import fixture
from .week4_cursor_stats import analyze,CONFIG as STATS
from .timing_events import source_sessions
from .timing_p6 import write_equal,gzip_equal,gzread,progress
from .timing_census import read,filehash

GRID=((20,30),(80,30),(40,60))

def configuration(jump,window,constructed=False):
    if (jump,window) not in GRID:raise ValueError('Only the packet frozen texture grid')
    return dict(card='S4-texture',jump=jump,window=window,constructed=constructed,seed=20261102)

def run(output,inputs,config,verification=False):
    if config!=configuration(config['jump'],config['window'],config['constructed']):raise ValueError('Changed configuration')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);start=time.process_time()
    if config['constructed']:
        if inputs:raise ValueError('No human input in native fixture')
        stream=[(dict(session='fixture',writer='fixture'),None,dict(domain='constructed'),fixture())];expected=1
    else:
        if set(inputs)!={'source_inputs','parent_completion'}:raise ValueError('Source registry and complete parent required')
        parent=Path(inputs['parent_completion']);c=read(parent);s=read(parent.parent/'output/SUMMARY.json')
        if not c['fresh_process_verified'] or not s['complete_population']:raise ValueError('Incomplete parent')
        for n,h in c['outputs'].items():
            if filehash(parent.parent/n)!=h:raise ValueError('Changed parent '+n)
        source=read(inputs['source_inputs']);root=Path(source['repo_root'])
        def raw():
            for row,timeline,meta in source_sessions(source,'raw_roster'):
                events=[json.loads(x) for x in (root/meta['path']).read_text(encoding='utf8').splitlines() if x.strip()]
                yield row,timeline,meta,events
        stream=raw();expected=1399
    sessions=[];binding=[]
    for i,(row,timeline,meta,events) in enumerate(stream):
        value=extract(events,config['jump'],config['window'])
        if timeline is not None and value['final_document_sha256']!=hashlib.sha256(timeline['final_document'].encode()).hexdigest():raise ValueError('Final replay mismatch')
        value.update(session=row['session'],writer=row['writer'],genre=meta['domain'])
        path=output/'sessions'/(hashlib.sha256(row['session'].encode()).hexdigest()+'.json.gz')
        if verification:
            if gzread(path)!=value:raise ValueError('Source replay mismatch')
        else:gzip_equal(path,value)
        sessions.append(value);binding.append(dict(session=row['session'],raw=meta.get('source_sha256'),prepared=row.get('sha256')))
        progress(output/'PROGRESS.json',dict(phase='verify-source' if verification else 'source',done=i+1,total=expected))
    if len(sessions)!=expected:raise ValueError('Incomplete full population')
    census,support=assemble(sessions)
    if config['constructed']:
        # The fixture's opening displacement is below 80 characters and has no
        # paragraph crossing; only its two terminal step runs remain at 80.
        expected_ordinals={(20,30):[1,3,4],(80,30):[3,4],(40,60):[]}
        if [r['ordinal'] for r in sessions[0]['landings']]!=expected_ordinals[(config['jump'],config['window'])]:raise ValueError('Known followup window differs')
    primary,private=analyze(sessions,census['separable_groups'],STATS)
    genres={g:analyze([s for s in sessions if s['genre']==g],census['separable_groups'],STATS)[0] for g in sorted({s['genre'] for s in sessions})}
    summary=dict(census=census,primary=primary,genres=genres,descriptive=True,claim_upgrade=False,descendants=False,
                 parent_interval_available=False,stop_counter_comparable=False,
                 stop_counter_reason='Parent was unsupported and has no effect interval; no numerical convergence claim is possible.')
    values={'SUMMARY.json':summary,'PRIVATE_INFERENCE.json':private,'PRIVATE_SUPPORT.json':support,
            'BINDING.json':dict(config=config,sources=binding,inputs={k:filehash(v) for k,v in inputs.items()})}
    if verification:
        for name,v in values.items():
            if read(output/name)!=v:raise ValueError('Full texture replay mismatch '+name)
        return dict(verified=True,complete_source_replay=True,complete_statistical_replay=True)
    for name,v in values.items():write_equal(output/name,v)
    write_equal(output/'TIMING.json',dict(cpu_seconds=time.process_time()-start))
    return dict(status='complete',scientific_admission=False,descriptive=True)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
