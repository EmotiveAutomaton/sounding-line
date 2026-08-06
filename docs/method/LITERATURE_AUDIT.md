# Literature audit — what is occupied, what is refuted, what is left

> ## ⚠ ONE RECOMMENDATION IN THIS FILE WAS REJECTED, AND THE REJECTION WAS CORRECT
>
> A later sweep recommended **dropping Panksepp as a load-bearing premise**, and I relayed it as a
> lead conclusion. **The curator rejected it:** *"Panksepp in general may not be precise, but the
> idea of midbrain-localised solutions is absolutely load-bearing. If you drop that, we have what
> everyone else has, which is the wrong part. You did it again."*
>
> **"Again" is accurate — this is the second time.** The first was adopting Bullot & Reber's framing
> over the project's. Same mechanism both times: a literature return arrives in volume and confident
> prose, and I take its framing without testing between the two accounts.
>
> **Read this file with that in mind.** Occupied ground is real; a recommendation to abandon a
> premise because the literature is crowded is not the same finding, and should be treated as my
> inference rather than the audit's evidence. The replacement architecture is in
> [`../theory/THREE_LAYERS.md`](../theory/THREE_LAYERS.md).

**2026-08-05.** Three research subagents, briefed to fetch sources rather than trust search snippets
and to search adversarially. Every claim below is marked **READ** (source opened) or **SNIPPET**
(pointer only — verify before quoting). That distinction exists because two errors in this project
came from treating snippets as evidence.

**Summary: four of five core claims are substantially occupied, one is formally refuted, and the
genuinely unclaimed territory is narrower than this project has been assuming — and sits in the
instrument, not the theory.**

---

## 1 · The three layers are Bullot & Reber (2013), not Dennett or Marr

**Bullot & Reber, "The artful mind meets art history," *Behavioral and Brain Sciences* 36(2):123–137.**
READ (abstract; body paywalled). Three modes: **basic exposure → the artistic design stance →
artistic understanding**, where the design stance is *"sensitivity to art-historical contexts by means
of inquiries into the making, authorship, and functions of artworks."*

**That is mechanics / technique / metaphor, in a BBS target article with open peer commentary, framed
explicitly as cognition of artifacts.** Rejecting Panofsky did not save the claim — Bullot & Reber are
about *production and causal history*, which is exactly our axis.

**Two things cut the other way, and they are the opening:**

- **They assert a strict ordering** — the design stance is *"requisite for"* artistic understanding.
  **That directly contradicts the curator's "enter at any layer and ratchet."** The BBS commentaries
  attacked precisely the relations among the modes. **This contradiction is our contribution
  surface**, and it is a better position than claiming the layers.
- **The framework is weakly supported.** Chmiel & Schubert (2019), READ in full: 34 experiments
  across 23 publications testing its core prediction — **26% support, 18% inconclusive, 56% no
  support.** It is an occupied lot with a shaky building on it.

**The Dennett mapping has a specific defect.** The intentional stance is **instrumentalist by
design** — a predictive posture, not a claim to recover actual intent. If our output is "the maker's
actual goal," Dennett licenses *prediction*, not *identification*. That is a mismatch, not support.

**Better formal matches, unchecked (SNIPPET):** **Rasmussen's abstraction hierarchy** — five levels
with explicit means-ends links, built for diagnosis *from any level*, forty years of use. That is the
best formal match to the ratcheting claim and we have never looked at it. And **Floridi's Levels of
Abstraction**, which formalises nested and disjoint families — the "fractal, dozens per layer" claim,
already formalised.

**The standing objection we have never named:** **Wimsatt & Beardsley's Intentional Fallacy** (1946) —
intention is *"neither available nor desirable"* from the work. Modern intentionalists concede there
is no direct access to actual intention. A project claiming to recover intent that never addresses
this will be dismissed on sight by every humanities reader.

## 2 · "Values need many artifacts" is a theorem, and the optimism is formally refuted

**This is the single biggest correction in the audit.**

- **Amin, Jiang & Singh, "Repeated Inverse Reinforcement Learning," NeurIPS 2017.** READ (full text).
  Our decomposition exactly: reward `Y = θ* + R`, θ\* intrinsic and constant across tasks, R
  task-specific. And our consequence verbatim: *"it is impossible to identify θ⋆ from watching human
  behavior in a single task."* **The claim is right and it is nine years old.**
