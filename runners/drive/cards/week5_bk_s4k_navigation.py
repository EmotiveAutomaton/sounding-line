"""Exact KLICKE document reconstruction and physically logged navigation.

DESIGN CHECK: LESSONS 2/3/5; BK_S4K.md. UTF-16 positions, removed text and
independently supplied final text must match before a session contributes.
Missing or contradictory operations are explicit failures, never no-revision
labels. Actual click/arrow keys define arms; displacement cannot relabel them.
"""
from collections import Counter
import hashlib, re
from runners.stage9.coauthor import units, text_of
from .week4_cursor import geometry, sentence_index, near_edit

ARROWS = {'ArrowLeft','ArrowRight','ArrowUp','ArrowDown'}
MOVE = re.compile(r'Move From \[(\d+),\s*(\d+)\] To \[(\d+),\s*(\d+)\]')


def logged_text(text):
    """Decode the CSV's escaped special characters without altering Unicode."""
    mapping={'n':'\n','r':'\r','t':'\t','b':'\b','f':'\f','v':'\v','\\':'\\','"':'"',"'":"'"}
    result=[];i=0
    while i<len(text):
        if text[i]!='\\': result.append(text[i]);i+=1;continue
        if i+1>=len(text) or text[i+1] not in mapping: raise ValueError('Unrecognized text escape')
        result.append(mapping[text[i+1]]);i+=2
    return ''.join(result)


def canonical_final(text):
    # Textarea LF is exported as CRCRLF by the supplied Windows text writer.
    # The export adds exactly one terminal record newline. Never strip arbitrary
    # whitespace: original writer trailing spaces/newlines remain significant.
    normalized=text.replace('\r\r\n','\n').replace('\r\n','\n')
    if not normalized.endswith('\n'): raise ValueError('Final export record terminator absent')
    return normalized[:-1]


def operation(doc, event):
    """CursorPosition is after the edit; offsets are JavaScript UTF-16 units."""
    activity=event['Activity']; change=logged_text(event['TextChange']); cursor=int(event['CursorPosition'])
    if activity=='Nonproduction':
        if change not in ('NoChange',''): raise ValueError('Nonproduction reports text change')
        if not 0<=cursor<=len(doc): raise ValueError('Cursor outside document')
        return doc, []
    if activity in ('Input','Paste'):
        insert=units(change);start=cursor-len(insert);remove=[]
    elif activity=='Remove/Cut':
        insert=[];start=cursor;remove=units(change)
    elif activity=='Replace':
        if change.count(' => ')!=1: raise ValueError('Ambiguous replacement payload')
        before,after=change.split(' => ');remove=units(before);insert=units(after);start=cursor-len(insert)
    else:
        match=MOVE.fullmatch(activity)
        if not match: raise ValueError('Unrecognized text operation')
        a,b,c,d=map(int,match.groups())
        if not (0<=a<b<=len(doc) and 0<=c<d<=len(doc) and b-a==d-c):
            raise ValueError('Invalid move spans')
        moved=doc[a:b]
        if change not in ('NoChange','') and units(change)!=moved: raise ValueError('Move text disagrees')
        if a==c: return doc, []
        remaining=doc[:a]+doc[b:]
        result=remaining[:c]+moved+remaining[c:]
        if not 0<=cursor<=len(result): raise ValueError('Move cursor outside document')
        # Express the actual two-coordinate move as one exact replacement delta.
        left=min(a,c);right=max(b,d)
        return result, [{'retain':left},{'delete':right-left},{'insert':text_of(result[left:right])}]
    if start<0 or start+len(remove)>len(doc): raise ValueError('Edit extent outside document')
    if doc[start:start+len(remove)]!=remove: raise ValueError('Removed text disagrees with replay')
    result=doc[:start]+insert+doc[start+len(remove):]
    if not 0<=cursor<=len(result): raise ValueError('Edited cursor outside document')
    ops=[{'retain':start}]
    if remove: ops.append({'delete':len(remove)})
    if insert: ops.append({'insert':change if activity in ('Input','Paste') else after})
    return result, ops


def replay(record, collect_navigation=True):
    doc=[];last_cursor=0;version=0;navigation=[];edits=[];census=Counter();cached=None
    for event in record['events']:
        new,ops=operation(doc,event);cursor=int(event['CursorPosition']);changed=new!=doc
        key=event['DownEvent'];stamp=event['DownTime']/1000
        census['events']+=1;census['activity_'+event['Activity'].split(' From ')[0]]+=1
        if collect_navigation and not changed and cursor!=last_cursor:
            if cached is None: cached=geometry(doc)
            sentences,_,_=cached;idx=sentence_index(sentences,cursor)
            distance=None if idx is None else len(sentences)-1-idx
            kind='click' if key=='Leftclick' else 'arrow' if key in ARROWS else 'other'
            near=(sentences[max(0,idx-1)][0],sentences[min(len(sentences)-1,idx+1)][1]) if idx is not None else (cursor,cursor)
            navigation.append(dict(ordinal=event['ordinal'],time=stamp,kind=kind,position=cursor,
                displacement=cursor-last_cursor,version=version,distance=distance,
                bin=None if distance is None or distance<1 else '1' if distance==1 else '2' if distance==2 else '3-5' if distance<=5 else '>5',
                near_start=near[0],near_end=near[1]))
            census[kind+'_moves']+=1
        elif key=='Leftclick' or key in ARROWS:
            census['device_with_text_change' if changed else 'device_stationary']+=1
        if changed:
            edits.append(dict(ordinal=event['ordinal'],time=stamp,ops=ops,user=True))
            version+=1;cached=None
        doc=new;last_cursor=cursor
    final=text_of(doc)
    if final!=canonical_final(record['final_text']): raise ValueError('Independent final text mismatch')
    clock=max((e['UpTime']/1000 for e in record['events']),default=0)
    return dict(census=dict(census),navigation=navigation,edits=edits,last_observed_time=clock,
                final_document_sha256=hashlib.sha256(final.encode()).hexdigest(),final_text=final)


def extract(record, window=30):
    if window not in (30,60): raise ValueError('Declared follow-up windows only')
    replayed=replay(record);census=Counter(replayed['census']);nav=replayed['navigation'];landings=[]
    for index,row in enumerate(nav):
        following=nav[index+1] if index+1<len(nav) else None
        if row['kind']=='arrow' and following and following['kind']=='arrow' and following['version']==row['version'] and following['time']-row['time']<=2:
            census['inside_arrow_run']+=1;continue
        if row['kind']=='click':
            pass_through=False
            for later in nav[index+1:]:
                if later['time']-row['time']>2: break
                if later['kind']=='click': pass_through=True;break
            if pass_through: census['pass_through_click']+=1;continue
        if row['kind'] not in ('click','arrow') or row['bin'] is None: continue
        if replayed['last_observed_time']-row['time']<window:
            census['followup_window_censored']+=1;continue
        landings.append({**row,'edit_near':near_edit(row,replayed['edits'],window)})
    return dict(session=record['session'],writer=record['session'],landings=landings,
                census=dict(census),window_seconds=window,
                final_document_sha256=replayed['final_document_sha256'],
                writer_basis='Author paper section2.2: duplicates by same author removed;4992workers/4992texts.',
                selection_scope='Logged selection endpoint only; selection span and physical hand occupancy unobserved.')
