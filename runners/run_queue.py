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
    # ── DAY10b 2026-08-09 night: Phase 1 frontier recreations (G136, G138) + the event dataset
    {"name": "arg_extract", "est": 10,
     "cmd": [PY, "runners/run_arg_baselines.py", "--arm", "extract"],
     "produces": "results/arg_baselines/events.json", "needs": [],
     "why": "G136 input: every labelled revision as a choice event -- also G129's dataset"},
    {"name": "arg_features", "est": 15,
     "cmd": [PY, "runners/run_arg_baselines.py", "--arm", "features"],
     "produces": "results/arg_baselines/features.json",
     "needs": ["results/arg_baselines/events.json"],
     "why": "G136: recreate the published classification task, feature arm, author-split"},
    {"name": "arg_reader_12_coarse", "est": 100,
     "cmd": [PY, "runners/run_arg_baselines.py", "--arm", "reader", "--cycle", "12", "--grain", "coarse"],
     "produces": "results/arg_baselines/reader_12_coarse.json",
     "needs": ["results/arg_baselines/events.json"],
     "why": "G136: reader arm, first revision cycle, coarse -- checkpointed, resumes across passes"},
    {"name": "arg_reader_12_fine", "est": 110,
     "cmd": [PY, "runners/run_arg_baselines.py", "--arm", "reader", "--cycle", "12", "--grain", "fine"],
     "produces": "results/arg_baselines/reader_12_fine.json",
     "needs": ["results/arg_baselines/events.json"],
     "why": "G136: reader arm, first cycle, fine purposes"},
    {"name": "arg_reader_23_coarse", "est": 100,
     "cmd": [PY, "runners/run_arg_baselines.py", "--arm", "reader", "--cycle", "23", "--grain", "coarse"],
     "produces": "results/arg_baselines/reader_23_coarse.json",
     "needs": ["results/arg_baselines/events.json"],
     "why": "G136: reader arm, second revision cycle, coarse"},
    {"name": "arg_reader_23_fine", "est": 110,
     "cmd": [PY, "runners/run_arg_baselines.py", "--arm", "reader", "--cycle", "23", "--grain", "fine"],
     "produces": "results/arg_baselines/reader_23_fine.json",
     "needs": ["results/arg_baselines/events.json"],
     "why": "G136: reader arm, second cycle, fine"},
    {"name": "am_construction", "est": 60,
     "cmd": [PY, "runners/run_am_construction.py"],
     "produces": "results/am_construction/summary.json", "needs": [],
     "why": "G138: reproduce the impossibility degeneracy exactly, then relax it with the three human priors"},
    # ── DAY12 2026-08-10: pilot-c (analytic floor), CEM matching v2, replication v3 refire
    {"name": "argrec_fine_k4ub_recovery", "est": 40,
     "cmd": [PY, "runners/run_arg_recovery.py", "--grain", "fine", "--k", "4",
             "--arm", "recovery", "--uniform", "--balance"],
     "produces": "results/arg_recovery/fine_k4ub_recovery.json",
     "needs": ["results/arg_baselines/events.json"],
     "why": "G129-pilot-c: truth-balanced, the floor is analytic at 1/k -- the quotable design"},
    {"name": "argrec_fine_k4ub_blind", "est": 40,
     "cmd": [PY, "runners/run_arg_recovery.py", "--grain", "fine", "--k", "4",
             "--arm", "blind", "--uniform", "--balance"],
     "produces": "results/arg_recovery/fine_k4ub_blind.json",
     "needs": ["results/arg_baselines/events.json"],
     "why": "G129-pilot-c control: blind must now sit at 0.25 or the construction is still leaking"},
    {"name": "argrec_matched_recovery", "est": 35,
     "cmd": [PY, "runners/run_arg_matched_recovery.py", "--arm", "recovery"],
     "produces": "results/arg_recovery/matched_k4_recovery.json",
     "needs": ["results/arg_baselines/events.json"],
     "why": "G130c: the collision -- does the recovery margin survive the matching that killed content-ness?"},
    {"name": "argrec_matched_blind", "est": 35,
     "cmd": [PY, "runners/run_arg_matched_recovery.py", "--arm", "blind"],
     "produces": "results/arg_recovery/matched_k4_blind.json",
     "needs": ["results/arg_baselines/events.json"],
     "why": "G130c control: the matched subset's own blind floor"},
    # ── NIGHT11 2026-08-10: the overnight program -- recreations, controls, and the pilot redesign
    {"name": "arg_matched_control", "est": 25,
     "cmd": [PY, "runners/run_arg_matched.py"],
     "produces": "results/arg_baselines/matched_control.json",
     "needs": ["results/arg_baselines/events.json"],
     "why": "G130b: the decisive lexical-matching control -- does 'content' survive matching?"},
    # bst_gridworld DISABLED 2026-08-14 (second referee, item 7): the 4-action model's
    # summary is archived as summary_4action.json; the 9-action rebuild gets its own stage
    {"name": "scholawrite_download", "est": 25,
     "cmd": [PY, "runners/run_scholawrite.py", "--arm", "download"],
     "produces": "results/scholawrite/schema.json",
     "needs": ["results/scholawrite/HF_TOKEN_PRESENT"],
     "why": "G141 input: the dataset, schema dumped, fail-loudly on surprise"},
    {"name": "scholawrite_bert", "est": 200,
     "cmd": [PY, "runners/run_scholawrite.py", "--arm", "bert"],
     "produces": "results/scholawrite/bert.json",
     "needs": ["results/scholawrite/schema.json"],
     "why": "G141: fine-tuned BERT against the published 0.64 weighted F1"},
    {"name": "scholawrite_roberta", "est": 200,
     "cmd": [PY, "runners/run_scholawrite.py", "--arm", "roberta"],
     "produces": "results/scholawrite/roberta.json",
     "needs": ["results/scholawrite/schema.json"],
     "why": "G141: fine-tuned RoBERTa against the published 0.64"},
    {"name": "scholawrite_reader", "est": 90,
     "cmd": [PY, "runners/run_scholawrite.py", "--arm", "reader"],
     "produces": "results/scholawrite/reader.json",
     "needs": ["results/scholawrite/schema.json"],
     "why": "G141: zero-shot local reader, the analogue of their 0.13 Llama baseline"},
    {"name": "argrec_fine_k4u_recovery", "est": 45,
     "cmd": [PY, "runners/run_arg_recovery.py", "--grain", "fine", "--k", "4",
             "--arm", "recovery", "--uniform"],
     "produces": "results/arg_recovery/fine_k4u_recovery.json",
     "needs": ["results/arg_baselines/events.json"],
     "why": "G129-pilot-b: uniform candidates -- the prior-leak fix (L62)"},
    {"name": "argrec_fine_k4u_blind", "est": 45,
     "cmd": [PY, "runners/run_arg_recovery.py", "--grain", "fine", "--k", "4",
             "--arm", "blind", "--uniform"],
     "produces": "results/arg_recovery/fine_k4u_blind.json",
     "needs": ["results/arg_baselines/events.json"],
     "why": "G129-pilot-b control: blind must sit at chance under uniform candidates"},
    {"name": "argrec_fine_k4u_shuffle", "est": 45,
     "cmd": [PY, "runners/run_arg_recovery.py", "--grain", "fine", "--k", "4",
             "--arm", "shuffle", "--uniform"],
     "produces": "results/arg_recovery/fine_k4u_shuffle.json",
     "needs": ["results/arg_baselines/events.json"],
     "why": "G129-pilot-b control: shuffled truth at chance"},
    {"name": "argrec_coarse_k2_blind", "est": 40,
     "cmd": [PY, "runners/run_arg_recovery.py", "--grain", "coarse", "--k", "2",
             "--arm", "blind"],
     "produces": "results/arg_recovery/coarse_k2_blind.json",
     "needs": ["results/arg_baselines/events.json"],
     "why": "G129-pilot: the coarse arm's missing blind control"},
    {"name": "argrec_coarse_k2_shuffle", "est": 40,
     "cmd": [PY, "runners/run_arg_recovery.py", "--grain", "coarse", "--k", "2",
             "--arm", "shuffle"],
     "produces": "results/arg_recovery/coarse_k2_shuffle.json",
     "needs": ["results/arg_baselines/events.json"],
     "why": "G129-pilot: the coarse arm's missing shuffle control"},
    {"name": "argrec_fine_k12u_recovery", "est": 55,
     "cmd": [PY, "runners/run_arg_recovery.py", "--grain", "fine", "--k", "12",
             "--arm", "recovery", "--uniform"],
     "produces": "results/arg_recovery/fine_k8u_recovery.json",
     "needs": ["results/arg_baselines/events.json"],
     "why": "G129-pilot-b: the candidate-size curve's third point (capped at the label count)"},
    # ── DAY10d: the capability pass -- recreate the paper's exact numbers (his standard, 08-10)
    {"name": "arg_replication", "est": 90,
     "cmd": [PY, "runners/run_arg_replication.py"],
     "produces": "results/arg_baselines/replication.json", "needs": [],
     "why": "G136-exact: their features, their USE encoder, their XGBoost grid, their 5-fold -- PASS only at two-decimal match"},
    # ── DAY10c: G129-pilot (zero-shot choice recovery, preregistered in the runner) + PD-33 replication
    {"name": "argrec_coarse_k2_recovery", "est": 40,
     "cmd": [PY, "runners/run_arg_recovery.py", "--grain", "coarse", "--k", "2", "--arm", "recovery"],
     "produces": "results/arg_recovery/coarse_k2_recovery.json",
     "needs": ["results/arg_baselines/events.json"],
     "why": "G129-pilot: can the reader pick the recorded coarse purpose from the delta?"},
    {"name": "argrec_fine_k4_recovery", "est": 50,
     "cmd": [PY, "runners/run_arg_recovery.py", "--grain", "fine", "--k", "4", "--arm", "recovery"],
     "produces": "results/arg_recovery/fine_k4_recovery.json",
     "needs": ["results/arg_baselines/events.json"],
     "why": "G129-pilot: fine purposes, four candidates"},
    {"name": "argrec_fine_k8_recovery", "est": 50,
     "cmd": [PY, "runners/run_arg_recovery.py", "--grain", "fine", "--k", "8", "--arm", "recovery"],
     "produces": "results/arg_recovery/fine_k8_recovery.json",
     "needs": ["results/arg_baselines/events.json"],
     "why": "G129-pilot: fine purposes, eight candidates -- the candidate-size curve"},
    {"name": "argrec_fine_k4_blind", "est": 45,
     "cmd": [PY, "runners/run_arg_recovery.py", "--grain", "fine", "--k", "4", "--arm", "blind"],
     "produces": "results/arg_recovery/fine_k4_blind.json",
     "needs": ["results/arg_baselines/events.json"],
     "why": "G129-pilot control: no delta shown -- must sit at chance"},
    {"name": "argrec_fine_k4_shuffle", "est": 45,
     "cmd": [PY, "runners/run_arg_recovery.py", "--grain", "fine", "--k", "4", "--arm", "shuffle"],
     "produces": "results/arg_recovery/fine_k4_shuffle.json",
     "needs": ["results/arg_baselines/events.json"],
     "why": "G129-pilot control: shuffled truth -- must sit at chance"},
    {"name": "books_w80_cache", "est": 45,
     "cmd": [PY, "runners/build_features.py", "--corpora", "books", "--window", "80",
             "--suffix", "_w80"],
     "produces": "results/features/books_w80.json", "needs": [],
     "why": "PD-33 replication input: a second windowed cache with author labels"},
    {"name": "pd33_books", "est": 10,
     "cmd": [PY, "runners/run_pd33_books.py"],
     "produces": "results/positional_polish/pd33_books.json",
     "needs": ["results/features/books_w80.json"],
     "why": "PD-33 replication: does the polish-side author-share excess hold on books?"},
    # ── DAY10 2026-08-09 evening: the program's first buildable stages, in program order
    {"name": "event_harness_synthetic", "est": 5,
     "cmd": [PY, "runners/run_event_harness.py"],
     "produces": "results/event_harness/synthetic_validation.json", "needs": [],
     "why": "G130: the shared choice-recovery harness must pass five known-answer gates before any real corpus"},
    {"name": "pd33_decomposition", "est": 5,
     "cmd": [PY, "runners/run_pd33_decomposition.py"],
     "produces": "results/positional_polish/pd33_decomposition.json",
     "needs": ["results/features/argrewrite_w80.json"],
     "why": "PD-33: does the polish side's essay-boundness follow the author (maker signature) or the draft (state)?"},
    {"name": "cka_null_g128", "est": 45,
     "cmd": [PY, "runners/run_cka_null.py"],
     "produces": "results/cka_alignment/null_g128.json", "needs": [],
     "why": "G128: the permutation null L45's alignment still owes -- real correspondence or matrix smoothness?"},
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
     "produces": "results/audit/length_direction.json", "needs": [],
     "why": "was length a confound or a suppressor, per measure"},
    {"name": "multiplicity", "est": 1,
     "cmd": [PY, "runners/audit_multiplicity.py"],
     "produces": None, "needs": [],
     "why": "re-correct the whole family after new results land"},
]

# ── BUILD DAY 2026-08-09 — ten new instruments, loaded deep. CPU first, GPU, Ollama last.
STAGES_DAY9 = [
    {"name": "revision_homogeneity", "est": 6,
     "cmd": [PY, "runners/run_revision_homogeneity.py"],
     "produces": "results/revision_homogeneity/summary.json", "needs": [],
     "why": "G81: self-revision homogeneous vs imposed lumpy, with a synthetic-splice control"},
    {"name": "revision_purpose", "est": 12,
     "cmd": [PY, "runners/run_revision_purpose.py"],
     "produces": "results/revision_purpose/summary.json", "needs": [],
     "why": "PD-28: polish or the first depth signal on human text — the labels were on disk all along"},
    {"name": "feature_visibility", "est": 20,
     "cmd": [PY, "runners/run_feature_visibility.py"],
     "produces": "results/feature_visibility/summary.json", "needs": [],
     "why": "G87: low-visibility features carry who, high-visibility carry what"},
    {"name": "argrewrite_w80_cache", "est": 25,
     "cmd": [PY, "runners/build_features.py", "--corpora", "argrewrite", "--window", "80",
             "--suffix", "_w80"],
     "produces": "results/features/argrewrite_w80.json", "needs": [],
     "why": "G119 input: the small-window cache positional analysis needs"},
    {"name": "positional_polish", "est": 5,
     "cmd": [PY, "runners/run_positional_polish.py"],
     "produces": "results/positional_polish/summary.json",
     "needs": ["results/features/argrewrite_w80.json"],
     "why": "PD-1 at last: the definitional polish/depth test — the file's own falsifier"},
    {"name": "pooling_falsifier", "est": 40,
     "cmd": [PY, "runners/run_pooling_falsifier.py"],
     "produces": "results/pooling_falsifier/Qwen2.5-1.5B.json", "needs": [],
     "why": "G127: does the early/late story survive last-token and max pooling?"},
    {"name": "cka_alignment", "est": 45,
     "cmd": [PY, "runners/run_cka_alignment.py"],
     "produces": "results/cka_alignment/summary.json", "needs": [],
     "why": "G124: align families by computational events; where do the loci actually land?"},
    {"name": "reader_convergence3", "est": 80,
     "cmd": [PY, "runners/run_reader_convergence3.py"],
     "produces": "results/reader_convergence/summary_v3.json", "needs": [],
     "why": "G114b: judge-rated goal similarity + fixed-topic dose — the discriminator, rebuilt"},
]
for _m in ("Qwen/Qwen2.5-1.5B", "openai-community/gpt2-medium", "EleutherAI/pythia-1.4b",
           "HuggingFaceTB/SmolLM2-360M", "Qwen/Qwen2.5-0.5B", "openai-community/gpt2-large",
           "EleutherAI/pythia-410m", "HuggingFaceTB/SmolLM2-1.7B"):
    _t = _m.split("/")[-1]
    STAGES_DAY9.append({"name": f"coherence_v2_{_t}", "est": 20,
                        "cmd": [PY, "runners/run_coherence_v2.py", "--model", _m],
                        "produces": f"results/coherence_v2/{_t}.json", "needs": [],
                        "why": "G105: the rebuilt agreement statistic, known-answer gated — re-adjudicates G33"})
for _m in ("Qwen/Qwen2.5-1.5B", "openai-community/gpt2-medium", "EleutherAI/pythia-1.4b",
           "HuggingFaceTB/SmolLM2-360M", "openai-community/gpt2-large", "Qwen/Qwen2.5-0.5B",
           "EleutherAI/pythia-410m", "HuggingFaceTB/SmolLM2-1.7B"):
    _t = _m.split("/")[-1]
    STAGES_DAY9.append({"name": f"block_contribution_{_t}", "est": 20,
                        "cmd": [PY, "runners/run_block_contribution.py", "--model", _m],
                        "produces": f"results/block_contribution/{_t}.json", "needs": [],
                        "why": "G126: write norm, affect work, d-prime — the defensible per-block quantities"})
for _m in ("Qwen/Qwen2.5-1.5B", "openai-community/gpt2-medium", "EleutherAI/pythia-1.4b",
           "HuggingFaceTB/SmolLM2-360M", "Qwen/Qwen2.5-0.5B", "openai-community/gpt2-large",
           "openai-community/gpt2-xl", "EleutherAI/pythia-410m", "EleutherAI/pythia-2.8b",
           "HuggingFaceTB/SmolLM2-1.7B", "Qwen/Qwen2.5-3B"):
    _t = _m.split("/")[-1]
    STAGES_DAY9.append({"name": f"control_subspaces_{_t}", "est": 12,
                        "cmd": [PY, "runners/run_control_subspaces.py", "--model", _m],
                        "produces": f"results/control_subspaces/{_t}.json", "needs": [],
                        "why": "G43: is the early break affective or the input adapter's edge?"})
    STAGES_DAY9.append({"name": f"subspace_v2_{_t}", "est": 5,
                        "cmd": [PY, "runners/run_subspace_alignment.py", "--model", _m],
                        "produces": f"results/subspace/{_t}.json", "needs": [],
                        "why": "G111: regenerate under the rank-truncated basis and distant-matched null"})
for _m in ("HuggingFaceTB/SmolLM2-360M", "Qwen/Qwen2.5-0.5B", "Qwen/Qwen2.5-3B",
           "openai-community/gpt2-large", "openai-community/gpt2-xl",
           "EleutherAI/pythia-410m", "EleutherAI/pythia-2.8b", "HuggingFaceTB/SmolLM2-1.7B"):
    _t = _m.split("/")[-1]
    STAGES_DAY9.append({"name": f"binary_powered_{_t}", "est": 40,
                        "cmd": [PY, "runners/run_binary_salience.py", "--model", _m,
                                "--neutral-per", "500"],
                        "produces": f"results/binary_salience/{_t}_powered.json", "needs": [],
                        "why": "G21b map: where does the presence peak sit, family by family?"})
STAGES = STAGES_DAY9 + STAGES

# ── NIGHT LOAD 2026-08-08 — generated blocks: explicit model lists, deterministic order, every
# stage produces-guarded. Heavy models are spaced inside each corpus block so two shards rarely
# co-load more than ~9 GB; a rare unlucky alignment fails once and retries next pass.
_NIGHT_IND = ["openai-community/gpt2-xl", "Qwen/Qwen2.5-0.5B", "EleutherAI/pythia-2.8b",
              "EleutherAI/pythia-410m", "Qwen/Qwen2.5-3B", "HuggingFaceTB/SmolLM2-1.7B",
              "openai-community/gpt2-large"]
for _c in ("ladder", "ladder2", "ladder3"):
    for _m in _NIGHT_IND:
        _t = _m.split("/")[-1]
        STAGES.append({"name": f"induction_v2_{_c}_{_t}", "est": 20,
                       "cmd": [PY, "runners/run_induction_v2.py", "--corpus", _c, "--model", _m],
                       "produces": f"results/induction_v2/{_c}_{_t}.json", "needs": [],
                       "why": "L28 completion: the family-sign map, all 11 families x 3 ladders"})
