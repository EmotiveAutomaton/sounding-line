"""SL2/SL7/SL9: chronological writer populations and three provenance corpora.

DESIGN CHECK: LESSONS 2-5; CONTROLS 1,6. NULL: absent timestamps, target prompts
in own training, future records or aliased partitions refuse. ALTERNATIVE: strictly
earlier sessions support later choices, with all eligible writers retained. Existing
writer exposure never becomes fresh confirmation. Sparse text is a stress regime.
"""
from collections import defaultdict, Counter
from .common import REPO, freeze, read, digest, filehash
from runners.stage9.coauthor import delta_ops,suggestions
from runners.stage11.replay import replay
import json

def split_sessions(sessions):
    if len(sessions)<3 or any(type(r['timestamp']) not in (int,float) for r in sessions): return None
    rows=sorted(sessions,key=lambda r:(r['timestamp'],r['session']))
    test=rows[-1]; before=[r for r in rows if r['timestamp']<test['timestamp'] and r['prompt']!=test['prompt']]
    if len(before)<2:return None
    cal=before[-1]
    train=[r for r in before if r['timestamp']<cal['timestamp'] and r['prompt']!=cal['prompt']]
    if not train:return None
    return dict(train=train,calibration=[cal],evaluation=[test])

def corpus(session):
    p=REPO/session['path']
    if filehash(p)!=session['source_sha256']:raise ValueError('source changed before corpus preparation')
    events=[json.loads(x) for x in p.read_text(encoding='utf8').splitlines()]
    r=replay(events)
    if not r['reconstructed']:raise ValueError('unreconstructed training session')
    human=[]
    for e in events:
        if e.get('eventSource')=='user' and e.get('textDelta'):
            human.extend(op['insert'] for op in delta_ops(e['textDelta']) if isinstance(op.get('insert'),str))
    # Keystroke fragments retain their actual order. This is typed text, including
    # later-deleted text, not an invented final human-only document.
    accepted=[]
    for e in r['events']:
        if e['usable'] and e['verified_insertion']:
            accepted.extend(o['original'] for o in e['options'] if o['index'] in e['matched_option_indices'][:1])
    return dict(human_typed=''.join(human),mixed_final=r['final_document'],accepted_model='\n\n'.join(accepted))

def run(card,out,raw,tick):
    parent=raw/'jobs'/card['requires'][0]; roster=read(parent/'ROSTER.json')
    by=defaultdict(list)
    for r in roster:
        if r['reconstructed']:by[r['writer']].append(r)
    selected={};excluded=[];prepared=[];truth=[];allcorpora={};session_corpora=[]
    for i,(writer,sessions) in enumerate(sorted(by.items())):
        split=split_sessions(sessions)
        if not split:excluded.append(dict(writer=writer,reason='fewer than three strict-time, prompt-novel partitions'));continue
        selected[writer]={k:[r['session'] for r in v] for k,v in split.items()}
        sources={k:[] for k in ('human_typed','mixed_final','accepted_model')}
        for session in split['train']:
            c=corpus(session)
            session_corpora.append(dict(writer=writer,session=session['session'],timestamp=session['timestamp'],prompt=session['prompt'],texts=c))
            for kind,text in c.items():
                if text.strip() and text not in sources[kind]:sources[kind].append(text)
        allcorpora[writer]={k:'\n\n'.join(v) for k,v in sources.items()}
        for partition,rs in split.items():
            for session in rs:
                source=[json.loads(x) for x in (REPO/session['path']).read_text(encoding='utf8').splitlines()]
                items=read(parent/'reader'/f"{session['session']}.json")
                refs={r['key']:r for r in read(parent/'evaluator'/f"{session['session']}.json")}
                for item in items:
                    ref=refs[item['key']]
                    options=suggestions(source[item['ordinal']]['currentSuggestions'])
                    if [v['original'] for v in options]!=item['prospective']['alternatives']:raise ValueError('candidate order differs from source')
                    prepared.append(dict(key=item['key'],writer=writer,prompt=item['prompt'],session=item['session'],ordinal=item['ordinal'],option_indices=[v['index'] for v in options],
                        timestamp=session['timestamp'],domain=item['domain'],partition=partition,evidence=item['prospective']))
                    truth.append(dict(key=item['key'],handling=ref['target']['handling'],selected_index=ref['selected_index']))
        tick(dict(writers=i+1,total_writers=len(by)))
    if not selected:raise ValueError('no chronological eligible writer')
    freeze(out/'READER.json',prepared);freeze(out/'EVALUATOR.json',truth)
    freeze(out/'SPLITS.json',selected);freeze(out/'TEXT_CORPORA.json',allcorpora);freeze(out/'EXCLUSIONS.json',excluded)
    freeze(out/'SESSION_CORPORA.json',session_corpora)
    n=len(selected)
    freeze(out/'SUMMARY.json',dict(writers=n,excluded_writers=len(excluded),rows_by_partition=dict(Counter(r['partition'] for r in prepared)),
        estimand='future handling/choice of known writers; fixed prompt stimuli; within-writer prompt novelty; descriptive exposed corpus',
        independent_unit='writer; paired writer bootstrap plus prompt sensitivity; donor dependency retained',
        corpus_characters={w:{k:len(v) for k,v in c.items()} for w,c in allcorpora.items()},
        half_brier_margin=.01,forecast_halfwidths={str(sd):1.96*sd/n**.5 for sd in (.224,.230,.036,.092)},
        parity_at_worst_prior_variance='unattainable at available writer count',confirmation_disposition='UNRESOLVED, NO FRESH UNITS',
        pretraining_contamination='historical CoAuthor predates local reader packages; project exposure and pretraining exposure distinct',
        fresh_sources='post-cutoff Git/Wikipedia intake is a separate conditional study'))
    freeze(out/'ADMISSION.json',dict(admitted=True,chronology=True,local_prompt_novelty=True,confirmation=False))
