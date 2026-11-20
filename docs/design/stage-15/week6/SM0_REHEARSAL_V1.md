# SM0 runtime rehearsal

The portable fixture executes the unchanged, hash-bound SM0 job on constructed
CSV, SPSS and Stata files. Twenty-two cases cover distinct people, missing and
blank identifiers, ambiguous columns, malformed rows, unsupported archives,
outside-root access, repeated read reservations, export limits, suppression,
invalid counts and numerical-thread settings. Every case must pass without skips.
It combines the nine probe cases, three packaged-format cases and ten aggregate
boundary cases; it is separate from the earlier 22-case binding/probe bundle.

The local native rehearsal occupies one counted slot, with a 600-CPU-second
ceiling and a 1,200-second supervisor wall ceiling. Retain its measured cost
exactly once for the applicable preparation admission. The remote job adds its
own 600-second CPU and wall limits inside the existing sealed runner. It uses
two numerical threads and no GPU. Its audit hook refuses private-source opens
and directory enumeration; all fixtures are created in temporary storage.

The returned CSV identifies a constructed cohort of twenty synthetic people,
the complete test count, runtime package versions and measured cost. That count
is not a real-source population. The installed aggregate gate remains separate
and unchanged. A failure emits no qualification output. The remote invocation
counts against the packet's thirty-run Spark ceiling even though it reads no
private records. Preserve every failed invocation and do not exceed the packet's
three-failure bound for any one job.

Use `build_rehearsal.py` to produce a fresh self-contained `run.py` and manifest.
Review its exact hash, locally qualify it, record the publicly provided image
digest and installed runner/gate hashes, then use only the installed sealed
runner. A successful rehearsal permits the separately reviewed structure probe;
it does not admit SM1 or SM2, which still need source mapping, complete statistical
packaging, their own fixture and independent replay.

DESIGN CHECK: LESSONS sections 2-5 read. All declared cases must pass under either
scientific hypothesis. Wrong person counts, output leakage, changed source bytes,
missing cases and malformed input must refuse. Known-answer success qualifies
the runtime interface only; it cannot count as a scientific test or a null.
