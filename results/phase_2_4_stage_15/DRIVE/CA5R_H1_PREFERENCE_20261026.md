# S15-CA5-R-H1-20261026: complete separate Jester preference comparison

**Hypothesis.** Do a person's joke-topic preferences recur across different jokes after accounting for joke popularity and that person's general rating tendency?

**METHOD.** An exact program compared topic profiles across odd- and even-numbered jokes for all 50,691 approved complete Jester records, using 1,728,830 observed ratings. Eight lexical topics were frozen from all 150 complete joke texts before rating outcomes; one text without learned topic loading retains uniform weights under the separately frozen correction. Separate least-squares person and item effects on each half's actual observed cells remove additive rating generosity and popularity. Correlation measures how similarly a person's topic departures vary across halves, from minus one for opposite profiles to one for matching profiles; the primary equally weights persons and subtracts the rebuilt reference mean.

The full comparison uses 1,000 within-item residual reassignments and 200 within-person outcome reassignments, rebuilding the additive fit and profiles for each reassignment. Its 2,000 paired-person bootstrap samples resample the resulting real and mean-reference correlations with the fitted population adjustment fixed. Missing cells stay missing; no rater is dropped and no rating is imputed. Every source, feature, known-answer check and statistic was reconstructed in a fresh native process before this landing.

The table compares the same real-person mean correlation with two separately rebuilt references. The reference band is its 2.5th to 97.5th percentile across draws. The excess and its 95% interval use paired real-person resampling. Probabilities are one-sided descriptive permutation values, not multiplicity-adjusted confirmation.

| Comparison | Real mean | Reference mean / standard deviation | Reference 95% band | Excess over reference [95% paired interval] | Descriptive probability |
|---|---:|---:|---|---|---:|
| Primary: residuals reassigned among people within each joke | 0.024669 | 0.000034 / 0.002009 | [-0.003950, 0.004050] | 0.024636 [0.020876, 0.028524] | 0.000999001 |
| Outcome control: residuals reassigned within each person and half | 0.024669 | 0.000135 / 0.002025 | [-0.004068, 0.004038] | 0.024534 [0.020726, 0.028473] | 0.004975124 |

**Found.** Supports small joke-topic preference recurrence beyond additive person and item averages in the approved Jester records; this descriptive conditional comparison does not establish demographic-relative harm judgments or value recovery.

The full result is positive under the frozen conjunction of a positive lower interval endpoint and a primary permutation probability below .05. Neither reference triggers the inherited mean-bias warning: each mean is less than a quarter of its reference standard deviation. All 50,691 records remain, with no constant profiles. The ten unrated items remain in the text census and do not acquire invented ratings. The within-person reference is an outcome control, not a second independent dataset.

The validation table reports known constructed answers using the real exposure mask, not additional empirical effects. The null gate is exact for additive person/item effects; the noise gate concerns the mean of twenty fixed worlds, not absence of every individual false alarm.

| Validation or accounting check | Complete observation |
|---|---|
| Additive person/item null | Exactly zero residuals |
| Stable / reversed planted mean correlation | 0.558916 / -0.559733 |
| Twenty noise worlds: ensemble mean | 0.000405, within the frozen 0.03 tolerance |
| Targeted tests and constructed full-bank replay | Thirteen checks pass; original fixture failures and corrections retained |
| Main immutable pins / sealed outputs | 197 / 17 authenticated |
| Full execution and fresh verification | Complete; native workers exited and CPU lease released |
| Main CPU seconds, including replay | 715.875 |
| All construction reserves, preparation, failed attempt, pilot and main | 1260.375 of the original 1800 CPU seconds; no extension |

**Means.** Personal departures can recur in this joke-rating corpus after subtracting additive population responses and overall rating tendency. The average recurrence is small. The comparison is conditional on observed exposure, this joke bank, learned lexical coordinates, fitted population adjustment and the fixed reference banks. Recommendation-dependent exposure is not randomized or repaired by preserving its mask; residual exchangeability remains an assumption. Numeric item halves are not a test of persistence over time. Topic proxies are not validated psychological categories, and no causal mechanism, competence, objective joke quality, individual-person diagnosis or unrestricted-population claim follows.

The curator approved a separate preference comparison because demographic groups and harm labels are absent. The originally proposed demographic-relative harm replication therefore remains open; the existing DICES result is unchanged. The incomplete archive record remains quarantined by the earlier approval and the advertised-population discrepancy remains unresolved. Original failed text features and all pre-outcome corrections remain preserved. This completes CA5's third and final first-generation follow-up; no descendant is commissioned. No new tests were harvested from this operational notice.

The generic completion envelope always withholds scientific admission: it certifies execution, not a claim. Here the pinned main-mode module and its full fresh verification both admit the completed comparison; this landing applies the frozen outcome and control rules. The four quoted forward/reverse probabilities are registered as descriptive diagnostics under the active packet; their registration does not convert the study into confirmatory evidence.

[Original design](../../../../docs/design/stage-15/drive/CA5R_PREFERENCE_20261026.md) · [separate representation correction](../../../../docs/design/stage-15/drive/CA5R_PREFERENCE_H1_20261026.md) · [aggregate receipt](CA5R_H1_PREFERENCE_20261026.json). The aggregate receipt retains both opposite-tail probabilities, each 1.0. Private raw ratings, text, identities and reference-draw vectors are not included in this report.
