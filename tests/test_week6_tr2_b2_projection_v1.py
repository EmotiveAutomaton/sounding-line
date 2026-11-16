"""189 constructed source/replay cases, prepared only; counted owner run required.

DESIGN CHECK: LESSONS 2-5. Literal inputs/answers preserve B2 source semantics,
not proposed TR2 science. Corrupted membership must fail even if its manifest
hash is recomputed. No human archive or outcome array is accessed.
"""
from pathlib import Path
import importlib.util
import json
import sys
import pytest

HERE = Path(__file__).resolve().parent
if (HERE/'tr2_b2_pair_projection_v1.py').is_file():
    sys.path.insert(0, str(HERE))
    import tr2_b2_pair_projection_v1 as adapter
    bank_path = HERE/'tr2_b2_literal_bank_v1.py'
else:
    from runners.drive.cards import week6_tr2_b2_projection_v1 as adapter
    bank_path = HERE/'fixtures/tr2_b2_literal_bank_v1.py'

literal_spec = importlib.util.spec_from_file_location('tr2_prepared_literal_bank',
    bank_path)
literal = importlib.util.module_from_spec(literal_spec)
literal_spec.loader.exec_module(literal)


def run(tmp_path, rows, chunk_size=7, max_rows=adapter.MAX_ROWS):
    tmp_path.mkdir(parents=True, exist_ok=True)
    source = tmp_path/'CONSTRUCTED.json'
    source.write_bytes(adapter.canonical(dict(schema=adapter.SCHEMA, constructed_only=True, rows=rows)))
    inputs = dict(constructed_source=dict(path=str(source), sha256=adapter.digest(source)))
    config = dict(constructed_only=True, chunk_size=chunk_size, max_rows=max_rows)
    output = tmp_path/'output'
    assert adapter.execute(output, inputs, config)['scientific_admission'] is False
    assert adapter.verify(output, inputs, config)['independent_pair_replay'] is True
    return json.loads((output/'PROJECTION.json').read_text()), output, inputs, config


@pytest.mark.parametrize('case', literal.VALID, ids=[x[0] for x in literal.VALID])
@pytest.mark.parametrize('swap', [False, True])
@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('chunk_size', [1, 7])
def test_exact_pair_membership(tmp_path, case, swap, reverse, chunk_size):
    rows = literal.pair(case)
    if swap:
        rows[0]['Saved'], rows[1]['Saved'] = '0', '1'
    if reverse:
        rows.reverse()
    result, _, _, _ = run(tmp_path, rows, chunk_size)
    bit = 0 if swap else 1
    dimensions = ['Intervention'] + ([case[3]] if case[3] else [])
    expected = [dict(response_id='R-SEM-0', user='SEM-U0', session_id='SEM-S0',
                     dimension=dimension, positive=bit) for dimension in sorted(dimensions)]
    assert result['projection'] == expected
    assert result['pairs'] == [dict(response_id='R-SEM-0', row_count=2, valid=True, reasons=[])]
    assert result['users'] == [dict(user='SEM-U0', eligible=False,
                                   dimensions={dimension: [1, bit, 1] for dimension in dimensions})]
    assert result['census']['complete_valid_pairs'] == 1


@pytest.mark.parametrize('name', literal.BAD_NAMES)
def test_malformed_pair_dispositions(tmp_path, name):
    result, _, _, _ = run(tmp_path, literal.malformed(name))
    assert result['projection'] == result['users'] == []
    assert all(not pair['valid'] and pair['reasons'] for pair in result['pairs'])
    assert result['census']['complete_valid_pairs'] == 0
    assert result['census']['orphans'] == (2 if name == 'SPLIT-RESPONSE' else int(name == 'ORPHAN'))
    assert result['census']['duplicated_responses'] == int(name in ('THREE-ROWS', 'FOUR-ROWS'))


@pytest.mark.parametrize('missing', literal.COLUMNS)
def test_missing_required_field_refuses_before_publication(tmp_path, missing):
    rows = literal.pair(literal.VALID[0])
    del rows[0][missing]
    with pytest.raises(ValueError, match='Exact eight-column schema required'):
        run(tmp_path, rows)
    assert not (tmp_path/'output/PROJECTION.json').exists()
    assert not (tmp_path/'output/MANIFEST.json').exists()


@pytest.mark.parametrize('case', literal.VALID[5:], ids=[x[0] for x in literal.VALID[5:]])
def test_nonfocal_second_session_is_part_of_original_cohort(tmp_path, case):
    result, _, _, _ = run(tmp_path, literal.focal_base() + literal.pair(case, 'EDGE-SECOND', 'EDGE-S1'))
    assert result['users'] == [dict(user='SEM-U0', dimensions={
        'Species': [3, 3, 1], 'Gender': [3, 3, 1], 'Fitness': [3, 3, 1],
        'Intervention': [10, 10, 2]}, eligible=True)]
    assert result['census']['common_returning_fingerprints'] == 1
    assert result['census']['original_B2_source_case_pass'] is False
    assert len(result['projection']) == 19


