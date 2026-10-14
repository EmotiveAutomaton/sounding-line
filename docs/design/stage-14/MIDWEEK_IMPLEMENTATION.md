# October 13 midweek commission

The curator approved implementing the midweek errata and the corrected Gear 3
Round 2 recommendation, while retaining local Gear 2. The campaign is
`G3-S14-MAKER-1`, with a **$50 gross ceiling**, pilot first. The original briefs
are preserved beside this document; the approval and input hashes are in
`results/gear3/G3-S14-MAKER-1/`. No earlier cloud approval is reused.

The question is whether a maker's cross-session history predicts later recorded
handling of suggestions beyond no history, another maker's history, personal
class frequencies and a cheap partial-pooling model. This is a descriptive
human process-record comparison, not identification of human values.

## Corrections adopted before outcomes

- Existing P03 and candidate P04 results predict the selected continuation
  conditional on uptake. They cannot be relabelled as four-way handling scores.
  Their original target lists and exposure remain frozen. This campaign freezes
  a separate aligned handling roster and a new local handling baseline cell.
- The split uses the first floor(0.6 times session count) history sessions.
  Apply the below-40 prompt fallback after checking history-arm support. Retain
  eight-label minimum history; show up to sixteen historical decisions, at most
  four per session, across at least two prompts. The source brief's literal
  sixteen conflicts with its eight-label eligibility floor; actual counts and
  a full-sixteen sensitivity are required. No missing decisions are invented.
- Source event order remains canonical. Eight sessions with nonmonotone clock
  timestamps retain their place in chronology but supply no eligible decisions.
  Compute effort only for history-window decisions. Unicode insertion lengths
  use UTF-16. Missing ignore latency remains missing. Target effort never enters
  either features or a model bundle. A reopened menu remains one decision.
- All donor evidence must have resolved before the recipient's first eligible
  target. The specified cyclic donor is retained; unavailable donor history
  excludes that recipient, without searching for a favorable donor. Record
  unmatched character ratios and analyze a matched-ratio sensitivity.
- Exclude whole pilot writers from main. Selection uses support and hashes,
  never target outcomes. Unknown historical exposure is not fresh evidence.
- Promote history versus no history, personal frequencies and mixed logit to
  decision-bearing comparisons. The frozen family contains eleven contrasts:
  R27 same-session versus population, then R27 and Opus cross-session versus
  population, donor, no history, personal frequencies and mixed logit. Holm
  correction covers the full family; an unavailable Opus lane contributes no
  affirmative decision. A confidence interval containing zero is unresolved.
- Report baseline-relative log-loss gain in nats against population and personal
  frequencies. Do not call it exact predictive V-information or conclude that
  failure to beat a baseline proves the absence of other personal information.
  Log-loss comparisons use identical valid support, with invalid counts and
  a system-log-loss sensitivity assigning invalids -log(0.01).
- Accept probability sums within 0.01, normalize once, then require normalized
  values in [0.01, 0.97]. Reject duplicate fields, nonfinite values and booleans.
  No clipping, reasking or silent repair. Invalid system half-Brier is one.
- Profiles must use exactly the evidence represented by the matched plain H2/H3
  arms. The effort legend is descriptive. Keep M1 and M0 together or defer both.
  Compression share is undefined for nonpositive H2 gain; below 50% fails the
  proposed threshold, 50–70% is unresolved, and at least 70% is a candidate only
  with the matched wrong-maker control. None alone validates preference strength.

## Local work

SM1 freezes the historical target/exposure inputs and the separate new roster.
SM2 supplies population, smoothed personal frequency, last-decision and
partial-pooling handling baselines. SM3 adds class-conditioned historical effort
features, weighted personal intercepts and within-writer shuffled weights.
Global coefficients are fit unweighted; only personal residual fits receive
weights. Penalty choice uses the recipient's historical calibration portion;
other writers' later records never train an earlier recipient. Compare the
weighted model with both the unweighted effort-feature model and its shuffled
weight control. Report feature addition separately from weighting.

SM4 token counts, mixed-text provenance and sparse-history labels remain mandatory
for the existing adapter results. Prototype initialization is a distinct pending
GPU comparison: freeze history-only clusters and a random-cluster control,
include prototype training in equal total optimizer steps, and use an explicitly
aligned readout. It cannot inherit a four-way score from the existing candidate
readout or restart exhausted failed cells. SM5 and SM6 remain deferred to Stage
15 under the accepted recommendation. SM7 vocabulary applies to new prose;
the draft lexicon does not authorize structural theory changes.

