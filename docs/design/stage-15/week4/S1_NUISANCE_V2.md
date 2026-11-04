# S1 nuisance first engineering correction

The initial source-cost probe failed before any recurrence outcome: P6 occurrence timestamps are seconds, while the inherited session metadata are milliseconds. Subtracting them directly produced a negative elapsed time, which the validator refused. The original attempt, source, tests and charge remain intact.

The separate v2 wrapper converts only the session start from milliseconds to seconds at the nuisance interface. It leaves all occurrences, histories, donor matching, pair rules, exclusions, controls and estimator unchanged. A mixed-unit known answer now checks two elapsed seconds rather than assuming both source fields share units. The complete original native checks remain and the new source interface is independently replayed. This is healing attempt one, not a changed scientific design; all failed and repeated preparation charges remain part of S1.

The case check and sample route in [the original design](S1_NUISANCE.md) remain binding. Validation of this correction supplies no scientific score.
