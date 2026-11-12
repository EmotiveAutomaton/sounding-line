# Review of the November 10 record-keeping recommendation

Status: revised implementation approved by the curator on November 11, 2026,
beginning with generated views over preserved evidence. The additive pilot is
implemented under the [navigation contract](../../records/README.md). Original
filing sources, scientific protocols, worker configuration and wake scheduling
remain in force. No Ghost repository change or audit is claimed.

## Assessment

The separation of enduring claims, individual runs and theory-facing texture
notes is useful and implementable. The recommendation should not be applied
verbatim: its standing rule could prevent necessary evidence corrections, its
proposed migration would break current bindings without compatibility work,
and its automatic classification assumes distinctions the existing rows do
not always make.

The supplied [recommendation](RECORD_KEEPING_RECOMMENDATION_20261110.md) is
preserved byte for byte. It is dated November 10 and was reviewed locally on
November 11. The original intake remains at the workspace top level for provenance.

Source SHA-256: `2acbd09b112e6e48d7d1967f11c4864ef8218285c1d9aa89deac0d2a6b9f71f4`.

Inspection at repository commit `0bafb81c8dba2e75793bc09706f29921cd62cbab`:

| Record | Observed size or count |
|---|---:|
| Stage 15 ledger rows | 1,226 |
| Rows whose outcome is exactly `infrastructure` | 1,091 |
| Additional `historical infrastructure` rows | 6 |
| FINDINGS words / lines | 1,495,922 / 78,450 |
| STATE words / lines | 117,244 / 8,968 |

Word counts use whitespace-separated tokens; these are navigation measurements,
not model-token estimates. The recommendation's older counts are not used as
current measurements.

## Changes needed before implementation

1. **Separate claim standing from evidence validity.** A reviewed primary or
   replication can strengthen a scoped claim. A failed control, invalid source,
   attribution correction or broken dependency must be able to invalidate or
   downgrade its evidence immediately. It cannot wait for another human study
   or constructed replication. Preserve the active curator theory-pass rule
   for changes to theoretical interpretation. Run-level outcomes remain part
   of the record; their existence does not automatically change a theory claim.

2. **Introduce views before moving authoritative records.** Generate a concise
   scoreboard, science index and operations view over the existing records.
   Keep current IDs, source files, anchors and immutable receipts available.
   Current ledger sources bind a file, line, heading and file digest; active
   landing helpers also write to FINDINGS and refresh those bindings. Moving
   entries first would break the old readers or let the old writers recreate
   the problem. A later relocation needs an explicit source map, migrated
   writers and validators, compatibility anchors and a verified rollback.

3. **Represent uncertainty and multiple evidence types.** Keep `record_kind`
   separate from run purpose: a calibration and a health inspection can both
   have an infrastructure outcome while only one bears on an instrument's
   scientific sensitivity. Population needs `mixed`, `not_applicable` and
   `unknown`, as well as people, models and constructed. Preserve the existing
   detailed scope and distinguish evidence substrate from the reader or
   measuring program. For example, IN3.ic and IN4.ic use constructed outcomes
   conditional on a human observational design, read by an exact program.
   Backfill only explicit, unambiguous cases automatically; record the rule
   and its source. Unreviewed is different from uninformative. Missing values
   must not silently become false or uninformative.

4. **Give individual claims stable identities and explicit relationships.**
   A claim family is a grouping, not one statement whose members must share
   a standing. A run can support one claim and count against another. Keep a
   small reviewed claim register and many-to-many evidence links, each with
   its own bearing, scope and reason. A scoreboard renders reviewed standing
   and its basis; it does not vote over run counts, choose the newest outcome
   or infer standing from a keyword. Distinguish the last standing change from
   the most recent evidence review. Theory tags remain a controlled but
   extensible index, not a replacement for the hypothesis identifiers.

5. **Keep constructed evidence distinct from a guaranteed readout.** A result
   fixed by its setup belongs in a scale or construction report. Merely using
   synthetic data does not make a result fixed by construction. A genuine
   constructed comparison can establish a property under its assumptions;
   an additional repetition does not by itself turn that into human evidence.
   `by_construction` needs an explicit justification and an unreviewed state.

