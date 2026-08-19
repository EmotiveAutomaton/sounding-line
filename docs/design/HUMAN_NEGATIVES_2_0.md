# Human-negative assembly — Phase 2.1.6 working plan (2026-08-19)

**What this is, in plain words.** The detector we are building answers "did an AI
substantially help write this?" A detector is only trustworthy if it does not accuse
humans falsely — and the humans most often accused falsely are the ones writing quickly,
sloppily, or from templates, not the ones writing polished essays. So the benchmark needs
a large, varied collection of genuinely human writing (the "human negatives"), and the
human and AI examples must be matched on the obvious surface properties (length, register,
quality), because we measured what happens otherwise: unmatched, a trivial feature list
tells them apart at 98% without reading anything that matters (L135). This document is the
plan for collecting, licensing, and matching that human writing. Ruling 7 untouched:
everything here is $0.

**Curator ratifications (2026-08-19, verbatim decisions):**
1. **Revision labor: option (a).** The regimes needing real human revision (a person
   revising AI text; AI revising a person's text) are seeded by HIS OWN revision sessions
   logged as they naturally occur. No scheduled labor; the cells grow slowly and are
   reported thin meanwhile.
2. **Internal-vs-public rule: agreed.** Internal evaluation uses everything we hold; the
   public benchmark ships only license-verified cells.
3. **His caveat, adopted as a named rule — EVIDENCE FILTERS ARE PREREGISTERED ONLY:**
   internal calls never exclude data over licensing, shipping, or any other concern that
   is not a preregistered methodological gate. License status decides what SHIPS, never
   what counts as evidence. A promising internal result is never removed by a validity
   check that was not frozen before the run.

## 1. What we hold, and its licensing state (the audit checklist)

| corpus | human class | license state | action, whose |
|---|---|---|---|
| ArgRewrite (86 authors x 3 drafts) | careful process-recorded essays | research corpus; REDISTRIBUTION UNVERIFIED | mine: locate the license file in the distribution and record terms; benchmark can USE it internally regardless, redistribution decides only whether it ships in a public benchmark |
| 34-book corpus | human long-form | in copyright; internal research use only | mine: mark internal-only in the schema; it never ships |
| PAN human documents (by year) | web/document human text | varies BY YEAR; some years research-only | mine: per-year license read at the source packages we hold |
| ScholaWrite | process-recorded scholarly writing | public release with a stated license | mine: record the exact license string from the release |
| G133 commission machinery | low-effort timed human writing | ours when produced | blocked on §3 below |

**Standing rule adopted now: internal evaluation may use everything above; the PUBLIC
benchmark ships only cells whose license line is verified, and thin public cells are
reported thin, never padded** (the contract's own clause).

## 2. The missing class: low-effort and templated human text

The one human class not on our shelf. Sourcing constraint: anything authored after 2022 is
contamination-suspect, so honest sources are PRE-LLM corpora with clear licenses. Candidate
list to verify at source (mine, a reading task; fetch discipline applies, snippets do not
count): pre-2022 email corpora (business boilerplate), pre-2022 review datasets (short
low-effort registers), pre-2022 forum/QA dumps with research licenses, and template-filled
official text (public-domain government boilerplate). Each candidate gets: license line,
date bound proving pre-LLM authorship, register label, and a leakage-reference read before
admission (a source the 49 features solve trivially against our positives is admitted only
inside matched cells).

## 3. Curator decisions — RESOLVED 2026-08-19

Both asks were answered same day and are recorded at the top of this file: revision labor
runs on option (a) (his logged natural sessions), the internal-vs-public rule is ratified,
and his caveat is adopted as the evidence-filters-are-preregistered-only rule. **Nothing in
2.1.6 is blocked on the curator any longer.** Remaining work is all agent-side: the license
reads, the sourcing survey, the matched-cell construction, and the matched
leakage-reference rerun (the L135 instrument on matched cells — the number that tells us
whether matching worked), next build after the G159 wave.

## 4. Matched-cell construction (the build after the audit)

Cells matched on register (argumentative essay to argumentative essay first: ArgRewrite
finals vs G153/G159 essays), length (subsampled to overlapping bands), and quality where a
quality score exists; every cell carries lineage ids; the leakage reference reruns per cell
and its per-cell accuracy is the cell's shortcut label, reported alongside any detector
number forever (contract §3b interfaces; L135/L138 receipts).
