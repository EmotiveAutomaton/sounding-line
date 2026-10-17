# Suggestion pilot: lossless JSON checkpoint recovery

DESIGN CHECK: LESSONS 3-5 read October 17. NULL: altered JSON values, source
drift, incomplete rows, corrupt bytes or a live predecessor refuse. ALTERNATIVE:
the same native tokenizer offsets survive JSON's tuple-to-list normalization,
with every value, schema and binding preserved. No scientific gate is weakened.

This separate attempt retains the entire v2 precision, input selection, context,
model, scoring and resource contract. It corrects one storage comparison:
compare canonical JSON values before and after lossless compression, then replay
the full score schema. Python tuples and JSON arrays are equivalent at this
serialization boundary; changed offsets, losses or metadata remain failures.

The first v2 checkpoint is retained, independently checked and used to reproduce
the exact old failure and verify byte-identical success through the repaired
handler. It remains unregistered partial evidence, not a completed pilot result.
All selected scoring is rerun; no partial timing is reused. The v2 source and
failure stay immutable. Admission requires its independent failure receipt,
source hashes, retained checkpoint binding and exact native closure.

Charge v1, the precision diagnostic and v2 whole lifetimes against the original
two-hour pilot computation allowance. Reuse only the verified v1 input census,
not its scores. Main execution still requires the separately landed complete
v3 pilot and measured threefold forecast within 72 hours and 32 GiB. No automatic
main dispatch, new study, paid call, corpus reduction or threshold change.
