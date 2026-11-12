"""Constructed EX1 complete producer/replay and source-boundary fixtures.

No human logs, learned timing model, or encoder is loaded. Explicit Unicode
escapes keep the intended codepoints intact through Windows tool transports.
"""
from pathlib import Path
import hashlib
import json

from . import week5_ex1 as study
from .timing_text import replay_words
from .timing_p6 import gzip_equal


def event(ordinal, name, *, source=None, delta=None, **extra):
    return dict(eventNum=ordinal, eventName=name, eventTimestamp=1000*(ordinal+1),
        eventSource=source, textDelta=delta, **extra)


def typed_events(text='alpha', initial='Prompt\r\n'):
    result=[event(0,'system-initialize',currentDoc=initial)]
    # Keep the terminal newline; each character has its true UTF-16 insertion.
    doc=initial
    for char in text+' ':
        at=len(study.coauthor.units(doc[:-1]))
        result.append(event(len(result),'text-insert',source='user',
            delta={'ops':[{'retain':at},{'insert':char}]}))
        doc=doc[:-1]+char+doc[-1:]
    return result


def suggestion_events():
    result=[event(0,'system-initialize',currentDoc='Prompt\n'),
        event(1,'suggestion-open',currentSuggestions=[dict(index=0,original=' machine',trimmed='machine')]),
        event(2,'suggestion-select',currentSuggestionIndex=0),
        event(3,'text-insert',source='api',delta={'ops':[{'retain':6},{'insert':' machine'}]}),
        event(4,'text-insert',source='user',delta={'ops':[{'retain':14},{'insert':'s'}]})]
    return result


def posterior(words):
    # Constructed frozen timing values; no estimated human posterior is used.
    result=[]
    for word in words:
        if word['is_word'] and word['pause_seconds'] is not None:
            result.append(dict(ordinal=word['ordinal'],onset=True,fast=.25,
                interval_seconds=word['pause_seconds']))
    return result


def seal(root,module,inputs=None,config=None):
    files={p.relative_to(root).as_posix():study.io.sha(p) for p in (root/'output').rglob('*') if p.is_file()}
    study.io.write_json(root/'PLAN.json',dict(module=module,inputs=inputs or {},config=config or {}))
    study.io.write_json(root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,outputs=files))


