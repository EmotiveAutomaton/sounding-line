# Member 0073 admission

The 2.0.0 member release contains the momentary table and the original workbook. The archive removed the static table pending a privacy review. The commissioned analysis uses the momentary table alone. There are 227 source people and 8,628 records. The intake verified SHA-256 `bcc848ddafe76e24e71f5566e8d48e6ac19f9aeb1bf81b66e0b4557473acafd1` for the table and `443d127e41a2090752ed385df6c347d599b7da8edb92acc94cb471148adc2dbc` for the workbook. [Release](https://zenodo.org/records/22809936)

Sicorello and colleagues validated a momentary emotion-regulation questionnaire using six daily prompts over ten days. They tested the questionnaire's factor structure, change after stress, subsequent affective recovery and moderation by traits. The present question concerns how consistently an individual's event-to-mood slope repeats across observation periods. It does not use the regulation questionnaire. The event and affect measures are self-reports from the same prompt. The source sample was predominantly young university women. [Source paper, design and hypotheses](https://doi.org/10.31234/osf.io/k7mgv_v1)

| Source columns | Meaning and use |
|---|---|
| `id`, `day` | Split each person's recorded days chronologically, then compare the separated first and last thirds. |
| `negative_event`, `positive_event` | Original workbook NE.EVENT and PO.EVENT ask for the intensity of the worst and best experience since the last prompt. The paper specifies seven steps. The release contains exactly integer response codes 1 through 7 for both. Use 1 as the lowest intensity and 2–7 as above-floor. The original wording does not establish that a 1 always means that nothing happened. |
| `affect_grid_x`, `affect_grid_y` | Separate valence and arousal axes of the momentary affect grid. Keep both coordinates in the source direction. Report both for each event and keep their meanings distinct. |
| Other emotion items | Guilt and embarrassment about one's own feelings do not measure the registered mood outcomes. |

[Harmonized variable dictionary](https://openesmdata.org/datasets/0073_sicorello/) · [Original codebook](https://github.com/MaurizioSicorello/SDERSvalid_Analysis/blob/main/data/SDERSvalid_Codebook.xlsx)

Apply the published BN/BR within-person scaling, half-level and spread adjustment, 2,000 whole-person draws and the gap check. Compute the three forms' eligible people before scoring. Fit the graded form at its original one-step scale. For pooling retain the full-sample adjusted variance divided by the squared mean and its paired bootstrap uncertainty. Withhold that ratio when the mean interval covers zero, following the morning denominator rule. Arousal has no pleasant or unpleasant direction of its own. Record the curator's ruling on bipolar mood before any pooling.

DESIGN CHECK. Construct different within-person graded slopes, an exactly missing outcome, and a sparse separated-third case. Compare raw and adjusted estimates and interval endpoints with the previously qualified operator at the identical seed and support. Verify each graded point slope against per-person least squares in the independent pass. Preserve the per-diary 20,000 CPU-second ceiling including replay. Re-read the pointer and the authenticated local data immediately before opening the table. The storage release takes priority over a new start.

