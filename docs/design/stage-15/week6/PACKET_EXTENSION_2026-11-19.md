# Sounding Line, Stage 15, Week 6: the lattice extension

*19 November 2026. From the analyst (the implementation thread), for the Sounding Line owner. It extends Week 6 inside its approved clock and campaign ceiling. It adds to `PACKET.md` and `PACKET_EXTENSION_2026-11-15.md` and withdraws nothing in them except where section 2 says so. It carries no question for the curator: every choice is made here and can be overruled by him.*

**Where the files go.** This file: `docs/design/stage-15/week6/PACKET_EXTENSION_2026-11-19.md`. The pre-flight summary: `docs/design/stage-15/week6/PREFLIGHT_SUMMARY_2026-11-19.md`. The bundle `PREFLIGHT_2026-11-19.zip`: private intake, as before. The theory thread's Round 29 handoff, which this packet cites and does not replace: `docs/design/stage-15/week6/THEORY_HANDOFF_R29.md`. The thread's seed ledger, if the curator supplies it: `results/EVIDENCE_LEDGER_SEED_R29.jsonl`, unchanged.

## 0. Read first

- **Read at:** Sounding Line `005f38fa7` (19 November, 06:27 PST), the engine `14e2ced`, Ghost `fe7b22f69`, the theory thread through its Round 29 close (08:17 PST), and the Spark setup thread through 07:20 PST.
- **What the week showed** (the thread's count over every round, in the handoff, section 3): the results that cleared came where a person lived through a change and rated it. The two status diaries gave 8 clears in 20 results. The writing logs gave 71 results and no clear.
- **What this packet does with that.** It turns the diary handler, which is built and qualified, onto all nine channels, and it opens the Spark for the sealed sets. Almost every new card is a binding on installed modules.
- **What holds the program is building, not machine time.** On 18 November the recorded occupancy was about 2 of 192 slot-hours. Section 4 orders the cards for that.
- **The curator's direction, in his words** (18 and 19 November): "Building a lattice out of the channels and trying to find all of the channels would make a lot more sense"; "we don't have anything for play or for lust. Like, we actually need to spread wider and not just hit the convenient ones"; "We want to get the triggers to where we can identify them damn near every time."

## 1. Terms this packet uses

| Term | Meaning here |
|---|---|
| Member | one openESM release, named by its four-digit number |
| Prompt | one answered questionnaire of a diary |
| The floor | the lowest answer of a rating scale. For sliders from 0 to 100, any answer of 5 or less |
| Form L | the handler's installed form: predictors centred on the person's own mean over the card's rows, items scaled by their pooled within-person standard deviation, one joint least-squares fit, 2,000 whole-person bootstrap draws |
| Form O | new, section 3.0: the outcome is 1 when the answer is above the floor and 0 otherwise, fitted by logistic regression |
| Stand-in | a feeling word used to read a channel. A row about a stand-in is a row about a word |
| Fear-like set | anxious, ashamed and insecure (the three rated in the status diary) |
| The lattice | the table of signed predictions in section 5, written before any of its data are read |
| Sealed run | a job the agent starts on the Spark with `sudo sealed-run NAME SOURCE`; only gated totals return (section 3.7) |
| Claim id | one of the ids of the handoff's section 2 (T1 to T9, N1 to N3, A1 to A3, S1 to S3, AT1, AT2, TB1, P1, P2, M1 to M4, LP1 to LP15). Always written after the word claim. The engine's need codes N1 to N6 are a different list and do not appear in this packet |
| The collector | the separate agent thread that keeps the external data store. This repository asks it for things through the collector request folders its daily digests count |
| The registry | the external store's `_registry/REGISTRY.json`, with each source's `SOURCE.json`, `CARD.md` and `SCHEMA.json` (`docs/TOOLS.md`) |

## 2. Rulings and amendments

Rulings are the curator's, with his words and their dates. Amendments are the analyst's and are marked so.

| # | Item | Text |
|---|---|---|
| R19 | Names | The first need is **Competence** (was Knowledge; 19 November: "The reason I wanted to switch to competence is because of its interaction with identifiably competent."). The second is **Meaning** (was Nest; 18 November). Needs in reports: Competence, Meaning, Belonging, visibly respectable, visibly compassionate, the body. The stories' tranquility tag (safety) belongs to the body |
| R20 | A profile, not a label | "we're dealing with a PCA rather than a categorical distribution". A moment fires several channels, weighted by fit. Reports give the row of feelings, never only the largest |
| R21 | Labels | Pride, guilt and embarrassment are labels. "Embarrassment is what you feel when someone mocks you instead of shaming you." A test on a label is not reported as a channel test |
| R22 | SHAME's working trigger | "I guess decrease in competence with someone else present." LD1 tests the word present |
| R23 | Triggers are graded | "nothing is necessary and everything is sufficient". No card treats a feature as required |
| R24 | The Spark is worked by agents | "I'm not going to be running SparkStuffs by hand. That is not going to be the answer. Full stop". "I need to have agents be able to get up in there and do all their work in accordance with my standard spec sheet process." On the automatic output check replacing his review: "that needs to operate on the agent layer. I'll just assume an extra layer of stochastic error" |
| R25 | The record | "I want there to be a grander structure that we're building." Card RC1 |
| AH | Floors (analyst) | A card that compares a slope across contexts, strata, or levels of a second rating reads Form O as its primary and reports Form L beside it. Form O is not moved by a shifted floor. It is not a cure: it reads a difference in how noisy a feeling's answers are as a difference in slope. Each such card says so in its verdict. Reason: pre-flight section 2, worlds B and G |
| AI | Prior art and codebooks (analyst; the handoff's rule made concrete) | Before a card on a member not yet admitted is frozen: check each named item against the member's codebook, and read the source paper's design and stated hypotheses. Its result tables are not used to choose or tune a contrast. If the paper tested the same contrast, the card stays and is labelled a replication. An item that is absent voids its row; the row is not replaced |
| AJ | Sealed execution moves (analyst, under R24) | "MIDUS participant-data execution remains curator-local" is superseded. Sealed sets run on the Spark through the sealed runner. The combined Windows wrapper and the curator-entry candidate retire unrun and stay preserved. The qualified statistical cores and the source contract carry over unchanged |
| AK | Writing logs (the thread's advice, adopted) | No new theory card is sent to the writing logs. Cards already running there finish. KP1 is one of them |
| AL | Bounds (analyst's proposal; the owner's usual approval step applies) | Section 6, one table |
| AM | Spark runs and the workstation budgets (analyst) | A Spark run is not charged to a workstation CPU family. Its receipt records the job's hash, wall time and exit |

## 3. Cards

### 3.0 One estimator in two forms

- **Form L** is unchanged. It serves contrasts between two feelings on the same event in the same rows, as in ES1.
- **Form O.** Outcome: above the floor or not. Predictors: centred on the person's own mean over the card's rows and scaled by the pooled within-person standard deviation. Each person's own mean of every predictor enters as a covariate, because a logit cannot hold a separate intercept per person on this few prompts. Fit: plain logistic regression. Intervals: the same 2,000 whole-person draws, refitting in each. Coefficients are log-odds per within-person standard deviation.
- **Sensitivity for Form O**, where the installed core has it qualified: the conditional logit that removes the person's intercept exactly. It is reported beside the primary and does not replace it.
- **Qualification.** Form O is one new operator. Its fixture is `sl/pf_fixtures.py` of the bundle, which centres and scales as this section says: the build reproduces worlds A, B, D and G of LD1 and the four rows of the product form within two of the listed spreads. World B: no planted difference, a heavier floor in one context; Form O reads zero where raw ratings read plus 0.047. World G: no planted difference, one feeling noisier in one context; Form O reads plus 0.106. A build that reads zero in world G has not reproduced the form.
- **When a registered row lands.** Its estimate is at or past its bar on the predicted side and its interval excludes zero. This is the convention of the 15 November packet. The theory thread grades by its own rule, which asks the interval to clear the bar; the return gives estimate, interval and bar so it can.
- **Units and default bars.** Form L: standard units per within-person standard deviation of the predictor; a registered coefficient or contrast has the bar 0.05 unless its card says otherwise. Form O: log-odds per within-person standard deviation; a registered coefficient or contrast has the bar 0.10 and a product 0.05 unless its card says otherwise.

### 3.1 On the status diary already admitted (member 0057; member 0056 as the second sample)

Items below are from the public item list and match the names the installed parser already reads. Member 0056 lacks lonely, excluded, comfort and helped; rows that need them are void there.

#### LD1. SHAME alone and in company (handoff A3; claim T4)

- **Question.** Does a failure shame more after an interaction than after time alone?
- **Rows.** Every answered prompt. Context is interaction (`interaction` = 1) or solitary activity (`interaction` = 2).
- **Failure.** Felt success reversed: 7 minus `int_success` after an interaction, 7 minus `occup_success` after an activity, centred on the person's own mean over the card's rows. Context enters as its own term and in a product with failure; the product's coefficient is the difference between the two slopes.
- **Outcomes.** Ashamed (`int_ashamed`, `occup_ashamed`). Comparison feeling: sad (`int_sad`, `occup_sad`).
- **Primary (Form O).** The slope of ashamed on failure after interactions minus the same slope alone, minus that same difference for sad. Prediction from the curator's row: positive. Bar: 0.10.
- **What a positive result can and cannot mean.** It is not the floor (world B) and not company sharpening every bad feeling alike (world D). It can still be that ashamed's answers are noisier after time alone (world G), and nothing in this diary separates that from the curator's row. The verdict carries that sentence.
- **Also reported.** The ratio of the two slopes, company over alone, for every one of the feelings both contexts rate: a ratio shared by all of them points to noise or to company in general, and a ratio that is ashamed's alone is the curator's row or world G. The slope of ashamed on failure alone, by itself: above zero means failures shame with nobody in the room, which is the literature's weaker form ([Tangney and others 1996](https://doi.org/10.1037/0022-3514.70.6.1256): "a significant proportion of shame and guilt events occurred when respondents were alone"). The same difference for insecure, anxious, angry and lonely, as one table. Among interactions: in person against by phone or chat (`communication`), and one partner against more (`no_interactionpartner`).
- **Fixture, computed.** `pf_fixtures.py`, worlds A to G. A (0.30 against 0.15 planted): plus 0.237, spread 0.045. B (the floor trap): minus 0.010. D (company sharpens every bad feeling): plus 0.008. G (shame noisier alone, nothing else): plus 0.106.
- **Limits.** Felt success is a feeling and not an observed failure. Both ratings come from one prompt. Time alone means the last activity of five minutes or more without interaction; someone's opinion may still have been in mind.
- **Prior art.** Shame alone and exposed: Tangney 1996 above; [Smith and others 2002](https://doi.org/10.1037/0022-3514.83.1.138). Not found in a light search (titles and abstracts): a within-person comparison of this slope by context in a diary.

#### LD2. The status check with rank in hand (handoff A4 and B1; claim A3)

- **Question.** After criticism, does the feeling tilt toward anger when I outrank the other person and toward the fear-like set when they outrank me?
- **Common to the three forms.** Interaction prompts. Event: `status_criticised`, with the other five status events in the model. For each outcome a Form O fit. The quantity G is the coefficient for angry minus the mean of the coefficients for anxious, ashamed and insecure.
- **Form (b), the scored one: rank by my own conduct.** The product of criticised and `beh_leadership` ("I took the lead"), both centred. Primary: G for the product. Prediction: positive. Bar: 0.05 with the interval clear of zero. Second reading with `beh_selfesteem` ("I was self-assured").
- **Form (a): rank by the other person's role** (the analyst's). Prompts with one partner (`no_interactionpartner` = 1). Above me: Supervisor (code 1 of `interaction_partner1`). Below me: My employee (2) or My child (7). Peers: Co-worker (3), Friend or acquaintance (5), Partner (6), Sibling (9). Other codes are tabled and unscored. Primary: G for criticism below me minus G for criticism above me. Prediction: positive. Bar: 0.40, which is two spreads of the fixture.
  - **Support first, counts only, before any outcome is read:** at least 60 prompts with criticism above the floor in each of the two strata, from at least 40 people each. Under that, the card files its counts and a table, and gives no verdict.
  - **Known answer for the coding:** people report taking the lead more with those below them than with those above, as published for work roles ([Moskowitz, Suh and Desaulniers 1994](https://doi.org/10.1037/0022-3514.66.4.753); record checked, the finding is from the analyst's memory of the paper). If that fails here, the role codes do not carry rank in this sample and the verdict says so.
- **Form (c), the thread's:** the product of criticised and `int_superior`. Reported with its limit: superior is rated after the interaction, beside the feelings, and may be a result of the same moment.
- **Reading.** Under the status check all three are positive. If only (c) is, and only for the upstaged event, the item's wording explains it (the upstaged item presupposes holding the floor). The curator's account of held anger toward someone higher predicts that anger still rises under criticism from above, with the fear-like set beside it; the table by stratum shows that directly.
- **Fixture, computed.** The fixture has one fear-like rating standing for the three. Product form: no product planted reads minus 0.0072 (spread 0.0215) in Form O and plus 0.0091 (spread 0.0101) on raw ratings; 0.04 planted reads plus 0.072 and is seen in 90% of worlds. Role form, in Form O: 447 and 543 prompts in the two strata under assumed shares; nothing planted reads minus 0.020 (spread 0.206); a tilt of 0.10 reads plus 0.473 and is seen in 62% of worlds; a tilt of 0.20 is always seen.
- **Limits.** Role is rank in one relationship, not standing in general. My child may be an adult. Conduct and feeling come from one prompt.
- **Prior art.** What people do with anger differs by the target's rank in recalled episodes ([Kuppens, Van Mechelen and Meulders 2004](https://doi.org/10.1177/0146167204271176)) and in accounts of anger at work toward superiors, co-workers and subordinates ([Fitness 2000](https://doi.org/10.1002/(sici)1099-1379(200003)21:2<147::aid-job35>3.0.co;2-t); title checked, paper not opened). Not found in a light search: the split of anger against the fear-like feelings by the other person's role within one person's own daily interactions.

#### LD3. The solitary table: SEEKING's first diary row (analyst's card; claims T6, T2)

- **Why.** SEEKING has never had a test of its trigger. The same diary rates what the person did alone and how the activity was.
- **Rows.** Solitary-activity prompts.
- **The table (Form L).** Each of the fourteen feelings after the activity on the eight activity ratings together: `pleasant`, `fun`, `done` (tasks others assigned), `intellectual`, `overwhelmed`, `bored`, `concentrated`, `motivated`. It is filed whole, as ES1's table was.
- **Two registered contrasts,** bar 0.05 each:
  1. `intellectual` raises enthusiastic more than it raises relaxed. Pleasant and fun are in the model, so general good mood is held. Prediction: positive (SEEKING: good news on offer where there is something to work out).
  2. `overwhelmed` raises anxious more than angry. Prediction: positive (FEAR: a drop still coming, little power over it).
- **Described, not scored.** What a bored activity is followed by: whether the next answered prompt of that day is an interaction, and of what type. The curator's candidates for what boredom opens (PLAY, LUST) cannot be told apart here.
- **Limits.** Enthusiastic is also a marker of good mood in general, which is why pleasant and fun are held and why the contrast is against relaxed. One prompt carries both ratings.
- **Prior art.** The trigger of interest ([Silvia 2005](https://doi.org/10.1037/1528-3542.5.1.89), named in the thread's addendum of 18 November; that interest follows novelty together with the sense of being able to cope is the analyst's memory of the paper). Not found: this contrast in a diary.

#### LD4. Recipes: what the other words are made of (analyst's card; the report layer)

- **Why.** Pre-flight section 1: a diary shows how a word answers an event. It does not show a channel's trigger by itself. With one word taken as a marker per channel, the other words can be written as mixtures of the markers. This is the form of the curator's "PCA" that a diary supports.
- **Inputs.** Two tables of coefficients in Form L. Interactions: the fourteen feelings on every rated feature of the interaction, leaving out the two coronavirus items: the six status events and the seven conduct items, thirteen in member 0057, and comfort makes fourteen. Member 0056 has twelve. Solitary: LD3's table.
- **Anchors, fixed here.** Angry for RAGE, anxious for FEAR, lonely for PANIC/GRIEF, ashamed for SHAME, enthusiastic for SEEKING.
- **Recipe.** For each other word (proud, successful, superior, excluded, envious, resentful, insecure, relaxed, sad): the least-squares weights that write its row of coefficients as a sum of the anchors' rows. Intervals from whole-person draws that rebuild both tables.
- **Checks, in this order.** The condition number of the anchors' rows in each context: 15 or more means that context cannot be read, and the card says so. The count of directions that carry the table (singular values against their bootstrap noise): how many separate things the rated features move in fourteen words.
- **One registered test.** The correlation between recipes from interaction prompts and recipes from solitary prompts, over the nine other words' weights on the five anchors (45 numbers). The anchors' own rows are left out: each is its own unit by construction and would push the correlation toward 1. At 0.6 or more with the interval above 0.3, words keep their recipes across contexts. Pre-flight at this size and at weak triggers: 0.95 when they do (worst world 0.84), minus 0.06 when they do not (highest world 0.42).
- **Three sanity rows** (analyst's): resentful loads on angry more than on any other anchor; insecure loads on anxious and ashamed more than on angry; excluded loads on lonely most.
- **Reading rule.** A recipe says how a word's answers move with the anchors' answers across kinds of moment. It is not a definition of the word, and the anchors' purity is assumed, not tested.
- **Member 0056** has no lonely item and 327 people: four anchors, a description only.

### 3.2 Carried and amended

- **KP1** (the pause as a swap of attention; the only test on people of claim AT1). It is held at 100 of 2,000 draws. Section 6 proposes the allowance that finishes it. Nothing else about it changes.
- **LA6** (what is said just before a laugh; LP9). Built and waiting: admit and run as designed.
- **EN1** (email, the colored remainder). The thread's addendum of 18 November: add Ghost's two refresh rivals to the candidate set, and require at least 400 messages per writer.
- **IN13 Part D** runs when the engine's need export arrives. The engine packet of this date closes that export first.
- **CH13, CH14, ES3's held duration card, the MIDUS constructed qualifications:** as filed.

### 3.3 Laughter in the meetings (handoff A5; claim T7)

- **LA7. Who laughs at whose lines, by role (LP5).** Scenario meetings with assigned roles. A laugh by B is at A's line when it starts while A holds the floor or within 2.0 seconds after A's segment ends, and B is not A. Rate: such laughs per minute A holds the floor, for each ordered pair of roles. First fit the social causes (role, position in the turn, whether someone else is already laughing), then table what is left. No sign is registered: the curator's account allows the superior's laugh as the answer that grants a transgression, and in print the kind of laugh differs with the laugher's rank ([Oveis and others 2016](https://doi.org/10.1016/j.jesp.2016.04.005); record checked, paper not opened). The table is the result.
- **LA8. After a laugh the target does not join (LP6).** A's line draws a laugh and A does not laugh within 2.0 seconds. Outcome: A's share of speaking time over the next 60 seconds, against moments where A joined, with the meeting's phase and A's share over the previous 60 seconds held. Prediction from the curator's account of mockery: lower. Bar: 2 points of share with the interval clear of zero; draws by meeting.
- **Limits.** Roles are assigned for a design exercise among people who are not colleagues. Laughter is what the annotators marked.
- **Prior art.** Roles have been recognised from these meetings' talk ([Valente and Vinciarelli 2011](https://doi.org/10.21437/interspeech.2011-770)). Not found in a light search: laughs by ordered role pair, or the target's talk after an unjoined laugh.

### 3.4 On diaries held and not yet admitted

Each card begins with amendment AI. Item names are from the public lists. Each row below is registered now; a row whose item is missing is void.

#### LB1. Member 0060: SEEKING, LUST's opening, and two rows for RAGE (handoff B2 and B3; claims T6, T9, T1, A3)

199 students, four prompts a day for six weeks ([Beck and Jackson 2022](https://doi.org/10.1177/09567976221093307), whose own question was how well a person's next behaviour can be predicted).

- **SEEKING.** State `curious` ("Was curious about many different things") and `content`, each on `intellect` ("Deep thinking is required") with `positivity` held, Form L. Registered: curious rises more than content. The handoff's open question (does curiosity ride my own competence in the moment, or being seen) is a table with no sign: curious and excited on `efficient` and `inventive` (own competence), on `sociality` and `dominant` (being seen), together.
- **LUST's opening (Form O).** `mating` ("Potential romantic partners are present"; three answers) at one prompt, on three things at the previous prompt of the same day: `proud`, `bored_schoolwork`, and `purposeful` reversed. `mating` at the previous prompt and `sociality` now are held. Registered: all three positive, each its own row. Same-prompt row: with `sociality` held, `mating` goes with `excited` more than with `content`. The item rates the situation and not desire, so the card reads the opening and not the firing. Expect small effects ([Shanks and others 2015](https://doi.org/10.1037/xge0000116), on the record). The write-up stays clinical.
- **RAGE.** Over all prompts, with argument as 1 when `argument_family` or `argument_friend` is reported and 0 otherwise: the coefficient of argument on angry minus its coefficient on afraid (Form L). Registered: positive.
- **The status check again.** The product of that argument term and state `dominant` ("Was dominant, acted as a leader"), on angry against afraid, Form O. Registered: positive. This repeats LD2 form (b) on other people with other items.

#### LB2. Members 0042, 0043, 0044: the status check, three samples (handoff B1; claim A3)

342, 330 and 396 people ([Mostajabi and Wright 2024](https://doi.org/10.31219/osf.io/3szng), a preprint; the public list has each person's rating of their own dominance and warmth toward the other, and no rating of the other person).

- **Rows.** Prompts with an interaction. Unpleasantness: `happy_interaction` reversed and centred (members 0042 and 0043); in member 0044, which lacks the during-interaction feelings, momentary `happy` reversed.
- **Registered, one row per member (Form O).** The product of unpleasantness and own dominance (`dom_sub_you`, signed so that higher is more dominant; check the codebook), on angry against nervous (`angry_interaction` and `nervous_interaction`, or momentary `angry` and `nervous` in 0044). Prediction: positive.
- **Limit.** Acting dominantly may follow from anger as well as lead to it. The card reads an association.
- **Prior art.** Likely close: the link between own dominance and felt anger has a literature in this tradition. Read the preprint and the project's overview of earlier uses (`https://osf.io/7a5de`) before freezing; label a replication if it is one.

#### LB3. Member 0072: the need table in the open, CARE's first table, and PLAY's brake (handoff B4 names this member for CARE; the need table and the brake are the analyst's; claims N1, T1, T2, T3, T8, T7)

562 parents, one evening report a day for three weeks, licence CC BY 4.0 ([Neubauer and others 2021](https://doi.org/10.1111/cdev.13515), whose own question was autonomy-supportive parenting). Each evening it asks what went wrong today by kind, what the parent's needs met, ten feelings of the parent and ten of the child. It is the nearest open twin of the sealed MIDUS table and needs no Spark.

- **The table (Form L).** `parent_angry`, `parent_afraid`, `parent_worried` and `parent_sad`, each on the day's events together: the eight stressor items, `told_what_to_do`, `against_own_will`, `pressure`, `excluded_ostracized`, `failure`, `did_stupid`, `struggled`, `unappreciated`. Filed whole.
- **Registered rows,** bar 0.05 each:
  1. Blocked (the mean of `told_what_to_do` and `against_own_will`): angry rises more than afraid.
  2. `stressor_health` or `stressor_financial`: the mean of afraid and worried rises more than angry.
  3. `excluded_ostracized`: sad rises more than angry.
- **CARE's first table.** The child's drop: the mean of `child_sad`, `child_afraid` and `child_worried`, centred. Tabled against the parent's ten feelings and against `parenting_talked_worries`, with time spent with the child held. One registered row: on the child's drop, the parent's worried rises more than the parent's angry.
- **PLAY's brake.** `parenting_fun` ("My child and I had fun together today") on the parent's afraid, sad, angry and exhausted together, with `parenting_disagreements` and time with the child held. Registered: afraid lowers fun more than sad does. The theory's brake is a near threat and not any loud feeling.
- **Limits.** One report a day, by the parent, about both people. The weeks are from the first lockdown of 2020.

#### LB4. PLAY in two more members (handoff B5; claim T7)

- **Member 0070** (82 students; situations rated silly, repulsive, heartwarming and more; [van Halem and others 2020](https://doi.org/10.1002/per.2252)). `silly` on `expected`, `important`, `pleasant`, fearful and sad together, Form L, with `expected` and `important` signed so that higher is more expected and more important (check the codebook). Registered: expected lowers silly; important lowers silly; fearful lowers silly more than sad does. The first two are the analyst's reading of PLAY's row as the record words it (nothing loud, a small threat): a moment that is unimportant and not what was expected.
- **Member 0076** (519 adults; interactions rated from serious to playful). First establish that the held copy has rows; the public record says the data reached openESM by email. If it has: `interaction_playful` on the day's `stressed` with `interaction_pleasant` held, each signed so that higher is more playful, more stressful and more pleasant (check the codebook). Registered: negative. Tabled: playful and `interaction_meaningful` on how often the person meets this partner.

#### LB5. Member 0064: the bad feelings together (handoff B6; claims A2, T5)

245 people, outpatients and their partners, reporting after interactions ([Wright and others 2017](https://doi.org/10.1037/abn0000286)). No event is rated, so this card reads which feelings rise together.

- **Scales, from the public list.** Fear: afraid, scared, frightened, nervous, jittery, shaky. Anger: angry, hostile, irritable. Scorn: scornful, disgusted, loathing.
- **Registered,** as within-person partial correlations between scale means, with each person's mean removed and `distressed` and `upset` held: anger and fear rise together (positive; bar 0.05); scorn goes with fear less than anger does (the difference is negative; bar 0.05). The second comes from the one pair that never co-occurred in [Scherer and Meuleman's episodes](https://doi.org/10.1371/journal.pone.0058166), fear with contempt.
- **Read first:** [Trampe and others 2015](https://doi.org/10.1371/journal.pone.0145450), which mapped which feelings travel together in daily reports.
- **Limit.** A clinical sample. Six items for fear and three each for anger and scorn.

#### LB6. Member 0063: SEEKING at work (handoff B2; claim T6)

173 working adults, ten prompts a day for five days ([van Woerkom and others 2022](https://doi.org/10.1007/s10902-022-00546-x)). `inspired` on `good_at_this`, `appreciated`, `chose_doing` and `doubt` together, with `cheerful` held, Form L. Registered, from the curator's "And seeking would drive both": good at this is positive, and appreciated is positive. Two rows.

### 3.5 Not in this packet

- **Members 0049 and 0050** (helping and the helper's mood). The handoff's question for them is the source paper's own result ([Pronizius and others 2024](https://doi.org/10.1038/s41598-024-75261-z): helping goes with better mood, and with more stress when it costs effort). It is cited as CARE's cost and not rerun.
- **The two-language recall task** and **a nine-channel local reader** are the handoff's later items. The reader is in the engine packet.

### 3.6 The Spark lane: rules

As installed on 19 November. Where a later edition of `claude/SPARK_FACTS.md` differs, the sheet governs.

- **Reach.** From the workstation: `ssh spark` (host `[private endpoint omitted]`, user `agent`, the agent's own key). The agent has one root command, no Docker, and cannot read `/srv/private`. The rules on the box are `/home/agent/AGENTS.md`. Never power it off.
- **First call of a session:** `ssh spark "id; nvidia-smi -L"`. If the call waits on an approval nobody gives, the lane's cards are held with that reason and the workstation cards go on.
- **One record.** A job is written and committed in this repository, copied to the Spark, run there, and its returned files are copied back and committed with a receipt. The Spark keeps caches and nothing else.
- **GPU.** Any job that uses it holds `flock /home/agent/gpu.lock` for its whole run. The sealed image has no GPU work.
- **Heat** (the limit is the analyst's). The sheet says the GPU with every processor core loaded throttled, and a two-hour test was started on 19 November. Until the sheet records its result: a sealed job uses at most 4 numerical threads. The template sets this. The engine packet sets the same limit for GPU jobs.
- **The store** (the limit is the analyst's). The sheet says one of the NAS's drives was degraded on 19 November and that nothing heavy should run against it. Until the sheet says it cleared: no job reads more than 2 GB from the private mount, and nothing opens audio or video.

### 3.7 The sealed runner: contract

- **Call.** `ssh spark "sudo sealed-run NAME SOURCE"`. NAME and SOURCE each start with a lower-case letter or a digit, continue with lower-case letters, digits, hyphens or underscores, and have 64 characters at most. SOURCE is one folder under the private mount. A source beginning `midus-mr1-` is refused: the Refresher stays held out.
- **Job.** One file, `/home/agent/sealed-jobs/NAME/run.py`. It sees `/data` (the source, read-only) and `/out` (writable), a read-only root, a small `/tmp`, no network, 64 GB, six hours, and the image `sl-tabular:2026-11-16` (pandas, numpy, scipy, statsmodels, pyreadstat, pyarrow).
- **What returns.** The `.csv` files of `/out`, copied to `/home/agent/sealed-totals/NAME-<time>/`, and only if every file has a column `n`, every row's `n` is a whole number of 11 or more, no file has more than 2,000 rows, and all files together are at most 256 KB. Nothing the job prints returns. On a non-zero exit only the exit code returns.
- **Three habits every sealed job keeps** (pre-flight section 3; `spark/run_template.py`):
  1. It writes a status table in place of crashing: files read, people, each required variable present or missing.
  2. Every table goes through one writer that drops rows under 11 and writes whole-number counts. `n` is people, never rows.
  3. It uses the fixed exit codes of the template for what it cannot write down.
- **Blind discipline.** A job's hash is committed before its first real run. A rerun changes only what the exit code or the status table points at, and records why. A change of model after totals were seen is a new card. After three failed runs of one job, stop and file.
- **Intervals are computed inside the job.** Only totals leave, so each sealed card runs its own whole-person draws on the Spark.

### 3.8 Sealed cards

#### SM0. Reach, gate and structure

1. `ssh spark "sudo sealed-run test midus-mr1-p1"` must answer `refused: the MIDUS Refresher is held out`.
2. Rehearse the template against the local gate copy (`spark/rehearse.py`): seven cases as in the pre-flight summary.
3. A structure probe on each MIDUS source folder the registry lists for the second and third waves (the sheet shows `midus`, `midus-m2-p1`, `midus-m2-p2`, `midus-m3-p1`, `midus-m3-p2`): the status table only. It tells which folder holds the daily interviews and which the main survey.

#### SM1. The MIDUS table, second wave (handoff C1; cards MI1 to MI4 of 15 November; claims N1, A1, A3, S2, S3)

- **What it is.** The statistical cores that passed their 38 and 22 constructed cases, with the source contract whose checks passed inside the 31-case qualification, packed into one `run.py` in the template's shape. No model, support rule or threshold changes.
- **Rehearsal.** The same constructed fixtures, read through `/data`, in the image's package versions; then the local gate copy.
- **MI1 and MI3** need only the daily interviews and run first: the fourteen feelings on the seven areas at risk with severity, control and the count of stressors; the four contrasts of 15 November; what lingers by control.
- **MI2's trait checks and MI4** need the main survey beside the daily file. The runner mounts one folder. If the probe shows them in separate folders, file a request with the collector for a folder `midus-m2-joined` holding the two files side by side, unchanged, and run those two cards when it exists. They do not hold MI1 or MI3.
- **Returned tables.** Coefficients with their intervals and people counts; the four contrasts; the status table. Nothing by person, by day or by small group.
- **Why it is first on the Spark.** The curator's ruling made it the Spark's first job, and it is the largest table within reach in which people report what a day's trouble put at risk, how much control they had, and what they felt.

#### SM2. The same job on the third wave

A repeat on the same people. Run after SM1 returns, with the job unchanged.

#### SC1. CANDOR, the codebook first (handoff C2)

- **From the collector's card and schema for the CANDOR folder, no row opened,** a one-page note answering: whether any transcript version marks laughter and filled pauses; the exact names of the post-conversation items on how funny each person was, on the partner's status and on liking; what identifies a conversation and a speaker.
- **If the card and schema do not answer:** a sealed probe that returns counts only. For each transcript version: the number of conversations whose text contains each marker of a fixed list (`[laughter]`, `laugh`, `haha`, `um`, `uh`, `mm-hmm`). The survey's column names with people counts.
- **Terms.** No audio or video is opened. No voice prints or face prints. The corpus is [Reece and others 2023](https://doi.org/10.1126/sciadv.adf3197).

#### SC2. Funny, status and liking (handoff C3; LP11; after SC1)

Across conversations, with length and each person's share of talk held: the partner's rating of how funny I was, against the partner's liking of me and the partner's rating of my status. Registered, from the curator's prediction that PLAY's display raises seen as kind and lowers seen as competent a little: funny goes with liking more than with status (the difference of the two standardized coefficients; bar 0.05). Whole-conversation draws inside the job.

#### SC3. Repeats against fillers (handoff C4; claim AT1; only if SC1 finds both marked)

Do repeats and restarts cluster where a speaker changes topic, and fillers not? The sealed image has no text model, so topic change is the drop in shared words between adjacent windows, computed in the job. It is the last card of the lane. Fillers are partly chosen signals ([Clark and Fox Tree 2002](https://doi.org/10.1016/s0010-0277(02)00017-3)); repeats follow load ([Bortfeld and others 2001](https://doi.org/10.1177/00238309010440020101)).

### 3.9 RC1. The record rule (claims: all)

1. **A ledger file.** `results/EVIDENCE_LEDGER.jsonl`, append only. At every scientific landing, one row with the handoff's eleven fields: `id` (this repository's result id), `date`, `question` (one plain sentence), `data` (the source and how many people or units), `estimate`, `interval`, `bar`, `verdict` (the record's own word), `limit` (the record's own sentence on what the result does not establish), `claims` (one or more claim ids), `family` (the kind of data: diary, recalled events, sealed survey, meetings, chess, writing logs, and so on). Nothing private.
2. **The seed.** If the curator supplies the thread's ledger, it is filed unchanged beside the new file. A seed row known to be wrong is corrected by appending a row that names it.
3. **Claim ids for the theory rows.** A file `docs/theory/CLAIM_IDS.json` giving each of the 206 theory rows its claim ids, or `none`. No theory row is reworded. The rows marked `none` are listed in the return; that list answers the thread's open question about which claims its list of 23 lacks.
4. **The register.** Each entry of `docs/records/CLAIM_REGISTER.json` gains a field `theory_claims`.
5. Every card of this packet names its claim ids in its heading. Its landing writes the row.

### 3.10 LT1. The lattice score

At the Week 6 freeze, one table from section 5: each row's estimate, interval and verdict, and three counts. Decided rows (interval excludes zero). Decided rows on the predicted side. The same two counts with rows that share a source and a claim counted once. The rule for any count: with R decided rows and k on the predicted side, the set passes at 0.05 when the chance of k or more heads in R fair tosses is 0.05 or less. Marks from the pre-flight: 9 of 10, 10 of 12, 12 of 16, 15 of 20, 22 of 32, 28 of 44. The table is filed whether or not it passes. A row that could not run is listed with its reason and is not counted.

## 4. Order

Sized for two to three days of building. Machine time is not the limit.

| When | Cards | Why this order |
|---|---|---|
| First | SM0. Form O's operator and fixture. LD1, LD2, LD3 as bindings. KP1's release. LA6's admission | nothing here needs a new source; LD1 and LD2 answer rulings of 19 November |
| Next | SM1. LD4. LB1's admission and run | the Spark's first job; the first rows for SEEKING and LUST |
| Then | LB3. LB2. SM2. SC1. RC1 | the open need table; three samples for the status check |
| Last | LA7, LA8. LB4, LB5, LB6. SC2, SC3. LT1 at the freeze | |

**When building is the bottleneck,** keep in this order and drop from the bottom: SM1; LD2 and LD1; LD3 and LD4; LB1; LB3; KP1's release; RC1; the rest.

## 5. Predictions before data: the lattice

Written on 19 November. The fourteen by six interaction table of member 0057 has been seen (ES1); rows 2 to 4 use two of its items with moderators nobody has fitted. No other row's data has been opened by the analyst, the thread or, as far as the record shows, the owner.

| Row | Card | Source | Claim | Predicted sign |
|---|---|---|---|---|
| 1 | LD1 | 0057 | T4 | a failure shames more in company than alone, beyond what sad shows: positive |
| 2 | LD2 (b) | 0057 | A3 | criticism times took the lead, on angry against the fear-like set: positive |
| 3 | LD2 (a) | 0057 | A3 | criticism from below me against from above me: positive |
| 4 | LD2 (c) | 0057 | A3 | criticism times superior: positive |
| 5 | LD3 | 0057 | T6 | intellectual raises enthusiastic more than relaxed: positive |
| 6 | LD3 | 0057 | T2 | overwhelmed raises anxious more than angry: positive |
| 7 to 10 | LD1, LD2 (b), LD3 twice | 0056 | T4, A3, T6, T2 | the same four signs |
| 11 | LB1 | 0060 | T6 | deep thinking raises curious more than content: positive |
| 12 to 14 | LB1 | 0060 | T9 | possible mates present, after pride, after boredom, after low purpose: each positive |
| 15 | LB1 | 0060 | T9 | possible mates present goes with excited more than content: positive |
| 16 | LB1 | 0060 | T1 | an argument raises angry more than afraid: positive |
| 17 | LB1 | 0060 | A3 | an argument times dominant, on angry against afraid: positive |
| 18 to 20 | LB2 | 0042, 0043, 0044 | A3 | unpleasantness times own dominance, on angry against nervous: positive |
| 21 | LB3 | 0072 | T1 | blocked raises angry more than afraid: positive |
| 22 | LB3 | 0072 | T2 | a health or money stressor raises afraid and worried more than angry: positive |
| 23 | LB3 | 0072 | T3 | excluded raises sad more than angry: positive |
| 24 | LB3 | 0072 | T8 | the child's drop raises the parent's worried more than angry: positive |
| 25 | LB3 | 0072 | T7 | afraid lowers fun together more than sad does: the difference is negative |
| 26, 27 | LB4 | 0070 | T7 | expected lowers silly; important lowers silly: both negative |
| 28 | LB4 | 0070 | T7 | fearful lowers silly more than sad does: negative |
| 29 | LB4 | 0076 | T7 | a stressful day lowers playful, with pleasant held: negative |
| 30 | LB5 | 0064 | A2 | anger and fear rise together: positive |
| 31 | LB5 | 0064 | T5, A2 | scorn goes with fear less than anger does: negative |
| 32, 33 | LB6 | 0063 | T6 | inspired on good at this, and on appreciated: both positive |
| 34 to 37 | SM1 | MIDUS, second wave | N1, A1, A3 | the four contrasts of 15 November (others' regard at risk: ashamed over angry; routine disrupted: the anger words over the fear words; plans or health at risk: the fear words over angry; control: lonely, hopeless and sad fall more than angry) |
| 38 to 41 | SM2 | MIDUS, third wave | the same | the same four |
| 42 | SM1 | MIDUS, second wave | S2 | what lingers after low control against after high control: positive |
| 43 | LA8 | meetings | LP6 | the target's share of talk after an unjoined laugh: lower |
| 44 | SC2 | CANDOR | LP11 | funny goes with liking more than with status: positive |

Forty-four rows over fourteen sources (eleven diary members, MIDUS, the meetings and CANDOR). Every channel has at least one: RAGE (16, 21, 35, 39), FEAR (6, 10, 22, 36, 40), PANIC/GRIEF (23, 37, 41), SHAME (1, 7, 34, 38), DISGUST (31), SEEKING (5, 9, 11, 32, 33), PLAY (25 to 29, 43, 44), CARE (24), LUST (12 to 15). DISGUST and CARE rest on one row each, and both are weak rows.

**The analyst's guesses, so they can be scored too:** rows 2, 5, 16, 21, 22, 30 and the MIDUS anger and fear contrasts land. Row 1 lands small or not at all (shame after solitary failure is real). Row 3 cannot say for want of support. Rows 12 to 14 cannot say. Row 23 fails the way ES1's loneliness contrast did. Row 25 is a coin.

## 6. Proposed bounds (amendment AL)

| Bound | Proposal |
|---|---|
| Clock | unchanged: freeze 22 November 20:00 PST, drain 22:00, final addendum 23:00 |
| Gear | CPU-only Gear 2, two numerical threads per worker, the existing floors |
| Diary family (ES), added | 400,000 CPU-seconds; each new diary card 20,000 including replay; LD4 10,000 |
| Laughter family (LA), added | 60,000 CPU-seconds |
| KP family, for KP1 only | 70,000 CPU-seconds added (the filed projection for the remaining draws and their replay is about 67,525) |
| Sealed runs | not charged to a workstation family; at most thirty under this packet, reruns included (five probes, six jobs, and up to two reruns of each job leave room); six hours each by the runner |
| Campaign ceiling | unchanged at 6,000,000 CPU-seconds |

## 7. The return

One file at the freeze, `docs/exchange/THEORY_RETURN_LATTICE.md`, with: the lattice table of LT1; LD3's and LB3's tables whole; LD4's recipes with the two checks; the sealed tables as returned; the support counts of LD2 form (a); the list of theory rows with no claim id; every row that was void or could not run, with its reason. Each number carries its limit sentence. Verdicts in the record's own words. Nothing in the return asks the curator a question.

## 8. Limits of this packet

- Every diary row is a word. Pre-flight section 1 shows why that cannot be argued away inside one diary. The hedge is thin: the meetings, where the measure is conduct, and CANDOR's transcripts if SC3 runs.
- Thirteen of the fourteen sources are self-report: eleven diaries at one moment or one evening, MIDUS by telephone each evening, and CANDOR's ratings after a conversation. A shared habit of answering can move two ratings together. The contrasts are differences between feelings of the same tone for that reason. What MIDUS adds is not a different kind of measure. It adds what was at risk and how much control, asked in a large sample.
- Form O has a blind spot (amendment AH). A card that lands on it has shown a steeper slope or a quieter feeling, and cannot say which.
- Item names for the members not yet admitted come from public lists. Amendment AI is the check.
- The role shares behind LD2 form (a) are assumed; its support count comes first.
- The sealed runner's check is mechanical. It stops accidents. It is the curator's stated choice (R24) that it stands in for his review.
- The analyst opened no row of any dataset. The pre-flight is constructed worlds and public metadata.
