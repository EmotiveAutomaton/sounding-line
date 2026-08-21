# Deviations

**Every deviation is logged where it happened.** Carried from the Ghost Scale Simulation, where
the practice caught four separate criteria that turned out to be unable to do their own job — each
found by a later pass, and each retained and still computed rather than replaced.

## The rule

When a hash-locked artifact changes:

1. **Record it here**, before the change is made, with the reason.
2. **Retain the original** and keep computing it.
3. **Report it as failing if it fails.** A criterion rewritten after seeing a result and then
   reported as passing is the one thing this project cannot do.

Updating a lock hash without an entry here is a defect, not a shortcut. `soundingline/hashlock.py`
raises rather than warns for this reason.

## Amendments to the spec

`SOUNDING_LINE_SPEC.md` is pre-registered and is **not edited**. Amendments live in
[`gate0/LITERATURE.md` §8](../gates/gate0/LITERATURE.md) — A-1 through A-5 — because that is where they were
decided. They are indexed here so this file is the single entry point.

| id | what changed | where decided |
|---|---|---|
| A-1 | §6's novelty claim amended — bounded-family Bayesian inversion is prior art | Gate 0 §2 |
| A-2 | Gate 3 promoted; the free-form arm runs from Gate 1 in parallel | Gate 0 §2 |
| A-3 | D-4 resolved to "harden, and log" rather than "harden first, measure second" | Gate 0 §8 |
| A-4 | No fetcher until Gate 2 clears; corpora from RAID and the DFRLab audit | Gate 0 §8 |
| A-5 | The probe is hybrid — local for volume, API as quality reference | Gate 0 §8 |
| A-6 | Hand-picking reframed as **curation against pre-registered expectations**. Gate 1 makes no distributional claim, so a curated set calibrated against expectations written before any run is the correct design, not a weaker one. The spec's `may_not_claim` sentence stays attached to every Gate 1 number. | CANDIDATES.md §0 |
| A-7 | **Family v2.** `effort` split into `artifact_effort` and `demonstrated_work`, forced by the curator reaching for a dimension the family lacked and then splitting it in two before it was built. v1 is retained unedited and stays locked. | CALIBRATION_02 §5 |

## Deviations from pre-registered criteria

No pre-registered *criterion* has been altered. Two **additive** changes are recorded below:
both create new files rather than editing locked ones, so every v1 hash still verifies and
readings taken under v1 remain comparable to each other.

| date | artifact | change | reason | original still computed? |
|---|---|---|---|---|
| 2026-08-02 | `family_v1.yaml` | **not edited**; `family_v2.yaml` added alongside | Two calibration passes showed the family was missing a dimension the curator reached for unprompted, and then split it in two before it was built (C-4 revised). Editing v1 would have silently invalidated every reading taken under it. | **yes** — v1 loads via `FAMILY_V1_PATH` and stays locked |
| 2026-08-02 | `bounded_v2.yaml` | **re-locked once**, pre-commit and pre-run: the first hash was taken while the file still had CRLF endings. The lock fired on conversion to LF, which is correct behaviour — hashlock reads bytes on purpose. A hash recorded in error, not a criterion changed after a result. | n/a — no reading was ever taken under the CRLF hash |
| 2026-08-02 | `bounded_v1.yaml` | **not edited**; `bounded_v2.yaml` added alongside | Stage D cannot return a field it was never asked for. Only `stage_d_tradeoffs` differs; every other stage is byte-identical to v1. | **yes** — v1 stays locked |

### Obligations outstanding

| id | obligation | source |
|---|---|---|
| C-6 | Fit must decompose *few decisions made* from *decisions unreadable from here* | CALIBRATION_01 §4 |
| C-8 | Test whether high `demonstrated_work` motivates artifact production | CALIBRATION_02 §5 |
| C-9 | Chunk-position gradient — confounds convergence-across-chunks | CALIBRATION_02 §6 |
| C-11 | Flag curator readings of artifacts resembling the curator's own work | permanent |
| C-13 | **Decisions can be amortised into templates.** A reading changed on seeing an identically formatted sibling guide, revealing the format as a prior decision reused across artifacts. The instrument reads one artifact at a time and cannot see this. Related to E43. | curator, post-batch-2 |
| C-14 | **Row 1 (grooming networks) deferred to Gate 2.** Research organisations deliberately do not republish primary text, and A-4 forbids live fetching until Gate 2. | CURATION_BATCH_3 §1 |


## 2026-08-08 · SOUNDING_LINE_SPEC.md was deleted, pushed, and restored

**The hash-locked specification was deleted from the working tree by an unidentified operation in the
window between commits `bd83706` and `3c4a257` (2026-08-07 evening), swept into a bulk `git add -A`,
committed, and pushed.** It sat deleted in public history for roughly two hours. **Caught by hash-lock
verification during the 2026-08-08 integrity audit** — not by any person or process noticing.

Restored from `3c4a257~1` and **verified byte-exact against its locked sha256.** The deletion and the
restore both remain in history, which is the honest audit trail. The mechanism of deletion was not
identified; the window is narrow and the operations in it are logged in the transcript.

**Process change (in `CLAUDE.md` hard rules):** the lock check runs before every commit, and the
deletion lines of `git status` are read before any bulk stage. An unintended deletion is a
stop-everything event.

## 2026-08-08 · Five gate-era locked files live at new paths

`soundingline/locks.py` records `docs/gate0/…` and `docs/gate1/…`; the files were moved to
`docs/gates/gate0/…` and `docs/gates/gate1/…` in an earlier documentation reorganisation. **All five
verified hash-identical to their locks at the new paths** (`LITERATURE.md`, `item_A.md`, `item_B.md`,
`item_C.md`, `PROTOCOL_SEALED.md`). `locks.py` is itself never-edit, so the path mapping is recorded
here rather than there. `verify_all()` will report these five as missing until a wrapper maps paths;
use this entry as the map.

## 2026-08-21 · SOUNDING_LINE_SPEC.md moved off the repo top level

At the curator's instruction (audio, 2026-08-21 morning). `soundingline/locks.py` records the
lock under the key `SOUNDING_LINE_SPEC.md`; the file now lives at `docs/SOUNDING_LINE_SPEC.md`,
**verified hash-identical to its lock at the new path before the commit** (bytes unchanged; the
never-edit rule is untouched by a move). `locks.py` is never-edit, so this entry is the human
record of the mapping and `tools/verify_locks.py` (created the same pass) is the executable one —
it is now the canonical verifier, replacing the ad-hoc inline snippets, and carries both this
mapping and the 2026-08-08 gate-files prefix map above. Any future locked-file move gets a twin
entry here and in that tool's PATH_MAP, same pass.
