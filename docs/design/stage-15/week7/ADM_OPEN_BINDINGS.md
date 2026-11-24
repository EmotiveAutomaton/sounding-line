# ADM open-source admissions

The local deliveries supplied the original data, licence and codebook for both admissions. The source manifest and each data file are hash-checked before the analysis. The analyses use the registered ATL within-person operator, 2,000 whole-person draws and the existing shuffle reference.

| Source | Binding for ATL | Timing and scope |
|---|---|---|
| Implications of Sharing Daily Hassles | The ESM file identifies people and couples. It records the person's recent hassle, the partner's recent hassle, disclosure and listening (0/1), and momentary anger, disappointment, down-heartedness and nervousness (0–6). Disclosure and listening have structural missingness when neither partner reported a hassle. Keep that conditioning explicit. | The release identifies the measurement occasion. It supplies neither the same-day timestamps and elapsed gaps required for LAG nor a worry rating for TWO2. Members of a couple can give dependent answers. The packet's person bootstrap treats them separately. |
| American Time Use Survey Well-Being Module, 2010, 2012, 2013 and 2021 | The activity table identifies a respondent and activity number. Its interaction item includes telephone interaction (1 yes, 2 no). Use happy, sad, stressed, tired and pain (0–6) as separate outcomes. Treat other codes as missing. Meaningfulness is an appraisal. | Each respondent recalls selected activities from one diary day. A day adjustment duplicates the person adjustment. The module lacks the elapsed gaps between consecutive answered prompts. This is an unweighted comparison within respondents who reported on activities and carries no US-population estimate. |

The couples source is distributed under CC BY 4.0. The US Bureau of Labor Statistics module is public domain, with BLS attribution. The SPSS dictionaries label the couples measures. The BLS activity-file dictionary and questionnaire identify the response codes and sampled activities. [Couples study](https://osf.io/vzd5m/) · [BLS wellbeing module](https://www.bls.gov/tus/modules/wbdatafiles.htm)

## Design check

Use the released endpoints for each outcome. A constructed source with reversed binary codes and negative missing-value codes must preserve the intended exposure sign, separate structural missingness from a negative response, and leave the original survey identifier private. Both jobs repeat source decoding, fits and shuffles in a fresh native process. Each uses its ATL allowance, including replay. A group without enough event variation receives the original operator's void disposition.

