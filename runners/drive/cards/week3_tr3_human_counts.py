"""TR3 discovery human-production counts; no selection or carryover estimate.

DESIGN CHECK: LESSONS sections 2-5 read 2026-10-27. NULL and ALTERNATIVE
require exact known text counts, preserved later-deleted production, no mixed
API/user phrase and no cursor-concatenation fiction. Failure direction: any
source, Unicode, chronology, population or replay mismatch refuses admission.
Exhaustive states are verified counts or failure, never an empirical verdict.
"""
from collections import Counter
import hashlib
import math
from pathlib import Path
import time
import unicodedata

from runners.stage9.coauthor import units, text_of
from .timing_text import TOKEN, WORD
from .timing_census import read, filehash
from .timing_pmap_source import completed
from .timing_p6 import gzread, gzip_equal, write_equal, progress
from .week3_tr3_candidates import discovery_roster


def production_counts(unit):
    """Completed production, extended to wholly user-owned word 1-3 grams.

    Like the existing produced-word ledger, a word completes after a new typed
    separator, an edit elsewhere, or session end. Composition immediately
    revised/deleted before completion is not a word occurrence. Occurrence keys
    use lexical character identities, so re-scanning or changing whitespace
    cannot duplicate them. Literal punctuation counts when the user inserts it.
    """
    doc = units(unit['initial_document']); owners = [-1]*len(doc)
    born = []; counts = Counter(); observed = set(); pending = {}
    previous_ordinal = -1; previous_stamp = -float('inf'); edits = 0

    def save(key, support):
        if key not in observed:
            observed.add(key); counts[key[0]] += 1
        pending.pop(key, None)

    def boundary(position):
        if not 0 <= position <= len(doc):
            raise ValueError('UTF-16 boundary outside document')
        if 0 < position < len(doc) and 0xD800 <= doc[position-1] <= 0xDBFF and 0xDC00 <= doc[position] <= 0xDFFF:
            raise ValueError('split UTF-16 surrogate')

    def collect(left, right, ordinal, final=False, allowed_keys=None):
        # At most three adjacent whitespace chunks on each side suffice for
        # trigrams; a large single insertion/deletion still scans its full span.
        if final:
            left, right = 0, len(doc)
        else:
            for _ in range(3):
                while left > 0 and not chr(doc[left-1]).isspace(): left -= 1
                while left > 0 and chr(doc[left-1]).isspace(): left -= 1
                while right < len(doc) and not chr(doc[right]).isspace(): right += 1
                while right < len(doc) and chr(doc[right]).isspace(): right += 1
        fragment = text_of(doc[left:right]); offsets = [0]
        for ch in fragment: offsets.append(offsets[-1]+len(units(ch)))
        run = []; last_end = 0
        for match in TOKEN.finditer(fragment):
            gap = fragment[last_end:match.start()]
            if any(not c.isspace() for c in gap): run = []
            last_end = match.end()
            if not WORD.fullmatch(match.group()):
                run = []
                continue
            a,b = left+offsets[match.start()],left+offsets[match.end()]
            ids = tuple(dict.fromkeys(owners[a:b]))
            if not ids or -1 in ids:
                run = []
                continue
            run = (run+[(match.group().casefold(),a,b,ids)])[-3:]
            for n in range(1,len(run)+1):
                part = run[-n:]; begin = part[0][1]
                support = frozenset(owners[begin:b])
                # Whitespace produced by an API/initial source is not typing.
                if -1 in support: continue
                lexical = tuple(identity for token in part for identity in token[3])
                key = (f'w{n}:'+' '.join(token[0] for token in part),lexical)
                if allowed_keys is not None and key not in allowed_keys: continue
                if key in observed: continue
                right_owner = owners[b] if b < len(owners) else -1
                new_separator = right_owner >= 0 and born[right_owner] >= max(born[i] for i in lexical)
                if final or new_separator:
                    save(key,support)
                else:
                    pending[key] = support

    for edit in unit['edits']:
        ordinal,stamp = edit['ordinal'],edit['timestamp']
        if type(ordinal) is not int or ordinal <= previous_ordinal or type(stamp) not in (int,float) or not math.isfinite(stamp) or stamp < previous_stamp:
            raise ValueError('edit chronology differs')
        previous_ordinal,previous_stamp = ordinal,stamp
        ops=edit['operations'];touched=set();cursor=0
        for op in ops:
            actions=set(op)&{'insert','retain','delete'}
            if len(actions)!=1 or set(op)-{'insert','retain','delete','attributes'}:
                raise ValueError('unsupported delta operation')
            if 'insert' in actions:
                if not isinstance(op['insert'],str): raise ValueError('inserted text required')
                boundary(cursor);touched.update(owners[max(0,cursor-1):cursor+1])
            else:
                key=next(iter(actions));count=op[key]
                if type(count) is not int or count < 0: raise ValueError('invalid delta count')
                boundary(cursor);boundary(cursor+count)
                if key=='delete': touched.update(owners[max(0,cursor-1):min(len(doc),cursor+count+1)])
                cursor += count
        affected_pending=set()
        for key,support in list(pending.items()):
            if touched.isdisjoint(support): save(key,support)
            else:
                affected_pending.add(key);pending.pop(key)
        out=[];provenance=[];position=0;affected=[]
        for op in ops:
            if 'insert' in op:
                begin=len(out)
                for char in op['insert']:
                    values=units(char);identity=-1
                    if edit['source']=='user':
                        identity=len(born);born.append(ordinal)
                        if unicodedata.category(char).startswith('P'):
                            save(('p:'+char,(identity,)),frozenset((identity,)))
                    out.extend(values);provenance.extend([identity]*len(values))
                affected.append((max(0,begin-1),len(out)))
            elif 'retain' in op:
                stop=position+op['retain'];out.extend(doc[position:stop]);provenance.extend(owners[position:stop]);position=stop
            else:
                position+=op['delete'];affected.append((max(0,len(out)-1),len(out)))
        out.extend(doc[position:]);provenance.extend(owners[position:]);doc,owners=out,provenance
        if edit['source']=='user':
            for left,right in affected: collect(left,right,ordinal)
        elif affected_pending:
            # Retain a previously user-formed pending word if a non-user edit
            # leaves that exact lexical occurrence and adjacency unchanged.
            for left,right in affected: collect(left,right,ordinal,allowed_keys=affected_pending)
        edits+=1
    # Finish only phrases actually formed by a user edit. An API deletion
    # joining old typed fragments cannot invent a new human-produced phrase.
    for key,support in list(pending.items()): save(key,support)
    if text_of(doc)!=unit['final_document']: raise ValueError('final document differs')
    if len(born)!=unit['user_inserted_characters']: raise ValueError('typed character denominator differs')
    return dict(session=unit['session'],writer=unit['writer'],prompt=unit['prompt'],
        feature_counts=dict(sorted(counts.items())),typed_characters=len(born),edits=edits,
        scope='Completed produced word 1-3 grams with wholly typed lexical text and intervening whitespace; literal typed punctuation; later deletions retained')


