# D4 canonical successor: correction prediction remains null

**Hypothesis.** A writer's earlier content corrections predict later suggestion choices better than housekeeping corrections do.
**METHOD.** Reconstruct actual selected suggestions from authenticated CoAuthor records; fit the original correction-direction models on earlier sessions, select their penalty on separate calibration sessions and compare held-out half-Brier gains over uniform choice. Use 2,000 writer resamples and 200 within-writer, menu-size-matched outcome permutations with calibration reselection.
**Found.** The primary contrast is null, and the permutation reference triggers the predeclared bias warning. **Means.** This corrected descriptive comparison does not establish a predictive advantage for content corrections. It neither rejects the broader editing account nor supplies a clean control or an extension admission.

These are human writing-process records read by exact source reconstruction, frozen sentence embeddings and fitted choice models. The canonical choice repair changes 2,510 of 16,855 prepared choices in the source audit. On the actual supported predictive rows, it changes 122 of 2,064 calibration choices and one of 2,083 held-out choices. It changes no training correction, chronological partition, objective, penalty grid or support requirement. Original D4 outputs remain unchanged and source-held.

The table reports improvement in half of the multiclass Brier loss over a uniform distribution across the displayed offers. A positive gain is better prediction. The primary subtracts the housekeeping gain from the content gain. Each row uses the same 20 supported writers. Intervals are 95% writer-bootstrap percentile intervals; probabilities are descriptive two-sided normal-reference Wald approximations, not permutation probabilities. Frozen states follow the percentile interval and expected direction, so they need not agree with a Wald probability threshold.

| Correction source and comparison | Gain or gain difference | 95% interval | Descriptive probability | State |
|---|---:|---|---:|---|
| Model-generated text: content gain | -0.0003716054221 | [-0.001255439122, 0.0003430013553] | 0.3780571112 | null |
| Model-generated text: housekeeping gain | -0.0002861980367 | [-0.0006292019554, -2.196848467e-05] | 0.07409884103 | negative |
| Model-generated text: content minus housekeeping | -8.540738537e-05 | [-0.001063031787, 0.0007360727348] | 0.8554229618 | null |
| Writer-typed text: content gain | -0.001307306672 | [-0.00388719998, 0.0005708570215] | 0.2497870288 | null |
| Writer-typed text: housekeeping gain | -0.001801663161 | [-0.005135738001, 0.0008124625388] | 0.2465023556 | null |
| Writer-typed text: content minus housekeeping | 0.0004943564895 | [-0.003943391637, 0.004641286919] | 0.8212174928 | marginal |

The model comparison restricted to own-text support is exactly the same as the model rows above: both use these same 20 writers. It is retained in the JSON but is not counted twice in the probability ledger. The own-text secondary is not the conditional earlier-style extension and cannot reopen it.

Twenty of the original 61 writers lack the required chronological support of at least three training sessions, one calibration session and one test session. Of the remaining 41, another 21 lack at least five corrections across two training sessions in either required model-text correction class. Both own-text classes happen to be supported for every retained writer. The scoring population is conditional on uniquely selected accept/edit menus with at least two offers; request and acceptance are not predicted. Menus have equal weight within sessions, sessions within writers, and writers within the final mean.

Correction vectors are normalized before-to-after sentence-embedding differences. Separate regularized logistic soft-vote directions are fitted for content and housekeeping corrections, with penalties 0.01, 0.1, 1 and 10. A softmax over the offered suggestions converts the fitted direction into a conditional choice forecast. Calibration selects the penalty; held-out choices never fit the direction. Bootstrap seed is 20261018. The intervals condition on the fitted writer models and observed support.

The table below reports mean cosine similarity between correction-direction pairs from different training sessions, averaged within each writer and then across writers. It describes directional repetition, not forecasting accuracy, hidden intention or causal preference. These cohesion statistics have no paired fake-writer or outcome-shuffle reference of their own. The intervals and descriptive probabilities use the same writer-bootstrap convention.

| Correction source and class | Cross-session cosine cohesion | 95% interval | Descriptive probability |
|---|---:|---|---:|
| Model text, content | 0.02747726103 | [0.01578884128, 0.04103245441] | 3.368102581e-05 |
| Model text, housekeeping | 0.02436342204 | [0.01662809093, 0.03385718037] | 3.50496154e-08 |
| Own text, content | 0.09222805001 | [0.07720454501, 0.1094453932] | 3.933351817e-29 |
| Own text, housekeeping | 0.00705270655 | [0.006498906281, 0.007637665193] | 1.439319564e-129 |

All 200 outcome permutations are finite. Selected positions are shuffled within writer and menu size separately in calibration and test, preserving the same correction fits, menu support and weighting; each permutation reselects the calibration penalty. The reference mean is -0.0005004802172, standard deviation 0.001102945122, and 2.5th/97.5th percentiles [-0.002683524852, 0.001642283532]. The positive-direction permutation probability is 0.3631840796 (73/201). The absolute mean is 0.453767 standard deviations, above the frozen 0.25 threshold: **the bias flag fires**. The raw label “valid reference” means complete finite permutations; it does not mean the reference passed that bias check. This is not a clean-screen result or evidence of equivalence.

**Validity and disposition.** P5 before/after sentence windows can include unchanged context; deterministic content/housekeeping labels are not human intention labels. P3 is unavailable. Repeated correction direction does not prove a preference or predict its later use. The corrected primary remains descriptively null; the broader editing and expertise hypotheses remain open. The conditional earlier-style extension stays unrun and closed by the primary route. Family G's resolved prefix remains held pending earlier source corrections; no family stop is declared and this source successor is not counted again as a new ladder card.

All 53 source/input pins and 137 final artifacts verify. A fresh process reconstructs canonical choices and corrections, refits all writer models and repeats all 200 permutations and bootstrap summaries. The primary matches exactly. Both execution and verification record one thread for every loaded numerical pool. Exact native owner/child exits and CPU lease release verify. Controller elapsed time from owner creation through completion is 74.986193 seconds, within the unchanged 1,800-second combined execution/verification ceiling. Eight focused checks and complete native constructed-source validation preceded this single corpus dispatch. No engineering retry or threshold relaxation was needed.

The original result and its original single-shuffle control remain preserved. Eleven unique probabilities from this completed successor enter the descriptive ledger; they do not enter the confirmatory families. Theory rows, their afterwords and TODO integrate at 20:00 PDT under the active batch policy. Full card and immediate control/routing limits land now.

[Aggregate receipt](D4-predictive-canonical.json).
