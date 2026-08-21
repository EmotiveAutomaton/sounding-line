# The Phase 2.0 evaluation contract — G152, DRAFT v0.3 (amended 2026-08-21 under Phase 2.3)

**DRAFT — DO NOT FREEZE (2026-08-21).** The 2026-08-16 binary task is retained as a possible
downstream product layer, but it no longer defines the primary Phase 2 task. This file must be
reconciled with the Phase 2.3 reconstruction outputs (amendment v0.3 below) before curator
sign-off; there must be one active evaluation contract, never a binary contract and a process
contract that can disagree.

**Status: draft for the curator's sign-off. Nothing here binds until frozen; once frozen, no
result may change the task definition, splits, or success metric after scores are visible, and
the frozen version joins the hash-lock discipline.** Governing briefs:
[`PHASE_2_0_CONTEXT.md`](PHASE_2_0_CONTEXT.md) §§7, 8, 13 for the product layer;
[`PHASE_2_2_CONTEXT.md`](PHASE_2_2_CONTEXT.md) for the core representation. Theory groups
served: Decision Traces and Reader Heuristics (the instrument's task), Infrastructure (the
gate machinery).

**Amendment v0.2 (2026-08-19, Phase 2.2B — the representation replacement).** The core
representation of this program is the **trajectory reconstruction profile**
(`PHASE_2_2_CONTEXT.md` §9): reading identity, proximal reconstruction, trajectory
reconstruction, historical traces, anomaly profile, realization, validation status, and
claim boundary, every field declaring its input interface from §3b below. §1's binary
substantial-model-contribution question survives ONLY as a product-policy label emitted by
a separate classifier — it is no longer the primitive the program optimizes or the
ontology any battery adjudicates. The adjudication example set is unfrozen and superseded
as ontology (its file carries the ruling). No field trained or validated with process
metadata may appear in the final-artifact interface (§3b's rule, now doubly binding). A
provenance label and a reconstruction score are separate outputs, always.

**Amendment v0.3 (2026-08-21, Phase 2.3 — the process outputs).** The primary task is
restated: given an artifact, declared context, and a bounded reader interface, produce a
**calibrated reconstruction profile** that keeps viewer-coherent explanation,
reader-enactable process, historical-process correspondence, contribution-network
recovery, and abstention separate (`soundingline/reading_profile.py` and
`soundingline/process_record.py` implement the fields; the three process outputs are
defined in `docs/theory/THE_TRIPLE_INFERENCE.md` §2). Required outputs and their
known-answer ground truths:

| output | minimum representation | known-answer ground truth |
|---|---|---|
| `viewer_model` | ranked maker/process hypotheses plus evidence | reader calibration and held-out consequence, never plausibility alone |
| `reenactment_route` | ordered process candidate with prerequisites | successful recreation or withheld construction choice |
| `historical_process` | posterior or equivalence class over recorded events | version history, interaction logs, tool traces, or controlled construction |
| `contribution_network` | actor-role event graph | logged proposal, selection, ratification, veto, integration, repair, acceptance |
| `anomaly_trajectory` | access, origin, recognition, response, recurrence, integration | controlled anomaly histories and process records |
| `uncertainty` | calibrated confidence plus abstention reason | held-out calibration, per interface |
| `optional_provenance` | downstream binary or regime distribution | independently adjudicated regime labels, never inferred from the process score by definition |

Headline F1 is replaced as the primary by a panel (matched-candidate historical event
recovery; held-out process-fact prediction; reenactment success; actor-role and
dependency-edge recovery; per-field anomaly confusion; evidence localization;
calibration and selective risk per output; improvement over context-only, surface, and
no-generative-prior baselines; divergence between viewer coherence and historical
correspondence). No average across the panel produces an intent score. The freeze rule:
do not freeze until every field has at least one known-answer example, historical and
reenactment scoring can disagree without either being an error in the other, the
perceptual-access exception is represented, a generic secondary-goal guess earns no
credit, the binary layer is downstream and separately evaluated, and the curator signs
off on examples rather than an abstract rule. §§3 to 8 below (splits, calibration, hard
slices, claim tiers, baseline rule) survive unchanged and apply to every panel member.

## 1. The task (v0.1 binary form, retained as the OPTIONAL DOWNSTREAM PRODUCT LAYER only)

Binary decision, phrased exactly: **the probability that a generative model made a substantial
contribution to this artifact's final wording or structure.** Never "the author is AI."

**Substantial contribution (v0.1 policy).** Generated content materially determines final
wording or structure. Counts: direct generation; sentence-level rewriting; structural planning
that survives into the artifact; selection among model candidates where the selected wording
ships. Does not count: spellcheck, punctuation, casing, whitespace, citation formatting,
single-word synonym corrections accepted from a checker. No token-percentage threshold is the
construct; the policy is operationalized through the example set below.

**Adjudication examples (to be populated to >= 30 before freeze, 10 per band).** Three bands:
clear-positive, clear-negative, and adjudicated-hard (the band that trains the policy). Each
example carries the regime label, the process record that grounds it, and the ruling with one
sentence of reasoning. Hard-band seeds: a human outline expanded by a model then lightly
edited (positive); a model outline written out entirely by the human (negative — structure
alone without surviving wording is direction, not contribution, unless the structural planning
is the artifact's substance); grammar-tool rewrites of every sentence (positive once
sentence-level rewriting is systematic); translation by model of the author's own text
(positive, flagged as its own regime for reporting).

## 2. Authorship-regime taxonomy (training and evaluation resolution)

The eight regimes of the brief §8, verbatim in force: human; low-effort/templated human;
direct model generation; richly directed generation; human-to-model rewrite; model-to-human
revision; iterative mixed; incidental assistance. Binary collapse happens only at the
product-policy layer, version-stamped (`binary_policy: v0.1`). Mixed regimes retain degree and
revision-regime fields; supervision never erases process.

## 3. Metrics

**Primary (the frozen comparison):** pooled F1 at the benchmark's declared prevalence, on the
decisive held-out split (authors + domains + generator families held out together).

**Operational gate (co-primary, both must hold for "superior"):** true-positive rate at fixed
1% false-positive rate on human negatives, with the low-effort/templated human slice reported
separately — a gain that worsens low-effort-human false positives fails the gate regardless of
the headline.

**Secondary, all reported every run:** precision and recall separately; PR-AUC and ROC-AUC;
Brier score, expected calibration error, reliability plot; selective risk vs coverage when
abstention is on; worst-slice performance across the hard regimes; seed intervals (3 seeds
minimum on trained components, all reported, none dropped); runtime and cost per artifact.

**Decision-reader metrics (2.0D, independent of the detector):** candidate-choice accuracy vs
the measured floor; recovery beyond matched alternatives; evidence-span localization;
calibration; abstention quality on non-identifiable cases; transfer across artifact families.
No aggregate intent score substitutes for the tuple.

## 3b. Inference-input interfaces (added 2026-08-19, Phase 2.1.2; motivated by the L137 audit)

Three products, three input contracts. Every representation, feature block, and reader arm in
the program is annotated with its required inputs, and a representation may only serve an
interface whose inference inputs cover them. Drafts, deltas, prompts, and process records may
supply **training supervision, calibration targets, or ground truth** for any interface; they
enter **inference** only where listed.

| interface | inference inputs | claims it can carry |
|---|---|---|
| **I1 · final-artifact detector** (the public wedge, 2.0F–2.0H) | the final text, nothing else | provenance probability per §1; abstention |
| **I2 · paired-delta reader** (the 2.0D instrument) | old text + new text, delta stated explicitly | revision-purpose recovery; fabrication-bounded abstention |
| **I3 · process-aware authorship audit** (optional product, separate claims) | full process record: sources, drafts, deltas, interaction history | process-grounded contribution audit; never conflated with I1 performance |

**Standing assignments.** The 19-dimension change block reads both versions of a text: it
belongs to I2 and I3, and may serve I1 only as a training-time teacher or validation
instrument, never as an inference feature. The surface/statics leakage reference (L135) is an
I1 diagnostic. The G149 likelihood ruler is I3-shaped until a final-text form validates.

**Stacking preconditions (the four Phase 2.1 decision gates; 2.0F opens only when all four
hold on a repaired study):** (1) artifact-only recovery identifies realized, problem-directed
choices above a matched floor; (2) the effect transfers to the held-out model family; (3)
cheap length and surface baselines do not explain it; (4) evidence localization and abstention
behave correctly. Recorded responses, fixed now: recovery that works only with drafts or
deltas preserves I2/I3 and reconsiders the I1 wedge; only-surface-constraints recoverable
pauses the representation program for deeper exploratory work; a validated reader that adds no
conditional detector value keeps the capability claim and drops the public detector claim.

## 4. Split logic

- The decisive evaluation holds out **authors, domains, and generator families simultaneously**;
  diagnostic splits may isolate each shift source.
- All drafts, rewrites, paraphrases, and siblings of one source share a `lineage_id` and stay in
  one partition. Prompt templates and topic packages group when they can leak labels.
- Model versions recorded exactly; near-identical aliases are one family.
- Calibration data disjoint from test. The decisive comparison runs **once**, after thresholds
  and policies freeze. Later-discovered contamination triggers a dependency audit of every
  result that used the split (the PAN lesson, LESSONS §1d, applied to our own benchmark).

## 5. Baseline-selection rule (2.0E / G154)

The substrate is the **strongest reproducible methods current at the selection date**, recorded
with that date: (a) one strong trained detector representative of current competitive practice;
(b) one zero-shot/statistical method contributing distinct errors; (c) one surface-feature and
metadata reference that reveals leakage. If the strongest published method cannot be reproduced
from public materials, the exhausted routes are documented and the strongest reproducible
competitor stands — the finish line is never silently weakened, and a reproduction shortfall is
hunted as a defect first (LESSONS §1b applies in full).

## 6. Hard-regime slices (each reported separately, always)

Unseen generator family; unseen domain; unseen authors; human-to-model rewrite; model-to-human
reconstruction; richly-prompted-with-selection; low-effort human negatives; short texts (the
stratified short slice); distribution-shifted human writing where ethically sourced; benign
transformations (paraphrase, truncation, format shifts).

## 7. Claim language per outcome (fixed now)

| outcome | licensed language |
|---|---|
| headline + operational + hard-regime gates all clear | "improves the declared baseline on the frozen benchmark"; "superior" only with all three, named metrics and splits attached |
| decision reader validates, stack null | "the decision instrument recovers specified choices; complementarity to provenance detection is unsupported under tested conditions" |
| stack lifts in-domain only | no superiority claim of any kind; leakage investigation is the required next act |
| aggregate gain, low-effort-human FPR worsens | the stack is rejected or re-routed; no release under "superior" |
| reader fails known-answer gates | the representation is not an intent instrument; fusion stops; the claim reverts to §18.1 of the brief |

Forbidden claims stand as the brief §18.4 lists them, in full, for the whole phase.

## 8. Freeze checklist (empty until the freeze pass)

Data version + hashes · partitions · baselines + versions · primary metric + tie-breakers ·
binary policy version · threshold procedure · seed policy · exclusion/abstention rules · hard
slices · claim language. Frozen by: (curator sign-off pending) · sha256 of this file at freeze:
(pending) · date: (pending).
