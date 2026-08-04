# Theory — the whole state, compressed

One line per finding. Follow the link only if you need the argument.

---

## The instrument's core

| | claim | status |
|---|---|---|
| art = compressed intent | decisions per artifact, counting automatised ones | source theory |
| appreciation = IRL | reader inverts artifact → maker's reward function | source theory |
| the reading is a tuple | never one number — SPEC §5 | enforced in code |
| **depth = decisions RECOVERABLE** | a joint claim about artifact *and* reader | the goal |

## What the simulation established, and what this project inherited

| | | where |
|---|---|---|
| **E36** | depth moves **method** uptake; provably cannot move **purpose** uptake | method unlock is the primary |
| **N28** | if a measure moves where there is nothing to measure, every number above it is void | **this project has no analogue** → [SIM_REREAD](SIM_REREAD.md) |
| **E37** | the wall is *legible and empty* — non-invertibility, not illegibility | the one finding needing a posterior |
| **E38** | machine-matched reader: 1.000 on machine, 0.280 on human | ceiling on every gate |
| **E40** | optimise a surface cue and it decouples: pay more, get less | third failure mode |
| **E43** | compression removes decisions from the maker's **report**, not the artifact | [SIM_REREAD](SIM_REREAD.md) §4 |
| **E55** | reader-side intent gate cuts damage 23%, costs nothing clean, never reads the label | the successor's shape |
| **MIN** | no finding survives replacing the maker-modelling reader with a surface classifier | v9 ablation |

## What the curator's readings added

| | claim | where |
|---|---|---|
| **anomaly entry** | reading starts at *what demands explanation*, not at the whole artifact | [SUCCESSOR](../SUCCESSOR.md) §2 |
| **bidirectional loop** | purpose→method **and** method→purpose; entry set by partial expertise | [SUCCESSOR](../SUCCESSOR.md) §3 |
| **C-22, corrected** | flattened intent is **share**, not singularity → `purpose_breadth` | [FLATTENED_INTENT](FLATTENED_INTENT.md) |
| **surface ≠ depth** | two decision densities, split by *what the decision targets* | [SURFACE_AND_DEPTH](SURFACE_AND_DEPTH.md) |
| **S-1** | depth is stationary within an artifact; surface is not | untested |
| **persona limit** | what is recoverable is a presented face **and its leaks** | scope limit |

## Affect — the leg that opened up

| | claim | where |
|---|---|---|
| **two layers** | leaked (Panksepp primary) vs emblematic (Barrett tertiary) — **this is the field's reconciliation position** | [AFFECT_ARCHITECTURE](AFFECT_ARCHITECTURE.md) §1 |
| **ANPS dropped LUST** | because a questionnaire only reaches the tertiary layer. Artifacts don't have that limit | §2 |
| **no mapping exists** | primary-process systems → textual signatures: nothing published | [AFFECT_LITERATURE](AFFECT_LITERATURE.md) §1 |
| **unsupervised ≈ 0.4** | LIWC-class r=0.35–0.54; supervised transformers 0.85. Stage E is the former | §3–4 |
| **collapse predicted** | values will merge before they go silent → N-AFF-2 | §4 |
| **function words = leakage** | non-conscious, topic-independent, hard to fake, track *state* | **[LEAKAGE](LEAKAGE.md) §1** |
| **LLM internals ≈ core affect** | 171 causal emotion directions; PCs align to **valence/arousal** | **[LEAKAGE](LEAKAGE.md) §4** |
| **stage E is emblematic-only** | asking for a label returns a content-word judgement, on both outputs | [LEAKAGE](LEAKAGE.md) §1 |

## Options, costed

| | what | cost | gates |
|---|---|---|---|
| **D-0** | do function-word vectors separate by maker state? | **2h GPU** | **all of D** |
| **A** | leaked layer from function-word distributions | hours, no GPU | — |
| **C** | keep stage E, re-scoped as emblematic-only | free, built | — |
| **B** | activation readout for valence/arousal | an afternoon + VRAM | — |
| **D** | inverse planning over artifacts | **2-3 days to runnable** | D-0 |

D-0 came back **inconclusive at 38% power** — see [`../../results/d0/VERDICT.md`](../../results/d0/VERDICT.md).
D-0b is pre-registered with power computed first.

**Six directions, ranked, in [DIRECTIONS](DIRECTIONS.md).** The two strongest read the *reader*
rather than the artifact, and the cheapest (public-domain books) fixes both D-0's sample problem
and A's baseline problem at once. Costing of D: [OPTION_D](OPTION_D.md).

## Open, and blocking

| | |
|---|---|
| **C-14** | grooming corpus never sourced. Successor's required corpus, oldest debt |
| **C-20** | one reader. E10 says reader skill caps extraction; one reader cannot bound their own cap |
| **C-23** | human-shaped maker goals — partly answered by the two-layer model, unbuilt |
| **N28-analogue** | Gate 3 has no no-maker control. Gate 2 ran the nearest thing and it **failed** |
| **A-1** | can a model without interoception predict what affect a human attributes? |

---

## Reading order, if starting cold

1. [SIM_REREAD](SIM_REREAD.md) — what the simulation constrains
2. [SURFACE_AND_DEPTH](SURFACE_AND_DEPTH.md) — the two axes, hard-defined
3. [AFFECT_ARCHITECTURE](AFFECT_ARCHITECTURE.md) — the two layers and why they are the debate
4. [LEAKAGE](LEAKAGE.md) — how to measure the layer that matters
5. [../SUCCESSOR.md](../SUCCESSOR.md) — what gets built

Provenance for every curator contribution: [results/readings/PROVENANCE.md](../../results/readings/PROVENANCE.md)
