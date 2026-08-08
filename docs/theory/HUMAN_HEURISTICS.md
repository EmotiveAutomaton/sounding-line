# Human empathy heuristics — the tricks a person uses when the maker is absent

**A perfect solution exists in principle.** If you could model every neuron of a human brain, the
extraction has an answer — assuming no property of a brain adds randomness we are unaware of.

**In practice it is intractable**, and it converges only slowly: value data accumulated over time from
a variety of stimuli, approaching the answer the way a series approximation does. **So humans do not
solve the triple inference. They run heuristics at it.**

> While I don't expect we will have to rely on these heuristics when designing depth extraction, I
> expect AI will arrive at most, if not all of them, organically. Nevertheless it's worth keeping track
> of the ones we have run into that would be relevant as potential **feature-extracting amplifiers** in
> future, that other research teams may have missed.

**This file is that record.** Fifteen artifacts, two sessions, sixteen readings, one reader — and
**those readings have outperformed every measure we have built.** The curator is the only working
instrument this project has, so describing what he does is describing the thing we are trying to build.

---

## §0. The instrument panel — what each heuristic is worth, measured

**Added 2026-08-07 at the curator's instruction.** A heuristic that has been confirmed is not the same
as a heuristic that is *useful*, and the difference is a number. **Once a heuristic is found to work,
record how well** — because the expectation is that no single one carries enough signal and several
will have to be stacked.

> I'm expecting human heuristics to end up having to **stack a few of these** to extract intent value.

**So this table is the stacking budget.** It says what is available to combine and how much each
brings, and it is the first thing to consult before proposing that some combination will work.

| heuristic | measured strength | against what baseline | status |
|---|---|---|---|
| **polish variation within an artifact** (§1) | **0.565** macro-F1 on the field's topic-controlled task; **0.969 on the easy split, above its published best of 0.959** (audit-surfaced orphan, L26) | floor **0.444**, bar **0.830** (topic-controlled) / **0.959** (easy) | real, **not competitive where topic is controlled** — and above the bar where it is not, which probably means topic is doing the work there |
| **reading enters at an anomaly** (§2) | — | — | never measured. The simulation says stage order changes the answer by **exactly zero**, so expect a cost saving |
| **the confidence trajectory** (§3) | — | — | never measured; we have only ever kept means |
| **depth as a relation to a domain** (§4) | — | — | **blocked on a corpus that does not exist** |
| **enter at mechanics / technique / metaphor** (§5) | — | — | never measured in any direction |
| **interest as unrecovered decisions** (§6) | — | — | **blocked on an hour of his time**, and it is the cheapest unmeasured item here |
| **polish against effort** (§8) | — | — | blocked on an effort proxy, which automaticity makes unobservable |

**Two rules for this table.**

**Report strength against a named baseline, never alone.** *"Separates at 0.6"* is unreadable; *"0.6
against a chance of 0.2"* is three times chance and *"0.6 against a floor of 0.44 and a bar of 0.83"*
is mediocre. **The same number means opposite things depending on what it is next to.**

**Nothing enters this table until it has passed its controls.** A strength recorded before the
induction check is a strength recorded for something that may be reading the prompt. **The one
measured row above has been through its controls; anything added must be too.**

**What the table currently says.** One of seven heuristics has a number — uncompetitive on the
topic-controlled task, above the published bar on the uncontrolled split, which is probably topic
riding rather than the heuristic (L26). **Six of the seven have never been measured at all, and three of those are blocked on
things we could actually get** — an hour of his time, an effort proxy, and one corpus. **The stacking
question cannot be asked yet**, because there is nothing to stack: you cannot combine one measured
signal with six unknowns and predict anything about the combination.

---

## §0a. Techniques harvested from archaeology — and the ground truth we said did not exist

**2026-08-07.** Lithic analysis has spent forty years reconstructing makers from products. **It has a
validation protocol we have been saying nobody has, and we independently rebuilt it.**

### The intention-elicitation protocol — and our ladder is already a version of it

**Nonaka, Bril & Rein 2010, *Journal of Human Evolution* 59:155–167** [READ]. The design is startling
in its simplicity: **before each strike, the knapper draws the outline of the flake they intend to
detach directly onto the core**, in paint marker. Then they strike. The gap between intended and
realised is measured on matched attributes.

| skill grade | flaking success | mean prediction error, lateral axis | intended vs realised length |
|---|---|---|---|
| **experts** | 73% | **8.2 mm** | **R² = 0.655**, *p* < 0.001 |
| intermediates | 61% | 18.9 mm | not significant |
| novices | 54% | 25.8 mm | not significant |

*22 participants, 104 strikes. Skill is measured as intention–outcome fidelity, not as output quality.*

**Two things follow and the second is the more important.**

**Our intent ladder is this protocol.** Specify the intention first, produce the artifact, measure how
much of the specification is recoverable. **We arrived at it independently, and it has been validated
on stone since 2010.** That is a citation we did not know we had.

> **Even experts account for only ~65% of the variance in their own stated intention.**

**That is the most honest calibration target in this report.** Any instrument claiming to recover
intent from a product is working against a ceiling that **expert self-prediction already fails to
reach** — and it reframes what a good result looks like. **We should stop treating the gap between
our recovery and perfect recovery as failure.**

### The mechanical null model — the answer to decision-versus-constraint

**Dibble & Rezek 2009; Li, Lin, Rezek, Dibble et al., PLOS ONE 2020** [READ]. Controlled experiments
on **molded glass cores** show flake size and shape are dominated by two measurable geometric
variables — exterior platform angle and platform depth. Platform width follows mechanically from the
Hertzian cone angle, ~136°, a material constant, and is explicitly **"not under direct control by the
knapper."**

> **Model what the medium forces. Call only the residual a choice.**

**This is the correct shape of an answer to our central problem, and it is the one thing the
chaîne opératoire tradition itself never built.** It is also the same subtraction the depth
redefinition needs — but with the nuisance model *derived from mechanics* rather than assumed.

**The caveat from the same paper is severe:** the model explains high variance in controlled glass and
**"far lower"** variance in real assemblages. **The null model degrades badly off the bench.**

### Recurrence as the criterion of intentionality — and its weakness

**Soressi & Geneste 2011** [READ], the load-bearing sentence:

