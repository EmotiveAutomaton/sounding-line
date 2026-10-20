# Paired own-history pause comparison with marker-count adjustment

**Hypothesis.** Local-versus-pervasive production pauses depend more strongly on the writer's own history than on reassigned histories.
**METHOD.** Rebuild the original fixed-effect pause design and its frozen session reassignment. Pair identical supported occurrences, outcomes, real writers and nuisance variables, changing only the history-based marker classification. Use 2,000 paired real-writer bootstrap draws and 200 within-writer raw-outcome permutations, followed by complete source reconstruction and refitting in a fresh native process.
**Found.** The paired own-history advantage is null. **Means.** This comparison does not establish person-specific automaticity or attention. Positive separate-arm contrasts cannot establish the paired advantage.

The common population contains 5,990 occurrences from 30 real writers out of 71,038 original occurrences; 65,048 are unsupported by at least one rebuilt classification. No class is imputed and no conclusion extends automatically to those excluded rows. The original own-marker-count covariate remains in both arms.

The table reports the local-minus-pervasive log-pause coefficient in each arm and their paired difference, with writer-bootstrap 95% intervals. The primary expected direction is positive.

| Contrast | Estimate | 95% interval | Frozen state |
|---|---:|---|---|
| Own history | 0.20817745 | [0.09057080, 0.35283746] | positive |
| Reassigned history | 0.28241000 | [0.15367801, 0.40530890] | positive |
| Own minus reassigned (primary) | -0.07423255 | [-0.12893960, 0.01950539] | null |

The next table describes the fixed 200-permutation reference: mean, sample standard deviation, central 95% points and upper-tail probability for the observed statistic. A mean farther than one quarter of its own standard deviation from zero flags bias. Raw-outcome shuffling also destroys nuisance associations, so this remains a descriptive reference.

| Reference | Mean | SD | Central 95% points | Upper-tail probability | Bias flag |
|---|---:|---:|---|---:|---|
| Own history | -0.00435089 | 0.05104492 | [-0.09924983, 0.10675398] | 0.0049751244 | False |
| Reassigned history | -0.00512880 | 0.04865340 | [-0.10226634, 0.08420602] | 0.0049751244 | False |
| Paired difference | 0.00077791 | 0.03266236 | [-0.06655986, 0.06243256] | 0.9850746269 | False |

Correction texture below is the number and proportion of paired original occurrences with each logged category. An occurrence can appear in more than one category. These are descriptive proportions, not additional significance tests or a psychological burst/flow measure.

| History / marker class | Occurrences | Immediate deletion | Later edit | Within-burst insertion | Non-user change |
|---|---:|---|---|---|---|
| own / local | 981 | 16 (0.016310) | 16 (0.016310) | 0 (0.000000) | 0 (0.000000) |
| own / pervasive | 5009 | 210 (0.041925) | 148 (0.029547) | 0 (0.000000) | 0 (0.000000) |
| fake / local | 1092 | 17 (0.015568) | 18 (0.016484) | 0 (0.000000) | 0 (0.000000) |
| fake / pervasive | 4898 | 209 (0.042670) | 146 (0.029808) | 0 (0.000000) | 0 (0.000000) |

All 7,272 input pins and 34 output hashes verify. Complete fresh source/fit replay passes. Independent dummy-variable least squares reproduces both point estimates; independent arithmetic reproduces every interval, reference and secondary count from retained designs and blocks. Native workers exited and released their slot. Elapsed time is 206.096 seconds; total conservative charge including all validation and the retained failed attempt is 445.429 seconds within the original 3,600-second ceiling. Shared revision preparation is accounted separately and not rerun.

The [original joining failure and validated single retry](D30_PAIRED_RECOVERY_BUILD_20261019.md) remain recorded. Earlier original label-shuffle findings are unchanged; this paired null does not turn them into a person-specific result. No extension is automatically commissioned. Theory rows and afterwords integrate at the 20:00 digest.

[Complete aggregate evidence](D30-extension.fake-recovery.json) · [Frozen comparison](../../../docs/design/stage-15/drive/D30_PAIRED_FIXED_20261019.md) · [Exact-occurrence repair](../../../docs/design/stage-15/drive/D30_PAIRED_RECOVERY_20261019.md).
