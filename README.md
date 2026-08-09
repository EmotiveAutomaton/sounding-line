<p align="center">
  <img src="docs/assets/sounding-line.jpg" alt="A brass plumb bob and coiled line resting on an open bathymetric chart" width="100%">
</p>

<div align="center">
  <sub>◯ <a href="https://github.com/EmotiveAutomaton/ghost-scale-sim">Ghost text</a> — all of it.</sub>
</div>

# Sounding Line

**An instrument for reading intent out of real artifacts.**

A sounding line is a weighted cord lowered into water to find the bottom — the oldest depth
instrument there is. It returns a reading when there *is* a bottom, and runs out when there isn't.
"To sound someone out" already means to probe for their intentions.

> ### ⚠ Exploratory
>
> This is an **active research project under rapid development**, not a tool. Findings are
> provisional, measures are being rebuilt as they fail, and the record deliberately keeps the
> failures visible. Nothing here should be used to make a judgement about a real person's work.
>
> It is being pursued seriously and quickly. It is not finished, and several of its central
> measures have already been shown not to do what they were built to do.

---

## What it measures

**Depth: how many of a maker's decisions are recoverable from what they made.**

That is the whole thing. Everything below is in service of it.

It is **not an AI detector.** It never says *a machine wrote this*. It says *this much was decided
here, and this is the evidence*. That is a claim about the artifact, the maker can rebut it, and
being wrong about it is an ordinary disagreement rather than an accusation.

Which also means **firing on hurried human work is the measurement working.** Fast human work does
contain fewer recoverable decisions. Reframed as decision density rather than authorship, the
"false positive" stops being false.

And it means **you cannot evade it by writing more like a human**, because writing more like a
human — making more decisions, for more reasons — is the thing being measured.

---

## Why the obvious build fails

Point a language model at a page and ask *why was this made*. It **does not work**, and the reason
is the design.

Machine content is not goal-*empty*. It is goal-**foreign**: a real process, expressed in a
vocabulary the reader has no entry for. An unbounded reader asked an open question **will always
produce a coherent answer** — for anything, including sludge. Free-form intent attribution is not a
measurement. It is confident fabrication with good grammar.

What makes a human maker recoverable is that **the human solution space is bounded** — by
architecture, by embodiment, by metabolic cost, by having to choose one thing because doing both
was too expensive. The wall in front of generated content is not an absent maker. It is
**non-invertibility**: many maker-states mapping to one surface, where the surface is perfectly
familiar and the state behind it cannot be recovered. *Legible and empty.*

**So the probe imposes a bounded, human-shaped hypothesis family and measures fit inside it.** The
boundedness is the mechanism, not a limitation.

---

## Where it actually stands

**2026-08-07. Roughly forty tests across four gates, three simulation batches and eleven model
families.** The honest version, because the honest version is the point.

### What has survived its controls

| | |
|---|---|
| **The flagship, under a fair induction control** | The old induction control's regressors *contained the dose it claimed to remove* (L22). With the dose arithmetically removed instead, **the effect survives on all three independently generated corpora and gets stronger** — and three published linguistic features it had killed revive the same way, nine of nine tests (L23, L24) |
| **The per-layer intent correlation** | Correlation between how much intent a prompt specified and the reader's affective signal, computed layer by layer. **25 runs across 11 model families, 18 survive.** The no-maker control, re-adjudicated after an audit found its verdict gate could not fail (L26): **false fires at the rate luck supplies overall — but concentrated in the flagship family, where layer 21 fires on all three ladders and on maker-less text.** A permutation null decides it |
| **Specification recovery** | How much of a prompt's specification can be recovered from the artifact, against 48 topic-matched decoys. **Win rate 52.5% → 66.3% → 91.7% as specifications go from ten to sixty** — it scales with the strength of the manipulation |
| **Function words against specified state** | Closed-class word rates classify which rung an artifact came from at **1.6× to 3.0× chance**, scaling the same way. **No model involved.** Two independent channels agreeing on the same scaling is worth more than either |
| **Affect directions are real** | Four times chance on held-out sentences, while a word-counting model scored **exactly** chance |
| **Authorship as a calibration** | 7.6× chance, and identical at all four scrambling granularities — which proves the scrambling code is correct before any real number is computed |