def prepare(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    p6=root/'p6';timing=root/'timing';at=root/'at';raw_roster=[];index=[];timing_roster=[];posts={};locations=[]
    for n in range(6):
        events=typed_events('alpha' if n%2==0 else 'beta',initial='P\U0001f642 cafe\u0301\r\n')
        replay=replay_words(events);words=replay['words']
        sid=f'constructed-session-{n}';writer=hashlib.sha256(f'writer-{n%5}'.encode()).hexdigest()
        raw=root/f'raw-{n}.jsonl';raw.write_text(''.join(json.dumps(e)+'\n' for e in events),encoding='utf8')
        relative=f'ledger/session-{n}.json.gz';path=p6/'output'/relative
        gzip_equal(path,dict(session=sid,writer=writer,words=words))
        index.append(dict(session=sid,writer=writer,file=relative,sha256=study.io.sha(path)))
        raw_roster.append(dict(session=sid,path=raw.relative_to(root).as_posix(),source_sha256=study.io.sha(raw)))
        timing_roster.append(dict(session=sid,writer=writer));posts[sid]=posterior(words)
        mapped=study.scoring.context_rows(events,words)
        locations.append([dict(location,session=sid,writer=writer)
                          for word,location in zip(words,mapped) if word['is_word']])
    study.io.write_json(p6/'output/P6_INDEX.json',index)
    study.io.write_json(timing/'output/PRIVATE_ROSTER.json',timing_roster)
    gzip_equal(timing/'output/INTERVALS.json.gz',posts)
    seal(p6,'constructed.p6');seal(timing,'constructed.timing')
    study.io.write_json(root/'ROSTER.json',raw_roster)
    bound=dict(p6_root=str(p6),timing_root=str(timing),raw_roster=str(root/'ROSTER.json'),repo_root=str(root))
    pins={k:study.io.sha(Path(v)/'COMPLETE.json') if k in ('p6_root','timing_root')
          else study.io.sha(v) for k,v in bound.items() if k!='repo_root'}
    at_index=[]
    for n,rows in enumerate(locations):
        relative=f'sessions/session-{n:04d}.json.gz';path=at/'output'/relative
        gzip_equal(path,dict(binding=study.scoring.digest(pins),rows=rows))
        at_index.append(dict(file=relative,sha256=study.io.sha(path),words=len(rows)))
    study.io.write_json(at/'output/INDEX.json',at_index)
    study.io.write_json(at/'output/SUMMARY.json',dict(sessions=6,source_pins=pins))
    seal(at,'runners.drive.cards.week5_at_source',bound,{})
    return dict(at_root=str(at))


def check_normalization():
    cases=[('Cafe\u0301\r\nnext \t','Caf\u00e9\nnext'),
           ('a\u0301\u0327','\u00e1\u0327'), ('\u1100\u1161\u11a8','\uac01'),
           ('\U0001f642 z\r','\U0001f642 z')]
    for raw,expected in cases:
        actual,origins=study.normalize_with_origins(raw)
        assert actual==expected and len(actual)==len(origins)
        assert all(origin and max(origin)<len(raw) for origin in origins)
    return dict(complete_cases=len(cases))


def check_projection():
    writer=hashlib.sha256(b'constructed-writer').hexdigest()
    events=typed_events('alpha beta');words=replay_words(events)['words']
    value=study.session_projection('constructed',writer,0,events,words,posterior(words))
    typed=[r for r in value['words'] if r['source']=='typed']
    assert len(typed)==2 and typed[-1]['stop'] is True and typed[-1]['log_pause']==0
    # An accepted word modified by a writer remains fully represented as mixed.
    events=suggestion_events();words=replay_words(events)['words']
    mixed=study.session_projection('mixed',writer,0,events,words,posterior(words))
    last=mixed['words'][-1]
    assert last['source'] is None and last['mixed_provenance'] and last['stop'] is None
    assert last['constituent_sources']==['accepted_suggestion','typed']
    assert last['source_codepoint_counts']=={'accepted_suggestion':7,'typed':1}
    # Original source classes survive when the final writer edit is absent.
    events=events[:-1];words=replay_words(events)['words']
    uniform=study.session_projection('uniform',writer,0,events,words,posterior(words))
    assert uniform['words'][-1]['source']=='accepted_suggestion'
    return dict(signed_stop=True,mixed_preserved=True,accepted_preserved=True)


def execute(output,inputs,config):
    if inputs or config:raise ValueError('EX1 constructed fixture takes no external source')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    result=dict(normalization=check_normalization(),projection=check_projection())
    parents=prepare(output/'constructed');target=output/'consumer'
    first=study.execute(target,parents,dict(max_new_documents=1,max_wall_seconds=60))
    assert first['status']=='yielded' and first['completed']==1
    complete=study.execute(target,parents,dict(max_new_documents=6,max_wall_seconds=60))
    assert complete['sessions']==6 and complete['writers']==5
    first=study.verify(target,parents,dict(max_new_documents=1,max_wall_seconds=60))
    assert first['status']=='yielded' and first['verified'] is False and first['completed']==1
    verified=study.verify(target,parents,dict(max_new_documents=6,max_wall_seconds=60))
    assert verified['verified'] is True
    result.update(full_execute_reentry=True,full_independent_verify_reentry=True,
        text_exported=False,fixture_only=True,production_has_not_run=True)
    study.io.write_json(output/'FIXTURE.json',result)
    return result


def verify(output,inputs,config):
    output=Path(output);result=execute(output/'fresh_verify',inputs,config)
    if result!=study.read(output/'FIXTURE.json'):raise ValueError('Constructed EX1 fresh replay differs')
    return dict(verified=True,complete_constructed_replay=True)
