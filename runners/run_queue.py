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
    {"name": "ladder3_gen", "est": 150,
     "cmd": [PY, "runners/make_ladder3.py"],
     "produces": "corpora/ladder3/r60_14.json", "needs": [],
     "why": "the curator's extreme ladder, length fixed by rejection sampling"},

    {"name": "ladder3_score", "est": 20,
     "cmd": [PY, "runners/score_ladder.py", "--corpus", "ladder3"],
     "produces": "results/ladder3/score.json", "needs": ["corpora/ladder3/r60_14.json"],
     "why": "layer ratio on a corpus where length cannot be the explanation"},

    {"name": "features_ladder3", "est": 25,
     "cmd": [PY, "runners/build_features.py", "--corpora", "ladder3"],
     "produces": "results/features/ladder3.json", "needs": ["corpora/ladder3/r60_14.json"],
     "why": "342 features on the extreme ladder"},

    {"name": "sweep_all", "est": 15,
     "cmd": [PY, "runners/run_feature_sweep.py", "--corpora",
             "ladder,ladder2,ladder3,gate3,n28"],
     "produces": None, "needs": ["results/features/ladder3.json"],
     "why": "re-screen every feature now that a length-free ladder exists"},

    {"name": "length_direction_audit", "est": 20,
     "cmd": [PY, "runners/audit_length_direction.py"],
     "produces": "results/audit/length_direction.json", "needs": [],
     "why": "weakness 3b — every measure killed on a length correlation, re-checked for SIGN"},

    {"name": "fetch_corpora", "est": 40,
     "cmd": [PY, "runners/fetch_public_corpora.py"],
     "produces": "corpora/public/MANIFEST.json", "needs": [],
     "why": "ArgRewrite, Wikipedia quality classes, RAID — the human-text problem"},

    {"name": "multiplicity", "est": 1,
     "cmd": [PY, "runners/audit_multiplicity.py"],
     "produces": None, "needs": [],
     "why": "re-run the correction family after new results land"},
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
                                   stderr=subprocess.STDOUT, timeout=st["est"] * 60 * 4)
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
