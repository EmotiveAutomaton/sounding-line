# Implementation review of the October 14 commission

The requested direction is implementable in stages. Phase 0 is admitted to
implementation now; the full portfolio is not yet execution-ready. This review
keeps the supplied document unchanged and separates corrections to computation
from scientific decisions that still need validation. No desired weak result is
an acceptance criterion: strong individual signal must survive and be reported.

## Resolved in Phase 0

- Calibration has two levels of writer exclusion. Each outer writer is excluded
  from all fitting; stacking weights use inner out-of-writer predictions. Raw
  invalid responses remain in standalone system loss; a stack falls back to the
  existing partial-pooling baseline. Held-out labels never choose a temperature,
  class bias, EM prior, stacking weight or variant.
- The supplied EM-then-temperature path remains a separately reported arm.
  The reader's actual training class prior is unknown. Mean training predictions
  provide an explicit reference distribution; invariance of class-conditionals
  is an assumption, not a verified explanation of the raw bias. EM uses the
  unlabelled held-out maker batch and is therefore transductive, not online.
  A separately named bias-corrected-temperature arm tests class bias directly.
- Variance components use unequal cluster sizes and retain a negative untruncated
  between-maker estimate alongside its zero-truncated estimate. Writer-resampled
  intervals and a prompt-crossed gain sensitivity show uncertainty. Variance
  components do not identify causal preferences, and between-maker variance does
  not literally imply that additional decisions are useless.
- Prequential fitting requires a prior session to have ended strictly before the
  current session starts. Concurrent, tied and future sessions cannot train the
  model. Chronology exclusions and actual denominators are recorded; 16,959 and
  61 are source-census expectations, not forced analysis denominators. Both
  own-history and global-history prompt novelty are reported.

## Required before adaptive families

1. A posterior probability is not an e-value. e-LOND requires nonnegative inputs
   with null expectation at most one. Retain the adopted posterior futility rule,
   but validate a distinct e-value construction before promotions. No Phase 0
   bootstrap interval or posterior probability enters an e-LOND ledger.
2. Probability that an effect exceeds the useful margin and predictive probability
   of passing a later batch are different quantities. Implement the spec's primary
   pooled-effect rule; label predictive success as a separate sensitivity. Calibrate
   false kills over all allowed looks with independently generated Ghost validation
   sets, not the same simulations used to choose thresholds.
3. ASHA and Thompson allocation cannot silently turn compute pruning into scientific
   futility. Record every registered arm and missing batch; freeze intended support,
   selection and confirmation rules before launch.
4. Already exposed CoAuthor outcomes cannot become a virgin confirmation holdout.
   Freeze fresh temporal, maker and second-dataset confirmation support and its reuse
   ledger before adaptive inspection. Shared writers, prompts and calibration fits
   limit conditional bootstrap interpretations.
5. Engine pinning means actual implemented ToMpathy code at a commit, not just a
   document. At inspection, ToMpathy commit
   `d44aa862bd47b7d7ca7bddab2d23536e2254e24e` has no committed engine module.
   Sounding Line will not create a second product engine. Phase 0 reuses existing
   research baselines and makes no engine claim. Ghost twin admission is also
   required before the broader families; it is not presumed from a companion spec.
6. F6 must not score a purpose label supplied as an input. F8 cannot feed eventual
   text survival into an earlier forecast. F9 identification is not value recovery;
   no cross-dataset identity join or public identification model is admitted.
7. Dataset licenses, access and usable fields require direct verification when each
   adapter is built. No author messages, form submissions, gated-term acceptance,
   human recruitment or raw-data publication occurs in Phase 0.

## Timing, budget and disposition

Phase 0 is CPU-only and bounded before Friday October 16 at 10:00 PDT. Stage 14's
16:00 review and 18:00 joint packet remain. The thirteen broader families follow
the supplied week order and dependencies; a missing adapter or failed control
waits with a recorded reason. Repair triage distinguishes superseded cards from
unresolved questions. Old failures and cost remain in the original namespace.

Gear 3 is appropriate later for R3's schema-limited profile pilot, followed by an
admitted F4 slice. It offers no benefit for Phase 0. Before each future paid run,
record a cost forecast, fresh shared-ledger headroom and pilot gates, then dispatch
through the existing guarded path. The $44.52 remainder is shared, not a second
budget. B/C/D remain unavailable without the explicit future authorization stated
in the commission, even if a major-positive criterion is met.

## Method sources inspected

- [Xu and Ramdas, e-LOND](https://arxiv.org/html/2311.06412v1): inspected the
  e-value definition and arbitrary-dependence result; supports item 1, not the
  validity of a still-unspecified family e-value.
- [Alexandari et al., label shift and bias-corrected calibration](https://proceedings.mlr.press/v119/alexandari20a/alexandari20a.pdf):
  inspected EM updates, calibration methods and limitations. Label-shift assumptions
  and reference-prior misspecification matter; calibration is not evidence of mechanism.
- [Guo et al., temperature scaling](https://proceedings.mlr.press/v70/guo17a/guo17a.pdf):
  inspected validation fitting and scalar-temperature definition.
- [Yao et al., stacking](https://arxiv.org/html/1704.02030v3): inspected held-out
  predictive stacking and proper scoring. This implementation uses the declared
  half-Brier objective and two nonnegative weights summing to one.

The original spec's other citations are supplied references, not a claim that
this implementation pass independently read every cited work. Theory framing,
corrections and afterwords were refreshed before and after these method checks.
