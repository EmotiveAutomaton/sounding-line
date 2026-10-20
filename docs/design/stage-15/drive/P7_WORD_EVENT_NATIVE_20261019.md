# Native word-event diagnostic admission

The week packet commissions common word-event validation for scoped P7-D33.
This diagnostic exercises the existing implementation and exact frozen pilot;
it cannot admit the scientific comparison by itself.

DESIGN CHECK: LESSONS sections 3–5 read for this admission. Under both null and
alternative scientific outcomes, all original targets and the fixed native
sample are identical. Source changes, decoder disagreements, nonfinite losses,
canonical loss differences above 0.0001, missing targets or replay disagreements
refuse. Bounded enumerations explicitly retain incomplete status and context
overflows. Passing these checks establishes instrumentation only.

Keep all 612 original pilot targets. Count exact byte segmentations and Unicode
casefold aliases separately; retain nonword targets with their different event
definition. Select the first and last word of each original domain, four targets
total. Measure the canonical token path and at most 15 alternate exact-byte paths
for each, with the original visible token context and overlap retained. Do not
shorten context to accommodate an alternate path. Explicitly retain overflows.

Load the pinned GPT-2 medium model locally on CPU in float32, with two numerical
threads. Compare every nonspecial token's inverse byte mapping with the actual
native decoder. Compare canonical losses with the original completed pilot to
0.0001; reconstruct all structures and rescore every sampled path in a fresh
native process. Nineteen targeted constructed checks pass before dispatch.

The forecast is 300 wall seconds, including fresh replay. The cumulative original
ceiling is 900 seconds; charge the measured targeted test time plus 10 seconds
of launch overhead and a conservative 60-second allowance for the retained
earlier component tests whose receipt lacks a duration. No automatic doubling,
GPU, network model download, or paid computation is admitted. Use one counted
CPU slot, existing memory/disk floors, the demo reservation, native ownership
and immediate completion/failure monitoring. Preserve all source pins and outputs.

Exact byte-path counts are not complete word probabilities. Omitted aliases,
tokenizations, boundary-crossing tokens and start normalization remain unresolved.
The population reader's casefolded event and the writer-specific cache's unknown
event require a separate compatibility decision. No omitted mass is set to zero,
and diagnostic cost cannot establish algorithmic impossibility. Full-corpus P7
census remains superseded. This adds no research branch or scientific verdict.

Report the complete diagnostic and its limits in the instrument ledger and
operational records. Scientific admission remains false even on a clean pass.
