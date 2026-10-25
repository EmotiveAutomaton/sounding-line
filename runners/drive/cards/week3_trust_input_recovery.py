"""TR5 engineering healing1: semantic accepted atoms, original timed survival.

DESIGN CHECK: LESSONS3-5, 2026-10-25. Equivalent Quill encodings must assign
identical accepted characters and history. The unique canonical full-document
append proves the text; raw insertion lengths cannot count retained prefix text
as accepted. The original exact80% threshold and anchor-time queries remain.
"""
from contextlib import contextmanager

from runners.stage9.coauthor import units,text_of,delta_ops
from . import week3_trust_inputs as original
from . import week3_outcome_blocks_recovery as repaired

CONFIG=original.CONFIG
PILOT=original.PILOT


def history(events,timeline,canonical):
    certified={s['origin']:s for s in repaired.spans(events,timeline,canonical)}
    doc=units(events[0]['currentDoc']);owners=[None]*len(doc)
    current=pending=None;serial=0;records={}
    for ordinal,event in enumerate(events):
        name=event['eventName']
        if name=='suggestion-open':current=ordinal
        if name=='suggestion-select':pending=current
        ops=delta_ops(event.get('textDelta'))
        if not ops:continue
        user=event.get('eventSource')=='user';origin=pending if not user and pending is not None else None
        before=text_of(doc);prior=owners
        out=[];labels=[];position=0;removed=set();first_positions={}
        for op in ops:
            if 'insert' in op:
                for char in op['insert']:
                    out.extend(units(char));labels.extend([None]*len(units(char)))
            else:
                n=op.get('retain',op.get('delete'))
                if type(n) is not int or n<0 or position+n>len(doc):raise ValueError('invalid survival UTF16 boundary')
                if 'retain' in op:out.extend(doc[position:position+n]);labels.extend(owners[position:position+n])
                else:
                    gone=set(owners[position:position+n])-{None};removed|=gone
                    for tag in gone:first_positions.setdefault(tag[0],len(out))
                position+=n
        out.extend(doc[position:]);labels.extend(owners[position:]);doc=out;owners=labels
        if origin is not None:
            proof=certified[origin]
            if not before.endswith('\n') or text_of(doc)!=before[:-1]+proof['text']+'\n':
                raise ValueError('certified whole-document append differs')
            inserted=[];newlabels=[]
            for char in proof['text']:
                tag=(origin,serial);serial+=1;inserted.append(tag);newlabels.extend([tag]*len(units(char)))
            if len(inserted)!=proof['original_codepoints']:raise ValueError('certified original atom count differs')
            owners=prior[:-1]+newlabels+prior[-1:]
            if len(owners)!=len(doc):raise ValueError('canonical atom provenance length differs')
            records[origin]=dict(**proof,retention=[[ordinal,len(inserted)]],removed=set(),failure_position=None,failure_removed=None)
            pending=None
        if user:
            for key in {tag[0] for tag in removed}:
                r=records[key];r['removed'].update(tag for tag in removed if tag[0]==key)
                r['retention'].append([ordinal,r['original_codepoints']-len(r['removed'])])
                if ordinal==r['failure_ordinal']:
                    r['failure_position']=first_positions[key];r['failure_removed']=len(r['removed'])
    if text_of(doc)!=timeline['final_document']:raise ValueError('survival final text differs')
    for r in records.values():
        if r['retention'][-1][1]!=r['retained_codepoints']:raise ValueError('survival counts differ from independent replay')
        r.pop('removed')
    return records


@contextmanager
def canonical_survival():
    previous=original.history;original.history=history
    try:yield
    finally:original.history=previous


def execute(output,inputs,config):
    with canonical_survival():return original.execute(output,inputs,config)


def verify(output,inputs,config):
    with canonical_survival():return original.verify(output,inputs,config)
