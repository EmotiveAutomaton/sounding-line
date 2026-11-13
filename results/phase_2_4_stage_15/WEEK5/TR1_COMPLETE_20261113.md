# TR1 COMPLETE 20261113

**Hypothesis.** Does a person's response to recent luck recur across plays, after accounting for estimation noise, or is only their usual rating level repeatable? The primary asks about response sensitivity in the game; level and carryover are separate descriptive reports.

**METHOD.** Use the qualified repeat-play source and fit each play's twelve happiness ratings on an intercept and recent luck, discounted by the fixed factor 0.65. The first rating precedes the first choice; later ratings follow their stored trial. Compare adjacent observed completed plays, preserving missing attempt numbers, and correct their gain correlation for per-play estimation noise. Qualify the correction on three constructed worlds before human inference, then recompute all quantities in two thousand whole-person resamples. A distinct native verification child rebuilds the source, controls, every draw and final result in a separate replay tree.

**Found.** The completed phone-game comparison supports a stable response sensitivity to recent luck under its conditional measurement model; it does not identify a mood set point or a biological channel.

**Primary and case check.** Corrected gain stability, a correlation describing how consistently people retain their response ranking across plays, is 0.7276013113, with a 95% whole-person percentile interval [0.6473412760, 0.9142351637]. The complete interval is above the registered 0.5 bar. Its bootstrap standard error is 0.0791838957. The minimum corrected between-person gain variance is 0.0117381553, interval [0.0074038365, 0.0139274925], so both sides pass the separate positive-variance gate. The corrected stability ratio is not clipped to a correlation range.

**Sensitivity.** Approximate sees is 0.2217149081 and supports-at is 0.7217149081 for the 0.5 primary bar. These are 2.8 times the bootstrap standard error and that quantity plus the bar, respectively; they are optimistic normal approximations, not measured population power. The primary is not sensitivity-limited at its bar. The variance gate's corresponding approximate detection floor is 0.0050693078. Generic zero-bar flags on descriptive secondary outputs do not redefine the primary's sensitivity.

**Source and support.** The original CC0 source is Dryad DOI 10.5061/dryad.prr4xgxkk. There are 15,463 repeat-eligible people and 59,291 plays, with 711,492 rating occasions. The inherited exclusions retain 31,599 single-play people and five ambiguous people. There are 43,828 adjacent observed pairs, including 6,215 with missing intervening attempt numbers. Full and both six-rating half regressions must have rank; 981 pairs fail this common support rule, leaving 42,847 pairs from 15,344 people. No pair bridges an unsupported play. There are no negative calendar-gap pairs. This pair-weighted estimand can give frequent returners more weight and is not RR1's actual-first/second/third-play cohort.

**Measurement assumptions.** The selected sampling correction uses a stationary first-order autoregressive residual covariance with a pooled residual coefficient, re-estimated inside every person resample. The observed coefficient is 0.0881889687 and is not truncated by the prospective bound of plus/minus 0.95. Residual standard deviation is 12.8971233737 rating points and pooled within-play luck standard deviation 46.0475896567 task units. The noise fit supports 58,860 plays and retains 431 rank failures. Per-play residual scale uses the projected covariance trace, not independence-only degrees of freedom. This is a conditional measurement model, not a finding that the real residual process is exactly autoregressive.

Table: known-answer calibration on three constructed worlds using complete observed trial trajectories. Each world contains two thousand sampled people. The first column is planted adjacent-play gain stability; the next columns show the unclipped recovered value under the sampling-noise correction and temporal split-half correction. Passing requires all three absolute errors to be no greater than 0.1.

| Planted stability | Sampling correction | Split-half correction |
|---|---:|---:|
| 0.0 | -0.001273398 | -0.037244762 |
| 0.5 | 0.502338539 | 19.746097486 |
| 1.0 | 0.997438709 | 15.849313836 |

Only the sampling correction qualifies; the failed split-half candidate remains visible. The frozen selection chooses among qualifying methods by the smaller error at the middle world. The worlds retain actual choices and play counts, use a constant participant level, unbounded linear ratings and matched autoregressive noise. The gain dose is one pooled residual standard deviation per within-play luck standard deviation and is never tuned to recovered stability. These checks establish conditional instrument recovery; they are not independent human replication, a causal intervention on choices or a population power calibration.

Table: every prespecified secondary, using the same two thousand whole-person draws. Level stability and level/gain association are correlations. Carryover is the within-person change in next-play first rating per unit of the previous play's total undiscounted luck; gap bins use calendar days. These descriptions do not replace the primary decision or establish a mood mechanism.

| Secondary | Estimate | 95% interval | Bootstrap standard error |
|---|---:|---|---:|
| Level stability (rating-scale use) | 0.672314941 | [0.646563892, 0.698488199] | 0.013670620 |
| Gain divided by each play’s rating spread | Undefined | Invalid uncertainty: all 2,000 draws undefined | Undefined |
| Carryover, all gaps | 0.007660849 | [0.006348380, 0.008829464] | 0.000625672 |
| Carryover, zero to one day | 0.009919981 | [0.008422053, 0.011318893] | 0.000736809 |
| Carryover, over one to seven days | 0.000557948 | [-0.002937926, 0.004188754] | 0.001845982 |
| Carryover, over seven days | -0.007773103 | [-0.013483500, -0.002211093] | 0.002799388 |
| Level/gain association | -0.118855775 | [-0.134179823, -0.104768298] | 0.007350640 |

**Retained secondary limitation.** Standardizing gain by the play's rating spread produces no point estimate or interval; all draw ordinals zero through 1,999 are retained as failed for this field. No draw is deleted, replaced or clipped. Static inspection shows that the handler saves the standardized value but not its detailed refusal status. Nonfinite standardized inputs, insufficient variance and nonpositive corrected reliability are possible code paths; the saved aggregate alone cannot identify which occurred. No root cause is asserted without a separately counted diagnostic. This does not fail the independent unstandardized primary gate, and the standardized comparison licenses no claim. The original implementation and evidence remain unchanged.

**Integrity and cost.** Every one of the 1,003 final manifest files and all plan pins authenticate. Complete execution and independent replay agree on source support, nuisance noise, all three controls, estimator selection and every uncertainty/result value. The separate execution and verification children and supervisor exited normally, and their lease was released. The final attempt used 697.515625 complete native descendant CPU seconds, 802.176395 wall seconds and a thirty-second supervisor charge. Five counted attempts total 1,577.515625 CPU seconds including supervisors; with the earlier conservative 1,692-second fixture envelope, the total accounted amount is 3,269.515625 within the original 40,000-second ceiling. The fixture envelope is not measured CPU. All preceding checkpoints remain preserved.

**Means and limits.** Within these returning players and the declared noise model, response sensitivity recurs above the registered band. A stable rating level could reflect habitual scale use. Observational carryover and calendar-gap associations cannot establish experimentally forced rebound, a homeostatic set point, a channel's tissue identity or what the person could do. Luck in the task does not randomize return timing, missing records or rating habits. The findings therefore add a scoped persistent response component alongside current-state possibilities without settling the curator's level-versus-sensitivity ontology. Replay checks the computation on the same dataset; it is not independent population replication.

**Activation and next.** The activation list is empty because no named channel, trigger or set point is measured. Retain the complete result and invalid secondary in the final curator packet. Diagnose the missing standardized refusal reason in a separately bounded instrument step before considering a repair; do not change the primary or silently drop constant-rating plays. Packet-priority admissions come first; any follow-up needs its own frozen design and qualified instrument. No p-value or new study is introduced by this landing.
