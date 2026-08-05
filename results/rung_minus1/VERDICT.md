# Rung −1 and the granularity sweep — the ceiling control is clean, and the word shuffle is a wrecking ball

**2026-08-05.** Built after the curator challenged the shuffle test. Two questions in one run: does
any measure read *noise* as intent, and at what granularity does an effect actually live.

Pre-registration is in the header of `runners/run_rung_minus1.py`, written before the run.

---

## §1. Rung −1 — nothing reads noise as intent

> **No measure places word-shuffled text at or beyond the most-specified rung.** The ceiling control
> comes back clean.

That is the reassuring answer to the sharper form of the curator's worry — *any measure defined as
departure-from-expectation will score noise as maximally intentional.* None of ours does. The layer
ratio in particular puts word salad **far past the least-intent end**, which is the opposite failure
and not a failure at all.

**Caveat, and it matters for reading the JSON:** rung −1 is **uninformative for permutation-invariant
statistics.** Shuffling a corpus of bag-of-words measures returns the corpus mean by construction, so
`type_token_ratio`, `i_rate`, `causal_rate` and the rest all report `WEAK ~+0.5` at every
granularity. That is arithmetic, not evidence. **Rung −1 only says anything about measures that are
sensitive to order** — which here means the layer ratio.

---

## §2. The granularity sweep — and this is the number that settles it

Layer ratio on the ladder, where register, topic, format and generator are constant by construction:

| | value | position on the ladder |
|---|---|---|
| **rung 0** (least intent) | **1.1173** | 0.00 |
| rung 1 | 1.0934 | |
| rung 3 | 1.0683 | |
| rung 6 | 1.0436 | |
| **rung 10** (most intent) | **1.0671** | 1.00 |
| | | |
| paragraph-shuffled | 1.0837 | +0.67 |
| sentence-shuffled | 1.0798 | +0.75 |
| phrase-shuffled (5-word) | 1.1283 | −0.22 |
| **word-shuffled** | **1.2577** | **−2.79** |

**The entire ladder spans 0.050.** Word-shuffling moves the measure **0.140** — nearly **three times
the whole range of the thing the measure is supposed to detect**, and in a direction no rung ever
goes.

> **That is not an ablation. It is a perturbation ~3× larger than the signal.** Asking whether an
> effect "survives" being hit that hard is not a control; the measurement has been moved to a
> different operating point and the comparison is between two incommensurable things.
>
> `docs/theory/CONTROLS.md` §3 argued this from the human/machine numbers (both arms moved up ~14%).
> **This is the direct measurement of it, on the controlled corpus, and it is worse than argued.**

### What the curve actually says about the measure

| destroyed | measure moves | conclusion |
|---|---|---|
| paragraph order | ~nothing (1.084 vs a ladder mean of ~1.078) | **document structure contributes nothing** |
| sentence order | ~nothing (1.080) | **discourse order contributes nothing** |
| local syntax (phrase) | +0.050 — one full ladder span | **the effect lives at or below the sentence** |
| everything (word) | +0.140 — three spans | out of distribution; uninterpretable |

**Whatever the ladder's −0.275 is, it is carried locally, not by argument structure.** That is new,
it is specific, and no binary shuffle test could have produced it.

**Sentence-shuffling is the replacement control.** It stays grammatical, stays in distribution, keeps
register and vocabulary, and destroys only the order a reader would use to follow an argument.

---

## §3. The unrelated finding this run turned up, and it is not what it first looks like

Re-reading `results/ladder/ladder.json` under the revised doctrine: **five measures ranked the ladder
monotonically and every one was auto-labelled `VOCAB` and discarded** — because a permutation-invariant
statistic trivially "survives" shuffling.

| | rho vs rung | p | partial, length-controlled | prompt-echo rho |
|---|---|---|---|---|
| `you_rate` | +0.703 | <0.0001 | +0.664 | **+0.320 — contaminated** |
| **`causal_rate`** | **+0.659** | <0.0001 | **+0.566** | **0.000 — the prompts contain no causal words at all** |
| `density_scale_gain` | +0.548 | <0.0001 | — | (TTR, separately disqualified) |
| `insight_rate` | +0.457 | 0.0009 | +0.275 | +0.333 — partly contaminated |
| **`i_rate`** | **+0.407** | 0.0034 | **+0.368** | **0.000 — no first person in any prompt** |

The echo check rebuilds the exact prompts from their generation seeds and measures the same
categories **in the prompts themselves**. `causal_rate` and `i_rate` are the only two where the
prompt carries *literally zero* of the category at every rung, so neither can be the model echoing
its instructions. Both survive the length control.

### And then it fails to transfer, which is the whole point of checking

`causal_rate` on real artifacts against the no-maker set:

| | causal rate |
|---|---|
| **human (n = 51)** | **3.162** |
| thin (n = 12) | 5.353 (p = 0.025) |
| averaged (n = 12) | 5.359 (p = 0.069) |
| **rich (n = 12)** | **6.080** (p = 0.0011) |

**Machines use nearly twice the causal language humans do, and the `rich` arm — machine-written *with*
a purpose and audience — uses the most of all.** So the ladder ordering is real and clean, and it
points the wrong way.

> `causal_rate` is not measuring depth. **It is measuring how explicitly the reasoning is stated** —
> and that rises with specified intent *within a generator* while being higher in machine text than in
> human text generally.
>
> Which is E37's *legible and empty* wall, arriving from a new direction and on real text. Legibility
> and depth come apart, and this is a measure of the legibility half.

**It is not a rescued intent measure and must not be reported as one.** What it is worth: it is the
first quantity here that cleanly ranks the ladder with no echo and no length confound, and it names
what that ladder ordering *is* — explicitness, not depth.

---

## §4. What this changes

| | |
|---|---|
| **rung −1** | clean. No measure reads noise as intent. Only meaningful for order-sensitive measures — say so wherever it is cited |
| **the word shuffle** | **retired as a verdict-bearing control for anything order-sensitive.** It perturbs ~3× the signal. Keep it for permutation-invariant statistics, where it is exact |
| **sentence shuffle** | its replacement. In-distribution, grammatical, destroys only discourse order |
| **the layer ratio** | its ladder effect is carried **at or below the sentence**, not by document structure. Still unresolved, now better characterised |
| **the ladder's `FAIL`** | stands on the length void (rho +0.403 vs a 0.400 threshold), but **its second ground — "no measure ranks the rungs on anything but vocabulary" — was the shuffle test over-firing.** Five measures ranked the rungs; two of them cleanly |
| **`causal_rate`** | a legibility measure, not a depth measure. Logged, not adopted |
