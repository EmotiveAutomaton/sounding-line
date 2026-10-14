# G3-S14-MAKER-MAIN - own cross-session history shows no primary reader advantage

**Hypothesis.** Does a maker's earlier cross-session history help the cloud reader predict later handling of suggestions beyond no history, another maker's history, personal class frequencies and a cheap partial-pooling model?

**METHOD.** Complete the frozen Qwen3.5 27B Q4_K_M Modal main on 234 later suggestion-handling opportunities from 31 writers and 20 fixed prompts, excluding all three pilot writers. Four evidence arms make 936 calls: no history, earlier decisions in the same session, the maker's earlier cross-session decisions and another maker's earlier decisions. Compare their saved probabilities with the seven already fitted local handling baselines on identical target keys. Primary loss is half of the multiclass Brier score, averaged within writer and then equally across writers; invalid replies cost one. Pair all contrasts within writer, use 10,000 writer bootstrap resamples and two-sided sign flips with a plus-one correction, and retain crossed writer/prompt bootstrap sensitivity. Holm correction retains all eleven frozen primary slots; the five unavailable Opus tests occupy conservative unit slots without being reported as observed p-values. Reconstruct the full source data and every native prompt, verify all archives, source pins, residency and ended ownership, replay independent arithmetic/calibration and rerun the saved-output consumer without inference. Analysis implementation details were frozen and known-answer tested after collection but before this main scoring; no outcome selects a roster, model, control or next run.

The table shows the six available primary half-Brier contrasts. Gain is rival loss minus reader loss, so positive favors the reader. Writer and crossed writer/prompt columns are 95% bootstrap intervals; raw p is the two-sided writer sign-flip probability and Holm p adjusts across all eleven commissioned contrasts. The other five, for Opus, are unavailable.

| Reader evidence | Rival | Gain | Writer interval | Crossed interval | Raw p | Holm p (11) |
|---|---|---:|---|---|---:|---:|
| Same-session history | Population frequency | -0.052482 | [-0.087291, -0.017811] | [-0.118381, 0.018189] | 0.007399 | 0.059194 |
| Own cross-session history | Population frequency | -0.078032 | [-0.127322, -0.036352] | [-0.137694, 0.009163] | 0.000100 | 0.001100 |
| Own cross-session history | Other-maker history | -0.002207 | [-0.059362, 0.049326] | [-0.065989, 0.099290] | 0.943506 | 1.000000 |
| Own cross-session history | No history | 0.039965 | [-0.005489, 0.082221] | [-0.022267, 0.139080] | 0.079292 | 0.555044 |
| Own cross-session history | Personal frequency | -0.080962 | [-0.119201, -0.045748] | [-0.139314, -0.002333] | 0.000100 | 0.001100 |
| Own cross-session history | Partial-pooling model | -0.093760 | [-0.142058, -0.053707] | [-0.150998, -0.006920] | 0.000100 | 0.001100 |

**Found.** No primary predictive advantage is established for the own-history reader. Its difference from other-maker history is unresolved, as is its improvement over no history. It performs worse than population frequency, personal frequency and partial pooling under writer resampling and the eleven-slot Holm correction; the crossed prompt sensitivity retains the disadvantages to personal frequency and partial pooling, but includes zero against population frequency. Same-session history is worse than population frequency under the unadjusted writer interval, but its Holm result and crossed interval are unresolved. These findings concern this frozen reader and evidence construction; they do not establish that personal information is absent or that makers are interchangeable.

**Log loss and calibration.** On the same 232 valid own-history targets, the gain over population frequency is -0.254982 nats (writer interval [-0.396790, -0.126313]) and over personal frequency is -0.251306 ([-0.372772, -0.132407]). The full-support sensitivity assigning invalids -log(0.01) gives -0.288724 and -0.287034 respectively. Baseline probabilities are unchanged, and no valid-only mean is subtracted from an unmatched baseline mean. These are baseline-relative log-loss gains, not exact predictive V-information. Calibration uses ten literal bins and the probability assigned to the stated choice, with equal writer weight on valid support. One same-session response chooses a nonmaximal-probability class; its actual choice is retained for accuracy and calibration. Invalids count as incorrect in system accuracy, remain in system loss and have no invented calibration confidence. All class marginals, bin counts, paired log-loss sensitivities and descriptive contrasts are retained in the aggregate results.

