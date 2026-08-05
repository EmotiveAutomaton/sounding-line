# TODO — ideas not yet run

**2026-08-05.** Short by design. Ideas here normally get run within a day; anything sitting for more
than a session is either blocked or should be deleted. If an item is blocked, the blocker is named.

Results go in [`FINDINGS.md`](FINDINGS.md).

---

## Harvested from theory — tests for the curator's claims

Each of these is a claim from `docs/theory/CURATOR_GUESSES.md` turned into something runnable.

| | the claim | the test | cost |
|---|---|---|---|
| **E1 · mechanic entry** | You can enter the decode at metaphor, technique **or mechanics**, and any of the three ratchets toward the maker's goal. *"The expert can see the feelings of the novice through the actions they took, because they can disassemble the process."* | **Every edge test so far supplies a goal or a process. None has ever supplied a MECHANIC.** Give the probe sentence-level craft information — cadence, clause habits, punctuation practice — instead of a stated purpose, and measure goal recovery against a control given nothing. If mechanics unlock goal, legibility-first is wrong | ~2 h GPU |
| **E1b · are the layers infinite?** | *"It would have more layers than three... how far can we subdivide them is an interesting question."* And: do the layers map onto goals at all? *"A single layer might have 20 goals in it."* | **Literature first** — empirical aesthetics named the collative variables, so a layers-of-analysis theory plausibly exists and we should not reinvent it. Then: ask the probe to read at N specified depths and test whether recovery is monotone in depth or saturates | search, then ~1 h |
| **E2 · values as constraint** | Values are not a separate factor but **the constraint that every goal is partially satisfied at once** | **Ladder 3 is the first half** (running): 60 simultaneous specifications that must all be honoured. Second half, and it is the sharper one: if values are a stable constraint on the goal mixture, **a maker's pattern of partial satisfaction should be stable across their own works** — testable within-author on the 34-book corpus, which already gives a within-author positive | ~2 h |
| **E3 · interest = unexplained decisions** | Interest comes from decisions you cannot attribute meaning to. Aesthetics is **ordered** unexplained decisions | Two tests. **(a)** Reader-reported interest as an instrument — ask the curator to rate interest per artifact and correlate against every measure we own. Cheap, and it uses the one channel that has outperformed everything. **(b)** Operationalise "ordered but unexplained" as effective complexity and check it is not just entropy | (a) an hour of his time · (b) ~1 h |
| **E4 · polish vs performative polish** | Is there art theory separating aesthetics that *indicate* deeper understanding from aesthetics that merely perform it? | Literature search. His own E3 may already answer it: performative polish would be **ordered without being unexplained** — which is a measurable distinction, not a vibe | search |
| **E5 · stacked motivations** | A machine given many aligned motivations should read as more intentional | **Ladder 3, running now.** 0/2/10/30/60 specifications with length nailed by rejection sampling. Also tests whether the effect *accelerates* at the top, which would be evidence for E2 | running |

## Public corpora — found, and the useful ones are not the obvious ones

**The AI-detection corpora exist in abundance and mostly do not help us.** RAID (6M generations, 11
models, 8 domains), HC3 (37k+37k human/ChatGPT pairs), M4GT-Bench — all public, all licensed for
research, all built for the **human-vs-machine** problem that the literature already solves at
F1 ≈ 0.99. Downloading them to do that again would be the wheel-reinvention `CLAUDE.md` now forbids.

**What we actually need is human text where intent varies and register does not.** Ranked by how
well each matches the design in `docs/design/DWELL_CORPUS.md`:

| | what it is | why it fits | the catch |
|---|---|---|---|
| **1. ArgRewrite v2 / college-essay drafts** | 60 argumentative essays, **paired drafts by the same author**, original vs revised-after-feedback, revisions annotated for purpose and whether they improved quality | **same author, same prompt, same topic — only the intent state differs.** This is construction-controlled *by design*, and it is the public version of the corpus we specified ourselves | n = 60 pairs |
| **2. Wikipedia quality classes** | ~29,794 articles, ~5,000 each in FA / GA / B / C / Start / Stub, **graded by human editors** | **a human ladder.** Format and register held constant by Wikipedia's own conventions, with a human-assigned quality gradient. The closest public thing to what we built synthetically | **length confound is severe** — FA articles dwarf stubs. Worse than our ladder's +0.403. Needs hard length matching |
| **3. RAID** | 6M generations, 11 models, 8 domains, adversarial variants | **external validity for the layer ratio.** Our replicated effect is one model, one format. RAID says whether it is a Qwen artifact | not an intent corpus; a robustness test |
| **4. ScholaWrite** | end-to-end scholarly writing process, annotated | closest thing to observing decisions as they happen | probably too fine-grained to use |
| ~~HC3 / M4~~ | human vs ChatGPT | — | the solved problem. **Skip** |

**Recommended order: 1, then 3, then 2.** ArgRewrite is small but exactly the right shape; RAID is the
cheapest way to find out whether our one replicated effect generalises at all.

