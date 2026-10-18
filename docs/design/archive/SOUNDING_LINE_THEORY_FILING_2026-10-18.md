# Theory filing brief, 18 October walkthrough

*Spec sheet for the Sounding Line agent. File these positions at the 18 October 20:00 digest. Follow the theory format rules in `docs/theory/README.md`, run `tools/theory_lint.py`, and assign the next free identifiers.*

## How to apply

- **Source.** The curator's spoken walkthrough of 18 October 2026, about 09:15 PDT, answering the twelve questions in the analyst's `THEORY_QUESTIONS_2026-10-18.md`. File each quote with that date and source.
- **Quotes.** Use the excerpts below as written. Lexical repairs are marked in square brackets and listed under each item; keep that list in the handoff. Don't polish further. If lint forces a change inside a quote, report it.
- **Placement.** Place each block at the end of the named section, before the next heading, unless an existing row is named for a timeline line.
- **Rows.** Add each hypothesis row with the status and scope shown. Cite FINDINGS entries by their identifiers, for example the PMAP entry for PMAP. Revisit the afterword paragraph under every table you touch, in the same edit.
- **Literature.** The literature terms come from the analyst's research pass. Each gets one short sentence and a link. Mark it READ or SNIPPET by what you can open.
- **Fixed points.** Keep "preferences are set points" and the Panksepp vocabulary exactly as the theory docs already use them.

## 1. Fluency is communal; the variation is hers

**Target.** `READER_HEURISTICS.md` §6 (Distinguishing choice from constraint).

**His words.**
> priming is just as messy as expertise [...] recursive, collective, shared neural [weighting]

> fluency is communal, and the variation of that fluency is hers [...] if you pull out culture, it would remain

> you give wider error bars around what culture drives you to do, and then deviations are seen as more indicative

> hearing other words over time counts as practice [...] built-in expertise from culture, there's a cultural net there

Repair: "neural waiting" → "neural [weighting]".

