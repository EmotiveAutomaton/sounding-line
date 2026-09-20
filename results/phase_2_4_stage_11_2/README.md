# Stage 11.2 results

Latest inspection: worker failure and resource stop, September 20, 14:20 UTC

The original worker timed out and exited after the coordinator failure. Saved
calls replay offline, the GPU lock is released, and Ollama subsequently reports
no loaded model. The neural comparison is incomplete; all later jobs are unstarted.
Gear 2 remains authorized, but no whole block fits the original deadline at current
measured rates, including the faster scenario. All failures and uncertainty charges
remain. No restart uses the frozen dispatcher's stale admission-only forecast.
Watcher delivery and final-checkpoint helper verify; only the exited worker watch
is retired. Final reporting remains due at 15:00 UTC / 08:00 PDT, with missing
coverage and unavailable case roles explicit. See WORKER_TIMEOUT.json in Stage 11.2.
Earlier dated snapshots below describe the state at their own inspection times.

Historical coordinator inspection follows.

Latest allocation: Gear 2, explicitly resumed September 20. The coordinator's
six-hour wait has now failed; its original M0 worker survives and advances under
the unchanged deadline and budget guards. The secondary monitoring error is
repaired; see [timeout reconciliation](COORDINATOR_TIMEOUT.json). No replacement
dispatcher is launched while this worker survives. Earlier recovery is in
GEAR2_RESUME.json; recovery lineage stays in ignored raw/recovery/. Completed
calls, original uncertain charge, scientific code and original deadline remain.
Earlier Gear 1 statements below describe the retained historical handoff.

Gear 1 resumed after restart: original checkpoint and watcher helpers are active.
See GEAR1_RESUME.json; RESTART_HANDOFF.json preserves the completed halt.

Operative study: docs/design/PHASE_2_4_STAGE_11_2_CONTEXT.md, filed unchanged.
Historical Gear 1: sustained GPU queue paused by the owner; local model unloaded.
Light CPU work is limited to two threads. Original 18-hour service ceiling and
Sunday 15:00 UTC deadline remain. See GEAR1_HANDOFF.json for retained progress
and the interrupted-call reconciliation required before a future authorized resume.
Raw inputs, activations, outputs and calls remain in ignored raw/.
Only complete comparisons are interpreted; all failures and costs are retained.
L409-L410 are the exact development/test and candidate-revision comparisons.
The repaired separate 9B reader is admitted; HF activation conditions remain refused.
See BRANCHES.md for scope and explicit unavailable conditions, and LIVE_QUEUE_VALIDITY.json.

Final REPORT.md, final branch dispositions, machine comparisons, integrity receipt
and six inspectable cases remain due at the Sunday checkpoint. The offline packet
consumer and case-selection rules are prepared; they do not declare a final packet.
Reread this README before edits.
