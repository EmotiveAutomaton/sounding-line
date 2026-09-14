# Gear 3 Round 1: final selected curator packet

**Hypothesis.** A larger reader gains more from explicit reconstruction than from direct prediction or matched deliberation; correct session history and reusable procedures supply useful additional evidence.

**METHOD.** Compared the pinned Qwen 3.5 9B and 27B packages in 17 frozen cloud jobs on human handling of writing suggestions and, separately, constructed Ghost opportunity tasks. Replayed every complete native route from saved raw responses, then joined frozen local evaluator records. The primary measure is half multiclass Brier loss, a probability error score where lower is better; invalid attempts receive loss one. Writers or source cases receive equal weight. Prompt, writer, constructor and donor links determine dependency components. Cheap controls and the fixed same-confidence diagnostic remain separate from primary forecasts.

**Found.** The larger reader did not gain more from explicit reconstruction. It improved direct prediction, while reconstruction hurt its primary score on both main source families. Correct session history helped the larger reader, and descriptive procedure names helped relative to opaque names, but neither establishes a persistent maker model. The simple training-frequency baseline beat every main human model arm on the primary score.

**Means.** This is a completed descriptive comparison of reader packages and assistance methods. It does not isolate parameter count, demonstrate human empathy, recover historical intent, or close the general theory. A maker model inferred from earlier situations and actions, then tested without rebuilding it for each target, remains a candidate for a separately bounded study.

The main human comparison contains 64 opportunities from 14 writers, 21 sessions and three prompts. Its dependency graph joins into one component. The seven Ghost questions span five cases but also one connected component. History uses 24 targets from 13 writers; donor links join the paired comparison into one component. Representation assistance uses 24 targets from 14 writers and three components. Eight additional human opportunities have eight writers and two components; they are a new event slice, not eight new independent writers. No population confidence interval is licensed for these comparisons.

The table reports complete separate populations. A positive difference means the first named method has lower probability error. Reconstruction benefit compares executable proposals with matched deliberation; the interaction subtracts the smaller package's benefit from the larger package's benefit.

| Population | Larger direct benefit | Reconstruction benefit, 9B | Reconstruction benefit, 27B | Interaction |
|---|---:|---:|---:|---:|
| Main human handling | +0.0481 | -0.0195 | -0.0652 | -0.0456 |
| Ghost opportunity | +0.5433 | +0.4590 | -0.0512 | -0.5102 |
| Additional human events | +0.0409 | +0.0531 | -0.0891 | -0.1422 |

On main human handling, direct loss is 0.4361 for 9B and 0.3880 for 27B; executable proposals give 0.4473 and 0.4579. The training-frequency control gives 0.3209. It assigns zero probability to two realized outcomes, making its log loss infinite; no universal ranking across scoring rules is claimed. Larger direct generated-choice accuracy is 39.6%, versus 25.4% for the smaller package. Larger executable generated-choice accuracy is also 39.6%. At common fixed confidence its direct and executable forecasts tie at loss 0.4979: the primary probability-score disadvantage is not a corresponding loss of generated-choice accuracy. The smaller package's generated choice worsens with execution. Two main 9B attempts are invalid and remain in the system score.

The history table reports probability-error gains from correct predecision session history over the named alternative on the same targets. Positive favors correct history. These are interventions on the reader's evidence, not the human's past.

| Reader and method | Correct versus other-writer history | Correct versus no history | Loss with correct history |
|---|---:|---:|---:|
| 9B direct | +0.0437 | -0.0193 | 0.4199 |
| 9B executable | +0.0031 | +0.0615 | 0.4858 |
| 27B direct | +0.0858 | +0.0655 | 0.3108 |
| 27B executable | +0.0646 | +0.1108 | 0.3965 |

Correct history helps 27B against both alternatives under both methods. Its direct generated-choice accuracy improves by 19.2 percentage points against other-writer history and 15.4 against no history. The matched training-frequency control has loss 0.3810 and correct-history persistence 0.5769. Larger direct prediction beats both; its executable route beats persistence but not the frequency control. Smaller direct prediction does better without history than with correct history. Donor-linked support is one component, so these effects remain descriptive.

Representation losses below use the same 24 human targets, with lower better. Opaque and grounded procedures have identical definitions, episodes and support metadata, differing only in descriptions.

| Package | Stored examples | Opaque procedures | Grounded procedures | Grounded benefit over opaque |
|---|---:|---:|---:|---:|
| 9B | 0.3623 | 0.4207 | 0.3873 | +0.0334 |
| 27B | 0.3174 | 0.4064 | 0.3207 | +0.0857 |

For 27B, the naming benefit remains positive after omitting any one connected component, ranging from +0.0500 to +0.1091. Grounded procedures do not beat stored examples overall: difference -0.0033, with descriptive omission range -0.0236 to +0.0243. This is not an equivalence conclusion. The 9B naming range crosses zero, with one invalid grounded attempt retained. Common-confidence scoring narrows the larger naming gain to +0.0286, matching a 3.6-point generated-choice gain. Probability mixture/calibration contributes to the primary-score difference. No historical procedure-recovery claim follows.

On Ghost opportunity, direct loss falls from 0.5730 to 0.0298 with the larger package. Executing proposed candidates improves 9B to 0.1140 but worsens 27B to 0.0809. Both executed probability mixtures rank the realized option first on every weighted case; their separately generated choices achieve only 30% and 80%. All 28 native proposal evaluations execute without a model-mismatch flag, using two to four candidates from supports of 36 or 54. All proposed candidates have positive evidence likelihood. This is conditional operation on proposed support, not true-state recovery or a full-support posterior. Legal program reconstruction and artifact recreation are not measured by this opportunity API; Ghost reading was deferred after its pilot feedback failure.

