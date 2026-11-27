# RML1 · Does a steady room level predict when laughter starts?

**Registered prediction.** The curator predicts a negative weight on absolute change. The theory handoff predicts a negative weight on mean level. The relief account predicts a positive weight after a high followed by a fall.

**Source and sample.** Class P. ICSI Meeting Corpus (Janin et al., 2003) and AMI Meeting Corpus (Carletta et al., 2005), including OpenSLR SLR16 under its modified CC BY-NC-SA terms. Read each corpus separately. The combined ICSI model used 75 meetings. All 171 AMI meetings were excluded because an untimed laugh could not be masked. Sample size is reported in meetings.

**Registered quantities.** Estimate laugh starts per half minute using the preceding room sound and speech pace. Exclude annotated laughs from both predictors, hold prior laughter and fit within meetings. Use 2,000 whole-meeting resamples. The coefficients are on the log count scale.

| Quantity | Estimate [interval] | Size and unit | Observations | Reading |
|---|---:|---|---:|---|
| ICSI, source meetings | 75 |  meetings | — | Support |
| ICSI, complete annotation meetings | 75 |  meetings | — | Support |
| ICSI, untimed laugh exclusions | 0 |  meetings | — | Support |
| ICSI, pace, absolute change | -0.0138033 [-0.124146, 0.109455] | 75 meetings | — | Descriptive |
| ICSI, pace, signed change | -0.0094469 [-0.0794693, 0.0733038] | 75 meetings | — | Descriptive |
| ICSI, pace, mean level | 0.120309 [-0.0406677, 0.293464] | 75 meetings | — | Descriptive |
| ICSI, pace, mean level squared | -0.316136 [-0.599833, -0.0196685] | 75 meetings | — | Descriptive |
| ICSI, pace, high then fall | -0.0334044 [-0.287917, 0.241434] | 75 meetings | — | Descriptive |
| ICSI, pace, prior laughs | 0.0500932 [0.0410776, 0.0619648] | 75 meetings | — | Descriptive |
| ICSI, room, absolute change | -0.0558938 [-0.238486, 0.134813] | 75 meetings | — | Descriptive |
| ICSI, room, signed change | -0.00878769 [-0.107235, 0.0950012] | 75 meetings | — | Descriptive |
| ICSI, room, mean level | 0.0782072 [-0.186252, 0.343941] | 75 meetings | — | Descriptive |
| ICSI, room, mean level squared | -0.328016 [-1.41086, 0.179754] | 75 meetings | — | Descriptive |
| ICSI, room, high then fall | -0.00645285 [-0.732601, 0.858637] | 75 meetings | — | Descriptive |
| ICSI, room, prior laughs | 0.0498486 [0.0409738, 0.0616934] | 75 meetings | — | Descriptive |
| ICSI, sound, model disposition code | 12 |  meetings | — | Support |
| AMI, source meetings | 171 |  meetings | — | Support |
| AMI, complete annotation meetings | 0 |  meetings | — | Support |
| AMI, untimed laugh exclusions | 171 |  meetings | — | Support |
| AMI, pace, model disposition code | 12 |  meetings | — | Support |
| AMI, room, model disposition code | 12 |  meetings | — | Support |
| AMI, sound, model disposition code | 12 |  meetings | — | Support |

**Verdict — undecided.** In the 75 ICSI meetings the intervals for absolute change, mean level and a high followed by a fall all included zero. Every AMI meeting had an untimed laugh annotation, preventing a separate AMI estimate.

**Limit.** Sound level and speech pace stand in for stress. Laughs are loud and cluster in time. Excluding a whole meeting for an untimed laugh removed the entire AMI sample.

**Withholding and release condition.** Both corpus counts and every fitted coefficient are reported. No ICSI sound-only fit or AMI model met the registered model requirements. Code 12 records an unavailable fit.

[Released table](RML1.csv) · [Report generator](../../../tools/r48_reports.py) · [Original record](../../../results/phase_2_4_stage_15/WEEK8/RML1_R48_RETURN.md)
