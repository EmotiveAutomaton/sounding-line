"""Private, field-allowlisted B-roll selection loader with person/script sealing.

DESIGN CHECK: I02/H03/X01/X02/X08. Read released CSVs as data only. Script word
types are Bernoulli opportunities; highlights are not mutually exclusive actions.
Trial chronology is the randomized presentation index in the pinned task source.
No demographics, survey answers, network IDs or markup enter prepared reader data.
Empty selections remain attempts; non-script fragments have an explicit exclusion.
The released participant total is checked against, never forced to match, the paper.
"""
import argparse
import ast
from collections import Counter,defaultdict
import csv
import math
from pathlib import Path
import re
import time
import unicodedata

from runners.stage9.common import REPO,ROOT,closure,digest,file_hash,freeze,read


def literal(text, expected):
    if not isinstance(text,str) or len(text)>200000:
        raise ValueError('serialized task field exceeds bounded schema')
    value=ast.literal_eval(text)
    if not isinstance(value,expected):
        raise ValueError('unexpected serialized task field type')
    return value


def word(value):
    if not isinstance(value,str) or len(value)>200:
        raise ValueError('invalid task word')
    value=unicodedata.normalize('NFKC',value).casefold().replace('’',"'")
    return re.sub(r'^\W+|\W+$','',value,flags=re.UNICODE)


def selections(response):
    chunks=literal(response,dict)
    if len(chunks)>200:
        raise ValueError('too many highlight chunks')
    result=[]
    for key,chunk in sorted(chunks.items(),key=lambda p:int(p[0])):
        if not str(key).isdigit() or not isinstance(chunk,dict) or len(chunk)>400:
            raise ValueError('invalid highlight structure')
        positions=[int(k) for k in chunk]
        if any(str(k)!=str(int(k)) or int(k)<0 for k in chunk) or len(set(positions))!=len(positions):
            raise ValueError('invalid within-highlight position')
        result.append({'highlight_index':int(key),'words':[word(v) for k,v in sorted(chunk.items(),key=lambda p:int(p[0])) if word(v)]})
    return result


def partition(keys, pilot=(), seed='broll-person-v1'):
    keys=set(keys);pilot=set(pilot)
    if not pilot<=keys:
        raise ValueError('unknown exposed pilot group')
    available=sorted(keys-pilot,key=lambda k:digest({'split':seed,'key':k}))
    n=len(available);reserve=set(available[:math.ceil(.3*n)])
    remaining=[k for k in available if k not in reserve]
    development=set(remaining[:max(1,math.floor(.2*n))])
    return {k:'pilot' if k in pilot else 'reserve' if k in reserve else 'development' if k in development else 'discovery' for k in sorted(keys)}


def scripts(root):
    source={}
    with (root/'df_scripts_cleaned.csv').open(encoding='utf-8-sig',newline='') as stream:
        for row in csv.DictReader(stream):
            tokens=literal(row['word_lists'],list);unique=literal(row['unique_words'],list)
            if len(tokens)!=int(row['Nwords']) or len(unique)!=int(row['Nunique_words']) or len(set(tokens))!=len(unique):
                raise ValueError('released script counts do not reconcile')
            counts=Counter(word(w) for w in tokens if word(w))
            key=row['object'].casefold()
            if key in source:
                raise ValueError('duplicate script')
            source[key]={'script':row['script'],'topic':row['video_type'],'tokens':tokens,
                         'support':sorted(counts),'word_counts':dict(counts),'pos':defaultdict(Counter),
                         'source_words':int(row['Nwords']),'source_unique_words':int(row['Nunique_words'])}
    if len(source)!=12:
        raise ValueError('published twelve-script substrate not realized')
    with (root/'broll_transcript_vocab.csv').open(encoding='utf-8-sig',newline='') as stream:
        for row in csv.DictReader(stream):
            key=row['object'].casefold();w=word(row['word'])
            if key not in source:
                raise ValueError('POS annotation names unknown script')
            # POS and script tokenizers differ. Unmatched annotations stay out of
            # support; every support type gets a visible UNTAGGED category below.
            if w in source[key]['word_counts']:
                source[key]['pos'][w][row['type'] or 'UNTAGGED']+=1
    for data in source.values():
        data['pos']={w:sorted(data['pos'][w],key=lambda p:(-data['pos'][w][p],p))[0]
                     if data['pos'][w] else 'UNTAGGED' for w in data['support']}
    return source