- **But the recovery half is refuted.** Armstrong & Mindermann (NeurIPS 2018, READ): a policy cannot
  be uniquely decomposed into planner + reward, and *"cannot be resolved by observing the agent's
  policy in enough environments."* Skalse et al. (ICML 2023, READ) and Cao et al. (NeurIPS 2021,
  READ): rewards are only **partially identifiable in the infinite-data limit** — the consistent set
  is parameterised by an arbitrary function, an infinite-dimensional ambiguity no number of episodes
  reduces.

> **The operative variable is not the COUNT of artifacts. It is the DIVERSITY of the conditions under
> which they were made.** N artifacts made under identical conditions are informationally equivalent
> to one.

**That changes the test.** Our 34-book within-author design must vary *conditions* — genre, audience,
constraint, era — not merely accumulate works by the same person. A rank condition on conditions is
what buys identifiability; a bigger stack of similar books buys nothing.

**And the reframe that survives:** our bounded, human-shaped hypothesis family is not an engineering
convenience. **It is the normative assumption Armstrong & Mindermann prove you cannot do without.**
That is defensible and currently mislabelled in our own docs as a mechanism.

**Two small corrections:** a reward function weights *trajectories*, not policies — say trajectories.
And "attention temporarily amplifies a value component into a goal" is **formally unclaimed**, though
one neuro result argues attention gates *evidence* rather than *value*, which cuts against it.

## 3 · Value blindness: the strong form is false

**CONTRADICTED as stated.** Boer & Fischer meta-analysis (k = 91, N = 30,357, 31 countries, SNIPPET):
self-reported values **do** predict attitudes and behaviour, moderately and reliably.

**The defensible version** is Vazire's SOKA model (SNIPPET): self-knowledge is **domain-specific** —
self is best on internal traits, others are better on observable and highly evaluative ones. Plus:
implicit and explicit values are largely independent.

**But the art-making mechanism is genuinely unclaimed and currently unevidenced.** Bem's
self-perception theory is the general form; the art-specific version — *making an artifact improves
the maker's accuracy about their own values* — has no rigorous test. **It is the most directly
testable proposition in this entire set**: pre/post value self-report accuracy against a behavioural
or informant criterion, around a making task. Cheap, and open.

## 4 · Interest as unexplained decisions is occupied — and Berlyne was the wrong ancestor twice over

**Graf & Landwehr's Pleasure-Interest Model (2015/2017).** READ in full. **Interest** is explicitly
separated from pleasure and defined as *controlled, perceiver-driven engagement with disfluent
stimuli, triggered by disfluency reduction* — initially confusing material becoming comprehensible
under elaboration. **That is the curator's claim with the mechanism specified.** Contested: Consoli's
commentary (READ) argues the split is not clean.

**The best-evidenced live account is learning progress**, not information-gap and not Berlyne: Ten,
Kaushik, Oudeyer & Gottlieb, *Nature Communications* 12 (2021), READ — 382 participants, a model
combining accuracy and learning progress beats either alone for ~71–74% of participants. One strong
paper rather than a replicated literature, but it is the anchor to use.

**Silvia's two-appraisal model contradicts the strong form** (SNIPPET): interest requires
novelty-complexity **and coping potential**. Where novelty is high and coping is low the result is
**confusion**, a distinct emotion. So the claim should be **"detected but not yet attributed,"** not
"cannot be attributed."

**Highest-priority unread item in the whole audit:** Adair (2022), *"Interest, Disfluency, and
Underlying Values: a Better Theory of Aesthetic Pleasure,"* Review of Philosophy and Psychology
13(3):779–795. Paywalled. From the title this may collide with claims 3 and 4 combined.

**The one with usable numbers, and it is the right precedent:** Miall & Kuiken (1994),
*"Foregrounding, defamiliarization, and affect," Poetics* 22:389–407. READ in full. Four studies, 198
readers, three judges coding stylistic deviation per segment. Foregrounding correlates with reading
time (r = .27–.39), strikingness (r = .22–.45) and affect (r = .23–.33) — **and there is no
moderation by literary competence.** It also supplies a ready-made protocol — segment-level reading
time as a behavioural proxy for anomaly entry — which would take our human readings past n = 1.

## 5 · Followers as a value corpus: the graded part is 23 years old, the followers part is open

