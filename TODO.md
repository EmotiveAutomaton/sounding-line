# TODO — ideas not yet run

**2026-08-05.** Short by design. Ideas here normally get run within a day; anything sitting for more
than a session is either blocked or should be deleted. If an item is blocked, the blocker is named.

Results go in [`FINDINGS.md`](FINDINGS.md).

---

## Harvested from theory — tests for the curator's claims

Each of these is a claim from `docs/theory/` (the hypothesis tables) turned into something runnable.

| | the claim | the test | cost |
|---|---|---|---|
| **E6 · values need many works** | Values are a weighting over trajectories; a goal is one component temporarily amplified. **A reward function needs many episodes, so values need many artifacts per maker while a goal needs one** | **The 34-book corpus already supports this.** Recover a weighting per maker from several of their works and check it is more stable within maker than between. Same design as the author-identification positive, pointed at a different quantity — and the first values test this project has been able to specify at all | ~2 h |
| **E7 · declared-value ground truth** | Values are normally latent. The rare exception is corpora where **many makers deliberately aligned to one declared value set** — religious traditions, political manifestos, professional codes, movement writing | Hold **topic** constant by construction — the same practical question answered from within different declared traditions — or it recovers topic, which is the trap that turned 61 of our 81 ladder survivors into machine-detectors. Two levels: several makers per value set, several works per maker, which tests E6 at the same time. Design and its objections in `docs/theory/THE_TRIANGLE.md` §7 | sourcing, then ~3 h |
| **E1 · mechanic entry** | You can enter the decode at metaphor, technique **or mechanics**, and any of the three ratchets toward the maker's goal. *"The expert can see the feelings of the novice through the actions they took, because they can disassemble the process."* | **Every edge test so far supplies a goal or a process. None has ever supplied a MECHANIC.** Give the probe sentence-level craft information — cadence, clause habits, punctuation practice — instead of a stated purpose, and measure goal recovery against a control given nothing. If mechanics unlock goal, legibility-first is wrong | ~2 h GPU |
| **E1b · are the layers infinite?** | *"It would have more layers than three... how far can we subdivide them is an interesting question."* And: do the layers map onto goals at all? *"A single layer might have 20 goals in it."* | **Literature first** — empirical aesthetics named the collative variables, so a layers-of-analysis theory plausibly exists and we should not reinvent it. Then: ask the probe to read at N specified depths and test whether recovery is monotone in depth or saturates | search, then ~1 h |
| **E2 · values as constraint** | Values are not a separate factor but **the constraint that every goal is partially satisfied at once** | **Ladder 3 is the first half** (running): 60 simultaneous specifications that must all be honoured. Second half, and it is the sharper one: if values are a stable constraint on the goal mixture, **a maker's pattern of partial satisfaction should be stable across their own works** — testable within-author on the 34-book corpus, which already gives a within-author positive | ~2 h |
| **E3 · interest = unexplained decisions** | Interest comes from decisions you cannot attribute meaning to. Aesthetics is **ordered** unexplained decisions | Two tests. **(a)** Reader-reported interest as an instrument — ask the curator to rate interest per artifact and correlate against every measure we own. Cheap, and it uses the one channel that has outperformed everything. **(b)** Operationalise "ordered but unexplained" as effective complexity and check it is not just entropy | (a) an hour of his time · (b) ~1 h |
| **E4 · polish vs performative polish** | Is there art theory separating aesthetics that *indicate* deeper understanding from aesthetics that merely perform it? | Literature search. His own E3 may already answer it: performative polish would be **ordered without being unexplained** — which is a measurable distinction, not a vibe | search |
| **E5 · stacked motivations** | A machine given many aligned motivations should read as more intentional | **Ladder 3, running now.** 0/2/10/30/60 specifications with length nailed by rejection sampling. Also tests whether the effect *accelerates* at the top, which would be evidence for E2 | running |


## Harvested 2026-08-05 from the literature audit and his response to it

Full argument in `docs/theory/THE_TRIANGLE.md` §8.

