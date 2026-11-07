# IN: trigger fit and writer/reader appraisal agreement

DESIGN CHECK: LESSONS 2–5; CONTROLS 6–7. Independent signed and exact-null
linear constructions must recover their assigned coefficients; identical
channel and outside-item discrepancies must give exactly zero contrast.
Distinct-reader pairs exclude the diagonal. Invalid source joins, changing
scales, rank loss or failed resample fits are instrument failures, not nulls.
Whole writers are resampled for IN1–3 and whole texts for IN4.

The original Week 5 packet fixes hypotheses, direction, rivals, bars, family
ceiling and grids. This note freezes source-column and numerical choices before
human outcomes. These self-reports are descriptive evidence about prompted
events, not a direct biological measurement of Panksepp channels.

## Source

`crowd-enVent2023.zip` SHA-256
`61c22527795669a0556df8d7441d3a7bf13ef8b2266b0433881645e92bf885e6`.
The archive's LICENSE.txt expressly licenses corpus, questionnaires and
predictions under CC BY 4.0. Cite Troiano, Oberländer and Klinger (2023),
doi:10.1162/coli_a_00461. The paper PDF has a different licence and is not
included in derivative data.

Generation has 6,600 rows; validation has 6,000 rows. The README's prose says
1,000 texts but its stated five readers and actual 1,200 distinct text keys
give 6,000. Intake requires five distinct readers for each of 1,200 texts and
complete writer linkage. No inference follows the inconsistent README count.

The parser explicitly selects task columns; demographic and personality values
are never loaded. Source participant and text keys are transformed with the
private campaign salt, never exposed in results or requests. Generated text is
used only for whitespace word count and then dropped from the projection.
The truthfulness field uses sentences, not yes/no: `I never experienced that
event, but I really imagined how it would make me feel.` means an invented
event and is excluded, together with its validation rows. `--` means no recorded
answer and is counted separately, not treated as a confessed invention.

## Frozen appraisal map

Valence is excluded from every fit index and retained as the named rival.

| Prompt / mapped channel | Signed source columns in fit index |
|---|---|
| fear / FEAR | −goal_support, +predict_conseq, +urgency, −self_control |
| anger / RAGE | +other_responsblt, +other_control, −goal_support, +urgency, +self_control |
| sadness / PANIC/GRIEF | −goal_support, −self_control, −accept_conseq |
| disgust / DISGUST | +standards, +social_norms, +other_responsblt, +not_consider |
| joy / PLAY, partial | +goal_support, −urgency |
| boredom / low SEEKING, partial | +familiarity, −attention |

The response-style control is the mean of `suddenness`, `familiarity`,
`predict_event`, `goal_relevance`, `chance_responsblt`, `self_responsblt`,
`chance_control`, `attention`, and `effort`. `confidence` is distinct.
All item values are 1–5 and the scale check precedes fitting.

## Estimators

IN1 standardizes items within prompt, averages their signed values and
standardizes that index within prompt. Intensity and the three controls
(valence, confidence, response style) are likewise standardized within prompt.
The pooled fit has four prompt intercepts and common slopes. The index
coefficient is primary, bar 0.10; each primary channel gets its own secondary
fit. A channel under 300 texts is below-floor descriptive. Partial PLAY and
SEEKING remain separate texture, never merged into the four-channel primary.

IN2 standardizes FEAR unpleasantness, consequence anticipation, urgency and
confidence. It includes both interaction parents. The product of standardized
unpleasantness and anticipation is itself standardized; its slope is the
primary, bar 0.10. A negative interaction cannot separate uncertainty-sensitive
FEAR from stress in a single intensity rating.

IN3 fits separate FEAR and RAGE intercepts, own-control slopes and unpleasantness
slopes after within-prompt standardization. RAGE minus FEAR is the primary
contrast, bar 0.15; the two individual slopes accompany it.

IN4 first averages the five absolute reader-to-writer errors and the ten
unordered distinct reader-to-reader errors per text and item. Their difference
is excess error. The within-text primary is mean excess on its channel's
non-valence profile minus mean excess on items outside all six non-valence
profiles. Excluded valence items cannot enter the outside comparator. The
pooled primary uses equal weights over the four fitted prompt intercepts,
bar 0.10 rating points; per-channel estimates are secondary. Reader agreement
is not interpreted as ground truth about the writer.

OLS cluster sufficient statistics are algebraically identical to repeated
cluster rows. All 2,000 primary bootstrap draws refit the complete model.
The original within-prompt normalization defines the reported units and is
held fixed across resampling. Texture uses 200 draws, and cannot upgrade a
claim without its separate 2,000-draw precision run. Rank loss is not silently
discarded or redrawn. Fewer than 20 clusters yields a pooled below-floor
descriptive record; fewer than two cannot provide an interval.

## Grid and execution

IN1 primary and four secondary channels; equal versus double-first-item
weights; ordinal versus intensity≥4; ≥10-word restriction; signs reversed for
each channel. Reversing all index signs algebraically reverses its fitted slope
and is reported as that diagnostic, not an independent finding. IN2 and IN3
follow the frozen primary model. IN4 runs pooled, per channel, and length-tercile
views. Branches IN1.w and IN1.r follow the packet after complete parent landing.

The source stage and every consumer expose execute/verify runtime interfaces.
Projection verification compares every retained cell; analysis verification
replays all bootstrap draws from the same fixed seed in a fresh process.
Projected peak RAM 0.5 GiB. Card ceilings: IN1 15,000, IN2 5,000, IN3 5,000,
IN4 10,000 CPU-seconds; family 60,000. All computation stays on CPU, at most two
threads, in counted slots. No source values or per-person tables are public.
