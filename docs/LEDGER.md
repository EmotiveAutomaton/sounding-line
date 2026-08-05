# The ledger — every test run, and what each one implies

**Current to 2026-08-05.** The single registry. If a test was run, it is here with a verdict and a
consequence. Where a verdict has been revised, both the old and new appear — **nothing is quietly
overwritten**, because the revision history is most of what has been learned.

Narrative versions live in `TEST_RESULT_BANK_1.md` and `TODAY_IN_PLAIN_ENGLISH.md`. **This file is
the list.** Methodology for the controls: `theory/CONTROLS.md`.

---

## §1. The scoreboard

| # | test | asked | verdict | consequence |
|---|---|---|---|---|
| **G0** | Gate 0 | does the fetcher get clean text? | **PASS** | corpus pipeline trusted |
| **G1** | Gate 1 | does the probe return structured readings? | **PASS** | tuple format enforced |
| **G2** | Gate 2 | does the reading separate human from generated? | **FAIL** | first N28-analogue failure |
| **G3** | Gate 3 | method unlock, A vs B halves | **UNINTERPRETABLE** | not negative — N13 stability null failed, sd 0.808 within vs 0.087 between |
| **D-0** | function words vs maker state | do FW vectors separate states? | **INCONCLUSIVE** | 38% power, caught post-hoc |
| **D-0b** | D-0 with power computed first | same, powered | **FAIL** | the channel is there; the state is not |
| **G-1** | books, author ID | can FW identify authors? | **PASS 7.6×** | the channel works |
| **G-2** | books, within-author works | more than identity? | **PASS 2.05×** | capacity for state exists |
| **B** | affect directions in a reader | are they real? not lexical? | **PASS 4× chance** | bag-of-words = exactly chance. **Bimodal across depth** |
| **W-1** | the wall as displacement | does a reader move further for a human maker? | **FAIL** | −0.0049, p=0.53. Clean: no length confound |
| **W-2** | wall, spread | | **UNINFORMATIVE** | n = 3 |
| **R-1** | refusal, 5 components | does a reader refuse differently? | **UNINFORMATIVE** | pass condition had a 50% FP rate. Not banked |
| **C-N28** | no-maker controls | does `scale_gain` move where nothing is? | **RETRACTION** | ordering was perfect, then died to length + shuffle |
| **LAD** | the intent ladder | monotone over 5 rungs of specified intent | **FAIL** | VOID on length (rho +0.403 vs 0.400 threshold) **and** no measure ranked rungs |
| **LR-1** | layer ratio, thirds | low/high-order affect ratio | weak | thirds average the dead middle into both terms |
| **LR-2** | layer ratio, loci | same, split at validated loci | large gap | human 0.697 vs machine 1.055 |
| **LR-3** | layer ratio, controls | is the gap real? | **NOT A DISCRIMINATOR** | **reason revised — see §4** |
| **DIV** | `purpose_breadth` | does it measure motivational variety? | **DEAD** | killed by sim T-2, not by us |
| **ACC** | the gzip accident | | recorded | bounded arm refused all 5; **free-form returned 5 confident readings at max depth** on 44.5% garbage |

---

## §2. The dead, grouped by cause

**Ten measures.** The grouping is the finding — they did not fail ten different ways.

### Killed by length (3)

| | |
|---|---|
| `density.scale_gain`, first form | rho = **+0.877** against word count. It was measuring how long the text was |
| the intent ladder | rho = **+0.403** against output length, threshold 0.400. Failed by a hair and the hair counts |
| several early Gate 2 variants | never separately written up |

### Killed by vocabulary / register (4)

| | |
|---|---|
| `density.scale_gain`, length-controlled | became **type-token ratio**, rho = **−0.879**, survived shuffling |
| the `rich` vs `thin` ordering | perfect theory-shaped ordering, then died to the same controls |
| function-word rates, individually | each is a univariate vocabulary statistic |
| layer ratio, human-vs-machine gap | **C3 register control**: commercial copy sits 26% of the way from essays to machine, p = 0.0033 |

