"""Earlier-artifact training rules and concrete exceptions; fixed executor.

DESIGN CHECK: LESSONS2-5, reader priors/traversal and reconstruction corrections.
NULL: constant or balanced uninformative targets admit no nonconstant procedure.
ALTERNATIVE: a repeatable feature boundary admits an executable rule, retaining
its mistakes as candidate memories. Both branches need two writer components;
this is a training support filter, NOT a generalization or significance gate.
R1 and R4 use the same view-specific pool and 6000-byte representation ceiling.
Human rules are approximate behavior hypotheses; native Ghost motifs are not
human operation laws. No historical goal or personal-procedure truth is inferred.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import math
from pathlib import Path
import time

from . import earlier_programs as programs
from .contracts import canonical, digest
from .ollama import now, write_new
from .queue import read
from .reader import from_record, tokens

STORE_BYTES = 6000
MAX_EXAMPLES = 2
MAX_RULES = 3


def identity():
    paths = ['earlier_memory.py', 'earlier_programs.py', 'human_programs.py', 'coauthor.py', 'contracts.py', 'reader.py']
    return {p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
            for p in ['runners/stage10/' + f for f in paths] + ['runners/stage9/program_inference.py']}


def joined(training, answers):
    truth = {r['task_id']: r for r in answers}
    if not training or len(truth) != len(answers) or len(training) != len(truth) or set(truth) != {r['task_id'] for r in training}:
        raise ValueError('training records must join one to one')
    rows = []
    for r in sorted(training, key=lambda r: r['task_id']):
        task = from_record(r); answer = truth[task.task_id]
        description = dict(task.choices).get(answer['correct_choice'])
        action = next((k for k, v in programs.DESCRIPTIONS.items() if v == description), None)
        if action is None or not answer.get('writer_component') or not answer.get('source_event'):
            raise ValueError('training action or dependency metadata missing')
        rows.append({'task': task, 'features': programs.features(task), 'action': action,
                     'group': answer['writer_component'], 'event': answer['source_event']})
    return rows


def induce(training, answers):
    """Small decision stumps; training-only selection, never a claimed true plan."""
    rows = joined(training, answers); libraries = {}; counts = 0
    for view in sorted({r['task'].evidence_view for r in rows}):
        subset = [r for r in rows if r['task'].evidence_view == view]
        if len({r['event'] for r in subset}) != len(subset):
            raise ValueError('a repeated view/event cannot increase rule support')
        groups = Counter(r['group'] for r in subset)
        weight = [1 / (len(groups) * groups[r['group']]) for r in subset]
        constant_loss = min(sum(w for r, w in zip(subset, weight) if r['action'] != a) for a in programs.ACTIONS)
        candidates = []
        for feature in programs.FEATURES.keys() - {'constant'}:
            values = sorted({r['features'][feature] for r in subset})
            for left, right in zip(values, values[1:]):
                threshold = (left + right) / 2
                if threshold > 100000:
                    continue
                sides = [[i for i, r in enumerate(subset) if (r['features'][feature] < threshold) == lower] for lower in (True, False)]
                if any(len({subset[i]['group'] for i in side}) < 2 for side in sides):
                    continue
                actions = [min(programs.ACTIONS, key=lambda a: (sum(weight[i] for i in side if subset[i]['action'] != a), a)) for side in sides]
                if actions[0] == actions[1]:
                    continue
                program = dict(feature=feature, threshold=threshold, below=actions[0], otherwise=actions[1])
                predictions = [programs.execute(program, r['features'])['action'] for r in subset]
                counts += len(subset)
                loss = sum(w for r, w, pred in zip(subset, weight, predictions) if r['action'] != pred)
                if loss >= constant_loss - 1e-12:
                    continue
                candidates.append({'program': program, 'training_loss': loss, 'constant_training_loss': constant_loss,
                                   'branch_groups': [len({subset[i]['group'] for i in side}) for side in sides],
                                   'correct_training_ids': [r['task'].task_id for r, p in zip(subset, predictions) if p == r['action']],
                                   'exception_training_ids': [r['task'].task_id for r, p in zip(subset, predictions) if p != r['action']]})
        # Different thresholds with the same branch meaning are distinct rules,
        # but keep at most one rule per feature, chosen before any target access.
        selected = []; features = set()
        for c in sorted(candidates, key=lambda c: (c['training_loss'], canonical(c['program']))):
            if c['program']['feature'] in features:
                continue
            selected.append(c); features.add(c['program']['feature'])
            if len(selected) == MAX_RULES:
                break
        libraries[view] = selected
    return {'libraries': libraries, 'executor_evaluations': counts,
            'training_sha256': digest(training), 'answers_sha256': digest(answers),
            'selection': 'writer-balanced training error below best constant; two components on each branch; at most one rule per feature',
            'meaning': 'training-induced feature rules, not validated human plans or historical goals'}


def fit(prepared, output):
    start = time.perf_counter(); frozen = read(prepared / 'FROZEN.json')
    public = read(prepared / 'train-public.json'); target = read(prepared / 'train-evaluator.json')
    if digest(public) != frozen['public_sha256']['train'] or digest(target) != frozen['evaluator_sha256']['train']:
        raise ValueError('frozen training source changed')
    manifest = {'sources': identity(), 'frozen_sha256': digest(frozen)}
    result = induce(public['tasks'], target['targets'])
    result['manifest'] = manifest
    path = output / 'MEMORY.json'
    if path.exists():
        saved = read(path)
        if any(saved[k] != result[k] for k in result):
            raise ValueError('saved human memory does not reproduce')
        return saved
    output.mkdir(parents=True, exist_ok=True)
    result.update(at=now(), wall_seconds=time.perf_counter()-start, model_calls=0)
    write_new(path, result)
    return result


def represent(task, training, answers, learned, arm):
    """No private grouping, identifiers or target outcomes enter the model view."""
    started = time.perf_counter()
    if arm not in {'R1-memory', 'R4-opaque', 'R4-grounded'}:
        raise ValueError('undeclared human memory condition')
    if digest(training) != learned['training_sha256'] or digest(answers) != learned['answers_sha256']:
        raise ValueError('memory and retrieval source pools differ')
    rows = joined(training, answers)
    programs.features(task)
    if task.task_id in {r['task'].task_id for r in rows}:
        raise ValueError('target occurs in training')
    procedures = []; exceptions = set()
    for i, rule in enumerate(learned['libraries'].get(task.evidence_view, []) if arm != 'R1-memory' else []):
        p = rule['program']
        item = {'id': 'p' + str(i), 'program': p}
        if arm == 'R4-grounded':
            item['description'] = f"If {p['feature']} < {p['threshold']}, predict {p['below']}; otherwise {p['otherwise']}."
            item['training_uses'] = {'matching': len(rule['correct_training_ids']), 'exceptions': len(rule['exception_training_ids'])}
        procedures.append(item); exceptions.update(rule['exception_training_ids'])
    representation = {'procedures': procedures, 'examples': [],
                      'scope': 'generic training rules and episodes; no personal or historical intent claim'}
    if len(canonical(representation).encode('utf8')) > STORE_BYTES:
        raise ValueError('procedure definitions exceed common memory ceiling')
    query = tokens(task.evidence); ranked = []
    for r in rows:
        source = r['task']
        if source.evidence_view != task.evidence_view:
            continue
        count = tokens(source.evidence)
        norm = math.sqrt(sum(v*v for v in query.values()) * sum(v*v for v in count.values()))
        similarity = sum(v*count.get(k, 0) for k, v in query.items()) / norm if norm else 0
        ranked.append((0 if source.task_id in exceptions else 1, -similarity, source.task_id, r))
    ids = []; skipped = []
    for _, _, identifier, r in sorted(ranked, key=lambda r: r[:3]):
        source = r['task']
        episode = {'evidence_view': source.evidence_view, 'evidence': source.evidence,
                   'question': source.question, 'observed_outcome': programs.DESCRIPTIONS[r['action']]}
        candidate = {**representation, 'examples': [*representation['examples'], episode]}
        if len(canonical(candidate).encode('utf8')) > STORE_BYTES:
            skipped.append(identifier); continue
        representation = candidate; ids.append(identifier)
        if len(ids) == MAX_EXAMPLES:
            break
    # Empty stores are explicit behavior, never invented or truncated examples.
    receipt = {'arm': arm, 'training_sha256': digest(training), 'answers_sha256': digest(answers),
               'memory_sha256': digest(learned), 'selected_ids': ids, 'size_skipped_ids': skipped,
               'exception_ids': [i for i in ids if i in exceptions], 'store_bytes': len(canonical(representation).encode('utf8')),
               'store_limit_bytes': STORE_BYTES, 'representation_sha256': digest(representation),
               'wall_seconds': time.perf_counter()-started, 'executor_evaluations': 0, 'model_calls': 0}
    return representation, receipt
