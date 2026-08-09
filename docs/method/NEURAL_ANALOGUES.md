# Neural analogues — what "activity" and "noise" may honestly mean for a transformer

**Subagent research report, 2026-08-09, digested.** Commissioned by the curator to ground the
"models never peak in the final layer" family of claims. Sources tagged READ (fetched and opened)
or SNIPPET per the standing rule; the full report with citations lives in the session task output
and the key items below carry their anchors.

## The two frame corrections, which change how §6-family claims must be worded

**1. The comparison is misaligned on both sides.** "Models never peak in the final layer" is a
claim about *decodability* (how well a readout recovers information); "salience/CEN/DMN bright
peaks" is a claim about *hemodynamic contrast* (metabolic/synaptic signal). Different kinds. The
legitimate common frame is **decoding**: our per-layer affect projections are the LLM twin of fMRI
MVPA — and affective neuroscience itself moved to MVPA because univariate bright-peaks failed for
emotion (READ: Kragel & LaBar 2016, TICS; READ: Lindquist et al. 2012, BBS — "little support for
the locationist view").

**2. Nothing in a dense transformer can "peak" in the energy sense.** Every block executes
identical FLOPs on every token; only representational content varies. "Which block is most active"
is ill-posed; "which block is most decodable" is well-posed.

## The vocabulary table

| human quantity | defensible LLM analogue | confidence · key source |
|---|---|---|
| MVPA decoding accuracy | per-block probe accuracy / concept-direction projection (what we compute) | READ · Kragel & LaBar 2016; Zou 2023 (RepE); Skean 2025 |
| LFP / synaptic input (what BOLD tracks) | the per-block residual **write** Δh = h_{l+1} − h_l, standardized — not the stream state | READ both halves · Logothetis 2001; Heimersheim & Turner 2023 |
| BOLD task contrast | between-condition difference of a per-block measure; **never raw norm** (norms grow ~1.045×/block; top activations are input-independent bias terms) | READ · Logothetis 2008; Sun 2024 |
| single-neuron firing rate | post-nonlinearity MLP unit / SAE feature (polysemanticity caveat) | READ Sun · SNIPPET Elhage 2022 |
| attention / precision (synaptic gain on prediction error) | softmax attention as Bayesian marginalization — **computational-level only, not mechanism** | READ, contested · Feldman & Friston 2010; Singh & Buckley 2023; contra Lindsay 2020, Jain & Wallace 2019 |
| prediction error / surprise | token surprisal −log p | READ, under attack · Schrimpf 2021; contra Oh & Schuler 2023, Antonello & Huth 2024 |
| trial-to-trial biophysical noise | **none at temperature 0.** Nearest: within-condition cross-stimulus variance; superposition interference | READ neuro side · Faisal 2008; Stein 2005 |
| physiological artifact (motion, vascular) | rogue dimensions / massive activations contaminating measures | READ · Timkey & van Schijndel 2021; Sun 2024 |
| neuromodulatory gain / arousal | temperature or global scaling — speculative, do not deploy | flagged, no source |

**Strongest attacks, one per analogy:** magnitude-as-activity — Sun 2024 (top activations are
fixed bias terms) plus the exponential depth confound; attention-as-attention — Lindsay 2020
(self-attention can implement a convolution; no limited-resource competition); surprisal — Oh &
Schuler 2023 (larger models fit reading times *worse*); probing peaks — Hewitt & Liang 2019
(accuracy reflects probe capacity without a selectivity control); the whole enterprise — Jonas &
Kording 2017 (the microprocessor lesion study).

## Three quantities our probe could compute per block (the actionable part)

1. **Standardized write norm** ‖z_{l+1} − z_l‖ — the analogue of what BOLD actually indexes
   (input/processing delta), in the standardized space that already neutralizes rogue dimensions.
   Exclude BOS/padding.
2. **Affect work** (z_{l+1} − z_l) · v̂_c — signed per-block push along each concept direction;
   dot product makes contributions **telescope exactly** to the final projection, an additive
   per-block decomposition. Nearly free from cached states.
3. **Per-block d′** — between-class mean projection difference over within-class SD, held-out:
   the population-neuroscience quantity, and the right normalizer for the early/late ratio, since
   raw cosines inherit each block's geometry.

Plus a QC alarm (share of top-3 dimensions in projection magnitude — the fMRI-artifact analogue)
and a naming rule: **say "contribution," never "activity," in write-ups**; call unexplained
within-class variance "unmodeled," never "noise" (variability may be signal — Stein 2005).

## The falsifier that applies to us today

Extraction choice systematically biases layer-wise conclusions (READ via mirror: Hadidi et al.
2025 — mean pooling included; untrained-transformer brain-predictivity fully accounted for by
positional signals and word rate). **Our `Reader.read` mean-pools. Every early/late profile claim
should be re-run under last-token and max pooling before it hardens** — queued as a falsifier arm.