## Execution and reporting

`runners/stage14_midweek/` is separate from the live local queue. The original
v11 coordinator keeps its memory, residency, source and runtime gates. Resource
holds are not empty work and grant no authority to stop other applications.

All cloud invocations pass through `runners/gear3.py stage14`. Integer-cent
reservations share the existing authoritative ledger: pilot 350, Modal main
1400, API main 2850 and protected reserve 400. Unknown attempts keep their
reservation. No automatic retry, substituted model or paid expansion is allowed.
Account access and billing readiness are separate checks. Missing API credentials
hold the API lane while independent Modal and CPU setup continues.

The discarded Modal pilot runs twelve targets across four arms serially and
then at concurrency two, with unique request journals. One retained model load,
full GPU residency, exact tokenizer-bound raw prompts, actual token-count
verification and complete archive replay are required. Transport timeout exceeds
the per-call allowance; independent call and allocation deadlines stop work.
Main admission needs the fully valid pilot and a conservative measured forecast
inside its envelope. Main is not automatically launched by a PASS flag.

Friday October 16, 10:00 PDT remains the reporting reserve and 18:00 PDT the
scientific packet checkpoint. Six-hour operational inspections and immediate
terminal alerts remain. Full internal write-through precedes watcher ACK;
unfinished artifact scores are not curator reports.

## Implemented state and remaining gates

The aligned SM2/SM3 producer and saved-output consumer are complete and internally
landed. The main roster has 31 writers and 234 targets, excluding three whole
pilot writers. Historical source pins, temporal fitting keys and every saved
proper score verify. The separate exposure supplement identifies positive exact
key witnesses in completed Stage 14 predictions; it does not convert absent
witnesses to untouched status or change the frozen roster.

The two paid adapters have now executed their first pilots. The Modal pilot's
ninety-six replies pass complete archive, native prompt/token, wire and residency
replay; its conservative booking is 68 cents and its provider app is stopped.
The curator subsequently confirmed sufficient account headroom. The unchanged
936-call main is now complete and internally landed. Complete archive/native
prompt/token and residency replay, source reconstruction and saved-output
analysis verify. Invalids remain in system loss; no primary reader advantage is
established. The 1,340-cent reservation reconciles to 476 cents with ended
ownership, pending final invoice. Combined campaign booking is 548 cents.
The cold first pilot request remains in the original frozen timing estimate.
All unavailable API comparisons remain explicit in the eleven-slot family;
the Modal cell does not close the joint campaign or authorize a repair.

The configured API credential passes model-access checks for all three readers.
The first six-request Sonnet profile pilot completed, but two output-limit stops
fail its matched-profile prerequisite. Complete request reconstruction, temporal
and evidence matching, offline replay and ended-batch token accounting pass. The
booking reconciles from six to four cents; originals and invalids remain. The API
reader pilot and main are unsubmitted, and the existing dependency guard refuses.
A submitted batch is never automatically retried. Any repair needs a separately
reviewed plan; no prompt, cap, model or matched control is silently changed.
Ended batches with complete token accounting may reconcile downward; other cases
retain the full reservation. Permitted profile shortening is explicitly recorded,
and complete paired profiles must finish before their reader arms.
The twenty-four-hour batch submission allowance does not guarantee completion of
several dependent waves by Friday; unfinished lanes remain visible in the packet.

SM4's token/provenance requirements apply to the completed adapter ladder. Its new
prototype runner is not implemented or admitted: after the GPU lane freed, a
separately frozen synthetic handling readout failed semantic admission. Candidate
selection cannot stand in for four-way handling. Preserve this
conditional task rather than counting it as runnable capacity. Its eventual design
must include a separate donor/random-cluster control, recipient-specific temporal
cuts and prototype training in equal total compute. SM5/SM6 are deferred.

Before any paid request, retain the superseded preflight plan and freeze current
sources. The first data preflight used a rounded-up split and insufficiently strict
cursor construction; no model or score call used it. Data-v2 corrects both before
the local producer. No source brief is rewritten; corrections live here and in the
versioned preparation evidence. Main admission appends the discarded pilot's
variance and throughput measurements to its own frozen admission record, preserving
the original plan and recognizing the instability of a three-writer variance estimate.
