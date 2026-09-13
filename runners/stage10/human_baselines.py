"""Frozen, training-only inexpensive CoAuthor handling controls.

DESIGN CHECK: LESSONS3-5 and CONTROLS1-6 reread. NULL: balanced labels
independent of features yield uniform priors and feature predictions. ALTERNATIVE:
a planted length/lexical relation is learned without writer or target identifiers.
Missing classes retain their zero empirical prior; fixed always-ignore remains
an explicit control, never a replacement for invalid reader output. All fitting
and standardization use training only; evaluation answers are never opened.
"""
from collections import Counter
import hashlib
from pathlib import Path
import re
import time

import numpy as np

from . import human_programs as programs
from .contracts import digest
from .human_memory import joined
from .ollama import now, write_new
from .queue import read
from .reader import from_record

ARMS = ('class-prior', 'surface-features', 'always-ignore', 'previous-handling')
CONFIG = dict(schema='stage10.human-cheap-controls.1', bins=32, steps=1000,
              learning_rate=.1, l2=.01, lexical_scale=1.0,
              training='writer-balanced within view; no development or evaluation fitting')


def identity():
    paths = ['human_baselines.py', 'human_memory.py', 'human_programs.py', 'coauthor.py',
             'reader.py', 'contracts.py', 'queue.py', 'ollama.py']
    return {p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
            for p in ['runners/stage10/'+name for name in paths]}


def vector(task):
    tokens = lambda text: re.findall(r'\w+', text.casefold())
    observed = programs.features(task)  # validates exact evidence whitelist
    document = task.evidence['document']; suggestions = task.evidence['suggestions']
    lengths = [len(tokens(s)) for s in suggestions]
    # Menu position is represented before outcomes: lengths and draft overlap by slot.
    # No selected position, later edit, group ID or response enters these features.
    values = [np.log1p(observed['draft_words']), np.log1p(len(suggestions)),
              np.log1p(min(lengths)), np.log1p(max(lengths)), np.log1p(sum(lengths)/len(lengths)),
              observed['maximum_word_overlap']]
    doc_words = set(tokens(document))
    for index in range(5):
        text = suggestions[index] if index < len(suggestions) else ''
        words = tokens(text)
        values += [int(index < len(suggestions)), np.log1p(len(words)),
                   len(set(words) & doc_words)/max(1, len(set(words)))]
    for text in (document, ' '.join(suggestions)):
        words = tokens(text); hashed = [0.] * CONFIG['bins']
        for word in words:
            index = int(hashlib.sha256(word.encode('utf8')).hexdigest()[:8], 16) % CONFIG['bins']
            hashed[index] += 1/max(1, len(words))
        values.extend(hashed)
    return values


def softmax(logits):
    exp = np.exp(logits - logits.max(axis=-1, keepdims=True))
    return exp / exp.sum(axis=-1, keepdims=True)


def fit(training, answers):
    rows = joined(training, answers); models = {}
    for view in sorted({r['task'].evidence_view for r in rows}):
        subset = [r for r in rows if r['task'].evidence_view == view]
        if len({r['event'] for r in subset}) != len(subset):
            raise ValueError('duplicate training event within view')
        groups = Counter(r['group'] for r in subset)
        weights = np.array([1/(len(groups)*groups[r['group']]) for r in subset])
        x = np.array([vector(r['task']) for r in subset], dtype=float)
        y = np.array([[float(r['action'] == a) for a in programs.ACTIONS] for r in subset])
        mean = (weights[:,None]*x).sum(axis=0)
        scale = np.sqrt((weights[:,None]*(x-mean)**2).sum(axis=0))
        scale[scale < 1e-12] = 1
        x = np.column_stack([np.ones(len(x)), (x-mean)/scale])
        coef = np.zeros((x.shape[1], len(programs.ACTIONS)))
        # Fixed convex multinomial logistic objective; no validation-driven tuning.
        for _ in range(CONFIG['steps']):
            gradient = x.T @ (weights[:,None]*(softmax(x @ coef)-y))
            gradient[1:] += CONFIG['l2']*coef[1:]
            coef -= CONFIG['learning_rate']*gradient
        if not np.isfinite(coef).all():
            raise ValueError('nonfinite cheap feature fit')
        models[view] = dict(mean=mean.tolist(), scale=scale.tolist(), coef=coef.tolist(),
                            prior=(weights[:,None]*y).sum(axis=0).tolist(),
                            events=len(subset), writer_groups=len(groups))
    return dict(config=CONFIG, models=models, actions=list(programs.ACTIONS),
                training_sha256=digest(training), training_answers_sha256=digest(answers),
                numpy_version=np.__version__)


