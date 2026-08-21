# This is not data science. What is it, and what tooling actually fits?

**Reusable design principle (2026-08-21).** Wide candidate generation, explicit constraint
evaluation, archive preservation, and avoidance of population-size-one search remain binding
principles. The specific measure-evolution loop is not automatically the current scheduled
build; Phase 2.3's adaptive branch registry is the operative application of the broader search
frame. Scheduled work lives in `TODO.md`.

**2026-08-05**, at the curator's reframe, which corrected a category error I had been making for
three days:

> Data science goes into the Ghost Scale. Over here what we need is more like **engineering loops**.
> Testing for possibilities of things that work. **Creatively exploring a space and trying things new
> to search for solutions to a specific problem that exists in the real world.** You keep thinking
> we're doing data science here, and to an extent we are, but **we're also trying to make something.**

He is right, and the distinction has teeth. The scaffolding I found in the first search —
preregistration templates, research compendia, sanity-check statistics — is all for **establishing
that a claim is true.** None of it helps **find a thing that works.** Those are different activities
with different tooling, and I sent the first set to the simulation
([`FOR_GHOST_SCALE_SIM_3.md`](../sim/FOR_GHOST_SCALE_SIM_3.md)) because that is the repo doing that job.

---

## §1. What kind of problem this actually is

Stated precisely, so the right literature can be found:

> **Search a space of candidate measures — functions from artifact to number — for one that ranks
> intent, under a battery of constraints that most candidates violate.**

That is not hypothesis testing. It is **constrained search over a design space with an expensive
evaluator**. Which is a completely standard problem shape with a mature literature, and it is not
the literature I had been reading.

**And here is what falls out of stating it that way:**

> **We have spent three days building the evaluation function for a search we never ran.**
>
> Length control, echo check, construction control, transfer check, no-maker null, rung −1, the
> positive control — that is a **seven-term fitness function with a validated harness**. It costs
> minutes to run. We have been feeding it **one hand-written candidate at a time**, at roughly three
> candidates a day, and calling each death a finding.

Ten deaths in three days is not bad luck and it is not even bad measures. **It is a search with a
population size of one.**

---

## §2. What the search returned, and the one that fits

### Quality-Diversity / MAP-Elites — the right frame

