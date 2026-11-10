"""Read-only LA native receipt validation; no launch, copy or model execution.

Week 5 records exact FILETIME ticks. Guard receipts use psutil epoch floats;
both are matched by PID, executable and creation time, never PID alone.
"""
from pathlib import Path
from types import FunctionType, SimpleNamespace
import math
from . import week5_la_admission_prepare as legacy
from .week5_resume import output_manifest
from runners.stage9.process_identity import is_same_live_process

require, read, sha, path = legacy.require, legacy.read, legacy.sha, legacy.path


def native(value):
    require(set(value) == {'pid', 'created_ticks', 'executable'} and
            type(value['pid']) is int and value['pid'] > 0 and
            type(value['created_ticks']) is int and value['created_ticks'] > 116444736000000000 and
            isinstance(value['executable'], str) and value['executable'], 'Exact Week 5 native FILETIME identity required')
    return value


def key(value):
    value = native(value)
    return value['pid'], value['created_ticks'], str(Path(value['executable'])).casefold()


def guard_matches(value, actual):
    actual = native(actual)
    stamp = value.get('creation_time')
    # Ten microseconds covers conversion from exact 100 ns FILETIME to a
    # floating Unix epoch. This is identity representation, not score tolerance.
    return (type(value.get('pid')) is int and value['pid'] == actual['pid'] and
            str(Path(value.get('executable', ''))).casefold() == str(Path(actual['executable'])).casefold() and
            type(stamp) in (int, float) and math.isfinite(stamp) and
            abs(stamp - (actual['created_ticks'] - 116444736000000000) / 10000000) <= 1e-5 and
            isinstance(value.get('command_line'), list) and bool(value['command_line']))


def exited(root, plan_sha):
    owner = read(Path(root) / 'OWNER.json')
    require(owner.get('plan_sha256') == plan_sha, 'Native owner is bound to another plan')
    require(not is_same_live_process(native(owner['native'])), 'Actual native owner remains live')


def corrected_legacy():
    namespace = dict(legacy.__dict__)
    for name, value in legacy.__dict__.items():
        if isinstance(value, FunctionType) and value.__module__ == legacy.__name__:
            clone = FunctionType(value.__code__, namespace, value.__name__, value.__defaults__, value.__closure__)
            clone.__kwdefaults__ = value.__kwdefaults__
            namespace[name] = clone
    namespace['exited'] = exited
    return SimpleNamespace(**namespace)


def completed(value, family, module):
    return corrected_legacy().completed(value, family, module)


def phase_records(root, operations):
    result = []
    for phase in operations:
        value = native(read(root / (phase.upper() + '_NATIVE.json'))['native'])
        require(not is_same_live_process(value), 'Native phase remains live')
        usage = read(root / (phase.upper() + '_JOB_USAGE.json'))
        require(usage.get('exit_code') == 0 and usage.get('includes_all_descendants_and_exited_processes') is True,
                'Successful native descendant accounting is absent')
        result.append(dict(root=str(root), phase=phase, native=value, cpu_seconds=legacy.positive(usage['cpu_seconds'])))
    return result


def paused(value, family, module):
    root = path(value, legacy.BASE)
    require(not any((root / n).exists() for n in ('COMPLETE.json', 'FAILED.json', 'MONITOR_FAILED.json')),
            'Ambiguous or failed predecessor is not a valid pause')
    plan, receipt = read(root / 'PLAN.json'), read(root / 'PAUSED.json')
    require(plan.get('campaign') == 'S15-WEEK5' and plan.get('family') == family and plan.get('module') == module,
            'Different native predecessor producer')
    require(receipt.get('status') == 'PAUSED' and receipt.get('checkpoint_validation_required') is True and
            receipt.get('paused_operation') in ('execute', 'verify'), 'Explicit paused native phase required')
    legacy.pins(plan['pins'])
    exited(root, sha(root / 'PLAN.json'))
    expected = receipt.get('checkpoint_outputs')
    require(isinstance(expected, dict) and bool(expected) and output_manifest(root / 'output') == expected,
            'Complete exact paused output manifest required')
    phases = ['execute'] if receipt['paused_operation'] == 'execute' else ['execute', 'verify']
    records = phase_records(root, phases)
    require(legacy.positive(receipt['cpu_seconds']) + 1e-9 >= sum(r['cpu_seconds'] for r in records),
            'Paused terminal undercounts native phases')
    return root, plan, receipt, records


def linked_copy(prior, successor, old_plan, new_plan):
    resume = new_plan.get('resume')
    require(isinstance(resume, dict) and path(resume['root']) == prior and
            resume.get('plan_sha256') == sha(prior / 'PLAN.json') and
            resume.get('paused_sha256') == sha(prior / 'PAUSED.json'), 'Different native resume predecessor')
    for k in ('module', 'inputs', 'config', 'family', 'campaign'):
        require(old_plan[k] == new_plan[k], 'Changed paired continuation contract: ' + k)
    before, after = legacy.pins(old_plan['pins']), legacy.pins(new_plan['pins'])
    require(all(after.get(k) == v for k, v in before.items()), 'Continuation dropped predecessor pins')
    copy = read(successor / 'RESUMED_FROM.json')
    expected = read(prior / 'PAUSED.json')['checkpoint_outputs']
    require(copy.get('adapter') == 'week5_resume_v2' and copy.get('module') == new_plan['module'] and
            path(copy['predecessor']) == prior and copy.get('plan_sha256') == resume['plan_sha256'] and
            copy.get('paused_sha256') == resume['paused_sha256'] and copy.get('copied') == expected,
            'Actual authenticated native copy receipt required')
    for name, expected_hash in expected.items():
        p = (successor / 'output' / name).resolve()
        p.relative_to(successor / 'output')
        require(sha(p) == expected_hash, 'Continuation changed retained immutable checkpoint bytes')


def chain(value, family, module):
    root, plan, done = completed(value, family, module)
    items = [dict(root=root, plan=plan, terminal=done, records=phase_records(root, ['execute', 'verify']))]
    seen = {root}
    current, current_plan = root, plan
    while current_plan.get('resume'):
        predecessor = path(current_plan['resume']['root'], legacy.BASE)
        require(predecessor not in seen and len(seen) < 10000, 'Cyclic or unbounded native continuation chain')
        seen.add(predecessor)
        prior, prior_plan, receipt, records = paused(predecessor, family, module)
        linked_copy(prior, current, prior_plan, current_plan)
        items.append(dict(root=prior, plan=prior_plan, terminal=receipt, records=records))
        current, current_plan = prior, prior_plan
    items.reverse()
    identities = [key(read(item['root'] / 'OWNER.json')['native']) for item in items]
    require(len(set(identities)) == len(identities), 'Native continuation reuses an owner identity')
    return items
