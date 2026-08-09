# TODO — ideas not yet run

**2026-08-05.** Short by design. Ideas here normally get run within a day; anything sitting for more
than a session is either blocked or should be deleted. If an item is blocked, the blocker is named.

Results go in [`FINDINGS.md`](FINDINGS.md).

---

## THE PROGRAM (2026-08-09) — the standing order of work, above everything below

The unit of analysis changed from one number per artifact to the recorded decision event, which
carries target, alternatives, choice, dependencies, and context. Event recovery must validate
before any summary statistic means anything. Full statement in `docs/STATE.md` and the README.

| | what it is | the test | status |
|---|---|---|---|
| **G129 · preregister the ArgRewrite choice-recovery analysis** | Each aligned revision is an event with a recorded fine-grained purpose, not a feature carrier. The best immediate bridge corpus, since it holds two revision cycles, purpose labels at two grains, assigned goals, and scores | Bounded candidate set per revision (true purpose plus matched false purposes); reader gets brief and final artifact only; score against brief alone, source alone, shuffled labels, unchanged passages, matched surface revisions. Split train/test **by author, never by revision**. Report confusion matrices by fine purpose, per-author recovery, failure categories, decoy performance, error clustering | preregistration first, then ~half day |
| **G130 · the shared event-level recovery harness** | One harness every recovery test runs through, so controls stop being reinvented per runner | Known-answer synthetic events, shuffled-label null, unchanged-passage null, matched-decoy construction as library code; a runner passes the harness before its numbers count | ~1 day, gates G129 |
| **G130b · the decisive lexical-matching control** | L42's relabel hangs on this. If "content" stops being identifiable once lexical sophistication is unavailable as a shortcut, L42 was another sophistication measure | Match content and surface revisions on insertion/deletion size, word-count change, word rarity, sentence position, original difficulty, feedback-prompted or not; re-run purpose classification on the matched set | ~2 h once G129 runs |
| **G131 · the factorial choice-structure benchmark** | The ladder varies specification count and cannot separate target from amount from coupling from realization. Four factors the theory treats as distinct | Paired artifacts from same base material, matched vocabulary, instruction count, topic, register, length. Crossings answer which construct the dose-responsive quantities track (prompt pressure, intent density, instruction volume, integration, or embodied choices). Specification recovery rebuilds here with candidates differing by **structural consequence**, not echoable words | design ~1 day, generation ~2 h |
| **G132 · ScholaWrite as process evidence** | Dense longitudinal keystroke and intention records, nearly 62,000 edits, but five preprints, so five top-level units and weak population evidence. Complementary to ArgRewrite | Do decision traces persist into finals; does recovered ordering match real ordering; do integrated changes trace differently from isolated ones; do reader entry points coincide with real revision events. Nesting stays explicit in every number | import ~2 h, analyses ~1 day |
| **G133 · the commissioned crossed pilot** | Public cross-domain corpora vary topic, not kind; the search became a time sink. Four makers suffice to debug measurement and estimate variance, not to support claims | Cross domain familiarity, effort condition, revision target, and at least two artifact kinds. Record brief, version history, post-task decision cards, alternatives considered, independent quality judgments, later blind recovery by multiple readers. No think-aloud, it changes the process. **Blocked until the harness recovers known synthetic decisions without lexical shortcuts.** Reader agreement is reliability, not validity | his sourcing + design ~2 days |
| **G134 · the estimator tournament in the parent simulation** | A statistic gets tested where ground truth exists first, and the variational solver once returned a confident wrong answer that exact inference corrected | Small decision-generating world; compare direct choice recovery, residualisation after predicted expertise, constrained joint inference, no-values baseline, identity-only baseline. Exact inference first, PyMDP as approximation check. Deliverable is a **failure-boundary map** (expertise error, artifact count, kind diversity, commission alignment, drive visibility, concealment, reader misspecification), not an average | sim-side, brief to ghost-scale |
| **G135 · held-out tradeoff prediction** | The residual hypothesis survives only if an inferred profile predicts unseen choices across kinds. Biography resemblance is not ground truth, and humans confidently overread makers too | Infer profile from several artifacts; present a new kind containing a real tradeoff; predict the compromise; compare against expertise plus brief plus context without the profile; repeat under commission | **blocked on G133 + G134** |

