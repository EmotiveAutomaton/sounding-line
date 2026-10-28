# P3c CPU classifier execution and calibration

DESIGN CHECK: LESSONS 2–5 read for this P3c design on October 27; statistic and
model hazards reread before implementation. A random binary classifier has
chance-corrected agreement near zero; the useful instrument must reach the
packet's unchanged Cohen kappa of 0.6 against all two hundred frozen agent
labels. Constant reference, missing predictions and overlength selected pairs
do not pass. This is agent-reference agreement, not recovered human intention.

Use the exact downloaded checkpoint and tokenizer, revision
d9e6e6ee893e9f36cbba8047b838ccbfea1c1c32. Authenticate the full model inventory
and completed source receipts before loading. Local files only, no remote code,
weights-only loading, CPU float32, evaluation mode, eager attention, one
numerical thread, seed 20261026, and one before/after pair per forward call.
No model fitting, threshold selection, GPU or network access occurs.

First execute a native model check on four constructed pairs covering a surface
repair, numeric information change, Unicode and empty revised text. Repeat
each exact request and require identical labels and logits/probabilities within
relative tolerance 1e-5 and absolute tolerance 1e-6. Check actual CPU/precision,
evaluation state, checkpoint label ordering and finite outputs. This is a
numerical/interface check; no semantic accuracy claim follows from it. A long
constructed pair must be rejected before inference. Recompute all checks in a
separate native process. Targeted known-answer checks independently validate
the binary kappa table, exact pass boundary, missing/constant reference refusal,
the serialized source consumer, immutable replay and corruption rejection.

After that gate, authenticate every saved edit pair. Tokenize both complete
sentence windows without truncation and retain the full length census and every
overlength event. RoBERTa's limit is 512 paired tokens including separators.
The original 1,000 timing events and 200 blind calibration events must all fit;
otherwise record unsupported selected inputs without replacing or scoring them.
Overlength events outside those sets remain explicitly unresolved for later
population inference. Calibration cannot license their clipping or removal.

Time all first 1,000 events in their existing canonical order, then predict all
200 frozen calibration events in their existing order, including any overlap.
Keep individual logits and probabilities privately. Require repeat parity for
overlap. Compute the unchanged complete binary kappa and retain the five-class
table and label marginals. Independently reconstruct all source joins, token
counts and all 1,200 predictions in a fresh process before landing. No interim
agreement score or sample selection is reported. No p-value is introduced.

The native validation has a 180 CPU-second allowance including replay. Add a
120-second construction/test reserve to the recorded 218.0625 CPU seconds.
Calibration/timing is separately capped at 1,800 CPU seconds including replay,
under the original cumulative 14,400-second ceiling. The complete forecast and
token coverage determine whether all events or the packet's already frozen
random prefix can fit after all prior costs and independent verification.
Neither population labels nor downstream studies are admitted by this pilot.

A failed agreement gate is a result, not an engineering repair. Follow the
packet's second-labeler route only after its concrete transfer and spending
admission; this file makes no paid dispatch. Original attempts and all charges
remain recorded. No new follow-up generation is registered by this shared pass.
