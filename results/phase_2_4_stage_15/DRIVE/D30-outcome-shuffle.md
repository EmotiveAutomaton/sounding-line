# D30: required within-writer outcome-shuffle control

**Hypothesis.** D30's timing contrast should disappear when outcomes are shuffled within each writer.
**METHOD.** Keep the original eligible occurrences, marker labels, covariates and estimator fixed; permute log pauses once within writer and refit all 2,000 writer-bootstrap draws.
**Found.** The shuffled contrast is marginal: 0.0143 log-pause units, with a 95% interval from -0.0525 to +0.0618. **Means.** It does not trigger the packet's positive negative-control flag. D32 is unfinished, so daily control coverage remains incomplete; the original positive writer-label controls still limit interpretation.

The single row is the completed original-primary control. The signed effect is
local minus pervasive log pause, adjusted within writer for length, population
frequency, sentence start, preceding punctuation and population surprisal.
The interval is a writer-cluster percentile interval. The probability is the
descriptive two-sided normal-reference Wald approximation, not a permutation
probability; routing remains based on the frozen interval bands.

| Comparison | Signed effect | 95% interval | Descriptive probability | State | Writers | Occurrences |
|---|---:|---|---:|---|---:|---:|
| Outcomes shuffled within writer | 0.0143251190 | [-0.0524675177, 0.0617607299] | 0.6120583702 | marginal | 30 | 71,038 |

This implements the missing control required by the ratified packet, section 3.5.
It is separate from the completed marker-label and writer-label controls. The
implementation and permutation were frozen after the original findings were known
and before this control ran. The fixed seed is 20261017; there was no seed search
or repeated permutation until a favorable outcome. Each eligible occurrence takes
one outcome from the same writer, preserving that writer's entire outcome multiset.
The original primary's order, support, design and fitted point estimate reproduce.
Neither the original primary nor its stricter extension is replaced. The extension
is not the target of this control.

Eight targeted checks pass, including original-handler design parity in all three
timing modes, planted-effect destruction, a positive failure flag that can fire,
reversed-sign preservation, exact writer multiset preservation, saved-boundary
resume, immutable reentry, fresh-process replay and source/output mutation refusal.
Production completed both execution and fresh replay of all 2,000 draws. The owner
verified all 31 pins and 32 completion output hashes, independently solved the
full demeaned design with least squares, checked permutation membership and the
Wald arithmetic, and verified all native exits and released CPU lease. Aggregate
bindings and closure evidence are in [the receipt](D30-outcome-shuffle.json).
Raw rows, writer identities and source text remain private. No GPU or paid call.

The positive-only daily failure flag does not fire; a marginal control is retained
as marginal, not silently renamed null. A raw outcome shuffle also destroys
outcome-nuisance associations, so this is not a conditional causal test. It cannot
repair the positive writer-label controls or establish automaticity. D32's whole
card remains unfinished, so the [20:00 snapshot](DIGEST_20261017.md) still lacks
complete daily coverage. No family count, scientific admission or stage closure
changes. Theory/TODO integration follows at the next scheduled daily digest.
