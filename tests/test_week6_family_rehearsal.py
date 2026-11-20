"""Regression checks for the final mounted BF rehearsal and the immutable source pins."""
import json
from pathlib import Path
import sys

import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
SCIENCE=ROOT/"runners/drive/sealed/week6-sm-science"
MI=ROOT/".agent-state/drive-20261115/full-week-extension/mi"
for path in reversed((SCIENCE,ROOT/"runners/drive/cards",MI,MI/"sealed-wrapper-mi4-nullfix-v4",
                       MI/"mi4-v1",MI/"statcore-v1",MI/"statcore-v2")):
    sys.path.insert(0,str(path))
import argument_bank
import argument_panel
import build_family
import daily_fixture
import family_rehearsal


def test_constructed_bf_known_answers():
    fixture = daily_fixture.records()
    exposure = argument_panel.exposure(fixture["diary"])
    values = argument_panel.daily_scores(fixture["diary"])
    data = argument_panel.person_totals(exposure, values)
    counts, expected = family_rehearsal.argument_answers()
    rosters, _ = argument_bank.contributors(data)
    assert counts==len(rosters[1])==len(rosters[3]) and len(rosters[2])==576
    for number in (1,2,3):
        x=np.array([data[p] for p in sorted(rosters[number])])
        w=np.ones(len(x))
        assert argument_bank._scores(x,w,number,False)==pytest.approx(expected[number-1],abs=1e-9)
        assert argument_bank._scores(x,w,number,True)==pytest.approx(expected[number-1],abs=1e-9)


def test_family_packages_are_reproducible_and_reject_a_changed_source(tmp_path):
    edition=json.loads((SCIENCE/"source_map.json").read_text("utf8"))
    source=tmp_path/"source"
    samples=daily_fixture.construct(source,edition)
    path=source/"MANIFEST.json"
    path.write_text(json.dumps(dict(constructed_only=True,private_source_reads=0,people=576,sources=samples)),"utf8")
    first=build_family.build_family(tmp_path/"first",path)
    assert first==build_family.build_family(tmp_path/"second",path)
    assert first["jobs"]["family-mounted-rehearsal"]!=first["jobs"]["family-inside-rehearsal"]
    assert first["jobs"]["midus-m2-joined"]!=first["jobs"]["family-mounted-rehearsal"]
    target=source/samples["M2"]["diary"]["filename"]
    with target.open("r+b") as stream:
        byte=stream.read(1)
        stream.seek(0)
        stream.write(bytes([byte[0]^1]))
    with pytest.raises(ValueError,match="differs"):
        build_family.build_family(tmp_path/"third",path)
