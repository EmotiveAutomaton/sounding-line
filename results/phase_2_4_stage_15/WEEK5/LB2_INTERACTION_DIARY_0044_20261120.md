# LB2 INTERACTION DIARY 0044 20261120

**Limited sensitivity.** Approximate detectable magnitude 0.0942, against a 0.05 bar.

**Question.** In unpleasant interactions, does acting more dominantly change the odds of reporting anger more strongly than the odds of reporting nervousness?

**Method.** Include reported interactions with all required items present. Unpleasantness is 100 minus happiness. Within each person, center unpleasantness and reported dominance and scale each by its pooled within-person standard deviation. Fit above-five anger and above-five nervousness separately using identical reports, both main terms, their product and both person means. Subtract the two product coefficients. Refit on 2,000 shared whole-person draws and reproduce every draw in a fresh process. The sensitivity uses the full feeling ratings in a linear model. [Frozen definitions](../../../docs/design/stage-15/week6/LB2_INTERACTION_DIARIES_20261120.md).

The registered anger-minus-nervousness interaction in cohort 0044 was inconclusive. The matched analysis used 386 people and 4,916 interaction reports.

| Contrast | Estimate | 95% interval | Valid draws |
|---|---:|---|---:|
| Registered occurrence | 0.0404 | [-0.0221, 0.1076] | 2000 |
| Descriptive occurrence | 0.0404 | [-0.0221, 0.1076] | 2000 |
| Linear ratings sensitivity | 0.0537 | [0.0062, 0.1022] | 2000 |

The registered bar is +0.05 in log-odds interaction units, with the interval above zero. Entire interval above the bar: no. Bootstrap SD 0.0336, approximate detectable magnitude 0.0942, approximate magnitude for support 0.1442. These last two quantities use the normal-reference 2.8-SD rule. The complete coefficient table retains every unavailable fit.

**Population.** Momentary ratings on interaction prompts. The original source contained 8,768 prompts from 396 identified roster members. 387 people reported interactions. There were 3,776 prompts without an interaction, 37 with missing interaction status and 39 interaction reports with incomplete required ratings. Among complete reports, 2,010 anger ratings and 2,704 nervousness ratings exceeded five.

**Limits.** The same person rated their behaviour and feelings on one occasion. Anger may have preceded the reported dominance. Unequal response noise can change above-floor slopes. This cohort rated how they felt at the prompt, which can differ from feeling during the interaction. The optional within-person conditional-logit sensitivity lacked a qualified binary diary solver. The full rating-scale sensitivity is shown above.

**Integrity and cost.** A 100-draw pilot used 1.65625 CPU seconds. It authenticated 7 output files. The completed run and replay used 33.4688 CPU seconds and authenticated 250 output files and 88 frozen inputs. One 14-case qualification was charged once across all three cohorts. Combined measured cost was 158.297 CPU seconds of the shared 20,000-second allowance.

**Source credit.** Mostajabi and Wright and openESM, release 2.0.0, CC BY-NC 4.0. [Authors’ study](https://doi.org/10.31219/osf.io/3szng) · [Registration](https://osf.io/7a5de).

[Complete coefficients](LB2_INTERACTION_DIARY_0044_20261120_COEFFICIENTS.csv) · [Aggregate receipt](LB2_INTERACTION_DIARY_0044_20261120.json). [Signed comparison sheet](LB2_INTERACTION_DIARY_0044_20261120_SHEET.md) · [Figure](LB2_INTERACTION_DIARY_0044_20261120.png).