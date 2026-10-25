# WA1: saved adapter labels and measurement sensitivity

The Week 3 packet commissions a CPU-only audit of the original personal-adapter
comparisons. This source implementation freezes the 86 completed readout cells
in Stage 14's final adapter table. Later Stage 15 R6 repairs remain separate.
It does not reopen training or use the GPU.

## Label and retained-source finding

The code chain explicitly uses the logged selection field: Stage 11 replay sets
`selected_index` from `currentSuggestionIndex`; Stage 14 records and personal
data preserve it; `adaptive_v2.prepare_cases` maps it into the offered options.
Canonical inserted-choice auditing therefore applies. The manifest census finds
all 86 readout completions and predictions plus all 86 producer `COSTS.json`
files, including calibration and evaluation raw likelihoods for base, own,
pooled and donor models. These are source-availability findings, not corrected
performance results.

The shared chronology dataset has 1,086 calibration/evaluation rows before the
original model-specific token filters. Their keys all join the canonical-choice
audit. The source handler must still authenticate each file, tokenizer and
original model-specific roster at execution; census existence alone does not
admit a result.

## Fixed source preparation

`week3_adapter_inputs` authenticates original completions and cards, the common
reader/evaluator/chronology inputs, native tokenizer files and the canonical
audit. It reproduces the old case ordering and token lengths with the frozen
case-preparation code. It binds every raw likelihood array to its original
calibration/evaluation keys and reproduces all four length-normalized original
temperatures and evaluation probability vectors. Missing, duplicated, reordered
or unsupported saved rows refuse completion instead of shrinking a cell.

Each retained case carries both old and uniquely verified canonical target
positions. Canonical option IDs, original session/writer/ordinal and raw-source
hash must agree. Ambiguous insertions are not replaced by logged selections.
Every original cell and its original token-filtered population remains intact.
The output contains private likelihoods, token lengths and hashed identities;
public output is a source census only. Fresh verification reconstructs all cells
and rechecks source pins, without neural inference or a new performance result.

## Statistical consumer and timing admission

WA1a will recalibrate the frozen length-normalized likelihood readouts using
canonical labels on the original earlier calibration partition, then evaluate
canonical labels on the original evaluation population. The old calibrated
scores remain a separate audit. Report the calibrated base against uniform for
each original cell, plus own against base/pooled/donor under the rounds' original
writer and crossed writer/prompt intervals. Repeated cells are not independent
human studies.

WA1b must preserve the original useful-margin rule: own-minus-rival loss has
both 95% interval upper bounds below -0.01. The packet's four planted sizes are
0.01, 0.02, 0.03 and 0.05 half-Brier, at the original sample sizes, 1,000 worlds,
seed 20261026. A plant must remain a legal probability vector and its achieved
writer-level improvement must be checked. If a requested improvement cannot be
reached, retain that cell as unsupported; do not clip probabilities, silently
drop writers or call a smaller plant the requested size. The repeated-world
sampling and planting transformation need a frozen, known-answer-checked
implementation before any power output is admitted. No universal 2.5% or 80%
rate is inferred merely from a boundary or a point estimate.

The implemented consumer is `week3_adapter_audit`. A per-writer mixture moves
each retained personal probability vector toward its canonical observed choice.
One weight is chosen for all of that writer's evaluation cases so that mean
half-Brier improves by exactly the requested amount. A writer whose retained
loss is smaller than that amount makes the whole cell/plant unsupported; no
writer is removed. The output reports every resulting actual advantage against
base, pooled and donor separately. These are added improvements over the retained
personal forecast, not a common total advantage over all rivals. The conditional
minimum detectable improvement must not license a total-advantage exclusion.

Each of 1,000 worlds resamples complete writer clusters at the original writer
count with seed 20261026. Duplicate draws become distinct synthetic writer
units; prompt support is reconstructed for that world. Each world runs the
original 4,000 writer and crossed writer/prompt draws, with original seeds
141010 and 141011, and the strict all-three-rival margin rule. Cells with exactly
the same writer/prompt roster share the random bank; they remain separate cells,
not independent replications. Wilson intervals describe Monte Carlo uncertainty.

The original evaluation population has one prompt per writer. The consumer
asserts this before using an exact optimization: a sampled prompt's multiplicity
cancels in each writer's within-prompt mean, leaving writer weights gated by
prompt presence. A known-answer check reproduces both original 4,000-draw
intervals. A different population fails rather than changing the statistic.

`week3_adapter_timing` runs every cell, calibration and original interval with
the first 100 worlds. It discards scientific scores, repeats the workload in
fresh verification, and projects all 1,000 worlds. The source, timing pilot,
analysis and fresh verification share WA1's two-CPU-hour cap. Native validation,
measured cost and owner budget admission are required before full dispatch.
No corpus job is launched by this builder.