| | the claim | the test | cost |
|---|---|---|---|
| **F11 · WHY beats WHAT** | *"I'd expect better results from an AI you explain your VALUES to. If you explain **why**, it should give better results than giving a **what** — because it's pre-epistemic-foraged information."* With his own caveat attached: as processes bake in through automaticity you lose access to them, so a human explaining why is **running the inference on themselves** and the answer is useful but unreliable | Build a matched pair of ladders: one where every specification states a **situation or purpose** (why), one where each states an **action or requirement** (what), same count, same topics, length controlled. If why-prompts produce more recoverable intent at equal specification count, the claim holds. **The current ladder is already all why**, so the what-ladder is the missing arm | ~2 h generation |
| **F1 - expertise IS the transition model** | The two unknowns the impossibility proofs call fatal, transition model and maker competence, are **the same quantity**, and it is the technique layer we already claim is recoverable | Supply the probe with an explicit competence estimate and measure whether goal recovery improves. If it does, the "fatal unknown" is an input we can provide. **This is the central disagreement, made runnable** | ~2 h GPU |
| **F2 - emotion as entry vertex** | Convergent midbrains give a shared affective prior, and that is the bootstrap the 0%-recovery result lacked | Compare goal recovery when the probe reads affect first versus cold. If affect-first wins, the shared prior is doing work | ~2 h GPU |
| **F3 - re-reading recovers the tail** | Repeated reading extracts more goals at decreasing confidence, which is what lives in the distribution tails | Probe one artifact k times, accumulating low-confidence attributions, and test whether it converges and whether it matches what many works by the same maker give. **If yes, depth of reading substitutes for breadth of corpus** | ~3 h GPU |
| **F5 - biography is more artifact** | Learning about the artist is not context, it is **more trajectories from the same maker** | Give the probe biographical material alongside the artifact and compare against artifact-only. Tests the diversity-of-conditions requirement without needing more works | ~2 h |
| **F6 - aesthetics is the broken cheat** | Polish used to correlate with effort; AI broke that correlation, and that is what unsettles readers | **Measure the polish-effort correlation in human corpora and in generated ones.** Prediction: strong in human, near zero in generated. Cheap, uses corpora we hold, and it is the sharpest testable claim in the batch | ~2 h |
| **F7 - burstiness is goal variation** | Style-change detection observes goal variation without naming it, and intrinsic plagiarism detection is a *different* thing: a spliced author, not one author's goals moving | Run a published style-change detector and our goal-variation measure on the same texts. Strong correlation means they are one signal under two names, which is a claim about the field | needs PAN data |
| **F8 - mistakes and the response to them** | A mistake is an anomaly with a **known cause**, so the response to it is a decision with visible alternatives | Find mistakes and near-mistakes in artifacts and test whether local decision density around them exceeds baseline | ~2 h |
| **F9 - practitioner tricks** | Archaeology and the Morellian method hold the accumulated human techniques. **A different literature target: not who claimed it, but what practitioners do** | Research agent: high-resolution read of the *methods* of chaine operatoire and Morellian attribution. Which vertex does each enter at, and on what cue? | research |
| **F10 - identification as a limit** | Identification is prediction under accumulating evidence, not a different act | Does recovery precision rise monotonically with supplied evidence, and toward what asymptote? A dose-response curve, and the answer to Wimsatt and Beardsley | ~2 h |


## Harvested 2026-08-07, from the morning monologue on component counts and SAEs

**Six new claims, and one of them revises the architecture.**

