# Source review for the extensive local research program

**Analyst research record, September 23, 2026.** Supports the
[proposed program](STAGE12_LOCAL_RESEARCH_PROGRAM.md); no scientific execution or
theory change follows from this review. READ below means the named portions of
the primary source were fetched and inspected, not that the entire paper was
read. Abstract/search-only pointers are not used as evidence. This is a targeted
exploratory review, not an exhaustive novelty search or a systematic meta-analysis.

## Theory and existing evidence read before comparison

The initial complete theory read is retained in the private continuity record.
For this planning task, relevant sections and their correction history were
reread: Reader Heuristics §1 and §§4–7/10; The Triple Inference §§1/2/7; Decision
Traces §§1/6; Three Cognitive Layers §§3/8; the theory index. The context,
common-cause and identifiability passages were reread after external research.
The program keeps the curator's distinction between supported historical
reconstruction and a reader-enactable route, between domain expertise and
realized process, and between directed attention and warranted belief.

Local primary records: FINDINGS L434–L436 and the completed local/failed cloud
closeouts; the original Stage 12 commission; addendum proposal and implementation
freeze; current scoped operation/access consumers; shared-source and expertise
handoffs; method LESSONS §§3–5 and relevant CONTROLS. Fresh feasibility checks
inspect raw timing, ARIES exclusions, the existing CoAuthor census, strict
ScholaWrite extraction, realization audits and cached reader availability.
No old result is rerun, reclassified or replaced by this plan.

## Primary literature and the test each source changes

### R1. Intrinsic correction can fail without an independent check

[Large Language Models Cannot Self-Correct Reasoning Yet, ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/file/8b4add8b0aa8749d80a34ca5d941c355-Paper-Conference.pdf).
**READ:** correction-method comparisons in §3.2–3.3 and limitations/discussion
in §§5–7. Their tested reasoning settings distinguish intrinsic revision from
feedback that supplies information about correctness. Prompt and stopping
details can make apparently comparable correction protocols different.
**Limit:** this is not a theorem that all revision fails, or a test of our
maker-history interfaces. **Design consequence:** LP04 keeps later evidence and
saved/fresh contexts paired; LP06 distinguishes additional evidence from
repetition. Correction/damage and total attempts both remain visible.
**Prior art:** correction comparisons are established; our extension is the
within-history frame cross with source-known later targets.

### R2. Independent verification can reduce answer contamination