### Killed by a scale or instrument mismatch (2)

| | |
|---|---|
| document-level activation reading | directions fitted on 12-word sentences, applied to 4,000-char documents |
| `separability()` | univariate, averaged over categories — said "no signal" on **author ID**, the most established result in stylometry. Replaced by `delta_classify()` |

### Killed by the simulation, with ground truth (1)

| | |
|---|---|
| `purpose_breadth` | **T-2**: confounded with difficulty. At matched difficulty, excess breadth from diversity = **−0.013 to −0.025**, i.e. zero. S-2's validation retracted separately — its emitter never wired up |

### Never alive (2)

Gate 3's method unlock (a ratio of counts with a near-zero denominator — sim S-1: reads **17.65**
where truth is 0) and the refusal battery (uninformative threshold).

---

## §3. What is still standing

Four became two and a half in one day.

| | status | ceiling |
|---|---|---|
| **function words** (`delta_classify`) | **alive** | author identification. 7.6× on identity, 2.05× within-author. Well-established; we are not past the field |
| **affect directions** (`results/b`) | **alive** | 4× chance on held-out sentences, **not lexical**, bimodal across depth. Real, small, unexploited |
| **layer ratio** | **reopened** | was called dead on shuffle evidence it was not entitled to. Not a human/machine discriminator (C3), but its status as a measure is **unresolved** — `theory/CONTROLS.md` §3 |
| ~~`purpose_breadth`~~ | **dead** 2026-08-05 | difficulty statistic |
| **the five controls** | alive | shuffle, length, register, no-maker, and now rung −1 |

---

## §4. Revisions and retractions

Kept in full. This is the most load-bearing section in the file.

| what | was | is | why |
|---|---|---|---|
| **Gate 3** | FAIL | **UNINTERPRETABLE** | N13 failed; the card says the stability null outranks the p-value. Sim S-1 confirmed the statistic independently |
| **D-0** | FAIL | **INCONCLUSIVE** | post-hoc power simulation: 38%. The simulation touched no data |
| **`separability()`** | trusted since D-0 | **wrong** | understated a known-good signal to absent. Every result using it was re-derived |
| **`scale_gain`** | the primary measure | **disqualified in its own header** | TTR |
| **layer ratio** | "the gap is vocabulary, 121% shuffle survival" | **"not a human/machine discriminator, on register grounds"** | the shuffle test is invalid for model-internal measures — it moved **both** arms up ~14%, a common-mode shift, not an ablation. `theory/CONTROLS.md` §3 |
| **sim S-2** | `purpose_breadth` validated at matched density | **retracted** | the emitter ignored `artifact.goal`; feature streams bit-identical with the mixture off |
| **sim S-3** | shield amplification: +0.125 detectability | **+0.046** | threshold was fitted per-cell on labelled test data. Effect survives at ⅓ size |
| **the triangle** | three mutually bootstrapping vertices | **a directed flow, source → sink, additive** | T-1: three of six edges exactly zero; superadditive excesses mixed-sign and within noise |

---

## §5. The controls, and their kill counts

Full doctrine in `theory/CONTROLS.md`. Ranked by what they license, not by how often they fire.

| level | control | kills | notes |
|---|---|---|---|
| 1 | **construction** — hold register/topic/format fixed by building it that way | ladder, C3 | **strongest.** Removes the confound rather than subtracting it |
| 2 | **matched comparison** — within-author, within-maker | G-2 | matching is never perfect |
| 3 | **null population** — N28 / no-maker | `scale_gain` ordering | catches measures that move on nothing |
| 4 | **ceiling population** — rung −1, shuffled text on the ladder | *none yet — new* | catches measures that **peak** on nothing |
| 5 | **ablation** — the shuffle test | 6 | **valid for text statistics, invalid for model readouts** |
| — | **length** | 3 | run before every verdict, no exceptions |
| — | **power, computed first** | D-0 | added after D-0 ran at 38% |