for _m in ("HuggingFaceTB/SmolLM2-1.7B", "openai-community/gpt2-xl", "EleutherAI/pythia-2.8b"):
    _t = _m.split("/")[-1]
    STAGES.append({"name": f"readouts_{_t}", "est": 15,
                   "cmd": [PY, "runners/run_depth_readouts.py", "--model", _m],
                   "produces": f"results/depth_readouts/{_t}.json", "needs": [],
                   "why": "G104 completion: v2-rule readouts for the last three families"})
for _m in ("Qwen/Qwen2.5-3B", "HuggingFaceTB/SmolLM2-1.7B",
           "openai-community/gpt2-xl", "EleutherAI/pythia-2.8b"):
    _t = _m.split("/")[-1]
    for _c in ("ladder", "ladder3"):
        STAGES.append({"name": f"layercorr_{_c}_{_t}", "est": 15,
                       "cmd": [PY, "runners/run_layer_correlation.py",
                               "--corpus", _c, "--model", _m],
                       "produces": f"results/layer_correlation/{_c}_{_t}.json", "needs": [],
                       "why": "L12 matrix completion: one of the 8 missing ladder cells"})
STAGES += [
    {"name": "specrec_ladder_d96", "est": 30,
     "cmd": [PY, "runners/run_spec_recovery.py", "--corpus", "ladder", "--decoys", "96"],
     "produces": "results/spec_recovery/ladder_d96.json", "needs": [],
     "why": "L19: halve the chance rate on the first ladder (decoys-tagged filename, no overwrite)"},
    {"name": "specrec_ladder2_d96", "est": 40,
     "cmd": [PY, "runners/run_spec_recovery.py", "--corpus", "ladder2", "--decoys", "96"],
     "produces": "results/spec_recovery/ladder2_d96.json", "needs": [],
     "why": "L19: halve the chance rate on the held-out ladder"},
    {"name": "specrec_ladder2_echo50", "est": 40,
     "cmd": [PY, "runners/run_spec_recovery.py", "--corpus", "ladder2", "--decoys", "96",
             "--echo-threshold", "0.5"],
     "produces": "results/spec_recovery/ladder2_echo50.json", "needs": [],
     "why": "G113: graded echo — does recovery survive at half-overlap specs?"},
    {"name": "specrec_ladder2_echo25", "est": 40,
     "cmd": [PY, "runners/run_spec_recovery.py", "--corpus", "ladder2", "--decoys", "96",
             "--echo-threshold", "0.25"],
     "produces": "results/spec_recovery/ladder2_echo25.json", "needs": [],
     "why": "G113: graded echo at quarter-overlap"},
    {"name": "specrec_ladder_noecho", "est": 30,
     "cmd": [PY, "runners/run_spec_recovery.py", "--corpus", "ladder", "--decoys", "96",
             "--no-echo"],
     "produces": "results/spec_recovery/ladder_noecho.json", "needs": [],
     "why": "G113: does the strict echo kill replicate on the first ladder?"},
    {"name": "provenance_ladder", "est": 30,
     "cmd": [PY, "runners/run_provenance_framing.py", "--corpus", "ladder"],
     "produces": "results/provenance_framing/ladder.json", "needs": [],
     "why": "G115 replication arm, first ladder"},
    {"name": "provenance_ladder3", "est": 35,
     "cmd": [PY, "runners/run_provenance_framing.py", "--corpus", "ladder3"],
     "produces": "results/provenance_framing/ladder3.json", "needs": [],
     "why": "G115 replication arm, extreme ladder"},
    {"name": "binary_powered_gpt2-medium", "est": 40,
     "cmd": [PY, "runners/run_binary_salience.py", "--model", "openai-community/gpt2-medium",
             "--neutral-per", "500"],
     "produces": "results/binary_salience/gpt2-medium_powered.json", "needs": [],
     "why": "G21b cross-family: is layer-0-as-presence-peak a Qwen fact or an architecture fact?"},
    {"name": "binary_powered_pythia-1.4b", "est": 40,
     "cmd": [PY, "runners/run_binary_salience.py", "--model", "EleutherAI/pythia-1.4b",
             "--neutral-per", "500"],
     "produces": "results/binary_salience/pythia-1.4b_powered.json", "needs": [],
     "why": "G21b cross-family, second architecture"},
    {"name": "activation_variance", "est": 45,
     "cmd": [PY, "runners/run_activation_variance.py"],
     "produces": "results/activation_variance/summary.json", "needs": [],
     "why": "HH-3/PD-3: within-artifact variance of the reader's affective series — not pre-empted by anyone"},
    {"name": "layercorr_nomaker_sig", "est": 15,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "nomaker",
             "--model", "Qwen/Qwen2.5-1.5B", "--save-signals"],
     "produces": "results/layer_correlation/nomaker_Qwen2.5-1.5B_sig.json", "needs": [],
     "why": "G107 input: the per-artifact signal matrix the permutation null needs"},
    {"name": "nomaker_permutation", "est": 5,
     "cmd": [PY, "runners/run_nomaker_permutation.py"],
     "produces": "results/audit/nomaker_permutation.json",
     "needs": ["results/layer_correlation/nomaker_Qwen2.5-1.5B_sig.json"],
     "why": "G107: clustered luck or label leak — the flagship control question, decided by permutation"},
]

# ── NIGHT12 2026-08-10: overnight + workday — ScholaWrite protocol arms and PD-34.
# The encoder stages serialize themselves on one GPU through results/.gpu.lock inside the
# runner, so the night shards cannot collide on the card.
STAGES += [
    {"name": "pd34_argrewrite", "est": 25,
     "cmd": [PY, "runners/run_pd34_movement.py",
             "--cache", "results/features/argrewrite_w80.json",
             "--out", "results/positional_polish/pd34_argrewrite.json"],
     "produces": "results/positional_polish/pd34_argrewrite.json",
     "needs": ["results/features/argrewrite_w80.json"],
     "why": "PD-34: polish movement in the order-sensitive form PD-1's void demanded, essays"},
    {"name": "pd34_books", "est": 25,
     "cmd": [PY, "runners/run_pd34_movement.py",
             "--cache", "results/features/books_w80.json",
             "--out", "results/positional_polish/pd34_books.json"],
     "produces": "results/positional_polish/pd34_books.json",
     "needs": ["results/features/books_w80.json"],
     "why": "PD-34 second corpus: does the movement asymmetry hold on books?"},
    {"name": "scholawrite_bert_testsmall", "est": 200,
     "cmd": [PY, "runners/run_scholawrite.py", "--arm", "bert", "--eval", "test_small"],
     "produces": "results/scholawrite/bert_testsmall.json",
     "needs": ["results/scholawrite/schema.json"],
     "why": "G141 protocol pin: is the published 0.64 earned on the shipped test_small split?"},
    {"name": "scholawrite_roberta_testsmall", "est": 200,
     "cmd": [PY, "runners/run_scholawrite.py", "--arm", "roberta", "--eval", "test_small"],
     "produces": "results/scholawrite/roberta_testsmall.json",
     "needs": ["results/scholawrite/schema.json"],
     "why": "G141 protocol pin, second architecture"},
]
for _k in range(5):
    STAGES.append({"name": f"scholawrite_bert_lopo{_k}", "est": 200,
                   "cmd": [PY, "runners/run_scholawrite.py", "--arm", "bert",
                           "--lopo", str(_k)],
                   "produces": f"results/scholawrite/bert_lopo{_k}.json",
                   "needs": ["results/scholawrite/schema.json"],
                   "why": f"G141 leak-free protocol: hold out project {_k}, the number the "
                          f"within-project split cannot supply"})
for _k in range(5):
    STAGES.append({"name": f"scholawrite_roberta_lopo{_k}", "est": 200,
                   "cmd": [PY, "runners/run_scholawrite.py", "--arm", "roberta",
                           "--lopo", str(_k)],
                   "produces": f"results/scholawrite/roberta_lopo{_k}.json",
                   "needs": ["results/scholawrite/schema.json"],
                   "why": f"G141 leak-free protocol, second architecture, project {_k}"})

# ── NIGHT12c 2026-08-11: the faithful ScholaWrite arms per the subagent protocol pin --
# balanced class weights, head-of-document truncation, the published wrapper typo, 10 epochs.
# The pass target is the paper's own per-class table (its printed 0.64 is internally
# inconsistent by ~0.05); the revision diff gates interpretation.
STAGES += [
    # sw_revision_diff REMOVED 2026-08-12: terminal-benign — the pinned revision no longer
    # exists on the Hub even under gated access (L82), so the stage can never succeed and was
    # failing every pass. Main is canonical by default; the runner stays for the record.
    {"name": "scholawrite_bert_faithful", "est": 400,
     "cmd": [PY, "runners/run_scholawrite.py", "--arm", "bert", "--faithful",
             "--epochs", "10"],
     "produces": "results/scholawrite/bert_faithful.json",
     "needs": ["results/scholawrite/schema.json"],
     "why": "G141 faithful arm: their exact protocol; compare the per-class profile, not one digit"},
    {"name": "scholawrite_roberta_faithful", "est": 400,
     "cmd": [PY, "runners/run_scholawrite.py", "--arm", "roberta", "--faithful",
             "--epochs", "10"],
     "produces": "results/scholawrite/roberta_faithful.json",
     "needs": ["results/scholawrite/schema.json"],
     "why": "G141 faithful arm, second architecture"},
]

# ── NIGHT12b 2026-08-11, REVISED by the subagent pin (L79): the noprecision arm is
# disconfirmed (precision is a real class; two different 85s). The v4 arms carry the pinned
# construction: Revision-Index units, multi-purpose discard, their features, their published
# footnote hyperparameters. Cheap without the grid; CPU, runs beside the GPU stages.
STAGES += [
    {"name": "arg_v4_fixed", "est": 60,
     "cmd": [PY, "runners/run_arg_replication.py", "--extract", "v4",
             "--out", "replication_v4.json"],
     "produces": "results/arg_baselines/replication_v4.json",
     "needs": [],
     "why": "G136 v4: the pinned construction with published hyperparameters, both tasks"},
    {"name": "arg_v4_balanced", "est": 45,
     "cmd": [PY, "runners/run_arg_replication.py", "--extract", "v4", "--balanced",
             "--tasks", "fine", "--out", "replication_v4_balanced.json"],
     "produces": "results/arg_baselines/replication_v4_balanced.json",
     "needs": [],
     "why": "G136 in-house confirmation: the subagent's run falsified balanced weighting "
            "(+0.01-0.02 only); this replicates that in our pipeline"},
    {"name": "arg_v4_diff", "est": 50,
     "cmd": [PY, "runners/run_arg_replication.py", "--extract", "v4", "--diff-features",
             "--tasks", "fine", "--out", "replication_v4_diff.json"],
     "produces": "results/arg_baselines/replication_v4_diff.json",
     "needs": [],
     "why": "G136 change-representation suspect: concatenated embeddings never state what "
            "changed; explicit difference features are the mechanism candidate for the "
            "small-class collapse"},
    {"name": "arg_v4_oversample", "est": 50,
     "cmd": [PY, "runners/run_arg_replication.py", "--extract", "v4", "--oversample",
             "1.49", "--tasks", "fine", "--out", "replication_v4_oversample.json"],
     "produces": "results/arg_baselines/replication_v4_oversample.json",
     "needs": [],
     "why": "G136 single-cause hypothesis: a 1.49x oversample of the five small classes "
            "predicts majority .29, word-usage F1 .45, and rare classes .35-.54 all at once"},
    {"name": "arg_v4_diff_binary", "est": 50,
     "cmd": [PY, "runners/run_arg_replication.py", "--extract", "v4", "--diff-features",
             "--tasks", "binary", "--out", "replication_v4_diff_binary.json"],
     "produces": "results/arg_baselines/replication_v4_diff_binary.json",
     "needs": [],
     "why": "G136 binary gate: the .93 target is live from the released data and the "
            "difference features are untried there; the last binary lever short of encoder "
            "archaeology"},
]

# ── NIGHT13 2026-08-11: the tertiary-prediction burn. Phase 1's remainder (the BST figure
# arm) is implementation work, not compute, so it stays day-work; tonight burns GPU and CPU
# on accrued OPEN rows. GPU stages serialize through soundingline/gpulock.
STAGES += [
    # CPU: window-size robustness for the PD-33/34 family (the "one window size" caveat)
    {"name": "features_argrewrite_w40", "est": 30,
     "cmd": [PY, "runners/build_features.py", "--corpora", "argrewrite", "--window", "40",
             "--suffix", "_w40"],
     "produces": "results/features/argrewrite_w40.json", "needs": [],
     "why": "PD-33/34 robustness input: the second window size"},
    {"name": "features_books_w40", "est": 60,
     "cmd": [PY, "runners/build_features.py", "--corpora", "books", "--window", "40",
             "--suffix", "_w40"],
     "produces": "results/features/books_w40.json", "needs": [],
     "why": "PD-33/34 robustness input, books"},
    {"name": "features_ladder3_w80", "est": 30,
     "cmd": [PY, "runners/build_features.py", "--corpora", "ladder3", "--window", "80",
             "--suffix", "_w80"],
     "produces": "results/features/ladder3_w80.json", "needs": [],
     "why": "PD-3 input: machine long-form windows"},
    {"name": "pd33_books_w40", "est": 10,
     "cmd": [PY, "runners/run_pd33_books.py", "--cache", "results/features/books_w40.json",
             "--out", "results/positional_polish/pd33_books_w40.json"],
     "produces": "results/positional_polish/pd33_books_w40.json",
     "needs": ["results/features/books_w40.json"],
     "why": "PD-33 robustness: does the author-share split survive the window choice?"},
    {"name": "pd34_argrewrite_w40", "est": 25,
     "cmd": [PY, "runners/run_pd34_movement.py",
             "--cache", "results/features/argrewrite_w40.json",
             "--out", "results/positional_polish/pd34_argrewrite_w40.json"],
     "produces": "results/positional_polish/pd34_argrewrite_w40.json",
     "needs": ["results/features/argrewrite_w40.json"],
     "why": "PD-34 robustness, essays at the second window"},
    {"name": "pd34_books_w40", "est": 25,
     "cmd": [PY, "runners/run_pd34_movement.py",
             "--cache", "results/features/books_w40.json",
             "--out", "results/positional_polish/pd34_books_w40.json"],
     "produces": "results/positional_polish/pd34_books_w40.json",
     "needs": ["results/features/books_w40.json"],
     "why": "PD-34 robustness, books at the second window"},
    {"name": "pd2_signed_books", "est": 25,
     "cmd": [PY, "runners/run_pd34_movement.py", "--signed",
             "--cache", "results/features/books_w80.json",
             "--out", "results/positional_polish/pd2_signed_books.json"],
     "produces": "results/positional_polish/pd2_signed_books.json",
     "needs": ["results/features/books_w80.json"],
     "why": "PD-2 at last: the signed-trend decay form on the corpus where movement exists"},
    {"name": "pd2_signed_argrewrite", "est": 25,
     "cmd": [PY, "runners/run_pd34_movement.py", "--signed",
             "--cache", "results/features/argrewrite_w80.json",
             "--out", "results/positional_polish/pd2_signed_argrewrite.json"],
     "produces": "results/positional_polish/pd2_signed_argrewrite.json",
     "needs": ["results/features/argrewrite_w80.json"],
     "why": "PD-2 control surface: essays were flat in |trend|, so signed should be too"},
    {"name": "pd3_machine_ladder3", "est": 25,
     "cmd": [PY, "runners/run_pd34_movement.py",
             "--cache", "results/features/ladder3_w80.json",
             "--out", "results/positional_polish/pd3_ladder3.json"],
     "produces": "results/positional_polish/pd3_ladder3.json",
     "needs": ["results/features/ladder3_w80.json"],
     "why": "PD-3: machine artifacts should show flat polish across position, no maker to "
            "reallocate attention"},
    # GPU, serialized by the lock: the two-layers question, then the mapping sweep
    {"name": "g28_twolayers", "est": 200,
     "cmd": [PY, "runners/run_g28_twolayers.py"],
     "produces": "results/g28_twolayers/summary.json", "needs": [],
     "why": "G28: leaked vs emblematic as two distributions or one question twice, with the "
            "test-retest arm as the built-in null; the caveat over the whole leak battery"},
]
for _m in ("Qwen/Qwen2.5-0.5B", "EleutherAI/pythia-410m", "HuggingFaceTB/SmolLM2-360M",
           "openai-community/gpt2-medium", "Qwen/Qwen2.5-1.5B", "EleutherAI/pythia-1.4b",
           "HuggingFaceTB/SmolLM2-1.7B", "openai-community/gpt2-large", "Qwen/Qwen2.5-3B",
           "openai-community/gpt2-xl", "EleutherAI/pythia-2.8b"):
    _t = _m.split("/")[-1]
    STAGES.append({"name": f"g20_mapping_{_t}", "est": 90,
                   "cmd": [PY, "runners/run_g20_mapping.py", "--model", _m],
                   "produces": f"results/g20_mapping/{_t}.json", "needs": [],
                   "why": "G20a vs G20b, never tested directly: valence/category/beyond-"
                          "lexicon curves per block, thirds-banded verdict, permutation-"
                          "gated; the beyond-lexicon rise is G143's handoff candidate"})

# ── NIGHT13b 2026-08-12: the follow-ups the landings earned (all CPU, all existing runners)
STAGES += [
    {"name": "pd2_signed_books_w40", "est": 20,
     "cmd": [PY, "runners/run_pd34_movement.py", "--signed",
             "--cache", "results/features/books_w40.json",
             "--out", "results/positional_polish/pd2_signed_books_w40.json"],
     "produces": "results/positional_polish/pd2_signed_books_w40.json",
     "needs": ["results/features/books_w40.json"],
     "why": "PD-2 robustness: is the decay window-robust where the magnitude asymmetry was not?"},
    {"name": "pd2_signed_argrewrite_w40", "est": 20,
     "cmd": [PY, "runners/run_pd34_movement.py", "--signed",
             "--cache", "results/features/argrewrite_w40.json",
             "--out", "results/positional_polish/pd2_signed_argrewrite_w40.json"],
     "produces": "results/positional_polish/pd2_signed_argrewrite_w40.json",
     "needs": ["results/features/argrewrite_w40.json"],
     "why": "PD-2 robustness, essays at the second window"},
    {"name": "pd2_signed_ladder3", "est": 20,
     "cmd": [PY, "runners/run_pd34_movement.py", "--signed",
             "--cache", "results/features/ladder3_w80.json",
             "--out", "results/positional_polish/pd2_signed_ladder3.json"],
     "produces": "results/positional_polish/pd2_signed_ladder3.json",
     "needs": ["results/features/ladder3_w80.json"],
     "why": "the account separator: if machine polish also DECAYS the register account gains; "
            "if machine rises while humans fall, reallocation regains ground"},
    {"name": "pd34_ladder3_w40", "est": 30,
     "cmd": [PY, "runners/build_features.py", "--corpora", "ladder3", "--window", "40",
             "--suffix", "_w40"],
     "produces": "results/features/ladder3_w40.json", "needs": [],
     "why": "machine window-robustness input"},
    {"name": "pd3_ladder3_w40", "est": 20,
     "cmd": [PY, "runners/run_pd34_movement.py",
             "--cache", "results/features/ladder3_w40.json",
             "--out", "results/positional_polish/pd3_ladder3_w40.json"],
     "produces": "results/positional_polish/pd3_ladder3_w40.json",
     "needs": ["results/features/ladder3_w40.json"],
     "why": "PD-3 reversal robustness at the second window"},
]

