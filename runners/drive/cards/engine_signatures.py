"""EV2: cross-prompt recurrence of the frozen engine's signature phrases.

DESIGN CHECK (2026-10-19): LESSONS sections 3-5 and CONTROLS sections 3,6,7
read for this build. Null: equal recurrence gives zero; a writer-specific planted
phrase gives a positive contrast. Prompt-only phrases cannot create an effect.
Session-label reassignments retain prompt rosters and fixed source rows. Their
absolute mean above .25 SD flags bias under either hypothesis. Missing matches
are an explicit S1 population, not zeros. Changed evidence, nonfinite values,
or failed replay refuse completion. Unsupported/invalid/negative/null/marginal/
positive bands are exhaustive; only a valid positive licenses recurrence.
No private-preference, attention, causal or out-of-corpus inference follows.
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import math
from pathlib import Path
import re

import numpy as np
from threadpoolctl import threadpool_limits

from runners.drive.engine_export_join import digest, exact_span
from runners.stage14.common import read, filehash, atomic
from . import engine_export_full as reader, states_v2
from .timing_pmap_source import bound_record
from .timing_p6 import gzread, gzip_equal, write_equal
from .timing_stats import bind, check_binding

CONFIG = dict(mode='full-reader', draws=2000, permutations=200, seed=20261018,
              min_signatures=200, min_writers=20)
CONSTRUCTED = dict(CONFIG, mode='constructed')


def matching(text, phrase):
    """Lowercase literal substring, including overlaps, as the pinned exporter.

    No whitespace/punctuation rewrite or invented word-boundary filter. The
    packet requests lowercase (not casefold); this distinction is retained.
    """
    if not phrase:
        raise ValueError('empty signature')
    return len(re.findall('(?='+re.escape(phrase.lower())+')', text.lower()))


def population(documents, values):
    if len(documents) != len(values) or not documents:
        raise ValueError('missing full document/export population')
    result = []
    for doc, value in zip(documents, values, strict=True):
        if (hashlib.sha256(doc['text'].encode('utf8')).hexdigest() != doc['textSha256']
                or value['keys'] != doc['keys'] or value['textSha256'] != doc['textSha256']
                or value['inputRecordSha256'] != digest(doc)):
            raise ValueError('export identity mismatch')
        keys = doc['keys']
        if any(not isinstance(keys[k], str) or not keys[k] for k in ('writer','session','prompt')):
            raise ValueError('missing writer/session/prompt identity')
        if value['status'] not in ('complete','unsupported'):
            raise ValueError('unfinished or failed export')
        raw = value['habits']['raw']
        words = raw['words'] + raw['quotedWords']
        if type(raw['words']) is not int or type(raw['quotedWords']) is not int or min(raw['words'],raw['quotedWords']) < 0:
            raise ValueError('invalid pinned word denominator')
        phrases = value['departurePhrases']
        if len(phrases) > 15:
            raise ValueError('not the pinned top15 phrase prefix')
        selected = set()
        for phrase in phrases:
            a,b = exact_span(doc['text'],phrase['span'])
            text = doc['text'][a:b]
            if not text or not math.isfinite(phrase['departure']):
                raise ValueError('invalid phrase')
            sections, paragraphs = set(),set()
            for occurrence in phrase['occurrences']:
                x,y = exact_span(doc['text'],occurrence['span'])
                if doc['text'][x:y].casefold() != text.casefold():
                    raise ValueError('false signature occurrence')
                sections.add(occurrence['section']); paragraphs.add(occurrence['region'])
            if (phrase['sectionSupport'] != len(sections) or phrase['paragraphSupport'] != len(paragraphs)
                    or type(phrase['recurring']) is not bool
                    or phrase['recurring'] != (phrase['departure'] > 0 and len(sections) >= 2)):
                raise ValueError('false exported recurrence declaration')
            if phrase['departure'] > 0 and (len(sections) >= 2 or len(paragraphs) >= 2):
                selected.add(text.lower())
        result.append(dict(**keys,text=doc['text'],words=words,signatures=sorted(selected)))
    result.sort(key=lambda r:r['session'])
    if len({r['session'] for r in result}) != len(result):
        raise ValueError('duplicate session')
    return result


def assignments(rows, permutations, seed):
    """Shuffle session ownership within prompt; preserve each writer/prompt count."""
    labels=np.array([r['writer'] for r in rows]); prompts=sorted({r['prompt'] for r in rows})
    rng=np.random.default_rng(seed)
    result=[labels]
    for _ in range(permutations):
        fake=labels.copy()
        for prompt in prompts:
            positions=np.array([i for i,r in enumerate(rows) if r['prompt']==prompt])
            fake[positions]=rng.permutation(labels[positions])
        result.append(fake)
    return result


def targets(rows, labels):
    """Metadata-only matched donor pools. Require support for every own prompt."""
    groups=defaultdict(list); by_prompt=defaultdict(list)
    for i,(row,writer) in enumerate(zip(rows,labels,strict=True)):
        groups[(str(writer),row['prompt'])].append(i); by_prompt[row['prompt']].append(i)
    result={}
    for writer,source_prompt in sorted(groups):
        matched=[]
        for prompt in sorted(by_prompt):
            if prompt==source_prompt or (writer,prompt) not in groups: continue
            own=groups[writer,prompt]
            other=[i for i in by_prompt[prompt] if labels[i]!=writer]
            a=sum(rows[i]['words'] for i in own);b=sum(rows[i]['words'] for i in other)
            if a<=0 or b<=0:
                matched=[];break
            matched.append((own,other,a,b))
        result[writer,source_prompt]=matched
    return result


def evaluate(rows, labels, pools, counts, phrase_index, source_ids):
    values={}; own_rates={}; other_rates={}
    for i in source_ids:
        row=rows[i]; ps=[phrase_index[p] for p in row['signatures']]
        match=pools[str(labels[i]),row['prompt']]
        if not match:raise ValueError('fixed source row lost matched support')
        denominator=sum(a for _,_,a,_ in match)
        own=np.zeros(len(ps)); other=np.zeros(len(ps))
        for own_ids,other_ids,a,b in match:
            own+=counts[np.ix_(ps,own_ids)].sum(axis=1)
            other+=counts[np.ix_(ps,other_ids)].sum(axis=1)*(a/b)
        own*=10000/denominator;other*=10000/denominator
        own_rates[i]=own.tolist();other_rates[i]=other.tolist()
        values[i]=float(np.mean(own-other))
    return values,own_rates,other_rates


def cluster_means(rows, values, writers):
    return np.array([np.mean([v for i,v in values.items() if rows[i]['writer']==w]) for w in writers])


def interval(values, draws, seed):
    rng=np.random.default_rng(seed)
    samples=np.mean(values[rng.integers(0,len(values),(draws,len(values)))],axis=1)
    low,high=np.quantile(samples,[.025,.975]).tolist();effect=float(np.mean(values))
    return dict(effect=effect,ci_low=low,ci_high=high,
                state=states_v2.contrast_state(effect,low,high),writers=len(values),draws=draws)


def reference(samples, observed):
    samples=np.asarray(samples,float)
    if len(samples)<2 or not np.isfinite(samples).all():raise ValueError('invalid control draws')
    mean=float(np.mean(samples));sd=float(np.std(samples,ddof=1))
    low,high=np.quantile(samples,[.025,.975]).tolist()
    return dict(mean=mean,sd=sd,q025=low,q975=high,
                biased=abs(mean)>.25*sd, draws=len(samples),
                p_one_sided_descriptive=float((1+np.sum(samples>=observed))/(1+len(samples))))


def analyze(rows, config, progress=lambda x:None):
    rows=sorted(rows,key=lambda r:r['session'])
    if len({r['session'] for r in rows})!=len(rows):raise ValueError('duplicate session')
    labels=assignments(rows,config['permutations'],config['seed'])
    pools=[targets(rows,a) for a in labels]
    candidates=[i for i,r in enumerate(rows) if r['signatures']]
    eligible=[i for i in candidates if all(p[str(a[i]),rows[i]['prompt']] for a,p in zip(labels,pools))]
    writers=sorted({rows[i]['writer'] for i in eligible})
    support=dict(documents=len(rows),signature_documents=len(candidates),
        signatures=sum(len(rows[i]['signatures']) for i in candidates),
        signature_writers=len({rows[i]['writer'] for i in candidates}),
        matched_documents=len(eligible),matched_signatures=sum(len(rows[i]['signatures']) for i in eligible),
        matched_writers=len(writers),dropped_documents=len(candidates)-len(eligible))
    dispositions=[dict(session=r['session'],writer=r['writer'],signatures=len(r['signatures']),
        status='matched' if i in eligible else 'no-signature' if i not in candidates else 'unsupported-matched-prompt-roster') for i,r in enumerate(rows)]
    if support['matched_signatures']<config['min_signatures'] or len(writers)<config['min_writers']:
        return dict(card='EV2',status='complete',state='unsupported',support=support,
                    badge=None,reason='signature/writer or common matched-support floor'),dict(dispositions=dispositions)
    phrases=sorted({p for i in eligible for p in rows[i]['signatures']}); pindex={p:i for i,p in enumerate(phrases)}
    counts=np.array([[matching(r['text'],p) for r in rows] for p in phrases],dtype=np.int64)
    matrices=[]; source_rates=None
    for k,(assignment,pool) in enumerate(zip(labels,pools)):
        values,own,other=evaluate(rows,assignment,pool,counts,pindex,eligible)
        matrices.append(cluster_means(rows,values,writers))
        if k==0:source_rates=[dict(session=rows[i]['session'],writer=rows[i]['writer'],phrases=rows[i]['signatures'],own=own[i],other=other[i]) for i in eligible]
        if k%10==0:progress(dict(phase='reassignments',completed=k,total=config['permutations']))
    matrices=np.array(matrices); primary=interval(matrices[0],config['draws'],config['seed']+1)
    paired=interval(matrices[0]-matrices[1:].mean(axis=0),config['draws'],config['seed']+1)
    control=reference(matrices[1:].mean(axis=1),primary['effect'])
    state='invalid' if control['biased'] else primary['state']
    badge='recurs in the writer\'s other work' if state=='positive' else 'page-local' if state=='null' else None
    summary=dict(card='EV2',status='complete',state=state,primary=primary,paired_fake_writer_contrast=paired,
        reassignment_reference=control,support=support,badge=badge,
        population='S1 common supported document-signatures across real and all200 prompt-stratified session reassignments',
        interpretation='Final-document phrase recurrence only; original population remains open where support is missing',
        interval_scope='Equal writer means of equal source-document means; phrase and comparison pools frozen, real-writer paired resampling',
        family_counter=False,descriptive=True)
    return summary,dict(dispositions=dispositions,source_rates=source_rates,writers=writers,
                        writer_means_by_assignment=matrices.tolist(),counts_sha256=digest(counts.tolist()))


def load(inputs, config):
    if config not in (CONFIG,CONSTRUCTED):raise ValueError('unregistered EV2 configuration')
    if config==CONSTRUCTED:
        if set(inputs)!={'fixture'}:raise ValueError('constructed input only')
        fixture=read(inputs['fixture']);return population(fixture['documents'],fixture['exports'])
    if set(inputs)!={'reader_completion'}:raise ValueError('authenticated reader completion required')
    root,plan=reader.authenticate(inputs['reader_completion'],'runners.drive.cards.engine_export_full')
    if plan['config']['mode']!='full-reader':raise ValueError('complete full-reader parent required')
    records,_,_,_=reader.load(plan['inputs'],plan['config'])
    values=gzread(root/'output/FEATURES.json.gz')
    return population([r['document'] for r in records],values)


def run(output,inputs,config,operation):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if operation=='verify' or (output/'TIMING_BINDINGS.json').exists():check_binding(output,inputs,config)
    with threadpool_limits(limits=1):
        rows=load(inputs,config)
        summary,detail=analyze(rows,config,lambda p:atomic(output/'PROGRESS.json',p))
    if operation=='execute':
        write_equal(output/'SUMMARY.json',summary);gzip_equal(output/'DETAIL.json.gz',detail)
        if not (output/'TIMING_BINDINGS.json').exists():bind(output,inputs,config,['SUMMARY.json','DETAIL.json.gz'])
        return summary
    if summary!=read(output/'SUMMARY.json') or detail!=gzread(output/'DETAIL.json.gz'):
        raise ValueError('fresh source/statistic/control reconstruction differs')
    return dict(verified=True,summary=summary,fresh_source_authentication=True,
                full_statistic_replay=True,full_control_replay=True)


def execute(output,inputs,config):return run(output,inputs,config,'execute')
def verify(output,inputs,config):return run(output,inputs,config,'verify')
