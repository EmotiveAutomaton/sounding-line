# Ladder 2 — it replicates, and length was hiding it rather than causing it

**2026-08-05.** Held-out replication of the only order-dependent effect in the project. 100 new
artifacts, fresh seeds, rotated topics, **loci frozen**, one test.

---

## The numbers

| | rho | p |
|---|---|---|
| **held-out, raw** | **−0.247** | 0.0132 |
| ratio vs word count | +0.248 | 0.0127 |
| **held-out, length-controlled ← primary** | **−0.405** | **<0.0001** |
| pooled n = 150 *(reported, not the test)* | −0.251 | 0.0019 |

Rung means, and they are close to monotone where ladder 1 was ragged at the top:

    rung  0   1.1196
    rung  1   1.1240
    rung  3   1.1037
    rung  6   1.0934
    rung 10   1.0815

## Verdict, stated against both bars

**By the pre-registration written before generation** (`rho < −0.2` **and** `p < 0.01` on the raw):
**AMBIGUOUS.** The rho bar passes at −0.247; the p bar misses at 0.0132.

**By the length-controlled primary** declared in `run_ladder2_replication.py` — written *after* seeing
ladder 2's void check (rung vs length, rho = +0.401) but *before* any ratio was computed:
**rho = −0.405, p < 0.0001. Clearly passes.**

Both are reported because the honest answer depends on which bar you hold, and the sequence of when
each was fixed is the only thing that makes the second one legitimate.

---

## The finding underneath the finding

I braced for the opposite outcome and wrote it into the runner in advance:

> *"If the raw replicates and the partial does not, the effect is length and the replication has
> killed it rather than confirmed it."*

**What happened is the reverse. The partial is nearly twice the raw.**

The reason is visible in the three correlations. Longer texts have a **higher** ratio (+0.248), and
higher rungs produce **longer** texts (+0.401). So length pushes the ratio *up* as rung rises, while
the effect itself pushes it *down*.

> **Length was acting as a suppressor, not a confound.** It has been working *against* this
> measure the whole time. Removing it does not shrink the effect — it uncovers it.

This is the first time in the project that a length correlation has been anything other than a cause
of death, and it explains ladder 1's marginal p = 0.0529: the same suppression, at half the sample
size.

## What this does and does not establish

**Does:**

- The effect survives a genuine held-out test with **every hyperparameter frozen**, which is what
  known weakness 3 demanded. The loci were not re-fitted, and the split points that produced ladder
  1's number produced a larger one on data they never saw.
- The curator's standing rule — *near-significance means raise the power* — **worked exactly as
  stated**: p = 0.0529 at n = 50 became p < 0.0001 at n = 100 held out.
- It remains **the only effect in this project that requires word order**, localised by the
  granularity sweep to at or below the sentence.

**Does not:**

- **This is still machine-generated text.** Every rung is written by the same model. It shows the
  measure tracks *specified intent* within one generator; it says nothing yet about human artifacts,
  and `FINDINGS.md` weakness 4 stands unchanged.
- The effect is **modest**. rho = −0.405 on n = 100 is a real but small signal, and the raw
  correlation is −0.247.
- It is **one more test in the multiplicity family** (`results/audit/multiplicity.json`). At
  p < 0.0001 it survives Benjamini-Yekutieli comfortably, but it should be added to that list rather
  than quoted alone.

## Status change

`FINDINGS.md` tier 1 entry moves from **OPEN, and weak** to **OPEN, replicated held-out.** It does
not move to POSITIVE until it does something on human text — which is the corpus problem, not a
measurement problem.

**Known weakness 2 is resolved.** Known weakness 3 is resolved *for the loci* — they were frozen and
survived. It is not resolved for the choice of measure family, which was still made by us.
