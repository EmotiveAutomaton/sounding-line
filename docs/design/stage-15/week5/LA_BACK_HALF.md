# LA3–LA4: repetition and the social layer, November 11

Prospective builder delivery under PACKET_BACK_HALF.md. Not admitted or
committed by this document. Original LA modules, inputs and receipts remain
immutable. This extension uses no reader language model, selected AT reader,
GPU, paid service or new participant data. It reads the qualified LA0 source
and the already pinned AMI/ICSI annotation archives.

## DESIGN CHECK

Read LESSONS §§3–5, the original LA design and source/matching code, the new
packet, the November 11 theory handoff, G264 and its afterword/corrections.
The contrast can fail in either direction. A planted +0.35 log-pause contrast
must recover positively, its reversed counterpart negatively, and exact zero
must remain in the null band. The ordinary against/support/inconclusive bands
are exhaustive; no unresolved interval is called absence. A broad interval
reports the sensitivity it actually has. Whole-meeting bootstrap dependence
is preserved even when persons attend multiple meetings.

Fixed-effect calculations have direct dense dummy-regression oracles. Under
an event-level starter property, the required laugh fixed effect removes the
property exactly; the program must not invent a standalone starter coefficient.
Shared background varies across possible joiners within laughs and across
starters within person-meeting units, so it can survive those effects, but
only where the source supplies that variation. No identifiable residual
variation means design cannot test. Role and situational coefficients are
empirical scale reports rather than independent theory claims.

Constructed actual-handler fixtures cover pause timing, lexical order, exact
30-second boundaries, distinct content lemmas, ambiguous simultaneous starters,
one-second joins, all three signed cases, full replay and immutable continuation.
The actual metadata ZIP adapter is tested with constructed XML of the packaged
schema. Missing chronology, missing labels, changed source and changed saved
blocks refuse or retain explicit unsupported states. No successful-only draw
collection or redraw is permitted.

## Source extension and limits

Use `week5_la_back_half_source` as the first source stage of the applicable
card. It reads exact qualified ACTS, LAUGHS and METADATA files, with hashes in
the reviewed plan, and the three original `week5_la_source.PINS` archives.
The existing 32-byte campaign salt preserves meeting and local speaker keys;
new global-person and group keys use distinct HMAC namespaces. No raw identity,
text, per-act record or private group map enters aggregate output or commits.
AMI/ICSI CC BY 4.0 attribution and the original release qualifications remain.

AMI `corpusResources/meetings.xml` supplies scenario status, date, start time,
speaker role and global participant. Scenario suffixes a–d define the four
ordered phases; other AMI meetings are single groups. Date formats are the
packaged day-month-four/two-digit-year formats. ICSI dialogue-act participant
attributes link word streams to global people; original English variety and
region remain distinct constructs. Unknown roles are not guessed.

The extension also reads every lexical word's explicit timing from the same
pinned AMI and ICSI-core word XML, including words outside supported dialogue
acts. SPEECH.json.gz contains salted meeting/speaker keys and start/end only,
with no word text. It supplies pause and recent-speech histories. Untimed or
reversed word intervals are counted and not fabricated; the result therefore
measures observed timed speech. ICSI-plus remains a duplicate, not another
population. Constructed XML and unannotated-word fixtures cover this adapter.

AMI dates are source-local calendar coordinates, not asserted UTC. Where a
start clock is missing, its interval spans the recorded day. Across meetings,
a repeat is accepted only if the lower bound of its separation clears the
declared exclusion. If the bounded unknown clock could change repeat versus
middle, the act is timing-unsupported and counted. A distinct earlier phase
does not by itself prove a thirty-second separation. Same-meeting gaps are
exact. Fresh/no-shared-content and confirmed repeats remain usable when
their categories do not depend on the missing clock.

