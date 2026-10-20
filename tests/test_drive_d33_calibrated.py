"""Support-only selection and exact production-handler known-answer replay."""
from copy import deepcopy
from pathlib import Path
import pytest

from runners.drive.cards import timing_d33_calibrated as card
from runners.drive.cards.timing_d33_supported_counts import copied
from runners.drive.cards.timing_p6 import write_equal
from runners.drive.cards.timing_census import read
from tests.test_drive_cards_timing_d33_supported import make_design


def fixture():
    rows = make_design()
    writers = {}
    for writer in sorted({r['writer'] for r in rows}):
        writers[writer] = dict(calibration_keys=[] if writer == '5' else [[writer+'_cal', 0]],
            calibration_words=0 if writer == '5' else 1, original_calibration_words=1,
            supported_sessions=dict(calibration=[] if writer == '5' else [writer+'_cal'], evaluation=['w'+writer+'_s']),
            unsupported_sessions=dict(calibration=[writer+'_cal'] if writer == '5' else [], evaluation=[]),
            retained_evaluation_words=32, unsupported_evaluation_words=0,
            original_alpha=.5, calibration_available=writer != '5')
    roster = dict(writers=writers, retained_keys=[[r['session'], r['index']] for r in rows],
                  unsupported_keys=[], coverage=dict(original_words=len(rows), original_writers=6,
                  retained_words=len(rows), unsupported_words=0, retained_writers=6,
                  retained_calibration_words=5, unsupported_calibration_words=1))
    return rows, roster


def fixture_prepared(output, inputs, config, verifying=False):
    if config != card.CONFIG: raise ValueError('fixture config changed')
    rows, old = fixture()
    roster = card.select_population(old, dict(rows=rows))
    keys = {tuple(k) for k in roster['retained_keys']}
    kept = [r for r in rows if (r['session'], r['index']) in keys]
    if verifying:
        if read(output/'SUPPORTED_ROSTER.json') != roster: raise ValueError('fixture roster changed')
    else: write_equal(output/'SUPPORTED_ROSTER.json', roster)
    tuning = {w: dict(valid=w != '5') for w in old['writers']}
    cov = {'constructed': dict(words={str(i): dict(in_prompt=0, in_visible_text=0,
        in_previous_shown_suggestion=0, on_screen=r['on_screen']) for i, r in enumerate(kept)})}
    return kept, roster, tuning, cov


def execute(output, inputs, config):
    """Native constructed handler uses the exact production inference and files."""
    result = copied(card.execute, prepared=fixture_prepared)(Path(output), inputs, config)
    if result['primary']['state'] != 'positive' or result['coverage']['retained_writers'] != 5:
        raise ValueError('native planted effect or support selection failed')
    if result['statistics']['primary']['own_minus_donor']['state'] != 'positive':
        raise ValueError('native joint donor comparison failed')
    return dict(instrument_only=True, known_answer_passed=True, result=result)


def verify(output, inputs, config):
    return copied(card.verify, prepared=fixture_prepared)(Path(output), inputs, config)


def test_selection_is_outcome_blind_and_preserves_original():
    rows, old = fixture(); before = deepcopy(old)
    selected = card.select_population(old, dict(rows=rows))
    for row in rows: row['log_pause'] = -1e99; row['own_surprise'] = 1e88
    assert card.select_population(old, dict(rows=rows)) == selected
    assert old == before
    assert selected['coverage']['retained_words'] == 160
    assert selected['coverage']['calibration_unsupported_words'] == 32
    assert selected['coverage']['retained_writers'] == 5
    assert selected['coverage']['unsupported_sessions']['evaluation'] == 1


def test_original_history_gaps_remain_distinct_and_partition_every_row():
    rows, old = fixture(); missing = old['retained_keys'].pop(0); old['unsupported_keys'].append(missing)
    old['writers']['0']['retained_evaluation_words'] -= 1
    old['writers']['0']['unsupported_evaluation_words'] += 1
    selected = card.select_population(old, dict(rows=rows))
    assert selected['coverage']['unsupported_words'] == 33
    assert selected['coverage']['calibration_unsupported_words'] == 32
    assert missing not in selected['calibration_unsupported_keys']
    assert set(map(tuple, selected['retained_keys'])).isdisjoint(map(tuple, selected['unsupported_keys']))
    assert len(selected['retained_keys'])+len(selected['unsupported_keys']) == len(rows)


@pytest.mark.parametrize('defect', ['duplicate', 'missing'])
def test_invalid_original_partition_refuses(defect):
    rows, old = fixture()
    if defect == 'duplicate': old['retained_keys'].append(old['retained_keys'][0])
    else: old['retained_keys'].pop()
    with pytest.raises(ValueError, match='exact partition'): card.select_population(old, dict(rows=rows))


def test_empty_calibration_never_gets_imputed():
    rows, old = fixture()
    for part in old['writers'].values(): part['calibration_keys'] = []
    selected = card.select_population(old, dict(rows=rows))
    assert selected['retained_keys'] == []
    assert len(selected['unsupported_keys']) == len(rows)


def test_production_input_and_config_are_strict():
    with pytest.raises(ValueError, match='exact calibration'): card.load_source({}, card.CONFIG)
    with pytest.raises(ValueError, match='exact calibration'):
        card.load_source(dict(prior_completion='', prior_receipt=''), dict(card.CONFIG, bootstrap_draws=20))
