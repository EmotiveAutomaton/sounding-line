# LGH6 · Does more voiced laughter predict another speaker joining within one second?

**Registered prediction.** The registered prediction is that a speaker’s more voiced laughs are more likely to draw another speaker into laughter.

**Source and sample.** Class P. ICSI Meeting Corpus (Janin et al., 2003) and AMI Meeting Corpus (Carletta et al., 2005), including OpenSLR SLR16 under its modified CC BY-NC-SA terms. Each corpus has a separate fit. ICSI comprised 75 source meetings, with 52 speakers and 75 meetings in the held-out panel. AMI comprised 171 source meetings, with 184 speakers and 171 meetings in the held-out panel.

**Registered quantities.** Measure the voiced fraction of active sound before a join. Exclude intervals with under 200 ms of active sound. On the original held-out laughs fit a within-speaker linear probability model, then add level and prior laughter, then meeting effects. A coefficient is the probability difference per unit of voiced fraction. Repeat descriptively on all eligible laughs. Use 2,000 whole-meeting draws for intervals and 1,000 within-speaker, within-meeting shuffles for the first model. The control rows give the 95th percentile and the upper-tail permutation probability. The earlier ICSI component profile uses whole annotated utterances.

ICSI, heldout, voicing model 1: -0.125239 [-0.226345, -0.0164268] (52 people).

<details><summary>All 38 released quantities</summary>

| Quantity | Estimate [interval] | Size and unit | Observations | Reading |
|---|---:|---|---:|---|
| ICSI, source meetings | 75 |  meetings | — | Support |
| ICSI, short intervals | 1271 | 48 people | — | Support |
| ICSI, heldout, model disposition code | 0 | 52 people | 75 | Support |
| ICSI, heldout, voicing model 1 | -0.125239 [-0.226345, -0.0164268] | 52 people | — | Opposite direction |
| ICSI, heldout, voicing model 1, shuffle95 | 0.0335549 | 52 people | — | Control |
| ICSI, heldout, voicing model 1, shuffle_upper | 1 | 52 people | — | Control |
| ICSI, heldout, voicing model 2 | -0.141943 [-0.237266, -0.0412717] | 52 people | — | Opposite direction |
| ICSI, heldout, voicing model 3 | -0.147847 [-0.240805, -0.046048] | 52 people | — | Opposite direction |
| ICSI, all, model disposition code | 0 | 52 people | 75 | Support |
| ICSI, all, voicing model 1 | -0.0400561 [-0.113133, 0.0435754] | 52 people | — | Descriptive |
| ICSI, all, voicing model 1, shuffle95 | 0.0446932 | 52 people | — | Control |
| ICSI, all, voicing model 1, shuffle_upper | 0.916084 | 52 people | — | Control |
| ICSI, all, voicing model 2 | -0.057664 [-0.13022, 0.021941] | 52 people | — | Descriptive |
| ICSI, all, voicing model 3 | -0.0613697 [-0.131977, 0.0166333] | 52 people | — | Descriptive |
| AMI, source meetings | 171 |  meetings | — | Support |
| AMI, short intervals | 2024 | 185 people | — | Support |
| AMI, heldout, model disposition code | 0 | 184 people | 171 | Support |
| AMI, heldout, voicing model 1 | -0.0729743 [-0.149104, -0.000906994] | 184 people | — | Opposite direction |
| AMI, heldout, voicing model 1, shuffle95 | 0.0511349 | 184 people | — | Control |
| AMI, heldout, voicing model 1, shuffle_upper | 0.998002 | 184 people | — | Control |
| AMI, heldout, voicing model 2 | -0.113251 [-0.191042, -0.0458598] | 184 people | — | Opposite direction |
| AMI, heldout, voicing model 3 | -0.124879 [-0.202309, -0.0512348] | 184 people | — | Opposite direction |
| AMI, all, model disposition code | 0 | 189 people | 171 | Support |
| AMI, all, voicing model 1 | -0.0172544 [-0.0590137, 0.0342566] | 189 people | — | Descriptive |
| AMI, all, voicing model 1, shuffle95 | 0.0201685 | 189 people | — | Control |
| AMI, all, voicing model 1, shuffle_upper | 0.647353 | 189 people | — | Control |
| AMI, all, voicing model 2 | -0.0676185 [-0.113066, -0.0173844] | 189 people | — | Descriptive |
| AMI, all, voicing model 3 | -0.0664736 [-0.112193, -0.0149482] | 189 people | — | Descriptive |
| ICSI, earlier component 3, share of held-out laughs | 0.0420595 | 34 people | — | Descriptive |
| ICSI, earlier component 3, target speaking share before | 0.422898 | 21 people | — | Descriptive |
| ICSI, earlier component 3, target speaking share after | 0.34135 | 21 people | — | Descriptive |
| ICSI, earlier component 3, target speaking share change | -0.0815488 | 21 people | — | Descriptive |
| ICSI, earlier component 3, annotated utterance length, seconds | 5.48334 | 34 people | — | Descriptive |
| ICSI, earlier component 3, bursts | 9.21839 | 34 people | — | Descriptive |
| ICSI, earlier component 3, voiced fraction | 0.333935 | 34 people | — | Descriptive |
| ICSI, earlier component 3, relative pitch, semitones | 7.6307 | 34 people | — | Descriptive |
| ICSI, earlier component 3, pitch interquartile range, semitones | 14.6509 | 34 people | — | Descriptive |
| ICSI, earlier component 3, relative level, dB | -2.67239 | 34 people | — | Descriptive |

</details>

**Verdict — against on ICSI, against on AMI.** The ICSI held-out within-speaker coefficient was -0.125 (95% interval -0.226 to -0.016). All three held-out intervals lay below zero. All three descriptive ICSI intervals using all eligible laughs included zero. The AMI held-out within-speaker coefficient was -0.073 (95% interval -0.149 to -0.001). All three held-out intervals lay below zero. The earlier ICSI component made up about 4.2% of held-out laughs. Its targets’ mean speaking share fell by about 8.2 percentage points. These descriptive statistics and its six acoustic means come from previously released tables; they have no registered intervals.

**Limit.** Laughter that overlaps speech is not in the ICSI sample, and that may be a kind of its own. Joined laughs supply shorter measurement windows. A funnier moment may affect both voicing and joining, so this analysis cannot identify a causal effect.

**Withholding and release condition.** All released models, shuffle controls and short-interval counts are filed. The earlier sound profile is available for ICSI component 3 only. Its acoustic means describe 34 speakers; the target speaking-share comparison used 21.

[Released table](LGH6.csv) · [Report generator](../../../tools/r48_reports.py) · [Original record](../../../results/phase_2_4_stage_15/WEEK8/LGH6_R48_RETURN.md)
