# Bounded producer continuation

The immutable resume adapter's generic draw and wall limits do not cover the
document, embedding-chunk and paired-fit quanta used by GO2, CA1 and V1. This is
an operational mismatch: increasing a stopped producer's work quantum must
not change its scientific contract or discard its completed prefixes.

`week5_resume_v2` preserves the original draw/wall exception and adds only:

- `week5_go_history_bounded_h2`: `max_new_documents`, producer `max_cpu_seconds`.
- `week5_bk_ca1_features`: `max_new_chunks`.
- `week5_bk_v1`: `max_new_fits`.

These are positive finite stopping bounds; counts must be integers. The added
keys remain scientific configuration for every other module. In particular,
clustering enablement, fixtures, draws, permutations, models, source membership,
feature and fitting definitions remain exact. The producer CPU quantum is
distinct from the outer attempt and family ceilings, which remain enforced by
the runtime. This adapter does not authorize additional compute or admission.

The native owner must be stopped and bound to the pinned predecessor plan.
The pinned pause must request checkpoint validation and have a complete output
manifest. Completed, failed, live, changed or ambiguous predecessors refuse.
Inputs, module, family and campaign are equal. Every predecessor pin is retained
with the identical hash; only new runtime/adapter pins may be added. The full
checkpoint tree, including independent replay, is copied to a fresh empty
attempt and rehashed. Operational stop/progress files are excluded using the
unchanged manifest rule. The predecessor is never edited. The consumer still
validates its own seals and performs its full independent replay.

Native constructed proof uses a separate producer process, waits for its actual
exit, copies all three module contracts in another process, and re-verifies the
complete copy in a third process. Targeted refusal cases cover source/output
tampering, missing pins, altered semantics, native liveness, ambiguous terminals,
owner/plan mismatch, and a nonempty destination. This is an adapter proof, not a
new human result. The original adapter and all prior attempts stay immutable.
