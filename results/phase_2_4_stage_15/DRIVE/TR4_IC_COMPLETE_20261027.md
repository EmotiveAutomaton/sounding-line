# Complete TR4 instrument check

**Hypothesis.** Could the unchanged handling-forecast pipeline recognize known preference-like changes, or can its reporting rule block an adaptive reader that actually tracks them?

**METHOD.** Evaluate the complete frozen matrix of three categorical-probability change magnitudes and four independent seeds per magnitude. Each constructed world has eighteen writers, four discovery and fourteen test, twenty-four sessions and one hundred choices per session. At the halfway point acceptance probability changes by the declared magnitude, with opposite directions across writers and the remaining probability redistributed equally. Corresponding magnitudes share initial probabilities and random draws within each seed. Preserve all six parent forecasts, discovery-only tuning, prospective scoring, two hundred outcome-order references, one thousand writer-label references, two thousand paired uncertainty draws and the original reference-bias gate. Independently regenerate the truth, observations and complete analysis of every world, including retained checkpoints.

**Found.** In constructed worlds, planted drift produces positive forecast-gain intervals, but the unchanged biased-reference gate prevents positive admission; volatility-reliability uncertainty remains unsupported.

This table reports counts among all four completed worlds at each frozen change magnitude. Magnitude is the absolute change in acceptance probability, also the total-variation change of the four-class distribution. Positive admission means the full unchanged primary rule passes; positive interval means the lower writer-cluster gain bound exceeds zero before that rule's reference gate. The last two columns count fired bias flags and unsupported reliability uncertainty, respectively.

| Change magnitude | Worlds | Positive admission | Positive gain interval | Biased reference | Unsupported reliability |
|---|---:|---:|---:|---:|---:|
| 0.00 | 4 | 0 / 4 | 0 / 4 | 4 / 4 | 4 / 4 |
| 0.15 | 4 | 0 / 4 | 4 / 4 | 4 / 4 | 4 / 4 |
| 0.30 | 4 | 0 / 4 | 4 / 4 | 4 / 4 | 4 / 4 |

The preregistered largest-change admission fraction is zero of four, beside zero of four under stationarity. Every changed world nevertheless has a positive forecast-gain interval before the reference gate. This separates tracking behavior in these worlds from the complete rule's ability to license a result. It does not justify removing the gate, substituting a secondary model or revising the completed human comparison.

The following table includes every completed world. Gain is whole-history log loss minus adaptive local-level log loss per choice; positive values favor adaptation. Intervals are the original writer-cluster 95% percentile intervals. Bias ratio is the absolute outcome-reference mean divided by its sample standard deviation; the frozen flag fires above 0.25. Undefined draws are retained paired volatility-reliability draws, not dropped observations. These are descriptive constructed-world diagnostics, not new significance tests.

| Change magnitude | Frozen seed | Forecast gain | Gain interval | Reference bias ratio | Undefined reliability draws |
|---|---:|---:|---|---:|---:|
| 0.00 | 202610260 | -0.000291030 | [-0.000553704, -0.000078726] | 1.656120 | 2000 / 2000 |
| 0.00 | 202610261 | -0.000333352 | [-0.000755484, 0.000014203] | 1.670260 | 2000 / 2000 |
| 0.00 | 202610262 | -0.000452550 | [-0.000806916, -0.000227546] | 1.436491 | 2000 / 2000 |
| 0.00 | 202610263 | -0.000407849 | [-0.000925214, 0.000013126] | 1.343842 | 2000 / 2000 |
| 0.15 | 202610260 | 0.012395816 | [0.010567882, 0.014296457] | 2.763051 | 1610 / 2000 |
| 0.15 | 202610261 | 0.011883782 | [0.010299946, 0.013504410] | 2.584967 | 1516 / 2000 |
| 0.15 | 202610262 | 0.014927238 | [0.013380767, 0.016353381] | 2.697600 | 968 / 2000 |
| 0.15 | 202610263 | 0.014174634 | [0.010706694, 0.017301635] | 2.422509 | 590 / 2000 |
| 0.30 | 202610260 | 0.076138069 | [0.069681135, 0.082180699] | 5.191237 | 2000 / 2000 |
| 0.30 | 202610261 | 0.074561239 | [0.069087634, 0.079998826] | 4.974182 | 2000 / 2000 |
| 0.30 | 202610262 | 0.079351491 | [0.071309251, 0.088263147] | 4.993182 | 2000 / 2000 |
| 0.30 | 202610263 | 0.077128983 | [0.071064132, 0.083092182] | 5.480281 | 2000 / 2000 |

All latent probability vectors, sampled counts, seed identities and change magnitudes independently reconstruct. The oracle penalty of retaining old probabilities is exactly zero in stationary worlds and positive in every changed world. All twelve reference banks and paired uncertainty banks retain their full frozen counts. No world, unsupported correlation, model or dose is discarded. The reference mean is displaced even in stationary worlds; this gate is therefore not a diagnostic that uniquely identifies planted drift. The causal reason for its displacement is not established by this comparison.

**Means.** The tested adaptive forecast can respond to the planted changes in this particular regime, while the unchanged reporting rule admits none. The complete instrument has not established useful calibrated sensitivity, and volatility reliability remains unsupported. Four independent seeds per magnitude provide a coarse conditional diagnostic, not a general size/power estimate, a human negative or recovery of human values. The human parent S15-TR4-20261027 and the broader drift claim remain unchanged. The exact program reads constructed categorical counts, not human judgments or generated narratives.

The original progress-file failure and all of its cost remain recorded. The distinct recovery preserved five exact execution checkpoints and independently recomputed all twelve worlds. All 48 pinned inputs/code records and 29 sealed outputs authenticate; every native worker exited and its CPU lease released. Recovery execution plus full replay used 809.046875 CPU seconds. Cumulative construction/test reserves, initial validation, timing, failed execution, repair validation and recovery total 1267.828125 of the original 1800 CPU seconds. No extension was used.

This completes the single first-generation instrument check. A firing scientific gate is a result and is not repaired. No descendant, additional calibration grid, human reanalysis, GPU restart, paid work or external transfer is authorized by this landing. No new tests were harvested from the operational wake. TR3's explicit no-further-retry decision hold and the other resource/source/transfer holds persist; the ready-card backlog remains incomplete.