> *"It is because a gesture is constant or recurrent that it can be interpreted as intentional."*

**That is the repetition claim, named, in another field.** And the honest reading is the one the
harvest supplies: **recurrence is equally consistent with habit, with training, and with a constraint
that is itself constant.** Which is the habit-shadow objection arriving from archaeology.

### Stage-differentiated signal — different features carry different things

**Gosselain 2000** [SNIPPET — the open PDF is scanned images with no text layer]. Different stages of
production carry different social information **because they are learned differently and are
differently visible**:

    fashioning / shaping    embodied motor habit, early apprenticeship, low visibility,
                            highly resistant to change  ->  deep group boundaries
    decoration / surface    highly visible, consciously borrowed in contact  ->  fluid,
                            situational identity
    clay selection          tracks local environment, not identity at all

**This is the leaked/emblematic split and the polish split, arrived at from pottery.** The text
partition it implies: **sentence rhythm, clause-embedding habits and punctuation reflexes** are
low-visibility and early-acquired; **vocabulary, formatting and structural convention** are visible
and easily copied. **They should carry information about different things at different scales**, which
is a structural hypothesis rather than an analogy.

### Error handling beats error rate

**Val Lastari core-skill study, *Lithic Technology* 49(4), 2024** [SNIPPET, 403]. The diagnostic is not
the error but the response. **Novice cores show "insistence and stacked steps"** — repeated failed
strikes on a surface already ruined, errors compounding. **Expert cores show hinges that "determine
the abandon of the core"** — the expert recognises an unrecoverable state and stops, or executes a
corrective removal.

> **Error rate is a weak signal. Error handling is a strong one**, and it measures metacognitive
> self-monitoring rather than execution quality.

### Rigidity, not error, is the novice signature

**Roux & Bril 2005; Bril et al. 2010** [SNIPPET]. Expertise shows as **invariance under perturbation**
— experts adjust their striking movement to a changed hammer weight so that kinetic energy at impact
stays constant. Low-skilled artisans **"had great difficulties adapting to new raw material (glass
instead of stone), revealing rigid skills."**

**This suggests an active probe rather than passive reading:** perturb the task — change genre, length,
audience — and measure whether quality is preserved.

### Three reliability numbers that should frighten us

| | |
|---|---|
| diacritical scar-ordering error rate | **21% overall**, 25% for beginners, **15% even for experts**, and errors are *"not random but mostly in specific-difficult places"* |
| blind test, heat-treatment diagnosis | **72.6%** overall — but **43.3%** for one material, **worse than chance**, hidden inside the aggregate |
| inter-analyst reliability for chaîne opératoire coding | **it exists, and I recorded the opposite an hour ago.** See below — the correction matters more than the original claim |

**Two rules follow directly:** report **per-feature** accuracy rather than an aggregate, because the
aggregate hid a 43% category here — and **measure inter-annotator agreement before believing any
extraction.**

### The reliability study does exist, and its result is worse than its absence would have been

**Correction to what I wrote an hour ago.** I recorded that no inter-analyst reliability study exists
for this coding step. **One does**, and it is the most rigorous thing in the harvest.

**Pargeter et al. 2023, *American Antiquity* 88(2):163–186** [READ, full PDF, open access]. **Eleven
analysts, 100 flakes, 38 attributes, two years**, all flakes knapped by one person, analysts blind to
which of two production strategies each came from.

| attribute class | result |
|---|---|
| **ratio** — mass, dimensions, technological length | **10 strong, 7 substantial, none below** |
| **discrete** — dorsal scar counts by sector | only the total and the proximal sector reach substantial; **the rest fall below** |
| **nominal** — plan form, edge shape, cross-section, **platform morphology** | **5 strong, 4 substantial, and 7 below substantial** |

**The failures concentrate in exactly the interpretively loaded attributes**, and the Levallois-specific
finding is the one that should worry us most: **platform morphology agreement was 0.22 *worse* on the
Levallois assemblage**, and four of five scar-sector discrepancies came from it. **The attributes that
diagnose the sophisticated method are the least reliably coded.**

**Two findings that generalise past lithics.**

> **Years of experience had no effect. Training background did.** *"Increasing replicability in lithic
> analysis is more about changing training than increasing experience per se."*

**And they agreed a unified set of definitions in advance and still found significant disagreement.**
Shared definitions are not sufficient.

**The defence, published 2026 [SNIPPET], and it is a real dilemma rather than a dodge:** selecting
attributes *for* replicability **privileges the trivially measurable over the behaviourally
meaningful** — and their named example is platform morphology, precisely the attribute that failed.
*"Discarding attributes because differently-trained analysts disagree risks discarding data that are
crucial for meaningful inference."*

> **That cuts directly at us.** Our 342-feature funnel drops features that fail a filter. **If the
> meaningful features are systematically the hard-to-code ones, a reliability filter removes signal
> and looks like rigour while doing it.**

### The falsification test they ran on themselves — and it is the most damaging result here