Across 256 main-human native evaluation rounds, no proposed rule is syntactically constant, but substituting each rule's realized action leaves its single-task mixture unchanged in every check. Smaller generated choices belong to the mixture maximum on 60 of 128 rounds; larger choices on 102 of 128. These are round-level readout diagnostics, not independent makers or reasoning ablations. The current method produces fresh task-specific rules, not a persistent writer model.

The extra eight-event human slice retains a negative larger-reader interaction, while the smaller package benefits from execution there. The training-frequency control still beats all its model methods on primary loss. This source-dependent reversal prevents a blanket method ranking.

## Worked examples

The source spec requested advantage, reversal and failure examples. We select the smallest SHA256(task identifier) in each category: a correct larger direct choice with an incorrect smaller direct choice; a larger direct probability advantage with a larger executable disadvantage; and an invalid smaller direct attempt. These are explicit post-score display definitions, not preregistered additional analyses. The same task wins the first two categories and is shown once; no replacement is selected for variety. Original first-task-per-cell consumer examples remain private and unchanged.

- **Advantage and reversal:** a writer working on a school-curriculum essay saw a suggestion menu. Both readers received the draft, suggestions and permitted earlier handling. The writer accepted a suggestion without editing the insertion. Larger direct prediction chose that outcome with loss 0.0625; smaller direct prediction chose incorrectly with loss 0.3750. Executing proposed rules changed the larger loss to 0.2550 and the smaller loss to 0.0150. Yet the smaller executable reader's separate generated choice was wrong. The probability mixture and the narrated decision disagree on a retained case.
- **Interface failure:** at another school-curriculum essay menu, the human again accepted without editing. Smaller direct and deliberative attempts were invalid, each receiving system loss one, without invented predictions. Both executable readers returned valid distributions with loss 0.2550; larger direct prediction made a valid but wrong choice with loss 0.5575.

The categories contain 17, 10 and one main-human events respectively. Their selection is illustrative; no new inferential test follows. Human text, identities, raw replies and evaluator bindings remain private.

## Completion, cost and next decision

All 17 frozen scientific jobs completed, including 810 attempted forecast routes with three invalid routes retained. No scientific job or cell was dropped. Five reading-task exclusion entries, five dependent counterparts, eight entries withheld to preserve repair reserve and eighteen prefix-tail entries retain their reasons. These are branch entries, not independent subjects. A second human corpus, adaptive routing and private Ghost confirmation remain unrun. All sources were historically exposed descriptive allocations.

All $31.75 remains booked: $2.83 pilot, $1.02 Reserve repairs, $14.92 main comparisons, $6.99 history, $4.38 representations and $1.61 breadth. No provider-attributed final invoice is available. Zero confirmed cents means unconfirmed billing, not free computation. The unchanged $50 cap leaves $18.25 nominal allowance, subject to the lower workspace backstop; $8.98 of repair reserve remains protected. Originally observed $30 credits and a separate $1 storage allowance do not increase the gross budget. Retained cloud artifacts can still accrue storage charges; no deletion or new resource is commissioned by closeout.

Scientific work records 1,318 model calls, 1,942,658 input tokens and 199,027 generated tokens. Worker duration totals 17,283 seconds, about 4.80 hours; reported model-server duration is about 1.59 hours. Worker time includes loading and execution but is not an invoice or a complete attribution of provider startup/teardown. Sequence plus local consumer took about five hours. Original setup, failed-pilot and repair reservations remain retained.

All 76 bound launch files verify. The 8,452 returned scientific evidence files remain unchanged; offline replay reproduces four final packet files byte for byte with no new inference. All 40 model/context loads verify fully GPU resident. Original scientific native owners have ended. Six scientific apps still listed by the provider are stopped; all seventeen task inventories are empty, with older stopped apps absent from the current list. Local Stage 10 remains in first gear, both scheduling controllers suspended, with results and frozen queues preserved. This closes finite Gear 3 Round 1, not the broader local Stage 10 study.

**Next decision.** Review these findings before commissioning another cloud allocation. The strongest candidate is a maker model inferred from pre-cutoff situations and actions, held fixed or updated under a declared rule, compared against direct prediction, task-specific voting, retrieval and cheap persistence across independent source groups. Ghost reading requires a separately scoped feedback-path repair; adaptive human routing needs more independent development writers. Grounded representation access merits consideration but does not establish that expanding the current grid will recover intent. No further paid work, gear change or theory rewrite follows automatically. No tests were harvested from this operational wake.

## Complete measurement appendix

R0 is direct prediction; R2 matched deliberation; R3 task-specific executable proposals; R1-memory stored examples; R4 opaque or grounded procedures. Same-confidence maps the recorded human choice to 0.85 and each other action to 0.05, without replacing the primary forecast. Loss is half multiclass Brier loss; system loss keeps invalids at one, valid-only excludes them. Accuracies weight writers/cases equally; probability accuracy splits tied maxima. Calibration error is the fixed binned confidence/accuracy gap. Log loss is in nats, with zero support kept infinite. Components are connected dependencies, not participants.

### B: coauthor-handling, artifact-only

Predict how the human will handle this displayed model-suggestion menu. Evidence view: artifact. Counts: 24 events, 3 prompts, 14 sessions, 13 writers.

