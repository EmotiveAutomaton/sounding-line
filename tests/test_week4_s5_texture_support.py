import json
import pytest
from runners.drive.cards import week4_s5_texture_support as s
from runners.drive.cards.week4_s5_h1 import extract


def test_known_case_and_exact_support_floor():
    assert all(s.known_checks().values())


def test_gap_threshold_equalities_and_long_breaks():
    for ceiling in (600, 1800, 3600):
        for gap in (ceiling - .001, ceiling, ceiling + .001):
            rows = s.fixture(1, 1)[:2]
            rows[1]['timestamp'] = gap * 1000
            records, audit = extract(rows, ceiling)
            assert len(records) == 1
            assert records[0]['break_gap'] == (gap > ceiling)
            assert audit['long_gaps'] == (gap > ceiling)


def test_project_scoped_authors_do_not_merge():
    rows = s.fixture(2, 30)
    for row in rows:
        row['project'] = row['author']
        row['author'] = 'same-label'
    summary, _, _, projects = s.build(rows)
    assert len(projects) == summary['source_project_scoped_authors'] == 2
    assert summary['variants']['gap-60-minutes']['qualifying_authors'] == 2
    assert all(v['state'] == 'design cannot test' for v in summary['variants'].values())


def test_ambiguous_edges_stay_missing():
    rows = s.fixture(1, 2)
    rows[2]['timestamp'] = rows[1]['timestamp']
    records, audit = extract(rows, 3600)
    assert audit['missing: ambiguous timestamp block'] == 3
    assert len(records) == 1


def test_native_reentry_and_changed_output_refusal(tmp_path):
    config = s.configuration('constructed')
    s.execute(tmp_path, {}, config)
    assert s.verify(tmp_path, {}, config)['complete_source_replay']
    result = json.loads((tmp_path / 'SUMMARY.json').read_text())
    assert not result['scientific_effect_computed'] and len(result['variants']) == 5
    (tmp_path / 'SUMMARY.json').write_text('{}')
    with pytest.raises(ValueError, match='replay'): s.verify(tmp_path, {}, config)


def test_config_and_input_refusal(tmp_path):
    with pytest.raises(ValueError): s.configuration('bad')
    with pytest.raises(ValueError, match='Frozen'): s.execute(tmp_path, {}, dict(s.configuration('constructed'), minimum_authors=5))
    with pytest.raises(ValueError, match='No human'): s.execute(tmp_path, {'source_identity': 'unused'}, s.configuration('constructed'))