**Rung −1 does not exist yet and should.** Put shuffled text on the ladder below rung 0. If a measure
scores word salad above the most-specified rung, it is reading unpredictability and is dead whatever
its rho was. Cheap: the shuffled texts are already generated.

---

## §6. The simulation ledger

Two batches. Ground truth is why these are worth more per unit of compute than anything run here.

| | asked | result |
|---|---|---|
| **S-1** | is the unlock statistic sound? | **broken.** 17.65 where truth is 0; r = 0.086 with the graded measure; undefined in 378–467 of 467 |
| **S-2** | `purpose_breadth` at matched density | **RETRACTED** — emitter never wired |
| **S-3** | is the leak readable? | 0.899. Shield amplification **increases** detectability — **revised to ⅓ size by T-4** |
| **S-4/5** | does stage reorder change the answer? | **0.000**. It is a ~5% cost win, nothing more |
| **S-6** | surface decay | practised surface decays **6.5× faster**; synthetic surface is **flat** |
| **T-1** | is the triangle real / symmetric? | **not a triangle.** process→depth +0.840, depth→process +0.356, **three edges exactly 0**. Goal at ceiling (1.000). Additive, not superadditive. Values vertex **does not exist** — H(values\|goal) = 0 |
| **T-2** | goal diversity vs automaticity | **confounded with difficulty.** Kills `purpose_breadth` |
| **T-3** | is a decision count ever well-defined? | **YES, in a regime** — long mode dwell. Dwell moves concentration **2×** what length does |
| **T-4** | does divergence survive an uncertain reader? | **yes** — survives 50% channel swap, wrong cardinality, prior noise to 0.8. **Fails on partial (25%) concealment** |
| **T-5** | is process a better detector than goal? | **tie** (median +0.015 / −0.002). T-1's asymmetry has **no instrument consequence** |

**Curator predictions checked against T-1:** goal easiest to recover — **held** (at ceiling).
Process most useful when supplied — **held** (the only two live edges). No symmetry — **held**.
T-3 negative — **wrong**, it came back positive with a regime.

---

## §7. What the pattern says

Six statements the ledger supports, in descending confidence.

1. **Every measure that reads the text has died to length, register, or vocabulary.** Ten for ten.
   This is no longer a run of bad luck; it is the shape of the problem.

2. **The only signals that have ever survived are read out of the *reader*, not the artifact** —
   function-word geometry and affect directions. Both are small. Both are real.

3. **Counting is the recurring error.** Gate 3's unlock, the refusal battery, decision density — all
   counts, all failed, and S-1 showed why with ground truth: a count over a diffuse posterior has an
   undefined denominator. T-3 then found the exception, which is the useful part.

4. **Controls by construction have never been wrong; controls by ablation have been wrong twice.**
   The ladder and C3 agree with everything. The shuffle test over-fired on word choice and then gave
   an invalid verdict on a model-internal measure.

5. **The simulation is worth more per hour than the GPU here.** It killed `purpose_breadth`,
   retracted its own S-2, found the fitted-threshold flaw in S-3, and talked us out of rebuilding the
   probe around process. **None of that was findable on real text**, because none of it has ground
   truth.

6. **What is missing is a corpus, not a measure.** Everything that works, works when register, topic,
   format and maker are held fixed by construction. There is no such corpus of *human* artifacts with
   varying maker state. **That is now the binding constraint** — and T-3 has specified one shape it
   should have: artifacts whose makers hold a single sub-goal for long stretches.

---

## §8. Owed

| | |
|---|---|
| **C-14** | grooming corpus — oldest debt, never sourced |
| **C-19** | do the bounded and free-form arms disagree, systematically? |
| **C-20** | a second reader. One reader cannot bound their own cap (E10) |
| **rung −1** | the ceiling control, §5 — cheap, undone |
| **sentence-shuffle sweep** | replace the binary shuffle test with a granularity curve |
| **the dwell corpus** | T-3's regime: sustained single-purpose artifacts |
| **artifacts 6–10, session 02** | curator-side |