def prepare():
    started=time.time();output=ROOT/'private/prepared/broll-v1'
    if (output/'COMPLETE.json').exists():
        return read(output/'COMPLETE.json')
    archive=read(ROOT/'intake/BROLL_ARCHIVE.json')
    rights=read(ROOT/'intake/BROLL_REUSE_REVIEW.json')
    if rights.get('private_research_analysis_accepted') is not True or rights['archive_sha256']!=archive['sha256']:
        raise ValueError('source-specific reuse review missing')
    root=ROOT/'private/intake/materialized'/archive['sha256'];csv.field_size_limit(2**24)
    stimuli=scripts(root);records=[];people=defaultdict(list);exclusions=Counter();first_raw=None
    with (root/'broll_alldata_vocab.csv').open(encoding='utf-8-sig',newline='') as stream:
        first_vocab=next(csv.DictReader(stream))
    with (root/'broll_alldata.csv').open(encoding='utf-8-sig',newline='') as stream:
        for raw in csv.DictReader(stream):
            # No copying of arbitrary source fields: private identifiers are
            # replaced here, and survey/demographic/free-response fields discarded.
            person=digest({'broll-person':raw['gameID']})[:24]
            if first_raw is None:first_raw=person
            key=raw['object'].casefold();trial=int(raw['trialNum']);goal=raw['goal']
            if raw['eventType']!='test' or key not in stimuli or goal not in ('informative','entertaining') or not 0<=trial<12:
                raise ValueError('unexpected released test-trial schema')
            highlights=selections(raw['response'])
            chosen={w for h in highlights for w in h['words']}
            absent=chosen-set(stimuli[key]['support'])
            reason='selected fragment outside script vocabulary' if absent else None
            if reason:exclusions[reason]+=1
            row={'key':digest({'person':person,'trial':trial,'script':key})[:24],
                 'person':person,'script_key':key,'trial':trial,'goal':goal,
                 'highlights':highlights,'selected_words':sorted(chosen),
                 'labels':[int(w in chosen) for w in stimuli[key]['support']],
                 'usable':reason is None,'exclusion':reason,'unmatched_word_count':len(absent)}
            records.append(row);people[person].append(row)
    for rows in people.values():
        if (len(rows)!=12 or {r['trial'] for r in rows}!=set(range(12)) or len({r['goal'] for r in rows})!=1
                or {r['script_key'] for r in rows}!=set(stimuli)):
            raise ValueError('participant chronology or script coverage is not a complete unique sequence')
    pilot={first_raw,digest({'broll-person':first_vocab['gameID']})[:24]}
    person_split=partition(people,pilot)
    # The script associated with the inspected released highlight example cannot
    # become a newly untouched script reserve. Its text itself is public stimulus.
    script_split=partition(stimuli,{first_vocab['object'].casefold()},seed='broll-script-v1')
    identity={'source':archive,'reuse_review':rights,'sources':closure([Path(__file__).resolve(),REPO/'runners/stage9/common.py']),
              'files':{n:file_hash(root/n) for n in ('broll_alldata.csv','df_scripts_cleaned.csv','broll_transcript_vocab.csv')},
              'unit':'participant with crossed script dependence; word-type Bernoulli opportunities',
              'chronology_source':read(ROOT/'intake/BROLL_TASK_SOURCE.json'),
              'person_split':person_split,'script_split':script_split,
              'labels':'recorded highlighted normalized word types; no occurrence/scan-path or unobserved imagery claim'}
    freeze(output/'IDENTITY.json',identity);freeze(output/'SCRIPTS.json',stimuli)
    for name in ('pilot','development','discovery','reserve'):
        freeze(output/(name+'.json'),[r for r in records if person_split[r['person']]==name])
    receipt={'identity_sha256':digest(identity),'attempted_records':len(records),'people':len(people),'scripts':len(stimuli),
             'usable_records':sum(r['usable'] for r in records),'exclusions':dict(exclusions),
             'empty_selection_attempts':sum(not r['selected_words'] for r in records),
             'person_split_counts':dict(Counter(person_split.values())),
             'script_split_counts':dict(Counter(script_split.values())),
             'checked_source_count':{'scripts':12,'exact_match':True,'per_script_word_counts_exact':True},
             'paper_count_comparison':{'reported_people':818,'released_people':len(people),'reported_annotations':8880,
                                      'released_annotations':len(records),'reproduced':False,
                                      'disposition':'released file is a different analysis population; no numerical paper reproduction claim'},
             'chronology_verified':'each participant has exactly one presentation index 0..11; pinned source assigns it after shuffling',
             'scope':'private released-data loader; predictive baseline, cross-source audit and scientific package acceptance remain owed',
             'preparation_seconds':time.time()-started,'completed_at':time.time()}
    freeze(output/'COMPLETE.json',receipt);freeze(ROOT/'intake/BROLL_PREPARATION.json',receipt)
    return receipt


if __name__=='__main__':
    print(prepare())
