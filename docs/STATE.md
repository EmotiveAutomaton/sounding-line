# STATE: the agent's operational file

> ## ⚠ IF YOU HAVE JUST BEEN COMPACTED: RELOAD THE THEORY FIRST
>
> Before any research, any literature reading, or any judgement about a result:
> **read the whole of `docs/theory/`, newest first, then `FINDINGS.md`, then this file.** A
> compaction preserves what happened and loses the framework's shape, which is exactly the state in
> which confident literature overwrites it. That has happened twice. See `CLAUDE.md`, first section.

**Rewritten 2026-08-08, immediately before an expected compaction.** Everything below is current.

## ⚠ HARD CONSTRAINTS, SET BY THE CURATOR 2026-08-08

1. **SUBAGENTS ONLY WHEN HE ASKS** (corrected 2026-08-08; the blanket ban was temporary and I
   over-wrote it). He asks → spawn, briefed per CLAUDE.md; he says "ultracode" → Workflow tool,
   conservatively sized; otherwise inline. The 08-05 spawn-at-discretion authorisation stays retired.
2. **Token conservation.** Most important work first; batch tool calls; no polling loops; keep
   replies dense. The session usage limit was hit once already (9-agent fleet died mid-flight).
3. **Model is now Fable at max effort** (was Opus at medium for most of the project, which he
   considers a possible source of accumulated sloppiness, hence the standing audit).

## The priority ladder, his words, in order

1. **`docs/theory/` files (not `essays/`) perfectly interpretable at a glance and very clean.**
   His quotations are the most valuable information in the project. Never delete them; shrink or
   move only if no longer relevant to their section.
2. **The model and all the tests**, meaning the solo audit of every runner and recorded number
   (details in `FINDINGS.md`).
3. **Minor errors**, prioritised at my discretion.

## Renaming and the five-file contract (renames 2026-08-08/09, contract final 2026-08-09)

**THE_EMPATHY_TRIANGLE.md became THE_TRIPLE_INFERENCE.md**, references updated repo-wide, his choice.
**The provenance must never be lost.** He is *specifically modelling human empathy*, the process he
believes human empathy is. "Triple inference" names the mechanism; empathy remains the phenomenon.
His words to that effect are the second blockquote of the renamed file. TR- identifiers unchanged.
Then **POLISH_AND_DEPTH.md became DECISION_TRACES.md** and **HUMAN_HEURISTICS.md became
READER_HEURISTICS.md** (2026-08-09, both his restructure directives; PD-/HH- identifiers unchanged).

**Each theory file owns exactly one question, and cross-links transmit conclusions only:**

    THE_TRIPLE_INFERENCE     what is inferred; dependencies among targets; identifiability
    THREE_COGNITIVE_LAYERS   what architecture might support the inference
    DECISION_TRACES          what observable traces the maker's decisions leave
    READER_HEURISTICS        how a bounded reader finds, combines, and calibrates those traces
    ALIGNMENT                what objective should govern a system after it can read them

**Reserved vocabulary:** functional level / region / block / subspace. "Layer" unqualified is
banned. Blockquotes are the curator's words only. The corrected ontology's load-bearing
distinctions: **process ≠ expertise, drives ≠ values, three questions not three equal nodes,
depth is domain-relative** (the relation cannot be measured by varying one side).

**Style rules for every curated markdown (his directive, 2026-08-09).** No em dashes and no en
dashes in prose; restructure the sentence instead. Colons live in headers, titles, and labels
only, never as transition devices inside sentences. Inside his quote blocks an em dash becomes an
en dash and nothing else changes. No "it's not A, it's B" punchline constructions.

## The research program (superseded the 08-09 morning scoping, same day)

**The unit of analysis changed.** Stop searching for a scalar that correlates with depth. Validate
recovery of individual, independently recorded choices, where a decision event carries target,
alternatives, choice, dependencies, and context. Summaries (amount, breadth, integration, with
calibration separate) come only after event recovery works. Denominator is choice opportunities,
never words. "Specified intent" is now "specified constraint dose" wherever the ladder is meant.

