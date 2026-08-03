# The successor design

**Started 2026-08-03, while Gate 3 was still running and before its result was seen.** That timing
is deliberate and it is the same discipline as C-22: a successor designed after a number is a
successor designed to explain that number.

> Let's clarify the successor design. Start planning it out now, I think, because this process
> needs to... I uncovered some useful things through going through this process. It was just
> painful and a little bit brutal.
>
> — the curator, after session 01

**This is not a replacement for Gate 3 and does not depend on Gate 3 failing.** If G3.1 holds, this
is what gets built on top of it. If it fails, this is what replaces it. The design is the same
either way, which is the point of writing it now.

---

## §0. What changed, in one paragraph

Three gates have told this project that its measures do not separate what it wanted separated. One
afternoon of a human reading ten text files told it **what the measures are missing**, which is a
different and more useful kind of information. The successor is built from that afternoon: it reads
the way the curator actually read, rather than the way the §3 loop assumes reading works.

---

## §1. The one-line change to what the instrument claims

Current, from SPEC §1: *not an AI detector, an intent detector.*

Proposed:

> **It reports what a maker's decisions were ultimately for, how concentrated that answer is, and
> how much of the maker is recoverable at all — and it says when the answer is that no one is
> recoverable.**

Three outputs, none of them a verdict about a person: **terminal-value concentration**,
**reconstructibility**, and an explicit **wall** state. Every one is rebuttable by the maker, which
is the property the detection framing can never have.

---

## §2. Stage 0 — the anomaly pass

**The single most valuable thing session 01 produced, and the cheapest to build.**

The curator entered every successful reading through a specific oddity, never through the artifact
as a whole:

| artifact | the anomaly | what it unlocked |
|---|---|---|
| technical debt essay | no acronyms anywhere, in a technical piece | *deliberately staying at the level of theory* |
| leaky abstractions | *"earlier, for the sake of simplicity, I told a little fib"* | *"that line is written by a human 100%"*, and then depth that had been invisible |
| affiliate roundup | JotForm at #1, Amazon at #2 | *this is an ad for JotForm*, and the two descriptions then read completely differently |

The probe has no such stage. Stage A asks for the purpose of the whole artifact and every later
stage is conditioned on it.

**Build:** a stage that runs *before* any purpose is proposed and answers one question — **what in
this artifact does not fit, and what would have to be true of the maker for it to fit?** Output is
a ranked list of anomalies with located evidence spans. Stage A then receives them.

**Falsifier.** If purposes proposed after the anomaly pass are no better recovered than purposes
proposed without it, the stage buys nothing and comes out. Measured on span-level agreement across
seeds, not on plausibility.

---

## §3. The loop runs both ways

> If you figure out part of either piece — the values or the method — you can immediately use that
> to jump into the goal, and then use that to figure out the rest of the process. Maybe you can
> even use the part you have expertise on specifically.

E36 established purpose → method within a reading. It did not establish that the reverse cannot
happen, and the curator ran it in reverse three times out of three.

**Build:** the loop takes an entry point rather than assuming one. Given an anomaly with strong
evidence, it may propose a *method* hypothesis first and derive purpose from it, then re-derive
method under the settled purpose. The existing purpose-first path stays; which path fires is
recorded.

**Falsifier.** If the method-first path never fires, or fires and produces the same reading, the
cycle is unidirectional after all and E36 was the whole story.

---

## §4. Family v3 — an affective dimension

The bounded family is entirely cognitive-instrumental: purpose, audience, depth, cost_borne,
trade_offs, artifact_effort, demonstrated_work. **The curator's readings are overwhelmingly
affective** — irritated, performative anger that was real once, quiet expert, no-nonsense gruff
contractor, someone with something to prove, a child who just learned a heuristic. He noticed
himself doing it and named it as the human prior that makes the space tractable:

> I'm reaching for the edges of the solution space that humans use to simplify the solution state.
> And I'm reflexively doing so... **Panksepp's primitives**, or some such. It's a great starting
> point.

**Build:** a small affective dimension over the maker's state, bounded and ordinal like the rest of
the family, with each value requiring located evidence in the same way `alternative_rejected` does.
Locked as `family_v3.yaml`; v1 and v2 stay untouched.

**The risk, stated in advance.** This is the change most likely to make the probe confabulate. An
affective label is exactly the thing a language model will supply fluently whether or not it is
supported. **The evidence requirement is not decoration here, it is the whole safeguard**, and
family v3 must ship with a null: on artifacts with no maker, the affective posterior must stay
flat. That is E36's N28 applied to the new dimension, and this time it is written before the
measure exists rather than discovered afterwards.

---

## §5. What Gate 4 tests, and on what

**Corpus.** A corpus this project has not seen — the Gate 3 card requires it and C-14 has owed it
since the beginning. **Grooming content is the corpus**: E55's motivating case, the simulation's
only constructive result, and this project's oldest debt, all the same acquisition.

**Reader.** Two, not one. C-20 has been owed for as long as C-14, and E10 says reader skill caps
extraction — one reader cannot bound their own cap.

**Instrument for the human side.** Not an ordering. The curator's own verdict on the session 01
protocol:

> I wasn't giving you what you needed, because what I needed was some kind of Likert scale.

So: labelled scales with anchors, per artifact, plus the free-form commentary that produced
everything valuable in session 01. Randomised order per reader — fatigue was visible by slot 09 and
it runs one way.

**The primary.** Not A-vs-B separation. Session 01 says the split may not exist in the shape the
Gate 3 card assumes — a Half B roofing page read as clearly human with real depth, a Half A post
read as possibly not human at all. The successor's primary is **agreement between the instrument
and human readers on reconstructibility**, artifact by artifact, with the wall as an explicit
category rather than a low score.

That is a harder test and a more honest one: it can fail without anyone having to believe a
corpus label.

---

## §6. Measures carried forward, and their status

| measure | status |
|---|---|
| `purpose_breadth` | **promoted.** C-22's corrected form — concentration, not singularity. Recorded for every Gate 3 artifact. |
| gated unlock | **built, untested.** `measures/gated.py`. Its first job is the control raw unlock failed. |
| raw unlock | **kept as a baseline.** Gate 3's primary; the gated version has to beat it. |
| fit (Pareto panel) | **kept.** Nothing has argued against it. |
| surface variance within artifact | **new.** S-1..S-4 in `docs/theory/SURFACE_AND_DEPTH.md`. Nothing measures position. |
| purpose agreement | **demoted to diagnostic.** E36 says purpose is constructed flat; C-22 says commercial work agrees *more*. |

---

## §7. What this design is not allowed to do

- **Fit itself to the Gate 3 corpus.** Those 51 artifacts have been read many times. Any measure
  tuned on them is unfalsifiable, and the locked card says so.
- **Claim provenance.** §7 of the findings gives a mechanism linking flat motive to delegated
  method. It raises a prior. It is not a detector and must never be reported as one.
- **Ship an affective dimension without its null.** See §4.
- **Treat a gate failure as a stop.** Per the curator, and it is a correction to my practice rather
  than a relaxation of the spec: the gates are telemetry for building, not verdicts on whether to
  continue. A failed threshold produces candidate fixes and a written reason, not a halt.
