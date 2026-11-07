# B2 complete exposure and cohort texture

**Hypothesis.** How does the finite-choice refusal comparison depend on requiring more observed choices, and how much of that variation accompanies changing the returning-fingerprint cohort?

**METHOD.** Freeze thresholds from four through eleven valid choices per original dimension. At each threshold retain only members of the original common returning-fingerprint cohort meeting that threshold in every dimension. Integrate every possible subset at the threshold count, at exactly three choices, and at each fingerprint's own minimum dimension count. Contrast mean expected never-trading probability for species/intervention against gender/fitness, jointly resampling whole fingerprints for 2,000 draws. Preserve a paired threshold-minus-three exposure difference within each selected cohort. Combine only exactly identical statistic vectors. Retain marginal descriptive 95% percentile intervals; the bounded-mean fallback applies only to homogeneous vectors. Require at least 1,000 fingerprints, stop unsupported nested cohorts, and stop after five consecutive cards whose three exposure estimates all stay within half the original parent's 95% interval width. The exact-cache successor changes only source representation and reproduces every field of the original 32-draw probe; full separate-process recalculation validates the complete family.

**Found.** The exposure-and-cohort grid changes the observed refusal contrast and reverses the paired exposure difference across selected cohorts; this is descriptive sensitivity only.

The table reports every registered threshold. Eligible fingerprints and their share refer to the original 301,689-fingerprint cohort. Each remaining cell is a species/intervention-minus-gender/fitness difference in percentage points, followed by its marginal descriptive 95% interval. The three exposure summaries use the same selected cohort within a row; cohorts differ between rows. These intervals are not simultaneous and are not used for new hypothesis tests.

| Required choices in every dimension | Eligible fingerprints | Original cohort (%) | Exactly the threshold | Exactly three | Own minimum |
|---|---:|---:|---|---|---|
| 4 | 215797 | 71.529622 | 15.889833 [15.754983, 16.028247] | 13.870703 [13.748971, 13.993970] | 14.784932 [14.645866, 14.929497] |
| 5 | 96973 | 32.143366 | 15.399214 [15.230486, 15.563245] | 13.294120 [13.155697, 13.437463] | 12.563660 [12.388715, 12.737025] |
| 6 | 74564 | 24.715518 | 14.956290 [14.777454, 15.133661] | 13.327713 [13.176828, 13.475348] | 11.613362 [11.426776, 11.796644] |
| 7 | 49037 | 16.254156 | 13.681364 [13.494963, 13.866081] | 13.307966 [13.146676, 13.463820] | 9.388905 [9.196528, 9.576874] |
| 8 | 40415 | 13.396246 | 12.654126 [12.463242, 12.842546] | 13.441694 [13.279700, 13.607606] | 8.377897 [8.184476, 8.569396] |
| 9 | 31502 | 10.441879 | 11.393706 [11.198219, 11.589160] | 13.631925 [13.451247, 13.800881] | 6.911968 [6.715851, 7.114452] |
| 10 | 27361 | 9.069273 | 10.271985 [10.074913, 10.479208] | 13.741093 [13.574790, 13.926065] | 6.076607 [5.881113, 6.278910] |
| 11 | 23150 | 7.673465 | 9.153474 [8.954961, 9.352307] | 13.974212 [13.790242, 14.162387] | 5.113700 [4.913611, 5.311166] |

The next table isolates the exposure change within each selected cohort. It subtracts the exactly-three pooled contrast from the threshold-exposure contrast, in percentage points. A sign change concerns this finite-sampling comparison, not a reversal of an individual's preference.

| Required choices | Paired threshold-minus-three difference and descriptive 95% interval |
|---|---|
| 4 | 2.019130 [1.984726, 2.052530] |
| 5 | 2.105094 [2.055248, 2.156599] |
| 6 | 1.628578 [1.546787, 1.702875] |
| 7 | 0.373398 [0.281676, 0.458904] |
| 8 | -0.787568 [-0.894774, -0.680087] |
| 9 | -2.238219 [-2.354490, -2.114234] |
| 10 | -3.469107 [-3.608284, -3.330822] |
| 11 | -4.820738 [-4.960099, -4.685497] |

The paired difference is positive at required counts four through seven and negative at eight through eleven in these selected cohorts. The exactly-three contrasts vary more modestly across the selected cohorts. The threshold-exposure contrast remains positive throughout the finite grid, while its magnitude falls across the displayed thresholds. No threshold is selected as preferred, no practical-bar rule is added, and no claim receives stronger status from this descriptive family.

The table retains all four expected never-trading rates as percentages. Each row names a cohort threshold and exposure rule. These are finite hypothetical-choice summaries, not population prevalences or measurements of terminal identity.