**Deprioritized by the program, by name.** Detector benchmark races. Feature stacking before choice
recovery validates. Entropy, compression, effective complexity, component counts, centroid
distance (L29 showed the failure). More global averages (L35 showed the failure). More transformer
address searches, since the transferable result is tracking, and architecture work now supports an
artifact criterion rather than becoming the criterion. Values from the 34-book corpus, which
establishes identity capacity and nothing more without behavioral tradeoffs. Interest ratings as
ground truth (still useful inside `READER_HEURISTICS`). Alignment experiments, per the dormancy
ruling in `ALIGNMENT.md`.

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
| **E3 · interest = unexplained decisions** | Interest comes from decisions you cannot attribute meaning to. Aesthetics is **ordered** unexplained decisions | Two tests. **(a)** Reader-reported interest as an instrument. Ask the curator to rate interest per artifact and correlate against every measure we own. Cheap, and per the program these ratings inform `READER_HEURISTICS` only, never ground truth, since interest may reflect fluency, novelty, confusion, or personal relevance. **(b)** Operationalise "ordered but unexplained" as effective complexity and check it is not just entropy | (a) an hour of his time · (b) ~1 h |
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
| **G114b · rebuild the convergence discriminator** | v2 ran and discriminated nothing (L35): agreement flat across a ten-spec dose gap and highest on maker-less text — the token-overlap metric reads topical narrowness before latent intent, and the essays group died to a file-extension assumption | Topic-matched groups (same topics across all five), graded answer-similarity (local-model pairwise rating or embeddings) instead of token overlap, essays-path fix; then the H2-vs-flattened collision is actually adjudicable | **done (L46): NEITHER-CLEANLY — fixed-topic dose gap −0.02, wrong sign; the judge saturates near 0.9 on all coherent text. Three designs, zero dose sensitivity** |
| **G114-retire · the convergence family retires** | Three operationalisations (bits, token overlap, judge-rated similarity) each failed to make reader convergence move with dose; the third produced orderly numbers with no dose in them | **Resolved by the program (2026-08-09), which deprioritizes global-average measures by name.** The family's question survives only in event-level form, whether independent readers recover the same recorded *choice*, which the G130 harness measures for free as reader disagreement | closed |
| **G116 · Kolmogorov and the average fish** | Two essay claims never tested: machine text "lacks the high Kolmogorov complexity inherent to biological constraint satisfaction," and generation is "regression toward the mean" | (1) incompressibility (lzma ratio) vs rung, length-partialled, three ladders; (2) feature-space centroid distance, human vs machine (register uncontrolled — flagged) | **done (L29): NO-TRACK on all ladders; no human-machine compressibility gap (0.4552 vs 0.4562); centroid ran backwards. A register-matched centroid test is the only live remnant** |
| **G121 · loop locks must record Windows pids** | The lock files store MSYS `$$`, which maps to nothing in Task Manager — the 08-07 day loop survived every kill for two days and spawned overlapping lineages (the real cause of the overnight timeouts) | Both `run_forever_*` scripts write `$(cat /proc/$$/winpid)` beside the msys pid; the night trap kills by winpid process tree; the mutual-exclusion guards check winpid liveness | infra, ~30 min |
| **G120 · queue stage timeout starves heavy arms under shards** | Six overnight arms burned two hours each into TIMEO: two shards co-loading 3B-class models thrash the 12 GB card. The 120-min stage timeout is right for solo runs and wrong under contention | Either per-stage timeout scaled from `est`, or a `heavy: true` stage flag the night script serialises; cheapest: keep heavy arms out of multi-worker nights | infra, ~1 h |
| **G119 · positional polish needs a small-window cache** | PD-1/PD-3 (the definitional polish/depth test, never run) needs within-artifact position series; the argrewrite cache has one window per essay at the 200-word setting | Add a window-size argument to `build_features`, build `argrewrite` at ~80 words to its own cache file, then positional variance of polish-proxy features: human drafts should move, machine ladder text should be flat (PD-3) | **re-queued 08-09 after a false start (L43): v1 built the cache at the old window size and verdicted on zero essays; window plumbing, zero-data guard, and the depth feature list all repaired** |
| **G113 · separate echo-carried from echo-inevitable** | The strict echo restriction kills spec recovery on the held-out ladder — but honouring a specification inevitably shares its words, so zero-overlap exclusion removes exactly the executed specs. The unrestricted echo–bits correlations were ~0, which points the other way | Graded overlap thresholds (score at ≤10%, ≤25%, ≤50% shared content words) and a function-word-only scoring arm, where echo is impossible by construction; the pre-registration's intent survives if recovery holds anywhere below full overlap | design first, ~half day |
| **G112 · characterise the gpt2 mirror** | L28: gpt2-medium's early/late ratio *rises* with intent at Qwen's strength under the same fair control — a sign flip, not a null | Per-layer correlation profile against the loci fractions: do 7%/76% of depth straddle opposite-signed machinery in gpt2? The per-layer maps (L12) already exist for this comparison | ~1 h CPU |
| **G104 · finish the 11-family matrix** | The cross-family replication table has empty cells: four families never ran the first and extreme ladders, and seven of eleven never got depth readouts | Depth sweeps for Qwen2.5-3B, SmolLM2-1.7B, gpt2-xl and pythia-2.8b on both missing corpora; depth readouts for four more families | **queued 08-08** |
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
| **PD-33 · decompose the essay-boundness split by author and draft** | L55's accidental positive: polish-side features are 2.5× more essay-bound than depth-side at fixed topic, and "essay" conflates author with draft stage | Recompute the between-share with author as the grouping unit, then draft-within-author; if the polish side's share follows the author, the maker-signature reading stands; if it follows the draft, it is revision state | ~1 h, cached |
| **re-audit every length-killed measure for DIRECTION** | **known weakness 3b, and it is the most likely place a real result is buried.** Length turned out to be a *suppressor* on the layer ratio, not a confound — it was working against the effect. Every measure this project killed on "correlates with length" was killed without checking the **sign** of the relationship against the sign of the effect. At minimum: `scale_gain` v1 (+0.877), the ladder void (+0.403), and every VOID verdict | **the method was wrong, not just the measure.** If even one of the ten deaths was a suppression case, it comes back | **done (L54): one in six effect-bearing features per ladder sat in the suppression regime; readability-ease recurs as the rescue. Bookkeeping only, no revivals chased, per the program** |
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
| **G30 · attention dwell** | Text spent on something past what the argument needs is measurable | The LUST signature and a second leakage channel at once. **Needs a model of argumentative need**, which is the unbuilt part | design first || **G32 · polish late, leakage early** | Polish measures correlate with late-layer structure, leakage measures with early | Uses measures we already own on both sides | ~1 h |
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

