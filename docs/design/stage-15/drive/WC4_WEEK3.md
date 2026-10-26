# WC4: repeatability of what varies least

This freezes the routine implementation choices for the October25 packet's WC4,
before corpus extraction or comparison. Built is not dispatched or measured.
All source, actual-model validation, pilot, main and fresh-verification costs
share the original3,600CPU-second ceiling. The owner admits each native plan.

**DESIGN CHECK.** LESSONS3–5, CONTROLS and the packet's reliability defaults were
read on October25. Exchangeable labels should have no real-minus-reference
advantage. Repeated writer-specific variance patterns should increase agreement;
opposite patterns should reverse it. Flat population-average profiles have no
between-writer variation and are unsupported. Missing opportunities are missing, never
zero. An absent variance denominator is unsupported, not a negative result.

## Complete source and properties

The source handler `week3_stability_inputs` retains all1,399 canonical sessions.
It authenticates PMAP's complete source joins and WB1's fully verified event
preparation, and independently replays the repaired canonical accepted-span
provenance. The original logged selection index is never an option identity.
The source pilot uses the fixed first140 sorted session identities for cost
only. Its output cannot enter the scientific consumer.

| Property | Frozen measurement per session |
|---|---|
| Sentence length | Mean letter-bearing tokens per nonempty sentence of the final reconstructed document |
| Words per burst | Mean completed P6 typed-word onsets assigned to each WB1 typing burst by its raw source ordinals, including zero-word bursts |
| Pause before a sentence | Mean positive WB1 sentence/paragraph-onset interval; both endpoints are eligible single-character writer insertions and intervals touching suggestions are excluded upstream |
| Acceptance rate | Canonical accept-or-edit menus divided by fully observed canonical menus; censored unresolved menus are counted separately |
| Edit-after-accept rate | Canonical edit menus divided by canonical accept-or-edit menus |
| Retained share | Original canonical accepted Unicode characters surviving at session end divided by all original accepted characters; later typed replacements are not retained originals |
| Lexical density | Final-document letter-bearing tokens tagged NOUN, PROPN, VERB, ADJ or ADV divided by all letter-bearing tokens |
| Punctuation rate | Final-document Unicode-punctuation tokens divided by word-plus-punctuation tokens |

Artifact properties describe the complete final document, including surviving
prompt and model material. They are not a human-only writing channel. Process
properties describe logged production events, not physical keypresses. A word
crossing several typing bursts belongs to the burst containing its first
produced ordinal. P6 includes typed words later deleted. Sentence/paragraph
onset pauses retain WB1's exact source filters, with exclusions in that receipt.

The locally installed `en_core_web_sm`3.8.0 supplies POS tags. The complete model
directory and package versions are hashed before launch. Parser, entity reader
and lemmatizer are disabled; spaCy's deterministic sentencizer supplies sentence
boundaries. A separate actual-model smoke gate checks two simple constructed
sentences, repeat inference and fresh-process reproduction. Constructed source
annotations are an explicit test-only path and cannot enter corpus plans.

## Frozen split, profile and primary

The packet's at-least50-events threshold is interpreted literally as raw logged
events, including initialization and system/hover entries. Every below-threshold
or missing-property session remains in the source census. The comparison uses
eligible sessions with all eight measured properties; its exclusions and share
are explicit. A writer needs at least two such sessions in each half to estimate
all eight variances. A minimum of three supported writers is required. This is
a measurement-supported population, not evidence about writers with no acceptance
opportunity or no measured sentence-onset interval.

Whole prompts alternate between halves in order of each writer's earliest
eligible session timestamp, with prompt identity breaking ties. That mapping is
frozen before permutation. No prompt or session appears in both halves for a
writer. Prompt adjustment subtracts the session-weighted mean of each property
within prompt over all eligible sessions. The adjustment reads no writer label.

For each writer, half and property, compute the sample variance of those
prompt-adjusted session values. Divide by the equal-writer average sample
variance for that property in that half. An average of zero prevents inference;
the eight-property question is not silently reduced. The resulting ratio is1
for the population average and less than1 for a relatively steady property.

For each of the eight properties, compute its Pearson split-half correlation
across the supported writers' variance ratios. The primary is the unweighted
mean of those eight correlations. This measures whether writers retain their
relative variability on the same dimensions; it is not a correlation of raw
session means or an identification score. No unsupported property is dropped.
For floating-point degeneracy, a population variance at most1e-24 is unsupported
and a product of centered vector norms at most1e-20 is unsupported. These
constants are fixed before corpus work; neither rescales or drops a property.

Shuffle complete writer labels across eligible sessions within each prompt
1,000times, seed20261026. Rebuild every writer variance, population denominator,
ratio and agreement. The frozen recipient writer/prompt mapping and within-prompt
label counts preserve all admitted support. Sessions belonging to writers lacking
their own estimable profile remain in the assignment bank and prompt adjustment.
The reference is computed on the identical supported writer set every time.

Report real agreement, its real-writer interval, permutation mean/SD/95% band
and one-sided descriptive p. Subtract mean permutation reliability from real
reliability; 2,000paired real-writer resamples rebuild all eight nonlinear
correlations in the real arm and every reference arm, giving the contrast
interval. Retaining each half's population scales in resamples is algebraically
exact because Pearson correlation cancels column scaling. Non-estimable
resamples make the interval unsupported; none are silently discarded.
The inherited quarter-SD zero-centering flag is retained
for this reliability reference. A flagged reference is descriptive only.
Otherwise an interval above zero and p<.05 supports positive repeatability;
an interval below zero is negative, and remaining bands are not detected with
sensitivity unquantified. No unmeasured useful-effect sensitivity is claimed.

## Gates, replay and limits

The source and comparison each run through the common execute/verify interface.
Fresh verification reopens original source bindings and repeats all calculations;
saved profile scores never stand in for the reference reconstruction. The analysis
cost pilot uses100full reference rebuilds and no scientific output. Its conservative
projection charges ten times the entire pilot calculation, twice for fresh replay;
the owner also adds all source/native/pilot charges before main admission.

Known-answer fixtures cover exact positive, exact reversal, orthogonal zero-effect
profiles and flat profiles with no estimable correlation,
prompt-shift invariance, label-support preservation, opportunity denominators,
actual POS-model loading, complete serialization/reentry, fresh native verification
and mutation refusal. Vectorized paired resampling is checked against literal
nonlinear correlation rebuilds, including a degenerate draw. Failures and model
smoke remain distinct from corpus results.

The initial unfrozen draft used within-writer profile cosine. Its null and reverse
known-answer references developed a nonzero offset and failed the control. That
draft never ran on the corpus; the conventional across-writer reliability above
replaces it before freeze. The failed constructed receipt is retained privately.

Even a positive result identifies repeatable observed variability only. Habit,
constraint and absence of disturbance remain rivals; no open-loop variability or
controlled goal is measured. Ghost's W2 provides the separate known-construction
warning requested by the packet. Its findings cannot be transferred as a numerical
correction without a justified cross-system correspondence.
