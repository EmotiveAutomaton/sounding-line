"""Constructed archive, coverage and restart cases; never a human source.

DESIGN CHECK: LESSONS 2-5. Both scientific directions use identical original
pair/cohort handling. Resume must retain every row; corruption cannot become
completion. Literal original-reader comparison and independent replay are
required. This qualifies only source engineering, never TR2 inference.
"""
from pathlib import Path
from contextlib import ExitStack
import importlib.util
import json

import pytest

HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p/'runners/theory_days/moral.py').is_file())


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


handler = HERE/'tr2_b2_archive_v1.py'
if not handler.is_file():
    handler = REPO/'runners/drive/cards/week6_tr2_b2_archive_v1.py'
route = load('tr2_b2_archive_candidate', handler)
bank = load('tr2_b2_literal_bank', REPO/'tests/fixtures/tr2_b2_literal_bank_v1.py')


def records():
    result = bank.focal_base() + bank.pair(bank.VALID[5], 'SECOND-SESSION', 'EDGE-S1')
    for n, case in enumerate(bank.VALID):
        result += bank.pair(case, 'VALID-' + str(n), 'SEM-S0')
    for n, name in enumerate(bank.BAD_NAMES):
        result += bank.malformed(name, 'BAD-' + str(n), 'BAD-S0')
    return result


def make(tmp_path, rows=None, **changes):
    tmp_path.mkdir(parents=True, exist_ok=True)
    rows = records() if rows is None else rows
    archive = bank.envelope(tmp_path, rows)
    schema = route.backlog_intake.moral_header(archive)
    census = route.moral.prepare(archive, tmp_path/'reference.sqlite', tmp_path/'reference.jsonl.gz')
    value = dict(kind='constructed_fixture', archive=dict(path=str(archive), sha256=route.sha(archive),
        bytes=archive.stat().st_size), member=schema['member'], expanded_bytes=schema['expanded_bytes'],
        expected_census={field: census[field] for field in route.FIELDS},
        expected_counts_sha256=route.sha(tmp_path/'reference.jsonl.gz'), metadata_pins=[])
    path = tmp_path/'SOURCE_CONTRACT.json'
    route.atomic(path, value)
    inputs = dict(source_contract=dict(path=str(path), sha256=route.sha(path)))
    config = dict(constructed_only=True, buckets=4, chunk_rows=7,
        owner_remaining_card_cpu_seconds=60000, slice_cpu_seconds=120,
        slice_wall_seconds=240, max_output_bytes=2**30, first_cost_prefix=False)
    config.update(changes)
    return tmp_path/'output', inputs, config, rows


def edit_contract(inputs, change):
    path = Path(inputs['source_contract']['path'])
    value = route.read(path)
    change(value)
    route.atomic(path, value)
    inputs['source_contract']['sha256'] = route.sha(path)


def until_done(output, inputs, config, independent=False):
    results = []
    for _ in range(300):
        result = route.run(output, inputs, config, independent)
        results.append(result)
        if result['status'] == 'complete':
            return results
        assert result['status'] == 'yielded' and result['verified'] is False
        assert not (output/('SOURCE_VERIFIED.json' if independent else 'PRODUCER_COMPLETE.json')).exists()
    raise AssertionError('Constructed bounded route did not terminate')


def complete(case):
    output, inputs, config, _ = case
    until_done(output, inputs, config)
    until_done(output, inputs, config, True)
    assert route.verify(output, inputs, config)['verified'] is True
    return output


def first_chunk(case):
    output, inputs, config, _ = case
    result = route.execute(output, inputs, dict(config, max_new_units=1))
    assert result['status'] == 'yielded' and result['reason'] == 'completed_work_unit_quantum'
    assert set(route.read(output/'producer/STATE.json')) == {'raw/000000'}
    return output/'producer/raw/000000'


