# TD6 complete comparison

**Hypothesis.** Do disgust-tagged comments contain less expressed modelling of another mind than matched anger-tagged comments?

**METHOD.** Match without replacement within subreddit and whitespace-length decile. Require two disgust labels and no anger, versus two anger labels and no disgust; use the predeclared one-label fallback if fewer than 300 pairs remain. Count only the exact subject/verb token patterns, express hits per token, and compare rates relatively to anger. Resample whole matched pairs within subreddit 2,000 times; retain the original pairs in the he/she/they companion. Constructed signed, null, matching and zero-denominator checks precede human execution; the entire computation independently replays.

**Found.** The registered disgust-versus-anger mind-language comparison is inconclusive; the sparse person-targeted companion cannot establish reduced mental modelling.

The strict rule yields 732 disgust candidates, 1,485 anger candidates and 190 matched pairs, activating the frozen fallback. The fallback yields 2,786 disgust candidates, 4,380 anger candidates and 1,437 pairs. The primary does not decide whether the relative reduction exceeds 10%.

Each row shows matched pairs, exact phrase hits and lexical tokens in each arm, relative rate difference and the within-subreddit 95% interval. A difference of -0.1 means 10% fewer hits per token relative to anger. The companion is not the primary.

| Population | Pairs | Disgust hits / tokens | Anger hits / tokens | Relative difference | Interval | Mechanical rule |
|---|---:|---:|---:|---:|---|---|
| primary | 1437 | 34 / 20067 | 36 / 20018 | -0.0578617 | [-0.378018, 0.414195] | inconclusive |
| person_targeted | 49 | 2 / 950 | 5 / 974 | -0.589895 | [-0.659329, -0.485744] | supports |

The primary stratum support is {"subreddits": 412, "singleton_subreddits": 94, "pairs_in_singletons": 94}; the person-targeted support is {"subreddits": 41, "singleton_subreddits": 35, "pairs_in_singletons": 35}. These counts describe subreddit resampling, not people. Singleton strata cannot vary their pair under the specified bootstrap. The companion has only two versus five phrase hits; its narrow conditional interval must not be read as precise evidence about new subreddits or mental modelling. No undefined bootstrap draws occurred. The observed phrase dictionary is a lexical proxy and misses many ways of describing minds. Its constructed arithmetic checks do not validate construct coverage. Sensitivity was untested at the original landing; the complete registered rare-count calibration now records limited sensitivity and poor companion coverage under its conditional model (S15-TD6-IC-SENSITIVITY-20261106). The human estimates and original verdicts are retained.

**Means.** Preserve the primary inconclusive result and the separately labelled companion. Register a sensitivity check that includes rare phrase counts and the observed stratum sizes before interpreting a non-detection as absence.


Design commit: `abeee0d8b773fd223bd17771438571698e2ec423`. Complete execution and independent replay used 29.125 CPU seconds. All pinned sources, output hashes and native exits verify. No p-value is added. Raw text and identities remain private.
