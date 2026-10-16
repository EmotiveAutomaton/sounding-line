# Shared-engine interfaces

Sounding Line consumes canonical ToMpathy commit
`2a0c54233344ae3f64bed9806442289d7dab726a`. The immutable local archive contains
the committed `engine/` tree; it is a dependency capsule, not an editable fork.
No files or services in the companion's working tree are changed.

`runners/next_round/engine_interface.py` verifies every archived file and the
interpreter executable before calls, and asserts that imports come from that
capsule. It uses the companion's existing Python environment with one numerical
thread. Its installed dependency environment is shared and is not a separately
frozen dependency closure; revalidate after environment changes before scientific
use. This interface currently performs local ingestion and conformance checks,
not production serving, registry publishing or scientific model promotion.

The normalized panel boundary requires a named dataset, exact source-byte hash,
codebook, expected row count and per-row source identity, maker label, alternatives,
chosen alternative and observed opening/resolution times. Missing chronology and
ties remain exclusions. Naive or reversed times, duplicate row/option identities,
absent chosen options and census mismatches refuse. Do not invent times, equate
released evaluator labels with people, or join identities across datasets.

The actual engine ingest path passed a constructed three-row fixture: one usable
choice, one missing-time exclusion and one tie. Repeating ingestion leaves one
decision. Three malformed exchange mutations refuse. The engine enables no
scientific module without scoped witnesses. [Receipt](../../../results/phase_2_4_stage_15/ENGINE_INTERFACE_PUBLIC.json).

Native DICES, Community Alignment, PRISM and MultiPref mappings remain separate
admission work. This exchange test does not resolve their codebooks, temporal
availability, released-label census or unit-of-analysis differences. Raw participant
data and provider records stay in the private Stage 15 `raw/` tree.

The Ghost interface is its versioned admission witness, consumed by the canonical
engine's `Admissions` contract: exact implementation/schema hashes, domain, a
passed constructed-world record and a Sounding Line real-data record. Probability
claims additionally require calibration and a passed real-data gate. Missing
witnesses remain a hold; fixture admissions must never be installed as production
admissions. Required next-round twins are not yet available in the inspected checkout.

The paid profile interface is [R3](R3_STRUCTURED_PROFILES.md). Its first structured
pilot completed but failed literal admission. No profile main or feature fit is
admitted, and the old LLM judge role remains retired.

## New committed interface verified October 15

The versioned `engine_interface_v2.py` pins `82789fdb50d9366ab9352129b01ee37622554dfa`
in a separate immutable capsule. Actual interface export and all six constructed
native-panel checks pass; all 117 archived source files verify before/after.
The archive pin supplies commit identity because the export has no checkout
metadata. [Receipt](../../../results/phase_2_4_stage_15/ENGINE_INTERFACE_V2_PUBLIC.json).
Native real-data semantic validation and exact implementation-hash admissions
remain mandatory. The earlier capsule and its evidence remain unchanged.