## Harvested 2026-08-07 from the theory pass — the triple inference

**Same identifiers as `docs/theory/THE_TRIPLE_INFERENCE.md`.**

| | the claim | the test | cost |
|---|---|---|---|
| **G49 · values are the residue of expertise** | *"Extract the useless parts of the expertise. The useful parts were the parts that are maxed, and we don't want that. **Values are everything else** — everything you accidentally baked in through expertise, extracted over time."* | **It inverts the search.** Every dead measure looked in the *optimised* part of an artifact, which is exactly where selection has flattened the individual out. Needs a model of what a domain's expertise is optimised *for*, which is the unbuilt piece | design first |
| **G50 · what separates a value from a tic** | The value-carrying part of that residual is what survives a **domain change**; arbitrary residue does not | The objection to G49 is that residue is mostly noise with no content. **This is the separator**, and it needs one maker across different kinds of artifact — the corpus every thread keeps arriving at | blocked on corpus |
| **G51 · repetition as the carrier** | *"The way it's baked in implies you've taken those actions many times, and that itself is information."* A habit is evidence a choice was available and repeatedly taken | Measurable as within-maker consistency of a choice where alternatives existed | ~2 h |
| **G47 · drives upstream of process** | *"I would assume that drives are upstream of even process."* Completes the generative ordering | Supplying drives should improve process recovery as much as supplying process improves goal recovery. **The one edge that would distinguish a river from a triangle** | ~2 h |
| **G48 · a maker's weighting is stable within maker** | Values are more stable within maker than between | **The 34-book corpus already supports the design.** The first values test the project has been able to specify at all | ~2 h |
| **G56 · supply a mechanic, not a goal** ★ | Supplied expertise unlocks the rest as effectively as supplied legibility | **Every edge tested so far supplies a goal or a process. None has ever supplied a mechanic.** Also the arm that would falsify legibility-first, and the same operation G49 needs in order to subtract | ~2 h GPU |
| **G60 · the convergence rate** | Recovery error shrinks with more artifacts by one maker, toward a small residual | The disagreement with the impossibility proofs, made measurable. **Report the asymptote, not just the slope** — the theorems constrain how much ambiguity is left and nobody has measured it | sim |
| **G61 · supply competence** | An explicit competence estimate improves goal recovery | If it does, **the "fatal unknown" the proofs call fatal is an input we can provide** | ~2 h GPU |
| **G62 · the teacher assumption** ★ | Assuming the maker intends to be understood improves recovery. **A fourth constraint on the hypothesis space, standard in cooperative IRL, and free** | **Must be tested against concealment cases**, where the assumption is false and would license confident wrong inference. *"When to assume a teacher"* is itself the measurable question | ~2 h |
| **G63 · aesthetics as scaffolding** | Aesthetic structure is partly deliberately-left hooks that make an artifact easier to deconstruct — metacommentary, high-level metaphor that lets a reader move down through the levels | Would make polish partly **communicative** rather than only performative, which is a different claim from anything in `DECISION_TRACES.md` | design first |
| **G64 · re-reading recovers the tail** | Depth of reading substitutes partially for breadth of corpus | **G49 says the tail is where the un-optimised residue lives**, so this and the values claim are the same bet from opposite ends | ~3 h GPU |
| **G65 · works per maker** | Value recovery improves sharply with more works per maker; goal recovery does not | Two-level design; tests G48 at the same time | blocked on corpus |
| **G66 · graded adherence** | Degree of alignment to a declared value set is recoverable as a graded quantity | **A ladder made of humans**, which is what every corpus we hold fails to be. **One sourcing effort unblocks three sections** | sourcing |
| **G52 · values composed with process** | What an artifact exposes is values already pushed through the maker's expertise | **The cheapest discriminator among the three policy-mapping claims** — if removing process from the reading changes what is recovered, the composition is real and G49 has something to subtract | ~2 h GPU |
| **G53 · is attention doing work?** | Attention distorts the mapping, rather than papering a gap | Flagged as suspect by its own author. **Any design leaning on it must state what would show attention is not needed** | design first |
| **G54 · every drive partially satisfied** | Values are the constraint that all active drives are partially satisfied at once, not a separate factor | A build, in the parent simulation | a build |
| **G55 · diversity vs expertise** | Motivational diversity rises with expertise while agreement about purpose stays flat | **Must survive a difficulty control — neither of the two attempts so far would have.** G49 depends on this: if expertise does not move decisions into drives, the residue of expertise is not where values live | ~2 h |
| **G57–G59 · the untested edges** | Prior information at any vertex improves recovery at the others; entry is possible at any sub-level; closeness is a prior held before the artifact is seen | **One edge of six has ever been measured.** G59 is the only place in the theory where the reader's prior relationship does the work rather than the text | ~2 h each |