The pinned ICSI metadata and timed words provide no meeting dates. Its letter
prefix identifies a series, but its numeric suffix is retained only as a
source label, not asserted to prove chronology. ICSI cross-meeting repetition
and prior co-attendance therefore remain source-held until a reviewed, pinned
ordering map cites documentary provenance. The full LA3 combined-corpus
primary retains that dependency; the commissioned AMI-only texture can run
independently. LA4's AMI primary and ICSI variety/region terms do not depend on
chronology. A supplied order map enables the actual co-attendance consumer;
there is no zero placeholder. Missing global-person identities are counted.

Lemmas use the installed `en_core_web_sm` 3.8.0 linguistic tagger/lemmatizer,
with parser/NER disabled and original corpus word boundaries preserved. This
is not the LA1 reader-model arm. Its complete resource manifest is pinned.
Loading is owner-admitted only; a built-in constructed “children were running”
check must return “child be run” before corpus processing. Builder tests use a
deterministic lemma substitute and do not load the real resource. The first
source stage measures its actual load/processing resource use under native
accounting; the old feature catalog does not supply a human-card forecast.

Alphabetic, case-folded lemmas are counted over qualified act words. For each
corpus separately, remove its 200 most frequent lemmas, breaking frequency
ties alphabetically. No lexical word “laugh” is removed merely for spelling;
annotation marks remain excluded by the original source. Lemma blocks of 64
acts are immutable and resumable. Corpus stop lists are fixed from all
qualified act words before repetition outcomes are computed. Empty content
sets satisfy the literal no-shared-content fresh rule and are separately
counted so this limitation is visible.

## LA3

The original LA0 window is end−1 through end+2 seconds, using vocal laughter
from someone other than the act's speaker. Source label timing and all original
word exclusions remain unchanged. Within the frozen group and documented
meeting order, repeat requires two distinct content lemmas in common
subsequence order with one prior laughed-after act whose end is at least
30 seconds earlier. Fresh shares none with any earlier laughed act, including
ones too recent to qualify a repeat. Intermediate and time-unsupported cases
are counted and set aside. Earlier meeting phases precede later phases but
do not supply an invented gap. Simultaneous act starts are not ordered by ID.
The control history is the corresponding
nonlaughed-act history, explicitly an analogous general-repetition diagnostic.

Pause is max(0, current start − latest preceding speech end) using anyone's
timed lexical speech. Overlap produces zero. The source-start boundary and
no-prior-laugh boundary are marked rather than pretending pre-observation
history was observed. Log pause is log(1+seconds). Fit fresh versus repeat
with global-speaker fixed effects, log(1+act word count), act-type indicators,
corpus, minutes into the meeting, previous-speaker-same, log(1+time since
the last laugh ended), and boundary indicators. Ongoing earlier laughter has
zero recency. Absorbed nuisance columns are allowed; an absorbed target is not.
Speaker effects are re-estimated under each draw's meeting multiplicities.

The primary is fresh minus repeat. Shuffle fresh/repeat labels within source
speaker and meeting 20 times. Freeze the working bar before inference as
max(0.10, 2*mean(abs(null contrast)) + 3*sample-SD(null contrast)). A failed
null fit makes the primary untestable, not an omitted permutation.

Case: at least 200 repeat acts spanning 30 meetings. Otherwise rerun the
declared two-distinct-lemmas/any-order/10-second fallback and label every
interpretation below-floor descriptive. Retain original case counts. Default
support floor for other estimates is 20 independent meetings; one meeting
has no population interval.

Controls use LA1's exact same-meeting/speaker/act-type rule, length difference
at most max(2,20% of case length), and the deterministic closest five. Each
matched case has weight one; its eligible controls total weight one. Repeat
controls may appear in multiple sets as in LA1, with complete meeting clusters
preserving that dependence. Secondary estimates are the control fresh-minus-
repeat contrast, primary minus control contrast on shared meeting draws,
fresh laughed acts versus matched fresh nonlaughed acts, and the difference
in act-initial “um”/“uh” rate, with the fresh and repeat rates also reported.
These are descriptive estimates, without additional theory verdicts or an
invented rate-scale bar. Eligible fresh/repeat cases and controls are frozen
before applying the exact matching rule. The fresh-case contrast makes the quick-wit
selection rival visible; a null primary cannot separate no attention cost
from slow jokes failing to get a laugh.

