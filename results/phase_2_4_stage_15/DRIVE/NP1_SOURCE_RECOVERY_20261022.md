# NP1: completed probe-like event census and source recovery

**Hypothesis.** Recorded corrections, rejection runs and returns to a prompt may
be frequent enough to support future probe-oriented reading.
**METHOD.** Count the three frozen event categories over every authenticated
session, retaining zero-event sessions. Reconstruct the original D39 correction
ledger from raw logs wherever its originating menu is absent from the reduced
menu table; separately verify the complete census in a fresh native process.
**Found.** The full census is verified complete and reaches the packet's common-event
planning threshold. **Means.** Observed events are available for future scoped
reading; frequency alone does not identify deliberate probing or private goals.

All 1,399 sessions and 61 writers are retained. The table gives each category's
total, pooled events per session, and the mean of writers' own per-session rates.
Categories can occur together and writers contribute unequal session counts.

| Recorded event | Total | Pooled rate | Mean writer rate |
|---|---:|---:|---:|
| Accepted model span with at least 80% of original codepoints deleted | 429 | 0.306648 | 0.213936 |
| Maximal run of at least three dismissals | 292 | 0.208721 | 0.209247 |
| Session after that writer's first on the same prompt | 792 | 0.566119 | 0.269971 |
| Sum of categories | 1,513 | 1.081487 | 0.693154 |

There are 983 sessions with at least one counted event. The fixed routing rule
uses the pooled summed rate: below one is rare, one or more is common. The
different equal-writer rate illustrates the weighting dependence; it does not
replace the frozen rule. No uncertainty interval or inferential probability was
commissioned for this descriptive census. D38's later five-menu support filter
belongs to its gradient and is not used here. Blank original spans and own-text
corrections do not enter the accepted-model category.

## Preserved failure and one repair

The original attempt stopped before producing a census at 07:04:42 PDT. Four
authenticated model corrections lacked an originating prepared-menu row. The
first source check incorrectly required that reduced table to contain every
acceptance already recorded by the raw D39 extractor. This is an engineering
failure, not a negative finding about probing.

The separately named recovery uses original source-roster and timeline pins.
All four affected session ledgers reproduce exactly from the original event
logs. No session, correction or menu row was dropped or invented. Existing
contradictory menu handling still refuses. Original sources, thresholds and
failed output remain unchanged. The [repair contract](../../../docs/design/stage-15/drive/NP1_SOURCE_RECOVERY_20261022.md)
describes the source proof and the single retry limit.

Nineteen targeted checks pass, including unchanged original checks and source
tampering, duplicates, Unicode, wrong handling and saved-output corruption.
The first test invocation had nine fixture setup errors because mutation tests
used the production exclusive writer; only the fixture writer was corrected.
That first report is retained. Complete native constructed execution and
fresh-process verification pass. The corpus retry then completed at 07:23:48 PDT;
all output and source pins verify, all owners/children exited and leases released.

The retry used 10.913776 wall seconds. A conservative 300-second prior charge
covers preparation, the failed attempt, diagnostics and validation, bringing
accounted time to 310.913776 seconds against the original 1,800-wall-second
two-thread conversion of one CPU-hour. Its combined run/replay cap was 600
seconds. There is no cost reset or S4 doubling.

The [aggregate receipt](NP1_SOURCE_RECOVERY_20261022.json) binds the original
failure, tests, native validation, recovered completion and source hashes.
Participant identifiers, raw text and individual proof rows remain private.
No new p-value, null-family count or scientific admission is introduced.
Instrument ledger, method lesson, FINDINGS and queue records are updated.
No tests harvested from this operational wake. Theory interpretation remains
unchanged; daily integration retains the evidence and limitations.