def rehash_receipt(output, key, mutate):
    folder = output/'producer'/key
    receipt = route.read(folder/'RECEIPT.json')
    mutate(folder, receipt)
    route.atomic(folder/'RECEIPT.json', receipt)
    state = route.read(output/'producer/STATE.json')
    state[key] = route.sha(folder/'RECEIPT.json')
    route.atomic(output/'producer/STATE.json', state)


@pytest.mark.parametrize('saved_flip', [False, True])
@pytest.mark.parametrize('reverse', [False, True])
def test_original_pair_and_cohort_semantics(tmp_path, saved_flip, reverse):
    rows = records()
    if saved_flip:
        # Only valid flags change sign; malformed literal cases retain their defects.
        for row in rows:
            if row['ResponseID'].startswith(('VALID-', 'EDGE-', 'SECOND-')):
                row['Saved'] = str(1-int(row['Saved']))
    if reverse:
        rows.reverse()
    case = make(tmp_path, rows)
    output = complete(case)
    expected = route.core.independent_replay(rows)
    observed = []
    for b in range(case[2]['buckets']):
        observed.extend(route.lines(output/f'producer/pairs/{b:02d}'/'PROJECTION.jsonl.gz'))
    assert sorted(observed, key=lambda x: (x['response_id'], x['dimension'])) == expected['projection']
    assert list(route.lines(output/'producer/merge/PRIVATE_COUNTS.jsonl.gz')) == expected['users']
    assert route.read(output/'SOURCE_VERIFIED.json')['scientific_admission'] is False


@pytest.mark.parametrize('count', [1, 4, 32])
def test_exhaustive_engineering_partition_preserves_all_rows(tmp_path, count):
    case = make(tmp_path, buckets=count)
    output = complete(case)
    source = route.read(output/'producer/merge/SOURCE.json')
    assert source['rows'] == len(case[3])
    assert route.sha(output/'producer/merge/PRIVATE_COUNTS.jsonl.gz') == route.sha(tmp_path/'reference.jsonl.gz')


def test_one_unit_resume_preserves_complete_source_and_replay(tmp_path):
    case = make(tmp_path, max_new_units=1)
    output, inputs, config, _ = case
    producer = until_done(output, inputs, config)
    replay = until_done(output, inputs, config, True)
    assert len(producer) == len(replay) and len(producer) > 10
    assert all(x['completed_new_units'] == 1 for x in producer[:-1] + replay[:-1])
    assert route.sha(output/'producer/merge/PRIVATE_COUNTS.jsonl.gz') == route.sha(output/'replay/merge/PRIVATE_COUNTS.jsonl.gz')


def test_seal_before_journal_update_is_reconciled(tmp_path):
    case = make(tmp_path)
    folder = first_chunk(case)
    receipt_pin = route.sha(folder/'RECEIPT.json')
    route.atomic(case[0]/'producer/STATE.json', {})
    complete(case)
    assert route.read(case[0]/'producer/STATE.json')['raw/000000'] == receipt_pin


def test_partial_interrupted_workspace_is_preserved_and_never_adopted(tmp_path):
    case = make(tmp_path)
    first_chunk(case)
    partial = case[0]/'producer/partial/interrupted'
    partial.mkdir()
    (partial/'work.sqlite').write_bytes(b'not a completed SQLite workspace')
    pin = route.sha(partial/'work.sqlite')
    complete(case)
    assert route.sha(partial/'work.sqlite') == pin
    assert all('partial' not in key for key in route.read(case[0]/'producer/STATE.json'))


@pytest.mark.parametrize('name', ['RECEIPT.json', 'b00.jsonl.gz'])
def test_missing_journaled_evidence_refuses(tmp_path, name):
    case = make(tmp_path)
    folder = first_chunk(case)
    (folder/name).rename(folder/(name + '.missing'))
    with pytest.raises(ValueError, match='Missing journaled work unit|Work-unit file coverage'):
        route.execute(*case[:3])
    assert not (case[0]/'PRODUCER_COMPLETE.json').exists()


