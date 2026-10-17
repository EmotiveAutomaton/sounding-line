# October 16 drive packet: implementation review

**Recommendation: proceed after targeted amendments.** The proposed research
direction is implementable. The shared measurements and measured-shape exports
can support several useful questions without waiting for engine promotion.
Several controls, evaluation definitions and resource estimates need correction
before the affected studies launch. These are not reasons to abandon the program.

**Status: assessment only.** The curator asked to review the incoming packet and
return issues. No campaign, download, model call or companion message was launched
by this review. The packet's embedded handoff authorization does not replace that
current request. Existing study gates and authority remain unchanged.

Reviewed source: workspace-root `SOUNDING_LINE_DRIVE_PACKET_2026-10-16(1).md`,
revision 2, all 974 lines; SHA-256
`d9261c5e93c91adc21ef9db79a6047581a178614f2ecef13d854b9d57338886c`.
Line references below address those exact bytes. Review date: October 16, 2026.

Method: compare the complete packet with current Stage 15 records, the Phase 0
and Stage 14 baseline/API/budget code, the UTF-16 CoAuthor replay, current Ghost
twin input consumers, the relevant theory and controls, and official model,
provider and corpus documentation. This is an implementation/design review, not
a new data analysis. The packet's corpus counts and simulation power claims were
not independently reproduced here.

## Amend before the affected launch

1. **Freeze how paid features are trained and evaluated, not just the baseline.**
   P4 and G3-A (lines 171–175, 785–811, 823–827) define a frozen free-feature
   model and then compare it with a model augmented by paid features. They do not
   specify the augmented model's fitting/calibration split, refit rule, or the
   evaluation cohort at each look. Training that model on the same outcomes used
   for its gain would make the stopping rule optimistic. Random labeling order
   must also remain separate from chronological prediction order.

   Freeze a common source/target roster, chronological training/calibration/test
   partitions, tuning rule, session weighting, invalid-response handling and
   out-of-sample predictions for both arms. Keep later sessions out of earlier
   features and fits. Specify whether gains cover all writers or only eligible
   writers, with support floors. The existing Phase 0 nested writer fitting is a
   useful pattern, not automatic validation of the new augmented model.

   The proposed futility thresholds can be used as resource decisions once this
   is fixed. A z statistic of −0.5 is not strong evidence of a negative effect;
   z below zero is not evidence of absence. The quoted 77% power and 4.6% false
   positive rate belong to the supplied simulation, not yet to repeated sessions
   from these writers. Retain its code and assumptions; validate the actual
   clustered, fitted procedure before attaching those operating characteristics.
   G3-B's agreement expansion and G3-D's identification gate need their own named
   decision rules: neither has the universal half-Brier statistic in section 5.

2. **V1 does not currently create a null world for every listed pipeline.**
   Lines 284–294 redraw handling outcomes while retaining real process features.
   Keystroke and decision-timing identity can remain intact. D16 could therefore
   correctly identify writers in the supposed null world. This would be falsely
   counted as a test failure. Likewise, observed prior handling and content
   histories can retain information inconsistent with the simulated history.

   Split V1 by target: outcome-prediction injection, process-identity injection,
   and text/adaptation injection are different constructions. Regenerate all
   outcome-derived lags recursively, including the last-three-choice habit term;
   refit affected models. For four-class half-Brier the known gain is
   `0.5 * mean(sum((q - p)**2))`, rather than the scalar binary expression unless
   a binary target is explicitly chosen. Ten worlds per grid point support a
   coarse diagnostic with wide binomial uncertainty, not precise false-positive
   calibration or a well-resolved 80% recovery boundary. Do not use successful
   recovery of these particular injections to conclude all real weak signals
   belong to writers rather than to untested instrument limitations.

