import json
import os
import subprocess
import sys

import pytest

from runners.stage12.revision_replay import canonical_primary


def fixture_rows(effect):
    return [dict(unit=f'u{i}', cluster=f'c{i}', method=method, frame=frame,
                 mode=mode, update='diagnostic',
                 excess_half_brier=effect if frame == 'false' and mode == 'saved' else 0.)
            for i in range(8) for method in ('account', 'direct')
            for frame in ('false', 'true') for mode in ('saved', 'fresh')]


@pytest.mark.parametrize('effect,expected', [(0., 'EQUIVALENT'), (.1, 'HARM'), (-.1, 'BENEFIT')])
def test_known_answer(effect, expected):
    result = canonical_primary(fixture_rows(effect))
    assert result['mean'] == pytest.approx(effect)
    assert result['low'] == pytest.approx(effect)
    assert result['high'] == pytest.approx(effect)
    assert result['disposition'] == expected


def test_missing_and_duplicate_pairs_refused():
    rows = fixture_rows(.1)
    for broken in (rows[:-1], rows + [rows[0]]):
        with pytest.raises(ValueError):
            canonical_primary(broken)


def test_conflicting_cluster_refused():
    rows = fixture_rows(.1)
    rows[0]['cluster'] = 'different'
    with pytest.raises(ValueError):
        canonical_primary(rows)


def test_independent_process_hash_seed_and_row_order():
    rows = fixture_rows(.1)
    for i, row in enumerate(rows):
        row['excess_half_brier'] += (i % 11) / 100
    expected = canonical_primary(rows)
    assert canonical_primary(list(reversed(rows))) == expected
    code = ('import json,sys; from runners.stage12.revision_replay import canonical_primary; '
            'print(json.dumps(canonical_primary(json.load(sys.stdin)),sort_keys=True))')
    replies = [subprocess.check_output([sys.executable, '-c', code], input=json.dumps(rows),
               text=True, env=dict(os.environ, PYTHONHASHSEED=seed)) for seed in ('1', '987')]
    assert replies[0] == replies[1]
    assert json.loads(replies[0]) == expected