### What died, and why it is the useful half

**Every measure that reads the *artifact* has died — to length, then register, then vocabulary, in
that order.** **Dated correction (2026-08-08): the final three kills were the broken control's, not
the features' — all three revive under the fair control, on all three ladders (L24). The deaths to
length and register stand.** Decision density was word count, then vocabulary diversity. Of 342 published linguistic
features, **61 of the 81 that replicated were machine-detectors**; the three survivors died to a test
of whether the prompt *caused* a feature without *containing* it.

**The depth profile across layers is architectural.** Identical between intent-laden text and text
with no maker at all, in **every one of nine model families**, with the peak landing anywhere from
layer 2 to layer 47. **The bimodal profile this project once reported was a two-model artifact.**

**Gate 3, the primary for a month, is void twice over** — its statistic reads a large positive where
the truth is zero, and 76 features separate its two halves, so almost any measure would.

### Six criteria that could not do their own job

**This is the recurring failure and it is worth more than any single result.**

    the unlock statistic          read a large positive where the ground truth was zero
    parallel analysis             returned 335 components on pure Gaussian noise
    the ladder's length ceiling   voided the founding question on a rank correlation over a
                                  4% length difference
    the induction control         its regressors contained the dose -- what it "controlled
                                  away" was the treatment itself
    the no-maker verdict gate     required abs(nan) > 0.2 -- DEAD was the only reachable
                                  verdict, under any data whatsoever (audit L26)
    the affect shuffle gate       its pass threshold sat below the statistic's arithmetic
                                  floor in every recorded run (audit L26)

**A standing rule now covers it: run every measure on data whose answer you already know, before
running it on data whose answer you don't.** Noise in, zero out.

### The binding constraint

It is no longer a measure. **Three separate hypotheses are blocked on the same corpus: one maker
across different KINDS of artifact** — different register, audience and purpose, not different
topics. Depth as a relation to a domain needs it; the polish-variation claim needs it; values needing
many works needs it.

**It turns out to be genuinely rare.** The cross-genre authorship literature describes its own data as
*"scarce and very limited in size"*, and most corpora carrying a "cross-domain" label are cross-*topic*
underneath — PAN's cross-domain tasks are all fan fiction, varying fandom rather than kind.

---

## What is being built now

**One human read fifteen artifacts aloud, blind, in plain text.** That produced more usable design
than three gates: reading starts at **an anomaly** rather than at the whole artifact, the loop runs
**both ways**, and *"depth is a property of the writer with respect to the domain"* — which makes
depth a **relation** rather than an attribute, and is why the missing corpus is fatal rather than
inconvenient. **A relation cannot be measured by varying one side.**

**Those readings are the richest hypothesis source the project has** — not a validated instrument,
because no independent ground truth has ever scored them — which means the most generative evidence
in the project has a sample size of one reader, and is treated accordingly.

### The proximal goals

Because depth is a relation, the near-term work is scoped by what can be measured *without* the
missing corpus while the corpus is pursued:

1. **Run the definitional test.** Depth-side quantities should hold still across an artifact's
   positions while polish-side quantities move; if both move equally the polish/depth split is
   wrong by its own words. Built, currently re-running after a false start its own sample count
   caught.
2. **Cross the causal gate.** Everything decodable so far could be a correlate; patching and
   erasing the recovered structure while measuring what changes is the decisive test the
   architecture claims wait on.
3. **Price the third target.** Value recovery works as *method* in the parent simulation —
   profiles converge across artifacts, an absent drive reads under commission. What it needs on
   real text is exactly the corpus problem above, so corpus sourcing is a research task, not
   logistics.