@pytest.mark.parametrize('name', literal.BAD_NAMES)
def test_malformed_second_session_cannot_rescue_original_cohort(tmp_path, name):
    result, _, _, _ = run(tmp_path, literal.focal_base() + literal.malformed(name, 'EDGE-SECOND', 'EDGE-S1'))
    assert result['users'] == [dict(user='SEM-U0', dimensions={
        'Species': [3, 3, 1], 'Gender': [3, 3, 1], 'Fitness': [3, 3, 1],
        'Intervention': [9, 9, 1]}, eligible=False)]
    assert result['census']['complete_valid_pairs'] == 9
    assert result['census']['common_returning_fingerprints'] == 0


def test_nonfocal_only_is_not_original_common_cohort(tmp_path):
    rows = [row for session in range(4) for choice in range(3)
            for row in literal.pair(literal.VALID[5], f'N-{session}-{choice}', f'S{session}')]
    result, _, _, _ = run(tmp_path, rows)
    assert result['users'] == [dict(user='SEM-U0', dimensions={'Intervention': [12, 12, 4]}, eligible=False)]


def combined_rows():
    rows = literal.focal_base() + literal.pair(literal.VALID[5], 'EDGE-SECOND', 'EDGE-S1')
    for index, case in enumerate(literal.VALID):
        rows += literal.pair(case, f'VALID-{index}', f'VALID-S{index}')
    for index, name in enumerate(literal.BAD_NAMES):
        rows += literal.malformed(name, f'BAD-{index}', f'BAD-S{index}')
    return rows


def test_unchanged_original_producer_matches_all_constructed_aggregate_fields(tmp_path):
    rows = combined_rows()
    result, _, _, _ = run(tmp_path/'adapter', rows)
    original = tmp_path/'original'
    original.mkdir()
    census, users = literal.run_source(original, rows)
    assert result['users'] == users
    for field in ('rows', 'responses', 'orphans', 'duplicated_responses', 'complete_valid_pairs',
                  'fingerprints', 'common_returning_fingerprints', 'three_scenario_fingerprints'):
        assert result['census'][field] == census[field]
    assert result['census']['original_B2_source_case_pass'] == census['source_case_pass']


def test_row_and_chunk_order_replay_is_byte_identical(tmp_path):
    rows = combined_rows()
    _, one, _, _ = run(tmp_path/'one', rows, 1)
    _, two, _, _ = run(tmp_path/'two', list(reversed(rows)), 7)
    assert (one/'PROJECTION.json').read_bytes() == (two/'PROJECTION.json').read_bytes()


TAMPERS = ('missing_record', 'duplicate_record', 'positive_bit', 'session_id',
           'missing_pair', 'cohort', 'census', 'manifest')


@pytest.mark.parametrize('change', TAMPERS)
def test_corrupt_projection_refuses_even_with_rehashed_manifest(tmp_path, change):
    result, output, inputs, config = run(tmp_path, literal.focal_base())
    if change == 'missing_record':
        result['projection'].pop()
    elif change == 'duplicate_record':
        result['projection'].append(dict(result['projection'][0]))
    elif change == 'positive_bit':
        result['projection'][0]['positive'] = 1-result['projection'][0]['positive']
    elif change == 'session_id':
        result['projection'][0]['session_id'] = 'invented-session'
    elif change == 'missing_pair':
        result['pairs'].pop()
    elif change == 'cohort':
        result['users'][0]['eligible'] = True
    elif change == 'census':
        result['census']['rows'] += 1
    (output/'PROJECTION.json').write_bytes(adapter.canonical(result))
    manifest = json.loads((output/'MANIFEST.json').read_text())
    manifest['projection_sha256'] = adapter.digest(output/'PROJECTION.json')
    if change == 'manifest':
        manifest['scientific_admission'] = True
    (output/'MANIFEST.json').write_bytes(adapter.canonical(manifest))
    reason = 'Projection manifest mismatch' if change == 'manifest' else 'Independent complete-pair replay mismatch'
    with pytest.raises(ValueError, match=reason):
        adapter.verify(output, inputs, config)


def test_changed_source_pin_refuses_replay(tmp_path):
    _, output, inputs, config = run(tmp_path, literal.pair(literal.VALID[0]))
    source = Path(inputs['constructed_source']['path'])
    source.write_bytes(source.read_bytes() + b' ')
    with pytest.raises(ValueError, match='Constructed source hash changed'):
        adapter.verify(output, inputs, config)


@pytest.mark.parametrize('case', ('row_bound', 'literal_string', 'extra_column', 'constructed_only'))
def test_bounded_handler_refusals(tmp_path, case):
    rows = literal.pair(literal.VALID[0])
    if case == 'row_bound':
        with pytest.raises(ValueError, match='Constructed row bound'):
            run(tmp_path, rows, max_rows=1)
    elif case == 'literal_string':
        rows[0]['Saved'] = 1
        with pytest.raises(ValueError, match='Source fields must be literal strings'):
            run(tmp_path, rows)
    elif case == 'extra_column':
        rows[0]['participant_demographic'] = 'must not be processed'
        with pytest.raises(ValueError, match='Exact eight-column schema required'):
            run(tmp_path, rows)
    else:
        with pytest.raises(ValueError, match='Constructed-only handler'):
            adapter.execute(tmp_path/'output', {}, dict(constructed_only=False))
