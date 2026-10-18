# D2 primary dispatch

Historical launch record. The primary later completed after one exact-score
replay repair; [the full result](D2.md) supersedes its execution status.

**Question:** Does choice prediction improve when the offered suggestions are
more dissimilar?

**Method:** the [frozen implementation](../../../docs/design/stage-15/drive/D2_PRIMARY.md)
fits conditional choice probabilities on earlier sessions, selects one penalty
on calibration sessions and scores later sessions. Training-defined extreme
dissimilarity quintiles supply the registered log-score contrast. The full
pipeline also runs with fixed independent uniform choices as a control.

Eight targeted checks pass, including known answers, objective/probability
parity, chronological exclusion, future-label invariance, source mutation
refusal, saved-boundary yield, immutable reentry and fresh-process replay.
The first test invocation hit the restricted system temporary folder before
four fixtures could start; the workspace-local runs pass. No scientific attempt
was consumed by that fixture setup error.

Input authentication finds 12,196 observed selected menus and 41 eligible
chronological writer partitions. The primary weights writers with both extreme
quintiles; its final support is determined only after full execution. Intervals
condition on the fitted forecasts and training-defined bins. Producer scores
are covariates, not probabilities; predictive gain is not content specificity
or personal taste. The hierarchical Bayes extension remains separately gated.

The counted CPU dispatcher binds 32 source/input/test files, reserves one slot,
uses at most two numerical threads at below-normal priority and retains its
resource floors, forecast yield and retry limit. No GPU or paid call.
[Dispatch ledger](../../../docs/design/stage-15/drive/DISPATCH_20261017.json).
This launch record carries no scientific score or completion claim.
