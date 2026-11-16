# IN13B REFERENCE 20261116

**Hypothesis.** The words of a report distinguish nearby feeling labels better than its writer's twenty-one event ratings do; the all-report preflight should be reproducible at its original population scope.

**METHOD.** Use all 6,600 reports, including the 42 declared imagined events, as the separately labelled analyst reference. Retain the same five label pairs, five whole-writer held-out folds and frozen learners as the qualified primary. The ratings arm standardizes in training only and fits logistic regression with inverse penalty strength 1. The word arm uses training-only unigram/bigram term-frequency inverse-document-frequency weights, minimum document count 2, sublinear frequency and inverse penalty strength 10. Average discrimination area equally over folds, and the word-minus-ratings gain equally over pairs. Resample whole writers 2,000 times with shared draws across arms and pairs. The interval is conditional on the fitted held-out predictions and excludes retraining uncertainty. Fresh verification refits the frozen learners and independently computes rank-based discrimination and the complete draw bank.

**Found.** The complete equal-pair reference gain is 0.096454, with 95% interval [0.076544, 0.116727], across 1,944 writers in the bootstrap roster. The bootstrap standard error is 0.010177, approximate detection scale 0.028495 and approximate support scale 0.078495 against the design's 0.05 bar. All 2,000 draws are valid. As prospectively specified, this exposed all-report reference receives no supports/against verdict. It is not an independent replication of the qualified primary.

Each row is one label pair. Discrimination area is the probability that the classifier ranks a randomly selected first-label report above a second-label report; 0.5 is chance ranking and 1 is perfect. The gain subtracts the ratings arm from the words arm. Intervals are conditional whole-writer reference intervals, not separate primary decisions.

| Label pair | Ratings area | Words area | Gain | 95% interval | Writers |
| --- | --- | --- | --- | --- | --- |
| pride / joy | 0.612972 | 0.757495 | 0.144523 | [0.105098, 0.184810] | 793 |
| guilt / shame | 0.627458 | 0.699711 | 0.072253 | [0.008050, 0.135127] | 423 |
| fear / sadness | 0.727846 | 0.862564 | 0.134717 | [0.101047, 0.169923] | 849 |
| anger / disgust | 0.748633 | 0.786772 | 0.038138 | [0.000895, 0.074682] | 811 |
| trust / joy | 0.798300 | 0.890936 | 0.092636 | [0.060853, 0.123485] | 824 |

The following six largest absolute appraisal differences for each pair are descriptive, source-selected features, not held-out hypotheses. Each signed number is the first-label mean minus the second-label mean, in the declared standardized rating units. No interval or scientific verdict is assigned to these thirty features. Vocabulary weights and words remain private.

| Label pair | Appraisal | Standardized difference |
| --- | --- | --- |
| pride / joy | goal support | -0.293225 |
| pride / joy | pleasantness | -0.226681 |
| pride / joy | chance responsibility | -0.211500 |
| pride / joy | unpleasantness | 0.204639 |
| pride / joy | chance control | -0.177356 |
| pride / joy | attention | 0.132090 |
| guilt / shame | unpleasantness | -0.393920 |
| guilt / shame | own control | 0.339025 |
| guilt / shame | pleasantness | 0.314427 |
| guilt / shame | wish not to consider the event | -0.256986 |
| guilt / shame | suddenness | -0.212219 |
| guilt / shame | others control | -0.148828 |
| fear / sadness | attention | 0.487266 |
| fear / sadness | violation of social norms | 0.402921 |
| fear / sadness | urgency | 0.386732 |
| fear / sadness | event predictability | -0.298441 |
| fear / sadness | own control | 0.242343 |
| fear / sadness | wish not to consider the event | -0.239737 |
| anger / disgust | goal relevance | 0.560538 |
| anger / disgust | effort | 0.556314 |
| anger / disgust | others control | 0.366865 |
| anger / disgust | attention | 0.343260 |
| anger / disgust | familiarity | 0.305120 |
| anger / disgust | chance control | -0.245336 |
| trust / joy | pleasantness | -0.887391 |
| trust / joy | unpleasantness | 0.778074 |
| trust / joy | wish not to consider the event | 0.616983 |
| trust / joy | goal support | -0.574426 |
| trust / joy | violation of own standards | 0.474706 |
| trust / joy | violation of social norms | 0.395356 |

**Means.** The supplied all-report computation is now reproduced with complete numerical verification at its declared scope. The qualified-event primary remains the governing study population. Both comparisons share reports, learner choices, prior exposure and lexical cues, so this reference adds neither independent confirmation nor identification of the event's subject matter as the causal carrier of a feeling. No biological channel claim follows.

**Source and scope.** The preserved [Crowd-enVENT source](https://doi.org/10.1162/coli_a_00461) is licensed CC BY 4.0. The qualified roster contains 6,558 of 6,600 prompted reports, excluding 42 declared imagined events while retaining 3,030 reports whose writers were not asked about truthfulness. Qualification therefore does not mean independent verification of real experience. Human supplied labels and ratings are the targets; exact programs perform the calculations. These are adult retrospective reports elicited to fit a feeling prompt. Prompt selection, common reporting habits and retrospective judgments remain rivals. No demographic columns enter these analyses. Individual records, joins, narratives, fitted predictions and vocabulary weights remain in ignored storage; only aggregate results are filed.

**Completeness and limits of validation.** All 2,000 registered whole-writer draws are retained, with no failed draw removed or replaced. The committed design, complete constructed known-answer and zero fixtures, original source pins and a fresh independent replay are preserved. Numerical replay validates a computation, not an independent scientific replication. Applicable controls do not include unrun empirical permutations; none is marked passed. Plan pins, all completion outputs and exact native exits authenticate. No p-value is introduced. The approximate detection scale is 2.8 times the bootstrap standard error; the approximate support scale adds the practical bar. These optimistic normal approximations are not measured population power. Full results enter the campaign's internal packet under its final-packet reporting rule.

**Accounting and evidence.** This final attempt used 39.015625 whole-Job CPU-seconds across execution and verification. All 66 completion-bound outputs and 183 plan pins authenticate. Earlier preparation, prefixes, failures and ordinary coordination charges remain in the same original card and family budgets. This filing resets no allowance. Exact terminal, plan, output and verification hashes are preserved in the aggregate receipt.
