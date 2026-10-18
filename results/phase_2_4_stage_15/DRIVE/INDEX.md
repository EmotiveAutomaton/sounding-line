# October 16 drive: execution index

## October 18 implementation wave

The [October 18 mid-run errata](../../../docs/design/stage-15/drive/SOUNDING_LINE_MIDRUN_ERRATA_2026-10-18.md)
is active. [Implemented changes](MIDRUN_20261018.md) and the [selected-option audit](SELECTED_OPTION_AUDIT_20261018.md)
supersede prior retry restrictions and exposed result interpretations below.
Environmental resumes preserve science and original limits; invalid data and code
failures still have one retry. No partial scientific scores are reported.

| Card | Complete state or execution status | Evidence / next action |
|---|---|---|
| PMAP | production source-census failure before extraction; single repair being prepared | [Failure](PMAP-preflight-failed.md); synthetic fixture had passed |
| V5.d | verified complete; primary null, route undetermined, fake control invalid | [Full decomposition and support failure](V5.d.md) |
| V4.c | corrected split authorized; implementation underway | Original V4 labels unchanged; null-world calibration required |
| D33.pair / .fake; D30.v2 / .fake | implementation underway | Same-row comparisons; no new scores |
| D23 | primary marginal; single extension verified null | [Primary](D23.md), [extension](D23-extension.md); reader half awaits P1 |
| D12 | original selected-score primary under source-validity hold | [Original record](D12.md); canonical rank-only variant being built |
| D29 | primary and timer extension verified complete | [Length](D29.md), [timer](D29-timer.md); timer diagnostics invalid, no internal-target admission |
| D14 | primary inference held on selected-vector source defect; restoration admission held | [Audit](SELECTED_OPTION_AUDIT_20261018.md), [original](D14.md) |
| D4 | original inference under selected-label validity hold | [Audit](SELECTED_OPTION_AUDIT_20261018.md), [original](D4.md) |
| D24 | pilot verified; first main failed, single repaired attempt saved at cost yield | [Instrument](D24-pilot.md), [cost hold](WAVE2_CONTINUATION.md) |
| D15 / V3 | both complete: D15 marginal, V3 positive conditional reliability | [D15](D15.md), [V3 table](V3.md) |
| D28 | negative primary verified; reversal extension closed | [Full comparison/control warning](D28.md) |
| D38 | primary source exposed; extension statistic invariant but opening gate held | [Audit](SELECTED_OPTION_AUDIT_20261018.md), [original extension](D38-extension.md) |
| D3 / D3-content | both single engineering retries failed source validation; invalid | [Complete failure record](D3-recovery.md); no further engineering retry |
| D18 | canonical retry verified complete; primary null | [Complete result](D18.md); independent of prepared choice index; P1 fluency gate retained |
| D20 | lossless recovery verified complete; lexical primary positive | [Complete comparison and control limits](D20.md) |
| D11 | verified primary positive; later-text secondary held on source defect | [Complete report](D11.md); writer-slope extension awaits calibrated V4.c |
| D30.p | crossed-model cost pilot verified; full pipeline building | [Instrument](D30.p-pilot.md) |
| D30.r | metadata inspection verified; replication held | [Missing mappings](D30.r-intake.md) |
| TC | positive instrument; verified complete | [Timing census](TC.md); use admitted logged intervals |
| V5 | verified descriptive proxy; V5.d decomposition complete with explicit control deficit | [Original](V5.md); no cross-population headroom denominators |
| P8 | extraction verified complete; backend probability semantics unresolved | [Raw score recovery](P8.md); one engineering retry used |
| P5 | verified complete | [Full sentence/edit ledger](P5.md); reviewed consumers eligible |
| P6 | exact-score recovery verified complete | [Recovery](P6.md); [original diagnosis](P6-failed.md) retained |
| P4 | primary marginal; extension positive, with a similarly positive shuffled control | [Primary](P4.md), [extension](P4-extension.md); no content-specific inference or further extension; V4 taste/habit lens blind |
| P1 suggestion pass | validated environmental continuation prepared, waiting for cold GPU floor | [Mid-run authority](MIDRUN_20261018.md); original failures/checkpoints preserved |
| V4 | verified complete; blind for taste and habit | [Full calibration](V4.md); combined reader rejects all shuffled nulls, oracle sees plants; FX1/personal panels unadmitted |
| D34 | primary and single extension verified complete; both marginal | [Primary](D34.md), [extension](D34-extension.md); one routing null, mechanism unresolved; V4 taste/habit lens blind |
| D30 | primary marginal; verified extension positive, with positive writer-shuffle control | [Primary](D30.md), [extension](D30-extension.md); automaticity not established; [.s](D30.s.md) is verified complete; .p native pilot verified and main building; .r metadata preflight verified with actual mapping gap |
| D30.s | verified complete; positive paired specification median | [Complete texture](D30.s.md); original positive writer-control warning persists |
| D30 daily outcome shuffle | verified complete; marginal, no positive failure flag | [Complete required control](D30-outcome-shuffle.md); D32 outcome shuffle now complete and marginal; other control failures still limit interpretation |
| D35 | verified complete; null | [Complete report](D35.md); no extension or texture |
| D33 | verified complete; primary and writer-shuffle control positive | [Full report](D33.md); personal specificity unestablished; single stronger-baseline extension awaits P7, then texture |
| D6 | verified complete; pooled hover-position primary null | [Complete report](D6.md); no extension; unobserved exposure remains unidentified |
| D2 | original selected-label inference held; extension also awaits V4.c | [Original record](D2.md); diagnostics require canonical choices |
| D17 | environmental continuation verified complete; positive writer stability | [Complete result](D17-complete.md); psychological component identity unestablished |
| D39 | verified complete; null primary and unresolved secondary | [Complete report](D39.md); no decay extension; one A null after the D33 reset |
| D32 | saved execution complete; selected-label inference and routing held | [Audit](SELECTED_OPTION_AUDIT_20261018.md); original results retained |
| D34.v1 | verified complete; marginal, no extension | [Supported subset](D34.v1.md); directly linked model corrections only, broader question OPEN |
| Jester text intake | verified input only; ratings parser pending | [Exact text/source verification](JESTER_TEXT_INTAKE.md); P7 pilot verified; full corpus cost remains unadmitted |
| P7 | full corpus census superseded; scoped D33/Jester CPU execution being built | [Mid-run plan](../../../docs/design/stage-15/drive/BATCH_PLAN_20261018_W2_MIDRUN.md); no full-corpus restart |
| P3/P1 typed+history/new source intakes/Gear 3 routes | implementation remains | No claim of a fully built packet |

