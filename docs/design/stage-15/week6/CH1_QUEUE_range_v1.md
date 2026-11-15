# Original-roster chess scoring: disjoint range adapter

Prepared November 15, 2026 under Week 5 two-day amendment V and Week 6 §5.
This is an additive engineering candidate. It grants no production admission,
changes no scientific source or setting, and does not supersede a live worker.

## DESIGN CHECK

Read LESSONS §§3–5 and the original `../week5/CH_BACK_HALF_QUEUE.md`.
Under a null or an alternative, each original ordinal must receive the same
unchanged scorer, one separate native execution and one separate native replay.
The valid operational band is a complete contiguous nonempty interval; gaps,
overlap, changed source/node pins, an unsealed predecessor, a live/unknown native
owner, and changed retained bytes refuse. A stopped process is not a scientific
completion. A constructed fixture's expected ordinals are stated independently
of the adapter, and mocked process records never establish native qualification.

## Existing limitation and additive change

The committed `week5_ch_queue_backhalf_v1` accepts a starting offset but no
end-exclusive bound. Its `while next_offset < expected_positions` can reach the
end of the entire roster. The committed `week5_ch_queue_manifest_v1` accepts only
that module's completed counted queues. Neither supports concurrent disjoint
range admission today. The existing worker must continue serially until a
reviewed transition is possible; new shard code does not change its loaded code.

`week5_ch_queue_range_v1` is an isolated version of that queue. Its native worker,
bounded scorer, original scorer, two single-thread Stockfish processes, 64 MiB
hash per engine, node setting, unit seals and distinct native replay are unchanged.
The added manifest fixes each shard's half-open interval `[begin,end)` and its
pause rank. Buffers and complete-unit dispatch stop at that end. All shards
retain the original global denominator and original source hash; final replay
also traverses the unscored tail to check the complete denominator. No rows are
resampled, sorted anew, or omitted from the requested remainder.

The pilot marker is five percent of the shard's frozen range, not a CPU fraction.
At the queue wall boundary it yields with a checkpoint instead of calling a
partial range complete. A counted, fully authenticated new-attempt copy resumes
the same frozen range. Owner-yield and resource interruptions retain active unit
evidence and all cost; a range completes only at its exact end with no active
unit and every closed native unit authenticated. A completed shard still has
`population_complete:false`.

`week5_ch_manifest_range_v1` validates one to five contiguous ranges covering
the exact remaining interval. Its default partition balances 64-position units,
with the final partial unit in the final range. Two numerical threads per shard,
one shared lease and one outer all-descendant CPU charge per attempt remain.
Nested execute/replay cost is diagnostic and must not be added a second time.
The helper returns reverse pause order but never signals or launches a process.

## Handover gates and owner procedure

1. Keep the current original-roster worker untouched while preparing and testing.
   Do not derive an admitted start ordinal from a live progress snapshot.
2. After qualification, arrange an ordinary authenticated clean checkpoint/exit
   under the existing owner/runtime procedure. A `PAUSED` filename is insufficient:
   `QUEUE_STATE.active` must be null, all state units must be sealed and authenticated,
   and the final state's `next_offset` fixes the new range start. If an existing
   owner request interrupts an unclosed unit, retain it and continue serially;
   this version does not discard or relabel that unit to force a handover.
   A practical owner-reviewed route is a short **original-module** continuation
   from that pause with `max_new_draws:1`. The original checkpoint binding
   explicitly excludes this operational quantum. It finishes the whole retained
   active unit and its fresh replay, then yields at the next closed-unit check
   with `active:null`. It does not restrict the unit to one position. This route
   must pass its constructed logic case and an actual counted resume/runtime
   rehearsal before use; its output copy and all costs remain authenticated.
3. Authenticate actual native owner and execute/verify identities and contained
   descendant exits; reconcile lease release by exact holder identity. Preserve
   original PLAN, source pins, terminal, complete checkpoint inventory, original
   failed/paused directories and all charges. A missing/unknown identity holds.
