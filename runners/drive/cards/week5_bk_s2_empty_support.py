"""Isolated S2 empty-timing-stratum guard; original h1 projection unchanged.

DESIGN CHECK: BK_S2_EMPTY_SUPPORT.md, LESSONS2/3/5. Empty strata retain all
source rows and receive no threshold/class; nonempty and tied thirds are exact
original computations. Nonfinite eligible values still fail the strict ruler.
"""
from collections import Counter,defaultdict
import math
import numpy as np
from .week5_bk_s2_source_h1 import project,private_key,SEED,produced_words
from .week4_timing_ruler import thirds


def classify_and_controls(sessions):
    by_writer=defaultdict(list);bigram=defaultdict(lambda:defaultdict(list));words=defaultdict(list)
    for session in sessions:
        by_writer[session['writer']].extend(r for r in session['sentences'] if r['timing_state']=='eligible')
        for key,value in session.pop('bigram_intervals').items():bigram[session['writer']][key].extend(value)
        words[session['writer']].append(session)
    support=[dict(writer=writer,eligible_timing_sentences=len(rows),status="eligible_timing_present" if rows else "no_eligible_timing") for writer,rows in sorted(by_writer.items())]
    for writer,rows in by_writer.items():
        if not rows:continue
        labels,cuts=thirds([r['hesitancy'] for r in rows])
        for row,label in zip(rows,labels):row['class']=label
    for writer,group in words.items():
        medians={k:float(np.median(v)) for k,v in bigram[writer].items()};all_intervals=[v for values in bigram[writer].values() for v in values]
        fallback=float(np.median(all_intervals)) if all_intervals else None
        history=Counter();total=0
        for session in sorted(group,key=lambda s:(s['timestamp'],s['session'])):
            allwords=session.pop('first_words');births={}
            for word in sorted(allwords,key=lambda w:w['ordinal']):
                births[word['ordinal']]=math.log((history[word['token']]+1)/(total+len(history)+1))
                history[word['token']]+=1;total+=1
            for row in session['sentences']:
                if row['timing_state']!='eligible':continue
                ws=row['words'];freq=[w['population_log_frequency'] for w in ws]
                if any(x is None or not math.isfinite(x) for x in freq):row['timing_state']='missing_population_frequency';continue
                pair_values=[medians.get(w['token'][i:i+2],fallback) for w in ws for i in range(len(w['token'])-1)]
                if not pair_values or any(x is None or x<=0 for x in pair_values):row['timing_state']='missing_bigram_ruler';continue
                row['controls']=dict(sentence_length=len(ws),mean_word_length=float(np.mean([w['length'] for w in ws])),
                    population_log_frequency=float(np.mean(freq)),own_prior_log_frequency=float(np.mean([births[w['ordinal']] for w in ws])),
                    bigram_log_seconds=float(np.mean(np.log(pair_values))),paragraph_boundary=int(row['paragraph_start']),
                    sentence_boundary=1,time_on_task_minutes=row['start_seconds']/60,session_order=session['session_order'],
                    distance_sentences=row['distance_sentences'],remaining_minutes=row['remaining_seconds']/60)
    return support
