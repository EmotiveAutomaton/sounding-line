# P3C CALIBRATION COMPLETE 20261027

**Hypothesis.** Can the commissioned CPU classifier distinguish edits that change meaning from those that do not well enough to supply edit-intent labels for later comparisons?

**METHOD.** Authenticate the exact IteraTeR checkpoint and tokenizer, all completed edit-pair sources and the two hundred annotations frozen blind before prediction. Census the untruncated token lengths of all 203,462 pairs; time the original thousand events and predict all two hundred calibration pairs in their fixed order. Collapse the five categories to meaning-changed versus the other four, and compute Cohen kappa, agreement corrected for the class frequencies. Require the unchanged threshold of 0.6. Independently reconstruct the complete source census and all 1,200 predictions in a fresh native process, retaining numerical and categorical parity. At landing, reconstruct the complete agreement tables and kappa again from sealed predictions and annotations.

**Found.** The edit-intent classifier fails its frozen agreement gate against agent-made labels; population edit-intent labels remain unadmitted.

The table compares every frozen agent label (rows) with the classifier label (columns), after the predetermined binary collapse. These are agent judgments about visible edits, not human ground truth or recovered private intentions.

| Agent-made reference | Classifier: no meaning change | Classifier: meaning change | Total |
|---|---:|---:|---:|
| No meaning change | 191 | 3 | 194 |
| Meaning change | 5 | 1 | 6 |
| Total | 196 | 4 | 200 |

Raw agreement is 0.96, while the class-frequency chance agreement is 0.9512. Cohen kappa is 0.18032786885245752, below the frozen 0.6 requirement. The full five-class table and all label marginals remain sealed in the complete summary. The event-uniform sample is strongly imbalanced; that is a limitation of this fixed calibration, not permission to balance, relabel, replace or tune it after seeing predictions. No interval or p-value was specified or introduced.

**Means.** This completed instrument result blocks population use of this checkpoint for the commissioned edit-intent consumers. It is not an execution defect and licenses no gate-healing retry. All 203,462 source pairs fit the exact paired-token limit without clipping or omission, and numerical replay passes, but those facts do not rescue semantic validity. No population intent labels, human purpose inference or downstream effect is admitted. The instrument ledger carries this result; the theory remains unchanged.

The packet routes the failed classifier to Gear 3 node P as a separate second labeler. That route still requires the campaign order, concrete transfer and spending admission and its own blind calibration; no provider request is made here. The deterministic PP4/WD2 fallback is not activated, because the second labeler has not failed. Existing source/cost and GPU holds remain. This shared pass registers no new follow-up generation, and no new hypothesis is harvested from the operational wake.

The first thousand predictions use 322.0625 CPU seconds and the two hundred calibration predictions use 60.328125. The direct population forecast from the timing set is 65527.480375 CPU seconds before replay or overhead; it is a diagnostic rate projection, not a dispatch or validity admission. Complete execution and independent replay use 823.1875 CPU seconds. Cumulative charges and construction/test reserves are 1185.390625 of the original 14,400-second box. All native workers exited and released their lease. The wider commissioned queue remains underbuilt, rather than finished. Earlier running snapshots are historical. No GPU restart, paid request or external transfer occurred.
