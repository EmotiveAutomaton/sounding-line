<p align="center">
  <img src="docs/assets/sounding-line.jpg" alt="A brass plumb bob and coiled line resting on an open bathymetric chart" width="100%">
</p>

<div align="center">
  <sub>◯ <a href="https://github.com/EmotiveAutomaton/ghost-scale-sim">Ghost text</a>, all of it.</sub>
</div>

# Sounding Line

**An instrument for reading intent out of real artifacts.**

A sounding line is a weighted cord lowered into water to find the bottom, the oldest depth
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

It is **not an AI detector.** Where a detector would say *a machine wrote this*, this says *this
much was decided here, and this is the evidence*. That is a claim about the artifact, the maker can
rebut it, and being wrong about it is an ordinary disagreement rather than an accusation.

Which also means **firing on hurried human work is the measurement working.** Fast human work does
contain fewer recoverable decisions. Reframed as decision density rather than authorship, the
"false positive" stops being false.

And it means **you cannot evade it by writing more like a human**, because writing more like a
human, making more decisions for more reasons, is the thing being measured.

---

## Why the obvious build fails

Point a language model at a page and ask *why was this made*. It **does not work**, and the reason
is the design.

Machine content is goal-**foreign** rather than goal-*empty*, a real process expressed in a
vocabulary the reader has no entry for. An unbounded reader asked an open question **will always
produce a coherent answer**, for anything, including sludge. Free-form intent attribution is
confident fabrication with good grammar, never a measurement.

What makes a human maker recoverable is that **the human solution space is bounded**, by
architecture, by embodiment, by metabolic cost, by having to choose one thing because doing both
was too expensive. The wall in front of generated content is **non-invertibility** rather than an
absent maker, many maker-states mapping to one surface, where the surface is perfectly familiar
and the state behind it cannot be recovered. *Legible and empty.*

**So the probe imposes a bounded, human-shaped hypothesis family and measures fit inside it.** The
boundedness is the mechanism.

---

## Where it actually stands

**2026-08-09. Fifty-odd tests across four gates, three simulation batches and eleven model
families.** The honest version, because the honest version is the point.

### What has survived its controls

| | |
|---|---|
| **The flagship, under a fair induction control** | The old induction control's regressors *contained the dose it claimed to remove* (L22). With the dose arithmetically removed instead, **the effect survives on all three independently generated corpora and gets stronger**, and three published linguistic features it had killed revive the same way, nine of nine tests (L23, L24). What this measures is response to **specified constraint dose** within one generator. Whether it touches human intent, depth, or decisions is exactly what the current program tests |
| **The per-block dose correlation** | Correlation between a prompt's specified constraint dose and the reader's affective signal, computed block by block. **25 runs across 11 model families, 18 survive.** The no-maker control, re-adjudicated after an audit found its verdict gate could not fail (L26), fires at the rate luck supplies overall but concentrates in the flagship family. The permutation test ran and **could not distinguish leak from luck** (L40), so that concentration stands as an open liability |
| **Function words against specified dose** | Closed-class word rates classify which rung an artifact came from at **1.6× to 3.0× chance**, scaling with dose. **No model involved.** (Specification recovery, which once corroborated this through a second channel, turned out to be carried by lexical echo and left the flagship summary, L36) |
| **Affect directions are real** | Four times chance on held-out sentences, while a word-counting model scored **exactly** chance |
| **Authorship as a calibration** | 7.6× chance, and identical at all four scrambling granularities, which proves the scrambling code is correct before any real number is computed |

### What died, and why it is the useful half

**Every measure that reads the *artifact* has died, to length, then register, then vocabulary, in
that order.** **Dated correction (2026-08-08): the final three kills were the broken control's, not
the features', and all three revive under the fair control on all three ladders (L24). The deaths
to length and register stand.** Decision density was word count, then vocabulary diversity. Of 342
published linguistic features, **61 of the 81 that replicated were machine-detectors**; the three
survivors died to a test of whether the prompt *caused* a feature without *containing* it.

**The block profile is a fact about the model, not the maker.** Identical between intent-laden
text and text with no maker at all, in **every one of eleven model families**, with the peak
landing anywhere from block 2 to block 47. **The bimodal profile this project once reported was a
two-model artifact.**

**Gate 3, the primary for a month, is void twice over.** Its statistic reads a large positive where
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

It is no longer a measure. **Three separate hypotheses are blocked on the same corpus, one maker
across different KINDS of artifact**, different register, audience and purpose rather than
different topics. Depth as a relation to a domain needs it; the polish-variation claim needs it;
values needing many works needs it.

**It turns out to be genuinely rare.** The cross-genre authorship literature describes its own data
as *"scarce and very limited in size"*, and most corpora carrying a "cross-domain" label are
cross-*topic* underneath. PAN's cross-domain tasks are all fan fiction, varying fandom rather than
kind. The program now leads this thread with a small commissioned pilot rather than more corpus
hunting.

---

## What is being built now

**One human read fifteen artifacts aloud, blind, in plain text.** That produced more usable design
than three gates. Reading starts at **an anomaly** rather than at the whole artifact, the loop runs
**both ways**, and *"depth is a property of the writer with respect to the domain"*, which makes
depth a **relation** rather than an attribute, and is why the missing corpus is fatal rather than
inconvenient. **A relation cannot be measured by varying one side.**

**Those readings are the richest hypothesis source the project has.** They are not a validated
instrument, because no independent ground truth has ever scored them, so the most generative
evidence in the project has a sample size of one reader and is treated accordingly.

