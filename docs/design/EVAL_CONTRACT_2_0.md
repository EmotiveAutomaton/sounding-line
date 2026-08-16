# The Phase 2.0 evaluation contract — G152, DRAFT v0.1 (2026-08-16, NOT YET FROZEN)

**Status: draft for the curator's sign-off. Nothing here binds until frozen; once frozen, no
result may change the task definition, splits, or success metric after scores are visible, and
the frozen version joins the hash-lock discipline.** Governing brief:
[`PHASE_2_0_CONTEXT.md`](PHASE_2_0_CONTEXT.md) §§7, 8, 13. Theory groups served: Decision
Traces and Reader Heuristics (the instrument's task), Infrastructure (the gate machinery).

## 1. The task

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
