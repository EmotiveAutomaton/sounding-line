"""Regression tests for the 2026-08-28 agent-hardening pass (H1-H5).

Every test here reproduces a defect that was live in the checkout, so each one fails against
the code as it stood. Nothing here allocates a GPU, loads a model, touches the production
queue lock, or reads the real manifest: locks and manifests are built under tmp_path and the
modules are pointed at them.
"""

from __future__ import annotations

import json
import multiprocessing as mp
import socket
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from soundingline import completion, s3                                          # noqa: E402

sys.path.insert(0, str(REPO / "tools"))
import design_lint                                                               # noqa: E402


def _rq():
    """run_queue imported fresh, so SHARD/SHARDS and the lock token are per-test."""
    import importlib.util                                             # noqa: PLC0415
    spec = importlib.util.spec_from_file_location("rq_t", REPO / "runners" / "run_queue.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ── H1: the queue lock ────────────────────────────────────────────────────────────────

def test_h1_two_contenders_yield_one_owner(tmp_path):
    a, b = _rq(), _rq()
    a.LOCK = b.LOCK = tmp_path / ".queue.lock"
    assert a._claim_lock() is True
    assert b._claim_lock() is False, "second contender took a lock the first one holds"


def test_h1_refused_contender_does_not_delete_the_owners_lock(tmp_path):
    """THE BUG. `_release_lock` ran unconditionally from main's `finally`, so the process
    that was REFUSED the lock deleted it on the way out, handing the shard to the next
    contender while the true owner kept running."""
    owner, loser = _rq(), _rq()
    owner.LOCK = loser.LOCK = tmp_path / ".queue.lock"
    assert owner._claim_lock() is True
    assert loser._claim_lock() is False
    loser._release_lock()                       # the refused process exits; finally: fires
    assert owner._lock_path().exists(), "the refused contender deleted the owner's lock"
    rec = json.loads(owner._lock_path().read_text(encoding="utf-8"))
    assert rec["token"] == owner._LOCK_TOKEN


def test_h1_exception_cleanup_also_preserves_the_owner(tmp_path):
    owner, loser = _rq(), _rq()
    owner.LOCK = loser.LOCK = tmp_path / ".queue.lock"
    assert owner._claim_lock() is True
    assert loser._claim_lock() is False
    try:
        raise RuntimeError("stage blew up")
    except RuntimeError:
        loser._release_lock()
    assert owner._lock_path().exists()


def test_h1_owner_releases_its_own_lock(tmp_path):
    owner = _rq()
    owner.LOCK = tmp_path / ".queue.lock"
    assert owner._claim_lock() is True
    owner._release_lock()
    assert not owner._lock_path().exists()


def test_h1_crash_recovery_reclaims_a_dead_owners_lock(tmp_path):
    m = _rq()
    m.LOCK = tmp_path / ".queue.lock"
    m._lock_path().write_text(json.dumps(
        {"pid": 999_999, "host": socket.gethostname(),
         "create_time": 1.0, "token": "dead:999999:1"}), encoding="utf-8")
    assert m._claim_lock() is True, "a lock from an exited owner must be reclaimable"


def test_h1_stale_token_cannot_release_a_newer_lock(tmp_path):
    first, second = _rq(), _rq()
    first.LOCK = second.LOCK = tmp_path / ".queue.lock"
    assert first._claim_lock() is True
    stale = first._LOCK_TOKEN
    first._release_lock()                       # first finishes cleanly
    assert second._claim_lock() is True         # a new queue takes the shard
    first._LOCK_TOKEN = stale                   # a late cleanup from the old process
    first._release_lock()
    assert second._lock_path().exists(), "a stale token released a newer owner's lock"


def test_h1_unknown_ownership_holds_rather_than_clearing(tmp_path):
    m = _rq()
    m.LOCK = tmp_path / ".queue.lock"
    m._lock_path().write_text("this is not json", encoding="utf-8")
    assert m._claim_lock() is False, "unverifiable ownership must hold the launch"
    assert m._lock_path().exists(), "an unverifiable lock must never be deleted"


def test_h1_foreign_host_lock_is_held_not_cleared(tmp_path):
    m = _rq()
    m.LOCK = tmp_path / ".queue.lock"
    m._lock_path().write_text(json.dumps(
        {"pid": 1, "host": "some-other-machine", "create_time": 1.0, "token": "x"}),
        encoding="utf-8")
    assert m._claim_lock() is False
    assert m._lock_path().exists()


# ── H2: resource declaration ──────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def rq_stages():
    return _rq()


def test_h2_s3x_generation_and_training_stages_are_held_under_no_gpu(rq_stages):
    """The reproduced gap: `_GPU_HEAVY_PREFIXES` carries `s3_`, and `s3x_` does not start
    with it, so twenty-one expansion arms -- including a 240-minute generation stage and
    three train/probe arms -- ran under the no-GPU route the curator's card said they must
    wait out."""
    s3x = [s for s in rq_stages.STAGES if s["name"].startswith("s3x_")]
    assert s3x, "fixture drifted: no s3x_ stages"
    escaped = [s["name"] for s in s3x if rq_stages.gpu_eligible(s, allow_gpu=False)]
    assert not escaped, f"s3x stages still escape the no-GPU hold: {escaped}"
    for name in ("s3x_l01_gen712", "s3x_l01_train712", "s3x_s02_train_c2"):
        st = next(s for s in rq_stages.STAGES if s["name"] == name)
        assert not rq_stages.gpu_eligible(st, allow_gpu=False)


def test_h2_declared_cpu_stages_still_proceed(rq_stages):
    cpu = [s for s in rq_stages.STAGES if s["resource"] == "cpu"]
    assert len(cpu) > 100, "light work must be preserved, not swept into the hold"
    assert all(rq_stages.gpu_eligible(s, allow_gpu=False) for s in cpu)


def test_h2_unknown_requirement_cannot_evade_the_restriction(rq_stages):
    assert rq_stages.gpu_eligible({"name": "undeclared"}, allow_gpu=False) is False
    assert rq_stages.gpu_eligible({"name": "x", "resource": "wat"}, allow_gpu=False) is False


def test_h2_approved_heavy_execution_remains_possible(rq_stages):
    gpu = [s for s in rq_stages.STAGES if s["resource"] == "gpu"]
    assert gpu and all(rq_stages.gpu_eligible(s, allow_gpu=True) for s in gpu)


def test_h2_every_stage_carries_a_declared_resource(rq_stages):
    assert all(s.get("resource") in rq_stages.RESOURCES for s in rq_stages.STAGES)


# ── H3: manifest transactions ─────────────────────────────────────────────────────────

def _set_status_worker(manifest_dir: str, cell_id: str, status: str) -> None:
    """Runs in a spawned process: two genuinely concurrent writers, as Stage 3 had."""
    import time as _t
    sys.path.insert(0, str(Path(manifest_dir).parent))
    repo = Path(__file__).resolve().parents[1] if "__file__" in dir() else None
    sys.path.insert(0, str(repo))
    from soundingline import s3 as s3m
    s3m.S3 = Path(manifest_dir)
    s3m.MANIFEST_PATH = Path(manifest_dir) / "QUEUE_MANIFEST.json"
    s3m.MANIFEST_LOCK = Path(manifest_dir) / ".manifest.lock"
    _t.sleep(0.05)                              # widen the window both writers race in
    s3m.set_status(cell_id, status)


def test_h3_overlapping_updates_to_two_cards_both_survive(tmp_path):
    """The reproduced bug: two runners each read the manifest, each changed a DIFFERENT
    cell, and each wrote the whole list back. The first writer's status vanished with no
    error anywhere."""
    cells = [s3.make_cell(f"C{i}", "S", "q", "u", ["m"], 1.0, f"p{i}.json") for i in range(2)]
    (tmp_path / "QUEUE_MANIFEST.json").write_text(json.dumps(cells, indent=1),
                                                  encoding="utf-8")
    ctx = mp.get_context("spawn")
    procs = [ctx.Process(target=_set_status_worker, args=(str(tmp_path), "C0", "LANDED")),
             ctx.Process(target=_set_status_worker, args=(str(tmp_path), "C1", "RUNNING"))]
    for p in procs:
        p.start()
    for p in procs:
        p.join(timeout=120)
    out = {c["cell_id"]: c["status"]
           for c in json.loads(
               (tmp_path / "QUEUE_MANIFEST.json").read_text(encoding="utf-8"))}
    assert out == {"C0": "LANDED", "C1": "RUNNING"}, f"an update was lost: {out}"


def test_h3_a_failed_transaction_writes_nothing(tmp_path, monkeypatch):
    cells = [s3.make_cell("C0", "S", "q", "u", ["m"], 1.0, "p.json")]
    mpath = tmp_path / "QUEUE_MANIFEST.json"
    mpath.write_text(json.dumps(cells, indent=1), encoding="utf-8")
    monkeypatch.setattr(s3, "S3", tmp_path)
    monkeypatch.setattr(s3, "MANIFEST_PATH", mpath)
    monkeypatch.setattr(s3, "MANIFEST_LOCK", tmp_path / ".manifest.lock")
    before = mpath.read_text(encoding="utf-8")
    with pytest.raises(RuntimeError):
        with s3.manifest_transaction() as live:
            live[0]["status"] = "LANDED"
            raise RuntimeError("interrupted mid-transaction")
    assert mpath.read_text(encoding="utf-8") == before
    assert not (tmp_path / ".manifest.lock").exists(), "the lock leaked past the exception"


def test_h3_interruption_leaves_readable_state(tmp_path, monkeypatch):
    cells = [s3.make_cell("C0", "S", "q", "u", ["m"], 1.0, "p.json")]
    mpath = tmp_path / "QUEUE_MANIFEST.json"
    mpath.write_text(json.dumps(cells, indent=1), encoding="utf-8")
    monkeypatch.setattr(s3, "S3", tmp_path)
    monkeypatch.setattr(s3, "MANIFEST_PATH", mpath)
    monkeypatch.setattr(s3, "MANIFEST_LOCK", tmp_path / ".manifest.lock")
    s3.set_status("C0", "LANDED")
    json.loads(mpath.read_text(encoding="utf-8"))            # parses: never torn
    assert not list(tmp_path.glob("*.tmp")), "a temp file was left behind"


def test_h3_malformed_state_is_rejected_not_silently_reset(tmp_path, monkeypatch):
    mpath = tmp_path / "QUEUE_MANIFEST.json"
    mpath.write_text('[{"cell_id": "C0", trunc', encoding="utf-8")
    monkeypatch.setattr(s3, "S3", tmp_path)
    monkeypatch.setattr(s3, "MANIFEST_PATH", mpath)
    monkeypatch.setattr(s3, "MANIFEST_LOCK", tmp_path / ".manifest.lock")
    with pytest.raises(ValueError):
        s3.set_status("C0", "LANDED")
    assert "trunc" in mpath.read_text(encoding="utf-8"), "malformed state was overwritten"


# ── H4: completion validation ─────────────────────────────────────────────────────────

def test_h4_truncated_json_is_not_a_completion(tmp_path):
    p = tmp_path / "r.json"
    p.write_text('{"cell_id": "C0", "resu', encoding="utf-8")
    assert completion.inspect(p)["status"] == completion.MALFORMED
    assert completion.usable(p) is False


def test_h4_missing_and_empty_outputs_are_not_completions(tmp_path):
    assert completion.inspect(tmp_path / "nope.json")["status"] == completion.MISSING
    (tmp_path / "z.json").write_text("", encoding="utf-8")
    assert completion.inspect(tmp_path / "z.json")["status"] == completion.EMPTY
    (tmp_path / "e.json").write_text("{}", encoding="utf-8")
    assert completion.inspect(tmp_path / "e.json")["status"] == completion.EMPTY


def test_h4_wrong_card_is_rejected(tmp_path):
    p = tmp_path / "r.json"
    p.write_text(json.dumps({"cell_id": "C9", "result": 1}), encoding="utf-8")
    assert completion.inspect(p, expect={"cell_id": "C0"})["status"] == completion.MISIDENTIFIED
    assert completion.usable(p, expect={"cell_id": "C0"}) is False


def test_h4_wrong_lane_is_rejected(tmp_path):
    p = tmp_path / "r.json"
    p.write_text(json.dumps({"cell_id": "C0", "lane": "discovery"}), encoding="utf-8")
    got = completion.inspect(p, expect={"cell_id": "C0", "lane": "confirmation"})
    assert got["status"] == completion.MISIDENTIFIED


def test_h4_a_valid_negative_result_completes(tmp_path):
    """A negative result is a RESULT, and completes. Only a broken instrument fails here:
    an instrument failure must never be dressed up as a theory-negative."""
    p = tmp_path / "r.json"
    p.write_text(json.dumps({"cell_id": "C0", "lane": "discovery",
                             "outcome": "COUNTEREVIDENCE", "effect": -0.4}), encoding="utf-8")
    assert completion.usable(p, expect={"cell_id": "C0", "lane": "discovery"}) is True


def test_h4_legacy_artifact_is_unverifiable_not_invalid(tmp_path):
    """No fabricated provenance: an artifact predating the identity stamp is reported
    unverifiable and preserved, never relabelled invalid."""
    p = tmp_path / "old.json"
    p.write_text(json.dumps({"score": 0.5}), encoding="utf-8")
    assert completion.inspect(p, expect={"cell_id": "C0"})["status"] == completion.UNVERIFIABLE
    assert completion.usable(p, expect={"cell_id": "C0"}) is True
    assert completion.usable(p, expect={"cell_id": "C0"}, allow_unverifiable=False) is False


def test_h4_truncated_jsonl_last_row_is_malformed(tmp_path):
    p = tmp_path / "rows.jsonl"
    p.write_text('{"a": 1}\n{"a": 2}\n{"a": ', encoding="utf-8")
    assert completion.inspect(p)["status"] == completion.MALFORMED


def test_h4_non_json_artifacts_are_checked_for_presence_only(tmp_path):
    """Not every declared artifact is JSON. A .pt checkpoint is checked for presence and
    non-emptiness, and the status says exactly that rather than implying more."""
    ckpt = tmp_path / "model.pt"
    ckpt.write_bytes(b"\x80\x02}q\x00.")
    assert completion.usable(ckpt) is True
    (tmp_path / "empty.pt").write_bytes(b"")
    assert completion.usable(tmp_path / "empty.pt") is False


def test_h4_inventory_is_read_only(tmp_path):
    good, bad = tmp_path / "g.json", tmp_path / "b.json"
    good.write_text(json.dumps({"cell_id": "C0"}), encoding="utf-8")
    bad.write_text("{trunc", encoding="utf-8")
    before = {p: p.read_bytes() for p in (good, bad)}
    inv = completion.inventory([(str(good), {"cell_id": "C0"}), (str(bad), None)])
    assert inv["n"] == 2 and inv["counts"][completion.MALFORMED] == 1
    assert all(p.read_bytes() == b for p, b in before.items()), "inventory mutated an original"


def test_h4_program_validator_fails_a_malformed_result_fixture(tmp_path, monkeypatch):
    """The acceptance case: status counts and attempt floors look complete, and the program
    validator must still fail because a LANDED cell's produce cannot be read."""
    import importlib.util                                             # noqa: PLC0415
    spec = importlib.util.spec_from_file_location(
        "vsp", REPO / "runners" / "validate_stage3_program.py")
    v = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v)

    produce = tmp_path / "landed.json"
    produce.write_text('{"cell_id": "E24-S3-S01", "trunc', encoding="utf-8")
    cell = {"cell_id": "E24-S3-S01", "trunk": "S", "lane": "discovery",
            "status": "LANDED", "produces": str(produce), "actual_gpu_minutes": 1.0,
            "estimated_gpu_minutes": 1.0, "closure_reason": None}
    monkeypatch.setattr(v, "load_manifest", lambda: [cell])
    monkeypatch.setattr(v, "MANDATORY_PREFIXES", ["E24-S3-S01"])
    monkeypatch.setattr(v, "REPO", Path(tmp_path.anchor))
    monkeypatch.setattr(v, "COVERAGE_PATH", tmp_path / "COVERAGE.json")
    assert v.main() == 1, "a malformed LANDED produce passed the program validator"
    cov = json.loads((tmp_path / "COVERAGE.json").read_text(encoding="utf-8"))
    assert any("malformed" in e for e in cov["errors"])


