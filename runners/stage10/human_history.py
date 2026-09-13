"""Matched other-writer history for R0 and a development-selected rival.

DESIGN CHECK: LESSONS3-5, CONTROLS1-6, READER_HEURISTICS4/5/10 reread.
NULL: another writer's matched history helps equally; personal attribution is
not licensed. ALTERNATIVE: correct earlier handling improves held-out behavior
prediction beyond matched other-writer history. This is an evidence intervention,
not word shuffling. Fix draft/menu/options, history length and original source
population. Choose R3 or grounded R4 by development process-record Brier only,
then original call cost and arm name on ties. One development writer supports
an engineering choice, not general route superiority. No evaluation outcomes
are used for selection, pairing or production. Unmatchable cases remain listed.
"""
from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path

from runners.stage9.process_identity import native_identity
from soundingline.gpulock import GPU_LOCK, acquire_gpu_lock, release_gpu_lock
from . import comparison, human_routes, human_memory_routes, human_proposal, ollama
from .contracts import digest, canonical
from .human_effort_evaluation import metadata
from .queue import read, status
from .reader import from_record, build


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity():
    return {**human_memory_routes.identity(),
            **{'runners/stage10/'+name: file_hash(Path(__file__).with_name(name)) for name in
               ('human_history.py','comparison.py','human_effort_evaluation.py')}}


def choose_rival(tasks, answers, routes):
    values = {}
    for arm in ('R3', 'R4-grounded'):
        if set(routes[arm]) != {task.task_id for task in tasks}:
            raise ValueError('development rival roster incomplete')
        predictions = {task.task_id: {**routes[arm][task.task_id], 'task_public':task.public()} for task in tasks}
        scored = comparison.cell(tasks, answers, predictions, 'development process-record rival selection')
        values[arm] = dict(brier=scored['summary']['brier_system'],
                           model_calls=sum(row['model_calls'] for row in routes[arm].values()),
                           groups=scored['summary']['groups'])
    chosen = min(values, key=lambda arm: (values[arm]['brier'], values[arm]['model_calls'], arm))
    return dict(chosen=chosen, candidates=values,
                rule='minimum development writer-balanced system half-Brier; tie original calls then arm name',
                limitation='engineering selection; the current single development writer cannot establish general superiority')


def pair_histories(tasks, identities):
    if len({t.task_id for t in tasks}) != len(tasks) or any(t.evidence_view != 'process-record' for t in tasks):
        raise ValueError('unique process-record tasks required')
    pairs, excluded = [], []
    for task in sorted(tasks, key=lambda t:t.task_id):
        history = task.evidence['earlier_handling']
        candidates = [q for q in tasks if identities[q.task_id]['writer_component'] != identities[task.task_id]['writer_component']
                      and len(q.evidence['earlier_handling']) == len(history)]
        if not history or not candidates:
            excluded.append(dict(task_id=task.task_id, reason='no earlier history' if not history else 'no other writer with exactly matched history length'))
            continue
        donor = min(candidates, key=lambda q:(q.evidence['earlier_handling'] == history, digest(['s10-history-v1',task.task_id,q.task_id])))
        altered = replace(task, evidence={**task.evidence,'earlier_handling':list(donor.evidence['earlier_handling'])})
        pairs.append(dict(original=asdict(task), altered=asdict(altered), donor_task_id=donor.task_id,
                          original_writer=identities[task.task_id]['writer_component'],
                          donor_writer=identities[donor.task_id]['writer_component'],
                          prompt_component=identities[task.task_id]['prompt_component'],
                          source_event=identities[task.task_id]['source_event'],
                          history_length=len(history), history_changed=history != donor.evidence['earlier_handling']))
    return pairs, excluded


