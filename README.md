# Sounding Line

**An instrument for reading intent out of real artifacts.**

A sounding line is a weighted cord lowered into water to find the bottom — the oldest depth
instrument there is. It returns a reading when there *is* a bottom, and runs out when there isn't.
"To sound someone out" already means to probe for their intentions.

---

## This is not an AI detector. It is an intent detector.

Those come apart, and the place they come apart is the entire contribution.

A person directing a language model carefully — many decisions, revisions, a real purpose, a real
audience — produces an artifact with **a great deal of recoverable intent**. A person churning out
search-engine filler produces an artifact with almost none. **The instrument ranks the first above
the second, and that is the correct answer**, even though the first involved a machine and the
second did not.

Three things follow:

**It steps out of the arms race.** Every surface detector is locked in a loop where detection
improves, evasion improves, and false accusation climbs. **You cannot evade an intent probe by
writing more like a human.** Writing more like a human — making more decisions for more reasons —
is the thing being measured. The only way to defeat it is to actually mean something.

**It has no false-accusation problem.** The instrument never says *a machine wrote this*. It says
*little was decided here*. That is a claim about the artifact, the maker can rebut it with
evidence, and being wrong about it is an ordinary disagreement rather than an accusation.

**Firing on hurried human work is the measurement working, not a bug.** Fast human work does
contain fewer decisions. Reframed as decision density rather than machine authorship, the "false
positive" stops being false.

---

## How it works, and why the obvious version doesn't

The obvious build — point a language model at a page and ask *why was this made* — **does not
work.**

Machine content is not goal-*empty*. It is goal-**foreign**: a real purpose, pursued by a real
process, expressed in a vocabulary the reader has no entry for. So an unbounded reader asked an
open question **will always produce a coherent answer**, for anything, including sludge. Free-form
intent attribution is not a measurement. It is confident fabrication with good grammar.

What separates a human maker is that **the human solution space is bounded** — by architecture, by
embodiment, by metabolic cost, by having to choose one thing over another because doing both was
too expensive. That boundedness is what makes a human maker *invertible* from their work. The wall
in front of generated content is not the absence of a maker; it is **non-invertibility** — a
many-to-one map from maker-states to surfaces, where the surface is perfectly familiar and the
state behind it cannot be recovered.

**So the probe imposes a bounded, human-shaped hypothesis family and measures fit inside it.** The
boundedness is not a limitation of the design. It is the mechanism.

The family lives in [`soundingline/family/family_v1.yaml`](soundingline/family/family_v1.yaml) —
data, not code, so it can be argued with by someone who doesn't read Python.

### The loop, not a chain

Goal, process, and values are not separately measurable. Each conditions the others, and the
recursion is the method:

```
    bounded goal hypotheses ──→ posterior over purpose
              ↑                          │
              │                          ↓
    re-weight posterior          extract the decision chain
    given what the method   ←──  visible under that purpose
    reveals about purpose               │
                                        ↓
                            implied values: what was optimised,
                            what was traded away to get it
```

**Run to convergence and record the trajectory, not just the endpoint.** How fast it converges,
and whether it converges at all, is data. A real maker should tighten the loop quickly; an artifact
with no coherent maker should either oscillate or settle into a confident answer that *differs on
every run*.

---

## What comes out

Four quantities. **The reading is the tuple** — none alone is sufficient, and reporting one alone
invites the overclaim.

| | |
|---|---|
| **Fit** | How well the best hypothesis in the bounded family explains the artifact. **Low fit is the wall.** |
| **Convergence** | Agreement across independent reconstructions. Hollow content produces *confident mutual disagreement*. Needs no ground truth, which is what makes it deployable on real text. |
| **Depth** | How many levels of decision are recoverable. Ranks a carefully directed model output above human filler. |
| **Audience posterior** | Probability the intended reader was not a person. Says the socially useful thing without ever making an accusation about authorship. |

---

## Status

**Gate 0 passed.** [`docs/gate0/LITERATURE.md`](docs/gate0/LITERATURE.md) is the literature review,
and it amended the spec in five places — most importantly, bounded-family Bayesian intent inversion
turned out to be prior art, so the novelty claim moved to the artifact-level object and the corpus
application. Read it before reading anything else here.

**Gate 1 is pre-registered and not yet run.** [`prereg/gate1.py`](prereg/gate1.py).

The gates are decision points, not a schedule. Each one's honest options are continue, redesign,
or stop.

| gate | what it establishes |
|---|---|
| 0 | the literature actually checked — **passed** |
| 1 | the bounded family exists and a single artifact can be read |
| 2 | the falsifiers run — human SEO vs grooming, rich-prompted vs thin-prompted model output. **If the instrument cannot separate those pairs, stop and redesign.** |
| 3 | the boundedness ablation. If bounded ≈ free-form, the architecture is wrong |
| 4 | baselines and severity — a false-positive rate published alongside every claim |
| 5 | the corpus gate. The first gate that needs money |

---

## Security posture

**The corpus under study is adversarial content engineered to influence language models.** That is
not a risk of this project, it is the definition of the subject matter. Feeding it to a model-based
probe *is* the attack surface, and getting it wrong does not produce a bad result — it produces a
result that is silently the attacker's.

- **Fetch and analysis are separate processes with separate privileges.** Fetch reaches the network
  and writes to a content-addressed store. Analysis reads only from that store and has **no network
  at all**.
- **The probe gets no tools.** Not a restricted set — the empty set. It reads and returns a
  constrained schema. It cannot fetch, write, execute, or call anything.
- **All fetched text is data, never instruction**, delimited and tagged with source and trust level.
- **Nothing is re-hosted.** Hashes and offsets are public; text stays local.

This is the dual-LLM / CaMeL pattern, and the 2026 consensus is that it is defence in depth rather
than a solution. The spec derived it independently before the name was known; see
[`docs/gate0/LITERATURE.md` §7](docs/gate0/LITERATURE.md).

---

## Prior work

This project is a direct offshoot of the **[Ghost Scale
Simulation](https://github.com/EmotiveAutomaton/ghost-scale-sim)** — a ten-version, pre-registered
model of how readers work out what a maker was for, and what happens when nothing was. The
findings that lead into this instrument are E2 (confident mutual disagreement under a false label),
E20 (invention peaks in the middle of the readability axis), E36 (pinning purpose roughly doubles
method recovery), E37 (the wall is non-invertibility, not vocabulary), E55 (asking *who made this
and why* is a defence where surface filtering is not), and E57 (better detection does not mean
fewer false accusations, once content adapts).

**The simulation is cited as prior work and is not imported.** Its model has no counterpart in real
text, and shared code would drift into a claim that the two are the same object. They are not — one
is a mechanism, the other is an instrument built on the mechanism's implications.

**The habits carry over, not the code:** spec written before code and never edited afterwards;
hash-locked pre-registration; a null for every headline; every deviation logged where it happened;
and the severity rule — *every headline gets its false-positive rate before it gets a sentence.*

The underlying theory is *Art as an Algorithmic Virus*
([10.5281/zenodo.19407789](https://doi.org/10.5281/zenodo.19407789)).

---

## Licence

See [LICENSE](LICENSE).
