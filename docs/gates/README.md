# The gates, reclassified: instrument gates and claim gates

**Amendment A-8.** The spec's gates are unchanged in content. What changes is what each one is
allowed to conclude — and the change is a *correction to my practice*, not a relaxation of the
spec's.

---

## §1. The error this fixes

`SOUNDING_LINE_SPEC.md` line 334:

> **Gate 1 — the bounded family exists and a single artifact can be read.** One page in, a
> four-part reading out, on a hand-picked example of each corpus type. **Success is
> *interpretable output*, not accuracy.**

And the next line:

> **Gate 2 — the falsifiers run.** Human SEO vs grooming, **and rich-prompted model output vs
> thin.**

**The rich-versus-thin comparison is a Gate 2 falsifier. I imported it into Gate 1 as C-18 and
then failed Gate 1 on it.** The spec says in as many words that Gate 1 is not an accuracy test,
and I made it one.

Consequences of that single error, all of which propagated:

- Gate 1 returned "cannot proceed" on a criterion that was never Gate 1's to run.
- C-18 ranked artifacts on a scalar, which SPEC §5 forbids independently.
- Three fit components were diagnosed as broken *by* a criterion that should not have been
  applied — the diagnoses stand on their own mechanics, but the framing that produced them was
  wrong.

**On its actual criterion, Gate 1 passes:** one artifact in, a four-part reading out, on every
corpus type available, interpretable, 9/9 valid on the API arm with agreement 1.00.

---

## §2. The distinction

Every gate is one of two kinds and the honest options differ.

**Instrument gates** ask *does the thing work*. Failure means fix the thing. Iterating until it
works is called engineering and is the correct response.

**Claim gates** ask *is the finding real*. Failure means the finding is not established, and
iterating until it passes is called p-hacking. Here a failure must be able to stop the project.

| gate | kind | asks | on failure |
|---|---|---|---|
| 0 — literature checked | claim | has someone built this? | stop or reposition |
| **1 — a single artifact can be read** | **instrument** | does it produce an interpretable reading? | **fix it** |
| **2 — the falsifiers run** | **mixed** | can it separate the pairs? | see §3 |
| 3 — boundedness ablation | **claim** | does bounded beat free-form? | **§2 of the spec is wrong; rebuild** |
| 4 — baselines and severity | **claim** | does it beat the alternatives, with a false-positive rate? | the contribution is not established |
| 5 — the corpus gate | instrument, then claim | does it run at scale, and does the weighting help? | fix, then evaluate |

---

## §3. Gate 2 is mixed, and the split matters

Gate 2 runs two falsifiers and they are different kinds:

- **Human SEO vs grooming** — *instrument*. If the probe cannot separate them, the measures need
  work. Nothing about the theory is at stake in whether a particular measure discriminates.
- **Rich-prompted vs thin-prompted** — **claim.** This is SPEC §1's entire reframe. If a
  carefully directed model output cannot be ranked above undirected output, the reframe has no
  empirical support and no amount of measure engineering fixes that.

**So Gate 2's second falsifier is the first place a failure is allowed to stop the project**, and
it must be run under claim-gate discipline: pre-registered, tuple-level, reported as failing if
it fails, and *not* iterated on until it passes.

Everything before it may be engineered freely.

---

## §4. The discipline that makes engineering legitimate

The failure mode of "treat it as engineering" is tuning until the answer is the desired one. The
line, and it is checkable in the commit log:

> **Fix for a diagnosed mechanism, never for a ranking. Write the diagnosis down before checking
> whether the fix helped.**

Every measure change so far satisfies this:

| change | diagnosed mechanism | helped the preferred ranking? |
|---|---|---|
| offsets → model quotes, code locates | models cannot count characters | n/a |
| exact → graded matching | light paraphrase scored as fabrication | yes |
| stage B → counterfactual enumeration | `support` detected the word "alternative" | yes |
| silence ≠ fabrication in grounding | wall and E2 collapsed into one number | n/a |
| **concentration is not fit** | **rewards single-purposedness** | **no — it explains why the preferred artifact ranked last** |

The last row is the important one. A change that diagnoses why the *desired* result did not occur,
and that would not have been noticed had the result gone the other way, is the signature of
engineering rather than rationalising.

**A change made because an artifact "should" score higher is a deviation and gets logged as one.**

---

## §5. What may be claimed today

- **Gate 1: passed**, on the spec's criterion. The instrument reads an artifact and returns an
  interpretable four-part reading.
- **C-18: fired, mis-specified, retained.** Both recorded, in that order, permanently.
- **Nothing about the theory has been tested.** The bounded-vs-free-form comparison has not been
  run. Until it is, the project has no evidence for or against its central architectural claim,
  and no result here may be read as either.