def prepare(prepared, memory, original_r3, original_r4, output):
    frozen = read(prepared/'FROZEN.json')
    training, labels, learned = human_memory_routes.inputs(prepared, memory)
    dev = read(prepared/'development-public.json'); evaluation = read(prepared/'evaluation-public.json')
    if digest(dev) != frozen['public_sha256']['development'] or digest(evaluation) != frozen['public_sha256']['evaluation']:
        raise ValueError('original public cohort changed')
    parents = [original_r3/'COMPLETE.json',original_r4/'COMPLETE.json']
    if any(not p.is_file() or read(p).get('status') != 'COMPLETE' for p in parents):
        raise ValueError('both complete original rivals required before selection')
    tasks = [from_record(row) for row in dev['tasks'] if row['evidence_view'] == 'process-record']
    routes = {'R3':{},'R4-grounded':{}}
    for task in tasks:
        for arm in routes:
            directory = (original_r3/'attempts'/task.task_id if arm == 'R3' else
                         original_r4/'attempts'/digest(['development',task.task_id,arm])[:32])
            if not (directory/'COMPLETE.json').is_file():
                raise ValueError('development route incomplete; no calls allowed')
            # Completed route validation reconstructs bindings and checks every retained file.
            route = (human_routes.route(task,directory) if arm == 'R3' else
                     human_memory_routes.route(task,directory,arm,training,labels,learned))
            routes[arm][task.task_id] = route
    outcomes = read(prepared/'development-evaluator.json')
    if digest(outcomes) != frozen['evaluator_sha256']['development']:
        raise ValueError('development answers changed')
    selected = {t.task_id for t in tasks}
    targets = {r['task_id']:dict(truth=r['correct_choice'],group=r['writer_component'],
                                dependencies=['prompt:'+r['prompt_component']],event=r['source_event'])
               for r in outcomes['targets'] if r['task_id'] in selected}
    fit = choose_rival(tasks, targets, routes)
    identities = metadata(prepared,'evaluation',frozen)
    evaluated = [from_record(row) for row in evaluation['tasks'] if row['evidence_view'] == 'process-record']
    pairs, excluded = pair_histories(evaluated,identities)
    if not pairs:
        raise ValueError('no eligible matched-history population')
    sources = identity()
    input_files = [prepared/'FROZEN.json', prepared/'train-public.json',prepared/'train-evaluator.json',
                   prepared/'development-public.json',prepared/'development-evaluator.json',
                   prepared/'evaluation-public.json',prepared/'evaluation-evaluator.json',memory/'MEMORY.json',*parents]
    pins = {str(path):file_hash(path) for path in input_files}
    for pair in pairs:
        task = from_record(pair['altered'])
        kwargs,_ = build(task,'R0',training,labels); ollama.request_for(task,**kwargs)
        if fit['chosen'] == 'R4-grounded':
            representation,_ = human_memory_routes.representation_for(task,training,labels,learned,'R4-grounded')
            # Existing validated packing reserves the full refinement feedback budget.
            human_memory_routes.proposal.request_for(task,None,representation)
        else:
            representation = None
            human_memory_routes.proposal.request_for(task,None)
        reserved = {'reserved': ''}
        reserved['reserved'] = 'x' * (4096-len(canonical(reserved).encode('utf8')))
        human_memory_routes.proposal.request_for(task,reserved,representation)
    result = dict(schema='stage10.mismatched-history.1', sources=sources,input_files=pins,
                  training_root=str(prepared), memory_root=str(memory), fit=fit,pairs=pairs,excluded=excluded,
                  original_process_tasks=len(evaluated), maximum_model_calls=3*len(pairs),
                  planned_routes=2*len(pairs), evaluation_outcomes_used=False,
                  source_access='byte-checked evaluation identity projection; supplied predecision history only',
                  matching='different writer; exact history length; prefer changed sequence, then fixed hash order',
                  comparison='compare original true-history predictions on exactly these task IDs; no original rerun')
    result = json.loads(canonical(result))
    if (output/'FROZEN.json').exists():
        if read(output/'FROZEN.json') != result:
            raise ValueError('history selection or frozen evidence changed')
    else:
        ollama.write_new(output/'FROZEN.json',result)
    return result


