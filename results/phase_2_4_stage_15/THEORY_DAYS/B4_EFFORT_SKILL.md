# B4 complete effort and skill comparison

**Hypothesis.** Does additional deliberation improve move quality more for stronger chess players, as a proxy test of the curator's effect-equals-effort-times-power conjecture?

**METHOD.** Use the frozen one-percent game draw from the complete April 2017 Lichess month, retaining games with clock and engine-evaluation annotations and moves passing the source checks. Model negative centipawn loss on standardized rating, log seconds and their standardized product, with phase and absolute prior evaluation as declared controls. Instrument time and its rating product using a prior clock at most ten seconds and its rating product. Report ordinary least squares beside the two-stage diagnostic. Recompute both stages in 2,000 game-cluster bootstrap draws and independently replay the complete calculation. Constructed positive, negative and null fixtures and independent two-stage arithmetic preceded the run.

**Found.** The registered chess effort-by-skill diagnostic is inconclusive; the ordinary regression association does not establish that effort and power multiply causally.

The table reports the coefficient on the standardized interaction, in centipawns, with game-cluster percentile intervals. Higher quality means less centipawn loss. The primary supports only when its entire interval exceeds +1, counts against the proxy prediction when its entire interval is at or below zero, and is otherwise inconclusive.

| Model | Product coefficient | 95% interval | Role |
|---|---:|---|---|
| Low-clock instrument diagnostic | -2.498420 | [-15.897875, 11.944513] | Primary: inconclusive |
| Ordinary regression | 2.522756 | [1.253713, 3.761304] | Descriptive companion |

The sample has 9912 usable games and 514787 moves, exceeding the frozen 1,000-game and 10,000-move floors. Both model matrices have full rank. The excluded-instrument partial F statistics are 9708.616868 and 8416.349592, above the frozen ten-point numerical gate. All 2000 bootstrap draws have valid numerical fits; none are dropped. The point-fit strength gate passes. Bootstrap draws with weaker but nonsingular instruments are retained under the implementation; this record does not assert that every resample passes the point-fit strength gate.

Instrument strength does not establish exclusion. Low remaining time can directly impair decisions, and hard positions can both use time and worsen play. Absolute prior evaluation is an incomplete difficulty control. The ordinary regression and instrumental diagnostic have different signs and uncertainty; the companion cannot replace the registered primary after outcomes. Rating is an imperfect skill proxy and elapsed seconds is an imperfect effort proxy. These observations therefore neither identify causal effort nor prove or refute the general multiplicative conjecture.

The one-percent draw precedes annotation filtering, but the analysis sample is annotation-dependent. One-second clock precision excludes nonpositive measured elapsed times; mate evaluations are excluded rather than converted into centipawns. Game clustering conditions on the sampled games and observed players. Repeated players across games and unknown cross-game dependence are not modeled, so this is not new-player population uncertainty. Complete source counts and dispositions remain in B4_SOURCE.md. No usernames, game identifiers or raw moves enter public artifacts. Source: [Lichess CC0 database](https://database.lichess.org/).

Known-answer validation checks implementation under its stipulated strong instruments. Sensitivity at the one-centipawn practical size was untested at the primary landing; the complete registered conditional calibration now records limited sensitivity (S15-TD-B4-IC-SENSITIVITY-20261106). The human estimate and inconclusive verdict are unchanged, and neither equivalence nor a negative finding follows. A valid-null or inconclusive scientific gate is not an engineering failure and is not healed.

**Means.** Freeze and validate B4.ic, a first-generation sensitivity check at the one-centipawn practical bar on the observed design, capped at 3,600 CPU seconds within the original campaign allowance and clock. No descendant follow-ups. Preserve the original result. The curator's effect, effort and power remain the theory terms; the chess measures are analyst proxies. No new tests were harvested from this operational wake beyond the commissioned first-generation follow-up rule.

Design commit: `897988ff9659171ed9f6a028ead6fe4cbd6fd5de`. Execution plus complete independent replay used 4.796875 CPU seconds. Every input pin, output hash and native coordinator/child exit verifies. The native completion's generic scientific-admission flag is false; the frozen full-model plan admits scientific interpretation and this owner-reviewed write-through supplies it. No p-value is added. Scientific reporting remains in the final packet at drain.