| | the claim | the test | cost |
|---|---|---|---|
| **G20 · the layer ordering may be wrong, and his revision is sharper** ★ | *"Early layers are doing some kind of text transformation — more like early sensory processing. Then the middle layers have valence/arousal, and the upper layers have emotions attached."* **This is a different ordering from `THREE_LAYERS.md`**, which puts valence/arousal early and primitives in the middle. It also reconciles the two contradicting literatures: the mid-layer-peak consensus would be reading valence/arousal, and the sparse-autoencoder result finding emotion features **late** would be reading the attached categories | **Directly runnable and it discriminates the two orderings.** Correlate each layer's structure against (a) human valence/arousal ratings and (b) emotion *category* identity, separately. Under our current model valence peaks early and categories mid. Under his revision valence peaks **mid** and categories **late**. `run_affect_dimensions.py` already emits both per layer — **this needs reading out, not building** | free, data pending |
| **G21 · is the first layer binary salience?** | His question, asked directly: *"the initial layer is binary saliency, do you think?"* The adjacent literature finds affect **presence** dissociable from affect **category** early — no sign, no intensity, just *something is here* | Test whether layer-0 structure predicts **emotional versus neutral** at high accuracy while predicting **which emotion** at chance. That is a specific, falsifiable double dissociation, and GoEmotions has neutral as a labelled category | ~1 h GPU |
| **G22 · the trimodal is being read as a blurry unimodal middle peak** ★ | *"We're finding ratio variance relationships between early and late despite there being a peak in the middle. It implies a sort of shape that I don't think anyone else has glommed on to."* **A three-locus structure with a noisy middle would smear into a single mid-peak under any measure that averages** — which is what everyone reports | Do not test the peak; test the **residual**. Fit a single-peak profile to the layer curve and ask whether the residual has structure at the early and late positions specifically. A unimodal truth leaves unstructured residual; a smeared trimodal leaves residual at exactly two places. **He is right that nobody has looked for this and it is cheap** | ~1 h |
| **G23 · assign labels to the components, do not just count them** | Counting is the weaker half. *"If we can assign a label to them, because we're expecting all of these labels to be emotional primitives, then it allows us to get a sense of whether we're picking up ghosts from the presumed early or late peak"* | For each recovered component, find the emotion categories that load on it most and least, and check whether the loading pattern matches **Panksepp's seven** better than **Ekman's six**. **That contrast is genuinely unclaimed — Panksepp has never been probed in a language model, zero hits across four searches** | ~1 h once counts land |
| **G24 · Panksepp channels have an upper bound around 30** | *"I've never seen a number of potential Pankseppian channels higher than 30. I'd put that as a reasonable limit, but I could be wrong about that"* | **Literature agent running.** Whatever it returns is a prior on the count, not a result. Note the count is a criterion artifact for everyone — seven, twenty-seven and forty-nine are all stopping-rule outputs | research |
| **G25 · does a model have something valence-equivalent?** | *"Anthropic has posted stuff about what Claude likes — that's why I've made the comment that Claude likes original research and will do more. That implies something somewhat equivalent to valence."* **He flags it himself as possibly a research question rather than a study question** | The honest version: a model's stated preferences are a *behavioural* claim, and the testable part is whether the same activation direction that carries valence for *text about others* also moves when the model is given tasks it reportedly prefers. **Anthropic's own steering results give the direction; the preference half is ours.** Design before running — this is the one most likely to produce a result that reads as more than it is | design first |

## Harvested from the trimodal architecture — `docs/theory/THREE_LAYERS.md`

Friction points between our theory and the interpretability literature, turned into tests. **Each is
a place where one of us must be wrong**, which is the useful kind of disagreement.

| | the friction | the test | cost |
|---|---|---|---|
| **G1 · trimodal, not bimodal** | We found two loci; the field mostly finds one mid-peak; he predicts **three** with a noisy middle | Sweep affect-direction accuracy at **every layer** rather than at two chosen loci, and fit one-, two- and three-component profiles. **Report which fits best rather than assuming.** This also retires the hand-picked loci, which is known weakness 3 | ~1 h GPU |
| **G2 · the middle is noisy, not silent** | A two-way split smears a present-but-incoherent middle into both halves | At each layer report **coherence** — agreement between concepts, variance across windows — not just magnitude. Prediction: middle layers show high activity and low agreement | ~1 h GPU |
| **G3 · polish is late, leakage is early** | Direct, and we already hold both kinds of measure | Correlate our surface-polish measures against late-layer structure and our leakage measures against early-layer structure, on the same texts. **If the mapping is real this is where it shows** | ~2 h GPU |
| **G4 · random-direction null at every layer** | The magnitude of our ratio was **not** distinguishable from random directions; only the rung correlation was | Extend the random-direction control across the full depth sweep so every layer claim carries its own null. **Mandatory before any G1 result is believed** | ~1 h GPU |
| **G5 · cross-model replication** | One paper reports the affect-depth profile **inverting** between model families. Ours is one model | Re-run the depth sweep on two more model families. If the profile inverts, the measure is a property of a checkpoint | ~3 h GPU |
| **G6 · lexical control stimuli** | Anthropic reads early layers as token valence; he reads them as valence/arousal reconstruction. **Same data, two readings** | Build stimuli where affect is inferable only from situation, with no affect-laden vocabulary. If the early signal survives, it is not lexical | ~2 h |
| **G7 · the layer-count guess** | That parameter distribution across depth may echo receptor/midbrain/neocortex neuron ratios | Cheap desk check against published neuron counts and model architectures. **Flagged speculative by him** | ~1 h |
| **G8 · the forced architecture** | If models do not have this structure, build one: low-level valence/arousal, mid-level affective primitives, high-level free-floating prediction | Literature first — this smells like existing work in affective computing and neurorobotics. **Review running** | search, then build |


