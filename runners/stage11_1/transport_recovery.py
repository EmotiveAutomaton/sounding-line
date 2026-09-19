"""Offline reconciliation of a forecast-only cell; never dispatch inference.

DESIGN CHECK: LESSONS 3-5. NULL: missing or changed evidence, an incomplete
replacement, or a changed roster must refuse a whole-cell completion. ALTERNATIVE:
all original tasks replay through the unchanged parser and scoring functions,
using retained complete chains plus explicitly charged replacement chains.
The original incomplete namespace and its uncertain charge remain immutable.
"""
import argparse
import copy
import hashlib
from pathlib import Path

from .common import PRIVATE, read, freeze, digest
from . import branch_runtime as branch


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin():
    return branch.sources() | {'runners/stage11_1/transport_recovery.py': sha(Path(__file__))}


def scoped(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('recovery path outside root')
    return path


def prepare(root, original_path, replacement_id, fake=False):
    """Freeze a supplement containing only unfinished independent task chains."""
    original = read(original_path)
    if original.get('pilot') or any(
        t['kind'] != 'forecast' or any(k in t for k in ('reveal', 'history_ref', 'account_ref'))
        for t in original['tasks']
    ):
        raise ValueError('recovery supports independent forecasts only')
    if replacement_id == original['id'] or Path(replacement_id).name != replacement_id:
        raise ValueError('separate recovery identity required')
    job = root / 'branch_jobs' / original['id']
    if (job / 'COMPLETE.json').exists():
        raise ValueError('original already has terminal disposition')
    binding = read(job / 'BINDING.json')
    if binding != dict(plan_digest=digest(original), sources=branch.sources(), fake=fake):
        raise ValueError('original binding differs')
    inventory = {str((job / 'BINDING.json').relative_to(root)): sha(job / 'BINDING.json')}
    outputs, remaining, origins = {}, [], []
    for task in original['tasks']:
        directory = root / 'calls' / original['id'] / task['id']
        block = root / 'blocks' / digest([original['id'], task['id']])[:24]
        for parent in (directory, block):
            for path in parent.rglob('*.json'):
                inventory[str(path.relative_to(root))] = sha(path)
        complete = all((directory / str(i) / 'ATTEMPT.json').exists()
                       for i in range(len(branch.task_steps(task))))
        if complete:
            if read(block / 'END.json')['uncertainty']:
                raise ValueError('uncertain completed chain requires separate review')
            status, output = branch.execute_task(root, original, task, outputs, fake, True)
            if status != 'COMPLETE':
                raise ValueError('retained task failed replay')
            outputs[task['id']] = output
            origins.append(original['id'])
        else:
            if directory.exists() or block.exists():
                # This repair admits only a failed first call with no response.
                first = directory / '0'
                end = read(block / 'END.json')
                requests = list(directory.rglob('REQUEST.json'))
                if (requests != [first / 'REQUEST.json'] or list(directory.rglob('RAW.json'))
                    or list(directory.rglob('ATTEMPT.json'))
                    or not read(first / 'TRANSPORT_FAILED.json')['uncertain']
                    or not end['uncertainty']
                    or end['charged_seconds'] != 300 * len(branch.task_steps(task)) + 30):
                    raise ValueError('unsupported partial chain')
                evidence, intermediate = branch.public_for(task, {}, root)
                request = branch.model.request_for(evidence, branch.task_steps(task)[0], intermediate, 4)
                request['model'] = branch.PROFILES[task.get('profile', 'qwen')][0]
                if read(first / 'REQUEST.json')['request'] != request:
                    raise ValueError('failed request differs')
            remaining.append(copy.deepcopy(task))
            origins.append(replacement_id)
    if not remaining or len({t['id'] for t in original['tasks']}) != len(origins):
        raise ValueError('empty recovery or duplicate original tasks')
    replacement = dict(copy.deepcopy(original), id=replacement_id, tasks=remaining,
                       maximum_calls=sum(len(branch.task_steps(t)) for t in remaining))
    replacement_path = root / 'branch_plans' / (replacement_id + '.json')
    freeze(replacement_path, replacement)
    recipe = dict(id=original['id'] + '-recovered', original_path=str(original_path.relative_to(root)),
                  original_digest=digest(original), replacement_path=str(replacement_path.relative_to(root)),
                  replacement_digest=digest(replacement), task_origins=origins, inventory=inventory,
                  sources=pin(), fake=fake,
                  scope='Supplement scores are not the whole-cell comparison. Replay this full roster before interpretation.')
    path = root / 'branch_recovery' / recipe['id'] / 'RECIPE.json'
    freeze(path, recipe)
    return path, replacement_path


def replay(root, recipe_path):
    recipe = read(recipe_path)
    if recipe['sources'] != pin():
        raise ValueError('recovery source changed')
    for name, expected in recipe['inventory'].items():
        if sha(scoped(root, name)) != expected:
            raise ValueError('original evidence changed')
    original = read(scoped(root, recipe['original_path']))
    replacement_path = scoped(root, recipe['replacement_path'])
    replacement = read(replacement_path)
    if digest(original) != recipe['original_digest'] or digest(replacement) != recipe['replacement_digest']:
        raise ValueError('recovery plan changed')
    if (root / 'branch_jobs' / original['id'] / 'COMPLETE.json').exists():
        raise ValueError('original disposition changed')
    if {k: v for k, v in replacement.items() if k not in ('id', 'tasks', 'maximum_calls')} != {
        k: v for k, v in original.items() if k not in ('id', 'tasks', 'maximum_calls')
    }:
        raise ValueError('replacement method differs')
    observed = {str((root / 'branch_jobs' / original['id'] / 'BINDING.json').relative_to(root))}
    observed.update(str(p.relative_to(root)) for p in (root / 'calls' / original['id']).rglob('*.json'))
    for task in original['tasks']:
        block = root / 'blocks' / digest([original['id'], task['id']])[:24]
        observed.update(str(p.relative_to(root)) for p in block.rglob('*.json'))
    if observed != set(recipe['inventory']):
        raise ValueError('original inventory changed')
    origins = recipe['task_origins']
    if (len(origins) != len(original['tasks'])
        or set(origins) - {original['id'], replacement['id']}
        or replacement['tasks'] != [t for t, p in zip(original['tasks'], origins) if p == replacement['id']]):
        raise ValueError('recovery roster differs')
    saved = read(root / 'branch_jobs' / replacement['id'] / 'COMPLETE.json')
    if saved['status'] != 'COMPLETE' or saved['fake'] != recipe['fake']:
        raise ValueError('replacement not complete')
    _, recovered = branch.execute(root, replacement_path, recipe['fake'], replay_only=True)
    outputs = {}
    for task, origin in zip(original['tasks'], origins):
        if origin == replacement['id']:
            outputs[task['id']] = recovered[task['id']]
        else:
            status, output = branch.execute_task(root, original, task, outputs, recipe['fake'], True)
            if status != 'COMPLETE':
                raise ValueError('retained task incomplete')
            outputs[task['id']] = output
    return recipe, original, outputs


def analyze(root, recipe_path):
    recipe, original, outputs = replay(root, recipe_path)
    fit = read(root / 'CHEAP_FIT.json')
    groups, rows = {}, []
    for task in original['tasks']:
        output = outputs[task['id']]
        forecasts = [(task['method'], output['forecast'])] + [
            (name, branch.predict(output['evidence'], fit, aligned=aligned)[0])
            for name, aligned in [('alignment', True), ('marginal', False)]]
        for method, forecast in forecasts:
            key = (task['condition'], task.get('profile', 'qwen'), method)
            if method in ('alignment', 'marginal') and any(
                row['key'] == task['evaluator']['key'] for row in groups.get(key, [])
            ):
                continue
            scored = branch.episode(task['evaluator'], forecast)
            groups.setdefault(key, []).append(scored)
            rows.append(dict(condition=key[0], profile=key[1], method=method, score=scored))
    names = {original['id'], read(scoped(root, recipe['replacement_path']))['id']}
    blocks = [p.parent for p in (root / 'blocks').glob('*/START.json') if read(p)['job'] in names]
    attempts = sum(len(list((root / 'calls' / name).rglob('REQUEST.json'))) for name in names)
    result = dict(status='COMPLETE', recipe_digest=digest(recipe), sources=pin(), fake=recipe['fake'],
                  tasks=len(outputs), retained_calls=sum(len(o['parts']) for o in outputs.values()),
                  attempted_calls_including_failure=attempts,
                  charged_seconds_including_failure=sum(read(p / 'END.json')['charged_seconds'] for p in blocks),
                  cells=[dict(condition=k[0], profile=k[1], method=k[2], **branch.summarize(v)) for k, v in groups.items()],
                  original_remains_incomplete=True, no_fresh_confirmation=True)
    directory = root / 'branch_recovery' / recipe['id']
    freeze(directory / 'ROWS.json', rows)
    freeze(directory / 'COMPLETE.json', result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('recipe', type=Path)
    parser.add_argument('--root', type=Path, default=PRIVATE)
    args = parser.parse_args()
    result = analyze(args.root, args.recipe)
    print(f"Whole-roster replay complete: {result['tasks']} tasks; no inference dispatched")


if __name__ == '__main__':
    main()