**Support and limits.** Twenty-seven writers have eight targets, two have five, one has seven and one has one; equal-writer weighting is retained. Observed classes are 121 accept, 52 edit, 56 dismiss and five ignore. Own histories contain sixteen decisions for 26 writers, twelve for three and eight for two. Donor histories range from eight to twenty-three decisions because the frozen construction matches rendered character length; four main donors miss the 15% ratio band. Full-sixteen sensitivity retains 26 writers/201 targets; matched donor length retains 27/202; both retain 22/169. Own versus donor remains unresolved in all three, and the subsets do not establish an own-history advantage. The frozen exposure roster positively witnesses eighteen targets; the Stage 14 supplement witnesses thirty-three, with forty-six in their union and 188 unknown. Missing witnesses never imply untouched evidence. These public human process records and GPT-3 suggestions may also have appeared in model pretraining. Writer bootstrap and sign-flip inference assume writer independence that shared histories/donors do not establish; crossed prompt resampling does not repair that shared-evidence dependence. The prompts are fixed, profile/effort API comparisons are unavailable, and this is neither a causal preference-strength estimate nor a human value-identification test.

**Validity and accounting.** All 2,345 archive members, 23 frozen launch bindings, 936 native prompt/wire reconstructions, 468 residency records and exact returned prompt-token counts verify. The entire prepared data build reconstructs from 2,892 source bindings, including exclusions and chronology. The exposure supplement's 161 bindings verify. Ten responses contain a zero probability below the frozen floor; no clipping, repair or reask occurs. Invalid counts are three without history, four with same-session history, two with own cross-session history and one with donor history. The maximum cumulative invalid fraction at completed concurrency groups is 3.846%, below the frozen 5% stop threshold. Six targeted known-answer and serialization tests pass; independent score arithmetic, stated-choice calibration and byte-stable consumer reentry pass. Reentry exposed integer histogram keys that become strings in JSON. The original consumer and first outputs are preserved; a separately pinned successor changes only histogram serialization and its record version. All predictions, per-writer values and reported statistics match the original exactly; independent source reconstruction and byte-stable successor reentry pass. Native supervision exits and the provider app is stopped. Measured allocation is 6,963.564 seconds; the main reservation reconciles from $13.40 to a conservative $4.76, pending final invoice. Combined campaign booking is $5.48, including both Modal runs and the failed API profile pilot.

**Means.** Preserve the completed Modal cell and all invalids. The separate Sonnet profile pilot still fails the complete paired-profile prerequisite, so the API reader pilot and main remain unsubmitted; no automatic retry, model substitution or relaxed output cap follows. The local reader-runtime hold and failed SM4 admission also remain. No tests were harvested from this operational wake. SM7 leaves theory files unchanged, and joint scientific synthesis remains in Friday's final packet; the unavailable API slots cannot support an affirmative conclusion.


## Method summaries

Each method uses the same full target roster for system loss and accuracy; valid log loss and calibration use that method's valid support. Lower losses and calibration error are better; higher accuracy is better. Paired comparisons below use identical support, unlike a subtraction of these marginal summaries.

| Method | Valid / attempted | System half-Brier | Valid log loss | System accuracy | Valid calibration error |
|---|---:|---:|---:|---:|---:|
| Last recorded decision | 234 / 234 | 0.367593 | 1.298551 | 0.465553 | 0.288573 |
| Partial-pooling model | 234 / 234 | 0.294481 | 1.047100 | 0.554263 | 0.069609 |
| Population frequency | 234 / 234 | 0.310209 | 1.093452 | 0.534101 | 0.060600 |
| Personal frequency | 234 / 234 | 0.307278 | 1.095143 | 0.535714 | 0.084843 |
| Effort-weighted personal fit | 234 / 234 | 0.294417 | 1.049192 | 0.562327 | 0.086157 |
| Shuffled effort weights | 234 / 234 | 0.294519 | 1.047813 | 0.550230 | 0.054184 |
| Unweighted effort features | 234 / 234 | 0.294847 | 1.050344 | 0.542166 | 0.052996 |
| No history | 231 / 234 | 0.428205 | 1.566549 | 0.426267 | 0.351346 |
| Same-session history | 230 / 234 | 0.362691 | 1.295898 | 0.458295 | 0.200565 |
| Own cross-session history | 232 / 234 | 0.388240 | 1.360603 | 0.426037 | 0.234584 |
| Other-maker history | 233 / 234 | 0.386034 | 1.376582 | 0.424654 | 0.225707 |

## Full saved-output contrasts

All entries are rival-minus-reader gains. Half-Brier is the primary metric only for the six marked comparisons above; all remaining entries here are descriptive and unadjusted. Log loss uses identical pairwise valid support; system log loss includes invalid penalties. Intervals are writer and crossed writer/prompt 95% resampling intervals.