# ── NIGHT13c 2026-08-12: the owed backlog, crafted (PD-11 standing-policy rerun; the
# sign-funnel's register-matched fiction; the fiction arms of PD-2 and G80)
STAGES += [
    {"name": "pd11_rerun_k20", "est": 250,
     "cmd": [PY, "runners/run_d0b.py", "--arm", "local", "--k", "20",
             "--seed-base", "9000", "--out-tag", "_rerun_k20"],
     "produces": "results/d0b/d0b_rerun_k20.json", "needs": [],
     "why": "PD-11's owed powered re-run per the standing near-significance policy: held out, "
            "hyperparameters frozen, fresh seeds, doubled n against the 2.0x bar"},
    {"name": "gen_fiction", "est": 200,
     "cmd": [PY, "runners/run_gen_fiction.py"],
     "produces": "corpora/machine_fiction_manifest.json", "needs": [],
     "why": "sign-funnel step 1: register-matched machine fiction, two generator families"},
    {"name": "features_fiction_qwen", "est": 25,
     "cmd": [PY, "runners/build_features.py", "--corpora", "machine_fiction_qwen",
             "--window", "80", "--suffix", "_w80"],
     "produces": "results/features/machine_fiction_qwen_w80.json",
     "needs": ["corpora/machine_fiction_manifest.json"],
     "why": "sign-funnel input, generator one"},
    {"name": "features_fiction_ds", "est": 25,
     "cmd": [PY, "runners/build_features.py", "--corpora", "machine_fiction_ds",
             "--window", "80", "--suffix", "_w80"],
     "produces": "results/features/machine_fiction_ds_w80.json",
     "needs": ["corpora/machine_fiction_manifest.json"],
     "why": "sign-funnel input, generator two"},
    {"name": "pd2_signed_fiction_qwen", "est": 20,
     "cmd": [PY, "runners/run_pd34_movement.py", "--signed",
             "--cache", "results/features/machine_fiction_qwen_w80.json",
             "--out", "results/positional_polish/pd2_signed_fiction_qwen.json"],
     "produces": "results/positional_polish/pd2_signed_fiction_qwen.json",
     "needs": ["results/features/machine_fiction_qwen_w80.json"],
     "why": "the sign-funnel's decisive cell: does register-matched machine fiction still "
            "rise where human fiction falls?"},
    {"name": "pd2_signed_fiction_ds", "est": 20,
     "cmd": [PY, "runners/run_pd34_movement.py", "--signed",
             "--cache", "results/features/machine_fiction_ds_w80.json",
             "--out", "results/positional_polish/pd2_signed_fiction_ds.json"],
     "produces": "results/positional_polish/pd2_signed_fiction_ds.json",
     "needs": ["results/features/machine_fiction_ds_w80.json"],
     "why": "the same cell under a second generator family, the shared-representation guard"},
]

# ── METHODS PASS 2026-08-12 (L93): reruns the audit earned, each behind its own gate.
# Stages enter here only once their runner exists; the rest of the plan lives in TODO.md.
STAGES += [
    {"name": "pooling_falsifier_v2", "est": 75,
     "cmd": [PY, "runners/run_pooling_falsifier.py"],
     "produces": "results/pooling_falsifier/Qwen2.5-1.5B_v2.json", "needs": [],
     "why": "L44 correction: v1 read rungs 0-1 only (rung-ordered manifest truncated at 40); "
            "v2 is full-n with a mean-arm reproduce-gate before the other poolings are read"},
]

# ── SECOND GEAR restock 2026-08-12 (the gear-rename pass): the no-maker expansion serving
# L40's power and weakness 6 in one chain; G80's register-matched fiction comparison.
STAGES += [
    {"name": "g80_fiction", "est": 10,
     "cmd": [PY, "runners/run_g80_scaffolding.py", "--fiction"],
     "produces": "results/g80_scaffolding/summary_fiction.json",
     "needs": ["corpora/machine_fiction_manifest.json"],
     "why": "G80's cleaner machine comparison: whole-document fiction, two generator families"},
    {"name": "nomaker2_gen", "est": 200,
     "cmd": [PY, "runners/make_nomaker_set.py", "--out-dir", "corpora/nomaker2",
             "--per-kind", "24", "--seed-base", "20000"],
     "produces": "corpora/nomaker2/COMPLETE.json", "needs": [],
     "why": "L40 power: 72 more no-maker artifacts, frozen construction, fresh seeds"},
    {"name": "nomaker_ds_gen", "est": 260,
     "cmd": [PY, "runners/make_nomaker_set.py", "--out-dir", "corpora/nomaker_ds",
             "--per-kind", "24", "--seed-base", "30000", "--model", "deepseek-r1:7b"],
     "produces": "corpora/nomaker_ds/COMPLETE.json", "needs": [],
     "why": "weakness 6 at last: the no-maker construction from a second generator family"},
    {"name": "layercorr_nomaker2", "est": 60,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "nomaker2",
             "--save-signals"],
     "produces": "results/layer_correlation/nomaker2_Qwen2.5-1.5B_sig.json",
     "needs": ["corpora/nomaker2/COMPLETE.json"],
     "why": "the signal matrix the powered permutation test needs"},
    {"name": "layercorr_nomaker_ds", "est": 60,
     "cmd": [PY, "runners/run_layer_correlation.py", "--corpus", "nomaker_ds",
             "--save-signals"],
     "produces": "results/layer_correlation/nomaker_ds_Qwen2.5-1.5B_sig.json",
     "needs": ["corpora/nomaker_ds/COMPLETE.json"],
     "why": "the same reader over the second family's no-maker text — the shared-"
            "representation cell (weakness 6)"},
    {"name": "g107_powered", "est": 30,
     "cmd": [PY, "runners/run_nomaker_permutation.py", "--corpora", "nomaker,nomaker2",
             "--perms", "5000", "--out-tag", "_powered"],
     "produces": "results/audit/nomaker_permutation_powered.json",
     "needs": ["results/layer_correlation/nomaker2_Qwen2.5-1.5B_sig.json"],
     "why": "L40 was UNDECIDED at 36 artifacts (p=.095/.089); the identical test at 108 "
            "with 5000 permutations, per the near-significance policy"},
]

# ── SIGN-FUNNEL ROUND 2 (2026-08-12 evening, L97's near-significance): the deepseek signed
# cell landed marginal in the HUMAN direction (-0.28, p=.055, n=13); the policy says double n
# with everything frozen. Same premises, fresh seeds, both families for symmetry.
STAGES += [
    {"name": "gen_fiction_r2", "est": 220,
     "cmd": [PY, "runners/run_gen_fiction.py", "--round", "1"],
     # the qwen arm never drops pieces, so its last round-2 piece is the completion marker;
     # deepseek retries ride along on later passes via per-piece skip-if-exists
     "produces": "corpora/machine_fiction_qwen/piece_29.txt", "needs": [],
     "why": "the powered fiction round: 15 more pieces per family at fresh seeds"},
    {"name": "features_fiction_qwen_r2", "est": 40,
     "cmd": [PY, "runners/build_features.py", "--corpora", "machine_fiction_qwen",
             "--window", "80", "--suffix", "_w80r2"],
     "produces": "results/features/machine_fiction_qwen_w80r2.json",
     "needs": ["corpora/machine_fiction_qwen/piece_29.txt"],
     "why": "both-rounds cache, generator one"},
    {"name": "features_fiction_ds_r2", "est": 40,
     "cmd": [PY, "runners/build_features.py", "--corpora", "machine_fiction_ds",
             "--window", "80", "--suffix", "_w80r2"],
     "produces": "results/features/machine_fiction_ds_w80r2.json",
     "needs": ["corpora/machine_fiction_qwen/piece_29.txt"],
     "why": "both-rounds cache, generator two"},
    {"name": "pd2_signed_fiction_qwen_r2", "est": 20,
     "cmd": [PY, "runners/run_pd34_movement.py", "--signed",
             "--cache", "results/features/machine_fiction_qwen_w80r2.json",
             "--out", "results/positional_polish/pd2_signed_fiction_qwen_r2.json"],
     "produces": "results/positional_polish/pd2_signed_fiction_qwen_r2.json",
     "needs": ["results/features/machine_fiction_qwen_w80r2.json"],
     "why": "the rise cell at doubled n, frozen"},
    {"name": "pd2_signed_fiction_ds_r2", "est": 20,
     "cmd": [PY, "runners/run_pd34_movement.py", "--signed",
             "--cache", "results/features/machine_fiction_ds_w80r2.json",
             "--out", "results/positional_polish/pd2_signed_fiction_ds_r2.json"],
     "produces": "results/positional_polish/pd2_signed_fiction_ds_r2.json",
     "needs": ["results/features/machine_fiction_ds_w80r2.json"],
     "why": "the decisive powered cell: does deepseek fiction DECAY like human text at n~28"},
    {"name": "activation_variance_fiction", "est": 45,
     "cmd": [PY, "runners/run_activation_variance.py", "--fiction"],
     "produces": "results/activation_variance/summary_fiction.json",
     "needs": ["corpora/machine_fiction_qwen/piece_29.txt"],
     "why": "L39's owed register-matched arm: does the reader's affective series still move "
            "more through books than through machine FICTION, per generator family"},
]

# ── G146 2026-08-13: the 2x2 that separates base from post-training. The local second family
# is a distillation onto the home family's own base, so the sign flip (L100/L101) tracks
# post-training; the cross needs llama-base cells in both lineages: deepseek-r1:latest is the
# llama-8B reasoning distill (installed), llama3.1:8b the llama instruct (pulled 08-13).
G146_MODELS = ("deepseek-r1:latest=machine_fiction_r1l8,"
               "llama3.1:8b=machine_fiction_llama")
STAGES += [
    {"name": "gen_fiction_g146", "est": 260,
     "cmd": [PY, "runners/run_gen_fiction.py", "--models", G146_MODELS],
     "produces": "corpora/machine_fiction_llama/piece_14.txt", "needs": [],
     "why": "G146 round 0: fifteen chapters each from the llama-base cells of the 2x2"},
    {"name": "gen_fiction_g146_r2", "est": 260,
     "cmd": [PY, "runners/run_gen_fiction.py", "--models", G146_MODELS, "--round", "1"],
     "produces": "corpora/machine_fiction_llama/piece_29.txt",
     "needs": ["corpora/machine_fiction_llama/piece_14.txt"],
     "why": "G146 round 1: the powered n per cell, matching the first two families"},
    {"name": "features_fiction_r1l8", "est": 40,
     "cmd": [PY, "runners/build_features.py", "--corpora", "machine_fiction_r1l8",
             "--window", "80", "--suffix", "_w80"],
     "produces": "results/features/machine_fiction_r1l8_w80.json",
     "needs": ["corpora/machine_fiction_llama/piece_29.txt"],
     "why": "G146 cache: llama-base reasoning cell"},
    {"name": "features_fiction_llama", "est": 40,
     "cmd": [PY, "runners/build_features.py", "--corpora", "machine_fiction_llama",
             "--window", "80", "--suffix", "_w80"],
     "produces": "results/features/machine_fiction_llama_w80.json",
     "needs": ["corpora/machine_fiction_llama/piece_29.txt"],
     "why": "G146 cache: llama-base instruct cell"},
    {"name": "pd2_signed_fiction_r1l8", "est": 20,
     "cmd": [PY, "runners/run_pd34_movement.py", "--signed",
             "--cache", "results/features/machine_fiction_r1l8_w80.json",
             "--out", "results/positional_polish/pd2_signed_fiction_r1l8.json"],
     "produces": "results/positional_polish/pd2_signed_fiction_r1l8.json",
     "needs": ["results/features/machine_fiction_r1l8_w80.json"],
     "why": "G146: does llama-base reasoning DECAY like the qwen-base reasoning cell did"},
    {"name": "pd2_signed_fiction_llama", "est": 20,
     "cmd": [PY, "runners/run_pd34_movement.py", "--signed",
             "--cache", "results/features/machine_fiction_llama_w80.json",
             "--out", "results/positional_polish/pd2_signed_fiction_llama.json"],
     "produces": "results/positional_polish/pd2_signed_fiction_llama.json",
     "needs": ["results/features/machine_fiction_llama_w80.json"],
     "why": "G146: does llama-base instruct RISE like the qwen-base instruct cell did"},
]

# ── G147 2026-08-13: the PAN 2024 hard-split winner, recreated from its notebook paper at his
# ruling. The printed 0.863 is on the held-back TIRA test set; the exact-value gates are the
# notebook's own validation table (single arms .8423/.8567/.8490, majority vote .8658).
STAGES += [
    {"name": "pan_roberta_hard", "est": 120,
     "cmd": [PY, "runners/run_pan_winner.py", "--encoder", "roberta", "--warmup", "0.06"],
     "produces": "results/pan_winner/roberta_hard.json", "needs": [],
     "why": "G147 member 1 of 3: roberta-base. Collapsed to constant predictions without "
            "warmup at their lr (archived _collapsed); 0.06 recorded as the divergence fix"},
    {"name": "pan_deberta_hard", "est": 300,
     "cmd": [PY, "runners/run_pan_winner.py", "--encoder", "deberta", "--no-amp",
             "--warmup", "0.06", "--batch", "12", "--accum", "5"],
     "produces": "results/pan_winner/deberta_hard.json", "needs": [],
     "why": "G147 member 2 of 3: deberta-base (v1), their strongest single arm (.8567 gate); "
            "fp32 because its disentangled attention overflows under fp16 autocast. Micro-batch "
            "12 x accum 5 (same effective 60, same step count): batch 30 fp32 OOMed on the "
            "shared card 2026-08-14"},
    # pan_ernie_hard (no-warmup) DELETED 2026-08-14: superseded by pan_ernie_hard_sched;
    # two stages must never share a produces (second referee, item 1)
    # pan_vote_hard RELOCATED behind the corrected members (second referee, item 4)
]

# ── 24H RESTOCK 2026-08-13 evening: the missed-test audit's catches and the completion arms.
# The window lesson (LESSONS §3) demands the 40-word window for every fiction movement cell;
# the reader-side and scaffolding arms extend to all four generator families.
for _fam in ("qwen", "ds", "r1l8", "llama"):
    STAGES += [
        {"name": f"features_fiction_{_fam}_w40", "est": 30,
         "cmd": [PY, "runners/build_features.py", "--corpora", f"machine_fiction_{_fam}",
                 "--window", "40", "--suffix", "_w40"],
         "produces": f"results/features/machine_fiction_{_fam}_w40.json",
         "needs": [],
         "why": f"window-robustness cache, {_fam} family (the w80-only caveat)"},
        {"name": f"pd2_signed_fiction_{_fam}_w40", "est": 15,
         "cmd": [PY, "runners/run_pd34_movement.py", "--signed",
                 "--cache", f"results/features/machine_fiction_{_fam}_w40.json",
                 "--out", f"results/positional_polish/pd2_signed_fiction_{_fam}_w40.json"],
         "produces": f"results/positional_polish/pd2_signed_fiction_{_fam}_w40.json",
         "needs": [f"results/features/machine_fiction_{_fam}_w40.json"],
         "why": f"the {_fam} sign cell at the second window; claim nothing from one window"},
    ]
STAGES += [
    {"name": "pd34_fiction_r1l8", "est": 15,
     "cmd": [PY, "runners/run_pd34_movement.py",
             "--cache", "results/features/machine_fiction_r1l8_w80.json",
             "--out", "results/positional_polish/pd34_fiction_r1l8.json"],
     "produces": "results/positional_polish/pd34_fiction_r1l8.json",
     "needs": ["results/features/machine_fiction_r1l8_w80.json"],
     "why": "unsigned magnitude cell for the llama-base reasoning family"},
    {"name": "pd34_fiction_llama", "est": 15,
     "cmd": [PY, "runners/run_pd34_movement.py",
             "--cache", "results/features/machine_fiction_llama_w80.json",
             "--out", "results/positional_polish/pd34_fiction_llama.json"],
     "produces": "results/positional_polish/pd34_fiction_llama.json",
     "needs": ["results/features/machine_fiction_llama_w80.json"],
     "why": "unsigned magnitude cell for the llama-base instruct family"},
    {"name": "activation_variance_fiction4", "est": 75,
     "cmd": [PY, "runners/run_activation_variance.py", "--fiction"],
     "produces": "results/activation_variance/summary_fiction4.json", "needs": [],
     "why": "the reader-side cell for all four generator families; completes the 2x2 on the "
            "second instrument"},
    {"name": "g80_fiction4", "est": 12,
     "cmd": [PY, "runners/run_g80_scaffolding.py", "--fiction"],
     "produces": "results/g80_scaffolding/summary_fiction4.json", "needs": [],
     "why": "prompt-burden rates for the two new families, extending L98"},
]

# ── 24H RESTOCK round 2 (2026-08-14 morning): the llama reader-cell top-up. RETIRED 2026-08-14
# midday: llama3.1:8b produced ZERO chapters meeting the floor across two rounds (0/45 pieces
# at 900 then at 800 words, each retried twice) — the model's chapter length is the ceiling,
# and scaffolding the prompt to force length would break the same-prompt construction across
# families (the G80/L98 lesson: prompt structure is itself a signal). The llama reader-side
# cell stays n = 3, recorded as underpowered in L105's caption.

# ── THE REFEREE'S ARMS (2026-08-14, Opus adversarial audit at his order): the tests each
# reopened verdict demands, queued the same day.
STAGES += [
    {"name": "pan_ernie_hard_sched", "est": 150,
     "cmd": [PY, "runners/run_pan_winner.py", "--encoder", "ernie", "--warmup", "0.06"],
     "produces": "results/pan_winner/ernie_hard.json", "needs": [],
     "why": "referee: members ran under different LR schedules (constant-LR result archived); "
            "one recipe for all three before the vote"},
    {"name": "pan_roberta_leakfree23", "est": 130,
     "cmd": [PY, "runners/run_pan_winner.py", "--encoder", "roberta", "--warmup", "0.06",
             "--drop-leaked-2023", "--out-tag", "_leakfree23"],
     "produces": "results/pan_winner/roberta_hard_leakfree23.json", "needs": [],
     "why": "second referee: the IDENTIFIED settling arm — drop only the 210 contaminated "
            "PAN23 docs (97.3% of data kept); --no-2023 confounded leak with a 50% cut"},
    {"name": "sw_bert_hfd_s42", "est": 300,
     "cmd": [PY, "runners/run_scholawrite.py", "--arm", "bert", "--faithful",
             "--hf-defaults", "--epochs", "10", "--seed", "42", "--out-tag", "_hfd_s42"],
     "produces": "results/scholawrite/bert_faithful_hfd_s42.json", "needs": [],
     "why": "referee: their Trainer supplied linear decay, clipping, and decay exclusions "
            "our loop dropped; framework-faithful arm, seed 1 of 3"},
    {"name": "sw_bert_hfd_s43", "est": 300,
     "cmd": [PY, "runners/run_scholawrite.py", "--arm", "bert", "--faithful",
             "--hf-defaults", "--epochs", "10", "--seed", "43", "--out-tag", "_hfd_s43"],
     "produces": "results/scholawrite/bert_faithful_hfd_s43.json", "needs": [],
     "why": "seed 2 of 3: no fine-tune verdict from one seed"},
    {"name": "sw_bert_hfd_s44", "est": 300,
     "cmd": [PY, "runners/run_scholawrite.py", "--arm", "bert", "--faithful",
             "--hf-defaults", "--epochs", "10", "--seed", "44", "--out-tag", "_hfd_s44"],
     "produces": "results/scholawrite/bert_faithful_hfd_s44.json", "needs": [],
     "why": "seed 3 of 3; the published value is judged against the seed interval"},
    {"name": "pan_vote_hard", "est": 5,
     "cmd": [PY, "runners/run_pan_winner.py", "--vote", "--member-tags",
             "roberta=_headdrop25,deberta=_headdrop25_s43,ernie=_headdrop25"],
     "produces": "results/pan_winner/vote_hard.json",
     "needs": ["results/pan_winner/roberta_hard_headdrop25.json",
               "results/pan_winner/deberta_hard_headdrop25_s43.json",
               "results/pan_winner/ernie_hard_headdrop25.json"],
     "why": "the system vote (gate .8658), behind three members under ONE recipe: head-scope "
            "dropout 0.25, warmup 0.06. Deberta member retargeted to the s43 stabilizer rung "
            "(2026-08-16): the seed-42 head-scope run collapsed flat and wrote no prediction "
            "siblings, so the vote gates on the rung that might train"},
    {"name": "sw_roberta_hfd_s42", "est": 300,
     "cmd": [PY, "runners/run_scholawrite.py", "--arm", "roberta", "--faithful",
             "--hf-defaults", "--epochs", "10", "--seed", "42", "--out-tag", "_hfd_s42"],
     "produces": "results/scholawrite/roberta_faithful_hfd_s42.json", "needs": [],
     "why": "second referee: the 0.64 is claimed for BOTH architectures and roberta is the "
            "worse miss; its framework arm cannot stay unrun"},
    {"name": "sw_bert_hfd_b8", "est": 420,
     "cmd": [PY, "runners/run_scholawrite.py", "--arm", "bert", "--faithful",
             "--hf-defaults", "--epochs", "10", "--batch", "8", "--seed", "42",
             "--out-tag", "_hfd_b8"],
     "produces": "results/scholawrite/bert_faithful_hfd_b8.json", "needs": [],
     "why": "second referee: the batch-8 reading of checkpoint-30760 is a 10-epoch schedule "
            "read at half decay; per-epoch history supplies the epoch-5 point"},
    {"name": "pan25_wqd_hard", "est": 150,
     "cmd": [PY, "runners/run_pan25_winner.py", "--difficulty", "hard"],
     "produces": "results/pan25_winner/wqd_hard.json", "needs": [],
     "why": "G148: the phase's first reachable TEST-set exact-value gate (L109 found the "
            "labeled 2025 test split in our store, verified genuine). The fully-specified "
            "2025 winner against its printed 0.830; contamination gate 0.4%, clean"},
    {"name": "arg_v4_gridmax_binary", "est": 150,
     "cmd": [PY, "runners/run_arg_replication.py", "--extract", "v4", "--grid",
             "--tasks", "binary", "--out", "v4_gridmax_binary.json"],
     "produces": "results/arg_baselines/v4_gridmax_binary.json", "needs": [],
     "why": "referee: if the published cells are grid maxima, max-over-their-36-point-grid "
            "is the like-for-like number for the embedding rows"},
]