3. **Specify common text units and feasible context windows for P1/D21.**
   Lines 139–148 request the whole preceding document and compare token surprise
   across different tokenizers. Tokens are not shared observation units. Pythia
   410M's official configuration has a 2,048-position context, so the requested
   whole-document condition is not guaranteed to fit. Longer writer-history
   conditions also need an explicit packing rule.

   Pin tokenizers as well as weights; align scores to common text spans, preserve
   native token scores, and choose a declared common-unit normalization. Freeze
   context budgets, prompt/history order, target-token masking, overflow handling
   and comparable-row eligibility. Never silently label a truncated context
   "whole document." Measure token counts and throughput before promising the
   three-to-five-hour runtime. Residual inter-reader disagreement is disagreement;
   it is not automatically noise or a measured information-support gap.
   [Official Pythia configuration](https://huggingface.co/EleutherAI/pythia-410m/blob/main/config.json).

4. **Keep native measurement validity separate from predictive utility.**
   P3's blind agent labels are explicitly disclosed, which is appropriate.
   G3-B also correctly says agreement is not truth. Nevertheless, constructed
   batteries plus agreement do not establish native accuracy of register, edit
   intent, contradiction or claim change. A feature can improve handling
   prediction while measuring something other than its assigned meaning.

   Before D14/D22 make goal-protection claims, freeze a question-specific native
   reference sample, annotation provenance, ambiguous-case policy, category-wise
   error report and action on failure. Use labels independent of the reader under
   evaluation. Agent references can support a bounded diagnostic but must retain
   their limitations. The packet's fallback to meaning-change versus fluency when
   style/coherence fail is useful; give that fallback measurable eligibility
   criteria before looking. Derive "protected variables" on separate sessions
   from those used to score their restoration. Preserve the distinctions in
   [native readiness](F4_NATIVE_READINESS.md).

5. **Repair D6's exposure assumptions and several claim-to-test mappings.**
   Independence of display position from one model-probability score (line 342)
   does not itself establish randomized assignment. Verify the actual assignment
   mechanism and its applicability to the released sessions. More directly,
   "unhovered = unseen" (line 350) is unsupported: the original interface allowed
   arrow-key navigation and Enter selection. Reading also need not move a pointer.
   [CoAuthor paper, section 4.2](https://cs.stanford.edu/~minalee/pdf/chi2022-coauthor.pdf).

   Combine keyboard and pointer events, distinguish highlight from examination,
   and retain uncertainty about exposure. Test sensitivity to plausible exposure
   models. Verified randomization could identify a display-position effect, but
   does not by itself separate attention, default-selection and preference.

   Preserve the other theoretical questions while making their readouts honest:
   decision latency alone is not uniquely cognitive identity (D16); declining
   exploration does not itself measure narrowing uncertainty (D23); the ten-minute
   finish-button threshold does not isolate drive devaluation (D24); restoration
   after editing does not alone establish a controlled internal set point (D14).
   These can yield useful descriptive constraints with their rival explanations
   retained. The exploratory label does not supply missing identification.

6. **Fix two mathematical readouts before they become shared infrastructure.**
   V2's binning residual (line 113) includes within-bin forecast/outcome covariance,
   not merely forecast variance. For binary outcomes it is the weighted sum of
   `Var(f | bin) - 2 * Cov(f, y | bin)`. Its sign need not be positive. The
   small-bin correction at line 120 divides by zero for singleton bins and has
   assumptions affected by repeated decisions. Declare bin merging, cluster
   handling and whether the corrected decomposition still closes; retain the raw
   exact score and reconstruction residual separately.

   D27's ratio of AUCs or R-squared values (line 331) is not the fraction of
   process information retained. Chance AUC is 0.5; held-out R-squared can be
   negative. Report each target's out-of-sample prediction and improvement over
   its baseline, with uncertainty. Do not label the ratio an information share.
   This preserves the question about what a page retains without building a
   misleading percentage into the answer.

7. **Reconcile the cloud fallback with its cap and account limits.**
   The quoted Haiku and Sonnet batch prices are current:
   [official Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing).
   The $60 hard campaign ceiling and separate approval beyond $10 are implementable.
   They do not guarantee all branches fit.

   The L40S price is $0.000542/second. Nine hours is $17.56 for the GPU alone,
   or $24.59 with the packet's 1.4 safety factor, before CPU, RAM or storage.
   Using the existing adapter's two physical CPU cores and 32 GiB adds enough to
   reach about **$29.00 with that factor**, exceeding G3-F's $25 cap. This is a
   calculation for that resource configuration, not a measured fallback runtime.
   [Official Modal prices](https://modal.com/pricing).

   Keep the cap and shorten the admitted workload after a measured pilot, or
   explicitly revise the allocation within the total ceiling. Count all API
   requests and tokens first. Define the first-$10 path if Haiku fails and the
   fallback must precede any useful literal pass. Recheck account-wide headroom
   across campaigns; a new campaign identifier does not reset provider limits.
   Each fallback question must bind a passing prompt/parser/model/runtime identity;
   the separate Qwen label-contract candidate cannot borrow original-Qwen admission.

## Implementation details that need no new research decision

- **S0 is useful and matches a real dependency.** Ghost's current status still
  holds T1–T4 on measured inputs and module gates. Its consumer checks the retained
  source file's bytes against the supplied hash. Ship the exact reference and
  source-artifact mapping, not only four unattached JSON summaries. The packet
  correctly anticipates T2's `seconds` versus `values` mismatch. These exports do
  not repair the separately failed profile witness or admit product modules.
- **Finish the dependency graph.** D16 uses V3, which uses D15, in addition to
  D17/P2. D22 needs D14's vectors before its high-ranked analysis. Prioritize those
  prerequisites explicitly. Share P4/D1's baseline code and frozen inputs instead
  of fitting two subtly different baselines.
- **Reuse the current replay.** `runners/stage9/coauthor.py` already implements
  UTF-16 deltas and persistent insertion provenance. Extend it in a new version
  with known-answer fixtures for timing and final-span origins. Multi-character
  inserts, paste, waits and timestamp precision must not become invented individual
  keypresses. Internal replay consistency is not an independently observed final page.
- **Bound corpus acquisition and inference separately.** September's standard
  Lichess archive is 29.2 GB compressed and contains about 89.6 million games.
  A downloaded month is not an inference-size specification. Freeze the 100-player
  cohort, eligible games, per-player/per-week support and game/position caps; stream
  parsing and budget disk usage. Likewise bound full Wikipedia histories and count
  eligible labeled edits and promotion events before promising costs or runtime.
  [Official Lichess database](https://database.lichess.org/).
- **Make the adaptive rule reproducible.** Each local card needs one named primary
  contrast and predicted direction; several currently have multiple outcomes.
  Distinguish the three-hour implementation budget from an analysis look. Preserve
  the initial sample and extension separately, report all attempted specifications,
  and label ordinary intervals as exploratory and not selection-adjusted. If an
  open-ended branch uses e-values, specify its valid construction and dependence
  assumptions; changing the statistic's name is insufficient.
- **Reconcile timetable and resource priority.** Section 7 says "to Thursday" but
  the dates specify Tuesday October 20 reporting and Wednesday October 21 freeze.
  Use those explicit dates after correcting the heading. Prioritize Sounding Line
  through resource coordination; do not terminate other projects' owned workers.

The first implementation tranche should be the bounded aggregate exports, replay
validation, corrected shared statistics and source/context census. Those establish
the prerequisites for the high-ranked questions. Resolve the seven amendments in
the frozen cards before their dependent analyses or paid reservations. No change to
the core theory or abandonment of a proposed research family is required by this review.
