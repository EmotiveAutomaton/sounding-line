import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from runners.drive.cards.timing_census import read, write, filehash
from runners.drive.cards.timing_stopping import CONFIG, execute, verify, summarize, extract
from runners.drive.timeline import rebuild


def stopping_inputs(root, direction=1, durations=None):
    """Real serialized P2: prompt text must never contribute stopping length."""
    root = Path(root).resolve()
    foundation = root / "foundation"
    index, metadata = [], []
    for writer in range(20):
        x = 100 + 10 * writer
        y = 2 * x + 20 if direction == 1 else 500 - x if direction == -1 else 100 + (2 * writer - 19) ** 2
        for session in range(4 if durations is None else len(durations)):
            identity = f"w{writer:02d}s{session:02d}"
            words = x if session % 2 == 0 else y
            duration = 700 + session if durations is None else durations[session]
            events = [dict(eventName="system-initialize", eventSource="api", eventTimestamp=1000,
                           currentDoc="prompt words stay excluded\n"),
                      dict(eventName="text-insert", eventSource="user", eventTimestamp=2000,
                           textDelta=dict(ops=[dict(retain=26), dict(insert=" " + "word " * words)])),
                      dict(eventName="system-finish", eventSource="user", eventTimestamp=1000 + duration * 1000)]
            timeline = rebuild(events, [])
            raw = root / "raw" / (identity + ".jsonl")
            raw.parent.mkdir(parents=True, exist_ok=True)
            raw.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8", newline="\n")
            timeline.update(session=identity, writer=str(writer), prompt="prompt", source_sha256=filehash(raw))
            path = foundation / "sessions" / (identity + ".json")
            write(path, timeline)
            index.append(dict(session=identity, writer=str(writer), file=path.relative_to(foundation).as_posix(), sha256=filehash(path)))
            metadata.append(dict(session=identity, writer=str(writer), prompt="prompt", timestamp=session,
                                 path=raw.relative_to(root).as_posix(), source_sha256=filehash(raw)))
    side = root / "prepared_sessions.json"
    write(side, metadata)
    write(foundation / "SESSION_INDEX.json", index)
    write(foundation / "PLAN.json", dict(pins={side.relative_to(root).as_posix(): filehash(side)}))
    write(foundation / "COMPLETE.json", dict(status="COMPLETE", plan_sha256=filehash(foundation / "PLAN.json"),
          outputs={"SESSION_INDEX.json": filehash(foundation / "SESSION_INDEX.json")}))
    return dict(repo_root=str(root), prepared_sessions=str(side), session_index=str(foundation / "SESSION_INDEX.json"),
                foundation_complete=str(foundation / "COMPLETE.json"), foundation_plan=str(foundation / "PLAN.json"))


def fresh_verify(tmp_path, module, output, inputs, config, primary):
    manifest = tmp_path / "verification.json"
    write(manifest, dict(output=str(output), inputs=inputs, config=config))
    code = f"import json,sys; from pathlib import Path; from {module} import verify; x=json.load(open(sys.argv[1])); print(json.dumps(verify(Path(x['output']),x['inputs'],x['config'])))"
    child = subprocess.run([sys.executable, "-c", code, str(manifest)], text=True, capture_output=True, timeout=60,
                           env=dict(os.environ, PYTHONHASHSEED="431"), creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name == "nt" else 0)
    assert child.returncode == 0, child.stderr
    assert json.loads(child.stdout)["primary"] == primary


@pytest.mark.parametrize("direction,state", [(1, "positive"), (0, "null"), (-1, "negative")])
def test_serialized_known_answer_and_fresh_process(tmp_path, direction, state):
    inputs = stopping_inputs(tmp_path / "source", direction)
    output = tmp_path / "run"
    result = execute(output, inputs, CONFIG)
    assert result["state"] == state
    assert result["effect"] == pytest.approx(direction, abs=1e-14)
    assert read(output / "STOPPING_ROWS.json")[0]["words"] == 100
    assert result["writers"] == 20
    assert result["bootstrap_draws"] == 2000
    assert verify(output, inputs, CONFIG)["verified"]
    assert execute(output, inputs, CONFIG) == result
    fresh_verify(tmp_path, "runners.drive.cards.timing_stopping", output, inputs, CONFIG, result)
    assert read(output / "FIRST_TENTH.json")["includes_fresh_source_verification"]


