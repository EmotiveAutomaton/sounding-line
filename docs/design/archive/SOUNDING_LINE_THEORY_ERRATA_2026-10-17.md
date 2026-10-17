# Sounding Line theory errata, 17 October: one inference, trust, teardrops and pervasiveness

17 October 2026. Two readers:
- **The curator** reads Part A: what gets filed where, in his words, with what the research says and where the analyst pushes back.
- **The Sounding Line agent** applies Part D.

The edits are against `docs/theory` at `6c063f5cd`, which is unchanged since the 16 October errata were applied at 04:30. All 34 edits were checked by script before delivery:
- every anchor occurs exactly once in its file, before and after the earlier edits;
- the edited files pass `tools/theory_lint.py --all`;
- no inserted line carries a dash, a banned word, or a colon outside a label.

The same edits, as data, are in `SOUNDING_LINE_THEORY_ERRATA_2026-10-17.edits.json`.

New identifiers:
- **G198 to G202**;
- **HH-GOALS-EMERGE, HH-LAST-PASS, HH-OVERLAYS, HH-ATTENTION-TRUST, HH-ONE-SCALE, HH-NO-TRANSLATION, HH-PERVASIVENESS**;
- **D-SELF-MODEL, D-EDIT-REPLACES, D-PAUSE-BOXES, D-OWN-SURPRISE**.

All are unused anywhere in the repository at `6c063f5cd`.

## Part A. What changes, with your words

Your direction for this filing was "extract my quotes as you can, sprinkle them throughout, correct the grammar and stuff, and assume that I know what I'm talking about." So the quotes are cleaned for grammar, and the lexical repairs are listed in Part B. Each position is filed as yours, with its research standing beside it. Where the literature disagrees, the prose says so plainly.

### THE_TRIPLE_INFERENCE.md

**1. One inference, three entries** (new block after "Bounded, not irrational"; new row **G198**).

> "So, functional reverse engineering from the top, assuming they would use it for the same thing we would use it for; the second one being the person; the third one being the process. It's still here."

The three questions become entries into one joint inference.
- **Support.** Computational theory of mind does exactly this: one inversion that infers beliefs, desires and percepts together (Baker et al. 2017).
- **Your "human trick" has two halves with names.** Its function-first half is the **teleological stance** (Gergely & Csibra); for artifacts, children's function-first explanations are already cited in READER_HEURISTICS §3, where this same entry from above sits as HH-ENTRY-RELIABILITY. Its "our own requirements" half is **egocentric projection**: people adjust from their own view and stop early (Epley et al. 2004). The person and the process are the new entries.
- **Two terms to learn:**
  - Research calls the inference **mentalizing** or **theory of mind**. "Empathy" in its narrow sense means sharing a feeling, and it runs on a separable brain network (Kanske et al. 2015). Your quote keeps "empathy"; prose for outsiders says theory of mind.
  - The unity is computational, not mechanistic. Belief tracking may run on two systems, one fast and inflexible, one slow and flexible (Apperly & Butterfill 2009).

Sounding Line's D37 measures how much each entry carries.

**2. A value is a decision you still agree with** (new block in §4; new row **G199**).

> "I made that decision previously, and I still agree with that decision, and therefore that decision is going to continue being my autocomplete."

Your test for a value is **present endorsement**. Philosophy's version is Frankfurt's second-order volition, and "wanting to want" is the same thing.
- Your "laziness" is the **cost of control**: control is bought only when its payoff beats its cost (Shenhav et al. 2013). "Fatigue" is the weaker reading, because ego depletion failed a 23-lab replication (d = 0.04).
- **Pushback, a real objection:** endorsement is self-report. Your own 06:21 point is that stated purpose runs through a self-model, so the criterion needs a behavioral check. G191's disturbance probe is the candidate: a value you endorse should be defended by varied means.
- Your mesa-optimizer question is filed with it.

**3. A theory that can't lose** (new block in §7; no new row).

> "If everything becomes calibration, the theory can't lose."

The quote keeps your framing on both sides of it: it opens with "I am having more trouble with this one" and ends with "Honestly, I'm kind of stumbling." The prose agrees with the description and **dissents from the comfort.** In Lakatos's terms, a framework that can't lose is a research programme's **hard core**. A programme is judged by whether the models around the core keep predicting new things, or only absorb results ("degenerating"). So what can lose here are the models. FX1, frozen today, is the first, and it can't run until the instruments see planted taste.

### THREE_COGNITIVE_LAYERS.md

**4. Attention trains the autocomplete, and habits grow** (new block in §1; new row **G200**).

> "What you have attention over is System 2, and System 2 creates System 1 over time."

> "Ghosts of repetitions."

