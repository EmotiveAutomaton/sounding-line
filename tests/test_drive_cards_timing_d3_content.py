import json
import math
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from runners.drive.cards import timing_d3_content as card
from runners.drive.cards.timing_census import read, write, filehash
from runners.drive.timeline import rebuild


def fixture_inputs(root, direction):
    root = Path(root).resolve()
    index, roster, sessions, content = [], [], [], []
    foundation = root / "foundation"
    for writer in range(10):
        identity, clock, document = str(writer), 0, "abcd \n"
        events, menus, prepared = [], [], []
        def event(name, source="user", delay=1, **kwargs):
            nonlocal clock
            clock += delay
            events.append(dict(eventName=name, eventSource=source, eventTimestamp=clock*1000, **kwargs))
        event("system-initialize", "api", currentDoc=document)
        for i in range(20):
            event("suggestion-open")
            ordinal = len(events)-1
            key = f"{writer}-{i}"
            prepared.append(dict(key=key, session=identity, writer=str(writer), ordinal=ordinal, document=document, menu=["abcd "], inserted="abcd "))
            content.append(dict(key=key, session=identity, writer=str(writer), cosine=[.5], scalars=[[5, 1, 0., 0]]))
            event("suggestion-select", delay=i+1)
            event("text-insert", "api", textDelta=dict(ops=[dict(retain=len(document)-1), dict(insert="abcd ")]))
            document = document[:-1] + "abcd \n"
            reversed_ = i < 4 if direction == 1 else 8 <= i < 12 if direction == -1 else False
            if reversed_:
                event("text-delete", textDelta=dict(ops=[dict(retain=len(document)-6), dict(delete=5)]))
                document = document[:-6] + "\n"
            menus.append(dict(key=key, ordinal=ordinal, end_ordinal=len(events), handling="edit" if reversed_ else "accept", menu=["abcd "]))
        raw = root / "raw" / (identity + ".jsonl")
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_text(''.join(json.dumps(e)+'\n' for e in events), encoding="utf-8", newline="\n")
        timeline = rebuild(events, menus)
        timeline.update(session=identity, writer=str(writer), prompt="p", source_sha256=filehash(raw))
        path = foundation / "sessions" / (identity + ".json")
        write(path, timeline)
        index.append(dict(session=identity, writer=str(writer), file=path.relative_to(foundation).as_posix(), sha256=filehash(path)))
        roster.append(dict(session=identity, writer=str(writer), prompt="p", source_sha256=filehash(raw), path=raw.relative_to(root).as_posix()))
        sessions.append(dict(session=identity, writer=str(writer), prompt="p", timestamp=0, rows=prepared))
    raw_roster, metadata = root / "ROSTER.json", root / "SESSIONS.json"
    write(raw_roster, roster); write(metadata, sessions)
    write(foundation / "SESSION_INDEX.json", index)
    write(foundation / "PLAN.json", dict(pins={p.relative_to(root).as_posix():filehash(p) for p in [raw_roster, metadata]}))
    write(foundation / "COMPLETE.json", dict(status="COMPLETE", plan_sha256=filehash(foundation / "PLAN.json"), outputs={"SESSION_INDEX.json":filehash(foundation / "SESSION_INDEX.json")}))
    content_root = root / "content"
    write(content_root / "PLAN.json", dict(pins={metadata.relative_to(root).as_posix():filehash(metadata)}))
    write(content_root / "RECORDS.json", content)
    write(content_root / "COMPLETE.json", dict(status="COMPLETE", outputs={p.name:filehash(p) for p in content_root.glob("*.json")}))
    return dict(repo_root=str(root), raw_roster=str(raw_roster), prepared_sessions=str(metadata),
                foundation_plan=str(foundation / "PLAN.json"), foundation_complete=str(foundation / "COMPLETE.json"),
                session_index=str(foundation / "SESSION_INDEX.json"), content_complete=str(content_root / "COMPLETE.json"))


@pytest.mark.parametrize("direction,state", [(1, "positive"), (0, "null"), (-1, "negative")])
def test_actual_serialized_adjusted_curve_and_fresh_process(tmp_path, direction, state):
    inputs = fixture_inputs(tmp_path / "source", direction)
    output = tmp_path / "output"
    result = card.execute(output, inputs, card.CONFIG)
    assert result["state"] == state
    assert result["ladder_update"] is False
    assert result["observations"] == 200
    assert "<polyline" in (output / "LATENCY_CURVE.svg").read_text()
    assert len(read(output / "CONTENT_DETAILS.json")["bootstrap_coefficients"]) == 2000
    manifest = tmp_path / "verify.json"
    write(manifest, dict(output=str(output), inputs=inputs, config=card.CONFIG))
    code = "import json,sys; from pathlib import Path; from runners.drive.cards.timing_d3_content import verify; x=json.load(open(sys.argv[1])); print(json.dumps(verify(Path(x['output']),x['inputs'],x['config'])))"
    child = subprocess.run([sys.executable, "-c", code, str(manifest)], capture_output=True, text=True, timeout=60,
                           env=dict(os.environ, PYTHONHASHSEED="431"), creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name == "nt" else 0)
    assert child.returncode == 0, child.stderr
    assert json.loads(child.stdout)["primary"] == result


def test_joint_coefficients_match_independent_dense_fit():
    rng = np.random.default_rng(421)
    x = rng.normal(size=(240, 6))
    y = -.3*x[:, 0] + .2*x[:, 1] + .1*x[:, 2] + rng.normal(0, .1, 240)
    owners = np.repeat(np.arange(12).astype(str), 20)
    groups = card.sufficient(x, y, owners, within=True)
    a, b = x.copy(), y.copy()
    for owner in sorted(set(owners)):
        ix = owners == owner
        a[ix] -= a[ix].mean(0); b[ix] -= b[ix].mean()
    assert card.coefficients(groups) == pytest.approx(np.linalg.lstsq(a, b, rcond=None)[0], abs=1e-12)
    a[:, 1] = a[:, 0]
    with pytest.raises(ValueError, match="not identifiable"):
        card.coefficients(card.sufficient(a, b, owners, within=True))


def test_resume_and_forged_content_refusal(tmp_path):
    inputs = fixture_inputs(tmp_path / "source", 1)
    output = tmp_path / "output"
    write(output / "YIELD_REQUEST.json", {})
    assert card.execute(output, inputs, card.CONFIG)["status"] == "yielded"
    checkpoint = next((output / "sessions").glob("*.json"))
    retained = checkpoint.read_bytes()
    (output / "YIELD_REQUEST.json").unlink()
    assert card.execute(output, inputs, card.CONFIG)["state"] == "positive"
    assert checkpoint.read_bytes() == retained
    path = Path(inputs["content_complete"]).parent / "RECORDS.json"
    content = read(path); content[0]["scalars"][0][0] += 1
    path.write_text(json.dumps(content), encoding="utf-8")
    complete = read(inputs["content_complete"]); complete["outputs"]["RECORDS.json"] = filehash(path)
    Path(inputs["content_complete"]).write_text(json.dumps(complete), encoding="utf-8")
    with pytest.raises(ValueError, match="do not reconstruct"):
        card.extract(inputs, card.CONFIG)


def test_unsupported_latency_and_exact_config(tmp_path):
    inputs = fixture_inputs(tmp_path / "source", 1)
    rows, exclusions = card.extract(inputs, card.CONFIG)
    for row in rows: row["latency"] = 1.
    assert card.summarize(rows, exclusions, card.CONFIG)[0]["state"] == "invalid"
    with pytest.raises(ValueError, match="configuration"):
        card.extract(inputs, dict(card.CONFIG, seed=True))
