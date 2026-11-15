# LA6: before a laugh

Status: runnable source and analysis handlers, array primitives and constructed
checks prepared. No participant table was read or fitted during this build, and
no native production run is admitted. Authority is
[the supplied packet](PACKET.md), section 3D. Its inherited LA family allowance
is 450,000 CPU-seconds under the [execution addendum](EXECUTION_ADDENDUM.md); this document
does not create a separate allowance or alter live workers.

## Frozen question and table

Predict whether an utterance is followed by a prepared laugh label from its act,
words and prior context, with meetings held out. The primary is area under the
receiver-operating curve against 0.60. No act direction is registered. Report
act-type odds and meeting-cluster intervals, both with and without elapsed time
since the last laugh. Laugh clustering is a by-construction caution, not evidence
of a new trigger. Tags: `H18-S5`; record kind `claim`; eventual activation is
empty until an admitted result changes the record.

Use the existing qualified LA source and its label definition, preserving its
source and completion pins. The in-memory boundary requires every prepared
utterance's meeting, speaker, stable ID, start/end, laugh-safe text, act type and
boolean label, plus the identically scoped laugh-event table. It rejects duplicate
IDs, nonboolean labels, invalid times and absent speaker/act data. No model scores
or demographic fields are read.

The older LA matching helper cannot be reused: it matches on act type and length,
which would remove two requested predictors. The new match is the nearest
nonlaugh utterance by the same speaker in the same meeting, at least 30 seconds
away by start time. A tie uses earlier start then source ID. Matching is with
replacement because the packet gives no uniqueness constraint; reused controls
are reported and remain in their original meeting. Every unmatched case keeps
its disposition. Cases are never selected by their predictor values.

## Features and estimator

The nine numeric fields are the original parser's word count (not a new
alphabetic-token count), change of speaker from the last completed
utterance, unique-word overlap with the last two completed utterances divided by
the current utterance's unique-word count, any repeated word of the most recent
different speaker, first-person singular, negation, a question mark, tenth of the
observed utterance span, and seconds since the last completed laugh. The first
observed utterance time substitutes for the last-laugh time when none precedes
the row. This no-prior-laugh convention is explicit and uses no future event.
Missing previous utterances contribute empty overlap; overlapping unfinished
utterances cannot enter history. Act type is categorical. The source label itself
and laughter annotations never enter the predictors.

`runners/drive/cards/week6_la6_v1.py` uses five deterministic meeting-disjoint
folds (fewer when fewer meetings exist). All categorical encoding and numeric
scaling are trained on each fold's training meetings. Unseen acts receive the
reference coding; folds and their actual meetings are retained. Logistic fits
use fixed L2 regularization with C=1, no tuning, and raise on convergence warnings.
Act odds are therefore regularized descriptive odds relative to the alphabetic
reference act, with that convention reported rather than hidden.

The prediction interval resamples complete meetings over frozen held-out
predictions. The act-coefficient intervals refit the logistic model in each whole
meeting draw. A draw lacking an act invalidates the act intervals; it is never
redrawn. Two thousand draws are required for native primary inference. Single
meetings receive no population interval; fewer than 20 meetings stay descriptive.
The array fixture may request fewer draws and never qualifies primary inference.

## DESIGN CHECK

LESSONS sections 2 and 3 were read. With one binary act present in one fifth of
controls and one third of cases, the analytic odds ratio is 2 and area is 17/30.
This fixture intentionally does not clear the primary bar: successful ruler
recovery cannot be confused with a positive primary. Equal feature distributions
must give exactly one half. Strong separation must be able to clear the bar.
Constructed timestamp cases check the 30-second boundary, speaker/meeting
restriction, deterministic ties, reuse, completed-history rule and immunity to
future laugh events. Distinct meeting folds and source-identity failures are
asserted. Bootstrap checks exercise both feature arms and the one-meeting guard.

If source support is insufficient, keep the case/control census and pooled
description with the exact unsupported reason. A rank/convergence/data failure
is an instrument event, not a null. A cost excess uses the inherited whole-meeting
sample route with its frozen selection and sample-scoped report; it cannot select
individual utterances after outcomes.

## Runnable handlers and exact source

