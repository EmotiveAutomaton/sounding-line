# Gate 0 — the literature, actually checked

**Status: passed, with one required amendment to the spec.**

`SOUNDING_LINE_SPEC.md` §6 states its own caveat plainly: *"this is three search rounds, not a
literature review. A proper one is milestone zero, before a line of code."* This document is that
milestone. It was written before any Sounding Line code existed, and the repository's first commit
contains it.

The gate's honest options were **continue, redesign, or stop**. The verdict is **continue** — but
one claim in §6 does not survive contact with the literature, and the architecture's novelty
statement has to move. That amendment is §2 below and it is the most important thing in this
document.

---

## 1. What the gate was asking

§6 made three claims about the field. Each is checked here against sources, and each gets a verdict.

| § 6's claim | verdict |
|---|---|
| AI-text detection is a solved-and-failing field | **confirmed, and more strongly than §6 knew** |
| Intent inference exists, but only about *users in interactive settings* | **partly wrong — see §2** |
| Artifact-level author-intent reconstruction as a corpus instrument is unoccupied | **confirmed** |

---

## 2. The amendment: bounded-family Bayesian inversion is already published

**§6 said intent inference is "all about user intent in interactive settings." That is not
accurate, and the inaccuracy is load-bearing.**

[AutoToM (arXiv 2502.15676)](https://arxiv.org/abs/2502.15676) is architecturally the same machine
the spec describes in §2 and §3. It proposes an initial agent model, performs **automated Bayesian
inverse planning** over it with an LLM backend, and — this is the part that matters —
*"iteratively refines the model by introducing additional mental variables and/or incorporating more
timesteps,"* **guided by inference uncertainty**. Its hypothesis-sampling module *"leverages an LLM
to propose only a small set of quality hypotheses for each latent variable."*

Read those two sentences against the spec:

- "a small set of quality hypotheses per latent variable" **is** §4's bounded hypothesis family.
- "iteratively refines, guided by inference uncertainty" **is** §3's loop-not-chain.
- It even reports *"human-like confidence estimates"*, which is adjacent to §5's convergence.

The same shape appears in [LLM-augmented inverse planning
(2507.03682)](https://arxiv.org/abs/2507.03682), which explicitly uses an LLM to generate hypotheses
and likelihoods while a Bayesian inverse-planning model computes posteriors, and in
[hypothesis-driven Theory-of-Mind reasoning (2502.11881)](https://arxiv.org/pdf/2502.11881). The
lineage runs back through [NIPE (2306.14325)](https://arxiv.org/pdf/2306.14325) and
[language-augmented Bayesian ToM (2408.12022)](https://arxiv.org/pdf/2408.12022).

### What survives

**All of this work inverts an agent acting in a scenario. None of it inverts an artifact to recover
its maker.** The observable in every case is a trajectory — an agent moving, choosing, speaking in a
dialogue — and the latent is that agent's belief or goal *at a point in time*. Sounding Line's
observable is a finished object with no trajectory, and its latent is a maker-state that has to be
recovered from the object's structure alone. §2's non-invertibility argument — a many-to-one map from
maker-states to surfaces — has no counterpart in the ToM literature, because in the ToM setting the
map is assumed invertible and the question is only how expensively.

### What the project may no longer claim

**"Bounded hypothesis family plus Bayesian inversion" is not novel and must not be presented as
novel.** It is prior art with a name, a benchmark record, and an implementation. Claiming it would
be the first thing a reviewer kills, and correctly.

The contribution is the **object** and the **measurement**:

1. artifact → maker-state, where no trajectory exists to invert;
2. a bounded family that is **human-shaped by construction** (§4) rather than scenario-derived,
   with the boundedness itself as the mechanism (§2);
3. **non-invertibility as a measured quantity** — the wall (E37) — rather than a failure to be
   engineered around;
4. the corpus application (§10 Gate 5), which is unoccupied (see §5).

### What the project gains

A validated method to borrow rather than invent, and a baseline family that is stronger than "a
model asked why was this made." AutoToM's model-adjustment loop is a better-specified version of
§3's recursion and should be read properly before `loop/` is written.

### Consequence for the gates

**Gate 3 — the boundedness ablation — is promoted from a check to the headline experiment.** With
bounded inversion already published, the ablation *bounded-vs-unbounded on artifacts* is the load-
bearing claim that is not already someone else's. §7 already called it "the ablation that decides
whether any of this is a contribution." That was right; it is now also the ablation that decides
whether the contribution is *distinguishable*. The free-form arm runs from Gate 1 in parallel, not
as a later ablation.

---

## 3. Detection is failing, and the failure is E57 published independently

§6's read was correct and the evidence is stronger than it cited.

**Adversarial paraphrase defeats detectors wholesale.** [Adversarial Paraphrasing
(2506.07001)](https://arxiv.org/abs/2506.07001) is a *training-free* attack that humanizes any
AI-generated text by paraphrasing under the guidance of a detector. Against eight detectors across
three categories it achieves an **average true-positive-rate reduction of 87.88%** with minimal
quality degradation. Earlier, DIPPER degraded watermarking and DetectGPT by **52.8%** and **65.7%**
respectively.

**Benchmark accuracy and real-world reliability have come apart.** [Why AI-Generated Text Detection
Fails (2603.23146)](https://arxiv.org/html/2603.23146v2) finds models achieving near-state-of-the-art
benchmark performance while failing under cross-domain and cross-generator evaluation, with feature
importance varying across generators and datasets. [A survey on detector robustness
(MDPI 13/13/2145)](https://www.mdpi.com/2227-7390/13/13/2145) describes a **dichotomy of performance
versus resilience**. [Paraphrasing-attack resilience
(2605.14240)](https://arxiv.org/abs/2605.14240) and [MASH (2601.08564)](https://arxiv.org/pdf/2601.08564)
extend the picture.

**This is E57, arrived at independently.** The simulation's E57 found that once content adapts, the
false-alarm rate stops falling and peaks at **65% of careful human work**; E57b found a stale
detector stops discriminating without stopping accusing. The published literature reports the same
structure from the other direction. Cite this as a coherence check, exactly as §6 recommends —
**and do not overstate it.** E57 is a simulation of a mechanism; these are measurements of real
systems. They agree in shape. That is all that may be claimed.

**The conflation §6 warned about is real and should be pre-empted in writing.** DetectGPT and
Binoculars measure token-prediction consistency under perturbation. That is a surface-statistical
property *of the generator*. Intent-attribution consistency is a different object. A reviewer will
conflate them; §7's baseline table already contains the experiment that separates them.

---

## 4. The convergence measure already exists, and its cost is a design constraint

§5's **Convergence** — "agreement across independent reconstructions — different chunks, orderings,
seeds, framings" — is a known method under two names.

- **SelfCheckGPT** samples multiple outputs and measures disagreement/contradiction, on the
  intuition that knowledgeable generations are more self-consistent.
- **Semantic entropy** computes entropy over semantic-equivalence classes of sampled generations,
  and generalises to unseen questions.

Surveys of the 2026 state of the art treat both as mature ([uncertainty-quantification suite,
2504.19254](https://arxiv.org/pdf/2504.19254); [semantic entropy in RAG,
2505.07528](https://arxiv.org/pdf/2505.07528)).

**Two consequences, one good and one expensive.**

*Good:* the novelty statement is clean and narrow. Everyone measures semantic entropy over **factual
claims**. Sounding Line measures it over **intent attributions**. E2's central finding — confident
mutual disagreement on hollow content — is exactly that quantity, and E20 already predicts where it
peaks along the readability axis (~a tenth readable). That is a pre-existing, pre-registered
prediction about a measure the field already trusts, which is a considerably better position than
inventing a measure.

*Expensive:* the field's own assessment is that [consistency sampling's cost scales with every extra
generation, making it better suited to pre-deployment evaluation than high-volume production
scoring](https://www.braintrust.dev/articles/best-hallucination-detection-tools-2026). Sounding
Line's cost is worse than the general case, because each sample is not one generation but a **loop
run to convergence**. Total cost per artifact is `k samples × loop iterations × model calls`.

**This must be priced at Gate 1, not discovered at Gate 5.** §10's "do not pay for compute before
Gate 4 comes back clean" is preserved by the hybrid-probe decision (D-6 below): a local quantised
model carries the convergence sampling, and an API model provides a quality reference on a held-out
slice.

---

## 5. The corpus application is unoccupied

Searches for author-intent or communicative-intent scoring as a **pretraining data filter** return
nothing on the axis this project proposes. What exists is quality filtering: bucketing crawled pages
by quality score, up-sampling high and discarding low; multi-stage dedup, cleaning, language ID and
quality filtering as the standard pipeline. The definition of quality is itself a value judgement
made by a model, as §6 notes.

**Scoring the inferred *author* rather than the *text* is a different axis, and it is open.** This
is Gate 5 and it remains the project's largest claim.

---

## 6. The corpus problem is much smaller than §7 assumed

§7's table asked for seven corpora. Most are already built by other people, which removes both cost
and — critically — most of §8's attack surface for the first two gates.

| §7 row | source | status |
|---|---|---|
| pre-2020 archived text | [RAID](https://arxiv.org/html/2405.07940v1) — all human text published pre-2022 | **free** |
| personal blogs, forum long-posts | RAID (reddit, wikipedia, news, books, poetry, recipes; 11 genres) | **free** |
| model output, thin automated prompt | RAID — 11 models × 4 decoding strategies × 12 adversarial attacks | **free** |
| model output, rich deliberate prompt | **must be generated** — this is the §1 claim and nobody has built it | **build** |
| commercial SEO filler, human-written | partial: SEO appears as a domain in [DetectRL-X](https://arxiv.org/pdf/2605.15518) and related multilingual benchmarks | **partial** |
| press releases, institutional boilerplate | must be assembled | **build** |
| identified grooming networks | [DFRLab, *Pravda in the pipeline* (April 2026)](https://dfrlab.org/2026/04/08/pravda-in-the-pipeline/) | **derived, no crawling** |

RAID is 10M+ documents and is at <https://github.com/liamdugan/raid>.

**The grooming corpus no longer requires pointing a fetcher at a live influence operation.** DFRLab
audited Common Crawl and found Pravda-network content already inside the public training pipeline.
The Pravda network published over 3.6 million articles in 2024 and roughly 23,000 per day, with the
apparent primary objective of flooding training data rather than reaching human readers — and
[Anthropic / UK AISI / Alan Turing Institute found as few as 250 malicious documents can compromise
a 13B model](https://blackbird.ai/blog/poisoned-at-the-source-ai-training-data-is-under-attack/).

**A live controversy the project is walking into, and should walk into deliberately.** There is a
published dissent — [*LLMs grooming or data voids?*](https://www.researchgate.net/publication/396591096_LLMs_grooming_or_data_voids_LLM-powered_chatbot_references_to_Kremlin_disinformation_reflect_information_gaps_not_manipulation)
— arguing that chatbot references to Kremlin disinformation reflect **information gaps rather than
manipulation**. This is not an obstacle. It is a question the instrument is unusually well suited to
adjudicate: a data void and a grooming campaign should produce *different audience posteriors*, and
§4's machine-audience dimension is the discriminating measurement. Recorded here as a target, not a
claim.

**The obligation this defers.** Building no fetcher until Gate 2 is a rigor trade, made knowingly:
the grooming corpus is then *someone else's sample*, with their selection criteria and their
inclusion decisions inherited unexamined. **This must be revisited before any claim about grooming
prevalence is made.** Logged here so it cannot be quietly forgotten.

---

## 7. §8's sandboxing has a name and a 2026 consensus

The spec derived its fetch/analysis split independently. It is the **dual-LLM pattern**, proposed by
Simon Willison in 2023 and operationalised as **CaMeL** — capabilities for machine learning — in
2025 ([2505.22852](https://arxiv.org/pdf/2505.22852)). The correspondence is close enough to be worth
stating line by line:

| §8 requires | CaMeL calls it |
|---|---|
| split fetch from analysis, separate processes and privileges | privileged LLM / quarantined LLM |
| the probe model gets no tools, structured output only | the quarantined LLM cannot invoke tools and has no persistent state |
| all fetched text is data, tagged with source and trust level | capability labels tracking data provenance through the execution graph |
| egress allowlist, no credentials in environment | egress constrained so exfiltration is blocked even when injection succeeds |

Related: [type-directed privilege separation (2509.25926)](https://arxiv.org/pdf/2509.25926),
[ClawGuard (2604.11790)](https://arxiv.org/pdf/2604.11790), and [adaptive evaluation of out-of-band
defenses (2606.26479)](https://arxiv.org/html/2606.26479v1).

**The consensus is that this is mitigation, not a solution.** The 2026 position, acknowledged across
OpenAI, Anthropic and Google DeepMind publications, is that [prompt injection cannot be fully solved
within current LLM architectures](https://zylos.ai/research/2026-04-12-indirect-prompt-injection-defenses-agents-untrusted-content/);
what is achievable is defence in depth. §8's non-negotiables are therefore correct as written and
should not be relaxed on the grounds that a named framework now exists.

**One design consequence for this repository, stated here because it is easy to get backwards:** the
correct MCP posture for the analysis process is **the empty set**. Not a restricted set. Giving the
probe any tool at all would be this project's first security defect.

---

## 8. Amendments to the spec, recorded

The spec is pre-registered and **is not edited**. These are the deltas, recorded here where they
were decided.

**A-1 — §6's novelty claim is amended.** Bounded-family Bayesian intent inversion is prior art
(§2 above). The novelty is the artifact-level object, non-invertibility as a measurement, and the
corpus application. §6's sentence "artifact-level author-intent reconstruction, as a corpus
instrument, appears unoccupied" survives; the sentence "all of it is about user intent in
interactive settings" does not.

**A-2 — Gate 3 is promoted.** The boundedness ablation runs from Gate 1 in parallel with the bounded
arm, rather than after Gate 2. Rationale in §2 above.

**A-3 — D-4 resolves to "harden, and log."** The spec's default was *harden first, measure second,
and never both in the same run.* Amended: harden per CaMeL, and **record every injection-detection
trigger as data** without letting it enter the reading. This preserves "never both in the same run"
— the log is not an input to any measurement — while accumulating the evidence §8's elegant-
validation option would need later. Deciding this before Gate 1 was required by the spec; it is
decided.

**A-4 — no fetcher is built until Gate 2 clears.** Corpora come from RAID and the DFRLab audit.
This removes most of §8's attack surface for Gates 0–2 and reaches the falsifiers sooner. The
deferred rigor obligation is recorded in §6 above and is a blocker on any prevalence claim.

**A-5 — the probe is hybrid.** Local quantised model carries convergence sampling volume; an API
model provides a quality reference on a held-out slice. Forced by §4's cost analysis. Both arms are
recorded per reading so the local/API delta is itself measurable rather than assumed away.

**D-1, D-2, D-3, D-5 stand at their spec defaults**: fixed hand-written hypothesis family; both
numbers and account, numbers primary and account marked as illustration; trade-offs only for value
extraction; research demo first.

---

## 9. What would have failed this gate

Recorded so the gate is falsifiable rather than decorative. Gate 0 would have returned **stop** or
**redesign** if any of the following had been found:

1. **Artifact-level author-intent reconstruction already built and evaluated.** Not found. The
   nearest work (§2) inverts agents in scenarios, not artifacts.
2. **A published bounded-vs-unbounded ablation showing boundedness buys nothing.** Not found. The
   ToM literature assumes boundedness helps and does not ablate it against free-form attribution on
   artifacts.
3. **Intent-based corpus filtering already deployed.** Not found (§5).
4. **A demonstration that intent-attribution consistency reduces to surface statistics.** Not found,
   and the two are treated as distinct objects throughout the uncertainty-quantification literature.

The fourth is the one most likely to be discovered *by this project itself*, at Gate 2, as
falsifier 1 in §7 — *convergence tracks topic coherence*. It is not a literature question and the
literature could not have settled it.

---

## 10. The severity rule, carried over

The simulation's habit transfers: **every headline gets its false-positive rate before it gets a
sentence.** Nothing in this document is a result. It is a survey, and its own severity caveat is
that a literature search finds what it is worded to find. Four search families were run — intent
inference and inverse planning; detection failure and adversarial evasion; consistency and semantic
entropy; corpus poisoning and injection defence. **A fifth family that was not run is the design and
HCI literature on authorship, provenance and creative process**, which may contain a
qualitative version of this instrument. That is the most likely place a missed prior lives, and it is
named here rather than discovered later.

---

## Sources

- [AutoToM: Scaling Model-based Mental Inference via Automated Agent Modeling](https://arxiv.org/abs/2502.15676)
- [Towards Machine Theory of Mind with LLM-Augmented Inverse Planning](https://arxiv.org/abs/2507.03682)
- [Hypothesis-Driven Theory-of-Mind Reasoning for Large Language Models](https://arxiv.org/pdf/2502.11881)
- [The Neuro-Symbolic Inverse Planning Engine (NIPE)](https://arxiv.org/pdf/2306.14325)
- [Understanding Epistemic Language with a Language-augmented Bayesian Theory of Mind](https://arxiv.org/pdf/2408.12022)
- [Adversarial Paraphrasing: A Universal Attack for Humanizing AI-Generated Text](https://arxiv.org/abs/2506.07001)
- [Why AI-Generated Text Detection Fails: Evidence from Explainable AI Beyond Benchmark Accuracy](https://arxiv.org/html/2603.23146v2)
- [Enhancing the Robustness of AI-Generated Text Detectors: A Survey](https://www.mdpi.com/2227-7390/13/13/2145)
- [Paraphrasing Attack Resilience of Various AI-Generated Text Detection Methods](https://arxiv.org/abs/2605.14240)
- [MASH: Evading Black-Box AI-Generated Text Detectors via Style Humanization](https://arxiv.org/pdf/2601.08564)
- [RAID: A Shared Benchmark for Robust Evaluation of Machine-Generated Text Detectors](https://arxiv.org/html/2405.07940v1)
- [DetectRL-X: Towards Reliable Multilingual and Real-World LLM-Generated Text Detection](https://arxiv.org/pdf/2605.15518)
- [Uncertainty Quantification for Language Models: Black-Box, White-Box, LLM Judge, and Ensemble Scorers](https://arxiv.org/pdf/2504.19254)
- [SEReDeEP: Hallucination Detection via Semantic Entropy and Context-Parameter Fusion](https://arxiv.org/pdf/2505.07528)
- [Best hallucination detection tools for LLM applications (2026)](https://www.braintrust.dev/articles/best-hallucination-detection-tools-2026)
- [DFRLab — Pravda in the pipeline: early evidence of state-adjacent propaganda in AI training data](https://dfrlab.org/2026/04/08/pravda-in-the-pipeline/)
- [LLMs grooming or data voids? (dissenting analysis)](https://www.researchgate.net/publication/396591096_LLMs_grooming_or_data_voids_LLM-powered_chatbot_references_to_Kremlin_disinformation_reflect_information_gaps_not_manipulation)
- [Poisoned at the Source: AI Training Data Is Under Attack](https://blackbird.ai/blog/poisoned-at-the-source-ai-training-data-is-under-attack/)
- [Operationalizing CaMeL: Strengthening LLM Defenses for Enterprise Deployment](https://arxiv.org/pdf/2505.22852)
- [Preventing Prompt Injection with Type-Directed Privilege Separation](https://arxiv.org/pdf/2509.25926)
- [ClawGuard: A Runtime Security Framework for Tool-Augmented LLM Agents](https://arxiv.org/pdf/2604.11790)
- [Adaptive Evaluation of Out-of-Band Defenses Against Prompt Injection in LLM Agents](https://arxiv.org/html/2606.26479v1)
- [Indirect Prompt Injection: Attacks, Defenses, and the 2026 State of the Art](https://zylos.ai/research/2026-04-12-indirect-prompt-injection-defenses-agents-untrusted-content/)
