"""Unqualified operation-aware initial-roster pilot over the frozen collector.

No numeric algorithm or source order changes. The actual completed-row quantum
already exists in the collector. This adapter binds its first ceil(N/20) rows
to distinct execute and independent-verify native pauses. This is not five
percent of fitting, score-file work, total work, or CPU time.
"""
from pathlib import Path
import json
import sqlite3

from . import week5_ch_collection_bounded_v1 as collection
from . import week5_ch_pipeline_checkpoint as ck
from .week5_ch_source import digest, write_json
from runners.stage9.process_identity import is_same_live_process


MODULE = 'runners.drive.cards.week5_ch_collection_pilot_v1'
PILOTS = {operation: 'COLLECTION_'+operation.upper()+'_ROSTER_PILOT.json'
          for operation in ('execute', 'verify')}


def boundary(count):
    if type(count) is not int or not 1 <= count <= 400000:
        raise ValueError('Complete frozen position denominator required')
    return (count+19)//20


def contract(inputs, config):
    if 'max_new_draws' in config:
        raise ValueError('Pilot adapter derives the exact phase quantum itself')
    return dict(collector=collection.identity(inputs, config),
                pilot_adapter_sha256=digest(__file__),
                denominator=config['expected_positions'],
                boundary=boundary(config['expected_positions']),
                unit='initial frozen roster rows in original source order',
                requested_fraction=.05, scope='initial_roster_traversal_only')


def read(path):
    return collection.read_json(path)


def context(output, inputs, config):
    """Require the actual counted plan and runtime's whole-copy provenance."""
    output = Path(output).resolve()
    root = output.parent
    plan = read(root/'PLAN.json')
    if (plan.get('module') != MODULE or plan.get('inputs') != inputs or plan.get('config') != config
            or plan.get('campaign') != 'S15-WEEK5' or plan.get('family') != 'CH'
            or plan.get('fixture_passed') is not True or not plan.get('reviewed_design_commit')):
        raise ValueError('Reviewed counted CH pilot plan required')
    owner = read(root/'OWNER.json')
    if owner.get('plan_sha256') != digest(root/'PLAN.json'):
        raise ValueError('Actual native owner plan binding differs')
    copied = root/'RESUMED_FROM.json'
    if 'resume' not in plan:
        if copied.exists():
            raise ValueError('Unrequested copied checkpoint')
    else:
        resume = plan['resume']
        prior = Path(resume['root']).resolve()
        receipt = read(copied)
        if (Path(receipt['predecessor']).resolve() != prior
                or receipt['plan_sha256'] != resume['plan_sha256']
                or receipt['paused_sha256'] != resume['paused_sha256']
                or digest(prior/'PLAN.json') != resume['plan_sha256']
                or digest(prior/'PAUSED.json') != resume['paused_sha256']):
            raise ValueError('Whole-checkpoint native provenance differs')
        paused, previous = read(prior/'PAUSED.json'), read(prior/'PLAN.json')
        if (paused.get('status') != 'PAUSED' or paused.get('checkpoint_validation_required') is not True
                or receipt['copied'] != paused['checkpoint_outputs']
                or any(previous[key] != plan[key] for key in ('module', 'inputs', 'config', 'family', 'campaign'))
                or any((prior/name).exists() for name in ('COMPLETE.json', 'FAILED.json'))):
            raise ValueError('Incomplete or changed native continuation')
        previous_owner = read(prior/'OWNER.json')
        if (previous_owner.get('plan_sha256') != resume['plan_sha256']
                or is_same_live_process(previous_owner['native'])):
            raise ValueError('Predecessor owner not terminal and bound')
    return root, plan


def copied_pilot(output, operation, inputs, config):
    """A copied receipt must also belong to its original terminal native pause."""
    output = Path(output)
    name = PILOTS[operation]
    path = output/name
    if not path.exists():
        return None
    ck.copied(path, output, lambda: ck.require(output))
    receipt = read(path)
    bound = contract(inputs, config)
    if (receipt.get('binding') != bound or receipt.get('operation') != operation
            or receipt.get('completed_roster_rows') != bound['boundary']
            or receipt.get('population_complete') is not False
            or receipt.get('cpu_fraction_claimed') is not False
            or receipt.get('full_collection_fraction_claimed') is not False):
        raise ValueError('Wrong or reinterpreted roster pilot')
    origin = Path(receipt['producer_attempt_root']).resolve()
    # A pilot can be older than the immediate copied predecessor. Follow the
    # immutable resume links instead of trusting an unpinned old PAUSED file.
    cursor = Path(output).resolve().parent
    seen = set()
    while cursor != origin:
        if cursor in seen:
            raise ValueError('Cyclic pilot ancestry')
        seen.add(cursor)
        current = read(cursor/'PLAN.json')
        link = current.get('resume')
        if not link:
            raise ValueError('Pilot origin is not an authenticated ancestor')
        ancestor = Path(link['root']).resolve()
        if (digest(ancestor/'PLAN.json') != link['plan_sha256']
                or digest(ancestor/'PAUSED.json') != link['paused_sha256']):
            raise ValueError('Changed ancestor plan or pause receipt')
        ancestor_plan = read(ancestor/'PLAN.json')
        if (ancestor_plan.get('module') != MODULE or ancestor_plan.get('inputs') != inputs
                or ancestor_plan.get('config') != config):
            raise ValueError('Changed ancestor collection scope')
        cursor = ancestor
    plan_path = origin/'PLAN.json'
    paused = read(origin/'PAUSED.json')
    plan = read(plan_path)
    if (digest(plan_path) != receipt['producer_plan_sha256']
            or plan.get('module') != MODULE or plan.get('inputs') != inputs or plan.get('config') != config
            or paused.get('status') != 'PAUSED' or paused.get('paused_operation') != operation
            or paused.get('checkpoint_validation_required') is not True
            or paused.get('checkpoint_outputs', {}).get(name) != digest(path)
            or any((origin/terminal).exists() for terminal in ('COMPLETE.json', 'FAILED.json'))):
        raise ValueError('Pilot has no matching original native pause')
    owner = read(origin/'OWNER.json')
    if (owner.get('plan_sha256') != receipt['producer_plan_sha256']
            or is_same_live_process(owner['native'])):
        raise ValueError('Pilot producer still live or rebound')
    return receipt


