"""Known-answer and isolation checks for training-only human memory.

DESIGN CHECK: LESSONS2-5. Repeated informative branches must be learned; balanced
noise, constant targets and single-component support must admit no procedure.
Wrong labels/joins/private fields and changed frozen inputs must be refused.
This is an instrument check with constructed data, not a scientific comparison.
"""
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
from tempfile import TemporaryDirectory
from . import human_memory as memory, human_programs as programs
from .contracts import PublicTask, choices_for, digest, canonical
from .ollama import write_new, now


def task(i, words, view='artifact'):
    evidence = {'document': 'word ' * words, 'suggestions': ['word idea']}
    if view == 'process-record':
        evidence['earlier_handling'] = ['edit']
    return PublicTask(digest(['constructed-human-memory', i])[:32], 'coauthor-handling', view,
                      evidence, 'Predict subsequent handling.', choices_for(list(programs.DESCRIPTIONS.values()), str(i)),
                      'before next menu', 'human handling of model suggestions', 'constructed instrument case')


def rows(kind='signal'):
    public = []; answers = []
    for g in range(3):
        for words in (1, 12):
            actions = list(programs.ACTIONS) if kind == 'null' else [('accept' if words == 1 else 'edit') if kind != 'constant' else 'accept']
            for a in actions:
                t = task(len(public), words)
                public.append(asdict(t))
                answers.append({'task_id': t.task_id, 'writer_component': str(g) if kind != 'one-group' else 'one',
                                'source_event': t.task_id, 'correct_choice': next(k for k, v in t.choices if v == programs.DESCRIPTIONS[a])})
    return public, answers


def run(output):
    checks = []
    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)
    def refuse(name, f):
        try:
            f()
        except ValueError:
            checks.append(name); return
        raise AssertionError(name)
    training, answers = rows()
    learned = memory.induce(training, answers)
    rule = learned['libraries']['artifact'][0]['program']
    check('planted boundary executes both unseen sides', all(programs.execute(rule, programs.features(task(100+i, n)))['action'] == a for i, (n, a) in enumerate(((2, 'accept'), (10, 'edit')))))
    for kind in ('null', 'constant', 'one-group'):
        check(kind + ' admits no procedure', not memory.induce(*rows(kind))['libraries']['artifact'])
    check('row ordering cannot change induction', memory.induce(training[::-1], answers[::-1])['libraries'] == learned['libraries'])
    altered = deepcopy(answers); altered[0]['correct_choice'] = 'o_00000000'
    refuse('unsupported training answer', lambda: memory.induce(training, altered))
    refuse('duplicate training records', lambda: memory.induce(training + [training[0]], answers))
    changed = deepcopy(training); changed[0]['evidence']['private_goal'] = 'forbidden'
    refuse('private evidence fields', lambda: memory.induce(changed, answers))
    target = task(100, 3)
    refuse('in-training target', lambda: memory.represent(memory.from_record(training[0]), training, answers, learned, 'R1-memory'))
    refuse('changed pool', lambda: memory.represent(target, training, altered, learned, 'R4-opaque'))
    representations = {}
    for arm in ('R1-memory', 'R4-opaque', 'R4-grounded'):
        rep, receipt = memory.represent(target, training, answers, learned, arm)
        representations[arm] = rep
        check(arm + ' exact common byte cap', receipt['store_bytes'] == len(canonical(rep).encode('utf8')) <= memory.STORE_BYTES)
        check(arm + ' private grouping absent', all(key not in canonical(rep) for key in ('writer_component', 'source_event', 'correct_training_ids')))
        reordered, _ = memory.represent(replace(target, choices=target.choices[::-1]), training, answers, learned, arm)
        check(arm + ' option permutation invariance', reordered == rep)
    check('opaque and grounded definitions identical', [r['program'] for r in representations['R4-opaque']['procedures']] == [r['program'] for r in representations['R4-grounded']['procedures']])
    check('retrieval contains no induced procedures', not representations['R1-memory']['procedures'])
    # A retained mistake is prioritized without altering its observed outcome.
    exception_answers = deepcopy(answers)
    exception_answers[-1]['correct_choice'] = next(k for k, v in memory.from_record(training[-1]).choices if v == programs.DESCRIPTIONS['dismiss'])
    exceptional = memory.induce(training, exception_answers)
    rep, receipt = memory.represent(target, training, exception_answers, exceptional, 'R4-opaque')
    check('actual training exception retained first', bool(receipt['exception_ids']) and receipt['selected_ids'][0] == training[-1]['task_id'])
    check('exception outcome unchanged', rep['examples'][0]['observed_outcome'] == programs.DESCRIPTIONS['dismiss'])
    # The artifact view must not inherit rules fitted to process-only evidence.
    check('absent view has no borrowed procedures', not memory.represent(task(200, 4, 'process-record'), training, answers, learned, 'R4-opaque')[0]['procedures'])
    output.mkdir(parents=True, exist_ok=False)
    with TemporaryDirectory(dir=output) as tmp:
        root = Path(tmp); prepared = root/'source'; prepared.mkdir()
        public = {'tasks': training}; labels = {'targets': answers}
        frozen = {'public_sha256': {'train': digest(public)}, 'evaluator_sha256': {'train': digest(labels)}}
        for name, value in [('FROZEN.json', frozen), ('train-public.json', public), ('train-evaluator.json', labels)]:
            write_new(prepared/name, value)
        first = memory.fit(prepared, root/'fit')
        check('complete fit replay is immutable', memory.fit(prepared, root/'fit') == first)
        original_read = memory.read
        def guarded(path):
            if path.name not in {'FROZEN.json', 'train-public.json', 'train-evaluator.json', 'MEMORY.json'}:
                raise AssertionError('nontraining file accessed')
            return original_read(path)
        memory.read = guarded
        try:
            check('fit reads training only', memory.fit(prepared, root/'fit') == first)
        finally:
            memory.read = original_read
        (prepared/'train-public.json').write_text(canonical({'tasks': changed}), encoding='utf8')
        refuse('frozen training corruption refused', lambda: memory.fit(prepared, root/'fit'))
    result = {'at': now(), 'status': 'PASS', 'checks': checks, 'sources': memory.identity(),
              'actual_model_calls': 0, 'scope': 'constructed memory instrument; literal route pilot and scientific comparisons still required'}
    write_new(output/'COMPLETE.json', result)
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    print(canonical(run(parser.parse_args().output)))