def test_receipt_mutation_refuses(tmp_path):
    case = make(tmp_path)
    folder = first_chunk(case)
    receipt = route.read(folder/'RECEIPT.json')
    receipt['meta']['rows'] += 1
    route.atomic(folder/'RECEIPT.json', receipt)
    with pytest.raises(ValueError, match='Work-unit receipt changed'):
        route.execute(*case[:3])


def test_artifact_mutation_refuses(tmp_path):
    case = make(tmp_path)
    folder = first_chunk(case)
    with (folder/'b00.jsonl.gz').open('ab') as stream:
        stream.write(b'corruption')
    with pytest.raises(ValueError, match='Work-unit artifact changed'):
        route.execute(*case[:3])


@pytest.mark.parametrize('field,value', [('buckets', 3), ('chunk_rows', 9)])
def test_changed_resume_partition_refuses(tmp_path, field, value):
    case = make(tmp_path)
    first_chunk(case)
    with pytest.raises(ValueError, match='Resume binding changed'):
        route.execute(case[0], case[1], dict(case[2], **{field: value}))


def test_changed_archive_after_checkpoint_refuses(tmp_path):
    case = make(tmp_path)
    first_chunk(case)
    source = Path(route.read(case[1]['source_contract']['path'])['archive']['path'])
    with source.open('ab') as stream:
        stream.write(b'changed')
    with pytest.raises(ValueError, match='Original archive hash or size changed'):
        route.execute(*case[:3])


@pytest.mark.parametrize('field', ['rows', 'complete_valid_pairs'])
def test_wrong_original_coverage_or_census_refuses(tmp_path, field):
    case = make(tmp_path)
    edit_contract(case[1], lambda value: value['expected_census'].__setitem__(field, value['expected_census'][field]+1))
    with pytest.raises(ValueError, match='row/member coverage|census reconciliation'):
        route.execute(*case[:3])
    assert not (case[0]/'PRODUCER_COMPLETE.json').exists()


def test_wrong_original_cohort_bytes_refuse(tmp_path):
    case = make(tmp_path)
    edit_contract(case[1], lambda value: value.__setitem__('expected_counts_sha256', '0'*64))
    with pytest.raises(ValueError, match='Original cohort bytes differ'):
        route.execute(*case[:3])


def test_changed_contract_hash_refuses(tmp_path):
    case = make(tmp_path)
    with Path(case[1]['source_contract']['path']).open('ab') as stream:
        stream.write(b' ')
    with pytest.raises(ValueError, match='Source metadata contract changed'):
        route.execute(*case[:3])


def test_independent_replay_refuses_rehashed_producer_choice_corruption(tmp_path):
    case = make(tmp_path)
    output, inputs, config, _ = case
    until_done(output, inputs, config)
    key = next(f'pairs/{b:02d}' for b in range(config['buckets'])
               if list(route.lines(output/f'producer/pairs/{b:02d}'/'PROJECTION.jsonl.gz')))
    def corrupt(folder, receipt):
        path = folder/'PROJECTION.jsonl.gz'
        rows = list(route.lines(path))
        rows[0]['positive'] = 1 - rows[0]['positive']
        path.rename(folder/'PROJECTION.original.gz')
        with ExitStack() as stack:
            stream = route.zipped(stack, path)
            for row in rows:
                stream.write(route.data(row))
        # Keep original bytes outside the immutable unit so file coverage remains exact.
        (folder/'PROJECTION.original.gz').rename(output/'CORRUPTED_PROJECTION_ORIGINAL.gz')
        receipt['files'][path.name] = dict(sha256=route.sha(path), bytes=path.stat().st_size)
    rehash_receipt(output, key, corrupt)
    with pytest.raises(ValueError, match='Full independent source/observation replay differs'):
        until_done(output, inputs, config, True)
    assert not (output/'SOURCE_VERIFIED.json').exists()


def test_missing_producer_complete_refuses_before_replay(tmp_path):
    case = make(tmp_path)
    first_chunk(case)
    with pytest.raises(ValueError, match='Missing complete producer'):
        route.verify(*case[:3])
    assert not (case[0]/'replay').exists()


