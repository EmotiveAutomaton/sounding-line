"""S4 counted source census; no cursor-choice or revision effect is scored."""
from pathlib import Path
import json,hashlib,time
from .week4_cursor import extract,assemble
from .timing_events import source_sessions
from .timing_p6 import write_equal,gzip_equal,gzread,progress
from .timing_census import read,filehash

def configuration(mode):
    if mode not in ('constructed','timing','full'):raise ValueError('Unknown source mode')
    return dict(card='S4-source',mode=mode,seed=20261102,jump=40,window=30,expected_sessions=1 if mode=='constructed' else 140 if mode=='timing' else 1399)

def fixture():
    text='First sentence. Second sentence in another place. Third sentence.'
    def e(name,time,pos,**kw):return dict(eventName=name,eventTimestamp=time*1000,currentCursor=pos,eventSource='user',**kw)
    return [e('system-initialize',0,len(text),currentDoc=text),e('cursor-backward',1,0),e('cursor-forward',5,1),
        e('cursor-forward',6,2),e('cursor-backward',10,1),e('system-finish',45,1)]

def run(output,inputs,config,verification=False):
    if config!=configuration(config.get('mode')):raise ValueError('Frozen source configuration required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);started=time.process_time();sessions=[];bindings=[]
    if config['mode']=='constructed':
        if inputs:raise ValueError('Constructed census has no corpus input')
        stream=[(dict(session='fixture',writer='fixture'),None,dict(domain='constructed'),fixture())]
    else:
        if set(inputs)!={'source_inputs'}:raise ValueError('Frozen source registry required')
        source=read(inputs['source_inputs']);root=Path(source['repo_root'])
        def raw_stream():
            for row,timeline,meta in source_sessions(source,'raw_roster'):
                raw=root/meta['path'];events=[json.loads(x) for x in raw.read_text(encoding='utf8').splitlines() if x.strip()]
                yield row,timeline,meta,events
        stream=raw_stream()
    for i,(row,timeline,meta,events) in enumerate(stream):
        if i>=config['expected_sessions']:break
        value=extract(events,config['jump'],config['window'])
        if timeline is not None and value['final_document_sha256']!=hashlib.sha256(timeline['final_document'].encode()).hexdigest():raise ValueError('Exact final document replay differs')
        value.update(session=row['session'],writer=row['writer'],genre=meta['domain'])
        path=output/'sessions'/(hashlib.sha256(row['session'].encode()).hexdigest()+'.json.gz')
        if verification:
            if gzread(path)!=value:raise ValueError('Cursor source replay differs')
        else:gzip_equal(path,value)
        sessions.append(value);bindings.append(dict(session=row['session'],source_sha256=meta.get('source_sha256'),prepared_sha256=row.get('sha256')))
        progress(output/'PROGRESS.json',dict(phase='verify-source' if verification else 'source',done=i+1,total=config['expected_sessions']))
    if len(sessions)!=config['expected_sessions']:raise ValueError('Source population incomplete')
    summary,support=assemble(sessions);summary.update(mode=config['mode'],complete_population=config['mode']=='full',scientific_admission=False)
    if config['mode']=='constructed':
        if summary['cursor_census'].get('inside_step_run')!=1 or [r['ordinal'] for r in sessions[0]['landings']]!=[1,3,4]:raise ValueError('Constructed cursor answer differs')
    values={'SUMMARY.json':summary,'PRIVATE_SUPPORT.json':support,'BINDING.json':dict(config=config,sources=bindings,inputs={k:filehash(v) for k,v in inputs.items()})}
    if verification:
        for k,v in values.items():
            if read(output/k)!=v:raise ValueError('Complete source summary differs: '+k)
        return dict(verified=True,complete_source_replay=True)
    for k,v in values.items():write_equal(output/k,v)
    write_equal(output/'TIMING.json',dict(cpu_seconds=time.process_time()-started,sessions=len(sessions)))
    return dict(status='complete',scientific_admission=False)
def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
