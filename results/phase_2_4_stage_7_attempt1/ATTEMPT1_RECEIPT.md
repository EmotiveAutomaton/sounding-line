# Stage 7 attempt 1 (2026-09-02 10:46 to 11:04): stopped in the integrity block, superseded

Launched 10:46 (pilot 4.6 min, workload tier 0.705). I01, I02, I03, I14, I04, D07, D08, D01,
D03, D06 landed; I05, I06, I10, I11 landed INSTRUMENT_FAILED on their own should-break cases;
the engine was stopped mid-I07 on the curator's order to check every queued cell before it
runs. The read-through found the stop truth false in every constructed world. Repairs,
measurements, and the relaunch are recorded in FINDINGS L332 and the registry's Stage-7
runtime log. Nothing scientific ran; the capsules, predictions, oracle bundles, posteriors,
and raw outputs of this attempt were pruned; the dependency audit (deterministic) was copied
forward to the relaunched root.