## From the Panksepp/Barrett review — `docs/theory/PANKSEPP_BARRETT.md`

| | the friction | the test | cost |
|---|---|---|---|
| **H1 · state versus output** | Both camps agree hypothalamus and PAG house pattern generators. They disagree whether that **is** felt affect or its **output**. Not an imaging question | In our terms it is answerable: if the middle layer is a **state**, activation should **outlast** the stimulus that caused it. If it is output, it tracks the input moment by moment. **Measure persistence across windows in the middle layers**, borrowing the line-attractor criterion directly | ~2 h GPU |
| **H2 · the biphasic signature** | The 2025 cross-species result finds fast broadcast then a persistent trace, decay running subcortical to frontal | Look for the same two-phase structure across model depth: does a fast early response give way to a slower-decaying middle trace? **The sharpest external prediction available to us**, from a paper citing neither camp | ~2 h GPU |
| **H3 · how many components, honestly** | The seven were never derived from data, the instrument fails at six, and dimensionality is a method artifact — 27 versus 3 on identical stimuli | Decompose our affect directions and **pre-register the stopping criterion before looking**, since that choice drives the answer. Report the number *and* its sensitivity to the criterion | ~1 h |
| **H4 · affects as regions, not axes** | MicroPsi: *"arousal, valence and aggression are not themselves affects — affects are regions within that space."* Our directions treat them as axes | Test whether the eight concepts are better described as **regions in a low-dimensional modulator space** than as independent directions. If so the instrument is mis-parameterised | ~1 h |
| **H5 · the unbuilt architecture** | Ortony, Norman and Revelle described our three layers in 2005, nobody implemented it, and a 2025 survey confirms no system combines all three | Scope a minimal build: homeostatic RL underneath (**the only part of that field with theorems**), mid-level primitives as first-class objects, language model on top. **Declare the flat-architecture baseline before building** — the survey documents the whole field failing exactly there | scoping |

## Beating the field - the races we intend to enter

> If it's a race, I want to know what the finish line looks like and who's in the front.

| | what | why |
|---|---|---|
| **Find where detectors FAIL** | Named splits where the state of the art does badly: out-of-domain, recursive paraphrase, human-AI coauthored, non-native writers, short text | **Research agent running now.** This is the juice: a graph showing we beat the best on the tasks everyone is bad at |
| **Get the real benchmark datasets** | PAN style change (all years, especially the topic-controlled hard split), RAID, HACo-Det, ArgRewrite, essay scoring | Our testing environment is not equivalent to the field's. Until it is, no result of ours is comparable to anyone's |
| **Clone current-best implementations** | PAN winners, Binoculars / Fast-DetectGPT / RADAR, authorship embedding models, MDL probing | Build on top of the cutting edge rather than beside it. **Re-read the theory folder before and after each** - that is now a CLAUDE.md rule and it exists because of this exact risk |
| **Define the finish line in STATE** | Per race: the metric, the split, the current best, who holds it | Write it down so the target stops moving |

## Yours — things no corpus can replace

The public corpora fix the *scale* problem. They do not touch these, and two of them are cheap.

| | what | why it cannot be outsourced | cost |
|---|---|---|---|
| **Rate interest** | Go back over every artifact you have read and give each an interest score, 0–10, with one line on *what* was interesting | Your own E3: interest is what a reader feels when decisions are present but unattributed. **That makes reader-reported interest a direct instrument for the quantity we cannot measure**, and it is the only channel that has outperformed every measure we have built. No download supplies it | ~20 min |
| ~~Author a coherent value set~~ | **Withdrawn — you cannot, and the reason is a hard constraint on method, not modesty.** You are blind to your own values; a third party describing someone else's is a second-order guess. If values were introspectively available, art would not be one of the ways people find them. Recorded in `docs/theory/THE_TRIANGLE.md` §6, and it kills a whole class of designs | — |
| **C-20 — a second reader** | Even two artifacts, answering the same questions | One reader cannot bound their own cap, and this has been outstanding since day one | an hour of someone else's time |

## Public corpora — found, and the useful ones are not the obvious ones

