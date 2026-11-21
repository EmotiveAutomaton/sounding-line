# LB2 INTERACTION DIARY 0043 20261120

**Limited sensitivity.** Approximate detectable magnitude 0.0622, against a 0.05 bar.

**Question.** In unpleasant interactions, does acting more dominantly change the odds of reporting anger more strongly than the odds of reporting nervousness?

**Method.** Include reported interactions with all required items present. Unpleasantness is 100 minus happiness. Within each person, center unpleasantness and reported dominance and scale each by its pooled within-person standard deviation. Fit above-five anger and above-five nervousness separately using identical reports, both main terms, their product and both person means. Subtract the two product coefficients. Refit on 2,000 shared whole-person draws and reproduce every draw in a fresh process. The sensitivity uses the full feeling ratings in a linear model. [Frozen definitions](../../../docs/design/stage-15/week6/LB2_INTERACTION_DIARIES_20261120.md).

The registered anger-minus-nervousness interaction in cohort 0043 was supports. The matched analysis used 328 people and 7,769 interaction reports.

| Contrast | Estimate | 95% interval | Valid draws |
|---|---:|---|---:|
| Registered occurrence | 0.0873 | [0.0458, 0.1321] | 2000 |
| Descriptive occurrence | 0.0873 | [0.0458, 0.1321] | 2000 |
| Linear ratings sensitivity | 0.0922 | [0.0560, 0.1292] | 2000 |

The registered bar is +0.05 in log-odds interaction units, with the interval above zero. Entire interval above the bar: no. Bootstrap SD 0.0222, approximate detectable magnitude 0.0622, approximate magnitude for support 0.1122. These last two quantities use the normal-reference 2.8-SD rule. The complete coefficient table retains every unavailable fit.

**Population.** During-interaction ratings. The original source contained 11,683 prompts from 330 identified roster members. 328 people reported interactions. There were 3,754 prompts without an interaction, 106 with missing interaction status and 54 interaction reports with incomplete required ratings. Among complete reports, 3,856 anger ratings and 4,602 nervousness ratings exceeded five.

**Limits.** The same person rated their behaviour and feelings on one occasion. Anger may have preceded the reported dominance. Unequal response noise can change above-floor slopes. The harmonized during-interaction field names were used. Their original wording is less certain. The optional within-person conditional-logit sensitivity lacked a qualified binary diary solver. The full rating-scale sensitivity is shown above.

**Integrity and cost.** A 100-draw pilot used 1.85938 CPU seconds. It authenticated 7 output files. The completed run and replay used 49.4375 CPU seconds and authenticated 250 output files and 88 frozen inputs. One 14-case qualification was charged once across all three cohorts. Combined measured cost was 158.297 CPU seconds of the shared 20,000-second allowance.

**Source credit.** Mostajabi and Wright and openESM, release 2.0.0, CC BY-NC 4.0. [Authors’ study](https://doi.org/10.31219/osf.io/3szng) · [Registration](https://osf.io/7a5de).

[Complete coefficients](LB2_INTERACTION_DIARY_0043_20261120_COEFFICIENTS.csv) · [Aggregate receipt](LB2_INTERACTION_DIARY_0043_20261120.json). [Signed comparison sheet](LB2_INTERACTION_DIARY_0043_20261120_SHEET.md) · [Figure](LB2_INTERACTION_DIARY_0043_20261120.png).