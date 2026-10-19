# Engine departure and pauses: verified positive association

**Hypothesis.** Words with higher engine departure scores follow longer pauses within a writer's session, after the original word and history covariates are accounted for.
**METHOD.** Fit the log pre-word pause on exact page-normalized departure among surviving engine-scored D33 words, absorb nested writer/session intercepts, and use 2,000 whole-writer bootstrap draws and 200 within-session departure permutations.
**Found.** The complete slope is positive and its permutation reference passes the frozen bias check. **Means.** The scoped engine route is supported: “tested on human writing logs: flagged words came after longer pauses”. This is a conditional association on retained words, not causal attention evidence.

The table reports the change in log pre-word pause for one unit of the engine's page-normalized departure, its whole-writer percentile 95% interval, and the complete permutation reference. Departure units are the page interquartile range of allocated word surprisal; all covariates remain in their original units.

| Comparison | Estimate | Interval or reference spread | State |
|---|---:|---|---|
| Original conditional slope | +0.072960162 | 95% interval [+0.060292895, +0.086472619] | positive |
| Within-session permutation slopes | mean -0.000057300 | SD 0.005000101; middle 95% [-0.009874185, +0.010076593] | bias check passes |

The slope corresponds to approximately 7.57% longer pause per departure unit, conditional on the fitted terms; the transformed interval is 6.21% to 9.03%. This is a multiplicative association, not a predicted change from an intervention.

The next table accounts for every original D33 typed-word row. Only exact surviving occurrences scored by the pinned exporter enter the regression; excluded words never receive a zero departure.

| Original-row disposition | Rows |
|---|---:|
| Engine names/numbers/code holdout | 1,727 |
| No exact exporter lexical span | 2 |
| Excluded by engine content-word definition | 25,102 |
| Scored surviving content word | 44,494 |
| Original word no longer intact in final text | 7,277 |

The complete original population has 78,602 words from 41 writers. The fitted subset contains 44,494 words from all 41 writers across 286 sessions; all 1,399 source documents remain in the authenticated export. No scored session has constant departure. Population surprise, word length, log frequency, sentence-start, following-punctuation and original own-minus-population history surprise are retained exactly. Every eligible word contributes once, so large sessions contribute more observations; uncertainty resamples complete writers.

As frozen under S5, writer and session intercepts are fixed. Session effects span their nested writer effects, so within-session demeaning gives the same slope as explicit writer/session dummy least squares without redundant columns. It estimates within-session association, not an additional between-session slope or a random-intercept estimand. The reference shuffles departure only within each original session and retains the other terms. All 200 draws are complete, with no redraw or successful-only inference. Its absolute mean remains below one quarter of its standard deviation. A fake-writer control is inapplicable to a per-document score. No additional probability is reported.

The engine pin is ToMpathy `5f3ad0a304727fff5e1a6beca592e786ee71b181`, with the authenticated Qwen2.5-0.5B preview-reader/export ancestry retained. Preview token-loss allocations are not whole-word probability estimates. This result does not cover deleted words, unscored content, accepted text as original typing, an entire paragraph's attention history or the cause of a pause. Survival into the final document selects the analyzed population. No automatic badge deployment occurred; the packet's stated association route is licensed only with these limits.

All 9,058 source pins and 10 terminal artifacts verify. Fresh native verification repeats source authentication, the entire statistic and every control. Independent owner audit reauthenticates every original row, reconstructs the centered design, checks the primary with QR least squares, verifies all 2,000 bootstrap slopes with an independent direct solver, and verifies all 200 permutation slopes with residualized least squares plus every within-session membership and saved permutation hash. All native workers exited and the counted slot is released. Execution through terminal, including fresh verification, took 117.014186 seconds of the original 3,600-second analysis allowance. No GPU, new reader or paid call occurred.

EV1, EV2 and EV3 are now executed and recorded with their distinct control dispositions. The engine feature table and other authorized backlog remain unfinished. Daily integration and the Sunday final-packet schedule remain unchanged.

[Complete aggregate evidence](EV1_PAUSES_V1.json) · [frozen design and validation](EV1_BUILD_20261019.md).