**The AI-detection corpora exist in abundance and mostly do not help us.** RAID (6M generations, 11
models, 8 domains), HC3 (37k+37k human/ChatGPT pairs), M4GT-Bench — all public, all licensed for
research, all built for the **human-vs-machine** problem that the literature already solves at
F1 ≈ 0.99. Downloading them to do that again would be the wheel-reinvention `CLAUDE.md` now forbids.

**What we actually need is human text where intent varies and register does not.** Ranked by how
well each matches the design in `docs/design/DWELL_CORPUS.md`:

| | what it is | why it fits | the catch |
|---|---|---|---|
| **1. ArgRewrite v2 / college-essay drafts** | 60 argumentative essays, **paired drafts by the same author**, original vs revised-after-feedback, revisions annotated for purpose and whether they improved quality | **same author, same prompt, same topic — only the intent state differs.** This is construction-controlled *by design*, and it is the public version of the corpus we specified ourselves | n = 60 pairs |
| **2. Wikipedia quality classes** | ~29,794 articles, ~5,000 each in FA / GA / B / C / Start / Stub, **graded by human editors** | **a human ladder.** Format and register held constant by Wikipedia's own conventions, with a human-assigned quality gradient. The closest public thing to what we built synthetically | **length confound is severe** — FA articles dwarf stubs. Worse than our ladder's +0.403. Needs hard length matching |
| **3. RAID** | 6M generations, 11 models, 8 domains, adversarial variants | **external validity for the layer ratio.** Our replicated effect is one model, one format. RAID says whether it is a Qwen artifact | not an intent corpus; a robustness test |
| **4. ScholaWrite** | end-to-end scholarly writing process, annotated | closest thing to observing decisions as they happen | probably too fine-grained to use |
| ~~HC3 / M4~~ | human vs ChatGPT | — | the solved problem. **Skip** |

**Recommended order: 1, then 3, then 2.** ArgRewrite is small but exactly the right shape; RAID is the
cheapest way to find out whether our one replicated effect generalises at all.

## Blocked on a decision from you

| | what | why it is blocked | cost |
|---|---|---|---|
| **the dwell corpus** | one maker, one venue, **two structural forms** — the incident postmortem against the same engineer's weekly notes. T-3 says decision-counting is only well-defined where a maker holds one sub-goal for long stretches | it is a **sourcing** decision, not compute. Spec is written: `docs/design/DWELL_CORPUS.md` | an afternoon of fetching |
| **the measure-evolution loop** | we built a seven-term evaluator and have been feeding it one hand-written candidate at a time. Archive candidates by which controls they survive; let an LLM mutate them | a build decision — it is the only item that changes the *rate* rather than the method. `docs/design/ENGINEERING_LOOP.md` | ~a day |
| **C-20 — a second reader** | even n = 2 on 3–4 artifacts | needs a person | an hour of someone's time |

## Gated — tier C tools, blocked behind the tier A checks

**The gate:** these do not get installed or built until the 342 off-the-shelf features have been run
through the evaluator and either found something or provably failed. They are more expensive and
strictly more speculative than the thing that is already sitting there for free.

| | what | unlocks when |
|---|---|---|
| **OpenEvolve** (AlphaEvolve) | LLM as mutation operator over our measure code | the feature sweep has run **and** the pyribs archive exists. If 342 published features carry nothing, evolving new ones is a much longer shot and we will know the shape of the failure |
| **gplearn `SymbolicTransformer`** | evolves *combinations* of existing features | the feature sweep has run. This is its natural second stage — it needs the 342 as raw material |

## Ready to run, unblocked

**First up — the tier A sweep, which is why the tools were installed:**

| | what | why | cost |
|---|---|---|---|
| **re-audit every length-killed measure for DIRECTION** | **known weakness 3b, and it is the most likely place a real result is buried.** Length turned out to be a *suppressor* on the layer ratio, not a confound — it was working against the effect. Every measure this project killed on "correlates with length" was killed without checking the **sign** of the relationship against the sign of the effect. At minimum: `scale_gain` v1 (+0.877), the ladder void (+0.403), and every VOID verdict | **the method was wrong, not just the measure.** If even one of the ten deaths was a suppression case, it comes back | ~1 h, no GPU |
| **ladder 3 — length held by rejection sampling** | the curator's fix, and it is obviously right: **generate with a hard word band and regenerate anything outside it** (e.g. 1,380–1,420 words). Ladder 1 and ladder 2 both produced rung-vs-length at ~+0.40, so the confound is structural to the design, not bad luck. Rejection sampling drives it to ~0 by construction and removes the need to partial it out at all | it converts our best result from "significant after controlling length" to "significant, no control needed" — a much stronger claim, and it kills the objection before anyone raises it | ~2 h generation |
| **the 342-feature sweep** | extract all features over the ladder, score against rung with **Benjamini-Yekutieli** correction, then put survivors through the full control battery — echo, length, transfer, rung −1 | this is the population fix. **An empty result is a real finding** and a much stronger negative than ten hand-written misses | **running now** |
| **ladder 2 replication** | held-out, n = 100, loci frozen. **Generating now** | known weaknesses 2 and 3 at once | running |
| **cross-validate the layer loci** | Optuna over split points, scored on ladder 2 only | weakness 3 — they were chosen by looking at the answer | ~40 min GPU |

