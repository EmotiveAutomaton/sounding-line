# The 342-feature sweep — ~100 features rank the ladder, and B1 splits along human/machine

**2026-08-05.** LFTK + BiberPlus + TextDescriptives over four corpora, three forms each
(whole-document, windowed mean, windowed coefficient of variation), everything under
Benjamini-Yekutieli.

---

## §0. A bug in my own verdict, caught before it was reported

The first run printed `gate3 cv-only: 15 <<< B1 HAS SOMETHING`. **That number was meaningless.**
Survivor lists were capped at 25 for readability and the set comparison used the capped lists, so
"cv-only" was comparing *top-25 orderings*, not survivor sets. Fixed to compare full sets, and a
`mean` control added — `mean` uses the same windows as `cv`, so anything `cv` finds that `mean` also
finds is a windowing effect rather than a variation effect. The corrected number is **7**.

---

## §1. The ladder is massively separable — and this is not yet good news

| corpus | n | form | tested | uncorrected p<.05 | expected by chance | **survive BY** |
|---|---|---|---|---|---|---|
| **ladder** | 50 | whole | 332 | 169 | 16.6 | **89** |
| | | mean | 322 | 177 | 16.1 | **96** |
| | | cv | 322 | 36 | 16.1 | **1** |
| **ladder2** *(held out)* | 100 | whole | 337 | 179 | 16.9 | **121** |
| | | mean | 328 | 185 | 16.4 | **135** |
| | | cv | 328 | 48 | 16.4 | **0** |

**About a hundred off-the-shelf linguistic features rank the five rungs after correction for
multiplicity, and it replicates on a held-out ladder at higher n.** The strongest are pronoun rates,
auxiliary-verb rates, subordinating conjunctions and adjective density — `lftk_a_pron_pw`,
`lftk_a_aux_ps`, `lftk_n_sconj`, `biber_PRP`, `biber_THATD`, down to p ≈ 1e-11.

**Why this is not a result yet, and the reason is specific.** The survivor list is dominated by
**pronoun and person features**, and 22 of the 30 prompt specifications mention *the reader* or
*someone*. `you_rate` was already measured as prompt-contaminated at echo rho = +0.320. **The single
most likely explanation for this entire list is instruction echo**, and the ladder also carries a
structural length confound at rung-vs-length +0.40 in both halves.

> **Nothing here is adopted until it clears the echo check, the length control and the transfer
> test.** That is the whole point of having a battery, and this is exactly the shape of result that
> has died nine times in this project.

## §2. B1 — the within-artifact variation, and the answer is not simple

**The headline the data supports:**

| corpus | kind of text | whole | mean | **cv** | cv-only |
|---|---|---|---|---|---|
| ladder | machine | 89 | 96 | **1** | 0 |
| ladder2 | machine | 121 | 135 | **0** | 0 |
| gate3 | **human** | 76 | 71 | **20** | **7** |

**Coefficient of variation finds essentially nothing on machine text and something on human text.**
Zero and one survivor across 150 machine artifacts; twenty survivors on 35 human ones, seven of which
neither whole-document form finds.

**Two readings, and I cannot separate them with this data:**

1. **B1's mechanism.** *"The performance is what costs something, so the performance is what slips."*
   A machine has no veneer to slip — it generates uniformly — so within-artifact variation should be
   near-zero on the ladder and present in humans. **That is exactly the pattern.**
2. **Register.** Gate 3's halves are essays/technical against commercial web copy. Those genres differ
   in *how much they vary internally*, and cv would pick that up without any maker being involved.

**Reading 2 is the more likely one and it should be assumed until excluded**, because §3 shows the
Gate 3 split is a register split.

**What the ladder can and cannot say.** It is worth being explicit that **the ladder cannot test B1
at all.** B1 is a claim about a human performance decaying under cost. Every ladder artifact is
machine-written, so a null there is not evidence against B1 — it is the absence of the thing B1 is
about. The ladder result belongs in the record as a *baseline*: cv is near-silent where no maker is
performing.

**Status: B1 is NOT settled, and it is now sharper than before.** The test it actually needs is
within-artifact variation across human artifacts **with register held constant by construction** —
which is the corpus we do not have, and which `TODO.md` now points at ArgRewrite v2 for.

## §3. Gate 3 — 76 features separate the halves, and that is a negative result

`whole` finds **76** features separating half A from half B under BY correction, at p down to 1.9e-6:
stopword rate, auxiliary rate, adverb rate, pronoun `it`.

**This is not evidence that Gate 3 measured something.** It is the opposite:

> **The two halves of the Gate 3 corpus differ so broadly on ordinary linguistic features that
> almost any measure would separate them.** Separating them was never evidence of depth, intent, or
> anything else. It was evidence of genre.

That independently confirms C3 (commercial copy sits 26% of the way toward machine text, p = 0.0033)
and it confirms the curator's own suspicion, recorded on day two before any of this:

> *The corpus split may not exist... G3.1 may be looking for a boundary that is not there in the
> shape the card assumes.*

**Gate 3's VOID verdict stands and is now better supported.** It was void because its statistic was
undefined; it is *also* void because its populations differ on everything.

## §4. What did not run

**The no-maker N28 test was skipped.** The cached corpus has three kinds (thin/rich/averaged) and
tsfresh's relevance table needs a two-class target, and the comparison that matters — human against
no-maker — needs the two corpora pooled with a binary label. That is a runner fix, not a finding, and
it is the most important missing cell in this table: **342 features have not yet been asked whether
they move where there is no maker.**

## §5. Consequences

| | |
|---|---|
| **~100 ladder features** | CANDIDATES. Owe echo, length and transfer. Pronoun dominance makes echo the prime suspect |
| **B1** | not settled. Sharper: cv is silent on machine text and active on human text, and register is the leading alternative explanation |
| **Gate 3** | VOID confirmed on a second, independent ground — the halves differ on everything |
| **the feature libraries** | they work, they find things, and the correction machinery does its job. The gap between uncorrected (169–186) and corrected (76–135) is the multiplicity problem made visible |
| **N28 on 342 features** | **not run, and it is the next thing** |