**Historical routing snapshot, held pending selected-source correction and current digest:** family resolved-prefix null counts: K 0, B 2, A 2, G 2, E 0, R 1, S 0, P 0.
D15 adds one E routing null, V3 resets it and P4's positive extension keeps E at zero; D37 remains dependency-held.
D33's positive primary resets A after D35; the already-landed D39 null then gives
one; D23's null extension adds the second, with invalid D17 excluded. D33's single extension and required texture remain unfinished. No family stops.
V4 labels: **the lens is blind to taste at every tested size** and **the lens is
blind to habit at every tested size**. Its false-positive gate fails; interpret
writer-level taste/habit nulls and any later family stop as instrument-limited.
These labels do not replace the separate controls on direct process-record cards.
D34 and its variant resolve the first two G entries; shared/instrument passes do not count.
D32's null examination extension resolves its marginal parent as one routing null; D6 then adds a second. D2's extension is the next unresolved B entry.
D2's primary is complete and its single conditional hierarchical extension is saved at its cost boundary. D31 needs verified intake and admitted labels. Additional ranked cards are still being implemented; the packet is not fully built.
The P4 shared fit is marginal; its single extension is complete. A separate
interval-state correction preserves valid percentile intervals that exclude
their point estimate; completed TC/V5/P8/P4 labels are unchanged. Live source
pins stay frozen and later labels receive the same audit before routing.
[Completed 20:00 integration](DIGEST_20261017.md) records theory/TODO work and the explicitly incomplete daily control coverage.
[Operations](OPS_LOG.md) records failures, recoveries and dispatch.
One planned check remains at most one hour ahead; the [six-hour inspection](HEALTH_20261017_1501.json)
records actual identities, progress, resources, delivery and performed recovery.
The dated October 16/earlier October 17 records below retain their original scope.

**Historical execution snapshot before the mid-run amendment:** [the full suggestion pass is invalid after its second
GPU-safety failure](SUGGESTION_MAIN_V5_FAILED.md). Every saved checkpoint
validates, but the one-retry limit forbids another attempt under this packet.
V4 is complete with failed null calibration; D32 and its single examination extension are verified complete; the extension primary is null. D17 is invalid after its second engineering failure; its evidence is retained and its conditional extension is closed. Full reader output remains unavailable;
typed/history preparation and other unbuilt cards remain open. No paid batch.

Recovery history: [fixed memory pilot](READER_PILOT_V6.md),
[paired precision](SMOL_PRECISION_V1.md), [original numerical failure](SUGGESTION_PILOT_V1_FAILED.md),
[checkpoint failure/repair](SUGGESTION_PILOT_V2_FAILED.md),
[valid pilot held by runtime](SUGGESTION_PILOT_V3.md), and
[direct telemetry validation](GPU_TELEMETRY_V1.md). Original evidence is retained.

The packet is partly implemented. Completed work below has a full internal
write-through; registered studies still need executable plans. No unfinished
scientific scores are reported. Earlier Stage 15 queues remain closed.

Content representations, V2 decomposition and the full 150-world Phase 0
calibration are verified complete. Earlier reader resource failures remain in
[their report](READER_PILOT_V4.json); the later memory and throughput recoveries
above provide the currently admitted path. Chess download is verified; bounded
parsing remains unbuilt. Immediate terminal/failure supervision is active.
The [02:45 health inspection](../HEALTH_20261017_0245_PUBLIC.json) is historical;
the [08:53 inspection](../HEALTH_20261017_0853_PUBLIC.json) verifies advancing
checkpoints, native/GPU ownership, evidence and delivery. No recovery required.
[ACK is verified](../HEALTH_20261017_0853_ACK_PUBLIC.json); next health is October 17 14:58:11 PDT.

