"""Explicit native guarded-v5 collection; original numerical reduction unchanged."""
from pathlib import Path
from types import FunctionType
from . import week5_la_pipeline_v4 as original
from . import week5_la_pipeline_v5 as paired
from . import week5_la_scoring_guard_v1 as guarded
from . import week5_la_native_evidence as native
from .week5_at_selection import selected_reader
from .week5_at_scoring import digest
from .timing_census import read, filehash
from .timing_p6 import gzread

CORE = dict(paired.CORE, **{
    'week5_la_pipeline_v5.py': '74d54713f43c08fdd32461a192ff5081a5d08a7f97a3e8e2e300d545e3a97a90',
    'week5_la_scoring_guard_v1.py': 'b080143f604c0a8491fff98006f7a42c25e6093718f542a2024009a0e3be88b6',
    'week5_at_precision_guard.py': guarded.GUARD_SHA256,
})


def required_pins(plan):
    pins = native.legacy.pins(plan['pins'])
    for name, sha in CORE.items():
        path = Path(__file__).parent / name
        native.require(filehash(path) == sha and pins.get(str(path.resolve()).casefold()) == sha,
                       'Unreviewed or unpinned exact guarded numerical producer')
    for name, value in plan['inputs'].items():
        path = Path(value) / 'COMPLETE.json' if name.endswith('_root') else Path(value)
        native.require(pins.get(str(path.resolve()).casefold()) == filehash(path), 'Unpinned exact paired input')
    native.require(plan.get('owner_reviewed') is True and plan.get('fixture_passed') is True and
                   bool(plan.get('reviewed_design_commit')) and plan.get('numerical_threads') == 2 and
                   plan.get('gpu') is False and plan.get('paid') is False and plan.get('ollama') is False,
                   'Native owner/design/CPU qualification declarations required')


def checkpoint_proof(root, plan):
    """Full completed act and independent replay seals, without model calls."""
    paired.validate(plan['inputs'], plan['config'])
    inputs = plan['inputs']
    binding = digest(dict(inputs={k: filehash(Path(v) / 'COMPLETE.json') if k.endswith('_root') else filehash(v)
                                  for k, v in inputs.items()}, config=plan['config'], numerical_spec=paired.NUMERICAL_SPEC))
    reader = selected_reader(inputs['selection_root'], read(inputs['causal_manifest']))
    output = root / 'output'
    expected = dict(binding=binding, implementation_sha256=CORE['week5_la_pipeline_v5.py'], core=paired.CORE,
                    numerical_spec=paired.NUMERICAL_SPEC, selected_reader_binding=reader,
                    masked_precision='float32_original', collector_admission=False)
    native.require(read(output / 'CHECKPOINT_PRODUCER.json') == expected, 'Paired checkpoint provenance differs')
    rows = gzread(inputs['rows'])
    native.require(rows and len({r['id'] for r in rows}) == len(rows), 'Paired source population missing or duplicated')
    native.require({p.name for p in (output / 'verified_acts').glob('*.json')} ==
                   {f'act-{i:03d}{suffix}' for i in range(len(rows)) for suffix in ('.json', '.seal.json')},
                   'Every original act must have exactly one complete independent replay seal')
    evidence = {}
    for i, row in enumerate(rows):
        value = paired.act_value(output, i, row, binding)
        native.require(value is not None, 'Completed paired act absent')
        path = output / 'verified_acts' / f'act-{i:03d}.json'
        checked = paired.sealed(path, paired.replay_binding(output, i, row, binding))
        native.require(checked == paired.replay_evidence(output, i, value), 'Complete paired replay proof differs')
        evidence[path.relative_to(root).as_posix()] = filehash(path)
    return evidence


