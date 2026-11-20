# LA6 LENGTH HELD ONSETS 20261120

**Question.** Can observable context predict a new laugh when the case and control utterances have similar word counts?

**Finding.** For both windows and both feature sets, prediction remained below the registered area of 0.60. The analyst’s predeclared guess was that the with-history arm would fall below 0.60 after length matching. Both intervals fell below that threshold.

Exclude utterances overlapping observed vocal laughter from one second before their start through their end. Match cases to controls from the same speaker and meeting using the original 30-second separation, time rule, deterministic ties and replacement. A case requires a new onset strictly after utterance end and within the indicated window. The length tolerance is two words or one fifth of the case utterance, whichever is larger. Both windows retained more than half the strict pairs when matched on length. The frozen rule selected matched controls in both windows.

The original five meeting folds, training-only transforms, C=1 model and both feature sets were fixed. Elapsed laughter history is present in one set. Matching, timing and word-count definitions are identical across its two arms. Predictive area is computed on held-out meetings. An interval wholly above 0.60 supports the registered threshold and one wholly below it counts against. An interval that spans 0.60 leaves that comparison inconclusive. Intervals are nominal. Chance is 0.50. Detection above chance and the effect needed for support use 2.8 times each arm’s bootstrap standard error.

| Window in seconds | Feature set | Meetings | Area | Whole-meeting 95% interval | Bootstrap SE | Detectable area above chance | Area for 80% support | Decision |
|---:|---|---:|---:|---|---:|---:|---:|---|
| 1 | With history | 197 | 0.5707 | 0.5568 to 0.5860 | 0.0075 | 0.0209 | 0.6209 | against |
| 1 | Without history | 197 | 0.5648 | 0.5501 to 0.5799 | 0.0076 | 0.0213 | 0.6213 | against |
| 2 | With history | 202 | 0.5604 | 0.5493 to 0.5727 | 0.0061 | 0.0171 | 0.6171 | against |
| 2 | Without history | 202 | 0.5504 | 0.5389 to 0.5616 | 0.0059 | 0.0164 | 0.6164 | against |

| Window in seconds | Original utterances | Overlap exclusions | Strict cases | Strict matched pairs | Distinct strict controls | Reused strict copies | Length-matched pairs | Distinct length controls | Reused length copies |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 221,947 | 107,878 | 2,911 | 2,888 | 2,698 | 190 | 2,867 | 2,713 | 154 |
| 2 | 221,947 | 107,878 | 5,734 | 5,690 | 4,950 | 740 | 5,654 | 5,112 | 542 |

The aggregate record includes the full act-category point table, the reference category, the unavailable-draw counts and all arm-specific limitations. Absent categories prevent population intervals for those odds. The later pooled act comparison has its own frozen dictionaries. The annotation identifies a new vocal laugh in recorded meetings. It cannot establish surprise, shared inference, a causal role for length or the proposed PLAY mechanism. Comparison with the parent also changes eligibility and matching, which precludes assigning a causal share to word count.

The 100-draw pilot used 49.7188 native CPU seconds. The full continuation and fresh replay used 260.375. All 8,103 output hashes, both source preparations, every held-out point and every draw passed verification. Source credit belongs to the AMI Meeting Corpus and ICSI Meeting Corpus and their annotation teams.

[Result sheet](LA6_LENGTH_HELD_ONSETS_20261120_SHEET.md) · [Figure](LA6_LENGTH_HELD_ONSETS_20261120.png) · [All aggregate estimates](LA6_LENGTH_HELD_ONSETS_20261120.json) · [Original study](LA6_COMPLETE_20261119.md).