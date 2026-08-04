# Provenance ledger — what the curator said, and what it changed

**The index this project was missing.** Every substantive thing the curator has contributed, on one
line, paired with what it produced and where that lives. Written at his instruction:

> There needs to be a repository of linking my commentary and what we gained from it on a
> one-to-one basis... **let's make sure we don't lose this to the context drift over time, because
> this was valuable.**

**Rules for this file.** One row per contribution. Newest at the top of each section. A row is
added the same day the contribution is made, never reconstructed later. If a contribution changed
nothing, it still gets a row saying so — an idea that went nowhere is part of the record, and a
ledger that only lists wins is a ledger nobody can trust.

**Status vocabulary.** `built` — in code or in the corpus. `written` — a doc exists. `planned` —
scheduled, not started. `open` — accepted and unaddressed. `rejected` — considered and not taken,
with the reason.

---

## Session 01 — ten artifacts read blind, 2026-08-03

| # | What he said | What it produced | Where | Status |
|---|---|---|---|---|
| S1.1 | *"Is it a three goddamn part process?"* — partial expertise solves the easy layer → motivation → reverse-engineer the rest | The loop is unidirectional and purpose-first; E36 is half a cycle. **Entry point is an anomaly, not a purpose.** | `curator_session_01_findings.md` §2 | **built** — the loop now takes an entry point; `run_loop(anomaly_pass=True)` |
| S1.2 | *"I noted the oddity, the thing that demanded an explanation, first"* — three times, on three artifacts | An anomaly stage before any purpose is proposed. Cheapest high-value build in the project. | same §2 | **built** — `bounded_v6.yaml` stage zero, `StageZeroOut`, locked |
| S1.3 | *"Not the whole pie"* — corporate goals are many and real; one term takes a disproportionate **share** | C-22 corrected from *singular vs layered* to **concentration**. That is `purpose_breadth`. | `FLATTENED_INTENT.md` correction; `run_gate3.py` records it | **built** |
| S1.4 | *"How often I reach for the emotional state of the author... Panksepp's primitives"* | First answer to C-23. The bounded family has **no affective dimension at all**. | findings §4 | **built** — `family_v3.yaml` `performed_affect`, stage E, N-AFF, locked |
| S1.5 | Thick/thin assessments for all ten; then *"we need to hard define"* these | Surface and depth defined as decision densities separated by **what the decision targets**; asymmetry derived from automaticity | `docs/theory/SURFACE_AND_DEPTH.md` | **written** |
| S1.6 | *"Surface thickness gets thinner as people get lazy while their depth remains constant"* | S-1..S-4: depth is stationary within an artifact, surface is not. Machine content predicted to show **flat surface**. | same, §4 | **built** — `measures/position.py`, `runners/run_s1.py`, `DecisionV6.targets` |
| S1.7 | *"It's not that I'm failing to extract... it's that I don't even try"* | The wall is reached by **shortcut on a surface cue**, before inference is attempted — E54's pre-shut gate in a human | findings §6 | **open** |
| S1.8 | *"A hidden motive so shallow that an AI could accomplish it easily"* | Links C-22 to provenance through the maker's own cost-benefit, with no detector and no surface signature | findings §7 | **open** |
| S1.9 | *"A hyper-optimizing machine waiting on every little variable will super focus on that"* | Measured: Wayback banner on 7/23 Half B, 0/28 Half A. Gate 3 restarted on sanitised input. | D-6, `run_gate3.py` | **built** |
| S1.10 | *"I strongly disagree with the decision to keep date in... you're just wrong on that call"* | Overruled me. Date **values** censored to `[year]`/`[date]`, the fact of a date kept. Gate 3 restarted again. | `report/sanitize.py` | **built** |
| S1.11 | Recognised an author **from line shape, before reading a word** | Reflow + one-artifact-per-host + exclude-already-read. Recognition beats extraction noise as a contaminant. | `report/sanitize.py`, `reexport_for_reading.py` | **built** |
| S1.12 | *"I'm being presented a specific face... it is the presentation I'm tapping into"* | What is recoverable is a **persona plus its leaks**, not a person. Belongs in `may_not_claim`. | findings §9 | **open** |
| S1.13 | *"I'm kind of gassing out... as a fatigue effect"* | Reading order must be randomised per reader or late artifacts are systematically under-read | findings §9 | **planned** — session 02 |
| S1.14 | *"I wasn't giving you what you needed... what I needed was some kind of Likert scale"* | The ordering question was the wrong instrument. Session 02 uses a labelled scale, not a sort. | successor §5 | **planned** |
| S1.15 | Ratings: roofing page (Half B) **5**, clearly human, depth beneath; a Half A post at **3–4**, maybe not human | **The curator's ordering does not respect the corpus split.** G3.1 is looking for a boundary that may not exist in the card's shape. | findings §1 | **open** — decides the successor |