# ── MIDDAY RESTOCK 2026-08-14: the dropout-scope fork (the all-module reading of the winner's
# 0.25 collapsed roberta to a 9-epoch flatline while ernie trained fine under it, so the
# printed number is scope-ambiguous; the head-only reading is the usual notebook meaning and
# all three members rerun under it so the vote compares one recipe to one recipe), plus the
# referee's second ArgRewrite route.
STAGES += [
    {"name": "pan_roberta_headdrop25", "est": 130,
     "cmd": [PY, "runners/run_pan_winner.py", "--encoder", "roberta", "--warmup", "0.06",
             "--dropout-scope", "head", "--out-tag", "_headdrop25"],
     "produces": "results/pan_winner/roberta_hard_headdrop25.json", "needs": [],
     "why": "scope fork, member 1: head-only 0.25 (encoder dropouts at pretrained defaults). "
            "All-module 0.25 flatlined 9 epochs at 0.352; default-0.1 scored 0.8558"},
    {"name": "pan_ernie_headdrop25", "est": 150,
     "cmd": [PY, "runners/run_pan_winner.py", "--encoder", "ernie", "--warmup", "0.06",
             "--dropout-scope", "head", "--out-tag", "_headdrop25"],
     "produces": "results/pan_winner/ernie_hard_headdrop25.json", "needs": [],
     "why": "scope fork, member 2: ernie landed 0.8798 under all-module 0.25, so its head-only "
            "cell measures the scope lever on a member that tolerates both"},
    {"name": "pan_deberta_headdrop25", "est": 300,
     "cmd": [PY, "runners/run_pan_winner.py", "--encoder", "deberta", "--no-amp",
             "--warmup", "0.06", "--batch", "12", "--accum", "5",
             "--dropout-scope", "head", "--out-tag", "_headdrop25"],
     "produces": "results/pan_winner/deberta_hard_headdrop25.json", "needs": [],
     "why": "scope fork, member 3: fp32 (fp16 overflow), micro-batch 12 x accum 5 after the "
            "batch-30 fp32 OOM; the vote's strongest member (.8567 gate)"},
    {"name": "arg_v4_fourblock_binary", "est": 90,
     "cmd": [PY, "runners/run_arg_replication.py", "--extract", "v4", "--pair-encoding",
             "fourblock", "--tasks", "binary", "--out", "v4_fourblock_binary.json"],
     "produces": "results/arg_baselines/v4_fourblock_binary.json", "needs": [],
     "why": "referee route 2 for the embedding rows: the standard [u; v; |u-v|; u*v] pair "
            "encoding at the published config. Grid-max over the bare concatenation landed "
            "NOT-MATCHED (-.043/-.052), so this is the last unexplored local route"},
]

# ── NIGHT RESTOCK 2026-08-14: the wqd runner carries pinned printed TEST gates for all
# three difficulties (easy 0.958, medium 0.823, hard 0.830) and the 2025 edition is
# within-year clean at every split (0.2-0.4%, L108/L109; the runner's own contamination
# gate aborts above 1% regardless) — so the phase's reachable test-set exact-value gate
# count goes from one to three for the cost of two stages.
STAGES += [
    {"name": "pan25_wqd_easy", "est": 150,
     "cmd": [PY, "runners/run_pan25_winner.py", "--difficulty", "easy"],
     "produces": "results/pan25_winner/wqd_easy.json", "needs": [],
     "why": "G148 test-set gate 2 of 3: the 2025 winner's printed easy test 0.958"},
    {"name": "pan25_wqd_medium", "est": 150,
     "cmd": [PY, "runners/run_pan25_winner.py", "--difficulty", "medium"],
     "produces": "results/pan25_winner/wqd_medium.json", "needs": [],
     "why": "G148 test-set gate 3 of 3: the 2025 winner's printed medium test 0.823"},
    # ── BST v2 follow-ups (L119 landed Exp-1 marked arm at printed precision). CPU stages;
    # they never touch the GPU lock, so they run beside the trainings.
    {"name": "bst_exp1_all", "est": 90,
     "cmd": [PY, "runners/run_bst_gridworld.py", "--arm", "all",
             "--out", "exp1_v2_all.json"],
     "produces": "results/bst_gridworld/exp1_v2_all.json", "needs": [],
     "why": "the goal-prior contradiction's second arm: the appendix's all-non-obstacle-"
            "squares support, same best-fit gates; the marked arm (the Exp-1 main text) "
            "landed at printed precision (L119)"},
    # ── MORNING 2026-08-16: deberta's head-scope arm collapsed flat (its second failure
    # mode after the fp16 overflow). The stabilizer ladder runs recipe-preserving order
    # (L118's stochastic-fragility lesson): seed change first.
    {"name": "pan_deberta_headdrop25_s43", "est": 620,
     "cmd": [PY, "runners/run_pan_winner.py", "--encoder", "deberta", "--no-amp",
             "--warmup", "0.06", "--batch", "12", "--accum", "5",
             "--dropout-scope", "head", "--seed", "43", "--out-tag", "_headdrop25_s43"],
     "produces": "results/pan_winner/deberta_hard_headdrop25_s43.json", "needs": [],
     "why": "stabilizer rung 1 for the collapsed deberta member: same recipe, seed 43. If "
            "it collapses too, rung 2 is warmup 0.10, rung 3 lr 4e-5, each recorded as a "
            "named divergence-fix assumption"},
]

# ── The L113 window cells: the magnitude square's llama half ran wide-window only, and the
# window lesson (LESSONS §3) says no fiction movement cell is believed at one window. Cheap
# CPU stages over the cached w40 features; the qwen cells get their w40 reading in the same
# sweep so the whole square carries both windows.
for _fam in ("qwen", "ds", "llama", "r1l8"):
    STAGES += [
        {"name": f"pd34_fiction_{_fam}_w40", "est": 15,
         "cmd": [PY, "runners/run_pd34_movement.py",
                 "--cache", f"results/features/machine_fiction_{_fam}_w40.json",
                 "--out", f"results/positional_polish/pd34_fiction_{_fam}_w40.json"],
         "produces": f"results/positional_polish/pd34_fiction_{_fam}_w40.json",
         "needs": [f"results/features/machine_fiction_{_fam}_w40.json"],
         "why": "L113 robustness: the magnitude-tracks-lineage square at the 40-word window"},
    ]



# ── PHASE 2.0 FREE-PATH RESTOCK 2026-08-16: the week's grind under standing ruling 7 (no
# material spend; everything below is local). The G129 confirmatory battery runs the prereg
# card (prereg/g129.py, Amendment 1) off the shared manifest so every arm sees identical
# events and candidate sets; the verdict stage computes the preregistered bands only after
# every arm has landed. G149's ruler gate validates the motivation-shift sampler on planted
# switches in the validated BST engine. G153's local pilot proves the benchmark's
# process-recording loop on the two independent local lineages at zero dollars.
STAGES += [
    {"name": "g129_change_block", "est": 25,
     "cmd": [PY, "runners/run_g129_confirm.py", "--arm", "change_block"],
     "produces": "results/g129/change_block.json",
     "needs": ["results/g129/manifest.json"],
     "why": "G129 A4: the 19-dim declared baseline the reader must beat (L85), "
            "author-grouped CV, probabilities restricted to the shared candidate sets"},
    {"name": "g129_recovery", "est": 90,
     "cmd": [PY, "runners/run_g129_confirm.py", "--arm", "recovery"],
     "produces": "results/g129/recovery.json",
     "needs": ["results/g129/manifest.json"],
     "why": "G129 A1, the claim arm: delta + candidates on the balanced full set (H-A)"},
    {"name": "g129_blind", "est": 60,
     "cmd": [PY, "runners/run_g129_confirm.py", "--arm", "blind"],
     "produces": "results/g129/blind.json",
     "needs": ["results/g129/manifest.json"],
     "why": "G129 A2, the floor arm: VOID gate if off the analytic 1/k"},
    {"name": "g129_shuffle", "est": 90,
     "cmd": [PY, "runners/run_g129_confirm.py", "--arm", "shuffle"],
     "produces": "results/g129/shuffle.json",
     "needs": ["results/g129/manifest.json"],
     "why": "G129 A3, the leakage arm: permuted truth must read at chance or the run is VOID"},
    {"name": "g129_brief", "est": 60,
     "cmd": [PY, "runners/run_g129_confirm.py", "--arm", "brief"],
     "produces": "results/g129/brief.json",
     "needs": ["results/g129/manifest.json"],
     "why": "G129 A5: assignment context alone, no delta (context-only control)"},
    {"name": "g129_source", "est": 60,
     "cmd": [PY, "runners/run_g129_confirm.py", "--arm", "source"],
     "produces": "results/g129/source.json",
     "needs": ["results/g129/manifest.json"],
     "why": "G129 A6: original sentence alone, no delta (topic-only control)"},
    {"name": "g129_unchanged", "est": 45,
     "cmd": [PY, "runners/run_g129_confirm.py", "--arm", "unchanged"],
     "produces": "results/g129/unchanged.json",
     "needs": ["results/g129/manifest.json"],
     "why": "G129 A7 (Amendment 1): no-op deltas with an explicit no-revision option; "
            "fabrication rate = the reader's Taramsa bound, symmetric changed control beside"},
    {"name": "g129_recovery_matched", "est": 40,
     "cmd": [PY, "runners/run_g129_confirm.py", "--arm", "recovery_matched"],
     "produces": "results/g129/recovery_matched.json",
     "needs": ["results/g129/manifest.json"],
     "why": "G129 H-B: the truth-balanced matched draw (L126's analytic-floor amendment); "
            "n=176 of the powered 283, shortfall clause engages at verdict"},
    {"name": "g129_blind_matched", "est": 30,
     "cmd": [PY, "runners/run_g129_confirm.py", "--arm", "blind_matched"],
     "produces": "results/g129/blind_matched.json",
     "needs": ["results/g129/manifest.json"],
     "why": "G129: the matched floor arm, expected back at analytic 1/k after balancing"},
    {"name": "g129_verdict", "est": 5,
     "cmd": [PY, "runners/run_g129_confirm.py", "--verdict"],
     "produces": "results/g129/verdict.json",
     "needs": ["results/g129/recovery.json", "results/g129/blind.json",
               "results/g129/shuffle.json", "results/g129/brief.json",
               "results/g129/source.json", "results/g129/unchanged.json",
               "results/g129/recovery_matched.json", "results/g129/blind_matched.json",
               "results/g129/change_block.json"],
     "why": "G129: the preregistered bands, McNemar reader-vs-block, VOID gates, and "
            "fabrication rates, computed once, every statistic on disk"},
    {"name": "g149_switch_sampler", "est": 90,
     "cmd": [PY, "runners/run_g149_switch_sampler.py"],
     "produces": "results/g149/switch_sampler.json",
     "needs": ["results/bst2009_reference/fig3_stimuli_canon.json"],
     "why": "G149 ruler gate: planted goal switches in the validated BST engine; the "
            "shift sampler must detect and localize them with false alarms priced at 5% "
            "before any motivation-shift claim touches text. CPU, runs beside trainings"},
    {"name": "g153_gen_qwen", "est": 240,
     "cmd": [PY, "runners/run_g153_local_gen.py", "--family", "qwen"],
     "produces": "corpora/g153_pilot/qwen/manifest.json", "needs": [],
     "why": "G153 free path: the benchmark's process-recording loop proven end to end on "
            "the seen local lineage (R1 thin-prompt 4 domains x 2 lengths + R3 rewrites), "
            "explicit decoding recorded at generation time"},
    {"name": "g153_gen_llama", "est": 240,
     "cmd": [PY, "runners/run_g153_local_gen.py", "--family", "llama"],
     "produces": "corpora/g153_pilot/llama/manifest.json", "needs": [],
     "why": "G153 free path: the HELD-OUT local lineage's arm of the same pilot"},
]

# ── EVENING RESTOCK 2026-08-18: the G131 factorial generation arms, the construct test's
# corpus (2 targets x (3,8) x 2 couplings + zero control, 10 topics, both local families,
# instruction sets recorded as ground truth at generation time). The recovery study runs
# over this corpus next restock.
STAGES += [
    {"name": "g131_gen_qwen", "est": 200,
     "cmd": [PY, "runners/run_g131_gen.py", "--family", "qwen"],
     "produces": "corpora/g131_factorial/qwen/manifest.json", "needs": [],
     "why": "G131 factorial corpus, seen family: the construct test that separates target, "
            "amount, and coupling, with planted instruction sets as ground truth"},
    {"name": "g131_gen_llama", "est": 200,
     "cmd": [PY, "runners/run_g131_gen.py", "--family", "llama"],
     "produces": "corpora/g131_factorial/llama/manifest.json", "needs": [],
     "why": "G131 factorial corpus, held-out family: identical instruction draws by "
            "construction, so family is a clean second factor"},
]

# ── PHASE 2.1 RESTOCK 2026-08-19 (the audit pass, L137): the G131 corpus is exploratory
# until realization is adjudicated; these are the G158 foraging stages. The mechanical
# stage and the baselines ran inline at build time; the reader adjudication arms are the
# queued GPU work (556 semantic instruction-assignments at temp 0, checkpoint-resuming).
STAGES += [
    {"name": "g158_reader_qwen", "est": 120,
     "cmd": [PY, "runners/run_g158_adjudicate.py", "--reader", "qwen"],
     "produces": "results/g158/realization_reader_qwen.json",
     "needs": ["results/g158/realization_mechanical.json"],
     "why": "G158 realization adjudication, seen family: realized/unrealized/ambiguous "
            "with required verbatim evidence spans; model-judged and flagged (adjudicator "
            "shares the qwen lineage with this half of the text)"},
    {"name": "g158_reader_llama", "est": 120,
     "cmd": [PY, "runners/run_g158_adjudicate.py", "--reader", "llama"],
     "produces": "results/g158/realization_reader_llama.json",
     "needs": ["results/g158/realization_mechanical.json"],
     "why": "G158 realization adjudication, held-out family: same adjudicator across "
            "families so the cross-family comparison is instrument-constant"},
    {"name": "g158_reader_validate", "est": 30,
     "cmd": [PY, "runners/run_g158_adjudicate.py", "--validate"],
     "produces": "results/g158/reader_validation.json",
     "needs": ["results/g158/realization_reader_qwen.json",
               "results/g158/realization_reader_llama.json"],
     "why": "G158 adjudicator validation: the reader re-judges a stratified sample of the "
            "mechanically decidable assignments blind, and the over-credit rate (reader "
            "realized where the exact string test says unrealized) gates whether stage "
            "(c) may consume reader verdicts; the live arms' zero ambiguous calls made "
            "this the binding check"},
]

# ── PHASE 2.1 BUILD-OUT 2026-08-19 afternoon (his directive; L139 constraints applied):
# stage (c) artifact-only recovery on the mechanical exact-grade truth, and the G129b
# fresh confirmatory under prereg/g129b.py (manifest built at design time, seed 37,
# caliper relaxation fired -> matched 200 of 283, H-B pre-committed to pilot tier).
STAGES += [
    {"name": "g158_recovery_surface", "est": 90,
     "cmd": [PY, "runners/run_g158_recovery.py", "--arm", "surface"],
     "produces": "results/g158/recovery_r1_done.json",
     "needs": ["results/g158/realization_mechanical.json"],
     "why": "G158 stage (c) claim+floor arms: artifact-only pick among mechanically "
            "verified candidates (100 events, truth realized, decoys unsatisfied), plus "
            "the blind floor on identical sets"},
    {"name": "g158_recovery_none", "est": 20,
     "cmd": [PY, "runners/run_g158_recovery.py", "--arm", "none"],
     "produces": "results/g158/recovery_r5_done.json",
     "needs": ["results/g158/realization_mechanical.json"],
     "why": "G158 stage (c) fabrication control: zero-instruction essays with an "
            "explicit none option; L139's acquiescence predicts failure UP, measured"},
    {"name": "g158_recovery_problem", "est": 120,
     "cmd": [PY, "runners/run_g158_recovery.py", "--arm", "problem"],
     "produces": "results/g158/recovery_r6_done.json",
     "needs": ["results/g158/realization_mechanical.json"],
     "why": "G158 stage (c) attenuated problem-pool arm: scored against assignment, "
            "nulls preregistered uninterpretable, only above-echo-bar positives act"},
    {"name": "g158_recovery_summarize", "est": 10,
     "cmd": [PY, "runners/run_g158_recovery.py", "--arm", "summarize"],
     "produces": "results/g158/recovery_summary.json",
     "needs": ["results/g158/recovery_r1_done.json", "results/g158/recovery_r2_done.json",
               "results/g158/recovery_r5_done.json", "results/g158/recovery_r6_done.json"],
     "why": "G158 stage (c) scoring pass: echo bar and oracle wiring check on identical "
            "candidate sets, truth-balanced reads, per-cell tables, one summary file"},
]

for _arm, _est in (("recovery", 150), ("blind", 100), ("shuffle", 150), ("brief", 100),
                   ("source", 100), ("unchanged", 120), ("recovery_matched", 60),
                   ("blind_matched", 40)):
    STAGES += [
        {"name": f"g129b_{_arm}", "est": _est,
         "cmd": [PY, "runners/run_g129_confirm.py", "--card", "b", "--arm", _arm],
         "produces": f"results/g129b/{_arm}.json",
         "needs": ["results/g129b/manifest.json"],
         "why": f"G129b confirmatory arm {_arm} under prereg/g129b.py: fresh seed, "
                "directional gates with both expectations stated at freeze"},
    ]
