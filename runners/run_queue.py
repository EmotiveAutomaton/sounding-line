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

# name, command, produces (skip if exists), needs (defer if missing), rough minutes
STAGES: list[dict] = [
    {"name": "pan_feat_hard_250", "est": 45,
     "cmd": [PY, "runners/run_pan_features.py", "--difficulty", "hard", "--n-train", "250", "--n-test", "250"],
     "produces": None, "needs": [],
     "why": "342 features on PAN hard style change, 250 train problems, scored their way"},
    {"name": "pan_feat_medium_250", "est": 45,
     "cmd": [PY, "runners/run_pan_features.py", "--difficulty", "medium", "--n-train", "250", "--n-test", "250"],
     "produces": None, "needs": [],
     "why": "342 features on PAN medium style change, 250 train problems, scored their way"},
    {"name": "pan_feat_easy_250", "est": 45,
     "cmd": [PY, "runners/run_pan_features.py", "--difficulty", "easy", "--n-train", "250", "--n-test", "250"],
     "produces": None, "needs": [],
     "why": "342 features on PAN easy style change, 250 train problems, scored their way"},
    {"name": "pan_feat_hard_600", "est": 45,
     "cmd": [PY, "runners/run_pan_features.py", "--difficulty", "hard", "--n-train", "600", "--n-test", "400"],
     "produces": None, "needs": [],
     "why": "342 features on PAN hard style change, 600 train problems, scored their way"},
    {"name": "corr48_ladder2", "est": 8,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder2", "--n-random", "48"],
     "produces": None, "needs": [],
     "why": "per-layer intent correlation on ladder2 with a 4x tighter random-direction null"},
    {"name": "corr48_ladder3", "est": 8,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder3", "--n-random", "48"],
     "produces": None, "needs": [],
     "why": "per-layer intent correlation on ladder3 with a 4x tighter random-direction null"},
    {"name": "corr48_nomaker", "est": 8,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "nomaker", "--n-random", "48"],
     "produces": None, "needs": [],
     "why": "per-layer intent correlation on nomaker with a 4x tighter random-direction null"},
    {"name": "corr48_ladder", "est": 8,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder", "--n-random", "48"],
     "produces": None, "needs": [],
     "why": "per-layer intent correlation on ladder with a 4x tighter random-direction null"},
    {"name": "corr_ladder2_Qwen2.5-3B", "est": 12,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder2", "--model", "Qwen/Qwen2.5-3B"],
     "produces": "results/layer_correlation/ladder2_Qwen2.5-3B.json", "needs": [],
     "why": "per-layer intent correlation, ladder2 read by Qwen2.5-3B"},
    {"name": "depth_ladder2_Qwen2.5-3B", "est": 12,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder2", "--model", "Qwen/Qwen2.5-3B"],
     "produces": "results/depth_sweep/ladder2_Qwen2.5-3B.json", "needs": [],
     "why": "depth profile shape, ladder2 read by Qwen2.5-3B"},
    {"name": "corr_nomaker_Qwen2.5-3B", "est": 12,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "nomaker", "--model", "Qwen/Qwen2.5-3B"],
     "produces": "results/layer_correlation/nomaker_Qwen2.5-3B.json", "needs": [],
     "why": "per-layer intent correlation, nomaker read by Qwen2.5-3B"},
    {"name": "depth_nomaker_Qwen2.5-3B", "est": 12,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "nomaker", "--model", "Qwen/Qwen2.5-3B"],
     "produces": "results/depth_sweep/nomaker_Qwen2.5-3B.json", "needs": [],
     "why": "depth profile shape, nomaker read by Qwen2.5-3B"},
    {"name": "corr_ladder2_pythia-2.8b", "est": 12,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder2", "--model", "EleutherAI/pythia-2.8b"],
     "produces": "results/layer_correlation/ladder2_pythia-2.8b.json", "needs": [],
     "why": "per-layer intent correlation, ladder2 read by pythia-2.8b"},
    {"name": "depth_ladder2_pythia-2.8b", "est": 12,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder2", "--model", "EleutherAI/pythia-2.8b"],
     "produces": "results/depth_sweep/ladder2_pythia-2.8b.json", "needs": [],
     "why": "depth profile shape, ladder2 read by pythia-2.8b"},
    {"name": "corr_nomaker_pythia-2.8b", "est": 12,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "nomaker", "--model", "EleutherAI/pythia-2.8b"],
     "produces": "results/layer_correlation/nomaker_pythia-2.8b.json", "needs": [],
     "why": "per-layer intent correlation, nomaker read by pythia-2.8b"},
    {"name": "depth_nomaker_pythia-2.8b", "est": 12,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "nomaker", "--model", "EleutherAI/pythia-2.8b"],
     "produces": "results/depth_sweep/nomaker_pythia-2.8b.json", "needs": [],
     "why": "depth profile shape, nomaker read by pythia-2.8b"},
    {"name": "corr_ladder2_gpt2-xl", "est": 12,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder2", "--model", "openai-community/gpt2-xl"],
     "produces": "results/layer_correlation/ladder2_gpt2-xl.json", "needs": [],
     "why": "per-layer intent correlation, ladder2 read by gpt2-xl"},
    {"name": "depth_ladder2_gpt2-xl", "est": 12,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder2", "--model", "openai-community/gpt2-xl"],
     "produces": "results/depth_sweep/ladder2_gpt2-xl.json", "needs": [],
     "why": "depth profile shape, ladder2 read by gpt2-xl"},
    {"name": "corr_nomaker_gpt2-xl", "est": 12,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "nomaker", "--model", "openai-community/gpt2-xl"],
     "produces": "results/layer_correlation/nomaker_gpt2-xl.json", "needs": [],
     "why": "per-layer intent correlation, nomaker read by gpt2-xl"},
    {"name": "depth_nomaker_gpt2-xl", "est": 12,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "nomaker", "--model", "openai-community/gpt2-xl"],
     "produces": "results/depth_sweep/nomaker_gpt2-xl.json", "needs": [],
     "why": "depth profile shape, nomaker read by gpt2-xl"},
    {"name": "corr_ladder2_SmolLM2-1.7B", "est": 12,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder2", "--model", "HuggingFaceTB/SmolLM2-1.7B"],
     "produces": "results/layer_correlation/ladder2_SmolLM2-1.7B.json", "needs": [],
     "why": "per-layer intent correlation, ladder2 read by SmolLM2-1.7B"},
    {"name": "depth_ladder2_SmolLM2-1.7B", "est": 12,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder2", "--model", "HuggingFaceTB/SmolLM2-1.7B"],
     "produces": "results/depth_sweep/ladder2_SmolLM2-1.7B.json", "needs": [],
     "why": "depth profile shape, ladder2 read by SmolLM2-1.7B"},
    {"name": "corr_nomaker_SmolLM2-1.7B", "est": 12,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "nomaker", "--model", "HuggingFaceTB/SmolLM2-1.7B"],
     "produces": "results/layer_correlation/nomaker_SmolLM2-1.7B.json", "needs": [],
     "why": "per-layer intent correlation, nomaker read by SmolLM2-1.7B"},
    {"name": "depth_nomaker_SmolLM2-1.7B", "est": 12,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "nomaker", "--model", "HuggingFaceTB/SmolLM2-1.7B"],
     "produces": "results/depth_sweep/nomaker_SmolLM2-1.7B.json", "needs": [],
     "why": "depth profile shape, nomaker read by SmolLM2-1.7B"},
    {"name": "bits24_ladder", "est": 25,
     "cmd": [PY, "runners/run_spec_recovery.py", "--corpus", "ladder", "--decoys", "24"],
     "produces": None, "needs": [],
     "why": "bits of specification recovered from ladder against 24 matched decoys"},
    {"name": "bits48_ladder", "est": 25,
     "cmd": [PY, "runners/run_spec_recovery.py", "--corpus", "ladder", "--decoys", "48"],
     "produces": None, "needs": [],
     "why": "bits of specification recovered from ladder against 48 matched decoys"},
    {"name": "bits24_ladder2", "est": 25,
     "cmd": [PY, "runners/run_spec_recovery.py", "--corpus", "ladder2", "--decoys", "24"],
     "produces": None, "needs": [],
     "why": "bits of specification recovered from ladder2 against 24 matched decoys"},
    {"name": "bits48_ladder2", "est": 25,
     "cmd": [PY, "runners/run_spec_recovery.py", "--corpus", "ladder2", "--decoys", "48"],
     "produces": None, "needs": [],
     "why": "bits of specification recovered from ladder2 against 48 matched decoys"},
    {"name": "bits24_ladder3", "est": 25,
     "cmd": [PY, "runners/run_spec_recovery.py", "--corpus", "ladder3", "--decoys", "24"],
     "produces": None, "needs": [],
     "why": "bits of specification recovered from ladder3 against 24 matched decoys"},
    {"name": "bits48_ladder3", "est": 25,
     "cmd": [PY, "runners/run_spec_recovery.py", "--corpus", "ladder3", "--decoys", "48"],
     "produces": None, "needs": [],
     "why": "bits of specification recovered from ladder3 against 48 matched decoys"},
    {"name": "features_all", "est": 30,
     "cmd": [PY, "runners/build_features.py", "--corpora", "ladder,ladder2,ladder3,nomaker,gate3,argrewrite"],
     "produces": None, "needs": [],
     "why": "cache 342 features for every corpus we hold"},
    {"name": "sweep_all", "est": 10,
     "cmd": [PY, "runners/run_feature_sweep.py", "--corpora", "ladder,ladder2,ladder3,argrewrite,gate3,n28"],
     "produces": None, "needs": [],
     "why": "re-screen every feature across every corpus including the human one"},
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


def main() -> None:
    state: dict = {"started": time.strftime("%Y-%m-%d %H:%M"), "stages": []}
    STATUS.parent.mkdir(parents=True, exist_ok=True)

    def save() -> None:
        STATUS.write_text(json.dumps(state, indent=2), encoding="utf-8", newline="\n")

    failed: set[str] = set()
    for st in STAGES:
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


if __name__ == "__main__":
    main()
