# Stage 15 theory days

The curator commissioned this CPU-only Gear 2 campaign on November 6, 2026.
The [unchanged supplied packet](PACKET.md) defines seven primary cards and four
ordered backlog cards. [Review](REVIEW.md) records implementation decisions;
[intake](DATA_INTAKE.md) governs the three public sources. Each card has a separate
design note that must be committed before its first scientific outcome.

Source intake and constructed validation are prerequisites, not scientific results.
The campaign has a shared 15 CPU-hour budget, including source preparation,
validation and independent replay. Per-card limits and all previous attempts remain
binding. No paid calls or GPU work are admitted. The curator clarified that there
is no separate Gear 3 pass to implement.

The conservative operational clock starts November 6 at 07:00 PST, the supplied
packet's local handoff time rounded down. Starts freeze November 7 at 19:00 PST;
drain is November 8 at 07:00 PST. This does not extend the handoff window.
Week 4 retains its own distinct clock; neither campaign silently borrows the other's
budget. Source, runtime and consumer readiness are recorded separately.

Results are filed under `results/phase_2_4_stage_15/THEORY_DAYS/`, with `S15-TD`
claim identifiers. Full internal write-through precedes watcher acknowledgment;
the final curator digest follows drain. No unfinished per-artifact scores are reported.