| Reader | Rival | Metric | Targets | Gain | Writer interval | Crossed interval | Raw p (half-Brier only) |
|---|---|---|---:|---:|---|---|---:|
| No history | Last recorded decision | half_brier | 234 | -0.060613 | [-0.118219, -0.003555] | [-0.154828, 0.028930] | 0.054295 |
| No history | Last recorded decision | log_loss | 231 | -0.262576 | [-0.473159, -0.038696] | [-0.652583, 0.075752] | not tested |
| No history | Last recorded decision | system_log_loss | 234 | -0.300582 | [-0.520293, -0.069003] | [-0.696615, 0.045801] | not tested |
| No history | Partial-pooling model | half_brier | 234 | -0.133725 | [-0.173058, -0.093071] | [-0.203931, -0.056455] | 0.000100 |
| No history | Partial-pooling model | log_loss | 231 | -0.513878 | [-0.669795, -0.354726] | [-0.820912, -0.244496] | not tested |
| No history | Partial-pooling model | system_log_loss | 234 | -0.552033 | [-0.718405, -0.385153] | [-0.882926, -0.264320] | not tested |
| No history | Population frequency | half_brier | 234 | -0.117997 | [-0.155046, -0.080714] | [-0.183128, -0.047678] | 0.000100 |
| No history | Population frequency | log_loss | 231 | -0.468815 | [-0.604963, -0.325967] | [-0.764985, -0.222328] | not tested |
| No history | Population frequency | system_log_loss | 234 | -0.505681 | [-0.656015, -0.351705] | [-0.822576, -0.239517] | not tested |
| No history | Personal frequency | half_brier | 234 | -0.120927 | [-0.160842, -0.079868] | [-0.196811, -0.045773] | 0.000100 |
| No history | Personal frequency | log_loss | 231 | -0.465927 | [-0.633492, -0.291198] | [-0.810084, -0.186227] | not tested |
| No history | Personal frequency | system_log_loss | 234 | -0.503990 | [-0.679784, -0.324513] | [-0.865193, -0.210909] | not tested |
| Same-session history | Last recorded decision | half_brier | 234 | 0.004902 | [-0.048264, 0.056817] | [-0.089501, 0.095107] | 0.865113 |
| Same-session history | Last recorded decision | log_loss | 230 | -0.008914 | [-0.206296, 0.184481] | [-0.372474, 0.314765] | not tested |
| Same-session history | Last recorded decision | system_log_loss | 234 | -0.045365 | [-0.248817, 0.154242] | [-0.402614, 0.285787] | not tested |
| Same-session history | Partial-pooling model | half_brier | 234 | -0.068210 | [-0.102266, -0.035598] | [-0.126198, 0.001627] | 0.001100 |
| Same-session history | Partial-pooling model | log_loss | 230 | -0.251412 | [-0.388866, -0.119679] | [-0.494402, -0.002643] | not tested |
| Same-session history | Partial-pooling model | system_log_loss | 234 | -0.296816 | [-0.448497, -0.151238] | [-0.539721, -0.042892] | not tested |
| Same-session history | Population frequency | half_brier | 234 | -0.052482 | [-0.087291, -0.017811] | [-0.118381, 0.018189] | 0.007399 |
| Same-session history | Population frequency | log_loss | 230 | -0.206744 | [-0.340415, -0.073426] | [-0.470064, 0.036519] | not tested |
| Same-session history | Population frequency | system_log_loss | 234 | -0.250464 | [-0.399073, -0.104699] | [-0.511639, -0.002631] | not tested |
| Same-session history | Personal frequency | half_brier | 234 | -0.055412 | [-0.090223, -0.021905] | [-0.120332, 0.011991] | 0.005099 |
| Same-session history | Personal frequency | log_loss | 230 | -0.199543 | [-0.342854, -0.055436] | [-0.471057, 0.033700] | not tested |
| Same-session history | Personal frequency | system_log_loss | 234 | -0.248773 | [-0.406502, -0.095476] | [-0.521551, -0.006007] | not tested |
| Same-session history | Own cross-session history | half_brier | 234 | 0.025549 | [-0.024105, 0.076465] | [-0.061998, 0.089797] | 0.339766 |
| Same-session history | Own cross-session history | log_loss | 228 | 0.052662 | [-0.118515, 0.214573] | [-0.257837, 0.274746] | not tested |
| Same-session history | Own cross-session history | system_log_loss | 234 | 0.038261 | [-0.160068, 0.230550] | [-0.280137, 0.283258] | not tested |
| Own cross-session history | Last recorded decision | half_brier | 234 | -0.020647 | [-0.062104, 0.020452] | [-0.092632, 0.070825] | 0.353765 |
| Own cross-session history | Last recorded decision | log_loss | 232 | -0.043629 | [-0.184939, 0.104178] | [-0.304685, 0.272443] | not tested |
| Own cross-session history | Last recorded decision | system_log_loss | 234 | -0.083625 | [-0.224418, 0.063294] | [-0.364675, 0.233529] | not tested |
| Own cross-session history | Partial-pooling model | half_brier | 234 | -0.093760 | [-0.142058, -0.053707] | [-0.150998, -0.006920] | 0.000100 |
| Own cross-session history | Partial-pooling model | log_loss | 232 | -0.300452 | [-0.441363, -0.172619] | [-0.497595, -0.030571] | not tested |
| Own cross-session history | Partial-pooling model | system_log_loss | 234 | -0.335076 | [-0.477128, -0.205477] | [-0.550210, -0.058821] | not tested |
| Own cross-session history | Population frequency | half_brier | 234 | -0.078032 | [-0.127322, -0.036352] | [-0.137694, 0.009163] | 0.000100 |
| Own cross-session history | Population frequency | log_loss | 232 | -0.254982 | [-0.396790, -0.126313] | [-0.449859, 0.009657] | not tested |
| Own cross-session history | Population frequency | system_log_loss | 234 | -0.288724 | [-0.435155, -0.155010] | [-0.507537, -0.017308] | not tested |
| Own cross-session history | Personal frequency | half_brier | 234 | -0.080962 | [-0.119201, -0.045748] | [-0.139314, -0.002333] | 0.000100 |
| Own cross-session history | Personal frequency | log_loss | 232 | -0.251306 | [-0.372772, -0.132407] | [-0.457999, -0.003855] | not tested |
| Own cross-session history | Personal frequency | system_log_loss | 234 | -0.287034 | [-0.407996, -0.165296] | [-0.519424, -0.032552] | not tested |
| Own cross-session history | No history | half_brier | 234 | 0.039965 | [-0.005489, 0.082221] | [-0.022267, 0.139080] | 0.079292 |
| Own cross-session history | No history | log_loss | 229 | 0.198499 | [0.033911, 0.362074] | [-0.022145, 0.596821] | not tested |
| Own cross-session history | No history | system_log_loss | 234 | 0.216957 | [0.049273, 0.387805] | [-0.033557, 0.634510] | not tested |
| Own cross-session history | Other-maker history | half_brier | 234 | -0.002207 | [-0.059362, 0.049326] | [-0.065989, 0.099290] | 0.943506 |
| Own cross-session history | Other-maker history | log_loss | 231 | 0.020936 | [-0.140637, 0.167180] | [-0.175864, 0.372497] | not tested |
| Own cross-session history | Other-maker history | system_log_loss | 234 | 0.006666 | [-0.176113, 0.170010] | [-0.205429, 0.366161] | not tested |
| Other-maker history | Last recorded decision | half_brier | 234 | -0.018441 | [-0.073514, 0.036571] | [-0.102420, 0.056430] | 0.529547 |
| Other-maker history | Last recorded decision | log_loss | 233 | -0.081123 | [-0.268249, 0.107314] | [-0.404553, 0.201073] | not tested |
| Other-maker history | Last recorded decision | system_log_loss | 234 | -0.090291 | [-0.282229, 0.101396] | [-0.423613, 0.198503] | not tested |
| Other-maker history | Partial-pooling model | half_brier | 234 | -0.091553 | [-0.129734, -0.055661] | [-0.158722, -0.030093] | 0.000100 |
| Other-maker history | Partial-pooling model | log_loss | 233 | -0.330591 | [-0.461099, -0.201055] | [-0.589370, -0.113544] | not tested |
| Other-maker history | Partial-pooling model | system_log_loss | 234 | -0.341742 | [-0.480439, -0.207120] | [-0.606093, -0.122076] | not tested |
| Other-maker history | Population frequency | half_brier | 234 | -0.075825 | [-0.107200, -0.045813] | [-0.134857, -0.024652] | 0.000200 |
| Other-maker history | Population frequency | log_loss | 233 | -0.285133 | [-0.396517, -0.172243] | [-0.523162, -0.099616] | not tested |
| Other-maker history | Population frequency | system_log_loss | 234 | -0.295390 | [-0.414194, -0.178370] | [-0.540958, -0.104600] | not tested |
| Other-maker history | Personal frequency | half_brier | 234 | -0.078755 | [-0.117453, -0.041698] | [-0.154176, -0.016860] | 0.000400 |
| Other-maker history | Personal frequency | log_loss | 233 | -0.281635 | [-0.424027, -0.139260] | [-0.584247, -0.052900] | not tested |
| Other-maker history | Personal frequency | system_log_loss | 234 | -0.293699 | [-0.445637, -0.146042] | [-0.605995, -0.057810] | not tested |