**Graded ideology scaling is settled prior art** — Wordscores (Laver, Benoit & Garry, *APSR* 2003),
Wordfish (2008), Text-Based Ideal Points (ACL 2020, READ). Pitching graded-versus-binary as novel
would be immediately fatal.

**The followers design is genuinely open** — nobody scores followers against a founder's own text for
graded value uptake. **But the reason is a validity problem, not an oversight:** anchor-based scaling
works *because* reference positions are known in advance. Deriving the value set from the followers
removes the anchor and collapses into unsupervised scaling. Bruinsma & Gemenis (READ), 164 European
manifestos: *"Wordscores fails to deliver valid party positions."*

**Nearest real precedent:** Barron, Huang, Spang & DeDeo, *PNAS* 115(18) (2018), READ — resonance =
novelty − transience, measuring a speaker by what followers retained. But it measures **topical
persistence**, not uptake of a value set.

**Four confounds, all documented, all of which bite:** style imitation is a community-lifecycle
artifact independent of belief; topical vocabulary is confounded with position; founder-to-follower is
a register jump; and selection bias on visible followers is uncontrolled everywhere.

**Do not build on Moral Foundations Theory dictionaries.** Rehbein et al. (ACL 2025, READ in full):
human coders agree at r = .79–.98, and *"none of the dictionary-based measures shows a significant
correlation with the human coders for all four foundations."* Conclusion: *"dictionaries are not a
valid approach for examining morality in text."* MFT's own factor structure also failed to replicate.

## 6 · Two things about our own method

**The intent ladder is a published design.** CS4 (arXiv 2410.04197, READ abstract) systematically
increases prompt constraint count and observes output behaviour. Different dependent variable, same
apparatus, 2024.

**And there is a published explanation for our 61-of-81 problem.** *"How You Prompt Matters!"*
(arXiv 2311.08369v4, READ in full): adding task-oriented constraints to a generation instruction
swings machine-detector F1 by **up to 14.4 standard deviations** — larger than paraphrase or sampling
noise. ChatGPT essays went from 78.2 F1 plain to 37.9–83.9 with constraints. **The amount of
specification in a prompt is a first-order driver of provenance detectability.** So our independent
variable is structurally entangled with the thing we filter against, our funnel is right to exist,
and it should be expected to keep eating candidates.

**Our machine-detector filter is weaker evidence than we have been treating it as.** "AI detection is
solved" holds in-domain only: fine-tuned detectors drop >20 points out of domain, and HACo-Det (READ
in full) finds metric-based detectors at **0.462 F1 against a 0.433 random baseline** on human-AI
coauthored text. The 61 features we removed are corpus-specific. **Run the filter against two
disjoint corpora and keep only what survives both.**

**And the field that actually studies writers' decisions stopped inferring them from the product.**
Keystroke logging — Inputlog, Leijten & Van Waes — records pauses, revisions and source use directly
(SNIPPET). **A keystroke-logged corpus would give actual decision counts to validate any artifact-side
proxy against**, which is the one thing every dead measure here lacked.

---

## What is left, being deliberately stingy

1. **The affective layer-depth ratio in a reading model as a function of specification density.**
   Nothing found using a low-order/high-order affective ratio as an instrument pointed at a **third
   party** — the writer. Adjacent work points at the model's own state or the text's affect.
2. **Within-artifact variance of probe activations** — not perplexity (burstiness does that), not
   surface style (PAN does that). Narrow, and it is the un-preempted version of the veneer claim.
3. **Spec recovery in bits** — `I(specification ; artifact | topic)` estimated by contrastive
   scoring against topic-matched decoys. Built and passing; see `results/spec_recovery/`.
4. **Bullot & Reber's ordering claim, contradicted** — entry at any layer, against their "requisite
   for". Their framework is only 26% supported, so this is contestable ground rather than settled.
5. **Does making an artifact improve the maker's accuracy about their own values?** Unclaimed,
   unevidenced, cheap, and testable.
6. **The failure record itself** — ten ruled-out measures, four voids, pre-registered and hash-locked,
   with a corrected verdict after a post-hoc power simulation. Publishable as methodology in a field
   that publishes almost none of it.

## The deep vulnerability, named in two literatures at once

**Equifinality** (archaeology: many production paths → one artifact) and **partial identifiability**
(IRL: many reward functions → one policy) are the same problem. If this instrument has one structural
weakness, that is it — and the IRL side supplies a formal vocabulary the humanities side lacks.