The qualified source root is
`results/phase_2_4_stage_15/raw/drive-week5-20261107/LA-source/`, produced by
`runners.drive.cards.week5_la_source`. Its inspected COMPLETE receipt is SHA-256
`a213dbbb23eaf6524c2a08b90726a24d25ac578deed52a71ca279c0a1eae05b0`; COMPLETE and
VERIFIED metadata report fresh verification. The manifest pins are:

| Table | SHA-256 |
|---|---|
| `output/ACTS.json.gz` | `46cde8e75a429e89224fdab746c237f6f0f2f5d68d624d2835b94a7b9d6d46cd` |
| `output/LAUGHS.json.gz` | `44c7fcde05eb02e19a67f84765c6b00133d0cd8e9ebf176daf896b4f8f98ff3f` |
| `output/METADATA.json.gz` | `25c409123b943cb982b2f5f804741f7211fd5afec436e92c2f40a51c0798df47` |

Only receipt identities were inspected in this build. The source handler hashes
the actual tables at execution and inherits the original parser-code pins via
`week5_la_prepare_v1.bound_source`.

`runners.drive.cards.week6_la6_source_v1` supplies `execute`/`verify`. It rebuilds
the original vocal/all-speaker labels with the unchanged one-second-left,
two-second-right rule over every original utterance, including early utterances
with empty history. It never reads LA1's history-truncated scoring batches.
Meeting checkpoints retain all features, matches and unsupported dispositions;
verification reconstructs the source in a fresh checkpoint namespace.
Inputs: `source_root` at the exact root above. Configuration:
`{"phase":"LA6-prepare","max_new_meetings":8,"max_wall_seconds":600}`.

`runners.drive.cards.week6_la6_runner_v1` supplies bounded `execute`/`verify` for
both feature arms and all 2,000 draws. Inputs are `prepared_run` and `owner_review`.
`review_contract()` binds the owner-written receipt to the preparation COMPLETE,
source adapter, mathematics, runner and stated conventions. No approval receipt
has been written by the builder. Configuration:
`{"phase":"LA6","draws":2000,"max_new_draws":10,"max_wall_seconds":600}`.
Replay reconstructs every draw with the frozen solver. Independently derived
analytic AUC/matching checks are fixtures; a second native optimizer is not claimed.

## Verification, repairs and remaining admission

### Inherited-control audit, before admission

[Week 3 section 0.5](../week3/PACKET.md) requires a null that can fail each
measure, at least 200 within-writer permutations, and at least 1,000 writer-label
permutations within prompt for reliability and identification nulls.
[Week 4 section 0.5](../week4/PACKET.md) repeats the 200-permutation default.
[Week 5 section 0.6](../week5/PACKET.md) carries Week 4 defaults under its
CoAuthor-timing clause and makes meeting the LA cluster. On review, the owner
confirmed that this restricted carry-forward does not impose the older generic
permutation minimum on the new LA6 card. LA6 has its own constructed-null
fixture. The earlier builder audit incorrectly promoted that generic minimum
to an additional admission gap; this paragraph corrects that reading before
any human run. Q, U and AA do not waive a scientific control that actually
applies, but no waiver is needed for a rule outside this source's contract.

This table separates implemented controls from optional unimplemented references.

| Requirement or control | Exact implementation or remaining gap |
|---|---|
| Frozen labels, same-speaker/meeting matching and 30-second separation | `week6_la6_source_v1.project_meeting` and `week6_la6_v1.match`; every original qualified utterance is considered and reused controls are counted. |
| No future context; both laugh-history arms | `feature_rows`, `held_out`, and runner `point`; only completed earlier context enters, and both registered arms are fitted. |
| Meetings held out, training-only encoding and scaling | `held_out`; all copies of a reused control remain in one meeting fold. |
| Whole-meeting uncertainty | Runner `one_draw` and `summarize`: all 2,000 draws, frozen held-out predictions for area and refitted act odds. |
| Known-answer alternative and null | Constructed analytic odds/area, identical-distribution null, separation and leakage fixtures. These do not constitute permutations of the empirical table. |
| Within-unit permutation sensitivity | **Optional, not implemented; not an inherited admission gate.** Any future version must freeze a defensible meeting/speaker exchangeability argument and transformation. Reused source utterances cannot receive inconsistent labels in separate matched copies. |
| At least 1,000 label permutations for reliability/identification | LA6 estimates predictive separation and act odds, not reliability or person identification. That specific clause has no direct LA6 target. This does not waive the separate within-unit null audit. |