### The proximal goals

The unit of analysis is changing. The program stops searching for a scalar that correlates with
"depth" and starts validating recovery of individual, independently recorded choices. A decision
event carries its target, the alternatives that were available, the choice made, its dependencies,
and its context. For each event the question is whether the finished artifact lets a bounded
reader recover the actual choice better than context alone and better than matched false
alternatives. Only after that works do recovered events get summarized as amount, breadth, and
integration, with calibration reported separately. The denominator is declared choice
opportunities or revision events, never words, because per-word density recreates the length trap.

1. **Turn the revision corpus into a choice-recovery study.** Each labelled revision is an event
   with a recorded purpose. The reader picks the actual purpose from a bounded candidate set,
   scored against the brief alone, shuffled labels, unchanged passages, and matched decoys, split
   by author. The decisive control matches content and surface revisions on lexical sophistication
   and asks whether "content" remains identifiable once the shortcut is gone.
2. **Replace the ladder with a factorial benchmark** crossing target (surface against
   problem-directed), amount, coupling, and realization, so the dose-responsive quantities face a
   real construct test.
3. **Validate estimators where ground truth exists.** The parent simulation runs the estimator
   tournament with exact inference first and reports a failure-boundary map, not an average score.
4. **Keep killing our own instruments first.** The audit record above is the point, not the
   embarrassment.

The nearest defensible public result is narrow. Given a fixed brief and a held-out human author,
the finished artifact allowed a bounded reader to recover specified problem-directed revision
purposes above matched alternatives, beyond what the brief and surface changes supplied. That is
small enough to defend and large enough to justify everything downstream.

### The theory, in five files

[`docs/theory/`](docs/theory/) is the hypothesis store, holding every claim, its status, and what
would test it. **More than 130 numbered hypotheses**, each carrying whether it was checked on real
text, in the parent simulation, or against published work. Each file owns one question and they do
not overlap:

| | |
|---|---|
| **the triple inference** | *what is inferred*. Three target families at different timescales (proximal goal, process, persistent motivational organization), their dependencies, and what makes values identifiable at all |
| **three cognitive layers** | *what architecture might support the inference*. The affective-machinery claim, its evidence in eleven model families, and the build gates |
| **decision traces** | *what observable traces decisions leave*. Target × control × terminal topology as independent axes of every trace, with polish splitting into attraction and translation |
| **reader heuristics** | *how a bounded reader finds and combines those traces*. Priors, entry cues, traversal, calibration, and an instrument panel recording what each heuristic is measured to be worth |
| **alignment** | *what objective should govern a system that can read them*. The terminal value as the balanced sum of seeking and acting. Formally dormant, a boundary specification with a written wake condition |

---
## Repository

| | |
|---|---|
| [`SOUNDING_LINE_SPEC.md`](SOUNDING_LINE_SPEC.md) | written before any code, hash-locked, never edited |
| [`docs/theory/`](docs/theory/) | **the hypothesis store**, every claim, its status, and what would test it |
| [`FINDINGS.md`](FINDINGS.md) | **the method archive**, how each test was actually run |
| [`TODO.md`](TODO.md) | what has not been run, under the same identifiers as the theory |
| [`docs/method/`](docs/method/) | what a control licenses, the ledger, deviations, literature reviews |
| [`docs/sim/`](docs/sim/) | traffic with the parent simulation, both directions |
| [`docs/gates/README.md`](docs/gates/README.md) | instrument gates vs claim gates |
| [`soundingline/family/`](soundingline/family/) | the hypothesis family, **data rather than code**, so it can be argued with without reading Python |
| [`soundingline/probe/`](soundingline/probe/) | prompts (locked), schema, two arms |
| [`soundingline/measures/`](soundingline/measures/) | fit, unlock, gated unlock, position |
| [`prereg/`](prereg/) | the cards, locked before each run |
| [`results/readings/`](results/readings/) | human reading sessions, and a provenance ledger |
| [`fetch/`](fetch/) | corpus acquisition, importing nothing from the analysis package by design |
| [`runners/`](runners/) | one file per experiment, each opening with its own pre-registration |
| [`run_forever_day.sh`](run_forever_day.sh) · [`run_forever_night.sh`](run_forever_night.sh) | the queue, one job at a time or the whole machine |

---

## Lineage

Direct offshoot of the [Ghost Scale Simulation](https://github.com/EmotiveAutomaton/ghost-scale-sim),
a simulation of what happens to a reader who can no longer tell whether there is a mind behind
what they are reading. That project established the mechanisms; this one asks whether they can be
measured on real things.

Underlying theory: [Art: A Unifying Model](https://abrahamhaskins.org/art), art as compressed
intent, appreciation as inverse reinforcement learning.

**Prior art, noted rather than discovered late.** The inversion this project performs is
Bayesian Theory of Mind / inverse planning (Baker, Saxe & Tenenbaum). The parent simulation
constructed it independently for a different domain. The contribution here is not the inversion,
it is running it over **artifacts** rather than over trajectories, which nobody appears to have
done.

---

## Cautions

The instrument may not claim that a machine wrote something. It may not quote any one of its
quantities alone. And it may not read low depth as low value, since low depth means few decisions
are *recoverable*, which is a claim about the artifact and the reader jointly.

One curator, one model, English only, a corpus biased by which sites permit crawling. No claim
about prevalence, and none about any individual.

**MIT licensed. Read the deviations before quoting a number.**
