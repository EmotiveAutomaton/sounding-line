"""Commissioned D30 revision timing labels, without a scientific contrast.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-6 reread October19. Both null and
alternative require exact chronology and original-row retention. Constructed
deletions before/at/after a two-second pause must separate correctly; API and
insertion-only changes cannot become human immediate deletions. False source,
missing occurrence, changed threshold, changed saved output and exhausted cost
must refuse. No hypothesis test or person-specific inference is performed.

Retain P6's clock: consecutive logged text deltas, not inferred keypresses.
Anchor at the last production delta of the original occurrence; a gap >=2 s
starts a new burst, including the edit at that boundary. Keep source and kind
separate. A word can have both an immediate deletion and a later edit. An
insertion before the boundary is neither an immediate deletion nor a later edit.
"""
from bisect import bisect_right
from collections import Counter
from pathlib import Path
import math
import time

from .timing_census import read, filehash
from .timing_p6 import gzread, gzip_equal, write_equal
from .timing_revision_input import relative
from .timing_stats import bind, check_binding
from runners.stage14.common import atomic

CONFIG = dict(mode='full', expected_sessions=1399, cumulative_wall_seconds=900)
LABELS = ('immediate_user_deletion', 'later_user_edit',
          'within_burst_user_insertion', 'non_user_change')


def classify(value):
    clock = value['delta_clock']; by_id = {}; boundaries = []
    last_ordinal = -1; last_time = -math.inf
    for row in clock:
        ordinal = row['ordinal']; seconds = row['seconds']
        if (type(ordinal) is not int or ordinal <= last_ordinal or
                not isinstance(seconds, (int, float)) or not math.isfinite(seconds)
                or seconds < last_time):
            raise ValueError('invalid delta chronology')
        for name in ('inserted_codepoints', 'inserted_utf16', 'deleted_utf16'):
            if type(row[name]) is not int or row[name] < 0:
                raise ValueError('invalid delta counts')
        if by_id and seconds-last_time >= 2.0:
            boundaries.append(ordinal)
        by_id[ordinal] = row; last_ordinal = ordinal; last_time = seconds
    audits = value['revision_events']
    if type(value['occurrence_count']) is not int or len(audits) != value['occurrence_count']:
        raise ValueError('occurrence count differs')
    rows = []
    for index, audit in enumerate(audits):
        production = audit['production_ordinals']
        if (audit['index'] != index or not production or
                production != sorted(set(production)) or
                audit['production_first_ordinal'] != production[0] or
                audit['production_last_ordinal'] != production[-1]):
            raise ValueError('invalid occurrence identity')
        for ordinal in production:
            if ordinal not in by_id or by_id[ordinal]['event_source'] != 'user' or by_id[ordinal]['inserted_codepoints'] <= 0:
                raise ValueError('invalid production delta')
        chars = audit['character_ids']
        if not chars or len(chars) != len(set(chars)) or any(type(i) is not int or i < 0 for i in chars):
            raise ValueError('invalid character identity')
        boundary_index = bisect_right(boundaries, production[-1])
        boundary = boundaries[boundary_index] if boundary_index < len(boundaries) else None
        changes = []; previous = production[-1]
        for change in audit['changes']:
            ordinal = change['ordinal']; event = by_id.get(ordinal)
            if (event is None or ordinal < previous or change['seconds'] != event['seconds'] or
                    change['event_source'] != event['event_source'] or change['kind'] not in ('delete', 'insert')):
                raise ValueError('revision event differs from source clock')
            affected = change['affected_character_ids']
            if len(affected) != len(set(affected)) or not set(affected).issubset(chars):
                raise ValueError('revision character identity differs')
            if change['kind'] == 'delete' and (not affected or event['deleted_utf16'] <= 0):
                raise ValueError('deletion without deleted characters')
            if change['kind'] == 'insert' and (affected or event['inserted_codepoints'] <= 0):
                raise ValueError('invalid insertion change')
            before = boundary is None or ordinal < boundary
            if event['event_source'] != 'user': label = 'non_user_change'
            elif not before: label = 'later_user_edit'
            elif change['kind'] == 'delete': label = 'immediate_user_deletion'
            else: label = 'within_burst_user_insertion'
            changes.append(dict(ordinal=ordinal, kind=change['kind'],
                                event_source=change['event_source'], before_next_pause=before, label=label))
            previous = ordinal
        counts = Counter(c['label'] for c in changes)
        rows.append(dict(index=index, production_last_ordinal=production[-1],
                         next_pause_ordinal=boundary, changes=changes,
                         counts={k:counts[k] for k in LABELS}))
    return dict(session=value['session'], occurrence_count=len(rows), rows=rows,
                clock='all logged text deltas; same as original P6', pause_seconds=2.0)


