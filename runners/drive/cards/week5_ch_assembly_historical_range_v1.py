"""Historical-safe successor of the preserved CH1 ordinal-union collector.

Reuses the qualified preboot-exit proof only after actual access denial.
Original collector, scorer, range module and evidence are unchanged.

DESIGN CHECK: LESSONS 3-5, amendment V. Under either scientific outcome a
collection requires every original ordinal exactly once at the original node
and engine/source pins. COMPLETE, PAUSED and FAILED remain distinct. Only
sealed, separately replayed units can contribute. Gaps, overlaps, active units,
changed bytes, unknown/live native owners and unmatched denominators refuse.
Operational prefix audits never emit a population-complete batch manifest.
"""
from pathlib import Path
from datetime import datetime, timezone
import json
import math

from . import week5_ch_queue_backhalf_v1 as queue
from . import week5_ch_queue_range_v1 as ranged
from . import week5_ch_pipeline_checkpoint as ck
from .week5_ch_source import digest, write_json
from runners.stage9.process_identity import is_same_live_process
from . import week5_historical_exit_v1 as historical

SCHEMA = 'CH1-authenticated-ordinal-union-range-v1'
MODULES = {queue.__name__, ranged.__name__}
HISTORICAL_EXIT_PROOFS = {}
METADATA_CAP = 256 * 1024**2


def read(path):
    path = Path(path)
    size = path.stat().st_size
    if size > METADATA_CAP:
        raise ValueError('Assembly metadata exceeds its explicit bound')
    with path.open('rb') as stream:
        content = stream.read(size + 1)
    if len(content) != size:
        raise ValueError('Assembly metadata size changed during read')
    return json.loads(content)


def spec(path):
    return dict(path=str(Path(path).resolve()), sha256=digest(path))


