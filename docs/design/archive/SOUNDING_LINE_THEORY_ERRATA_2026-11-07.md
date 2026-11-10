# Sounding Line theory errata, 7 November 2026: the curator's answers to the walkthrough

*Supplied with the Stage 15 Week 5 packet. Apply at handoff by the 6 November procedure, with the modes defined at the head of Part D: parse Part D's Anchor/Text fenced-block pairs exactly, apply them to the named files in order, and write a receipt with before and after hashes. Written against `origin/main` at `dcbcc26de`. Blockquotes are the curator's words only, from his audio-transcribed message of Saturday 7 November 2026, 07:02 PST, in the project's theory and analyst thread. The quotes are verbatim; transcription notes sit in the caption under them and in the rows, outside quotation marks.*

## Part A. What changes

1. **Channels.** They fire at graded strength and can fire together. You wondered whether a channel's strength is how well the situation fits its trigger, so that FEAR is as loud as the predicted harm is strong (new row G252).
2. **Stress, FEAR and anxiety.** Stress is caused by uncertainty; in your gun example, uncertainty about what to do. Anxiety is "a light form of fear". Your 4 November "uncertainty leads to things like anxiety" meant stress (new row G253, refining G238).
3. **Set points are never seen.** Only the efforts that restore them are seen, those efforts often overshoot, and enough of them let a reader zero in (G254). Precision sharpens with time near a set point (G255), and a lasting deficit far from it dulls the need (G256). Security is maximized, with value that falls as other needs get louder, and the balance across needs is the control (G257).
4. **DISGUST and SEEKING.** DISGUST may be SEEKING's opposite, with PLAY, LUST and CARE on a loop. This is filed as a hypothesis (G258).
5. **CARE and the word scales.** CARE's top word is about concern, and love may be long-term mutual appreciation (G259). The everyday word scales are a display aid for ToMpathy, not part of the analysis (G260).
6. **Identity in how one decides.** Taking too long means a value is nested in too large a decision tree; not applying a value one understands means it was rejected or nested; and you proposed predicting the trade from everything else known about the person (G261).
7. **Other new rows.**
   - Several motives behind one act, split by a network of associations (G262).
   - Revision as an alignment check against several goals (G263).
   - Laughter as an inference marker (G264).
   - Recursive refinement of old inferences (G265).
8. **Closing and re-checking.**
   - Closing keeps what a source taught, and re-checking only weakens it. RAGE can drive a targeted re-read (HH-CLOSE-KEEPS).
   - Shared inference lets in-groups deceive outsiders (HH-SHARED-INFERENCE).
   - ToMpathy's closed-source state flags nothing (HH-ENGINE-NO-FLAGS).

The literature status in each row comes from three research passes of 7 November. Labels: (lit, READ) for full text, (lit, abstract) for abstract only, and plain words where only metadata, an opening section or a secondary account was seen. This is stricter than the README's READ and SNIPPET and than the 6 November rows, where READ covered abstracts too. Keep the labels as written.

## Part B. Sources

- The curator's words: his message of 2026-11-07, 07:02 PST, verbatim. G253 also quotes two of his turns in the project's theory discussion thread: 3 November, 16:35 PST (turn 4), and 4 November, 12:06 PST (turn 11).
- Literature: the analyst's research notes of 7 November, checked against the sources the same day. Each study is cited in its row, with its read level.

## Part C. Older text changed

The afterwords under the three tables gain sentences for the new rows, and G229, G236, G238 and G241 gain or extend timeline lines. No quote or row text is removed.

## Part D. Exact edits

**Modes.** These replace the 6 November wording, which appended text to the anchor itself.
- `insert_after`: the anchor is one whole line. Insert the Text as new lines directly after that line. F1a's Text begins with a blank line, which separates it from the paragraph above.
- `insert_after_line_starting`: exactly one line starts with the anchor. Insert the Text as new lines directly after that line, with no blank line, so the new rows join the same table.
- `replace`: the anchor is a string that occurs exactly once in the file, possibly inside a longer line. Replace that string with the Text.
- Every anchor must match exactly once at application time; refuse the edit otherwise.
- Replace `{FILED}` with the application date.
- The JSON copy holds the same strings, with no leading line breaks beyond F1a's blank line.

