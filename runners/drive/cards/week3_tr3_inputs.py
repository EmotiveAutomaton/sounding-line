"""Complete TR3 display/chronology census; no scientific feature or effect.

DESIGN CHECK: LESSONS 2-5 reread 2026-10-26. NULL and ALTERNATIVE retain
all source sessions and displays. Ambiguous handling stays unknown. Missing
source/split coverage, changed bytes, unordered clocks or replay differences
fail closed; tied/overlapping sessions remain without invented precedence.
Known answers cover exposure, Unicode, chronology, split and tamper refusal.
"""
from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import math
import time

from runners.stage9.coauthor import suggestions, delta_ops
from . import week3_frames_io as source
from .timing_census import read, filehash
from .timing_pmap_source import completed
from .timing_p6 import write_equal, gzip_equal, gzread, progress


def clock(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('finite observed clock required')
    return value


def prepare(meta, events, timeline, canonical, p6):
    identity = tuple(meta[k] for k in ('session', 'writer', 'prompt'))
    if any(tuple(row[k] for k in ('session', 'writer', 'prompt')) != identity for row in (timeline, p6)):
        raise ValueError('source identity mismatch')
    start, end = clock(meta['timestamp']), clock(meta['end_at'])
    if end < start or (p6['timestamp'], p6['end_at']) != (start, end):
        raise ValueError('session chronology mismatch')
    canonical_menus = {r['ordinal']: r for r in canonical['events']}
    if len(canonical_menus) != len(canonical['events']):
        raise ValueError('duplicate canonical menu')
    displays, edits, seen = [], [], set()
    origin = None
    previous = -math.inf
    for ordinal, event in enumerate(events):
        stamp = clock(event['eventTimestamp'])
        if stamp < previous or not start <= stamp <= end:
            raise ValueError('raw clock outside session or unordered')
        previous = stamp
        name = event.get('eventName')
        if name in ('suggestion-open', 'suggestion-reopen'):
            offered = suggestions(event.get('currentSuggestions'))
            if name == 'suggestion-open':
                origin = ordinal
                if origin not in canonical_menus or canonical_menus[origin]['options'] != offered:
                    raise ValueError('raw/canonical display coverage differs')
                seen.add(origin)
            if origin is None:
                raise ValueError('reopen without original display')
            c = canonical_menus[origin]
            if offered != c['options']:
                raise ValueError('reopen alternatives changed')
            displays.append(dict(ordinal=ordinal, timestamp=stamp, origin=origin,
                reopened=name == 'suggestion-reopen', options=offered,
                handling=c['decision'] if c['usable'] else None,
                handling_usable=c['usable'], handling_exclusion=c.get('exclusion')))
        ops = delta_ops(event.get('textDelta'))
        if ops and event.get('eventSource') == 'user':
            edits.append(dict(ordinal=ordinal, timestamp=stamp, operations=ops,
                              inserted_characters=sum(len(o['insert']) for o in ops if 'insert' in o)))
    if seen != set(canonical_menus):
        raise ValueError('canonical menu not observed in raw source')
    return dict(session=identity[0], writer=identity[1], prompt=identity[2],
        start=start, end=end, displays=displays, user_edits=edits,
        produced_token_count=len(p6['words']),
        typed_inserted_characters=sum(r['inserted_characters'] for r in edits),
        outcome_features_prepared=False)


def assemble(rows, split, complete_population=True):
    if len({r['session'] for r in rows}) != len(rows):
        raise ValueError('duplicate session')
    counts = Counter(r['writer'] for r in rows)
    if split['seed'] != 20261026 or set(split['writers'].values()) != {'discovery', 'test'}:
        raise ValueError('frozen WB1 split required')
    if complete_population and (dict(counts) != split['session_counts'] or set(counts) != set(split['writers'])):
        raise ValueError('WB1 split population differs')
    if not set(counts) <= set(split['writers']):
        raise ValueError('writer missing from WB1 split')
    groups = defaultdict(list)
    for row in rows:
        groups[row['writer']].append(row)
    roster, overlaps = [], set()
    for writer, group in sorted(groups.items()):
        for row in sorted(group, key=lambda r: (r['start'], r['session'])):
            prior = sorted(r['session'] for r in group if r['end'] < row['start'])
            ambiguous = sorted(r['session'] for r in group if r['session'] != row['session']
                               and max(r['start'], row['start']) <= min(r['end'], row['end']))
            overlaps.update(tuple(sorted((row['session'], sid))) for sid in ambiguous)
            roster.append(dict(session=row['session'], writer=writer, half=split['writers'][writer],
                prompt=row['prompt'], start=row['start'], end=row['end'],
                strict_prior_sessions=prior, overlapping_or_touching_sessions=ambiguous,
                chronological_index=len(prior), displays=len(row['displays']),
                typed_inserted_characters=row['typed_inserted_characters']))
    summary=dict(sessions=len(rows), writers=len(counts), repeat_writers=sum(v > 1 for v in counts.values()),
        sessions_with_strict_history=sum(bool(r['strict_prior_sessions']) for r in roster),
        overlapping_or_touching_pairs=len(overlaps),
        unique_menus=sum(sum(not d['reopened'] for d in r['displays']) for r in rows),
        display_events=sum(len(r['displays']) for r in rows),
        unknown_handling_display_events=sum(sum(not d['handling_usable'] for d in r['displays']) for r in rows),
        typed_inserted_characters=sum(r['typed_inserted_characters'] for r in rows),
        halves={half: dict(writers=sum(split['writers'][w] == half for w in counts),
                          sessions=sum(r['half'] == half for r in roster),
                          sessions_with_strict_history=sum(r['half'] == half and bool(r['strict_prior_sessions']) for r in roster))
                for half in ('discovery', 'test')},
        scientific_admission=False, outcome_features_prepared=False,
        exposure_scope='Recorded display opportunity, not observed attention',
        typing_scope='Raw user insertion characters; no concatenated-delta n-grams or carryover outcome')
    return dict(roster=roster, summary=summary)


def run(output, inputs, config, verification=False):
    mode=config.get('mode')
    if config != dict(mode=mode, seed=20261026) or mode not in ('constructed', 'full', 'pilot'):
        raise ValueError('frozen source configuration required')
    output=Path(output);output.mkdir(parents=True, exist_ok=True)
    if mode == 'constructed':
        if set(inputs) != {'fixture'}:raise ValueError('fixture required')
        fixture=read(inputs['fixture']); selected=fixture['sessions'];sources=None;split=fixture['split']
    else:
        if set(inputs) != {'pmap_completion','wb1_completion','wb1_split'}:raise ValueError('exact source inputs required')
        completed(inputs['wb1_completion'], inputs['wb1_split'])
        split=read(inputs['wb1_split'])
        selected,sources=source.load({'pmap_completion':inputs['pmap_completion']}, dict(card='TR3-inputs',mode=mode,
            expected_sessions=1399,session_limit=1399 if mode=='full' else 140,seed=20261026))
    rows=[];bindings=[];started=time.process_time()
    for i,item in enumerate(selected):
        args,pins=source.source_args(item,sources);row=prepare(**args);rows.append(row)
        bindings.append(dict(session=row['session'], source_hashes=pins))
        path=output/'sessions'/(hashlib.sha256(row['session'].encode()).hexdigest()+'.json.gz')
        if verification:
            if gzread(path) != row:raise ValueError('session replay differs')
        else:gzip_equal(path,row)
        if sources is not None and sources.unit_binding(row['session']) != pins:raise ValueError('source changed during preparation')
        progress(output/'PROGRESS.json',dict(phase='verify-source' if verification else 'source',done=i+1,total=len(selected)))
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():raise InterruptedError('source yields at session boundary')
    value=assemble(rows,split,complete_population=mode!='pilot')
    value['summary'].update(full_population=mode=='full',constructed=mode=='constructed',cost_only=mode=='pilot')
    payloads={'CENSUS.json':value,'SUMMARY.json':value['summary'],'WB1_WRITER_SPLIT.json':split,
              'BINDING.json':dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()},units=bindings)}
    for name,value in payloads.items():
        if verification:
            if read(output/name) != value:raise ValueError('aggregate replay differs')
        else:write_equal(output/name,value)
    if verification:return dict(verified=True,complete_source_replay=True,scientific_admission=False)
    if not (output/'TIMING.json').exists():write_equal(output/'TIMING.json',dict(cpu_seconds=time.process_time()-started,
        sessions=len(rows),scope='Source only; later features and statistics unmeasured'))
    return dict(status='complete',counts_only=True,scientific_admission=False,summary=payloads['SUMMARY.json'])


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