4. File an immutable `CLEAN_PREDECESSOR_RETIRED` handover with exact hashes, current
   terminal and state binding, full sealed-unit audit, and historical prefix
   inventory. Include the failed original queue's accepted sealed prefix without
   converting its failure into COMPLETE. The range validator checks the pinned
   receipt and terminal/native metadata; the owner's complete checkpoint and
   historical-prefix audit is a separate required evidence operation.
5. Freeze the source, engine, original denominator, original node count, seven
   required implementation pins and all ranges in one immutable manifest.
   Commit reviewed source/design first; then owner-review the exact manifest and
   each counted plan, current cumulative budgets, projected peaks and output cap.
   Fresh range attempts are not resumes of the old different adapter.
6. Admit at most five shards, subject to the eight shared slots, at most six filler
   slots, two short-card slots, campaign clocks and current resource headroom.
   Week 6 production additionally waits for actual Week 5 drain reconciliation.
7. If commit headroom nears the floor, owner supervision requests pauses in
   descending pause rank, waiting for authenticated exit/released lease before
   deciding whether another shard must pause. The same hard guards remain active
   independently. Do not claim automated reverse-order management: this delivery
   supplies a deterministic recommendation, not a running coordinator.

The final collector remains held until a separately reviewed assembler can
authenticate the union of all original completed intervals, retained failed and
paused sealed prefixes, and new complete ranges exactly once. This delivery
does not broaden the original manifest's COMPLETE-only rule, manufacture old
completion markers, or license analysis from a partial population.

## Constructed qualification and costs

The source-free focused test uses an 11-row literal ordinal world. The sealed
prefix is `[0,2)`; three ranges are `[2,5)`, `[5,8)`, `[8,11)`. The independent
expected engine call multiset is `2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10`.
It checks exact shard ends including short final units, execute pause/resume,
final-verifier pause/resume, immutable predecessor bytes, changed source and
score refusals, complete denominator mismatches beyond the local shard, manifest
gaps/overlap/duplicate IDs, changed node/range settings, and production refusal
without real handover evidence. Mocked native receipts prove protocol only.
Direct handover cases also exercise clean acceptance, a live/unknown original
native owner, wrong terminal status/hash, missing native evidence, wrong cursor,
and omitted prior-cost audit. A retained active original unit is replayed and
sealed under the one-unit operational quantum in a separate constructed case.

Exact command (one owner-counted serial test token required):

```
.venv/Scripts/python.exe -X utf8 -B -m pytest -q tests/test_week5_ch_queue_range_v1.py --basetemp=.agent-state/drive-20261115/full-run-build/chess/pytest_range_v1
```

Conservative proposed focused allowance: 60 CPU seconds, 180 wall seconds,
0.5 GiB RAM. No human source, native scoring, GPU or external call.

Native qualification uses the existing eight constructed legal-board inputs,
including the single-legal-move and unique-mate controls, fixed at 1,000,000 nodes.
Two frozen ranges `[0,4)` and `[4,8)` run one at a time through the owner-counted
runtime. Range 1 uses an execute pause after two positions, a copied final-verifier
pause after two, then a copied complete attempt. Range 2 completes independently.
Require exact known answers, separate native execute/replay identities per unit,
unchanged predecessor bytes, exact disjoint coverage, all Jobs exited, leases
released, and outer CPU at least nested unique CPU. Existing original eight-board
qualification remains evidence for unchanged scorers, not for new range control.
Two preceding original-module attempts also test an active-unit pause and a
real copied one-unit continuation to a clean boundary. Proposed ceiling: six
attempts of 300 CPU seconds and 1,200 wall seconds each;
actual measured costs replace forecasts and remain in CH/campaign accounting.
Do not run this candidate until the focused checks pass and owner review admits it.

Prepared, tested, native-qualified, committed, admitted and running are distinct
states. At preparation no tests or native jobs have run for this version.
