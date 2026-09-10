"""Full 96-unit discarded generation cell on the actual local adapter package.

DESIGN CHECK: I03/C02/X07/X12. Original no-change population construction, header
only, 336 sampled tokens, 28 parsed lines, all attempted calls retained. The actual
source outputs are frozen before evaluation. This is timing, never admission.
NULL: empty/prose/illegal trajectories cannot pass the original broad criterion.
ALTERNATIVE: generated constructor trajectories validate the parser and executor.
"""
import argparse
from collections import Counter
from pathlib import Path
import time
import uuid

from runners.stage8.constructor import population as POP
from runners.stage8.constructor import purpose as PU
from runners.stage8.constructor.gradient import make_world_ext
from runners.stage8.reader import logfmt as LF
from runners.stage9.common import REPO, ROOT, Units, closure, digest, freeze, read
from runners.stage9.competence import rate
from runners.stage9.generation_evaluator import original_broad_comparator, score_attempt
from runners.stage9.generation_policy import LEGACY
from runners.stage9.runtime import execute
from runners.stage9.service_owner import resident


def original_world(lid):
    """Manually reviewed Stage 8 E04 no-change construction, on a fresh pilot band."""
    source = POP.sample_world(lid, finish=False)
    names = source['state']['names']
    world = make_world_ext(lid, source['domain'], source['shape'], goal=source['goal_name'],
                          law_name=names['law'], belief=names['belief'], residue=names['residue'],
                          tendency=names['tendency'],
                          forced_cext={'brief_sections': source['state']['external_context']['brief_sections']},
                          owner_all=source['goal_name'] if source['goal_name'] in PU.PURPOSES else None,
                          no_change=True)
    world['goal_name'] = world['state']['names']['goal']
    return world


def prepare(output):
    path = output / 'WORLD_PLAN.json'
    if path.exists():
        return read(path)
    worlds, excluded = [], []
    for domain in POP.DOMAINS:
        kept = 0
        for i in range(400):
            world = original_world(POP.pop_lid(i, domain, 9920000))
            if world['degenerate']:
                excluded.append({'lineage': world['lid'], 'reason': 'constructor degeneracy'})
                continue
            worlds.append(world)
            kept += 1
            if kept == 48:
                break
        if kept != 48:
            raise ValueError('bounded pilot construction failed to realize 48 units per domain')
    plan = {'worlds': worlds, 'excluded': excluded, 'scope': 'discarded original-population timing only',
            'reference_scores': [POP.marginal_log_likelihood(w)['per_event'] for w in worlds]}
    if any(v is None for v in plan['reference_scores']):
        raise ValueError('missing original reference likelihood')
    freeze(path, plan)
    return plan


def run(family, training, output):
    training, output = Path(training).resolve(), Path(output).resolve()
    complete = read(training / 'COMPLETE.json')
    adapter = training / complete['selected_checkpoint']
    if closure([adapter])['sha256'] != complete['selected_checkpoint_sha256']:
        raise ValueError('pilot adapter checkpoint identity changed')
    plan = prepare(output)
    source_files = [REPO / 'runners/stage9' / name for name in (
        'generation_pilot.py', 'common.py', 'competence.py', 'scoring.py',
        'generation_evaluator.py', 'generation_policy.py', 'runtime.py', 'reader.py',
        'features.py', 'service_owner.py', 'model_service.py', 'neural.py', 'train.py')]
    sources = closure(source_files + [REPO / 'runners/stage7/constructor',
                       REPO / 'runners/stage7/reader', REPO / 'runners/stage8/constructor',
                       REPO / 'runners/stage8/reader/logfmt.py', REPO / 'runners/readout_repair.py',
                       REPO / 'runners/stage7/runtime.py', REPO / 'runners/s5_lib.py'])
    identity = {'family': family, 'training_complete': complete, 'world_plan_sha256': digest(plan),
                'sources': sources, 'attempts': 96, 'generation': LEGACY,
                'max_new_tokens': 336, 'max_lines': 28, 'precision': 'float16',
                'scope': 'discarded complete generation timing; no scientific admission'}
    units = Units(output, identity)
    if (output / 'COMPLETE.json').exists():
        return read(output / 'COMPLETE.json')
    started = time.time()
    config = {'family': family, 'adapter': str(adapter), 'adapter_sha256': closure([adapter])['sha256'],
              'precision': 'float16', 'device': 'cuda', 'batch_size': 4,
              'max_context': 4096, 'max_support': 128, 'max_new_tokens': 336, 'generation': LEGACY}
    with resident(output / 'services' / uuid.uuid4().hex[:12], config) as (ready, token):
        freeze(output / 'PACKAGE.json', ready['identity'])
        for i, world in enumerate(plan['worlds']):
            if units.get(world['lid']) is not None:
                continue
            ev = POP.evidence_at(world, world['cut'], {'unit_ref': 'u', 'condition_ref': 'header'})
            evidence = {'prefix': LF.compose([], LF.header_from_evidence(ev), []), 'options': {}}
            task = {'operation': 'generate', 'identity': {**ready['identity'], 'information_sha256': digest(evidence)},
                    'max_new_tokens': 336, 'seed': 992001 + i}
            result = execute(evidence, task, ready['endpoint'], token, root=output / 'capsules', timeout=900)
            units.put(world['lid'], {'result': result, 'domain': world['domain'], 'seed': task['seed']})
    # Evaluation begins only after every attempted generation is durably committed.
    attempts = [score_attempt(w, units.get(w['lid'])['result']) for w in plan['worlds']]
    frozen_evaluation = {'attempts': attempts, 'worlds': [w['lid'] for w in plan['worlds']]}
    freeze(output / 'EVALUATION.json', frozen_evaluation)
    comparison = original_broad_comparator(attempts, plan['reference_scores'], 96)
    valid_only = [a for a in attempts if a['valid_execution']]
    # Stage 8 excluded invalid reader executions. Keep that denominator explicitly
    # beside the complete-attempt rule; they coincide only if all calls were valid.
    old_denominator = original_broad_comparator(valid_only, plan['reference_scores'], len(valid_only)) if valid_only else None
    rates = {name: rate(sum(bool(a[name]) for a in attempts), 96)
             for name in ('valid_execution', 'legacy_feasible', 'strict_feasible', 'stopped')}
    receipt = {'identity_sha256': digest(identity), 'complete': True, 'attempts': 96,
               'domains': dict(Counter(w['domain'] for w in plan['worlds'])),
               'world_construction_excluded': len(plan['excluded']), 'wall_seconds': time.time() - started,
               'full_attempt_comparator': comparison, 'historical_valid_only_denominator': old_denominator,
               'rates': rates, 'completed_at': time.time(), 'scientific_admission': False,
               'limitation': 'discarded adapter/pilot units; original likelihood conditions on true tendency; no expanded-population or scientific package passage'}
    freeze(output / 'COMPLETE.json', receipt)
    return receipt


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--family', required=True, choices=['qwen', 'smollm'])
    p.add_argument('--training', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    run(args.family, args.training, args.output)
