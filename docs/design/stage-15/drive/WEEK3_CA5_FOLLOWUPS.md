# CA5 follow-ups: fixed specifications and severity versus topic recurrence

The positive CA5 landing licenses these two first-generation follow-ups under
the [Week 3 packet](../week3/PACKET.md), section 0.3C. Each has an original
ceiling of 1,800 CPU seconds, including execution and independent replay.
Neither creates another generation of follow-ups. CA5.r is a separate card.
This document and the source modules freeze definitions before their outcomes.

The question is whether the observed recurring harm judgments survive ordinary
coding and split choices, and whether recurring overall severity accompanies
the recurring topic pattern. The interpretation remains perceived harm
judgments. Neither test identifies objective safety, independent values,
competence or a causal psychological mechanism.

Both cards authenticate the completed, freshly verified positive CA5 parent
and its exact source/codebook hashes. They retain all 123 released raters and,
separately, all 104 raters in the published quality subset. The original CA5
module is unchanged. Missing or duplicate person/item records fail admission.
Any rater without a same-group peer makes that entire specification unsupported;
no rater is dropped to repair support. Constant topic profiles contribute zero
and are counted.

CA5.s reports all twelve cells in the Cartesian product below. The table lists
each specification axis and all its permitted values; no cell is selected after
seeing its outcome.

| Axis | Frozen values |
|---|---|
| Unsure response | 0, 0.5, or 1; No stays 0 and Yes stays 1 |
| Item halves | Odd/even numeric IDs; first 175/last 175 in ascending numeric-ID order |
| Rater population | All 123; published quality subset of 104 |

Every judgment is retained under each coding. Numeric item order is not treated
as temporal order. A topic is usable for correlation only if it occurs in both
halves, determined entirely by item metadata. All 350 items still contribute to
each rater's half mean. Topic support counts accompany every cell. The statistic
is the original equal-rater mean Pearson correlation between centered harm-topic
profiles, minus its rebuilt permutation mean.

Each cell has 1,000 independent itemwise rater reassignments within the frozen
gender-by-race strata and 2,000 paired-rater bootstrap resamples. Seed 20261026
and all reference counts are fixed. Reassignment rebuilds the leave-one-rater-out
group/item mean and the centered profiles. Cells use the same deterministic seed
schedule to avoid adding arbitrary reference differences across specifications.
Per-cell intervals are unadjusted 95% intervals; all twelve permutation
probabilities additionally receive Holm adjustment. The summary declares that
all fixed specifications pass only if every cell has a positive interval and
an adjusted probability below .05. Failure of that summary is not a declaration
that every specification is null or negative; all cells remain visible.

CA5.m fixes the original Unsure=0.5 coding and odd/even item split. It reports
two distinct endpoints for each complete population:

1. Topic recurrence is the original mean within-rater correlation across
   centered harm-topic profiles.
2. Severity recurrence is the correlation across raters between their mean
   leave-one-rater-out group/item deviation in the two halves.

These endpoints use different statistical units and are never subtracted.
Severity can recur with no centered topic pattern; a balanced topic pattern
can recur with no overall severity. Both can also recur together. Those are
descriptive signatures, not a causal partition or a share of variance explained.
Non-detection of one endpoint is not evidence that its mechanism is absent.

The same 1,000 within-group/item reassignments rebuild both endpoints. The
2,000 bootstrap samples resample complete rater rows, conditional on the
observed group/item adjustment, as in the parent. For severity, the correlation
is recomputed on the same sampled raters for the real data and for every null
draw before taking the difference. Constant correlations contribute exact zero.
Four endpoint-by-population probabilities receive Holm adjustment; intervals
are per-endpoint unadjusted 95% intervals. A reported recurring endpoint needs
both a positive interval and an adjusted probability below .05. Unsupported
cells cannot acquire a positive finding through the family adjustment.

DESIGN CHECK: LESSONS sections 3–5 and CONTROLS sections 1–7 were reread. Known
constructions check exact group/item nulls, stable severity without topic
recurrence, stable topic directions without severity, coexistence and sign
reversal. Fifteen targeted checks pass, including parity with the original
profile construction, an actual assignment-reference positive control, the
severity bootstrap against an explicit loop, all fixed cells and populations,
complete replay, source/parent admission and altered-summary refusal. The first
test collection failed on a test-helper import; correcting its package-qualified
path resolved that collection issue without changing the analysis.

The private handoff is
`.agent-state/drive-20261025/choice-handoff/CA5_FOLLOWUPS_READY.json`.
It pins the source modules, constructed native fixture and exact corpus inputs.
The owner must run native validation and admit measured costs before dispatch.
No corpus run or native launch has been performed by this builder. The parent
used 95.5 CPU seconds for execution plus replay; six complete specification
analyses forecast about 573 CPU seconds before a conservative timing margin.
That comparison is a forecast, not an actual measurement of either follow-up.
Outputs are aggregate only; no participant text, identities or profiles are
written to the report.