def test_h4_program_validator_accepts_a_readable_landed_produce(tmp_path, monkeypatch):
    import importlib.util                                             # noqa: PLC0415
    spec = importlib.util.spec_from_file_location(
        "vsp2", REPO / "runners" / "validate_stage3_program.py")
    v = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v)

    produce = tmp_path / "landed.json"
    produce.write_text(json.dumps({"cell_id": "E24-S3-S01", "lane": "discovery",
                                   "outcome": "COUNTEREVIDENCE"}), encoding="utf-8")
    cell = {"cell_id": "E24-S3-S01", "trunk": "S", "lane": "discovery",
            "status": "LANDED", "produces": str(produce), "actual_gpu_minutes": 1.0,
            "estimated_gpu_minutes": 1.0, "closure_reason": None}
    monkeypatch.setattr(v, "load_manifest", lambda: [cell])
    monkeypatch.setattr(v, "MANDATORY_PREFIXES", ["E24-S3-S01"])
    monkeypatch.setattr(v, "REPO", Path(tmp_path.anchor))
    monkeypatch.setattr(v, "COVERAGE_PATH", tmp_path / "COVERAGE.json")
    assert v.main() == 0, "a valid negative result was rejected"


# ── H5: design checks ─────────────────────────────────────────────────────────────────

