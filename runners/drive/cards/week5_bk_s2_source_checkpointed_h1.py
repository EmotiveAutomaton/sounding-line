"""S2 isolated append-ancestry repair with session quantum and full replay.

Execution reuses sealed per-session projections. Verification recomputes every
session, including copied prefixes. max_new_draws is the runtime's operational
quantum key here, measured in complete source sessions rather than resamples.
"""
from collections import Counter
from pathlib import Path
import copy,json,time
from . import week5_bk_s2_source_h1 as base
from .timing_pmap_source import completed,bound_record
from .timing_p6 import gzread,gzip_equal,write_equal,progress
from .timing_census import read,filehash
from .timing_events import source_sessions

def prepare(inputs,config):
    if config.get('mode')=='constructed':
        fixture=read(inputs['constructed_source'])
        if fixture.get('constructed') is not True:raise ValueError('Constructed source required')
        expected=len(fixture['sessions'])
        if config!={'card':'BK-S2-inputs','mode':'constructed','seed':base.SEED,'expected_sessions':expected,'max_new_draws':config['max_new_draws']}:raise ValueError('Invalid constructed source configuration')
        def stream():
            for i,value in enumerate(fixture['sessions']):
                yield dict(session='constructed-'+str(i),writer='constructed-writer'),dict(domain='creative'),value['events'],value['p6'],value['intervals'],value['revision'],dict(source_sha256=filehash(inputs['constructed_source']),ordinal=i),i
        return expected,stream(),b'constructed-source-privacy-salt'
    if config!={'card':'BK-S2-inputs','seed':base.SEED,'expected_sessions':1399,'max_new_draws':config['max_new_draws']}:raise ValueError('Frozen complete S2 source configuration required')
    rev=Path(inputs['revision_completion']);revroot=rev.parent/'output';completed(rev,revroot/'INDEX.json');revindex={r['session']:r for r in read(revroot/'INDEX.json')}
    completed(inputs['p6_completion'],inputs['p6_index']);pindex={r['session']:r for r in read(inputs['p6_index'])}
    timing=Path(inputs['timing_completion']);tr=timing.parent/'output'
    for name in ('PRIVATE_ROSTER.json','INTERVALS.json.gz'):completed(timing,tr/name)
    roster={r['session']:r for r in read(tr/'PRIVATE_ROSTER.json')};intervals=gzread(tr/'INTERVALS.json.gz')
    if len(revindex)!=1399 or set(revindex)!=set(pindex) or set(pindex)!=set(roster) or set(roster)!=set(intervals):raise ValueError('S2 complete source population mismatch')
    source=read(inputs['source_inputs'])
    def stream():
        for row,timeline,meta in source_sessions(source,'raw_roster'):
            key=row['session']
            # Cached projections need the authenticated source identities, but
            # raw JSON parsing and project() are deferred until actually needed.
            def payload(key=key,meta=meta,row=row):
                old=bound_record(revroot/'INDEX.json',revindex[key]);p6=bound_record(inputs['p6_index'],pindex[key])
                if p6['writer']!=row['writer'] or old['writer']!=row['writer'] or roster[key]['writer']!=row['writer']:raise ValueError('S2 writer identity mismatch')
                raw=Path(source['repo_root'])/meta['path'];events=[json.loads(line) for line in raw.read_text('utf8').splitlines() if line.strip()]
                return events,p6,intervals[key],old
            binding=dict(source_sha256=meta['source_sha256'],revision_sha256=revindex[key]['sha256'],p6_sha256=pindex[key]['sha256'],timing_source_sha256=filehash(inputs['timing_completion']))
            yield row,meta,payload,None,None,None,binding,roster[key]['session_order']
    return 1399,stream(),Path(inputs['salt']).read_bytes()

