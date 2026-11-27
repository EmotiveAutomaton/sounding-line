# LGH1-ICSI · Do laughter acoustics form reproducible groups that predict what happens in a meeting?

**Registered prediction.** Three or four mixture components, one density-connected group and explanatory differences on at least two held-out facts.

**Source and sample.** Class P. Janin et al. (2003), The ICSI Meeting Corpus, CC BY 4.0. The six original aggregate tables identify the contributing speakers. The source-census rows count annotations, intervals, channels and meetings in the original records.

**Registered quantities.** Train and test on separate halves of laughter-only utterances. Compare the variation explained for each held-out fact with its shuffle reference. The source tables contain no effect intervals. A value of one in the largest and nearest flags means the component met that condition.

facts, Another speaker joins, fraction explained: 0.0431484 (52 people).

<details><summary>All 37 released quantities</summary>

| Quantity | Estimate [interval] | Size and unit | Observations | Reading |
|---|---:|---|---:|---|
| facts, Speaking at onset, fraction explained | 0.0173735 | 52 people | — | Descriptive |
| facts, Speaking at onset, shuffle 95 | 0.00260636 | 52 people | — | Control |
| facts, Another speaker joins, fraction explained | 0.0431484 | 52 people | — | Descriptive |
| facts, Another speaker joins, shuffle 95 | 0.00248137 | 52 people | — | Control |
| facts, Target share changes, fraction explained | 0.002013 | 52 people | — | Descriptive |
| facts, Target share changes, shuffle 95 | 0.00610669 | 52 people | — | Control |
| fractions, component 3, share | 0.0420595 | 34 people | — | Descriptive |
| fractions, component 3, largest | 0 | 34 people | — | Descriptive |
| fractions, component 3, nearest to largest | 0 | 34 people | — | Descriptive |
| mixture, components | 6 | 52 people | — | Descriptive |
| mixture, dip groups | 1 | 52 people | — | Descriptive |
| mixture, heldout components | 6 | 52 people | — | Descriptive |
| mixture, half agreement | 0.851395 | 52 people | — | Descriptive |
| overlap, other speaking | 1 | 52 people | — | Descriptive |
| overlap, heldout laughs | 3408 | 52 people | — | Descriptive |
| target minutes, component 3, share before | 0.422898 | 21 people | — | Descriptive |
| target minutes, component 3, share after | 0.34135 | 21 people | — | Descriptive |
| target minutes, component 3, share change | -0.0815488 | 21 people | — | Descriptive |
| within groups, Speaking at onset, component 3, mean | 0.206897 | 34 people | — | Descriptive |
| within groups, Speaking at onset, component 3, axis slope | -0.017082 | 34 people | — | Descriptive |
| within groups, Another speaker joins, component 3, mean | 0.574713 | 34 people | — | Descriptive |
| within groups, Another speaker joins, component 3, axis slope | 0.0187615 | 34 people | — | Descriptive |
| within groups, Target share changes, component 3, mean | -0.0815488 | 21 people | — | Descriptive |
| within groups, Target share changes, component 3, axis slope | -0.0286795 | 21 people | — | Descriptive |
| complete six measures | 8275 | 75 meetings | — | Support |
| invalid audio interval | 3 | 75 meetings | — | Support |
| laughter marks | 12633 | 75 meetings | — | Support |
| laughter only utterances | 8420 | 75 meetings | — | Support |
| measured intervals | 8408 | 75 meetings | — | Support |
| meetings | 75 | 75 meetings | — | Support |
| missing actor or time | 2 | 75 meetings | — | Support |
| mixed marks | 4213 | 75 meetings | — | Support |
| mixed utterances | 3778 | 75 meetings | — | Support |
| people without laughter marks | 7 | 75 meetings | — | Support |
| shared channel assignments | 2 | 75 meetings | — | Support |
| unbound or shared mic | 7 | 75 meetings | — | Support |
| verified channels | 467 | 75 meetings | — | Support |

</details>

**Verdict — mixed.** The mixture count exceeded its predicted range. Density joining returned one group. Speaking at onset and joining each exceeded the shuffle threshold. Change in the target’s speaking share stayed below it.

**Limit.** Laughter overlapping speech is absent from the sample. The same speaker or meeting can appear in both halves.

**Withholding and release condition.** The original output retained one component profile. The report includes every filed aggregate. No other component estimate or joined-versus-unjoined interval was retained. Individual speech measurements stay in the job.

[Released table](LGH1-ICSI.csv) · [Report generator](../../../tools/r48_reports.py) · [Original record](../../../results/phase_2_4_stage_15/WEEK7/LGH1_ICSI_ACOUSTICS.md)