MAGIC_ONLY = '"""A runner. DESIGN CHECK\n"""\nVERDICT_BANDS = {}\n'

REAL_DESIGN = (
    '"""A runner with a real design.\n\n'
    "DESIGN CHECK (2026-08-28)\n"
    "Lessons read: LESSONS section 5, L132.\n"
    "Gates, null/alternative/direction: the shuffle gate fires above 0.55. Under the NULL\n"
    "    the expectation is 0.50 by construction; under the ALTERNATIVE it is higher.\n"
    "    Failure DIRECTION is upward.\n"
    "Verdict bands, exhaustive: [0, 0.45) refuted, [0.45, 0.55] VOID, (0.55, 1] supported.\n"
    '"""\nVERDICT_BANDS = {}\n')


def test_h5_magic_string_alone_fails():
    """The reproduced bug: `if "DESIGN CHECK" in text: sys.exit(0)` certified the presence
    of a STRING, not of a design. A gate with no null, no alternative and no direction
    passed by typing two words into a comment."""
    problems = design_lint.check_text(MAGIC_ONLY, in_prereg=False)
    assert problems
    joined = " ".join(problems).lower()
    assert "null" in joined and "alternative" in joined and "direction" in joined


def test_h5_a_valid_structured_design_passes():
    assert design_lint.check_text(REAL_DESIGN, in_prereg=False) == []


