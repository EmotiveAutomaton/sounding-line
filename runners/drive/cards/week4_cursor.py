"""S4 source census and exact cursor landing instrument.

DESIGN CHECK: Week4 S4 and LESSONS2-5 reviewed 2026-11-02. Mouse identity
is absent from cursor events: no click inference. Constructed step runs,
pass-through jumps, API moves, Unicode positions and near/far edit outcomes
must reproduce. Unsupported geometry stays explicit; no threshold tuning.
"""
from pathlib import Path
from collections import Counter,defaultdict
import bisect,json,math,re,time,hashlib
import numpy as np
from runners.stage9.coauthor import units,text_of,apply_delta,delta_ops
from .events_p5 import sentence_bounds
from .timing_events import source_sessions
from .timing_p6 import write_equal,gzip_equal,gzread,progress
from .timing_census import read,filehash

def geometry(doc):
    text=text_of(doc);offset=[0]
    for c in text:offset.append(offset[-1]+len(units(c)))
    sentences=[(offset[a],offset[b]) for a,b in sentence_bounds(text)]
    words=sorted({offset[k] for m in re.finditer(r"[^\W_]+(?:['’][^\W_]+)*",text) for k in m.span()})
    paragraphs=[offset[m.end()] for m in re.finditer(r'\n+',text)]
    return sentences,words,paragraphs

def motion(old,new,words,paragraphs,jump=40):
    if old==new:return 'stationary'
    if abs(old-new)>jump or bisect.bisect_right(paragraphs,old)!=bisect.bisect_right(paragraphs,new):return 'jump'
    adjacent=None
    if new>old:
        i=bisect.bisect_right(words,old)
        if i<len(words):adjacent=words[i]
    else:
        i=bisect.bisect_left(words,old)-1
        if i>=0:adjacent=words[i]
    return 'step' if abs(old-new)==1 or new==adjacent else 'other'

def sentence_index(spans,position):
    if not spans:return None
    return min(len(spans)-1,max(0,bisect.bisect_right([a for a,b in spans],position)-1))

def shift_boundary(point,ops,right=False):
    """Map a saved boundary through a delta, retaining insert-side affinity."""
    old=0;shift=0
    for op in ops:
        if 'retain' in op:old+=op['retain']
        elif 'insert' in op:
            if old<point or (old==point and right):shift+=len(units(op['insert']))
        elif 'delete' in op:
            n=op['delete']
            if old<=point<old+n:return old+shift
            if old+n<=point:shift-=n
            old+=n
    return point+shift

def near_edit(landing,edits,seconds=30):
    left,right=landing['near_start'],landing['near_end']
    for edit in edits:
        if edit['ordinal']<=landing['ordinal']:continue
        if edit['time']-landing['time']>seconds:break
        pos=0;hit=False
        for op in edit['ops']:
            if 'retain' in op:pos+=op['retain']
            elif 'delete' in op:
                hit|=pos<right and pos+op['delete']>left;pos+=op['delete']
            elif 'insert' in op:hit|=left<=pos<=right and bool(op['insert'])
        if hit and edit['user']:return True
        left=shift_boundary(left,edit['ops']);right=shift_boundary(right,edit['ops'],True)
    return False

