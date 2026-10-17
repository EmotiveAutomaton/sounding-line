import math
import json
from pathlib import Path
import pytest
from runners.drive.cards import timing_p6 as original
from runners.drive.cards import timing_p6_recovery as recovery
from runners.drive.cards.timing_census import write, filehash


def fixture(tmp_path):
    output = tmp_path / "original/output"
    words = [dict(population_probability=.1, population_surprisal=-math.log(.1)) for _ in range(1001)]
    sequential = 0.
    for word in words:
        sequential += word["population_surprisal"]
    assert sequential != sum(w["population_surprisal"] for w in words)
    original.gzwrite(output / "scores/s.json.gz", dict(words=words))
    index = [dict(session="s", writer="w", file="scores/s.json.gz", sha256=filehash(output / "scores/s.json.gz"),
                  word_count=len(words), scored_count=len(words), total_nll=sequential)]
    write(output / "P6_INDEX.json", index)
    write(output / "P6_PRIMARY.json", original.summary(index))
    write(output / "P6_BINDINGS.json", dict(config={}, inputs={}, repo_root=str(tmp_path.resolve()),
                                           index_sha256=filehash(output / "P6_INDEX.json")))
    write(output.parent / "PLAN.json", dict(module="runners.drive.cards.timing_p6", config={}, pins={},
                                            inputs=dict(repo_root=str(tmp_path))))
    write(output.parent / "FAILED.json", dict(status="FAILED", error="verify child exited 1"))
    write(tmp_path / "diagnosis.json", dict(native_ended=True, sequential_reductions_exact=True,
                                          failure_sha256=filehash(output.parent / "FAILED.json")))
    inputs = dict(original_plan=str(output.parent / "PLAN.json"), original_failure=str(output.parent / "FAILED.json"),
                  diagnosis=str(tmp_path / "diagnosis.json"))
    return output, inputs


def test_real_arithmetic_difference_replays_exactly_and_reentry_preserves_bytes(tmp_path):
    source, inputs = fixture(tmp_path)
    dest = tmp_path / "recovery"
    result = recovery.execute(dest, inputs, {})
    before = {p.relative_to(dest): filehash(p) for p in dest.rglob("*") if p.is_file()}
    assert recovery.verify(dest, inputs, {})["primary"] == result
    assert recovery.execute(dest, inputs, {}) == result
    assert before == {p.relative_to(dest): filehash(p) for p in dest.rglob("*") if p.is_file()}
    assert filehash(source / "scores/s.json.gz") == filehash(dest / "scores/s.json.gz")


def test_changed_score_and_changed_total_still_fail(tmp_path):
    source, inputs = fixture(tmp_path)
    dest = tmp_path / "recovery"
    recovery.execute(dest, inputs, {})
    p = dest / "scores/s.json.gz"
    p.write_bytes(p.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="evidence changed"):
        recovery.verify(dest, inputs, {})
    index = original.read(source / "P6_INDEX.json")
    index[0]["total_nll"] += 1e-10
    (source / "P6_INDEX.json").write_text(json.dumps(index), encoding="utf8")
    with pytest.raises(ValueError, match="exact sequential"):
        recovery.replay_scores(source)


def test_wrong_attempt_and_changed_failure_refused(tmp_path):
    _, inputs = fixture(tmp_path)
    write(tmp_path / "wrong.json", dict(status="FAILED", error="verify child exited 1"))
    with pytest.raises(ValueError, match="another attempt"):
        recovery.source_binding(dict(inputs, original_failure=str(tmp_path / "wrong.json")), {})
    Path(inputs["original_failure"]).write_text(json.dumps(dict(status="FAILED", error="verify child exited 1; altered")), encoding="utf8")
    with pytest.raises(ValueError, match="diagnosis binding"):
        recovery.source_binding(inputs, {})
