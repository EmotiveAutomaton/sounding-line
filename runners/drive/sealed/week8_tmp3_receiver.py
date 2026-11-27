"""TMP3 conversation receiver. All text, join keys and score panels stay in memory.

DESIGN CHECK (2026-11-27). Lessons read: LESSONS §§2–5. Gates,
null/alternative/direction: under the null of an unbound speaker or a missing
matched random head the component cannot run. Under the alternative, a
reciprocal dyad with ordered turns retains the correct speaker and rater.
The failure direction is a self/partner reversal or a trained-only comparison.
Verdict bands per arm, exhaustive: valid components pass to the reviewed
producer and disclosure gate; ambiguous joins or heads leave a void component.
"""
from collections import Counter, defaultdict
from dataclasses import dataclass
import math
from pathlib import Path

from runners.drive.sealed.week6_sc2_source_v1 import PINS as ORIGINAL
from runners.drive.sealed.week6_sc1_counts_v1 import source_layout

TRAITS=('extraversion','agreeable','conscientious','neurotic','open')
IDS=('conversation_id','user_id','partner_id')
OWN=('how_enjoyable','affect')
RATINGS=(*OWN,*[prefix+field for prefix in ('my_','your_') for field in TRAITS])
TEXT=('conversation_id','turn_id','speaker','utterance')
PINS={k:ORIGINAL[k] for k in ('survey','speech')}

@dataclass
class Speaker:
    conversation: str
    speaker: str
    turns: tuple
    outcomes: dict

def score(value,high,integer):
    if value is None or isinstance(value,bool):
        return None
    try:
        v=float(value)
    except (ValueError,TypeError):
        return None
    if not math.isfinite(v) or not 1<=v<=high or (integer and not v.is_integer()):
        return None
    return v

def project(surveys,turns):
    """Keep text ordered and align a reciprocal partner's rating to its target."""
    dyads=defaultdict(list); by_meeting=defaultdict(list)
    for row in surveys:
        dyads[row['conversation_id']].append(row)
    for t in turns:
        by_meeting[t['conversation_id']].append(t)
    result=[];excluded=Counter()
    for conv,rows in sorted(dyads.items()):
        if len(rows)!=2 or not isinstance(conv,str) or not conv:
            excluded['invalid_survey_pair']+=1;continue
        a,b=rows
        if (not all(isinstance(r['user_id'],str) and r['user_id'].strip() for r in rows)
                or a['user_id']==b['user_id'] or a['user_id']!=b['partner_id'] or b['user_id']!=a['partner_id']):
            excluded['invalid_survey_pair']+=1;continue
        text=by_meeting.get(conv,[])
        ids=[t['turn_id'] for t in text]
        if not ids or any(type(i) is not int or i<0 for i in ids) or len(set(ids))!=len(ids):
            excluded['ambiguous_turn_order']+=1;continue
        ordered=sorted(text,key=lambda t:t['turn_id'])
        # The provider describes speech recorded before a partner joins or
        # after departure. Apply the original edge trim, including its limit.
        content=ordered[1:-1]
        if any(t['speaker'] not in (a['user_id'],b['user_id']) or not isinstance(t['utterance'],str) for t in content):
            excluded['unknown_turn_speaker_or_text']+=1;continue
        for person,other in ((a,b),(b,a)):
            utterances=tuple(t['utterance'] for t in content if t['speaker']==person['user_id'] and t['utterance'].strip())
            if not utterances:
                excluded['no_turns_for_speaker']+=1;continue
            outcomes={k:score(person.get(k),9,True) for k in OWN}
            for trait in TRAITS:
                for dest,source,prefix in (('self',person,'my_'),('partner',other,'your_')):
                    v=score(source.get(prefix+trait),5,False)
                    outcomes[dest+'_'+trait]=v
            result.append(Speaker(conv,person['user_id'],utterances,outcomes))
    return result,dict(excluded)

def in_seal(source):
    """Read only the approved survey and the original timed transcript projection."""
    import pyarrow.parquet as pq
    base=source_layout(Path(source),PINS)
    raw=[]
    for kind,keys,optional in [('survey',IDS,RATINGS),('speech',TEXT,())]:
        with pq.ParquetFile(base/PINS[kind][0]) as pf:
            names=pf.schema_arrow.names
            if any(names.count(k)!=1 for k in keys):
                raise ValueError('Unavailable original source key')
            chosen=[*keys,*[k for k in optional if names.count(k)==1]]
            raw.append(pf.read(columns=chosen,use_threads=False).to_pylist())
    return project(*raw)

def pair_outputs(trained,random,fields):
    """Handle the result of the real adapter once its published schema binds."""
    if not fields or len(fields)!=len(set(fields)) or set(trained)!=set(random):
        raise ValueError('Unmatched learned and random output panels')
    for speaker in trained:
        for name in fields:
            a=trained[speaker].get(name);b=random[speaker].get(name)
            if a is None or b is None:
                continue
            if type(a) not in (int,float) or type(b) not in (int,float) or not math.isfinite(a) or not math.isfinite(b):
                continue
            yield speaker,name,a,b

def fixture():
    rows=[dict(conversation_id='one',user_id=k,partner_id=v,how_enjoyable=n,affect=4,
            my_extraversion=n,your_extraversion=z) for k,v,n,z in (('a','b',2,1),('b','a',3,4))]
    turns=[dict(conversation_id='one',turn_id=i,speaker=k,utterance=u) for i,k,u in
           [(4,'boundary','end'),(2,'b','An invented reply.'),(1,'a','One invented opening.'),(3,'a','The last invented turn.'),(0,'boundary','start')]]
    result,omitted=project(rows,turns)
    assert not omitted and len(result)==2 and result[0].turns==('One invented opening.','The last invented turn.')
    assert result[0].outcomes['partner_extraversion']==4 and result[0].outcomes['self_extraversion']==2
    assert result[1].outcomes['partner_extraversion']==1 and result[1].outcomes['self_open'] is None
    assert project(rows,turns+[turns[1]])[1]=={'ambiguous_turn_order':1}
    assert project([rows[0],dict(rows[1],partner_id='b')],turns)[0]==[]
    a={('one','a'):{'field':1.,'unpaired':2.}}
    b={('one','a'):{'field':0.,'unpaired':None}}
    assert list(pair_outputs(a,b,['field','unpaired']))==[(('one','a'),'field',1.,0.)]
    return dict(speakers=2,one_invented_conversation=True,ordered_turns=True,reciprocity=True,
                missing_trait_scoped=True,both_heads_required=True,real_producer_rehearsal_pending=True)