def run(output,inputs,config,verification=False):
    quantum=config.get('max_new_draws')
    if type(quantum)is not int or quantum<1:raise ValueError('Positive complete-session quantum required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);started=time.process_time()
    binding=dict(inputs={k:filehash(v) for k,v in inputs.items()},config={k:v for k,v in config.items() if k!='max_new_draws'})
    if verification:
        if read(output/'SOURCE_BINDING.json')!=binding:raise ValueError('S2 copied source binding changed')
    else:write_equal(output/'SOURCE_BINDING.json',binding)
    expected,stream,salt=prepare(inputs,config);new=0;sessions=[];census=Counter();reused=0
    for i,(row,meta,events,p6,intervals,old,unit_binding,order) in enumerate(stream):
        path=output/'raw-sessions'/f'{i:05d}.json.gz'
        saved=gzread(path) if path.exists() else None
        if saved is not None and saved['source_binding']!=unit_binding:raise ValueError('S2 cached session source changed')
        if saved is not None and not verification:value=saved;reused+=1
        else:
            if callable(events):events,p6,intervals,old=events()
            values,counts,pairs=base.project(events,p6,intervals,old);original,_=base.produced_words(p6['words'])
            session=dict(session=base.private_key(salt,row['session']),writer=base.private_key(salt,row['writer']),genre=meta['domain'],
                         timestamp=p6.get('timestamp',order),session_order=order,sentences=values,bigram_intervals=pairs,first_words=original)
            value=dict(source_binding=unit_binding,session=session,census=counts)
            if verification:
                if saved!=value:raise ValueError('S2 independent complete-session projection differs')
            else:gzip_equal(path,value)
            new+=1
        sessions.append(copy.deepcopy(value['session']));census.update(value['census'])
        progress(output/'PROGRESS.json',dict(phase='verify' if verification else 'source',sessions=i+1,total=expected,new_sessions=new,reused_sessions=reused))
        pilot_sessions=70 if expected==1399 else 1
        if not verification and i+1==pilot_sessions:
            pilot=output/'PILOT.json'
            if pilot.exists():
                if read(pilot)['sessions']!=pilot_sessions or read(pilot)['total']!=expected:raise ValueError('Copied S2 pilot boundary changed')
            else:write_equal(pilot,dict(sessions=i+1,total=expected,cpu_seconds=time.process_time()-started,new_sessions=new,reused_sessions=reused))
        if (output/'YIELD_REQUEST.json').exists() or not verification and new>=quantum and i+1<expected:
            progress(output/('VERIFY_CHECKPOINT.json' if verification else 'CHECKPOINT.json'),dict(sessions=i+1,total=expected,new_sessions=new,reused_sessions=reused,full_source_verification=False))
            return dict(status='yielded',reason='S2 complete-session quantum' if not verification else 'S2 verifier owner request; fresh verification restarts',checkpoint=dict(sessions=i+1,total=expected))
    if i+1!=expected:raise ValueError('S2 raw source incomplete')
    base.classify_and_controls(sessions)
    summary=dict(card='BK-S2-inputs',sessions=len(sessions),writers=len({s['writer'] for s in sessions}),census=dict(census),scientific_effect_computed=False,
                 primary_provenance='wholly typed at first complete production; subsequent mixed status does not remove the initial unit',
                 old_census_scope_correction='Old candidate census bounds only currently-wholly-typed targets, not all first-production units',constructed=config.get('mode')=='constructed')
    if verification:
        if sessions!=gzread(output/'PRIVATE_SENTENCES.json.gz') or summary!=read(output/'SUMMARY.json'):raise ValueError('S2 complete source replay differs')
        return dict(verified=True,all_source_cells_replayed=True,recomputed_sessions=new,copied_prefix_used_for_verification=False)
    gzip_equal(output/'PRIVATE_SENTENCES.json.gz',sessions);write_equal(output/'SUMMARY.json',summary)
    return dict(status='complete',new_sessions=new,reused_sessions=reused,scientific_effect_computed=False)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
