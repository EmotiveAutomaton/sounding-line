# BK SLOT BANK

**Hypothesis.** Does the counted allocator enforce the packet's original-bank limit for backlog work while preserving other families' access to available capacity?

**METHOD.** Review the predecessor-to-successor allocator change and its launcher, inspect real leases and retained admission records, then authenticate isolated allocation cases and a real counted execution with independent verification. Preserve all existing workers and leases.

**Found.** Backlog admission now uses only the original four CPU slots, with the corrected allocator independently verified and historical allocation deviations retained.

The successor restricts BK to slots zero through three; other families prefer the four additional slots and may use idle original slots. Resource admission, exclusive leases, checkpoint validation and numerical thread limits are unchanged. Nine targeted tests and the isolated native allocation proof cover original-bank saturation, cross-family fallback and preservation of occupied leases. The real counted fixture used original slot two, completed independent verification, sealed fifty-one files and consumed 0.921875 CPU seconds. Its owner exited and its lease was released.

The historical inspection retains nine BK admissions in the additional bank: one community-choice source pilot and eight constructed runtime fixtures. They are allocation deviations, not new scientific findings; their costs and outputs remain. No current BK lease violated the allocation at inspection, and no live worker was migrated or restarted. The corrected design was committed before new admission. New keystroke-source work now uses this launcher. No score, source, CPU ceiling or gear changed.
