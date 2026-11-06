# WEEK4 S6S H1 NATIVE CORRECTION 20261104

**Hypothesis.** Does the optimized specification implementation have the native validation attributed to it?

**METHOD.** Reconcile the native event against the landing hash, inspect the exact optimized plan, all outputs, source pins and exited native identities, then inspect the actual dependency pins in both cost probes and the running full calibration. Preserve the first landing bytes because they are pinned historical evidence.

**Found.** The optimized specification fixture passed native replay; its first landing misattributed the earlier fixture, and this corrected receipt supplies the actual source binding without changing valid computation.

The copied landing helper retained the earlier fixture directory for native mode only. The first receipt therefore contained the original fixture's completion and plan hashes, not the optimized fixture's. The optimized fixture independently completed beforehand, including its explicit exact-comparator-reuse check; 15 outputs and 48 pins verify. It charged 2.046875 CPU seconds. Seven original and four additional targeted checks were recorded separately. Both cost probes and full calibration directly pinned the actual optimized completion and charged its actual cost. The receipt-validation helper checked a full-write-through flag but failed to require its completion hash to equal that dependency. The resulting attribution and write-through defect is retained explicitly.

**Means.** Supersede the first attribution with this receipt. Preserve both originals and all prior charges; no estimator, output, ceiling, criterion or active source is edited. Actual native execution and downstream computation were valid, so they are not restarted merely to fix reporting. The next preparation helper must require exact receipt-to-completion equality and use this corrected receipt. Full calibration and human admission remain separate. No scientific result or new test is harvested from this correction.