STAGES += [
    {"name": "g129b_change_block", "est": 30,
     "cmd": [PY, "runners/run_g129_confirm.py", "--card", "b", "--arm", "change_block"],
     "produces": "results/g129b/change_block.json",
     "needs": ["results/g129b/manifest.json"],
     "why": "G129b declared baseline: the 19-dim change block, author-grouped CV, on the "
            "fresh-seed populations (CPU)"},
    {"name": "g129b_verdict", "est": 5,
     "cmd": [PY, "runners/run_g129_confirm.py", "--card", "b", "--verdict"],
     "produces": "results/g129b/verdict.json",
     "needs": ["results/g129b/recovery.json", "results/g129b/blind.json",
               "results/g129b/shuffle.json", "results/g129b/brief.json",
               "results/g129b/source.json", "results/g129b/unchanged.json",
               "results/g129b/recovery_matched.json", "results/g129b/blind_matched.json",
               "results/g129b/change_block.json"],
     "why": "G129b verdict under the corrected gates: one-sided VOIDs in the guarded "
            "direction, shuffle's 0.125 alternative expectation recorded beside the "
            "read, H-B at its pre-committed tier"},
]

# ── PHASE 2.1.5 CORPUS 2026-08-19 midday (G159, the rebuilt factorial; appended at the
# END of the stage list per the same-day ownership lesson): paired rewrites of the
# recorded G131 bases with realization crossed as R+/R- arms; the audit stage gates the
# corpus on its own exact-grade realization before any recovery study preregisters.
STAGES += [
    {"name": "g159_gen_qwen", "est": 180,
     "cmd": [PY, "runners/run_g159_gen.py", "--family", "qwen"],
     "produces": "corpora/g159_rebuild/qwen/manifest.json", "needs": [],
     "why": "G159 rebuild corpus, seen family: 80 instructed/uninstructed rewrite pairs "
            "of the recorded bases, realization as the arm"},
    {"name": "g159_gen_llama", "est": 180,
     "cmd": [PY, "runners/run_g159_gen.py", "--family", "llama"],
     "produces": "corpora/g159_rebuild/llama/manifest.json", "needs": [],
     "why": "G159 rebuild corpus, held-out family: identical instruction draws and "
            "identical bases-by-topic, so family stays a clean factor"},
    {"name": "g159_audit", "est": 10,
     "cmd": [PY, "runners/run_g159_gen.py", "--audit"],
     "produces": "corpora/g159_rebuild/realization_audit.json",
     "needs": ["corpora/g159_rebuild/qwen/manifest.json",
               "corpora/g159_rebuild/llama/manifest.json"],
     "why": "G159 self-gate: mechanical realization on R+ must clear 0.5 exact-grade or "
            "the corpus repeats the G131 defect and the recovery study does not proceed; "
            "R- counterfactual rates land beside the L138 base rates"},
]

# ── OWED-RUNNER WAVE 2026-08-19 (his directive: G94/G97/L56 plus the 2.1 buildables;
# G97 and the L56 settle ran inline at build time, CPU): G94 is the queued GPU pair.
STAGES += [
    {"name": "g94_taramsa_gpu", "est": 60,
     "cmd": [PY, "runners/run_g94_taramsa.py", "--arm", "gpu"],
     "produces": "results/g94/gpu_done.json", "needs": [],
     "why": "G94 Taramsa arms: fabrication on rung-0 (does the reader invent specs where "
            "none were given), recovery and blind per rung on reconstructed ground truth "
            "(join-checked against recorded prompt word counts before any call)"},
    {"name": "g94_taramsa_summarize", "est": 5,
     "cmd": [PY, "runners/run_g94_taramsa.py", "--arm", "summarize"],
     "produces": "results/g94/taramsa.json",
     "needs": ["results/g94/gpu_done.json"],
     "why": "G94 scoring: echo bar on identical candidate sets, per-rung dose tables, "
            "the Taramsa fabrication number"},
]

# ── G159 RECOVERY BATTERY 2026-08-19 evening (prereg/g159.py, frozen; Phase 2.1.5's
# decisive study and Phase 2.2A's closure boundary; appended at list end per the
# ownership lesson). Manifest built at freeze: P+ 100 / P- 100 / S+ 20.
for _arm, _est in (("p_plus", 60), ("p_minus", 60), ("blind", 40),
                   ("fabrication", 60), ("surface", 20), ("delta", 90)):
    STAGES += [
        {"name": f"g159_rec_{_arm}", "est": _est,
         "cmd": [PY, "runners/run_g159_recovery.py", "--arm", _arm],
         "produces": f"results/g159/{_arm}.json",
         "needs": ["results/g159/manifest.json"],
         "why": f"G159 arm {_arm} under the frozen card: realized-choice recovery with "
                "echo-matched decoys; the P- twins are the leak gate and realization "
                "null; the delta arm is interface I2, reported separately"},
    ]
STAGES += [
    {"name": "g159_rec_verdict", "est": 10,
     "cmd": [PY, "runners/run_g159_recovery.py", "--verdict"],
     "produces": "results/g159/verdict.json",
     "needs": ["results/g159/p_plus.json", "results/g159/p_minus.json",
               "results/g159/blind.json", "results/g159/fabrication.json",
               "results/g159/surface.json", "results/g159/delta.json"],
     "why": "G159 verdict: one-sided gates in guarded directions, echo-bar matching "
            "validation, the execution effect banded per the card, oracle wiring check"},
]

# ── EVENING RESTOCK 2026-08-16: the wqd hard gate landed 0.8293 vs printed 0.830 (seven
# ten-thousandths; L128) and easy landed 0.9535 vs 0.958. The fine-tune verdict rule
# (standing ruling 3, the referee refinement) grades on the three-seed interval, so both
# gates get their local seed arms; medium's follow when its seed-42 lands.
for _d, _s in (("hard", 43), ("hard", 44), ("easy", 43), ("easy", 44),
               ("medium", 43), ("medium", 44)):
    STAGES += [
        {"name": f"pan25_wqd_{_d}_s{_s}", "est": 150,
         "cmd": [PY, "runners/run_pan25_winner.py", "--difficulty", _d,
                 "--seed", str(_s), "--out-tag", f"_s{_s}"],
         "produces": f"results/pan25_winner/wqd_{_d}_s{_s}.json", "needs": [],
         "why": f"G148 {_d} gate, seed {_s}: the three-seed interval the fine-tune "
                "verdict rule requires; the official reads stay local per the stone"},
    ]


# ── PHASE 2.2D CORPUS 2026-08-20 (G162, licensed by L147's ruler pass; appended at list
# end). Six handling families as instructed rewrites with token-verifiable planted
# issues; the audit self-gates the corpus before any reading battery preregisters.
STAGES += [
    {"name": "g162_gen_qwen", "est": 120,
     "cmd": [PY, "runners/run_g162_gen.py", "--generator", "qwen"],
     "produces": "corpora/g162_anomaly/manifest_qwen.json", "needs": [],
     "why": "G162 anomaly corpus, seen generator: 60 handling-instructed rewrites of "
            "the recorded bases with string-testable planted issues"},
    {"name": "g162_gen_llama", "est": 120,
     "cmd": [PY, "runners/run_g162_gen.py", "--generator", "llama"],
     "produces": "corpora/g162_anomaly/manifest_llama.json", "needs": [],
     "why": "G162 anomaly corpus, held-out generator: identical fact cards and "
            "families, lineage to the same bases"},
    {"name": "g162_audit", "est": 5,
     "cmd": [PY, "runners/run_g162_gen.py", "--audit"],
     "produces": "corpora/g162_anomaly/handling_audit.json",
     "needs": ["corpora/g162_anomaly/manifest_qwen.json",
               "corpora/g162_anomaly/manifest_llama.json"],
     "why": "G162 self-gate: planted-issue presence, correction-marker separation, "
            "repetition and refrain counts; the reading battery preregisters only on "
            "CORPUS-STANDS"},
]


# ── G162-R READING BATTERY 2026-08-20 evening (prereg/g162.py frozen on CORPUS-STANDS;
# appended at list end). Validation-first order: the V arm gates interpretation.
for _arm, _est in (("validate", 90), ("classify", 60), ("classify_delta", 90),
                   ("blind", 30)):
    STAGES += [
        {"name": f"g162r_{_arm}", "est": _est,
         "cmd": [PY, "runners/run_g162_reading.py", "--arm", _arm],
         "produces": f"results/g162/{_arm}_done.json",
         "needs": ["corpora/g162_anomaly/handling_audit.json"],
         "why": f"G162-R arm {_arm}: handling classification under the frozen card; "
                "the validate arm is negative-class-heavy and gates all interpretation"},
    ]
STAGES += [
    {"name": "g162r_verdict", "est": 5,
     "cmd": [PY, "runners/run_g162_reading.py", "--verdict"],
     "produces": "results/g162/verdict.json",
     "needs": ["results/g162/validate_done.json", "results/g162/classify_done.json",
               "results/g162/classify_delta_done.json", "results/g162/blind_done.json"],
     "why": "G162-R verdict: V gate first, per-class confusion, the primary "
            "concealed-vs-unnoticed pair band, clean-family fabrication"},
]

# ── PHASE 2.3 ROOT WAVE 2026-08-21 (appended at list end; registry
# docs/design/archive/PHASE_2_3_REGISTRY.md; cards frozen before arms). G165 = the Wing G
# reader-ablation root on the frozen G159 manifest; G166 = the Wing B route-varied
# process-recorded corpus construction. The g165 gate (pipeline purity + anchor) ran
# and passed at build time; its produce gates every arm.
STAGES += [
    {"name": "g165_gate", "est": 2,
     "cmd": [PY, "runners/run_g165_ablation.py", "--gate"],
     "produces": "results/g165/gate.json", "needs": ["results/g159/manifest.json"],
     "why": "G165 exact-equivalence pipeline gate + known-answer anchor; every GPU arm "
            "waits on it (prereg/g165.py)"},
]
for _arm, _est in (("self_route", 150), ("cand_disc", 100),
                   ("self_route_leak", 80), ("cand_disc_leak", 50)):
    STAGES += [
        {"name": f"g165_{_arm}", "est": _est,
         "cmd": [PY, "runners/run_g165_ablation.py", "--arm", _arm],
         "produces": f"results/g165/{_arm}.json",
         "needs": ["results/g165/gate.json"],
         "why": f"G165 arm {_arm}: route-generation ablation against the recorded "
                "direct arm; leak arms run the twins where nothing was executed"},
    ]
STAGES += [
    {"name": "g165_verdict", "est": 5,
     "cmd": [PY, "runners/run_g165_ablation.py", "--verdict"],
     "produces": "results/g165/verdict.json",
     "needs": ["results/g165/self_route.json", "results/g165/cand_disc.json",
               "results/g165/self_route_leak.json",
               "results/g165/cand_disc_leak.json"],
     "why": "G165 verdict: leak gate first, paired McNemar vs recorded direct picks, "
            "echo-split cells standing per L148, exhaustive bands"},
    {"name": "g166_gen_qwen", "est": 150,
     "cmd": [PY, "runners/run_g166_routes.py", "--generator", "qwen"],
     "produces": "corpora/g166_routes/manifest_qwen.json", "needs": [],
     "why": "G166 route-varied corpus, seen generator: five recorded routes to "
            "surface-matched essays, process-logged by construction"},
    {"name": "g166_gen_llama", "est": 180,
     "cmd": [PY, "runners/run_g166_routes.py", "--generator", "llama"],
     "produces": "corpora/g166_routes/manifest_llama.json", "needs": [],
     "why": "G166 route-varied corpus, held-out generator: identical briefs and "
            "routes, lineage recorded"},
    {"name": "g166_audit", "est": 5,
     "cmd": [PY, "runners/run_g166_routes.py", "--audit"],
     "produces": "corpora/g166_routes/routes_audit.json",
     "needs": ["corpora/g166_routes/manifest_qwen.json",
               "corpora/g166_routes/manifest_llama.json"],
     "why": "G166 self-gate: yield, band, route-log completeness, cross-route "
            "degeneracy; the B0 reading battery preregisters only on CORPUS-STANDS"},
]

# ── PHASE 2.3 SECOND WAVE 2026-08-21 mid-morning (appended at list end). G165-D = the
# root-null's single predeclared discriminator on the G129b delta substrate
# (prereg/g165d.py); G166-R = the equifinality reading battery on the standing route
# corpus (prereg/g166.py, frozen on CORPUS-STANDS). Both gates ran and passed at build.
STAGES += [
    {"name": "g165d_gate", "est": 2,
     "cmd": [PY, "runners/run_g165d_ablation.py", "--gate"],
     "produces": "results/g165d/gate.json", "needs": ["results/g129b/manifest.json"],
     "why": "G165-D pipeline purity + anchor (recorded 0.4805/616); arms gate on it"},
]
for _arm, _est in (("sr_delta", 300), ("cd_delta", 180), ("sr_unchanged", 60)):
    STAGES += [
        {"name": f"g165d_{_arm}", "est": _est,
         "cmd": [PY, "runners/run_g165d_ablation.py", "--arm", _arm],
         "produces": f"results/g165d/{_arm}.json",
         "needs": ["results/g165d/gate.json"],
         "why": f"G165-D arm {_arm}: the ablation where direct reading is weak; "
                "sr_unchanged is the generation-stage fabrication gate"},
    ]
STAGES += [
    {"name": "g165d_verdict", "est": 5,
     "cmd": [PY, "runners/run_g165d_ablation.py", "--verdict"],
     "produces": "results/g165d/verdict.json",
     "needs": ["results/g165d/sr_delta.json", "results/g165d/cd_delta.json",
               "results/g165d/sr_unchanged.json"],
     "why": "G165-D verdict: fabrication gate first, paired McNemar, gap-closure vs "
            "the change block reported never banded"},
    {"name": "g166r_gate", "est": 2,
     "cmd": [PY, "runners/run_g166_reading.py", "--gate"],
     "produces": "results/g166/gate.json",
     "needs": ["corpora/g166_routes/routes_audit.json"],
     "why": "G166-R exact-equivalence purity; arms gate on it"},
    {"name": "g166r_surface", "est": 3,
     "cmd": [PY, "runners/run_g166_reading.py", "--surface"],
     "produces": "results/g166/surface.json",
     "needs": ["corpora/g166_routes/routes_audit.json"],
     "why": "G166-R mechanical surface baseline (S), leave-one-topic-out"},
]
for _arm, _est in (("process", 90), ("classify", 60), ("blind", 30)):
    STAGES += [
        {"name": f"g166r_{_arm}", "est": _est,
         "cmd": [PY, "runners/run_g166_reading.py", "--arm", _arm],
         "produces": f"results/g166/{_arm}.json",
         "needs": ["results/g166/gate.json"],
         "why": f"G166-R arm {_arm}: the process-aware ceiling gates interpretation "
                "(validation-first analog); artifact-only is the primary"},
    ]
STAGES += [
    {"name": "g166r_verdict", "est": 5,
     "cmd": [PY, "runners/run_g166_reading.py", "--verdict"],
     "produces": "results/g166/verdict.json",
     "needs": ["results/g166/process.json", "results/g166/classify.json",
               "results/g166/blind.json", "results/g166/surface.json"],
     "why": "G166-R verdict: P ceiling first, per-route confusion, the C-vs-S "
            "contest, exhaustive bands"},
]

# ── PHASE 2.3 THIRD WAVE 2026-08-21 afternoon (appended at list end). G167 = Wing A
# context conditioning on the route corpus (prereg/g167.py, card-leak audit passed at
# build — the audit caught and fixed its own first card); G169 part 1 = the Wing D
# repair's long-form corpus with the hedging-density gate the L150 null demanded.
STAGES += [
    {"name": "g167_gate", "est": 2,
     "cmd": [PY, "runners/run_g167_context.py", "--gate"],
     "produces": "results/g167/gate.json",
     "needs": ["corpora/g166_routes/routes_audit.json", "results/g166/classify.json"],
     "why": "G167 card-leak audit + pipeline purity; arms gate on it"},
]
for _arm, _est in (("true_card", 60), ("false_card", 60), ("irrelevant_card", 60)):
    STAGES += [
        {"name": f"g167_{_arm}", "est": _est,
         "cmd": [PY, "runners/run_g167_context.py", "--arm", _arm],
         "produces": f"results/g167/{_arm}.json",
         "needs": ["results/g167/gate.json"],
         "why": f"G167 arm {_arm}: does a feasibility card move committed mass "
                "toward compatible routes, and does a false card steer equally?"},
    ]
STAGES += [
    {"name": "g167_verdict", "est": 5,
     "cmd": [PY, "runners/run_g167_context.py", "--verdict"],
     "produces": "results/g167/verdict.json",
     "needs": ["results/g167/true_card.json", "results/g167/false_card.json",
               "results/g167/irrelevant_card.json"],
     "why": "G167 verdict: movement analysis vs the recorded no-card arm, "
            "CONDITIONS / PROJECTION / INERT exhaustive"},
    {"name": "g169_gen_qwen", "est": 240,
     "cmd": [PY, "runners/run_g169_longform.py", "--generator", "qwen"],
     "produces": "corpora/g169_longform/manifest_qwen.json", "needs": [],
     "why": "G169 long-form handling corpus, seen generator: 40 essays at 900-1300 "
            "words, four families, the L150 redesign substrate"},
    {"name": "g169_gen_llama", "est": 300,
     "cmd": [PY, "runners/run_g169_longform.py", "--generator", "llama"],
     "produces": "corpora/g169_longform/manifest_llama.json", "needs": [],
     "why": "G169 long-form corpus, held-out generator"},
    {"name": "g169_audit", "est": 5,
     "cmd": [PY, "runners/run_g169_longform.py", "--audit"],
     "produces": "corpora/g169_longform/longform_audit.json",
     "needs": ["corpora/g169_longform/manifest_qwen.json",
               "corpora/g169_longform/manifest_llama.json"],
     "why": "G169 self-gate: yield, length, plant thresholds, and the HEDGING "
            "DENSITY gate — instructed concealment must realize hedging or the "
            "corpus is refused as an L150 repeat"},
]

# ── G167-A5 EVIDENCE-CONFLICT 2026-08-21 mid-afternoon (appended at list end;
# prereg/g167a5.py frozen on the L155 PROJECTION verdict — the wing's single
# predeclared follow-up, after which Wing A pauses per the brief's W3 routing).
STAGES += [
    {"name": "g167a5_gate", "est": 2,
     "cmd": [PY, "runners/run_g167a5_conflict.py", "--gate"],
     "produces": "results/g167a5/gate.json", "needs": ["results/g159/manifest.json"],
     "why": "G167-A5 purity + anchor; arms gate on it"},
]
for _arm, _est in (("true_note", 60), ("false_note", 60), ("false_note_flag", 60)):
    STAGES += [
        {"name": f"g167a5_{_arm}", "est": _est,
         "cmd": [PY, "runners/run_g167a5_conflict.py", "--arm", _arm],
         "produces": f"results/g167a5/{_arm}.json",
         "needs": ["results/g167a5/gate.json"],
         "why": f"G167-A5 arm {_arm}: can a false production note override artifact "
                "evidence the reader provably reads (direct 0.86)?"},
    ]
STAGES += [
    {"name": "g167a5_verdict", "est": 5,
     "cmd": [PY, "runners/run_g167a5_conflict.py", "--verdict"],
     "produces": "results/g167a5/verdict.json",
     "needs": ["results/g167a5/true_note.json", "results/g167a5/false_note.json",
               "results/g167a5/false_note_flag.json"],
     "why": "G167-A5 verdict: EVIDENCE-HOLDS / MIXED / SUGGESTIBLE exhaustive; the "
            "wing pauses in every branch"},
]

# ── G169 v2 REPAIR 2026-08-21 (appended at list end). The v1 audit REFUSED the corpus
# (concealed plant 0.63, hedging 2.67 vs the 3.0 floor) — the gate doing its job. The
# ONE regeneration pass: accept-time verification per family, four tries, offset seeds.
STAGES += [
    {"name": "g169_regen_qwen", "est": 90,
     "cmd": [PY, "runners/run_g169_longform.py", "--regen", "qwen"],
     "produces": "corpora/g169_longform/manifest_qwen_v2.json",
     "needs": ["corpora/g169_longform/manifest_qwen.json"],
     "why": "G169 v2 repair, seen generator: replace only accept-failing artifacts "
            "with mechanical accept-time verification"},
    {"name": "g169_regen_llama", "est": 120,
     "cmd": [PY, "runners/run_g169_longform.py", "--regen", "llama"],
     "produces": "corpora/g169_longform/manifest_llama_v2.json",
     "needs": ["corpora/g169_longform/manifest_llama.json"],
     "why": "G169 v2 repair, held-out generator"},
    {"name": "g169_audit_v2", "est": 5,
     "cmd": [PY, "runners/run_g169_longform.py", "--audit", "--v2"],
     "produces": "corpora/g169_longform/longform_audit_v2.json",
     "needs": ["corpora/g169_longform/manifest_qwen_v2.json",
               "corpora/g169_longform/manifest_llama_v2.json"],
     "why": "G169 v2 audit, identical gates: if this refuses too, the long-form "
            "substrate waits for the curator — no further tuning"},
]