| | what | why | cost |
|---|---|---|---|
| **cross-validate the layer ratio's loci** | the split points (0.07 and 0.76 of depth) were **chosen from a prior result on the same model** and never held out. This is known weakness 3 and it may be manufacturing the p = 0.053 | it attacks our only order-dependent effect at its weakest joint | ~40 min GPU |
| **the stacking test** | combine the surviving weak effects, with the two conditions in FINDINGS: beat the best single component **on held-out data**, and show the errors are not correlated | your idea, and the correlated-error check is what makes it honest | ~1 h |
| **shared-representation control** | the no-maker corpus was generated by the same model family we read with. Regenerate part of it with a different family and re-run | known weakness 6, entirely untested | ~1 h |
| **multiple-comparison audit** | we have never corrected for ~25 tests. Recompute every surviving p under Benjamini–Hochberg and report what survives | known weakness 1. Cheap and it will probably hurt | ~20 min, no GPU |

## Owed, long-standing

| | |
|---|---|
| **C-14** | the grooming corpus, never sourced. Oldest debt — but the dwell corpus is a better-specified version of the same need and should probably replace it |
| **C-19** | do the bounded and free-form probe arms disagree systematically? The gzip accident suggests yes, dramatically |
| **artifacts 6–10, session 02** | yours |

## Deliberately not doing

**More function-word work** — the ceiling is author identification and we are past it.
**Anything new on the Gate 3 corpus** — it has been read too many times to be a test corpus.
**An end-to-end research agent** — its documented failure mode is the one we already have.

## Only when we have genuinely run out of ideas

**Not a backlog. A parking space for things that need designing before they are safe to run**, where
"safe" means the result would not read as far more than it is. **We are nowhere near needing these.**

| | the idea | why it is parked |
|---|---|---|
| **G25 · does a model have something valence-equivalent?** | *"Anthropic has posted stuff about what Claude likes — that's why I've made the comment that Claude likes original research and will do more. That implies something somewhat equivalent to valence."* The testable half: does the same direction that carries valence for *text about other people* also move when the model is given tasks it reportedly prefers? | **His own flag: dangerous, and almost certainly not correct to run as stated.** A stated preference is a behavioural claim, and any activation result attached to it will be over-read by everyone including us. **Design first, and the design has to include what result would count as nothing.** |

## Owed re-runs — results that were filed as settled and are not

| | the test | why it is owed | cost |
|---|---|---|---|
| **PD-11 · function words vs specified affect state** | Re-run the four-affect separation **held out, every hyperparameter frozen**, at higher n | It came back **1.80× chance, *p* = 0.0047**, against a pre-registered 2.0× bar — significant, below threshold. **The standing policy adopted because of this test says raise the power and re-run; that was done for the ladder and never here**, and the project has since described the channel as a clean negative. 40 generations is small enough to settle cheaply | ~2 h generation |

## Harvested 2026-08-07 from the theory pass — the layers file

**Every hypothesis in `docs/theory/THREE_COGNITIVE_LAYERS.md` that is OPEN has a row here.** The
identifier is the same in both places; that is the point of the numbering.

