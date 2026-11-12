# IN5–IN7: appraisal extension, November 11

Status: prospective builder delivery; not reviewed, committed or admitted by this
document. Authority is PACKET_BACK_HALF.md §§1 P–S, 2 IN5–IN7 and 3 queue B,
and original PACKET.md L(c). The November 11 theory handoff was read in full.
The existing IN source and every original module/receipt remain unchanged.

## DESIGN CHECK

Read LESSONS §3 on known answers, exhaustive bands, ordered cluster draws,
identifiability, exact-null classification and support floors; §4's distinction
between format and substantive qualification; §5 on immutable admitted evidence,
actual worker resources and complete dependency gates. There is no model arm.

Under a zero conditional coefficient, the signed slope is zero and an interval
contained in the ±0.10 band is against. A negative coefficient with an interval
below zero is against. A positive slope only supports when its lower endpoint
exceeds 0.10. Every other interval is inconclusive. A broad interval crossing the
bar is not a negative result. Constructed slopes −0.35, 0 and +0.35 exercise all
three signs and the actual classification, with 2,000 writer-cluster draws.
The complete handlers are separately executed and independently replayed on
constructed rating panels; this does not measure human-population sensitivity.

A shared item can make cross-channel profiles correlate by construction. Both
maps are computed, but the full-profile map is a scale report. The unique-item
map can fail, and no winning profile is selected before displaying the entire
map. A reader self-pair would bias excess error: the fixture requires the ten
distinct unordered pairs, with the known 1.2 − 2.0 = −0.8 rating-point answer.
Writer and reader identities are intentionally different in the IN6 fixture;
it requires the original writer cluster and a known standardized slope of one.
IN7 requires the untouched prompts and all 21 items in the frozen partition.
Its transmission fixture has positive error contrast and negative Fisher-z
contrast, showing why error alone does not establish failed transmission.

Rank-deficient points or bootstrap draws have no inferential result, and draws
are never omitted or retried. Fewer than 20 independent units retain a pooled
descriptive estimate; fewer than two have no interval. This is an instrument or
support limit rather than evidence against the theory. Source-hash mismatch,
duplicate panels and changed checkpoints refuse before acceptance.

## Source and common computation

Use the existing independently qualified `IN-source/output/generation.parquet`
and `validation.parquet`, under the Week 5 raw root. Their SHA-256 pins are:

- generation: `196fe2a4f72b36ae91516ee5caf762cb3ba04f7d69b6da4e53958587d44c1638`
- validation: `8c13fabfc8b08667763dd9049d5bf78337689fa17283b88a4e3dbd6a75426242`

They retain 6,558 generation rows and 5,955 reader rows after the existing
invented-event exclusion. Generation includes 547 fear reports. No raw text,
participant identity, demographics or personality field is newly read. Private
hashed identities are used only for joins and clusters and never returned in
aggregate results. Citation remains doi:10.1162/coli_a_00461, CC BY 4.0.

The new isolated `week5_in_back_half` handler has phases IN5, IN6 and IN7.
It imports the frozen original item definitions, z-score operation and decision
rule. Standardization is within prompt, uses sample SD, and stays fixed through
resampling. A zero-SD column follows the original divisor-one convention;
resulting singularity is explicit rather than silently removing the column.

Seed 20261107; canonical sorted clusters. Each draw uses SeedSequence of the
seed, the frozen comparison stream and global draw index. This is a new
prospective draw bank, not an attempted reuse of original IN draws. All
primary/secondary claim intervals use 2,000 whole-cluster resamples; the IN5
map uses 200. Every interval is the percentile interval. Bootstrap SE is the
sample SD of those same draws, `sees = 2.8*SE`, and
`supports_at = bar + 2.8*SE`. These are approximate normal sensitivity numbers,
slightly optimistic, not new calibration campaigns. For positive practical
bars, sees greater than the bar supplies the required limited-sensitivity line.
Zero-bar difference diagnostics retain their numerical SE without pretending
zero is a positive practical-sensitivity threshold.

Each inference group seals blocks of 32 globally indexed draws. Continuation
validates bindings, coverage and hashes; it does not re-seed or replace prior
blocks. The binding includes both complete source hashes, the original module,
the successor module and all scientific configuration. Only the operational
maximum-new-blocks limit is excluded. Resource requests are honored at every
block boundary. Verification reconstructs the source panels, normalization,
point fit and all draws into a separate replay tree, never accepting execution
checkpoints as independent verification. A replay can itself pause safely.

The first actual inference block writes an in-run cost probe, as amendment Q
requires. Its measured CPU covers that block only; no cold-start, whole-card,
or replay forecast is invented from it. Native accounting covers the complete
run. There is no separate qualification campaign or timing pilot for these
already-qualified-source cards.

## IN5

Use H, U and G exactly as commissioned, plus the original RAGE, PANIC/GRIEF and
DISGUST profiles. The six response-style items are familiarity, goal_relevance,
chance_responsblt, self_responsblt, chance_control and effort. The controls are
unpleasantness, confidence and that mean, all standardized within prompt.
Each profile first averages its signed standardized items, then standardizes
the index. Intensity is standardized within prompt. H is re-estimated with
the six-item style control.

