# Week 5 runtime successor

DESIGN CHECK: LESSONS 3–5. All admission and accounting in RUNTIME.md remain.
This successor binds every completed output file, including Parquet and CSV,
instead of selecting extensions. Mutable progress and open supervisor logs are
excluded. Source capsules and the original native receipt remain immutable.

A producer may yield at its own checkpoint quantum without a resource request.
That is retained as PAUSED, with its producer reason and checkpoint validation
requirement, not a missing-file failure. A resource request permits sixty
seconds for cooperative checkpointing before descendant containment terminates
the attempt and records an environmental failure. It never licenses an inference.

Known-answer validation runs the same native arithmetic/replay fixture on the
successor. Targeted checks exercise an extra binary output binding and a
producer-directed yield with no external request. Both outcome directions have
identical handling. The smaller route is the same finite constructed fixture.
