# TD4 word scales

**Hypothesis.** Do the curator's ordered emotion words behave as single increasing scales in independent human word norms?

**METHOD.** Apply the frozen words and emotion mappings to NRC Emotion Intensity v1 and VAD v2.1, with no stemming, synonyms or added zero scores. Require four covered words. Count adjacent inversions and rank correlation; fit dominance linearly on mapped intensity (arousal for LUST) and divide its residual standard deviation by arousal's standard deviation. Validate constructed straight, reversed, off-line and degenerate cases before the real run; reparse and recompute every result independently in a fresh process.

**Found.** The specified PLAY word order fails the frozen word-norm rule; four covered scales are inconclusive and three lack the required intensity coverage. These norms do not identify biological channels.

The table shows each declared scale, its number of intensity-covered words (arousal-covered words for LUST), adjacent reversals, rank correlation, the off-line residual ratio and the precommitted verdict. Correlation 1 means exact increasing rank order; the ratio is a linear-shape diagnostic. It is not an interval or a measure of a neural dimension.

| Scale | Covered words | Adjacent inversions | Rank correlation | Off-line ratio | Verdict |
|---|---:|---:|---:|---:|---|
| CARE | 3 | not available | not available | not available | design cannot test |
| DISGUST | 3 | not available | not available | not available | design cannot test |
| FEAR | 5 | 0 | 1 | 0.778331 | inconclusive |
| LUST | 4 | 0 | 1 | 0.550768 | inconclusive |
| PANIC/GRIEF | 4 | 1 | 0.8 | 0.509329 | inconclusive |
| PLAY | 5 | 2 | -0.3 | 0.309556 | against |
| RAGE | 6 | 1 | 0.942857 | 0.968449 | inconclusive |
| SEEKING | 3 | not available | not available | not available | design cannot test |

All declared words are available in VAD. Missing intensity scores leave SEEKING, CARE and DISGUST with three words each; those scales cannot test the registered joint criterion. CARE's joy companion has two covered words and SEEKING's joy companion three, also below the floor. Coverage masks in the aggregate receipt refer to positions in the already-public curator lists; no raw lexicon entries or wordwise norm values are published. The covered PLAY list has two reversals, meeting the against rule independently of its low residual ratio. The other four covered primary lists meet neither decisive band. No scale meets both the no-inversion and ratio-below-0.5 support rule.

Design commit: `abeee0d8b773fd223bd17771438571698e2ec423`. Native execution and full replay used 4.84375 CPU seconds. The original 360-second ceiling and single cumulative doubling remain; earlier native validation is charged separately in the campaign accounting. All source pins and complete output hashes verify, and the coordinator and both children have exited. No p-value was computed or added to the multiplicity family.

The source word ratings are associations rather than direct measurements of a drive. Coverage is conditional on the lexicon's emotion association entries. A lexical ordering failure narrows this particular supplied scale; it does not refute the curator's broader functional channel account, replace his terminology, or establish a second neural dimension. No operational threshold was changed after seeing the norms.

We use the NRC Emotion Intensity and NRC VAD lexicons created by Saif M. Mohammad at the National Research Council Canada: [Emotion Intensity](https://saifmohammad.com/WebPages/AffectIntensity.htm), [VAD](https://saifmohammad.com/WebPages/nrc-vad.html). Associated research: *Word Affect Intensities* (LREC 2018) and the VAD v2 research supplied with the 2025 release. The bundled research-use and no-redistribution terms remain in the private source archive.

**Means.** Preserve the original word order and this complete result. Continue the independent annotation and process tests; neither substitutes for a direct graded-channel measurement. A permitted follow-up must be frozen separately, remain inside this window and budget, and preserve the original result.
