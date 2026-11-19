# CH14: authenticated recovery after the attempt wall limit

The original V3 move-recency calculation reached its four-hour attempt wall
limit during execution. Its last atomic checkpoint contains 1,800 of the frozen
2,000 whole-player draws. The progress-only count of 1,809 grants no additional
checkpoint credit. The original failed attempt and every charge remain intact.

This is cost recovery of the same card, not an engineering repair of its model.
The [V3 design](CH13_CH14_RIDERS_V3.md), original source population, chronology,
comparators, seed, draw bank, fitting routines and independent formula replay
are unchanged. No reduced population, selected draw or new scientific test is
introduced. The original 40,000 CPU-second card ceiling and family/campaign
limits continue to include the failed attempt and this recovery qualification.

## DESIGN CHECK

Read: `docs/method/LESSONS.md` sections 3 through 5. Under both null and
alternative worlds, transport must preserve the exact saved draws and continue
the same seeded bank. An intact execute-only wall failure with exited native
identities may recover; changed inputs, configuration, code pins, receipts,
outputs, draw count, native ownership or destination must refuse. Full fresh
independent replay, rather than the copied checkpoint, determines verification.
No partial scientific estimates are inspected to choose a recovery route.

The separate wrapper checks a frozen manifest against the original plan,
failure, owner, child and job-accounting records. It accepts only the exact
execute-wall failure, with complete accounting and no replay or competing
terminal. It retains all predecessor source/code pins and confirms native exit.
Inside the counted child, it copies only the authenticated checkpoint and pilot
bytes into a fresh output directory and writes an explicit cost-recovery origin.
It never fabricates a PAUSED record. The existing PAUSED-only resumer remains
unchanged; later genuine pauses preserve their newer checkpoint through it.

The successor uses an eight-hour attempt wall bound and at most the remaining
card CPU allowance, with two numerical threads and unchanged shared-slot,
memory, disk and campaign-drain guards. The old four-hour bound was insufficient
for execution alone. Reference replay cost has not been measured on the whole
source; this longer wall bound does not promise completion within the CPU cap.
Any further cost route requires its own prospective accounting under the standing
rules; no automatic doubling is exercised by this recovery.

Qualification retains the original sixty constructed chess cases and adds exact
recovery, tamper refusal, seeded-prefix equivalence, later-pause continuation and
full independent replay checks. It runs in one counted CPU-only slot, bounded at
600 CPU seconds and 1,200 wall seconds, charged once to CH14. No participant
source is read by that qualification. Production requires its complete receipt,
the committed design and fresh ordinary admission.

The prior first-checkpoint report's statement that every wall boundary pauses
normally is corrected by the recovery record: a cooperative yield writes PAUSED;
the hard attempt wall writes FAILED and preserves only the last atomic checkpoint.
The earlier report and pinned receipts remain available as historical evidence.
