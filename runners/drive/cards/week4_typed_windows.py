"""Authenticated typed-window input for S1; no recurrence outcome or effect.

DESIGN CHECK: Week4 S1/0.5 and LESSONS2-5 reviewed 2026-11-02. Actual typed
adjacency must survive punctuation, but cannot bridge API/prompt text, a
backward production clock or a second version of an already-started word.
Later deletion never selects a word out. Known stops, nonoverlap, breaks and
sentence-local skeletons reproduce before complete-source admission.
"""
from pathlib import Path
from collections import Counter,defaultdict
import time
from .timing_pmap_source import completed,bound_record
from .timing_p6 import write_equal,gzip_equal,gzread,progress
from .timing_census import read,filehash
from .week4_timing_ruler import stretch_hesitancy,thirds

CONFIG=dict(card='S1-typed-windows',seed=20261102,expected_sessions=1399,window_words=8,dictionary_words=150)


def produced_words(records):
    """Keep the first completed word per original onset, without future flags.

    Revising an existing word can create another ledger version sharing its
    original first character. It is not a second production onset. A multiword
    insertion shares an ordinal too; it cannot have eligible single-char
    onset timing and is counted at that later join, never given invented times.
    """
    selected={};counts=Counter()
    for row in sorted((r for r in records if r['is_word']),key=lambda r:(r['ordinal'],r['completed_ordinal'],r['index'])):
        if row['ordinal'] in selected:counts['repeated_original_onset_versions']+=1
        else:selected[row['ordinal']]=row
    return list(selected.values()),counts


def connected(previous,current,lookup):
    """All intervening typed tokens must be punctuation in forward chronology."""
    at=current.get('previous_typed_token_index');seen=set();upper=current['ordinal']
    while at is not None:
        if at in seen or at not in lookup:return False
        seen.add(at);row=lookup[at]
        if row['ordinal']>upper or row['completed_ordinal']>current['completed_ordinal']:return False
        if at==previous['index']:return previous['ordinal']<current['ordinal']
        if row['is_word'] or row['ordinal']<previous['ordinal']:return False
        upper=row['ordinal'];at=row.get('previous_typed_token_index')
    return False


def skeleton_grams(words,dictionary,n=4):
    segments=[];current=[]
    for row in words:
        if row['sentence_start'] and current:segments.append(current);current=[]
        current.append(row['token'] if row['token'] in dictionary else '<content>')
    if current:segments.append(current)
    return [list(seq[i:i+n]) for seq in segments for i in range(len(seq)-n+1)
            if any(t!='<content>' for t in seq[i:i+n])]


def session_windows(record,intervals,dictionary,size=8):
    words,counts=produced_words(record['words']);lookup={r['index']:r for r in record['words']}
    if len(lookup)!=len(record['words']):raise ValueError('Duplicate typed occurrence')
    onset={}
    for r in intervals:
        if r['onset']:
            if r['ordinal'] in onset:raise ValueError('Duplicate timing onset')
            onset[r['ordinal']]=r
    windows=[];i=0
    while i<len(words):
        first=onset.get(words[i]['ordinal'])
        if first is None:counts['words_without_timed_onset']+=1;i+=1;continue
        if not first['stop']:i+=1;continue
        block=words[i:i+size]
        if len(block)!=size:counts['stop_without_full_window']+=1;i+=1;continue
        if any(not connected(a,b,lookup) for a,b in zip(block,block[1:])):
            counts['stop_with_disconnected_window']+=1;i+=1;continue
        timings=[onset.get(w['ordinal']) for w in block]
        # A formed contiguous candidate occupies its words even if unusable.
        i+=size;counts['formed_windows']+=1
        if any(t is None for t in timings):counts['window_missing_internal_timing']+=1;continue
        h=stretch_hesitancy(timings)
        if h['state']!='eligible':counts['window_'+h['state']]+=1;continue
        grams=skeleton_grams(block,dictionary)
        if not grams:counts['window_without_informative_gram']+=1
        windows.append(dict(indices=[r['index'] for r in block],ordinals=[r['ordinal'] for r in block],
            start_ordinal=block[0]['ordinal'],hesitancy=h['hesitancy'],grams=grams,
            words=[{k:r[k] for k in ('token','ordinal','sentence_start','length','seconds','index')} for r in block]))
    counts['eligible_timing_windows']=len(windows)
    return windows,dict(counts)


