"""TR3 discovery-only suggestion candidate counts, before human comparison.

DESIGN CHECK: LESSONS 2-5 reread 2026-10-26. Under NULL and ALTERNATIVE,
token counts must match known text, reopened menus count once, and test writers
never feed discovery. Changed source, split or repeat identity refuses. Exact
replay or explicit failure are exhaustive; neither licenses a carryover effect.
"""
from collections import Counter
import hashlib
from pathlib import Path
import time
import unicodedata

from .timing_text import TOKEN, WORD
from .timing_census import read, filehash
from .timing_pmap_source import completed
from .timing_p6 import gzread, write_equal, gzip_equal, progress


def features(text):
    """All word 1-3 grams within whitespace-connected runs; Unicode punctuation.

    Reuse the existing tokenizer, casefold words and keep punctuation literal.
    Symbols and unparsed non-whitespace break runs. No across-offer adjacency.
    """
    if not isinstance(text, str):
        raise ValueError('text required')
    text.encode('utf8', errors='strict')
    counts = Counter('p:'+c for c in text if unicodedata.category(c).startswith('P'))
    recent = []; end = 0
    for m in TOKEN.finditer(text):
        gap = text[end:m.start()]
        if any(not c.isspace() for c in gap):
            recent = []
        token = m.group()
        if WORD.fullmatch(token):
            recent = (recent + [token.casefold()])[-3:]
            for n in range(1, len(recent)+1):
                counts[f'w{n}:'+' '.join(recent[-n:])] += 1
        else:
            recent = []
        end = m.end()
    return dict(sorted(counts.items()))


def prepare(unit, roster):
    if roster['half'] != 'discovery':
        raise ValueError('test writer cannot feed discovery')
    if any(unit[k] != roster[k] for k in ('session','writer','prompt')):
        raise ValueError('unit identity mismatch')
    menus = {}; counts = Counter(); offers = characters = empty = 0
    previous = -1
    for d in unit['displays']:
        ordinal, origin = d['ordinal'], d['origin']
        if type(ordinal) is not int or ordinal <= previous:
            raise ValueError('display ordinals not strictly ordered')
        previous = ordinal
        options = d['options']
        if not isinstance(options, list) or any(not isinstance(t,str) for t in options):
            raise ValueError('invalid alternatives')
        if d['reopened']:
            if origin is None and not options:
                empty += 1
                continue
            if origin not in menus or menus[origin] != options:
                raise ValueError('reopen identity or alternatives differ')
            continue
        if origin != ordinal or origin in menus:
            raise ValueError('original menu identity differs')
        menus[origin] = options
        empty += not bool(options)
        for text in options:
            counts.update(features(text)); offers += 1; characters += len(text)
    return dict(session=unit['session'],writer=unit['writer'],prompt=unit['prompt'],
        menus=len(menus),offers=offers,characters=characters,empty_displays=empty,
        feature_counts=dict(sorted(counts.items())))


def discovery_roster(census, split, full):
    rows=census['roster'];counts=Counter(r['writer'] for r in rows)
    if len({r['session'] for r in rows}) != len(rows):
        raise ValueError('duplicate census session')
    if split['seed'] != 20261026 or dict(counts) != split['session_counts'] or set(counts)!=set(split['writers']):
        raise ValueError('split population differs')
    if set(split['writers'].values()) != {'discovery','test'}:
        raise ValueError('both writer halves required')
    if any(r['half'] != split['writers'][r['writer']] for r in rows):
        raise ValueError('writer half mismatch')
    if full and (len(rows)!=1399 or len(counts)!=61):
        raise ValueError('full primary source required')
    selected=sorted((r for r in rows if r['half']=='discovery'),key=lambda r:r['session'])
    if full and (len(selected)!=745 or len({r['writer'] for r in selected})!=31):
        raise ValueError('full discovery half required')
    return selected


def run(output, inputs, config, verification=False):
    mode=config.get('mode')
    if config!=dict(mode=mode,seed=20261026) or mode not in ('constructed','full'):
        raise ValueError('frozen candidate configuration required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);started=time.process_time()
    if mode=='constructed':
        if set(inputs)!={'fixture'}:raise ValueError('fixture required')
        f=read(inputs['fixture']);census=f['census'];split=f['split'];parent=None
    else:
        if set(inputs)!={'exposure_completion'}:raise ValueError('complete exposure parent required')
        parent=Path(inputs['exposure_completion']).parent
        for name in ('CENSUS.json','WB1_WRITER_SPLIT.json'):
            completed(inputs['exposure_completion'],parent/'output'/name)
        census=read(parent/'output/CENSUS.json');split=read(parent/'output/WB1_WRITER_SPLIT.json')
    selected=discovery_roster(census,split,mode=='full')
    counts=Counter();support=Counter();stats=Counter();bindings=[]
    for i,r in enumerate(selected):
        sid=r['session'];name=hashlib.sha256(sid.encode()).hexdigest()+'.json.gz'
        if parent is None:
            unit=f['units'][sid];unit_hash=None
        else:
            path=parent/'output/sessions'/name
            completed(inputs['exposure_completion'],path);unit_hash=filehash(path);unit=gzread(path)
        row=prepare(unit,r)
        if verification:
            if gzread(output/'sessions'/name)!=row:raise ValueError('candidate unit replay differs')
        else:gzip_equal(output/'sessions'/name,row)
        counts.update(row['feature_counts']);support.update(row['feature_counts'].keys())
        stats.update({k:row[k] for k in ('menus','offers','characters','empty_displays')})
        bindings.append(dict(session=sid,source_sha256=unit_hash))
        progress(output/'PROGRESS.json',dict(phase='verify-candidates' if verification else 'candidates',done=i+1,total=len(selected)))
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():
            raise InterruptedError('candidate counts yield at complete session boundary')
    summary=dict(stats,sessions=len(selected),writers=len({r['writer'] for r in selected}),
        candidate_features=len(counts),full_discovery_half=mode=='full',constructed=mode=='constructed',
        test_units_read=0,features_selected=False,scientific_admission=False,
        scope='Discovery suggestion frequencies only; no human comparison or carryover outcome')
    payloads={'SUMMARY.json':summary,
        'CANDIDATES.json':dict(counts=dict(sorted(counts.items())),session_support=dict(sorted(support.items()))),
        'BINDING.json':dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()},units=bindings)}
    for name,value in payloads.items():
        if verification:
            if read(output/name)!=value:raise ValueError('candidate aggregate replay differs')
        else:write_equal(output/name,value)
    if verification:return dict(verified=True,complete_candidate_replay=True,scientific_admission=False)
    if not (output/'TIMING.json').exists():write_equal(output/'TIMING.json',dict(cpu_seconds=time.process_time()-started))
    return dict(status='complete',counts_only=True,scientific_admission=False,summary=summary)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
