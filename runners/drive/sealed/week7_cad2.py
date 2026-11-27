"""Wire the frozen D33 operator to a projected conversation word clock."""
from collections import Counter, defaultdict
import math

from runners.drive.cards import timing_d33 as d33
from runners.drive.cards.timing_checkpoint import regression
from runners.drive.cards.week6_sealed_support_v1 import write_tables, SealedFailure


class OtherSpeakerCounts:
    def __init__(self, everyone, own):
        self.everyone = everyone
        self.own = own

    def __getitem__(self, key):
        return self.everyone[key] - self.own[key]


def assign_field_probabilities(sessions):
    """Accumulate each completed session once; exclude the target's entire history."""
    completed = sorted(sessions, key=lambda s: s['end_at'])
    everyone = (Counter(), Counter(), Counter())
    own_counts = defaultdict(lambda: (Counter(), Counter(), Counter()))
    own_words = Counter()
    total_words = 0
    cursor = 0
    for target in sorted(sessions, key=lambda s: s['timestamp']):
        while cursor < len(completed) and completed[cursor]['end_at'] < target['timestamp']:
            session = completed[cursor]
            writer = session['writer']
            uni, bi, contexts, n = d33.cache([session], math.inf)
            for combined, personal, increment in zip(everyone, own_counts[writer], (uni, bi, contexts)):
                combined.update(increment)
                personal.update(increment)
            total_words += n
            own_words[writer] += n
            cursor += 1
        writer = target['writer']
        own = own_counts[writer]
        total = total_words - own_words[writer]
        field = tuple(OtherSpeakerCounts(a,b) for a,b in zip(everyone,own)) + (total,)
        own_only = sum(everyone[0][word] == count for word,count in own[0].items())
        vocabulary = len(everyone[0]) - own_only
        for word in target['words']:
            if not total:
                word.update(population_probability=None,population_log_frequency=None)
                continue
            prior = (field[0][word['token']]+1)/(total+vocabulary+1)
            word.update(population_probability=d33.cache_probability(word,field,prior),
                        population_log_frequency=math.log(prior))


def project(conversations, *, chronological_stream=False, keep_rows_for=None):
    """Each span is an actual timed word. Session and turn clocks are different."""
    seen=set()
    speakers=defaultdict(list)
    stream=conversations if chronological_stream else sorted(conversations,key=lambda x:(x['start'],x['conversation']))
    last_start=-math.inf
    for c in stream:
        if c['conversation'] in seen or c['start']<last_start:
            raise ValueError('ambiguous conversation chronology')
        seen.add(c['conversation'])
        last_start=c['start']
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
                if keep_rows_for is None or p in keep_rows_for:
                    rows[p].append(dict(index=len(rows[p]),is_word=True,token=token,context=tokens[-1:],
                        length=len(token),sentence_start=word['sentence_start'],after_punctuation=word['after_punctuation'],
                        pause_seconds=None if last_end is None else start-last_end))
                tokens.append(token);last_end=end
            if tokens:sequences[p].append(tokens)
        for p in sequences:
            speakers[p].append(dict(writer=p,session=c['conversation'],timestamp=c['start'],
                end_at=c['end'],training_sequences=sequences[p],words=rows[p]))
    sessions=[s for group in speakers.values() for s in group]
    for p,group in speakers.items():
        if len({s['timestamp'] for s in group})!=len(group):
            raise ValueError('unresolved same-speaker conversation order')
    assign_field_probabilities(sessions)
    return sessions


def run(conversations,out,draws=2000,*,chronological_stream=False,keep_rows_for=None):
    sessions=project(conversations,chronological_stream=chronological_stream,keep_rows_for=keep_rows_for)
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
