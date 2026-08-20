# The adjudication example set — UNFROZEN, SUPERSEDED AS THE DECISION ONTOLOGY (2026-08-19)

**Resolution of the curator's flag.** He wrote same day: "Something seems fundamentally
wrong about this adjudication ask still" — and the Phase 2.2 brief
([`PHASE_2_2_CONTEXT.md`](PHASE_2_2_CONTEXT.md) §1) names the wrongness: binary
adjudication of who "made the decisions" was the wrong primitive question, not a
badly-drafted right one. The core representation is now the trajectory reconstruction
profile; the binary substantial-contribution label survives only as a product-policy
output at the classifier layer, never as the project's decision ontology.

**Status of this file: NEVER FREEZES. Retained whole as history** — the design that
exposed the wrong question — and its thirty cases keep one live use: historical stress
cases for the product-policy layer and hard-negative material for reconstruction
batteries. Do not expand it. The three policy lines it surfaced (systematicity, survival,
faithfulness) remain useful to the product label and are inherited there.

**What this is, in plain words.** The detector answers one question about a piece of
writing: "did an AI substantially help write this?" Before we tune anything toward that
label, the label itself has to be pinned down — otherwise, every time a result disappoints,
there is a quiet temptation to redefine what "counts" until it passes, and the whole
evaluation is worthless. Most cases need no discussion: an essay a model wrote is YES; a
2016 student essay is NO. The definition is actually decided at the borderline — spellcheck?
an AI outline the human wrote out in their own words? a human paraphrasing an AI draft
sentence by sentence? This document is thirty concrete cases with a ruling on each. The ten
borderline rulings ARE the definition.

**What the three groups below are.** Group A: ten obviously-AI cases (sanity anchors — if
the policy ever rules one of these NO, the policy is broken). Group B: ten obviously-human
cases (the same anchors from the other side). Group C: the ten borderline cases where
reasonable people could disagree — these are the only ones that need your judgment.

**What you actually do:** read Group C's ten rulings (five minutes). For any ruling that
reads wrong to you, say so — each disagreement moves the definition's line, I fold the
correction in, and then the definition freezes and every future test scores against it
unchanged. Groups A and B need only a skim. That is the entire ask.

Rulings use the contract's terms: POSITIVE = substantial model contribution to final wording
or structure; NEGATIVE = no substantial contribution (direction, spellcheck, and unexecuted
suggestion do not count). Examples marked HELD are real artifacts in our corpora; examples
marked CONSTRUCTED are specified on paper with the $0 local pipeline that would produce them.

## Group A — obviously AI-written (10 sanity anchors)

| # | example | regime | grounding | ruling |
|---|---|---|---|---|
| A1 | G153 thin-prompt essay, qwen family, any of the 120 | direct generation | HELD: `corpora/g153_pilot/qwen/*` with prompt, model, decoding, seed recorded | POSITIVE — every word is model output; the process record is total |
| A2 | G153 llama R3 rewrite of an ArgRewrite draft | human-to-model rewrite | HELD: `corpora/g153_pilot/llama/` rewrite cells, lineage-linked to the human draft | POSITIVE — the shipped wording is the model's even though the structure began human |
| A3 | G131 factorial essay, 8 instructions, interlocked | richly directed generation | HELD: `corpora/g131_factorial/*` with the instruction record | POSITIVE — rich human direction does not un-write the model's wording |
| A4 | G159 R+ instructed rewrite of a model base | iterative mixed (model-on-model) | HELD: `corpora/g159_rebuild/*` plus lineage to base | POSITIVE — twice-model; trivially inside the definition |
| A5 | A human outline (five bullet points) expanded to 600 words by a local model, shipped with light typo fixes | human-directed expansion | CONSTRUCTED: outline + `run_g153_local_gen.py`-style call, both recorded | POSITIVE — the contract's own hard-band seed resolved positive: surviving wording is the model's |
| A6 | Model translation of the author's own 500-word essay, shipped as the translation | translation | CONSTRUCTED: source text + translation call recorded | POSITIVE and flagged as its own regime for reporting, per contract §1 |
| A7 | A human selects the best of 4 model candidates and ships it unedited | selection among candidates | CONSTRUCTED: 4 candidates + selection recorded (the G129 candidate machinery generates this) | POSITIVE — selection among model wordings ships model wording |
| A8 | Grammar-tool rewrite applied to every sentence of a human essay | systematic sentence rewriting | CONSTRUCTED: ArgRewrite final + per-sentence local rewrite pass, diff recorded | POSITIVE once rewriting is systematic, per the contract's hard-band seed |
| A9 | A human writes 200 words, a model continues for 400, human trims the ending | iterative mixed | CONSTRUCTED: both segments + trim recorded | POSITIVE — the majority of shipped wording is model text and structurally load-bearing |
| A10 | Model-written conclusion paragraph appended to an otherwise human essay | partial generation | CONSTRUCTED: human body (ArgRewrite) + model conclusion, seam recorded | POSITIVE — a full structural unit of shipped wording is the model's |

## Group B — obviously human (10 sanity anchors)

