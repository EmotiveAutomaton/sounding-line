"""Training-only marginals and explicit, low-dimensional alignment histories.

DESIGN CHECK: LESSONS 2-5. NULL: a literal match does not identify selection;
identical visible histories must have identical rival forecasts. ALTERNATIVE:
before/after alignment locates retained offers, unmatched continuation and edits.
Compatible prototype histories are examples, not an exhaustive process posterior.
No learned classifier is fitted from fifteen episodes and five training writers.
"""
from collections import defaultdict
from difflib import SequenceMatcher
from .models import FIELDS,ACTIONS,SLOTS,SPAN_STATES
from .targets import norm
from .common import canonical


def fit(rows):
    writers={r['writer'] for r in rows};counts={w:sum(r['writer']==w for r in rows) for w in writers}
    result={'facts':{s:{k:[1/len(v)]*len(v) for k,v in FIELDS.items()} for s in SLOTS},'handling':[.25]*4}
    # One symmetric pseudo-episode plus writer-balanced training mass. The same
    # marginal prior is retained as a rival; no evaluation field is read here.
    for row in rows:
        weight=len(rows)/len(writers)/counts[row['writer']]
        for f in row['target']['facts']:
            for k,labels in FIELDS.items():result['facts'][f['slot']][k][labels.index(f[k])]+=weight
        result['handling'][ACTIONS.index(row['target']['handling'])]+=weight
    for item in result['facts'].values():
        for k,p in item.items():item[k]=[x/sum(p) for x in p]
    p=result['handling'];result['handling']=[x/sum(p) for x in p]
    result['training_episodes']=len(rows);result['training_writers']=len(writers)
    return result


def blank():
    return {s:dict(slot=s,actor='unknown',operation='absent',relation='none',span_ids=[],span_state='absent') for s in SLOTS}


def ids(evidence,start,end):
    return [a['id'] for a in evidence['anchors'] if a['start']<end and start<a['end']]


def put(facts,slot,actor,operation,relation,anchors):
    facts[slot]=dict(slot=slot,actor=actor,operation=operation,relation=relation,
        span_ids=anchors,span_state='located' if anchors else 'unlocated')


def prototype(e,handling,offer):
    before=e['before'];after=e['endpoint'];f=blank();inserted=handling in ('accept','edit')
    diff=[(tag,i,j,k,l) for tag,i,j,k,l in SequenceMatcher(None,before,after,autojunk=False).get_opcodes() if tag!='equal']
    append=after.startswith(before[:-1]) and before.endswith('\n') and after.endswith('\n')
    added=after[len(before)-1:-1] if append else ''
    start=len(before)-1
    if inserted:
        # Minimal representative: selected offer at the old endpoint. An edited
        # prototype uses replacement; unseen restoration histories remain possible.
        span=ids(e,start,start+len(offer)) if handling=='accept' else ids(e,start,len(after)-1) if append else []
        put(f,'selection','human_writer','select','selects',span)
        put(f,'entry','model','insert','selected_by',span)
        if handling=='edit':
            op='delete' if not added else 'format_edit' if norm(added)==norm(offer) else 'content_edit'
            put(f,'change','human_writer',op,'modifies',span)
            put(f,'removal','human_writer','delete','removes',[])
        elif added.startswith(offer) and len(added)>len(offer):
            put(f,'continuation','human_writer','insert','extends',ids(e,start+len(offer),len(after)-1))
    elif added:
        put(f,'continuation','human_writer','insert','none',ids(e,start,len(after)-1))
    if not append and diff:
        anchors=sorted({a for _,_,_,k,l in diff for a in ids(e,k,l)})
        removed=''.join(before[i:j] for _,i,j,_,_ in diff)
        inserted_text=''.join(after[k:l] for _,_,_,k,l in diff)
        put(f,'surrounding','human_writer','format_edit' if norm(removed)==norm(inserted_text) else 'content_edit',
            'unrelated' if inserted else 'none',anchors)
    return f


def predict(e,model,aligned=True):
    base=dict(facts=[dict(slot=s,**model['facts'][s],span_ids=[],span_state='unknown') for s in SLOTS],
        handling=list(model['handling']),attributes=dict(reviewed='unknown',endorsed='unknown',understood='unknown'))
    if not aligned or 'before' not in e:return base,dict(signal='artifact marginal only',compatible_histories='not identified')
    before=e['before'];after=e['endpoint'];append=before.endswith('\n') and after.startswith(before[:-1]) and after.endswith('\n')
    added=after[len(before)-1:-1] if append else ''
    matches=[o for o in e['alternatives'] if o and added.startswith(o.replace('\r\n','\n').replace('\r','\n'))]
    offer=max(matches,key=len) if matches else max(e['alternatives'],key=lambda o:SequenceMatcher(None,o,added,autojunk=False).ratio(),default='')
    # Fixed likelihood multipliers, pre-outcome. Exact retention supports the
    # minimal acceptance history but never eliminates human copying or editing.
    multipliers=[2.,1.,1.,1.] if matches else [0.,1.,1.,1.]
    weights=[p*m for p,m in zip(model['handling'],multipliers)];weights=[w/sum(weights) for w in weights]
    prototypes=[prototype(e,a,offer) for a in ACTIONS]
    out=[]
    for s in SLOTS:
        fact=dict(slot=s)
        for name,labels in FIELDS.items():
            # Reserve a fifth of each marginal to the training-only prior. This
            # openly heuristic blend protects against the nonexhaustive prototypes.
            fact[name]=[.2*base['facts'][SLOTS.index(s)][name][j]+.8*sum(w for w,p in zip(weights,prototypes) if p[s][name]==lab)
                        for j,lab in enumerate(labels)]
        span_votes=defaultdict(float)
        for w,p in zip(weights,prototypes):span_votes[(tuple(p[s]['span_ids']),p[s]['span_state'])]+=w
        span,state=max(span_votes,key=lambda x:(span_votes[x],str(x)))
        fact.update(span_ids=list(span),span_state=state);out.append(fact)
    return dict(base,facts=out,handling=weights),dict(
        signal=dict(pure_append=append,literal_offer_retained=bool(matches),added_characters=len(added),
            unmatched_continuation_characters=max(0,len(added)-len(offer)) if matches else len(added),
            closest_offer_similarity=SequenceMatcher(None,offer,added,autojunk=False).ratio()),
        compatible_histories=[dict(handling=a,weight=w,facts=list(p.values())) for a,w,p in zip(ACTIONS,weights,prototypes) if w>0],
        limitation='Representative minimal transforms, not exhaustive historical identification; text deletion/restoration and human copying may be invisible; weights are uncalibrated fixed heuristics.')
