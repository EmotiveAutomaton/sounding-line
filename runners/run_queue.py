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
# docs/design/PHASE_2_3_REGISTRY.md; cards frozen before arms). G165 = the Wing G
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

# ── Heavy-GPU marking, consumed by --no-gpu (first gear). Sustained trainings and sustained
# ollama generation hold for second gear; brief-touch reader stages stay unmarked by design
# ("the card only briefly" is first gear's own contract).
_GPU_HEAVY_PREFIXES = ("pan_", "pan25_", "sw_", "scholawrite_", "gen_fiction")
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
                    "g166r_process", "g166r_classify", "g166r_blind"}
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
