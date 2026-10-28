# P3c blind annotation criteria

DESIGN CHECK: LESSONS 2–5 read October 27. These criteria are fixed before the
operating agent opens the selected calibration pairs or any classifier predictions.
Under an uninformative binary prediction, chance-corrected agreement is expected
around zero; a useful instrument must reach the packet's unchanged 0.6 threshold.
Agreement with a constant reference is undefined, not a pass. An invalid input,
missing prediction or missing annotation refuses complete calibration. No class
is selected or removed after scoring. This is agent-reference validity, not human
ground truth or evidence of a writer's private intention.

The operating Codex agent labels all 200 frozen pairs from the blinded view.
Only before/after text and random aliases are shown, without writer/session,
origin, old classes, old embeddings or current model predictions. Labels and a
brief reason are frozen and hash-bound before classifier execution. The agent
is the annotator; these are explicitly agent-made labels, not curator judgments.

Assign the dominant observable edit category:

- **meaning-changed:** added, removed or altered substantive information,
  including negation, entities, quantities, claims, events or a complete content
  clause. Removing information counts, even without replacement.
- **fluency:** spelling, punctuation, spacing, grammatical inflection, or an
  unfinished token repaired/deleted without a recoverable new substantive claim.
- **clarity:** a more concise or explicit paraphrase preserving the recoverable
  content; removal of redundant wording without removing a distinct claim.
- **coherence:** connective/reference or organizational changes that primarily
  alter how preserved propositions are linked.
- **style:** tone, emphasis or voice changes without a substantive content change.

Meaning change takes precedence when a pair combines a substantive change with
surface repair. Otherwise use the primary visible operation, with fluency for
plain typing/backspacing mechanics. A partial token is not invented into a new
word or future claim; judge only what is visible. The labels describe visible
differences, not a claim to know why the writer made them. Record uncertainty
where a fragment admits more than one reading; still provide the best category
under these criteria for every frozen pair. Do not substitute clearer cases.

The primary gate collapses these five classes to meaning-changed versus the
other four, using ordinary Cohen kappa from the complete 2-by-2 table. Retain
the label marginals, uncertainty flags and full five-class table as context.
The fixed sample is event-uniform, not artificially class-balanced. No model
fine-tuning or threshold tuning is permitted. Pass/fail is recorded only after
the entire calibration and independent recomputation finish. A scientific or
agreement failure is never an engineering repair.

The publisher's model card supplies the five categories and paired tokenizer
interface. The operational fragment/tie rules above are analyst choices frozen
for this process-record application, not claims made by that paper.

Sources: [pinned model card](https://huggingface.co/wanyu/IteraTeR-ROBERTA-Intention-Classifier/blob/d9e6e6ee893e9f36cbba8047b838ccbfea1c1c32/README.md),
[official implementation](https://github.com/vipulraheja/iterater),
[repository license](https://github.com/vipulraheja/iterater/blob/main/LICENSE).
The official repository directly links this checkpoint and publishes Apache 2.0
terms. The Hugging Face card has no separate license field; that absence and the
exact retrieved notices must remain explicit in the intake receipt. No weights
or participant text are redistributed.
