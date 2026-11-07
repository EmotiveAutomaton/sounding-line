# TD4.m complete diagnostic

**Hypothesis.** Does the supplied PLAY list follow arousal even though it fails its mapped joy-intensity order?

**METHOD.** Reproduce the original result, then compare joy intensity, arousal and dominance on exactly its five jointly covered PLAY words. Count adjacent inversions and ties, rank each axis against the supplied order, and enumerate all ten unordered word pairs for cross-axis concordance, discordance or a tie. Recompute independently in a fresh process.

**Found.** Arousal does not restore the supplied PLAY word order on the same covered words; the lexical ordering failure remains.

The table gives each norm axis, adjacent reversals and ties, and its Spearman rank correlation with the supplied weak-to-strong order; 1 means exact increasing rank order.

| Axis | Adjacent reversals | Adjacent ties | Order correlation |
|---|---:|---:|---:|
| Joy intensity | 2 | 0 | -0.300000 |
| Arousal | 3 | 0 | -0.307794 |
| Dominance | 2 | 0 | -0.100000 |

Arousal minus joy order correlation is -0.007793505626. It is not a statistical effect estimate with sampling uncertainty. The next table compares axes on all ten unordered pairs of these same five words. A pair tied on either axis is counted only as tied.

| Axes compared | Concordant | Discordant | Tied | Rank correlation |
|---|---:|---:|---:|---:|
| Joy and arousal | 8 | 1 | 1 | 0.872082 |
| Joy and dominance | 9 | 1 | 0 | 0.900000 |
| Arousal and dominance | 8 | 1 | 1 | 0.872082 |

Thus the axes largely agree with one another in this tiny fixed set while neither joy nor arousal follows its supplied sequence. This does not identify why each word was placed there, a semantic cause, or a biological channel mechanism. All-VAD extra words are not added to change the comparison.

**Means.** This outcome-informed descriptive follow-up characterizes the original word-list result without replacing it or establishing a graded biological channel. No descendants. No new tests harvested from this wake. No p-value was added. Scientific reporting remains in the final packet at drain.

Design commit `706e2b74e890e22b337230ffa7a9380084bdccbc`. Full execution and replay used 3.703125 CPU seconds; all rungs total 9.875 against 180. Every output, pin and native exit verifies. Raw NRC norm entries remain private under the admitted noncommercial research terms. Source: Saif M. Mohammad, NRC Emotion Intensity v1 and VAD v2.1, as attributed in TD4_WORD_SCALES.
