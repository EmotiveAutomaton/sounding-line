"""Frozen disjoint ordinal ranges for the original CH1 scoring roster.

DESIGN CHECK: LESSONS 3-5, amendment V. Under either scientific outcome,
admission requires an exact, nonempty, contiguous partition after a retired
clean predecessor. Gaps, overlaps, changed source/node pins, an active old
owner, an unsealed unit, and unknown native identity all refuse. This module
never stops, launches or admits a process and never creates old completions.
"""
from pathlib import Path
import itertools
import math

from . import week5_ch_queue_backhalf_v1 as original
from .week5_ch_source import digest
from .week5_ch_pipeline_checkpoint import checked

SCHEMA = 'CH1-disjoint-range-v1'
ORIGINAL_MODULE = 'runners.drive.cards.week5_ch_queue_backhalf_v1'


def implementation_pins():
    from . import week5_ch_queue_range_v1 as adapter
    from . import week5_ch_queue_worker_v1 as worker
    return {str(Path(module.__file__).resolve()): digest(module.__file__)
            for module in (adapter, worker, original, original.bounded,
                           original.scorer, original.ck)} | {
                str(Path(__file__).resolve()): digest(__file__)}


def partition(begin, end, shards=5, unit=64):
    """Split units evenly; boundaries are relative to the preserved prefix."""
    if any(type(v) is not int for v in (begin, end, shards, unit)):
        raise ValueError('Integral range controls required')
    if not 0 <= begin < end <= 400000 or not 1 <= shards <= 5 or not 1 <= unit <= 64:
        raise ValueError('Range controls outside declared bounds')
    units = math.ceil((end - begin) / unit)
    count = min(shards, units)
    base, extra = divmod(units, count)
    ranges = []
    cursor = begin
    for index in range(count):
        stop = min(end, cursor + (base + (index < extra)) * unit)
        ranges.append(dict(id=f'shard-{index + 1}', begin=cursor, end=stop,
                           pause_rank=index + 1))
        cursor = stop
    return ranges


def validate_partition(manifest):
    if manifest.get('schema') != SCHEMA:
        raise ValueError('Unknown range manifest schema')
    begin, total = manifest.get('begin'), manifest.get('expected_positions')
    if type(begin) is not int or type(total) is not int or not 0 <= begin < total <= 400000:
        raise ValueError('Invalid original roster bounds')
    ranges = manifest.get('ranges')
    if not isinstance(ranges, list) or not 1 <= len(ranges) <= 5:
        raise ValueError('One to five disjoint ranges required')
    cursor = begin
    seen = set()
    for index, item in enumerate(ranges):
        if set(item) != {'id', 'begin', 'end', 'pause_rank'}:
            raise ValueError('Unexpected range fields')
        if (not isinstance(item['id'], str) or not item['id'] or item['id'] in seen or
                any(type(item[k]) is not int for k in ('begin', 'end', 'pause_rank')) or
                item['begin'] != cursor or not cursor < item['end'] <= total or
                item['pause_rank'] != index + 1):
            raise ValueError('Gapped, overlapping, empty or duplicated range')
        seen.add(item['id'])
        cursor = item['end']
    if cursor != total:
        raise ValueError('Range union does not cover the complete remainder')
    return ranges


