# Why Gate 2 failed: two findings the simulation already had, and I built against neither

Not a sample-size problem. Not a corpus problem. **The instrument is pointed at the wrong quantity
and is built on a reader the prior work predicted would fail on exactly this material.** Both were
established in the Ghost Scale Simulation, both are in `FINDINGS.md`, and I read that file before
writing a line of code.

---

## §1. E38 — the probe is a machine-matched reader, and that is a crossover

`docs/versions/v06-code-against-equation/RESULTS.md`, E38, measured:

| reader | content | goal accuracy |
|---|---|---|
| human-matched | human | **1.000** |
| human-matched | machine | 0.320 |
| **machine-matched** | **human** | **0.280** |
| **machine-matched** | **machine** | **1.000** |

> **Outcome: EXPERTISE_SUBSTITUTES.** The machine-matched reader gains 0.680 on machine content
> and gives up 0.720 on human content.

**Sounding Line's probe is a language model.** Its expectations *are* the machine's. It is the
bottom-left cell of that table by construction.

Gate 2 measured the same thing on real text:

| artifact | shape | purpose agreement |
|---|---|---|
| Eurogamer build guide | formulaic | **1.00** |
| Glad brand page | formulaic | **1.00** |
| plumber service-area template | formulaic | 0.67 |
| LocalThunk, building his own game | idiosyncratic human | **0.33** |
| RecipeTin Eats | idiosyncratic human | 0.67 |

The probe reads machine-shaped work perfectly and collapses on genuine human work. That is E38's
0.280-versus-1.000, reproduced, on a corpus the simulation never saw.

**This is not a measurement bug. It is a documented property of the reader I chose**, and the
simulation calls it "a crossover, not an upgrade."

---

## §2. E36 — purpose is the wrong quantity, and the simulation says so in as many words

E36 is V6's central finding, and it is about exactly this mistake:

> **Every measure of what a reader takes on, in every version of this project, has scored how much
> of the maker's PURPOSE it got.** Depth is built so the purpose is equally readable however deep
> the work is, so that measure could not move with depth whatever was true. This scores what the
> reader got of the maker's **METHOD**, which the reader has been quietly tracking all along and
> nobody ever read out.
>
> On the maker's method, depth moves uptake: **0.179 [0.099, 0.267]**. On the maker's purpose,
> measured on the same cells, it does not: **−0.028 [−0.116, 0.058]**.
>
> **The experiment was not wrong; it was pointed at the wrong quantity.**

Now look at what Gate 2 scored:

| criterion | quantity measured |
|---|---|
| F1.2 | **purpose** agreement |
| F2.1 | tuple, whose primary components are **purpose** agreement and audience |
| the ablation pilot's headline | **purpose** agreement |
| `Convergence.purpose_agreement` | **purpose** |

**Every discriminator I built is a purpose measure.** The simulation spent a whole version
discovering that purpose is the one channel that provably cannot move with intent density, and I
built the instrument on it anyway.

The spec even records the correct version. SPEC §3 cites E36 as *"pinning what someone was for
roughly doubles how much of their method you recover — intent is the key; the method is what it
opens."* I implemented the key and never measured what it opened.

---

## §3. What should be measured instead, and it is computable from data already collected

E36's temporal result is the one to build on:

> Within a single reading, process recovery before the goal settles is 0.050 and after it is
> **0.130** — a gain of 0.080, interval [0.041, 0.122], over 102 readings:
> *RESOLVING_THE_GOAL_UNLOCKS_THE_PROCESS*.

That is a **within-reading, within-artifact** measure. It needs no cross-sample agreement, which
is what E38 poisons — so it partially routes around the reader problem instead of fighting it.

**The loop already records it.** Every `LoopRun` stores decisions recovered per iteration:

```
item_A  [0, 2, 2, 5, 2]      item_B  [0, 2, 4, 2, 2]      item_C  [0, 1, 1, 1]
```

The proposed measure — **method unlock**: decisions recovered *after* the purpose posterior
settles, against decisions recovered *before* it. E36 predicts this rises with intent density and,
unlike purpose agreement, is not constructed flat.

Two further consequences fall out of the same finding:

- **`EXTRACTION_IS_SCALE_INVARIANT`** — recovery on a quarter-length window scored 0.415 against
  0.411 on the whole artifact. So chunking is cheap and legitimate, which matters for C-9's
  register-gradient hypothesis and for cost at scale.
- **The between-reader form of E36 FAILED in the simulation too** (0.047 against a required 0.15).
  Cross-sample agreement was the wrong shape there as well. I reproduced the simulation's own
  discarded criterion without noticing.

---

## §4. So: was it sample size, corpus, or mechanism?

**Mechanism, on both counts, and the corpus is the least of it.**

- **Not sample size.** F1.2 reversed by 0.14 with the wrong sign; more artifacts would sharpen a
  wrong-signed effect, not fix it.
- **Not the corpus.** The robots.txt losses biased row 3 toward the *less* commercial end, which
  should have made F1 *easier*, and it still failed. Losing MMOExp hurt, but the artifacts that
  did land already show the pattern cleanly.
- **The mechanism, twice over:** a reader the prior work says reads human work at 0.280, scored on
  a quantity the prior work says is constructed flat.

---

## §5. Recommendation on the API arm

**Do not spend it re-running the failed comparison.** Under E38 a larger model is still a
machine-matched reader, and the most likely outcome is a slightly better version of the same
failure — which costs money to learn nothing.

**Spend it, if at all, on the new measure**, after the local arm shows whether method-unlock
separates anything. The order that respects both the evidence and the budget:

1. **Implement method-unlock** from the trajectory data. Free — the data exists.
2. **Re-score Gate 2's existing readings** where trajectories were captured, and **re-run Gate 2
   locally** to capture them corpus-wide. Free but slow.
3. **If method-unlock separates the rows locally, run the API arm once** as the pre-registered
   replication. If it does not separate them locally, the API arm will not save it and the honest
   next question is §6's.

---

## §6. The question this leaves, stated plainly

If method recovery also fails to separate real makers from filler, then the remaining candidate is
the one that matters: **that recoverable intent, as this project defines it, is not more present
in genuine human work than in competent commercial work** — and that §1's reframe is wrong in a
way no measure fixes.

That is a real possibility and it should not be argued away. But it has **not** been tested yet,
because everything tested so far was pointed at purpose, and the simulation established before
this project began that purpose is the channel where the effect provably cannot appear.

**The theory has not failed. It has not yet been given a fair test.**
