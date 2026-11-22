"""Wire the frozen D33 operator to a projected conversation word clock."""
from collections import Counter, defaultdict
import math

from runners.drive.cards import timing_d33 as d33
from runners.drive.cards.timing_checkpoint import regression
from runners.drive.cards.week6_sealed_support_v1 import write_tables, SealedFailure


def project(conversations):
    """Each span is an actual timed word. Session and turn clocks are different."""
    if len({c['conversation'] for c in conversations})!=len(conversations):
        raise ValueError('ambiguous conversation key')
    speakers=defaultdict(list)
    for c in sorted(conversations,key=lambda x:(x['start'],x['conversation'])):
        if not math.isfinite(c['start']) or not math.isfinite(c['end']) or c['end']<=c['start']:
            raise ValueError('unknown conversation chronology')
        rows=defaultdict(list);sequences=defaultdict(list)
        for turn in c['turns']:
            p=turn['speaker'];tokens=[];last_end=None
            if not p:raise ValueError('unbound speaker')
            for word in turn['words']:
                token=word['token'].casefold()
                start,end=word['start'],word['end']
                if not token or not math.isfinite(start) or not math.isfinite(end) or not 0<=start<end<=c['end']-c['start']:
                    raise ValueError('unbound word time')
                if last_end is not None and start<last_end:
                    raise ValueError('overlapping word clocks')
                rows[p].append(dict(index=len(rows[p]),is_word=True,token=token,context=tokens[-1:],
                    length=len(token),sentence_start=word['sentence_start'],after_punctuation=word['after_punctuation'],
                    pause_seconds=None if last_end is None else start-last_end))
                tokens.append(token);last_end=end
            if tokens:sequences[p].append(tokens)
        for p in rows:
            speakers[p].append(dict(writer=p,session=c['conversation'],timestamp=c['start'],
                end_at=c['end'],training_sequences=sequences[p],words=rows[p]))
    sessions=[s for group in speakers.values() for s in group]
    for p,group in speakers.items():
        if len({s['timestamp'] for s in group})!=len(group):
            raise ValueError('unresolved same-speaker conversation order')
        for session in group:
            # All other speakers, restricted to previously completed conversations.
            others=(s for s in sessions if s['writer']!=p)
            field=d33.cache(others,session['timestamp'])
            uni,_,_,total=field
            for word in session['words']:
                if not total:
                    word.update(population_probability=None,population_log_frequency=None)
                    continue
                prior=(uni[word['token']]+1)/(total+len(uni)+1)
                probability=d33.cache_probability(word,field,prior)
                word.update(population_probability=probability,population_log_frequency=math.log(prior))
    return sessions


def run(conversations,out,draws=2000):
    sessions=project(conversations)
    rows,_,_=d33.make_rows(sessions,'word',False)
    people={r['writer'] for r in rows}
    if len(people)<11:raise SealedFailure(12,'insufficient evaluation speakers')
    cfg=dict(extension=False,bootstrap_draws=draws,seed=20261017)
    result=d33.analyze(rows,cfg)
    # Retain the original matched model controls when reading the field's term.
    nuis=[[r['population_surprisal'],r['personal_surprise'],1.,r['length'],
           r['log_frequency'],r['sentence_start'],r['after_punctuation']] for r in rows]
    field=regression(nuis,[r['log_pause'] for r in rows],[r['writer'] for r in rows],
                     random_intercept=True,draws=draws,seed=cfg['seed'])
    estimates=[]
    for code,item in enumerate((field,result,result.get('controls',{}).get('donor'),
                                 result.get('controls',{}).get('within_writer_surprise_shuffle')),1):
        if item and 'effect' in item:
            estimates.append(dict(measure=code,estimate=item['effect'],lower=item['ci_low'],
                                  upper=item['ci_high'],n=len(people)))
    return write_tables(out,dict(timing=estimates,
        support=[dict(evaluation_words=len(rows),n=len(people))]))
