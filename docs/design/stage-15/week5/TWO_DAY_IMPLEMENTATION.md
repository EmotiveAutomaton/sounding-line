# Two-day packet implementation

The curator authorized implementation on November 13, 2026, requested completion
as quickly as practical, and retained CPU-only Gear 2. The supplied packet is
preserved byte for byte as `PACKET_TWO_DAY.md`, SHA-256
`6b9b14b2ab7f40cce359619bafadf32783036708e0f1dd7b8d16a385d98c6412`.
The original parent-workspace file remains intact. This is an implementation
record, not a scientific result or a revision of the theory files.

## Approved correction before outcomes

The retained history sampler selects a two-percent prefix of the existing salted
player hash: `int(player[:16], 16) < 0.02 * 2**64`. Every selected key therefore
starts with hex 0. The packet's literal forecast split, putting keys starting
with 0, 1 or 2 into calibration, would leave no analysis players.

Asked whether to preserve the sample and use a separate fixed hash, the curator
answered: "Use a separate fixed hash (recommended)". Calibration membership is
now fixed by the first hexadecimal digit of
`SHA256("SG1-forecast|20261112|" + existing_salted_player_key)`: 0, 1 or 2 for
calibration, all others for analysis. This changes no source selection or player
identity. The split is frozen before the forecast or any CH8–CH12 effect is fit.
Source: `week5_ch_source.selected_history`; the original packet remains unchanged.

Two further source/design questions were resolved before outcomes. For CH10,
controlling separately for zero, one and two-or-more consecutive wins already
encodes the preceding win/loss, making its separate contrast unidentified. Asked
whether to control for the two-or-more-win bonus instead, the curator answered:
"Use the 2+ win bonus control (recommended)". The primary uses that indicator;
the original categorical specification remains recorded as unable to identify
the requested contrast. Unknown left-edge histories are not invented.

For IN11, the blank source questionnaire offers seconds, minutes, hours, days
and weeks, not measured elapsed time. Asked about fixed ordered ranks and
standardizing both intensity and duration before comparison, the curator answered:
"Use declared ordinal duration (recommended)". The ranks are respectively 1–5;
both outcomes are standardized within prompt. The event-duration control uses
the same declared ordering. "I had none" remains a separately counted exclusion
from the ordered-duration primary. Results concern reported duration categories,
with no invented conversion to seconds.

The owner's prospective RF1 index definition preserves the packet's three-read
versus two-read comparison: each signed marker rate is the number of comments
with a positive marker minus those with a negative marker, divided by early
comments. A paired read is the sum of its named rates. All six polarity counts,
denominators and within-comment overlaps remain separate in the source table.
The earlier six-coefficient draft is retained as a provisional descriptive
sensitivity, not the primary. Election identity and instrument gates still apply.

## Admission and review

Three builder queues are explicitly commissioned by packet section 4. A prepares
SG1 and CH8–CH12; B prepares RF1/CP1 intake, fixed markers and instrument checks;
C prepares IN9, IN11, IN12, LA5, RR3 and EX5. The owner reviews, admits, launches
and files results. Numerical development checks run serially while research jobs
continue. Builder completion is not scientific admission.

Review order is LA3/LA4; SG1 with CH6/CH7; CH8/CH12; IN9 items then cues; TR1/RR3;
CH9/CH10 after its instrument gate/CH11; LA5; IN11/IN12; RF1/CP1; EX5/EX4 and the
conditional ISEAR block. The original card and family ceilings and campaign clock
remain, with the packet's four added family ceilings pending safe runtime loading.
Table-card replay implements the formula independently on the verified input;
no redundant source qualification campaign is added.

The existing scoring queue accepts a start offset but consumes through the full
roster and rejects trailing rows. Its current committed manifest owns the whole
roster and provides no disjoint end boundary. Amendment V therefore retains serial
scoring under its explicit fallback. Overlapping jobs are not admissible. Scoring
does not take review priority from the packet's history-table studies.

## Preserved boundaries and unresolved dependencies

- The packet's Round 13–15 handoff files and theory-thread text were not present
  in the checked local handoff locations. Implementation uses its explicit formulas
  and attribution; no independent review of those absent sources is claimed.
- LA3's combined-corpus chronology remains held where ICSI ordering is undocumented.
  AMI-only repetition and LA4's language primary have independent routes. The first
  real metadata extension exposed AMI's `HHhMM` clock syntax; a separate source-v2
  repair also accepts `HH:MM` with strict numeric bounds. Original source and failed
  attempt are preserved; full evidence and charge are filed in the operational record.
- SG1 must compute opponent clocks, final board and mate during the raw traversal;
  the old player-only move payload cannot reconstruct them afterward.
- RF1 must establish election boundaries rather than assume candidate/year is an
  election. SNAP's linked software licence is not treated as a dataset-text licence.
  These qualifications remain explicit while local intake and marker preparation proceed.
- R7 authorizes only the duration and specified personality columns. Demographics
  remain unloaded. ISEAR still requires the local source and curator terms note.
- New family policy must be loaded through a reviewed transition that preserves
  active pinned code and all historical charges. A filed budget is not proof of
  runtime support.

The isolated [v11 continuation runtime](TWO_DAY_RUNTIME_V11.md) passes its scoped
language continuation and native-copy checks. The existing language families
can use it alongside the original chess worker. New-family registration remains
closed pending legacy-reader reconciliation and an unresolved historical native
identity inspection; passing unit checks alone does not release that hold.

All new result rows carry an activation list. Operational-only rows use an empty
list because they do not observe a channel firing. The retrospective activation
table is an evidence annotation pass, not a new analysis or automatic theory verdict.
The rolling theory return adds the packet's Round 15 map; pending means uncomputed.
Scientific scores remain internal until the final-packet reporting boundary.
