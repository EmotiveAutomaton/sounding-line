"""Constructed-only source/annotation fixtures; owner review precedes execution."""
import copy
import csv
import hashlib
import io
from pathlib import Path

import pandas as pd
import pytest

from runners.drive.cards import week6_rw1_source_v1 as source


def record(i, text='I will call. Clouds pass!'):
    values = dict.fromkeys(source.COLUMNS, '5'); values['text_long'] = text
    return source.person_record(values, i, b'x' * 32, 'constructed-source')


def sample():
    return source.sample_sentences([record(i) for i in range(120)])


def test_exact_unicode_offsets_and_declared_abbreviation_rule():
    text = '  I will call!\nClouds pass. Dr. X waits?  '
    spans = source.sentence_spans(text)
    assert [text[a:b] for a, b in spans] == ['I will call!', 'Clouds pass.', 'Dr.', 'X waits?']
    assert source.sentence_spans(' \n ') == []


def test_projection_refuses_extra_fields_and_preserves_missing_ratings():
    values = dict.fromkeys(source.COLUMNS, '5'); values['text_long'] = 'Clouds pass.'
    with pytest.raises(ValueError, match='nonallowlisted'):
        source.person_record({**values, 'demographic_sentinel': 'not imported'}, 0, b'x' * 32, 'fixture')
    values['fear'] = ''
    result = source.person_record(values, 0, b'x' * 32, 'fixture')
    assert result['ratings']['fear'] is None and result['dispositions'] == ['missing_fear']
    values['fear'] = '10'
    with pytest.raises(ValueError, match='original integer scale'):
        source.person_record(values, 0, b'x' * 32, 'fixture')


def test_sample_ignores_ratings_and_marker_enrichment():
    records = [record(i, 'I will call.' if i % 3 else 'Clouds pass.') for i in range(250)]
    a, binding = source.sample_sentences(records)
    changed = copy.deepcopy(records)
    for row in changed:
        row['ratings'] = dict.fromkeys(source.COLUMNS[1:], 9)
    b, other = source.sample_sentences(changed)
    assert a == b and binding == other
    assert len(a) == 200 and len({r['id'] for r in a}) == 200
    with pytest.raises(ValueError, match='distinct'):
        source.sample_sentences(records[:10])


def test_blank_forms_never_count_as_annotations(tmp_path):
    rows, binding = sample()
    form = source.annotation_form(rows, binding, 'hand')
    assert form['builder_id'] is None and not form['independently_annotated']
    assert all(r['label'] is None for r in form['annotations'])
    path = tmp_path / 'hand.json'; source.seal.checkpoint(path, form)
    with pytest.raises(ValueError, match='actual boolean'):
        source.read_form(path, rows, binding, 'hand')


def test_sealed_hand_form_requires_blinding_and_exact_sentences(tmp_path):
    rows, binding = sample(); form = source.annotation_form(rows, binding, 'hand')
    form.update(builder_id='constructed-only', independently_annotated=True,
                provenance_sha256='constructed-only-proof', automatic_labels_seen_before_hand_seal=True)
    for r in form['annotations']:
        r['label'] = False
    path = tmp_path / 'hand.json'; source.seal.checkpoint(path, form)
    with pytest.raises(ValueError, match='precede'):
        source.read_form(path, rows, binding, 'hand')
    form['automatic_labels_seen_before_hand_seal'] = False
    source.seal.checkpoint(path, form)
    assert source.read_form(path, rows, binding, 'hand')[0]['builder_id'] == 'constructed-only'
    form['annotations'][0]['text'] += ' changed'
    source.seal.checkpoint(path, form)
    with pytest.raises(ValueError, match='sentences'):
        source.read_form(path, rows, binding, 'hand')


def test_wrong_raw_source_refuses_before_csv_import(tmp_path, monkeypatch):
    path = tmp_path / 'source.csv'; path.write_bytes(b'text_long,worry\nexample,5\n')
    def forbidden(*args, **kwargs):
        raise AssertionError('Unpinned bytes reached CSV import')
    monkeypatch.setattr(source.pd, 'read_csv', forbidden)
    with pytest.raises(ValueError, match='Git blob'):
        source.load_source({'source_file': str(path), 'notice_directory': str(tmp_path), 'identity_salt': str(path)})