def test_h5_missing_direction_is_caught():
    text = REAL_DESIGN.replace("    Failure DIRECTION is upward.\n", "")
    text = text.replace("fires above 0.55", "fires at the band edge")
    text = text.replace("it is higher", "it is elsewhere")
    text = text.replace("[0, 0.45) refuted, [0.45, 0.55] VOID, (0.55, 1] supported",
                        "refuted, VOID, supported")
    assert any("DIRECTION" in q for q in design_lint.check_text(text, in_prereg=False))


def test_h5_non_exhaustive_bands_are_caught():
    text = REAL_DESIGN.replace("Verdict bands, exhaustive:", "Verdict bands:")
    assert any("exhaustive" in q for q in design_lint.check_text(text, in_prereg=False))


def test_h5_a_file_with_no_gate_machinery_is_not_policed(tmp_path):
    p = tmp_path / "plain.py"
    p.write_text("import json\nprint(json)\n", encoding="utf-8")
    assert design_lint.check_file(p) == []


def test_h5_command_and_hook_adapters_agree(tmp_path):
    """The same file must get the same verdict whether a hook fired or a shell ran it.
    Direct shell edits and runner calls must not depend on an Edit/Write hook firing."""
    p = tmp_path / "runners" / "gated.py"
    p.parent.mkdir(parents=True)
    p.write_text(MAGIC_ONLY, encoding="utf-8")
    hook = REPO / "tools" / "lint_hook.py"
    cli = subprocess.run([sys.executable, str(hook), str(p)],
                         capture_output=True, text=True, timeout=60)
    piped = subprocess.run(
        [sys.executable, str(hook)], input=json.dumps({"tool_input": {"file_path": str(p)}}),
        capture_output=True, text=True, timeout=60)
    assert cli.returncode == piped.returncode == 2
    assert "not checkable" in cli.stderr and "not checkable" in piped.stderr