## The alignment claim — all unsearched

**Same identifiers as `docs/theory/ALIGNMENT.md`. Nothing here has been checked against anything.**

| | the claim | the test | cost |
|---|---|---|---|
| **AL-4 · the manipulation shortcut** ★ | Making humans easier to read — simpler, more predictable, more uniform — lowers uncertainty, so **manipulation is *closer* under a naive reading of the objective** | **Do this first.** It is cheap to reason about and fatal if right, and it is the same structure as this project's own recurring error: an instrument that optimises a proxy destroys the thing. **A proposal that dies to its own second failure mode does not need a priority search** | reasoning, then formal |
| **AL-1 · is the balanced sum novel?** | The terminal value as epistemic + pragmatic value avoids the failure mode that bites *learn W then maximise W* | Literature sweep: assistance games, cooperative IRL, value learning under uncertainty, active preference elicitation, active inference. **None fetched.** He has since said he believes most components are already occupied | research |
| **AL-5 · anti-capture** | Value capture fails structurally because no subgroup can satisfy the appetite for evidence | **Social choice usually argues the opposite** — aggregation is where alignment gets hard. **A collision worth finding** | research |
| **AL-6 · does narrowing raise residual uncertainty?** | Formal version of AL-5 in a toy model | The only row that could be settled without a literature pass. Parent simulation | sim |
| **AL-3 · instrumental intrusion** | An unbalanced information-maximiser has an incentive to experiment on people | Not answerable by a side-constraint — **side-constraints are what this design exists to avoid needing** | reasoning |

## From the human-heuristics and polish files

| | the claim | the test | cost |
|---|---|---|---|
| **PD-28 · polish or depth?** ★ | The within-author revision effect is polish, not depth | **The highest-value unrun row in `DECISION_TRACES.md`.** 5,834 revisions are hand-labelled Surface or Content at 0.71–0.92 agreement. **If it survives among Content-only revisions, that is a depth signal on human text and the first one** | ~2 h |
| **PD-1 · the definitional test** | Depth-side quantities vary less across position than polish-side quantities | Never run as stated — the test that failed measured neither density separately. **If both move equally the distinction is not real** | ~2 h |
| **PD-3 · flat polish as the machine signature** | Machine artifacts show polish that does not move across position | **Sharper than any depth-based discriminator and needs no quality judgement** | ~2 h |
| **PD-15 · attention dwell** | Text spent past what the argument needs is measurable | The LUST signature and the second leakage channel at once. **Needs a model of argumentative need**, which is the unbuilt part | design first |
| **HH-3 · variance of probe activations** | Within-artifact variance of *activations* carries what surface-feature variance does not | **Burstiness does it with perplexity, PAN with surface style, nobody with probe outputs.** The only route here untried by both the field and us | ~2 h GPU |
| **HH-6 · enter at the anomaly** | Entering at the anomaly beats entering at the whole artifact | **A flag flip, not a build** — `bounded_v6`'s stage zero exists and has never been live. **Temper the expectation: the simulation says ordering changes the answer by exactly zero** | ~1 h |
| **HH-14 · interest ratings** ★ | Reader-reported interest correlates with unrecovered decisions | **An hour of his time, and it turns the one channel that has beaten every measure we own into data.** It also adjudicates between his account and processing-fluency, which predict opposite correlations | his hour |
| **HH-16 · effective complexity** | "Ordered but unexplained" is effective complexity rather than entropy | Operationalise and check it is not just entropy | ~1 h |
| **HH-17 · polish against effort** | The polish–effort correlation is strong in human corpora and near zero in generated ones | **Blocked on an effort proxy, and automaticity makes effort unobservable by construction** — the same fact that puts values in the residue. Any proxy needs its own defence first | design first |
| **G67 · the teacher assumption on generated text** | Readers grant intention-to-help to generated text, and that is why it misleads | **A claim about readers, not models.** Different from the polish–effort account, and the two predict different things when provenance is disclosed | ~2 h |

## Next up — 2026-08-07, from the specification-recovery result

**The measure that just passed recovers how much specification a prompt carried, against 48
topic-matched decoys. Win rate went 52.5% → 66.3% → 91.7% as the manipulation went from ten short
specifications to sixty.** These follow directly from it.

| | the claim | the test | cost |
|---|---|---|---|
| **G68 · where does human text sit on that scale?** ★ | Human artifacts should behave like a very high rung — a person writes under an enormous implicit specification | **The direct measure cannot run**: it needs a known specification and human text has none. **The version that does run inverts it.** Instead of recovering a *given* specification, generate N candidate specifications for an artifact and measure **how sharply the artifact discriminates among them** — dense intent should separate candidates cleanly, thin intent should not. **Calibrate on the ladder first**, where the answer is known: if the candidate-generation version reproduces 52.5 → 66.3 → 91.7, it is measuring the same thing and can be pointed at human text. **Without that calibration step the human number means nothing** | ~4 h |
| **G69 · does the intent signal move deeper as rung rises?** | *"As intention increases, later layers have to be used to extract it."* Strongest layer was 14, 19, 23 across three ladders of increasing strength | **Between-ladder is confounded three ways.** Ask it *within* one corpus: split by rung and find where the signal peaks for each. **Running now** | free |
| **G33 · late coherence against goal clarity** | Late-layer coherence should rise with rung; middle-layer should not | Pre-registered and the depth sweep has been emitting the ingredients all along. **Running now** | free |
| **G70 · bits recovered on the no-maker corpus** | The specification-recovery measure should return **nothing** where there is no maker | **The control that the layer correlation passed and this measure has never been given.** Until it runs, the specification-recovery result has one fewer control than the measure beside it | ~30 min |
| **PD-33 · do the accounts of machine-text unease dissociate?** | Broken polish–effort, flattened intent, missing translation and wrong shape may be four views of one latent cause — **missing mid-level affective primitives** | **If any one can be manipulated without moving the others, they are not one thing.** The cheapest arm is translation, because translation structure is countable | design first |

