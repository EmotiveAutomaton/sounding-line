# D37: complete calibration and cost specification

This continues D37_READERS_20261029.md. Freeze this matrix before any fitted
calibration-world or human effect is inspected. The source and reader fixtures
already validate chronology, computation and replay; they are not this test.

## DESIGN CHECK

LESSONS 3–5, CONTROLS 1–7 and the current D37 authority were read for this
implementation. In a common uniform population and in a page-only population,
there is no complementary entry signal. In the complementary population,
three independent entries contribute to the true action probability. Noise
alarms, lack of sensitivity, biased reference and execution invalidity remain
distinct. Failure is retained, never a reason to change a threshold or world.

## Frozen known-answer matrix

Thirty worlds: ten independent seeds each for common uniform choices,
page-only choices, and complementary choices. Eight writers, twelve sessions
each, eight menus per session, four handling classes. Three cyclic prompts
and two alternating settings cross writers and sessions. Use the actual
chronological partition function, with fully observed nonoverlapping session
clocks. Page and process inputs independently encode a random categorical cue;
eight independent Gaussian embedding coordinates add irrelevant dimensions.
Writers have fixed, balanced categorical lean cues. No fitted parameter is
supplied the latent world law.

Common-world truth is uniform. Page-only truth is the page cue with probability
0.75 and uniform otherwise. Complementary truth averages the three one-hot
page, person and process cues equally. Draw categorical outcomes from these
known probabilities. The generator retains the true probabilities separately;
only its sampled handling enters the fitted pipeline. Seeds are
20261026 + 200000 + world index 0 through 29, with worlds grouped in that order.
These are statistical calibration constructions, not models of a human mechanism.

Each world runs all recipients and the complete 200 within-writer outcome
permutations. Refit reliability, history, readers, selection and combination.
Keep preprocessing fixed because it uses no outcomes. Compute 2,000 writer
bootstrap draws on the primary, conditional on the fitted forecasts. Reference
statistics use precisely the same sessions and equal-session weighting.

A licensed constructed positive requires the primary interval above zero,
predicted-direction permutation p below 0.05, and no inherited quarter-SD bias
flag. A useful detection also requires a gain at least 0.01 half-Brier.
Admission requires at most two licensed positives among the ten common worlds,
at most two among the ten page-only worlds, and at least eight useful licensed
detections among the ten complementary worlds. Report every count and world,
plus binomial uncertainty; this small grid does not establish universal error
control. Any incomplete or numerically invalid world invalidates calibration.
An arithmetic-valid but scientific-gate-failing calibration does not get healed.
The human comparison remains held if this complete calibration fails.

## Complete workload and forecast

Human inference keeps all 41 eligible recipients and original scored rows;
the other 20 recipients retain their original source exclusions. Each recipient
runs the primary and all 200 full-reference fits, with histories rebuilt from
each permutation. The source retains all 16,855 prepared decisions. No partial
cost-probe coefficient is interpreted as a finding.

The bounded cost probe fits the five recipients with the most pooled training
decisions, ties by stable recipient key, for the primary and first permutation.
It also fits one complete complementary world, all eight recipients, primary
and first permutation. Both probes are independently reconstructed in a fresh
native process, including actual source admission and all model fits. Timings
separate preprocessing, history and fit cost, including actual proper-score
and session aggregation within each timed fit. Forecast each complete corpus
using the maximum observed per-recipient fit and preprocessing costs, the
complete 201 arms, and the matching history cost. Include 120 CPU seconds for
resampling/serialization and both complete execution and fresh replay. Apply
the frozen threefold safety factor; Week 3 section 6 then sets the full-run
ceiling at that recorded projection plus 50 percent. This is one forecast,
not repeated cap doubling. All initial-probe costs remain charged.

The probe has a 900 CPU-second attempt cap inside the initial 3,600-second
allowance. Add a 120 CPU-second workload-build reserve to the previously
charged reader/source preparation. Native fixture cost is charged as well.
No full human or calibration dispatch follows merely from a timing receipt:
its executable, validation, fresh source bindings and full projection must be
reviewed. Scientific gates remain separate. CPU only, no new agents or spend.