Class composition (unweighted events): Accept an offered model suggestion and leave that insertion unedited before the next new menu.: 11; Accept an offered model suggestion, then edit its inserted text before the next new menu.: 6; Explicitly dismiss the displayed suggestion menu without a verified selection.: 6; Leave this displayed menu without a recorded selection or explicit dismissal.: 1.

The rows contain each method/control on this complete cell, with the quantities defined above.

| Method/control | Attempts | Invalid | System loss | Valid loss | Choice accuracy | Probability accuracy | Calibration error | Valid log loss | Zero support | Components |
|---|---|---|---|---|---|---|---|---|---|---|
| methods/27b-R0 | 24 | 0 | 0.3763 | 0.3763 | 0.3846 | 0.4038 | 0.2712 | 1.3741 | 0 | 3 |
| methods/27b-R3 | 24 | 0 | 0.5073 | 0.5073 | 0.3846 | 0.2692 | 0.3500 | 1.9928 | 0 | 3 |
| methods/9b-R0 | 24 | 0 | 0.4006 | 0.4006 | 0.2692 | 0.2885 | 0.2688 | 1.4340 | 0 | 3 |
| methods/9b-R3 | 24 | 0 | 0.5473 | 0.5473 | 0.3462 | 0.2115 | 0.3923 | 2.1862 | 0 | 3 |
| cheap_controls/always-ignore | 24 | 0 | 0.9615 | 0.9615 | 0.0385 | 0.0385 | 0.9615 | infinite | 23 | 3 |
| cheap_controls/class-prior | 24 | 0 | 0.3810 | 0.3810 | 0.4231 | 0.4231 | 0.1769 | infinite | 1 | 3 |
| cheap_controls/previous-handling | 24 | 0 | 0.3810 | 0.3810 | 0.4231 | 0.4231 | 0.1769 | infinite | 1 | 3 |
| cheap_controls/surface-features | 24 | 0 | 0.4859 | 0.4859 | 0.4231 | 0.4231 | 0.4808 | 2.7723 | 0 | 3 |
| secondary_same_confidence/27b-R0-same-confidence | 24 | 0 | 0.5073 | 0.5073 | 0.3846 | 0.3846 | 0.4654 | 1.9060 | 0 | 3 |
| secondary_same_confidence/27b-R3-same-confidence | 24 | 0 | 0.5073 | 0.5073 | 0.3846 | 0.3846 | 0.4654 | 1.9060 | 0 | 3 |
| secondary_same_confidence/9b-R0-same-confidence | 24 | 0 | 0.5996 | 0.5996 | 0.2692 | 0.2692 | 0.5808 | 2.2329 | 0 | 3 |
| secondary_same_confidence/9b-R3-same-confidence | 24 | 0 | 0.5381 | 0.5381 | 0.3462 | 0.3462 | 0.5038 | 2.0150 | 0 | 3 |
| matched_correct_history/27b-R0 | 24 | 0 | 0.3108 | 0.3108 | 0.5385 | 0.5481 | 0.1885 | 1.1377 | 0 | 3 |
| matched_correct_history/27b-R3 | 24 | 0 | 0.3965 | 0.3965 | 0.3846 | 0.4231 | 0.2269 | 1.5569 | 0 | 3 |
| matched_correct_history/9b-R0 | 24 | 0 | 0.4199 | 0.4199 | 0.3462 | 0.3269 | 0.2758 | 1.4841 | 0 | 3 |
| matched_correct_history/9b-R3 | 24 | 0 | 0.4858 | 0.4858 | 0.3077 | 0.2885 | 0.3154 | 1.8482 | 0 | 3 |

Correct-history persistence on this subset: loss 0.5769, choice accuracy 0.4231, log loss infinite with 14 zero-support outcomes.

Paired differences below are positive for the first named method or correct-history condition; interaction is defined above. Omission ranges are descriptive, not confidence intervals. None means only one component. Finite log differences exclude nonfinite pairs and show their denominator. Individual anonymized component contrasts are in READOUT_DIAGNOSTICS.json.

| Contrast | Loss benefit | Components | Omission range | Finite log benefit | Finite pairs | Choice benefit |
|---|---|---|---|---|---|---|
| 27b-R0 | 0.0655 | 1 | None | 0.2364 | 24 | 0.1538 |
| 27b-R3 | 0.1108 | 1 | None | 0.4359 | 24 | 0.0000 |
| 9b-R0 | -0.0193 | 1 | None | -0.0501 | 24 | 0.0769 |
| 9b-R3 | 0.0615 | 1 | None | 0.3380 | 24 | -0.0385 |

### B: coauthor-handling, other-writer

Predict how the human will handle this displayed model-suggestion menu. Evidence view: process-record. Counts: 24 events, 3 prompts, 14 sessions, 13 writers.

Class composition (unweighted events): Accept an offered model suggestion and leave that insertion unedited before the next new menu.: 11; Accept an offered model suggestion, then edit its inserted text before the next new menu.: 6; Explicitly dismiss the displayed suggestion menu without a verified selection.: 6; Leave this displayed menu without a recorded selection or explicit dismissal.: 1.

The rows contain each method/control on this complete cell, with the quantities defined above.