def _inside(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError('Evidence path escaped its attempt root')
    return path


def _file_inventory(root, check):
    answer = {}
    for path in sorted(root.rglob('*')):
        check()
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            _inside(root.resolve(), rel)
            answer[rel] = ck.file_digest(path, check)
    return answer


def paused_terminal_inventory(inventory):
    """Exact original week5_resume.output_manifest basename exclusions.

    The full post-exit audit still binds every file. Only comparison with the
    historical PAUSED receipt uses the historical runtime's narrower schema.
    """
    return {name: value for name, value in inventory.items()
            if Path(name).name not in {'YIELD_REQUEST.json', 'PROGRESS.json'}
            and not Path(name).name.endswith('.tmp') and '.tmp.' not in Path(name).name}


def _native(record, terminal_path, identity_path):
    native = record.get('native', record)
    identity_path, terminal_path = Path(identity_path).resolve(), Path(terminal_path).resolve()
    if (not isinstance(native, dict) or set(native) != {'pid', 'created_ticks', 'executable'} or
            type(native['pid']) is not int or type(native['created_ticks']) is not int or
            not native['executable']):
        raise ValueError(f'Complete actual native identity required: {identity_path}')
    try:
        live = is_same_live_process(native)
    except OSError as exc:
        if exc.errno != 5:
            raise OSError(exc.errno, f'Native inspection refused for {identity_path}: {exc}') from exc
        # The separately qualified helper requires both creation and the exact
        # retained terminal to precede independently agreeing boot times.
        # A current inaccessible PID holder is never assigned an identity.
        try:
            terminal_at = read(terminal_path)['at']
            os_boot, kernel_boot = historical.boot_pair()
            proof = historical.preboot(native, terminal_at, os_boot, kernel_boot,
                                       datetime.now(timezone.utc).timestamp())
        except (OSError, ValueError, KeyError) as rejected:
            raise ValueError(f'Historical exit remains unknown for {identity_path}: {rejected}') from rejected
        HISTORICAL_EXIT_PROOFS[str(identity_path)] = dict(proof=proof,
            identity_file=spec(identity_path), terminal=spec(terminal_path))
        live = False
    if live:
        raise ValueError(f'Evidence still belongs to a live native process: {identity_path}')
    return native


def validate_historical_proofs(proofs, root, terminal_path):
    if not isinstance(proofs, dict):
        raise ValueError('Historical proof inventory required')
    for name, entry in proofs.items():
        path = Path(name).resolve()
        if not path.is_relative_to(root) or path == root:
            raise ValueError('Historical identity proof escaped attempt root')
        if not (path.name == 'NATIVE.json' or (path.parent == root and
                (path.name == 'OWNER.json' or path.name.endswith('_NATIVE.json')))):
            raise ValueError('Historical proof does not name native identity evidence')
        record = read(path)
        native = record.get('native', record)
        if entry['identity_file'] != spec(path) or entry['terminal'] != spec(terminal_path):
            raise ValueError('Historical identity or terminal binding changed')
        proof = entry['proof']
        if proof['native'] != native or proof['terminal_at'] != read(terminal_path)['at']:
            raise ValueError('Historical identity proof attributed to wrong record')
        expected = historical.preboot(native, proof['terminal_at'], proof['os_boot_ticks'],
            proof['kernel_boot_epoch'], datetime.fromisoformat(proof['inspected_at']).timestamp())
        if expected != proof:
            raise ValueError('Historical identity proof is not independently valid')


def capture_post_exit_audit(root, destination, check=lambda: None):
    """New immutable evidence inventory; never edits an original terminal."""
    root, destination = Path(root).resolve(), Path(destination).resolve()
    if destination.is_relative_to(root):
        raise ValueError('Post-exit audit must be outside preserved attempt evidence')
    HISTORICAL_EXIT_PROOFS.clear()
    names = [s for s in ('COMPLETE', 'PAUSED', 'FAILED') if (root / (s + '.json')).exists()]
    if len(names) != 1 or (root / 'MONITOR_FAILED.json').exists():
        raise ValueError('Unambiguous original terminal required')
    terminal = root / (names[0] + '.json')
    value = read(terminal)
    if value.get('status') != names[0] or value.get('accounting_reconciliation_required'):
        raise ValueError('Original terminal/cost requires owner reconciliation')
    native_paths = sorted({root / 'OWNER.json', *root.glob('*_NATIVE.json')})
    for path in native_paths:
        check()
        _native(read(path), terminal, path)
    for path in (root / 'output').glob('units/*/native/*/NATIVE.json'):
        check()
        _native(read(path), terminal, path)
    result = dict(schema=SCHEMA, status='POST_EXIT_EVIDENCE_AUDIT',
                  observed_at=datetime.now(timezone.utc).isoformat(),
                  terminal=spec(terminal), plan=spec(root / 'PLAN.json'),
                  original_disposition=names[0], attempt_cpu_seconds=value['cpu_seconds'],
                  native_files={p.name: digest(p) for p in native_paths},
                  job_usage_files={p.name: digest(p) for p in root.glob('*_JOB_USAGE.json')},
                  checkpoint_outputs=_file_inventory(root / 'output', check),
                  historical_exit_proofs=dict(HISTORICAL_EXIT_PROOFS),
                  scientific_admission=False, original_disposition_unchanged=True)
    write_json(destination, result)
    return result


def _attempt(item, inputs, total, nodes, constructed, check):
    if set(item) != {'terminal', 'plan', 'audit', 'begin', 'end'}:
        raise ValueError('Exact terminal/plan/audit and selected ordinal bounds required')
    begin, end = item['begin'], item['end']
    if type(begin) is not int or type(end) is not int or not 0 <= begin < end <= total:
        raise ValueError('Invalid selected interval')
    terminal_path = ck.checked(item['terminal'], check).resolve()
    root = terminal_path.parent
    plan_path = ck.checked(item['plan'], check).resolve()
    if plan_path != root / 'PLAN.json':
        raise ValueError('Plan belongs to another attempt')
    terminal = read(terminal_path)
    status = terminal.get('status')
    if status not in ('COMPLETE', 'PAUSED', 'FAILED') or terminal_path.name != status + '.json':
        raise ValueError('Unrecognized terminal identity')
    if sum((root / (s + '.json')).exists() for s in ('COMPLETE', 'PAUSED', 'FAILED')) != 1:
        raise ValueError('Conflicting terminal dispositions')
    if (root / 'MONITOR_FAILED.json').exists():
        raise ValueError('Unreconciled monitor failure requires explicit owner repair')
    cost = terminal.get('cpu_seconds')
    if type(cost) not in (float, int) or not math.isfinite(cost) or cost < 0:
        raise ValueError('Missing retained attempt cost')
    if terminal.get('accounting_reconciliation_required'):
        raise ValueError('Unreconciled failed cost cannot disappear from assembly')
    plan = read(plan_path)
    config = plan['config']
    if (plan['module'] not in MODULES or plan['inputs']['positions'] != inputs['positions'] or
            plan['inputs']['engine'] != inputs['engine'] or
            config['expected_positions'] != total or config.get('nodes', 1000000) != nodes):
        raise ValueError('Attempt has different source, engine, denominator or nodes')
    if bool(config.get('constructed_fixture')) != constructed:
        raise ValueError('Constructed and production evidence cannot share an assembly')
    # Every disposition needs a separately pinned post-exit inventory. Failure
    # receipts lacking a checkpoint map cannot manufacture one retrospectively.
    # The new audit records current preserved bytes as a new evidence object.
    audit = read(ck.checked(item['audit'], check))
    if (audit.get('schema') != SCHEMA or audit.get('status') != 'POST_EXIT_EVIDENCE_AUDIT' or
            audit.get('terminal') != item['terminal'] or audit.get('plan') != item['plan'] or
            audit.get('original_disposition') != status or
            audit.get('attempt_cpu_seconds') != cost):
        raise ValueError('Post-exit evidence audit has wrong attribution or cost')
    validate_historical_proofs(audit.get('historical_exit_proofs'), root, terminal_path)
    owner_path = root / 'OWNER.json'
    owner = read(owner_path)
    if owner.get('plan_sha256') != item['plan']['sha256']:
        raise ValueError('Owner does not bind the original plan')
    identities = []
    native_paths = sorted({owner_path, *root.glob('*_NATIVE.json')})
    if not (root / 'EXECUTE_NATIVE.json').exists():
        raise ValueError('Original native execution identity absent')
    for path in native_paths:
        check()
        if audit['native_files'].get(path.name) != digest(path):
            raise ValueError('Native owner evidence omitted or changed')
        identities.append(_native(read(path), terminal_path, path))
    if set(audit['native_files']) != {p.name for p in native_paths}:
        raise ValueError('Native owner evidence inventory differs')
    usage_paths = sorted(root.glob('*_JOB_USAGE.json'))
    operations = {p.name[:-len('_NATIVE.json')] for p in native_paths if p.name.endswith('_NATIVE.json')}
    required_usage = {operation + '_JOB_USAGE.json' for operation in operations}
    if not required_usage <= {p.name for p in usage_paths}:
        raise ValueError('An outer native operation lacks its Job usage')
    if status == 'COMPLETE' and 'VERIFY' not in operations:
        raise ValueError('COMPLETE lacks its separate native verification identity')
    if not usage_paths or audit['job_usage_files'] != {p.name: digest(p) for p in usage_paths}:
        raise ValueError('Original outer Job accounting omitted or changed')
    for path in usage_paths:
        usage = read(path)
        if (not usage.get('includes_all_descendants_and_exited_processes') or
                type(usage.get('cpu_seconds')) not in (float, int) or
                not math.isfinite(usage['cpu_seconds']) or usage['cpu_seconds'] < 0):
            raise ValueError('Outer Job cost is not fully retained')
    inventory = _file_inventory(root / 'output', check)
    if inventory != audit['checkpoint_outputs']:
        raise ValueError('Post-exit output inventory differs')
    if status == 'PAUSED' and terminal.get('checkpoint_outputs') != paused_terminal_inventory(inventory):
        raise ValueError('Original PAUSED inventory differs')
    if status == 'COMPLETE':
        if not terminal.get('fresh_process_verified'):
            raise ValueError('COMPLETE lacks original independent verification')
        for name, expected in terminal['outputs'].items():
            check()
            if ck.file_digest(_inside(root, name), check) != expected:
                raise ValueError('Original COMPLETE output hash differs')
        expected_output = {k[7:]: v for k, v in terminal['outputs'].items() if k.startswith('output/')}
        # The original runtime deliberately omitted these telemetry names from
        # COMPLETE. The new post-exit audit binds them too, without pretending
        # their old terminal contained hashes that it never recorded.
        omitted = set(inventory) - set(expected_output)
        excluded_names = {'PROGRESS.json', 'BUDGET_PROGRESS.json', 'MONITOR_READY.json', 'stdout.log', 'stderr.log'}
        if (not expected_output.items() <= inventory.items() or
                any(Path(name).name not in excluded_names and not name.endswith('.tmp') for name in omitted)):
            raise ValueError('COMPLETE omitted a required scientific or native evidence output')
    state = read(root / 'output/QUEUE_STATE.json')
    binding = state['binding']
    expected_config = {k: v for k, v in config.items() if k != 'max_new_draws'}
    if binding['inputs'] != plan['inputs'] or binding['config'] != expected_config:
        raise ValueError('Checkpoint differs from original input/configuration')
    expected_adapter = digest(queue.__file__ if plan['module'] == queue.__name__ else ranged.__file__)
    if (binding['implementation'].get('adapter') != expected_adapter or
            binding['implementation'].get('original_engine') != digest(queue.scorer.__file__) or
            binding['implementation'].get('bounded_engine') != digest(queue.bounded.__file__) or
            binding['implementation'].get('checkpoint_helper') != digest(queue.ck.__file__)):
        raise ValueError('Unreviewed queue/scorer/checkpoint implementation')
    if type(state['next_offset']) is not int or not config.get('offset', 0) <= begin < end <= state['next_offset'] <= total:
        raise ValueError('Selected prefix is not inside the sealed cursor')
    if plan['module'] == ranged.__name__:
        from . import week5_ch_manifest_range_v1 as partition_contract
        manifest = partition_contract.validate(plan['inputs']['range_manifest'], plan['inputs'], config)
        ranges = partition_contract.validate_partition(manifest)
        matching = [r for r in ranges if r['id'] == config['shard_id']]
        if (len(matching) != 1 or matching[0]['begin'] != config['offset'] or
                matching[0]['end'] != config['range_end'] or state['next_offset'] > config['range_end'] or
                manifest['positions'] != inputs['positions'] or manifest['engine'] != inputs['engine'] or
                manifest['nodes'] != nodes or manifest['expected_positions'] != total):
            raise ValueError('Range successor differs from its frozen partition')
        expected_status = 'CONSTRUCTED_ONLY' if config.get('constructed_fixture') else 'FROZEN_FOR_OWNER_ADMISSION'
        if manifest.get('status') != expected_status:
            raise ValueError('Range admission manifest has the wrong evidence scope')
    source = queue.scorer.iter_positions(inputs['positions']['path'])
    cursor = config.get('offset', 0)
    for _ in range(cursor):
        check()
        if next(source, None) is None:
            raise ValueError('Attempt offset outside original roster')
    selected = []
    selected_cursor = begin
    for item_unit in state['units']:
        check()
        unit = _inside(root / 'output', item_unit['path'])
        if digest(unit / 'UNIT_SEAL.json') != item_unit['seal_sha256']:
            raise ValueError('Unit seal differs from saved queue cursor')
        seal = queue.check_unit(unit, check)
        unit_plan = read(unit / 'UNIT.json')
        if (seal['begin'] != cursor or not cursor < seal['end'] <= state['next_offset'] or
                unit_plan['source_roster'] != inputs['positions'] or
                unit_plan['inputs']['engine'] != inputs['engine'] or
                unit_plan['config']['nodes'] != nodes or unit_plan['pins'] != queue.worker_pins()):
            raise ValueError('Sealed unit has wrong ordinal/source/node/native-code binding')
        local = queue.scorer.iter_positions(unit / 'PRIVATE_POSITIONS.jsonl.gz')
        count = 0
        for row in local:
            check()
            if count >= seal['positions']:
                raise ValueError('Sealed source slice exceeds its ordinal interval')
            if row != next(source, None):
                raise ValueError('Sealed row differs from its original full-roster ordinal')
            count += 1
        if count != seal['positions']:
            raise ValueError('Sealed source slice is truncated')
        for path in (unit / 'native').glob('*/NATIVE.json'):
            _native(read(path), terminal_path, path)
        overlaps = seal['begin'] < end and seal['end'] > begin
        if overlaps:
            if seal['begin'] != selected_cursor or seal['end'] > end:
                raise ValueError('Selection must consist of whole consecutive sealed units')
            selected.append(dict(begin=seal['begin'], end=seal['end'],
                batch=dict(path=str(unit / 'output/PRIVATE_SCORES'),
                           verify=spec(unit / 'output/VERIFY.json'), report=spec(unit / 'output/BATCH.json'),
                           score_bindings=spec(unit / 'SCORE_BINDINGS.json'), queue_unit_seal=spec(unit / 'UNIT_SEAL.json'),
                           source_terminal=item['terminal'], source_disposition=status,
                           prefix_evidence_audit=item['audit'])))
            selected_cursor = seal['end']
        cursor = seal['end']
    if cursor != state['next_offset'] or selected_cursor != end:
        raise ValueError('Sealed queue cursor or selected prefix has a gap')
    return dict(begin=begin, end=end, selected=selected, original_disposition=status,
                terminal=item['terminal'], audit=item['audit'], attempt_cpu_seconds=cost,
                excluded_active_unit=state['active'] is not None, native_owners=identities)


def calculate(inputs, config, check=lambda: None):
    if set(inputs) != {'positions', 'engine', 'attempts'}:
        raise ValueError('Exact original roster, engine and attempt manifest required')
    if set(config) - {'expected_positions', 'nodes', 'constructed_fixture', 'operational_prefix_only'}:
        raise ValueError('Unknown assembly setting')
    total = config.get('expected_positions')
    nodes = config.get('nodes', 1000000)
    if type(total) is not int or not 1 <= total <= 400000 or nodes not in (300000, 1000000, 3000000):
        raise ValueError('Original complete denominator and registered node count required')
    for value in inputs.values():
        ck.checked(value, check)
    roster_count = 0
    for _ in queue.scorer.iter_positions(inputs['positions']['path']):
        check()
        roster_count += 1
        if roster_count > total:
            raise ValueError('Original roster exceeds declared denominator')
    if roster_count != total:
        raise ValueError('Original roster shorter than declared denominator')
    manifest = read(inputs['attempts']['path'])
    if manifest.get('schema') != SCHEMA or not manifest.get('attempts'):
        raise ValueError('Frozen nonempty attempt evidence list required')
    attempts = [_attempt(item, inputs, total, nodes, bool(config.get('constructed_fixture')), check)
                for item in manifest['attempts']]
    intervals = sorted(attempts, key=lambda a: (a['begin'], a['end']))
    cursor = 0
    complete = True
    batches = []
    for attempt in intervals:
        if attempt['begin'] < cursor:
            raise ValueError('Duplicate or overlapping accepted ordinal interval')
        if attempt['begin'] != cursor:
            complete = False
        cursor = attempt['end']
        batches.extend(unit['batch'] for unit in attempt['selected'])
    complete = complete and cursor == total
    # Costs are not summed across copied unit seals; each unique original attempt
    # stays charged once, with parent accounting still the actual authority.
    costs = {}
    for attempt in attempts:
        key = attempt['terminal']['path']
        value = dict(terminal=attempt['terminal'], cpu_seconds=attempt['attempt_cpu_seconds'],
                     original_disposition=attempt['original_disposition'])
        if key in costs and costs[key] != value:
            raise ValueError('Same attempt has conflicting cost evidence')
        costs[key] = value
    audit = dict(schema=SCHEMA, population_complete=False, operational_only=True,
                 original_positions=total, covered_positions=sum(a['end']-a['begin'] for a in attempts),
                 exact_complete_ordinal_union=complete,
                 intervals=[{k: a[k] for k in ('begin', 'end', 'original_disposition', 'terminal', 'audit', 'excluded_active_unit')}
                            for a in intervals],
                 selected_attempt_costs=list(costs.values()),
                 all_other_historical_attempt_costs_remain_in_campaign_ledger=True)
    if config.get('operational_prefix_only'):
        return audit, None
    if not complete:
        raise ValueError('Full original ordinal population has not completed; operational audit only')
    report = dict(schema=SCHEMA, batches=batches, population_complete=True,
                  positions=total, roster_sha256=inputs['positions']['sha256'],
                  engine=inputs['engine'], node_limit=nodes,
                  source='Exact original ordinal union of independently replayed sealed units; original terminal dispositions retained')
    return audit, report


def _execute(output, inputs, config):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    audit, report = calculate(inputs, config, lambda: ck.require(output))
    write_json(output / 'PREFIX_AUDIT.json', audit)
    if report is not None:
        write_json(output / 'BATCHES.json', report)
    return dict(status='complete', operational_only=report is None,
                population_complete=report is not None, original_positions=config['expected_positions'])


def _verify(output, inputs, config):
    output = Path(output)
    audit, report = calculate(inputs, config, lambda: ck.require(output))
    if read(output / 'PREFIX_AUDIT.json') != audit:
        raise ValueError('Fresh prefix audit differs')
    if report is None:
        if (output / 'BATCHES.json').exists():
            raise ValueError('Operational prefix audit cannot emit collection admission')
    elif read(output / 'BATCHES.json') != report:
        raise ValueError('Fresh exact-union batch reconstruction differs')
    return dict(verified=True, full_evidence_reauthentication=True,
                population_complete=report is not None, operational_only=report is None)


def execute(output, inputs, config):
    return ck.guarded(_execute, output, inputs, config)


def verify(output, inputs, config):
    return ck.guarded(_verify, output, inputs, config)