LA3's fresh/repeat shuffle and LA4's background-label permutations are different
targets; they do not define LA6's control contract. A whole-meeting nonwrapping
time-shift reference was proposed to preserve laugh clustering, with a fixed
interior utterance window, recomputed labels/history/matches and full fold refits.
It is optional and unimplemented. Without a justified stationarity argument it
would be a descriptive temporal-alignment check, not an exact permutation test;
no new threshold or primary-population restriction is adopted. The current
review receipt does not attest this optional reference. Its absence is not a
remaining admission gate. The required source review, constructed fixture and
ordinary owner/runtime admission remain as stated below.

The final changed-source suite passed 24 constructed checks. A subsequent
nine-check source-wrapper pass verified the final DC1 roster contract and the
unchanged LA6 source/wrapper checks. Receipts, source hashes, process identity,
CPU/wall usage and exit codes are retained under
`.agent-state/drive-20261115/week6-builder-c-checks/`. Every run used two numerical
threads, a unique basetemp and disabled pytest caching. These are direct fixture
calls, not newly launched native research jobs.

An identical bootstrap bank initially exposed mean-rounding residue. The failed
receipt remains; dispersion now centers on its first draw so exact identity is
exactly degenerate, with no threshold or tolerance change. A source review also
replaced alphabetic recounting with the original parser's word count, including
nonalphabetic tokens, and added a regression check. First-utterance retention,
source-byte mutation, owner-review refusal and bounded execute/verify all pass.

Remaining: owner source/label/span and C=1 convention review;
committed design, any required full native qualification, versioned Week 6 runtime
admission and in-slot cost measurement. No human LA6 estimate or production
approval follows from these checks.

### Reporting correction and current-byte check

Before admission, the owner found a generic reporting mismatch: the old LA6
summary used `below bar` as a fourth outcome and included equality in support.
The revised reporting layer uses the Week 5 three-way rule on the unchanged
raw area scale: support requires the entire interval strictly above 0.60;
an interval wholly at or below 0.60 is against; the remainder is inconclusive.
Below-floor and degenerate cases instead have a descriptive `status` and no
scientific `outcome`. Every estimator, draw, contrast and numerical bar remains
unchanged. The previous code bytes and manifest are retained privately under
`CLASSIFIER_PRE_REPAIR/`, beside all earlier test receipts.

The new `tests/test_week6_outcome_labels_v1.py` passed 22 interval-boundary and
small synthetic-summary checks across LA6 and DC1. It fits no model and repeats
no earlier full numerical bank. `BUILDER_C_LABEL_TEST_RECEIPT.json` binds the
current reporting-code and fixture bytes; nonreporting function ASTs were
unchanged. Its wall/exit record is complete, but its CPU field measures only the
Windows launcher. `BUILDER_C_LABEL_ACCOUNTING_NOTE.json` preserves this limitation;
the launcher value is not a total preparation charge. The owner-review inventory
binds current code, design and fixtures to these retained receipts.

### Cost forecast and pilot boundary

No human-source timing measurement has been made. For five available folds,
each complete execution uses at most 12 initial logistic fits and 4,000
whole-meeting coefficient refits; complete replay repeats that work. These counts
exclude source projection, checkpoint serialization and final summaries, which
also need charging. Missing category support can only reduce the refit count;
it cannot authorize deletion or replacement of failed draws.

The owner must price the exact source preparation, fixed initial fits, per-draw
cost, checkpoint growth and complete fresh replay in a counted slot. Ten-draw
invocations and the 600-second cooperative wall bound keep resumable boundaries;
one in-progress fit is atomic and may overrun that cooperative check. Native
resource guards remain required. If the forecast exceeds 7,200 CPU-seconds,
the first 5% of the 2,000-draw bank is the checkpointed in-slot pilot. Its first
100 draws remain part of the unchanged full bank. No measured full-population
forecast or separate pilot allowance is asserted here. All prior preparation,
failed attempts and replay count within the inherited LA family allowance.
