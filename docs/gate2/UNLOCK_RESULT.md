# Method unlock — E36's prediction holds, on a tiny sample, and F2 still does not separate

**Status: EXPLORATORY.** Gate 2's failure stands and is not rehabilitated by this.

Run 2026-08-03, local arm, k=3, 14 artifacts. `results/gate2/unlock_scored.json`.

---

## §1. Result

| group | n | **unlock** |
|---|---|---|
| **row 2 — real makers** | 4 | **1.28** |
| **row 3 — commercial filler** | 3 | **0.92** |
| row 5 — pre-2020 human | 4 | 1.09 |
| generated A/B/C | 3 | 1.11 |

**E36's prediction holds: row 2 > row 3, gap +0.37, in the direction fixed by prior work.**

Per artifact, sorted by row:

| artifact | before → after | unlock |
|---|---|---|
| LocalThunk, building Balatro | 3.3 → **6.7** | **2.00** |
| Paul Graham, *Writing, Briefly* | 3.3 → 4.3 | 1.30 |
| Steam community guide | 8.0 → 7.7 | 0.96 |
| RecipeTin Eats | 2.7 → 2.3 | 0.88 |
| Glad brand page | 3.0 → 3.5 | 1.17 |
| Eurogamer build guide | 2.0 → 1.7 | 0.83 |
| plumber service-area template | 1.3 → 1.0 | 0.75 |
| Dragon Haven (GeoCities) | 2.3 → **3.7** | **1.57** |
| eHow ×3 | — | 1.00, 1.00, 0.80 |

---

## §2. What is genuinely encouraging

**The artifact that failed hardest on purpose measures succeeds hardest here.** LocalThunk's
account of building his own game scored purpose agreement **0.33** — the worst in the corpus — and
unlocks at **2.00**, the best. E36 predicted "pinning what someone was for roughly doubles how much
of their method you recover." It doubled.

**Row 3 sits below 1.0 twice, and never above 1.17.** An unlock below 1.0 means pinning the purpose
recovered *fewer* decisions than reading it cold — there was nothing further to find once you knew
what the page was for. That is a coherent description of commercial filler and it is not a
description the purpose-side measures could produce.

**Dragon Haven at 1.57** is the strongest single corroboration outside row 2. The curator read that
GeoCities roleplay page as "deeply human," and it unlocks more than every content-farm artifact in
its own row.

**The loop change helped the old measures too.** The named-alternative rate, which *reversed* at
Gate 2 (row2 0.28 vs row3 0.42), now runs the right way (0.51 vs 0.42). Continuing to read after
the posterior settles produced better decisions generally — so the fix was to the instrument, not
only an added metric.

---

## §3. What this does not do, stated plainly

**F2 still fails.** The generated pair does not separate: item A **1.00**, item C **1.00**, item B
**1.33** — the thin-prompted artifact unlocks *most*. Gate 2's claim falsifier is unrescued, and
the reframe remains unsupported.

**n = 4 versus 3.** Two of four row-2 artifacts are below 1.0 (RecipeTin 0.88, Steam guide 0.96).
The row means differ by 0.37 with per-artifact spread wider than that. This would not survive a
significance test and none was run.

**The choice to look here was post-hoc.** The measure was built after Gate 2 failed. What is not
post-hoc is the *direction*: E36 fixed the sign in a different codebase on different data before
this project existed. Predicting the sign in advance is the part that counts, and it was. Choosing
to test it after a failure is still the shape of motivated analysis and cannot be argued away.

**Unlock is trivially 1.0 where the posterior settles on the first pass.** Five artifacts sit at
exactly 1.00, and for those the measure says nothing — the "before" and "after" purposes were the
same. That subset is not random, and it includes both rich generated artifacts.

---

## §4. Where this leaves the three candidates

From `DIAGNOSIS.md` §6:

1. **The local arm is too weak** — still live, and now more testable: unlock is a within-reading
   measure, so the API arm can be spent on the artifacts where local unlock is ambiguous rather
   than re-running everything.
2. **The measures were wrong** — **partially confirmed.** Purpose was the wrong quantity, E36 said
   so, and switching to method moved the sign on both the new measure and the old one.
3. **The construct does not survive real artifacts** — **weakened but not eliminated.** It
   predicted no separation on real text in the right direction; there is some. It is small.

**The honest summary: this is the first measurement in the project that separates real makers from
commercial filler in the predicted direction.** It is also four artifacts against three, exploratory,
and does not save the claim falsifier.

---

## §5. What would make this real

A Gate 3 pre-registration, written before any further run, committing to:

- unlock as the **primary** discriminator, with purpose-side measures demoted to diagnostics;
- a corpus the measure has not seen — the seven robots-blocked artifacts are unusable, so this
  needs new sourcing;
- a stated threshold and a stated null, neither chosen after seeing these numbers;
- the API arm once, on that corpus, as the pre-registered replication.

**Until that runs, this is a promising direction and nothing more.** It may not be quoted as a
result, and Gate 2's failure remains the project's current standing verdict.
