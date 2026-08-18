<p align="center">
  <img src="docs/assets/sounding-line.jpg" alt="A brass plumb bob and coiled line resting on an open bathymetric chart" width="100%">
</p>

<div align="center">
  <sub>◯ Ghost image and Readme. AI provenance is declared; the research question, evaluation criteria,
  interpretation, and claims are curator-owned. See <a href="#who-did-what">Who did what</a>.</sub>
</div>

# Sounding Line

**A research instrument for testing which of a maker's recorded choices remain recoverable from a
finished artifact.**

A sounding line is a weighted cord lowered into water to find the bottom, the oldest depth
instrument there is. It returns a reading when there is a bottom, and runs out of line when there
is none. That is the design contract here: bounded readings, declared refusal conditions, and a
record that keeps the failures beside the survivors.

The current result is narrower than the ambition. On a corpus of 86 student essays with revision
purposes recorded per sentence by trained annotators, a bounded reader shown only the revision
delta picked the recorded purpose from matched candidate sets at 0.477 against a verified 0.232
floor, on 616 events ([the pilot chain](results/arg_recovery/)). After matching revisions on
size, rarity, position, and difficulty, most of that margin proved to ride the matched
covariates; a smaller delta-specific remainder survived (8.2 points, exact McNemar p = 4.5e-4),
and the raised matched floor was later shown to be label composition, not hidden signal
([`results/arg_recovery/floor_decomp.json`](results/arg_recovery/floor_decomp.json)). A powered,
preregistered confirmatory battery is in the queue
([`prereg/g129.py`](prereg/g129.py)).

Three things this does not establish: it is not a general intent detector, it is not a reader of
anyone's values, and it is not a tool for judging a person or their work. Nothing in this
repository should be used on a real person's writing to make a decision about them.

## The current research question

Given declared context and a bounded candidate family, can a finished artifact identify a choice
the maker independently recorded, better than context alone and better than matched false
alternatives?

The unit is a **decision event**: a target, the live alternatives, the selected change, its
dependencies, and the context it was made under. Depth is not a scalar read off an artifact. It
is a proposed summary of recoverable problem-directed choice structure, conditional on domain,
brief, medium, constraints, and evidence quality, and it is only defined after event recovery
works. Every scalar formulation this project tried before that definition died to length,
register, or vocabulary, and the record says so.

## What is being built now

Sounding Line is not defined by AI detection. The current phase tests whether an independently
validated representation of decision structure adds information to a conventional binary
AI-provenance classifier. The classifier is the public wedge and remains a target, not an
achieved result. Decision recovery is validated first, because a detector score cannot validate
the representation that produced it.

The two programs stay distinct:

- **Core program:** recover specified parts of a maker's recorded decision process under bounded
  conditions, with known-answer gates before any real corpus.
- **Product wedge:** test whether that representation improves AI-provenance classification over
  strong reproduced baselines, on a benchmark that varies provenance and delegated human choice
  independently.
- **Current evidence:** the narrow choice-event result above, its controls, and one null: the
  first naive feature-layering attempt did not improve its style-change substrate and doubled its
  seed variance ([FINDINGS L125](FINDINGS.md)).
- **Longer program:** test whether cross-artifact residual structure can support inference about
  persistent motivational weighting. Untested on people, by design, until the lower layers hold.

Low recoverable depth does not mean AI authorship. Hurried, constrained, expert, routine,
collaborative, or translated human work may leave little recoverable evidence, and
machine-assisted work may carry rich human decision structure. Provenance and recoverability are
separate targets that may correlate in a dataset; neither defines the other.

## Why the reader is bounded, and when it must refuse

An open-ended language model asked why an artifact was made will produce a coherent answer for
anything, including sludge. Free-form intent attribution is confident fabrication with good
grammar. So this instrument only ever answers closed questions:

- The brief, candidate family, comparison set, and scoring rule are declared before evaluation.
- The target choice must be independently recorded by the maker, or known by construction.
- Context-only and matched-false-alternative controls run beside every claim arm.
- Shuffled-truth arms must read at chance, or the run is void.
- The reader must abstain when the evidence does not discriminate among candidates. A
  fabrication-rate arm (no-op deltas with an explicit "no revision was made" option) measures how
  often it invents decisions that were not made.
- Evidence about a choice is never evidence about a person's character, worth, or moral status.

Embodiment, expertise, constraint, and time cost motivate hypotheses about why traces differ
between makers. They are motivation, not a demonstrated mechanism, and the record does not treat
them as one.

## Three projects, three jobs