| Method/control | Attempts | Invalid | System loss | Valid loss | Choice accuracy | Probability accuracy | Calibration error | Valid log loss | Zero support | Components |
|---|---|---|---|---|---|---|---|---|---|---|
| methods/27b-R0 | 24 | 0 | 0.3965 | 0.3965 | 0.3462 | 0.3462 | 0.2615 | 1.4395 | 0 | 3 |
| methods/27b-R3 | 24 | 0 | 0.4612 | 0.4612 | 0.3077 | 0.3269 | 0.2923 | 1.7392 | 0 | 3 |
| methods/9b-R0 | 24 | 0 | 0.4636 | 0.4636 | 0.2692 | 0.2885 | 0.3362 | infinite | 2 | 3 |
| methods/9b-R3 | 24 | 0 | 0.4888 | 0.4888 | 0.2692 | 0.3462 | 0.3808 | 1.8949 | 0 | 3 |
| cheap_controls/always-ignore | 24 | 0 | 0.9615 | 0.9615 | 0.0385 | 0.0385 | 0.9615 | infinite | 23 | 3 |
| cheap_controls/class-prior | 24 | 0 | 0.3810 | 0.3810 | 0.4231 | 0.4231 | 0.1769 | infinite | 1 | 3 |
| cheap_controls/previous-handling | 24 | 0 | 0.8462 | 0.8462 | 0.1538 | 0.1538 | 0.8462 | infinite | 20 | 3 |
| cheap_controls/surface-features | 24 | 0 | 0.4859 | 0.4859 | 0.4231 | 0.4231 | 0.4808 | 2.7723 | 0 | 3 |
| secondary_same_confidence/27b-R0-same-confidence | 24 | 0 | 0.5381 | 0.5381 | 0.3462 | 0.3462 | 0.5038 | 2.0150 | 0 | 3 |
| secondary_same_confidence/27b-R3-same-confidence | 24 | 0 | 0.5688 | 0.5688 | 0.3077 | 0.3077 | 0.5423 | 2.1240 | 0 | 3 |
| secondary_same_confidence/9b-R0-same-confidence | 24 | 0 | 0.5996 | 0.5996 | 0.2692 | 0.2692 | 0.5808 | 2.2329 | 0 | 3 |
| secondary_same_confidence/9b-R3-same-confidence | 24 | 0 | 0.5996 | 0.5996 | 0.2692 | 0.2692 | 0.5808 | 2.2329 | 0 | 3 |
| matched_correct_history/27b-R0 | 24 | 0 | 0.3108 | 0.3108 | 0.5385 | 0.5481 | 0.1885 | 1.1377 | 0 | 3 |
| matched_correct_history/27b-R3 | 24 | 0 | 0.3965 | 0.3965 | 0.3846 | 0.4231 | 0.2269 | 1.5569 | 0 | 3 |
| matched_correct_history/9b-R0 | 24 | 0 | 0.4199 | 0.4199 | 0.3462 | 0.3269 | 0.2758 | 1.4841 | 0 | 3 |
| matched_correct_history/9b-R3 | 24 | 0 | 0.4858 | 0.4858 | 0.3077 | 0.2885 | 0.3154 | 1.8482 | 0 | 3 |

Correct-history persistence on this subset: loss 0.5769, choice accuracy 0.4231, log loss infinite with 14 zero-support outcomes.

Paired differences below are positive for the first named method or correct-history condition; interaction is defined above. Omission ranges are descriptive, not confidence intervals. None means only one component. Finite log differences exclude nonfinite pairs and show their denominator. Individual anonymized component contrasts are in READOUT_DIAGNOSTICS.json.

| Contrast | Loss benefit | Components | Omission range | Finite log benefit | Finite pairs | Choice benefit |
|---|---|---|---|---|---|---|
| 27b-R0 | 0.0858 | 1 | None | 0.3018 | 24 | 0.1923 |
| 27b-R3 | 0.0646 | 1 | None | 0.1824 | 24 | 0.0769 |
| 9b-R0 | 0.0437 | 1 | None | 0.1554 | 22 | 0.0769 |
| 9b-R3 | 0.0031 | 1 | None | 0.0467 | 24 | 0.0385 |

### D: coauthor-handling, ordinary

Predict how the human will handle this displayed model-suggestion menu. Evidence view: process-record. Counts: 8 events, 2 prompts, 8 sessions, 8 writers.

Class composition (unweighted events): Accept an offered model suggestion and leave that insertion unedited before the next new menu.: 6; Accept an offered model suggestion, then edit its inserted text before the next new menu.: 1; Explicitly dismiss the displayed suggestion menu without a verified selection.: 1.

The rows contain each method/control on this complete cell, with the quantities defined above.

