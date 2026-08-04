# STATE — read this first after any context loss

**The one file that survives a compaction.** Updated 2026-08-03, end of day 2.

Everything below is either *true right now* or *the next thing to do*. Argument lives elsewhere and
is linked.

---

## 1 · What the project is

Measure **depth**: how many of a maker's decisions are recoverable from what they made.
Not an AI detector. Never claims authorship. `SPEC` is hash-locked and never edited.

Long-run goal, the curator's, stated plainly: **detect depth → give AI empathy → extract values.**
The third is the alignment goal. These are the same inversion read out at three levels, not three
projects.

---

## 2 · Running right now

| | |
|---|---|
| **Gate 3** | 51 artifacts, k=5, both arms, local. Started 14:57. **ETA ~03:30.** |
| output | `results/gate3/gate3_local_k5.json`, log `run_parallel.log` |
| score with | `runners/score_gate3.py` — written before any result, do not edit it to fit |
| card | `prereg/gate3.py`, hash `d373508e2373` |
| input | sanitised **and** date-censored (D-6). Restarted twice for this. |

**Do not narrate per-artifact numbers.** Score once, at the end, with the locked script.

---

## 3 · The four things that are true and were expensive to learn

**a. Unlock fails its own control.** Machine-generated artifacts scored **1.111** on method
unlock; competent commercial work scored **0.917**. If a measure moves where there is nothing to
measure, it is reading something else (E36's N28). Gate 3 has no N28-analogue and cannot be given
one now.

**b. The corpus split may not exist.** The curator's blind reading rated a Half-B roofing
marketing page *above* a Half-A blog post, and read it as unambiguously human with real depth. G3.1
may be looking for a boundary that is not there in the shape the card assumes.

**c. Reading starts at an anomaly, not at the artifact.** All three of the curator's best readings
entered through a specific oddity — an absence of jargon, an admitted fib, a self-serving ordering
— and then ran purpose→method **and** method→purpose. The §3 loop is unidirectional and
purpose-first. E36 is half a cycle.

**d. The probe is a machine-matched reader** (E38: 1.000 on machine content, 0.280 on human). This
is a ceiling on every gate, not a bug in any one of them.

---

## 3b · What the curator's readings established, and they outrank my measures

Two sessions, eleven artifacts. **These came from a person reading aloud and they have survived
every measure that has failed.** Full accounts in `../results/readings/`.

**The variation of the veneer is his primary detector.** Not surface *level* — surface **change**.
An opening reaching for professional register and then relaxing out of it. The performance is what
costs something, so the performance is what slips, and the slip is where the maker shows.
*Scope limit he attached: useless on published books, because editing sands the veneer flat.*
**That cuts at G's books result — 2.05× within-author separation there cannot be surface variance.**

**Depth is a property of the writer WITH RESPECT TO THE DOMAIN.** It does not vary within an
artifact unless the domain does. This is the sharpest definition of depth the project has, because
it makes depth a **relation** rather than an attribute. Falsifier attached: depth moves where
domain moves.

**Reading enters at an anomaly**, never at the whole artifact, and then runs purpose→method AND
method→purpose. Entry point is set by wherever he has partial expertise.

**Confidence in a maker moves while reading.** "It starts questionable" and "8 or 9 by the end"
are both true of one artifact; the trajectory carries what the endpoint does not.

**The share question is not answerable by a reader.** *"Fractal layers of nested goals placed there
by the subconscious. I'm extracting it all equally with no real ability to differentiate."* A share
needs a denominator and nested goals have none. C-22 keeps `purpose_breadth`; it lost its human
check, and validation moved to a mechanism test in the sim.

**The emblematic layer cannot use the Panksepp list.** *"People don't perform Panksepp-level
drives."* The eight values belong to the leaked layer only; emblematic is collected as free text.

**What is recoverable is a presented face and its leaks**, not a person. Scope limit on every claim.

**Artifact 01 of session 02** (`apenwarr.ca`): maker 8–9 by the end but questionable at the start;
leaked play+grief in the opening, care at the end; the specific leak was defensiveness about being
in systems design, read as leakage because the professional opening failed; no deception; veneer
medium→thin→thin; goal met. Contaminated by orthography — "programme" — which is an accepted
contaminant because normalising spelling would destroy evidence.

---

## 4 · The affect layer, compressed

Two layers, and they are **the field's reconciliation position**, not a design choice:

| | | |
|---|---|---|
| **leaked** | involuntary, got through | **Panksepp primary process** — core affect |
| **emblematic** | chosen, displayed | **Barrett tertiary** — constructed emotion |

Eight values, shared set: `none_recoverable · seeking · rage · fear · care · play · lust · grief`.
`family_v3.yaml`, locked, **not the default**.

**The measurement channel, and this is the finding the next phase runs on:**

> **Function words are the leaked layer.** Non-conscious, topic-independent, very hard to fake,
> and they track *state* not just identity (`I`-frequency predicts depression better than
> negative-emotion words do). Content-word choice is the emblematic layer.

**Stage E measures only the emblematic layer**, on both its outputs, because asking an LLM for a
label returns a content-word judgement. That is not fixable by rewording.

**And LLM activations sit closer to core affect than LLM outputs do** — 171 causal emotion
directions, principal components aligning to valence/arousal. The internal state the simulation
literature demands already exists; the move is to read it, not build one.

Three nulls, all written before any run: **N-AFF** (flat where no maker), **N-AFF-2** (values must
not collapse — predicted failure mode, from LIWC's 0.49 inter-motive correlation), **N-AFF-3**
(the two layers must not be identical; `leaked` predicted to separate *worse*).

---

## 5 · Next, in order of value per hour

| | what | cost | status |
|---|---|---|---|
| ~~D-0~~ | do function-word vectors separate by specified maker state? | 40 min | **INCONCLUSIVE** — ran at 38% power; corrected from FAIL. [verdict](../results/d0/VERDICT.md) |
| **A** | leaked layer from function-word distributions | hours, no GPU | |
| **C** | stage E kept, re-scoped as emblematic-only | free, built | |
| **B′** | mid-layer activation readout while the model READS; low-order/high-order ratio | an afternoon | **torch installing 2026-08-03** |
| **D** | inverse planning over artifacts | **2–3 days to runnable** | needs D-0 |

**D-0 was INCONCLUSIVE, not a failure, and the correction is mine.** I set a pass threshold
without checking whether the design could reach it. At 380-word samples an `I`-category appears
about five times, Poisson noise on five counts swamps everything, and a power simulation says
the design would have missed a real 2.4x effect **62% of the time** — its median outcome under a
true effect was *below* its own threshold. Same class of error as the four "criteria unable to do
their own job" the parent simulation logged. D-0b fixes it at 2,000+ words and k=10, power 99%.

The costing still holds: `ghost-scale-sim` already implements the whole inversion —
`HumanCreator`, `rollout_observer`, `generative_model`, `exact.py`, pymdp installed and verified.
The gap is one function: text → feature vector. Function words are that vector. The forward model
`P(features | state)` comes from having the LLM *write* under specified states and measuring the
emissions. Synthetic forward, real inverse. See [`theory/OPTION_D.md`](theory/OPTION_D.md).

---

## 6 · Owed, and blocking

| | |
|---|---|
| **C-14** | grooming corpus never sourced. The successor's required corpus. **Now the actual blocker** — the store has ~16 unread artifacts left. |
| **C-20** | one reader. Reader skill caps extraction; one reader cannot bound their own cap. |
| **C-19** | the two arms disagree; no API replication has run |
| **N28-analogue** | Gate 3 has none |

---

## 7 · Working agreements with the curator

- **This is engineering, not a verdict.** A failed gate produces candidate fixes and a written
  reason, never a halt. Locks are telemetry, not judgement.
- **Only tests that predict downstream trouble matter.** Report those; skip the commentary.
- **Do not narrate running numbers.**
- **Every contribution he makes gets a row in** `results/readings/PROVENANCE.md`, **the same day**,
  including the ones that changed nothing.
- **Docs are references, not essays.** He already knows the literature.
- **Never edit `SPEC` or a locked card.** Deviations go in `docs/DEVIATIONS.md`.
- He has been right and I have been wrong on: dropping LUST, keeping dates, the divergence
  direction, the cost of option D. **When he pushes back, check the local information before
  defending the estimate.**

---

## 8 · Where everything is

| | |
|---|---|
| whole theory, one line per finding | [`theory/README.md`](theory/README.md) |
| what gets built next | [`SUCCESSOR.md`](SUCCESSOR.md) |
| every curator contribution → what it changed | [`../results/readings/PROVENANCE.md`](../results/readings/PROVENANCE.md) |
| the two reading sessions | [`../results/readings/`](../results/readings/) |
| deviations from locked criteria | [`DEVIATIONS.md`](DEVIATIONS.md) |