| Project | Current job | Current authority | Does not establish |
|---|---|---|---|
| **Sounding Line** (this repo) | Recover specified recorded decisions from real artifacts under bounded conditions | Its own datasets, controls, preregistrations, and replayable verdicts | General human intent or values |
| [**Ghost Scale Sim**](https://github.com/EmotiveAutomaton/ghost-scale-sim) | Test inference mechanisms in constructed worlds with known latent variables | Behavior of the implemented simulator | Human value recovery or embodiment |
| [**Art: A Unifying Model**](https://abrahamhaskins.org/art) | State the broader hypothesis that artifacts carry compressed decision and motivational structure | A theory and research program | An implemented or validated reader |

## Relation to developmental active inference

The bridge is a sequence of unbuilt interfaces, not an equivalence. Notation first, because the
collision is real: active-inference literature uses `C` for the preferred-outcome distribution;
Sounding Line's own theory uses `C` for context. Here, `C_AIF` always means the active-inference
preference object and `C_context` always means declared making conditions.

| Layer | Object | Current status |
|---|---|---|
| Proximal artifact reading | Evidence about a recorded choice or purpose | Narrowly tested here, one corpus, confirmatory battery queued |
| Longitudinal maker inference | A posterior over a persistent latent profile after conditioning on task, expertise, constraints, and state | Tested only in abstract constructed form in Ghost Scale Sim; not validated on people |
| Preference construction | A justified rule for using profile evidence to propose task-specific `C_AIF` | Not built |
| Normative adoption | A policy for whose inferred preferences influence an agent, under what trust, consent, and safety constraints | Not solved by inference |
| Embodied development | Learning across sensorimotor interaction and developmental stages | Outside the current software evidence |

A recoverable maker profile is not itself `C_AIF`. At most, calibrated profile evidence could
become one input to a separate process that constructs or updates task-specific preferred
outcomes. Inference does not determine adoption.

The long-range hypothesis, in restrained form: across multiple artifacts, after modeling proximal
goals, expertise, constraints, and temporary state, a persistent residual may support inference
about stable motivational weighting. That is an open hypothesis, not a current result.

<p align="center">
  <img src="docs/assets/visual-map.png" alt="Layered visual map of behavior selection: a latent preference field, an attention beam lifting the current proximal goal, an elastic expertise lattice, a habit layer, and the composed policy-propensity landscape whose peaks meet a selection plane where one behavior point is chosen among lower-likelihood alternatives" width="100%">
</p>

<div align="center">
  <sub>Notional map of the longer research program. It separates the latent preference field,
  attention lifting the current proximal goal, the expertise lattice, habit, and the composed
  policy-propensity surface a behavior is selected from. The reader's problem is inverting it
  from the selected point back down. None of the geometry shown here has been recovered from
  human data.</sub>
</div>

## Quick verification

Two commands, both cheap, both run from a clean environment before publishing them here.

```
python -m venv .venv
.venv/Scripts/pip install numpy        # Windows; use .venv/bin/pip elsewhere
.venv/Scripts/python runners/run_event_harness.py
```

This replays the event-recovery harness's five known-answer gates on synthetic ground truth
(runs in about a second):

```
40 makers x 12 events, maker-split train/test
  oracle     accuracy 0.796  (chance 0.25, n=240)
  shuffle    accuracy 0.225  (chance 0.25, n=240)
  unchanged  accuracy 0.282  (chance 0.25, n=1200)
  blind      accuracy 0.227  (chance 0.25, n=1200)
  >>> HARNESS-VALID
```

A reader with access beats chance; shuffled labels, unchanged passages, and a blinded reader all
fall to chance; decoys are picked symmetrically when there is nothing to read. Real-corpus
studies (the choice-recovery chain above) run through this same harness code and may not run
unless these gates pass. To inspect a committed real-text verdict without running anything:

```
python -m json.tool results/arg_recovery/matched_k4_recovery.json
```

Full model-side experiments need a local model server and hours of GPU time; they are queue work,
not a quickstart, and every runner opens with its own preregistration.

## Representative evidence

| Evidence | What survived | What it licenses |
|---|---|---|
| Recorded choice recovery ([`results/arg_recovery/`](results/arg_recovery/)) | 0.477 vs a verified 0.232 floor on 616 events; an 8.2-point delta-specific margin after covariate matching; the raised matched floor decomposed as label composition | The exact narrow claim in the opening, and nothing wider |
| Known-answer gating ([`results/event_harness/`](results/event_harness/)) | Five synthetic gates, including two catches of the harness's own build defects | Confidence that the ruler is validated before the signal, the project's standing rule |
| First detector-layering test (FINDINGS L125) | A preregistered null: naive late fusion of surface-change channels did not improve the style-change substrate and doubled seed variance | The first representation and fusion attempt added no usable signal; deeper fusion stays gated on validated decision recovery |
| Publication recreation ([FINDINGS](FINDINGS.md), L119 to L128) | Baker, Saxe and Tenenbaum Experiment 1 at printed precision on fourteen published values; a held-out 2025 style-change test gate matched at 0.8293 against a printed 0.830 on contamination-audited data | Implementation discipline at exact-value grade, not validation of the umbrella theory |
| Retired instruments (FINDINGS, known weaknesses) | Six criteria that could not fail their own data, caught by audit; every artifact-scalar measure dead to length, register, or vocabulary | The failure class the known-answer rule now guards against |

The recreation work also surfaced findings about the field itself: internal inconsistencies in
four of the five recreated works (at the base rate the meta-research literature predicts), a
shared-task recipe whose own augmentation leaked a sixth of its validation set, and an evaluation
metric whose shipped code contradicts its published description. These were checked by separate
AI-assisted adversarial verification passes within the project. That is internal review, not
external replication by an independent lab; no one outside this project has re-run these numbers.

## Current state and next gate

The recreation phase is closing: three anchors closed at the exact-value standard, the fourth
carries a complete Experiment 1 at printed precision, and the fifth has one of its three test
gates matched with the rest in the queue. The current phase's next gate is the preregistered
choice-recovery confirmatory battery: eight arms, exhaustive verdict bands, a declared cheap
baseline the reader must beat, and a fabrication-rate arm. Its verdict lands through the queue.

The full running record lives in [`docs/STATE.md`](docs/STATE.md) (operational state, standing
rulings, phase end states) and [`FINDINGS.md`](FINDINGS.md) (every study, how it was run, what
came back). The governing brief for the current phase is
[`docs/design/PHASE_2_0_CONTEXT.md`](docs/design/PHASE_2_0_CONTEXT.md).

## Theory map

[`docs/theory/`](docs/theory/) is the hypothesis store: over 130 numbered hypotheses, each
carrying its status and what would test it. Each file owns one question:

| | |
|---|---|
| [the triple inference](docs/theory/THE_TRIPLE_INFERENCE.md) | what is inferred: three target families at different timescales (proximal goal, process, persistent motivational organization) and what makes values identifiable at all |
| [three cognitive layers](docs/theory/THREE_COGNITIVE_LAYERS.md) | what architecture might support the inference, and the evidence from eleven model families |
| [decision traces](docs/theory/DECISION_TRACES.md) | what observable traces decisions leave: target, control, and terminal topology as independent axes |
| [reader heuristics](docs/theory/READER_HEURISTICS.md) | how a bounded reader finds and combines traces: priors, entry cues, calibration, refusal |
| [alignment](docs/theory/ALIGNMENT.md) | what objective should govern a system that can read them. Formally dormant, with a written wake condition |

## Repository map

| | |
|---|---|
| [`FINDINGS.md`](FINDINGS.md) | the method archive: every study, its numbers, its verdict |
| [`TODO.md`](TODO.md) | the live queue of studies, phase-ordered, same identifiers as the theory |
| [`docs/STATE.md`](docs/STATE.md) | operational state and standing rulings |
| [`docs/method/`](docs/method/) | lessons (trigger-indexed), controls, deviations, literature reviews |
| [`docs/design/`](docs/design/) | build blueprints, including the current phase brief and evaluation contract draft |
| [`docs/TOOLS.md`](docs/TOOLS.md) | instrument ledger, each tool with its validation state |
| [`prereg/`](prereg/) | preregistration cards, frozen before their runs |
| [`runners/`](runners/) | one file per experiment, each opening with its own preregistration |
| [`soundingline/`](soundingline/) | the analysis package: hypothesis family as data, probe schema, measures, locks |
| [`docs/sim/`](docs/sim/) | traffic with the parent simulation, both directions |
| [`run_first_gear.sh`](run_first_gear.sh) · [`run_second_gear.sh`](run_second_gear.sh) · [`runners/gear3.py`](runners/gear3.py) | queue engines: partial machine, whole machine, and rare cloud bursts behind hard spending guardrails |

## Who did what

The research question, the theory, the experimental criteria, all claim decisions, and final
scientific responsibility are the curator's (Abraham Haskins). Code generation, refactoring,
queue operation, adversarial checking, literature retrieval, and copy editing are largely done
by AI coding agents working under the repository's rules, with every landed result written
through a fixed hypothesis-method-verdict record. AI-assisted review passes are used
adversarially inside the project and are never represented as independent validation. The hero
image is AI-generated and is marked as such at the top of this file.

## Cautions

The instrument may not claim that a machine wrote something. It may not quote any one of its
quantities alone. It may not read low recoverability as low value: low recoverability is a joint
property of the artifact, the reader, and the declared conditions.

One curator, one primary reading model, English only, corpora biased by which sources permit
collection. No claim about prevalence, and none about any individual.

MIT licensed. Read [`docs/method/DEVIATIONS.md`](docs/method/DEVIATIONS.md) before quoting a
number.
