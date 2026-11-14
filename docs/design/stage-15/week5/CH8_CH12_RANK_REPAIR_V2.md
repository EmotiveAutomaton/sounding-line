# CH8 zero-column rank repair, retained CH12

Prepared November 13, 2026. Unadmitted successor to CH8_CH12_TWO_DAY_V1.md.
No population, target, controls, resamples, support floor or source rule changes.

## DESIGN CHECK

The original constructed run passed 13 checks and failed both planted CH8
contrasts: the model returned unsupported. All original code, its 17 source
pins, native receipt and failed logs remain. Native Job charge was 8.6875 CPU
seconds. Neither failed contrast is treated as a scientific finding.

Static diagnosis: reconstructing a design from its Gram eigendecomposition can
leave numerical dust in columns whose original within-player variance was
exactly zero. Normalizing those vectors fabricates nuisance rank. The v2
implementation explicitly zeros these reconstructed columns before the same
conditional target-rank check. It never drops a truly varying confounder to
rescue a target. The missing-underdog and perfect-confounding refusal tests stay.

The unchanged 400-player positive and null contrasts must both pass with their
full 2,000 whole-player draws. An added test requires the original exactly-zero
form, tournament and control-class columns to be absent in both implementations.
All previous CH12, forecast, literal regression, checkpoint/copy/replay, source
yield and tamper-refusal checks run unchanged. Numerical qualification remains
pending until the versioned test receipt exists. The original design's measured
cost, full replay, source-scope and owner-admission gates all remain.