| **G70b · no-maker control for specification recovery** ★ | The bits measure should return **nothing** on text with no maker | **The strongest new result has one fewer control than the measure beside it.** The layer correlation was DEAD on no-maker in 11 of 11 families; specification recovery has never been run there. **Queued** | ~30 min |
| **G71 · why does gpt2-large fail everywhere?** | The per-layer correlation is DEAD on all three ladders in gpt2-large while smaller models survive | **Failures cluster by family, not by scale.** Points at tokenizer or training data rather than capacity. Cheap diagnostic: does gpt2-large also fail the affect-direction fit that everything else passes? | ~1 h |

| **G72 · why does the middle not move?** ★ | Coherence falls with rung at early and late depths and **does not move in the middle**, replicated across three ladders. Is that the noisy middle the architecture predicts, or an insensitivity of the coherence measure at that depth? | **Discriminate with a positive control**: construct a manipulation the middle *must* respond to and check the measure detects it there. If it does, the null is real and it is a dissociation in the load-bearing band | ~2 h |

## The void audit — 2026-08-07

**Every result recorded VOID or INCONCLUSIVE, re-assessed against what we now hold that we did not
then: eleven model families, a length-controlled extreme ladder, a no-maker corpus, 86 humans × 3
drafts, six years of topic-controlled style-change data, 43k human-labelled emotion comments, and a
GPU.**

| | what was voided | why it died | re-runnable now? |
|---|---|---|---|
| **V1 · the founding question** ★ | *Some measure ranks five rungs of specified intent* | Voided on its own pre-registered ceiling: rung and length correlate at 0.40 against a 0.40 limit | **YES, and the ceiling itself was wrong.** The 0.40 is a *rank* correlation over a **4.2% length spread** — 58 words on a 1,400-word median. Ladder 3 halves the spread to 1.9% and the rank correlation is unchanged at 0.414, because Spearman is scale-free. **A criterion that cannot tell a 4% difference from a confound.** Re-scoring now |
| **V2 · reader displacement varies more for machines** | Three artifacts | pure sample size | **YES, trivially.** 150 ladder artifacts, 36 no-maker, 86 authors × 3 drafts |
| **V3 · a reader refuses differently on human and machine text** | Pass condition had a **50% false-positive rate by arithmetic** | broken threshold, not broken design | **YES**, with a pre-registered threshold and power computed before the run |
| **V4 · function words separate maker states** | 38% power | short texts — at 380 words the pronoun rate gives **five tokens**, and the statistic divides by a variance made of Poisson noise on five counts | **YES, on longer text.** The 34-book corpus is 22M characters; ladder artifacts are 1,400 words. **D-0's own power analysis says exactly what to fix** |
| **V5 · purpose × affect separability** (D-0) | Same cause as V4 — the design could not have detected what it looked for at that text length | | **YES, same fix** |
| **V6 · affect-isolated decomposition** | Shuffling the labels changed the count not at all — found Reddit text confounds topic with emotion | the isolation step never ran | **YES, with topic-controlled generation** rather than found text |
| **V7 · half A contains more recoverable method than half B** (Gate 3) | Statistic reads a large positive where truth is zero; **and 76 features separate the halves**, so almost any measure would | corpus is confounded and has been read too many times | **NO on that corpus.** Needs a fresh one, and the question should be re-specified as singularity of terminal value |
| **V8 · the values vertex carries no information** | A single-artifact model cannot represent a quantity defined only across artifacts | | **NO — a build, not a re-run.** Scoped in `../sim/` |

**Six of eight are re-runnable, and two of those were killed by a criterion rather than by a result.**

| | the run | cost |
|---|---|---|
| **V1** | re-score the extreme ladder now that the ceiling is understood | running |
| **V2** | displacement variance at n = 150 rather than n = 3 | ~1 h |
| **V3** | refusal with a threshold whose false-positive rate is computed first | ~1 h |
| **V4 / V5** | function-word separability on book-length text | ~2 h |
| **V6** | affect decomposition on topic-controlled generated stories | ~4 h |
| **G102 · prior-art sweep before claiming originality** ★ | *"No one else is tracking layer ratio with respect to intent"* — his call, 2026-08-08 | Inline literature sweep (no agents needed): layer-wise affect ratio vs prompt specification, probing-by-depth vs instruction density. **Owed before any public claim** | ~1 h inline |

## Corpus sourcing — 2026-08-07, the one-maker-many-kinds problem

