# D32: examination markers among declined suggestions

This implements D32's one registered examination extension after its marginal
primary. It uses the frozen 50-cluster repertoire and D6's independently verified
interface extraction. It neither reruns clustering nor opens the null-only
repertoire-expansion variant. All comparisons are descriptive on exposed data.

**Question:** Do declined suggestions outside earlier writing more often lack
recorded examination markers during a short menu display?

**DESIGN CHECK:** LESSONS sections 3–5 and CONTROLS sections 1–4 reread
October 18. Equal within-writer group rates give exactly zero; planted increases
give a positive contrast and reversed increases a negative one. Missing source
bindings, inconsistent selections or fewer than three paired writers are invalid,
never null. Known-answer tests precede the corpus join and include serialization,
fresh-process replay, unknown targets, censoring and changed-source refusal.

**Population and join:** every eligible offer in D32's saved primary rows joins
D6 by unique menu key and displayed option position. Writer and session must
agree, and D32's acceptance indicator must equal D6's selected position. Declined
means not selected, including competitors in a menu where another option was
selected. It does not mean deliberately rejected. Accepted offers are excluded.
Menus with an unresolved hover target or a censored visible episode are excluded
from all contrasts, with counts retained. Non-five-item menus remain eligible.
Missing menus, duplicate offer identities and malformed fields fail the run.

**Primary:** within each writer, the outside-minus-inside difference in the
fraction of declined offers with no logged hover, no logged keyboard target,
not in the first displayed position, and total observed menu-visible duration
at most two seconds. Average the paired differences with equal writer weight.
Require at least three writers with both inside and outside declined offers.
The direction is positive. The denominator is all eligible declined offers in
each group, not only offers without a target event. The first-position exclusion
implements D6's conservative hypothetical default-first-for-all policy; actual
historical default configuration is not authenticated.

Two seconds is an implementation-selected operational cutoff, frozen before
joining these outcomes. It is not an attention threshold supplied by the packet
or validated by human observation. One- and five-second versions are fixed
sensitivities. All durations sum the menu's visible episodes, including reopening;
they are not option-specific gaze duration. Long, unmarked offers remain in the
denominator rather than silently becoming examined offers.

**Other fixed contrasts:** the share with recorded mouse hover (negative
direction); the share targeted by mouse or keyboard (negative); the literal
no-hover/short-display share (positive); the no-mouse-or-keyboard/short-display
share (positive); and the no-target/short-display share under D6's alternative
hypothetical first-default-only-for-argumentative policy (positive). These plus
the one- and five-second sensitivities accompany the primary; none replaces it.
Uncertainty uses 2,000 paired writer-bootstrap draws, seed 20261018, canonical
writer/offer order, and percentile intervals. It conditions on the saved
repertoire and interface extraction, without refitting clusters. A separate
two-sided normal-reference Wald probability is descriptive and may differ from
percentile-interval classification. No probability is fabricated at zero
bootstrap variance. Shared exhaustive direction-aware states govern routing.

**Control:** one fixed permutation of the outside labels among the same eligible
declined offers within each writer, seed 20261019; recompute the primary using
the same writer bootstrap. This retains per-writer denominators but breaks menu
associations. It is a diagnostic alignment control, not a conditional causal
null or a substitute for D32's already completed outcome-shuffle control.

**Limits and route:** no hover is not no exposure, and default highlighting is
not proof of attention. Neither a positive short-display proxy nor a negative
hover contrast identifies pruning, dislike, habit or taste. The result tests
the registered process distinction only through explicitly limited markers;
report both shares and their denominators rather than declaring a latent
mechanism. The marginal parent's family route uses this extension's primary
state: positive opens texture; other valid states count as one routing null.
Invalidity does not advance the counter. V4's fitted taste/habit lens stays blind.

**Execution:** one counted CPU slot, below-normal priority, at most two numeric
threads; no GPU or paid call. Forecast 600 seconds for execution plus independent
replay, maximum wall 1,800 seconds, output cap 256 MiB, original resource floors
unchanged. A first-tenth extraction checkpoint supplies the runtime projection;
yield requests are honored at saved extraction boundaries. Input, source, test
and contract hashes freeze in the dispatch plan. One engineering retry only.