def predict(task, fitted, arm):
    if arm not in ARMS or fitted['config'] != CONFIG or fitted['actions'] != list(programs.ACTIONS):
        raise ValueError('unknown baseline or changed fitted contract')
    model = fitted['models'][task.evidence_view]
    x = np.array(vector(task))
    if arm == 'surface-features':
        x = np.concatenate([[1.], (x-np.array(model['mean']))/np.array(model['scale'])])
        probabilities = softmax(x @ np.array(model['coef'])).tolist()
    elif arm == 'always-ignore':
        probabilities = [float(a == 'ignore') for a in programs.ACTIONS]
    elif arm == 'previous-handling' and task.evidence.get('earlier_handling'):
        probabilities = [float(a == task.evidence['earlier_handling'][-1]) for a in programs.ACTIONS]
    else:
        probabilities = model['prior']
    action = programs.ACTIONS[max(range(len(probabilities)), key=lambda i: probabilities[i])]
    by_description = {description: key for key, description in task.choices}
    return dict(choice=by_description[programs.DESCRIPTIONS[action]],
                probabilities={by_description[programs.DESCRIPTIONS[a]]: p for a, p in zip(programs.ACTIONS, probabilities)},
                explanation='Frozen inexpensive '+arm+' control; no historical goal claim.',
                insufficient_evidence=False)


def run(prepared, output):
    started = time.perf_counter()
    frozen = read(prepared/'FROZEN.json')
    public = {phase: read(prepared/(phase+'-public.json')) for phase in ('train','development','evaluation')}
    answers = read(prepared/'train-evaluator.json')
    if any(digest(value) != frozen['public_sha256'][phase] for phase, value in public.items()) or digest(answers) != frozen['evaluator_sha256']['train']:
        raise ValueError('frozen baseline inputs changed')
    manifest = dict(sources=identity(), frozen_sha256=digest(frozen), config=CONFIG,
                    numpy_version=np.__version__, evaluation_outcomes_opened=False)
    fitted = fit(public['train']['tasks'], answers['targets'])
    records = []
    for phase in ('development', 'evaluation'):
        for row in public[phase]['tasks']:
            task = from_record(row)
            for arm in ARMS:
                records.append(dict(phase=phase, task_id=task.task_id, arm=arm, task_public=task.public(),
                                    status='VALID', forecast=predict(task, fitted, arm), model_calls=0))
    result = dict(manifest=manifest, fitted=fitted, predictions=records)
    if (output/'COMPLETE.json').exists():
        saved = read(output/'COMPLETE.json')
        if saved['result_sha256'] != digest(result) or read(output/'RESULT.json') != result:
            raise ValueError('saved baseline fit or forecasts changed')
        return saved
    output.mkdir(parents=True, exist_ok=False)
    write_new(output/'RESULT.json', result)
    complete = dict(at=now(), status='COMPLETE', result_sha256=digest(result),
                    predictions=len(records), model_calls=0, sources=identity(),
                    wall_seconds=time.perf_counter()-started, target_outcomes_opened=False,
                    scope='complete training-only baseline producer; common comparison pending')
    write_new(output/'COMPLETE.json', complete)
    return complete
