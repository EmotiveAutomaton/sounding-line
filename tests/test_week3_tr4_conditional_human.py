import copy
import json
from pathlib import Path
import pytest
from runners.drive.cards import week3_tr4_analysis as original
from runners.drive.cards import week3_tr4_comparison as parent
from runners.drive.cards import week3_tr4_conditional as control
from runners.drive.cards import week3_tr4_conditional_human as human
from runners.drive.cards import week3_tr4_conditional_worlds as worlds
from runners.drive.cards.timing_census import filehash


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding='utf8')


def receipt(root, payloads):
    for name, value in payloads.items(): save(root/name, value)
    save(root/'COMPLETE.json', dict(status='COMPLETE', fresh_process_verified=True,
         outputs={name:filehash(root/name) for name in payloads}))
    return str(root/'COMPLETE.json')


def fixture(tmp_path):
    census = original.constructed('uniform')
    census['summary'] = dict(full_population=True)
    source = receipt(tmp_path/'source', {'output/CENSUS.json':census})
    prior, _ = parent.run_analysis(census, 3, 3, 11)
    old = receipt(tmp_path/'parent', {'output/RESULTS.json':prior,
          'output/BINDING.json':dict(inputs=dict(source_completion=filehash(source)))})
    parent_landing = tmp_path/'parent_landing.json'
    save(parent_landing, dict(full_write_through=True,id='S15-TR4-20261027',completion_sha256=filehash(old)))
    cells = [dict(family=f,result=dict(primary=dict(status='positive_conditional_order'
        if f == 'drift_30' else 'not_detected'))) for f, _ in worlds.WORLDS]
    cal = receipt(tmp_path/'cal', {'output/SUMMARY.json':worlds.summarize(cells),
          'output/BINDING.json':dict(config=worlds.CONFIGS['main'], inputs=dict(parent_landing=filehash(parent_landing)))})
    landing = tmp_path/'cal_landing.json'
    save(landing, dict(full_write_through=True,admitted=True,completion_sha256=filehash(cal)))
    return dict(source_completion=source,parent_completion=old,parent_landing=str(parent_landing),
                calibration_completion=cal,calibration_landing=str(landing))


def test_complete_human_handler_reentry_and_corruption(tmp_path):
    inputs = fixture(tmp_path)
    out = tmp_path/'out'
    assert human.execute(out, inputs, human.CONFIG)['status'] == 'complete'
    assert human.verify(out, inputs, human.CONFIG)['primary_and_population_preserved']
    result = json.loads((out/'RESULTS.json').read_text())
    assert result['primary']['status'] == 'unsupported'
    result['primary']['estimate'] = 9
    save(out/'RESULTS.json', result)
    with pytest.raises(ValueError, match='replay'): human.verify(out, inputs, human.CONFIG)


def test_failed_calibration_unlanded_or_changed_source_refuses(tmp_path):
    inputs = fixture(tmp_path)
    original_gate = json.loads(Path(inputs['calibration_landing']).read_text())
    for field in ('full_write_through','admitted'):
        save(Path(inputs['calibration_landing']), dict(original_gate, **{field:False}))
        with pytest.raises(ValueError, match='calibration'): human.load(inputs)
    save(Path(inputs['calibration_landing']), original_gate)
    summary = Path(inputs['calibration_completion']).parent/'output/SUMMARY.json'
    save(summary, dict(calibration_pass=False,gates=dict(all=False)))
    with pytest.raises(ValueError, match='changed'): human.load(inputs)
    with pytest.raises(ValueError, match='bindings'): human.load({})


def test_original_population_and_forecast_changes_refuse():
    census = original.constructed('change')
    prior, _ = parent.run_analysis(census, 3, 3, 11)
    current = control.analyze(census, 3, 11)
    assert human.preserve_parent(current, prior)['primary_and_population_preserved']
    damaged = copy.deepcopy(current)
    damaged['writer_losses'][0]['gain'] += .01
    with pytest.raises(ValueError, match='statistic'): human.preserve_parent(damaged, prior)
    damaged = copy.deepcopy(current)
    damaged['retained'].pop()
    with pytest.raises(ValueError, match='population'): human.preserve_parent(damaged, prior)