**Term to learn: Type 1 and Type 2 processing.** The field's own authors dropped "System" because it implies two located systems (Evans & Stanovich 2013). Your quotes keep System 1 and 2; the prose uses Type 1 and Type 2.
- **Support.** Your route has two classic mechanisms: stored solutions retrieved in one step (Logan's instance theory) and slow rules compiled into fast ones (Anderson). Capture errors and "strong-but-wrong" errors that grow with training and go undetected (Woltz 2000) are the nearest match to habits growing.
- **Pushback, a real objection, in two parts:**
  - No study found shows habits spreading to bigger circumstances. Habits are mostly right and bound to context (Wood & Rünger 2016).
  - Your chess reading needs a correction. In Bilalić's study the experts also failed to find the better move, so the familiar solution held their search, not just their eyes.

**5. Trauma is one-shot expertise** (new block in §1; new row **G201**).

> "Fear blurs it, because it's a one-shot. It is an incredibly highly weighted one-shot experience that then becomes applied to all kinds of stuff."

- **Support:**
  - Stronger threats widen fear generalization (Dunsmoor 2017).
  - Expertise differentiates (Goldstone).
  - Fear removing options from the landscape has a computational home: people **prune** decision trees at branches that start with a loss, even when the pruned branch was better (Huys et al. 2012).
- **What narrows it:**
  - Dunsmoor varied intensity, not the number of exposures.
  - One-trial fears are selective (Seligman).
  - Aversive learning sharpens discrimination in one study and blunts it in another.
  - Broad generalization from one example is what any Bayesian learner does.
- The clinical sense of trauma isn't claimed.

**6. Autocomplete all the way down** (new block in §5; new row **G202**).

> "I don't know that a machine that is autocomplete all the way down can grow it."

- **Your reading of transformer attention is right:** its update rule is a modern Hopfield network's, an associative memory (Ramsauer et al. 2020).
- **The reasoning-model evidence leans your way:**
  - training mostly reweights strategies the base model already had (Yue et al. 2025);
  - base models already "self-reflect" (Liu et al. 2025);
  - models encode whether an answer is right but don't use that signal (Zhang et al. 2025). That is a trust signal with no corrector to act on it.
- **Counterevidence is real but narrow:** prolonged training (ProRL), and a transformer trained from scratch (Rubin & Ringel 2026).
- **Status: OPEN for the missing corrector; CONTESTED for "autocomplete only".** "Echoes of human strategies" fits most of it; "autocomplete only" overstates it.

### READER_HEURISTICS.md

**7. Teardrops that emerge, overlay, and are topped by the last pass** (new block in §3; rows **HH-GOALS-EMERGE, HH-LAST-PASS, HH-OVERLAYS**).

> "Not every creation needs a hierarchy inherently."

- **Law backs the last pass, partly.** The Ninth Circuit's joint-authorship test weighs control, the "master mind", first among three factors.
- **The psychology of credit doesn't.** Writers' felt ownership and lay credit track influence and contribution, not final say (Draxler 2024; He et al. 2025). So the last pass decides who may declare the top goal, and contribution decides whose goals the work carries.
- **On overlays the field is split.** Routine action needs no explicit hierarchy (Botvinick & Plaut). Flexible action may need one (Cooper & Shallice).
- Ghost's N12 tests what an artifact can show of this.

**8. Attention is deciding what to trust** (new block in §4; row **HH-ATTENTION-TRUST**).

> "Attention is deciding to run an inference on whether to trust in a given specific setting."

**Term to learn: precision.** Your "trust" is the research term precision. Raising expected precision at a location draws processing there, which is your manual move (Feldman & Friston 2010).
- **The framework splits what you join** into three:
  - **attention**, meaning sensory precision;
  - **salience**, meaning where to look next, driven by expected information gain;
  - **control**, meaning precision on policies against a habit prior.
- **Pushback, a real objection:** in Parr et al. 2023, effort is the cost of acting against the habit. It isn't produced by adjusting trust, so one of your phrasings runs backwards.
- The safe corner fits the split exactly: gaze on the habit, and wrenching it away as policy precision.

**9. One scale: how fast things come apart** (new block in §5; rows **HH-ONE-SCALE** and **HH-NO-TRANSLATION**).

> "Interest is disassembly, and beauty is the rapid disassembly."

Filed as your rejection of the three-term split.
- **Support:** insight and its intensity predict liking (the "Aesthetic Aha", Muth & Carbon 2013), and the aha follows a sudden gain in fluency.
- **Against one scale:**
  - interest and pleasantness were unrelated in one series (Turner & Silvia 2006);
  - fluency beauty (symmetry, prototypes) has no interest phase.
- **Status: OPEN for beauty as fast resolution; CONTESTED for one scale joining interest and pleasure.** Your account fits beauty that arrives as insight better than beauty that arrives as ease, and nobody has measured resolution speed against beauty.
- **Landscapes** map onto Kaplan's preference matrix: coherence, legibility, complexity, mystery.
- **"No translation layer"** meets Kant's free beauty. The "computer-made" label and title findings favor "intent without an ulterior purpose" over "no intent"; the candy finding shows strong sensory pleasure can feel beautiful.
- Sounding Line's D36 (jokes) is a first test.

**10. Pervasive or local** (new block in §6; row **HH-PERVASIVENESS**).

> "Other characters being fearful imply that this character being fearful is about the author, not about the character."

**Term to learn: Kelley's covariation model.** It reads where a cause sits from three facts:
- **consensus:** do others do it here?
- **distinctiveness:** does she do it only here?
- **consistency:** does she do it every time?

Low, low, high puts the cause in the person, and your test is its distinctiveness leg.
- **Two fixes, both real objections:**
  - **Add consensus**, or genre conventions pass as the author.
  - **Pervasiveness shows the choice is the author's, not that it was automatic.** Poe claimed every point of "The Raven" was deliberate: pervasive and attended. A cue-bound habit or a one-shot fear can be local.
- **The restated test:** person-located, and insensitive to what it should track (fast, unrevised).
- Sounding Line's D30 and D31 and Ghost's N14 test it.

### DECISION_TRACES.md

**11. Two accounts of one purpose** (new block in §6; rows **D-SELF-MODEL** and **D-EDIT-REPLACES**).

> "Stated purpose is not actually 100%, because you are relying on the creator's self-model of their own motivation."

**Each account has its own literature:**
- **Reports made in the moment** are accurate for what was attended. Asking later forces people "to infer rather than remember" (Ericsson & Simon 1980), so your advice to record immediately is the standard advice.
- **Rereading is self-perception** (Bem).
- **Owning an autocompleted choice** is choice blindness (Johansson et al. 2005).
- **Death of the Author**, in criticism's older form, is the intentional fallacy (Wimsatt & Beardsley 1946).

Your Dungeon Crawler Carl example becomes D-EDIT-REPLACES: editing swaps an expertise-made block for attended choices.

**12. Pauses in boxes, and words that carry information** (new block in §6; rows **D-PAUSE-BOXES** and **D-OWN-SURPRISE**).

> "I do think you'd have different boxes in terms of how long those pauses tend to take."

- **The boxes are a known measurement:** lognormal mixtures with three components between words (lexical, supra-lexical, reflective).
- **Whether a writer's reflective boxes are her own is untested.** Per-student parameters held across prompts in one study (Guo et al. 2018); the reflective components were never checked. Sounding Line's D17 tests it.
- **Your "higher-information words"** become surprise against her own history, which D33 tests. At 10:15 you called the related question untestable ("There's no way to test four"), so D33 is labeled as my narrower attempt, not yours.

### README.md

A 17 October paragraph opens "Approved wording and source history". It also records your instruction to use the literature's terms and teach them.

### Left for your uptake

Ghost V23's N4b and N4c ran the probes that separate a learned end from a habit (G191). The README rule is that Ghost results enter these files on your uptake. Say the word and the next errata reads them in:
- **N4b:** changing the contingency gave 0.149 to 0.179 nats for two rules and nothing for habit.
- **N4c:** the reset probes gave 1.127 to 1.252 nats for all four rules, and actions alone left goal-directed control and habitual goal selection exactly aliased.

## Part B. Sources and quotation ledger

**Sources,** all Saturday 17 October 2026, in the project's theory and analyst thread:

| Key | Time | What it answered |
|---|---|---|
| K | 06:21 PDT | The curator's walkthrough of the analyst's 17 October theory pass |
| L | 07:52 PDT | The curator's answers to the analyst's 17 October discussion questions 1 to 10 |
| M | 10:15 PDT | The curator's answers to the analyst's second-round questions and scorecard |

**Filing direction (M):** "extract my quotes as you can, sprinkle them throughout, correct the grammar and stuff, and assume that I know what I'm talking about, that most of what you hear, that our fuck-ups are verbal artifacts, or speech-to-text artifacts, though, I mean, not all." Grammar is cleaned under that direction; meaning, hedges and conditionals are kept.

**Conventions:**
- Grammar is corrected as he directed: run-ons split, punctuation set, false starts and fillers removed.
- Omissions are marked [...]. Bracketed words are editorial.
- The raw transcripts contain no colons; where the cleaning draft had set one inside a quote, it became a comma or period. Punctuation is the filer's, not his.
- Profanity used as an intensifier is removed. Standalone profanity is kept (the 16 October rule).
- Withdrawn sentences are left out and listed below.

**Lexical repairs:**

| # | Raw transcript | Filed | Where |
|---|---|---|---|
| R1 | "manually rest control" | "manually wrest control" | RH §4 block |
| R2 | "It's being pulled to the area" | "[Her eye] is being pulled to the area" | RH §4 block (the preceding fragment "It's not her preference now, because her attention is." is incomplete and left out) |
| R3 | "you could find the autocorrect yourself" | "you could find the autocomplete yourself" | RH §6 block |
| R4 | "helps you hear more than anything" | "helps you here more than anything" | RH §6 block |
| R5 | "You can't have sudden expertise that appears through trauma. That's clearly a thing." | "You can have sudden expertise..." | TCL §1 block. The next sentence and the scenario require "can" |
| R6 | "secrets of actions" | "series of actions" | RH §3 block |
| R7 | "Tompathy" | "ToMpathy" | RH §3 block |
| R8 | "fearfulreasoning" | "fearful reasoning" | TCL §1 block |
| R9 | "Tomfathy" | "ToMpathy" | TTI §4 block |
| R10 | "thousand brain style" | "Thousand Brains style" | TTI §4 block |
| R11 | "the Mesa optimizers question" | "the mesa-optimizers question" | TTI §4 block |
| R12 | "dungeon crawler Carl" | "Dungeon Crawler Carl" (a book series title) | DT §6 block |
| R13 | Intensifiers removed: "messy as fuck" → "messy"; "record that shit" → "record that"; "goddamn" before "goals"; one before "algorithm", one before "messy" (editing), one before "softmax" (that sentence not filed) | | as listed |
| R14 | Insertions: "[set by]", "[there are]", "[thing]", "[it's]", "[authors']", "[Her eye]", "[for]" | | as listed |
| R15 | "narrow down in context" | "narrow down the context" | TTI opening block |
| R16 | "clouded from this expertise mapping" | "clouded by this expertise mapping" | TCL §1 block |
| R17 | "with capabilities of changing it gets to decide" | "with the capability of changing it. They get to decide" | RH §3 block |
| R18 | "the kind of raw true and it would" | "the kind of raw, true [thing] that would" | RH §5 block |
| R19 | "either intended to propagandize" | "whether intended to propagandize" | RH §5 block |
| R20 | "my answer to this kind of shit is always going to be" | "my answer is always going to be" (phrase removed) | RH §4 block |

**Not filed, and why:**
- **The consciousness lines at L and M.** He withdrew them at M: "every time I mention consciousness, I'm going to be wrong about things, because we don't know anything."
- **A speculative clinical aside at M's opening.** He flagged it as uncertain, and it is a clinical claim about a condition.
- **At M, "that's the third inference that's fine", and a repeated "third one being the person" after the list.** Both are slips that contradict the list itself.
- **L's "costs attract attention" passage.** He closed it with "I'm super not comfortable with this one."
- **L's remark on sight and trauma.** It depends on a question's context that the theory files don't hold.
- **The softmax sentence in L's set-point quote.** He called softmax "the wrong word" at M.

**Literature labels.** Labels follow the README:
- **read:** the primary text or full abstract was inspected in this day's research passes or the round-two fact check (Hagger, Hardwick, Ericsson & Simon, Wimsatt & Beardsley and Guo come from those);
- **abstract read:** only the abstract was;
- **snippet:** the source was seen in search results or checked as a citation only, not read.

Logan 1988, Anderson 1982, Norman 1981, Kelley 1973, Kaplan & Kaplan 1989, Frankfurt 1971, Bem 1972, Wegner & Wheatley 1999, Johansson et al. 2005, Ramsauer et al. 2020, Hubinger et al. 2019, Huys et al. 2012 and Babalola et al. 2026 are labeled snippet. Lakatos is cited through a summary read.

## Part C. Older text changed

Only afterwords and Confidence lines change. No existing row, quote or identifier is altered or removed.

| Edit | File | What changes |
|---|---|---|
| F1c | TTI §1 afterword | One sentence on G198; the Confidence line adds "the single-inference reading" to the untested list |
| F2c | TTI §4 afterword | One sentence on G199 |
| F4c, F4d | TCL §1 afterword | Two sentences on G200 and G201; the Confidence line adds the automatization account and one-shot expertise |
| F5c, F5d | TCL §5 afterword | One sentence on G202; the Confidence line adds the missing corrector |
| F6c | RH §3 afterword | One sentence on the three teardrop rows |
| F7c | RH §4 afterword | One sentence on HH-ATTENTION-TRUST |
| F8c, F8d | RH §5 afterword | Two sentences on the curator's one-scale account; the Confidence line adds HH-ONE-SCALE and HH-NO-TRANSLATION |
| F9c, F9d | RH §6 afterword | One sentence on HH-PERVASIVENESS; the Confidence line adds the pervasiveness test |
| F10c, F10d | DT §6 afterword | One sentence on the four new D rows; the Confidence statement adds them |

## Part D. Exact edits

**Apply in order:**
- Modes:
  - `insert_after` inserts the text immediately after the anchor;
  - `replace` replaces the anchor;
  - `insert_after_line_starting` appends the text to the end of the one line that starts with the anchor.
- Every anchor must match exactly once at application time; refuse the edit otherwise.
- Replace `{FILED}` with the application date.

**Then:**
1. Run `tools/theory_lint.py --all`.
2. Archive this file and an application receipt as `docs/design/archive/SOUNDING_LINE_THEORY_ERRATA_2026-10-17.md` and `docs/design/archive/THEORY_ERRATA_20261017_APPLIED.json`. These are the paths the README paragraph links.
3. Add the curator's three walkthroughs to `results/readings/PROVENANCE.md` the same day, one row each, as the root AGENTS.md requires.

This is a theory filing, not a result landing. It needs no FINDINGS entry beyond the receipt.

### F1a. `THE_TRIPLE_INFERENCE.md`, insert_after

Condition: none (the curator's 07:52 and 10:15 walkthroughs).

Anchor:

```text
([Rahnev & Denison, 2018](https://doi.org/10.1017/S0140525X18000936), read); timing, effort and
recorded context are the independent measures available here.
```

Text:

```text
**One inference, three entries** *(2026-10-17)*:

> Honestly, at this point it's not even the triple inference; it's all just one big inference of
> empathy. I've unified the three inferences, in a sense. What we have are a series of strategies
> you can use to solve the one big inference of empathy. [...] I guess figuring out the goal [...]
> was one of the shortcuts. It was a vertex. [...] I guess it still is the triple inference. It's
> fine. [...] One of them is just an early entry-point vertex that people often use, which isn't
> even a good one, as it can be so multifaceted, and it honestly probably comes down to, oh my god,
> the human trick of reverse engineering functionality based upon our own requirements. [...] So,
> functional reverse engineering from the top, assuming they would use it for the same thing we
> would use it for; the second one being the person; the third one being the process. It's still
> here. It survived somehow, all the way here.

*Curator's answers to the analyst's 17 October second-round questions and scorecard, 2026-10-17 (10:15 PDT), in the project's theory and analyst thread; filed {FILED}. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

> Functional just means, can I imagine situations in which having this nearby changes my
> forward-generating model? It's actually really easy to assess, especially if you can narrow down
> the context. Context-limited functionality is something that pretty quickly converges on
> something, largely because we share so many of our lower-level characteristics. All right, that's
> the reason. It's the human trick again.

*Curator's answers to the analyst's 17 October discussion questions, 2026-10-17 (07:52 PDT), in the project's theory and analyst thread; filed {FILED}. Contiguous excerpt; transcription repairs listed in the handoff.*

The restatement keeps the three questions and changes their standing. The canonical claim already
holds that evidence about one target constrains the posterior over the others; on the curator's
reading the three are entries into one joint inference, places a reader starts, rather than three
inferences run in turn. Computational theory of mind models the same thing as one inversion that
infers an agent's beliefs, desires and percepts jointly
([Baker et al., 2017](https://doi.org/10.1038/s41562-017-0064), read). The functional entry is the
entry from above already filed in [`READER_HEURISTICS.md`](READER_HEURISTICS.md) §3
(HH-GOAL-PYRAMID, HH-ENTRY-RELIABILITY); there it enters the maker's goal hierarchy, and here it
enters the whole inference. The person and the process are the new entries.

Its function-first half is what developmental psychology calls the teleological stance, reading an
act through its goal on the assumption that the actor takes the most efficient means available
([Gergely & Csibra, 2003](https://doi.org/10.1016/S1364-6613(03)00128-1), read), and its weakness is
the one the curator names, joined by the function-first explanation of artifacts already cited in
§3. People take another's perspective by adjusting from their own and stop once an estimate seems
plausible ([Epley et al., 2004](https://doi.org/10.1037/0022-3514.87.3.327), read), so a reader who
assumes the maker would use the thing as the reader would projects the reader's requirements onto a
goal that may have several parts. Two terms matter for outside readers. Research calls this
inference mentalizing or theory of mind, and empathy in its narrow sense, sharing another's feeling,
runs on a network separable from mentalizing
([Kanske et al., 2015](https://doi.org/10.1016/j.neuroimage.2015.07.082), read), so prose for
outside readers says theory of mind where the curator says empathy. And the unity is computational,
not mechanistic, since belief tracking appears to run on an efficient but inflexible system beside a
flexible and demanding one ([Apperly & Butterfill, 2009](https://doi.org/10.1037/a0016923), read).
No model of inference from artifacts with these three entries was found. Sounding Line card D37,
commissioned on 17 October, measures how much each entry carries on one scored task, a writer's next
decision.
```

### F1b. `THE_TRIPLE_INFERENCE.md`, insert_after_line_starting

Condition: none.

Anchor:

```text
| **L-tier2** |
```

Text:

```text
| **G198** | The three questions are entries into one joint inference, through the artifact's function, the person and the process, rather than three inferences run in turn; the functional entry, reverse engineering from the top on the assumption that the maker would use the thing as the reader would, is an early entry readers often use and an unreliable one, because goals have several parts and readers project their own requirements | **OPEN.** The curator's restatement (2026-10-17); the functional entry is HH-ENTRY-RELIABILITY's entry from above in [`READER_HEURISTICS.md`](READER_HEURISTICS.md) §3, applied to the whole inference. Theory of mind as one joint inversion, the teleological stance and egocentric anchoring have support (lit, READ); belief tracking may run on two systems, and empathy and mentalizing use separable networks (lit, READ); no model of inference from artifacts with these entries was found; Sounding Line card D37 is commissioned to measure the entries' weights on writers' decisions |
```

### F1c. `THE_TRIPLE_INFERENCE.md`, replace

Condition: none.

Anchor:

```text
the complete proposed expertise prerequisite. Confidence: untested, logic only for the
human recovery and relative-timescale claims; one bad test away for the scoped identity
curve and constructed demonstrations.
```

Text:

```text
the complete proposed expertise prerequisite. The three questions are held as entries into one
joint inference, through function, person and process, with the functional entry an often used and
unreliable one (G198). Confidence: untested, logic only for the
human recovery and relative-timescale claims and for the single-inference reading; one bad test
away for the scoped identity curve and constructed demonstrations.
```

### F2a. `THE_TRIPLE_INFERENCE.md`, insert_after

Condition: none (the curator's 07:52 walkthrough).

Anchor:

```text
([Baron & Spranca, 1997](https://www.rand.org/pubs/external_publications/EP19970407.html), read),
and honor may be partly such a rule.
```

Text:

```text
**A value is a decision you still agree with** *(2026-10-17)*:

> People keep telling me not to write in the register that I like to write in, and you know what?
> Fuck off with that. [...] It is kind of a value, in the sense that it's a solution that I have
> already put into place. I've worked out that this is a way of being seen as somewhat authentic,
> and that matters to me. [...] The biggest piece is that I made that decision previously, and I
> still agree with that decision, and therefore that decision is going to continue being my
> autocomplete [...]. If I disagree with that decision, then it would be a habit, or a previous goal
> that I have changed. [...] Whereas a habit would be, the motif just showed up at one point, I
> never really corrected it, and then I realized it was a bad idea, but I also don't want to put
> forth the effort in changing it, because cognitive fatigue, laziness, is certainly a thing. Habit
> takes effort to fight, because you have to repeat the other direction, and you could just be lazy.

> When a writer says she wants to be bolder, what she wants is for her automatic processes to be
> bolder. You can manually make boldness decisions, and what's more, it's hard to see the boldness
> decisions, because the expertise distorts your view of what's possible anyway, through attention.
> But as you make more and more bold decisions, the automatic processing finds more opportunities to
> use it. It becomes easier to take them reflexively. [...] The statement is kind of a plan. It's a
> plan to find opportunities and take them over time until it becomes automatic. And by definition,
> it is a value under construction, too.

> We all set up our own autocomplete, and we are our own autocomplete. However, we acknowledge that,
> more specifically, we are our current intent. And the goal is to craft it, to have your
> autocomplete always match your current intent.

> One of the answers is that all of your values are set points, in gradient fashion. You kind of
> need to collect all of them and put them into one big smorgasbord, which ToMpathy does currently
> support. [...] I think you balance all of the goals all the time, in the Thousand Brains style,
> but you do it from a single perspective, and those goals are solutions toward this final [...].
> God, I want to say parameters on the loss function of survival, but that's really the
> mesa-optimizers question, which is one that is super relevant here, because where do you stop, and
> what is the stopping point?

*Curator's answers to the analyst's 17 October discussion questions, 2026-10-17 (07:52 PDT), in the project's theory and analyst thread; filed {FILED}. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

The curator's test for a value is present endorsement. A learned solution stays a value while he
would still make the decision it encodes, and becomes a habit, or a goal he has dropped, once he
would not; the effort of reversing it is what keeps a disowned habit running. Philosophy has the
same structure in Frankfurt's account of the person, where a desire is one's own when a second-order
volition endorses it
([Frankfurt, 1971](https://www.yorku.ca/dimock/documents/FrankfurtFreedomoftheWillandtheConceptofaPerson.pdf),
snippet), and this file's wanting to want is the second-order desire. Psychology draws its line
elsewhere. Habits are responses cued by stable contexts that run whether or not they serve the
current goal ([Wood & Neal, 2007](https://doi.org/10.1037/0033-295X.114.4.843), read), and
endorsement adds what the outcome probes of G191 cannot see, the maker's present verdict on the
routine.

The laziness he names has a cost model. Control is allocated by its expected value net of an
intrinsic cost ([Shenhav, Botvinick & Cohen, 2013](https://doi.org/10.1016/j.neuron.2013.07.007),
read), which predicts that a disowned habit survives where the stakes are low. Fatigue is the weaker
reading, since a 23-laboratory replication of the ego-depletion effect found it near zero, d = 0.04
([Hagger et al., 2016](https://doi.org/10.1177/1745691616652873), abstract read). A stated
aspiration such as wanting to be bolder is, on his account, a plan to make the automatic process
match the current intent by repetition, a value under construction, which is the route to wanting to
want through repetition filed from the 2026-10-14 walkthrough. The analyst's caution is that
endorsement is self-report, and [`DECISION_TRACES.md`](DECISION_TRACES.md) §6 holds that a maker's
account of a purpose passes through a self-model, so the criterion needs a behavioral check. A
routine he endorses should be defended by varied means when disturbed, G191's test, and one he
disowns should yield wherever the stakes rise. His closing question, where a stack of goals serving
survival stops, is the mesa-optimization question of [`ALIGNMENT.md`](ALIGNMENT.md), a learned
optimizer whose objective can come apart from the one that trained it
([Hubinger et al., 2019](https://arxiv.org/abs/1906.01820), snippet), and his balancing of every
goal at once is, on the analyst's reading, closest to the largest-deficit rule above, though he
doubted any such scaling.
```

### F2b. `THE_TRIPLE_INFERENCE.md`, insert_after_line_starting

Condition: none.

Anchor:

```text
| **G192** |
```

Text:

```text
| **G199** | A learned solution is a value while the maker still endorses the decision it encodes, and a habit or a dropped goal once the maker no longer would; a disowned habit persists where the effort of reversing it outweighs its stakes, and a stated aspiration is a plan to make the automatic process match the current intent | **OPEN.** The curator's criterion (2026-10-17). Second-order endorsement in philosophy (lit, SNIPPET); habits as context-cued responses insensitive to current goals, and control allocated by its expected value net of cost (lit, READ); the ego-depletion account of fatigue failed a multi-laboratory replication (lit, READ); endorsement is self-report, so a behavioral check is needed, and G191's disturbance probe is the candidate; no project measurement |
```

### F2c. `THE_TRIPLE_INFERENCE.md`, replace

Condition: none.

Anchor:

```text
state, and to an end only when it passes that test (G192). The probes come from animal learning, and
the human evidence on habits is mixed.
Confidence: untested, logic only, with the sim demonstration held by §5.
```

Text:

```text
state, and to an end only when it passes that test (G192). The probes come from animal learning, and
the human evidence on habits is mixed. The curator's own test for a value is present endorsement, with
a habit as a routine the maker no longer endorses but has not paid to reverse (G199).
Confidence: untested, logic only, with the sim demonstration held by §5.
```

### F3. `THE_TRIPLE_INFERENCE.md`, insert_after

Condition: none (the curator's 07:52 walkthrough).

Anchor:

```text
[`READER_HEURISTICS.md`](READER_HEURISTICS.md) (stated in its §1, tested in its §8) with the
concealment caveat carried there; here it is one identifiability assumption among four.
```

Text:

```text
**A theory that can't lose** *(2026-10-17)*:

> I am having more trouble with this one. If everything becomes calibration, the theory can't lose.
> We're all zeroing in on an inference. This is always going to be an inference toward something
> that we're trying to find little tricks to get closer and closer on. That's what we're doing.
> That's where we're at right now. I know. That's why I'm so aggressive with this, because the
> theory can't lose. Isn't it fun to be on the right side of history, betting on the horse that can
> move at an infinite speed? [...] We're just being happy about being on a roll. Honestly, I'm kind
> of stumbling.

*Curator's answers to the analyst's 17 October discussion questions, 2026-10-17 (07:52 PDT), in the project's theory and analyst thread; filed {FILED}. Contiguous excerpt with a marked omission; transcription repairs listed in the handoff.*

He offered this while, in his words, stumbling. The analyst agrees with the description and dissents
from its comfort. A framework in which every outcome is calibration toward an inference cannot be
refuted by any one result, which philosophy of science calls the hard core of a research programme,
theories shielded from revision and surrounded by a protective belt of adjustable ones, and a
programme is judged by whether the theories around its core keep predicting new facts that are then
confirmed, or only absorb what arrives (Lakatos, 1970, through a
[summary](https://en.wikipedia.org/wiki/Research_program) read). What can lose here are the models
inside the framework, and each needs a rival that lacks its structure and a margin it must beat. The
first such test, frozen on 17 October as Sounding Line's FX1, asks whether inferring goals from a
writer's records predicts that writer better than the same records without a goal model, by a
registered share of the gap to the writer's own consistency ceiling. It cannot run yet, because the
project's instruments have not recovered planted taste or habit, and a failure now would indict the
pipeline rather than the framework, so the commissioned tests of the instruments come first. A
programme whose models only ever absorb results is what Lakatos called degenerating, however safe
its core.
```

### F4a. `THREE_COGNITIVE_LAYERS.md`, insert_after

Condition: none (the curator's 06:21, 07:52 and 10:15 walkthroughs).

Anchor:

```text
concurrent control remains a rival. Serial switching is therefore a candidate description of
focal control, not a frozen mechanism.
```

Text:

```text
**Attention trains the autocomplete, and habits grow** *(2026-10-17)*:

> Effectively, what we're trying to do here is capture System 2. Okay, we can speak that language;
> I'm cool with that. And what you have attention over is System 2, and System 2 creates System 1
> over time.

> I'll accept the word fluent. I think it's reasonable to have, but I do think fluent just means
> compressing the fastest. I mean, it's already compressed, but you're running the same algorithm.
> It's expertise. It's pre-compressed. It's the autocomplete.

> Chess experts [...] are leaving their eye movement on autocomplete while they attend to their own
> internal thoughts. They are thinking about the move that they are considering, and they aren't
> even really attending to their visual stimuli. So their visual stimuli, on autocomplete, simply
> move toward the most rapidly compressing information, the thing that's familiar, their fluency.

> The habit problem I hadn't really properly considered as terrible as it was, but you would get, oh
> my god, ghosts of repetitions, little minor solutions that you would be able to apply in bigger
> and bigger circumstances that would then be misapplied. It would kind of just grow. You would grow
> habits, and your job, in part, as the attention, is to squash those habits before they become
> problematic.

*Curator's answers to the analyst's 17 October second-round questions and scorecard, 2026-10-17 (10:15 PDT), in the project's theory and analyst thread; filed {FILED}. Separate excerpts with a marked omission; transcription repairs listed in the handoff.*

The research vocabulary he accepts has moved on. Its authors now say Type 1 and Type 2 processing
rather than System 1 and System 2, because systems suggest, falsely, two processes located in two
specific places; Type 2 is hypothetical thinking that loads working memory, and Type 1 includes both
innate modules and "experiential associations that have been learned to the point of automaticity"
([Evans & Stanovich, 2013](https://doi.org/10.1177/1745691612460685), read). The curator's claim
that deliberate processing builds automatic processing is one of Type 1's routes, with two classic
mechanisms, past solutions stored as instances and retrieved in one step in place of the algorithm
that first produced them (Logan, 1988, snippet), and slow declarative rules compiled into fast
productions (Anderson, 1982, snippet). It is not the only route, since innate modules and implicit
learning also make Type 1 processes, and the two-type split itself is disputed
([Melnikoff & Bargh, 2018](https://doi.org/10.1016/j.tics.2018.02.001), read). Fluency as
pre-compressed processing fits instance theory, where a familiar input retrieves an answer instead
of computing it, and habits resurface when people must respond under time pressure
([Hardwick et al., 2019](https://doi.org/10.1038/s41562-019-0725-0), abstract read).

The growth of habits has its closest experimental match in strong-but-wrong errors. A capture error
is a frequent, well-learned sequence taking over an intended one that shares its opening (Norman,
1981, snippet), and in sequence learning more training produced more errors on new sequences that
resembled the trained ones, errors made at normal speed that "appeared to be undetected"
([Woltz et al., 2000](https://doi.org/10.1037/0278-7393.26.3.601), read). The literature does not
yet support two parts of the claim. No study was found in which habits spread to larger and larger
circumstances, and habits are mostly right, "the efficient, default mode of response" bound to the
contexts that built them
([Wood & Rünger, 2016](https://doi.org/10.1146/annurev-psych-122414-033417), read), so
misapplication is the exception the account must explain, by similarity to the trained context. The
chess reading needs one correction. In the study it answers, experts who said they were looking for
a better move kept their eyes on features of the solution they already knew and did not find the
better one ([Bilalić, McLeod & Gobet, 2008](https://doi.org/10.1016/j.cognition.2008.05.005), read),
so the familiar solution held their search as well as their gaze, and attention running internally
did not escape it. Attention as the corrector that squashes misfiring habits is the policy-precision
reading in [`READER_HEURISTICS.md`](READER_HEURISTICS.md) §4.

**Trauma is one-shot expertise** *(2026-10-17)*:

> I do think that there might be an element to this that I'm missing, something like, the expertise
> decisions influence the spread of the current decisions you're looking at. It kind of leaks in,
> and I don't know if it always leaks in through unexamined subordinate decisions, or whether people
> sneak in fearful reasoning because they have been a coward in their past. [...] I think attention
> might be corrupted by expertise slightly too, maybe? That's a wall that I have to acknowledge is
> one that I am assuming, and I'm doing so unjustly.

*Curator's walkthrough of the analyst's 17 October theory pass, 2026-10-17 (06:21 PDT), in the project's theory and analyst thread; filed {FILED}. Contiguous excerpt with a marked omission; transcription repairs listed in the handoff.*

> I think the fearful reasoning is a big part of it. I think that's how it infects your current
> reasoning. [...] I think it's unintended expertise. [...] Trauma would be unintended expertise,
> which is what this is too. [...] But of course it also changes what you can see as an option at
> all, because it is expertise as well. Expertise would distort both directions. It adds, but it
> also removes possibilities from the landscape. And if your expertise is one of fear, then that is
> the way that the possibilities are removed from the landscape, because it applies itself
> accidentally.

*Curator's answers to the analyst's 17 October discussion questions, 2026-10-17 (07:52 PDT), in the project's theory and analyst thread; filed {FILED}. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

> You can have sudden expertise that appears through trauma. That's clearly a thing. So let's say
> she had a sudden trauma, and now this expertise is pattern-matching onto things that it shouldn't
> be pattern-matched onto, and she can't even see that her characters could fight back in this
> scenario [...]. Other writers in the same spot would not have that same problem. They would be
> more likely to see that option, because their lens isn't clouded by this expertise mapping that
> was flashed into position through one-shot learning in trauma. [...] She could even be actively
> trying to push out past that. [...] It's like making a chip in the wall of a cave that slowly
> erodes that cave around you a little bit further every time. But that cave-wall erosion is decided
> by expertise. [...] All the automatic decisions would kind of work against you a little bit, and
> you'd have to fight against yourself to an extent, as they would auto-fit scenarios that are
> slightly incorrect but fit well enough to make sense for the inference at large. Your autocomplete
> is broken.

> Expertise would sharpen discrimination through attending to more and more precise, small portions
> of what it is you're processing. But fear blurs it, because it's a one-shot. It is an incredibly
> highly weighted one-shot experience that then becomes applied to all kinds of stuff. The very
> process would be blurry by definition. It's intended to quickly and rapidly learn a new thing and
> apply it to new scenarios, because it is important.

*Curator's answers to the analyst's 17 October second-round questions and scorecard, 2026-10-17 (10:15 PDT), in the project's theory and analyst thread; filed {FILED}. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

The claim joins two literatures. Fear learning is the clearest case of learning from one highly
weighted experience, and stronger threats widen the generalization gradient, the range of stimuli
that come to evoke the response, without changing the initial learning
([Dunsmoor et al., 2017](https://doi.org/10.1037/bne0000186), read). Expertise runs the other way,
by differentiation, through which "stimuli that were once indistinguishable become psychologically
separated" ([Goldstone, 1998](https://doi.org/10.1146/annurev.psych.49.1.585), read). The half that
removes options has a computational home. In planning tasks people prune decision trees at branches
that begin with a large loss, a reflexive Pavlovian response that shapes goal-directed choice even
when the pruned branch held the better route
([Huys et al., 2012](https://pmc.ncbi.nlm.nih.gov/articles/PMC3297555/), snippet), which is fear
removing possibilities from the landscape.

Four findings narrow the claim. Dunsmoor and colleagues varied the threat's intensity, not the
number of exposures, and the curator's account joins the two. One-trial fears are selective, a
"nonarbitrary and limited set of objects"
([Seligman, 1971, republished 2016](https://doi.org/10.1016/j.beth.2016.08.006), read), and aversive
learning sharpened the discrimination of odors in one study
([Li et al., 2008](https://doi.org/10.1126/science.1152837), read) while blunting discrimination in
another ([Resnik et al., 2011](https://doi.org/10.1038/nn.2802), read). And broad generalization
from one example is what any Bayesian learner does before more examples tighten it
([Tenenbaum & Griffiths, 2001](https://doi.org/10.1017/S0140525X01000061), abstract read), so
breadth after one shot is not by itself a mark of fear. Trauma in its clinical sense has criteria
this file does not test; the claim filed here is about one-shot aversive learning acting as
expertise. Its reader-side consequence, that options pruned this way show as a branch never drawn
across a maker's work while other makers in the same place draw it, is the pervasiveness test in
[`READER_HEURISTICS.md`](READER_HEURISTICS.md) §6.
```

### F4b. `THREE_COGNITIVE_LAYERS.md`, insert_after_line_starting

Condition: none.

Anchor:

```text
| **G195** |
```

Text:

```text
| **G200** | Attended, deliberate processing builds automatic routines over time, the curator's System 2 creating System 1, and routines built by repetition grow into bigger and bigger circumstances and are misapplied unless attention checks them; fluency is the speed of a routine already compressed | **OPEN.** Automatization by stored instances and by compiled rules, and strong-but-wrong errors that rise with training and go undetected, have support (lit, READ and SNIPPET); Type 1 processing also has innate and implicit sources, the two-type split is disputed, and habits are mostly correct and bound to context, with no study found of habits spreading to larger circumstances (lit, READ); misapplication by similarity to the trained context is the analyst's proposed mechanism; Sounding Line card D35 is commissioned to test whether a writer's corrections become her defaults |
| **G201** | A single highly weighted aversive experience acts as expertise learned in one shot, broad where expertise built by repetition is narrow; it prunes options from the maker's landscape and fits later situations it does not match, while repeated expertise sharpens discrimination | **OPEN.** Stronger threats widen fear generalization, perceptual expertise differentiates, and aversive outcomes prune planning trees (lit, READ and SNIPPET); one-trial fears are selective, aversive learning both sharpens and blunts discrimination in different studies, and breadth after one example is general Bayesian behavior (lit, READ); the clinical sense of trauma is not tested; Sounding Line card D38 is a mild, exploratory analog, and Ghost study N9 tests whether pruning can be told from dislike |
```

### F4c. `THREE_COGNITIVE_LAYERS.md`, replace

Condition: none.

Anchor:

```text
studies of shared novelty (G194); that its reward is compression progress is the analyst's untested
proposal (G195).
```

Text:

```text
studies of shared novelty (G194); that its reward is compression progress is the analyst's untested
proposal (G195). Deliberate processing that builds automatic routines is one of several documented
routes to automaticity; that such routines grow and misfire has a partial match in strong-but-wrong
errors and no direct study (G200). A
one-shot aversive experience acting as broad expertise that prunes options has support in parts and
findings that narrow it (G201).
```

### F4d. `THREE_COGNITIVE_LAYERS.md`, replace

Condition: none.

Anchor:

```text
scaffold, formation account, universal prerequisite, drive mapping, SEEKING prediction, drive
repurposing and both PLAY proposals; one bad test away for the scoped
```

Text:

```text
scaffold, formation account, universal prerequisite, drive mapping, SEEKING prediction, drive
repurposing, both PLAY proposals, the automatization account and one-shot expertise; one bad test
away for the scoped
```

### F5a. `THREE_COGNITIVE_LAYERS.md`, insert_after

Condition: none (the curator's 07:52 and 10:15 walkthroughs).

Anchor:

```text
produce; telling them apart needs evidence on which later components read each copy.
```

Text:

```text
**Autocomplete all the way down** *(2026-10-17)*:

> Machines may only have the autocomplete, yeah? The second layer of attention-grabbing? Machines
> don't have that, do they? That's all humans. We always do that.

*Curator's answers to the analyst's 17 October discussion questions, 2026-10-17 (07:52 PDT), in the project's theory and analyst thread; filed {FILED}. Contiguous excerpt; transcription repairs listed in the handoff.*

> Okay, so it's not attention, it's the autocomplete, [for] "Attention Is All You Need". [...] It's
> just associative memory. All this is, is just the vectorization.

> I don't know that a machine that is autocomplete all the way down can grow it. Attention is a
> separate thing. It's the corrector.

> Self-reflection, verification, dynamic strategy adaptation. I'm not convinced that people are
> actually seeing those events, and that they aren't seeing echoes of the strategies humans use,
> very carefully autocompleted, because many of those processes would have specific autocomplete
> mechanisms.

*Curator's answers to the analyst's 17 October second-round questions and scorecard, 2026-10-17 (10:15 PDT), in the project's theory and analyst thread; filed {FILED}. Separate excerpts with a marked omission; transcription repairs listed in the handoff.*

The word attention means two things here. In a transformer it is a learned weighting over earlier
positions, and its update rule is that of a modern Hopfield network, a content-addressable
associative memory ([Ramsauer et al., 2020](https://arxiv.org/abs/2008.02217), snippet), which
supports the curator's reading of it as the autocomplete. In this file attention is the corrector,
the part that sets how far to trust each signal and can override the routine
([`READER_HEURISTICS.md`](READER_HEURISTICS.md) §4). Whether language models have that second layer
is open, and the evidence on reasoning models leans his way without settling it. Reinforcement
learning with verifiable rewards improves a model's first attempt while the base model wins when
many attempts are allowed, so the trained abilities "originate from and are bounded by the base
model" ([Yue et al., 2025](https://arxiv.org/abs/2504.13837), read); base models already show the
self-reflection that training was credited with
([Liu et al., 2025](https://arxiv.org/abs/2503.20783), read); and training gains require
verification, backtracking and subgoal setting to be present beforehand
([Gandhi et al., 2025](https://arxiv.org/abs/2503.01307), read).

Against that, prolonged training produced gains "where base models fail entirely regardless of the
number of attempts" ([ProRL, 2025](https://arxiv.org/abs/2505.24864), read), and a transformer
trained from scratch with only final-answer rewards learned an algorithmic chain of thought
([Rubin & Ringel, 2026](https://arxiv.org/abs/2609.28625), read). Verification is the sharper point.
Models' hidden states encode whether an answer is correct, and the models fail to use that signal
([Zhang et al., 2025](https://arxiv.org/abs/2504.05419), read), a trust signal without the corrector
that would act on it. The position the literature supports as of October 2026 is that such training
mostly reweights strategies learned from human text, with real but narrow expansion under particular
conditions, so echoes of human strategies fits most of it and autocomplete only overstates it.
```

### F5b. `THREE_COGNITIVE_LAYERS.md`, insert_after_line_starting

Condition: none.

Anchor:

```text
| **G196** |
```

Text:

```text
| **G202** | Language models are associative autocomplete without the second layer, the corrector that sets how far to trust each signal; transformer attention is associative memory, not attention in this file's sense, and reinforcement learning on reasoning mostly reweights strategies learned from human text rather than growing that layer | **OPEN for the missing corrector; CONTESTED (lit) for autocomplete only, since narrow genuine expansion is documented.** Transformer attention as associative memory (lit, SNIPPET); reasoning training bounded by the base model's strategies, self-reflection present before training, and correctness encoded but unused (lit, READ); prolonged training and training from scratch show narrow genuine expansion (lit, READ); no project measurement |
```

### F5c. `THREE_COGNITIVE_LAYERS.md`, replace

Condition: none.

Anchor:

```text
support and live rivals (G196). Confidence: existence, rotation, the adapter-edge rejection, and the
```

Text:

```text
support and live rivals (G196). Whether models lack the corrector that sets trust, so that their
reasoning training reweights human strategies rather than growing a second layer, leans the curator's
way with narrow counterevidence (G202). Confidence: existence, rotation, the adapter-edge rejection,
and the
```

### F5d. `THREE_COGNITIVE_LAYERS.md`, replace

Condition: none.

Anchor:

```text
causality; the depth-copy conjecture is untested, logic only (G196).
```

Text:

```text
causality; the depth-copy conjecture and the missing corrector are untested, logic only (G196,
G202).
```

### F6a. `READER_HEURISTICS.md`, insert_after

Condition: none (the curator's 07:52 and 10:15 walkthroughs).

Anchor:

```text
serving belonging alone, and it may be lust on top, habit or a learned end, which the second probe
of G191 in [`THE_TRIPLE_INFERENCE.md`](THE_TRIPLE_INFERENCE.md) §4 separates.
```

Text:

```text
**Teardrops that emerge, overlay, and are topped by the last pass** *(2026-10-17)*:

> Everyone has a teardrop that is them. At the very top of that teardrop, hypothetically, you've got
> survival, but just beneath it are all of your attempts to solve it. You're a teardrop missing its
> tip, under this frame of reference, and it's made up of a bunch of tiny smaller teardrops that fit
> together. They kind of form out your plan for your life, and they literally are series of actions
> you want to take for your life.

> I think you start with a single goal, and other goals kind of emerge from it. You notice, for
> example, as you are creating that spoon, that it actually fits in such a way that you could use
> this spoon in other ways. You could use it to impress the lady that you like. And so you then put
> a little bit of effort into making sure that both of these teardrops are stable, but now you're
> trying to do both, and it's hard to balance the two [...]. You make it look good for the lady, but
> then it's not as good a spoon.

> I think what the editor is doing is expanding the teardrop. You, as an author, had a specific
> goal. The editor is making different goals. [...] As I say this, the author probably does it for
> many different goals, which is why we have the weird teardrop shape in ToMpathy, where it's really
> multiple teardrops overlaid on top of each other. [...] So the editor really overlays other
> teardrop shapes on top, to make sure that they also have appropriate fit.

*Curator's answers to the analyst's 17 October discussion questions, 2026-10-17 (07:52 PDT), in the project's theory and analyst thread; filed {FILED}. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

> You can have a starting goal, but the problem is, once you have a starting goal, the other
> pattern-matching expertise pieces can look at what you have created, look at the landscape, the
> tools that you now have in front of them, the new starting positions that now exist, and you can
> literally, if you want, discard your original goal and decide that this is your new goal, that
> you've made something more than you expected.

> I do think that the top goal is kind of [set by] the last person to pass judgment over the whole
> thing with the capability of changing it. They get to decide what that top goal is. [...] If they
> had handed it over to the editor, so the editor got the final stamp of approval, or they both had
> to do it together, simultaneously, both of them agreeing on the same set, that would be the only
> case in which both of them have parallel, equivalently high teardrops, I guess.

> Practically speaking, there's no top as much as [there are] different lenses. There are different
> overlays that you can add to it, and you have to make sure that your overlay lines up properly.
> [...] The only way to truly climb on top of someone, teardrop-wise, is if you saw they made a
> comment and you wanted to address it in some way, by incorporating it into the overall structure.
> And then you put a node on top of that, and all of a sudden it becomes leading into your teardrop
> instead. [...] I think the hierarchy is only implied if it's implied by the structure of the
> creation, but it isn't necessarily implied by the actual creation. Not every creation needs a
> hierarchy inherently.

*Curator's answers to the analyst's 17 October second-round questions and scorecard, 2026-10-17 (10:15 PDT), in the project's theory and analyst thread; filed {FILED}. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

The teardrop is the curator's picture of the goal structure this section reads, a maker's hierarchy
capped by survival with its tip missing and built from smaller teardrops of the same shape. Three
claims come with it. Goals emerge during making, as expertise sees new uses in the partial work, and
an emergent goal can replace the one that started it. The top goal of a shared work belongs to
whoever holds the last pass with power to change it, with equal tops only when parties sign off
together. And goal structures overlay rather than nest, so a hierarchy exists only where the
creation's structure implies one, and one party rises above another only by taking the other's
contribution into its own structure under a node of its own. The research names for the first claim
are opportunistic planning
([Hayes-Roth & Hayes-Roth, 1978](https://apps.dtic.mil/sti/tr/pdf/ADA064445.pdf), snippet) and, in
design, problem-solution co-evolution
([Dorst & Cross, 2001](https://cschan.arch.iastate.edu/235/20_Dorst-Creativity_coevolution.pdf),
snippet), and one means serving several goals at once is multifinality.

Law matches the second claim more closely than psychology does. In the Ninth Circuit's test for
joint authorship, control, superintending the work as its "master mind", is the first of three
factors, and "absence of control over the work is strong evidence of absence of co-authorship"
(Aalmuhammed v. Lee, 2000, through a
[summary](https://www.fwrv.com/news-articles/co-authorship-claim-denied) read). People's own sense
of authorship tracks something else. Writers did not consider themselves the owners and authors of
text a model generated, and their sense of ownership rose with their influence on it
([Draxler et al., 2024](https://doi.org/10.1145/3637875), read), and credit in human and AI
co-creation varied with the type, amount and initiative of each contribution
([He, Houde & Weisz, 2025](https://arxiv.org/abs/2502.18357), read). So the last pass decides who
may declare the top goal, contribution decides whose goals the work carries, and the two part where
the last party changes little. A single-author preprint argues that final selection authority is not
sufficient for authorship ([Cao, 2026](https://arxiv.org/abs/2609.10738), read, not peer reviewed).

On the third claim the cognitive literature is split. Routine action sequences can be learned with
no explicit hierarchy of schemas, context held in a single distributed representation
([Botvinick & Plaut, 2004](https://doi.org/10.1037/0033-295X.111.2.395), read), while flexible
behavior has been argued to require explicit, hierarchically organized goal representations
([Cooper & Shallice, 2006](https://doi.org/10.1037/0033-295X.113.4.887), read). Without a hierarchy
the last judge's top goal describes an attribution rather than the work's structure, which is the
analyst's reading of where the second and third claims meet. Ghost study N12, commissioned on 17
October, tests what an artifact alone can show of emergence, overlays and final authority, with the
prediction that final authority is visible only where the overlaid goals conflict.
```

### F6b. `READER_HEURISTICS.md`, insert_after_line_starting

Condition: none.

Anchor:

```text
| **HH-SACRIFICE-ORDER** |
```

Text:

```text
| **HH-GOALS-EMERGE** | A maker starts from one goal, and others emerge during making as expertise sees new uses in the partial work; an emergent goal can join the first or replace it, and balancing two goals with one focus of attention costs each some fit | **OPEN.** The curator's claim (2026-10-17); the research terms are opportunistic planning, problem-solution co-evolution in design, and multifinality for one means serving several goals (lit, SNIPPET); learned ends that outlive their origin are G191 in [`THE_TRIPLE_INFERENCE.md`](THE_TRIPLE_INFERENCE.md) §4; Ghost study N12 is commissioned to test what an artifact shows of it |
| **HH-LAST-PASS** | The top goal of a shared work belongs to whoever holds the last pass over the whole with power to change it; equal tops exist only when parties sign off together | **OPEN for the last pass as the right to declare the top goal; CONTESTED (lit) for authorship following the last pass.** One appeals court's joint-authorship test weighs control first (lit, SNIPPET); writers' felt ownership and lay credit track influence and contribution rather than final say (lit, READ); one preprint argues final selection authority is insufficient (lit, READ); Ghost study N12 tests when final authority is identifiable from the artifact |
| **HH-OVERLAYS** | Goal structures overlay rather than nest; a work carries several makers' structures as lenses, a hierarchy exists only where the creation's structure implies one, and one party rises above another only by incorporating the other's contribution under a node of its own | **OPEN.** Routine sequences are learnable without a schema hierarchy, while flexible action has been argued to need one (lit, READ); the curator's claim; no project measurement; Ghost study N12 compares single-top and overlay readers |
```

### F6c. `READER_HEURISTICS.md`, replace

Condition: none.

Anchor:

```text
(HH-SACRIFICE-ORDER). Confidence: untested, logic only, resting on a contested literature.
```

Text:

```text
(HH-SACRIFICE-ORDER). Goals also emerge during making and can replace the first (HH-GOALS-EMERGE),
the top goal of a shared work belongs to whoever holds the last pass, a claim the law supports and the
psychology of credit qualifies (HH-LAST-PASS), and several makers' structures can overlay one work
without nesting (HH-OVERLAYS). Confidence: untested, logic only, resting on a contested literature.
```

### F7a. `READER_HEURISTICS.md`, insert_after

Condition: none (the curator's 07:52 and 10:15 walkthroughs).

Anchor:

```text
opposite timing. An audited reversal follows a fast first choice and a later review, a near-tie
reversal follows a slow first choice, and only the first carries the higher goal.
```

Text:

```text
**Attention is deciding what to trust** *(2026-10-17)*:

> Whenever we're in any kind of psychological space, my answer is always going to be, it's all of
> them. Every answer is always "it's all of them", because the one overarching rule is anything that
> can be associated will. That is a bit of a cop-out, though, so let me give you a better answer.

> Her past is just all previous habits. So yes, obviously it is her past, because it's pulling from
> that. [...] [Her eye] is being pulled to the area that is compressing the fastest, which is that
> corner, but she is purposefully going to move herself away from that, and that is her actual
> preference. That is her wanting to want, in this case. [...] I would even say that the automatic
> process of her eyes is to zero in on things that have compressing information. And if that's the
> flow state of the eyes, she will literally have to manually wrest control of her eyes to move them
> elsewhere. And that action, that very action, is attention.

> I do think, off the cuff, that trust is going to be the big piece. You are deciding how much to
> weight each signal, as always. [...] Allocating trust on, like, a math level is what we're doing.

*Curator's answers to the analyst's 17 October discussion questions, 2026-10-17 (07:52 PDT), in the project's theory and analyst thread; filed {FILED}. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

> I'm treating attention as both. You're right. Maybe I'm assuming it's the same thing, that what
> you're doing is adjusting the trust on various signals to control. Is that how you get control?
> The effort is gained through adjusting trust levels? That's what you do as an attender. All you
> can do, the safe option, is to decide what to trust. And in doing so, that automatically moves
> your eyes to some other place. There are manual ways to do this. You can just manually increase
> the belief that there is something interesting to be had in part of your field of view, and you
> can use that to wrench your eyes wherever you want. Maybe that's what attention is.

> Attention is a separate thing. It's the corrector. [...] Attention is trust, is what I think I'm
> trying to say here. Or rather, attention is deciding to run an inference on whether to trust in a
> given specific setting.

*Curator's answers to the analyst's 17 October second-round questions and scorecard, 2026-10-17 (10:15 PDT), in the project's theory and analyst thread; filed {FILED}. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

The research term for the curator's trust is precision. In predictive processing, attention is
"inferring the level of uncertainty or precision during hierarchical perception", and a cue that
raises the expected precision at a location draws processing there
([Feldman & Friston, 2010](https://doi.org/10.3389/fnhum.2010.00215), read), which is his manual
increase in the belief that something interesting lies in one part of the field of view. The
framework splits what he joins, though. Sensory precision is attention in that narrow sense; where
to look next is driven by expected information gain, which Parr and Friston separate as salience
([Parr & Friston, 2019](https://doi.org/10.1016/j.copsyc.2018.10.006), read); and control is the
precision on policies, the weight given to goal-directed evaluation against a habit prior. Effort
then reads as the divergence between context-sensitive beliefs about how to act and the
context-insensitive habit, and "effort is exerted to overcome a mental habit"
([Parr, Holmes, Friston & Pezzulo, 2023](https://doi.org/10.1016/j.neuropsychologia.2023.108562),
read; [Zénon, Solopchuk & Pezzulo, 2019](https://doi.org/10.1016/j.neuropsychologia.2018.09.013),
read). That reverses one of his phrasings. Effort is the cost of acting on sharp beliefs against the
habit, not something trust produces, and expected information gain follows from current uncertainty
rather than being set at will.

The safe corner fits the split. Her gaze runs on the habit and on what compresses fastest, and
wrenching it away is policy precision overriding the habit prior, the corrector of his second
answer. Arbitration between habitual and goal-directed control by their relative uncertainty is a
standard account of which one wins ([Daw, Niv & Dayan, 2005](https://doi.org/10.1038/nn1560), read).
Rival accounts of effort need no habit prior. Control may be allocated by its expected value net of
cost ([Shenhav, Botvinick & Cohen, 2013](https://doi.org/10.1016/j.neuron.2013.07.007), read) or
priced by the opportunity cost of other uses
([Kurzban et al., 2013](https://doi.org/10.1017/S0140525X12003196), read). Sounding Line card D39,
commissioned on 17 October, asks whether writers examine a source's next offers harder after it
fails them, and Ghost study N15 asks what that test can separate.
```

### F7b. `READER_HEURISTICS.md`, insert_after_line_starting

Condition: none.

Anchor:

```text
| **HH-REVERSAL-KINDS** |
```

Text:

```text
| **HH-ATTENTION-TRUST** | Attention is the corrector that sets how far to trust each signal, an inference on whether to trust in a given setting; control, and the effort of wrenching gaze, come from adjusting trust, as when raising the believed interest of a region moves the eyes there | **OPEN.** Attention as precision, salience as expected information gain, policy precision against a habit prior, effort as divergence from habit and arbitration by uncertainty each have support (lit, READ); the framework separates the attention, salience and control the curator joins, and treats effort as the cost of overriding habit rather than a product of trust (lit, READ); Sounding Line card D39 and Ghost study N15 are commissioned |
```

### F7c. `READER_HEURISTICS.md`, replace

Condition: none.

Anchor:

```text
opposite timing (HH-REVERSAL-KINDS). No model result licenses their internal psychological
```

Text:

```text
opposite timing (HH-REVERSAL-KINDS). Attention is held to be the corrector that allocates trust,
the precision placed on each signal, with salience and control as the framework's separate parts
(HH-ATTENTION-TRUST). No model result licenses their internal psychological
```

### F8a. `READER_HEURISTICS.md`, insert_after

Condition: none (the curator's 07:52 and 10:15 walkthroughs).

Anchor:

```text
drive's reward compression progress is, PLAY's on the analyst's proposal, is in
[`THREE_COGNITIVE_LAYERS.md`](THREE_COGNITIVE_LAYERS.md) §1.
```

Text:

```text
**One scale: how fast things come apart** *(2026-10-17)*:

> I feel like pleasure is also compressing information. It's just rapidly finding an easy path to a
> solution.

> Is beauty just the mix of interesting and pleasurable? Like, it's the rapidly disassembling, but
> it's also the kind of rapidly disassembling that's easy to find. [...] Yeah, I think it is that
> rapid disassembling. Maybe that is what beauty is, the most rapid of disassemblies.

> But with landscapes, does the landscape have opportunity? Is there variance in its offerings, in a
> way that gestures toward order, in a way that can be harnessed and understood? That is what beauty
> is. It's a pretty reasonable guess, honestly. It explains the oddities, like how people can
> describe the sudden appearance of a jaguar as beautiful [...]. Hitting beauty as an artist is more
> difficult, and is also in the eye of the beholder.

*Curator's answers to the analyst's 17 October discussion questions, 2026-10-17 (07:52 PDT), in the project's theory and analyst thread; filed {FILED}. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

> I think it's one scale, how fast things come apart. The beauty is the almost instant resolution;
> that's how I would almost want it. It's the pleasure piece. It's seeing a clear path where you can
> align your active states to a reward channel instantly [...]. There's a pleasure element to it,
> maybe. [...] Regardless, all three of those seem like the same thing to me. It just seems one
> scale.

> Interest is disassembly, and beauty is the rapid disassembly. [...] I actually am not sure I agree
> that what's beautiful is not necessarily interesting. I think my model would be that what's
> beautiful is something that was ever so briefly interesting, just for a second, and then at that
> moment was compressed. At some point it was interesting to you, and now you're seeing a little bit
> more of it, or in a new way, or something like that.

> The candy example is annoyingly good. [...] Perhaps something that's beautiful has to also have a
> total lack of any kind of translation layer, no teaching layer, whether intended to propagandize
> or otherwise. [...] If it is raw and stark in such a way that it has not been formatted for you,
> or for you specifically, but rather it is a natural occurrence of a sufficiently interesting
> thing, or it is the kind of raw, true [thing] that would effectively be a natural occurrence out
> of a human, just the autocomplete, sort of, on its own. A flawless alignment, as everything kind
> of fits into place. Maybe that's beauty. It's a starkness combined with that. Interesting. I'm
> less confident about these as we go.

*Curator's answers to the analyst's 17 October second-round questions and scorecard, 2026-10-17 (10:15 PDT), in the project's theory and analyst thread; filed {FILED}. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

The curator puts beauty, interest and pleasure on one scale, the speed at which a thing comes apart
into an understood structure, with interest the slower process and beauty the near-instant one, and
he rejects the analyst's three-term split for it. The closest findings support his link between
resolution and liking. Having an insight, and its intensity, "predicted subsequent gains in liking"
([Muth & Carbon, 2013](https://doi.org/10.1016/j.actpsy.2013.05.001), read); the affect of an aha
follows "the concomitant surprising fluency gain" of a sudden solution
([Topolinski & Reber, 2010](https://doi.org/10.1177/0963721410388803), read); and valence has been
defined formally as the rate at which free energy falls
([Joffily & Coricelli, 2013](https://doi.org/10.1371/journal.pcbi.1003094), read), a speed. The
nearest formal precedent places the terms the other way round. Schmidhuber puts beauty on
compressibility and interest on its first derivative, the progress
([Schmidhuber, 2009](https://doi.org/10.1007/978-3-642-02565-5_4), read), where the curator puts
beauty on fast progress, and his "ever so briefly interesting, just for a second, and then at that
moment was compressed" is the bridge, beauty as progress completed in a moment.

Two findings resist one scale, and a third fits half of it. Across 900 images beauty tracked
pleasure closely, r = 0.75 ([Brielmann & Pelli, 2019](https://doi.org/10.3389/fpsyg.2019.02420),
read), which fits his pleasure piece; but interest and pleasantness were "essentially unrelated",
and novelty and complexity raised interest while lowering pleasantness
([Turner & Silvia, 2006](https://doi.org/10.1037/1528-3542.6.4.670), read); and beauty from fluency,
as in symmetry and prototypes, has no interest phase to complete
([Reber, Schwarz & Winkielman, 2004](https://doi.org/10.1207/s15327957pspr0804_3), read). His
account fits beauty that arrives as insight better than beauty that arrives as ease, and no study
was found that measures the speed of resolution against beauty, the test the scale implies.

The landscape answer has a home in environmental psychology, whose preference matrix rates scenes on
coherence, legibility, complexity and mystery (Kaplan & Kaplan, 1989, snippet); coherence,
legibility and complexity predicted preference for urban parks in a 2025 study
([Pardela, Beck & Lis, 2025](https://doi.org/10.3097/LO.2025.1133), abstract read), and the
curator's variance that gestures toward order is, on the analyst's reading, complexity held within
coherence. The condition of no translation layer meets Kant, for whom pleasure in beauty "does not
depend on the subject's having a desire for the object" and charm or a governing concept makes the
judgment impure ([Ginsborg, 2022](https://plato.stanford.edu/entries/kant-aesthetics/), read). Two
findings complicate it. Strong sensory pleasure, candy included, can be felt as beautiful
([Brielmann & Pelli, 2017](https://doi.org/10.1016/j.cub.2017.04.018), read), and removing the human
maker lowers ratings, since identical images scored lower when labeled computer-made
([Kirk et al., 2009](https://doi.org/10.1016/j.neuroimage.2008.10.009), read), while understanding
an artist's intent raised liking ([Jucker et al., 2014](https://doi.org/10.2190/EM.32.2.c), read).
The label and title findings favor intent without an ulterior purpose over the absence of intent,
which is close to his raw, true human autocomplete. Sounding Line card D36, commissioned on 17
October as exploratory, tests whether jokes are liked more when their punchlines resolve faster.
```

### F8b. `READER_HEURISTICS.md`, insert_after_line_starting

Condition: none.

Anchor:

```text
| **HH-AESTHETIC-TERMS** |
```

Text:

```text
| **HH-ONE-SCALE** | Beauty, interest and pleasure lie on one scale, how fast a thing comes apart into an understood structure; interest is the disassembly and beauty the rapid one, so the beautiful was briefly interesting and then compressed | **OPEN for beauty as fast resolution; CONTESTED (lit) for one scale joining interest and pleasure.** The curator's account (2026-10-17), against the analyst's three-term split (HH-AESTHETIC-TERMS). Insight and its intensity predict gains in liking, aha affect follows a sudden gain in fluency, and valence can be defined as a rate (lit, READ); interest and pleasantness were unrelated in one series, and fluency-based beauty has no interest phase (lit, READ); no study found measures resolution speed against beauty; Sounding Line card D36 is a first, exploratory test |
| **HH-NO-TRANSLATION** | What is beautiful carries no translation layer, nothing formatted for the viewer or meant to teach or persuade, a natural occurrence or a maker's unforced autocomplete | **OPEN, the curator's tentative proposal.** Kant's disinterested and purpose-free beauty agrees (lit, READ); strong sensory pleasure can be felt as beautiful, removing the human maker lowers ratings, and grasping intent raises liking, so the label and title findings favor intent without an ulterior purpose over no intent (lit, READ); no project measurement |
```

### F8c. `READER_HEURISTICS.md`, replace

Condition: none.

Anchor:

```text
pleasure and interest rated separately to show it (HH-AESTHETIC-TERMS).
```

Text:

```text
pleasure and interest rated separately to show it (HH-AESTHETIC-TERMS). The curator holds the
opposite view, one scale of how fast things come apart, with beauty as interest resolved in a moment
(HH-ONE-SCALE), and he adds tentatively that beauty carries no layer formatted for the viewer
(HH-NO-TRANSLATION); the ratings test would separate the two accounts if it timed the resolution as
well as rating it.
```

### F8d. `READER_HEURISTICS.md`, replace

Condition: none.

Anchor:

```text
reader without an explaining goal forages or shrugs (HH-NO-TOP-GOAL), and for the three-term aesthetic
account (HH-AESTHETIC-TERMS).
```

Text:

```text
reader without an explaining goal forages or shrugs (HH-NO-TOP-GOAL), and for the three-term aesthetic
account (HH-AESTHETIC-TERMS) and the curator's one-scale account with its condition (HH-ONE-SCALE,
HH-NO-TRANSLATION).
```

### F9a. `READER_HEURISTICS.md`, insert_after

Condition: none (the curator's 10:15 walkthrough).

Anchor:

```text
abstract read). A caused mark can still carry no preference information, so the classifier needs
a place for it whatever it is called.
```

Text:

```text
**Pervasive or local: telling an autocompleted branch** *(2026-10-17)*:

> A reader would tell a branch she never saw from one she saw and declined because it would kind of
> suffuse all of the decisions that are similar to it. As characters got into situations, you could
> find the autocomplete yourself. There'd be characters that got into situations that were fearful,
> that would give them the opportunity to be fearful, and you would expect them to be fearful. And
> that would give you the background implication, piece by piece. You'd see it across everything.
> [...] Attention is limited, and so it's the limited nature of attention that helps you here more
> than anything. The biggest thing to tell a branch that has been autocompleted is the pervasiveness
> of similar-looking decisions. Other characters being fearful imply that this character being
> fearful is about the author, not about the character. It wasn't something they were attending to;
> it was something that they do automatically without realizing it.

*Curator's answers to the analyst's 17 October second-round questions and scorecard, 2026-10-17 (10:15 PDT), in the project's theory and analyst thread; filed {FILED}. Contiguous excerpt with a marked omission; transcription repairs listed in the handoff.*

Attribution theory has the instrument the curator describes. Kelley's covariation model reads where
the cause of a behavior sits from three facts, consensus (whether others respond the same way to the
same thing), distinctiveness (whether this person responds that way only to this thing) and
consistency (whether the response recurs whenever the thing is presented), and low consensus, low
distinctiveness and high consistency locate the cause in the person (Kelley, 1973, snippet;
[McArthur, 1972](https://doi.org/10.1037/h0032602), read). Other characters being fearful is low
distinctiveness; the author is the person, and characters, scene types and works are the entities
and occasions. The research pass adds one fact and one correction. The test needs consensus, what
other authors' characters do in matched scenes, or genre conventions pass as authors' traits, and
observers underuse it too, since in McArthur's data consensus explained 6.25 percent of the variance
in person attributions against 21.72 percent for distinctiveness. And covariation locates a cause
and says how general and stable it is, while judgments of control rest on a different fact, the
contingency of one's actions
([Van Overwalle & Heylighen, 1995](https://doi.org/10.1002/ejsp.2420250407), read).

Pervasiveness therefore shows that a choice belongs to the author, not that it was automatic. A
deliberate global policy is pervasive and attended, as Poe claimed of a poem in which no point was
"referrible either to accident or intuition"
([Poe, 1846](https://www.eapoe.org/works/essays/philcomp.htm), read), and the automatic cases the
habit and fear literatures describe can stay local, a habit being a response cued by a stable
context and insensitive to current goals
([Wood & Neal, 2007](https://doi.org/10.1037/0033-295X.114.4.843), read) and a one-shot fear one
that generalizes along similarity to the scene that taught it
([Dymond et al., 2015](https://doi.org/10.1016/j.beth.2014.10.001), read). The analyst's restatement
keeps the curator's test and adds the missing half. An autocompleted branch shows low consensus, low
distinctiveness and high consistency, which places it in the author, and it is insensitive to what
it should track, flat against the character's traits and the threat's size, fast, and seldom
revised. Computational literary studies found author and character signals "fused in novels"
([Bamman, Underwood & Smith, 2014](https://doi.org/10.3115/v1/P14-1035), read), so the separation
does not come free. Sounding Line cards D30 and D31 apply the test to writers' own markers and to
fiction's characters, and Ghost study N14 scores the curator's rule against the restated one where
the mechanisms are known.
```

### F9b. `READER_HEURISTICS.md`, insert_after_line_starting

Condition: none.

Anchor:

```text
| **HH-DIVERGENCE-CLASSES** |
```

Text:

```text
| **HH-PERVASIVENESS** | A branch a maker never draws because it was autocompleted away shows as the pervasiveness of similar decisions across the maker's work, other characters fearful where this one is, so it is about the author; restated, an autocompleted branch shows low consensus, low distinctiveness and high consistency and is also insensitive to what it should track, while pervasiveness alone shows only that the choice is the author's | **OPEN.** The curator's test (2026-10-17) with the analyst's restatement. Kelley's covariation model and its patterns (lit, READ and SNIPPET); observers underuse consensus, and control judgments rest on contingency rather than covariation (lit, READ); deliberate global policies are pervasive and attended, and cue-bound habits and one-shot fears can be local (lit, READ); Sounding Line cards D30 and D31 and Ghost study N14 are commissioned |
```

### F9c. `READER_HEURISTICS.md`, replace

Condition: none.

Anchor:

```text
unexplained variation or the reader's own errors (HH-DIVERGENCE-CLASSES). Confidence: the partition is one bad test
```

Text:

```text
unexplained variation or the reader's own errors (HH-DIVERGENCE-CLASSES). The curator's
pervasiveness test supplies a classifier for the habit class, valid for where a choice sits and
needing a second check, insensitivity to what the choice should track, before it can call the choice
automatic (HH-PERVASIVENESS). Confidence: the partition is one bad test
```

### F9d. `READER_HEURISTICS.md`, replace

Condition: none.

Anchor:

```text
home field; the remaining rows, the divergence classes included, are untested.
```

Text:

```text
home field; the remaining rows, the divergence classes and the pervasiveness test included, are
untested.
```

### F10a. `DECISION_TRACES.md`, insert_after

Condition: none (the curator's 06:21, 07:52 and 10:15 walkthroughs).

Anchor:

```text
difficulty, fatigue, constraints, and editing practice remain rivals. The distinction is
an analyst formulation of the example, not a validated sequence of learning stages.
```

Text:

```text
**Two accounts of one purpose** *(2026-10-17)*:

> I want to note that stated purpose is not actually 100%, because you are relying on the creator's
> self-model of their own motivation.

*Curator's walkthrough of the analyst's 17 October theory pass, 2026-10-17 (06:21 PDT), in the project's theory and analyst thread; filed {FILED}. Contiguous excerpt; transcription repairs listed in the handoff.*

> The artist can tell you what she was attending to. She can tell you what her higher-order goal was
> that she was trying to realign with. The problem was, as she was doing it, bits of her expertise
> were filling in without her. They were putting the post-its on the board without her knowledge,
> which is how expertise works. It fills out the rest of the puzzle for you rapidly.

> Strictly speaking, afterwards, when she looks at it, she can give you two things. She can give you
> what she was trying to do as she did it, her stated goal, and she can also go back and read it and
> come away with the impression of, like, huh, I guess I was trying to do this too, and I had no
> idea. So you can get both, actually. She can report it in both ways, and actually she has to
> reconcile that in her own head. That's part of why I think Death of the Author is interesting,
> because [authors'] own opinion can change over time, and that kind of creates the impression of
> mysticism, when it's actually two separate opinions. Also, memory makes this kind of ugly [...].
> You might misremember and think that you were intending to do things that you weren't. So really,
> you'd better record that immediately, as you're doing it.

> It doesn't surprise me that people defend choices they never made. We have this habit of owning
> all of our expertise. [...] So if you convince someone that their brain autocompleted a decision,
> that is their decision, and they know that, and so they feel themselves in it, especially if they
> can still find a reason to agree with it.

> You can put, for example, at the very top of the pyramid, I want to make a Dungeon Crawler Carl
> book. And as you're doing it, you decide to make distracting metaphors. So you let your brain just
> kind of fill it in with the things that distract you, and so you have a bunch of feet references.
> But then you have too many of them, and you realize that that expertise mapping has been going on.
> So you notice, for example, that there's a break in the inference between the expertise that was
> solving the problem in the bottom side of your inference panel automatically and the chain that
> leads it up to the top, which was your stated goal. And actually, as a result, it does even ever
> so slightly change the implied stated goal, if someone else were to read it. And you don't like
> that break. And so you go and you remove half the references to feet, for example, because you
> want to make sure that that chain is there. But in doing so, you break some local references. And
> now you have to go do a bunch of edits to make sure that things make sense, and you have to
> manually, basically, replace the block that was put in for you by your expertise with your own
> attention. That's why editing makes things so messy.

*Curator's answers to the analyst's 17 October discussion questions, 2026-10-17 (07:52 PDT), in the project's theory and analyst thread; filed {FILED}. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

The two accounts have separate literatures. The account given in the moment is closest to what was
attended, and verbal reports are accurate for information the person was attending to, while asking
for what was never attended forces people "to infer rather than remember"
([Ericsson & Simon, 1980](https://doi.org/10.1037/0033-295X.87.3.215), read), which is his advice to
record the purpose at once. The account given on rereading is inference from one's own work. People
infer their attitudes from their own behavior much as an observer would (Bem, 1972, snippet); they
feel they willed an act when a matching thought came just before it, whether or not the thought
caused it ([Wegner & Wheatley, 1999](https://philarchive.org/rec/WEGAMC), snippet); and in choice
blindness people handed a choice they had not made often failed to notice and gave reasons for it
([Johansson et al., 2005](https://pubmed.ncbi.nlm.nih.gov/16210542/), snippet), his owning of an
autocompleted decision. Literary theory reached the reader's half first, holding that "the design or
intention of the author is neither available nor desirable as a standard" for judging the work
([Wimsatt & Beardsley, 1946](https://pages.mtu.edu/~rlstrick/rsvtxt/wimsatt.htm), read); on the
curator's reading Death of the Author is one maker reconciling two accounts, the later of which is
one more reading.

For the triple inference this keeps stated purpose as evidence filtered through the maker's
self-model, never as ground truth, the restriction §6 of
[`THE_TRIPLE_INFERENCE.md`](THE_TRIPLE_INFERENCE.md) already places on self-report of values. His
editing example adds a mechanism to the ruling on two makers above. Expertise fills blocks without
the maker's attention, a break in the chain from those blocks to the stated goal is what the maker
notices, and the repair replaces an expertise-made block with attended choices, breaking local
references on the way, which, on the analyst's reading, predicts that edits arrive in clusters after
a removal.

**Pauses in boxes, and words that carry information** *(2026-10-17)*:

> My fingers are going to move in a rather similar cadence to my internal speech, assuming I can
> keep up with them, and they basically never can keep up with my internal speech, which makes me
> wonder if some of the noise is going to be that kind of physical stumbling. [...] It might
> indicate that she saw a dependency that she's checking. She's checking something to make sure it
> lines up properly. Maybe [it's] your phonological loop; maybe you're looking at it as it's being
> generated. And if it kicks up something bad, you have to stop and regenerate. [...] It might also
> be an indicator of a difficult choice. For example, there's a Sophie's Choice situation, where the
> decision you're making has large knock-on ramifications. [...] The idea that you have an internal
> generator and you're checking is not one I'm actually quite confident on.

> I'm trying to imagine how we could get more textured information, like word ordering, or some kind
> of word-choice mechanism, grabbing the words that are higher-information and treating that as
> maybe the higher-information words, or the higher-information sentences, indicate more attention.
> [...] If you're attending to the content, you would have more information.

*Curator's answers to the analyst's 17 October discussion questions, 2026-10-17 (07:52 PDT), in the project's theory and analyst thread; filed {FILED}. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

> I agree, the pause is a mixed signal. Though I do think you'd have different boxes in terms of how
> long those pauses tend to take. It'd still be messy.

*Curator's answers to the analyst's 17 October second-round questions and scorecard, 2026-10-17 (10:15 PDT), in the project's theory and analyst thread; filed {FILED}. Contiguous excerpt; transcription repairs listed in the handoff.*

Writing research measures his boxes. Pause durations are fit as mixtures of lognormal distributions,
read as transcription pauses beside a "more involved cognitive process"
([Almond et al., 2012](https://doi.org/10.1002/j.2333-8504.2012.tb02305.x), read), and between words
three components appear, which their authors read as lexical, supra-lexical and reflective
processing, with two components elsewhere
([Hall, Baaijen & Galbraith, 2022](https://doi.org/10.1007/s11145-022-10284-4), read). Per-student
lognormal parameters held across prompts in one study
([Guo et al., 2018](https://doi.org/10.1111/jedm.12172), read), but whether the reflective
components are a writer's own across sessions is untested, and in one 2026 study most keystroke
timing features were unstable as individual traits (Babalola et al., 2026, snippet). His candidate
causes are motor stumbling, the check of a dependency, regeneration after a failed check, and hard
choices; on the analyst's reading they map onto the boxes only loosely, stumbling onto the shortest,
checking and regeneration onto the middle, and hard choices onto the longest, since choices between
near-equal options are slow ([`READER_HEURISTICS.md`](READER_HEURISTICS.md) §4). The
higher-information words are surprisal, and the version that would mark attention is surprisal
against the writer's own history rather than the crowd's, the likelihood of a text under the
author's own grammar against a reference population's, which authorship research already computes
([Nini et al., 2026](https://doi.org/10.1057/s41599-025-06340-3), read). No writing study was found
linking language-model surprisal to the pause before a word. Sounding Line cards D17 and D33,
commissioned on 17 October, test the boxes' stability per writer and whether a writer pauses longer
before words her own history did not predict; the second is the analyst's narrower version of a
question the curator judged untestable at 10:15, whether surprisal shows how devoted a writer is.
```

### F10b. `DECISION_TRACES.md`, insert_after_line_starting

Condition: none.

Anchor:

```text
| **D-ACCEPT-EXPERTISE** |
```

Text:

```text
| **D-SELF-MODEL** | A maker's stated purpose is evidence filtered through the maker's self-model of their own motivation; stated in the moment it reports what was attended, read back later it is an inference from the work, and the maker reconciles the two accounts, with memory moving the later one | **OPEN.** Reports are accurate for attended information and inferred otherwise; people infer their attitudes from their own behavior, feel they willed acts their thoughts merely preceded, and give reasons for choices they did not make (lit, READ and SNIPPET); the intentional fallacy is the reader's side of the same split (lit, READ); no project measurement |
| **D-EDIT-REPLACES** | Editing replaces blocks that expertise filled in without attention with attended choices, where the maker notices a break in the chain from those blocks to the stated goal; the repair breaks local references, so edits cluster after a removal | **OPEN, logic only.** The curator's account (2026-10-17), refining D-EDIT-GUARD; experienced writers revise for meaning and structure (lit, READ, filed in [`READER_HEURISTICS.md`](READER_HEURISTICS.md) §4); Sounding Line's corrections cards D4, D22 and D35 are commissioned |
| **D-PAUSE-BOXES** | Pauses in writing mix several causes, motor stumbling behind inner speech, the check of a dependency, regeneration after a failed check, and hard choices with large consequences, and they fall into distinct duration boxes, with how a writer's pauses divide among the boxes a candidate trait | **OPEN.** Pause durations fit lognormal mixtures with three between-word components, and per-student parameters held across prompts in one study (lit, READ); the stability of a writer's reflective components across sessions is untested, and most keystroke timing features are unstable as traits (lit, SNIPPET); Sounding Line card D17 is commissioned |
| **D-OWN-SURPRISE** | Words that carry more information against the writer's own history than against the crowd's mark attended choices, so they should be preceded by longer pauses beyond the crowd's surprisal | **OPEN.** Likelihood ratios of a text under an author's own grammar against a population's are used in authorship verification (lit, READ); no writing study linking language-model surprisal to the pause before a word was found; at 10:15 the curator judged the related question, whether surprisal shows how devoted a writer is, untestable; Sounding Line card D33 is the analyst's narrower attempt |
```

### F10c. `DECISION_TRACES.md`, replace

Condition: none.

Anchor:

```text
(D-ACCEPT-EXPERTISE). Their status is untested, logic only.
```

Text:

```text
(D-ACCEPT-EXPERTISE). Their status is untested, logic only. A stated purpose passes through the
maker's self-model and comes in two accounts, the moment's and the rereading's (D-SELF-MODEL); editing
replaces blocks expertise filled with attended choices where the chain to the goal breaks
(D-EDIT-REPLACES); pauses mix causes in duration boxes (D-PAUSE-BOXES); and words surprising against
the writer's own history should mark attention (D-OWN-SURPRISE). Their status is untested, logic only.
```

### F10d. `DECISION_TRACES.md`, replace

Condition: none.

Anchor:

```text
instrument-dead; the collapse and floor decomposition stand as before; expertise reuse and the
two-maker rows are untested, logic only.
```

Text:

```text
instrument-dead; the collapse and floor decomposition stand as before; expertise reuse, the
two-maker rows and the purpose, editing, pause and surprise rows are untested, logic only.
```

### F11. `README.md`, insert_after

Condition: none.

Anchor:

```text
## Approved wording and source history
```

Text:

```text
The October 17 curator errata is applied across four theory files and this README. Its
[original text, quotations and repair ledger](../design/archive/SOUNDING_LINE_THEORY_ERRATA_2026-10-17.md)
and [application receipt](../design/archive/THEORY_ERRATA_20261017_APPLIED.json) preserve the exact
source, anchor checks, stable identifiers and before/after hashes. It files the curator's three
walkthroughs of that day. The triple inference is held as one joint inference with three entries,
function, person and process (G198); a value is a decision the maker still endorses (G199);
deliberate processing builds automatic routines, and one-shot aversive experience acts as broad
expertise (G200, G201); language models may lack the corrector, on his hedged reading (G202); goals
emerge, overlay and are topped by the last pass; attention allocates trust; aesthetics is one scale
of resolution speed on the curator's account; and pervasiveness locates a choice in its maker, with
automaticity a separate check. The curator asked that the files use the research literature's own
terms and teach them in place. His quotations keep System 1 and System 2, and the prose uses Type 1
and Type 2 processing, the current terms. Every position filed is OPEN. Ghost V23 results, N4b and
N4c included, are not imported by this errata and await curator uptake.
```