[MAP-Elites](https://www.emergentmind.com/topics/map-elites-algorithm) and
[novelty search](https://www.emergentmind.com/topics/open-ended-exploration) keep an **archive
indexed by behaviour**, not a single best solution. Each cell holds the best candidate *of that
behavioural type*. The founding argument is that optimising a single objective gets stuck, and that
**collecting diverse behaviours finds better solutions than pursuing the objective directly.**

**Why this is the fit, and it is almost embarrassing how well it maps:**

    fitness             rho against the ladder rungs
    behaviour space     WHICH CONTROLS THE CANDIDATE SURVIVES

The behaviour descriptors are already built. A candidate measure's coordinates are literally
`(needs order?, survives length?, free of prompt echo?, transfers to humans?, flat on no-maker?)` —
a 5-bit archive, 32 cells. Every one of our ten dead measures **occupies a cell**, and right now we
are throwing that information away instead of filing it.

> **The ten deaths are not ten failures. They are ten archive entries, and we deleted them.**

What an archive would answer that a sequence of deaths cannot: *which regions of measure-space are
occupiable at all?* If no candidate ever lands in `(needs order, length-clean, echo-clean, transfers)`
after a thousand tries, **that is a far stronger negative result than ten hand-written misses**, and
it is the kind of negative result worth publishing. If something does land there, we are done.

### LLM-driven evolutionary program search — the right machinery

[FunSearch](https://www.emergentmind.com/topics/funsearch-algorithm) introduced the LLM as a
**mutation operator** over program code, with a fixed evaluator scoring each child. AlphaEvolve
generalised it to whole codebases. Open implementations exist —
[OpenEvolve](https://github.com/jamesahou/openevolve),
[CodeEvolve](https://arxiv.org/html/2510.14150v1), and 2026's
[EvoLattice](https://arxiv.org/html/2512.13857), which combines the two ideas above by evolving over a
**quality-diversity graph**.

The loop: sample a parent from the archive → LLM writes a mutated child → evaluate → file it by
behaviour. An **island model** keeps sub-populations separate with occasional migration, which is how
these systems avoid the convergence-to-one-idea failure.

**Our version needs almost nothing new.** `soundingline/measures/` is the genome. `runners/` is the
evaluator. The controls are the fitness. The only missing piece is the loop and the archive.

### What does *not* fit

| | why not |
|---|---|
| [Active learning / DoE](https://www.nature.com/articles/s41524-019-0153-8) | for choosing which **experiment** to run next when experiments are expensive. Ours are minutes. Not the bottleneck |
| [Symbolic regression](https://arxiv.org/html/2605.29184v1) | fits an **equation to data**. We do not have the target variable — that is the entire problem |
| End-to-end research agents | optimise for **paper generation**; documented failure mode is ours already |

---

## §3. The proposal, concretely

**A measure-evolution loop.** Roughly a day to build, and it reuses everything.

| | |
|---|---|
| **genome** | a Python function `measure(text) -> float`, written by an LLM, in a sandbox with no I/O |
| **fitness** | `|rho|` against ladder rung, penalised by the length correlation |
| **behaviour** | the 5-bit control vector, giving a 32-cell archive |
| **seeds** | all ten dead measures, filed in their cells — they are the initial population, not garbage |
| **held-out** | **half the ladder is never scored during the search.** Non-negotiable; 50 artifacts will otherwise be memorised |
| **the stop** | a candidate in the `(needs order, length-clean, echo-clean, transfers)` cell |

**The honest risks, before anything is built:**

1. **Overfitting to 50 machine-written artifacts.** The ladder is small and entirely synthetic. A
   held-out split is mandatory, and even then a win on the ladder is a hypothesis about human text,
   not a result on it. This is the same wall §6 of the LEDGER names.
2. **Reward hacking.** A search told to maximise rho against rung will find the degenerate solution —
   most obviously, anything correlated with output length, which already tracks rung at +0.403. The
   length penalty must be in the fitness, not in a post-hoc check.
3. **It cannot invent a corpus.** If the answer is that no artifact-side measure works without a
   controlled human corpus, a search will confirm that faster and more convincingly. **That is still
   worth having**, and it is a better negative than ten hand-written ones.

---

## §4. What changes immediately, with or without the loop

Three things, and none needs new machinery:

1. **Stop deleting dead measures. File them.** Every death gets its control vector recorded. That is
   the archive, and it costs a table.
2. **Widen before narrowing.** The named agent pathology is *"adopted less ambitious hypotheses,
   producing extremely thorough negative findings rather than new ideas."* Every challenge here has
   been answered by adding a control and narrowing the claim. **The correct response to a dead measure
   is ten new candidates, not an eleventh control.** We now have more controls than measures, which is
   diagnostic on its own.
3. **Batch candidates.** The evaluator runs in minutes. There is no reason to write one measure, run
   it, write a verdict, and repeat. Twenty at once costs barely more than one.

> The instrument has not moved in three days. **The method got better every single day.** That ratio
> is the problem this file exists to fix.

---

## Sources

[MAP-Elites](https://www.emergentmind.com/topics/map-elites-algorithm) ·
[Open-ended exploration](https://www.emergentmind.com/topics/open-ended-exploration) ·
[FunSearch](https://www.emergentmind.com/topics/funsearch-algorithm) ·
[OpenEvolve](https://github.com/jamesahou/openevolve) ·
[CodeEvolve](https://arxiv.org/html/2510.14150v1) ·
[EvoLattice](https://arxiv.org/html/2512.13857) ·
[QD for LLM safety vulnerabilities](https://arxiv.org/html/2606.00801) ·
[QD limitations](https://arxiv.org/pdf/2407.17515) ·
[Can AI agents conduct open-ended AI research?](https://arxiv.org/pdf/2607.27191) ·
[Active learning in materials science](https://www.nature.com/articles/s41524-019-0153-8) ·
[Influence-guided symbolic regression](https://arxiv.org/html/2605.29184v1)
