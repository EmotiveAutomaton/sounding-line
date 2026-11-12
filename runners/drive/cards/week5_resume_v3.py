"""Module-scoped operational quanta over authenticated Week 5 checkpoints.

DESIGN CHECK: LESSONS 3-5. No scientific parameter, source pin or saved output
may change. This successor adds only reviewed producer stopping bounds; the
original adapter remains immutable. Both successful and failed science use
the same byte and native-owner checks.
"""
from pathlib import Path
import math
import shutil
from .batch_runtime import read, freeze, filehash, check_files
from .week5_resume import output_manifest
from runners.stage9.process_identity import is_same_live_process

BASE_KEYS = frozenset({'max_new_draws', 'max_wall_seconds'})
MODULE_KEYS = {
    'runners.drive.cards.week5_ex1': frozenset({'max_new_documents'}),
    'runners.drive.cards.week5_go_history_bounded_h2': frozenset({'max_new_documents', 'max_cpu_seconds'}),
    'runners.drive.cards.week5_bk_ca1_features': frozenset({'max_new_chunks'}),
    'runners.drive.cards.week5_bk_v1': frozenset({'max_new_fits'}),
}


def semantic_config(module, config):
    operational = BASE_KEYS | MODULE_KEYS.get(module, frozenset())
    for key in operational & config.keys():
        value = config[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError('Invalid operational bound: ' + key)
        if key.startswith('max_new_') and int(value) != value:
            raise ValueError('Nonintegral checkpoint quantum: ' + key)
    return {k: v for k, v in config.items() if k not in operational}


def copy_checkpoint(root, plan):
    spec = plan.get('resume')
    if not spec:
        return None
    from .week5_policy import ROOT
    old = Path(spec['root']).resolve()
    root = Path(root).resolve()
    campaign = Path(ROOT).resolve()
    old.relative_to(campaign)
    root.relative_to(campaign)
    if old == root:
        raise ValueError('Resume requires a new attempt root')
    for name, key in [('PLAN.json', 'plan_sha256'), ('PAUSED.json', 'paused_sha256')]:
        if filehash(old / name) != spec[key]:
            raise ValueError('Resume receipt pin mismatch')
    prior = read(old / 'PLAN.json')
    paused = read(old / 'PAUSED.json')
    if any((old / n).exists() for n in ('COMPLETE.json', 'FAILED.json')):
        raise ValueError('Ambiguous predecessor')
    owner = read(old / 'OWNER.json')
    if owner.get('plan_sha256') != spec['plan_sha256']:
        raise ValueError('Native owner plan binding mismatch')
    if is_same_live_process(owner['native']):
        raise ValueError('Predecessor still live')
    if paused.get('status') != 'PAUSED' or not paused.get('checkpoint_validation_required'):
        raise ValueError('Not a resumable pause')
    for key in ('module', 'inputs', 'family', 'campaign'):
        if plan[key] != prior[key]:
            raise ValueError('Changed scientific resume contract: ' + key)
    if semantic_config(plan['module'], plan['config']) != semantic_config(prior['module'], prior['config']):
        raise ValueError('Changed scientific configuration')
    # The successor may add its adapter/runtime closure, but never drop or
    # reinterpret a source, validation, input or predecessor-runtime pin.
    if any(plan['pins'].get(p) != digest for p, digest in prior['pins'].items()):
        raise ValueError('Dropped or changed predecessor pin')
    check_files(prior['pins'])
    check_files(plan['pins'])
    expected = paused.get('checkpoint_outputs')
    if not isinstance(expected, dict) or not expected or output_manifest(old / 'output') != expected:
        raise ValueError('Incomplete or changed checkpoint manifest')
    target = root / 'output'
    if target.exists() and any(target.iterdir()):
        raise ValueError('Resume target must be empty')
    for name, digest in expected.items():
        source = (old / 'output' / name).resolve()
        source.relative_to((old / 'output').resolve())
        dest = (target / name).resolve()
        dest.relative_to(target.resolve())
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        if filehash(dest) != digest:
            raise ValueError('Checkpoint copy mismatch')
    if output_manifest(target) != expected:
        raise ValueError('Checkpoint copy incomplete')
    receipt = dict(predecessor=str(old), plan_sha256=spec['plan_sha256'],
                   paused_sha256=spec['paused_sha256'], copied=expected,
                   adapter='week5_resume_v3', module=plan['module'],
                   operational_keys=sorted(BASE_KEYS | MODULE_KEYS.get(plan['module'], frozenset())))
    freeze(root / 'RESUMED_FROM.json', receipt)
    return receipt
