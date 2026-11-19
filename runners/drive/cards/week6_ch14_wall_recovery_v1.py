"""Authenticate a CH14 hard-wall checkpoint before the unchanged V3 handler.

DESIGN CHECK: LESSONS 3-5. An intact, stopped, execute-only wall failure
recovers byte-identical saved draws under the same scientific binding. A changed
source, model, receipt, native owner or output refuses before a source fit.
Null and alternative worlds take the same transport route; neither partial
estimates nor their signs select work. Fresh complete independent replay remains
mandatory. This does not amend the ordinary PAUSED-only resume adapter.
"""
from pathlib import Path
import shutil
import stat
from .batch_runtime import read, freeze, filehash, check_files
from .week5_resume import output_manifest
from .week6_policy_v1 import ROOT
from . import week6_ch_riders_v3 as base
from runners.stage9.process_identity import is_same_live_process

ORIGINAL = 'runners.drive.cards.week6_ch_riders_v3'
RECEIPTS = frozenset({'PLAN.json', 'FAILED.json', 'OWNER.json',
                      'EXECUTE_NATIVE.json', 'EXECUTE_JOB_USAGE.json'})
OUTPUTS = frozenset({'PILOT.json', 'RIDER_CHECKPOINT.json'})
ERROR = "TimeoutError('Combined execution/replay safety wall or drain ceiling')"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def regular(path):
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and not path.is_symlink() and
            not (getattr(info, 'st_file_attributes', 0) & 0x400),
            'Recovery file must be a regular non-reparse file')


def authenticate(output, inputs, config):
    output = Path(output).resolve()
    root = output.parent
    root.relative_to(Path(ROOT).resolve())
    require(output.name == 'output', 'Declared output directory required')
    manifest_input = inputs['wall_recovery']
    manifest_path = Path(manifest_input['path'])
    regular(manifest_path)
    require(filehash(manifest_path) == manifest_input['sha256'], 'Changed recovery manifest')
    spec = read(manifest_path)
    require(spec.get('version') == 1 and spec.get('kind') == 'CH14_EXECUTE_WALL_RECOVERY',
            'Unknown recovery contract')
    old = Path(spec['root']).resolve()
    old.relative_to(Path(ROOT).resolve())
    require(old != root, 'Recovery requires a new attempt')
    require(set(spec['receipts']) == RECEIPTS, 'Incomplete predecessor receipt set')
    for name, digest in spec['receipts'].items():
        regular(old / name)
        require(filehash(old / name) == digest, 'Changed predecessor receipt: ' + name)
    require(not any((old / name).exists() for name in
                    ('COMPLETE.json', 'PAUSED.json', 'VERIFY_NATIVE.json', 'VERIFIED.json')),
            'Ambiguous or replay-stage predecessor')
    prior = read(old / 'PLAN.json')
    failed = read(old / 'FAILED.json')
    usage = read(old / 'EXECUTE_JOB_USAGE.json')
    require(failed.get('status') == 'FAILED' and failed.get('failure_class') == 'cost'
            and failed.get('error') == ERROR
            and failed.get('accounting_reconciliation_required') is False
            and failed['wall_seconds'] >= prior['max_wall_seconds']
            and 0 <= failed['cpu_seconds'] < prior['max_cpu_seconds']
            and usage.get('includes_all_descendants_and_exited_processes') is True
            and usage['cpu_seconds'] == failed['cpu_seconds'], 'Not an accounted execute wall failure')
    owner = read(old / 'OWNER.json')
    require(owner['plan_sha256'] == spec['receipts']['PLAN.json'], 'Owner plan binding mismatch')
    for record in (owner, read(old / 'EXECUTE_NATIVE.json')):
        require(not is_same_live_process(record['native']), 'Predecessor native process still live')
    original_inputs = {k: v for k, v in inputs.items() if k != 'wall_recovery'}
    current = read(root / 'PLAN.json')
    require(prior['module'] == ORIGINAL and current['module'] == __name__, 'Changed handler contract')
    require(current['inputs'] == inputs and current['config'] == config, 'Invocation plan mismatch')
    require(original_inputs == prior['inputs'], 'Changed scientific inputs')
    semantic = lambda c: {k: v for k, v in c.items() if k != 'max_new_draws'}
    require(config.get('card') == 'CH14' and semantic(config) == semantic(prior['config']),
            'Changed scientific configuration')
    for key in ('campaign', 'family', 'budget_key'):
        require(current[key] == prior[key], 'Changed scientific accounting: ' + key)
    require(prior['campaign'] == 'S15-WEEK6' and prior['family'] == 'CH'
            and prior['budget_key'] == 'CH14', 'Wrong original study')
    require(all(current['pins'].get(p) == d for p, d in prior['pins'].items()), 'Dropped predecessor pin')
    require(current['pins'].get(str(manifest_path)) == manifest_input['sha256'], 'Unpinned recovery manifest')
    check_files(prior['pins'])
    expected = spec['output_manifest']
    require(set(expected) == OUTPUTS, 'Unexpected predecessor output set')
    for name in expected:
        regular(old / 'output' / name)
    require(output_manifest(old / 'output') == expected, 'Changed predecessor outputs')
    saved = read(old / 'output/RIDER_CHECKPOINT.json')
    require(saved['binding'] == base.identity(original_inputs, config), 'Changed checkpoint binding')
    require(isinstance(spec['checkpoint_draws'], int) and not isinstance(spec['checkpoint_draws'], bool)
            and len(saved['draws']) == spec['checkpoint_draws']
            and 0 < len(saved['draws']) < config.get('draws', 2000), 'Invalid saved draw count')
    origin = dict(adapter=__name__, recovery_sha256=manifest_input['sha256'],
                  predecessor_plan_sha256=spec['receipts']['PLAN.json'],
                  failed_sha256=spec['receipts']['FAILED.json'],
                  recovered_draws=spec['checkpoint_draws'])
    return original_inputs, spec, current, origin