@pytest.mark.parametrize('missing', bank.COLUMNS)
def test_each_missing_required_source_field_refuses(tmp_path, missing):
    case = make(tmp_path)
    archive = bank.envelope(tmp_path, case[3], [c for c in bank.COLUMNS if c != missing])
    def change(value):
        value['archive'].update(sha256=route.sha(archive), bytes=archive.stat().st_size)
    edit_contract(case[1], change)
    with pytest.raises((AssertionError, ValueError), match='missing|required|Missing|Required'):
        route.execute(*case[:3])
    assert not (case[0]/'PRODUCER_COMPLETE.json').exists()


def test_first_five_percent_cost_prefix_yields_once(tmp_path):
    case = make(tmp_path, first_cost_prefix=True)
    output, inputs, config, _ = case
    results = until_done(output, inputs, config)
    assert sum(r.get('reason') == 'first_five_percent_source_cost_prefix' for r in results) == 1
    marker = route.read(output/'producer/SOURCE_COST_PREFIX.json')
    assert marker['rows'] >= len(case[3])*.05
    assert marker['complete_program_cost_forecast'] is False
    assert marker['source_population_complete'] is False
    replay = until_done(output, inputs, config, True)
    assert sum(r.get('reason') == 'first_five_percent_source_cost_prefix' for r in replay) == 1


@pytest.mark.parametrize('name', ['YIELD_REQUEST', 'YIELD_REQUEST.json'])
def test_cooperative_yield_marker_never_claims_completion(tmp_path, name):
    case = make(tmp_path)
    output, inputs, config, _ = case
    output.mkdir()
    (output/name).write_text('{}', encoding='utf8')
    result = route.execute(output, inputs, config)
    assert result['status'] == 'yielded' and result['reason'] == 'YIELD_REQUEST'
    assert not (output/'PRODUCER_COMPLETE.json').exists()


@pytest.mark.parametrize('remaining', [0, 30, 60001])
def test_inclusive_card_remaining_allowance_must_be_bound(tmp_path, remaining):
    case = make(tmp_path, owner_remaining_card_cpu_seconds=remaining)
    with pytest.raises(ValueError, match='remaining original TR2 inclusive allowance'):
        route.execute(*case[:3])


@pytest.mark.parametrize('corruption', ['row_count', 'route'])
def test_rehashed_raw_unit_coverage_or_routing_corruption_refuses(tmp_path, corruption):
    case = make(tmp_path)
    folder = first_chunk(case)
    def corrupt(directory, receipt):
        if corruption == 'row_count':
            receipt['meta']['bucket_rows'][0] += 1
        else:
            source_bucket = next(b for b, n in enumerate(receipt['meta']['bucket_rows']) if n)
            target_bucket = (source_bucket+1) % case[2]['buckets']
            first = directory/f'b{source_bucket:02d}.jsonl.gz'
            second = directory/f'b{target_bucket:02d}.jsonl.gz'
            temporary = directory/'swap.tmp'
            first.rename(temporary)
            second.rename(first)
            temporary.rename(second)
            for b in (source_bucket, target_bucket):
                path = directory/f'b{b:02d}.jsonl.gz'
                receipt['files'][path.name] = dict(sha256=route.sha(path), bytes=path.stat().st_size)
            sizes = receipt['meta']['bucket_rows']
            sizes[source_bucket], sizes[target_bucket] = sizes[target_bucket], sizes[source_bucket]
    rehash_receipt(case[0], 'raw/000000', corrupt)
    with pytest.raises(ValueError, match='Bucket row coverage differs|Misrouted response row'):
        route.execute(*case[:3])
    assert not (case[0]/'PRODUCER_COMPLETE.json').exists()


def test_output_boundary_yields_without_complete(tmp_path):
    case = make(tmp_path, max_output_bytes=1)
    result = route.execute(*case[:3])
    assert result['status'] == 'yielded' and result['reason'] == 'derived_output_boundary'
    assert not (case[0]/'PRODUCER_COMPLETE.json').exists()