# ── G169-R SPAN BATTERY 2026-08-21 afternoon (appended at list end; prereg/g169r.py
# frozen on the v2 CORPUS-STANDS; the mechanical baseline ran CPU at build: 0.7949 —
# separability-at-all is already demonstrated, the reader arms decide semantics).
for _arm, _est in (("validate", 90), ("classify", 60), ("span", 40), ("blind", 15)):
    STAGES += [
        {"name": f"g169r_{_arm}", "est": _est,
         "cmd": [PY, "runners/run_g169_reading.py", "--arm", _arm],
         "produces": f"results/g169r/{_arm}_done.json",
         "needs": ["corpora/g169_longform/longform_audit_v2.json"],
         "why": f"G169-R arm {_arm}: the L150-owed span-level redesign on the "
                "standing long-form corpus; V gates interpretation"},
    ]
STAGES += [
    {"name": "g169r_verdict", "est": 5,
     "cmd": [PY, "runners/run_g169_reading.py", "--verdict"],
     "produces": "results/g169r/verdict.json",
     "needs": ["results/g169r/validate_done.json", "results/g169r/classify_done.json",
               "results/g169r/span_done.json", "results/g169r/blind_done.json",
               "results/g169r/mech.json"],
     "why": "G169-R verdict: V first, both primaries (CL pair, SP gap), the "
            "reader-vs-mechanical contest, fabricated-span rate"},
]

# ── THE LAST TWO ROOTS 2026-08-21 (appended at list end; his order). G171 = the F0
# ordered-accident ruler, ALL GATES PASSED both seeds at build (one recorded repair:
# the exclusive-consequence rule); its stage re-verifies from a clean run. G168 = the
# C0 role-randomized construction; the role-recovery battery preregisters on its audit.
STAGES += [
    {"name": "g171_ruler", "est": 15,
     "cmd": [PY, "runners/run_g171_accidents.py"],
     "produces": "results/g171/ruler_freshseed.json", "needs": [],
     "why": "G171 F0 ruler: pattern violation with later-dependence classification, "
            "both seeds, all gates; origin abstention enforced"},
    {"name": "g168_gen", "est": 180,
     "cmd": [PY, "runners/run_g168_roles.py", "--generate"],
     "produces": "corpora/g168_roles/manifest.json", "needs": [],
     "why": "G168 C0 construction: 40 two-actor logged cases, proposer x selection "
            "x veto crossed, every event schema-validated with actors"},
    {"name": "g168_audit", "est": 5,
     "cmd": [PY, "runners/run_g168_roles.py", "--audit"],
     "produces": "corpora/g168_roles/roles_audit.json",
     "needs": ["corpora/g168_roles/manifest.json"],
     "why": "G168 self-gate: yield, band, per-condition log completeness, SELECTION "
            "INTEGRITY (the chosen thesis must out-overlap every rejected one in "
            "the final essay), veto integrity"},
]

# ── G168-R ROLE RECOVERY 2026-08-21 late afternoon (appended at list end;
# prereg/g168r.py frozen on the C0 CORPUS-STANDS; gates passed at build). The LAST
# Stage-1 test: its verdict completes all seven roots and triggers the root map.
STAGES += [
    {"name": "g168r_gate", "est": 2,
     "cmd": [PY, "runners/run_g168_reading.py", "--gate"],
     "produces": "results/g168r/gate.json",
     "needs": ["corpora/g168_roles/roles_audit.json"],
     "why": "G168-R purity + balanced marginals; arms gate on it"},
]
for _arm, _est in (("process", 90), ("classify", 80), ("blind", 5)):
    STAGES += [
        {"name": f"g168r_{_arm}", "est": _est,
         "cmd": [PY, "runners/run_g168_reading.py", "--arm", _arm],
         "produces": f"results/g168r/{_arm}_done.json",
         "needs": ["results/g168r/gate.json"],
         "why": f"G168-R arm {_arm}: selection / veto / repair role recovery, "
                "per question, never aggregated"},
    ]
STAGES += [
    {"name": "g168r_verdict", "est": 5,
     "cmd": [PY, "runners/run_g168_reading.py", "--verdict"],
     "produces": "results/g168r/verdict.json",
     "needs": ["results/g168r/process_done.json", "results/g168r/classify_done.json",
               "results/g168r/blind_done.json"],
     "why": "G168-R verdict: the last Stage-1 root state; the root map follows"},
]

# ── PHASE 2.4 STAGE 1 2026-08-22 (appended at list end; ratified with continuous second
# gear; cards frozen: prereg/g172.py, g174.py, g177.py; spine guards all passed at build
# in tools/test_p24_spine.py). The three cheap roots; scouts refill only after the cold
# root map freezes.
STAGES += [
    {"name": "g172_corpus", "est": 180,
     "cmd": [PY, "runners/run_g172_corpus.py"],
     "produces": "results/g172/corpus_manifest.json", "needs": [],
     "why": "G172 P24-S0 corpus: 4 makers x entity-order goals, realization verified "
            "at accept time (L156 rule); manifest withheld under 90 percent fill"},
    {"name": "g172_matrix", "est": 240,
     "cmd": [PY, "runners/run_g172_matrix.py"],
     "produces": "results/g172/verdict.json",
     "needs": ["results/g172/corpus_manifest.json"],
     "why": "G172 similarity matrix: 9 readers, per-reader gates first, relation "
            "contrasts land the band (SIMILARITY-GRADED/EXACT-ONLY/FLAT/REVERSED)"},
    {"name": "g174_ruler", "est": 120,
     "cmd": [PY, "runners/run_g174_affect.py"],
     "produces": "results/g174/ruler.json", "needs": [],
     "why": "G174 P24-A0 causal affect ruler: explicit-fit scrubbed-test decoding, "
            "fear/joy approach-withdraw sign pair, controls, both seeds"},
    {"name": "g177_anchor", "est": 60,
     "cmd": [PY, "runners/run_g177_baselines.py", "--arm", "anchor"],
     "produces": "results/g177/anchor.json", "needs": [],
     "why": "G177 P24-H0 anchor: conditional-likelihood reader on the G159 realized "
            "revisions, the known-positive artifact-only target"},
    {"name": "g177_coauthor", "est": 30,
     "cmd": [PY, "runners/run_g177_baselines.py", "--arm", "coauthor"],
     "produces": "results/g177/coauthor_import.json", "needs": [],
     "why": "G177 CoAuthor import: fetch + inventory; objective actions only, token "
            "share never a target; nonzero exit and retry when unreachable"},
    {"name": "g177_sw_base", "est": 45,
     "cmd": [PY, "runners/run_g177_baselines.py", "--arm", "scholawrite"],
     "produces": "results/g177/scholawrite_lopo.json", "needs": [],
     "why": "G177 ScholaWrite LOPO mechanical baselines: frequency + Markov, label "
            "set fixed, per-project table (the L82 leak rule)"},
    {"name": "g177_sw_reader", "est": 240,
     "cmd": [PY, "runners/run_g177_baselines.py", "--arm", "scholawrite_reader"],
     "produces": "results/g177/scholawrite_reader.json",
     "needs": ["results/g177/scholawrite_lopo.json"],
     "why": "G177 ScholaWrite LOPO reader arm: local model over the fixed label set, "
            "citation known-answer subset per L139 before its verdicts count"},
]

# ── PHASE 2.4 DISCOVERY SCOUTS 2026-08-22 late (appended at list end; the root map is
# frozen at commit 95febbd BEFORE these queued — addendum §9.1 always-run set, discovery
# lane, outputs sealed from curator-facing reports until the walkthrough).
STAGES += [
    {"name": "scout_s02_para", "est": 90,
     "cmd": [PY, "runners/scout_s02_s05.py", "--arm", "paraphrase"],
     "produces": "results/scouts/s02_paraphrase_manifest.json",
     "needs": ["results/g172/verdict.json"],
     "why": "E24-S02 goal-preserving paraphrase of the similarity corpus (mechanical "
            "realized() acceptance per item; Qwen-paraphraser confound recorded)"},
    {"name": "scout_s02_matrix", "est": 180,
     "cmd": [PY, "runners/scout_s02_s05.py", "--arm", "matrix"],
     "produces": "results/scouts/s02_erasure.json",
     "needs": ["results/scouts/s02_paraphrase_manifest.json"],
     "why": "E24-S02 matrix re-run on erased artifacts: does the similarity gradient "
            "survive dialect destruction? Collapse = RIVAL-FAVORED (dialect)"},
]

# ── STAGE 2 WAVE 1 2026-08-23 (appended at list end; Stage-2 package ratified with the
# three-wave sequencing; discovery lane, statuses sealed to the daily cold map).
STAGES += [
    {"name": "scout_gen2", "est": 120,
     "cmd": [PY, "runners/scout_stage2_s.py", "--arm", "gen2"],
     "produces": "results/scouts/family2_manifest.json", "needs": [],
     "why": "E24-S3 second maker family: SmolLM2-instruct pair writes the same verified "
            "goal corpus (accept-time realization, retirement rule standing)"},
    {"name": "scout_norm", "est": 10,
     "cmd": [PY, "runners/scout_stage2_s.py", "--arm", "normalize"],
     "produces": "results/scouts/norm_manifest.json",
     "needs": ["results/scouts/family2_manifest.json"],
     "why": "E24-S1a mechanical normalization of both corpora, realization re-verified"},
    {"name": "scout_para2", "est": 150,
     "cmd": [PY, "runners/scout_stage2_s.py", "--arm", "para2"],
     "produces": "results/scouts/para2_manifest.json",
     "needs": ["results/scouts/family2_manifest.json"],
     "why": "E24-S1c independent non-Qwen paraphraser over both corpora"},
]
for _v, _need in (("orig", "results/scouts/family2_manifest.json"),
                  ("fam2", "results/scouts/family2_manifest.json"),
                  ("norm", "results/scouts/norm_manifest.json"),
                  ("para_qwen", "results/scouts/family2_manifest.json"),
                  ("para2", "results/scouts/para2_manifest.json")):
    STAGES += [
        {"name": f"scout_mx_{_v}", "est": 100,
         "cmd": [PY, "runners/scout_stage2_s.py", "--arm", "matrix", "--variant", _v],
         "produces": f"results/scouts/mx_{_v}_done.json", "needs": [_need],
         "why": f"Tree-S matrix over the {_v} variant, eleven readers, echo-gated"},
    ]
STAGES += [
    {"name": "scout_detector", "est": 15,
     "cmd": [PY, "runners/scout_stage2_s.py", "--arm", "detector"],
     "produces": "results/scouts/s2_detector.json",
     "needs": ["results/scouts/para2_manifest.json", "results/scouts/norm_manifest.json"],
     "why": "E24-S2 maker-family detector, topic-held-out, applied to every variant to "
            "VERIFY erasure rather than assume it"},
    {"name": "scout_s_analyze", "est": 10,
     "cmd": [PY, "runners/scout_stage2_s.py", "--arm", "analyze"],
     "produces": "results/scouts/s_wave1.json",
     "needs": ["results/scouts/mx_orig_done.json", "results/scouts/mx_fam2_done.json",
               "results/scouts/mx_norm_done.json", "results/scouts/mx_para_qwen_done.json",
               "results/scouts/mx_para2_done.json", "results/scouts/s2_detector.json"],
     "why": "Tree-S wave-1 synthesis: crossed reversal, erasure survival, detector map"},
]

# ── STAGE 2 WAVE 1 continuation 2026-08-23 (mirror erasure completes the crossed-imprint
# design; the smollm rows are otherwise erased only by their own family).
STAGES += [
    {"name": "scout_mirror", "est": 120,
     "cmd": [PY, "runners/scout_stage2_s.py", "--arm", "mirror"],
     "produces": "results/scouts/mirror_manifest.json",
     "needs": ["results/scouts/family2_manifest.json"],
     "why": "E24-S1d mirror arm: Qwen paraphraser over the SmolLM2 corpus, so each family "
            "is erased by a cross-family transformer as well as its own"},
    {"name": "scout_mx_para_qwen2", "est": 100,
     "cmd": [PY, "runners/scout_stage2_s.py", "--arm", "matrix",
             "--variant", "para_qwen2"],
     "produces": "results/scouts/mx_para_qwen2_done.json",
     "needs": ["results/scouts/mirror_manifest.json"],
     "why": "Tree-S matrix over the mirror-erased variant, eleven readers, echo-gated"},
    {"name": "scout_s_analyze2", "est": 10,
     "cmd": [PY, "runners/scout_stage2_s.py", "--arm", "analyze"],
     "produces": "results/scouts/s_wave1b_done.json",
     "needs": ["results/scouts/mx_para_qwen2_done.json"],
     "why": "Tree-S re-synthesis with the crossed-imprint design complete"},
]

# ── STAGE 2 next rungs 2026-08-23: the process-resolution ladder's surface-sensitive rung
# (does the family relation help only at literal instruction wording?) and the owed powered
# ScholaWrite validation (H1), which repairs the unpowered L161 gate.
STAGES += [
    {"name": "scout_mx_origL", "est": 100,
     "cmd": [PY, "runners/scout_stage2_s.py", "--arm", "matrix",
             "--variant", "orig", "--rung", "literal"],
     "produces": "results/scouts/mx_origL_done.json",
     "needs": ["results/scouts/mx_orig_done.json"],
     "why": "S4 rung 1 on the Qwen corpus: literal instruction wording as the candidate set"},
    {"name": "scout_mx_fam2L", "est": 100,
     "cmd": [PY, "runners/scout_stage2_s.py", "--arm", "matrix",
             "--variant", "fam2", "--rung", "literal"],
     "produces": "results/scouts/mx_fam2L_done.json",
     "needs": ["results/scouts/mx_fam2_done.json"],
     "why": "S4 rung 1 on the SmolLM2 corpus, same rung, crossed"},
    {"name": "scout_ladder_analyze", "est": 10,
     "cmd": [PY, "runners/scout_stage2_s.py", "--arm", "analyze"],
     "produces": "results/scouts/s_ladder_done.json",
     "needs": ["results/scouts/mx_origL_done.json", "results/scouts/mx_fam2L_done.json"],
     "why": "ladder synthesis: is the relation term larger at literal wording than at goal?"},
    {"name": "g177_sw_validation", "est": 90,
     "cmd": [PY, "runners/run_g177_baselines.py", "--arm", "sw_validation"],
     "produces": "results/g177/scholawrite_validation.json", "needs": [],
     "why": "H1 powered validation: stratified toward mechanically decidable citation "
            "edits with matched negatives, band derived at the sample size"},
]

# ── STAGE 2 routed alternative 2026-08-23: the prompted next-intention reader failed its
# powered gate, so the prospective interface moves to the non-generative form.
STAGES += [
    {"name": "g177_sw_nongen", "est": 90,
     "cmd": [PY, "runners/run_g177_baselines.py", "--arm", "sw_nongen"],
     "produces": "results/g177/scholawrite_nongen.json",
     "needs": ["results/g177/scholawrite_validation.json"],
     "why": "non-generative prospective reader: how much the draft raises each intention "
            "statement's likelihood; validated first on the same stratified subset"},
]

# ── STAGE 2 WAVE 2 2026-08-23 (the Tree-P process ecology and the Tree-H CoAuthor action
# tree; runners scout_stage2_p.py / scout_stage2_h.py, DESIGN CHECK blocks in both).
STAGES += [
    {"name": "scout_p_gen", "est": 150,
     "cmd": [PY, "runners/scout_stage2_p.py", "--arm", "gen"],
     "produces": "results/scouts/p_ecology_manifest.json", "needs": [],
     "why": "E24-P0 process ecology: 3 instruct makers x 4 preference profiles x 10 topics, "
            "exactly-two-evidence rule verified mechanically at accept time"},
    {"name": "scout_p_audit", "est": 5,
     "cmd": [PY, "runners/scout_stage2_p.py", "--arm", "audit"],
     "produces": "results/scouts/p_ecology_audit.json",
     "needs": ["results/scouts/p_ecology_manifest.json"],
     "why": "ecology audit: profile-following rate (interpretability gate) and the "
            "marginal-derived prediction floor"},
    {"name": "scout_p_read", "est": 120,
     "cmd": [PY, "runners/scout_stage2_p.py", "--arm", "read"],
     "produces": "results/scouts/p_read.json",
     "needs": ["results/scouts/p_ecology_audit.json"],
     "why": "E24-P2 system identification: recover the standing preference from k episodes, "
            "predict held-out selections; synthetic known-answer gate first"},
    {"name": "scout_h_events", "est": 20,
     "cmd": [PY, "runners/scout_stage2_h.py", "--arm", "events"],
     "produces": "results/scouts/h_coauthor_events.json", "needs": [],
     "why": "E24-H02b CoAuthor decision episodes: shown suggestion -> taken or dismissed, "
            "unreadable sessions counted never dropped"},
    {"name": "scout_h_baselines", "est": 10,
     "cmd": [PY, "runners/scout_stage2_h.py", "--arm", "baselines"],
     "produces": "results/scouts/h_coauthor_baselines.json",
     "needs": ["results/scouts/h_coauthor_events.json"],
     "why": "E24-H03 mechanical floors: majority, per-session first-half, previous-outcome, "
            "position; the margin over majority is the headline"},
]

# ── STAGE 2 continued build-out 2026-08-23 late (his directive: everything buildable,
# built; ETA calibration corrected downward). Geometry linkage, retention extraction,
# self-policy groundwork.
STAGES += [
    {"name": "scout_geo_capture", "est": 60,
     "cmd": [PY, "runners/scout_stage2_geo.py", "--arm", "capture"],
     "produces": "results/scouts/geo_capture_done.json", "needs": [],
     "why": "E24-S07 capture: late-stage representations for all readers and makers on a "
            "shared process-matched text set"},
    {"name": "scout_geo_link", "est": 20,
     "cmd": [PY, "runners/scout_stage2_geo.py", "--arm", "link"],
     "produces": "results/scouts/geo_link.json",
     "needs": ["results/scouts/geo_capture_done.json"],
     "why": "E24-S07 linkage: correspondence-null gate first, then double-centered rank "
            "relation between alignment and inversion margin (L61 rule: no raw CKA quoted)"},
    {"name": "scout_h_retention", "est": 25,
     "cmd": [PY, "runners/scout_stage2_h.py", "--arm", "retention"],
     "produces": "results/scouts/h_coauthor_retention.json", "needs": [],
     "why": "E24-H04b retained-versus-deleted: the decidable subset any future reader "
            "validation on this tree requires (the L167 obligation)"},
    {"name": "scout_p_self", "est": 45,
     "cmd": [PY, "runners/scout_stage2_p.py", "--arm", "self"],
     "produces": "results/scouts/p_self_policy.json", "needs": [],
     "why": "E24-E1 groundwork: each instruct model's own unprofiled selection policy, "
            "the self-distribution every route-tree analysis needs first"},
]