def test_fixed_csv_allowlist_excludes_uncommissioned_columns(tmp_path, monkeypatch):
    stream = io.StringIO(); writer = csv.DictWriter(stream, fieldnames=[*source.COLUMNS, 'private_extra'])
    writer.writeheader()
    for _ in range(2500):
        writer.writerow({**dict.fromkeys(source.COLUMNS, '5'), 'text_long': 'Clouds pass.',
                         'private_extra': 'CONSTRUCTED_UNIMPORTED_SENTINEL'})
    raw = stream.getvalue().encode(); path = tmp_path / 'source.csv'; path.write_bytes(raw)
    monkeypatch.setattr(source, 'GIT_BLOB', hashlib.sha1(('blob ' + str(len(raw)) + '\0').encode() + raw).hexdigest())
    monkeypatch.setattr(source, 'OSF_DECLARED_SHA256', hashlib.sha256(raw).hexdigest())
    notice = tmp_path / 'fixture-notice'; notice.write_bytes(b'constructed notice only')
    monkeypatch.setattr(source, 'NOTICE_PINS', {'fixture-notice': source.io.sha(notice)})
    salt = tmp_path / 'salt'; salt.write_bytes(b'x' * 32)
    original = pd.read_csv; calls = []
    def selected(*args, **kwargs):
        calls.append(kwargs['usecols']); return original(*args, **kwargs)
    monkeypatch.setattr(source.pd, 'read_csv', selected)
    table, _, _ = source.load_source({'source_file': str(path), 'notice_directory': str(tmp_path), 'identity_salt': str(salt)})
    assert calls == [list(source.COLUMNS)] and set(table.columns) == set(source.COLUMNS)
    assert 'CONSTRUCTED_UNIMPORTED_SENTINEL' not in table.to_json()


def test_bounded_complete_source_and_replay(tmp_path, monkeypatch):
    # Only source authentication is substituted; the production API has no fixture flag.
    table = pd.DataFrame([{**dict.fromkeys(source.COLUMNS, '5'), 'text_long': 'I will call. Clouds pass.'}
                          for _ in range(256)])
    identity = {'source_sha256': 'constructed-source', 'marker_sha256': source.io.sha(source.marker.__file__),
                'module_sha256': source.io.sha(source.__file__)}
    monkeypatch.setattr(source, 'load_source', lambda inputs: (table, b'x' * 32, identity))
    monkeypatch.setattr(source, 'private_output', lambda path: Path(path))
    small = {'phase': 'RW1-source', 'max_new_blocks': 1, 'max_wall_seconds': 600}
    output = tmp_path / 'source-output'
    assert source.execute(output, {}, small)['status'] == 'yielded'
    done = source.execute(output, {}, small)
    assert done['complete_preparation'] and done['people'] == 256
    assert not done['independent_annotations_complete'] and not done['human_outcomes_computed']
    assert source.verify(output, {}, small)['status'] == 'yielded'
    assert source.verify(output, {}, small)['verified']


def test_two_sealed_constructed_builder_pairs_remain_unadmitted(tmp_path, monkeypatch):
    rows, binding = sample(); run = tmp_path / 'run'; output = run / 'output'
    source.seal.checkpoint(output / 'SAMPLE.json', {'sentences': rows})
    source.io.write_json(output / 'RESULT.json', {'card': 'RW1-source', 'complete_preparation': True,
        'sample_manifest_sha256': binding, 'source_identity': {'marker_sha256': source.io.sha(source.marker.__file__),
                                                             'module_sha256': source.io.sha(source.__file__)}})
    source.io.write_json(run / 'COMPLETE.json', {'constructed_authentication_boundary': True})
    monkeypatch.setattr(source.seal, 'complete', lambda root, module: (Path(root), {}, {}))
    inputs = {'prepared_run': str(run)}
    for prefix in ('builder_a', 'builder_b'):
        hand = source.annotation_form(rows, binding, 'hand')
        hand.update(builder_id='constructed-' + prefix, independently_annotated=True,
                    provenance_sha256='constructed-only', automatic_labels_seen_before_hand_seal=False)
        for row in hand['annotations']:
            row['label'] = source.marker.plan_candidate(row['text'])
        hp = tmp_path / (prefix + '_hand.json'); source.seal.checkpoint(hp, hand)
        listed = source.annotation_form(rows, binding, 'list')
        listed.update(builder_id=hand['builder_id'], independently_annotated=True,
                      provenance_sha256='constructed-only', hand_receipt_sha256=source.io.sha(hp))
        for row in listed['annotations']:
            row['label'] = source.marker.plan_candidate(row['text'])
        lp = tmp_path / (prefix + '_list.json'); source.seal.checkpoint(lp, listed)
        inputs[prefix + '_hand'], inputs[prefix + '_list'] = str(hp), str(lp)
    result = source.review_markers(inputs, {'phase': 'RW1-marker-review'})
    assert result['status'] == 'reviewable' and not result['production_admitted']
    assert result['owner_identity_and_provenance_review_required']
    inputs['builder_b_hand'] = inputs['builder_a_hand']; inputs['builder_b_list'] = inputs['builder_a_list']
    with pytest.raises(ValueError, match='distinct'):
        source.review_markers(inputs, {'phase': 'RW1-marker-review'})
