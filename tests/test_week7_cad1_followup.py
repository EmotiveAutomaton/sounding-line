"""Expanded CAD1 with synthetic response codes and an already-released primary."""
import csv
from hashlib import sha256
import subprocess
import sys

import numpy as np

from runners.drive.sealed.week7_cad1_build import package
from tests.test_week7_sealed_pace_purpose import conversation_fixture, gate


def test_expanded_return_after_primary(tmp_path):
    tables = conversation_fixture()
    survey = tables['survey']
    turns = tables['speech']
    rng = np.random.default_rng(472)
    for name, maximum in [('how_enjoyable', 9), ('pre_affect', 9), ('arousal', 9),
                          ('overall_affect', 9), ('i_like_you', 7)]:
        survey[name] = rng.integers(1, maximum + 1, len(survey))
    attention = 'my_partner_paid_attention_to_me'
    raw_codes = [25, 21, 27, 22, 26, 24, 23]
    codes = {code: rank for rank, code in enumerate(raw_codes, 1)} | {-88: None}
    ranks = rng.integers(1, 8, len(survey))
    survey[attention] = [raw_codes[rank-1] for rank in ranks]
    for row, rank in zip(survey.itertuples(), ranks, strict=True):
        mask = ((turns.conversation_id == row.conversation_id) &
                (turns.speaker == row.user_id) & turns.turn_id.isin([1, 2]))
        rate = 1 + .1*row.how_enjoyable + .02*row.arousal + .04*rank
        turns.loc[mask, 'stop'] = turns.loc[mask, 'start'] + 2/rate
    source = tmp_path / 'data'
    source.mkdir()

    def check(label, counts=(48, 12), expected=0):
        pins = {}
        for field, frame in tables.items():
            path = source / (field+'.parquet')
            frame.to_parquet(path, index=False)
            pins[field] = (path.name, path.stat().st_size, sha256(path.read_bytes()).hexdigest())
        job = tmp_path / ('job-'+label)
        package(job, pins, attention_key=codes, published_support=counts)
        out = tmp_path / ('out-'+label)
        out.mkdir()
        result = subprocess.run([sys.executable, '-I', '-B', str(job/'run.py'), str(source), str(out)],
                                capture_output=True)
        assert result.returncode == expected, result.stderr[-500:]
        if expected:
            assert not list(out.iterdir())
        else:
            gate(out)
        return out

    out = check('same')
    with (out/'pace.csv').open() as f:
        row, = csv.DictReader(f)
    assert row['reading'] == '2' and row['n'] == '48'
    assert np.allclose([float(row[k]) for k in ('estimate','lower','upper')], .1)
    check('wrong-roster', counts=(49, 12), expected=25)
    survey.loc[survey.user_id == 'a0', attention] = -88
    blocked = check('one-person-complement')
    assert not (blocked/'pace.csv').exists()
    with (blocked/'support.csv').open() as f:
        assert all(int(r['n']) != 47 for r in csv.DictReader(f))
    survey.loc[0, attention] = 99
    check('unknown-code', expected=24)