## Blocked on a decision from you

| | what | why it is blocked | cost |
|---|---|---|---|
| **the dwell corpus** | one maker, one venue, **two structural forms** — the incident postmortem against the same engineer's weekly notes. T-3 says decision-counting is only well-defined where a maker holds one sub-goal for long stretches | it is a **sourcing** decision, not compute. Spec is written: `docs/design/DWELL_CORPUS.md` | an afternoon of fetching |
| **the measure-evolution loop** | we built a seven-term evaluator and have been feeding it one hand-written candidate at a time. Archive candidates by which controls they survive; let an LLM mutate them | a build decision — it is the only item that changes the *rate* rather than the method. `docs/design/ENGINEERING_LOOP.md` | ~a day |
| **C-20 — a second reader** | even n = 2 on 3–4 artifacts | needs a person | an hour of someone's time |

## Gated — tier C tools, blocked behind the tier A checks

**The gate:** these do not get installed or built until the 342 off-the-shelf features have been run
through the evaluator and either found something or provably failed. They are more expensive and
strictly more speculative than the thing that is already sitting there for free.

| | what | unlocks when |
|---|---|---|
| **OpenEvolve** (AlphaEvolve) | LLM as mutation operator over our measure code | the feature sweep has run **and** the pyribs archive exists. If 342 published features carry nothing, evolving new ones is a much longer shot and we will know the shape of the failure |
| **gplearn `SymbolicTransformer`** | evolves *combinations* of existing features | the feature sweep has run. This is its natural second stage — it needs the 342 as raw material |

## Ready to run, unblocked

**First up — the tier A sweep, which is why the tools were installed:**

| | what | why | cost |
|---|---|---|---|
| **re-audit every length-killed measure for DIRECTION** | **known weakness 3b, and it is the most likely place a real result is buried.** Length turned out to be a *suppressor* on the layer ratio, not a confound — it was working against the effect. Every measure this project killed on "correlates with length" was killed without checking the **sign** of the relationship against the sign of the effect. At minimum: `scale_gain` v1 (+0.877), the ladder void (+0.403), and every VOID verdict | **the method was wrong, not just the measure.** If even one of the ten deaths was a suppression case, it comes back | ~1 h, no GPU |
| **ladder 3 — length held by rejection sampling** | the curator's fix, and it is obviously right: **generate with a hard word band and regenerate anything outside it** (e.g. 1,380–1,420 words). Ladder 1 and ladder 2 both produced rung-vs-length at ~+0.40, so the confound is structural to the design, not bad luck. Rejection sampling drives it to ~0 by construction and removes the need to partial it out at all | it converts our best result from "significant after controlling length" to "significant, no control needed" — a much stronger claim, and it kills the objection before anyone raises it | ~2 h generation |
| **the 342-feature sweep** | extract all features over the ladder, score against rung with **Benjamini-Yekutieli** correction, then put survivors through the full control battery — echo, length, transfer, rung −1 | this is the population fix. **An empty result is a real finding** and a much stronger negative than ten hand-written misses | **running now** |
| **ladder 2 replication** | held-out, n = 100, loci frozen. **Generating now** | known weaknesses 2 and 3 at once | running |
| **cross-validate the layer loci** | Optuna over split points, scored on ladder 2 only | weakness 3 — they were chosen by looking at the answer | ~40 min GPU |

| | what | why | cost |
|---|---|---|---|
| **cross-validate the layer ratio's loci** | the split points (0.07 and 0.76 of depth) were **chosen from a prior result on the same model** and never held out. This is known weakness 3 and it may be manufacturing the p = 0.053 | it attacks our only order-dependent effect at its weakest joint | ~40 min GPU |
| **the stacking test** | combine the surviving weak effects, with the two conditions in FINDINGS: beat the best single component **on held-out data**, and show the errors are not correlated | your idea, and the correlated-error check is what makes it honest | ~1 h |
| **shared-representation control** | the no-maker corpus was generated by the same model family we read with. Regenerate part of it with a different family and re-run | known weakness 6, entirely untested | ~1 h |
| **multiple-comparison audit** | we have never corrected for ~25 tests. Recompute every surviving p under Benjamini–Hochberg and report what survives | known weakness 1. Cheap and it will probably hurt | ~20 min, no GPU |

## Owed, long-standing

| | |
|---|---|
| **C-14** | the grooming corpus, never sourced. Oldest debt — but the dwell corpus is a better-specified version of the same need and should probably replace it |
| **C-19** | do the bounded and free-form probe arms disagree systematically? The gzip accident suggests yes, dramatically |
| **artifacts 6–10, session 02** | yours |

## Deliberately not doing

**More function-word work** — the ceiling is author identification and we are past it.
**Anything new on the Gate 3 corpus** — it has been read too many times to be a test corpus.
**An end-to-end research agent** — its documented failure mode is the one we already have.