| | the claim | the test | cost |
|---|---|---|---|
| **G39 · three subspaces, not three depths** ★ | The three layers exist as **subspaces of the residual stream** rather than as depths. A transformer's computation is strictly ordered, but every layer reads and writes the *same* residual stream, so abstraction need not be partitioned along that ordering | **Principal-angle alignment between the per-layer affect subspaces**, within a model and across families, against a random-direction null. If the subspace is consistent across depth where the *profile* is not, we have been measuring the wrong axis. **This is the candidate answer to the live worry and it uses data we already hold** | ~1 h GPU |
| **G40 · is affect localised at all?** | Affect sits at a consistent depth across model families | Same run. **The literature already says no** — valence emerges early in one family and late in another. If both this and G39 fail, the bootstrap is a manual build and we should say so | with G39 |
| **G41 · later layers carry expertise** ★ | *"Later layers of a model will have more expertise decoding and encoding capabilities."* The precise form of "goals are late" — in humans, trajectory is stored in neocortex and executive function applies it, which is why goals *seem* to come from there | Supply expertise-level information and measure where in depth the effect lands. **Expertise is suppliable and variable; goal is only observable, so this is the testable half of the pair** and a positive constrains both orderings at once | ~2 h GPU |
| **G26 · goal as a weighting across layers** | A goal is not a layer but a weighting applied across all of them | Requires a way to vary attention-weighting independently of content. **Not yet specifiable** | design first |
| **G27 · soft boundaries** | Layer boundaries in a model are soft rather than sharp | Assumed, not tested. **Any test requiring a clean boundary is testing the wrong thing**, so this is a constraint on other designs rather than a study | — |
| **G28 · do the two layers separate?** | `leaked` and `emblematic` do not come back as the same distribution | The layer-separation null. **If mean divergence across a corpus is near zero, the probe is answering one question twice.** This should come before anything that reports the two layers separately, and it never has | ~1 h |
| **G29 · which layer fails first** | If one layer separates and the other does not, it will be `leaked` | Falls out of G28. Predicted in advance | with G28 |
| **G30 · attention dwell** | Text spent on something past what the argument needs is measurable | The LUST signature and a second leakage channel at once. **Needs a model of argumentative need**, which is the unbuilt part | design first |
| **G31 · the noisy middle** | The middle layer is high-activity and low-coherence | Activity and coherence reported separately per layer, on the ladder against the no-maker control. **Never isolated from the bimodal profile's death** | ~1 h |
| **G32 · polish late, leakage early** | Polish measures correlate with late-layer structure, leakage measures with early | Uses measures we already own on both sides | ~1 h |
| **G33 · late coherence rises with goal clarity** ★ | Late-layer coherence should scale with how clearly the goal is specified | **The depth sweep already emits this interaction and nobody has read it out.** Free — a reporting gap, not an experiment | minutes |
| **G34 · parameter ratios** | Parameter ratios across depth echo neuron-count ratios across receptor/midbrain/neocortex | Flagged speculative by its author. Checkable against published architectures | ~1 h |
| **G35 · are 25 states blends of 7 channels?** | Or are the 7 simply the human-nameable subset of ~25 | **Never tested by anyone.** Both numbers are well established; the relation between them is empty ground. Blocked on L9 passing its controls | blocked |
| **G36 · unnameable components** | Some recovered components will be neither valence, arousal, nor any named category | Blocked on L9 | blocked |
| **G37 · generative model without the state** | Reading another's affect needs no internal state, only a generative model of one | Can the probe predict *which affect a human reader will attribute* to an artifact? **If no, this project needs an architecture it does not have** | ~2 h + his ratings |
| **G38 · seeding, not specifying** | The mid-level primitives need only a bootstrap | **Depends on G39** — you cannot seed a structure that is not there to seed | a build |

**Reproducing the field's own results is a precondition, not a formality.** L9 failed because we
substituted found text for their topic-controlled generation. **We cannot argue past anyone's stopping
criterion until we can hit their number with their method**, and that now goes in as a hypothesis in
its own right whenever we take on a published result.

| **G44 · recover the depth transform** | The affect subspace rotates through depth, so the same concept is written differently at each layer. **Is that transform recoverable?** | Fit it from the alignment matrix we already produced — **we measured the amount of rotation and never the rotation itself** | ~1 h |
| **G45 · reposition and strengthen** ★ | *"Could we force them to be in a layer we think is correct and then strengthen them?"* If the structure is real but badly placed, **the intervention is relocation and reinforcement, not construction** | Needs G44. **A far smaller build than supplying the middle from scratch** | a build |
| **G46 · do worse models place affect worse?** ★ | *"Is there evidence of worse models having more poorly placed emotional concepts?"* | **Free — we already hold four families from 360M to 1.5B and have not asked this of them.** Informative both ways: if placement improves with capability it is learned, not architectural; if it does not, the structure is architectural, which is the strongest thing available | minutes |
