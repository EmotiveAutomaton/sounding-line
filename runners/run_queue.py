"""The persistent queue — named run_queue.py, NOT queue.py, which shadows the stdlib — run everything, forever, without supervision.

── WHY ───────────────────────────────────────────────────────────────────────────────────────

    We're not doing one at a time. We're trying to have them run continuously forever. It's the
    queue that matters.

The machine went idle twice in one session and both times the curator had to point it out. A queue
that survives him stepping away is worth more than any single result, because the binding constraint
on this project has never been ideas — it is that nothing runs while nobody is watching.

── HOW IT BEHAVES ────────────────────────────────────────────────────────────────────────────

**Skip what is done.** Every stage names the file it produces. If that file exists, the stage is
skipped, so the queue is safe to restart at any point and safe to run while something else is
already going.

**Never die.** A stage that fails is logged, marked, and the queue moves on. One broken runner must
not cost a night of compute. Stages that depend on a failed stage are skipped rather than run
against missing input.

**Say what happened.** `results/queue_status.json` is rewritten after every stage, so the state is
readable without reading logs. Each stage's own output goes to `results/<name>.log`.

**Order is by value per hour**, not by dependency alone — long GPU jobs first so the card is never
the thing waiting.

── ADDING A STAGE ────────────────────────────────────────────────────────────────────────────

One entry in `STAGES`. `needs` is a list of file paths that must exist; if any is missing the stage
is deferred rather than failed, so a queue run after new data arrives will pick it up.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = str(REPO / ".venv" / "Scripts" / "python.exe")
STATUS = REPO / "results" / "queue_status.json"


def _status_path():
    return STATUS if SHARDS == 1 else STATUS.with_name(f"queue_status_{SHARD}of{SHARDS}.json")

# name, command, produces (skip if exists), needs (defer if missing), rough minutes
STAGES: list[dict] = [
    # ── refill 2026-08-08: G21, G103 (fair control cross-family), G104 (finish the 11-family matrix)
    {"name": "binary_salience", "est": 45,
     "cmd": [PY, "runners/run_binary_salience.py"],
     "produces": "results/binary_salience/Qwen2.5-1.5B.json", "needs": [],
     "why": "G21: his question -- is layer 0 binary salience? presence-vs-category double dissociation"},
    {"name": "induction_v2_ladder2_pythia-1.4b", "est": 40,
     "cmd": [PY, "runners/run_induction_v2.py", "--corpus", "ladder2", "--model", "EleutherAI/pythia-1.4b"],
     "produces": "results/induction_v2/ladder2_pythia-1.4b.json", "needs": [],
     "why": "G103: does the fair-control flagship replicate outside the Qwen family?"},
    {"name": "induction_v2_ladder2_gpt2-medium", "est": 40,
     "cmd": [PY, "runners/run_induction_v2.py", "--corpus", "ladder2", "--model", "openai-community/gpt2-medium"],
     "produces": "results/induction_v2/ladder2_gpt2-medium.json", "needs": [],
     "why": "G103: fair-control flagship, second independent family"},
    {"name": "induction_v2_ladder2_SmolLM2-360M", "est": 30,
     "cmd": [PY, "runners/run_induction_v2.py", "--corpus", "ladder2", "--model", "HuggingFaceTB/SmolLM2-360M"],
     "produces": "results/induction_v2/ladder2_SmolLM2-360M.json", "needs": [],
     "why": "G103: fair-control flagship, third independent family"},
    # audit L26: v1 verdict logic was broken (argmax SHIFTS, missing taxonomy branch); the four
    # original files are preserved in v1_broken_verdicts/ and these re-runs regenerate them
    {"name": "readouts_refresh_Qwen2.5-1.5B", "est": 15,
     "cmd": [PY, "runners/run_depth_readouts.py", "--model", "Qwen/Qwen2.5-1.5B"],
     "produces": "results/depth_readouts/Qwen2.5-1.5B.json", "needs": [],
     "why": "L26: regenerate flagship readout under v2 verdict rules"},
    {"name": "readouts_refresh_SmolLM2-360M", "est": 15,
     "cmd": [PY, "runners/run_depth_readouts.py", "--model", "HuggingFaceTB/SmolLM2-360M"],
     "produces": "results/depth_readouts/SmolLM2-360M.json", "needs": [],
     "why": "L26: regenerate under v2 verdict rules (v1 mislabelled all-bands-positive as FLAT)"},
    {"name": "readouts_refresh_gpt2-medium", "est": 15,
     "cmd": [PY, "runners/run_depth_readouts.py", "--model", "openai-community/gpt2-medium"],
     "produces": "results/depth_readouts/gpt2-medium.json", "needs": [],
     "why": "L26: regenerate under v2 verdict rules"},
    {"name": "readouts_refresh_pythia-1.4b", "est": 15,
     "cmd": [PY, "runners/run_depth_readouts.py", "--model", "EleutherAI/pythia-1.4b"],
     "produces": "results/depth_readouts/pythia-1.4b.json", "needs": [],
     "why": "L26: regenerate under v2 verdict rules (v1 SHIFTS was an argmax crossover)"},
    {"name": "specrec_noecho_ladder2", "est": 45,
     "cmd": [PY, "runners/run_spec_recovery.py", "--corpus", "ladder2", "--decoys", "96", "--no-echo"],
     "produces": "results/spec_recovery/ladder2_noecho.json", "needs": [],
     "why": "L26: the pre-registered echo restriction, promised in the docstring, never implemented until now"},
    {"name": "readouts_Qwen2.5-0.5B", "est": 15,
     "cmd": [PY, "runners/run_depth_readouts.py", "--model", "Qwen/Qwen2.5-0.5B"],
     "produces": "results/depth_readouts/Qwen2.5-0.5B.json", "needs": [],
     "why": "G104: depth readouts, fifth family/size"},
    {"name": "readouts_gpt2-large", "est": 15,
     "cmd": [PY, "runners/run_depth_readouts.py", "--model", "openai-community/gpt2-large"],
     "produces": "results/depth_readouts/gpt2-large.json", "needs": [],
     "why": "G104: depth readouts, sixth"},
    {"name": "readouts_pythia-410m", "est": 15,
     "cmd": [PY, "runners/run_depth_readouts.py", "--model", "EleutherAI/pythia-410m"],
     "produces": "results/depth_readouts/pythia-410m.json", "needs": [],
     "why": "G104: depth readouts, seventh"},
    {"name": "readouts_Qwen2.5-3B", "est": 20,
     "cmd": [PY, "runners/run_depth_readouts.py", "--model", "Qwen/Qwen2.5-3B"],
     "produces": "results/depth_readouts/Qwen2.5-3B.json", "needs": [],
     "why": "G104: depth readouts, eighth -- largest that fits the card"},
    {"name": "sweep_ladder_Qwen2.5-3B", "est": 25,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder", "--model", "Qwen/Qwen2.5-3B"],
     "produces": "results/depth_sweep/ladder_Qwen2.5-3B.json", "needs": [],
     "why": "G104: fill the 11-family matrix -- first ladder, Qwen 3B"},
    {"name": "sweep_ladder3_Qwen2.5-3B", "est": 25,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder3", "--model", "Qwen/Qwen2.5-3B"],
     "produces": "results/depth_sweep/ladder3_Qwen2.5-3B.json", "needs": [],
     "why": "G104: extreme ladder, Qwen 3B"},
    {"name": "sweep_ladder_SmolLM2-1.7B", "est": 25,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder", "--model", "HuggingFaceTB/SmolLM2-1.7B"],
     "produces": "results/depth_sweep/ladder_SmolLM2-1.7B.json", "needs": [],
     "why": "G104: first ladder, SmolLM2 1.7B"},
    {"name": "sweep_ladder3_SmolLM2-1.7B", "est": 25,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder3", "--model", "HuggingFaceTB/SmolLM2-1.7B"],
     "produces": "results/depth_sweep/ladder3_SmolLM2-1.7B.json", "needs": [],
     "why": "G104: extreme ladder, SmolLM2 1.7B"},
    {"name": "sweep_ladder_gpt2-xl", "est": 35,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder", "--model", "openai-community/gpt2-xl"],
     "produces": "results/depth_sweep/ladder_gpt2-xl.json", "needs": [],
     "why": "G104: first ladder, gpt2-xl"},
    {"name": "sweep_ladder3_gpt2-xl", "est": 35,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder3", "--model", "openai-community/gpt2-xl"],
     "produces": "results/depth_sweep/ladder3_gpt2-xl.json", "needs": [],
     "why": "G104: extreme ladder, gpt2-xl"},
    {"name": "sweep_ladder_pythia-2.8b", "est": 35,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder", "--model", "EleutherAI/pythia-2.8b"],
     "produces": "results/depth_sweep/ladder_pythia-2.8b.json", "needs": [],
     "why": "G104: first ladder, pythia 2.8b"},
    {"name": "sweep_ladder3_pythia-2.8b", "est": 35,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder3", "--model", "EleutherAI/pythia-2.8b"],
     "produces": "results/depth_sweep/ladder3_pythia-2.8b.json", "needs": [],
     "why": "G104: extreme ladder, pythia 2.8b"},
    # ── refill 2026-08-08 evening: G103b (mirror replication), G21b (powered presence)
    {"name": "induction_v2_ladder_gpt2-medium", "est": 25,
     "cmd": [PY, "runners/run_induction_v2.py", "--corpus", "ladder", "--model", "openai-community/gpt2-medium"],
     "produces": "results/induction_v2/ladder_gpt2-medium.json", "needs": [],
     "why": "G103b: does the gpt2 mirror (+0.51, L28) replicate on the first ladder?"},
    {"name": "induction_v2_ladder3_gpt2-medium", "est": 35,
     "cmd": [PY, "runners/run_induction_v2.py", "--corpus", "ladder3", "--model", "openai-community/gpt2-medium"],
     "produces": "results/induction_v2/ladder3_gpt2-medium.json", "needs": [],
     "why": "G103b: the gpt2 mirror on the extreme ladder — three-for-three or a fluke"},
    {"name": "induction_v2_ladder_pythia-1.4b", "est": 25,
     "cmd": [PY, "runners/run_induction_v2.py", "--corpus", "ladder", "--model", "EleutherAI/pythia-1.4b"],
     "produces": "results/induction_v2/ladder_pythia-1.4b.json", "needs": [],
     "why": "G103b: pythia was null on the held-out ladder — null everywhere, or corpus-specific?"},
    {"name": "induction_v2_ladder3_pythia-1.4b", "est": 35,
     "cmd": [PY, "runners/run_induction_v2.py", "--corpus", "ladder3", "--model", "EleutherAI/pythia-1.4b"],
     "produces": "results/induction_v2/ladder3_pythia-1.4b.json", "needs": [],
     "why": "G103b: pythia on the extreme ladder"},
    {"name": "induction_v2_ladder_SmolLM2-360M", "est": 25,
     "cmd": [PY, "runners/run_induction_v2.py", "--corpus", "ladder", "--model", "HuggingFaceTB/SmolLM2-360M"],
     "produces": "results/induction_v2/ladder_SmolLM2-360M.json", "needs": [],
     "why": "G103b: SmolLM2 on the first ladder"},
    {"name": "induction_v2_ladder3_SmolLM2-360M", "est": 30,
     "cmd": [PY, "runners/run_induction_v2.py", "--corpus", "ladder3", "--model", "HuggingFaceTB/SmolLM2-360M"],
     "produces": "results/induction_v2/ladder3_SmolLM2-360M.json", "needs": [],
     "why": "G103b: SmolLM2 on the extreme ladder"},
    {"name": "binary_salience_powered", "est": 50,
     "cmd": [PY, "runners/run_binary_salience.py", "--neutral-per", "500"],
     "produces": "results/binary_salience/Qwen2.5-1.5B_powered.json", "needs": [],
     "why": "G21b: L27's presence probe had 40 neutral items — a coin flip with no power. 500 decides it"},
    # ── overnight battery 2026-08-08: tests derived from the essays + theory folder (G114-G117,
    # G42b/G44a, G46, G60, PD-19 close-out). CPU first, GPU after, Ollama last.
    {"name": "compression_ladder", "est": 3,
     "cmd": [PY, "runners/run_compression_ladder.py"],
     "produces": "results/compression/summary.json", "needs": [],
     "why": "G116: the essays' Kolmogorov and regression-to-the-mean claims, first test"},
    {"name": "placement_scale", "est": 2,
     "cmd": [PY, "runners/run_placement_scale.py"],
     "produces": "results/placement_scale/summary.json", "needs": [],
     "why": "G46: do weaker models place affective structure more poorly? (the live worry's second test)"},
    {"name": "subspace_bands11", "est": 2,
     "cmd": [PY, "runners/run_subspace_bands11.py"],
     "produces": "results/subspace_bands11/summary.json", "needs": [],
     "why": "G42b: two-band split on all 11 families; G44a: transform composability"},
    {"name": "acceleration_reread", "est": 1,
     "cmd": [PY, "runners/run_acceleration_reread.py"],
     "produces": "results/acceleration/summary.json", "needs": [],
     "why": "PD-19 close-out over L23's saved per-artifact rows"},
    {"name": "author_convergence", "est": 5,
     "cmd": [PY, "runners/run_author_convergence.py"],
     "produces": "results/author_convergence/summary.json", "needs": [],
     "why": "G60: the convergence curve and its asymptote, on the 34-book corpus"},
    {"name": "nomaker_specrec", "est": 30,
     "cmd": [PY, "runners/run_nomaker_specrec.py"],
     "produces": "results/spec_recovery/nomaker_control.json", "needs": [],
     "why": "G117: the no-maker control spec recovery never had — sharper after the echo kill"},
    {"name": "provenance_framing", "est": 45,
     "cmd": [PY, "runners/run_provenance_framing.py"],
     "produces": "results/provenance_framing/ladder2.json", "needs": [],
     "why": "G115: the paper's H1 in the reader — does the AI label alone move the affective read?"},
    {"name": "reader_convergence", "est": 90,
     "cmd": [PY, "runners/run_reader_convergence.py"],
     "produces": "results/reader_convergence/summary.json", "needs": [],
     "why": "G114: the paper's H2 vs flattened-intent — goal-inference convergence across five groups"},
    # ── standing stages: guarded skips that self-heal if a result file is ever lost
    {"name": "noisy_middle", "est": 1,
     "cmd": [PY, "runners/run_noisy_middle.py"],
     "produces": "results/noisy_middle/summary.json", "needs": [],
     "why": "G31: middle-third activity vs coherence, CPU readout over saved sweeps"},
    {"name": "induction_v2_ladder2", "est": 40,
     "cmd": [PY, "runners/run_induction_v2.py", "--corpus", "ladder2"],
     "produces": "results/induction_v2/ladder2.json", "needs": [],
     "why": "G75: the within-rung induction control -- re-adjudicates L1, L2 and L17 on ladder2"},
    {"name": "induction_v2_ladder3", "est": 35,
     "cmd": [PY, "runners/run_induction_v2.py", "--corpus", "ladder3"],
     "produces": "results/induction_v2/ladder3.json", "needs": [],
     "why": "G75: the within-rung induction control -- re-adjudicates L1, L2 and L17 on ladder3"},
    {"name": "induction_v2_ladder", "est": 25,
     "cmd": [PY, "runners/run_induction_v2.py", "--corpus", "ladder"],
     "produces": "results/induction_v2/ladder.json", "needs": [],
     "why": "G75: the within-rung induction control -- re-adjudicates L1, L2 and L17 on ladder"},
    {"name": "length_direction_audit", "est": 3,
     "cmd": [PY, "runners/audit_length_direction.py"],
     "produces": None, "needs": [],
     "why": "was length a confound or a suppressor, per measure"},
    {"name": "multiplicity", "est": 1,
     "cmd": [PY, "runners/audit_multiplicity.py"],
     "produces": None, "needs": [],
     "why": "re-correct the whole family after new results land"},
]



def rel(p: str) -> Path:
    return REPO / p


LOCK = REPO / "results" / ".queue.lock"

# Sharding exists so the overnight runner can use the whole machine without two processes ever
# picking the same stage. Stage i belongs to shard (i % shards). **No claim files, no races** --
# ownership is decided by arithmetic before anything starts.
SHARD, SHARDS = 0, 1


def _lock_path() -> Path:
    return LOCK if SHARDS == 1 else LOCK.with_suffix(f".{SHARD}of{SHARDS}.lock")


def _claim_lock() -> bool:
    """Refuse to start if another queue is already running.

    On 2026-08-07 two loops ran concurrently for twelve minutes, both executing the same stage and
    both writing the same output file. **That is a correctness risk, not a waste of cycles** — the
    loser's partial write can land on top of the winner's result. A stale lock from a killed process
    is cleared automatically, because a queue that refuses to start is worse than one that races.
    """
    import os                                                         # noqa: PLC0415
    lk = _lock_path()
    lk.parent.mkdir(parents=True, exist_ok=True)
    if lk.exists():
        try:
            pid = int(lk.read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            pid = -1
        alive = False
        if pid > 0:
            try:                                                      # Windows: signal 0 is a probe
                os.kill(pid, 0)
                alive = True
            except OSError:
                alive = False
        if alive:
            print(f"another queue is already running on this shard as pid {pid}. Refusing.")
            return False
        print(f"clearing a stale lock from pid {pid}")
    lk.write_text(str(os.getpid()), encoding="utf-8", newline="\n")
    return True


def main() -> None:
    global SHARD, SHARDS
    import argparse                                                   # noqa: PLC0415
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--shards", type=int, default=1,
                    help="run this process as one of N. Stage i is owned by shard i %% N, so two "
                         "shards can never pick the same stage")
    a = ap.parse_args()
    SHARD, SHARDS = a.shard, a.shards
    if not (0 <= SHARD < SHARDS):
        print(f"shard {SHARD} is not in range for {SHARDS} shards")
        return
    if not _claim_lock():
        return
    state: dict = {"started": time.strftime("%Y-%m-%d %H:%M"), "stages": []}
    _status_path().parent.mkdir(parents=True, exist_ok=True)

    def save() -> None:
        _status_path().write_text(json.dumps(state, indent=2), encoding="utf-8", newline="\n")

    mine = [s for i, s in enumerate(STAGES) if i % SHARDS == SHARD]
    if SHARDS > 1:
        print(f"shard {SHARD} of {SHARDS}: {len(mine)} of {len(STAGES)} stages")
    state["shard"] = f"{SHARD}/{SHARDS}"

    failed: set[str] = set()
    for st in mine:
        name = st["name"]
        entry = {"name": name, "why": st["why"], "est_minutes": st["est"]}

        missing = [n for n in st["needs"] if not rel(n).exists()]
        if missing:
            entry["status"] = "DEFERRED"
            entry["missing"] = missing
            print(f"[defer] {name}: waiting on {', '.join(missing)}", flush=True)
            state["stages"].append(entry); save(); continue

        if st["produces"] and rel(st["produces"]).exists():
            entry["status"] = "SKIPPED (already done)"
            print(f"[skip ] {name}", flush=True)
            state["stages"].append(entry); save(); continue

        log = REPO / "results" / f"{name}.log"
        print(f"[run  ] {name} — {st['why']} (~{st['est']} min)", flush=True)
        t0 = time.time()
        entry["status"] = "RUNNING"
        entry["log"] = str(log.relative_to(REPO))
        state["stages"].append(entry); save()
        try:
            with log.open("w", encoding="utf-8") as fh:
                r = subprocess.run(st["cmd"], cwd=REPO, stdout=fh,
                                   stderr=subprocess.STDOUT, timeout=max(st["est"], 5) * 60 * 6)
            entry["status"] = "DONE" if r.returncode == 0 else f"FAILED (exit {r.returncode})"
        except subprocess.TimeoutExpired:
            entry["status"] = "TIMEOUT"
        except Exception as e:                                        # noqa: BLE001
            entry["status"] = f"ERROR {type(e).__name__}"
        entry["minutes"] = round((time.time() - t0) / 60, 1)
        if not entry["status"].startswith("DONE"):
            failed.add(name)
            print(f"[{entry['status'][:5]}] {name} after {entry['minutes']} min "
                  f"— see {entry['log']}", flush=True)
        else:
            print(f"[done ] {name} in {entry['minutes']} min", flush=True)
        save()

    state["finished"] = time.strftime("%Y-%m-%d %H:%M")
    state["failed"] = sorted(failed)
    save()
    print(f"\nQUEUE FINISHED. {len(failed)} failed: {', '.join(sorted(failed)) or 'none'}")
    print(f"status: {STATUS.relative_to(REPO)}")


def _release_lock() -> None:
    try:
        _lock_path().unlink()
    except OSError:
        pass


if __name__ == "__main__":
    try:
        main()
    finally:
        _release_lock()
