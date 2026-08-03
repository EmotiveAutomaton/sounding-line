# The boundedness ablation — pilot

**The first evidence in this project that boundedness buys anything.** It points the way SPEC §2
predicts, on all three of the predictions written before the numbers were read.

**It is a pilot and not a claim.** Three artifacts, k=3, local arm, all three artifacts written by
me. Direction, not magnitude. Gate 3 proper needs the corpus and the API arm, under claim-gate
discipline (`docs/GATES.md` §2).

Run 2026-08-03, `runners/compare_arms.py`, from `results/readings/readings_local.json`.

---

## §1. Result

| item | arm | purpose agreement | confident disagreement | mean decisions | **named-alternative rate** |
|---|---|---|---|---|---|
| A | bounded | 0.67 | 0.11 | 2.0 | **0.67** |
| A | free-form | **0.33** | **0.41** | 2.7 | **0.00** |
| B | bounded | 1.00 | 0.00 | 2.0 | **0.67** |
| B | free-form | 1.00 | 0.00 | 3.0 | 0.33 |
| C | bounded | 1.00 | 0.00 | 3.0 | **0.67** |
| C | free-form | **0.67** | **0.18** | 4.7 | **0.00** |
| | | | | | |
| **mean** | **bounded** | **0.89** | **0.04** | 2.3 | **0.67** |
| **mean** | **free-form** | **0.67** | **0.20** | **3.4** | **0.11** |

---

## §2. The three predictions

Written into `compare_arms.py` before the numbers were looked at.

**P1 — free-form shows lower agreement across independent samples. CONFIRMED.**
0.89 bounded against 0.67 free-form. On item A the free-form arm returned three different
purposes in three runs — `persuade`, `inform`, `coordinate` — while the bounded arm returned the
same purpose twice.

**Confident disagreement is 5× higher unbounded: 0.20 against 0.04.** That quantity is the E2
signature made numerical — high self-reported confidence combined with low mutual agreement — and
it is the simulation's most robust inherited finding. This is the first time it has been measured
on real artifacts rather than simulated ones, and boundedness suppresses it.

**P3 — free-form does not find *fewer* decisions. CONFIRMED, and it is the important one.**
The free-form arm finds **more**: 3.4 against 2.3. So the effect is not that boundedness produces
more output. It is that unbounded output is **more abundant and less reproducible** — which is
precisely SPEC §2's claim that an unbounded reader "will always produce a coherent answer, for
anything," and that this is "confident fabrication with good grammar" rather than measurement.

Had bounded simply found more decisions with better agreement, the honest reading would have been
that the bounded prompt is just a better prompt. The volume going the other way is what makes the
agreement difference mean something.

---

## §3. The unpredicted finding, and it is the sharpest

**Named-alternative rate: bounded 0.67, free-form 0.11.** On two of three artifacts the free-form
arm scored **zero** — not one of the "decisions" it reported named a road not taken.

Under SPEC §4 those are not decisions. They are properties of the artifact:

> A DECISION requires a visible alternative that was not taken. If you cannot name what else the
> maker could have done there, it is not a decision — it is a property of the artifact.

So the free-form arm reports **more items, of which fewer are decisions at all**. It is
enumerating features and calling them choices. The bounded arm's stage-B counterfactual
enumeration — list the moves available *before* reading what this maker did — is what forces the
road-not-taken to exist, and it is the single mechanism most clearly doing work.

This was not predicted. It emerged from a measure (`support`) that was itself rebuilt two days
ago after being diagnosed as a keyword detector, which is worth noting in both directions: the
measure has a short and troubled history, and this is the first thing it has said that the
architecture did not already assume.

---

## §4. What may and may not be claimed

**May:** on this pilot, the bounded arm produced more reproducible readings, with a five-fold
lower E2 signature, and a six-fold higher rate of recovered decisions that are decisions rather
than descriptions — while reporting *fewer* items overall.

**May not:**
- that boundedness works. Three artifacts, k=3, one model, one author.
- anything about magnitude. The numbers are small-sample and the artifacts are not independent —
  A and C share a brief.
- that this settles Gate 3. Gate 3 is a **claim gate** and must be pre-registered and run on the
  corpus without iteration. This run informed no criterion and changed no measure; it is
  reported as instrument evidence.

**The honest caveat that cuts hardest:** all three artifacts are machine-written, by me, and two
of them share a brief. A free-form reader disagreeing with itself about *my* prose is weaker
evidence than it looks. The corpus artifacts — real human work with real makers — are where this
has to be repeated.

---

## §5. Consequence

A-2's commitment is now met: the free-form arm runs, and it has been compared. The project has,
for the first time, evidence bearing on the claim Gate 0 identified as load-bearing — that
bounded-family inference is doing something free-form attribution does not.

It points the right way. It is three artifacts.