**Three hypotheses are blocked on the same corpus and it turns out to be genuinely rare rather than
merely unfound.** The cross-genre authorship literature describes its own data as *"scarce and very
limited in size"*, and most corpora carrying a "cross-domain" label are cross-**topic** underneath.

| | corpus | kinds | makers | why it may not work |
|---|---|---|---|---|
| **C-30** | **CROSSNEWS** | bylined news articles vs the same journalist's social posts | 53 with both in a 40k-row sample; hundreds in full | **SURVEYED, and the survey is the problem.** Articles are fine — median **883 words**, 42% over 1,000. **Posts have a median of 17 words and *none* reach 300.** Usable only as pseudo-documents |
| **C-31** | **Guardian cross-genre** | opinion articles vs **book reviews**, both ~1,200 words | **13 at best, 5 in the accessible copy** | Under the 20-maker minimum, copyrighted, no clear licence. **But the kinds are comparable in form**, which CROSSNEWS's are not |
| **C-32** | **CMCC** | blog · email · essay · chat · discussion · interview, crossed with 6 fixed topics | 21 | **Exactly our design** — a deliberately crossed maker × kind matrix. **No download page found**; request-only until proven otherwise. Chat and email are short |
| **C-33** | longitudinal multi-domain, ~412 authors × {abstracts, blogs, news} | three real kinds | 412 | **Unverified** — repo referenced but not opened, identity method and licence unknown, abstracts likely under 300 words |
| — | PAN cross-domain attribution (2018–2021) | **DEAD END** | — | *"Cross-domain" means cross-fandom.* Every artifact is fan fiction — same genre, register, audience, purpose. **It varies topic, not kind**, which is the axis the whole hypothesis turns on |

**The objection that applies to CROSSNEWS and not to the Guardian, and it is the important one.** A
17-word post and an 883-word article do not differ by *kind* in the sense we need — **they differ by
medium, and length alone separates them completely.** That is the Gate 3 trap: two halves so broadly
different that almost any measure separates them, so separating them is never evidence. **A kind
contrast is only informative when the kinds are comparable in form.**

| | the job | cost |
|---|---|---|
| **C-30a** | Re-survey CROSSNEWS at 500k rows — 40k rows is 2.7% of it, so a maker's second genre may simply not have appeared | ~20 min |
| **C-30b** | If pseudo-documents are accepted, **state what changes**: a concatenation of a person's posts is a *sample of their writing in a register*, not a thing they made. **Legitimate for the relation test, illegitimate for anything within-artifact** | design |
| **C-31a** | Chase the full Guardian corpus, 13 authors. **Fewer makers but a fairer kind contrast** — and it may be the better test despite the size | sourcing |
| **C-32a** | Write to the CMCC authors. **It is the only corpus found that was built for exactly this question** | an email |

| **G76 · the function-word induction control** ★ | Classifying rung from function words may be reading style the prompt **induced** rather than a maker state | **The stage queued for this ran a runner with no `--corpus` argument and silently re-reported the held-out ladder's layer-ratio numbers.** The control does not exist and must be built as an arm of `run_void_power.py` — regress the function-word vector on specification identity out-of-fold, then re-classify | ~2 h |
| **G77 · refusal with a threshold that can fail** | A reader refuses differently on human and machine text | **The re-run used the threshold that voided it.** Three of five components under a null of no difference is five coin flips: P(at least 3) = 0.5 exactly, so PASS at exactly 3 is the modal outcome of nothing. **Replace with a permutation test and report the false-positive rate before the verdict** | ~1 h |
| **G78 · which subtraction is correct?** | Partialling out is linear and assumes the nuisance is additive and separable; the habit-shadow objection says it is neither. IRL constrains the reward class instead of regressing out a component | **Plant a known residual under a known nuisance in the simulation and see which recovery method finds it.** Settles the vocabulary before either is committed to | sim |

## Harvested 2026-08-07 from archaeology and connoisseurship — techniques, not citations

**Three subagents. Most of these are cheap because the thinking is already done.**