| Method/control | Attempts | Invalid | System loss | Valid loss | Choice accuracy | Probability accuracy | Calibration error | Valid log loss | Zero support | Components |
|---|---|---|---|---|---|---|---|---|---|---|
| methods/27b-R0 | 8 | 0 | 0.4434 | 0.4434 | 0.2500 | 0.2500 | 0.3500 | 1.5421 | 0 | 2 |
| methods/27b-R2 | 8 | 0 | 0.4459 | 0.4459 | 0.2500 | 0.2500 | 0.3625 | 1.5421 | 0 | 2 |
| methods/27b-R3 | 8 | 0 | 0.5350 | 0.5350 | 0.3750 | 0.2500 | 0.4000 | 2.0923 | 0 | 2 |
| methods/9b-R0 | 8 | 0 | 0.4844 | 0.4844 | 0.2500 | 0.1875 | 0.3375 | 1.7122 | 0 | 2 |
| methods/9b-R2 | 8 | 0 | 0.4981 | 0.4981 | 0.2500 | 0.1562 | 0.4062 | 1.7254 | 0 | 2 |
| methods/9b-R3 | 8 | 0 | 0.4450 | 0.4450 | 0.5000 | 0.4375 | 0.3750 | 1.6586 | 0 | 2 |
| cheap_controls/always-ignore | 8 | 0 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 1.0000 | infinite | 8 | 2 |
| cheap_controls/class-prior | 8 | 0 | 0.2336 | 0.2336 | 0.7500 | 0.7500 | 0.1500 | 0.8375 | 0 | 2 |
| cheap_controls/previous-handling | 8 | 0 | 0.5167 | 0.5167 | 0.5000 | 0.5000 | 0.5500 | infinite | 4 | 2 |
| cheap_controls/surface-features | 8 | 0 | 0.3425 | 0.3425 | 0.6250 | 0.6250 | 0.3182 | 2.1166 | 0 | 2 |
| secondary_same_confidence/27b-R0-same-confidence | 8 | 0 | 0.6150 | 0.6150 | 0.2500 | 0.2500 | 0.6000 | 2.2874 | 0 | 2 |
| secondary_same_confidence/27b-R2-same-confidence | 8 | 0 | 0.6150 | 0.6150 | 0.2500 | 0.2500 | 0.6000 | 2.2874 | 0 | 2 |
| secondary_same_confidence/27b-R3-same-confidence | 8 | 0 | 0.5150 | 0.5150 | 0.3750 | 0.3750 | 0.4750 | 1.9333 | 0 | 2 |
| secondary_same_confidence/9b-R0-same-confidence | 8 | 0 | 0.6150 | 0.6150 | 0.2500 | 0.2500 | 0.6000 | 2.2874 | 0 | 2 |
| secondary_same_confidence/9b-R2-same-confidence | 8 | 0 | 0.6150 | 0.6150 | 0.2500 | 0.2500 | 0.6000 | 2.2874 | 0 | 2 |
| secondary_same_confidence/9b-R3-same-confidence | 8 | 0 | 0.4150 | 0.4150 | 0.5000 | 0.5000 | 0.3500 | 1.5791 | 0 | 2 |

Paired differences below are positive for the first named method or correct-history condition; interaction is defined above. Omission ranges are descriptive, not confidence intervals. None means only one component. Finite log differences exclude nonfinite pairs and show their denominator. Individual anonymized component contrasts are in READOUT_DIAGNOSTICS.json.

| Contrast | Loss benefit | Components | Omission range | Finite log benefit | Finite pairs | Choice benefit |
|---|---|---|---|---|---|---|
| interaction | -0.1422 | 2 | [-0.7049999999999998, -0.06178571428571432] | -0.6169 | 8 | not available |
| deliberative_model_package_difference | 0.0522 | 2 | [-0.09500000000000008, 0.0732142857142857] | 0.1833 | 8 | 0.0000 |
| direct_model_package_difference | 0.0409 | 2 | [-0.07500000000000007, 0.057499999999999996] | 0.1701 | 8 | 0.0000 |
| structured_versus_direct/27b | -0.0916 | 2 | [-0.3649999999999999, -0.05249999999999999] | -0.5502 | 8 | 0.1250 |
| structured_versus_direct/9b | 0.0394 | 2 | [-0.0064285714285714024, 0.36] | 0.0536 | 8 | 0.2500 |
| within_model/27b | -0.0891 | 2 | [-0.34499999999999986, -0.05249999999999999] | -0.5502 | 8 | 0.1250 |
| within_model/9b | 0.0531 | 2 | [0.00928571428571431, 0.36] | 0.0668 | 8 | 0.2500 |

### A: ghost-opportunity, ordinary

Forecast the artifact after the declared target probe, using only the observed prior probes. Evidence view: process-record. Counts: 7 events, 5 ghost_cases.

Class composition (unweighted events): 0: 3; 1: 4.

The rows contain each method/control on this complete cell, with the quantities defined above.

| Method/control | Attempts | Invalid | System loss | Valid loss | Choice accuracy | Probability accuracy | Calibration error | Valid log loss | Zero support | Components |
|---|---|---|---|---|---|---|---|---|---|---|
| methods/27b-R0 | 7 | 0 | 0.0297 | 0.0297 | 0.9000 | 1.0000 | 0.1150 | 0.1353 | 0 | 1 |
| methods/27b-R2 | 7 | 0 | 0.0297 | 0.0297 | 1.0000 | 1.0000 | 0.1150 | 0.1353 | 0 | 1 |
| methods/27b-R3 | 7 | 0 | 0.0809 | 0.0809 | 0.8000 | 1.0000 | 0.2692 | 0.3209 | 0 | 1 |
| methods/9b-R0 | 7 | 0 | 0.5730 | 0.5730 | 0.4000 | 0.4000 | 0.6100 | infinite | 3 | 1 |
| methods/9b-R2 | 7 | 0 | 0.5730 | 0.5730 | 0.4000 | 0.4000 | 0.6100 | infinite | 3 | 1 |
| methods/9b-R3 | 7 | 0 | 0.1140 | 0.1140 | 0.3000 | 1.0000 | 0.3137 | 0.3922 | 0 | 1 |
| cheap_controls/first-option | 7 | 0 | 0.5000 | 0.5000 | 0.5000 | 0.5000 | 0.5000 | infinite | 4 | 1 |
| cheap_controls/uniform | 7 | 0 | 0.2500 | 0.2500 | 0.5000 | 0.5000 | 0.0000 | 0.6931 | 0 | 1 |

Paired differences below are positive for the first named method or correct-history condition; interaction is defined above. Omission ranges are descriptive, not confidence intervals. None means only one component. Finite log differences exclude nonfinite pairs and show their denominator. Individual anonymized component contrasts are in READOUT_DIAGNOSTICS.json.