def extract(events,jump=40,window=30):
    if not events or events[0]['eventName']!='system-initialize':raise ValueError('Initialization required')
    doc=units(events[0]['currentDoc']);owners=[None]*len(doc);previous_cursor=events[0].get('currentCursor')
    clock=-math.inf;last_time=None;version=0;cached=None;cursors=[];edits=[];counts=Counter();menus=[];menu=None
    for ordinal,event in enumerate(events):
        stamp=float(event['eventTimestamp'])/1000
        if not math.isfinite(stamp) or stamp<clock:raise ValueError('Invalid clock')
        clock=stamp;name=event['eventName'];cursor=event.get('currentCursor');ops=delta_ops(event.get('textDelta'))
        changed=any(('insert' in op and op['insert']) or op.get('delete',0) for op in ops)
        valid=type(cursor) is int and 0<=cursor<=len(doc)
        if name.startswith('cursor-'):
            counts['cursor_events']+=1
            span=event.get('cursorRange') or {}
            if event.get('eventSource')=='api':counts['api_cursor_excluded']+=1
            elif span.get('length',0):counts['selection_range_excluded']+=1
            elif not valid or type(previous_cursor) is not int or not 0<=previous_cursor<=len(doc):counts['unknown_position_excluded']+=1
            elif changed:counts['cursor_with_text_change_excluded']+=1
            else:
                if cached is None:cached=geometry(doc)
                sentences,words,paragraphs=cached;kind=motion(previous_cursor,cursor,words,paragraphs,jump)
                counts[kind]+=1;si=sentence_index(sentences,cursor)
                distance=None if si is None else len(sentences)-1-si
                near=(sentences[max(0,si-1)][0],sentences[min(len(sentences)-1,si+1)][1]) if si is not None else (cursor,cursor)
                cursors.append(dict(ordinal=ordinal,time=stamp,kind=kind,position=cursor,displacement=cursor-previous_cursor,
                    distance=distance,bin=None if distance is None or distance<1 else '1' if distance==1 else '2' if distance==2 else '3-5' if distance<=5 else '>5',
                    near_start=near[0],near_end=near[1],version=version,prior_event_seconds=None if last_time is None else stamp-last_time))
        if name in ('suggestion-open','suggestion-reopen'):
            if menu is not None:menus.append(menu)
            menu=dict(ordinal=ordinal,pointer=False,keyboard=False)
        elif name=='suggestion-hover' and menu is not None:menu['pointer']=True
        elif name in ('suggestion-up','suggestion-down') and menu is not None:menu['keyboard']=True
        elif name in ('suggestion-select','suggestion-close') and menu is not None:
            menus.append(menu);menu=None
        if changed:
            edits.append(dict(ordinal=ordinal,time=stamp,ops=ops,user=event.get('eventSource')=='user'))
            doc,owners,_=apply_delta(doc,owners,event.get('textDelta'),insertion_owner=None);version+=1;cached=None
        if type(cursor) is int and 0<=cursor<=len(doc):previous_cursor=cursor
        else:previous_cursor=None
        last_time=stamp
    if menu is not None:menus.append(menu)
    landings=[]
    for i,row in enumerate(cursors):
        next_row=cursors[i+1] if i+1<len(cursors) else None
        continues=next_row is not None and next_row['time']-row['time']<=2
        if row['kind']=='step' and continues and next_row['kind']=='step' and next_row['version']==row['version']:
            counts['inside_step_run']+=1;continue
        if row['kind']=='jump' and any(x['kind']=='jump' for x in cursors[i+1:] if x['time']-row['time']<=2):
            counts['pass_through_jump']+=1;continue
        if row['kind'] not in ('step','jump') or row['bin'] is None:continue
        if clock-row['time']<window:
            counts['followup_window_censored']+=1;continue
        landings.append(dict(row,edit_near=near_edit(row,edits,window)))
    pointer=Counter('both' if m['pointer'] and m['keyboard'] else 'pointer' if m['pointer'] else 'keyboard' if m['keyboard'] else 'neither' for m in menus)
    return dict(census=dict(counts),landings=landings,cursors=cursors,menu_census=dict(pointer),menus=menus,
        menu_scope='Raw open/reopen episodes; canonical choice joins remain separate before the descriptive choice comparison.',
        final_document_sha256=hashlib.sha256(text_of(doc).encode()).hexdigest())

def assemble(sessions):
    totals=Counter();menu=Counter();writers=defaultdict(Counter)
    for s in sessions:
        totals.update(s['census']);menu.update(s['menu_census'])
        for row in s['landings']:writers[s['writer']][(row['bin'],row['kind'])]+=1
    support={}
    for writer,counts in writers.items():
        bins=[b for b in ('1','2','3-5','>5') if counts[(b,'step')]>0 and counts[(b,'jump')]>0]
        support[writer]=dict(bins=bins,steps=sum(counts[(b,'step')] for b in bins),jumps=sum(counts[(b,'jump')] for b in bins))
    eligible=sum(r['steps']>=10 and r['jumps']>=10 for r in support.values())
    classified=sum(totals[k] for k in ('step','jump','other','stationary'));share=totals['jump']/classified if classified else 0
    separable=totals['step']>0 and share>=.05
    return dict(sessions=len(sessions),writers=len({s['writer'] for s in sessions}),cursor_census=dict(totals),menu_census=dict(menu),
        jump_share=share,separable_groups=separable,supported_writers=eligible,required_writers=20,case_supported=separable and eligible>=20,
        scientific_effect_computed=False,scope='Logged cursor geometry only; physical input device unknown outside suggestion menus.'),support
