# Does acting more dominantly change the balance of reported anger and nervousness?

In each of three diary cohorts, test whether an unpleasant interaction goes with a larger increase in anger than in nervousness when the same person reports acting more dominantly. Rows 18–20 of the lattice belong to members 0042, 0043 and 0044 respectively. Keep the three estimates and intervals separate. [November 19 packet, §§3.0 and 3.4](PACKET_EXTENSION_2026-11-19.md)

## Source and prior work

Mostajabi and Wright studied disinhibition and its facets as person-level predictors of average daily affect and interpersonal behaviour. The registration documents earlier work using these samples on antagonism, complementarity and stress. Those analyses motivate the question about anger and dominance. The particular within-person interaction contrast below is a secondary analysis of these data. This classification uses the authors’ study design, hypotheses, measures and registration history. Credit Mostajabi, Wright and openESM. All three held releases are version 2.0.0 under CC BY-NC 4.0. Their use here is noncommercial research with aggregate returns. [Authors’ preprint](https://doi.org/10.31219/osf.io/3szng) · [Original registration and previous uses](https://osf.io/7a5de)

| Member | Catalogue people | Source prompts | During-interaction or momentary feelings | Registered row |
|---|---:|---:|---|---:|
| 0042 | 342 | 17,761 | During the interaction | 18 |
| 0043 | 330 | 11,683 | During the interaction, using the harmonized dictionary fields | 19 |
| 0044 | 396 | 8,768 | Momentary, on prompts reporting an interaction | 20 |

The catalogue counts describe source coverage. The analysis reports the roster with an identifier, the number reporting an interaction, complete prompts and contributing people for each cohort. Each member’s original TSV byte count, SHA-256 and released item-dictionary SHA-256 are bound in the [source adapter](../../../../runners/drive/cards/week6_lb2_source_v1.py). The admission also verifies the licence, source record, layout and exact header.

## Items and comparison

Require a reported interaction (`interaction = 1`). Unpleasantness is 100 minus happy. In 0042 and 0043 use `happy_interaction`, `angry_interaction` and `nervous_interaction`. In 0044 use `happy`, `angry` and `nervous`. Higher `dom_sub_you` means more assertive, dominant or controlling. The authors specify a bipolar slider from −50 to +50 in all three cohorts. The main coding field and 101 response categories agree. The secondary labels in 0042 give zero at its lower endpoint and +50 at its upper endpoint. Use the authors’ signed coding and retain the documented discrepancy. An out-of-range value stops that source for review.

Use the same complete prompts for both feelings, both predictors and both models. For each predictor subtract that person’s mean over those prompts and divide by the pooled within-person standard deviation. In Form O fit a separate plain logistic regression for each feeling, including an intercept, both standardized predictors, their product and both person means. A feeling counts as above the packet’s slider floor when its 0–100 rating **exceeds five**. Scores from zero through five are in the floor category. The primary is the anger product coefficient minus the nervousness product coefficient. Its unit is a difference in log-odds interaction coefficients. A positive estimate of at least 0.05 with its 95% interval above zero meets the registered bar. Also record whether the entire interval exceeds 0.05.

For Form L, center and standardize each rated outcome within person with the pooled within-person scale. Fit the same standardized main terms and their product by least squares and report the difference in product slopes. Report main and product coefficients for both outcomes, the floor counts and both contrasts. The installed diary arithmetic qualifies plain logit and linear fits. The chess conditional-choice solver uses a different likelihood. The optional within-person conditional binary logit has no qualified diary implementation.

Use 2,000 indexed whole-person draws per cohort. Draw from the roster before exclusions, carrying the same multiplicity through both outcomes. The respective source seeds are 202611190042, 202611190043 and 202611190044. Refit on each draw and compare all cells against a fresh replay with independent regression arithmetic. Keep undefined and separated estimates in place. Any undefined draw leaves that metric’s interval unavailable. Below 20 contributing people, file the pooled within-person comparison as descriptive and mark the registered row unsupported. Across the three cohorts one LB2 budget covers the counted fixture, pilots, original banks and replays. At 100 original draws per member review the full projection before continuing.

## Design check

LESSONS §§3–5. Identical angry and nervous ratings give an exact zero contrast. A planted anger-specific product should be positive. Constructed cases check the slider boundary at five and six, item selection in all three cohorts, coding polarity, missing people and prompts, shared draws, invariance to a common change in scale origin, support loss, separation and independent numerical agreement. A source mismatch stops that member before fitting. The cost fallback is a prospectively fixed sample of whole people under the packet’s existing rule if the full target exceeds its allowance.

Dominance describes what the respondent did. Anger may precede that behaviour. The three feelings and the behaviour were reported on one occasion. Differential response noise can change a Form O slope. The third sample’s momentary measure and the second sample’s wording uncertainty limit a direct comparison among the three estimates.
