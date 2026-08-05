# Three candidates survive five filters — and one threat the battery cannot see

**2026-08-05.** The 342-feature sweep, filtered. This is the first time this project has had a
candidate measure that was not invented by us.

---

## The funnel

| filter | what it removes | left |
|---|---|---|
| — | all features | **342** |
| ranks the ladder, **BY-corrected** | multiplicity | 89 (ladder 1) |
| **replicates on the held-out ladder 2** | corpus-specific flukes | **81** |
| **does not separate human from no-maker** | AI-detection features — 61 of the 81 are these | **20** |
| **zero prompt echo** | instruction-following | **6** |
| **survives length control** (partial rho ≥ 0.2) | the confound that killed three measures | **3** |

**61 of 81 replicated features are AI detectors.** That is the single most useful number here: the
literature's F1 ≈ 0.99 result is sitting inside our ladder survivors, and without the N28 filter we
would have adopted it as an intent measure.

## The three

| feature | what it counts | rho vs rung | partial (length) | echo |
|---|---|---|---|---|
| **`biber_COND`** | **conditional subordination** — *if*, *unless* | +0.579 | **+0.494** (p = 1.7e−7) | 0.000 |
| **`biber_CONT`** | contractions | +0.484 | **+0.371** (p = 1.5e−4) | 0.000 |
| **`biber_PHC`** | phrasal coordination | −0.349 | **−0.254** (p = 0.011) | 0.000 |

All three on **ladder 2, held out, n = 100**, having first replicated on ladder 1.

**`biber_COND` is the interesting one and it is theory-shaped.** A conditional is the linguistic form
of *a decision under a constraint* — "if the reader is in situation X, do Y". More specified intent
producing more conditionals is what the theory would predict if the instrument were working.

---

## The threat the battery cannot see, and it is serious

**My echo check tests whether the prompt *contains* the feature. It cannot test whether the prompt
*induces* it.**

Echo rho = 0.000 for all three means those categories never appear in any prompt. But the
specification pool includes:

    "for a reader whose situation is probably not the standard one"
    "acknowledging that circumstances vary a lot"
    "acknowledging that the reader may not follow the advice"

**Those contain no conditionals and would obviously induce conditionals.** Same mechanism for
contractions: *"warmly, as though to someone you like"* and *"plainly, with no attempt to impress"*
contain no contractions and would produce them.

> **This is a second, subtler form of instruction-following — semantic induction rather than lexical
> echo — and the check I built is blind to it.** It is the same class of error as the original rich
> arm, which the curator caught, and I did not design against it.

`biber_COND` is the most exposed of the three, because the specs most likely to induce conditionals
are situational ones that appear at every rung above 0.

### The test that separates them

**Score each artifact against the specific specifications it was given.** If `biber_COND` tracks
*"how many of this artifact's own specs were conditional-inducing"* better than it tracks *rung*,
it is induction. If it tracks rung after that is partialled out, it is not. The specs are
recoverable from the generation seeds, so this is an hour and no GPU.

**Until that runs, none of these three should be described as working.**

## Also owed

- **Transfer.** Do they rank human artifacts, or invert like `causal_rate` did? Untested, and it is
  the filter that killed the best-looking result of the previous round.
- **Rung −1.** Do they peak on word salad?
- **Selection.** The BY correction was applied at the sweep stage, but the four subsequent filters
  select on outcome. The protection is that ladder 2 was held out and the filters are theory-driven
  rather than fitted — but these three p-values are conditioned on selection and should not be quoted
  as if they were pre-registered.

## Status

**OPEN, three candidates, none adopted.** The funnel worked, the N28 filter earned its place by
removing 61 AI detectors, and the echo filter removed 14 more. What remains is a real short list with
one named, unclosed hole.