def checkpoint(path, inputs, config):
    """Inspect bounded state/count metadata only; never read score estimates."""
    path = Path(path).resolve()
    con = sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)
    try:
        binding = ck.get(con, 'binding')
        state = ck.get(con, 'state')
        counts = {table:con.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]
                  for table in ('roster', 'scores', 'fits', 'analytical')}
    finally:
        con.close()
    if binding != collection.identity(inputs, config):
        raise ValueError('Checkpoint scientific binding changed')
    q = boundary(config['expected_positions'])
    if (state['roster'] != counts['roster'] or not 0 <= counts['roster'] <= q
            or any(counts[name] for name in ('scores', 'fits', 'analytical'))
            or any(state[name] for name in ('scores', 'fit', 'analytical'))
            or state['phase'] not in ('roster', 'scores')):
        raise ValueError('Checkpoint is not the first pre-score roster prefix')
    return state, counts


def record_pilot(output, workspace, root, operation, result, inputs, config, restored):
    bound = contract(inputs, config)
    db = Path(workspace)/'PRIVATE_COLLECTION.sqlite'
    if not db.exists():
        return result
    state, counts = checkpoint(db, inputs, config)
    if counts['roster'] < bound['boundary']:
        # A genuine earlier owner/resource interruption is not called a pilot.
        return result
    if result.get('status') != 'yielded':
        raise ValueError('Collector did not stop at the declared roster boundary')
    n, q = bound['denominator'], bound['boundary']
    receipt = dict(
        binding=bound, operation=operation, producer_attempt_root=str(root),
        producer_plan_sha256=digest(root/'PLAN.json'),
        completed_roster_rows=q, source_roster_rows=n, observed_fraction=q/n,
        first_whole_row_at_or_after_fraction=.05, exact_five_percent=(q*20==n),
        restored_execution_roster_rows=restored if operation=='execute' else 0,
        verification_prefix_credited=False, score_rows=0, complete_fit_units=0,
        analytical_rows=0, population_complete=False,
        cpu_fraction_claimed=False, full_collection_fraction_claimed=False,
        checkpoint_phase=state['phase'], checkpoint_sha256=digest(db),
        checkpoint_relative_path=db.relative_to(Path(output)).as_posix(),
        cumulative_cost_source='all native job usage, previous attempts, setup and runtime accounting; no CPU extrapolation here')
    write_json(Path(output)/PILOTS[operation], receipt)
    return dict(result, reason='First ceil(N/20) immutable roster rows completed; owner cost review required',
                roster_pilot=receipt, row_pilot_only=True)


def _execute(output, inputs, config):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    root, _ = context(output, inputs, config)
    bound = contract(inputs, config)
    execute_pilot = copied_pilot(output, 'execute', inputs, config)
    if execute_pilot:
        return collection.execute(output, inputs, config)
    if (output/'SOURCE_SEAL.json').exists():
        raise ValueError('Complete collection has no authenticated initial execute pilot')
    restored = 0
    db = output/'PRIVATE_COLLECTION.sqlite'
    if db.exists():
        ck.copied(db, output, lambda: ck.require(output))
        _, counts = checkpoint(db, inputs, config)
        restored = counts['roster']
    remaining = bound['boundary']-restored
    if remaining:
        result = collection.execute(output, inputs, dict(config, max_new_draws=remaining))
    else:
        result = dict(status='yielded', reason='Authenticated exact boundary recovered before pilot publication',
                      recovered_checkpoint=True)
    return record_pilot(output, output, root, 'execute', result, inputs, config, restored)


def _verify(output, inputs, config):
    output = Path(output)
    root, _ = context(output, inputs, config)
    if not copied_pilot(output, 'execute', inputs, config):
        raise ValueError('Independent verification requires the actual execute pilot')
    if copied_pilot(output, 'verify', inputs, config):
        return collection.verify(output, inputs, config)
    before = {path.name for path in output.glob('independent_collection-*') if path.is_dir()}
    result = collection.verify(output, inputs, dict(config, max_new_draws=boundary(config['expected_positions'])))
    new = [path for path in output.glob('independent_collection-*') if path.is_dir() and path.name not in before]
    if not new:
        if result.get('status') != 'yielded':
            raise ValueError('Fresh independent collection workspace missing')
        return result
    if len(new) != 1:
        raise ValueError('Ambiguous independent collection workspace')
    return record_pilot(output, new[0], root, 'verify', result, inputs, config, 0)


def execute(output, inputs, config):
    return ck.guarded(_execute, output, inputs, config)


def verify(output, inputs, config):
    return ck.guarded(_verify, output, inputs, config)