[Chain-of-Verification Reduces Hallucination in Large Language Models](https://arxiv.org/html/2309.11495v2).
**READ:** §3's joint, two-step and factored verification designs, and the opening
experimental setup/results in §4. The verification questions can be answered
without showing the original draft; precision improvements must be interpreted
with the number of facts produced.
**Limit:** large-model factual question answering is not process reconstruction,
and an independent model response is not an exact verifier. **Design consequence:**
LP19 separates planning, independent checking and revision, with public executable
checks; all packets pair correctness with useful yield.
**Prior art:** factored verification exists. No claim to reproduce its published
gains on the local model is made.

### R3. A positive counterexample to blanket correction pessimism

[Large Language Models Can Self-Correct with Key Condition Verification, EMNLP 2024](https://aclanthology.org/2024.emnlp-main.714.pdf).
**READ:** §4 verification method and §5.1 evaluation setup. Recovering a masked
condition provides a verification task distinct from merely reconsidering the
same answer. Some settings have exact checks; open answers require additional
judgment and can admit multiple valid forms.
**Limit:** agreement with a recovered condition need not prove the full reasoning
correct. **Design consequence:** LP19 requires source-valid, independently
checkable constraints; LP06's reference distinguishes repeated evidence from new
information. A failed intrinsic correction result does not retire verification.
**Prior art:** use the mechanism as a discriminating control, not as a guaranteed
repair or a newly invented technique.

### R4. Sticking with one's answer and following contrary advice can coexist

[Competing biases underlie overconfidence and underconfidence in LLMs, Nature Machine Intelligence, 2026](https://www.nature.com/articles/s42256-026-01217-9).
**READ:** results on initial-answer visibility, advice and attributed ownership;
discussion and experimental-method portions. The study manipulates whether the
earlier answer is shown, how advice relates to it, and who supposedly gave it.
It finds separable response tendencies rather than one uniform resistance to
correction. **Limit:** stated advisor accuracy is manipulated, and confidence
uses model probabilities; our verbal probability output is a different instrument.
**Design consequence:** LP05 crosses answer content, confidence and claimed
ownership; LP09 separately tests a declared, checkable reliability channel.
**Prior art:** these biases are already studied. Our question is whether their
separation explains errors in bounded maker reconstruction under known evidence.

### R5. Evidence availability and evidence use are different

[Lost in the Middle: How Language Models Use Long Contexts, TACL 2024](https://arxiv.org/html/2307.03172v3).
**READ:** abstract and opening controlled-position design description for
multi-document question answering and key-value retrieval. Useful information
can be harder to use at some positions despite being inside the context.
**Limit:** those tasks and context lengths do not establish a universal positional
law for our 8,192-token package. **Design consequence:** LP01 moves identical
evidence without changing its reference; LP10 compares raw access, indexed
retrieval and representation changes separately.
**Prior art:** position sensitivity is established. The local test is a ruler and
an alternative explanation for apparent account quality.

### R6. Seeking counterexamples needs a falsifiable ruler too

[Failing to Falsify, 2026 preprint](https://arxiv.org/html/2604.02485v1).
**READ:** task/design discussion, the described numeric-rule exploration,
Appendix C implementation and Appendix H auditing portions. Its prompts and
task examine confirmation-oriented versus falsifying exploration.
**Limit:** parts of the evaluation use model interpretation/code conversion;
invalid-format resampling is not the same as our all-attempt accounting.
Negating a hypothesis also need not maximize information.
**Design consequence:** LP07 compares neutral/counterexample instructions using
exact existing-world query values, random choice and an information reference;
LP08 distinguishes asking from knowing when to stop.
**Prior art:** exploratory bias is not a new claim. The proposed local test
removes model-judge dependence and separates inquiry quality from later use.

### R7. A good question and an eventual correct answer are different outcomes

[Guessing Game, EMNLP 2025](https://aclanthology.org/2025.emnlp-main.876.pdf).
**READ:** §3 method, §4.1 setup and the discussed metric limitations. The
interactive setting measures questioning and task success, while interpretation
and the candidate knowledge base constrain what its information measures mean.
**Limit:** question count among successes can conceal failed episodes, and an
open-language interpreter is not exact ground truth.
**Design consequence:** LP07 reports information gain, redundancy, later forecast
quality and cost on all attempts. LP08 uses declared decision costs and known
worthwhile/unworthwhile queries. The exact selector is explicitly privileged.
**Prior art:** active-question evaluation is established; our extension is a
source-known maker task with matched option nuisance controls.

### R8. A stated rationale is not evidence of its own causal role

[Reasoning Models Don't Always Say What They Think, 2025](https://arxiv.org/html/2505.05410v1).
**READ:** introductory experimental findings and §2 intervention methodology.
Hints can change answers without being acknowledged in the generated reasoning.
The design distinguishes answer influence from reporting that influence.
**Limit:** disclosed reasons do not establish the full internal cause, and pairs
selected for answer changes need a different denominator from all attempts.
**Design consequence:** LP05 treats ownership labels as interventions, not genuine
memory; LP14 and LP18 score independently witnessed traces rather than an account's
self-description. Repeat controls and full denominators remain.
**Prior art:** rationale faithfulness has an existing literature; this program
does not use a coherent explanation as proof of a recovered historical process.

### R9. Remembering, updating and retrieving require different tests

[LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory, ICLR 2025](https://arxiv.org/html/2410.10813v2).
**READ:** introduction and benchmark/control design passages, plus memory-schema
discussion. Its distinctions include extraction, combining sessions, temporal
reasoning, updates and abstention; storage and retrieval design matter.
**Limit:** benchmark histories can far exceed our local context allowance.
**Design consequence:** LP10 acquires representations before unseen questions;
LP11 separates own-maker familiarity from generic examples; LP16 keeps history
strictly earlier and respects dependency. External text memory is not a hidden
persistent model state.
**Prior art:** memory evaluation exists. Borrow distinctions, not the whole
benchmark or unsupported comparability claims.

### R10. Proper scoring keeps confidence distinct from ranking

[Gneiting and Raftery, Strictly Proper Scoring Rules, Prediction, and Estimation, 2007](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf).
**READ:** categorical scoring formulation and quadratic/logarithmic examples
in §3. Proper scores reward honest distributions in expectation, whereas pair
ordering alone does not determine probability quality.
**Limit:** propriety presumes the stated target; a human annotation is not a
distribution over hidden mental truth.
**Design consequence:** LP03 retains both ranking and the existing expected
half-Brier loss, irreducible reference floor, invalid penalties and infinite
loss flags. Abstention is reported alongside coverage, not as free improvement.
**Prior art:** the mathematics is established. We are validating its use in this
instrument, not introducing a new scoring rule or fitting to favorable outcomes.

### R11. Belief and goal inference is conditional on the decision model

[Baker, Saxe and Tenenbaum, Bayesian Theory of Mind, 2011](https://web.mit.edu/9.s915/www/classes/theoryOfMind.pdf).
**READ:** abstract, introduction and formal-framework description. Joint inference
over beliefs and desires is posed through a declared decision process.
**Limit:** simple controlled action settings and a specified planner do not make
arbitrary artifact histories identifiable or establish a human mechanism in an LLM.
**Design consequence:** LP09 conditions on known source reliability; LP11 separates
experience sources; LP12–14 retain incomplete candidate support and observational
equivalence instead of forcing one historical story.
**Prior art:** inverse planning is occupied ground. The research opportunity is
to test which additional traces/constraints make our bounded reconstruction useful.

### R12. What could have been chosen changes what an artifact tells us

[Hurwitz, Brady and Schachner, Detecting Social Transmission in the Design of Artifacts, 2019](https://bradylab.ucsd.edu/pdfs/HurwitzBradySchachner2019.pdf).
**READ:** portions comparing available materials/functional constraints and
alternative explanations, and the discussion of their inference implications.
**Limit:** these artifact judgments do not establish general recovery of makers'
values or validate our model readers.
**Design consequence:** LP13 preserves alternative historical routes; LP18 checks
realization; LP19 changes available actions and purpose only with native support.
Choice relative to constraint is the target, not mere feature count.
**Prior art:** inferring social/process information from artifact design is not
new. More complete controlled transfer and witnessed-path tests remain local aims.

### R13. ARIES labels have a specific evidential scope

[ARIES: A Corpus of Scientific Paper Edits Made in Response to Peer Reviews, 2024](https://arxiv.org/html/2306.12587v2).
**READ:** annotation and task setup in §§4.1–5.1, including the beginning of the
experimental results. Annotators have richer document/response access than a
restricted supplied-pair reader. Silver matching offers positive examples but
does not make every unlabeled pair negative; lexical retrieval is a real rival.
**Limit:** request/edit correspondence is not private purpose, author adoption,
natural class prevalence or successful edit generation.
**Design consequence:** LP15 uses explicit negatives, source-bound context,
paper weighting and matched lexical controls. New local papers are separated
from globally untouched evidence.
**Prior art:** annotation and correspondence tasks are established. Our controlled
evidence/formulation comparison is a diagnostic extension.

### R14. ScholaWrite records support bounded temporal questions

[ScholaWrite, official dataset card](https://huggingface.co/datasets/minnesotanlp/scholawrite).
**READ:** fields, splits, collection, annotation, public filtering, limitations
and use restrictions. Visible editor states and project-scoped authors are
recorded; annotators assign labels across consecutive spans. Public filtering
removes several kinds of event, including artifacts and multilabel records.
**Limit:** the next released event is not necessarily the next physical keystroke;
many adjacent labels share one annotation span. Five projects remain a small
population. Existing terms prohibit redistribution and reverse identification.
**Design consequence:** LP17 requires exact continuity, keeps gap exclusions,
tests persistence and boundary transitions, and reports only permitted aggregates.
**Prior art:** the dataset already supports writing-process modeling. No new
human-intention ground truth is asserted.

### R15. Agreement with advice can be an alternative to evidence use

[Towards Understanding Sycophancy in Language Models](https://arxiv.org/html/2310.13548v4).
**READ:** introductory design/model scope and answer-influence examples in §3.2.
Agreement with user views can influence outputs in the studied assistants.
**Limit:** this does not identify the same mechanism in every model or establish
that agreement with correct advice is harmful.
**Design consequence:** LP05 and LP09 cross correctness and provenance/reliability;
they do not label every change “sycophancy” or every refusal “good calibration.”
**Prior art:** social agreement effects are established. The useful local
comparison asks whether warranted updating survives misleading advice.

## What this review leaves open

The review does not identify a published evaluation combining all of the planned
source-known revision, evidence-dependence, question selection, memory transfer
and witnessed-process controls. That is a bounded search result, not proof of
novelty. The individual methods have substantial prior art.

Local inference on exposed human records can reveal failure modes and improve
the instrument. It cannot create new independent writers or supply unavailable
private-goal labels. New mechanism claims still need native constructed support;
human generalization needs appropriate independent human evidence. These limits
direct which discriminating tests to build; they do not replace the curator's
larger research question with a smaller one.
