# Stage 11: contribution reconstruction

The hypothesis that a contribution account improves recovery of recorded suggestion handling found no consistent support. We compared direct reading, contribution accounts and two cheap controls on 41 historical writing episodes, in two separately scored tranches. The account improved in two of four comparisons and worsened in two; the training prior beat every model and feature baseline on probability error. Correct handling guesses did not validate the richer creation histories.

The study is complete. Both frozen tranches finished under Gear 2, using one pinned
local Qwen 3.5 9B reader. These exposed human process records support descriptive
comparisons, not fresh confirmation. Each tranche has three connected dependency
components; no population interval or cross-tranche pooled score is asserted.

The table shows writer-balanced half multiclass Brier loss, a probability-error
measure where lower is better. Initial/extension contain 24/17 episodes and 14/13
writers. Artifact is the endpoint document; alternatives adds the before document,
offered menu and explicit differences. Prior and features are training-only rivals.
The last column is account minus direct; negative favors the account.

| Tranche | Evidence | Prior | Features | Direct | Account | Difference |
|---|---|---:|---:|---:|---:|---:|
| Initial | Artifact | 0.337035 | 0.671841 | 0.407068 | 0.413125 | +0.006057 |
| Initial | Alternatives | 0.337035 | 0.549281 | 0.448129 | 0.435536 | -0.012593 |
| Extension | Artifact | 0.254659 | 0.381920 | 0.337954 | 0.329185 | -0.008769 |
| Extension | Alternatives | 0.254659 | 0.410301 | 0.311669 | 0.422500 | +0.110831 |

The [full table](REPORT.md) includes all sixteen complete cells, accuracy, log loss
and invalid counts. [COMPARISONS.json](COMPARISONS.json) includes valid-only diagnostics,
writer/prompt spreads, token counts and latency for each cell. Infinite log losses
are retained. Four evaluation forecasts have invalid probability sums, all in the
alternatives-account arm; worst-loss scoring keeps them in the main comparison.
Five development forecasts also fail, and all eight discarded pilot calls pass.

The account costs 1.54–1.77 times the direct reader's server time across the four
comparisons. All 204 attempts remain: 164 evaluation, 32 development, eight pilot,
with no transport retries or partial remainder. Charged GPU service was 0.440201
hours of the four-hour ceiling; the 256-call and original elapsed deadlines held.
Total input/output tokens were 170,920/26,973. [INTEGRITY.json](INTEGRITY.json) retains
cost and phase dispositions. Inherited source exclusions remain binding; 543 further
opportunities were omitted by frozen sample limits, with zero context exclusions.

Open the private [reviewed contribution map](raw/contribution-map-reviewed-v2.html).
It contains six actual cases from six writers, forecasts first and logged handling
only after explicit reveal. The disclosed selection rule uses the first complete
tranche and includes correct recovery, confident error and ambiguity. No wholly
deleted/unlocated insertion existed in that eligible pool. All 49 proposed
operations in both views have source-based audit notes. Exact text, raw logs,
original forecasts and the original automatically audited viewer stay private and intact.

The audit distinguishes selecting text, editing elsewhere, editing the selected
text, and reviewing it. It includes a correct dismissal guess with unsupported
review claims, exact offered quotes assigned to a fictional narrator, and human
continuation misattributed as another model insertion. Some labelled edits are
formatting changes. None of these observations establishes depth of review,
expertise, proximal purpose, endorsement or values. The richer account remains a
set of inspectable hypotheses, not a validated whole creation history.

Twenty targeted Python tests and the synthetic end-to-end CLI rehearsal pass.
[Independent verification](VERIFICATION.json) reproduces all 290 sampled document
boundaries with a separate UTF-16 byte implementation and matches 64 score fields
exactly. All 204 responses reparse without new calls and all 54 source hashes match.
The reviewed viewer's actual script passes reveal/state tests. **Visual browser QA
remains unperformed:** this session has no connected browser surface. Source agreement
also remains distinct from an independent real final-document reference, which is absent.

Replay from the repository root, without model calls:

```powershell
./.venv/Scripts/python.exe -B -m runners.stage11.run report --verify
./.venv/Scripts/python.exe -B -m runners.stage11_packet
./.venv/Scripts/python.exe -B -m runners.stage11_review
./.venv/Scripts/python.exe -B -m runners.stage11_viewer_repair
```

The computational report and its original ready-for-review receipt are immutable;
this final report records the subsequent operator audit and interpretation (L390).
All six supplied theory amendments are applied. The original errata is archived,
its loose source deleted, and the unchanged Stage 11 specification filed. The
[local resource index](../../docs/TOOLS.md#stage-11-bounded-local-resource-check-2026-09-18)
covers seventeen checkouts. The requested historical July 31/August 1 notes were
not located in the bounded local search. No new tests were harvested from the wake;
there is no further automatic scientific dispatch.

Two questions for discussing the actual cases, without commissioning more work:

1. In Case 2, the writer keeps the offered sentence intact and develops the surrounding
   passage. Which recorded choice is worth attending to when understanding their contribution?
2. In Case 5, the reader incorrectly assigns a human continuation to the model.
   What additional context would let a contribution map distinguish deliberate uptake
   and development from mere continuation, without claiming to have measured review?

Separate analyst answer bank, offered as possibilities rather than curator conclusions:

- For Case 2: selection of the fragment; the subsequent human development; their relation
  within the resulting passage. Each can matter without equating time or edit count with contribution.
- For Case 5: the actual before/after process trace corrects attribution; a contemporaneous
  account of intent might bear on uptake; alternative selections could constrain the choice.
  The present logs alone do not establish the person's attention or understanding.

Precommit validity repair (OPS-S11-REPAIR1): the original viewer could hide
unlocated reference hypotheses after a passage click. The versioned viewer above
fixes this, with all 184 case/view/passage checks passing. Forecasts, source evidence,
semantic audits and scientific scores are unchanged. `FINAL_RECEIPT.json` remains
the original pre-repair receipt; its exact bound files are preserved privately.
`PRECOMMIT_RECEIPT.json` records the subsequent repair and publication checks.
