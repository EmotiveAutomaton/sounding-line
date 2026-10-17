# TC: timing census

**Question.** Are these writing logs fine enough to support the commissioned pause tests?
**METHOD.** Recount every authenticated user insertion and consecutive text-delta interval in all 1,399 sessions from 61 writers; apply the frozen character-share and clock-resolution bands. Replay the saved census in a fresh process and verify every bound input/output hash.

**Found.** Single-character insertions account for 99.23% of typed characters; the minimum positive recorded interval is 1 millisecond. The fixed rule admits per-character logged timing. Zero intervals account for 0.020% of delta intervals. State: **positive instrument**.

**Route.** Timing cards can use the frozen logged-interval convention. These are browser text-delta timestamps, not measurements of physical keystrokes or direct observations of attention. Coalesced insertion, input method and machine timing remain possible sources of error. No theoretical attention claim follows from instrument admission.

[Aggregate census and verified bindings](TC.json). This is a complete descriptive instrument pass; theory/TODO integration follows the packet's 20:00 digest.