| Contrast | Loss benefit | Components | Omission range | Finite log benefit | Finite pairs | Choice benefit |
|---|---|---|---|---|---|---|
| interaction | -0.5102 | 1 | None | -0.3541 | 4 | not available |
| deliberative_model_package_difference | 0.5433 | 1 | None | 0.3833 | 4 | 0.6000 |
| direct_model_package_difference | 0.5433 | 1 | None | 0.3833 | 4 | 0.5000 |
| structured_versus_direct/27b | -0.0512 | 1 | None | -0.1856 | 7 | -0.1000 |
| structured_versus_direct/9b | 0.4590 | 1 | None | 0.2561 | 4 | -0.1000 |
| within_model/27b | -0.0512 | 1 | None | -0.1856 | 7 | -0.2000 |
| within_model/9b | 0.4590 | 1 | None | 0.2561 | 4 | -0.1000 |

### C: coauthor-handling, ordinary

Predict how the human will handle this displayed model-suggestion menu. Evidence view: process-record. Counts: 24 events, 3 prompts, 16 sessions, 14 writers.

Class composition (unweighted events): Accept an offered model suggestion and leave that insertion unedited before the next new menu.: 13; Accept an offered model suggestion, then edit its inserted text before the next new menu.: 4; Explicitly dismiss the displayed suggestion menu without a verified selection.: 6; Leave this displayed menu without a recorded selection or explicit dismissal.: 1.

The rows contain each method/control on this complete cell, with the quantities defined above.

| Method/control | Attempts | Invalid | System loss | Valid loss | Choice accuracy | Probability accuracy | Calibration error | Valid log loss | Zero support | Components |
|---|---|---|---|---|---|---|---|---|---|---|
| methods/27b-R1-memory | 24 | 0 | 0.3174 | 0.3174 | 0.5357 | 0.5357 | 0.1714 | 1.2292 | 0 | 3 |
| methods/27b-R4-grounded | 24 | 0 | 0.3207 | 0.3207 | 0.5714 | 0.5179 | 0.1321 | 1.2776 | 0 | 3 |
| methods/27b-R4-opaque | 24 | 0 | 0.4064 | 0.4064 | 0.5357 | 0.3750 | 0.2036 | 1.5708 | 0 | 3 |
| methods/9b-R1-memory | 24 | 0 | 0.3623 | 0.3623 | 0.5000 | 0.5000 | 0.2446 | 1.3628 | 0 | 3 |
| methods/9b-R4-grounded | 24 | 1 | 0.3873 | 0.3607 | 0.4286 | 0.4464 | 0.1607 | 1.4242 | 0 | 3 |
| methods/9b-R4-opaque | 24 | 0 | 0.4207 | 0.4207 | 0.4286 | 0.3929 | 0.2571 | 1.6039 | 0 | 3 |
| cheap_controls/always-ignore | 24 | 0 | 0.9643 | 0.9643 | 0.0357 | 0.0357 | 0.9643 | infinite | 23 | 3 |
| cheap_controls/class-prior | 24 | 0 | 0.3080 | 0.3080 | 0.5714 | 0.5714 | 0.0286 | infinite | 1 | 3 |
| cheap_controls/previous-handling | 24 | 0 | 0.4364 | 0.4364 | 0.5714 | 0.5714 | 0.4571 | infinite | 10 | 3 |
| cheap_controls/surface-features | 24 | 0 | 0.4117 | 0.4117 | 0.5714 | 0.5714 | 0.4615 | 2.5390 | 0 | 3 |
| secondary_same_confidence/27b-R1-memory-same-confidence | 24 | 0 | 0.3864 | 0.3864 | 0.5357 | 0.5357 | 0.3143 | 1.4779 | 0 | 3 |
| secondary_same_confidence/27b-R4-grounded-same-confidence | 24 | 0 | 0.3579 | 0.3579 | 0.5714 | 0.5714 | 0.2786 | 1.3768 | 0 | 3 |
| secondary_same_confidence/27b-R4-opaque-same-confidence | 24 | 0 | 0.3864 | 0.3864 | 0.5357 | 0.5357 | 0.3143 | 1.4779 | 0 | 3 |
| secondary_same_confidence/9b-R1-memory-same-confidence | 24 | 0 | 0.4150 | 0.4150 | 0.5000 | 0.5000 | 0.3500 | 1.5791 | 0 | 3 |
| secondary_same_confidence/9b-R4-grounded-same-confidence | 24 | 1 | 0.4787 | 0.4721 | 0.4286 | 0.4286 | 0.4214 | 1.7815 | 0 | 3 |
| secondary_same_confidence/9b-R4-opaque-same-confidence | 24 | 0 | 0.4721 | 0.4721 | 0.4286 | 0.4286 | 0.4214 | 1.7815 | 0 | 3 |

Paired differences below are positive for the first named method or correct-history condition; interaction is defined above. Omission ranges are descriptive, not confidence intervals. None means only one component. Finite log differences exclude nonfinite pairs and show their denominator. Individual anonymized component contrasts are in READOUT_DIAGNOSTICS.json.

