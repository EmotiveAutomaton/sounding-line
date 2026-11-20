# LA6 STRICT ONSETS 20261120

**Question.** Can the observable context predict a new laugh after an utterance ends in a held-out meeting?

**Finding.** Both windows and both feature sets left prediction at the registered area of 0.60 inconclusive. The originally registered windows are reported separately.

Exclude utterances overlapping observed vocal laughter from one second before their start through their end. Match cases to controls from the same speaker and meeting using the original 30-second separation, time rule, deterministic ties and replacement. A case requires a new onset strictly after utterance end and within the indicated window. The length tolerance is two words or one fifth of the case utterance, whichever is larger. Each window used the original strict pairs.

The original five meeting folds, training-only transforms, C=1 model and both feature sets were fixed. Elapsed laughter history is present in one set. Matching, timing and word-count definitions are identical across its two arms. Predictive area is computed on held-out meetings. An interval wholly above 0.60 supports the registered threshold and one wholly below it counts against. An interval that spans 0.60 leaves that comparison inconclusive. Intervals are nominal. Chance is 0.50. Detection above chance and the effect needed for support use 2.8 times each arm’s bootstrap standard error.

| Window in seconds | Feature set | Meetings | Area | Whole-meeting 95% interval | Bootstrap SE | Detectable area above chance | Area for 80% support | Decision |
|---:|---|---:|---:|---|---:|---:|---:|---|
| 1 | With history | 202 | 0.5984 | 0.5845 to 0.6132 | 0.0075 | 0.0209 | 0.6209 | inconclusive |
| 1 | Without history | 202 | 0.5920 | 0.5777 to 0.6071 | 0.0076 | 0.0212 | 0.6212 | inconclusive |
| 2 | With history | 205 | 0.6059 | 0.5958 to 0.6166 | 0.0054 | 0.0152 | 0.6152 | inconclusive |
| 2 | Without history | 205 | 0.5966 | 0.5866 to 0.6071 | 0.0053 | 0.0150 | 0.6150 | inconclusive |

| Window in seconds | Original utterances | Overlap exclusions | Strict cases | Strict matched pairs | Distinct strict controls | Reused strict copies | Length-matched pairs | Distinct length controls | Reused length copies |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 221,947 | 107,878 | 2,911 | 2,888 | 2,698 | 190 | 2,867 | 2,713 | 154 |
| 2 | 221,947 | 107,878 | 5,734 | 5,690 | 4,950 | 740 | 5,654 | 5,112 | 542 |

The aggregate record includes the full act-category point table, the reference category, the unavailable-draw counts and all arm-specific limitations. Absent categories prevent population intervals for those odds. The later pooled act comparison has its own frozen dictionaries. The annotation identifies a new vocal laugh in recorded meetings. It cannot establish surprise, shared inference, a causal role for length or the proposed PLAY mechanism. Comparison with the parent also changes eligibility and matching, which precludes assigning a causal share to word count.

The 100-draw pilot used 44.9062 native CPU seconds. The full continuation and fresh replay used 261.156. All 8,103 output hashes, both source preparations, every held-out point and every draw passed verification. Source credit belongs to the AMI Meeting Corpus and ICSI Meeting Corpus and their annotation teams.

[Result sheet](LA6_STRICT_ONSETS_20261120_SHEET.md) · [Figure](LA6_STRICT_ONSETS_20261120.png) · [All aggregate estimates](LA6_STRICT_ONSETS_20261120.json) · [Original study](LA6_COMPLETE_20261119.md).