def load(inputs, config):
    constructed = (set(config)==set(CONFIG) and config['mode']=='constructed' and
                   type(config['expected_sessions']) is int and 1 <= config['expected_sessions'] <= 10 and
                   config['cumulative_wall_seconds']==120)
    if config != CONFIG and not constructed: raise ValueError('exact classifier scope required')
    if set(inputs) != {'source_complete', 'source_proof'}: raise ValueError('exact classifier inputs required')
    root = Path(inputs['source_complete']).parent; complete=read(inputs['source_complete']); proof=read(inputs['source_proof'])
    if (complete.get('status')!='COMPLETE' or not complete.get('fresh_process_verified') or
            not proof.get('verified') or not proof.get('write_through_complete') or
            proof.get('complete_sha256') != filehash(inputs['source_complete'])):
        raise ValueError('source completion not admitted')
    for name, digest in complete['outputs'].items():
        if filehash(root/name) != digest: raise ValueError('source output changed')
    index=read(root/'output/INDEX.json')
    if len(index)!=config['expected_sessions'] or len({r['session'] for r in index})!=len(index):
        raise ValueError('source population differs')
    for row in index:
        if row['file'] != relative(row['session']) or filehash(root/'output'/row['file'])!=row['sha256']:
            raise ValueError('source record differs')
    return root,index


def work(output, inputs, config, operation):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);started=time.monotonic()
    timing=output/'ACTIVE_TIME.json';prior=read(timing)['seconds'] if timing.exists() else 0.
    def elapsed(): return prior+time.monotonic()-started
    def guard():
        if elapsed()>config['cumulative_wall_seconds']: raise TimeoutError('classifier cumulative ceiling')
    try:
        guard();root,index=load(inputs,config)
        if operation=='verify': check_binding(output,inputs,config)
        totals=Counter();occurrence_totals=Counter();out_index=[]
        for row in index:
            guard();source=gzread(root/'output'/row['file']);value=classify(source);target=output/row['file']
            if source['session']!=row['session']: raise ValueError('source session differs')
            if operation=='execute': gzip_equal(target,value)
            elif gzread(target)!=value: raise ValueError('classified record differs')
            for item in value['rows']:
                totals.update(item['counts']);occurrence_totals.update({k:int(n>0) for k,n in item['counts'].items()})
            out_index.append(dict(session=row['session'],file=row['file'],sha256=filehash(target),occurrences=value['occurrence_count']))
            if operation=='execute':
                atomic(output/'PROGRESS.json',dict(completed=len(out_index),total=len(index),phase='revision-burst-input'))
                if (output/'YIELD_REQUEST.json').exists(): return dict(status='yielded',completed=len(out_index),scientific_admission=False)
        summary=dict(sessions=len(index),occurrences=sum(r['occurrences'] for r in out_index),
                     event_counts={k:totals[k] for k in LABELS},occurrence_counts={k:occurrence_totals[k] for k in LABELS},
                     pause_seconds=2.0,scientific_admission=False,clock='all logged text deltas; same as original P6')
        if operation=='execute':
            write_equal(output/'INDEX.json',out_index);write_equal(output/'SUMMARY.json',summary)
            if (output/'TIMING_BINDINGS.json').exists():check_binding(output,inputs,config)
            else:bind(output,inputs,config,['INDEX.json','SUMMARY.json']+[r['file'] for r in out_index])
        elif read(output/'INDEX.json')!=out_index or read(output/'SUMMARY.json')!=summary:raise ValueError('classifier aggregation differs')
        guard();return summary if operation=='execute' else dict(verified=True,full_classifier_replay=True,summary=summary,cumulative_seconds=elapsed())
    finally:atomic(timing,dict(seconds=elapsed()))


def execute(output,inputs,config): return work(output,inputs,config,'execute')
def verify(output,inputs,config): return work(output,inputs,config,'verify')
