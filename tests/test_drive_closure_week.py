"""Saved-score, unchanged-ruler and single-budget continuation checks."""
import ast
import inspect
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from runners.drive.cards import timing_closure_week as card
from runners.drive.cards import timing_closure_recovery as old
from runners.drive.cards.timing_census import read, write, filehash
from tests import test_drive_cards_timing_closure as fixture
from tests.test_drive_cards_timing_closure_recovery import failed_fixture


def native_inputs(root, direction=1):
    root=Path(root); original_complete=fixture.complete
    def dated_complete(output):
        path=Path(original_complete(output));value=read(path)
        value['at']='2026-10-18T00:00:01+00:00';path.write_text(json.dumps(value),encoding='utf-8')
        write(path.parent/'PLAN.json',dict(at='2026-10-18T00:00:00+00:00'))
        return str(path)
    with pytest.MonkeyPatch.context() as mp,patch.object(fixture,'complete',dated_complete):
        inputs=failed_fixture(root/'fixture',mp,direction)
        paused=root/'paused';write(paused/'output/YIELD_REQUEST.json',dict(reason='synthetic_pause'))
        result=old.execute(paused/'output',inputs,card.CONFIG)
        assert result['status']=='yielded'
        write(paused/'RESULT.json',result)
        write(paused/'PLAN.json',dict(at='2026-10-18T01:01:00+00:00',module=old.__name__,config=card.CONFIG,inputs=inputs,
            pins={str(Path(old.__file__).resolve()):filehash(old.__file__)}))
        write(paused/'PAUSED.json',dict(at='2026-10-18T01:01:02+00:00',status='PAUSED',saved_result_sha256=filehash(paused/'RESULT.json')))
    return dict(paused_plan=str(paused/'PLAN.json'),paused_record=str(paused/'PAUSED.json'))


def execute(output,inputs,config):
    """Native constructed-only adapter; corpus dispatch uses the production module."""
    with patch.object(card.measure,'Encoder',fixture.FixtureEncoder):
        return card.execute(Path(output),inputs,config)


def verify(output,inputs,config):
    with patch.object(card.measure,'Encoder',fixture.FixtureEncoder):
        return card.verify(Path(output),inputs,config)


@pytest.mark.parametrize('direction,state',[(1,'positive'),(0,'null'),(-1,'negative')])
def test_complete_unchanged_known_answers_and_reentry(tmp_path,direction,state):
    inputs=native_inputs(tmp_path,direction);output=tmp_path/'continued'
    source,prior,receipt=card.source(inputs,card.CONFIG)
    assert receipt['charged_prior_seconds']==13
    result=execute(output,inputs,card.CONFIG)
    assert result['state']==state and result['effect']==pytest.approx(.75*direction,abs=1e-10)
    with patch.object(old.measure,'Encoder',fixture.FixtureEncoder):
        original_rows,exclusions=old.score_rows(source,fixture.FixtureEncoder(source))
    expected,details=old.original.summarize(original_rows,card.CONFIG)
    assert result==expected
    assert read(output/'CLOSURE_ROWS.json')==original_rows
    assert read(output/'CLOSURE_DETAILS.json')==details
    assert verify(output,inputs,card.CONFIG)['primary']==result
    assert execute(output,inputs,card.CONFIG)==result
    for name,h in receipt['retained_files'].items():assert filehash(output/name)==h==filehash(prior/name)


def test_changed_checkpoint_and_changed_source_refuse(tmp_path):
    inputs=native_inputs(tmp_path);_,output,identity=card.source(inputs,card.CONFIG)
    name=next(iter(identity['retained_files']));target=output/name;before=target.read_bytes()
    target.write_bytes(before+b' ')
    with pytest.raises(ValueError,match='checkpoint'):card.source(inputs,card.CONFIG)
    target.write_bytes(before)
    plan=read(Path(inputs['paused_plan']));plan['pins'][str(Path(old.__file__).resolve())]='0'*64
    Path(inputs['paused_plan']).write_text(json.dumps(plan),encoding='utf-8')
    with pytest.raises(ValueError,match='pin changed'):card.source(inputs,card.CONFIG)


def test_budget_charges_pilot_and_both_prior_attempts_once(tmp_path):
    inputs=native_inputs(tmp_path);_,_,identity=card.source(inputs,card.CONFIG)
    assert identity['pilot_seconds']==1 and identity['prior_attempt_seconds']==12
    assert identity['original_cap_seconds']==2700 and identity['single_S4_cap_seconds']==5400
    p=Path(inputs['paused_record']);record=read(p);record['at']='2026-10-18T03:01:00+00:00';p.write_text(json.dumps(record),encoding='utf-8')
    with pytest.raises(ValueError,match='allowance exhausted'):card.source(inputs,card.CONFIG)


def test_resource_yield_and_resume_keep_original_bytes(tmp_path):
    inputs=native_inputs(tmp_path);output=tmp_path/'continued'
    write(output/'YIELD_REQUEST.json',dict(reason='resource_floor_yield'))
    assert execute(output,inputs,card.CONFIG)['status']=='yielded'
    first={p.name:p.read_bytes() for p in (output/'sessions').glob('*.json')}
    (output/'YIELD_REQUEST.json').unlink()
    assert execute(output,inputs,card.CONFIG)['state']=='positive'
    assert all((output/'sessions'/name).read_bytes()==value for name,value in first.items())
    assert verify(output,inputs,card.CONFIG)['verified']


def test_cap_saves_unit_then_yields_without_score_changes(tmp_path):
    inputs=native_inputs(tmp_path);source,_,_=card.source(inputs,card.CONFIG);output=tmp_path/'limit'
    with pytest.raises(card.CooperativeYield):
        card.score_rows(source,fixture.FixtureEncoder(source),output,lambda:5400.1)
    assert read(output/'YIELD_REQUEST.json')['reason']=='single_S4_cumulative_ceiling'
    assert len(list((output/'sessions').glob('*.receipt.json')))==1
    assert read(output/'CLOSURE_PROGRESS.json')['active_seconds']==5400.1


def test_scoring_function_changes_only_operational_budget():
    a=inspect.getsource(old.score_rows)
    a=a.replace('''            if active > 3 * FORECAST_SECONDS:
                raise RuntimeError("D24 threefold active-time ceiling")''','''            if active > CAP_SECONDS:
                atomic(output / "YIELD_REQUEST.json", dict(reason="single_S4_cumulative_ceiling"))
                raise CooperativeYield("saved source-bound session at cumulative allowance")''')
    a=a.replace('if overshoot or (output / "YIELD_REQUEST.json").exists():','if (output / "YIELD_REQUEST.json").exists():')
    assert ast.dump(ast.parse(a))==ast.dump(ast.parse(inspect.getsource(card.score_rows)))