| Contrast | Loss benefit | Components | Omission range | Finite log benefit | Finite pairs | Choice benefit |
|---|---|---|---|---|---|---|
| 27b/grounded_vs_R0 | 0.0465 | 3 | [-0.0628125, 0.10261363636363638] | 0.0626 | 24 | 0.1429 |
| 27b/grounded_vs_R3 | 0.1257 | 3 | [0.03999999999999998, 0.1818181818181818] | 0.4047 | 24 | 0.1071 |
| 27b/grounded_vs_examples | -0.0033 | 3 | [-0.023573076923076912, 0.02430000000000001] | -0.0485 | 24 | 0.0357 |
| 27b/grounded_vs_opaque | 0.0857 | 3 | [0.05, 0.10909090909090909] | 0.2932 | 24 | 0.0357 |
| 27b/opaque_vs_R0 | -0.0392 | 3 | [-0.1128125, -0.006477272727272717] | -0.2306 | 24 | 0.1071 |
| 27b/opaque_vs_R3 | 0.0400 | 3 | [-0.010000000000000023, 0.07272727272727271] | 0.1115 | 24 | 0.0714 |
| 27b/opaque_vs_examples | -0.0890 | 3 | [-0.10049615384615383, -0.06343749999999998] | -0.3417 | 24 | 0.0000 |
| 9b/grounded_vs_R0 | -0.0004 | 3 | [-0.144375, 0.04053977272727272] | -0.0220 | 23 | 0.0714 |
| 9b/grounded_vs_R3 | 0.1162 | 3 | [-0.059999999999999984, 0.15159090909090908] | 0.4832 | 23 | 0.2500 |
| 9b/grounded_vs_examples | -0.0250 | 3 | [-0.175, 0.034204545454545446] | -0.0614 | 23 | -0.0714 |
| 9b/grounded_vs_opaque | 0.0334 | 3 | [-0.09, 0.07522727272727271] | 0.1012 | 23 | 0.0000 |
| 9b/opaque_vs_R0 | -0.0338 | 3 | [-0.054375, -0.02665865384615384] | -0.1689 | 24 | 0.0714 |
| 9b/opaque_vs_R3 | 0.0829 | 3 | [0.030000000000000013, 0.10461538461538462] | 0.3820 | 24 | 0.2500 |
| 9b/opaque_vs_examples | -0.0584 | 3 | [-0.08499999999999999, -0.041022727272727266] | -0.2411 | 24 | -0.0714 |

### A: coauthor-handling, ordinary

Predict how the human will handle this displayed model-suggestion menu. Evidence view: process-record. Counts: 64 events, 3 prompts, 21 sessions, 14 writers.

Class composition (unweighted events): Accept an offered model suggestion and leave that insertion unedited before the next new menu.: 31; Accept an offered model suggestion, then edit its inserted text before the next new menu.: 12; Explicitly dismiss the displayed suggestion menu without a verified selection.: 19; Leave this displayed menu without a recorded selection or explicit dismissal.: 2.

The rows contain each method/control on this complete cell, with the quantities defined above.

| Method/control | Attempts | Invalid | System loss | Valid loss | Choice accuracy | Probability accuracy | Calibration error | Valid log loss | Zero support | Components |
|---|---|---|---|---|---|---|---|---|---|---|
| methods/27b-R0 | 64 | 0 | 0.3880 | 0.3880 | 0.3964 | 0.4179 | 0.2330 | 1.4167 | 0 | 1 |
| methods/27b-R2 | 64 | 0 | 0.3927 | 0.3927 | 0.4000 | 0.4036 | 0.2602 | 1.4397 | 0 | 1 |
| methods/27b-R3 | 64 | 0 | 0.4579 | 0.4579 | 0.3964 | 0.3321 | 0.2893 | 1.7536 | 0 | 1 |
| methods/9b-R0 | 64 | 1 | 0.4361 | 0.4307 | 0.2536 | 0.2705 | 0.2757 | 1.5458 | 0 | 1 |
| methods/9b-R2 | 64 | 1 | 0.4277 | 0.4219 | 0.2536 | 0.2741 | 0.2810 | 1.4905 | 0 | 1 |
| methods/9b-R3 | 64 | 0 | 0.4473 | 0.4473 | 0.2000 | 0.3482 | 0.2789 | 1.7555 | 0 | 1 |
| cheap_controls/always-ignore | 64 | 0 | 0.9714 | 0.9714 | 0.0286 | 0.0286 | 0.9714 | infinite | 62 | 1 |
| cheap_controls/class-prior | 64 | 0 | 0.3209 | 0.3209 | 0.5179 | 0.5179 | 0.0821 | infinite | 2 | 1 |
| cheap_controls/previous-handling | 64 | 0 | 0.5099 | 0.5099 | 0.4821 | 0.4821 | 0.5007 | infinite | 32 | 1 |
| cheap_controls/surface-features | 64 | 0 | 0.4407 | 0.4407 | 0.5143 | 0.5143 | 0.4048 | 2.5490 | 0 | 1 |
| secondary_same_confidence/27b-R0-same-confidence | 64 | 0 | 0.4979 | 0.4979 | 0.3964 | 0.3964 | 0.4536 | 1.8726 | 0 | 1 |
| secondary_same_confidence/27b-R2-same-confidence | 64 | 0 | 0.4950 | 0.4950 | 0.4000 | 0.4000 | 0.4500 | 1.8624 | 0 | 1 |
| secondary_same_confidence/27b-R3-same-confidence | 64 | 0 | 0.4979 | 0.4979 | 0.3964 | 0.3964 | 0.4536 | 1.8726 | 0 | 1 |
| secondary_same_confidence/9b-R0-same-confidence | 64 | 1 | 0.6148 | 0.6121 | 0.2536 | 0.2536 | 0.5964 | 2.2773 | 0 | 1 |
| secondary_same_confidence/9b-R2-same-confidence | 64 | 1 | 0.6148 | 0.6121 | 0.2536 | 0.2536 | 0.5964 | 2.2773 | 0 | 1 |
| secondary_same_confidence/9b-R3-same-confidence | 64 | 0 | 0.6550 | 0.6550 | 0.2000 | 0.2000 | 0.6500 | 2.4291 | 0 | 1 |

