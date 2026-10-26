import copy
import json
import subprocess
import sys

import pytest

from runners.drive.cards import week3_alignment_values_inputs as original
from runners.drive.cards import week3_alignment_values_supported as card
from runners.stage14.common import atomic, filehash, freeze, read
from tests.test_week3_alignment_values_inputs import fixture_chain


def config(fixed=4, supported=1):
    return dict(variant=card.VARIANT, expected_fixed_annotators=fixed,
                expected_supported_annotators=supported)


def census():
    rows = []
    for i, (fit, target) in enumerate([(True, True), (False, True), (True, False), (False, False)]):
        reasons = ([] if fit else ['no-comparisons-without-explanations'])
        reasons += [] if target else ['no-sampled-explanation-targets']
        rows.append(dict(writer=chr(97+i), fit_indices=[i*2] if fit else [],
                         targets=[dict(comparison_index=i*2+1, item_id=str(i))] if target else [],
                         support='unsupported-inputs' if reasons else 'pending-value-labels-and-model-fit',
                         unsupported_reasons=reasons))
    return rows


def test_all_missingness_classes_keep_original_rows_and_reasons():
    rows = census(); before = copy.deepcopy(rows)
    selected, membership = card.select(rows, config())
    assert rows == before and selected == [rows[0]]
    assert [r['included'] for r in membership] == [True, False, False, False]
    assert membership[-1]['unsupported_reasons'] == [
        'no-comparisons-without-explanations', 'no-sampled-explanation-targets']


def test_unsupported_flag_cannot_hide_fit_target_overlap():
    rows = census(); rows[0]['fit_indices'] = [1]
    with pytest.raises(ValueError, match='overlapping'):
        card.select(rows, config())
    rows = census(); rows[1]['unsupported_reasons'] = []
    with pytest.raises(ValueError, match='disposition'):
        card.select(rows, config())


def test_changed_population_or_scope_refuses():
    for cfg in [config(5, 1), config(4, 2), dict(config(), variant='CA3')]:
        with pytest.raises(ValueError):
            card.select(census(), cfg)
    rows = census(); rows[1]['writer'] = 'a'
    with pytest.raises(ValueError, match='order'):
        card.select(rows, config())


def supported_fixture(root):
    inputs = fixture_chain(root/'sources')
    out = root/'original/output'; original.execute(out, inputs, {})
    assert original.verify(out, inputs, {})['verified']
    freeze(out.parent/'COMPLETE.json', dict(status='COMPLETE', fresh_process_verified=True,
        outputs={'output/SUMMARY.json': filehash(out/'SUMMARY.json')}))
    inputs.update(partition_summary=str(out/'SUMMARY.json'),
                  partition_complete=str(out.parent/'COMPLETE.json'))
    return inputs


def test_complete_reentry_fresh_process_and_output_mutation(tmp_path):
    inputs = supported_fixture(tmp_path/'input'); out = tmp_path/'out'; cfg = config(30, 30)
    summary = card.execute(out, inputs, cfg)
    assert summary['fixed_annotators'] == summary['supported_annotators'] == 30
    assert not summary['scientific_admission'] and not summary['downstream_admission']
    assert card.execute(out, inputs, cfg) == summary
    script = ('import json; from runners.drive.cards.week3_alignment_values_supported import verify; '
              'assert verify(*json.loads(__import__("sys").argv[1]))["verified"]')
    subprocess.run([sys.executable, '-B', '-c', script, json.dumps([str(out), inputs, cfg])],
                   check=True, timeout=60, capture_output=True)
    changed = read(out/'PRIVATE_SUPPORTED_REFIT_TARGETS.json'); changed.pop()
    atomic(out/'PRIVATE_SUPPORTED_REFIT_TARGETS.json', changed)
    with pytest.raises(ValueError, match='payload differs'):
        card.verify(out, inputs, cfg)


def test_resealed_false_original_partition_refuses_raw_replay(tmp_path):
    inputs = supported_fixture(tmp_path/'input'); path = __import__('pathlib').Path(inputs['partition_summary'])
    rows = read(path.parent/'PRIVATE_REFIT_TARGETS.json'); rows[0]['fit_indices'].pop()
    atomic(path.parent/'PRIVATE_REFIT_TARGETS.json', rows)
    summary = read(path); summary['output_hashes']['PRIVATE_REFIT_TARGETS.json'] = filehash(path.parent/'PRIVATE_REFIT_TARGETS.json')
    atomic(path, summary)
    complete = read(inputs['partition_complete']); complete['outputs']['output/SUMMARY.json'] = filehash(path)
    atomic(inputs['partition_complete'], complete)
    with pytest.raises(ValueError, match='partition reconstruction'):
        card.execute(tmp_path/'out', inputs, config(30, 30))
