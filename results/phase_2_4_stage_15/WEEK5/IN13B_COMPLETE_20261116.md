# IN13B COMPLETE 20261116

**Hypothesis.** The words of a report distinguish nearby feeling labels better than its writer's twenty-one event ratings do.

**METHOD.** Compare five frozen label pairs on the qualified source using five folds that keep whole writers out of training. The ratings arm standardizes its twenty-one predictors in training only and fits logistic regression with inverse penalty strength 1. The word arm uses training-only unigram/bigram term-frequency inverse-document-frequency weights, minimum document count 2, sublinear frequency and inverse penalty strength 10. Average discrimination area equally over folds, then average the word-minus-ratings gain equally over the five pairs. The single practical bar is 0.05. Whole-writer resampling shares each of 2,000 draws across pairs and arms. The interval is conditional on the frozen fitted held-out predictions; it does not include retraining uncertainty. A fresh verification process refits every learner with the same frozen library and independently calculates rank-based discrimination and the complete draw bank.

**Found.** The equal-pair gain is 0.098538 with 95% interval [0.078287, 0.118877], wholly above the 0.05 bar. The frozen scoped rule supports a word advantage. Its bootstrap standard error is 0.010280, approximate detection scale 0.028785 and approximate support scale 0.078785. The shared bootstrap roster contains 1937 writers; all 2,000 draws are valid.

Discrimination area is the probability that a randomly chosen report of the first label ranks above one of the second; 0.5 is chance. Rows are the five fixed pairs. Rating and word columns are equal-fold areas; gains and intervals are descriptive pair components of the one primary, not five extra verdicts.

| Label pair | Ratings area | Word area | Gain | 95% interval | Writers |
| --- | --- | --- | --- | --- | --- |
| pride / joy | 0.617204 | 0.755186 | 0.137982 | [0.099173, 0.178803] | 792 |
| guilt / shame | 0.634482 | 0.702568 | 0.068086 | [0.004269, 0.133488] | 421 |
| fear / sadness | 0.725036 | 0.867715 | 0.142679 | [0.109068, 0.178885] | 846 |
| anger / disgust | 0.741589 | 0.787458 | 0.045869 | [0.008104, 0.083020] | 809 |
| trust / joy | 0.798319 | 0.896392 | 0.098073 | [0.067201, 0.128869] | 818 |

These are the six largest absolute standardized appraisal differences per pair, selected descriptively on the full pair. Signs mean first label minus second. They have no separate inferential gate and are not held-out feature discoveries.

| Pair | Rated event feature | Standardized difference |
| --- | --- | --- |
| pride / joy | goal support | -0.296931 |
| pride / joy | pleasantness | -0.224818 |
| pride / joy | chance responsibility | -0.213678 |
| pride / joy | unpleasantness | 0.204426 |
| pride / joy | chance control | -0.186612 |
| pride / joy | attention | 0.136532 |
| guilt / shame | unpleasantness | -0.396287 |
| guilt / shame | own control | 0.337553 |
| guilt / shame | pleasantness | 0.315226 |
| guilt / shame | wish not to consider the event | -0.254210 |
| guilt / shame | suddenness | -0.213525 |
| guilt / shame | attention | -0.149426 |
| fear / sadness | attention | 0.487208 |
| fear / sadness | violation of social norms | 0.398439 |
| fear / sadness | urgency | 0.387389 |
| fear / sadness | event predictability | -0.293183 |
| fear / sadness | own control | 0.244725 |
| fear / sadness | wish not to consider the event | -0.242074 |
| anger / disgust | goal relevance | 0.565021 |
| anger / disgust | effort | 0.553456 |
| anger / disgust | others control | 0.365631 |
| anger / disgust | attention | 0.339789 |
| anger / disgust | familiarity | 0.308753 |
| anger / disgust | chance control | -0.248104 |
| trust / joy | pleasantness | -0.890719 |
| trust / joy | unpleasantness | 0.786639 |
| trust / joy | wish not to consider the event | 0.607469 |
| trust / joy | goal support | -0.584629 |
| trust / joy | violation of own standards | 0.469204 |
| trust / joy | violation of social norms | 0.388865 |

**Means.** These particular lexical learners retain more label-separating information than the twenty-one-rating learner. This reproduces an exposed computation rather than supplying a blind test. It does not establish that subject matter alone explains the gap, that rated appraisals are causally irrelevant, or that labels identify separate biological channels. Classifier capacity, lexical cues, elicitation and training-set variability remain rivals. The separately labelled all-report reference and the commissioned need-tag extension remain separate runs; neither is inferred from this qualified-population result. Descriptive full-pair word weights stay private.

**Source and interpretation.** The preserved [Crowd-enVENT source](https://doi.org/10.1162/coli_a_00461) is licensed CC BY 4.0. Its qualified roster contains 6,558 of 6,600 prompted reports: 42 declared imagined events are excluded, while 3,030 reports whose writers were not asked about truthfulness remain. Qualified therefore does not mean independently verified real experience. Human supplied labels and ratings are the targets; exact programs perform the calculations. No demographic columns enter these analyses. Retrospective selection to fit an emotion prompt, shared reporting habits and the corpus's elicitation procedure remain rivals to psychological interpretations. Original source pins and prior exposure are preserved. Only aggregates are filed here; identities, row records, raw narratives, predictions and vocabulary weights remain in ignored storage.

**Controls and completeness.** The committed design and its complete constructed known-answer, zero and failure fixtures remain pinned. The applicable-control mapping distinguishes numerical validation from optional unrun empirical permutations; no such permutation is marked passed. All original 2,000 cluster draws and failed-draw rules are retained. A fresh process reconstructs the source and all draws through the declared independent arithmetic; numerical replay is not independent scientific replication. Every plan pin and completion output has been authenticated, both native phases exited successfully, and the recorded owner has exited. No p-value is introduced. Approximate detection scales use 2.8 times the bootstrap standard error; the approximate effect needed to clear the practical bar adds that bar. These slightly optimistic normal approximations do not measure actual population power. Complete records enter the campaign's internal packet; no unfinished-cell score is reported.

**Accounting and evidence.** This final attempt consumed 55.578125 whole-Job CPU-seconds across execution and verification. Its 66 completion-bound files and 183 plan pins authenticate. Original prefixes, preparation, retained failures and the ordinary per-attempt coordination charges remain in the same shared card and family accounting; this receipt does not create or reset an allowance. Terminal and verification hashes are preserved in the companion JSON.