| Required choices | Exposure inspected | Species (%) | Intervention (%) | Gender (%) | Fitness (%) |
|---|---|---:|---:|---:|---:|
| 4 | Threshold | 54.445064 | 14.412763 | 18.023180 | 19.054980 |
| 4 | Three | 62.384793 | 26.846192 | 30.249782 | 31.239796 |
| 4 | Own minimum | 46.352346 | 9.603571 | 12.795631 | 13.590423 |
| 5 | Threshold | 45.283571 | 7.701689 | 10.607996 | 11.578837 |
| 5 | Three | 60.135750 | 26.612579 | 29.546909 | 30.613181 |
| 5 | Own minimum | 33.528288 | 3.453686 | 5.641445 | 6.213208 |
| 6 | Threshold | 39.831618 | 4.237659 | 6.650691 | 7.506005 |
| 6 | Three | 59.872943 | 26.545741 | 29.325408 | 30.437852 |
| 6 | Own minimum | 29.484501 | 2.108523 | 3.921848 | 4.444452 |
| 7 | Threshold | 33.983358 | 2.284812 | 4.122269 | 4.783173 |
| 7 | Three | 59.066232 | 26.373543 | 28.854751 | 29.969092 |
| 7 | Own minimum | 22.445332 | 0.845519 | 2.088975 | 2.424067 |
| 8 | Threshold | 29.898676 | 1.279407 | 2.657479 | 3.212351 |
| 8 | Three | 58.920752 | 26.321851 | 28.595643 | 29.763572 |
| 8 | Own minimum | 19.426203 | 0.500135 | 1.429934 | 1.740610 |
| 9 | Threshold | 25.987084 | 0.707328 | 1.799756 | 2.107244 |
| 9 | Three | 58.766448 | 26.226496 | 28.352187 | 29.376906 |
| 9 | Own minimum | 15.603343 | 0.227964 | 0.949935 | 1.057436 |
| 10 | Threshold | 22.898406 | 0.404477 | 1.282080 | 1.476833 |
| 10 | Three | 58.711005 | 26.175241 | 28.176716 | 29.227344 |
| 10 | Own minimum | 13.555669 | 0.136227 | 0.739120 | 0.799561 |
| 11 | Threshold | 20.040635 | 0.244309 | 0.935705 | 1.042291 |
| 11 | Three | 58.706220 | 26.153864 | 27.914239 | 28.997421 |
| 11 | Own minimum | 11.264755 | 0.084278 | 0.550559 | 0.571075 |

All eight planned cards pass the support floor. No early stop fires: every card has at least one of its three exposure estimates farther than half the original parent interval width from that parent's point. The parent point is 14.509147 percentage points and the half-width is 0.141623 percentage points. Every consecutive-stability counter is zero. The finite grid is exhausted; this does not authorize extending it or creating descendants.

The source selection, offered scenarios, stable ordinary preferences and uncertain fingerprint linkage remain the strongest rivals. Whole-fingerprint bootstrap intervals assume exchangeable fingerprints; cross-fingerprint dependence and linkage errors are not modeled. Expected never-trading rates can fall mechanically as exposure grows. Holding a selected cohort fixed separates the arithmetic exposure change within it, but this is not a randomized intervention on people. None of these records observes current endorsement, satiation, actual personal sacrifice or unoffered trades. The original B2, component and two exposure results retain their exact evidence and status.

The first uncached cost probe remains held under its frozen forecast. Its separately committed exact-cache successor passes all original parent reproductions, complete original-probe equality, immutable reentry and independent elementwise source reconstruction. Full execution and independent replay used 98.09375 CPU seconds; every family attempt including preparation and the retained original probe totals 187.484375 CPU seconds. The campaign has 5558.21875 charged or conservatively reserved CPU seconds against 54,000. No budget reset occurred. Design commits: original `3fc54998fd811156487ec644ae99faa1f798972c`; cache successor `9b8f0a59209dbd3c68308eea59d69c200cef9638`. Every output, pin and exited native identity verifies. Raw counts and cached arrays stay private. Source attribution: Awad et al. (2018), [CC-BY Moral Machine all-session release](https://osf.io/3hvt2/).

**Means.** Retain this as descriptive exposure/cohort texture, with no new p-value, confidence upgrade or descendants. The supplied theory errata remains applied; this later result changes only the existing B2 result row and its afterword. The admitted research queue is now drained, with zero active slots and zero ready successors. TD1 to TD3 retrieval, B1 licensing and B3 licensing/semantics remain held; further texture is not yet built or admitted. No scientific failure is healed, no completed job is rerun, and no new tests are harvested from this wake. The existing six-hour health inspection remains due at 18:54:44 PST, ahead of the 19:00 source-outage trigger. Original CPU-only Gear 2 authority, ceiling, freeze/drain and final curator packet policy remain unchanged.