Paired differences below are positive for the first named method or correct-history condition; interaction is defined above. Omission ranges are descriptive, not confidence intervals. None means only one component. Finite log differences exclude nonfinite pairs and show their denominator. Individual anonymized component contrasts are in READOUT_DIAGNOSTICS.json.

| Contrast | Loss benefit | Components | Omission range | Finite log benefit | Finite pairs | Choice benefit |
|---|---|---|---|---|---|---|
| interaction | -0.0456 | 1 | None | -0.0510 | 63 | not available |
| deliberative_model_package_difference | 0.0351 | 1 | None | 0.0552 | 63 | 0.1464 |
| direct_model_package_difference | 0.0481 | 1 | None | 0.1335 | 63 | 0.1429 |
| structured_versus_direct/27b | -0.0698 | 1 | None | -0.3369 | 64 | 0.0000 |
| structured_versus_direct/9b | -0.0112 | 1 | None | -0.2230 | 63 | -0.0536 |
| within_model/27b | -0.0652 | 1 | None | -0.3140 | 64 | -0.0036 |
| within_model/9b | -0.0195 | 1 | None | -0.2784 | 63 | -0.0536 |

### Recorded resources

Each row sums retained work by branch, family, model and method. Calls, tokens, server and executor seconds are distinct resources. Human exact-program work is in-process and not separately metered by the executor-wall field. These records are not invoices.

| Branch/source/model/method | Routes | Calls | Input tokens | Generated tokens | Server seconds | Executor seconds |
|---|---|---|---|---|---|---|
| A/coauthor-handling/27b/R0 | 64 | 64 | 58983 | 8234 | 395.8183 | 0.0000 |
| A/coauthor-handling/27b/R2 | 64 | 128 | 130486 | 16064 | 529.8620 | 0.0000 |
| A/coauthor-handling/27b/R3 | 64 | 128 | 217962 | 23137 | 786.1058 | 0.0000 |
| A/coauthor-handling/9b/R0 | 64 | 64 | 58983 | 7211 | 348.1392 | 0.0000 |
| A/coauthor-handling/9b/R2 | 64 | 128 | 129465 | 14211 | 223.0789 | 0.0000 |
| A/coauthor-handling/9b/R3 | 64 | 128 | 218296 | 23298 | 341.6223 | 0.0000 |
| A/ghost-opportunity/27b/R0 | 7 | 7 | 4473 | 921 | 58.1120 | 0.0000 |
| A/ghost-opportunity/27b/R2 | 7 | 14 | 10336 | 1706 | 56.0891 | 0.0000 |
| A/ghost-opportunity/27b/R3 | 7 | 14 | 12391 | 1757 | 59.9141 | 0.0059 |
| A/ghost-opportunity/9b/R0 | 7 | 7 | 4473 | 599 | 71.6526 | 0.0000 |
| A/ghost-opportunity/9b/R2 | 7 | 14 | 10014 | 1190 | 20.3687 | 0.0000 |
| A/ghost-opportunity/9b/R3 | 7 | 14 | 12247 | 1880 | 37.6454 | 0.0062 |
| B/coauthor-handling/27b/R0 | 48 | 48 | 43334 | 6094 | 250.5682 | 0.0000 |
| B/coauthor-handling/27b/R3 | 48 | 96 | 160045 | 17473 | 588.9237 | 0.0000 |
| B/coauthor-handling/9b/R0 | 48 | 48 | 43334 | 5377 | 169.7637 | 0.0000 |
| B/coauthor-handling/9b/R3 | 48 | 96 | 160262 | 17552 | 251.8151 | 0.0000 |
| C/coauthor-handling/27b/R1-memory | 24 | 24 | 40761 | 2964 | 153.9031 | 0.0000 |
| C/coauthor-handling/27b/R4-grounded | 24 | 48 | 123993 | 8832 | 320.2537 | 0.0000 |
| C/coauthor-handling/27b/R4-opaque | 24 | 48 | 120531 | 8749 | 314.3167 | 0.0000 |
| C/coauthor-handling/9b/R1-memory | 24 | 24 | 40761 | 2518 | 136.4870 | 0.0000 |
| C/coauthor-handling/9b/R4-grounded | 24 | 48 | 124029 | 9020 | 141.1618 | 0.0000 |
| C/coauthor-handling/9b/R4-opaque | 24 | 48 | 120557 | 8757 | 131.3050 | 0.0000 |
| D/coauthor-handling/27b/R0 | 8 | 8 | 6917 | 1038 | 51.4741 | 0.0000 |
| D/coauthor-handling/27b/R2 | 8 | 16 | 15408 | 2004 | 67.4339 | 0.0000 |
| D/coauthor-handling/27b/R3 | 8 | 16 | 26269 | 2917 | 101.1136 | 0.0000 |
| D/coauthor-handling/9b/R0 | 8 | 8 | 6917 | 852 | 44.0992 | 0.0000 |
| D/coauthor-handling/9b/R2 | 8 | 16 | 15222 | 1700 | 26.9396 | 0.0000 |
| D/coauthor-handling/9b/R3 | 8 | 16 | 26209 | 2972 | 43.9253 | 0.0000 |

### Evidence

[Public results](RESULTS.json), [readout diagnostics and anonymous components](READOUT_DIAGNOSTICS.json), [independent verification](SCIENTIFIC_INSPECTION.json), [admission and exclusions](SCOPED_ADMISSION_PLAN.json). Original private packets, source texts, replies, evaluator labels, provider identities and billing records are retained. No failed original pilot is relabeled as a complete pilot.