4. **Keep killing our own instruments first.** The audit record below is the point, not the
   embarrassment.

### The theory, in five files

[`docs/theory/`](docs/theory/) is the hypothesis store — every claim, its status, and what would test
it. **More than 130 numbered hypotheses**, each carrying whether it was checked on real text, in the
parent simulation, or against published work. Each file owns one question and they do not overlap:

| | |
|---|---|
| **the triple inference** | *what is inferred* — three target families at different timescales (proximal goal, process, persistent motivational organization), their dependencies, and what makes values identifiable at all |
| **three cognitive layers** | *what architecture might support the inference* — the affective-machinery claim, its evidence in eleven model families, and the build gates |
| **decision traces** | *what observable traces decisions leave* — target × control × terminal topology as independent axes of every trace, with polish splitting into attraction and translation |
| **reader heuristics** | *how a bounded reader finds and combines those traces* — priors, entry cues, traversal, calibration, and an instrument panel recording what each heuristic is measured to be worth |
| **alignment** | *what objective should govern a system that can read them* — the terminal value as the balanced sum of seeking and acting. The furthest from current work and by a wide margin the least tested |

---
## Repository

| | |
|---|---|
| [`SOUNDING_LINE_SPEC.md`](SOUNDING_LINE_SPEC.md) | written before any code, hash-locked, never edited |
| [`docs/theory/`](docs/theory/) | **the hypothesis store** — every claim, its status, and what would test it |
| [`FINDINGS.md`](FINDINGS.md) | **the method archive** — how each test was actually run |
| [`TODO.md`](TODO.md) | what has not been run, under the same identifiers as the theory |
| [`docs/method/`](docs/method/) | what a control licenses, the ledger, deviations, literature reviews |
| [`docs/sim/`](docs/sim/) | traffic with the parent simulation, both directions |
| [`docs/gates/README.md`](docs/gates/README.md) | instrument gates vs claim gates |
| [`soundingline/family/`](soundingline/family/) | the hypothesis family — **data, not code**, so it can be argued with without reading Python |
| [`soundingline/probe/`](soundingline/probe/) | prompts (locked), schema, two arms |
| [`soundingline/measures/`](soundingline/measures/) | fit, unlock, gated unlock, position |
| [`prereg/`](prereg/) | the cards, locked before each run |
| [`results/readings/`](results/readings/) | human reading sessions, and a provenance ledger |
| [`fetch/`](fetch/) | corpus acquisition — imports nothing from the analysis package, by design |
| [`runners/`](runners/) | one file per experiment, each opening with its own pre-registration |
| [`run_forever_day.sh`](run_forever_day.sh) · [`run_forever_night.sh`](run_forever_night.sh) | the queue, one job at a time or the whole machine |

---

## Lineage

Direct offshoot of the [Ghost Scale Simulation](https://github.com/EmotiveAutomaton/ghost-scale-sim)
— a simulation of what happens to a reader who can no longer tell whether there is a mind behind
what they are reading. That project established the mechanisms; this one asks whether they can be
measured on real things.

Underlying theory: [Art: A Unifying Model](https://abrahamhaskins.org/art) — art as compressed
intent, appreciation as inverse reinforcement learning.

**Prior art, noted rather than discovered late:** the inversion this project performs is
Bayesian Theory of Mind / inverse planning (Baker, Saxe & Tenenbaum). The parent simulation
constructed it independently for a different domain. The contribution here is not the inversion —
it is running it over **artifacts** rather than over trajectories, which nobody appears to have
done.

---

## Cautions

The instrument may not claim: that a machine wrote something; any one of its quantities alone; that
low depth means low value — it means few decisions are *recoverable*, which is a claim about the
artifact and the reader jointly.

One curator, one model, English only, a corpus biased by which sites permit crawling. No claim
about prevalence, and none about any individual.

**MIT licensed. Read the deviations before quoting a number.**
