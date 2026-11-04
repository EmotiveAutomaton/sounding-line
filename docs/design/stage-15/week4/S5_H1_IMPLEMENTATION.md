# S5 numerical boundary repair and completed label reporting

This freeze retains the [original S5 design](S5_IMPLEMENTATION.md), coefficients, inputs, random effects, controls, seed and resampling rules. No empirical contrast has run. The preserved native constructed pass recovered numerical coefficients but incorrectly classified its exact zero as negative because its interval contained floating-point residue of order 1e-15.

Healing attempt one uses a separately versioned implementation. Values of absolute magnitude at most 1e-12 are treated as numerical zero **only for status classification**. Stored coefficients and interval values are unchanged. Known-zero, positive and reversed decisions are tested explicitly, as are resolvable effects on either side of this tolerance. The original sources, native receipt and omitted-test history remain intact.

The packet's fifteen-label companion is completed before empirical admission. Each fine label's run starts are compared with other implementation-label run starts within authors, retaining edit size, session time and author/project effects. Two authors with at least two starts in both arms are required for this descriptive companion; other labels are explicitly unsupported. These companion estimates and whole-author intervals are descriptive and cannot upgrade the primary. All observed fine labels also receive gap distributions and mixture-posterior summaries. The high-level primary and its thirty-planning-start/six-author floor are unchanged.

All preparation, original native validation and this repair are charged to the same S5 ceiling. The original card's case check and all-identity smaller route remain binding. No new paid or GPU work follows.
