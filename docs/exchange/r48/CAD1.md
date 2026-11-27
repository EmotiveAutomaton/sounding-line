# CAD1 · Does a speaker talk faster in conversations they enjoy more?

**Registered prediction.** Within the same speaker, pace increases with enjoyment.

**Source and sample.** Class S. CANDOR v1.1, BetterUp Labs, BetterUp, Inc. License v2.1 §3(b)(iii) permits non-identifying aggregate findings. Reece et al. (2023), The CANDOR corpus. [Source](https://huggingface.co/datasets/betterup/candor-tabular). The pace row counts repeat speakers. A singleton can supply the partner’s control.

**Registered quantities.** Difference in words per second per enjoyment point, holding pre-conversation mood, arousal and partner pace. Intervals resample whole conversations.

| Quantity | Estimate [interval] | Size and unit | Observations | Reading |
|---|---:|---|---:|---|
| Pace per enjoyment point | 0.0157296 [0.00854773, 0.0242714] | 742 people | — | Predicted direction |
| Repeat speakers | — | 742 people | — | Support |
| Single-complete-conversation speakers | — | 690 people | — | Support |

**Verdict — met for primary.** The entire primary interval is positive.

**Limit.** Enjoyment stands in for interest. A speaker can appear in several resampled conversations.

**Withholding and release condition.** The expanded fit requires the attention-item export key and missing-value codes.

[Released table](CAD1.csv) · [Report generator](../../../tools/r48_reports.py) · [Original record](../../../results/phase_2_4_stage_15/WEEK7/CAD1_PRIMARY_RETURN_20261125.md) · [Retained reporting terms and source credits](../../design/stage-15/R48_SOURCE_TERMS.md)
