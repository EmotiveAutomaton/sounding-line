# LGH2-survey · How does reported laughter relate to incoming and outgoing mood?

**Registered prediction.** These two survey comparisons are descriptions. The registered test requires speaker-linked laugh events.

**Source and sample.** Class S. CANDOR v1.1, BetterUp Labs, BetterUp, Inc. License v2.1 §3(b)(iii) permits non-identifying aggregate findings. Reece et al. (2023), The CANDOR corpus. [Source](https://huggingface.co/datasets/betterup/candor-tabular). Size counts distinct respondents. Observations count complete conversations.

**Registered quantities.** Whole-conversation intervals for relative laughter on incoming unpleasant mood and outgoing pleasant mood on relative laughter, holding incoming mood.

| Quantity | Estimate [interval] | Size and unit | Observations | Reading |
|---|---:|---|---:|---|
| Relative laughter on incoming mood | -0.0210054 [-0.0569237, 0.017856] | 1417 people | 1603 | Descriptive |
| Outgoing mood on relative laughter | -0.0319723 [-0.0598444, -0.00436877] | 1417 people | 1603 | Descriptive |

**Verdict — descriptive.** The first interval includes zero. The outgoing-mood interval is below zero.

**Limit.** Laughter was judged relative to a partner after the conversation and shares a reporter with mood.

**Withholding and release condition.** Testing the event-level prediction requires timed speaker-linked laughter.

[Released table](LGH2-survey.csv) · [Report generator](../../../tools/r48_reports.py) · [Original record](../../../results/phase_2_4_stage_15/WEEK7/LGH2_CANDOR_SURVEY_RETURN_20261125.md) · [Retained reporting terms and source credits](../../design/stage-15/R48_SOURCE_TERMS.md)
