# FIC1 exact prefix preparation

This is preparation for the commissioned 500, 1,000, 2,000 and full-word length
curve. It computes no identification score. The original 24 writers, 990 selected
sessions and 96 genre/prompt-half profiles remain fixed. LESSONS sections 3–5
were reread for the FIC1 implementation; the original 7,200 CPU-second total
includes this component, validation, earlier preparation and later statistics.

Profiles use their already frozen session chronology, then the production-word
ledger's completion order. A budget takes whole sessions until the boundary,
then precisely the required completed words from the last session. Complete
session features are retained unchanged. The partial-session selector is the
original GEN1 occurrence-bound implementation: token atoms and connected
whitespace through the last retained completion, excluding unselected words
even when inserted in the same delta. Later-deleted production remains. Prefix
rates and medians are pooled from counts and intervals, not averaged session
rates or medians. The original full-corpus PMAP dictionary remains transductive.

Every session's complete word ledger, token/character identities and typed-pair
records are saved for later controls to regroup and reconstruct prefixes. Typed
atoms are stored as a JSON-stable list, preserving integer indexing. A future
shuffle must rebuild its prefix allocation and features; these observed-profile
features cannot simply be reassigned as if word-budget selection were fixed.

Source seals, raw/canonical pins, exact PMAP pair replay, original FIC1 membership
and complete-session feature parity are mandatory under null and alternative.
Missing, altered or crossed sources refuse the instrument. Profiles shorter
than a requested budget stay explicitly unsupported; no padding, duplication,
new writers or silent exclusion. No accuracy or length-trend gate runs here.

Constructed checks cover cross-session boundaries, unselected same-delta words,
Unicode, later deletions, absent timing, chronology, exact quotas, source/output
corruption, saved-file reentry and full independent native replay. A measured
corpus sizing pass precedes the complete occurrence replay when needed. Shared
progress uses atomic unique-temp replacement with bounded sharing retries.

After full preparation, statistical implementation still needs the original
paired genre table, length adjustment, all packet controls, the approved
independent-donor correction, known-answer admission and measured total cost.
AUTH's primary remains separately calibrated and subject to ordered concrete
transfer/spending admission. No scientific gate is changed by this component.