**What it says.**
- Fast, fluent production draws on a communal store that hearing and reading train. A writer's own signal is her deviation from it.
- **"Hearing counts as practice" has support.**
  - Structural primes a speaker only heard persisted as strongly as ones she produced ([Bock et al. 2007](https://doi.org/10.1016/j.cognition.2006.07.003)).
  - With matched materials, comprehension and production priming did not differ ([Tooley & Bock 2014](https://doi.org/10.1016/j.cognition.2014.04.002)).
  - Saying a word and hearing it shortened its later production about equally ([Kahn & Arnold 2015](https://doi.org/10.1080/01690965.2013.848989)).
  - No own-against-other test on typed-word latency was found, so D33's shared effect is a new data point, and one this literature predicts.
- Culture works as a strong situation, so behaviour that departs from what the culture prescribes is more diagnostic of the person.
- **The literature's names:**
  - **Correspondent inference** ([Jones & Davis 1965](https://doi.org/10.1016/S0065-2601%2808%2960107-0)). Out-of-role self-presentations produced stronger trait inferences ([Jones, Davis & Gergen 1961](https://doi.org/10.1037/h0048514)).
  - Kelley's **discounting** and **augmentation** ([Kelley 1973](https://doi.org/10.1037/h0034225)). Culture-driven phrasing is discounted. Phrasing that persists against the culture's pull is augmented, and that is the informative event in his Marx example.
  - **Situational strength** ([Mischel 1977](https://archive.org/details/personalityatcro0000unse); [Meyer, Dalal & Hermida 2010](https://doi.org/10.1177/0149206309349309)).
  - **Cultural tightness** ([Gelfand et al. 2011](https://doi.org/10.1126/science.1197754)). [Uz 2015](https://doi.org/10.1177/0022022114563611) indexes it as low cross-person spread of behaviour, which is literally his "error bars".
- **The caution.** Observers under-discount: they still read an assigned essay as the writer's opinion. That is correspondence bias ([Gilbert & Malone 1995](https://doi.org/10.1037/0033-2909.117.1.21)), and it is the failure the engine must avoid.

**Rows:**
- **Communal fluency.** Words that earlier writing in the same interface predicts come faster, and the history may not need to be her own.
  - OPEN (test), human process record.
  - D33's own-history coefficient is 0.047 [0.033, 0.060].
  - A history pooled from shuffled writers predicts about as well, but on different support (unpaired). One other writer's equal-sized history gave 0.019 [−0.012, 0.051], marginal.
  - Personal specificity is not shown. Communality is not yet shown either.
  - D33.fake (same rows) and the supported match decide.
  - The D33 supported-match comparison is pending.
- **Personal variation.** The writer's own production is identifiable beyond what writers share.
  - SUPPORTED (test), human process record:
    - PMAP style identifies 47% of 45 writers against 0.7% for fake writers;
    - rhythm identifies 98%, with a device caveat.
- **Out-of-role diagnosticity.** Departures from culturally prescribed wording are more diagnostic of the person than conforming wording.
  - OPEN (lit support; no test yet).

## 2. The lean, competence and the pyramid

**Target.** `THE_TRIPLE_INFERENCE.md` §4 (Drives, values, and goals) for the pyramid and naming. `READER_HEURISTICS.md` §9 (Baselines and admissibility) for competence as the baseline. `DECISION_TRACES.md` §6 (Controlled change) for edit direction.

**His words.**
> competence is something we just optimize for. And so base rates are really your best attempt at competence [...] everyone's doing the same signal detection [...] how sensitive are you in detection

> [a divergence from competence] would indicate a larger preference

> Goals on goals on goals [...] terminal units of one's value function

> If someone corrected something in order to align with a higher order value, at the expense of a lower order value, that would be meaningful [...] the direction of the edits would be the key

> I do want to make sure that preferences are set points

> Temperament I would translate into just being a habit [...] A threshold would be more like a predisposition or personality

Repair: "[a divergence from competence]" supplies the subject he referred back to ("kindness tugging" against competence).

**What it says.
- **The competent baseline.** Every maker runs the same signal detection; base rates are the competent baseline.
  - A person's sensitivity (**d′**) is competence; her **criterion** is her lean.
  - The best criterion is β_opt = [P(noise)/P(signal)] × [(U_CR − U_FA)/(U_H − U_M)], so it depends on her own d′, the base rates and the payoffs ([Green & Swets 1966](https://archive.org/details/signaldetectiont0000gree); [Lynn & Barrett 2014](https://doi.org/10.1177/0956797614541991)).
  - Preference is the residual: her criterion minus that optimum. It can only be read when base rates and payoffs both vary.
- **Two cautions:**
  - **Accuracy isn't optimality.** Payoff-driven liberal responders were less accurate yet earned more (Lynn & Barrett 2014). People stay conservative under unequal payoffs, as if accuracy itself paid ([Maddox 2002](https://doi.org/10.1901/jeab.2002.78-567)).
  - **A shifted criterion is not uniquely decomposable** into belief, payoff and low sensitivity without normative assumptions ([Armstrong & Mindermann 2018](https://arxiv.org/abs/1712.05812)).
- **The pyramid** is a goal hierarchy.
  - **Its control-theory form is perceptual control theory:** "behavior is the control of input", and each level's output is a reference level, a set point, for the level below ([Powers 1973](https://doi.org/10.1126/science.179.4071.351); [Carver & Scheier 1982](https://doi.org/10.1037/0033-2909.92.1.111)).
  - **Goal systems theory names its edges:** **equifinality** (many means, one goal) and **multifinality** (one means, several goals) ([Kruglanski et al. 2002](https://doi.org/10.1016/S0065-2601%2802%2980008-9)).
  - **Its top** is Rokeach's **terminal values**, though his split of terminal from instrumental values did not hold up in later cross-cultural data.
- **The name he asked for:**
  - **personal striving** for the recurring unit, "what a person is characteristically trying to do" ([Emmons 1986](https://doi.org/10.1037/0022-3514.51.5.1058));
  - **means** for the single act that serves it;
  - **option** for the formal object, an action with its own policy that terminates when the set point is reached ([Sutton, Precup & Singh 1999](https://doi.org/10.1016/S0004-3702%2899%2900052-1)).
- **Edit direction.** An edit that sacrifices a lower-order goal for a higher one is a revealed ordering of the hierarchy. Observers already read value from what an agent pays: the **naive utility calculus** ([Jara-Ettinger et al. 2016](https://doi.org/10.1016/j.tics.2016.05.011)).
  - **Caution: counterfinality.** The more a means harms another goal, the more effective it looks for its own ([Schumpe et al. 2018](https://doi.org/10.3389/fpsyg.2018.01052)). So a costly edit may signal believed effectiveness rather than rank.

**Rows:**
- **Stable acceptance lean.** A writer's acceptance rate is stable across sessions.
  - SUPPORTED (test, descriptive), human process record:
    - V3 acceptance ICC 0.093 per decision, shuffle near 0;
    - acceptance split-half reliability 0.78 [0.59, 0.90] (D12's canonical rerun).
  - V5.d's lean component (0.029) has an invalid fake-writer control, and licenses no person-specific reading.
- **Lean as a signal-detection criterion.** OPEN: SDT1 and Ghost N17. Whether the lean is a belief or a price is part of the same question.
- **Competence as baseline.** Departures from a competent criterion indicate preference.
  - OPEN (lit, untested).
- **Sacrifice direction.** The direction of repeated edits that sacrifice one goal for another orders the goal hierarchy.
  - Constructed: SUPPORTED (sim), Ghost N4d. Conflict probes gain 0.10 to 0.99 nats with visible stakes; an exact alias holds at zero probes.
  - Human: OPEN.
- **Temperament as habit; threshold as predisposition.**
  - OPEN, logic only.

## 3. A person plus a mood

**Target.** `THE_TRIPLE_INFERENCE.md` §6 (Value blindness, and where longitudinal ground truth could come from).

**His words.**
> at an individual painting, what you're getting is not just a person, but a mood

> A mood is [...] a mix of particular drive states.

> Everything becomes habit. The expertise is the attentional part.

> How are we differentiating previous habit from previous expertise?

> We're using previous deviations from patterns to inform the definition of attention. But those deviations themselves become patterns.

> the more calories are spent, the more likely it is that attention was involved [...] the constituent cost is what matters

**What it says.**
- **State against trait.** One work shows a state over a trait. Separating them needs a time model of the person. Three supply it:
  - **whole trait theory:** a trait is the density distribution of momentary states ([Fleeson 2001](https://doi.org/10.1037/0022-3514.80.6.1011));
  - **latent state-trait theory** ([Steyer, Schmitt & Eid 1999](https://doi.org/10.1002/%28SICI%291099-0984%28199909/10%2913:5%3C389::AID-PER361%3E3.0.CO;2-A));
  - **contextual inference** ([Heald, Lengyel & Wolpert 2021](https://doi.org/10.1038/s41586-021-04129-3)).
  
  His set points have a time-series form in **DynAffect**: a personal home base, variability around it, and an attractor strength pulling back ([Kuppens, Oravecz & Tuerlinckx 2010](https://doi.org/10.1037/a0020962)). "A mood is a mix of drive states" fits the finding that momentary mood tracks recent prediction errors ([Rutledge et al. 2014](https://doi.org/10.1073/pnas.1407535111)).
- **Deviations that become patterns.** This is learning-rate control. Bayesian surprise decays by itself as a recurring deviation is absorbed ([Itti & Baldi 2009](https://doi.org/10.1016/j.visres.2008.09.007)), and how fast it is absorbed should follow volatility ([Behrens et al. 2007](https://doi.org/10.1038/nn1954)). A deviation becomes a pattern either by updating the old model or by opening a new latent cause.
- **Habit against expertise is now the named open problem.**
  - **The tests.** The literature's test is **outcome devaluation** or **contingency degradation**: goal-directed responding drops when its outcome loses value; habit persists ([Adams & Dickinson 1981](https://doi.org/10.1080/14640748108400816)). Human overtraining habits mostly fail to replicate ([de Wit et al. 2018](https://doi.org/10.1037/xge0000402)). The strongest human test uses time: old responses resurface when people must answer within about 300 to 600 ms ([Hardwick et al. 2019](https://doi.org/10.1038/s41562-019-0725-0)).
  - **"Expertise is the attentional part" is half supported.** Ericsson names avoiding "the arrested development associated with automaticity" as the expert's key challenge ([Ericsson 2006](https://doi.org/10.1017/CBO9780511816796.038)). Deliberate practice can be read as breaking and rebuilding habits ([Du, Krakauer & Haith 2022](https://doi.org/10.1016/j.tics.2022.02.002)). But attending to execution itself hurts experts ([Beilock et al. 2002](https://doi.org/10.1037/1076-898X.8.1.6)), so expert attention sits above execution: on outcomes, anomalies and overriding prepared responses.
- **The calorie proxy is contradicted.**
  - Task-evoked brain energy changes are often under 5% of baseline ([Raichle 2010](https://doi.org/10.1016/j.tics.2010.01.008)).
  - The glucose model of self-control failed, and multi-lab ego-depletion replications found d = 0.04 ([Hagger et al. 2016](https://doi.org/10.1177/1745691616652873)) and d = 0.06 ([Vohs et al. 2021](https://doi.org/10.1177/0956797621989733)).
  - The literature models effort as a computed cost: an **opportunity cost** ([Kurzban et al. 2013](https://doi.org/10.1017/S0140525X12003196)) or the **expected value of control** ([Shenhav, Botvinick & Cohen 2013](https://doi.org/10.1016/j.neuron.2013.07.007)). If his "constituent cost" means the price the control system charges per operation, that is the expected value of control, and he is aligned with the field.
  - Its proxies are time, errors, pupil size and demand avoidance. In writing they are pauses, bursts and revision density.
  - File the idea as "effort as cost" with that correction.

**Rows:**
- **Session state.** Choices agree more within a sitting than across sittings.
  - OPEN (test, descriptive), human process record, V5.d.
  - The within-sitting excess is confined to decisions under a minute apart: 0.546 against a lean expectation of 0.459. Beyond that, same-session agreement equals the lean.
  - This reads as short-range carry-over between neighbouring decisions, not a sitting-long state or mood. The source makes no causal session-boundary claim.
  - A context-specific personal component: null (V5.d).
- **Production state.** Process features are stable across sittings.
  - SUPPORTED (test): D17 slow-pause share, ICC 0.72; D29 stopping length, split-half 0.91; PMAP rhythm reliability, median 0.985.
- **Habit against expertise by context change and by time.**
  - OPEN.
  - ToMpathy's owner probe card asks the audience-change question.
- **Effort as metabolic cost.**
  - CONTESTED (lit).
  - Replace with: effort shows in time and correction cost. OPEN.

## 4. You can only read what you share

**Target.** `READER_HEURISTICS.md` §2 (Finding an entry point).

**His words.**
> empathy does require shared expertise

> as soon as you have some understanding of the other person's base rate, you can start to look for variations in that base rate to identify preference

> you can still reverse engineer from the middle [...] difficult and rare

> we [have] a lot more shared expertise with any AI model than you would with a human

Repair: "we had" → "we [have]", a tense repair; the sentence is about the present.

**What it says.
- **Shared base rates come first.** A reader needs the maker's base rates before deviations mean anything. Language counts as shared expertise.
  - His "base rate, then variations" is Cronbach's split of judgment accuracy into **normative accuracy** (knowing the typical person) and **distinctive accuracy** (knowing this person's departures) ([Cronbach 1955](https://doi.org/10.1037/h0044919); [Biesanz 2010](https://doi.org/10.1080/00273171.2010.519262)).
- **The literature makes shared expertise an amplifier, not a requirement.** In the **perception-action model**, perceiving another's state activates one's own representation of it, so empathy scales with similarity and experience ([Preston & de Waal 2002](https://doi.org/10.1017/S0140525X02000018)).
  - Emotions are recognized across cultures above chance, with an **in-group advantage** that shrinks with exposure ([Elfenbein & Ambady 2002](https://doi.org/10.1037/0033-2909.128.2.203)).
  - Shared motor expertise is a strong case: elite basketball players predicted free throws earlier than equally experienced watchers ([Aglioti et al. 2008](https://doi.org/10.1038/nn.2182)).
- **Two ways in:**
  - **From the top:** assume shared humanity.
  - **From the middle:** read the gesture's sequence in the artifact. Archaeology calls that the **chaîne opératoire** (Leroi-Gourhan).
    - Static traces carry production information: observers recover stroke direction from handwriting, and movements compatible with a painting's brushstrokes run faster ([Taylor, Witt & Grimaldi 2012](https://doi.org/10.1016/j.cognition.2012.06.012)).
    - Recognizing oneself from drawing kinematics depends on velocity information ([Knoblich & Prinz 2001](https://doi.org/10.1037/0096-1523.27.2.456)). That fits "difficult and rare".

**Rows:**
- **Shared coordinates.** A reader detects a maker's taste only in coordinates the reader already has.
  - OPEN.
  - The instrument is blind (V4, V4.c): every fitted reader false-alarms in both coordinate arms; only the oracle sees plants.
  - The descriptive predictive criterion favours the reader's own coordinates: 0.8 against 0.0 (V4.c diagnostics; test, constructed world).
  - Human, by analogy: the in-group advantage (lit).
- **Reading from the middle.**
  - OPEN.

## 5. Novelty, familiarity and processing time

**Target.** `READER_HEURISTICS.md` §4 (Updating and active search).

**His words.**
> indicative of confusion, processing time

> Familiarity often wins the choice [...] because it resolves more quickly, and [vision] moves to wherever surprise is decreasing the fastest

Repair: "[vision]" restores an elided subject.

**Row:**
- **Looked at, not taken.** Out-of-repertoire offers draw more examination without more acceptance.
  - Human process record, D32. The acceptance primary is marginal, and the examination extension's primary is null.
  - The hover figure (declined outside offers hovered 60.2% against 56.3%) is a secondary that ran opposite its prediction. "Declined" depends on the selected-option defect.
  - D32 is held for the selected-option audit; status OPEN until its canonical rerun.

## 6. Habits that get caught

**Target.** `READER_HEURISTICS.md` §7 (Habit, concealment, and revision).

**His words.**
> [the everywhere marks, faster and more revised, are] flow state [...] corrective expertise blocks

> [uncaught habits] fulfill some higher-order goals, so they don't look inefficient

> the thing attention would struggle with more so is misapplied expertise, out-of-context expertise

Repair: bracketed context supplied from the question.

**Rows:**
- **Flow with corrective blocks.** Everywhere marks are produced faster and revised more often than local ones.
  - Human process record, D30: 13.9 against 8.2 characters per second; revised 6.9% against 5.4%.
  - Interpretation: OPEN.
- **Misapplied expertise.** Attention's harder target is misapplied expertise, not habit.
  - OPEN, logic only.

## 7. Corrections that don't stick

**Target.** `DECISION_TRACES.md` §6 (Controlled change).

**His words.**
> far easier to reattach them [than to break them]

> an overlaid habit of fixing things as you do them

> catch the thought [...] stop the follow-up actions [...] eventually never even think about it

Repair: "[than to break them]" supplies the comparison his sentence implied.

**What it says.
- **Correction leaves the old route in place.** Correcting doesn't erase the original. **Extinction is new, context-bound learning,** and the old response can return in a new context; that return is **renewal** ([Bouton 2004](https://doi.org/10.1101/lm.78804)).
- **Reattaching is contested.** Whether pairing the old cue with a new outcome (**counterconditioning**) lasts better than extinction is unsettled:
  - in people, fear expectancy returned less after it ([Kang et al. 2018](https://doi.org/10.1016/j.brat.2018.06.009));
  - in rats, it renewed more ([Holmes, Leung & Westbrook 2016](https://doi.org/10.1101/lm.040659.115)).
- **"Catch the thought" needs one amendment.** The **competing response** of habit reversal works: d = 0.80 across 18 studies ([Bate et al. 2011](https://doi.org/10.1016/j.cpr.2011.03.013)). With planned interception (**implementation intentions**, [Gollwitzer 1999](https://doi.org/10.1037/0003-066X.54.7.493)), "if X, I will do Y instead" helps, while "if X, I will not do Y" backfired and strengthened the habit ([Adriaanse et al. 2011](https://doi.org/10.1177/0146167210390523)).

**Row:**
- **Corrections don't become defaults.**
  - OPEN (test), human process record. Timeline line: D35 came back null, −0.0013 [−0.0031, 0.0004].
  - It fits renewal; it does not test it.

## 8. Fear that looks like expertise

**Target.** `THE_TRIPLE_INFERENCE.md` §7 (Identifiability, not impossibility).

**His words.**
> A reader of minds would need it [...] that is how you place that in context [...] otherwise just noise on noise

> these known problems are going to have to come to grips with one by one

**Row:**
- **Narrow fear against narrow expertise.**
  - Aliased in constructed worlds under every tested probe (sim, Ghost N9).
  - Hypothesis, untested: the maker's other works could break the alias where their widths differ.
  - Human: OPEN.

## 9. Play

**Target.** `READER_HEURISTICS.md` §8 (Communicative shaping: the bard).

**His words.**
> play is a [scaler] [...] rules are relaxed

> Laughter is a way of saying you're getting near the edge, but it's entertaining [...] funny is getting as close to the line as possible and not interacting with it

> Getting in the wrong mode costs.

> play is part of how you express yourself [...] freedom [...] that's why you're able to find the author in fiction more so [...] play is going to be one of the better ways to identify others

Repair: "scaler" kept as spoken; meaning "scaler" or "scalar" is uncertain.

**What it says.**
- **Play is a frame.** It marks behaviour as not literal: **"this is play"** metacommunication ([Bateson 1955](https://pubmed.ncbi.nlm.nih.gov/13297882/)); the canid play bow is that frame made visible ([Bekoff 1995](https://doi.org/10.1163/156853995X00649)).
- **One correction to the wording: stakes relax, not rules.** Play's "relaxed field" (Burghardt 2005) means a fed, safe, unstressed animal, and social play stays closely regulated by signals. "Consequences are suspended" is the established version.
- **Humour.** "Near the line" is **benign violation**: amusement needs something wrong and okay at once ([McGraw & Warren 2010](https://doi.org/10.1177/0956797610376073)). The data show a sweet spot that depends on psychological distance, not a maximum at the line ([McGraw et al. 2012](https://doi.org/10.1177/0956797612443831)). Laughter as a play signal is in [Gervais & Wilson 2005](https://doi.org/10.1086/498281).
- **Why play would show the person.** Play and fiction are weak situations.
  - Traits do show more there, but modestly: r = .09 to .23 for conscientiousness and performance, higher in weak occupations ([Meyer, Dalal & Bonaccio 2009](https://doi.org/10.1002/job.602)).
  - Creative stories revealed openness and agreeableness only ([Kufner et al. 2010](https://doi.org/10.1016/j.jrp.2010.05.003)).
  - No study found compares the same writers' identifiability in fiction and exposition.
  - A missed frame inverts the reading.

**Rows:**
- **Play is a window.** Playful and fictional records identify the maker better per record, once the frame is detected.
  - OPEN. Sounding Line's GEN1 tests the identifiability half on CoAuthor stories against arguments. Ghost N18 computes the detector accuracy needed.
- **Ignoring play misreads preference.** In Ghost N8's constructed worlds, where play reverses expressed preference by construction, ignoring play signals cost up to 2.59 nats of preference log loss.
  - SUPPORTED (sim) as a method result under that stipulation.

## 10. Three entries, and what the third is for

**Target.** `THE_TRIPLE_INFERENCE.md`, the 17 October "One inference, three entries" block (add a timeline line to its row).

**His words.**
> for humans, one inference that needs all three entries. But for AI, because you aren't choosing what to uptake, you don't need the third entry [...] the information of the third entry should fall out [...] it is literally the signal telling you what to trust in a world where your only decision is deciding what to trust

**What it says.**
- A human reader chooses what to take up, so the process entry decides trust.
- A model reader doesn't choose its training uptake, so for it the process entry reduces to a trust signal.

**Row:** OPEN, logic only.

## 11. Trust moves with each mistake

**Target.** `READER_HEURISTICS.md` §4, the HH-ATTENTION-TRUST row (add a timeline line).

**His words.**
> it should move with each mistake. Everything gives evidence. Surprising mistakes are the most notable. Expected mistakes [...] you just fit that into how to use the tool properly

**What it says.** Trust updates per interaction, weighted by surprise. His model fits the trust-dynamics findings closely:
- failures move trust more than successes ([Yang, Schemanske & Searle 2023](https://doi.org/10.1177/00187208211034716));
- a beta-distribution Bayesian update fits trial-by-trial trust ([Guo & Yang 2021](https://doi.org/10.1007/s12369-020-00703-3));
- errors on easy items, the surprising ones, hurt trust most ([Madhavan, Wiegmann & Lacson 2006](https://doi.org/10.1518/001872006777724408));
- "fitting expected mistakes into how to use the tool" is what [Lee & See 2004](https://doi.org/10.1518/hfes.46.1.50_30392) call **functional specificity**, trust differentiated by function.

**Rows:**
- **Checking after a letdown.** OPEN (test). Timeline line: D39 came back null.
- **Narrowed avoidance after model errors.**
  - Positive in 9 writers (D38), now held for the selected-option audit.
  - The matched model-against-own comparison is marginal.

## 12. The person entry reads production

**Target.** `THE_TRIPLE_INFERENCE.md` §1 (The three target families).

**His words.**
> your suggestion's fine

This accepts the analyst's proposal that the person entry should read voice rather than preference.

**Row.** The person shows in production more than in selection.
- SUPPORTED (test), human process record.
- PMAP, identification across separate prompts among 45 writers:
  - rhythm 98%;
  - style 47%;
  - revision 31%;
  - length 20%;
  - handling 16%;
  - content taste near chance, with its control invalid.
- The rhythm-minus-handling contrast is 0.82 [0.71, 0.93], with a clean reassignment control. The style contrast's reassignment control is biased; keep that warning.

## Afterwords to revisit

Revisit the afterword paragraph under every table this brief touches, in the same edit. The cross-file conclusion to carry, in plain words:
- the person shows in how she produces, and that is stable across sittings;
- what she picks among offers shows a lean and little else in this corpus;
- goals and preferences need probes.

Confidence lines must use the fixed vocabulary:
- for the production results, "Confidence: one bad test away.";
- for the probe claims, "Confidence: one bad test away.", with the plain words saying the support is from constructed worlds only.
