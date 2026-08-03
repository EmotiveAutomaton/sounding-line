# Gate 2 — **F2.1 FAILED. The pre-registered stop condition fired.**

**Stated first, because the card requires it to be:**

> **F2.1 failing is a STOP condition for the reframe as stated.** It does not mean the instrument
> is worthless; it means SPEC §1's claim that a carefully directed model output ranks above
> undirected output is not supported, and every downstream document must say so before saying
> anything else.

Run 2026-08-03, local arm (qwen3.5:9b), k=3, 14 artifacts, family v2, card
`ba5dba173755`. Raw: `results/gate2/gate2_local_k3.json`, `scored.json`.

---

## §1. Scorecard

| id | kind | verdict | detail |
|---|---|---|---|
| **F2.1** | **claim** | **FAIL** | item A separated from item B on **1 of 5** tuple dimensions |
| **F2.2** | **claim** | **FAIL** | `artifact_effort` A=[2,1,3] B=[1,4] — overlapping |
| F1.1 | instrument | **FAIL** | named-alternative rate: row2 **0.28** vs row3 **0.42** — *reversed* |
| F1.2 | instrument | **FAIL** | purpose agreement: row2 **0.75** vs row3 **0.89** — *reversed* |
| F1.3 | instrument | PASS | machine-audience row3 0.05 > row2 0.03 (thin margin) |
| N8 | null | PASS | 5 distinct purposes, 5 distinct audiences — not scoring everything alike |
| N9 | null | PASS | row5 pre-2020 human machine-audience 0.12, below the 0.30 bar |
| N10 | null | **FAIL** | free-form separated the rows *better* than bounded (−0.06 vs −0.14) |
| N7 | report | — | mean length row2 10,486 chars, row3 5,587 |

**Five of eight criteria failed, including both claim falsifiers.**

---

## §2. SPEC §7's first named killer fired

The spec lists what would kill this project. First on the list:

> **Convergence tracks topic coherence.** A tidy spam farm is internally consistent. If the probe
> converges on garbage because the garbage is well-organised, **it is a quality classifier with
> extra steps.** Design against this from the first hour — the human-written-SEO corpus is the
> control that catches it.

**F1.2 is that, measured.** Commercial filler produced *higher* purpose agreement than real
makers' work — 0.89 against 0.75. The control caught exactly what it was built to catch.

The individual readings show why. The Eurogamer build guide and the Glad brand page both scored
agreement 1.00: they are tidy, single-purposed and internally consistent, and the probe reads them
the same way every time. LocalThunk's Balatro development timeline scored **0.33** — the probe
gave three different purposes in three runs for a solo developer's account of building his own
game, which is about as unambiguous a real maker as the corpus contains.

F1.1 reverses for a related reason: the plumber service-area template scored 0.67 on
named-alternative rate while the Balatro timeline scored **0.00**. The probe manufactures
counterfactuals more readily for formulaic text — where the genre's available moves are obvious —
than for idiosyncratic text, where they are not. **The counterfactual-enumeration mechanism, which
fixed the keyword problem at Gate 1, has its own failure mode: it works best where the genre is
most predictable, which is where intent is least present.**

---

## §3. What may legitimately qualify the F2 failure, and what may not

**The failure stands.** F2 was pre-registered without naming an arm, it ran on the local arm, and
it failed. That is the recorded outcome.

**A qualifier recorded BEFORE this run, in C-19:** the two arms do not measure the same thing.
H1.5 failed at Gate 1 on exactly this point — same locator, same prompts, same schema produce
grounding 0.34 and depth 2 locally against 0.80 and depth 4 on Opus 5. And the **API arm at Gate 1
separated A from B on 4 of 5 of these same dimensions**, including `artifact_effort` with no
overlap ([2,3,3] vs [1,1,1]) — which is F2.2 passing cleanly on the other arm.

So the position is: **the claim falsifier failed on the weaker of two instruments the project had
already documented as non-equivalent.** That is a real qualifier because it was recorded in
advance, and it is *not* a rescue because it does not make the failure go away.

**What may not be claimed:** that F2 "really" passed. It did not. One arm passed a similar
comparison at a different gate under a different criterion, and the other failed the
pre-registered one.

**The legitimate move, and the only one:** a single pre-registered replication of F2 on the API
arm, declared as a replication before it runs, with the local failure standing in the record
regardless of outcome. Not "run until it passes" — one run, declared, reported either way.

---

## §4. What this does and does not condemn

**Does not condemn:**
- N8 and N9 both passed. The instrument is not scoring everything alike, and it is not reading
  pre-2020 human work as machine-audienced — so the audience dimension is tracking something
  other than era or surface.
- F1.3 passed, though thinly.
- The reader, the fetcher, the isolation tests, the two-stage architecture: untouched by this.

**Does condemn, and this is the substantive one:**
- **`named_alternative_rate` and `purpose_agreement` cannot separate real makers from commercial
  filler on this corpus.** Both reversed. The measure the ablation pilot called "the sharpest
  discriminator available" discriminates in the wrong direction on real text.
- **N10 failing is worse than it looks.** Boundedness did not merely fail to help — free-form
  separated the rows *less badly* than bounded did. The ablation pilot's result does not
  generalise beyond the generated artifacts, exactly as N10 was written to detect.

---

## §5. Honest reading of where the project stands

The instrument reads artifacts reliably, returns interpretable four-part readings, and can be
inspected by a human. That is Gate 1 and it holds.

**What it cannot yet do is the thing it exists for**: separate artifacts by how much intent is
recoverable from them, on real text, in the direction the theory predicts. Two independent
falsifiers say so, one of them the spec's own first-named killer.

**The most likely candidates, in order, and none is established:**

1. **The local arm is too weak to carry this.** Supported by C-19 and by the Gate 1 API result.
   Testable in one run.
2. **The measures are wrong in a way that survives every fix so far.** `support` has now been
   rebuilt twice and inverted on real text both times.
3. **The construct does not survive contact with real artifacts.** Real makers' work is
   idiosyncratic and its available-moves set is not obvious; formulaic work advertises its own
   genre. If recoverable intent is systematically *harder* to see in genuine work, §1's reframe
   has a problem that is not a measurement problem.

**Candidate 3 is the one that would matter, and this run cannot distinguish it from candidates 1
and 2.** That distinction is the next real question, and it is a question about the theory rather
than about the code.