def validate_frozen(frozen):
    if frozen['sources'] != identity():
        raise ValueError('history worker sources changed')
    if any(file_hash(Path(p)) != value for p,value in frozen['input_files'].items()):
        raise ValueError('history source inputs changed')
    if frozen['fit']['chosen'] not in ('R3','R4-grounded'):
        raise ValueError('undeclared selected rival')
    prepared = Path(frozen['training_root'])
    original_frozen = read(prepared/'FROZEN.json')
    source_tasks = [from_record(r) for r in read(prepared/'evaluation-public.json')['tasks'] if r['evidence_view'] == 'process-record']
    expected_pairs, expected_exclusions = pair_histories(source_tasks, metadata(prepared,'evaluation',original_frozen))
    if json.loads(canonical(expected_pairs)) != frozen['pairs'] or expected_exclusions != frozen['excluded']:
        raise ValueError('history assignment does not reproduce from original sources')
    ids = []
    for pair in frozen['pairs']:
        original, altered = from_record(pair['original']), from_record(pair['altered'])
        expected = replace(original,evidence={**original.evidence,'earlier_handling':altered.evidence['earlier_handling']})
        if asdict(expected) != asdict(altered) or original.evidence_view != 'process-record' or pair['original_writer'] == pair['donor_writer']:
            raise ValueError('unmatched intervention changed more than history')
        if len(original.evidence['earlier_handling']) != len(altered.evidence['earlier_handling']) or not original.evidence['earlier_handling']:
            raise ValueError('history length or availability changed')
        ids.append(original.task_id)
    if not ids or len(ids) != len(set(ids)) or frozen['planned_routes'] != 2*len(ids) or frozen['maximum_model_calls'] != 3*len(ids):
        raise ValueError('empty, duplicate or inconsistent intervention roster')


def run(freeze, output):
    frozen = read(freeze); validate_frozen(frozen)
    training, labels, learned = human_memory_routes.inputs(Path(frozen['training_root']),Path(frozen['memory_root']))
    manifest = dict(frozen_sha256=digest(frozen),sources=identity(),arms=['R0',frozen['fit']['chosen']],
                    planned_routes=frozen['planned_routes'],maximum_model_calls=frozen['maximum_model_calls'])
    complete = (output/'COMPLETE.json').exists()
    if (output/'MANIFEST.json').exists():
        if read(output/'MANIFEST.json') != manifest:
            raise ValueError('history queue manifest changed')
    else:
        ollama.write_new(output/'MANIFEST.json',manifest)
    if not complete:
        if (output/'OWNER.json').exists() or GPU_LOCK.exists():
            raise RuntimeError('history queue requires native ownership inspection')
        owner = native_identity(os.getpid())
        if owner is None:
            raise RuntimeError('native history worker unavailable')
        ollama.write_new(output/'OWNER.json',dict(at=ollama.now(),native=owner))
        acquire_gpu_lock('stage10-human-history')
    rows = []
    try:
        for pair in frozen['pairs']:
            task = from_record(pair['altered'])
            for arm in manifest['arms']:
                if identity() != manifest['sources']:
                    raise ValueError('history worker changed during execution')
                directory = output/'attempts'/digest([task.task_id,arm])[:32]
                if complete and not (directory/('ATTEMPT.json' if arm == 'R0' else 'COMPLETE.json')).is_file():
                    raise ValueError('completed history evidence missing; no new calls')
                if arm == 'R0':
                    kwargs,_ = build(task,'R0',training,labels)
                    r = ollama.call(task,directory,**kwargs)
                    summary = dict(model_calls=1,generated_tokens=r['cost']['eval_count'],executor_evaluations=0)
                else:
                    r = human_routes.route(task,directory) if arm == 'R3' else human_memory_routes.route(task,directory,arm,training,labels,learned)
                    summary = {k:r[k] for k in ('model_calls','generated_tokens','executor_evaluations')}
                rows.append(dict(task_id=task.task_id,arm=arm,status=r['status'],sha256=digest(r),**summary))
                if not complete:
                    status(output/'STATUS.json',dict(at=ollama.now(),status='RUNNING',completed_routes=len(rows),planned_routes=manifest['planned_routes'],native=owner))
        result = dict(at=ollama.now(),status='COMPLETE',manifest_sha256=digest(manifest),rows=rows,
                      model_calls=sum(r['model_calls'] for r in rows),generated_tokens=sum(r['generated_tokens'] for r in rows),
                      target_outcomes_used=False,scope='mismatched-history prediction producer; complete paired scientific analysis pending')
        if complete:
            saved = read(output/'COMPLETE.json')
            if any(saved[k] != result[k] for k in result.keys()-{'at'}):
                raise ValueError('completed history receipt changed')
            return saved
        ollama.write_new(output/'COMPLETE.json',result)
        status(output/'STATUS.json',dict(at=ollama.now(),status='COMPLETE',completed_routes=len(rows)))
        return result
    finally:
        if not complete:
            release_gpu_lock()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument('--freeze',type=Path,required=True); parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    try:
        run(args.freeze,args.output)
    except Exception as error:
        if not (args.output/'FAILED.json').exists():
            ollama.write_new(args.output/'FAILED.json',dict(at=ollama.now(),error=repr(error)))
        raise
