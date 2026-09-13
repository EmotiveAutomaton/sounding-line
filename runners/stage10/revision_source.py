"""Versioned ScholaWrite next released-edit projection for Stage 10.

DESIGN CHECK: canonical Stage 9 source loader and Stage 10 evidence contract.
NULL/ALTERNATIVE both require same-project/author/session positive chronological
successors and exact document continuity. Current, previous-artifact and recorded
edit evidence stay distinct. Selection reads no target value. Projects are the
independent units; labels are released annotator categories, not personal goals.
"""
from collections import Counter
from dataclasses import asdict
from pathlib import Path
import argparse

from runners.stage9.schola_cases import inputs
from .contracts import PublicTask, choices_for, digest, canonical
from .ollama import now, write_new, request_for
from .queue import read

DESCRIPTIONS = {
    'schola_category': {
        'PLANNING': 'The next released edit is annotated as planning: generating or organizing ideas or sections.',
        'IMPLEMENTATION': 'The next released edit is annotated as implementation: producing text or inserting manuscript objects, citations or references.',
        'REVISION': 'The next released edit is annotated as revision: changing clarity, coherence, structure, style, formatting, fluency or scientific accuracy.'},
    'schola_location': {
        'first_quarter': 'The next released edit first changes a character in the first quarter of the current editor text.',
        'second_quarter': 'The next released edit first changes a character in the second quarter of the current editor text.',
        'third_quarter': 'The next released edit first changes a character in the third quarter of the current editor text.',
        'last_quarter': 'The next released edit first changes a character in the last quarter of the current editor text.',
        'no_change': 'The next released event leaves the visible editor text unchanged.'}}


def task_from(row, view):
    record = row['views']['record']
    if set(record) != {'document', 'previous_document', 'previous_category', 'previous_location'}:
        raise ValueError('canonical public source projection changed')
    if row['target_source_ordinal'] <= row['source_ordinal']:
        raise ValueError('future source boundary is not later')
    if view == 'artifact': evidence = {'document': record['document']}
    elif view == 'earlier-artifacts': evidence = {'document': record['document'], 'earlier_drafts': [record['previous_document']]}
    elif view == 'process-record': evidence = dict(record)
    else: raise ValueError('undeclared revision evidence view')
    if not all(isinstance(record[k], str) for k in record): raise ValueError('nontext source field')
    if record['previous_category'] not in DESCRIPTIONS['schola_category'] or record['previous_location'] not in DESCRIPTIONS['schola_location']:
        raise ValueError('source-native previous labels changed')
    label = 'annotated category' if row['kind'] == 'schola_category' else 'first changed-character location'
    return PublicTask(digest(['s10-schola-v1', row['key'], view])[:32], row['kind'], view, evidence,
        'Predict the ' + label + ' of the next released edit by this author in this project and session.',
        choices_for(list(DESCRIPTIONS[row['kind']].values()), row['key']),
        'next released edit after the shown editor state, same author/project/session, positive gap within thirty minutes',
        'project-scoped human author; source annotations are not writer-stated goals',
        'historically exposed ScholaWrite; descriptive whole-project separation')


def prepare(output, fold=0, per_project=8):
    if not 1 <= per_project <= 32: raise ValueError('bounded source cohort required')
    rows, source = inputs('scientific', fold)
    publics, evaluators, exclusions = {}, {}, []
    for lane, own in rows.items():
        publics[lane], evaluators[lane] = [], []
        counts = Counter(); groups = {}
        for row in own: groups.setdefault(row['source_key'], []).append(row)
        for event in sorted(groups, key=lambda key: digest(['s10-schola-screen-v1', key])):
            pair = groups[event]
            if len(pair) != 2 or {r['kind'] for r in pair} != set(DESCRIPTIONS):
                raise ValueError('both native targets must share a complete source boundary')
            unit = pair[0]['unit']
            if counts[unit] >= per_project: continue
            tasks = [(row, task_from(row, view)) for row in pair for view in ['artifact', 'earlier-artifacts', 'process-record']]
            # Whole text only. Reserve room for common retrieval/procedure data and
            # the complete largest allowed execution feedback before any model call.
            if any(len(canonical(task.public()).encode('utf8')) > 6500 for _, task in tasks):
                exclusions.append({'event': event, 'lane': lane, 'reason': 'whole public task exceeds shared 6500-byte envelope'})
                continue
            for row, task in tasks:
                request_for(task, context_tokens=16384)
                publics[lane].append(asdict(task))
                evaluators[lane].append({'task_id': task.task_id, 'correct_choice': next(k for k,v in task.choices if v == DESCRIPTIONS[row['kind']][row['truth']]),
                    'source_event': row['key'], 'boundary': event, 'writer_component': row['unit'], 'prompt_component': row['unit'],
                    'source_ordinal': row['source_ordinal'], 'target_source_ordinal': row['target_source_ordinal']})
            counts[unit] += 1
        if not publics[lane]: raise ValueError('no eligible source tasks in required project partition')
    for left, right in [('train', 'development'), ('train', 'evaluation'), ('development', 'evaluation')]:
        if {r['writer_component'] for r in evaluators[left]} & {r['writer_component'] for r in evaluators[right]}:
            raise ValueError('project separation changed')
    frozen = {'status': 'FROZEN', 'at': now(), 'fold': fold, 'per_project': per_project,
              'source_sha256': digest(source), 'public_sha256': {k: digest({'tasks':v}) for k,v in publics.items()},
              'evaluator_sha256': {k: digest({'targets':v}) for k,v in evaluators.items()},
              'identity_sha256': {k: digest({'targets':[{a:b for a,b in r.items() if a!='correct_choice'} for r in v]}) for k,v in evaluators.items()},
              'counts': {k: {'tasks':len(v), 'events':len({r['boundary'] for r in evaluators[k]}),
                             'projects':len({r['writer_component'] for r in evaluators[k]})} for k,v in publics.items()},
              'exclusions': exclusions, 'scope': 'same frozen released-edit boundaries; three evidence views, two separate targets; no new population claim'}
    output.mkdir(parents=True, exist_ok=False)
    write_new(output/'SOURCE.json', source)
    for lane in publics:
        write_new(output/(lane+'-public.json'), {'tasks':publics[lane]})
        write_new(output/(lane+'-evaluator.json'), {'targets':evaluators[lane]})
        write_new(output/(lane+'-identity.json'), {'targets':[{k:v for k,v in r.items() if k!='correct_choice'} for r in evaluators[lane]]})
    write_new(output/'FROZEN.json', frozen)
    write_new(output/'COMPLETE.json', {'status':'COMPLETE','frozen_sha256':digest(frozen),'source_sha256':digest(source)})
    return frozen


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--fold',type=int,default=0);p.add_argument('--per-project',type=int,default=8)
    a=p.parse_args();prepare(a.output,a.fold,a.per_project)
