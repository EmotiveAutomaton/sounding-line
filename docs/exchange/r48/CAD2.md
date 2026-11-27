# CAD2 · Do unexpected words follow longer pauses within speakers?

**Registered prediction.** Population surprise and personal surprise each increase log pause after mutual adjustment.

**Source and sample.** Class S. CANDOR v1.1, BetterUp Labs, BetterUp, Inc. License v2.1 §3(b)(iii) permits non-identifying aggregate findings. Reece et al. (2023), The CANDOR corpus. [Source](https://huggingface.co/datasets/betterup/candor-tabular). Size counts distinct repeat speakers. Observations count evaluation words.

**Registered quantities.** Within-turn positive gaps on the original AWS transcription, resampling whole speakers. Donor and shuffle fits are controls.

| Quantity | Estimate [interval] | Size and unit | Observations | Reading |
|---|---:|---|---:|---|
| Population surprise | 0.072647 [0.0613681, 0.0846179] | 185 people | 136081 | Predicted direction |
| Personal surprise | 0.046731 [0.0222076, 0.070033] | 185 people | 136081 | Predicted direction |
| Donor-speaker control | -0.031278 [-0.0754268, 0.0159553] | 185 people | 136081 | Control |
| Within-speaker shuffle | 0.0104137 [-0.0120456, 0.0310848] | 185 people | 136081 | Control |

**Verdict — met.** Both registered slopes are positive and both control intervals include zero.

**Limit.** Automatic segmentation and word frequencies are imperfect measures of pauses and expectation.

**Withholding and release condition.** All returned contrasts released.

[Released table](CAD2.csv) · [Report generator](../../../tools/r48_reports.py) · [Original record](../../../results/phase_2_4_stage_15/WEEK7/CAD2_ORIGINAL_WORD_TIMING_RETURN_20261126.md) · [Retained reporting terms and source credits](../../design/stage-15/R48_SOURCE_TERMS.md)