| | the technique | the test | cost |
|---|---|---|---|
| **G85** | **The intent ladder already IS the Nonaka intention-elicitation protocol** — specify first, produce, measure recovery. Validated on stone since 2010 | **Nothing to build.** What to take is the calibration ceiling: **expert knappers reach R² = 0.655 against their own stated intention.** Re-read every null in the project against that ceiling rather than against perfect recovery | free |
| **G86** | **A mechanical null model** — model what the medium forces, call only the residual a choice | The one thing chaîne opératoire never built, and **the same subtraction the depth redefinition needs**, with the nuisance derived rather than assumed. For text: predict the artifact from genre + length + prompt alone, treat the residual as candidate choice | ~3 h |
| **G80** | **Reserve versus overpaint** — did the structure make room for a claim, or was it inserted into a structure that does not accommodate it | **Computable on one static text with no version history.** Separates load-bearing commitments from bolted-on ones | ~2 h |
| **G81** | **Self-revision is homogeneous and continuous; an imposed hand is lumpy and discrete** | Author vs editor vs co-author vs tool. **Distributional, not semantic** — and the discriminator this project needs most | ~2 h |
| **G79** | **The four-part Morellian admissibility filter**, criterion 4 especially | **It predicts where habit is switched off.** Elegant variation suppresses individual signal exactly where our measures currently see most variety | ~2 h |
| **G88** | **Error handling rather than error rate** | Novices thrash on a ruined surface; experts abandon or repair. **Measures metacognition, not execution** | ~2 h |
| **G89** | **Rigidity under perturbation as the novice signature** | An **active probe**: change genre, length or audience and measure whether quality is preserved | ~3 h |
| **G87** | **Partition features by visibility and acquisition age** | Low-visibility early-acquired features track deep identity; visible ones track situational identity | ~2 h |
| **G92** | **Inter-annotator agreement before any extraction is believed**, and per-feature accuracy rather than an aggregate | **Their aggregate of 72.6% concealed a 43.3% category, worse than chance.** And a published study found that agreeing definitions in advance was *not sufficient* | ~2 h |
| **G93** | **Does a reliability filter remove signal?** ★ | The 2026 rebuttal says selecting attributes *for* replicability privileges the trivially measurable over the behaviourally meaningful. **Our 342-feature funnel drops features that fail filters** — if the meaningful ones are systematically the hard ones, the funnel removes signal and looks like rigour | ~2 h |
| **G94** | **Run our own Taramsa test** ★ | They reconstructed sequences by the standard method at a site where refits gave the truth, and **the method invented a production stage that never happened.** Our analogue: reconstruct intent on a corpus where the true specification is known — **which is the ladder** — and check not just correlation but **whether the reconstruction posits things that were not there** | ~2 h |
| **G83** | **Adopt the graded attribution vocabulary** | Three axes at once, and **"workshop of" is the mixed human-and-tool provenance category we would not have invented** | free |
| **G90** | **Report separability as a cross-validated confusion matrix** | *"These two processes separate at 80% on this feature set"*, never *"we can read the maker"* | convention |
| **G95** | **Report composition, not labels** | Tostevin's wine analogy: a château name cannot tell you how similar two wines are; a *cépage* can. **"40% attractiveness-directed, 25% teaching-directed, 35% residual" is arguable; "high depth" is a label** | convention |

| **G96 · the expedient-intent test** ★ | Have the **same maker** produce the same artifact carefully and hurriedly, and ask whether the measure separates hurried-expert from genuine-novice | **The single largest untested confound in the archaeology literature, unrun by anyone in any medium** — they cannot commission a Palaeolithic knapper and we can commission a writer. **Our README already claims "firing on hurried human work is the measurement working," and that claim has never been tested** | ~3 h + writers |
| **G97 · maker as a random effect** | Every skill study compares group means across individuals, pseudo-replicating artifacts within makers. **The one study that used hierarchical models found skill effects mostly vanish** | Re-analyse our within-maker results with maker as a random effect. **If our effects vanish too, we have been measuring individuals rather than the quantity** | ~1 h |
| **G98 · are our errors clustered?** | Overshoots in a 100-core sequence *"recurred in bursts separated by runs of properly constrained strikes"* — **clustered, not Poisson** | Check the dispersion of any error-like feature we extract. **An error rate on a small sample measures which burst you sampled** | ~1 h |