**Allocation across the five files.** DECISION_TRACES is primary (choice-event recovery, depth
against polish, forced-constraint nulls). READER_HEURISTICS is operational support (bounded
candidates, entry points, calibration, reader disagreement). THE_TRIPLE_INFERENCE is the secondary
program (process recovery first, longitudinal value prediction later). THREE_COGNITIVE_LAYERS is
instrument research only (do model quantities improve choice recovery). ALIGNMENT is dormant, a
boundary specification with a written wake condition.

**The queue, in order.** Re-adjudicate stale labels (done, L2/L30/L34/L36/L40/L42). Build and
validate the shared event-level recovery harness (G130, **done, HARNESS-VALID, L56**). Then the
frontier-recreation phase his 08-09 evening directive inserted ahead of everything else. **The
pass standard (his ruling, 08-10): a recreation passes only by reproducing published exact
values to roughly typo distance; a large shortfall is a defect in our model of their pipeline
and is hunted, not caveated; download, run, and remove the exact models papers used where
needed.** The recreations: recreate
ArgRewrite's published revision-classification baselines (G136, the gate G129 runs behind),
recreate the Baker–Saxe–Tenenbaum gridworld in the parent sim (G137, G134's substrate), recreate
the Armstrong–Mindermann unidentifiability construction then relax it with the three human priors
(G138). Then the program proper: G129 preregistered ArgRewrite choice recovery, G130b lexical
matching, G131 factorial benchmark, G132 ScholaWrite behind its own baseline recreation, G133
commissioned pilot, G134 estimator tournament, G135 held-out tradeoff prediction. `TODO.md` now
opens with the plan and carries the full phase tables.

**Deprioritized by name.** Detector races, feature stacking before choice recovery validates,
entropy and compression style summaries, more global averages, more transformer address searches,
values from the 34-book corpus, interest ratings as ground truth (still useful inside
READER_HEURISTICS), alignment experiments.

## The solo audit: nine scopes, status

| scope | status |
|---|---|
| **queue ↔ runner contracts** | **PARTIAL.** Found: 3 unguarded stages churning (fixed); bits96 overwrote the 48-decoy file; two stages tested nothing (L20). **Remaining:** systematic argparse-vs-STAGES sweep; explain the 78-second ladder2 re-score (G99) |
| **spec reconstruction vs generation** | **CLEARED, decisively.** 100/100 ladder2 seeds and 175/175 topics match the consumer formula; ladder3 generation holds draws constant across retries. Plus the find of the day, **L22, where the induction control's regressors contain the dose** (row-sum = rung; ladder3 pool = 60 = all drawn at top rung) |
| **reader-side statistics** | **LARGELY DONE via rebuilds.** Coherence formula: statistic was geometrically void (L26) → rebuilt known-answer-gated, G33 re-adjudicated across eight families (L47). Subspace basis: rank-7-in-8 confirmed → rank-truncated v2 with matched null, no verdict flips, eleven families (L50). Remaining: run_layer_correlation null symmetry |
| **spec-recovery / void_power math** | **PARTIAL.** Found: bits saturated (near-binary; win rate is the honest statistic); shuffle chance 1/48 = 2.08%. **Remaining:** tie rule `>=`, decoy construction overlap, v4 StratifiedKFold degeneracy |
| **features / BY / units** | **NOT STARTED.** Priority: run_pan_features keys-from-first-problem-only; BY implementation in select.py; units consistency across the three feature libraries |
| **decomposition family** | **NOT STARTED.** Priority: the participation-ratio correction formula (behavioural test on known-rank synthetic data); **the hard-coded VAD table in run_affect_dimensions is UNVERIFIED against real NRC-VAD, a fabrication risk on the replication gate** |
| **core package + locks** | **DONE for locks:** SPEC was deleted 08-07, caught by hash check, restored byte-exact (DEVIATIONS); 5 gate files relocated to docs/gates/, hash-verified. **Remaining:** activations.py token pooling (BOS handling per family, a candidate mechanism for cross-family sign flips); n=4 direction stability |
| **docs vs data** | **PARTIAL** (n=40 label fixed). **Remaining:** systematic sweep of every FINDINGS number against its JSON; orphan sweep; G-identifier collisions (G70/G70b known) |
| **corpora integrity** | **NOT STARTED.** Priority: ladder3 out-of-band tail rung-correlation in absolute words; manifest-vs-disk counts; PAN train/validation leakage (DONE 2026-08-14: L106/L108 — cross-year 16-20%, within-year on easy/medium, leaked pairs score 1.0) |

## The theory glance-clean worklist (priority 1)

**Both directed restructure passes landed 2026-08-09.** THREE_COGNITIVE_LAYERS (four-claim first
screen, address/tracking umbrellas), DECISION_TRACES (Part I model / II ledger / III contested
estimators), THE_TRIPLE_INFERENCE (object table, generative account, four value-carrier accounts,
evidence rows distributed into the sections that interpret them, 08-10), READER_HEURISTICS (loop /
cue families / calibration, dashboard last). Format
spec in `docs/theory/README.md` covers the afterword-before-table rule, the fixed confidence
vocabulary, no notables columns, and voids at one line each at the bottom. **Standing rule: his
blockquotes are untouchable; my prose compresses. Structural changes are proposals in chat first.**

## Queue / infrastructure state

- **The gears (renamed from day/night 2026-08-12).** First gear: `bash run_first_gear.sh`, one
  detached shell (survives sessions), serial, part of the CPU with the GPU mostly the curator's;
  lock in `results/.gear1.lock`, stop with `taskkill //F //T //PID $(sed -n 2p
  results/.gear1.lock)`. Second gear: `bash run_second_gear.sh [hours] [workers]`, sharded,
  as much CPU and GPU as the work can take, loaded about a day deep; lock in
  `results/.gear2.lock` (each refuses while the other's winpid is alive; legacy
  `.loop.lock`/`.overnight.lock` still checked through the transition). Queue has pid lock +
  `--shard/--shards`.
- **Morning state 2026-08-09, revised after the process audit.** The overnight TIMEOs had a deeper
  cause than two-shard contention, because **the 2026-08-07 day loop never died.** The lock files
  record MSYS pids that do not map to Task Manager, so every lock-based kill since 08-07 hit the
  wrong process; the immortal loop (plus both night shards, whose cleanup trap also failed on
  Windows) kept spawning queue lineages, and by morning up to four lineages shared the one card,
  hence the 2-hour timeouts. **All lineages killed via Windows pids (PowerShell); exactly one day
  loop now runs at WINDOWS pid 107224.** Kill loops with `Stop-Process` on Windows pids from
  `Get-CimInstance`, never the lock files' pids (G121 makes the scripts record winpids). Queue
  integrity held throughout; produces-guards kept the lineages off each other's outputs.
  **2026-08-09 evening state.** DAY9 fully burned and written through (L44 to L55). DAY10 loaded
  in program order: the event-recovery harness (validated, L56), the PD-33 decomposition (MAKER,
  L57), and the G128 alignment null (GPU, in flight). Next builds are Phase 1's frontier
  recreations (G136 ArgRewrite baselines, G137 gridworld, G138 impossibility construction), per
  the plan at the head of `TODO.md`.
- **Audit L26 landed (2026-08-08, the conservative fleet):** 15 confirmed defects. Two more criteria
  that could not fail (the no-maker NaN gate, re-adjudicated at luck level overall with the flagship
  concentration sent to G107; the affect shuffle gate below its arithmetic floor). Coherence
  statistic VOID (G105), SHIFTS argmax artifact (withdrawn, re-runs queued), ladder3 decoy
  exhaustion (clean rungs still carry +0.529), argrewrite BY backwards (re-run), affect-dims
  quadruple-broken (G106), atomic cache writes + completeness checks in. **FINDINGS L26 is the
  index; the fleet's full output holds the line-level list for G109/G110.**
- Every stage must carry a `produces` guard. Verify hash locks + read `git status` deletions before
  every commit (CLAUDE.md hard rule, born of the SPEC deletion).

## Open decisions / owed

- **G75 DONE (L23): survives all three ladders −0.42 to −0.52, p ≤ 0.0004; L17 resolved; L2's kills
  reversed under the fair control and relabelled (2026-08-09).**
- The four-file corpus problem (one maker, many kinds): CROSSNEWS = pseudo-documents only;
  Guardian (13 authors) better kind-contrast; CMCC = email the authors (C-32a). The program's G133
  commissioned pilot now leads this thread.
- Interest ratings on his 15 artifacts, owed by him; per the program they inform READER_HEURISTICS
  only, never ground truth (HH-14).
- PAN22 Aston application, his side.
- Rotate the Anthropic API key pasted early in the project, his side, still owed.
