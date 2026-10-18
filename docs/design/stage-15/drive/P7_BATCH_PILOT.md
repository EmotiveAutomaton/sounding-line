# P7 causal batching: fixed-input engineering comparison

The completed [original execution pilot](P7_EXECUTION_PILOT.md) is frozen.
Its full-corpus estimate exceeds the allowance. This separate comparison tests
whether computation can be shared without changing any target or model score.
It implements the existing unconditional P7 commission, with no new science.

Use every one of the original pilot's 612 targets, authenticating its source
pins, completion hashes, raw-prefix reconstruction and model manifest. Preserve
CPU float32, two threads, evaluation mode, exact native tokenization and the
1,024-token left crop. Group consecutive targets only when their complete
cropped native-ID sequences are prefixes of one common sequence. A single
causally masked forward over that longest sequence supplies their original
positions. Revisions, changed tokenization and shifted windows split groups.
No future token may enter an earlier conditional distribution.

**DESIGN CHECK.** LESSONS 3–5 reread October 18. Under either a scientific null
or alternative, every saved original target loss must agree within absolute
0.0001 nats, with exact IDs and crop. A nonfinite/negative loss, changed source,
missing unit, damaged checkpoint or larger error refuses. Actual tiny-transformer
checks cover branch changes, shorter reentry, Unicode, token-boundary changes
and overflow, with deliberate mutations that must fail. Serialized yield/resume,
immutable completed reentry and actual counted-runtime fresh verification are
tested. Production verification reconstructs all native identities and every
comparison, plus fresh direct forwards for first/middle/last targets per domain.

Checkpoint complete domains with their binding and hashes. Yield at that saved
boundary; do not restart a saved domain. One counted CPU slot, below-normal,
600-second forecast, 1,800-second combined execute/verify wall cap and 256 MiB
output cap. Existing native monitor, source and resource gates remain in force.
No GPU, paid call, model download or automatic retry occurs.

The pilot reports cost and numerical agreement only. Domain-rate projection
excludes full source replay and final verification. The complete corpus has
different context-length and edit distributions, so this projection alone
cannot admit main even if it falls below the allowance. Next admission needs
actual corpus work-shape coverage, including cropped windows, measured bounds
and prior charges. D30.s gets no automatic ranked-card credit for this shared
instrument. D33 and D36 remain separate unfinished consumers.

Public output contains aggregate checks, timings and hashes only. Original
source text, token losses and participant identities remain private. Whole-pilot
write-through follows the active campaign policy before completion ACK.
