import csv
from pathlib import Path
import pytest
from runners.drive.cards import week6_in13_v1 as study
from runners.drive.cards import week6_in13_im1_fixture_v1 as fixture
from runners.drive.cards import week6_in13_in15_common_v1 as common


def table_rows(root):
    with (root/'exchange/SCORES.tsv').open(encoding='utf8', newline='') as stream:
        return list(csv.reader(stream, delimiter='\t'))


def replace_table(root, value, rows):
    path = root/'exchange/CHANGED.tsv'
    with path.open('w', encoding='utf8', newline='') as stream:
        csv.writer(stream, delimiter='\t', lineterminator='\n').writerows(rows)
    manifest = common.seal.read(root/'exchange/IM1.json')
    manifest.update(table=path.name, table_sha256=common.io.sha(path))
    target = root/'exchange/CHANGED.json'; common.io.write_json(target, manifest)
    value['inputs'].update(im1_manifest=str(target), im1_manifest_sha256=common.io.sha(target))


def test_im1_exact_full_roster_qualified_subset_separate_scales_and_independent_parser(tmp_path):
    value = fixture.bundle(tmp_path)
    with fixture.upstream(tmp_path, value):
        actual, identity = study.load(value['inputs'], value['config'])
        replay, reference = study.load(value['inputs'], value['config'], independent=True)
    common.compare(actual.to_dict('records'), replay.to_dict('records')); common.compare(identity, reference)
    assert len(actual) == value['expected_primary_rows'] == value['expected_full_rows']-1
    assert identity['IM1']['rows'] == value['expected_full_rows']
    assert identity['IM1']['score_averaging'] is False
    assert set(actual.coder_a__power) == {0, 2} and set(actual.coder_b__power) == {80, 100}
    assert set(identity['IM1']['scales']) == {'coder_a', 'coder_b'}


@pytest.mark.parametrize('defect', ['missing_row', 'duplicate_id', 'foreign_id', 'blank_id', 'extra_column', 'missing_column',
    'duplicate_column', 'extra_value', 'empty_score', 'nonfinite', 'out_of_scale'])
def test_im1_resealed_malformed_tables_are_refused_in_both_parsers(tmp_path, defect):
    value = fixture.bundle(tmp_path); rows = table_rows(tmp_path)
    if defect == 'missing_row': rows.pop()
    elif defect == 'duplicate_id': rows[-1][0] = rows[1][0]
    elif defect == 'foreign_id': rows[-1][0] = 'unregistered-report'
    elif defect == 'blank_id': rows[-1][0] = ' '
    elif defect == 'extra_column':
        rows[0].append('age')
        for row in rows[1:]: row.append('REFUSED_SENTINEL')
    elif defect == 'missing_column':
        for row in rows: row.pop()
    elif defect == 'duplicate_column': rows[0][2] = rows[0][1]
    elif defect == 'extra_value': rows[1].append('REFUSED_SENTINEL')
    elif defect == 'empty_score': rows[1][1] = ''
    elif defect == 'nonfinite': rows[1][1] = 'NaN'
    elif defect == 'out_of_scale': rows[1][1] = '3'
    replace_table(tmp_path, value, rows)
    with fixture.upstream(tmp_path, value):
        for independent in (False, True):
            with pytest.raises(ValueError): study.load(value['inputs'], value['config'], independent)


@pytest.mark.parametrize('member', ['SCORES.tsv', 'coder_a-scale.json', 'coder_b-scale.json', 'IM1.json', 'CHOICE.json'])
def test_im1_unpinned_mutation_is_refused(tmp_path, member):
    value = fixture.bundle(tmp_path); path = tmp_path/'exchange'/member
    path.write_bytes(path.read_bytes()+b'\n')
    with fixture.upstream(tmp_path, value), pytest.raises(ValueError, match='pin differs'):
        study.load(value['inputs'], value['config'])


@pytest.mark.parametrize('defect', ['absent_input', 'missing_declaration', 'after_outcomes', 'other_primary', 'scale_pin', 'duplicate_coder'])
def test_im1_prospective_choice_and_coder_identity_refusals(tmp_path, defect):
    value = fixture.bundle(tmp_path); inputs = value['inputs']
    choice = common.seal.read(inputs['im1_choice_manifest'])
    if defect == 'absent_input': inputs.pop('im1_choice_manifest')
    elif defect == 'missing_declaration': choice.pop('declared_before_outcomes')
    elif defect == 'after_outcomes': choice['declared_before_outcomes'] = False
    elif defect == 'other_primary': choice['primary_coder'] = 'coder_b'
    elif defect == 'scale_pin': choice['coders']['coder_a']['scale_sha256'] = '0'*64
    elif defect == 'duplicate_coder':
        manifest = common.seal.read(inputs['im1_manifest']); manifest['coders'][1] = manifest['coders'][0]
        path = tmp_path/'exchange/DUPLICATE.json'; common.io.write_json(path, manifest)
        inputs.update(im1_manifest=str(path), im1_manifest_sha256=common.io.sha(path))
    if defect not in ('absent_input', 'duplicate_coder'):
        path = tmp_path/'exchange/NEW_CHOICE.json'; common.io.write_json(path, choice)
        inputs.update(im1_choice_manifest=str(path), im1_choice_manifest_sha256=common.io.sha(path))
    with fixture.upstream(tmp_path, value), pytest.raises(ValueError): study.load(inputs, value['config'])


def test_im1_duplicate_json_and_resealed_source_change_after_checkpoint_refused(tmp_path):
    value = fixture.bundle(tmp_path); inputs = value['inputs']
    path = tmp_path/'exchange/DUPLICATE_CHOICE.json'
    body = Path(inputs['im1_choice_manifest']).read_text(encoding='utf8')
    path.write_text(body.replace('{', '{"schema":"IN13C-choice-v1",', 1), encoding='utf8')
    bad = {**inputs, 'im1_choice_manifest': str(path), 'im1_choice_manifest_sha256': common.io.sha(path)}
    with fixture.upstream(tmp_path, value), pytest.raises(ValueError, match='Duplicate IM1 JSON'):
        study.load(bad, value['config'])
    with fixture.upstream(tmp_path, value):
        assert study.execute(tmp_path/'output', inputs, {**value['config'], 'max_new_draws': 1})['status'] == 'yielded'
        rows = table_rows(tmp_path); rows[1][1] = '1.9'; replace_table(tmp_path, value, rows)
        with pytest.raises(ValueError, match='binding changed'):
            study.execute(tmp_path/'output', value['inputs'], value['config'])


def test_im1_full2000_separate_execute_and_replay_with_opposite_coder_signs(tmp_path):
    proof = fixture.separate_chain(tmp_path)
    assert proof['passed'] and proof['separate_processes'] and proof['independent_source_parser']
    assert proof['real_IM1_present_or_admitted'] is False
