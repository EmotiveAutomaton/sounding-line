# TR4 IC PROGRESS FAILURE 20261027

**Hypothesis.** Did the instrument check finish, or did an operational failure interrupt its declared matrix?

**METHOD.** Inspect the original child exception, counted descendant CPU, exact native exits, source pins, released CPU lease and retained checkpoint prefix. Compare the failure path with the progress writer rather than interpreting partial constructed-world statistics.

**Found.** The TR4 instrument check stopped on a Windows progress-file replacement refusal; the incomplete matrix is unscored and its completed checkpoints are preserved.

**Means.** Windows returned access denied during atomic replacement of the shared progress JSON. The writer had no bounded retry for this known sharing failure; the interfering process is not established. The native runtime correctly retained an engineering failure. Five complete execution checkpoints precede the interrupted sixth world, and independent verification never began. They are preserved byte-for-byte but are not admitted results. All workers exited and the lease released. Failed execution used 248.21875 CPU seconds; cumulative charge and reserve are 396.25 of the separate 1,800 seconds. The completed human parent remains unchanged.

The first of two allowed instrument-check engineering repairs will harden only progress I/O and checkpoint continuation. It must validate bounded refusal/retry behavior, unchanged full outputs, tamper refusal and fresh replay of every world. A distinct successor may reuse the authenticated prefix, then finish every remaining world and independently reconstruct the entire twelve-world matrix. All failed cost remains charged, and remaining execution plus validation must fit the original ceiling. No dose, seed, reference, model, estimator or gate may change. TR3 retains its separate no-retry hold; other holds and the unfinished ready-card backlog remain. No new scientific test was harvested.
