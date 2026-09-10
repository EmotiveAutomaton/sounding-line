"""Collect actual learner-prefix attempts and correct continuations in discarded pilots.

DESIGN CHECK: C01/C05/X08; Ross et al. 2011, Algorithm 3.1, motivates visited-state labels.
This is a fixed-policy collection adaptation, not iterative DAgger or its regret theorem.
NULL: invalid output leaves state unchanged and cannot masquerade as a learner visit.
ALTERNATIVE: the actual applied actions determine the teacher's continued clock/state.
Endpoint inputs contain only rendered visible context; teacher targets stay private.
"""
import argparse
import copy
from pathlib import Path
import time
import uuid

from runners.stage8.reader import logfmt as LF
from runners.stage9.common import REPO, ROOT, Units, closure, digest, freeze, read
from runners.stage9.construction import Replay, rendered_prefix
from runners.stage9.recipes import sampled_world, POP, parameter_partition
from runners.stage9.runtime import execute
from runners.stage9.service_owner import resident


MATCHED_TEACHER_DRAWS = 4


def collect_one(world, predict, maximum_actions=4, teacher_draws=MATCHED_TEACHER_DRAWS, render=rendered_prefix):
    cut = min(2, len(world['trajectory']['steps']))
    history = copy.deepcopy(world['trajectory']['steps'][:cut])
    replay = Replay(world, history, extend_visible=True)
    attempts, examples = [], []
    visited = 0
    for turn in range(maximum_actions + 1):
        prefix = render(world, replay.steps)
        # Each independent continuation begins at this exact actual prefix.
        targets = []
        for draw in range(teacher_draws):
            teacher = Replay(world, replay.steps, extend_visible=True)
            tail, stopped = teacher.continue_teacher(int(digest({'world': world['lid'], 'turn': turn, 'draw': draw})[:12], 16))
            lines = [LF.event_line(e['i'], e['type'], e['section'], e['slot'], e['outcome']) for e in tail]
            if stopped:
                lines.append(LF.stop_line(len(teacher.steps)))
            if lines:
                targets.append({'target': '\n'.join(lines), 'stopped': stopped, 'events': tail})
        examples.append({'prefix': prefix, 'targets': targets, 'learner_actions_applied': visited,
                         'actual_state_sha256': digest(replay.snapshot()), 'actual_prefix': copy.deepcopy(replay.steps),
                         'extensions': copy.deepcopy(replay.extensions), 'teacher_clock': len(replay.steps)})
        if turn == maximum_actions:
            break
        evidence = {'prefix': prefix, 'options': {}}
        result = predict(evidence, turn)
        before = digest(replay.snapshot())
        attempt = {'turn': turn, 'evidence_sha256': digest(evidence), 'result': result,
                   'state_before_sha256': before, 'applied': False}
        if not result.get('accepted'):
            attempt['failure'] = 'invalid reader execution'
            attempts.append(attempt)
            break
        text = result['prediction']['text']
        nonempty = [line.strip() for line in text.splitlines() if line.strip()]
        event = LF.parse_line(nonempty[0]) if nonempty else None
        attempt['unused_generated_lines'] = nonempty[1:]
        if event is None or event['i'] != len(replay.steps):
            attempt['failure'] = 'first generated line is not a current-clock action'
            attempts.append(attempt)
            break
        if event.get('stop'):
            attempt['stopped'] = True
            attempts.append(attempt)
            break
        try:
            actual = replay.apply(event)
        except ValueError as exc:
            assert digest(replay.snapshot()) == before
            attempt['failure'] = str(exc)
            attempts.append(attempt)
            break
        attempt.update(applied=True, actual=actual, state_after_sha256=digest(replay.snapshot()))
        attempts.append(attempt)
        visited += 1
    return {'lineage': world['lid'], 'domain': world['domain'], 'starting_expert_events': cut,
            'attempts': attempts, 'examples': examples, 'learner_actions_applied': visited,
            'scope': 'one-action free proposals with first-line parsing; all extra output retained; not full-rollout admission'}


def pilot(family, training, output, count=64):
    if count != 64:
        raise ValueError('the prespecified discarded collection pilot has 64 worlds')
    output, training = Path(output).resolve(), Path(training).resolve()
    training_complete = read(training / 'COMPLETE.json')
    adapter = training / training_complete['selected_checkpoint']
    sources = closure([REPO / 'runners/stage9', REPO / 'runners/stage7/constructor', REPO / 'runners/stage7/reader',
                       REPO / 'runners/stage8/constructor', REPO / 'runners/stage8/reader/logfmt.py'])
    identity = {'family': family, 'training_complete': training_complete, 'sources': sources, 'count': count,
                'actions_per_world': 4, 'teacher_draws_per_state': 4, 'band': 9940000,
                'coverage': 'both', 'scope': 'discarded collection timing and target/exposure accounting only',
                'source_operation': 'https://proceedings.mlr.press/v15/ross11a/ross11a.pdf Algorithm 3.1, read pp.627-630; fixed-policy adaptation, no inherited guarantee'}
    units = Units(output, identity)
    if (output / 'COMPLETE.json').exists():
        return read(output / 'COMPLETE.json')
    config = {'family': family, 'adapter': str(adapter), 'adapter_sha256': closure([adapter])['sha256'],
              'precision': 'bfloat16', 'device': 'cuda', 'batch_size': 1,
              'max_context': 2048, 'max_support': 128, 'max_new_tokens': 64}
    started = time.time()
    with resident(output / 'services' / uuid.uuid4().hex[:12], config) as (ready, token):
        for domain in POP.DOMAINS:
            for i in range(count // 2):
                key = domain + '-' + str(i)
                if units.get(key) is not None:
                    continue
                world = sampled_world(POP.pop_lid(i, domain, 9940000), 'both')
                def predict(evidence, turn):
                    return execute(evidence, {'operation': 'generate', 'identity': {**ready['identity'], 'information_sha256': digest(evidence)},
                                              'max_new_tokens': 32, 'seed': 99001 + i * 10 + turn},
                                   ready['endpoint'], token, root=output / 'capsules', timeout=900)
                row = collect_one(world, predict)
                row['parameter_partition_for_future_science'] = parameter_partition(world)
                units.put(key, row)
    rows = [u['row'] for u in units.all()]
    from transformers import AutoTokenizer
    from runners.stage9.train import BASES
    base = BASES[family]
    tok = AutoTokenizer.from_pretrained(base['model'], revision=base['revision'], local_files_only=True)
    lengths = [{'prefix_tokens': len(tok(e['prefix'], add_special_tokens=True).input_ids),
                'target_tokens': [len(tok(t['target'] + tok.eos_token, add_special_tokens=False).input_ids) for t in e['targets']],
                'learner_actions_applied': e['learner_actions_applied']} for r in rows for e in r['examples']]
    receipt = {'identity_sha256': digest(identity), 'worlds_attempted': len(rows), 'wall_seconds': time.time() - started,
               'actual_learner_actions': sum(r['learner_actions_applied'] for r in rows),
               'worlds_with_actual_learner_visits': sum(r['learner_actions_applied'] > 0 for r in rows),
               'lengths': lengths, 'completed_at': time.time(), 'training_match_accepted': False,
               'limitation': 'invalid/stopped first proposals create no learner-visited successor; retained, never replaced'}
    freeze(output / 'COMPLETE.json', receipt)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--family', choices=['qwen', 'smollm'], required=True)
    parser.add_argument('--training', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    pilot(args.family, args.training, args.output)
