# LA9 SAMPLED POOLED ACTS 20261120

**Question.** Which pooled dialogue acts predict the matched laughter label in the fixed sample of whole meetings?

In the selected meetings, AMI social utterances had higher odds of coinciding with the matched laughter label than information exchange. The odds ratios were 5.97 with prior laughter in the model and 5.63 without it. The two models supplied 20 nonreference intervals in total.

**Population.** 61 whole meetings selected from 246 AMI and ICSI meetings; 52 contributed matched pairs. Corpus allocation: {'AMI': 42, 'ICSI': 19}. The Hamilton rule and seed 20261102 selected meetings using only corpus metadata. All original pairs within each meeting, source coding and reference levels were retained. The original dense L2 model was fitted in both history arms. Intervals use 2,000 resamples of whole contributing meetings. A class needed at least 50 distinct held-out utterances. The reference for both arms is AMI information exchange. A ratio of one means equal odds. The sample included 49,230 matched rows. 423 distinct utterances lacked a scored class and remained nuisance terms. Rows are grouped by whether prior laughter was included. Each interval is for its own comparison.

| History covariate | Source and pooled class | Distinct utterances | Odds ratio | 95% interval | Reading |
|---|---|---:|---:|---|---|
| with history | AMI/information_exchange | 2221 | 1.0000 | undefined | reference |
| with history | AMI/no_speaker_intention | 1971 | 1.1522 | 0.8578 to 1.5991 | estimated |
| with history | AMI/other | 219 | 1.3274 | 0.9207 to 2.1926 | estimated |
| with history | AMI/possible_action | 732 | 1.3773 | 1.0457 to 1.8404 | estimated |
| with history | AMI/previous_discussion | 2156 | 1.6116 | 1.3370 to 2.1293 | estimated |
| with history | AMI/social | 340 | 5.9703 | 3.6147 to 11.8027 | estimated |
| with history | ICSI/backchannel | 2919 | 1.1689 | 0.6658 to 3.0835 | estimated |
| with history | ICSI/disruption | 3179 | 2.0113 | 1.2613 to 4.8619 | estimated |
| with history | ICSI/filler | 1422 | 1.1896 | 0.7303 to 2.9809 | estimated |
| with history | ICSI/question | 1346 | 1.7328 | 1.1179 to 4.0975 | estimated |
| with history | ICSI/statement | 11872 | 1.5378 | 1.1751 to 2.5389 | estimated |
| without history | AMI/information_exchange | 2221 | 1.0000 | undefined | reference |
| without history | AMI/no_speaker_intention | 1971 | 1.1585 | 0.8505 to 1.6241 | estimated |
| without history | AMI/other | 219 | 1.2515 | 0.8517 to 2.0627 | estimated |
| without history | AMI/possible_action | 732 | 1.4087 | 1.0745 to 1.8843 | estimated |
| without history | AMI/previous_discussion | 2156 | 1.6151 | 1.3365 to 2.1515 | estimated |
| without history | AMI/social | 340 | 5.6253 | 3.2715 to 11.2030 | estimated |
| without history | ICSI/backchannel | 2919 | 1.3610 | 0.7979 to 3.5945 | estimated |
| without history | ICSI/disruption | 3179 | 2.1309 | 1.3035 to 5.2193 | estimated |
| without history | ICSI/filler | 1422 | 1.3004 | 0.7849 to 3.2206 | estimated |
| without history | ICSI/question | 1346 | 1.7822 | 1.1010 to 4.3843 | estimated |
| without history | ICSI/statement | 11872 | 1.6242 | 1.2554 to 2.6518 | estimated |

**Limit.** Corpus annotation systems describe different speech functions. The matched label can include laughter already underway. Timing and topic do not identify the speaker’s intent or the cause of laughter. ICSI coefficients use the AMI information-exchange reference, so they combine differences in corpus and speech function. The full-source pilot projected a cost above the allowance.