Rows name the Week 5 and Ghost V27 cards that will test them ("Test:", "Tests:"). Keep these pointers as written; the cards themselves are in the packets and TODO.md.

**New identifiers:** G252 to G265; HH-CLOSE-KEEPS, HH-SHARED-INFERENCE and HH-ENGINE-NO-FLAGS. All are unused anywhere in the repository at `dcbcc26de`.

**Then:**
1. Run `tools/theory_lint.py --all`.
2. Archive this file and the receipt as `docs/design/archive/SOUNDING_LINE_THEORY_ERRATA_2026-11-07.md` and `docs/design/archive/THEORY_ERRATA_20261107_APPLIED.json`.
3. Add the curator's 7 November message to `results/readings/PROVENANCE.md` the same day, one row, as the root AGENTS.md requires.

This is a theory filing, not a result landing.

### F1a. `docs/theory/THREE_COGNITIVE_LAYERS.md`, insert_after

Condition: none (the curator's 7 November answers, filed as his words and OPEN rows).

Anchor:

```text
reader's stopping rule in its §5 (HH-CLOSE-MODEL).
```

Text:

```text

**The 7 November answers: graded channels, set points never seen, stress apart from FEAR, closing that keeps** *(2026-11-07)*:

> One, they can all fire, they can fire simultaneously if they need to. Two, they are fired in
> increasing and decreasing amounts. There's like a strength to their application. So you're not
> just applying anger, you're applying like 49% of anger to the solution.

> I do wonder if the amount that they trigger is simply decided upon how well the scenario fits their
> trigger. How strong is the prediction of future harm? Because that is what determines how loud fear
> is, I guess. Which would explain why repeated systematic desensitization makes sense.

> Immediately, fear triggers because there are now futures in which I die. They are much more likely
> just being in the same room as this thing.

> And I would have a lot of stress in this situation because I don't know how to deal with this.
> Like, I don't know, like, Is fighting a good idea? Is running a good idea? Is talking? There's a
> lot of uncertainty, and that would immediately cause a lot of stress as a result.

> Anxiety is a light form of fear, and stress is caused by uncertainty. I think I do want to separate
> those clearly.

> When I said anxiety leads to things like stress, leads to things like anxiety, what I meant was leads
> to things like stress, to be clear.

> you actually would never see where the set point fits, which is actually kind of the whole point,
> and kind of why this works as an alignment solution, because you never actually see the set point,
> you just see when it diverges too far from a comfort space and how much effort people are therefore
> willing to push it back towards the middle.

> People will often overshoot. In fact, they'll do that all the time.

> as you get closer and closer to any individual set point it kind of fractally gets more precise like
> I don't just want to be at 71 degrees I want to be at 71.1 degrees provided I've stayed at exactly 71
> for the last I don't know 100 years

> I think it's the opposite of the effect of what happens to rich people. I think you just get, the
> resolution decreases. It's still there, but it just gets weaker, and it'd have to be extreme stimuli
> to cause some kind of an effect in comparison.

> security is something you try to maximize [...] You do try to maximize that. The problem is its value
> decreases as you get further and other needs get louder.

> deviation from that setpoint, from Margin's setpoint specifically, has to be balanced against the
> other ones. That's the actual control, is that it's being balanced.

> I think disgust might be the opposite of seeking.

> Once you've made an inference, a little piece of it is with you forever. And so yes, even closing it
> still keeps what you learned before.

> rechecking what they told you is a separate and effortful act that you have to do. And even then, all
> you're doing is kind of weakening the associations that you've made now.

*Curator's message answering the analyst's 7 November walkthrough questions, 2026-11-07 (07:02 PST), in the project's theory and analyst thread; filed {FILED}. An audio transcript, quoted verbatim in separate excerpts with a marked omission. The two gun excerpts are his worked example of someone putting a gun on the table. "Margin" is his margin from dissolution, transcribed "margin of distribution" in the same message. "When I said anxiety leads to things like stress, leads to things like anxiety" restates his 4 November "uncertainty leads to things like anxiety". His example for the dulled need is LUST, "the only one that kind of can get totally ignored and cut off".*

The curator now grades each channel, wondering whether its strength is the fit to its trigger, with
FEAR as loud as the predicted harm is strong. He holds that stress is caused by uncertainty, in his
gun-on-the-table example uncertainty about what to do, and separates it from FEAR and from anxiety,
"a light form of fear"; he corrected his 4 November line to name stress, not anxiety. Set points are
never observed: only the restoring efforts are, which overshoot, and precision sharpens with time
near a set point and dulls under a lasting deficit far from it. Security is maximized, with value
falling as other needs grow, and the balance across needs is the control. DISGUST may be
SEEKING's opposite, the other side of a loop of PLAY, LUST and CARE. Closing keeps what a source
taught; re-checking only weakens it. The literature bearing on each sits in the rows below
(G252 to G260) and in [`READER_HEURISTICS.md`](READER_HEURISTICS.md) §5 (HH-CLOSE-KEEPS).
```

### F1b. `docs/theory/THREE_COGNITIVE_LAYERS.md`, insert_after_line_starting

Condition: none (the curator's 7 November answers, filed as his words and OPEN rows).

Anchor:

```text
| **G247** |
```

Text:

```text
| **G252** | Channels fire at graded strength and can fire together; a channel's strength may be the fit of the situation to its trigger, so FEAR is as loud as the predicted harm is strong, with uncertainty layered on top of a prototype trigger (extends G236) | **OPEN.** The curator's account (2026-11-07), the trigger fit offered as a wonder ("I do wonder"). Exposure patients improved when their threat expectancy fell, and surprise alone did not predict outcome (lit, abstract: Pittig et al., 2023); for vivid outcomes such as shocks, choices and willingness to pay were less sensitive to middle probabilities and more to the step from impossible to possible, so possibility rather than probability may set the volume, though felt fear was not measured (lit, abstract: Rottenstreich & Hsee, 2001); exposure may add a competing safety prediction rather than lower the harm prediction (lit, abstract of a review: Craske et al., 2014). Tests: S15-W5 IN1 to IN3 (Crowd-enVENT); Ghost V27 K4 (a constructed-world card whose primary is reported for scale) |
| **G253** | Stress is caused by uncertainty, in his gun example uncertainty about what to do; anxiety is "a light form of fear"; and the curator's 4 November "uncertainty leads to things like anxiety" meant stress (refines G238) | **OPEN.** The curator's account and correction (2026-11-07). Stress tracked irreducible uncertainty about shocks in a task where nothing the person did changed the shocks, which fits his rule and his 3 November "irreducible uncertainty" and adds stress with no decision to make (lit, READ: de Berker et al., 2016); detected control switches off the default passive response to prolonged aversive events, which fits his trained agent, and the paper holds that passivity is the unlearned default rather than a learned certainty that nothing helps (lit, abstract: Maier & Seligman, 2016); in rats, startle boosted by a warning cue and startle boosted by bright light, which the authors call conditioned and unconditioned fear, needed separable structures, the central amygdala and the bed nucleus of the stria terminalis (lit, abstract: Walker & Davis, 1997), and in people an anti-anxiety drug reduced defensive behaviour on approach to a threat but not on departure from it (lit, abstract: Perkins et al., 2009), both against anxiety as a lesser dose of the same FEAR; on the analyst's reading, the tradition behind the second treats anxiety as the conflict of approaching a threat, close to his gun example, which the uncertainty papers call stress; uncertainty as the essence of stress, centred on which strategy to select, about what to do next, is a theory-paper statement of his version (lit, READ: Peters, McEwen & Friston, 2017); the constructed-emotion view denies the shared core he names (lit, READ: Barrett, 2017). Test: Ghost V27 K4 (a constructed-world card whose primary is reported for scale) |
| **G254** | Set points are never seen, only the efforts that restore them, which let a reader zero in on them more and more precisely; restoring efforts often overshoot | **OPEN.** The curator's account (2026-11-07). On one model, offered in a multi-author review as possibly better than a single set point, body fat is defended only at upper and lower boundaries, with weak or no regulation between, so efforts may locate edges rather than a middle (lit, abstract and one section: Speakman et al., 2011), and on the analyst's reading his comfort space is already a band, so the pressure is on its middle; core body temperature is held by separate loops with their own thresholds (lit, abstract: Romanovsky, 2007); plans made hungry overshoot and plans made full undershoot, so overshoot has a mirror (lit, READ: Loewenstein, O'Donoghue & Rabin, 2003); refeeding overshoots body fat (lit, abstract: Dulloo et al., 1997). Tests: S15-W5 CH4 (chess clock reserves); Ghost V27 K3 |
| **G255** | A set point's precision rises with time spent near it: rich people are soft | **OPEN.** The curator's account (2026-11-07). Occupants of air-conditioned buildings respond about twice as strongly per degree as those of naturally ventilated ones, whose acceptable range is about 70% wider (lit, READ: de Dear & Brager, 1998); in one naturally ventilated building, occupants with different degrees of window control responded differently at the same temperatures, clothing and activity, so precision may track control rather than history (lit, abstract: Brager, Paliaga & de Dear, 2004). Test: S15-W5 SP2 |
| **G256** | A lasting unmet need loses resolution, so it takes extreme stimuli to move it | **OPEN.** The curator's account (2026-11-07), with LUST as his example. Deprived neurons raise their own gain (lit, abstract: Turrigiano et al., 1998), and in visual cortex deprived of one eye, firing fell for two days, which fits, then returned to its set point two to three days later with the eye still closed (lit, abstract: Hengen et al., 2013); ten of thirteen blindfolded volunteers hallucinated within 96 hours (lit, abstract: Merabet et al., 2004); semi-starvation made food a preoccupation while sex drive fell (lit, a secondary account of the Minnesota experiment; Keys et al., 1950, not read); lonelier people showed weaker reward responses to pleasant pictures of people and stronger visual responses to unpleasant ones, in cross-sectional data (lit, abstract: Cacioppo et al., 2009); a search cut short found no well-designed study of desire after long abstinence. His rule is consistent, time near a set point sharpening it and a long deficit far from it dulling it, but on the analyst's reading the standard accounts of adaptation, efficient coding and homeostatic gain, do not use distance from a set point, and both predict sharper sensitivity after a long deficit; with a weak, noisy input efficient coding trades fine detail for sensitivity (lit, abstract: Atick & Redlich, 1990), which could keep the lost resolution but not the need for extreme stimuli. What reads distance from a set point is open. Tests: S15-W5 SP3; Ghost V27 K3 |
| **G257** | Security is maximized, its value falling as other needs get louder, and the balance across needs is the control (refines G241) | **OPEN.** The curator's account (2026-11-07), answering whether security is a defended set point or a plain preference for more; the substance matches his 3 November account (G241). A falling value and a defended set point both predict less risk-taking the further behind one is; S15-W5 MD3 (TD3) reports, beside its primary, the slope below zero minus the slope above it, where a positive contrast, risk-taking falling faster with each point behind than it rises with each point ahead, favours a defended set point, a contrast near zero a falling value, and a negative one a rival's pattern (house money if both slopes are positive, break-even if the slope below zero is negative). Test: S15-W5 MD3 |
| **G258** | DISGUST may be SEEKING's opposite, with PLAY, LUST and CARE on a loop | **OPEN, logic only.** The curator's hypothesis (2026-11-07). Panksepp grouped LUST with SEEKING, RAGE and FEAR as ancient systems and CARE, PANIC/GRIEF and PLAY as social ones, a grouping by evolutionary age (lit, READ: Montag & Panksepp, 2017), and did not count DISGUST as a primary system (lit, opening text: Panksepp, 2007), a cost to the channel rather than evidence against the loop; dopamine depletion left disgust reactions essentially unchanged (lit, abstract: Berridge, Venier & Robinson, 1989), and a bitter taste raised dopamine over minutes in the accumbens core and prefrontal cortex but not reliably in the shell (lit, abstract: Bassareo, De Luca & Di Chiara, 2002), while within milliseconds tastes of opposite valence moved accumbens dopamine in opposite directions (lit, abstract: Roitman et al., 2008), so the two are separable and DISGUST's oldest trigger can turn SEEKING up on the slower timescale; disgust sensitivity correlated -0.46 with sensation seeking (lit, abstract: Haidt, McCauley & Rozin, 1994), and a disgust expression narrows the senses where a fear expression widens them (lit, abstract: Susskind et al., 2008), in his favour; curiosity draws people toward aversive outcomes such as shocks (lit, abstract: Hsee & Ruan, 2016), against; looking away from disgusting images persisted over 24 exposures (lit, abstract: Dalmaijer et al., 2021), in his favour |
| **G259** | CARE's top word is about concern; love may be long-term mutual appreciation, his "current best guess", offered instead of "a sort of recursive updating that involves care and requires care" | **OPEN.** The curator's account (2026-11-07), refining G229, with his "top four" read as "top word". In photo-viewing scans, romantic and maternal love deactivated a common set of regions associated with negative emotion, social judgment and mentalizing (lit, abstract: Bartels & Zeki, 2004); long-term intense love engaged the ventral tegmental area and dorsal striatum, SEEKING's dopamine circuit, with attachment regions, and the paper names no region as mentalizing, though the angular gyrus, part of the temporo-parietal junction, appeared against a close friend (lit, READ: Acevedo et al., 2012); the percentage he half-remembered is from a survey: 40% of a US random sample and 29% of a New York sample married over ten years reported being very intensely in love (lit, abstract: O'Leary et al., 2012); parents watching their own infants engaged a caregiving network that includes mentalizing regions (lit, abstract: Abraham et al., 2014), and a partner's name flashed below awareness recruited regions for representing self and others (lit, abstract: Ortigue et al., 2007), so, on the analyst's reading, whether love uses mentalizing may depend on the task |
| **G260** | The everyday word scales are a display aid for ToMpathy, not part of the analysis (refines G236) | **OPEN, adopted as the working position.** The curator (2026-11-07): "Word scales are barely even a working tool", meant as "a visual indicator when someone highlighted over that particular drive". The word-norm and substitution results constrain that display, not the channels (S15-TD4-C2, S15-TD5-C2) |
```

### F1c. `docs/theory/THREE_COGNITIVE_LAYERS.md`, insert_after_line_starting

Condition: none (the curator's 7 November answers, filed as his words and OPEN rows).

Anchor:

```text
| **G229** |
```

Text:

```text
|   | | *(2026-11-07: the curator puts concern at the top of CARE's word scale and proposes love as long-term mutual appreciation, his current best guess; see G259)* |
```

### F1d. `docs/theory/THREE_COGNITIVE_LAYERS.md`, insert_after_line_starting

Condition: none (the curator's 7 November answers, filed as his words and OPEN rows).

Anchor:

```text
| **G236** |
```

Text:

```text
|   | | *(2026-11-07: the curator calls the word scales a display aid for ToMpathy rather than part of the analysis; see G260)* |
```

### F1e. `docs/theory/THREE_COGNITIVE_LAYERS.md`, insert_after_line_starting

Condition: none (the curator's 7 November answers, filed as his words and OPEN rows).

Anchor:

```text
| **G238** |
```

Text:

```text
|   | | *(2026-11-07: the curator says stress is caused by uncertainty, illustrated by not knowing what to do in his gun example, calls anxiety "a light form of fear", and says his 4 November "uncertainty leads to things like anxiety" meant stress; see G253)* |
```

### F1f. `docs/theory/THREE_COGNITIVE_LAYERS.md`, replace

Condition: none (the curator's 7 November answers, filed as his words and OPEN rows).

Anchor:

```text
on 4 November he called it a set point and named it security)* |
```

Text:

```text
on 4 November he called it a set point and named it security; 2026-11-07: he holds security as maximized, its value falling as other needs get louder, balanced against the other set points; see G257)* |
```

### F1g. `docs/theory/THREE_COGNITIVE_LAYERS.md`, replace

Condition: none (the curator's 7 November answers, filed as his words and OPEN rows).

Anchor:

```text
Confidence: one bad test away for the word-norm comparison; untested, logic only for the channel mechanisms.
```

Text:

```text
A channel's strength as the fit of the situation to its trigger has support in exposure therapy, where outcomes followed falling threat expectancy, and a rival in possibility outweighing probability for vivid harms (G252). Stress as caused by uncertainty fits the measured link between stress and irreducible uncertainty, while anxiety as a light FEAR meets evidence that the two come apart (G253). Set points read only from the efforts that restore them may give the edges of a zone rather than its middle, and those efforts err on both sides of it (G254). Precision that sharpens near a set point (G255) and dulls under a lasting deficit far from it (G256) needs, on the analyst's reading, a mechanism that reads distance from the set point, which the standard accounts of adaptation lack. Security is maximized against the balance of needs (G257); DISGUST as SEEKING's opposite meets evidence that the two are separable (G258); love as long-term mutual appreciation meets a signature of SEEKING and attachment (G259); and the word scales are a display aid, not a measure (G260). Confidence: one bad test away for the word-norm comparison; untested, logic only for the channel mechanisms and the set-point dynamics.
```

### F2a. `docs/theory/THE_TRIPLE_INFERENCE.md`, insert_after_line_starting

Condition: none (the curator's 7 November answers, filed as his words and OPEN rows).

Anchor:

```text
| **S15-TD-B2-C5** |
```

Text:

```text
| **G261** | Identity shows in how one decides: taking too long means the value is nested "at too large of an inference" ("Your decision tree should be smaller"), not applying a value one understands means it was rejected or nested, and a model of the person predicts the trade ("can we predict a trade-off given everything else we know about the person?") | **OPEN.** The curator's account (2026-11-07). Slow deliberation over a taboo trade, a child's life against money, drew more outrage, with slowness described as difficulty, and the outcome mattered more than the timing (lit, READ: Tetlock et al., 2000, Experiment 2); speed amplifies what an act signals about certainty, and a slow refusal to save a child was judged better than a quick one (lit, READ: Critcher, Inbar & Pizarro, 2013); observers credit struggle (lit, abstract: Starmans & Bloom, 2016; lit, READ: Everett, Pizarro & Crockett, 2016), reading slowness as a value in conflict rather than one rejected; observers' inferences from a choice and its timing matched a model that runs choice timing backward to estimate preference strength, in favour of the timing half of the predictive trade-off, while the person-specific half did not come out reliably (lit, READ: Gates et al., 2021); more thought lowered a person's influence when the decision was easy and raised it when it was hard (lit, READ: Kupor et al., 2014); deciders change their timing when watched (lit, READ: Konovalov & Krajbich, 2023). Test: Ghost V27 K1 (a constructed-world card whose primary is reported for scale) |
| **G262** | One act can serve several motives at once, split by a network built on association ("anything that can be associated will"), with loops where inputs become outputs | **OPEN.** The curator's account (2026-11-07). Explaining away is the computation, done on graphs by belief propagation, whose fixed points on loopy graphs are stationary points of a Bethe free energy (lit, abstract: Yedidia, Freeman & Weiss, 2005); on a diagnosis network with many rare causes per finding, loopy propagation oscillated with "no obvious relationship to the correct posteriors" (lit, READ: Murphy, Weiss & Jordan, 1999); people often fail to explain away, making an associative rich-get-richer error (lit, abstract: Rehder & Waldmann, 2017), against plain association; learning that tracks its own uncertainty does explain away (lit, READ: Dayan & Kakade, 2001), in his favour; in schizophrenia, loops in which beliefs corrupt the evidence and the evidence corrupts the beliefs fitted reasoning best, with the evidence-to-belief loops tracking positive symptoms (lit, abstract: Jardri et al., 2017); that such loops count evidence twice unless inhibition cancels them is the 2013 theory, known here only from a secondary summary. Hebb's postulate is causal (lit, secondary: Hebb, 1949, quoted by Brown, Bligh & Garden, 2021), and at the synapse firing in the wrong order weakens the link (lit, abstract: Bi & Poo, 1998); the phrase "fire together, wire together" is credited by secondary sources to Löwel & Singer (1992; lit, abstract, which lacks the phrase) and Shatz (1992; not read). Test: Ghost V27 K2 (a constructed-world card whose primary is reported for scale) |
| **G263** | Revision checks alignment against several goals one at a time, some serving greater goals and some disconnected from them, as with views on slavery and the willingness to make money, where what bothers one is the kind of person one wants to be | **OPEN.** The curator's account (2026-11-07), extending global revision (D-GLOBAL-REVISION in [`DECISION_TRACES.md`](DECISION_TRACES.md) §6) and the several ends of G249. Test, in part: S15-W5 GO2 (PEP and EIP histories: whether later text follows a revised goal, not the one-at-a-time check) |
| **G264** | Laughter marks the completion of a hidden structure, and shared laughter marks shared inference | **OPEN.** The curator's idea (2026-11-07), "worth checking". In 1,200 conversational laughs, laughter followed statements, questions and material that did not seem humorous outside the conversation (lit, abstract: Provine, 1993), and only 10 to 20 percent followed anything joke-like, while speakers laughed almost 50 percent more than their audiences (lit, READ: Provine, 2000, his popular account of the same data); a caption that resolved a puzzling picture gave insight without mirth, while captions that also linked remote concepts gave both, so resolution may be necessary but is not enough (lit, abstract: Amir et al., 2015); an annotation study rejected the assumption that laughter directly follows what it laughs at (lit, abstract: Mazzocconi, Tian & Ginzburg, 2020); the encryption theory, that humor signals shared knowledge, is published (lit, metadata only: Flamson & Barrett, 2008) and tested (lit, abstract: Flamson & Barrett, 2013). PLAY's reward is already filed, as the analyst's proposal, as compression progress (G195 in [`THREE_COGNITIVE_LAYERS.md`](THREE_COGNITIVE_LAYERS.md) §1). The rat's 50-kHz chirp, proposed as primitive laughter, comes with play and tickling (lit, abstract: Panksepp & Burgdorf, 2003) and with reward anticipation, rising when amphetamine is put into the accumbens (lit, abstract: Burgdorf et al., 2001), and in hide-and-seek rats called while seeking and finding and fell silent while hiding (lit, abstract: Reinhold et al., 2019), so the ancestral call marks a state rather than a found structure, against the marker reading. Tests: S15-W5 LA1 and LA2; Ghost V27 K7 |
| **G265** | New inferences should refine old ones, recursively, so that the relationships between levels are checked | **OPEN, logic only.** The curator's direction (2026-11-07). Test: Ghost V27 K6 |
```

### F2b. `docs/theory/THE_TRIPLE_INFERENCE.md`, replace

Condition: none (the curator's 7 November answers, filed as his words and OPEN rows).

Anchor:

```text
Confidence: one bad test away for the finite-choice comparison; untested, logic only for the learned-end distinction, with the sim demonstration held by §5.
```

Text:

```text
Identity is also held to show in how one decides, with slowness read as a value nested in too large a decision tree and a model of the person predicting the trade; observers do read decision time, but as certainty or conflict that amplifies what the act says, and they credit struggle (G261). One act serving several motives is a case of explaining away, which belief propagation computes and which loops with many rare causes can derail, while plain association fails to explain away (G262). Revision checked against each goal in turn (G263), laughter as a marker of a completed structure, which most conversational laughter does not fit (G264), and the recursive refinement of old inferences (G265) are untested. Confidence: one bad test away for the finite-choice comparison; untested, logic only for the learned-end distinction, with the sim demonstration held by §5, and for the decision-time, motive, revision, laughter and recursion proposals.
```

### F3a. `docs/theory/READER_HEURISTICS.md`, insert_after_line_starting

Condition: none (the curator's 7 November answers, filed as his words and OPEN rows).

Anchor:

```text
| **HH-CLOSE-MODEL** |
```

Text:

```text
| **HH-CLOSE-KEEPS** | Closing on a source keeps what it already taught; re-checking is a separate, effortful act that only weakens those associations, and RAGE can drive it as a targeted re-read that works inferences the other way | **OPEN.** The curator's account (2026-11-07), extending HH-CLOSE-MODEL. Inferences people drew themselves resist correction more than stated misinformation (lit, abstract: Rich & Zaragoza, 2016), and extinction adds new, context-bound learning rather than erasing the old (lit, abstract: Bouton, 2004), in his favour on what stays and against re-checking as weakening; jurors given reason to suspect the motive behind information returned verdicts no different from unexposed jurors, without re-reading (lit, abstract: Fein et al., 1997), against, though with one piece of information judged soon after in a mock trial, and material already woven into a single picture resisted discounting (lit, abstract: Schul & Burnstein, 1985); one correction leaves a small residue on average (lit, abstract: Walter & Tukachinsky, 2020), though persistence is large on other measures and largest when people built their own reasons (lit, abstract: Chan et al., 2017); the sleeper effect appears only when the discounting cue follows the message (lit, READ: Kumkale & Albarracín, 2004); anger increases reliance on cues (lit, abstract: Bodenhausen, Sheppard & Kramer, 1994) and can increase careful processing when relevant (lit, abstract: Moons & Mackie, 2007). Test: Ghost V27 K5 (a constructed-world card whose re-read and tag primary is reported for scale) |
| **HH-SHARED-INFERENCE** | Shared inference lets an in-group deceive an outsider ("this friction is probably where bad actors live"), and other people's warnings and gossip are an early read of a source | **OPEN.** The curator's account (2026-11-07). Lie detection averages 54 percent, seeing a sender's baseline first adds about 3.7 points, and judges may be loath to call people who resemble them liars (lit, READ: Bond & DePaulo, 2006); pairs of liars matched on what they had planned but diverged on unanticipated questions while truthful pairs stayed consistent (lit, abstract: Vrij et al., 2009; lit, READ: Vernham, Granhag & Mac Giolla, 2016), against shared inference filling in a group's lie; lies were detectable across cultures, and foreigners were often judged more truthful (lit, abstract: Bond & Atoum, 2000); Ponzi schemes do better when an affinity link is present, so the documented exploit is real or fake insiders defrauding insiders (lit, abstract: Deason, Rajgopal & Waymire, 2015, a working paper); a conversation's partners understood its references better than overhearers who heard every word (lit, READ: Schober & Clark, 1989), and coded appeals carry their meaning to the in-group while it eludes the outgroup, concealment rather than a lie (lit, abstract: Albertson, 2015), in his favour. No study was found of an in-group deceiving an outsider together. Test: Ghost V27 K5 |
| **HH-ENGINE-NO-FLAGS** | ToMpathy's closed-source state does not flag a source's earlier claims; correction is a re-read pass | **OPEN, adopted as the working position.** The curator (2026-11-07), doubting the walkthrough's proposal that a closed source flag its earlier claims for re-checking: "there's no way to go back and flag them". People remember a claim's falsity as well as its truth (lit, abstract: Nadarevic & Bell, 2024), and suspicion of a source's motive discounted its material without re-reading (HH-CLOSE-KEEPS), against. Ghost V27 K5's retroactive-tag arm is null by construction in G3's world, where the gate closes when the reader's posterior on the truth is near 0.5, so it reports a tag's size for scale without pricing it, and the position stays untested |
```

### F3b. `docs/theory/READER_HEURISTICS.md`, replace

Condition: none (the curator's 7 November answers, filed as his words and OPEN rows).

Anchor:

```text
the other's mind stays modelled (HH-CLOSE-MODEL).
```

Text:

```text
the other's mind stays modelled (HH-CLOSE-MODEL). Closing keeps what a source already taught, and inferences readers drew themselves resist correction more than stated claims; how much survives a correction depends on the measure, and suspicion of a source's motive discounted its material without re-reading, so re-reading is not the only repair (HH-CLOSE-KEEPS). Shared inference hides meaning from outsiders, while the documented exploit of shared identity runs inside the group (HH-SHARED-INFERENCE). The engine's closed state flags nothing, adopted as the working position; Ghost V27's tag arm is null by construction and leaves it untested (HH-ENGINE-NO-FLAGS).
```

### F3c. `docs/theory/READER_HEURISTICS.md`, replace

Condition: none (the curator's 7 November answers, filed as his words and OPEN rows).

Anchor:

```text
HH-NO-TRANSLATION) and the closing of the model (HH-CLOSE-MODEL).
```

Text:

```text
HH-NO-TRANSLATION), the closing of the model and what closing keeps (HH-CLOSE-MODEL, HH-CLOSE-KEEPS), in-group deception through shared inference (HH-SHARED-INFERENCE) and the engine's closed state (HH-ENGINE-NO-FLAGS).
```
