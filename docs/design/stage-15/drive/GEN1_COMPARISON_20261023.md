# GEN1: matched genre identification and controls

The [week commission](WEEK_PACKET_20261018.md) asks whether a writer is easier
to identify from creative writing than argumentative writing. This implements
that existing question after the completed matched-input preparation. No new
campaign, family count, model call or paid compute is commissioned.

## Frozen inputs and measurement

Authenticate the completed GEN1 matching manifest, original PMAP dictionary,
PMAP sessions, original production-word ledger, and completed revision character
identities. Reconstruct every unrestricted raw bigram count and interval and
require exact equality with completed PMAP before retaining matched atoms.
Original source bytes and completed attempts remain unchanged.

Style pools word and punctuation counts over the exact retained token prefix,
with the original full-PMAP dictionary and denominator. Within-word and word-onset
timing use only retained occurrences. A raw event cutoff alone is insufficient.
Under S5, bigrams require both endpoints to be retained token atoms or whitespace
connected to those atoms through whitespace-only adjacency. The adjacency must
have been observed at insertion by the latest retained completion event. This
retains separators without importing another word from the same event, inventing
adjacency after deletion, or substituting full-session aggregates. Uncompleted
fragments and unretained occurrences do not supply matched bigrams. This explicit
matched-exposure definition is narrower than unrestricted session rhythm;
report source/retained pair counts. Timing remains logged deltas, not keypresses.

Use the already frozen prompt halves, separately by genre in the primary mode.
The fallback retains its mixed-genre split and exploratory label. Within each
channel freeze the common writer roster supported in both halves of both genres
before scoring. Report all dropped writers. Missing cells are not zeroes.
Pool session counts for style and timing observations for medians; never average
session averages. Nearest-neighbour distance, B-only scaling and partial-feature
imputation, constant-feature removal and fractional ties inherit PMAP exactly.

## Controls and inference

- Primary: creative minus argumentative style identification, expected positive.
  Rhythm is secondary. Fixed B galleries remain intact during 2,000 paired
  real-probe-writer bootstrap draws, seed 20261018.
- Within-writer reference: 200 independent fair genre exchanges of each matched
  session pair, preserving the paired word quotas and writer/genre session counts.
  Reconstruct prompt halves and profiles for each exchange.
- Same-row fake-writer reference: 200 session reassignments within each genre,
  preserving label counts, using seed 20261019. Reconstruct prompt halves and
  profiles, then pair each real writer's contrast with its mean fake contrast in
  a 2,000-draw real-writer bootstrap. Also retain each genre's own-minus-fake and
  chance-centered fake reference. This is an assignment control, not new data.
- Never redraw a failed-support reference or shrink its frozen gallery. Any
  incomplete bank disables that reference probability and the positive claim.
  Report the failed count. Flag a reference mean exceeding one quarter of its
  standard deviation; a constant nonzero reference is biased.
- A positive claim requires the primary interval above zero, complete reference
  banks, centered within-writer and fake references (including genre-level
  chance-centered checks), a positive real-minus-fake contrast, and original
  primary population support. Unresolved, negative and control-invalid outcomes
  do not justify genre weighting. Actual weighting still requires Ghost N18.
  All probabilities are descriptive; no family counter changes.

## Validation, execution and accounting

Known answers cover signed/reversed/zero effects, chance ties, missing timing,
fixed support, row and count preservation, Unicode, repeated/deleted occurrences,
within-event cutoffs, complete source reconstruction and changed saved results.
Run both handlers through the counted contained native runtime, with fresh-process
reconstruction, before corpus dispatch. Validate the complete control bank, not
just an isolated statistic. Every source and executable is pinned in each plan.

Prior GEN1 charges are 279.617759 wall seconds. Reserve another 150 seconds for
the new validation and native rehearsals, conservatively retained even if actual
cost is smaller. The original conservative ceiling is 1,800 wall seconds for one
CPU-hour; all feature execution and replay, statistical execution and replay,
failures and earlier preparation count. S4 permits one cumulative doubling only.
Feature execution/replay initially receives at most 900 seconds, with no scientific
contrast in that component. The comparison is separately admitted from its actual
remaining allowance and measured native timing. Both have hard supervisor caps.

Immediate completion/failure/disappearance monitoring and the independent
six-hour health check remain active. Full internal write-through precedes ACK;
the scheduled final packet retains its reporting policy. No unfinished scores.
