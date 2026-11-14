# CH9: a quick return after losing on time while ahead

Prepared November 13, 2026, unadmitted, under the two-day packet. Uses only the
complete SG1 table and the already approved forecast split. No engine or new
source scan. A public game rating is not standing in a room.

## DESIGN CHECK

The four packet losses must classify exactly: time forfeit at material +2 is
FLAGGED-AHEAD; Normal at -3 is OUTPLAYED; time forfeit while behind and Normal
at balance zero are excluded. A checkmating final move independently qualifies
OUTPLAYED. Tournament and provisional-session exclusions precede classification.
Other records are counted, never mapped to an implicit control category.

QUICK uses `seconds_to_next - duration_est`, requiring an observed uncensored
next game and a finite nonnegative duration. Gaps from zero through 120 seconds
qualify; negative estimated gaps are missing because an overlapping estimate
does not establish a quick subsequent start. The 120-second boundary, missing
duration and censored tail all have literal constructed answers. The inherited
duration is explicitly an estimate excluding two unobserved first-move latencies.

The one primary is FLAGGED-AHEAD minus OUTPLAYED in a player-fixed-effect linear
probability model of QUICK, with E, games so far, prior surprise form, losing
streak, sine/cosine hour and tournament flag (constant after exclusion). All
eligible control classes remain, since the packet names no class exclusion;
class composition counts remain visible. Missing E/form excludes a regression
row but not the classification/denominator census. Bar is 0.03. A mechanically
constructed multi-player case checks the actual sufficient-statistic and
independent formula path, alongside the literal classification fixture.

Secondaries retain the packet's exact scope: among QUICK next games, the
source-defined rematch share for each kind of loss; the same shares after
clear-favourite losses; adjusted STOP contrasts for all eligible kinds and for
clear-favourite losses. STOP does not require a supported duration, so its
denominator is separately reported. REMATCH/STOP retain SG1's start-gap session
rule; a long game can produce an apparent session break even when the next
start is soon after its estimated end. This is a stated source limitation.

All 2,000 draws resample complete players with the fixed packet seed. They
recompute every registered model/share. One-person and constant-outcome models,
homogeneous binary shares, and undefined target contrasts retain diagnostics
without population intervals. Targets are tested conditional on retained
controls. No nuisance collinear with the target is dropped to rescue it.
Independent replay recomputes all table-derived classifications and formulas,
using the separate raw-sum fixed-effect identity and least-squares solver.

Setup streams one player's history at a time and stores only sufficient
statistics and small per-player counts. The first candidate completes setup
then stops at 100/2,000 draws; it is not a 5%-CPU claim. Resume requires an
authenticated complete new-attempt copy; verification starts fresh. Actual
setup/fit/memory and whole-card cost remain owner gates. The ceiling is 40,000
CPU seconds inside the existing CH family. Native scientific admission and
all complete replay/native exit/lease receipts remain pending.

The card remains descriptive: playing well, prior state, game duration and
clock state differ between the two kinds of loss. A rematch also requires the
other player's consent. Activation records RAGE versus SHAME as the packet's
behavioral analogy, not evidence that either emotional channel was measured.
