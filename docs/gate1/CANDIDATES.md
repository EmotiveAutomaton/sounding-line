# Gate 1 — candidate artifacts, for curation

**Status: a menu, not a selection.** Nothing here is chosen. This document exists so the seven
Gate 1 artifacts can be *curated* from a wide field rather than *recalled* from memory, and so
that the field itself is on the record before anything is picked from it.

Read [§0](#0-the-methodological-point-that-changes-how-this-list-should-be-used) first. It is the
part that matters.

---

## §0. The methodological point that changes how this list should be used

The Gate 1 card says, in `may_not_claim`:

> n is seven, the artifacts are hand-picked by the author, and hand-picking is selection on the
> dependent variable.

That is true of hand-picking **as ordinarily practised**, and it is a fatal objection to a
distributional claim. But Gate 1 makes no distributional claim. SPEC §10: *"Success is
interpretable output, not accuracy."* The question is whether the instrument produces a reading a
human can argue with — and for that question, a curated set is not a weaker design than a random
one. It is the **correct** design, and the analogy is exact: you calibrate an instrument against
known standards, not against a random sample of the world.

What separates calibration from selection-on-the-DV is a single, checkable discipline:

> **The expected reading is written down, per artifact, before the instrument is run — and it is
> hash-locked.**

If the expected reading is recorded first, a curated set becomes a set of standards and the
instrument can *fail against them*. If it is not, the curator's judgement and the instrument's
output are the same object wearing two hats, and no result means anything.

**So the proposal is:**

1. Curate seven from this list — one per corpus type in SPEC §7.
2. For each, write the expected four-part reading **before any run**: rough fit (high/low),
   expected convergence, expected depth band, and expected mass on the machine-audience
   hypothesis. Prose is fine; precision is not the point, *commitment* is.
3. Hash-lock the manifest and the expectations together, as `prereg/gate1_calibration.py`.
4. Run. Every artifact where the instrument disagrees with the curator is a finding — and it is
   genuinely ambiguous which of the two was wrong, which is exactly the right position to be in
   at Gate 1.

**This is a change to what the spec said, and it should be recorded as an amendment (A-6) rather
than slipped in.** The spec's `may_not_claim` sentence stays true and stays attached to every
Gate 1 number; what changes is that "hand-picked" becomes "curated against pre-registered
expectations," which is a stronger claim than the spec assumed was available.

**One selection rule that must hold regardless:** the curator may not read a candidate looking for
one the instrument will do well on. The criterion is *"I can state in advance what should come
out"*, never *"I think it will score high."* Those come apart most sharply on the SEO row, which
is the row the whole gate turns on.

---

## §1. What each row has to do

The seven rows are not seven examples. Each one is load-bearing against a specific failure.

| # | Corpus type | What it tests | The failure it catches |
|---|---|---|---|
| 1 | Identified grooming network | the target case | — |
| 2 | Personal blog / newsletter / forum long-post | real maker, real decisions | fit that can't go high |
| 3 | **Human-written SEO filler** | **the critical confound** | **convergence tracking topic coherence** |
| 4 | Press release / institutional boilerplate | human, obligation-discharging, low depth by design | depth reading as quality |
| 5 | Pre-2020 archived text | near-certainly human, no contamination | contamination in the "human" baseline |
| 6 | Model output, **rich deliberate** prompt | **should score HIGH** | the instrument being an AI detector |
| 7 | Model output, **thin automated** prompt | should score low | — |

**Rows 3 and 6 are the ones to spend curation effort on.** Row 3 is SPEC §7's first killer:
a tidy spam farm is internally consistent, and if the probe converges on garbage because the
garbage is well-organised, the instrument is a quality classifier with extra steps. Row 6 is §1's
entire claim — a carefully directed model output must outrank human filler, or the instrument is
an AI detector wearing a theory.

Rows 1, 2, 4, 5, 7 are comparatively easy to source well. **Do not let that make them the ones
that get the attention.**

---

## §2. Row 1 — identified grooming network

**Source, and do not deviate from it:** the [DFRLab / CheckFirst Pravda
Dashboard](https://checkfirst.network/project/pravda-dashboard/) and the [April 2026 Common Crawl
audit](https://dfrlab.org/2026/04/08/pravda-in-the-pipeline/). Domain lists and per-country
breakdowns are published on GitHub and updated hourly. Per A-4, we take content **as already
captured in the audit** rather than fetching from live network domains.

Because the manifest stores hashes and offsets rather than text, candidates here are described by
*kind* rather than URL. Pick by shape:

| id | shape to look for | why it is a distinct test |
|---|---|---|
| G-1 | a near-verbatim syndicated republication appearing across many network domains | maximal machine-audience signal; the artifact was made to be *counted*, not read |
| G-2 | a lightly-rewritten wire story with an inserted framing paragraph | the decision chain is real but tiny and all at one level — tests whether depth separates from length |
| G-3 | a high-volume auto-translated item | tests whether the probe reads translation artefacts as absence of a maker (it should not) |
| G-4 | a network item that is *well written* and topical | **the hardest case in this row** — if fit comes out high here, that is informative and possibly bad news |
| G-5 | an item from the Glassbridge cluster named in the 2026 audit | a second network, so row 1 is not one operator's house style |

**Curation note:** G-4 is the one worth arguing about. A grooming artifact with genuine
craft behind it *has* a recoverable maker with a real purpose — and §4's whole design says
`audience: machine` is a hypothesis in the family rather than a residual. The right expected
reading may well be *high fit, high convergence, high machine-audience* — which would be the
instrument working perfectly and saying something uncomfortable.

---

## §3. Row 2 — personal blogs, newsletters, forum long-posts

Real makers, visible decisions. The abundance here is the risk: it is easy to pick something
beautifully written, which measures craft rather than recoverable intent.

**Pick for visible rejected alternatives, not for prose quality.** The instrument's `Decision`
type requires an `alternative_rejected`; an artifact where the maker never shows their working
will score low no matter how good it is, and that is correct behaviour.

| id | kind | what makes it a good standard |
|---|---|---|
| B-1 | a long technical post-mortem (outage, bug hunt, migration) | decisions and rejected alternatives are the genre's *content* — should be the highest-fit artifact in the whole set |
| B-2 | an essay that visibly changes its own mind mid-piece | tests level-3/4 depth: framing and stance choices, not just local ones |
| B-3 | a "why I built this / why I stopped" project retrospective | cost-borne and trade-offs are explicit; good standard for row-4 contrast |
| B-4 | a long-form forum reply in a specialist community | a *specific known group* audience — tests that dimension away from `general_public` |
| B-5 | a personal newsletter issue with a strong recurring voice | tests whether voice is mistaken for depth (it should not be) |
| B-6 | a recipe or how-to written by someone with an actual opinion | deliberately mundane subject, high decision density — a strong anti-"depth is prestige" control |
| B-7 | a hobbyist's exhaustive comparison writeup | high effort, possibly *low* depth — N21's effort/depth dissociation, in the wild |
| B-8 | an "ask" post: someone thinking out loud about a decision they have not made yet | purpose = `express`, audience = `known_group`; a rare corner of the family |

**Curation note:** B-7 is a trap worth setting deliberately. If the instrument reads effort as
depth, N21's dissociation does not transfer from the simulation to real text, and that is worth
knowing at Gate 1 rather than Gate 4.

---

## §4. Row 3 — human-written SEO filler *(the critical confound)*

**This is the row the gate turns on, and it is the hardest to source honestly.**

The requirement is: **human-written**, and nearly intentless. That combination is much rarer than
it sounds — most modern SEO filler is machine-written, which makes it row 7 rather than row 3 and
destroys the control. The confound only works if the artifact is unambiguously human and
unambiguously hollow.

**The reliable source is the pre-2020 content-farm era**, which predates capable generative models
and is therefore human by construction:

| id | kind | note |
|---|---|---|
| S-1 | a Demand Media / eHow-era how-to (c. 2008–2013) | written to a keyword brief by a paid human at volume — **the canonical row-3 artifact** |
| S-2 | an About.com / early-Answers-site topic page from the same era | same economics, different house style |
| S-3 | a pre-2020 "best X of YEAR" affiliate listicle | purpose = `sell` with a thin veneer of `inform`; tests whether the family separates them |
| S-4 | a local-services doorway page ("plumber in <city>") pre-2020 | near-zero decision density, human, *and* machine-audience — the closest human analogue to row 1 |
| S-5 | a scraped-and-lightly-rewritten product description | human labour, no human intent |
| S-6 | a pre-2020 press-release-to-article rewrite from a low-tier outlet | human, obligation-shaped, adjacent to row 4 |
| S-7 | a keyword-stuffed "ultimate guide" of the 3,000-word era | **long and hollow — the single best test of "depth is just length"** |

**Curation note:** S-7 earns its place by being *long*. If the instrument's depth reading tracks
length, S-7 will out-score B-6, and the falsifier fires at Gate 1 instead of Gate 2. Include it.

**Sourcing:** the Wayback Machine, dated pre-2020, is the practical route and it also satisfies
row 5's contamination requirement. RAID's human text (all published pre-2022) is a second source
but skews toward well-formed genres — it has no content-farm domain, so it does **not** cover
this row. That is worth stating plainly: **row 3 cannot be sourced from RAID and must be
curated by hand.**

---

## §5. Row 4 — press releases and institutional boilerplate

Human, obligation-discharging, low depth *by design*. The expected reading is the interesting
part: **low depth but not low fit.** A press release has a perfectly recoverable maker and a
perfectly clear purpose — it is just that almost no decisions are visible. If fit comes out low
here, fit is measuring something closer to "decision density" than "hypothesis quality," and the
two need separating.

| id | kind | note |
|---|---|---|
| P-1 | a corporate quarterly-earnings press release | purpose = `discharge_obligation`, audience = `known_group` (analysts) |
| P-2 | a university research press release | genuine content, formulaic frame — tests the seam |
| P-3 | a software EULA or privacy policy | the purest `discharge_obligation` artifact available |
| P-4 | city-council or planning-committee minutes | human, procedural, near-zero authorial intent, real informational content |
| P-5 | an SEC 10-K risk-factors section | boilerplate with *legally consequential* word choices — decisions exist but are nearly invisible |
| P-6 | a product recall notice | high stakes, low depth; tests that the instrument does not read stakes as depth |
| P-7 | a conference call-for-papers | formulaic, but someone made real scoping decisions |

**Curation note:** P-5 is the sharpest instrument in this row. Risk-factor language is negotiated
word by word by expensive people — it is *maximally* decided and *minimally* legible. If the
probe recovers even one real decision there, that is a strong signal; if it recovers a confident
chain of invented ones, that is E2 firing on real text and would be the most important thing
Gate 1 could find.

---

## §6. Row 5 — pre-2020 archived text

Near-certainly human, no contamination. Cheapest row to fill; **RAID covers it outright** (all
human text published pre-2022) and Project Gutenberg / Wayback cover the rest.

| id | kind |
|---|---|
| A-1 | a pre-2020 BBC news article (RAID `news` domain) |
| A-2 | a pre-2020 arXiv abstract (RAID `abstracts`) |
| A-3 | a pre-2020 Reddit long-post (RAID `reddit`) |
| A-4 | a pre-2020 IMDb review (RAID `reviews`) |
| A-5 | a Gutenberg essay or letter, pre-1930 |
| A-6 | a Usenet or early-web personal page, 1995–2005 |
| A-7 | a pre-2020 Wikipedia plot summary (RAID `wiki`) |

**Curation note:** A-6 is worth including for a reason unrelated to contamination. Early-web
personal pages have a *wildly* different surface from anything in the model's recent training
distribution while having obvious, legible human intent. If fit collapses there, the instrument is
reading familiarity rather than recoverability — which is precisely the E37 distinction between a
vocabulary deficit and a missing inversion, tested on real text.

---

## §7. Row 6 — model output under a rich, deliberate prompt *(nobody has built this)*

**This must be generated, and it is the pair that distinguishes this project from every detector
in existence.** SPEC §7: if the instrument cannot separate rows 6 and 7, it is an AI detector
wearing a theory.

The generation protocol matters more than the model. "Rich and deliberate" must mean *many
decisions by a human*, not *a long prompt*:

| id | protocol | what it isolates |
|---|---|---|
| R-1 | a real working document from this project, produced through many turns of human direction and revision | **the most honest available example** — the decisions are documented in git history |
| R-2 | a piece written to a detailed human-authored brief, then revised across ≥5 rounds of human critique | revision depth |
| R-3 | a piece where the human rejected ≥3 whole approaches before accepting one | rejected alternatives exist and are *real* |
| R-4 | a technical explainer written for one named person with stated constraints | audience = `specific_person`, richly specified |
| R-5 | a piece produced by a human who supplied their own research, structure, and examples | the model supplied prose only |
| R-6 | R-2's *first draft*, before any revision | **the internal control** — same model, same brief, no accumulated decisions |

**R-6 is the most valuable single artifact in this document.** It holds the model, the topic, and
the prompt fixed and varies only the accumulated human decision-making. If the instrument cannot
rank R-2 above R-6, §1's reframe has no empirical support, and that is a Gate 1 result rather than
a Gate 3 one.

**A conflict of interest to state out loud:** R-1 is a document whose maker is also the
instrument's author, scored by the instrument's author. It is the most convenient artifact
available and the least independent. Include it if you like the reflexivity, but it cannot be the
row's only entry, and its expected reading should be written by someone who did not write it — or
not written at all, and the artifact reported as uncalibrated.

---

## §8. Row 7 — model output under a thin, automated prompt

**Free.** RAID supplies 11 models × 4 decoding strategies × 12 adversarial attacks across all
eight domains, generated exactly this way.

| id | kind | note |
|---|---|---|
| T-1 | RAID generation, greedy decoding, no prompt engineering | the plainest case |
| T-2 | RAID generation of the *same* source item as an A-row artifact | holds topic fixed, varies provenance |
| T-3 | RAID generation under an adversarial paraphrase attack | tests that fit does not move under surface evasion — **evasion should not help here, and if it does, that is the arms race reappearing** |
| T-4 | a bulk-generated SEO page from the current era | the modern analogue of S-1; **row 3's shadow** |
| T-5 | a thin-prompted piece on the *same brief* as an R-row artifact | the direct rich-vs-thin pair |

**Curation note:** T-3 is the row's most valuable entry. The whole §1 argument is that you cannot
evade an intent probe by writing more like a human. T-3 is that claim's first contact with real
adversarial text, and a fit increase under paraphrase would be a serious result against the
project.

---

## §9. If seven is the budget, the seven that carry the most

Offered as a starting point to argue with, not a recommendation to accept.

| row | pick | why this one |
|---|---|---|
| 1 | **G-4** (well-written network item) | the uncomfortable case, not the easy one |
| 2 | **B-1** (technical post-mortem) | should be the highest-fit artifact in the set; if it is not, stop |
| 3 | **S-7** (long keyword-stuffed guide) | long *and* hollow — fires the depth-is-length falsifier immediately |
| 4 | **P-5** (10-K risk factors) | maximally decided, minimally legible |
| 5 | **A-6** (early-web personal page) | unfamiliar surface, obvious intent — the E37 distinction |
| 6 | **R-2** (heavily revised) | §1's whole claim |
| 7 | **R-6** (R-2's first draft) | the internal control that makes row 6 mean anything |

**Note what this costs:** row 7 is spent on R-6 rather than on a RAID item, because the R-2/R-6
pair is worth more at n=7 than a generic thin generation. T-3 and S-1 are the first two additions
if the budget stretches to nine — and T-3 in particular is a claim about the project's central
argument that will otherwise go untested until Gate 4.

---

## §10. What this document commits to

- Nothing is selected. This is the field.
- The expected readings do not exist yet and **must be written before any run** (§0).
- No artifact text enters the repository. Manifests carry hashes, offsets, and source
  identifiers only (SPEC §8).
- Rows 3 and 6 are hand-curated and cannot be sourced from an existing benchmark. Rows 5 and 7
  can. Row 1 comes from the DFRLab audit, not from live fetching (A-4).
- **The deferred rigor obligation from Gate 0 §6 still stands** and is not discharged by this
  document: the grooming corpus remains someone else's sample, and that blocks any prevalence
  claim until a fetcher exists and is used deliberately.