**Bar-Yosef & Van Peer 2009, *Current Anthropology* 50(1)** [READ, full text plus all seven comments
and the authors' reply]. They took a site with a **65% refit rate** — where the true sequence is
physically known — reconstructed two sequences by the standard mental method, and **compared the
reconstruction against the refits.**

| what the mental reconstruction said | what the refits showed |
|---|---|
| a "preferential Levallois flake" | refits onto a *unipolar-recurrent* blank |
| a "unipolar-recurrent" series | part of a *bipolar* exploitation |
| three "centripetal-recurrent" flakes | **not Levallois flakes at all** — convexity-maintenance flakes |
| a "centripetal-recurrent method" present in the assemblage | **no evidence of it whatsoever.** The method was an artifact of the analysis |
| a blank read as an **early**-stage product | **the 25th flake of 37** |

> **The model invented a production method that never happened, and misdated a late product to the
> beginning of the sequence.**

**And the formal categories dissolved at the individual scale.** Four technical groups were resolved
into four individual knappers — **each of whom produced the entire formal range.** *"From a
behavioural point of view, it seems that our formal categories have little significance."*

**Their own footnote:** the two analyses *"should have been independently performed by two or more
analysts, whereas they have now been executed by the same person."* **n = 1.**

**The honest scope of the critique, because it is routinely overread.** The authors **conceded the
defence in their own reply**: *"we concur with the general consensus that the problem is not with the
operational sequence concept itself but with its implementation."* **Anyone citing this as a refutation
of the method is overreading its authors.**

### Four more attacks, and each has a version aimed at us

**The desired-product fallacy.** *"It is within our framework of reference that the predetermined
product looks as if it must have been the desired product, not within theirs."* **Our version: the
feature we find most recoverable is not thereby the thing the maker was trying to do.**

**Operational sequences do not imply agency.** Davidson's comment: sequences exist in carcass
disarticulation with no agency at all, so *"demonstration of OS alone does not establish either agency
or intentionality."* **And his inversion is sharper** — non-Levallois flakes show use-wear *more* often
than the supposedly desired Levallois ones. *"They almost look like accidents."*

**The return of the expert, named from inside the French tradition.** Djindjian: *"les études de
chaîne opératoire depuis le milieu des années 1980 ne font appel à aucune quantification"* — a
deliberate reaction against the quantitative turn, replacing argument with **"un retour de l'expert,
qui serait seul capable, par l'expérimentation."* Tostevin's version: *"the absence of standard
reporting of data produces a scientifically unconvincing argument beyond the appeal to authority."*

**And the reason it is not settled: nobody answered.** Tostevin, on the state of the debate —
*"so one-sided as barely to deserve the label... I know of no direct response from chaîne opératoire
proponents"* in eight years, and fifteen years of silence on an earlier polite critique. **No French
practitioner commented on the flagship critique of their method.**

### The one reframing worth stealing outright

**Tostevin's wine analogy.** Both traditions label assemblages the way one labels a château. *"Using
such labels, neither approach can tell you how similar the wines really are to each other."* What is
needed is the **cépage** — 85% Cabernet Sauvignon, 10% Cabernet Franc, 5% Merlot — **comparable
continuous variables, so that similarity becomes a measurable quantity rather than a type
assignment.**

> **That is the difference between saying "this artifact is high-depth" and saying "this artifact is
> 40% attractiveness-directed, 25% teaching-directed, 35% residual."** The second is arguable; the
> first is a label.

### How to report an identifiability claim

Two studies put numbers on equifinality: preferential Levallois flakes classify at **89.3%**
cross-validated against 33.3% chance; Discoid versus centripetal Levallois separates at **80%** with
random forest. **Two genuinely distinct production concepts still overlap 20% in their products.**

> **Not "we can read the maker" but "these two processes separate at 80% under cross-validation, on
> this feature set."** Adopt the convention.

### The critique, and the parts that land

**"An illusion of reading the minds of prehistoric knappers"** is the charge of **overformalization** —
that a rich descriptive vocabulary creates the *feeling* of explanation while adding no predictive
content. **His inversion of this is recorded in [`POLISH_AND_DEPTH.md`](POLISH_AND_DEPTH.md)** and it
holds, but the mechanism named here is worth keeping separately: **a vocabulary can feel explanatory
and predict nothing.**

**The field's three named structural limits map one-to-one onto ours:**

| their problem | ours |
|---|---|
| **co-occurrence** — several unrelated processes in one assemblage, and *"it is impossible to determine"* whether that is one group using several or several groups in succession | **multi-author and mixed human/tool provenance.** They say it is unsolvable without refitting |
| **representation** — only steps present in numbers can be recognised; with few pieces *"it is impossible to determine whether this process is representative or anecdotal"* | small-n readings |
| **completeness** — reconstructed sequences *"cannot be considered as exhaustive"* | **there is no way to bound what you missed** |

**And one practice to refuse outright.** The French approach defines attributes **after** laying the
assemblage out and seeing what looks interesting, and defends it: *"this a posteriori definition of
attributes is not less objective than an a priori attribute definition."* **That defence is wrong, it
is a garden of forking paths, and if we do anything resembling it we will deserve what follows.
Pre-register the feature set.**

### Where we actually stand relative to them

> **We are in the position of an archaeologist handed one finished handaxe and no flakes** — which is
> the position in which every practitioner in this literature agrees inference is weakest.

Refitting — physically reassembling debitage — is their gold standard precisely because it is
**non-inferential**: *"when two pieces go CLICK, there is no other match possible."* At one site 51%
of the assemblage refitted and resolved **three distinct knappers**. **We have no debitage.** The text
analogue exists and is a century old — **genetic criticism**, the *avant-texte* of notes, drafts and
proofs — but it needs the drafts, which finished text does not supply.

| # | technique | status | notables |
|---|---|---|---|
| **G85** | Intention elicitation with a pre-registered target | **ALREADY BUILT — the intent ladder is this protocol**, arrived at independently | **Validated on stone since 2010.** And it supplies a calibration ceiling: experts reach only R² = 0.655 against their *own* stated intention |
| **G86** | A mechanical null model — subtract what the medium forces, call the residual choice | **OPEN, and it is the right shape for decision-versus-constraint** | **The one thing chaîne opératoire never built.** Caveat: the analogous model degrades badly off the bench |
| **G87** | Stage-differentiated partition of features by visibility and acquisition age | **OPEN** | Low-visibility early-acquired features track deep identity; visible ones track situational identity. **A structural hypothesis, not an analogy** |
| **G88** | Error *handling* rather than error rate | **OPEN** | Novices thrash on a ruined surface; experts abandon or repair. **Measures metacognition, not execution** |
| **G89** | Rigidity under perturbation as the novice signature | **OPEN, and it implies an active probe** | Change genre, length or audience and measure whether quality is preserved |
| **G90** | Report separability as a cross-validated confusion matrix | **OPEN, a reporting convention** | *"These two processes separate at 80%"*, never *"we can read the maker"* |
| **G91** | Inter-annotator agreement and per-feature accuracy before any extraction is believed | **OPEN, and mandatory** | Their aggregate of 72.6% concealed a **43.3%** category — worse than chance |

**What these add up to.** **Seven techniques, one of which we already built without knowing it.** The
most valuable is not a technique but a number: **expert knappers predict only 65% of the variance in
their own intentions**, which means the ceiling on intent recovery is set by the maker's own
self-knowledge and not by our instrument. **That reframes every null in this project** — we have been
measuring our distance from perfect recovery when perfect recovery is not the relevant target.

**The second most valuable is the mechanical null model**, because it is the only principled answer
anyone has to decision-versus-constraint and **it is the same subtraction the depth redefinition
needs**, with the nuisance derived rather than assumed. **And the three reliability numbers are the
warning**: a field that skipped inter-annotator agreement, defended post-hoc feature selection, and
reported aggregates that hid a worse-than-chance category is a field whose methods we should take and
whose habits we should not.

---

## §0b. Techniques harvested from connoisseurship and technical art history

**2026-08-07.** Art history has been reading makers off objects for 150 years and we had never mined
it for **method**. This is the harvest: not who said what, but the actual moves. **Everything here is
a candidate import, not an adopted one**, and the failure record at the end is as important as the
techniques.

### The Morellian filter — an admissibility test for features, and the best single import

**The ears were never the point.** Morelli **repudiated the ear and hand plates** as *"caricatures
made to engage the public"* and deleted them from his definitive edition. **Anyone porting "look at
the ears" has ported the anecdote.** What he actually stated is a **selection rule**, and it stacks
two independent filters:

> …the most conspicuous characteristics of a painting, which are the easiest to imitate: eyes raised
> towards the heavens in the figures of Perugino, Leonardo's smiles, and so on. **We should examine
> instead the most trivial details that would have been influenced least by the mannerisms of the
> artist's school:** earlobes, fingernails, shapes of fingers and of toes.
>
> — Ginzburg, *Clues*, 96–97 [READ verbatim]

**Imitability** — what a forger copies — and **school contamination** — what the tradition supplies
rather than the individual. And the four-part admissibility test reconstructed from Wollheim: a
feature may be used only if it

    1. has a form amenable to individual expression
    2. is NOT characteristic of a school or tradition
    3. is NOT depicted in an accidental or haphazard fashion
    4. is NOT one of a suite of similar features that require variation

**Criterion 4 is the non-obvious one and it is the highest-leverage import.** Four ears standing side
by side in a group portrait: the maker must **deliberately differentiate** them, so habit is
suppressed. **It predicts where habit gets switched off**, which is a failure mode stylometry ignores
entirely. The text analogue is elegant variation — a writer avoiding repetition is a writer overriding
their own defaults, so **exactly the places our measures find most "varied" may be the places carrying
least individual signal.**

### The inverse-salience rule — and it is our concealment answer

**Diagnostic weight is *inversely* proportional to how conspicuous a feature is**, because attention —
the imitator's — flows to the conspicuous. Berenson's version: a *"subconscious signature"* of *"small
particularities which escape even the notice of copyists and forgers."*

**Cheap to implement and counter-intuitive: build a salience model, then deliberately discard your most
interpretable features.**

**The honest limit:** this is a claim about **the adversary's attention budget**, not about physics.
A sophisticated adversary who has read Morelli inverts it. **It buys asymmetry, not security.**

### Reserve versus overpaint — recoverable from a single static artifact

**The best import after the filter, and it needs no version history.**

A conservator asks whether the maker left a **gap** for an element — planned — or painted it **on top
of** existing figures — a late addition. In the Beuckelaer study the roasted goat *"was added only as
work on the composition was still progressing"*, which reads as **late narrative emphasis rather than
initial intent.**

**The text analogue is direct and computable.** Did the document's structure **make room** for a claim
— it is in the outline, a section exists for it, forward references anticipate it — or was the claim
**inserted into** a structure that does not accommodate it: a parenthesis, an appendix, a paragraph
breaking the section's parallelism? **That separates load-bearing commitments from bolted-on ones, on
one static text.**

**And abandoned scaffolding ports as well:** squaring grids present on the preparatory drawings and
absent from the final panels mean *"this plan must have been abandoned."* In text: a numbering scheme
that stops, a *"we return to this below"* that never lands, a defined term used once.

### Self-revision versus an imposed hand — distributional, not semantic

The field enforces a hard gate: a change made by a later restorer **is not a pentimento**. How they
tell, from documented patron-forced revisions: imposed changes show *"distinct steps"*, while
Beuckelaer's are *"of like kind"* throughout with *"constant adjustment."*

> **Imposed changes are lumpy, discrete and heterogeneous. Self-revision is homogeneous, continuous
> and of like kind.**

**That is computable and it is the discriminator this project needs most** — author against editor
against co-author against tool. **Essential rather than optional.**

### Suspicious regularity — and it may invert one of our assumptions

Forensic document examination formalises copying as a loss of **line quality**. The counter-intuitive
tell is that **the imitator is *more* regular than the genuine article**, because they are executing
carefully rather than habitually — *"they will form the characters more carefully, creating even lines
with no variation in pen pressure."*

> **If our instrument treats high internal consistency as evidence of expertise, this literature says
> we may have it backwards.** Genuine habitual production carries characteristic irregularity, and its
> absence is the tell.

[SNIPPET only — forensic specifics not reached at primary-source depth.]

### The graded attribution vocabulary — steal it wholesale

**by · attributed to · studio of · circle of · school of · follower of · manner of · after**

**It is not a probability scale.** It factors uncertainty along **three independent axes at once** —
*proximity* (social distance from the maker), *temporality* (contemporary or later), and *intent*
(**after** is an honest copy; **manner of** is where deliberate fakes cluster). And *attributed to*
encodes **partial authorship** — *"either in part or completely"* — which a scalar cannot express.

> **"Workshop of" is the category this project will need most and would not have invented:
> partial, supervised, mixed human-and-tool provenance.**

### Baseline-relative diagnosticity — infrastructure, not technique

Morelli's method is feature-matching **against a school baseline**, requiring *"repeated and
painstaking visual comparisons"* over large numbers of works. *"As the botanist lives among his fresh
or dried plants… so the art connoisseur ought to live among his photographs."*

> **Without a genre and register baseline corpus you cannot tell an individual habit from a
> convention, and the instrument will confidently report the genre's decisions as the author's. This
> is the most likely way it fails silently** — and it is the same failure that killed 61 of our 81
> replicated features.

### Two channels, never averaged

**The failure record is one-directional and it should determine the architecture.** Every historical
exposure of a forgery came from a **hard external falsifier** — titanium white in a 1914 painting, a
broken provenance chain, a confession. **The stylistic channel has never independently caught a
competent forger.** Berenson was fooled for years. Beltracchi produced ~300 forgeries over 35 years,
entered catalogues raisonnés, and was caught by a **pigment supply-chain accident.** The Rembrandt
Research Project demoted *The Polish Rider* and then re-promoted it from the same object.

> **Build two channels: hard falsifiers that can veto, stylistic inference that can propose and never
> veto. Do not average them into one score.** The fields that averaged them produced the Getty kouros.

### What Ginzburg says we are not allowed to claim

The evidential paradigm — Morelli, Freud and Holmes as one epistemology — is *"totally unrelated to
the scientific criteria of the Galileian paradigm."* It is **individualising rather than
generalising**: *"indirect, presumptive, conjectural,"* with *"an unsuppressible speculative margin."*

> **If the instrument outputs a confidence percentage, it is claiming a status this entire tradition
> says is unavailable.** That is why the field built a graded *vocabulary* instead of a numeric scale.

### And the finding that should temper all of it

**Morelli did not practise his own method.** A study of his 1865 notebooks found **one** morphological
attribution in the entire account; *"the overriding ground for attribution is quality."* His famous
Giorgione attribution, in his own words: *"the spirit of the master met mine, and the truth flashed
upon me."*

> **We are importing a promising untested specification, not a validated instrument with a 150-year
> track record.** The Morellian filter is a good idea that happens to be well stated in Morelli's
> theoretical writing, and it was largely not used. **Say so in our own documentation.**

**A scope mismatch to hold onto.** Connoisseurship optimises for *who made this*. We want *what
decisions, expertise and values are legible in this*. **Reserve/overpaint, self-revision, pentimenti
and cross-version differencing transfer cleanly. The filter and the inverse-salience rule were built
for identity and need re-aiming** — a feature can be highly individuating and reveal nothing about
values, and **the conspicuous features Morelli tells us to discard may be exactly where values live.**

| # | technique | status | notables |
|---|---|---|---|
| **G79** | The four-part admissibility filter, criterion 4 especially | **OPEN, and the best single import** | **Predicts where habit is switched off** — elegant variation suppresses the individual signal exactly where our measures see most variety |
| **G80** | Reserve versus overpaint, on text structure | **OPEN** | **Computable on one static text with no version history.** Separates load-bearing commitments from bolted-on ones |
| **G81** | Self-revision is homogeneous, imposed change is lumpy | **OPEN, and the discriminator we need most** | Author vs editor vs co-author vs tool. **Distributional, not semantic** |
| **G82** | High internal consistency indicates *imitation*, not expertise | **OPEN, and it may invert an assumption we hold** | The imitator executes carefully; the habitual producer is irregular |
| **G83** | Adopt the graded attribution vocabulary | **OPEN** | Three axes at once, and **"workshop of" is the mixed-provenance category we would not have invented** |
| **G84** | Two channels — falsifiers veto, style proposes, never averaged | **OPEN, architectural** | **Every historical catch came from a hard falsifier; the stylistic channel has never caught a competent forger unaided** |

**What these add up to.** **Six operational techniques, none of them ours, none of them yet run**, and
three of the six attack problems this project has been stuck on: which features are admissible at all,
how to tell the maker's revision from someone else's, and how to express partial authorship. **The
import is cheap because the thinking is done.** What it costs is the tradition's own liabilities —
unfalsifiability, a market-tainted history, and an inventor who did not follow his own rule — and the
correct response to that is Morelli's own scope limit: **a check on a prior judgement, not a generator
of judgements.** Position it that way and we inherit 150 years of defensibility; position it as an
oracle and we inherit 150 years of well-earned attacks.

---

## §1. The primary detector is the *variation* of the polish, not its level

> When I've been talking about the veneer in my head, I've been thinking about the imagery and
> iconography.

Not polish level — polish **change**. An opening reaching for professional register and then relaxing
out of it. **The performance is what costs something, so the performance is what slips, and the slip
is where the maker shows.**

**His own scope limit, attached when he stated it:** *useless on published books, because editing
sands the polish flat.*

### The timeline, because this is the claim with the most history and the least resolution

    1. Stated as his primary detector. Nothing in the project measured position within an artifact --
       every quantity was an artifact-level scalar, so nothing could have seen it.
    2. Simulation supported the mechanism: practised polish decays 6.5x faster than depth, and
       synthetic polish is flat. (sim S-6)
    3. Measured on MACHINE text as within-artifact variance of 342 features. Found 1 and 0 surviving
       features. UNINFORMATIVE -- a machine has no performance to slip, so a null there is the
       absence of the thing, not evidence against it.
    4. Measured on HUMAN text with maker, prompt, topic and register all fixed -- 86 students, three
       drafts each. 0 of 313 features survive correction, against 12 for the plain average.
    5. Found that the FIELD ALREADY DETECTS THIS, and detects it well.

**Step 5 is the one that changes the reading of step 4**, and this file previously got it wrong by
treating the null as damaging to the hypothesis.

| what the field does | what it is |
|---|---|
| **burstiness** — GPTZero's second headline metric | literally the standard deviation of per-sentence perplexity across one document. **Shipped commercially since 2023** |
| **unmasking** — Koppel & Schler, 2004 | chunk a document, separate the chunks, read the *shape of the degradation curve*. Canonical in authorship verification for 22 years |
| **intrinsic plagiarism detection** | find a passage anomalous relative to the rest of its own document, no reference corpus |
| **PAN Style Change Detection** | a shared task running continuously since 2018. **The topic-controlled bar is 0.830 macro-F1** |

> **The phenomenon is real and other people measure it successfully. We failed to measure it.**

**That is a different conclusion from "the hypothesis is wrong", and it points at our instrument.**
Either the operationalisation is wrong — variance of arbitrary surface *features* may simply not be
where the performance lives — or redrafting is the wrong axis, since a student redrafting an
assignment three times may not be varying the performance at all. **Both are fixable. Neither was
tested.**

**One further caution from the same audit:** a 2025 study of hidden states as author representations
found **document-level mean pooling best**, which is evidence against the variance idea at the
representation level too.

**What is not pre-empted:** within-artifact variance of **probe activations** rather than of
perplexity or surface style. Nobody found doing that.

### And his reading of what the field is measuring, which is a claim rather than a complaint

> It's not burstiness. It's not unmasking. **It is goal variation** — all of them varying in relative
> strength as you express yourself. People aren't seeing it for what it is.

**One distinction I collapsed and he separated:** intrinsic plagiarism detection finds *a different
author spliced in*. **That is not one author's goals shifting across their own piece**, and merging
them overstated how much of this is pre-empted.

| # | hypothesis | status | notables |
|---|---|---|---|
| **lit** | Within-artifact variation of polish carries the maker | **SUPPORTED (READ)** — seven years of shared-task baselines at **0.830** on topic-controlled data | **The phenomenon is real and other people measure it well.** That changes what our null means |
| **L7** | Variance of arbitrary surface features is the right operationalisation | **REJECTED (test).** 0 of 313 features survive on human text with maker, prompt, topic and register fixed | **This is what actually died** — and the plain average found 12 on the same data, so windowing itself was not the problem |
| **HH-3** | Within-artifact variance of **probe activations** carries what surface-feature variance does not | **OPEN, and not pre-empted by anyone** | Burstiness does it with perplexity, PAN with surface style. **Nobody found doing it with probe outputs** |
| **HH-4** | Redrafting is the wrong axis; the claim needs artifacts of **different kinds** by one maker | **OPEN** | A student redrafting an assignment three times **may not vary the performance at all**, which would make L7 uninformative rather than negative |
| **L11** | Our measure beats 0.830 on the topic-controlled split | **REJECTED (test).** 342 features reach **0.565** against a floor of 0.444 and a published best of **0.830** | **Real but not competitive** — a third of the way from floor to bar. **This is the answer to §1: the gap is our instrument.** It also confirms the field's own conclusion that pure stylometry has been displaced by fine-tuned transformers on this task. **Orphan surfaced by the audit (L26): the same bank scores 0.969 on the *easy* split, above its published best of 0.959** — split-conditional, since the easy split is not topic-controlled and the win may ride topic |

**What these add up to.** The claim and our measure of it came apart, **and we now have the number that
proves it was the measure.** Our 342-feature bank scores **0.565** on the field's own topic-controlled
task, against a floor of 0.444 and a published best of 0.830 — **real signal, a third of the way from
floor to bar, and not competitive.** A mature field detects within-document variation successfully and
we found nothing —
which points at the instrument rather than the hypothesis, and this file previously got that backwards.
**Two candidate faults, both fixable, neither tested:** the operationalisation may be wrong (variance
of arbitrary surface features is not obviously where a performance lives) or the axis may be wrong
(redrafting may not vary the performance at all). **HH-3 is the version nobody has pre-empted** —
variance of *probe activations* rather than of perplexity or surface style — and it is the only route
here that is both untried by the field and untried by us.

### What this retires

**The revision-wobble test was a false start, and he did not propose it.**

> The problem is that revisions from a human author are always going to carry **the same level of
> intent density across the board.**

**So the null stands but its target was mis-specified.** It tested whether human redrafting varies the
performance; on his account human redrafting should not vary it at all, **which makes the null
unsurprising rather than informative.**

**What would have been interesting instead, in his words:** *AI* revision — the moment the model's
attentional mapping shifts away from your goal and you reach out to correct it. *"Allow me to pick you
up with the largest pole of the tent in my distorted policy space."* He predicts a vague unifying
effect and declines to claim even that.

## §2. Reading enters at an anomaly, never at the artifact

> The thing that most jumps out at me isn't mistakes but **unusual constructions, or odd decisions
> that I can't find an explanation for.**

Then it runs purpose→method **and** method→purpose, with the entry point set by wherever he has
partial expertise — which is [`THE_TRIPLE_INFERENCE.md`](THE_TRIPLE_INFERENCE.md) §2's enter-at-any-sub-level claim
described from the inside.

**His own discomfort, recorded because he raised it:** *"I hate that a lot of this is me picking out
mistakes and typos, which is also a trick for AI and it's not okay. But it is a way of extracting
decisions."*

**And the mechanism that connects this to mistakes:** a **mistake** is an anomaly with a *known
cause*, so the maker's response to it is a decision with its alternatives visible. *"The importance of
the mistake — the mistake, and the way the author can be presumed to have responded to it, is one of
the more useful pieces of information once you have observed it."*

| # | hypothesis | status | notables |
|---|---|---|---|
| **HH-6** | Entering at the anomaly beats entering at the whole artifact | **OPEN** | **The machinery exists and has never been the live path** — `bounded_v6`'s stage zero runs the anomaly pass first and feeds stage A. A flag flip and a comparison, not a build |
| **HH-7** | Local decision density around a mistake exceeds baseline | **OPEN** | Needs mistakes *located* first, and nothing does that. **A mistake is an anomaly with a known cause**, which is what makes it more tractable than an anomaly |
| **S-4/S-5** | Stage ordering changes the answer | **REJECTED (sim)** — by exactly zero; anomaly-first settles ~5% sooner | **This weakens HH-6's expected size before it is run.** Honest prediction: a cost saving, not a finding |

**What these add up to.** The entry-point claim is cheap to test and **the simulation has already
lowered what we should expect from it** — reordering the probe's stages changed the answer by exactly
zero, and only the cost moved. **So HH-6 is worth running to close the question rather than to open
one.** The more interesting row is HH-7, because a mistake is an anomaly whose *cause is known*, which
means the maker's response to it is a decision with its alternatives visible — **the only place in
this file where we could see a decision and its counterfactual at the same time.**

## §3. Confidence in a maker moves while reading

> It starts questionable... 8 or 9 by the end.

**The trajectory carries what the endpoint does not.** Every reading this project records is a final
number.

**Related to §1 by more than coincidence** — both say the within-artifact *series* is where the
information is, and we have only ever kept means. **The same 2025 result that found document-level
mean pooling best is evidence against both.**

| # | hypothesis | status | notables |
|---|---|---|---|
| **HH-9** | The confidence trajectory across a reading carries more than its endpoint | **OPEN.** Score windows sequentially and keep the series | **Every reading this project records is a final number**, so the series has never existed to be checked |

**What this adds up to.** One row, never run, and it shares a fate with §1: **both say the
within-artifact *series* is where the information is, and we have only ever kept means.** The one
piece of external evidence bears against both — a 2025 study of hidden states as author
representations found document-level mean pooling best. **That is not decisive, because it was
optimising for author identity rather than for maker state**, but it is the reason neither row should
be run expecting a large effect.

## §4. Depth is a property of the writer **with respect to the domain**

> It does not vary within an artifact unless the domain does.

**This is the sharpest definition in the project**, because it makes depth a **relation** rather than
an attribute — and it arrived with its own falsifier attached: *depth moves where domain moves.*

**Why it matters more than it looks.** The binding constraint on this project has been the absence of
a controlled human corpus. **This says why that is fatal rather than inconvenient: a relation cannot
be measured by varying one side.** Every measure that has died, died reading artifacts alone.

| # | hypothesis | status | notables |
|---|---|---|---|
| **HH-10** | Depth measured on one maker moves when the domain moves and not otherwise | **OPEN, blocked on a corpus we do not have** | **Previously written up as "directly runnable". That was wrong** — it is directly *specifiable*, and nothing we hold supplies it |

**What this adds up to, and it is the most consequential row in the file.** Making depth a *relation*
rather than an attribute explains why the corpus problem is fatal rather than inconvenient: **a
relation cannot be measured by varying one side, and every measure that died, died reading artifacts
alone.** The falsifier came attached to the claim — *depth moves where domain moves* — which is rare
and makes this cheap to settle the moment the corpus exists. **It is the same corpus HH-4 needs, and
the same one three sections of the triple inference need.**

## §5. Process is hierarchical, and you can enter the decode at any level

> Walking up to an unknown oil painting, you can engage with it on the level of **metaphor** — why did
> the author craft what they did. On the level of **technique**, like perspective. On the level of
> **mechanics** — how did they move their hand as they painted.
>
> **You can use any piece of knowledge about any of those three channels to begin the decoding.**

**Vocabulary decision: mechanics / technique / metaphor stands.** Panofsky was the wrong citation and
he rejected it correctly — those levels are about *what an image depicts*, not *how a thing was made*,
and perspective, oil paint and meaning genuinely do not sort into that scheme.

**Dennett's three stances is the right citation and not the terminology:**

| his label | Dennett | what it reads |
|---|---|---|
| **mechanics** | physical stance | how the hand moved; the material act |
| **technique** | design stance | how it is built to work; perspective, structure |
| **metaphor** | intentional stance | what the maker meant by it |

**And it is not one person's scheme** — Marr's computational / algorithmic / implementational, and
Newell's and Pylyshyn's independent versions, all land on three levels with the same structure. **Four
thinkers converging is a result about the shape of the problem, not a coincidence of naming.**

One caveat worth holding: **"metaphor" is narrower than the top layer needs** — the intentional stance
covers *purpose*, not only *meaning*, and this project's top layer has to carry goal.

**Still open, and he flagged it:** whether the layers are really three or arbitrarily subdividable.
Nobody in that convergence argues three is forced; they argue three is *useful*.

### This is where we collide with the literature, and the collision is the contribution

| # | hypothesis | status | notables |
|---|---|---|---|
| **lit** | Entry is possible at any of the three levels and ratchets to the others | **CONTESTED (READ)** | **Bullot & Reber assert a strict ordering** — the design stance is *"requisite for"* artistic understanding — and the open peer commentary attacked precisely the relations among their modes. **This contradiction is our contribution surface** |
| **lit** | Bullot & Reber's framework is well supported | **REJECTED (READ-FULL)** | Chmiel & Schubert, 34 experiments across 23 publications: **26% support, 18% inconclusive, 56% no support.** An occupied lot with a shaky building on it |
| **G56** | Supplying **mechanics-level** information unlocks goal recovery | **OPEN, and it is the missing direction in the whole edge programme** | **Every edge tested so far supplies a goal or a process. None has ever supplied a mechanic.** Same row as the triple inference's G56 |

**What these add up to.** We disagree with the only framework that occupies this ground, **and that
framework is weakly supported by its own field's replication record** — so the collision is worth
taking rather than conceding. **The disagreement is specific and testable**: they say the design
stance is a prerequisite, we say entry is possible anywhere and ratchets. **G56 is the experiment,
and it has never been run in either direction by anyone.** The formal home for our side is one we have
never read — **Rasmussen's abstraction hierarchy**, five levels with explicit means-ends links, built
for diagnosis *from any level*, forty years of use.

**The formal match we have never looked at is Rasmussen's abstraction hierarchy** — five levels with
explicit means-ends links, built for diagnosis **from any level**, forty years of use. **That is a
better formal home for the ratcheting claim than anything we have cited, and nobody here has read it.**

## §6. Interest is unexplained decisions — which makes the reader an instrument

> Interest comes from finding decisions that you can't attribute meaning to, which implies there's
> more meaning you don't fully understand — either a **process** you aren't aware of, or an **extra
> motivation** you aren't aware of.
>
> **Artfulness is making a lot of unexplained decisions. Aesthetics is the appearance of having made
> unexplained decisions but for a reason, in an ordered sense.**

**This connects §2's anomaly-entry to a mechanism**, and it makes *interest* a proxy for **unrecovered
decisions** — which is the quantity this whole project is trying to measure.

> **If interest is what a reader feels when decisions are present but unattributed, then
> reader-reported interest is an instrument — and it is one we can ask a human for directly.**

**And it answers his own open question about performative polish.** He asked whether art theory
separates aesthetics that *indicate* deeper understanding from aesthetics that merely perform it.
**Under §6, performative polish is ordered without being unexplained** — which is a measurable
distinction rather than a vibe.

**A correction that matters, because it was mine and it was load-bearing.** I offered **Berlyne's
collative variables** — novelty, complexity, uncertainty, conflict — as live support. Reading the
source rather than the search snippet: *"Berlyne's arousal theory of aesthetic appreciation has been
mostly abandoned"* on mixed empirical results. **The vocabulary survives; the mechanism does not, and
this claim must not lean on it.** The live descendants are **processing-fluency** accounts, which sit
at the *opposite* pole — pleasure from ease. **That tension is the field's live debate and his claim
sits on one side of it.**

**His "ordered but unexplained" is close to effective complexity** — structure that is neither random
nor trivially regular. **That is a real, formalisable quantity and it is the better formal target.**

| # | hypothesis | status | notables |
|---|---|---|---|
| **HH-14** | Reader-reported interest correlates with unrecovered decisions | **OPEN, blocked on him.** Interest ratings on his fifteen read artifacts | **An hour of his time, and it turns the one channel that has beaten every measure we own into data** |
| **lit** | Berlyne's collative variables support the interest claim | **REJECTED (READ)** | *"Berlyne's arousal theory of aesthetic appreciation has been mostly abandoned."* **One fetch found this after fifteen searches had not** — the vocabulary survives, the mechanism does not |
| **HH-16** | "Ordered but unexplained" is effective complexity rather than entropy | **OPEN** | Effective complexity is a real formalisable quantity — **neither random nor trivially regular** — and it is a better target than the vocabulary we borrowed |

**What these add up to.** The idea is intact and the support I first gave it was wrong. **Interest as
a proxy for *unrecovered decisions* is the only claim in this project that turns the reader into an
instrument**, and it costs an hour rather than a corpus. Its formal home is effective complexity, not
Berlyne — **and the live debate in the field runs the opposite way**, with processing-fluency accounts
locating pleasure in *ease* rather than in unresolved structure. **That tension is not a problem for
the claim; it is the thing HH-14 would adjudicate**, because the two accounts predict opposite
correlations between interest and recoverability.

## §7. The maker is a bard, not a teacher — and that is two motivations, not one

**2026-08-07.** The cooperative-IRL literature says inference gets easier if you assume a **teacher**
— someone who intends to be understood. **His refinement is that a maker is something more specific
than a teacher, and the difference is the part nobody has formalised.**

> What we're actually looking for is **a bard**, to be a little bit more precise. **There are two
> motivations. They want to grab your attention through aesthetic capture, and they also want to make
> it easy for you to ingest the data.** And that's the teacher aspect.

> How on earth do they shape it in order to create that effect? **I assume they try to model the brain
> of their listener. Of course they do.** Which makes all interactions this kind of **collaborative
> back-and-forth.**

**So the maker is running the triple inference in reverse while making the thing.** They model the
reader, then shape the artifact so the reader's inference lands where they want it. **That means an
artifact is not a trace of a maker's process — it is a trace of a maker's process *plus their model of
you*.** Which is a second inference problem sitting on top of the one this project is trying to solve,
and it is the reason the teacher assumption pays: **structure placed to be understood is structure
that can be read.**

**And the asymmetry he names is the sharpest thing here:**

> **AI isn't interacting with this. It's only trying to take, it's not giving.**

**A model generating text is not modelling your inference and shaping for it** — not in the sense a
bard does, where the shaping is the point. **If that is right, the missing thing in generated text is
not effort and not polish. It is the second half of a collaboration**, and that is a different account
of the unease from either the polish–effort story in §8 or the flattened-intent story in
[`POLISH_AND_DEPTH.md`](POLISH_AND_DEPTH.md) §4.

**He flags the obvious objection himself:** *"yes, this is just a restatement of CIRL with different
terms."* **It is, up to the aesthetic layer — and that layer is the addition.** Cooperative IRL has
the teacher and the shared task. It does not have *attention capture as a separate motivation from
comprehensibility*, and it does not have the observation that both are deliberately placed.

| # | hypothesis | status | notables |
|---|---|---|---|
| **HH-19** | A maker has two shaping motivations — attention capture and comprehensibility — and they are separable | **OPEN** | **This splits polish into two constructs.** See [`POLISH_AND_DEPTH.md`](POLISH_AND_DEPTH.md) §2b, which carries the measurement side |
| **HH-20** | Makers model the reader's inference and shape the artifact for it | **OPEN** | If true, **an artifact is a trace of the maker's process plus their model of the reader** — a second inference problem sitting on the first |
| **G62** | Assuming the maker intends to be understood improves recovery | **OPEN** | **Must be tested against concealment**, where the assumption is false and licenses confident wrong inference |
| **HH-21** | Generated text lacks the collaborative half — it takes without giving | **OPEN, and it is a claim about what is absent** | **A third account of the unease**, distinct from broken polish–effort and from flattened intent, and the three predict different things |

**What these add up to.** This is the newest material in the file and none of it is measured, **but it
is the only account here that makes the maker an active participant rather than a source of traces.**
Its value is that it converts a vague prior — *assume good faith* — into two specific, separable
things a maker deliberately does, one of which (comprehensibility scaffolding) is **exactly the
structure a reader would exploit** and has never been looked for. **The risk is that it is
unfalsifiable as stated**: almost any artifact property can be called reader-modelling after the fact,
so HH-19's separability is the load-bearing test — **if attention capture and comprehensibility cannot
be pulled apart in measurement, this is a story rather than a mechanism.**

## §8. Aesthetics was the cheat, and AI broke it

> Aesthetics is one of the **easiest goals to judge**, because it is literally surface polish — you
> can explicitly judge whether the maker succeeded at it, and implicitly the value of what you are
> seeing by **how much you want to look at it. It is a self-referring goal and you can cheat it pretty
> easily.**
>
> **It's also the piece that's misfiring on AI specifically. Previously it correlated with effort very
> highly. Now it does not. That's what's breaking.**

**The sharpest available account of why generated text unsettles readers.**

**And it reframes the effort heuristic rather than accepting it.** People rate identical artifacts
higher when told more effort went in, more so when quality is ambiguous. The literature audit offered
that as an adversarial reading of depth — a bias in the reader. **On his account it is not a bias. It
is a normally-valid inference that a new kind of artifact has broken.**

| # | hypothesis | status | notables |
|---|---|---|---|
| **HH-17** | The polish–effort correlation is strong in human corpora and near zero in generated ones | **OPEN, and the corpora are already held** | **Needs an effort proxy, which is the unspecified part** — and effort is exactly the quantity automaticity makes unobservable |
| **HH-18** | The effort heuristic is a valid inference broken by a new artifact class, not a reader bias | **OPEN**, and it follows from HH-17 | **The reframe is the contribution.** The literature calls it a bias in the reader; this calls it a normally-valid inference that something new has broken |

**What these add up to.** Both rows rest on being able to measure **effort**, and nothing in this
project can. That is not an oversight — **automaticity makes effort unobservable by construction**,
which is the same fact that makes the polish/depth asymmetry work and the same fact that puts values
in the residue rather than the signal. **So the sharpest testable claim in this file is blocked on the
quantity the rest of the theory says is hidden**, and any proxy we adopt will need its own defence
before HH-17 means anything.

