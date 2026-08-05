# Goal diversity vs expertise — a clean null on a proxy that is probably wrong

> ## ⚠ THE PROPOSED REPLACEMENT IS ALSO DEAD — 2026-08-05
>
> This file closes by recommending `purpose_breadth` as the correct measure, run on early vs late
> works by the same author, with the second prediction that `purpose_agreement` stays flat.
>
> **That test is cancelled and `purpose_breadth` is retired.** Simulation T-2 built a pure-difficulty
> axis with no motivational diversity anywhere in the world and `purpose_breadth` tracked it
> perfectly (goal accuracy 0.425 → 0.965 as breadth fell 0.793 → 0.272). Against **equally hard
> single-drive work**, excess breadth attributable to diversity was **−0.013, −0.025, −0.021** — zero
> or slightly negative, and inside the noise curve. `construct_is_confounded_with_difficulty: true`.
>
> Separately, **sim S-2 — cited here as `purpose_breadth`'s validation — is retracted at source.**
> Its emitter ignored `artifact.goal` once a creator was bound, so the feature streams were
> bit-identical with the mixture switched off. It measured nothing.
>
> **The curator's mechanism is untouched** — practice → automaticity → drives → variety is not
> refuted, and the simulation says plainly it cannot test that causation. What died is our instrument
> for it. Any replacement must survive a **difficulty control**, which neither of the two tried so far
> would have.
>
> → [`../../docs/FROM_GHOST_SCALE_SIM_2.md`](../../docs/FROM_GHOST_SCALE_SIM_2.md) · [`../../docs/LEDGER.md`](../../docs/LEDGER.md)

**2026-08-05.** 337 windows, 10 authors, early works against late works by the same person.
Identity controlled by construction. CPU only.

| | |
|---|---|
| late > early | **5 of 10 authors** |
| mean difference | **+0.0006** |
| career position vs diversity | rho = **+0.025**, p = 0.65 |
| sign test | p = 0.62 |

**Nothing.** Not a weak effect — a coin flip.

---

## The measure was the wrong one and that is the finding

The claim is that **motivational** variety rises with expertise, because automaticity moves
decisions out of deliberate control and into drives. I measured **the entropy of the function-word
category profile**.

Those are only the same thing if motivations show up as the shape of a function-word distribution —
which is exactly what this project has not established and has repeatedly failed to establish.
**Eighth instance of the instrument not matching the object**, caught in analysis this time rather
than after a positive was reported.

**Career position is also not expertise.** Austen's four novels span fifteen years; Darwin's three
span thirty. A late work is not automatically a more automatised one.

---

## The test that would actually address it

`purpose_breadth` — the entropy of the probe's **purpose posterior** — is the right quantity, and
the simulation validated it at matched decision density (S-2, −0.108, interval excluding zero, with
neither trap firing).

So: **run the probe on early and late works by the same author and compare `purpose_breadth`.**
Same within-author control, correct measure, and it carries the second prediction that makes it a
real test rather than a restatement:

- `purpose_breadth` **rises** with career position
- `purpose_agreement` **stays flat** — one goal, more sources feeding it

**With the floor-effect warning the simulation attached:** on transparent material with a long look,
entropy collapses to ~1e-10 in both arms and the test measures nothing. Books are long and 19th
century prose is not transparent, so this is the better bet than the Gate 3 corpus was.

GPU work, queued behind the ladder.