The sole primary is U's standardized slope in fear reports, bar 0.10. H, U, G
and the joint seven-item fear regression use the same fear-writer resamples;
U−H and U−G are paired draw differences. The RAGE five-item, PANIC/GRIEF
three-item and DISGUST four-item regressions put every signed item in the
model simultaneously with the same controls. Each uses its own prompt's
writer resamples. These are joint models, not separate item regressions.

For specificity, each of the six unique-item profiles is fitted to fear and
to pooled anger/sadness/disgust with prompt intercepts. Fear minus pooled
other is paired within a resampling of all mapped-prompt writers. No writer
who appears across prompts is split into independent prompt clusters.

The full and unique versions of the six-by-four map use one paired whole-writer
bank across all mapped prompts. Unique sets and signs are exactly those in
the packet. The map summary is the mean of H/fear, RAGE/anger,
PANIC_GRIEF/sadness and DISGUST/disgust minus the mean of their twelve cross
slopes. Both versions are saved; full is by-construction/scale only, unique is
the diagnostic to read. No claim verdict is attached to a 200-draw texture.

Reading implements the packet's four branches in order and adds “FEAR's own”
only when the chosen profile's unique specificity interval exceeds zero.
The packet does not label H-only support or U support with H significantly
stronger. Those cases retain every estimate and say “unlisted combination,”
rather than being mislabeled “None fits.” Untestable comparisons also remain
explicit. The whole card and every eventual claim are exploratory: this is
the third look at the same reports. Theory tag H12-T1. Ceiling 8,000 CPU-seconds.

## IN6

Use all 396 mapped-prompt validation texts, five readers each. Within each
prompt, standardize reader appraisal items, form each reader's signed mean
fit index for that prompt's original profile, and standardize the reader
index. Average exactly five readers per text, then standardize that mean
within prompt. Standardize writer intensity and reader-mean unpleasantness
within prompt. Regress writer intensity on mean fit, with prompt intercepts
and mean unpleasantness. The single standardized slope has bar 0.10.

Join text back to generation's writer key and resample whole writers across
prompts. A writer with multiple validation texts contributes all of them.
Neither reader identity nor text identity substitutes for this cluster.
All four text-level variants use the same writer draws: original fit,
U replacing H only for fear, G replacing H only for fear, and reader-mean
attributed intensity replacing fit. Each variant's predictor is standardized
within prompt after the five-reader mean.

The same-rater secondary regresses each reader's standardized attributed
intensity on her standardized fit, controlling her own standardized
unpleasantness and prompt intercepts. It uses the same writer-cluster bank
for consistency, is explicitly scale only/by construction, and is not a
reader-population generalization. This analyst-added engine magnitude has
`theory_tags: []`; it is not relabeled a commissioned H12 hypothesis.
Ceiling 5,000 CPU-seconds.

## IN7

Exclude every fear/anger/sadness/disgust validation text. Count the remaining
texts at intake; the packet's approximate count is not imposed as a result.
The original source projection already includes these other prompts, so no
raw archive recovery or exclusion change is needed. Preserve every complete
five-reader panel during text bootstrap resampling.

Freeze the packet's named stance three, other stance five, event eight and
unclassed five exactly. Negative prompts are anger, boredom, disgust, fear,
guilt, sadness and shame; positive are joy, pride and relief; all remaining
prompt labels are “other.” This exhaustive wording-based rule is frozen
before outcomes and cannot be optimized from their estimates.

Per item, excess error is the mean five absolute reader–writer errors minus
the mean ten distinct unordered reader–reader errors. The primary is named
stance mean minus event mean, equally weighted across texts, in original
rating points, bar 0.10. Other stance minus event, and both contrasts by
the frozen prompt groups, use the same text draws. Every item is reported.

Transmission is Pearson correlation across texts between writer rating and
the five-reader mean. The diagnostic is mean Fisher z across event items
minus mean Fisher z across all eight stance items. Correlation itself and
Fisher z are both retained per item. A constant rating or exact ±1 correlation
has undefined Fisher z; no clipping, zero replacement or dropped item makes
it finite. This diagnostic can be untestable without erasing the excess-error
comparison. A positive primary point estimate with a nonpositive transmission
point estimate begins “spread, not transmission”; any limited-sensitivity
statement follows on that same first line. Both intervals remain visible.

The selected-three origin on the old mapped prompts is disclosed. On primary
support, the other-stance comparison (also bar 0.10) states whether the
class extends beyond the selected three; an inconclusive class estimate
does not establish that only three items matter. Theory tag H12-T3.
Ceiling 8,000 CPU-seconds.

## Records and admission

Aggregate estimands carry `record_kind`, `theory_tags` and `by_construction`.
Claim outcomes require 2,000 draws and the cluster floor. Run receipts have
no scientific verdict; 200-draw maps are textures. Full maps and the IN6
same-rater secondary are by-construction scale reports. The root owns full
write-through, theory updates, exports and the final packet.

Builder fixtures include full execute/verify, positive/negative/exact-null
OLS, profile partition, joint-model dimensions, exact pair arithmetic,
writer-owned known slope, Fisher-z diagnostic, independent replay,
pause/continuation byte preservation, changed-source/checkpoint rejection,
human reduced-draw refusal and descriptive floors. Targeted tests require
the owner's serial test token. Fixture results, actual resources, source
hashes and nonadmitted request templates are delivered privately. This
document does not assert that tests have passed or the cards are admitted.
