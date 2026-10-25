# FR1: writing after repeated dismissal

25 October 2026. Commission: Week 3 packet section 2.4. This is a builder's
implementation freeze, not a finding. The original full 1,399-session population
is retained in the source census; population support is decided before effects.

The source handler `week3_frames_inputs` authenticates the completed PMAP source
chain and original raw/P2/P6/canonical records. A maximal sequence of at least
three canonical dismissals is one frustration event. A maximal single dismissal
is a control; maximal two-dismissal runs are neither. Accept, edit and ignore
break runs. Censored events are retained in the census but cannot provide a
complete observed event. The anchor is the final dismissal's resolution.

Each window contains the next 50 produced typed words, with punctuation tokens
between those words retained. Partial windows are unsupported. The control is
from the same writer and prompt, preferring the same session, then minimizing
the sum of absolute differences in elapsed-session fraction and produced-word
position. Exact ties sort by session and ordinal. Controls may be reused; the
statistical unit remains the writer. Accepted spans crossing 80% deletion use
the same immediate window as an explicitly secondary comparison, authenticated
by WC2's original Unicode-atom replay.

Both arms' window tokens are excluded from the writer profile before any
selection. A seeded random quarter, rounded upward, of the writer's other
sessions with at least 50 produced tokens is held out for planting. Sessions
containing either arm are not calibration sessions. Profiles use the remaining
typed text outside both arms; calibration text never enters profiles. Writers
without 50 training tokens and 50 held-out tokens remain in the full census with
their calibration support absent. The seed is 20261026 with a stable writer
hash. Context contains one nearest-position complete window from each different
writer sharing the prompt, matched separately for the two arms.

The prespecified primary support requires 100 complete matched frustration
events from 25 writers, including independent calibration and context support.
Fewer events produce `unsupported`, not a null. The original event/window/match
census and calibration exclusions are retained separately so an input gap is
visible. No writer or session is selected using an effect.

Source execution checkpoints every complete session; fresh verification
reconstructs every selected session and aggregate independently. The constructed
fixture exercises maximal runs, complete and incomplete windows, profile and
calibration exclusion, separate context matches, exact reentry, fresh process
replay and altered-source rejection. Four targeted source checks pass.

The first owner-ready step is a 140-session cost-only pilot. It retains the full
target population in its configuration and marks support incomplete. Its timing
projects full source extraction and independent replay and excludes all prior
charges and downstream embedding/statistical work. The owner's 3,600-second
parent allowance must cover everything before full dispatch. Source replay is
not a scientific control.

`week3_frames_analysis` now builds the complete comparison. Its style vector is
the completed PMAP roster's 100 frequent words plus punctuation, divided by all
produced word and punctuation tokens. Distance is L1, without data-tuned weights.
This is a frequent-word style measure, not a claimed function-word-only lexicon.
The population context term averages the matched other-writer windows separately
for each arm. Every possible full-profile assignment is evaluated on the same
event and control rows, preserving the context calculation for that profile.

Calibration replaces the first 10 or 20 words of a matched different-writer
neutral window with held-out words from the target writer. The neutral window
always remains 50 words. Both the initial 20% gain and the increment from 20% to
40% must have a positive writer-cluster lower interval. Calibration failure
invalidates the instrument rather than becoming a null. No held-out text enters
the target's training profile.

The primary first averages event differences within each writer, then weights
writers equally. Two hundred whole-profile label permutations, including fixed
points, recompute each writer's contrast on identical rows. Own minus mean fake
uses 2,000 paired real-writer resamples. A separate 200-draw within-writer arm-label
reference sign-swaps paired occurrences. Its mean, SD, interval and one-sided
probability are reported; a mean farther than 0.25 SD from zero flags bias under
the retained outcome-shuffle rule. A positive requires positive primary and
own-minus-fake lower intervals, arm-label probability below .05, passing plant
calibration and no biased reference. Probabilities remain descriptive.

The pause contrast and accepted-then-deleted contrast are secondary. The
embedding secondary uses the already frozen MiniLM CPU float32 encoder, mean
pooling including boundary tokens and the original first-254-token exposure.
Each window's distance to all corresponding dismissed offers is averaged, and
then event minus matched control is computed. Truncation scopes are saved.

The analysis pilot encodes only the first tenth of unique required texts and
measures the complete style/control computation; it issues no scientific state.
Full fresh verification repeats the complete calculation and every embedding.
Unsupported primary source support skips embedding expense and records
unsupported. Five additional checks recover a known effect and reversal, retain
a null, reject a shared effect as a person advantage, validate held-out plants,
and execute a complete fresh constructed replay. Native owner validation and
real-input cost admission remain outstanding.