The original [capacity failure](V1_CAPACITY_V2.json) is fully recorded. The
[lossless recovery completed](V1_PHASE0.json), preserving all 120 complete
checkpoints and fitting the remaining 30 worlds. Native exit and released lease
verify. The reader recovery above is complete; remaining cards still need executable plans.

Paid admission is complete: four cents spent, no active batch. Six constructed
features pass; tone, contradiction and themes remain disabled. G3-A/B/D/F are
not built. The first-$10 guard remains; more than $10 needs the packet's detailed
final approval. The conditional slight overrun has no automatic numeric allowance.

The shared-pass table reports execution readiness, not scientific admission.

| Shared pass | State |
|---|---|
| P2 | verified complete |
| S0-T1 | delivered aggregate |
| S0-T4 | delivered aggregate |
| S0-T4-104 | held released exclusion roster |
| V2 | verified complete |
| P1 | pilot verified; full suggestion pass invalid after its permitted retry; typed/history unbuilt |
| P3 | blind reference and classifier not built |
| P4 | full fit and single extension verified; specificity not established |
| S0-T2 | download verified parsing not built |
| S0-T3 | delivered source identity review required |

Completed [decomposition](V2.md) and [content features](CONTENT_V2.json).
Completed evidence: [P2 replay](P2.md), [paid admission](G3-A0.md), [S0 references](S0.md).
Apparatus failures and separate repairs: [reader pilot](P1.md), [content encoder](CONTENT.md).

Each row below identifies a commissioned study in priority order and whether its
runner exists. Dependencies are necessary inputs, not evidence of admission.

| Rank | Card and question | Status | Dependencies |
|---:|---|---|---|
| 1 | D21: Reader/context convergence | registered not built | P1 |
| 2 | D22: Editing hierarchy | registered not built | P2, P3, D14 |
| 3 | V1: Target-specific planted recovery | Phase 0 verified complete; other arms not built | none for implemented arm |
| 4 | D27: What the page retains | registered not built | P1, P2 |
| 5 | D6: Position and exposure | registered not built | P2 |
| 6 | D16: Writer verification from process | registered not built | P2, D17, D15, V3 |
| 7 | D23: Exploration across experience | non-reader primary verified marginal; extension eligible | [D23](D23.md); reader half awaits P1 |
| 8 | D14: Protected variables and restoration | registered not built | P2, P3 |
| 9 | D12: Model-probability departures | logged-score primary verified null; conditional extension closed | [D12](D12.md) |
| 10 | D29: Stopping and thresholds | registered not built | P2 |
| 11 | D13: Surprisal and decision effort | registered not built | P1, P2 |
| 12 | D24: Closure around task threshold | registered not built | P2 |
| 13 | D20: Dismissed text influence | registered not built | P2 |
| 14 | D28: Near ties and later reversal | registered not built | P1, P2 |
| 15 | D2: Contextual taste | registered not built | P1, P4 |
| 16 | D18: Deletion and sacrifice | registered not built | P1, P2 |
| 17 | D15: Writer/prompt variance | registered not built | P2 |
| 18 | V3: Per-feature reliability | registered not built | D15 |
| 19 | D11: Prior own-text fit | registered not built | P1, P2 |
| 20 | D1: Free and literal predictive gain | registered not built | P4, G3-A |
| 21 | D4: Correction intent | registered not built | P2, P3 |
| 22 | D3: Reversal and survival | registered not built | P2 |
| 23 | D17: Pause and burst structure | registered not built | P2 |
| 24 | D5: Final versus own-text identity | registered not built | P2 |
| 25 | D8: Wikipedia editor intent | registered not built | S0-T3, P3 |
| 26 | D7: Dwell decomposition | registered not built | P2 |
| 27 | D9: Rater learning curves | registered not built | D10 |
| 28 | D23b: Chess exploration | registered not built | S0-T2 |
| 29 | D24b: Wikipedia promotion trajectories | registered not built | S0-T3 |
| 30 | D19: Factorized process/content recipes | registered not built | P1, P2 |
| 31 | D10: Embedding panels | registered not built | S0-T4 |

Next engineering work: complete/verify the active suggestion pass; implement separate
reader-pass typed/context/history packing;
P4/D1 fitting under [recipient-specific chronology](../../../docs/design/stage-15/drive/P4_CHRONOLOGY.md);
blind native edit references; bounded chess parsing and Wikipedia text pairs;
then concrete gated paid routes. The earlier failed Ghost profile witness still
blocks that separate engine comparison; descriptive work does not bypass it.

Consumer coverage is complete for the audited selection path: D2 training/calibration/test and D12 primary labels are exposed; D6 selection-derived sensitivities are held while its direct-hover primary remains. P8, P4 and D28 are invariant to this defect. [Exact aggregate audit](SELECTED_OPTION_AUDIT_20261018.md).