def test_writer_pairs_chronology_and_uncertainty():
    rows = []
    for w in range(20):
        for j in range(4):
            rows.append(dict(writer=str(w), session=f"{w}-{j}", timestamp=j, words=100 + 3*w + j*j + (w%3)*j, duration_seconds=700))
    primary, details = summarize(list(reversed(rows)), CONFIG)
    pairs = details["writer_pairs"]
    x, y = np.array([p["odd_mean"] for p in pairs]), np.array([p["even_mean"] for p in pairs])
    assert pairs[0]["odd_sessions"] == ["0-0", "0-2"]
    rng = np.random.default_rng(CONFIG["seed"])
    samples = []
    for _ in range(2000):
        chosen = rng.integers(0, 20, 20)
        samples.append(np.corrcoef(x[chosen], y[chosen])[0, 1])
    assert primary["ci_low"] == pytest.approx(np.quantile(samples, .025), abs=1e-12)
    assert primary["bootstrap_se"] == pytest.approx(np.std(samples, ddof=1), abs=1e-12)
    assert primary["controls"]["even_half_writer_identity_shuffle"]["effect"] != primary["effect"]
    rows[1]["timestamp"] = 0
    altered, detail = summarize(rows, CONFIG)
    assert altered["excluded_writers"] == 1
    assert detail["excluded_writers"][0]["reason"] == "tied session start times"
    assert sum(detail["word_residues_100"]) == len(rows)


def test_invalid_and_exact_config(tmp_path):
    assert summarize([], CONFIG)[0]["state"] == "invalid"
    rows = [dict(writer=str(w), session=f"{w}-{j}", timestamp=j, words=100, duration_seconds=700) for w in range(20) for j in range(2)]
    assert summarize(rows, CONFIG)[0]["state"] == "invalid"
    with pytest.raises(ValueError, match="configuration"):
        execute(tmp_path, {}, dict(CONFIG, extension=0))


def test_resume_and_source_authentication(tmp_path):
    inputs = stopping_inputs(tmp_path / "source")
    output = tmp_path / "run"
    write(output / "YIELD_REQUEST.json", {})
    assert execute(output, inputs, CONFIG)["status"] == "yielded"
    saved = next((output / "sessions").glob("*.json"))
    saved_hash = filehash(saved)
    (output / "YIELD_REQUEST.json").unlink()
    assert execute(output, inputs, CONFIG)["state"] == "positive"
    assert filehash(saved) == saved_hash
    rows = read(output / "STOPPING_ROWS.json")
    rows[0]["words"] += 1
    (output / "STOPPING_ROWS.json").write_text(json.dumps(rows), encoding="utf-8")
    binding = read(output / "TIMING_BINDINGS.json")
    binding["outputs"]["STOPPING_ROWS.json"] = filehash(output / "STOPPING_ROWS.json")
    (output / "TIMING_BINDINGS.json").write_text(json.dumps(binding), encoding="utf-8")
    with pytest.raises(ValueError, match="reconstruct from authenticated"):
        verify(output, inputs, CONFIG)
    side = Path(inputs["prepared_sessions"])
    side.write_text(side.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(ValueError, match="metadata source changed"):
        extract(inputs)


def test_projection_yield_and_cap(tmp_path):
    inputs = stopping_inputs(tmp_path / "source")
    output = tmp_path / "run"
    from runners.drive.cards.timing_events import CooperativeYield
    with pytest.raises(CooperativeYield):
        extract(inputs, output, lambda: 100.)
    assert read(output / "FIRST_TENTH.json")["forecast_overshoot"]
    with pytest.raises(RuntimeError, match="threefold"):
        extract(inputs, tmp_path / "cap", lambda: 1801.)
