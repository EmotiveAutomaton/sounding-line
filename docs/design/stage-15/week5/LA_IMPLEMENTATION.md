# LA reader and continuation specification

Prospective supplement, November 7, 2026, to [LA](LA.md). The commissioned
pipeline is CPU-only and waits for a fully admissible AT2 reader selection.

## DESIGN CHECK

The native constructed fixture uses actual tiny CPU RoBERTa forwards. An
all-zero model has exactly zero before/after resolution; both arms retain the
same old token IDs after left cropping. A random tiny model reproduces in a
fresh process. Conditional positive, reversed and balanced-null worlds, and a
positive joining world, check the statistical paths. No human estimate was
used to choose these controls or the supplemental mappings below.

LA1's primary preparation combines AMI and ICSI, with corpus-specific textures.
AMI appears first operationally because its laughter is explicitly timed;
combining does not relabel ICSI metadata or double-count ICSI-plus transcripts.
Only completed previous dialogue acts enter context: an overlapping act's
unspoken tail cannot predict an earlier word. All preceding completed talk is
available to the causal tokenizer's fixed 1,024-token crop. Resolution compares
the previous five completed acts, with three/ten-act textures. Preparation
writes eight-act blocks incrementally, avoiding repeated full-meeting prefix
strings in memory. It supplies no outcome-fitted selection.

`week5_la_pipeline` has three operations. `prepare` consumes verified LA0 and
emits scored-row inputs or LA2 participant pairs. `score` requires one act block,
the pinned masked and causal manifests, and a verified AT2 selection root whose
`selection_admissible` is true. Every paired masked forward is independently
repeated, alongside exact causal token checks. Surprise is nats per lexical
word; resolution is mean nats per retained old token. `collect` requires every
declared block and tolerates at most 1% explicitly recorded unsupported reader
items, as amendment M permits. It emits raw-text-free private analysis rows.

`week5_la` fits LA1/LA2 with 2,000 meeting-cluster refits for primaries and 200
for screening. LA2 uses a pooled intercept model below twenty meetings rather
than the primary within-meeting transform. A single meeting still gets its
pooled point estimate, but cannot receive a fabricated cluster interval.
Metadata absence, zero-event pairs, unidentifiable contrasts and failed draws
remain explicit. The first LA2 contrast is AMI native language; ICSI English
variety and region are separate descriptive replications of their own constructs.

Own-laugh and other-laugh preparations implement LA1.s. Others-only is also an
unconditional declared texture. `week5_la_followup` implements LA1.i after the
surprise route: compare current-minus-next-act surprisal across matched laughed
and nonlaughed acts, controlling current surprise and the original matched
strata. The next act starts after the current act ends. Controlling current
surprise prevents the arithmetic subtraction itself from manufacturing an
effect. Its analyst-declared practical scale is 0.01 nats/word; it is a separate
descriptive branch and never upgrades the parent's primary.

Model scoring uses eight-act blocks with a 600-second execute target to leave
room for full fresh paired verification within the 30-minute batch quantum.
Measured native accounting includes both readers' cold loads. The first 5%
in-slot pilot, subsequent sample/doubling route and family continuation follow
the packet and owner runtime; unscored or unbuilt dependencies do not occupy a
research slot or count as executable buffer capacity.
# Metadata-only sample route

`week5_la_scope` projects whole meetings before scoring, stratified by corpus
using Hamilton allocation and seed 20261102. It retains every act, laugh and
speaker metadata record in each chosen meeting. A measured cost pilot sets
the count; no laugh or model outcome selects the sample. Its source-shaped
output feeds the unchanged preparation pipeline. Downstream records disclose
the meeting count, full count and share; below twenty meetings uses the
already declared descriptive fallback. Native source projection and full
2,000-draw LA1/LA2 primary and companion handlers have executed and replayed
in separate processes on constructed inputs.