def guard_proof(root, done, records):
    """Match sealed monitor/load receipts to actual native phase identities."""
    outputs = done['outputs']
    evidence, seen_phases = {}, set()
    current_records = [r for r in records if Path(r['root']).resolve() == root.resolve()]
    native.require({r['phase'] for r in current_records} == {'execute', 'verify'}, 'Current complete native phases absent')
    matched_guards, matched_loads, cpu_totals = {}, {}, {}
    for name, sha in sorted(outputs.items()):
        p = Path(name)
        if not p.parts or p.parts[0] != 'output':
            continue
        is_guard = 'guard_invocations' in p.parts and p.name.startswith('GUARD_')
        is_load = p.parent.as_posix() == 'output/load_admissions'
        if not (is_guard or is_load):
            continue
        path = root / name
        native.require(filehash(path) == sha, 'Sealed native guard/load receipt changed')
        value = read(path)
        identities = [r for r in records if native.guard_matches(value.get('identity', {}), r['native'])]
        native.require(len(identities) == 1, 'Guard/load receipt has no exact actual native phase owner')
        record = identities[0]
        key = native.key(record['native'])
        native.require(value.get('limits') == guarded.LIMITS, 'Changed native resource guard thresholds')
        if is_guard:
            native.require(value.get('phase') == record['phase'] and value.get('status') in ('returned', 'refused_before_model_load'),
                           'Guard status or phase differs from actual child')
            if value['status'] == 'returned':
                first = value['initial']
                native.require(first['commit_headroom_bytes'] >= guarded.LIMITS['start_commit_bytes'] and
                               first['ram_available_bytes'] >= guarded.LIMITS['start_ram_bytes'], 'Guard started below original headroom')
                native.require(value.get('peak_working_set_bytes', 0) > 0 and value.get('wall_seconds', 0) > 0,
                               'Actual guard memory/time receipt absent')
                cpu = value['cpu_seconds']
                native.require(type(cpu) in (int, float) and cpu >= 0, 'Invalid guard CPU')
                cpu_totals[key] = cpu_totals.get(key, 0) + cpu
                matched_guards[key] = matched_guards.get(key, 0) + 1
        else:
            native.require(value.get('stage') in ('causal', 'masked') and value.get('action') in ('admit', 'refuse') and
                           value.get('guard_sha256') == guarded.GUARD_SHA256, 'Unknown paired-load admission')
            if value['action'] == 'admit':
                snapshot = value['snapshot']
                native.require(snapshot['commit_headroom_bytes'] >= guarded.LIMITS['start_commit_bytes'] and
                               snapshot['ram_available_bytes'] >= guarded.LIMITS['start_ram_bytes'], 'Paired load admitted below original gate')
                matched_loads.setdefault(key, set()).add(value['stage'])
        evidence[name] = sha
    for record in records:
        key = native.key(record['native'])
        native.require(cpu_totals.get(key, 0) <= record['cpu_seconds'] + 1e-9, 'Guard CPU exceeds actual complete phase accounting')
    for record in current_records:
        key = native.key(record['native'])
        native.require(matched_guards.get(key, 0) >= 1 and matched_loads.get(key) == {'causal', 'masked'},
                       'Actual current execute/verify lacks both native guarded loads')
        seen_phases.add(record['phase'])
    native.require(seen_phases == {'execute', 'verify'}, 'Complete independently guarded paired phases required')
    return evidence


def producer(root, plan):
    if plan.get('module') != guarded.__name__:
        return original.producer(root, plan)
    root = Path(root).resolve()
    items = native.chain(root, 'LA', guarded.__name__)
    native.require(items[-1]['plan'] == plan, 'Collector plan differs from actual native plan')
    for item in items:
        required_pins(item['plan'])
    admission = native.corrected_legacy()
    snapshot = admission.frozen()
    selection = admission.selected(plan['inputs']['selection_root'], snapshot)
    native.require(filehash(plan['inputs']['causal_manifest']) == selection['selected_manifest']['sha256'] and
                   filehash(plan['inputs']['masked_manifest']) == snapshot['masked_model']['manifest']['sha256'],
                   'Real primary selected reader or frozen masked/tokenizer snapshot differs')
    verified = read(root / 'VERIFIED.json')
    native.require(verified.get('complete_paired_mask_reforward') is True and
                   verified.get('immutable_within_act_replay') is True, 'Actual full independent masked replay is absent')
    records = [r for item in items for r in item['records']]
    guards = guard_proof(root, items[-1]['terminal'], records)
    checkpoints = checkpoint_proof(root, plan)
    return dict(module=guarded.__name__, plan_sha256=filehash(root / 'PLAN.json'),
                complete_sha256=filehash(root / 'COMPLETE.json'), core=CORE,
                native_guard_receipts=guards, complete_replay_seals=checkpoints,
                primary_selected_reader=selection,
                all_attempt_native_cpu_seconds=sum(item['terminal']['cpu_seconds'] for item in items),
                native_attempts=[dict(root=str(item['root']), plan_sha256=filehash(item['root'] / 'PLAN.json')) for item in items])


def collect(output, inputs, config, verifying=False):
    if config != {'operation': 'collect'}:
        raise ValueError('Exact original LA collection operation required')
    fn = FunctionType(original.collect.__code__, dict(original.collect.__globals__, producer=producer),
                      original.collect.__name__, original.collect.__defaults__, original.collect.__closure__)
    return fn(output, inputs, config, verifying)


def execute(output, inputs, config):
    return collect(output, inputs, config)


def verify(output, inputs, config):
    return collect(output, inputs, config, True)
