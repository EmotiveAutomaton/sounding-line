# Engine habit identification: complete, control-invalid

**Hypothesis.** The engine's habit descriptions identify a writer across different prompts better than the same procedure identifies reassigned writers.
**METHOD.** Average fixed engine features over each writer's prompt-alternating halves, identify against the complete fixed second-half gallery, and compare paired real-probe scores with 200 whole-session reassignments and 2,000 writer-bootstrap draws.
**Found.** Both complete variants fail the frozen fake-reference bias check. **Means.** EV3 is INVALID for habit-identification admission; the positive observed contrasts do not license a validated habit badge. This is a control failure, not a negative finding about the proposed habit mechanism.

The table gives correct-identification fractions, average reassigned-writer accuracy, paired real-minus-fake accuracy difference with its conditional 95% interval, and median Spearman-Brown corrected split-half reliability. Each row uses 45 writers and chance 1/45. The PMAP style row is the previously completed descriptive reference, not a newly fitted cross-method contrast. All three rows retain their biased fake references.

| Input and features | Real accuracy | Fake mean | Paired difference [95% interval] | Median reliability | Control disposition |
|---|---:|---:|---|---:|---|
| Final-document engine habits | 0.377778 | 0.014333 | +0.363444 [+0.229994, +0.497558] | 0.714264 | INVALID: fake-reference bias |
| Surviving typed-fragment engine habits | 0.511111 | 0.030000 | +0.481111 [+0.332094, +0.628231] | 0.747341 | INVALID: fake-reference bias |
| PMAP typed words and punctuation | 0.466667 | 0.007000 | +0.459667 [+0.306108, +0.613114] | 0.475518 | Biased reference retained |

The chance-centered fake-reference mean and standard deviation are -0.007888889 and 0.016656055 for final documents, and +0.007777778 and 0.026523906 for typed fragments. Both absolute means exceed the predeclared one-quarter-standard-deviation boundary. All 200 assignments are supported for both variants; no redraw, successful-only inference or smaller-gallery rescue occurred. The observed paired intervals are positive, but that does not override this control. No gate was changed after seeing the corpus.

All 1,399 sessions from 61 writers enter the input audit; 16 writers lack the original four-session/two-prompt split eligibility. Both original and common supported galleries contain the same 45 writers. Final profiles use 17 features; typed profiles retain 16 nonconstant features, with em-dash constant. There are no absent gallery features, missing cells or tied probes in the actual galleries. The JSON retains every feature's reliability, including the undefined typed em-dash value and negative final em-dash reliability.

Engine rates use the pinned engine's unquoted-word denominator, eight fixed connectives, six punctuation marks, sentence-length mean/spread and quoted-word share. Per-session vectors are averaged without pooling word counts. PMAP's earlier style row instead uses its corpus-selected 100 typed words plus 22 punctuation features, including subsequently deleted text. The typed engine variant contains only surviving typed runs separated by synthetic boundaries at non-typed gaps. It is neither all historical typing nor original continuous prose. These differences prevent reading the displayed rows as a controlled ranking of instruments. Reliability medians are descriptive feature summaries, not a channel-level reliability or a records-needed estimate.

The pinned engine is ToMpathy `5f3ad0a304727fff5e1a6beca592e786ee71b181`. The authenticated inputs retain the preview-reader/export ancestry; this comparison makes no additional reader, GPU or paid calls. All 9,087 source pins and 10 terminal artifacts authenticate. Fresh native verification repeats the complete statistic and controls. Independent owner audit authenticates every original row, rebuilds all prompt splits and all 402 galleries with a separate nearest-neighbor oracle, reproduces every saved probe score, checks all count-preserving assignments, recomputes the paired bootstrap and both fired bias gates, and verifies native exits and slot release.

Execution plus fresh verification took 151.499594 seconds. Habit preparation's 244.105902 seconds remain charged, giving 395.605496 seconds of the original 3,600-second EV3 allowance. No retry is required for execution integrity; rerunning an unchanged valid execution would not cure the frozen control failure. Departure analysis and the complete engine feature table remain unfinished. No public badge deployment follows; daily integration and the Sunday final-packet schedule remain unchanged.

[Complete aggregate evidence](EV3_IDENTIFICATION_V1.json) · [fixed design and known-answer validation](EV3_IDENTIFICATION_BUILD_20261019.md) · [PMAP reference](PMAP.md).