def install(output, spec, current, origin):
    output = Path(output)
    root = output.parent
    marker = root / 'RESUMED_FROM.json'
    origin_path = output / 'RECOVERY_ORIGIN.json'
    if current.get('resume'):
        # The unchanged PAUSED-only adapter already copied and checked this
        # later continuation. Never reset it to the older wall checkpoint.
        receipt = read(marker)
        resume = current['resume']
        require(receipt['adapter'] == 'week6_resume_v1'
                and Path(receipt['predecessor']).resolve() == Path(resume['root']).resolve()
                and receipt['plan_sha256'] == resume['plan_sha256']
                and receipt['paused_sha256'] == resume['paused_sha256'], 'Unproved paused continuation')
        base.ck.copied(origin_path, output)
        require(read(origin_path) == origin, 'Changed recovery origin')
        return
    require(not marker.exists() and (not output.exists() or not any(output.iterdir())),
            'Fresh recovery target must be empty')
    output.mkdir(parents=True, exist_ok=True)
    old = Path(spec['root'])
    for name, digest in spec['output_manifest'].items():
        destination = output / name
        shutil.copyfile(old / 'output' / name, destination)
        require(filehash(destination) == digest, 'Recovery copy mismatch')
    require(output_manifest(output) == spec['output_manifest'], 'Incomplete recovery copy')
    freeze(origin_path, origin)
    freeze(marker, dict(adapter=__name__, predecessor=str(old),
                        plan_sha256=spec['receipts']['PLAN.json'],
                        failed_sha256=spec['receipts']['FAILED.json'],
                        copied=spec['output_manifest'], recovered_draws=spec['checkpoint_draws']))


def execute(output, inputs, config):
    original_inputs, spec, current, origin = authenticate(output, inputs, config)
    install(output, spec, current, origin)
    return base.execute(output, original_inputs, config)


def verify(output, inputs, config):
    original_inputs, _, _, origin = authenticate(output, inputs, config)
    require(read(Path(output) / 'RECOVERY_ORIGIN.json') == origin, 'Changed recovery origin')
    return base.verify(output, original_inputs, config)
