# Affect in text — what exists, and what family v3 is actually proposing

**Searched 2026-08-03**, at the curator's instruction: *"You're going to have to do a pretty decent
literature review if you want to align these to specific behaviours, because I'd imagine this has
been done at length. I'm wondering whether this is fertile ground for research even."*

**Short answer: it has been done at length, twice, on two adjacent problems — and not on this
one.** The gap is real. It is also narrower and more dangerous than I said this morning.

---

## §1. The headline

**No published mapping exists from Panksepp's primary-process systems to textual signatures.**
Searched from the affective-neuroscience side, the NLP side, the LLM side, and the personality-
measurement side. The systems are validated in behaviour, pharmacology and lesion work; the
instrument built on them (ANPS) is a **self-report questionnaire**, not a text measure.

So family v3 is not an application of existing work. That part of this morning's claim survives.

**But two mature literatures sit either side of it, and both say something uncomfortable about how
family v3 is currently built.**

---

## §2. What ANPS did — and the thing it did that I also did

The Affective Neuroscience Personality Scales operationalise **six** of the seven systems:
PLAY, SEEK, CARE, ANGER, FEAR, SADNESS. Meta-analysed across 21 studies, 10 languages, ~10,000
subjects, with clean Big Five convergence — Extraversion↔PLAY, Agreeableness↔CARE and inversely
ANGER, Openness↔SEEK, Emotional Stability inversely FEAR/SADNESS/ANGER.

**LUST is the one they dropped.**

That is worth putting plainly, because the curator overruled me for dropping it and I had assumed I
was being idiosyncratic. I was not — **I was reproducing the field's own convention**, and his
objection is therefore an objection to the field, not merely to me. It may still be right. It is a
bigger claim than either of us treated it as, and it should be argued on its merits rather than on
mine:

> Against the field: a self-report inventory drops LUST because *asking people about it* fails.
> That is a measurement-access problem, not evidence the system is absent from behaviour. The
> curator's mechanism — it shows in what an artifact bothers to **justify** — is precisely a route
> that does not depend on self-report.

That is a genuinely defensible position and it is now the strongest argument in this file.

---

## §3. The adjacent field that has already solved a version of this

**Implicit motive coding** — McClelland's power, achievement, affiliation — is the mature
literature the curator suspected existed. It coincidentally maps onto Panksepp:

| McClelland | nearest Panksepp | evidence |
|---|---|---|
| achievement | **SEEKING** | SEEKING is the appetitive/goal-pursuit system |
| affiliation | **CARE / PANIC-GRIEF** | affiliation is bonding plus separation-avoidance |
| power | **RAGE** | high implicit-power individuals show anger arousal to power stimuli |

Sixty years of work, and the automation history is the important part:

| approach | agreement with human coders |
|---|---|
| **marker-word / LIWC dictionaries** | **r ≈ 0.35 – 0.54** |
| **supervised transformers** (2020–2026) | **r ≈ 0.85**, 85% coder agreement, 99% faster |

**And the discriminant result, which is the one that matters here:** LIWC-based motive scores
correlated with *each other* up to **0.49**. The lexical approach could not keep three motives
apart.

---

## §4. What that says about stage E, and it is not comfortable

Stage E asks a language model to read an artifact and distribute points across eight affective
values, unsupervised, from a prompt.

**That is a marker-word-class instrument wearing a transformer's clothes.** It has no supervised
signal, no coder-agreement calibration, and no training on the construct. The 0.85 figure belongs
to models *fine-tuned on hand-coded protocols*. Nothing about family v3 is in that regime.

The realistic expectation is the 0.35–0.54 band — and, more importantly, **the 0.49 discriminant
failure.** The predicted failure mode is not that the probe reports no affect. It is that it
reports affect that does not separate: `seeking`, `care` and `fear` collapsing into one blurred
positive-engagement factor across every artifact.

**N-AFF does not catch that.** N-AFF checks flatness on no-maker artifacts. A probe whose eight
values are really two would sail through it.

So a second null is added, before any run:

> **N-AFF-2 (discriminant).** Across the corpus, the eight affective values must not collapse.
> Pairwise correlation of value weights across artifacts must stay below 0.6 for at least
> two-thirds of pairs. If the values only look distinct in the family file, the dimension is
> reporting one number under eight names.

That is directly modelled on the failure the implicit-motive literature already documented, which
is the whole reason to have read it.

---

## §5. The other adjacent field: appraisal theory in NLP

The live frontier in text emotion is the move **away from Ekman-style categories** toward
**cognitive appraisal dimensions** — self-consequences, consequences for others, situational
control — annotated at the appraisal level rather than the label level. There is recent work
assessing GPT-4's reliability at annotating appraisal ratings, and benchmarks testing LLM appraisal
reasoning.

**Two things follow.**

The field is moving in the same direction family v3 is: away from *what emotion is this* and toward
*what evaluation produced it*. That is convergent validity for the idea.

And there is a live alternative the project should not pretend it did not see: appraisal dimensions
are **continuous, fewer, and already have annotation protocols and LLM baselines**, where Panksepp
values are categorical, eight-way, and have neither. If N-AFF-2 fails, appraisal dimensions are the
successor to the successor.

---

## §6. What survives, for the review questions

**Q2 — the fear/grief boundary.** The literature does not settle it *for text*, but it does keep
them apart everywhere else: ANPS scores FEAR and SADNESS as separate validated scales that
correlate without merging, and both load inversely on Emotional Stability while remaining distinct.
**Keeping them separate is defensible.** What is not defensible is my current gloss, which has
`fear` carrying status-anxiety — a bonding concern, and therefore PANIC/GRIEF's territory, not
FEAR's. That gloss should move.

**Q4 — can lust be scored.** Nothing in the literature helps, because the field's own instrument
declined the question. The curator's justification-based signature is, as far as this search goes,
**novel**, and it is the one place here that could be a contribution rather than an application.

---

## §7. Is it fertile ground?

Yes, and more specifically than *"nobody has done it."*

The unclaimed position is: **primary-process affective systems, recovered from artifacts rather
than from self-report, as evidence about a maker rather than about a respondent.** The implicit-
motive field reads *narratives produced under an instruction to project*. This project reads
*artifacts made for other reasons entirely*. That is a different measurement problem and the
existing apparatus does not cover it.

The honest framing of the risk, and it is the same one this project keeps meeting: an
unsupervised LLM asked for an affective label will produce one. The literature has already
measured what that is worth without supervision, and the answer is *about 0.4*.

---

## Sources

- [Selected Principles of Pankseppian Affective Neuroscience](https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2018.01025/full)
- [Meta-analysis: primary emotional systems and Big Five](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8018956/)
- [A Brief Form of the Affective Neuroscience Personality Scales](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3406066/)
- [The future of the ANPS: seven pressing matters](https://www.cambridge.org/core/journals/personality-neuroscience/article/future-of-the-affective-neuroscience-personality-scales-a-reflection-on-seven-pressing-matters/470449DC7963968CFDD1B56797C115E9)
- [Are implicit motives revealed in mere words? Testing the marker-word hypothesis](https://pmc.ncbi.nlm.nih.gov/articles/PMC3797396/)
- [Motivational Computing: Transformer-Based Automation of Implicit Motive Coding](https://www.tandfonline.com/doi/full/10.1080/00223891.2026.2630930)
- [Automated coding of implicit motives: a machine-learning approach](https://link.springer.com/article/10.1007/s11031-020-09832-8)
- [Emotion Analysis in NLP: Trends, Gaps and Roadmap](https://arxiv.org/pdf/2403.01222)
- [Assessing the Reliability and Validity of GPT-4 in Annotating Emotion Appraisal Ratings](https://arxiv.org/pdf/2503.16883)
- [Implicit Motives — Schultheiss & Köllner](https://www.psych2.phil.uni-erlangen.de/~oschult/humanlab/publications/SchultheissKoellner_InPress_new.pdf)
- [LIWC-22 Drives documentation](https://docs.receptiviti.com/frameworks/drives)
