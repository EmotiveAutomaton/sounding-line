# Recalled anger and sadness in the original ISEAR questionnaire

R1.i asks whether unexpected events are associated with more intense anger and whether that association is larger for anger than for sadness. The two proposed thresholds are each 0.08 standard deviations. A qualifying contrast must reach its own threshold with its 95% interval above zero. Both contrasts must qualify to support the joint prediction. The analyst separately predicted a positive anger slope no larger than the sadness slope. [Commissioning packet, section 5.3](PACKET_EXTENSION_2026-11-20.md)

## Source and eligibility

Use the original numeric responses in the ISEAR Access database, table `DATA`. The verified archive contains a single database. Its edition has SHA-256 `04ffbc24950f4effd85ede4b735f2a16bbec5a3a21262e5d7879e6556ead902e` after extraction. A schema-only query returned the requisites below. The original ISEAR questionnaire supplies the response categories and their direction. The separate SPSS edition labels the four families of analysis variables as series-mean transformations. The original Access responses preserve the questionnaire’s inapplicable and missing answers.

| Role | Original field | Coding |
|---|---|---|
| Elicited feeling | EMOT | 3 anger, 4 sadness |
| Feeling intensity | INTS | 1 to 4, increasing intensity |
| Expectedness | EXPC | 1 to 3, increasing expectation. Compute unexpectedness as 4 minus the response |
| Event pleasantness | PLEA | 1 pleasant, 2 neutral, 3 unpleasant |
| Causal agent | CAUS | 1 self, 2 close persons, 3 other persons, 4 impersonal agency. Fit category indicators |
| Person grouping | COUN, CITY, SUBJ | Verify the site and local subject number using the repeated questionnaire structure before scoring |

Read only identity and feeling codes to check the grouping first. Tabulate the number of anger and sadness reports, the number of people supplying both, incomplete identity codes and duplicate person-by-feeling records. Each person could give at most one original report per feeling. Hold an ambiguous key for source review. Do not choose a key by comparing fitted effects. Use eligible whole people from the union of the two feeling rosters and retain their reports together in each draw. Record the individual and joint complete-case counts. Exclude an inapplicable, missing or out-of-range response from the affected fit and report the reason. Source narratives, demographic values and individual responses stay private.

## Estimation and checks

For each feeling, fit intensity on reversed expectedness, entered with ordinal pleasantness and nominal causal agency. Standardize intensity, reversed expectedness and pleasantness within the complete reports for that feeling. Use the same person multiplicities in both fits and recompute the means, scales and adjusted slopes in every draw. Categories absent from a particular resample contribute no separate coefficient there. A singular target or zero intensity or predictor variance leaves that contrast unidentified. Preserve the sibling slope when one outcome lacks support. Report the anger slope, sadness slope and their paired difference using 2,000 whole-person bootstrap draws. Report how many draws are defined for each quantity. A population interval requires a complete valid bank and the packet’s cluster floor.

The constructed fixture must recover known adjusted slopes and their difference after adding an agency association, reject duplicated person-feeling keys and invalidate a constant target predictor. The verification path independently solves the weighted regressions and checks both source rosters, every draw and all reported limits. The two models and the source grouping will be frozen before outcomes. The source was collected by Klaus R. Scherer, Harald G. Wallbott and the international ISEAR collaborators for research on recalled emotional events.

Unexpectedness is measured by whether the person expected the event. The item does not measure how quickly it unfolded. The ratings concern a remembered event selected for a specified feeling.