| **G105 · a coherence statistic that can measure agreement** | The audit (L26) proved the current one cannot: globally centred directions sum to zero, so 8-way agreement is geometrically impossible and the recorded number is an arbitrary-axis projection, sign-unstable across refits | Mean pairwise sign agreement of projections onto uncentred per-concept contrasts — **with a known-answer validation on synthetic agreeing/disagreeing data before any real read**; then re-adjudicate G33 and the depth-sweep middle verdicts | **done, all eight families (L47): every gate passes; 0 of 24 cells rise with dose, agreement FALLS in the Qwen family — G33 rejected in direction. Sub-chance baseline observation unclaimed** |
| **G106 · rebuild the affect-count instrument** | Four independent defects (L26): participation-ratio correction misattributed and scale-fragile, bi-cross-validation pinned at its cap in 135/138 fits, shuffle gate arithmetically unpassable, VAD reference written from memory (18/28 entries off by >0.1) | Column-standardise before the SVD; implement the cited estimator or drop the citation; raise the cap and treat boundary argmin as no-selection; gate on a statistic with a known direction under label destruction; **vendor the real NRC-VAD with a checksum** | design first |
| **G107 · a permutation null for the no-maker control** | 5 of 11 no-maker runs fire under the computable rule (L26); the flagship's fires [5,7,13,17,21] overlap its held-out-ladder survivors 3-of-5, and layer 21 fires everywhere including maker-less text | Save per-artifact signal rows in `run_layer_correlation` (done), then a label-permutation null for the joint rule and the overlap — decides clustered luck vs a real label leak | **queued for the night** |
| **HH-3 · activation-series variance, queued at last** | The §1 heuristic's untried operationalisation — within-artifact variance of *probe activations*, which burstiness (perplexity) and PAN (surface style) never did | The reader's early/late ratio per window as a positional series; books-vs-machine at matched series length (PD-3's flat-machine signature) plus rung-vs-variance on two ladders | **queued for the night** |
| **G122 · causal patching of the affect geometry** | The build's decisive gate: everything decodable so far could be a correlate. *"Move from decoding to causation"* | Patch, erase, or steer the recovered subspace and measure whether goal/process inference changes while lexical and topical performance hold; causal-abstraction methods are the standard | design ~1 day |
| **G123 · the unique error fingerprint** | The missing-middle prediction risks collapsing into generic emotion probing without its distinctive signature | Hold surface affect, category, goal, and expertise constant while varying the latent drive explanation; ask whether drive ambiguity specifically produces the predicted goal-inference failure | design ~1 day |
| **G124 · align families by computational events, not depth fractions** | Fixed block addresses have failed to transfer everywhere we looked; the 7%/76% loci are Qwen-shaped | Representation change-points or CKA across families, then re-test the flagship at aligned stages — may explain the sign map (G112's best route) | **done (L45): the events are portable — early locus lands in the first sixth in 4 of 5 families, late at 62–83% in all 5; SmolLM2 refuses the alignment (28% deep), the sign-map exception again** |
| **G128 · a permutation null for the event alignment** | The alignment's best-match assignment (L45) has no null: with 25–37 blocks per family, some lawful-looking landing pattern may fall out of any smooth similarity matrix | Recompute the block-matching on label-shuffled and phase-scrambled text pairings; the landing depths should scatter if the alignment is real and persist if it is an artifact of smoothness | ~1 h, cached activations |
| **G125 · commissioned human work for the absent-drive signature** | S-14 is proven as method in simulation (V11: perfect under commission, compliance collapses to 0.5); only real work can establish the real signature | Same brief, repeated makers, multiple artifacts, independent records of process and motivation — his side for sourcing, ours for design | blocked on people |
| **G126 · per-block contribution and d′ readouts** | The analogue research names what our profiles should have been measuring: the per-block *write* (what BOLD actually tracks), the signed *affect work* that telescopes to the final projection, and per-block d′ as the honest signal-to-noise | Add the three quantities to the readout path (cached states make two of them nearly free), plus the rogue-dimension QC alarm; then re-read the address-umbrella claims in the new units | **done, all eight families (L48): QC clean everywhere; write/work geography maker-blind and input-edge-concentrated universally; d′ placement lawless — Qwen early at both sizes, other families scatter with size reversing direction; home-family selection caution filed in the entry** |
| **G127 · the pooling falsifier** | Extraction choice systematically biases layer-wise conclusions (Hadidi 2025), and every profile we own mean-pools | Re-run the flagship ratio and one per-block map under last-token and max pooling; if the early/late shape moves, every address claim inherits the caveat | **done (L44): SPLIT — the profile geography is pooling-invariant (r ≥ 0.98, same peak block); the flagship ratio changes sign-and-significance class per pooling. Geography stands, ratio falls further** |
| **E7b · follower-corpus sourcing detail** *(moved from the triple inference §10 per the reorganisation — the theory file keeps the blocking rows G65/G66 only)* | The value-ground-truth design: many makers deliberately aligned to one declared value set, read through deep followers, adherence graded | Sourcing candidates: religious traditions, political manifestos, professional codes, open-source governance, movement writing. Construction: hold topic constant (same practical question — money, work, family, obligation, death — answered from within different traditions); founding work analysed separately from followers; degree-of-adherence is the label. Known confounds to design against: canon-formation selection, translation, era; "declared ≠ held" is tolerable because the needed label is what an artifact was made *under* | sourcing, then ~3 h |
| **G43-first · non-affective control subspaces** | The early break gates how every mapping claim reads; if syntax/topic/frequency/position subspaces all break at the same place, the boundary is the input adapter's edge | Measure four non-affective subspaces identically to the affect one, all eleven families, saved matrices make it CPU | **done, 11/11 (L49): ADAPTER-EDGE unanimous — every subspace type snaps at the affect subspace's block in every family. The break carries no mapping information; the gate resolved deflationary** |
| **G108 · a wider specification pool** | The extreme ladder's decoys exhaust at rungs 30/60 (L26): half the corpus is not the contest its chance figure claims | A 120-spec pool so the complement supplies distinct decoys at every rung; regenerate the extreme contests | corpus build |
| **G109 · stale-reference sweep** | L26 unverified tier: dead filenames (THE_TRIANGLE, THREE_LAYERS), wrong anchors (§8c→§7 etc.), TR-13 orphaned by the rename, `ideate.py` hard-codes an archived path | One pass over the fleet's line list (task output, docs-data findings); fix `ideate.py` before it is ever queued | ~1 h |
| **G110 · TODO hygiene pass** | L26: stale "running now" rows finished days ago, duplicate identifiers (E1=G56, E6≈G48, interest-ratings ×3), done work still listed as owed | Mark done rows with their L-numbers, collapse duplicates to one identifier each | ~30 min |
| **G111 · subspace basis rank fix** | L26 unverified tier: centred 8-vector span is rank 7, so the 8th QR column is junk diluting every alignment ~1/8, and the null band is mismatched to the distant-pairs statistic | Truncate to the nonzero-R rank, centre the null construction identically, match the null statistic to distant pairs; **verdicts stand at current margins** — this is for the numbers, not the conclusion | **done, 11/11 (L50): DEPTH everywhere, no verdict flips — adjacent 0.78–0.96, distant 0.21–0.42, null ~0.05. The v1 rank caveat is retired** |