| # | example | regime | grounding | ruling |
|---|---|---|---|---|
| B1 | ArgRewrite draft 1, any author | human | HELD: `corpora/public/argrewrite/` (2016-era, pre-LLM) | NEGATIVE — pre-LLM human process writing with revision records |
| B2 | ArgRewrite final draft after two human revision rounds | human, revised | HELD: same corpus, draft 3 | NEGATIVE — human revision of human text |
| B3 | A chapter from the 34-book corpus | human long-form | HELD: `corpora/store/` books (pre-LLM publication dates) | NEGATIVE — publication predates the technology |
| B4 | ScholaWrite preprint text with full keystroke process record | human, process-recorded | HELD: public ScholaWrite (its record shows human keystrokes) | NEGATIVE — the process record IS the evidence |
| B5 | A human essay run through a spellchecker (dozens of single-word corrections accepted) | incidental assistance | CONSTRUCTED: ArgRewrite final + recorded spellcheck diff | NEGATIVE — the contract excludes spellcheck explicitly |
| B6 | A human essay where the author asked a model "is my thesis clear?" and got "yes" | incidental assistance | CONSTRUCTED: query + reply recorded, zero text changed | NEGATIVE — consultation without contribution to wording or structure |
| B7 | A model outline (five bullets) that a human writes out entirely in their own words | model-directed human writing | CONSTRUCTED: outline + human text (curator-produced when needed) | NEGATIVE per the contract's hard-band seed — structure alone without surviving wording is direction, unless the outline is the artifact's substance |
| B8 | A human rewrite, from scratch and from memory, of a model draft read once the day before | model-inspired human writing | CONSTRUCTED: both texts recorded, no copying tool involved | NEGATIVE — influence without contribution; no model wording or structure survives verbatim |
| B9 | Templated business boilerplate filled in by a human (pre-2022 template) | low-effort/templated human | CONSTRUCTED from a pre-LLM template source (2.1.6 sourcing) | NEGATIVE — low decision density is not model contribution; the slice the operational gate protects |
| B10 | A timed 15-minute human response, no tools (the low-effort commission form) | low-effort human | CONSTRUCTED: the G133 commission machinery, tools-off attestation | NEGATIVE — effort is not the construct; provenance is |

## Group C — the borderline ten (the only group needing your judgment)

| # | example | regime | grounding | ruling + reasoning |
|---|---|---|---|---|
| C1 | Human essay; model suggests reordering two body paragraphs; human drags them | model structural edit | CONSTRUCTED: suggestion + diff recorded | **POSITIVE, narrowly** — structure materially changed by the model and the change ships; wording untouched. The v0.1 line: structural planning that survives counts |
| C2 | Same as C1 but the human rejects the reorder | unexecuted suggestion | CONSTRUCTED | **NEGATIVE** — an unexecuted suggestion contributes nothing to the artifact |
| C3 | Model fixes agreement errors in 3 of 40 sentences, wording otherwise human | light model copyedit | CONSTRUCTED: per-sentence diff | **NEGATIVE, at the boundary** — non-systematic, meaning-preserving corrections sit with spellcheck; systematic rewriting (A8) is the flip |
| C4 | Human writes every sentence, but the model chose the essay's five arguments from its list of twelve | model content selection | CONSTRUCTED: list + selection recorded | **POSITIVE, narrowly** — argument selection is structure; five of five load-bearing choices are the model's |
| C5 | Human paraphrases a model draft sentence-by-sentence with the draft on screen | close paraphrase | CONSTRUCTED: both texts + alignment | **POSITIVE** — sentence-level structure and argument order survive wholesale; this is rewriting the surface of a model artifact |
| C6 | Model-written title and section headings on a human body | furniture only | CONSTRUCTED | **NEGATIVE, at the boundary** — headings are wording but rarely the artifact's substance; flips POSITIVE where headings carry the argument (a listicle) |
| C7 | Human translates a model essay into their second language, loosely | model-to-human translation | CONSTRUCTED | **POSITIVE** — the argument structure is the model's; translation looseness does not launder provenance |
| C8 | A 50/50 collage: alternating human and model paragraphs, human-assembled | iterative mixed | CONSTRUCTED: per-paragraph provenance | **POSITIVE** — half the shipped wording is model text; degree recorded in the regime fields, binary collapses positive |
| C9 | Human dictates ideas aloud; model transcribes AND lightly cleans filler | transcription-plus | CONSTRUCTED: audio-equivalent source + cleaned text | **NEGATIVE, narrowly** — faithful transcription with filler removal contributes no wording the human did not speak; flips the moment the model restructures sentences (then it is A8's class) |
| C10 | The curator's own workflow: audio transcript → agent-drafted document → curator line edits | iterative mixed, high human direction | HELD in kind: this project's documents | **POSITIVE** — the shipped wording is substantially agent-drafted; direction and editing do not reduce the drafting below "substantial." Included deliberately so the policy is applied to ourselves |

## What the sign-off decides

The groups claim three policy lines, each carried by specific pairs: systematicity separates
copyedit from rewrite (C3 vs A8); survival separates suggestion from contribution (C1 vs C2,
B7 vs C4); and faithfulness separates transcription from drafting (C9 vs C10). If any ruling
above reads wrong to the curator, the disagreement names a policy line, the ruling flips at
sign-off, and the reasoning sentence is rewritten to carry the corrected line. The set
freezes with the contract; its sha256 joins the freeze checklist (mechanics in EVAL_CONTRACT_2_0.md §8).