def run(output,inputs,config,verification=False):
    mode=config.get('mode')
    if config!=dict(mode=mode,seed=20261026) or mode not in ('constructed','full'):
        raise ValueError('frozen human-count configuration required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);started=time.process_time()
    if mode=='constructed':
        if set(inputs)!={'fixture'}: raise ValueError('fixture required')
        f=read(inputs['fixture']);census,split=f['census'],f['split'];parent=None
    else:
        if set(inputs)!={'exposure_completion','typing_completion'}: raise ValueError('exact completed parents required')
        source=Path(inputs['exposure_completion']).parent;parent=Path(inputs['typing_completion']).parent
        for name in ('CENSUS.json','WB1_WRITER_SPLIT.json'): completed(inputs['exposure_completion'],source/'output'/name)
        completed(inputs['typing_completion'],parent/'output/SUMMARY.json')
        census=read(source/'output/CENSUS.json');split=read(source/'output/WB1_WRITER_SPLIT.json')
    selected=discovery_roster(census,split,mode=='full');counts=Counter();support=Counter();stats=Counter();bindings=[]
    for i,r in enumerate(selected):
        sid=r['session'];name=hashlib.sha256(sid.encode()).hexdigest()+'.json.gz'
        if parent is None:
            unit=f['units'][sid];h=None
        else:
            path=parent/'output/sessions'/name;completed(inputs['typing_completion'],path);h=filehash(path);unit=gzread(path)
        if any(unit[k]!=r[k] for k in ('session','writer','prompt')): raise ValueError('typing identity differs')
        row=production_counts(unit)
        if row['typed_characters']!=r['typed_inserted_characters']: raise ValueError('exposure denominator differs')
        if verification:
            if gzread(output/'sessions'/name)!=row: raise ValueError('human counts replay differs')
        else: gzip_equal(output/'sessions'/name,row)
        counts.update(row['feature_counts']);support.update(row['feature_counts'].keys())
        stats.update(typed_characters=row['typed_characters'],edits=row['edits'])
        bindings.append(dict(session=sid,source_sha256=h))
        progress(output/'PROGRESS.json',dict(phase='verify-human-counts' if verification else 'human-counts',done=i+1,total=len(selected)))
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists(): raise InterruptedError('human counts yield at complete session boundary')
    summary=dict(stats,sessions=len(selected),writers=len({r['writer'] for r in selected}),
        candidate_features=len(counts),full_discovery_half=mode=='full',constructed=mode=='constructed',
        test_payloads_read=0,features_selected=False,scientific_admission=False,
        scope='Discovery human-production counts only; no feature selection, matched exposure or carryover outcome')
    payloads={'SUMMARY.json':summary,'COUNTS.json':dict(counts=dict(sorted(counts.items())),session_support=dict(sorted(support.items()))),
        'BINDING.json':dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()},units=bindings)}
    for name,value in payloads.items():
        if verification:
            if read(output/name)!=value: raise ValueError('human aggregate replay differs')
        else: write_equal(output/name,value)
    if verification:return dict(verified=True,complete_human_counts_replay=True,scientific_admission=False)
    if not (output/'TIMING.json').exists():write_equal(output/'TIMING.json',dict(cpu_seconds=time.process_time()-started,sessions=len(selected)))
    return dict(status='complete',counts_only=True,scientific_admission=False,summary=summary)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