Texture configurations: prior-act separation 5 and 120 seconds, three shared
lemmas, the separate exclusion of acts within 5 seconds of a preceding laugh,
AMI and ICSI individually, and the previous-speaker-same own-gap subset.
These are separate 200-draw textures under the one 40,000 CPU-second card
ceiling. A texture retains its specified separation/lemma rule when below
the case floor, with descriptive status; it does not silently become the
primary's fallback. The original primary remains fixed. Theory tag H12-T4.

## LA4

A bout starter has an onset after at least three observed seconds without
any laugh, using prior laugh ends. Exclude and count simultaneous distinct
starters rather than assigning an arbitrary identity. Every other member of
the meeting's source roster is a possible joiner; joining is an onset in
the next one second, inclusive. Entry/exit times are not observed, and the
nominal meeting-roster interpretation of “present” is disclosed.

The linear probability model includes a laugh fixed effect and a person-within-
meeting fixed effect. Situational terms are the joiner's authorship of the
latest ended act, speech overlapping the preceding ten seconds, and her laugh
onsets in the preceding sixty seconds. Tied latest acts retain their speakers
as a set. No target or later observation enters those history terms.

The AMI shared-native-language coefficient is the sole primary, bar 0.02.
ICSI shared English variety and shared region are separate secondary
constructs. Documented chronology enables log(1+earlier corpus meetings
attended by both global people), with strict earlier timestamps and no
current/future meeting contribution. That secondary stays held if any
required date or identity is missing.

The starter-spoke-line main effect is constant within each laugh and is
explicitly non-identifiable under the mandatory fixed effect. Owner review
authorized frozen descriptive background slopes split by whether the starter
spoke the preceding line; these do not replace the primary. Role-based AMI
models replace person effects, with and without situational terms, reporting
their coefficients and within-laugh R-squared for scale. Missing roles are
counted. No empirical scale coefficient is labeled mechanically true.

Twenty label permutations within each meeting's known-label participants
are reported for AMI language and each ICSI construct, preserving missing
positions and participant roster. The primary bar remains 0.02; LA4's packet
does not commission a null-derived replacement bar. Background fits absorb
the two fixed effects per meeting exactly; whole-meeting multiplicities do
not change that projection. The finite nuisance regression is refitted in
each draw. AMI and ICSI meetings are resampled separately, pairing all variants
within their corpus. Two- and three-second joining windows are 200-draw
textures. Ceiling 30,000 CPU-seconds. Theory tag H12-T5.

## Continuation, reporting and owner gates

Seed 20261107, deterministic global draw indices, canonical ordering. Main
and claim-bearing intervals use 2,000 resamples; textures use 200. Every
estimate saves the percentile interval and bootstrap SE. Where a bar is
specified it also saves sees=2.8*SE and supports_at=bar+2.8*SE, with the required
limited-sensitivity line when sees exceeds the bar. Secondary scale terms
without a commissioned bar retain supports_at=null and no theory verdict.
No additional sensitivity campaign is created. Public
claim/texture/run tags and theory tags remain distinct; interim scores are
not emitted to the curator.

Inference seals blocks of sixteen draws, checks resource requests at block
boundaries, and independently reconstructs all products for verification.
Metadata, temporal-feature, indexed-history, joining-table and fixed-effect
preparation also check resource requests at bounded record/meeting boundaries;
they do not depend on preprocessing finishing within a guard's grace period.
The shared-lemma index has an exhaustive-history equivalence fixture and
changes neither category nor time support.
The first completed block supplies the in-run cost probe; resource/whole-card
forecasts remain unmeasured until actual source/counting evidence is obtained.
Owner review, committed design, existing source qualification, current runtime
closure, resource envelope, remaining family ceiling and complete fixture
evidence precede admission. No separate native qualification campaign is
requested under amendment Q. Full write-through and ACKs belong to the owner.

IN8 was checked separately: `data/external/isear/` is absent at this build.
It waits on the source and curator terms note and holds no worker slot.