6. **Specify the authority and provenance of CURRENT and QUOTES.** No exact
   theory-thread state file is identified by the supplied recommendation.
   CURRENT needs a named, versioned, curator-approved source, source digest,
   as-of date and links to the underlying positions. Until then, the existing
   theory files remain authoritative. QUOTES must distinguish the exact text
   currently filed from an independently checked original transcript. Preserve
   documented transcription repairs, source date, filing date and supersession
   relationships. The existing contract allows curator-directed corrections
   and removal, with history retained in Git; a new index must not override
   those instructions or resurrect removed quotations as current.

7. **Keep texture notes beside their full results and use existing attention.**
   A theory-facing texture card can say what the result suggests without
   presenting itself as a verdict on the whole claim. Its underlying frozen
   estimates, controls, thresholds, pass/fail outcomes and null results remain
   accessible. Apply the prospective “what would this change?” check to new
   designs; do not change a running card or hide an uninteresting outcome.
   The weekly re-read is annotation work within existing authorized attention,
   not a new autonomous agent, wake cadence or research run. It avoids new
   experiment compute, but still consumes reviewer time and model tokens.

## Approved implementation sequence

1. Freeze a migration inventory containing IDs, source bindings, output paths,
   source hashes and the current writer/validator entry points. Preserve the
   original ledger and intake. Identify live writers before any migration.
2. Add a versioned annotation overlay keyed by existing IDs. Start with an
   explicit reviewed/unreviewed state and deterministic provenance for the
   few fields that can be populated safely. Do not rewrite the old outcome or
   scope fields. Use a claim register plus evidence links for reviewed mappings.
3. Generate SCOREBOARD, a science-only navigation view, an operations view and
   START_HERE_FOR_AGENTS under 300 lines. Retain original records as the source
   during this transition. Show incomplete classification prominently.
4. Pilot the views and five queries on a bounded, fully reviewed set: human
   attention evidence; constructed method checks; a claim's evidence and
   corrections; completed textures for a theory line; operational failures
   affecting a claim's instrument. Validate answers against the original rows.
5. Build QUOTES as a source-linked inventory, with ambiguous attribution or
   missing dates flagged. Generate CURRENT only after its authoritative input
   and revision rules are settled. Do not silently retire the long theory files.
6. Add one bounded old-stage re-read to the existing work list. Store its exact
   source theory revision and scope. It may fill reviewed annotations and
   propose interpretation; it does not authorize new experiments or silently
   promote claims. Re-evaluate the claimed twenty-stage schedule against the
   actual stage inventory and available review time.
7. Change the startup contract and landing writers together after the pilot
   passes. Switch first to the short navigation views. Only then consider
   physically relocating operations, with historical links and receipts
   preserved. Update instruction files explicitly and retain a rollback path.

## Acceptance checks

- Every original ID and source receipt remains reachable; no entry disappears
  because it is operational, invalid, superseded, null or unclassified.
- Old consumers continue to resolve the original sources during the additive
  phase. Duplicate IDs, missing sources and stale generated views fail validation.
- A failed control can withdraw evidence validity without waiting for new data;
  merely appending an operational receipt cannot strengthen a scientific claim.
- A mixed-source calibration, an administrative inspection and a human primary
  remain distinguishable in generated queries. Unknown classifications are visible.
- A run bearing differently on two claims is represented without duplicating
  its execution or forcing one global bearing.
- Construction guarantees, measured constructed outcomes and human evidence
  remain separate; independent replication is not inferred from replay.
- Quote text matches its declared source exactly; repaired wording and unavailable
  original transcripts are labelled honestly. Supersession does not erase provenance.
- Regeneration is deterministic, records source versions and does not touch
  active experiment inputs, frozen scoring or the authorized wake policy.

These checks require targeted fixtures for the navigation and migration tools,
not new scientific experiments. The approved additive implementation preserves
the legacy production schema and scientific standing. Broader annotation review,
CURRENT's authoritative source and physical relocation remain the explicitly
sequenced later work; they are not silently represented as completed here.
