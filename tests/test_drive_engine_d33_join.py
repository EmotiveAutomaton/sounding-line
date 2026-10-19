"""Exact production joins cannot substitute a same-spelling replacement."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from runners.drive.engine_d33_join import join_rows
from runners.drive.engine_occurrences import final_document
from tests.test_drive_engine_occurrences import event


def fixture():
    events = [event(0, doc=''), event(100, [{'insert': 'cat cat '}]),
              event(200, [{'delete': 3}, {'insert': 'cat'}])]
    record = final_document(events, dict(writer='w', session='s', prompt='p'))
    rows = [dict(writer='w', session='s', index=i, length=3,
        personal_surprise=.25, donor_surprise=-.3, population_surprisal=2.,
        log_pause=-.7, log_frequency=-4., sentence_start=0, after_punctuation=1)
        for i in range(3)]
    return rows, [record]


def test_duplicate_spelling_and_original_covariates_preserved():
    rows, records = fixture()
    original = copy.deepcopy(rows)
    result = join_rows(rows, records)
    assert [r['original'] for r in result['rows']] == original == rows
    assert [r['final_codepoints'] for r in result['rows']] == [None, [4,7], [0,3]]
    assert result['support']['dispositions'] == {
        'outside-input-cohort':0, 'not-intact-final-word':1, 'awaiting-engine-score':2}
    assert not result['engine_scored'] and not result['scientific_admission']
    result['rows'][0]['original']['log_pause'] = 9.
    assert rows == original


def test_missing_cohort_session_remains_explicit_and_zero_score_absent():
    rows, records = fixture()
    rows.append(dict(rows[0], session='other'))
    result = join_rows(rows, records)
    assert len(result['rows']) == len(rows)
    assert result['rows'][-1]['disposition'] == 'outside-input-cohort'
    assert result['rows'][-1]['character_ids'] is None
    assert 'departure' not in result['rows'][-1]


@pytest.mark.parametrize('mutation,match', [
    ('duplicate-row','duplicate original'), ('duplicate-session','duplicate input'),
    ('wrong-writer','writer differs'), ('missing-word','word missing'),
    ('nonfinite','nonfinite'), ('length','length differs'),
    ('false-source','typed provenance'), ('false-span','typed provenance'),
    ('changed-text','bytes differ'), ('wrong-support','support differs')])
def test_mutations_refuse(mutation, match):
    rows, records = fixture()
    if mutation == 'duplicate-row': rows.append(copy.deepcopy(rows[0]))
    elif mutation == 'duplicate-session': records.append(copy.deepcopy(records[0]))
    elif mutation == 'wrong-writer': rows[0]['writer'] = 'another'
    elif mutation == 'missing-word': rows[0]['index'] = 999
    elif mutation == 'nonfinite': rows[0]['log_pause'] = float('nan')
    elif mutation == 'length': rows[0]['length'] = 4
    elif mutation == 'false-source': records[0]['document']['provenance'][0]['source'] = 'accepted'
    elif mutation == 'false-span': records[0]['occurrences'][1]['final_codepoints'] = [0,3]
    elif mutation == 'changed-text': records[0]['document']['text'] = 'dog cat '
    elif mutation == 'wrong-support': records[0]['support']['intact_final_words'] = 9
    with pytest.raises(ValueError, match=match): join_rows(rows, records)


def test_unicode_span_is_codepoints_not_utf16_or_bytes():
    events = [event(0, doc='😀 '), event(100, [{'retain':3}, {'insert':'Straße '}])]
    record = final_document(events, dict(writer='w',session='s',prompt='p'))
    rows, _ = fixture()
    result = join_rows([dict(rows[0], length=6)], [record])
    assert result['rows'][0]['final_codepoints'] == [2,8]


def test_fresh_serialized_process_is_identical(tmp_path):
    rows, records = fixture()
    src = tmp_path/'join.json'
    src.write_text(json.dumps(dict(rows=rows, records=records)), encoding='utf8')
    code = ('import json,sys;from runners.drive.engine_d33_join import join_rows;'
            'print(json.dumps(join_rows(**json.load(open(sys.argv[1]))),sort_keys=True))')
    child = subprocess.run([sys.executable, '-B', '-c', code, str(src)],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True,
        timeout=30, env={**os.environ, 'PYTHONHASHSEED':'613'},
        creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name=='nt' else 0)
    assert child.returncode == 0, child.stderr
    assert json.loads(child.stdout) == join_rows(rows, records)
