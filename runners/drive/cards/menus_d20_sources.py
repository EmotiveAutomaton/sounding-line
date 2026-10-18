"""Authenticated produced-word windows and frozen P5/CONTENT_V2 representations.

DESIGN CHECK: LESSONS 3-5 read October18. A token begun before dismissal is not
new uptake even when completed later. Exactly50 completed lexical occurrences
must follow resolution; short tails remain exclusions. Later-deleted words stay
in scope. Original source identity changes refuse extraction. P6 is a verified
cache of the existing production ledger, not a new scientific admission gate.
"""
from collections import Counter
from pathlib import Path
import math
import numpy as np
from .menus_io import read,sha256
from .events_d4_sources import bind_completed
from .events_p5 import model_identity
from .timing_census import session_paths
from .timing_p6 import gzread


def load(inputs):
    for key,complete in (('p5_inputs','p5_completion'),('p5_index','p5_completion'),
                         ('p6_index','p6_completion'),('p6_plan','p6_completion')):
        bind_completed(inputs[complete],inputs[key])
    binding=read(inputs['p5_inputs'])
    for key in ('sessions','content_model'):
        if Path(binding['paths'][key]).resolve()!=Path(inputs[key]).resolve() or binding['sha256'][key]!=sha256(inputs[key]):
            raise ValueError('P5 source binding differs')
    p6plan=read(inputs['p6_plan'])
    if 'original_plan' in p6plan['inputs']:
        original=inputs['p6_original_plan']
        if p6plan['inputs']['original_plan']!=original or p6plan['pins'].get(original)!=sha256(original):
            raise ValueError('P6 recovery source binding differs')
        p6plan=read(original)
    if p6plan['inputs']['prepared_sessions']!=inputs['sessions']:
        raise ValueError('P6 session source differs')
    if p6plan['pins'].get(inputs['sessions'])!=sha256(inputs['sessions']):
        raise ValueError('P6 roster binding differs')
    content=read(inputs['content_complete'])
    if content.get('status')!='COMPLETE':raise ValueError('content incomplete')
    for key in ('content_records','content_vectors','content_model'):
        found=[v for k,v in content['outputs'].items() if Path(k).name==Path(inputs[key]).name]
        if found!=[sha256(inputs[key])]:raise ValueError('content binding differs')
    model_identity(inputs['content_model'])
    sessions=read(inputs['sessions']);records=read(inputs['content_records'])
    mapping={s['session']:s for s in sessions};features={r['key']:r for r in records}
    if len(mapping)!=len(sessions) or len(features)!=len(records):raise ValueError('duplicate source identity')
    p6=read(inputs['p6_index']);p5=read(inputs['p5_index'])
    if {s['session'] for s in p6}!=set(mapping) or {s['session'] for s in p5}!=set(mapping):
        raise ValueError('source roster coverage differs')
    timelines={entry['session']:path for entry,path in session_paths(inputs)}
    if set(timelines)!=set(mapping):raise ValueError('foundation roster differs')
    vectors=np.load(inputs['content_vectors'],mmap_mode='r',allow_pickle=False)
    if vectors.ndim!=2 or vectors.shape[1]!=384 or not np.isfinite(vectors).all():raise ValueError('content vector dimensions')
    halves={}
    for writer in sorted({s['writer'] for s in sessions}):
        group=sorted((s for s in sessions if s['writer']==writer),key=lambda s:(s['timestamp'],s['session']))
        halves.update({s['session']:i%2 for i,s in enumerate(group)})
    return dict(sessions=mapping,features=features,vectors=vectors,p6={s['session']:s for s in p6},
                p6_root=Path(inputs['p6_index']).parent,timelines=timelines,halves=halves)


def word_window(words,resolution,size=50):
    ordered=sorted((w for w in words if w['is_word']),key=lambda w:(w['completed_ordinal'],w['index']))
    later=[w for w in ordered if w['ordinal']>resolution and w['completed_ordinal']>resolution]
    chosen=later[:size]
    return chosen if len(chosen)==size else None


def session_rows(data,sid):
    session=data['sessions'][sid];entry=data['p6'][sid]
    path=(data['p6_root']/entry['file']).resolve();path.relative_to(data['p6_root'].resolve())
    if sha256(path)!=entry['sha256']:raise ValueError('production ledger changed')
    ledger=gzread(path);timeline=read(data['timelines'][sid])
    for record in (ledger,timeline):
        if (record['session'],record['writer'],record['prompt'])!=(sid,session['writer'],session['prompt']):
            raise ValueError('session identity differs')
    decisions={d['key']:d for d in timeline['decisions']}
    if set(decisions)!={r['key'] for r in session['rows']}:raise ValueError('decision coverage differs')
    words=ledger['words'];lexical=[w for w in words if w['is_word']]
    rows=[];counts=Counter()
    for source in sorted(session['rows'],key=lambda r:(r['ordinal'],r['key'])):
        decision=decisions[source['key']];feature=data['features'][source['key']]
        if decision['handling']!=source['handling'] or decision['ordinal']!=source['ordinal']:
            raise ValueError('decision identity differs')
        if (feature['session'],feature['writer'])!=(sid,session['writer']) or len(feature['options'])!=len(source['menu']):
            raise ValueError('content menu identity differs')
        resolution=decision['resolution_ordinal']
        if resolution is None:
            # An unresolved ignored menu is usable as a predecision donor;
            # it never supplies a dismissed-target window.
            if source['handling']=='dismiss':raise ValueError('dismissed menu has no observed resolution')
            resolution=source['ordinal']
        window=word_window(words,resolution)
        before=sum(w['completed_ordinal']<=resolution for w in lexical)
        progress=min(9,int(10*before/max(1,len(lexical))))
        vectors=data['vectors'][feature['options']]
        if len(vectors) and not np.allclose(np.linalg.norm(vectors,axis=1),1,atol=1e-5,rtol=0):raise ValueError('unnormalized options')
        row=dict(key=source['key'],session=sid,writer=session['writer'],prompt=session['prompt'],
            half=data['halves'][sid],progress_decile=progress,handling=source['handling'],resolution_ordinal=resolution,
            options=source['menu'],option_vectors=vectors.tolist(),window=None if window is None else ' '.join(w['token'] for w in window),
            window_indices=None if window is None else [w['index'] for w in window],
            window_ordinals=None if window is None else [[w['ordinal'],w['completed_ordinal']] for w in window],
            window_revised=None if window is None else sum(bool(w['revised']) for w in window))
        counts['menus']+=1;counts['dismissed']+=source['handling']=='dismiss'
        counts['dismissed_short_tail']+=source['handling']=='dismiss' and window is None
        rows.append(row)
    return rows,dict(counts),dict(ledger=sha256(path),timeline=sha256(data['timelines'][sid]))
