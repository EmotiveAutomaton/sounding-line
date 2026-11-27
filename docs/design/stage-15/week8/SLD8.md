# SLD8 · First MIDUS daily diary

The original first-wave main survey (ICPSR 2760 v19, DS0001) and daily diary (ICPSR 3725 v6, DS0001) share the person key `M2ID` and family key `M2FAMNUM`. The read-only source is `midus-m1-joined`. The archive receipt has SHA-256 `78e5f3eadbc22637f1b8b2ad83e22209417c59f6039edea3451cba6362d76cae`. The original survey codebook has SHA-256 `ff303eb8cf0a0d511b30674e6e59e9cb3b01c42f5db7695c2267c819d6a12167` and the diary codebook has SHA-256 `4c15b3258e8aa538f0178ce54cdebd0b5c0be55920898daa52c0584741f0ab55`.

| Binding | First-wave source | Use |
|---|---|---|
| Survey traits | A1SNEURO, A1SEXTRA, A1SAGREE, A1SCONS, A1SOPEN | Five separate released questionnaire composites. SLD3 uses Neuroticism. |
| Calendar | A2DDAY | Interview days 1–4 and 5–8 |
| Stressor occurrence | A2DF1 through A2DF7 | The same seven event categories as in wave two. A yes establishes a stressor day. All seven answers must be no for a reference day. |
| Six single feelings | A2DC2, A2DC4, A2DC6, A2DC7, A2DC9, A2DC10 | In this order they match wave-two B2DC1 through B2DC6. Codes 1–5 run from all to none of the time. Subtract the observed code from five to recover the wave-two direction and range. |
| Other feelings | A2DC11 combines anger and irritability. Several other separate wave-two ratings are absent. | The eight unmatched single-item cells, the registered anger and fear groups, the fourteen-item mean and contrasts requiring them are void. SLD6 and its between-wave pooling require that full mean. |

The structure check reads the two sets of keys, the diary day and the headers. It verifies the original bytes, a unique survey person, unique valid diary person-days, matching family codes on linked people and the primary fields. Its single count is the complete main-survey roster documented in the codebook (7,108). Score only the six comparable channels of SLD3 plus their fifteen eligible pairwise differences. Use the Week 7 operator and its original contrast codes, whole families for all 2,000 draws, both stages of the prior release check and a fresh decode for the replay. Everyone contributing to a difference must contribute to both channels. A withheld or unbound cell stays void.

Class S. The ICPSR terms restrict redistribution and identification. The MIDUS project conditions exclude distributed cells below ten. The installed gate requires eleven distinct people and checks the revealed rosters jointly. Cite the specific deposits and the MIDUS funding acknowledgement on the return. [Main survey](https://doi.org/10.3886/ICPSR02760.v19). [Daily diary](https://doi.org/10.3886/ICPSR03725.v6). [MIDUS acknowledgements](https://midus.wisc.edu/citation-acknowledgement/).

**Design check.** Use made SPSS survey and daily files to test the opposite response directions, a missing item, a family mismatch, duplicate diary days and edition changes. Recover a planted effect in the original SLD3 operator. Only the complete survey count and gated aggregates can leave. The same-day interview measures both the occurrence of a stressor and the reported feeling.
