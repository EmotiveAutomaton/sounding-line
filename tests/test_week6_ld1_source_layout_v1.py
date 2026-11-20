"""Known-answer literal OpenESM layout, with no source observations."""
import hashlib

import numpy as np
import pandas as pd
import pytest

from runners.drive.cards import week6_ld12_common_v1 as core
from runners.drive.cards import week6_lattice_source_v1 as source


@pytest.mark.parametrize("member", ["0056", "0057"])
def test_original_activity_names_and_clock_fields_are_not_interchangeable(tmp_path, member):
    canonical = source.columns(member, "LD3")
    originals = {"occup_" + name: name for name in source.ACTIVITY}
    valid = {originals.get(k, k): "3" for k in canonical}
    valid.update(day="1", id="solitary", interaction="2", bored="5",
                 created_esm="2026-02-12T10:45:00Z", ended_esm="2026-02-12T10:50:00Z",
                 communication="", type_interaction="")
    other = dict(valid, id="company", interaction="1", type_interaction="3", communication="2")
    path = tmp_path / "constructed.tsv"
    pd.DataFrame([valid, other]).to_csv(path, sep="\t", index=False)
    pin = dict(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    data = core.source_projection(member, path, pin, [""], lambda: None, "LD3")
    assert data.people == 2 and data.units.tolist() == [1] and data.ordinals.tolist() == [0]
    assert data.values["bored"].tolist() == [5.]
    assert set(source.ACTIVITY) <= data.values.keys()
    frames = list(core.next_prompt_frames(member, path, pin, [""], lambda: None))
    assert len(frames) == 1 and frames[0]["occup_bored"].tolist() == ["5", "5"]
    assert frames[0]["type_interaction"].tolist() == ["", "3"]
    assert frames[0]["communication"].tolist() == ["", "2"]
    assert set(frames[0].columns) == {"id", "day", "created_esm", "ended_esm", "interaction",
                                     "occup_bored", "type_interaction", "communication"}
    assert core.COMMUNICATION_LABELS[2] == "via phone/chat"
    assert core.INTERACTION_TYPE_LABELS[3] == "leisure activity"
    frame = pd.DataFrame([valid, other]).rename(columns={"bored": "occup_bored"})
    frame.to_csv(path, sep="\t", index=False)
    changed = dict(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    with pytest.raises(ValueError):
        core.source_projection(member, path, changed, [""], lambda: None, "LD3")
