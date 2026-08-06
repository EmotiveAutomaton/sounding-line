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
    {"name": "corr_ladder2_Qwen2.5-1.5B", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder2",
             "--model", "Qwen/Qwen2.5-1.5B"],
     "produces": "results/layer_correlation/ladder2_Qwen2.5-1.5B.json", "needs": [],
     "why": "per-layer intent correlation, ladder2 read by Qwen2.5-1.5B"},
    {"name": "corr_ladder3_Qwen2.5-1.5B", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder3",
             "--model", "Qwen/Qwen2.5-1.5B"],
     "produces": "results/layer_correlation/ladder3_Qwen2.5-1.5B.json", "needs": [],
     "why": "per-layer intent correlation, ladder3 read by Qwen2.5-1.5B"},
    {"name": "corr_ladder_Qwen2.5-1.5B", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder",
             "--model", "Qwen/Qwen2.5-1.5B"],
     "produces": "results/layer_correlation/ladder_Qwen2.5-1.5B.json", "needs": [],
     "why": "per-layer intent correlation, ladder read by Qwen2.5-1.5B"},
    {"name": "corr_nomaker_Qwen2.5-1.5B", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "nomaker",
             "--model", "Qwen/Qwen2.5-1.5B"],
     "produces": "results/layer_correlation/nomaker_Qwen2.5-1.5B.json", "needs": [],
     "why": "per-layer intent correlation, nomaker read by Qwen2.5-1.5B"},
    {"name": "corr_ladder2_Qwen2.5-0.5B", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder2",
             "--model", "Qwen/Qwen2.5-0.5B"],
     "produces": "results/layer_correlation/ladder2_Qwen2.5-0.5B.json", "needs": [],
     "why": "per-layer intent correlation, ladder2 read by Qwen2.5-0.5B"},
    {"name": "corr_ladder3_Qwen2.5-0.5B", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder3",
             "--model", "Qwen/Qwen2.5-0.5B"],
     "produces": "results/layer_correlation/ladder3_Qwen2.5-0.5B.json", "needs": [],
     "why": "per-layer intent correlation, ladder3 read by Qwen2.5-0.5B"},
    {"name": "corr_ladder_Qwen2.5-0.5B", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder",
             "--model", "Qwen/Qwen2.5-0.5B"],
     "produces": "results/layer_correlation/ladder_Qwen2.5-0.5B.json", "needs": [],
     "why": "per-layer intent correlation, ladder read by Qwen2.5-0.5B"},
    {"name": "corr_nomaker_Qwen2.5-0.5B", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "nomaker",
             "--model", "Qwen/Qwen2.5-0.5B"],
     "produces": "results/layer_correlation/nomaker_Qwen2.5-0.5B.json", "needs": [],
     "why": "per-layer intent correlation, nomaker read by Qwen2.5-0.5B"},
    {"name": "corr_ladder2_pythia-1.4b", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder2",
             "--model", "EleutherAI/pythia-1.4b"],
     "produces": "results/layer_correlation/ladder2_pythia-1.4b.json", "needs": [],
     "why": "per-layer intent correlation, ladder2 read by pythia-1.4b"},
    {"name": "corr_ladder3_pythia-1.4b", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder3",
             "--model", "EleutherAI/pythia-1.4b"],
     "produces": "results/layer_correlation/ladder3_pythia-1.4b.json", "needs": [],
     "why": "per-layer intent correlation, ladder3 read by pythia-1.4b"},
    {"name": "corr_ladder_pythia-1.4b", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder",
             "--model", "EleutherAI/pythia-1.4b"],
     "produces": "results/layer_correlation/ladder_pythia-1.4b.json", "needs": [],
     "why": "per-layer intent correlation, ladder read by pythia-1.4b"},
    {"name": "corr_nomaker_pythia-1.4b", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "nomaker",
             "--model", "EleutherAI/pythia-1.4b"],
     "produces": "results/layer_correlation/nomaker_pythia-1.4b.json", "needs": [],
     "why": "per-layer intent correlation, nomaker read by pythia-1.4b"},
    {"name": "corr_ladder2_pythia-410m", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder2",
             "--model", "EleutherAI/pythia-410m"],
     "produces": "results/layer_correlation/ladder2_pythia-410m.json", "needs": [],
     "why": "per-layer intent correlation, ladder2 read by pythia-410m"},
    {"name": "corr_ladder3_pythia-410m", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder3",
             "--model", "EleutherAI/pythia-410m"],
     "produces": "results/layer_correlation/ladder3_pythia-410m.json", "needs": [],
     "why": "per-layer intent correlation, ladder3 read by pythia-410m"},
    {"name": "corr_ladder_pythia-410m", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder",
             "--model", "EleutherAI/pythia-410m"],
     "produces": "results/layer_correlation/ladder_pythia-410m.json", "needs": [],
     "why": "per-layer intent correlation, ladder read by pythia-410m"},
    {"name": "corr_nomaker_pythia-410m", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "nomaker",
             "--model", "EleutherAI/pythia-410m"],
     "produces": "results/layer_correlation/nomaker_pythia-410m.json", "needs": [],
     "why": "per-layer intent correlation, nomaker read by pythia-410m"},
    {"name": "corr_ladder2_gpt2-medium", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder2",
             "--model", "openai-community/gpt2-medium"],
     "produces": "results/layer_correlation/ladder2_gpt2-medium.json", "needs": [],
     "why": "per-layer intent correlation, ladder2 read by gpt2-medium"},
    {"name": "corr_ladder3_gpt2-medium", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder3",
             "--model", "openai-community/gpt2-medium"],
     "produces": "results/layer_correlation/ladder3_gpt2-medium.json", "needs": [],
     "why": "per-layer intent correlation, ladder3 read by gpt2-medium"},
    {"name": "corr_ladder_gpt2-medium", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder",
             "--model", "openai-community/gpt2-medium"],
     "produces": "results/layer_correlation/ladder_gpt2-medium.json", "needs": [],
     "why": "per-layer intent correlation, ladder read by gpt2-medium"},
    {"name": "corr_nomaker_gpt2-medium", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "nomaker",
             "--model", "openai-community/gpt2-medium"],
     "produces": "results/layer_correlation/nomaker_gpt2-medium.json", "needs": [],
     "why": "per-layer intent correlation, nomaker read by gpt2-medium"},
    {"name": "corr_ladder2_gpt2-large", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder2",
             "--model", "openai-community/gpt2-large"],
     "produces": "results/layer_correlation/ladder2_gpt2-large.json", "needs": [],
     "why": "per-layer intent correlation, ladder2 read by gpt2-large"},
    {"name": "corr_ladder3_gpt2-large", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder3",
             "--model", "openai-community/gpt2-large"],
     "produces": "results/layer_correlation/ladder3_gpt2-large.json", "needs": [],
     "why": "per-layer intent correlation, ladder3 read by gpt2-large"},
    {"name": "corr_ladder_gpt2-large", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder",
             "--model", "openai-community/gpt2-large"],
     "produces": "results/layer_correlation/ladder_gpt2-large.json", "needs": [],
     "why": "per-layer intent correlation, ladder read by gpt2-large"},
    {"name": "corr_nomaker_gpt2-large", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "nomaker",
             "--model", "openai-community/gpt2-large"],
     "produces": "results/layer_correlation/nomaker_gpt2-large.json", "needs": [],
     "why": "per-layer intent correlation, nomaker read by gpt2-large"},
    {"name": "corr_ladder2_SmolLM2-360M", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder2",
             "--model", "HuggingFaceTB/SmolLM2-360M"],
     "produces": "results/layer_correlation/ladder2_SmolLM2-360M.json", "needs": [],
     "why": "per-layer intent correlation, ladder2 read by SmolLM2-360M"},
    {"name": "corr_ladder3_SmolLM2-360M", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder3",
             "--model", "HuggingFaceTB/SmolLM2-360M"],
     "produces": "results/layer_correlation/ladder3_SmolLM2-360M.json", "needs": [],
     "why": "per-layer intent correlation, ladder3 read by SmolLM2-360M"},
    {"name": "corr_ladder_SmolLM2-360M", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "ladder",
             "--model", "HuggingFaceTB/SmolLM2-360M"],
     "produces": "results/layer_correlation/ladder_SmolLM2-360M.json", "needs": [],
     "why": "per-layer intent correlation, ladder read by SmolLM2-360M"},
    {"name": "corr_nomaker_SmolLM2-360M", "est": 3,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "nomaker",
             "--model", "HuggingFaceTB/SmolLM2-360M"],
     "produces": "results/layer_correlation/nomaker_SmolLM2-360M.json", "needs": [],
     "why": "per-layer intent correlation, nomaker read by SmolLM2-360M"},
    {"name": "depth_ladder2_Qwen2.5-1.5B", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder2",
             "--model", "Qwen/Qwen2.5-1.5B"],
     "produces": "results/depth_sweep/ladder2_Qwen2.5-1.5B.json", "needs": [],
     "why": "depth profile shape, ladder2 read by Qwen2.5-1.5B"},
    {"name": "depth_ladder3_Qwen2.5-1.5B", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder3",
             "--model", "Qwen/Qwen2.5-1.5B"],
     "produces": "results/depth_sweep/ladder3_Qwen2.5-1.5B.json", "needs": [],
     "why": "depth profile shape, ladder3 read by Qwen2.5-1.5B"},
    {"name": "depth_ladder_Qwen2.5-1.5B", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder",
             "--model", "Qwen/Qwen2.5-1.5B"],
     "produces": "results/depth_sweep/ladder_Qwen2.5-1.5B.json", "needs": [],
     "why": "depth profile shape, ladder read by Qwen2.5-1.5B"},
    {"name": "depth_nomaker_Qwen2.5-1.5B", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "nomaker",
             "--model", "Qwen/Qwen2.5-1.5B"],
     "produces": "results/depth_sweep/nomaker_Qwen2.5-1.5B.json", "needs": [],
     "why": "depth profile shape, nomaker read by Qwen2.5-1.5B"},
    {"name": "depth_ladder2_Qwen2.5-0.5B", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder2",
             "--model", "Qwen/Qwen2.5-0.5B"],
     "produces": "results/depth_sweep/ladder2_Qwen2.5-0.5B.json", "needs": [],
     "why": "depth profile shape, ladder2 read by Qwen2.5-0.5B"},
    {"name": "depth_ladder3_Qwen2.5-0.5B", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder3",
             "--model", "Qwen/Qwen2.5-0.5B"],
     "produces": "results/depth_sweep/ladder3_Qwen2.5-0.5B.json", "needs": [],
     "why": "depth profile shape, ladder3 read by Qwen2.5-0.5B"},
    {"name": "depth_ladder_Qwen2.5-0.5B", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder",
             "--model", "Qwen/Qwen2.5-0.5B"],
     "produces": "results/depth_sweep/ladder_Qwen2.5-0.5B.json", "needs": [],
     "why": "depth profile shape, ladder read by Qwen2.5-0.5B"},
    {"name": "depth_nomaker_Qwen2.5-0.5B", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "nomaker",
             "--model", "Qwen/Qwen2.5-0.5B"],
     "produces": "results/depth_sweep/nomaker_Qwen2.5-0.5B.json", "needs": [],
     "why": "depth profile shape, nomaker read by Qwen2.5-0.5B"},
    {"name": "depth_ladder2_pythia-1.4b", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder2",
             "--model", "EleutherAI/pythia-1.4b"],
     "produces": "results/depth_sweep/ladder2_pythia-1.4b.json", "needs": [],
     "why": "depth profile shape, ladder2 read by pythia-1.4b"},
    {"name": "depth_ladder3_pythia-1.4b", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder3",
             "--model", "EleutherAI/pythia-1.4b"],
     "produces": "results/depth_sweep/ladder3_pythia-1.4b.json", "needs": [],
     "why": "depth profile shape, ladder3 read by pythia-1.4b"},
    {"name": "depth_ladder_pythia-1.4b", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder",
             "--model", "EleutherAI/pythia-1.4b"],
     "produces": "results/depth_sweep/ladder_pythia-1.4b.json", "needs": [],
     "why": "depth profile shape, ladder read by pythia-1.4b"},
    {"name": "depth_nomaker_pythia-1.4b", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "nomaker",
             "--model", "EleutherAI/pythia-1.4b"],
     "produces": "results/depth_sweep/nomaker_pythia-1.4b.json", "needs": [],
     "why": "depth profile shape, nomaker read by pythia-1.4b"},
    {"name": "depth_ladder2_pythia-410m", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder2",
             "--model", "EleutherAI/pythia-410m"],
     "produces": "results/depth_sweep/ladder2_pythia-410m.json", "needs": [],
     "why": "depth profile shape, ladder2 read by pythia-410m"},
    {"name": "depth_ladder3_pythia-410m", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder3",
             "--model", "EleutherAI/pythia-410m"],
     "produces": "results/depth_sweep/ladder3_pythia-410m.json", "needs": [],
     "why": "depth profile shape, ladder3 read by pythia-410m"},
    {"name": "depth_ladder_pythia-410m", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder",
             "--model", "EleutherAI/pythia-410m"],
     "produces": "results/depth_sweep/ladder_pythia-410m.json", "needs": [],
     "why": "depth profile shape, ladder read by pythia-410m"},
    {"name": "depth_nomaker_pythia-410m", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "nomaker",
             "--model", "EleutherAI/pythia-410m"],
     "produces": "results/depth_sweep/nomaker_pythia-410m.json", "needs": [],
     "why": "depth profile shape, nomaker read by pythia-410m"},
    {"name": "depth_ladder2_gpt2-medium", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder2",
             "--model", "openai-community/gpt2-medium"],
     "produces": "results/depth_sweep/ladder2_gpt2-medium.json", "needs": [],
     "why": "depth profile shape, ladder2 read by gpt2-medium"},
    {"name": "depth_ladder3_gpt2-medium", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder3",
             "--model", "openai-community/gpt2-medium"],
     "produces": "results/depth_sweep/ladder3_gpt2-medium.json", "needs": [],
     "why": "depth profile shape, ladder3 read by gpt2-medium"},
    {"name": "depth_ladder_gpt2-medium", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder",
             "--model", "openai-community/gpt2-medium"],
     "produces": "results/depth_sweep/ladder_gpt2-medium.json", "needs": [],
     "why": "depth profile shape, ladder read by gpt2-medium"},
    {"name": "depth_nomaker_gpt2-medium", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "nomaker",
             "--model", "openai-community/gpt2-medium"],
     "produces": "results/depth_sweep/nomaker_gpt2-medium.json", "needs": [],
     "why": "depth profile shape, nomaker read by gpt2-medium"},
    {"name": "depth_ladder2_gpt2-large", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder2",
             "--model", "openai-community/gpt2-large"],
     "produces": "results/depth_sweep/ladder2_gpt2-large.json", "needs": [],
     "why": "depth profile shape, ladder2 read by gpt2-large"},
    {"name": "depth_ladder3_gpt2-large", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder3",
             "--model", "openai-community/gpt2-large"],
     "produces": "results/depth_sweep/ladder3_gpt2-large.json", "needs": [],
     "why": "depth profile shape, ladder3 read by gpt2-large"},
    {"name": "depth_ladder_gpt2-large", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder",
             "--model", "openai-community/gpt2-large"],
     "produces": "results/depth_sweep/ladder_gpt2-large.json", "needs": [],
     "why": "depth profile shape, ladder read by gpt2-large"},
    {"name": "depth_nomaker_gpt2-large", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "nomaker",
             "--model", "openai-community/gpt2-large"],
     "produces": "results/depth_sweep/nomaker_gpt2-large.json", "needs": [],
     "why": "depth profile shape, nomaker read by gpt2-large"},
    {"name": "depth_ladder2_SmolLM2-360M", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder2",
             "--model", "HuggingFaceTB/SmolLM2-360M"],
     "produces": "results/depth_sweep/ladder2_SmolLM2-360M.json", "needs": [],
     "why": "depth profile shape, ladder2 read by SmolLM2-360M"},
    {"name": "depth_ladder3_SmolLM2-360M", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder3",
             "--model", "HuggingFaceTB/SmolLM2-360M"],
     "produces": "results/depth_sweep/ladder3_SmolLM2-360M.json", "needs": [],
     "why": "depth profile shape, ladder3 read by SmolLM2-360M"},
    {"name": "depth_ladder_SmolLM2-360M", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "ladder",
             "--model", "HuggingFaceTB/SmolLM2-360M"],
     "produces": "results/depth_sweep/ladder_SmolLM2-360M.json", "needs": [],
     "why": "depth profile shape, ladder read by SmolLM2-360M"},
    {"name": "depth_nomaker_SmolLM2-360M", "est": 3,
     "cmd": [PY, "runners/run_depth_sweep.py", "--corpus", "nomaker",
             "--model", "HuggingFaceTB/SmolLM2-360M"],
     "produces": "results/depth_sweep/nomaker_SmolLM2-360M.json", "needs": [],
     "why": "depth profile shape, nomaker read by SmolLM2-360M"},
    {"name": "bits_ladder_8", "est": 4,
     "cmd": [PY, "runners/run_spec_recovery.py", "--corpus", "ladder", "--decoys", "8"],
     "produces": None, "needs": [],
     "why": "bits of specification recovered from ladder, against 8 decoys"},
    {"name": "bits_ladder_16", "est": 4,
     "cmd": [PY, "runners/run_spec_recovery.py", "--corpus", "ladder", "--decoys", "16"],
     "produces": None, "needs": [],
     "why": "bits of specification recovered from ladder, against 16 decoys"},
    {"name": "bits_ladder2_8", "est": 4,
     "cmd": [PY, "runners/run_spec_recovery.py", "--corpus", "ladder2", "--decoys", "8"],
     "produces": None, "needs": [],
     "why": "bits of specification recovered from ladder2, against 8 decoys"},
    {"name": "bits_ladder2_16", "est": 4,
     "cmd": [PY, "runners/run_spec_recovery.py", "--corpus", "ladder2", "--decoys", "16"],
     "produces": None, "needs": [],
     "why": "bits of specification recovered from ladder2, against 16 decoys"},
    {"name": "bits_ladder3_8", "est": 4,
     "cmd": [PY, "runners/run_spec_recovery.py", "--corpus", "ladder3", "--decoys", "8"],
     "produces": None, "needs": [],
     "why": "bits of specification recovered from ladder3, against 8 decoys"},
    {"name": "bits_ladder3_16", "est": 4,
     "cmd": [PY, "runners/run_spec_recovery.py", "--corpus", "ladder3", "--decoys", "16"],
     "produces": None, "needs": [],
     "why": "bits of specification recovered from ladder3, against 16 decoys"},
    {"name": "length_direction_audit", "est": 2,
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