---

## Session 02 — stopped after artifact 01 to fix the protocol, 2026-08-03

| # | What he said | What it produced | Where | Status |
|---|---|---|---|---|
| S2.1 | *"The variation of the veneer is one of the loudest indicators I've found"* | Not surface LEVEL — surface **change**. S-1 is his primary detector, not my hypothesis. | `curator_session_02.md` §1 | **open** — measure exists, untested |
| S2.2 | *"Useless against a real published book because of the layers of editing"* | Scope limit on the whole surface-variance measure — **and it says today's books result cannot be surface variance.** | same §1 | **open** — testable, cheap |
| S2.3 | *"Depth is a property of the writer **with respect to the domain**"* | Sharpest definition of depth the project has. Makes depth a RELATION. Falsifier attached: depth moves where domain moves. | same §2 | **written** |
| S2.4 | *"People don't perform Panksepp-level drives"* | The emblematic layer cannot use the primary-process list. family_v3's "named simplification" is now a known error. | same §3 | **built** — emblematic is free text |
| S2.5 | *"Fractal layers of nested goals placed there by the subconscious. I'm extracting it all equally"* | **The share question is not answerable by a reader.** A share needs a denominator; nested goals have none. C-22 keeps `purpose_breadth`, loses its human check. | same §4 | **built** — Q4 cut; C-22 moved to a mechanism test |
| S2.6 | *"It starts questionable"* and 8–9 by the end | Confidence in a maker MOVES while reading. The trajectory carries what the endpoint does not. | same §5 | **built** — Q1 asks for movement |
| S2.7 | *"programme"* — spelling gave it away | Orthography is an unlisted contamination channel. Not fixed: normalising spelling would destroy evidence. | same §5 | **accepted contaminant** |

---

## Before session 01

| # | What he said | What it produced | Where | Status |
|---|---|---|---|---|
| C.1 | *"Corporations steal your intention and replace it with money... it's a flattening"* | C-22, logged mid-run before Gate 3 results, with five failable predictions | `docs/theory/FLATTENED_INTENT.md` | **written** — F-3 checkable |
| C.2 | *"High expertise should produce the same number of visible decisions"* | E43 corrected: compression removes decisions from the **maker's report**, not from the artifact; the reader is unaffected | `SIM_REREAD.md` §4 | **built** into family v2 reasoning |
| C.3 | *"I'm drawing too much information from surface level indicators"* | The plain-text export. Every prior calibration was of a rendered web page. | C-21, `export_for_reading.py` | **built** |
| C.4 | *"If it's in the theory, it counts as a prediction"* | Method unlock accepted as theory-derived rather than post-hoc; direction fixed by E36 before the project began | `prereg/gate3.py` | **built** |
| C.5 | *"This is an engineering problem, not a scientific verdict"* | Stop conditions demoted from verdicts to telemetry. A failed threshold produces candidate fixes, not a halt. | this session's practice | **open** — not yet written into `GATES.md` |
| C.6 | *"Autism is a confound... your only participant is autism"* | Single-reader limitation named in `may_not_claim`; C-20 second reader still owed | `prereg/gate3.py` | **open** |
| C.7 | *"That's just context rot"* — stopping the repo audit | Scope discipline: not everything adjacent is worth reading | — | **built** into practice |
| C.8 | *"It needs to be in a field in which I have expertise"* | Corpus moved to games/technical writing. **Now in tension with S1.1** — fit needs expertise, unlock needs *partial* expertise. | findings §1 | **open** — no single corpus serves both |

---

## Contributions that changed nothing yet

Kept visible on purpose.

| # | What he said | Why it is still open |
|---|---|---|
| C-14 | grooming corpus | Never sourced. It is E55's motivating case and the successor's required corpus. The oldest unpaid debt here. |
| C-19 | the two arms disagree | Hybrid readings remain unsound; no API replication has run |
| C-20 | a second reader | Every calibration is one person. E10 says reader skill caps extraction; one reader cannot bound their own cap. |
| C-23 | no analog for human-shaped maker goals | S1.4 proposes affective primitives as the answer. Nothing is built. |
