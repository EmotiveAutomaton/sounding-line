# AT numerical precision successor

This engineering correction supersedes only the float32 computation choice in
`AT.md` for newly admitted score banks. The original runs, pins, failed fresh
checks and CPU charges remain evidence. Source rows, model weights/revisions,
tokenization, context caps, word overlap, cached-prefix clock, entropy and
surprisal definitions, sampling, estimators and practical bars are unchanged.

## Failure and correction

The original Pythia cached computations reproduce their saved values exactly.
Fresh full-prefix evaluation nevertheless differs beyond the fixed 0.0001-nat
gate on multiple model sizes and chunks. Tokens and cropping match. Changing
attention to eager evaluation did not fix the retained failing case.

Scoring v4 loads the exact pinned float32 tensors and converts them to float64
before inference. The original float32 logits-to-log-softmax and entropy
reductions remain explicit. Every model in a comparison bank uses this same
choice. The immutable `AT-FP64-1` specification enters both the complete row
binding and summary. The fresh-forward tolerance remains 0.0001 nats. No failed
model or source row is omitted. Collector v3 refuses old handlers, absent or
different numerical specifications and mixed model revisions/context lengths.
Even previously accepted float32 chunks cannot join a float64 bank.

## Cost and resources

This candidate requires new cost admission. Double precision changes both the
model memory footprint and runtime. Account original failed attempts, failed
eager diagnosis, all precision controls, cold loading, execution and independent
verification. Use measured per-model peak working sets and complete-chunk CPU
costs; do not extrapolate only a successful token or discount fresh verification.
The largest model's weights alone require approximately 11.2 GB in float64;
admission must add activations, loading/conversion overlap and runtime memory.
Do not start a whole bank until the native controls and updated 5% pilot route
are reviewed. The full model bank and source scope are preserved. The packet's
sample/doubling and continuation rules still govern cost rather than a favorable
model subset or a relaxed numerical gate.

## DESIGN CHECK

Known-answer native controls cover GPT2, GPTNeoX, Llama and Qwen2, with prefix
extension, shortening, divergence and context rollover. All constructed token
losses and entropies are independently reconstructed from uncached logits;
resource yield and resume are exercised. Collector controls reject mixed
precision and revisions. The actual retained failed chunks are replayed in
their entirety by `week5_at_precision_case`, with the original seeded 2%
fresh-forward checks and preserved original failure hashes. Their private
receipts report native execute and separate fresh-process verify costs and peak
working sets. No scientific comparison, selected reader or completed pilot is
licensed by these engineering controls alone.
