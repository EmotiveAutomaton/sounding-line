# Week 5 laughter: LA0, LA1 and LA2

Prospective design, 2026-11-07. Packet authority: [Week 5](PACKET.md).
CPU-only Gear 2; no audio download, GPU, paid service or participant lookup.
Family ceiling 450,000 CPU seconds; LA1 300,000; LA2 20,000. A ceiling is not
a runtime request. Source, timing, full analysis and fresh verification all
count under the same family. The first 5% in-slot pilot is required whenever
the initial cost projection exceeds 7,200 CPU seconds.

## DESIGN CHECK

Read method LESSONS sections 3–5 and CONTROLS sections 1–6, November 7.
The meaning claim is tested by conditional association in observed meetings;
neither laughter nor pseudo-likelihood identifies understanding by definition.
Resolution is scored on identical old tokens before and after the current act.
Signed planted conditional worlds, exact balanced nulls, collinearity refusal,
literal lexical “laugh” versus annotation marks, and timing-boundary fixtures
make both directions and failures reachable. These controls are construction
checks, not human evidence. Raw text, IDs, per-act scores and metadata remain
in ignored storage. Primary results wait for full uncertainty and write-through.

## Source and provenance

The exact packet URLs were fetched once. `week5_la_intake` enforces an allowlist,
256 MiB archive ceiling, 50 GiB free disk, ZIP CRC, traversal/symlink rejection,
and 2 GiB expanded size limit. Actual archive SHA-256 values are frozen in
`week5_la_source.PINS`; raw archives and `SOURCE.md` stay private.
AMI URL advertises 1.6.2, while its packaged README identifies release 1.7,
June 16, 2014. Both facts are retained; actual bytes, rather than a guessed
version, define the source. AMI and ICSI packaged licences are CC BY 4.0;
acknowledge their corpus creators and cite their corpus papers in the landing.
ICSI-plus includes the core transcript layers. It is pinned and retained but
not concatenated into a duplicate population.

LA0 reads AMI timed word streams, vocal `laugh` events and dialogue-act pointer
ranges, and ICSI words, vocal descriptions containing `laugh`, and dialogue acts.
NXT ranges follow document order. XML IDs never become URLs or queries. A single
existing campaign HMAC salt replaces all meeting, speaker and act identities.
All vocal, comment, nonvocal, disfluency and gap annotations are removed from
scoring text and word counts; literal spoken words such as “laugh” remain words.
ICSI “while laughing” comments are removed from text and retained separately
for a broader-label texture. Primary outcomes use vocal marks. Explicit laugh
times are preferred; missing times are bounded by the immediately adjacent
timed lexical words. Unbounded/reversed times are unsupported and counted.
Acts without interpretable pointers, type, lexical words or bounds are counted
and excluded. Source verification reparses every retained record independently.

AMI supplies native-language metadata. ICSI supplies varieties of English and
regions, not a declaration of native language or nationality. LA2 therefore
labels these as different constructs and reports corpus-specific contrasts;
it will not call ICSI English variety a native language. Unknown metadata is
excluded and counted. No demographic proxy is invented.

## LA1: retrospective resolution

An act is a case if a vocal laugh intersects the last one second of the act
or the two seconds after its end. Laughter within that window is an outcome
only. Match each case to at most five noncase acts in the same meeting,
speaker and act type, with length difference at most max(2 words, 20% of case
length); order candidates by length difference, onset and salted ID. Matching
never reads model scores. Record every unmatched case.

The causal-model surprise is supplied by AT2's prospectively selected best
final-context reader; a partial AT2 bank does not release this dependency.
Use the preceding dialogue text as causal context. For distilroberta-base,
score every token of the preceding five acts by masking it alone, before and
after appending the current act. Hold the identical old-token IDs in both
arms and use the same left crop to fit 512 tokens; count dropped support.
Resolution is the mean after-minus-before log probability of those old tokens.
Mask batches are bounded and CPU-only; pin tokenizer/model/package manifests.

Fit matched conditional logistic regression of case versus controls on
resolution and surprise, both standardized using the retained matched bank.
Primary: resolution log odds per SD, practical bar log(1.10). Repeat the full
conditional fit in 2,000 meeting-cluster resamples. Retain singular or failed
draws as invalid; never select only successful draws. At fewer than twenty
meetings, report a pooled descriptive fallback with its dependence limitation.
Two hundred draws screen secondary textures; they cannot replace primary
uncertainty. Full refit verification must reproduce every aggregate.

Textures: aftermath windows 1, 3 and symmetric ±5 seconds; preceding-act counts
3 and 10; AMI and ICSI separately; others' laughter only. If resolution clears,
separate own versus others' laughter. If only surprise clears, test whether
next-act surprise falls. No branch is silently promoted to primary.

## LA2: joining

For each labelled participant pair within a meeting, calculate the symmetric
mean fraction of each speaker's laugh onsets within one second of the other's.
Pairs with no source laugh for a member have undefined event fractions and are
counted as unsupported, not manufactured zeros. Contrast same versus different
background within meetings, adjusting for both individual laugh rates. Use
2,000 meeting-cluster refits and bar 0.02. A lack of within-meeting background
contrast is unsupported, not a negative result. AMI native language is primary;
ICSI English variety and region remain explicitly separate descriptive tests.

## Execution

Source adapter `week5_la_source.execute/verify`: exact inputs `archive_root`
and `identity_salt`, empty config; peak reservation 3 GiB. It performs no
scientific model fit. `week5_la.execute/verify` consumes frozen, fully scored
private rows. Long score banks checkpoint at act blocks, include cold-load and
fresh verification cost, and yield within the native quantum. A job cannot
be admitted merely because a design or function exists: the complete selected
model receipt, controls, cost pilot and resource guards must all pass first.
