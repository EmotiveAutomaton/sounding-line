# The crossed provenance-decision benchmark — G153, design draft v0.1 (2026-08-16)

**Status: build blueprint for 2.0C. The normative contracts live in
[`PHASE_2_0_CONTEXT.md`](PHASE_2_0_CONTEXT.md) §11 (factorial axes, split rules, record schema)
and [`EVAL_CONTRACT_2_0.md`](EVAL_CONTRACT_2_0.md) (task, metrics, splits); this file adds only
the concrete construction plan and is superseded in place when the build lands.** Theory
groups: Decision Traces (the dose decomposition), Infrastructure (everything else). Data
acquisition is BLOCKED on two curator decisions: the generator budget (subagent survey in
flight, 2026-08-16) and human-corpus licensing for redistribution.

## 1. Cell structure, pilot scale

Eight regimes × 4 domains (essay/argument, narrative fiction, technical exposition, short
professional — one domain fully held out) × 3 length bins (short < 150 words, the stress
slice; medium 150-600; long > 600) × 4-6 generator families (>= 1 family fully held out).
Pilot target: ~2,500-4,000 artifacts, no cell below 30, hard slices oversampled. Full scale is
a separate later decision priced by the subagent survey.

## 2. The shortcut-breaking counterexamples (built by construction, not hoped for)

Quality-matched human/AI pairs (same brief, quality-scored, matched); low-decision human
(templates, timed low-effort commissions) against high-decision AI (rich prompting + selection
+ heavy human revision, process-recorded); identical source text pushed through different
transformation histories (one lineage, many regimes — the single strongest design element,
since it pins provenance while everything else varies); same generator across domains and
multiple generators within one domain; sibling artifacts grouped by `lineage_id` into one
partition, always.

## 3. Sources

**Human negatives (held already, licensing check owed before redistribution):** the 86-author
three-draft essay corpus (careful human + revision records); the 34-book corpus (long-form);
PAN-year human documents (licensing varies by year — audit); ScholaWrite (process-recorded
writing, leave-one-project-out by construction per L82); fresh low-effort negatives need
sourcing (templated business text, timed responses) — the one human class we do not hold.

**Positives and mixed regimes (generated in-house, process-recorded by construction):** every
generation logs prompt, model + exact version, decoding settings, candidates shown, selection,
and each revision pass — the process record IS the ground truth, which is the benchmark's
advantage over every scraped alternative. Local families: qwen3.5:9b and llama3.1:8b are the
two independent local lineages; **deepseek-r1:7b is architecturally a Qwen distill (verified
locally, 2026-08-16 subagent survey) and is recorded as qwen-lineage, never counted as an
independent family** — the family-alias rule of the brief §11.2 applied to our own shelf.
Frontier API families per the approved slate and the curator's budget ruling. Human-revision
regimes need human revisers: the curator (logged), plus commissioned revisers as a later
decision — the pilot can run with model-to-human cells thin, reported as thin, never padded.
**The survey's standing objection, adopted into the design: dollars are not the binding
constraint on this benchmark, human revision labor is (regimes 4 and 5 are 0% automatable);
simulating "the human" with a second model would make the central contrast synthetic and is
forbidden.**

## 3b. Acquisition plan (subagent survey, 2026-08-16; all prices/ToS fetched at source)

**Slate (7 lineages, 3 held out):** gpt-5.1, claude-sonnet-5, gemini-3.7-flash (paid, seen);
qwen3.5:9b local (seen); llama3.1:8b local, grok-4.3, deepseek-v4-flash (HELD OUT); plus a
small claude-opus-5/gpt-5.5 quality stratum. Held-out families differ in pretraining lineage,
not just vendor, and include one local family so unseen-family is not confounded with
deployment channel. API-family lineage independence is undisclosed and is stated as an
assumption in the preregistration.

**Budget (curator decisions pending):** pilot expected ~$57, envelope $120; full scale
expected ~$395, envelope $600 as a separate later decision. External API spend is its own
governance line, NOT gear 3. Free credits worth applying for: OpenAI Researcher Access
($1,000, quarterly review) and Anthropic AI for Science (up to $20,000) — either covers the
full benchmark; the pilot does not block on them.

**Binding ToS constraints, planned into the split design NOW:** (1) OpenAI's classifier
carve-out is conditioned on non-distribution of the trained model, so **OpenAI-generated
artifacts sit in test/calibration partitions only** if detector weights will ever be released
(the constraint and the generator-family holdout can be satisfied by the same partition if
planned now; planned later they conflict). Anthropic and Google assign output rights with no
distribution condition. (2) **Paid tiers only** — the Gemini free tier feeds prompts and
outputs back into training, contaminating the benchmark as a held-out artifact. (3) Released
text carries per-record provider terms in `provenance.license`; schema/prompts/metadata under
CC BY 4.0; no blanket CC0 on generated text.

**Mechanics folded into the pipeline build:** batch APIs everywhere offered (50% off;
DeepSeek off-peak halves again); results join by `custom_id`, never position (a positional
join is exactly how a rewrite gets attached to the wrong lineage); prompt-prefix caching
makes rich-direction candidates 2-4 nearly free; **decoding is RECORDED, not controlled**
(the newest Claude models accept no sampling parameters), so `decoding` is a per-provider
dict with a schema version, and local Ollama defaults are set explicitly, never inherited.

## 4. Decision-dose decomposition (never one number)

Recorded per artifact, from the process log: prompting level, selection events, ordering
choices, constraint-setting, local edits (count + span), structural revisions, acceptance
decisions. A compact dose variable may be derived for analysis; the components ship. Human
decision dose is not time, prompt length, turn count, quality, or authorship (brief §7.4).

## 5. Build order

1. Schema + manifest tooling (extends the §11.3 record schema; hashes, lineage keys, split
   assignment as code, not hand-lists).
2. Generation pipeline over local families first — free, proves the process-recording loop
   end to end on ~200 artifacts before any dollar is spent.
3. Frontier-family generation per the approved slate (BLOCKED: budget ruling).
4. Human-negative assembly + licensing audit; low-effort sourcing plan to the curator.
5. Split construction + leakage audit (the surface/metadata reference model from 2.0E doubles
   as the leakage detector here).
6. Data card + freeze per the evaluation contract.
