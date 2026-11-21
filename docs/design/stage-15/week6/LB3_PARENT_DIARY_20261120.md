# LB3 · Parents’ daily reports of stress and feelings

Five registered comparisons use the evening reports of adults living with a schoolchild during the first COVID-19 lockdown in Germany. Each adult rated their own feelings, their child's feelings and the day's events. The catalogue lists 562 participants and up to 21 observations per person. The held diary has 7,747 records. The source and the diary have distinct denominators. [Lattice packet](PACKET_EXTENSION_2026-11-19.md) · [openESM member 0072](https://openesmdata.org/datasets/0072_neubauer/)

## Source and prior study

The held release is version 1.0.0, under CC BY 4.0. Credit Andreas Neubauer and colleagues and openESM. The published study registered same-day associations between autonomy-supportive parenting, parental need fulfillment and child well-being. It also examined reciprocal changes across days and longer-term family adjustment. The present comparisons use individual feeling and stressor items from that diary. The published hypotheses were used to establish scope before inspecting the study outcomes. [Published design and hypotheses](https://onlinelibrary.wiley.com/doi/full/10.1111/cdev.13515) · [Held release](https://zenodo.org/records/17361779)

Use the harmonized time-series table alone. Its 2,793,431 bytes have SHA-256 `767cc1edcdfdf48b799499f07f02a1d3e3978dc10148c20f530e3b126afc284e`. The item dictionary has SHA-256 `0086a6bb082826acf4e5b14e7c20775059c2edb281a51854a0544cc259339dbb`. All required items occur in the held header and dictionary. The eight yes-or-no stressors record 1 for an event and 0 for its absence in the harmonized data. The need, feeling and parenting ratings run from 1 to 7. Time with the child has separate hour and minute entries.

## Estimands

Use Form L. Center every predictor and outcome on the reporting parent's mean over the rows of that fit, then scale by its pooled within-parent standard deviation. Fit the predictors together. Each registered difference uses a common set of complete reports for its component slopes. For the full descriptive tables, use each outcome’s own available reports and give its denominator. Intervals draw 2,000 whole parents from the fixed original roster, retaining the same multiplicities across all rows. A fresh process reproduces every draw. The source seed is 202611190072.

| Row | Within-parent comparison | Direction and practical bar |
|---|---|---|
| 21 | On feeling blocked, compare the slopes of anger and fear. Average the ratings for being told what to do and acting against one's will. Replace those two predictors with their mean in this fit and retain the other 14 event predictors. | Anger minus fear, at least 0.05 |
| 22 | On a reported health or financial stressor, compare mean fear and worry slopes with anger. Represent either stressor with a single indicator in this fit and retain the other 14 event predictors. | Mean fear and worry minus anger, at least 0.05 |
| 23 | On feeling excluded, compare sadness with anger while holding the other 15 event predictors. | Sadness minus anger, at least 0.05 |
| 24 | On the parent's rating of the child's distress, compare parental worry with anger, controlling for time together. Average the child's sadness, fear and worry before centering. | Worry minus anger, at least 0.05 |
| 25 | Predict having fun together from parental fear, sadness, anger and exhaustion together, controlling for disagreements and time with the child. | Fear slope minus sadness slope, at most −0.05 |

Each registered interval must exclude zero in the stated direction. Retain both endpoints and the separate whole-interval practical-bar reading. File the complete four-by-sixteen parent-feeling table and the coefficients for all ten parent feelings and discussing worries against child distress and time together.

Build the roster before analytical exclusions. One study day represents one report per parent. Count and exclude observations with a missing day or an ambiguous duplicated parent-day. A composite rating requires all its components. Either documented positive establishes a health or financial event. Both negatives are required to establish absence. Time together is 60 times hours plus minutes. An absent component leaves time unknown. Count invalid and missing durations separately. Other complete reports from the same person remain eligible.

## Qualification and limits

DESIGN CHECK. Under identical outcome profiles the corresponding difference is exactly zero. Planted effects have the registered signs for the positive and negative contrasts. Tests cover source pins, coding after harmonization, a missing child rating, partial event information, discrepancies in time fields, duplicated parent-days, whole-parent multiplicities and agreement between the two numerical paths. A constant or rank-deficient predictor prevents identification of the affected model. Record its missing cells and failed draws. The pilot measures the first 100 resamples before full admission under the inclusive 20,000 CPU-second card ceiling.

Both people's emotions came from one parent's evening report. A parent in a bad mood can rate the child more negatively and recall more conflict. These data cannot separate that possibility from a response to the child's feelings. They describe households in an exceptional three-week period.
