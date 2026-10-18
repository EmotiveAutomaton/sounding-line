"""Actual serialized pilot, complete receipt, byte reuse and fresh refit."""
from pathlib import Path
import pytest

from runners.drive.cards import menus_v4_split_admitted as m
from runners.drive.cards.menus_io import read,write,sha256
from tests.test_drive_cards_menus_v4_saved_diagnostics import fixture


def test_sealed_pilot_reuse_and_source_refusal(tmp_path):
    inputs,_=fixture(tmp_path/"source")
    config=dict(m.core.FIXTURE_CONFIG,mode="fixture_pilot")
    pilot=tmp_path/"pilot";output=pilot/"output"
    pilot.mkdir()
    write(pilot/"PLAN.json",dict(module="runners.drive.cards.menus_v4_split_admitted",inputs=inputs,config=config,
        pins={str(Path(m.__file__).resolve()):sha256(m.__file__)},synthetic_fixture_only=True))
    initial=m.execute(output,inputs,config)
    assert initial["execution_only"] and initial["primary"] is None and initial["synthetic_fixture_only"]
    assert len(initial["worlds"])==1
    assert m.execute(output,inputs,config)==initial
    assert m.verify(output,inputs,config)["verified"]
    write(pilot/"COMPLETE.json",dict(status="COMPLETE",fresh_process_verified=True,synthetic_fixture_only=True,
        outputs={p.relative_to(pilot).as_posix():sha256(p) for p in pilot.rglob("*") if p.is_file()}))
    full_inputs=dict(inputs,pilot_plan=str(pilot/"PLAN.json"),pilot_complete=str(pilot/"COMPLETE.json"),pilot_summary=str(output/"SUMMARY.json"))
    full=tmp_path/"full";full_config=dict(config,mode="fixture_full")
    result=m.execute(full,full_inputs,full_config)
    assert result["world_count"]==1 and result["primary"] is None
    assert m.execute(full,full_inputs,full_config)==result
    assert m.verify(full,full_inputs,full_config)["verified"]
    receipt=read(full/"PILOT_REUSE.json")
    assert receipt["byte_exact"]
    for name in receipt["copied"]:
        assert (full/name).read_bytes()==(output/name).read_bytes()
    path=output/"worlds/taste_matched-0.4-0.json"
    path.write_text(path.read_text()+" ",encoding="utf8")
    with pytest.raises(ValueError,match="checkpoint changed"):
        m.execute(full,full_inputs,full_config)
