# STATE — the agent's operational file

> ## ⚠ IF YOU HAVE JUST BEEN COMPACTED: RELOAD THE THEORY FIRST
>
> Before any research, any literature reading, or any judgement about a result:
> **read the whole of `docs/theory/`, newest first, then `FINDINGS.md`, then this file.** A
> compaction preserves what happened and loses the framework's shape, which is exactly the state in
> which confident literature overwrites it. That has happened twice. See `CLAUDE.md`, first section.

**Rewritten 2026-08-08, immediately before an expected compaction.** Everything below is current.

## ⚠ HARD CONSTRAINTS, SET BY THE CURATOR 2026-08-08

1. **NO SUBAGENTS. NONE.** No Agent tool, no Workflow tool, no research agents, no fleets. The
   standing authorisation from 08-05 is **suspended by him, explicitly** — token limits. Do all nine
   audit scopes and all research **inline, yourself, slowly**. He may restore a fleet later; until he
   says so in his own words, spawn nothing. **Do not resume workflow `wf_8f6826fa-9ee`.**
2. **Token conservation.** Most important work first; batch tool calls; no polling loops; keep
   replies dense. The session usage limit was hit once already (9-agent fleet died mid-flight).
3. **Model is now Fable at max effort** (was Opus at medium for most of the project — he considers
   that a possible source of accumulated sloppiness, hence the standing audit).

## The priority ladder, his words, in order

1. **`docs/theory/` files (not `essays/`) perfectly interpretable at a glance and very clean.**
   His quotations are the most valuable information in the project — never delete them; shrink or
   move only if no longer relevant to their section.
2. **The model and all the tests** — the solo audit of every runner and recorded number
   (details in `FINDINGS.md`).
3. **Minor errors**, prioritised at my discretion.

## Renaming, done 2026-08-08

**THE_TRIPLE_INFERENCE.md → THE_TRIPLE_INFERENCE.md**, references updated repo-wide, his choice.
**The provenance must never be lost:** he is *specifically modelling human empathy* — the process he
believes human empathy is. "Triple inference" names the mechanism; empathy remains the phenomenon.
His words to that effect are the second blockquote of the renamed file. TR- identifiers unchanged.

## The solo audit — nine scopes, status

| scope | status |
|---|---|
| **queue ↔ runner contracts** | **PARTIAL.** Found: 3 unguarded stages churning (fixed); bits96 overwrote the 48-decoy file; two stages tested nothing (L20). **Remaining:** systematic argparse-vs-STAGES sweep; explain the 78-second ladder2 re-score (G99) |
| **spec reconstruction vs generation** | **CLEARED, decisively.** 100/100 ladder2 seeds and 175/175 topics match the consumer formula; ladder3 generation holds draws constant across retries. Plus the find of the day: **L22 — the induction control's regressors contain the dose** (row-sum = rung; ladder3 pool = 60 = all drawn at top rung) |
| **reader-side statistics** | **NOT STARTED.** Priority items: run_depth_readouts coherence formula and band split (cross-family sign flips now carry theory weight — could a per-family sign convention manufacture them?); run_subspace_alignment basis dimension after centring (span ≤ 7 not 8?); run_layer_correlation null symmetry |
| **spec-recovery / void_power math** | **PARTIAL.** Found: bits saturated (near-binary; win rate is the honest statistic); shuffle chance 1/48 = 2.08%. **Remaining:** tie rule `>=`, decoy construction overlap, v4 StratifiedKFold degeneracy |
| **features / BY / units** | **NOT STARTED.** Priority: run_pan_features keys-from-first-problem-only; BY implementation in select.py; units consistency across the three feature libraries |
| **decomposition family** | **NOT STARTED.** Priority: the participation-ratio correction formula (behavioural test on known-rank synthetic data); **the hard-coded VAD table in run_affect_dimensions is UNVERIFIED against real NRC-VAD — fabrication risk on the replication gate** |
| **core package + locks** | **DONE for locks:** SPEC was deleted 08-07, caught by hash check, restored byte-exact (DEVIATIONS); 5 gate files relocated to docs/gates/, hash-verified. **Remaining:** activations.py token pooling (BOS handling per family — candidate mechanism for cross-family sign flips); n=4 direction stability |
| **docs vs data** | **PARTIAL** (n=40 label fixed). **Remaining:** systematic sweep of every FINDINGS number against its JSON; orphan sweep; G-identifier collisions (G70/G70b known) |
| **corpora integrity** | **NOT STARTED.** Priority: ladder3 out-of-band tail rung-correlation in absolute words; manifest-vs-disk counts; PAN train/validation leakage |

## The theory glance-clean worklist (priority 1), file by file

Format spec is in `docs/theory/README.md`. Per file, in this order:
1. **THE_TRIPLE_INFERENCE.md** — rename landed; check flow after all insertions; §2 additivity-vs-Venn discussion could compress.
2. **POLISH_AND_DEPTH.md** — grew the most mid-session: the redefinition block + four objections + naming search + latent-variable insert sit ABOVE §1. **Restructure so the current definition and its status are §1**, the naming search compresses, and the objections sit with the definition they attack.
3. **THREE_COGNITIVE_LAYERS.md** — verify section numbering after the worry-section move; the two-orderings §1 is good; §8 (worry) and §9 (build) flow.
4. **HUMAN_HEURISTICS.md** — §0a/§0b harvest sections are long; consider moving the technique tables to `docs/method/` with one-line pointers, keeping only what changes theory.
5. **ALIGNMENT.md** — smallest, mostly fine.
**Rule for the pass: his blockquotes are untouchable; my prose compresses.**

## Queue / infrastructure state

- **Day loop:** one detached shell (survives sessions), lock in `results/.loop.lock`; stop with
  `kill $(cat results/.loop.lock)`. Night: `bash run_forever_night.sh [hours] [workers]` (refuses
  while day loop runs). Queue has pid lock + `--shard/--shards`.
- **STAGES now:** `run_induction_v2.py` on ladder2 / ladder3 / ladder — **the rebuilt within-rung
  induction control (G75★★), which re-adjudicates L1, L2's kills, and L17** — then the two audits.
  It saves per-artifact rows so future re-analyses are CPU-only.
- Every stage must carry a `produces` guard. Verify hash locks + read `git status` deletions before
  every commit (CLAUDE.md hard rule, born of the SPEC deletion).

## Open decisions / owed

- **G75 result → re-adjudicate L1 / L2 / L17 in FINDINGS and theory tables when it lands.**
- The four-file corpus problem (one maker, many kinds): CROSSNEWS = pseudo-documents only;
  Guardian (13 authors) better kind-contrast; CMCC = email the authors (C-32a).
- Interest ratings on his 15 artifacts — owed by him, cheapest instrument test (HH-14).
- PAN22 Aston application — his side.
- Rotate the Anthropic API key pasted early in the project — his side, still owed.
