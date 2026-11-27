# ACC1 · Does a change in reward trajectory predict first-play happiness?

**Registered prediction.** Prior work predicts a positive acceleration coefficient. The packet’s alternative forecast was an interval crossing zero. The positive reading requires all three fits to clear zero.

**Source and sample.** Class P. Rutledge and colleagues, Great Brain Experiment first plays, Dryad (CC0). [Deposit](https://doi.org/10.5061/dryad.prr4xgxkk). The table identifies contributing people or paired observations for each estimate.

**Registered quantities.** Hold out whole players. Fit the second difference in realized reward on the test players under the frozen one-rate model, two-rate model and endpoint exclusion. Intervals resample whole test players.

| Quantity | Estimate [interval] | Size and unit | Observations | Reading |
|---|---:|---|---:|---|
| All players, one fading rate | 0.00300221 [0.00248818, 0.003528] | 12715 people | — | Predicted direction |
| All players, one fading rate, bootstrap standard error | 0.000266478 | 12715 people | — | Descriptive |
| All players, two fading rates | 0.00237036 [0.00186587, 0.00289023] | 12715 people | — | Predicted direction |
| All players, two fading rates, bootstrap standard error | 0.000265735 | 12715 people | — | Descriptive |
| All players, development common rate | 0.65 | 29665 people | — | Descriptive |
| All players, development good rate | 0.5 | 29665 people | — | Descriptive |
| All players, development bad rate | 0.7 | 29665 people | — | Descriptive |
| Endpoint sensitivity, one fading rate | 0.00288702 [0.00243725, 0.00334414] | 11652 people | — | Predicted direction |
| Endpoint sensitivity, one fading rate, bootstrap standard error | 0.000234009 | 11652 people | — | Descriptive |
| Endpoint sensitivity, development common rate | 0.65 | 27202 people | — | Descriptive |
| Endpoint sensitivity, development good rate | 0.5 | 27202 people | — | Descriptive |
| Endpoint sensitivity, development bad rate | 0.7 | 27202 people | — | Descriptive |

**Verdict — positive.** All three held-out coefficients have positive lower bounds. The scale-end check and the two-rate fit retain the direction.

**Limit.** A rating comes every two or three trials. The last three rewards can reach before the previous rating. The preflight also found excess positive readings under a scale ceiling.

**Withholding and release condition.** All registered fits are reported.

[Released table](ACC1.csv) · [Report generator](../../../tools/r48_reports.py) · [Original record](../../../results/phase_2_4_stage_15/WEEK8/ACC1_R48_RETURN.md)
