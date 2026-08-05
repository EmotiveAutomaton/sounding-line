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

Honest version, because the honest version is the point.

| | |
|---|---|
| **Gate 0** literature | passed |
| **Gate 1** the family exists, an artifact can be read | passed |
| **Gate 2** the falsifiers | **failed** on purpose-based measures. Diagnosed to two findings from the parent simulation, and rebuilt. |
| **Gate 3** the claim gate — does method unlock separate care from filler? | **running**, 51 artifacts, pre-registered and hash-locked |

**A control that already failed, and matters more than any of the above.** Artifacts with no
maker at all — machine-generated — scored *higher* on method unlock than competent commercial work.
If a measure moves where there is nothing to measure, it is reading something else. That result is
why the successor design exists and why it was written before Gate 3's numbers were seen.

Everything is pre-registered and content-hash-locked before it runs. Criteria that were changed
afterwards are logged, the originals retained and still computed, and reported as failing if they
fail.

---

## What is being built now

Two things happened in one day and they changed the project.

**A human read ten artifacts aloud**, blind, in plain text. That produced more usable design than
the three gates had: reading starts at **an anomaly** rather than at the whole artifact; the loop
runs **both ways**, not purpose-first; and the corpus split the gates test **may not exist** in the
shape assumed — a commercial roofing page read as more human, with more depth beneath it, than a
personal blog post.

**And the affective layer opened up.** The hypothesis family was entirely cognitive — purpose,
audience, depth, cost — while a human reader's account of a maker is overwhelmingly *affective*.
The split that fell out — what **leaked** versus what was **performed** — turns out to be the
reconciliation position between the two dominant theories of emotion, which was not the plan.

### The four experiments this produced, in plain terms

**A — can you measure what a writer did not choose to say?**
Function words — *the, of, but, I, without* — are produced below deliberation. They are why
authorship attribution works: you cannot fake them, because you are not choosing them. If they
carry a maker's *state* and not only their identity, they are a channel into the part of a person
that shows up in writing without being put there.
**Built. Runs on the corpus. Not yet a classifier** — within-group variance swamps the between-group
difference, and the largest apparent signal is probably genre rather than leakage. What it needs is
a baseline *per maker* rather than per corpus, which needs a corpus organised by maker.

**C — is asking a model "what stance is this performing" a measurement or an opinion?**
An opinion. Asking a language model about a text returns a judgement about the words that were
*chosen*, which is the performed layer by construction — no rewording reaches the unchosen one.
**So the field was renamed to say so.** It is kept rather than deleted, because comparing the
model's guess against the measured channel is itself a real test: can a system with no interior
predict what leaks out of one?

**D-0 — could the whole approach work at all?**
Before building the expensive thing, the cheap version: have a model write the same piece under
sixteen different specified states, and see whether the function-word signatures separate.
**It did not separate — and then the test itself turned out to be too weak to have shown it.**
At 380 words a category like *I* appears about five times, and five is not a number you can do
statistics with. A power simulation says the design would have missed a real effect 62% of the
time. **Verdict corrected from FAIL to INCONCLUSIVE**, which is worse than a failure and more
useful than a false one. The redesign is written, with its power computed *first* this time.

**B — does the machine already have the thing we are looking for?**
Recent interpretability work finds that language models build internal emotion structure nobody
designed: directions in activation space that causally control behaviour, arranged along
**valence and arousal** — and, tellingly, the low-order features sit near the input while
higher-order predictive ones sit further out. That is the same two-layer split, appearing
unbidden in a system built for something else.
**Not yet built.** It is the most promising and the least certain thing on the list.

Full state, one line per finding: **[docs/theory/README.md](docs/theory/README.md)**

---

## Repository

| | |
|---|---|
| [`SOUNDING_LINE_SPEC.md`](SOUNDING_LINE_SPEC.md) | written before any code, hash-locked, never edited |
| [`docs/theory/`](docs/theory/) | the live theory, compressed |
| [`docs/design/SUCCESSOR.md`](docs/design/SUCCESSOR.md) | what gets built next, written before Gate 3's result |
| [`docs/gates/README.md`](docs/gates/README.md) | instrument gates vs claim gates |
| [`docs/method/DEVIATIONS.md`](docs/method/DEVIATIONS.md) | every change to a locked criterion |
| [`soundingline/family/`](soundingline/family/) | the hypothesis family — **data, not code**, so it can be argued with without reading Python |
| [`soundingline/probe/`](soundingline/probe/) | prompts (locked), schema, two arms |
| [`soundingline/measures/`](soundingline/measures/) | fit, unlock, gated unlock, position |
| [`prereg/`](prereg/) | the cards, locked before each run |
| [`results/readings/`](results/readings/) | human reading sessions, and a provenance ledger |
| [`fetch/`](fetch/) | corpus acquisition — imports nothing from the analysis package, by design |

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

---

<sub>Haven't edited any of this yet — it's on the list. Should be roughly current.</sub>