def classify(sessions):
    by_writer=defaultdict(list)
    for session in sessions:
        for window in session['windows']:by_writer[session['writer']].append(window)
    support={}
    for writer,windows in sorted(by_writer.items()):
        labels,cuts=thirds([w['hesitancy'] for w in windows])
        for w,label in zip(windows,labels):w['class']=label
        counts=Counter(labels);informative=Counter(w['class'] for w in windows if w['grams'])
        support[writer]=dict(cuts=cuts,classes=dict(counts),informative_classes=dict(informative),
            candidate_supported=informative['flow']>=20 and informative['hesitant']>=20)
    return support


def run(output,inputs,config,verification=False):
    if config!=CONFIG:raise ValueError('Frozen S1 input configuration required')
    if set(inputs)!={'p6_index','p6_completion','timing_completion'}:raise ValueError('Unexpected S1 inputs')
    start=time.process_time();output=Path(output);index=read(inputs['p6_index'])
    completed(inputs['p6_completion'],inputs['p6_index'])
    if len(index)!=config['expected_sessions']:raise ValueError('Wrong P6 primary population')
    timing=Path(inputs['timing_completion']);tr=timing.parent/'output'
    for name in ('PRIVATE_ROSTER.json','INTERVALS.json.gz'):completed(timing,tr/name)
    roster={r['session']:r for r in read(tr/'PRIVATE_ROSTER.json')};intervals=gzread(tr/'INTERVALS.json.gz')
    ids={r['session'] for r in index}
    if len(ids)!=len(index) or ids!=set(roster) or ids!=set(intervals):raise ValueError('Exact population join failed')
    records=[];counts=Counter()
    for i,row in enumerate(index):
        r=bound_record(inputs['p6_index'],row)
        if r['session']!=row['session'] or r['writer']!=roster[r['session']]['writer']:raise ValueError('Writer/session join failed')
        records.append(r)
        # Frozen dictionary uses all completed typed word occurrences, including
        # revisions/deletions. Candidate-onset deduplication is a separate rule.
        counts.update(w['token'] for w in r['words'] if w['is_word'])
    dictionary=sorted(counts,key=lambda t:(-counts[t],t))[:config['dictionary_words']]
    frozen=dict(words=dictionary,counts={w:counts[w] for w in dictionary},total_words=sum(counts.values()),
        rule='Completed writer-produced word occurrences; Unicode casefold, frequency descending, lexical ties; no outcome used.')
    if not verification:write_equal(output/'FROZEN_DICTIONARY.json',frozen)
    sessions=[];total=Counter()
    for i,r in enumerate(records):
        windows,census=session_windows(r,intervals[r['session']],set(dictionary),config['window_words'])
        total.update(census)
        sessions.append(dict(session=r['session'],writer=r['writer'],prompt=r['prompt'],timestamp=r['timestamp'],end_at=r['end_at'],
            genre=roster[r['session']]['genre'],session_order=roster[r['session']]['session_order'],windows=windows,census=census))
        progress(output/'PROGRESS.json',dict(phase='verify' if verification else 'windows',done=i+1,total=len(records)))
    support=classify(sessions)
    summary=dict(sessions=len(sessions),writers=len({s['writer'] for s in sessions}),dictionary_words=len(dictionary),
        census=dict(total),writers_meeting_window_floor_before_donor_support=sum(r['candidate_supported'] for r in support.values()),
        required_writers=25,scientific_effect_computed=False,scope='Timing/window source support only; exact earlier donor capacity remains to be checked.')
    values={'SUMMARY.json':summary,'FROZEN_DICTIONARY.json':frozen,'PRIVATE_SUPPORT.json':support,
        'BINDING.json':dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()},sources=index)}
    if verification:
        for name,value in values.items():
            if read(output/name)!=value:raise ValueError('S1 source replay differs: '+name)
        if gzread(output/'WINDOWS.json.gz')!=sessions:raise ValueError('S1 window replay differs')
        return dict(verified=True,complete_source_replay=True)
    for name,value in values.items():write_equal(output/name,value)
    gzip_equal(output/'WINDOWS.json.gz',sessions)
    write_equal(output/'TIMING.json',dict(cpu_seconds=time.process_time()-start))
    return dict(status='complete',scientific_admission=False)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