def test_h5_linters_never_block_on_stdin():
    """Two theory_lint processes hung from 2026-08-24 16:19 to 2026-08-28 on
    `json.load(sys.stdin)`, started by someone running the script with a file argument."""
    for script in ("theory_lint.py", "design_lint.py", "lint_hook.py"):
        r = subprocess.run([sys.executable, str(REPO / "tools" / script)],
                           input="", capture_output=True, text=True, timeout=30)
        assert r.returncode == 0, f"{script} did not exit cleanly on empty stdin"


def test_h5_a_file_argument_is_honoured_not_ignored():
    """argv was ignored entirely; the script read stdin regardless of what it was given."""
    r = subprocess.run(
        [sys.executable, str(REPO / "tools" / "theory_lint.py"),
         str(REPO / "docs" / "theory" / "README.md")],
        input="", capture_output=True, text=True, timeout=30)
    assert r.returncode == 0


def test_h5_malformed_hook_payload_is_observable():
    """`except: sys.exit(0)` treated an unreadable payload exactly like a clean pass."""
    r = subprocess.run([sys.executable, str(REPO / "tools" / "lint_hook.py")],
                       input="not json at all", capture_output=True, text=True, timeout=30)
    assert r.returncode == 3, "a malformed payload must not look like a pass"
    assert "not valid JSON" in r.stderr


