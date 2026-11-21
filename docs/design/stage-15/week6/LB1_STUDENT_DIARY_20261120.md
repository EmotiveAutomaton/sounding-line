# LB1 · Student diary measurements and source review

The seven registered rows ask whether demanding thought accompanies curiosity, whether the potential presence of romantic partners follows particular earlier situations, and whether arguments accompany anger more than fear. They refer to reported feelings and the situations students perceived. They do not identify a channel or establish which came first within one prompt. [Lattice packet, §3.4](PACKET_EXTENSION_2026-11-19.md)

## Source and prior study

The held openESM member 0060 is release 2.0.0. Its time-series table contains 8,672 assessments and its catalogue lists 199 college students. Beck and Jackson studied a narrower sample of 104. Their preregistered study used person-specific forecasts of subsequent studying, procrastination and loneliness, assessed the accuracy of those forecasts and compared personal, situational and time predictors. The paper also combined family and friend disagreements. The seven within-person contrasts here ask different questions. The design and declared outcomes established this distinction. Published result tables supplied no contrast or tuning decision. Credit Emorie Beck, Joshua Jackson and openESM. The held source carries CC BY-NC 4.0. The research uses it for noncommercial open tests and files aggregates. [Original study and methods](https://doi.org/10.1177/09567976221093307) · [openESM codebook](https://openesmdata.org/datasets/0060_beck/) · [Held release](https://zenodo.org/records/22764751)

The original TSV has SHA-256 `14cc03a8b6886d20b68ee2bff8bdc8aa6baaaccfda307c883a24f121c2f6ca3c` and is 2,473,213 bytes. The held item dictionary has SHA-256 `f727d31c958524abad63a5ec01dbab79bdb6cb139ffe7948ce339f76a6ddd175`. Each named item is present. Curious, content, excited, effective work, inventiveness, dominance, pride, purpose, anger and fear use five point ratings. Intellectual demand, positivity, social opportunity and potential romantic partners use three points. Schoolwork boredom and the two argument items record occurrence as zero or one. Possible partners rates opportunity. It does not measure desire.

## Registered rows

| Row | Model and comparison | Positive practical bar |
|---|---|---:|
| 11 | In the same prompts, compare the slopes of curiosity and contentment on intellectual demand, controlling for positivity. Use standardized within-person linear models. | 0.05 |
| 12–14 | Predict whether perceived romantic opportunity is above its floor. Fit earlier pride, schoolwork boredom and low purpose together. Hold earlier opportunity and current social opportunity. File each coefficient separately. | 0.10 each |
| 15 | Compare the above-floor excitement and contentment slopes on current romantic opportunity, holding current social opportunity. | 0.10 |
| 16 | Compare the standardized anger and fear slopes on reporting any family or friend argument. | 0.05 |
| 17 | Compare the anger and fear coefficients on the product of argument and state dominance in matched above-floor models. Include both main effects. | 0.05 |

All seven require a 95% whole-person interval excluding zero in the registered direction. File linear-rating sensitivities beside the occurrence primaries. The descriptive competence table fits curiosity and excitement on efficiency, inventiveness, social opportunity and dominance jointly. The primary occurrence model uses the established person means and within-person scales. The product is formed from the two centered and scaled predictors following LD2. Two ratings compared within a row use exactly the same completed prompts. Distinct comparisons retain their own denominators. An argument is present if either item is one, absent if both are zero, and otherwise missing. Low purpose is six minus the original five point item.

## Prompt order and checks

The harmonized prompt number is unavailable, and hour blocks can repeat. Use study day, hour and minute. Within a person and day, pair the current response with the immediately preceding recorded time. Exclude transitions touching tied times. An undated response makes that person's lag order ambiguous. A missing clock within a known day makes that day's order ambiguous. Preserve other eligible days and all valid same-prompt rows. Do not bridge an intervening response whose ratings are missing. File source counts, ordering exclusions and per-model support. Resample the full sorted person roster 2,000 times with indexed source seed 202611190060. Keep the same multiplicity on both sides of every contrast. Replay the bank in a fresh process before scoring.

DESIGN CHECK. Known-answer fixtures exercise the two response scales, original item names, ties and missing history, whole-person resampling, separate source denominators, shifted floors, constant or separated fits, and the sign of a planted contrast. Source bytes and dictionary pins must match before either execution phase. Current ratings share one reporting occasion. Differential reporting noise can create an apparent occurrence interaction. Acting dominantly can follow an argument or anger.
