# WC2: failed means, retained direction

Commission: Week 3 packet section 2.4, rank 5. Shared ceiling: 2 CPU-hours,
including source preparation, feature pilot, main execution and fresh replay.
Only the owner dispatches. These modules do not change live cards, claims or
theory. The current build has no corpus result.

## Source and support

`week3_outcome_blocks_inputs` reads the completed PMAP recovery's authenticated
P2/P6/raw/canonical sources. Every original accepted character is an immutable
Unicode codepoint atom. User deletion crosses 80% once per original span.
The actual inserted text must match the unique canonical selected option;
the recorded selection index never selects the target. The original and rebuilt
failure counts are retained. Partial spans, noncanonical origins and incomplete
windows are explicit census entries. No source session is silently removed.

The full input pass covers all 1,399 sessions. A separate pilot uses the first
140 sorted IDs and is never an admissible source for the full comparison.
The source pipeline reports both complete windows and complete windows with
the required other-writer reference. The primary needs 150 such events and
25 writers. Below either threshold it is unsupported, not null.

The next 50 produced typed words use P6's production occurrences, including
later-deleted occurrences. Order is onset ordinal then original occurrence
index. A word whose onset precedes the deletion is excluded even if completed
later. The primary starts at the first subsequent P6 sentence-start word;
the deletion-onset sensitivity starts immediately after the deletion. P6's
sentence flag reflects the contemporaneous document, including punctuation;
it is not a sentence boundary guessed from final surviving text. Words are
joined by spaces for the semantic and phrase comparison. The construct is a
production-word window, not a final contiguous passage or a keypress measure.

## Frozen implementation choices

- A window's relative position is its first produced word index divided by
  the session's complete produced-word count. For each other writer on the
  same prompt, choose the complete sentence-start window nearest this position,
  with session ID then onset ordinal breaking exact ties. Average donors with
  equal writer weights. Donor counts and distances remain inspectable.
- A kept reference retains at least 80% of its original characters at session
  end. Select one same-writer accepted-and-kept span with a complete sentence
  window and context, with replacement, nearest in squared relative-position
  difference plus squared log word-length ratio. The packet specifies position
  and length matching without a caliper; no new exclusion caliper is introduced.
  Each match and distance is retained. Missing kept references do not discard
  primary events; the paired persistence ratio has its own explicit population.
- Embedding advantage is chosen-span cosine minus the arithmetic mean cosine
  to all unchosen same-menu options. Own and donor windows use the same ruler.
  MiniLM is the completed content pass's local, hash-locked all-MiniLM-L6-v2,
  CPU float32, first 254 native tokens with CLS/SEP and mean pooling then
  L2 normalization. Full visible-token receipts are saved. No download or GPU.
- Primary aggregation is an equal-event mean within each writer followed by
  an equal-writer mean. Its 95% interval resamples writers 2,000 times.
  The wording contrast combines bigram and trigram occurrence shares; repeated
  occurrences count, and the denominator is all window bigram/trigram positions.
  The wording interval is 90%. Content-word overlap is descriptive only.
  The fixed function-word sequence secondary filters to the explicit source-code
  lexicon before measuring the same phrase overlap; it cannot alter routing.
- Before own contrasts, freeze the band from external-context phrase values:
  one event-averaged value per tested writer; band is 0.25 between-writer SD.
  The reachability projection is `1.6448536269514722 * SD / sqrt(writers)`
  using that same context-only spread. If larger, it replaces the original
  band, with both values and the reason retained. Own outcomes never widen it.
- Exact route boundaries: embedding CI including zero is no direction; wholly
  below zero moves away; wholly above zero uses the phrase interval. Entirely
  inside the closed equivalence band is same end/new means; lower bound strictly
  above the band is lingering taste; all other positive cases are unresolved.
- The kept denominator must have 95% lower bound at least 0.01 cosine. Numerator
  and denominator use the same event pairs and writer roster. Ratios are
  unresolved if any paired bootstrap denominator is nonpositive.
- Each writer's descriptive persist/drop rate uses the sign of the event's
  own-minus-context embedding advantage. Reliability uses whole prompt halves,
  at least four sessions and two prompts, and 1,000 within-prompt writer-label
  permutations on the fixed eligible roster. Unsupported or zero-variance
  halves remain explicit; invalid draws are not discarded or replaced.
  The 200 eventwise own/context swaps within writer are a separate diagnostic
  exchangeability reference. They are not a causal randomization test.

## Runnable chain and verification

1. `week3_outcome_blocks_inputs`: constructed/native fixture, 140-session cost
   pilot, then separate full source pass if cumulatively admitted. Counts only.
2. `week3_failed_means_features`: same full source population; separate first-tenth
   unique-text pilot, then full features if total projection fits the shared cap.
   Only selected deleted events and their matched kept references are encoded.
3. `week3_failed_means`: all frozen contrasts, diagnostics and writer records,
   with a fresh full statistic replay. A pilot or constructed feature completion
   cannot be consumed as a corpus feature set.

Every module has `execute(output, inputs, config)` and `verify(output, inputs,
config)`. Reentry checks saved content; verification reconstructs its complete
assigned stage. Source records, private texts, word indices, model scopes,
writer means and raw reference draws remain private. Owner writes the public
claim ledger only after complete validation and the required landing.

Known-answer tests cover zero signal, pure shared-topic signal, retained semantic
direction with new wording, lingering wording, reversed direction, exact route
boundaries, UTF-16 surrogate atoms, 80% equality, wrong logged choices, source and
output corruption, complete-window support, matched populations, and two-entry
native handler contracts. The first topic fixture initially gave only its donor
the planted topic; its expected cancellation was invalid. It was corrected to
plant the same topic in both arms; the estimator was unchanged.
