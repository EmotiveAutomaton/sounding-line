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
| ~~D-0~~ | do function-word vectors separate by specified maker state? | 40 min | **FAILED 2026-08-03** — ratio 0.78, 0 categories above 2.0. [verdict](../results/d0/VERDICT.md) |
| **A** | leaked layer from function-word distributions | hours, no GPU | |
| **C** | stage E kept, re-scoped as emblematic-only | free, built | |
| **B** | `transformers` + mid-layer activation readout | an afternoon + VRAM | torch not installed |
| **D** | inverse planning over artifacts | **2–3 days to runnable** | needs D-0 |

**D is blocked, not slow.** D-0 failed: function-word vectors do not separate specified maker
states in generated text. The mechanistic reading is that a model has no leaked layer because it
has nothing unchosen — which makes the failure a prediction about the human/machine contrast
rather than a dead end, and that is a NEW hypothesis needing human artifacts with known states.

The rest of the costing still holds: `ghost-scale-sim` already implements the whole inversion —
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