# ── STAGE 2 day-2 openers 2026-08-23 late: the neutral-corpus geometry replication L168
# owes, and the process-aware ceiling that is the one measurement left on the prospective
# interface.
STAGES += [
    {"name": "scout_geo_capture_n", "est": 45,
     "cmd": [PY, "runners/scout_stage2_geo.py", "--arm", "capture",
             "--source", "neutral"],
     "produces": "results/scouts/geo_capture_neutral_done.json", "needs": [],
     "why": "E24-S07 neutral replication capture: the same thirteen models on eighty human "
            "student essays no matrix model produced"},
    {"name": "scout_geo_link_n", "est": 20,
     "cmd": [PY, "runners/scout_stage2_geo.py", "--arm", "link",
             "--source", "neutral"],
     "produces": "results/scouts/geo_link_neutral.json",
     "needs": ["results/scouts/geo_capture_neutral_done.json"],
     "why": "E24-S07 neutral linkage: does the alignment-inversion relation survive when "
            "the shared texts carry no process structure?"},
    {"name": "g177_sw_ceiling", "est": 30,
     "cmd": [PY, "runners/run_g177_baselines.py", "--arm", "sw_ceiling"],
     "produces": "results/g177/scholawrite_ceiling.json", "needs": [],
     "why": "the process-aware ceiling: is the next-intention label recoverable from its "
            "own realized edit, deciding whether the boundary belongs to readers or to "
            "the annotation"},
]

# ── STAGE 2 causal branch 2026-08-23 night (its opening condition, the neutral geometry
# replication, landed at 0.768; E24-S08 decides whether mapped geometry is USED).
STAGES += [
    {"name": "scout_s8", "est": 150,
     "cmd": [PY, "runners/scout_stage2_s8.py", "--arm", "run"],
     "produces": "results/scouts/s8_transfer.json", "needs": [],
     "why": "E24-S08 causal direction transfer: maker goal directions mapped into the "
            "cross-family reader, amplified and ablated on artifact tokens, decode gate "
            "before anything, norm-matched random and shuffled controls"},
]

# ── STAGE 2 queue-day 2 opener 2026-08-24 (the affect-ruler rebuild the day-1 close
# named; L162's failure mechanics addressed in the design: 2.5x bank, cross-seed
# consensus locus with the degenerate edge excluded, ladder doses under tolerance).
STAGES += [
    {"name": "scout_a_decode", "est": 90,
     "cmd": [PY, "runners/scout_stage2_a.py", "--arm", "decode"],
     "produces": "results/scouts/a_decode.json", "needs": [],
     "why": "E24-A1/A2 rebuilt ruler: 120 lexicon-clean situations, consensus locus "
            "across three seed splits or INSTRUMENT-FAILED with instability quantified"},
    {"name": "scout_a_causal", "est": 120,
     "cmd": [PY, "runners/scout_stage2_a.py", "--arm", "causal"],
     "produces": "results/scouts/a_causal.json",
     "needs": ["results/scouts/a_decode.json"],
     "why": "the causal re-attempt at the consensus locus: fear/joy sign pair over 24 "
            "scenarios, ladder dose, random and shuffled controls with their own "
            "null-effect failure condition"},
]

# ── STAGE 2 queue-day 2 reload 2026-08-24 early (the last three authorized spine items;
# after these, everything remaining is gated on the curator's walkthrough).
STAGES += [
    {"name": "scout_s6", "est": 25,
     "cmd": [PY, "runners/scout_stage2_s6.py", "--arm", "run"],
     "produces": "results/scouts/s6_tokenizer.json", "needs": [],
     "why": "E24-S6 tokenizer control: does token-segmentation overlap explain the "
            "crossed matrix better than family, double-centered, permutation-nulled"},
    {"name": "g177_anchor_context", "est": 90,
     "cmd": [PY, "runners/run_g177_baselines.py", "--arm", "anchor_context"],
     "produces": "results/g177/anchor_context.json", "needs": [],
     "why": "H05/X05 for the likelihood reader: does a false production note override "
            "evidence the reader provably reads at 0.78, as it did for the prompted "
            "family in G167"},
    {"name": "scout_p_pilot", "est": 60,
     "cmd": [PY, "runners/scout_stage2_p.py", "--arm", "pilot"],
     "produces": "results/scouts/p_pilot.json", "needs": [],
     "why": "the L169 obligation: attractiveness-rebalanced items on three topics, "
            "12-cell compliance pilot; the successor factorial is justified only at "
            "0.70 following"},
]

# ── STAGE 3 (E24-S3, 2026-08-24): the week-long inversion forest. Wave 0 rulers and
# known-positive gates first (V01/E02/A02 gate their trunks), then Wave 1 roots.
# Manifest: results/phase_2_4_stage_3/QUEUE_MANIFEST.json; statuses via soundingline.s3.
S3R = "results/phase_2_4_stage_3"
STAGES += [
    # wave 0 — rulers and admission gates
    {"name": "s3_v01_ruler", "est": 60,
     "cmd": [PY, "runners/s3_run_v.py", "--arm", "v01"],
     "produces": f"{S3R}/V/V01/ruler.json", "needs": [],
     "why": "E24-S3-V01 choice-set ruler: exact Bayes recovery, strength monotonicity, "
            "blind floor, and the makers' 85 percent enactment gate — V02-V06 hang on it"},
    {"name": "s3_e02_ruler", "est": 80,
     "cmd": [PY, "runners/s3_run_e.py", "--arm", "e02"],
     "produces": f"{S3R}/E/E02/gate.json", "needs": [],
     "why": "E24-S3-E02 route ruler on known-policy targets: records-aware must beat "
            "target-only and compute-matched filler, else the E trunk's routes are "
            "instrument-failed before E03 spends anything"},
    {"name": "s3_a02_anchor", "est": 45,
     "cmd": [PY, "runners/s3_run_a.py", "--arm", "a02"],
     "produces": f"{S3R}/A/A02/anchor.json", "needs": [],
     "why": "E24-S3-A02 steering known-positive: additive valence steering with sign "
            "pair, random/shuffled controls, capability-toleranced dose ladder — every "
            "A-trunk causal arm is blocked until this stands"},
    {"name": "s3_s01_gate3", "est": 70,
     "cmd": [PY, "runners/s3_run_s.py", "--arm", "gate3"],
     "produces": f"{S3R}/S/S01/gate3.json", "needs": [],
     "why": "E24-S3-S01 third-family admission: TinyLlama-1.1B-Chat vs OLMo-2-1B-Instruct "
            "at the 85 percent accept-time realization floor on the G172 bank"},
    # wave 1 — trunk roots
    {"name": "s3_e01_selfpolicy", "est": 90,
     "cmd": [PY, "runners/s3_run_e.py", "--arm", "e01"],
     "produces": f"{S3R}/E/E01/profiles.json", "needs": [],
     "why": "E24-S3-E01 self-policy profiles: three instruct readers choose with no "
            "policy line; exact posterior over axis profiles, split-half and paraphrase "
            "stability"},
    {"name": "s3_a01_corpus", "est": 60,
     "cmd": [PY, "runners/s3_run_a.py", "--arm", "a01"],
     "produces": f"{S3R}/A/A01/corpus.json", "needs": [],
     "why": "E24-S3-A01 action-tendency corpus: 24 scenes x 4 tendencies x 2 makers, "
            "source twins by scene, accept-time anchor realization, complete quads only"},
    {"name": "s3_s01_gen3", "est": 90,
     "cmd": [PY, "runners/s3_run_s.py", "--arm", "gen3"],
     "produces": f"{S3R}/S/S01/family3_manifest.json",
     "needs": [f"{S3R}/S/S01/gate3.json"],
     "why": "E24-S3-S01 family-3 corpus from the gate winner, 0.9 yield gate withholds "
            "the manifest"},
    {"name": "s3_s01_matrix3", "est": 80,
     "cmd": [PY, "runners/s3_run_s.py", "--arm", "matrix3"],
     "produces": f"{S3R}/S/S01/matrix3_done.json",
     "needs": [f"{S3R}/S/S01/family3_manifest.json"],
     "why": "E24-S3-S01 new matrix cells only: fam3 reader x old corpora, all readers x "
            "fam3 corpus; Stage-2 reads reused for existing cells (deterministic)"},
    {"name": "s3_s01_analyze", "est": 5,
     "cmd": [PY, "runners/s3_run_s.py", "--arm", "analyze"],
     "produces": f"{S3R}/S/S01/verdict.json",
     "needs": [f"{S3R}/S/S01/matrix3_done.json"],
     "why": "E24-S3-S01 three-family crossed reversal, completeness-guarded, cells "
            "beside contrasts"},
    {"name": "s3_v02_recovery", "est": 60,
     "cmd": [PY, "runners/s3_run_v.py", "--arm", "v02"],
     "produces": f"{S3R}/V/V02/verdict.json",
     "needs": [f"{S3R}/V/V01/ruler.json"],
     "why": "E24-S3-V02 artifact-only preference recovery with a dose curve over "
            "artifacts shown, mechanical extraction, exact posterior"},
    {"name": "s3_l01_gen", "est": 110,
     "cmd": [PY, "runners/s3_run_l.py", "--arm", "gen"],
     "produces": f"{S3R}/L/L01/data_control_s6.jsonl", "needs": [],
     "why": "E24-S3-L01 teacher number-sequence data, 6 seeds x trait/control, strict "
            "numeric filter (benign anchor: an animal preference; safety section 0)"},
    {"name": "s3_l01_train", "est": 45,
     "cmd": [PY, "runners/s3_run_l.py", "--arm", "train"],
     "produces": f"{S3R}/L/L01/adapter_control_s6_r16/adapter_model.safetensors",
     "needs": [f"{S3R}/L/L01/data_control_s6.jsonl"],
     "why": "E24-S3-L01 LoRA students, one per seed x condition, same base init"},
    {"name": "s3_l01_probe", "est": 35,
     "cmd": [PY, "runners/s3_run_l.py", "--arm", "probe"],
     "produces": f"{S3R}/L/L01/verdict.json",
     "needs": [f"{S3R}/L/L01/adapter_control_s6_r16/adapter_model.safetensors"],
     "why": "E24-S3-L01 probe: owl rate per student, full menu distribution, "
            "trait-minus-control over seed pairs"},
    {"name": "s3_c01_ruler", "est": 50,
     "cmd": [PY, "runners/s3_run_c.py", "--arm", "c01"],
     "produces": f"{S3R}/C/C01/verdict.json", "needs": [],
     "why": "E24-S3-C01 late-fusion ruler: exact hold/flip ground truth per item, "
            "graded conflict dose (0/2/8), presentation order crossed"},
    {"name": "s3_d01_ecology", "est": 60,
     "cmd": [PY, "runners/s3_run_d.py", "--arm", "d01"],
     "produces": f"{S3R}/D/D01/manifest.json", "needs": [],
     "why": "E24-S3-D01 four-world ecology: three directed worlds plus an undirected "
            "control, three workers each, 48 episodes per world; reach and exact "
            "attribution per world and per worker"},
    {"name": "s3_m01_patching", "est": 40,
     "cmd": [PY, "runners/s3_run_m.py", "--arm", "m01"],
     "produces": f"{S3R}/M/M01/verdict.json", "needs": [],
     "why": "E24-S3-M01 activation patching: per-block transfer curve of a standing "
            "policy into a bare prompt, identity and mismatched-scenario nulls, "
            "known-positive prompted-shift gate"},
    {"name": "s3_h01_read", "est": 120,
     "cmd": [PY, "runners/s3_run_h.py", "--arm", "h01_read"],
     "produces": f"{S3R}/H/H01/verdict.json",
     "needs": [f"{S3R}/H/H01/bank.json"],
     "why": "E24-S3-H01 RACE rhetorical purpose vs detail, two likelihood readers, "
            "question-only floor, paired within-passage contrast"},
    {"name": "s3_h04_fit", "est": 60,
     "cmd": [PY, "runners/s3_run_h.py", "--arm", "h04"],
     "produces": f"{S3R}/H/H04/verdict.json",
     "needs": [f"{S3R}/H/H04/episodes.json"],
     "why": "E24-S3-H04 CoAuthor contextual-fit AUC on balanced take/dismiss "
            "decisions — the separation position and length could not make"},
    {"name": "s3_s02_data", "est": 80,
     "cmd": [PY, "runners/s3_run_s.py", "--arm", "s02_data"],
     "produces": f"{S3R}/S/S02/pairs_SmolLM2-_cheap_c1.jsonl", "needs": [],
     "why": "E24-S3-S02 training pairs: policy-prompted makers enact; pairs stored "
            "bare-prompt -> realized recommendation, held-out scenarios excluded"},
    {"name": "s3_s02_train", "est": 60,
     "cmd": [PY, "runners/s3_run_s.py", "--arm", "s02_train"],
     "produces": f"{S3R}/S/S02/adapter_SmolLM2-_cheap_c1/adapter_model.safetensors",
     "needs": [f"{S3R}/S/S02/pairs_SmolLM2-_cheap_c1.jsonl"],
     "why": "E24-S3-S02 four LoRA adapters: 2 families x 2 policies, weight-borne "
            "standing policy"},
    {"name": "s3_s02_eval", "est": 50,
     "cmd": [PY, "runners/s3_run_s.py", "--arm", "s02_eval"],
     "produces": f"{S3R}/S/S02/verdict.json",
     "needs": [f"{S3R}/S/S02/adapter_SmolLM2-_cheap_c1/adapter_model.safetensors"],
     "why": "E24-S3-S02 held-out enactment with no policy line; exact posterior must "
            "recover the trained policy; bare maker is the floor"},
    {"name": "s3_l02_grid", "est": 90,
     "cmd": [PY, "runners/s3_run_l.py", "--arm", "l02"],
     "produces": f"{S3R}/L/L02/verdict.json",
     "needs": [f"{S3R}/L/L01/verdict.json"],
     "why": "E24-S3-L02 rank x template grid: rank 4/64 on the L01 data, rank 16 on a "
            "second template; per-cell transmission gaps beside the canonical cell"},
    {"name": "s3_d02_ruler", "est": 70,
     "cmd": [PY, "runners/s3_run_d.py", "--arm", "d02"],
     "produces": f"{S3R}/D/D02/verdict.json", "needs": [],
     "why": "E24-S3-D02 upstream dose ruler: firm/hedged/none director lines, paired "
            "episodes, known dose ordering as the gate"},
    {"name": "s3_e03_factorial", "est": 100,
     "cmd": [PY, "runners/s3_run_e.py", "--arm", "e03"],
     "produces": f"{S3R}/E/E03/verdict.json",
     "needs": [f"{S3R}/E/E02/gate.json"],
     "why": "E24-S3-E03 similarity x route factorial: self / other-family / "
            "programmatic targets, truth = the target's own realized choice"},
    {"name": "s3_a03_tournament", "est": 45,
     "cmd": [PY, "runners/s3_run_a.py", "--arm", "a03"],
     "produces": f"{S3R}/A/A03/tournament.json",
     "needs": [f"{S3R}/A/A01/corpus.json"],
     "why": "E24-S3-A03 basis/locus tournament on the tendency corpus, scene-fold "
            "held-out decode, shuffled null per cell, anchor phrases stripped"},
    {"name": "s3_c02_sources", "est": 45,
     "cmd": [PY, "runners/s3_run_c.py", "--arm", "c02"],
     "produces": f"{S3R}/C/C02/verdict.json", "needs": [],
     "why": "E24-S3-C02 source reliability: verified-track-record archives, "
            "reliable/unreliable/conflict conditions, counterbalanced names"},
    # E24-S3-M02 resolved INSTRUMENT_FAILED in the manifest (the M01 gate
    # failed, so there is no localized depth to interchange); its stage is
    # removed so the queue-empty check can reach zero.
    {"name": "s3_s03_gradient", "est": 10,
     "cmd": [PY, "runners/s3_run_s.py", "--arm", "s03"],
     "produces": f"{S3R}/S/S03/verdict.json",
     "needs": [f"{S3R}/S/S01/verdict.json"],
     "why": "E24-S3-S03 relatedness gradient over the complete three-family matrix, "
            "within-artifact rung permutation"},
    {"name": "s3_l03_fullft", "est": 90,
     "cmd": [PY, "runners/s3_run_l.py", "--arm", "l03"],
     "produces": f"{S3R}/L/L03/verdict.json",
     "needs": [f"{S3R}/L/L01/verdict.json"],
     "why": "E24-S3-L03 full-finetune students on the same data/probe as the LoRA "
            "arm; parameterization is the only moving part"},
    {"name": "s3_d03_structure", "est": 60,
     "cmd": [PY, "runners/s3_run_d.py", "--arm", "d03"],
     "produces": f"{S3R}/D/D03/verdict.json",
     "needs": [f"{S3R}/D/D01/manifest.json"],
     "why": "E24-S3-D03 central vs distributed direction: per-worker posterior "
            "homogeneity as the discriminating signature"},
    {"name": "s3_e04_conflict", "est": 40,
     "cmd": [PY, "runners/s3_run_e.py", "--arm", "e04"],
     "produces": f"{S3R}/E/E04/verdict.json",
     "needs": [f"{S3R}/E/E01/profiles.json", f"{S3R}/E/E02/gate.json"],
     "why": "E24-S3-E04 self-projection intrusion: error direction on conflict items "
            "against the symmetric-error null"},
    {"name": "s3_a04_dissociate", "est": 40,
     "cmd": [PY, "runners/s3_run_a.py", "--arm", "a04"],
     "produces": f"{S3R}/A/A04/verdict.json",
     "needs": [f"{S3R}/A/A03/tournament.json"],
     "why": "E24-S3-A04 fear-anger dissociation: tendency must separate what the "
            "frozen valence axis cannot"},
    {"name": "s3_c03_biography", "est": 50,
     "cmd": [PY, "runners/s3_run_c.py", "--arm", "c03"],
     "produces": f"{S3R}/C/C03/verdict.json", "needs": [],
     "why": "E24-S3-C03 biography vs record: four context conditions, conflict "
            "decides narrative-vs-evidence"},
    {"name": "s3_a06_suppress", "est": 40,
     "cmd": [PY, "runners/s3_run_a.py", "--arm", "a06"],
     "produces": f"{S3R}/A/A06/verdict.json",
     "needs": [f"{S3R}/A/A03/tournament.json"],
     "why": "E24-S3-A06 expressivity suppression: does tendency survive a flat "
            "register? Suppression verified on surface before leakage is claimed"},
    {"name": "s3_c04_position", "est": 45,
     "cmd": [PY, "runners/s3_run_c.py", "--arm", "c04"],
     "produces": f"{S3R}/C/C04/verdict.json",
     "needs": [f"{S3R}/C/C01/verdict.json"],
     "why": "E24-S3-C04 conflict position early/middle/late where Bayes is "
            "position-invariant"},
    {"name": "s3_c05_uptake", "est": 45,
     "cmd": [PY, "runners/s3_run_c.py", "--arm", "c05"],
     "produces": f"{S3R}/C/C05/verdict.json",
     "needs": [f"{S3R}/C/C01/verdict.json"],
     "why": "E24-S3-C05 attend-vs-weigh decomposition: mechanical recall stage "
            "before prediction on the FLIP items"},
    {"name": "s3_c06_sycophancy", "est": 45,
     "cmd": [PY, "runners/s3_run_c.py", "--arm", "c06"],
     "produces": f"{S3R}/C/C06/verdict.json",
     "needs": [f"{S3R}/C/C01/verdict.json"],
     "why": "E24-S3-C06 does an expressed user hope bend prediction against the "
            "record; hint-following rate on conflict items"},
    {"name": "s3_e05_probing", "est": 30,
     "cmd": [PY, "runners/s3_run_e.py", "--arm", "e05"],
     "produces": f"{S3R}/E/E05/verdict.json",
     "needs": [f"{S3R}/E/E02/gate.json"],
     "why": "E24-S3-E05 active probing: pick the discriminating record over the "
            "uninformative one, exact answer known"},
    {"name": "s3_v04_transfer", "est": 50,
     "cmd": [PY, "runners/s3_run_v.py", "--arm", "v04"],
     "produces": f"{S3R}/V/V04/verdict.json",
     "needs": [f"{S3R}/V/V01/ruler.json"],
     "why": "E24-S3-V04 cross-domain profile transfer, exact ceiling first, "
            "within-domain cells beside cross"},
    {"name": "s3_m03_crossmodel", "est": 40,
     "cmd": [PY, "runners/s3_run_m.py", "--arm", "m03"],
     "produces": f"{S3R}/M/M03/verdict.json",
     "needs": [f"{S3R}/M/M01/verdict.json"],
     "why": "E24-S3-M03 the M01 procedure on the second family; curves compared at "
            "normalized depth"},
    {"name": "s3_m04_equivalence", "est": 30,
     "cmd": [PY, "runners/s3_run_m.py", "--arm", "m04"],
     "produces": f"{S3R}/M/M04/verdict.json",
     "needs": [f"{S3R}/M/M01/verdict.json",
               f"{S3R}/S/S02/adapter_Qwen2.5-_robust_c1/adapter_model.safetensors"],
     "why": "E24-S3-M04 prompt/activation/adapter shift-vector agreement on shared "
            "scenarios"},
    {"name": "s3_l04_geometry", "est": 40,
     "cmd": [PY, "runners/s3_run_l.py", "--arm", "l04"],
     "produces": f"{S3R}/L/L04/verdict.json",
     "needs": [f"{S3R}/L/L01/data_control_s6.jsonl"],
     "why": "E24-S3-L04 does anything measurable separate trait from control number "
            "sequences; cross-seed train/test, surface then representation"},
    {"name": "s3_l05_policychannel", "est": 120,
     "cmd": [PY, "runners/s3_run_l.py", "--arm", "l05"],
     "produces": f"{S3R}/L/L05/verdict.json", "needs": [],
     "why": "E24-S3-L05 a decision policy through the number channel, probed in the "
            "environment with the exact posterior"},
    {"name": "s3_e06_ordering", "est": 60,
     "cmd": [PY, "runners/s3_run_e.py", "--arm", "e06"],
     "produces": f"{S3R}/E/E06/verdict.json",
     "needs": [f"{S3R}/E/E02/gate.json"],
     "why": "E24-S3-E06 record-before-question vs after, where exact inference is "
            "order-blind"},
    {"name": "s3_d04_levels", "est": 45,
     "cmd": [PY, "runners/s3_run_d.py", "--arm", "d04"],
     "produces": f"{S3R}/D/D04/verdict.json",
     "needs": [f"{S3R}/D/D01/manifest.json"],
     "why": "E24-S3-D04 direction-vs-preference attribution on balanced episodes, "
            "with and without the world record"},
    {"name": "s3_d05_rewrite", "est": 50,
     "cmd": [PY, "runners/s3_run_d.py", "--arm", "d05"],
     "produces": f"{S3R}/D/D05/verdict.json", "needs": [],
     "why": "E24-S3-D05 the relay ladder: policy grip vs paraphrase hops, hop texts "
            "saved"},
    {"name": "s3_d06_prospective", "est": 50,
     "cmd": [PY, "runners/s3_run_d.py", "--arm", "d06"],
     "produces": f"{S3R}/D/D06/verdict.json",
     "needs": [f"{S3R}/D/D01/manifest.json"],
     "why": "E24-S3-D06 forecasting a directed worker's fresh choice from the world "
            "record; truth generated accept-time first"},
    {"name": "s3_s04_procladder", "est": 90,
     "cmd": [PY, "runners/s3_run_s.py", "--arm", "s04"],
     "produces": f"{S3R}/S/S04/verdict.json", "needs": [],
     "why": "E24-S3-S04 six-procedure ladder with per-rung compliance checks; "
            "reader arm against a word-echo floor (the G166 question, mechanized)"},
    {"name": "s3_s05_bottleneck", "est": 120,
     "cmd": [PY, "runners/s3_run_s.py", "--arm", "s05"],
     "produces": f"{S3R}/S/S05/verdict.json", "needs": [],
     "why": "E24-S3-S05 15-word-summary bottleneck erasure; does the crossed "
            "reversal survive semantic-only transmission"},
    {"name": "s3_s06_attribution", "est": 50,
     "cmd": [PY, "runners/s3_run_s.py", "--arm", "s06"],
     "produces": f"{S3R}/S/S06/verdict.json", "needs": [],
     "why": "E24-S3-S06 does naming the maker family help goal recovery, and does "
            "a wrong name hurt; conditional-reader interface"},
    {"name": "s3_s07_confirm", "est": 10,
     "cmd": [PY, "runners/s3_run_s.py", "--arm", "s07"],
     "produces": f"{S3R}/S/S07/verdict.json",
     "needs": [f"{S3R}/S/S03/verdict.json"],
     "why": "E24-S3-S07 reserve-quarter confirmation of the S-trunk headline, "
            "frozen md5 side assignment"},
    {"name": "s3_a05_mixtures", "est": 50,
     "cmd": [PY, "runners/s3_run_a.py", "--arm", "a05"],
     "produces": f"{S3R}/A/A05/verdict.json",
     "needs": [f"{S3R}/A/A03/tournament.json"],
     "why": "E24-S3-A05 two-tendency blends read as top-2 of the single-tendency "
            "centroids, fit only on singles"},
    {"name": "s3_a07_causal", "est": 60,
     "cmd": [PY, "runners/s3_run_a.py", "--arm", "a07"],
     "produces": f"{S3R}/A/A07/verdict.json",
     "needs": [f"{S3R}/A/A02/anchor.json", f"{S3R}/A/A03/tournament.json"],
     "why": "E24-S3-A07 steering the tendency directions during forced-choice "
            "endings; sign pair + random control under capability tolerance"},
    {"name": "s3_h02_transfer", "est": 90,
     "cmd": [PY, "runners/s3_run_h.py", "--arm", "h02"],
     "produces": f"{S3R}/H/H02/verdict.json",
     "needs": [f"{S3R}/H/H01/verdict.json"],
     "why": "E24-S3-H02 the purpose-vs-detail structure on the RACE middle split, "
            "nothing tuned between"},
    {"name": "s3_h03_social", "est": 80,
     "cmd": [PY, "runners/s3_run_h.py", "--arm", "h03"],
     "produces": f"{S3R}/H/H03/verdict.json", "needs": [],
     "why": "E24-S3-H03 SocialIQA social-intent control with the same scorer and "
            "question-only floor"},
    {"name": "s3_h07_reviews", "est": 20,
     "cmd": [PY, "runners/s3_run_h.py", "--arm", "h07"],
     "produces": f"{S3R}/H/H07/verdict.json", "needs": [],
     "why": "E24-S3-H07 OpenReview mirror hunt; RESOURCE_BLOCKED with receipts if "
            "no mirror reachable"},
    {"name": "s3_v05_editor", "est": 40,
     "cmd": [PY, "runners/s3_run_v.py", "--arm", "v05"],
     "produces": f"{S3R}/V/V05/verdict.json",
     "needs": [f"{S3R}/V/V01/ruler.json"],
     "why": "E24-S3-V05 editor profile from edit directions: exact half then a "
            "model-editor arm"},
    # ── frozen-ladder expansion cells that need no new code (2026-08-26)
    {"name": "s3x_l01_gen712", "est": 240,
     "cmd": [PY, "runners/s3_run_l.py", "--arm", "gen", "--seeds",
             "7,8,9,10,11,12"],
     "produces": f"{S3R}/L/L01/data_control_s12.jsonl", "needs": [],
     "why": "E24-S3-L01/X1 six fresh data seeds (independent-information rung 1); "
            "the transmission null's n doubles if the theory needs it"},
    {"name": "s3x_l01_train712", "est": 45,
     "cmd": [PY, "runners/s3_run_l.py", "--arm", "train", "--seeds",
             "7,8,9,10,11,12"],
     "produces": f"{S3R}/L/L01/adapter_control_s12_r16/adapter_model.safetensors",
     "needs": [f"{S3R}/L/L01/data_control_s12.jsonl"],
     "why": "E24-S3-L01/X1 students for seeds 7-12"},
    {"name": "s3x_l01_probe712", "est": 35,
     "cmd": [PY, "runners/s3_run_l.py", "--arm", "probe", "--seeds",
             "7,8,9,10,11,12"],
     "produces": f"{S3R}/L/L01/verdict_r16_t1_s7-12.json",
     "needs": [f"{S3R}/L/L01/adapter_control_s12_r16/adapter_model.safetensors"],
     "why": "E24-S3-L01/X1 probe; separate verdict name, canonical untouched"},
    {"name": "s3x_s02_data_c2", "est": 80,
     "cmd": [PY, "runners/s3_run_s.py", "--arm", "s02_data", "--cohort", "2"],
     "produces": f"{S3R}/S/S02/pairs_SmolLM2-_cheap_c2.jsonl", "needs": [],
     "why": "E24-S3-S02/X1 second independent adapter cohort, fresh data seeds"},
    {"name": "s3x_s02_train_c2", "est": 60,
     "cmd": [PY, "runners/s3_run_s.py", "--arm", "s02_train", "--cohort", "2"],
     "produces": f"{S3R}/S/S02/adapter_SmolLM2-_cheap_c2/adapter_model.safetensors",
     "needs": [f"{S3R}/S/S02/pairs_SmolLM2-_cheap_c2.jsonl"],
     "why": "E24-S3-S02/X1 cohort-2 adapters"},
    {"name": "s3x_s02_eval_c2", "est": 50,
     "cmd": [PY, "runners/s3_run_s.py", "--arm", "s02_eval", "--cohort", "2"],
     "produces": f"{S3R}/S/S02/verdict_c2.json",
     "needs": [f"{S3R}/S/S02/adapter_SmolLM2-_cheap_c2/adapter_model.safetensors"],
     "why": "E24-S3-S02/X1 cohort-2 evaluation against the cohort-1 verdict"},
    # ── expansion + adversarial arms built 2026-08-26 (careful-and-slow order)
    {"name": "s3x_v01x1", "est": 30,
     "cmd": [PY, "runners/s3_run_v.py", "--arm", "v01x1"],
     "produces": f"{S3R}/V/V01/profiles5to8.json", "needs": [],
     "why": "E24-S3-V01/X1 blends + EIG strength leg (margin metric retired, L215); "
            "identifiability 29/30 proven at build"},
    {"name": "s3x_v04x4", "est": 40,
     "cmd": [PY, "runners/s3_run_v.py", "--arm", "v04x4"],
     "produces": f"{S3R}/V/V04/domain3.json",
     "needs": [f"{S3R}/V/V04/verdict.json"],
     "why": "E24-S3-V04/X4 third-domain transfer (events bank, 144 anchors "
            "self-tested)"},
    {"name": "s3x_e03x1", "est": 60,
     "cmd": [PY, "runners/s3_run_e.py", "--arm", "e03x1"],
     "produces": f"{S3R}/E/E03/policies7to12.json",
     "needs": [f"{S3R}/E/E02/gate.json"],
     "why": "E24-S3-E03/X1 six blend-policy targets, record route, verdict-gated "
            "on E02"},
    {"name": "s3x_e03x4", "est": 45,
     "cmd": [PY, "runners/s3_run_e.py", "--arm", "e03x4"],
     "produces": f"{S3R}/E/E03/domain2.json",
     "needs": [f"{S3R}/E/E02/gate.json"],
     "why": "E24-S3-E03/X4 record route on the held-out process domain"},
    {"name": "s3x_c01x4", "est": 45,
     "cmd": [PY, "runners/s3_run_c.py", "--arm", "c01x4"],
     "produces": f"{S3R}/C/C01/domain2.json", "needs": [],
     "why": "E24-S3-C01/X4 late-fusion ruler on the process domain — is the L209 "
            "base failure domain-general? Cache-safe file tags"},
    {"name": "s3x_d01x1", "est": 40,
     "cmd": [PY, "runners/s3_run_d.py", "--arm", "d01x1"],
     "produces": f"{S3R}/D/D01/roles5to8.json",
     "needs": [f"{S3R}/D/D01/manifest.json"],
     "why": "E24-S3-D01/X1 fresh worker-role permutation over the directed worlds; "
            "kills D01 if reach moves with assignment"},
    {"name": "s3x_a06x4", "est": 60,
     "cmd": [PY, "runners/s3_run_a.py", "--arm", "a06x4"],
     "produces": f"{S3R}/A/A06/domain2.json",
     "needs": [f"{S3R}/A/A01/corpus.json"],
     "why": "E24-S3-A06/X4 channel-audit-first suppression on a second scene bank "
            "(the L201 lesson enforced: no GPU without a verifiable channel)"},
    {"name": "s3x_s05x3", "est": 120,
     "cmd": [PY, "runners/s3_run_s.py", "--arm", "s05x3"],
     "produces": f"{S3R}/S/S05/eraser3.json",
     "needs": [f"{S3R}/S/S01/gate3.json"],
     "why": "E24-S3-S05/X3 the bottleneck through the stake-free OLMo eraser — "
            "stronger erasure evidence than the SmolLM channel"},
    {"name": "s3x_xv2", "est": 20,
     "cmd": [PY, "runners/s3_run_x.py", "--arm", "xv2"],
     "produces": f"{S3R}/X/XV2_verdict.json",
     "needs": [f"{S3R}/A/A02/anchor.json"],
     "why": "XV2 adversary on the steering anchor: neutral-pair control and "
            "token-injection probe"},
    {"name": "s3x_xv3", "est": 30,
     "cmd": [PY, "runners/s3_run_x.py", "--arm", "xv3"],
     "produces": f"{S3R}/X/XV3_verdict.json", "needs": [],
     "why": "XV3 adversary on the sycophancy override: ignorant-stranger "
            "attribution vs the 0.833 baseline"},
    {"name": "s3x_xv4", "est": 25,
     "cmd": [PY, "runners/s3_run_x.py", "--arm", "xv4"],
     "produces": f"{S3R}/X/XV4_verdict.json",
     "needs": [f"{S3R}/L/L01/data_control_s6.jsonl"],
     "why": "XV4 adversary on the transmission carrier: trivial scalars and "
            "length-matched representation"},
    {"name": "s3x_h03_retry", "est": 90,
     "cmd": [PY, "runners/s3_run_h.py", "--arm", "h03"],
     "produces": f"{S3R}/H/H03/retry_receipt.json", "needs": [],
     "why": "E24-S3-H03 retry through the parquet branch; writes its receipt "
            "in both outcomes so the stage resolves either way"},
    {"name": "s3x_l01x1_final", "est": 5,
     "cmd": [PY, "runners/s3_run_x.py", "--arm", "l01x1_final"],
     "produces": f"{S3R}/L/L01/seeds7to12.json",
     "needs": [f"{S3R}/L/L01/verdict_r16_t1_s7-12.json"],
     "why": "E24-S3-L01/X1 finalizer: pooled 12-seed transmission gap into the "
            "manifest produce"},
    {"name": "s3x_s02x1_final", "est": 5,
     "cmd": [PY, "runners/s3_run_x.py", "--arm", "s02x1_final"],
     "produces": f"{S3R}/S/S02/cohort2.json",
     "needs": [f"{S3R}/S/S02/verdict_c2.json"],
     "why": "E24-S3-S02/X1 finalizer: cohort-2 vs cohort-1 recovery comparison"},
]

