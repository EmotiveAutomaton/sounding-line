# DR1 actual-input timing admission

This implements the outstanding timing requirement of the [full comparison](DIRECTED_READING_BUILD_20261020.md).
The original scientific runner, policy definitions, 200 random orders, 2,000
paired writer draws, full reference gallery and eligible writer cohort stay
unchanged. This pilot adds no scientific contrast or new research question.

DESIGN CHECK: LESSONS sections 3–5 read. Under either null or alternative,
outcomes cannot choose timing units or admission. Full-gallery formula parity,
known-answer work counts, immutable inputs and exact fresh replay are required.
Incomplete units, invalid timings or altered evidence fail closed.

Reuse the original hash-bound PMAP session records and dictionary. For every
eligible writer, use the full gallery and original reference/deviation formulas;
evaluate chronological, directed and mixed order, plus fixed random replicates
0–4 with their original seeds. Retain every prefix in each sampled order.
Record deterministic output hashes and byte counts, and elapsed work times.
Do not report sampled policy scores or calculate a pilot contrast.

Repeat the entire pilot in a separate native process and require exact hashes.
For each writer use the slower of the two observed runs for each fixed policy,
and the slowest observed random order to forecast each of the full 200 orders.
Add source/preparation overhead, multiply by two for full execution and replay
and by two again for forecast margin, then add 30 seconds for startup and final
aggregation. Estimate ledger capacity from the largest sampled serialized
order, also doubled. This is a conservative measured forecast, not a guarantee;
the full-run hard deadline remains binding.

Six targeted checks include exact sampled-output parity with the original full
runner, complete counts and margins, malformed work/timing refusal, eligibility,
source/output tampering and full serialized handlers. Complete contained native
constructed validation precedes the real-input pilot. All participant records
and per-writer timing identities stay in ignored raw storage.

Reserve 300 wall seconds for prior DR1 preparation and all constructed
validation; cap the actual pilot's combined execution/replay at 600 seconds.
The original two-CPU-hour ceiling converts conservatively to 3,600 wall seconds
at two numerical threads. Add the pilot's measured charge before full admission;
S4 permits at most one cumulative doubling, to 7,200 wall seconds, if needed.
No reset, reduced full-run order count or automatic successor dispatch follows
from pilot completion. The owner verifies its complete evidence and admits or
holds the original comparison against remaining cost and resources.
