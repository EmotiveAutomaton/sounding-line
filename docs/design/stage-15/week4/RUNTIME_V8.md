# Week 4 runtime v8: actual progress-temporary race

This is engineering recovery under amendment B, with no scientific change.
S2-source-sample execution finished, but v7's monitor failed during verification
when `timing_p6.progress` replaced its PID-named temporary between enumeration
and stat. The UUID-temporary exception did not cover that actual writer.
The failed attempt, pinned v7 and source capsule remain immutable.

The case and its check: both repository atomic writers must survive concurrent
accounting; vanished ordinary files and other I/O failures must still refuse.
Use the writers' actual names, deterministic disappearance between enumeration
and stat, concurrent native writing/scanning, exact retained byte totals, and a
native oversized fixture that must terminate through the unchanged byte guard.

The smaller route: constructed fixtures only, within the original 120 CPU-second
runtime-validation allowance, including the prior 15-second reserve and original
1.578125-second native run. Reserve a further 20 seconds for targeted tests and
preparation. Each fresh native fixture gets at most 30 CPU seconds; the second
uses the first's measured charge. No corpus is admitted by these checks.

Only vanished `PROGRESS.json.<positive decimal PID>.tmp` names are added to the
existing UUID JSON temporary exception. Present temporaries still count; ordinary
missing files, near-match names, permissions and other I/O errors remain fatal.
Containment, scientific modules, CPU/wall/output ceilings, slots, campaign window,
inputs and seed stay unchanged. The launcher and runtime are versioned copies;
neither prior attempt nor shared writer is edited.

S2 retains its original 3,600 CPU-second allowance and 1,800-second analytical
reserve. Its failed attempt charged 615.859375 seconds, including the forced-stop
margin; prior charge was 487.25. Complete replay must start at the beginning.
The interrupted verification's measured pace with the unchanged 1.5 factor
forecasts 717.442630 seconds, exceeding the remaining 696.890625 even before
continuation validation. The smaller timing-prefix forecast is retained but
cannot override the observed slower corpus verification. Do not dispatch replay
or admit these saved inputs without separately validated, affordable recovery.

No partial verification credit, changed population, repaired scientific score,
new paid work, GPU restart, publication or delegation is authorized here.