def check_handover(manifest, is_live=None):
    """Read exact terminal metadata and native owners; never infer an exit."""
    if is_live is None:
        from runners.stage9.process_identity import is_same_live_process
        is_live = is_same_live_process
    handover = original.read(checked(manifest['handover']))
    if handover.get('status') != 'CLEAN_PREDECESSOR_RETIRED':
        raise ValueError('Authenticated clean handover required')
    root = Path(handover['root']).resolve()
    pins = handover['files']
    required = {'PLAN.json', 'OWNER.json', 'EXECUTE_NATIVE.json', 'output/QUEUE_STATE.json'}
    if not required <= set(pins):
        raise ValueError('Handover lacks required native/plan/state evidence')
    for name, expected in pins.items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file() or digest(path) != expected:
            raise ValueError('Handover evidence changed or escaped its root')
    terminal_name = handover['terminal']
    if terminal_name not in ('COMPLETE.json', 'PAUSED.json') or terminal_name not in pins:
        raise ValueError('Clean terminal proof required; failure is not completion')
    if any((root / name).exists() for name in ('FAILED.json', 'MONITOR_FAILED.json')):
        raise ValueError('Current predecessor has a conflicting failure terminal')
    terminal = original.read(root / terminal_name)
    if terminal.get('status') != terminal_name[:-5]:
        raise ValueError('Terminal status disagrees with its identity')
    outputs = terminal['outputs'] if terminal_name == 'COMPLETE.json' else terminal['checkpoint_outputs']
    state_key = 'output/QUEUE_STATE.json' if terminal_name == 'COMPLETE.json' else 'QUEUE_STATE.json'
    if outputs.get(state_key) != pins['output/QUEUE_STATE.json']:
        raise ValueError('Terminal does not bind the clean checkpoint')
    state = original.read(root / 'output/QUEUE_STATE.json')
    plan = original.read(root / 'PLAN.json')
    if (plan['module'] != ORIGINAL_MODULE or state['active'] is not None or
            state['next_offset'] != manifest['begin'] or
            plan['inputs']['positions'] != manifest['positions'] or
            plan['inputs']['engine'] != manifest['engine'] or
            plan['config']['expected_positions'] != manifest['expected_positions'] or
            plan['config'].get('nodes', 1000000) != manifest['nodes']):
        raise ValueError('Predecessor is not a clean checkpoint of the same roster')
    if state['binding'] != original.identity(plan['inputs'], plan['config']):
        raise ValueError('Predecessor checkpoint implementation/configuration changed')
    positions = original.scorer.iter_positions(checked(plan['inputs']['positions']))
    cursor = plan['config'].get('offset', 0)
    for _ in range(cursor):
        if next(positions, None) is None:
            raise ValueError('Predecessor begins outside its original roster')
    for item in state['units']:
        unit = (root / 'output' / item['path']).resolve()
        if not unit.is_relative_to(root / 'output'):
            raise ValueError('Predecessor unit escaped its output root')
        if digest(unit / 'UNIT_SEAL.json') != item['seal_sha256']:
            raise ValueError('Predecessor unit seal changed')
        seal = original.check_unit(unit)
        unit_plan = original.read(unit / 'UNIT.json')
        if (seal['begin'] != cursor or seal['end'] > manifest['begin'] or
                unit_plan['source_roster'] != manifest['positions'] or
                unit_plan['inputs']['engine'] != manifest['engine'] or
                unit_plan['config']['nodes'] != manifest['nodes']):
            raise ValueError('Predecessor unit coverage or source binding differs')
        local = itertools.islice(original.scorer.iter_positions(unit / 'PRIVATE_POSITIONS.jsonl.gz'), seal['positions'])
        count = 0
        for row in local:
            if row != next(positions, None):
                raise ValueError('Predecessor unit differs from original ordinal')
            count += 1
        if count != seal['positions']:
            raise ValueError('Predecessor unit source is truncated')
        cursor = seal['end']
    if cursor != manifest['begin']:
        raise ValueError('Clean predecessor cursor lacks exact sealed coverage')
    native_files = sorted({root / 'OWNER.json', *root.glob('*_NATIVE.json')})
    for path in native_files:
        if path.name not in pins:
            raise ValueError('Native owner file omitted from handover')
        record = original.read(path)
        native = record.get('native', record)
        if not {'pid', 'created_ticks', 'executable'} <= set(native) or is_live(native):
            raise ValueError('Predecessor native owner is live or unproved')
    if (handover.get('all_sealed_units_authenticated') is not True or
            handover.get('all_checkpoint_outputs_authenticated') is not True or
            handover.get('all_descendant_jobs_exited') is not True or
            handover.get('leases_released') is not True or
            handover.get('all_prior_attempt_costs_retained') is not True or
            not handover.get('historical_prefix_inventory')):
        raise ValueError('Owner audit of saved evidence, exits and costs is incomplete')
    # These owner audit fields accompany exact pinned evidence. They are not
    # substitutes for the separate counted prefix-authentication procedure.
    return handover


def validate(manifest_spec, inputs, config):
    manifest = original.read(checked(manifest_spec))
    ranges = validate_partition(manifest)
    if (manifest['positions'] != inputs['positions'] or manifest['engine'] != inputs['engine'] or
            manifest['expected_positions'] != config['expected_positions'] or
            manifest['nodes'] != config.get('nodes', 1000000)):
        raise ValueError('Range source, denominator or node pin differs')
    matches = [r for r in ranges if r['id'] == config.get('shard_id')]
    if len(matches) != 1 or (matches[0]['begin'], matches[0]['end']) != (config.get('offset'), config.get('range_end')):
        raise ValueError('Shard is not the exact frozen range')
    if manifest.get('status') == 'CONSTRUCTED_ONLY':
        if config.get('constructed_fixture') is not True:
            raise ValueError('Constructed manifest cannot admit production')
    elif manifest.get('status') == 'FROZEN_FOR_OWNER_ADMISSION':
        if config.get('constructed_fixture'):
            raise ValueError('Production manifest is not a constructed fixture')
        check_handover(manifest)
    else:
        raise ValueError('Candidate manifest is not admitted')
    pins = manifest.get('implementation_pins', {})
    if not implementation_pins().items() <= pins.items():
        raise ValueError('Required range implementation source closure differs')
    for path, expected in pins.items():
        if digest(path) != expected:
            raise ValueError('Range implementation pin changed')
    return manifest


def reverse_pause_order(manifest, active_ids):
    """Recommendation only; the owner requests and authenticates each pause."""
    ranges = validate_partition(manifest)
    active = set(active_ids)
    if not active <= {r['id'] for r in ranges}:
        raise ValueError('Unknown active shard')
    return [r['id'] for r in reversed(ranges) if r['id'] in active]
