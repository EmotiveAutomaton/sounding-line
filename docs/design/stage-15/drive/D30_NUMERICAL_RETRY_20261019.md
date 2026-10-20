# D30: one certified numerical retry

This is the single engineering retry permitted by the October 18 mid-run rule 2.
The original main stopped at a non-converged bootstrap fit after saving its
complete checkpoint prefix. It supplies no scientific result. Original source,
failure, logs and checkpoints remain immutable.

The numerical diagnostic reproduces the same failure from the fixed design and
random stream. Its line search ends on a floating-point plateau. A local Newton
continuation from that exact last iterate reaches the original gradient
tolerance; this is neither a changed start nor a different statistical model.

The separate certified fitter calls the original fitter first. Every successful
original fit is returned unchanged. Only its explicit abnormal line-search stop
permits continuation, within the original total 200-iteration limit, with at
most 20 local Newton steps and 50 step halvings. Two finite-difference scales
must give positive curvature on free variance coordinates. The projected
gradient must satisfy the original 0.000001 tolerance; objective movement from
the stopped iterate must remain within the original relative 0.0000000001
function tolerance. A step is accepted only when that gradient strictly
improves within the same function tolerance. Variance ceilings, undefined
information, exhausted iterations and indefinite curvature continue to refuse.
No failed draw is deleted, redrawn or replaced by a different contrast.

Rows, seeds, fixed and random effects, primary, four arms and all controls stay
fixed. The recovery authenticates the failed attempt and each saved block's
binding and receipt, then copies the completed prefix byte-for-byte. Fresh
verification refits the entire comparison, including that prefix, and requires
exact saved-result equality. The original point-parity gate also remains.

The frozen prior cost includes both pilots, the entire failed main and a
conservative 180-second reserve for this bounded numerical diagnosis and
validation. The original 19,800-second total is unchanged; the supervisor also
retains 60 seconds of administration margin. The remaining cost projection and
week resource/drain guards remain active. A further engineering failure ends
this card for the campaign; it cannot be relabelled environmental.

**DESIGN CHECK.** LESSONS sections 3-5, particularly certified solutions,
unchanged accuracy, complete serialization and immutable historical sources.
Require exact successful-fit preservation, positive/zero/reversed known
answers, the retained actual failure at the original tolerances, explicit
rejection of non-line-search failure, bad curvature, exhausted iterations,
variance ceilings and nonlocal changes, plus complete serialized prefix reuse,
tamper refusal and fresh counted native replay. Retain every validation failure.
No corpus score is reported until full execution and verification finish.
