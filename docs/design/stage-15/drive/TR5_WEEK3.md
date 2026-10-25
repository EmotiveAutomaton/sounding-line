# TR5: failure after an accepted run

25 October 2026. Builder freeze for Week 3's TR5; no corpus result.

The source handler `week3_trust_inputs` retains all 1,399 original canonical
sessions, with an independent replay of accepted Unicode atoms. The failure
anchor is the first user deletion crossing 80% of the original accepted span.
Sparse retention histories preserve each accepted span's surviving original
characters at every deletion. Run length counts consecutive earlier accepted
and kept menus before the failed acceptance, pooled at five, with retention
judged at that failure anchor. Later deletions cannot move the original bin.

The five menus on each side must be in the same session and have observed
canonical resolution. Menus resolving at the anchor are in the before window.
The position decile is the number of canonical menus resolved by the anchor,
divided by the session's total canonical menu count, with the endpoint in decile
nine. This definition is shared by failure and control anchors. The source
also retains each canonical menu's logged temperature, without imputing missing
settings, for the explicitly observational secondary.

Every failure is matched to all supported accepted-span control points of the
same writer and the same run length and position decile. A control anchor uses
the failure's exact elapsed delay after its own accepted insertion; the state is
the last logged state at or before that time. The control's own span must retain
at least 80% of its original characters at that anchor. Later deletion does not
disqualify it. Controls with incomplete or censored five-menu windows are
unsupported. Each failure averages its matched controls; control multiplicity
does not give the failure more primary weight.

The median run length is frozen across complete matched failures before the
comparison, and divides long (at least the median) from short. Support requires
60 complete matched failures from 20 writers and both bins. All candidate,
complete-window and matched counts are retained separately. Thin support is
unsupported rather than null.

The strict secondary requires crossing the deletion threshold within 30 seconds
after insertion, then user-typed replacement of at least half the deleted
characters within 60 seconds of failure. The replacement begins at the first
deleted position of the failed span; that position follows earlier edits and
advances through contiguous replacement insertions. Counts use Unicode
codepoints and positions use the original UTF-16 coordinates. This does not
require replacement wording to match the deleted AI wording.

Request-rate windows use raw request counts divided by actual elapsed seconds
between the first before-menu opening and the anchor, and between the anchor
and the fifth after-menu resolution. A zero-duration window is missing, never
zero. The acceptance outcome remains the before-minus-after rate over five
canonical menus. Raw drops alone carry no person or trust claim.

The source pilot selects the first 140 canonical session identifiers solely for
timing and explicitly marks scientific support incomplete. Complete extraction
and fresh replay, prior native/pilot charges, the controlled comparison and
learner secondaries all share the original 7,200 CPU-second ceiling. The full
comparison and held-out learner work share that ceiling. No source replay is
represented as a scientific control.

`week3_trust_analysis` implements the complete comparison. Each failure's
matched controls are averaged first. Within each run bin, failure-minus-control
differences are averaged within writer and then equally across writers. The
primary is long minus short. Two thousand real-writer resamples carry both arms
together. If a bootstrap sample lacks a bin, the card reports unsupported cluster
resampling, with its count, rather than silently discarding that sample. Two
hundred within-writer permutations shuffle frozen run-bin labels across matched
failure rows; the matched control remains attached. The reference mean, SD,
interval and descriptive one-sided probability are retained, including the
standing 0.25-SD bias flag. A positive requires a positive lower interval and
probability below .05 with no biased-reference flag. Request rate and the strict
retyping subset use the same explicit comparison as secondaries.

The handling learners freeze a chronological split per writer: the first 75% of
whole sessions train, the last 25% test, requiring at least four sessions. Their
target is accept/edit versus other observed canonical handling. Missing or
censored choices never become zero outcomes. The fixed learner freezes its
Beta(1,1)-smoothed training acceptance rate. The adaptive learner tracks squared
prediction error with a 0.05 update, and uses learning rate
`clip(base + gain * sqrt(variance), .01, .8)`, choosing base in .01/.05/.1 and gain
in .2/.5/1 by training prequential likelihood. This operational learner is an
analyst implementation of adaptive handling, not an identified psychological
process. The exact Bernoulli change-point mixture retains every run length and
selects hazard .01/.025/.05/.1/.2 on training prequential likelihood. Test choices
are scored before updating; no test outcome chooses a parameter. Writer-level
held-out likelihood gains per choice against the fixed reader receive clustered
intervals. No optional session-reset variant is included.

The temperature secondary is a writer-demeaned linear probability regression on
temperature, session position and their interaction. Writer moment matrices
permit exact cluster resampling without changing the fit. Missing settings,
insufficient setting variation and nonestimable resamples are explicit.
Assignment remains unverified, so this is observational throughout.

Six analysis checks pass: matched-regression cancellation, a positive contrast
and reversal, exact prediction-before-update, unpruned change-point histories,
online gains after a known change, no held-out tuning, complete constructed fresh
replay and mutation/admission guards. The source component has five additional
checks. Actual native owner validation and measured source/statistic cost
admission remain separate. A first-tenth source pilot and a separate complete
statistic timing pilot are provided; neither can license a scientific claim.
