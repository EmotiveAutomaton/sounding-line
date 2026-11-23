# LGH1 ICSI ACOUSTICS

## Against, and clear

No contrary estimate with an interval clear of its registered bar was returned. The mixture-count prediction missed on the observed count.

| Question or prior guess | ICSI result | Reading |
|---|---|---|
| Groups differ on at least two held-out facts | Two of three exceeded their own shuffle threshold | Registered bar met on this corpus |
| Three or four mixture groups | Six in both halves, the upper end of the search | Prediction missed |
| Density joining leaves one group | One remained | Prediction held; this rule can also merge genuine near neighbours |
| Groups differ in whether another person joins | Above the shuffle threshold | Prediction held |
| Largest group holds over half and has highest target share | Only component 3 could be reported; it was not the largest | ○ Undecided |
| A group under a tenth has falling target share and is nearest the largest | Component 3 met the size and direction conditions only; the other components cannot be scored | ○ Undecided |
| Joined laughs have less voicing and higher pitch | No joined-versus-unjoined interval was returned | ○ Undecided |
| Categories versus a continuum | Within-component slopes are descriptive and available for one component | ○ Left open by design |


Janin et al. (2003), *The ICSI Meeting Corpus*, CC BY 4.0. One official transcript per meeting supplied 12,633 laughter marks across 75 meetings. Of these, 4,213 marks occurred in 3,778 mixed utterances. Among 8,420 laughter-only utterances, two lacked an actor or time, seven lacked an unambiguous microphone and three fell outside the usable signal. Measurement covered 8,408 intervals on the qualified channel inventory (467 verified channels). All six features were available on 8,275. The anonymous mixed-mark shares cover 54 speakers with marked laughter; seven others had no marks. See the [source census](ICSI_SOURCE_AND_OPEN_BINDINGS_20261122.md).

Duration is annotated utterance length. The other measures were bursts, voiced fraction, median pitch relative to the speaker’s own speech in that recording, pitch spread and relative sound level. Pitch used voiced frames. Voiced fraction divided voiced frames by active frames, including unvoiced sound. On 40 ms frames stepped every 10 ms, activity required RMS of at least 1% of the interval’s largest frame RMS, with an absolute floor of 10⁻¹². Speaker reference pitch stayed inside the job.

The fixed split allocated 4,138 laughs to fitting and 4,137 to testing. Both fits chose six Gaussian components by BIC among one to six. On the held-out half the two assignments had adjusted Rand agreement of 0.851. The registered midpoint-density rule merged the components into one. In the constructed checks this rule could also merge distinct but nearby groups. The group comparisons below use assignments from the training fit.

| Held-out fact (52 contributing people per row) | Variation explained | 95th percentile of 200 fact shuffles |
|---|---:|---:|
| Laugher speaking at onset | 1.737% | 0.261% |
| Another person joined within 1 s | 4.315% | 0.248% |
| Change in target’s share of talk | 0.201% | 0.611% |

The comparison used a shuffle among laughs. No effect interval was returned. Laughs from the same speaker or meeting can occur on both sides of the split. Across components, the single-target change in share of talk fell below its shuffle threshold. For this measure BG requires exactly one other candidate; speaking time is the target’s divided by everyone’s total speaking time in each complete minute, excluding silence.

Component 3 accounted for 4.21% of held-out laughs (34 people). Among its reportable single-target events, mean share went from 42.29% to 34.13% (21 people). This component was neither the largest nor its nearest neighbour. The reported overlap cell counted 3,408 held-out laughs with another person speaking at onset (52 people). It describes speech on another microphone; the sampling exclusion concerns mixed content in the laugher’s own annotated utterance. The within-group table gives descriptive slopes of −0.0171 for speaking, +0.0188 for joining and −0.0287 for target change on the first acoustic axis in component 3. These slopes have no reported intervals. Partner ratings belong to the separate sealed source.

The held-out association meets one registered condition. The largest-group and rare-neighbour conditions remain undecided, so this source cannot select a reward group for LGH2. The measurements allow both regions of a continuum and distinct kinds. A verified fresh process reproduced the seven aggregate CSVs. The anonymous speaker-share table matches the independent census in every row; its two serializations differ only in line endings. The original channel-parser stop cost 2.0625 CPU-seconds. The repaired run including replay cost 5,169.125, for 5,171.1875 CPU-seconds in total on this ICSI study.

Laughter that overlaps speech is not in the sample, and that may be a kind of its own.

[facts](LGH1_ICSI_ACOUSTICS_facts.csv) · [mixture](LGH1_ICSI_ACOUSTICS_mixture.csv) · [fractions](LGH1_ICSI_ACOUSTICS_fractions.csv) · [target minutes](LGH1_ICSI_ACOUSTICS_target_minutes.csv) · [overlap](LGH1_ICSI_ACOUSTICS_overlap.csv) · [within groups](LGH1_ICSI_ACOUSTICS_within_groups.csv) · [Figure](LGH1_ICSI_ACOUSTICS.png) · [Prediction sheet](LGH1_ICSI_ACOUSTICS_SHEET.md).