## Fixed support sensitivities

These descriptive half-Brier gains repeat all available primary contrasts on each predeclared subset. Full-sixteen means sixteen own-history decisions; matched means donor rendered length within 15% of own history; both applies both filters. No subset replaces the full main roster or chooses a next run.

| Subset | Reader | Rival | Writers / targets | Gain | Writer interval | Crossed interval |
|---|---|---|---:|---:|---|---|
| full_sixteen | Same-session history | Population frequency | 26 / 201 | -0.051399 | [-0.091686, -0.010886] | [-0.121012, 0.016809] |
| full_sixteen | Own cross-session history | Partial-pooling model | 26 / 201 | -0.071803 | [-0.107956, -0.036684] | [-0.136284, 0.001812] |
| full_sixteen | Own cross-session history | Population frequency | 26 / 201 | -0.052349 | [-0.088562, -0.016918] | [-0.116597, 0.022603] |
| full_sixteen | Own cross-session history | Personal frequency | 26 / 201 | -0.061064 | [-0.093567, -0.029014] | [-0.128163, 0.009918] |
| full_sixteen | Own cross-session history | No history | 26 / 201 | 0.060968 | [0.024350, 0.098726] | [-0.005875, 0.143848] |
| full_sixteen | Own cross-session history | Other-maker history | 26 / 201 | 0.026056 | [-0.018487, 0.073341] | [-0.037277, 0.097965] |
| donor_length_matched | Same-session history | Population frequency | 27 / 202 | -0.039835 | [-0.077000, -0.002517] | [-0.113857, 0.038541] |
| donor_length_matched | Own cross-session history | Partial-pooling model | 27 / 202 | -0.092397 | [-0.143616, -0.047430] | [-0.156048, 0.002111] |
| donor_length_matched | Own cross-session history | Population frequency | 27 / 202 | -0.075052 | [-0.128318, -0.029124] | [-0.142104, 0.022185] |
| donor_length_matched | Own cross-session history | Personal frequency | 27 / 202 | -0.080837 | [-0.122780, -0.041710] | [-0.146069, 0.006732] |
| donor_length_matched | Own cross-session history | No history | 27 / 202 | 0.033489 | [-0.015443, 0.077116] | [-0.035951, 0.139986] |
| donor_length_matched | Own cross-session history | Other-maker history | 27 / 202 | -0.003339 | [-0.065895, 0.052563] | [-0.072888, 0.108905] |
| both | Same-session history | Population frequency | 22 / 169 | -0.035680 | [-0.080762, 0.007055] | [-0.115514, 0.039232] |
| both | Own cross-session history | Partial-pooling model | 22 / 169 | -0.066138 | [-0.104169, -0.029774] | [-0.142045, 0.015886] |
| both | Own cross-session history | Population frequency | 22 / 169 | -0.044023 | [-0.081768, -0.006852] | [-0.119567, 0.038671] |
| both | Own cross-session history | Personal frequency | 22 / 169 | -0.057293 | [-0.093294, -0.022658] | [-0.135151, 0.024104] |
| both | Own cross-session history | No history | 22 / 169 | 0.056839 | [0.017997, 0.097447] | [-0.020400, 0.148320] |
| both | Own cross-session history | Other-maker history | 22 / 169 | 0.029806 | [-0.019340, 0.078702] | [-0.044129, 0.107224] |

## Worked scoring examples

A uniform four-category forecast has half-Brier 0.375; a perfect forecast has zero and a completely wrong point forecast has one. A saved main reply assigning zero to a category violates the frozen 0.01 probability floor even when its four numbers sum to one: it receives system half-Brier one and system log loss -log(0.01), with its original response retained. A valid stated choice that differs from the largest probability is scored as that stated choice for accuracy and confidence calibration. These apparatus examples disclose no human text or target identities.

Theory files remain unchanged under SM7. Proposed implications for the existing reader and maker-history rows belong to the curator's final-packet review, with the unavailable API comparisons explicit.