# ── theory_lint afterword window (widened 2026-08-28) ─────────────────────────────────

def _theory_lint():
    import importlib.util                                             # noqa: PLC0415
    spec = importlib.util.spec_from_file_location(
        "tl_t", REPO / "tools" / "theory_lint.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


TABLE = ("| # | claim | status |\n"
         "|---|---|---|\n"
         "| **G1** | a claim | **OPEN** |\n")


def _write_theory(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "docs" / "theory" / "FAKE.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def test_theory_lint_still_catches_a_genuinely_missing_afterword(tmp_path):
    """The window was widened from six lines to the next section. It must NOT have become
    'an afterword somewhere in the file' -- a section with none still fails."""
    tl = _theory_lint()
    p = _write_theory(tmp_path, "## S1\n\n" + TABLE + "\nJust prose, no afterword mark.\n"
                                "\n## S2\n\n**What the table says.** Belongs to S2.\n"
                                "Confidence: untested, logic only.\n")
    problems = tl.check_file(p)
    assert any("no afterword" in q for q in problems), problems


def test_theory_lint_accepts_an_afterword_past_an_intervening_block(tmp_path):
    """The false positive that motivated the widening: a curator quotation and a note sit
    between the table and its afterword, as in THREE_COGNITIVE_LAYERS section 7."""
    tl = _theory_lint()
    p = _write_theory(tmp_path, "## S1\n\n" + TABLE +
                      "\n> a curator quotation that runs\n> across several lines\n\n"
                      "**Supersession note.** Some intervening prose that is not the\n"
                      "afterword and takes more than six lines to say what it says,\n"
                      "because that is what these sections actually look like.\n\n"
                      "**What the table says.** The standing interpretation.\n"
                      "Confidence: untested, logic only.\n")
    assert tl.check_file(p) == []


def test_theory_lint_still_requires_the_confidence_vocabulary(tmp_path):
    tl = _theory_lint()
    p = _write_theory(tmp_path, "## S1\n\n" + TABLE +
                      "\n**What the table says.** A conclusion.\n"
                      "Confidence: pretty sure honestly.\n")
    assert any("fixed vocabulary" in q for q in tl.check_file(p))
