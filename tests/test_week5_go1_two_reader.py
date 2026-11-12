import json
import numpy as np
import pytest
from runners.drive.cards import week5_go1_two_reader as go
from runners.drive.cards import week5_go1_two_reader_fixture as fixture


def bank():
    rows = fixture.rows()
    allocation = go.core.allocate(rows)
    return rows, allocation, {'tfidf': fixture.scores(allocation, np.arange(60) < 10),
                              'encoder': fixture.scores(allocation, np.arange(60) < 50)}


def test_complete_signed_and_exact_null_cases():
    assert set(fixture.arithmetic()) == {'positive', 'negative', 'exact-null'}


def test_support_is_exact_two_reader_intersection():
    rows, allocation, values = bank()
    values['tfidf'][0] = np.nan
    values['encoder'][1] = np.nan
    result, samples = go.compare(rows, allocation, values)
    assert result['documents'] == 58 and result['context_unsupported_queries'] == 2
    assert len(samples) == 2000 and result['primary_ready']


def test_third_reader_cannot_change_primary_support():
    rows, allocation, values = bank()
    values['language_model'] = np.full_like(values['encoder'], np.nan)
    with pytest.raises(ValueError, match='exactly TFIDF and encoder'):
        go.compare(rows, allocation, values)


def test_below_author_floor_remains_descriptive():
    rows, allocation, values = bank()
    for i, row in enumerate(rows):
        row['author'] = f'author-{i % 7}'
    result, _ = go.compare(rows, allocation, values)
    assert result['outcome'] == 'below floor, descriptive'


def test_no_common_support_is_unsupported():
    rows, allocation, values = bank()
    values['encoder'][:] = np.nan
    result, samples = go.compare(rows, allocation, values)
    assert result['status'] == 'unsupported' and len(samples) == 0


def test_whole_actual_fixture_and_replay(tmp_path):
    assert fixture.execute(tmp_path, {}, {})['no_AT2_dependency']
    assert fixture.verify(tmp_path, {}, {})['verified']
    scored = tmp_path / 'encoder/output/SCORED.json'
    value = json.loads(scored.read_text('utf8'))
    value['reader'] = 'language_model'
    go.io.write_json(scored, value)
    rows, allocation = go.original.prepared_rows({'documents': str(tmp_path / 'documents.json')}, {})
    with pytest.raises(ValueError, match='identity differs'):
        go.bank(scored.parent, 'encoder', rows, allocation)


def test_unfinished_bank_refused(tmp_path):
    root = tmp_path / 'bank'
    go.io.write_json(root / 'COMPLETE.json', {'status': 'RUNNING'})
    go.io.write_json(root / 'VERIFIED.json', {'verified': False})
    go.io.write_json(root / 'PLAN.json', {})
    with pytest.raises(ValueError, match='independently verified'):
        go.bank(root / 'output', 'encoder', [], [])


def test_lm_scoring_is_not_silently_enabled(tmp_path):
    with pytest.raises(ValueError, match='no language-model'):
        go.execute(tmp_path, {}, {'phase': 'GO1-score', 'reader': 'language_model'})


@pytest.mark.parametrize('draws', [1, 199, 1999])
def test_unregistered_draw_counts_refused(draws):
    rows, allocation, values = bank()
    with pytest.raises(ValueError, match='draw count'):
        go.compare(rows, allocation, values, draws)