# ── Heavy-GPU marking, consumed by --no-gpu (first gear). Sustained trainings and sustained
# ollama generation hold for second gear; brief-touch reader stages stay unmarked by design
# ("the card only briefly" is first gear's own contract).
_GPU_HEAVY_PREFIXES = ("pan_", "pan25_", "sw_", "scholawrite_", "gen_fiction", "s3_")
_GPU_HEAVY_NAMES = {"nomaker2_gen", "nomaker_ds_gen", "g153_gen_qwen", "g153_gen_llama",
                    "g159_gen_qwen", "g159_gen_llama", "g94_taramsa_gpu",
                    "g159_rec_p_plus", "g159_rec_p_minus", "g159_rec_blind",
                    "g162_gen_qwen", "g162_gen_llama", "g162r_validate", "g162r_classify",
                    "g162r_classify_delta", "g162r_blind",
                    "g159_rec_fabrication", "g159_rec_surface", "g159_rec_delta",
                    "g131_gen_qwen", "g131_gen_llama",
                    "g129_recovery", "g129_blind", "g129_shuffle", "g129_brief",
                    "g129_source", "g129_unchanged", "g129_recovery_matched",
                    "g129_blind_matched", "g158_reader_qwen", "g158_reader_llama",
                    "g158_reader_validate", "g158_recovery_surface",
                    "g158_recovery_none", "g158_recovery_problem",
                    "g129b_recovery", "g129b_blind", "g129b_shuffle", "g129b_brief",
                    "g129b_source", "g129b_unchanged", "g129b_recovery_matched",
                    "g129b_blind_matched",
                    "g165_self_route", "g165_cand_disc", "g165_self_route_leak",
                    "g165_cand_disc_leak", "g166_gen_qwen", "g166_gen_llama",
                    "g165d_sr_delta", "g165d_cd_delta", "g165d_sr_unchanged",
                    "g166r_process", "g166r_classify", "g166r_blind",
                    "g167_true_card", "g167_false_card", "g167_irrelevant_card",
                    "g169_gen_qwen", "g169_gen_llama",
                    "g167a5_true_note", "g167a5_false_note", "g167a5_false_note_flag",
                    "g169_regen_qwen", "g169_regen_llama",
                    "g169r_validate", "g169r_classify", "g169r_span", "g169r_blind",
                    "g168_gen", "g168r_process", "g168r_classify",
                    "g172_corpus", "g172_matrix", "g174_ruler", "g177_anchor",
                    "g177_sw_reader", "scout_s02_para", "scout_s02_matrix",
                    "scout_gen2", "scout_para2", "scout_mx_orig", "scout_mx_fam2",
                    "scout_mx_norm", "scout_mx_para_qwen", "scout_mx_para2",
                    "scout_mx_para_qwen2", "scout_mx_origL", "scout_mx_fam2L",
                    "g177_sw_validation", "g177_sw_nongen", "scout_p_gen", "scout_p_read", "scout_geo_capture", "scout_p_self", "scout_geo_capture_n", "scout_s8", "scout_a_decode", "scout_a_causal", "g177_anchor_context", "scout_p_pilot"}
for s_ in STAGES:
    if s_["name"].startswith(_GPU_HEAVY_PREFIXES) or s_["name"] in _GPU_HEAVY_NAMES:
        s_["gpu"] = True

_prods = [s_["produces"] for s_ in STAGES]
_shared = sorted({q for q in set(_prods) if _prods.count(q) > 1})
assert not _shared, f"stages share a produces path: {_shared}"


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
    ap.add_argument("--no-gpu", action="store_true",
                    help="first gear: skip stages marked gpu (heavy trainings and sustained "
                         "generation). The card is the curator's; those stages wait for second "
                         "gear. Brief GPU touches by unmarked stages are allowed by design")
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

    # ownership by stable NAME digest, never list index: inserting a stage mid-list under a
    # live lineage used to re-own every later stage between passes, and a blocked stage
    # launched twice under old and new owners (2026-08-19, the duplicate shuffle arms;
    # LESSONS §5). md5 because Python hash() is process-salted (the G131 seed lesson).
    import hashlib as _hl                                              # noqa: PLC0415
    own = lambda s: int(_hl.md5(s["name"].encode()).hexdigest(), 16) % SHARDS  # noqa: E731
    mine = [s for s in STAGES if own(s) == SHARD]
    if a.no_gpu:
        held = [s["name"] for s in mine if s.get("gpu")]
        mine = [s for s in mine if not s.get("gpu")]
        if held:
            print(f"[gear1] holding {len(held)} gpu stage(s) for second gear: "
                  f"{', '.join(held)}", flush=True)
        state["held_for_gear2"] = held
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
            # a clean exit that never wrote its produce is a failure, not a DONE — the fiction
            # feature stages ran "DONE" for a day on a silent per-corpus skip (2026-08-12).
            # The exists() check retries briefly: one stage (gridmax, 2026-08-14) recorded a
            # false no-produce with the file on disk at the stage-end minute, so filesystem
            # visibility immediately after subprocess exit is not trusted bare.
            if entry["status"] == "DONE" and st.get("produces"):
                for _ in range(20):
                    if rel(st["produces"]).exists():
                        break
                    time.sleep(0.5)
                if not rel(st["produces"]).exists():
                    entry["status"] = "FAILED (exit 0, no produce)"
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
