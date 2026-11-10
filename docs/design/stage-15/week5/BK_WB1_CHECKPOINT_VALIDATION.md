# WB1 exact batch and pilot validation

This completes the untested paths listed in [the WB1 continuation design](BK_WB1.md).
It changes checkpoint granularity and measures the original work. No human
effect, candidate roster, window, random draw, model or threshold changes.
All historical attempts and charges remain; the validation itself is charged
to WB1 in the backlog family. No GPU, paid call or Ollama is used.

## DESIGN CHECK

**The case and its check.** A long original session can exceed the cooperative
yield grace. The new encoder preserves the original prompt call, sorted
context-text list, sixteen-text batch boundaries and partial final batch,
while sealing each batch's exact arrays and token scopes. Its native proof
compares these with the original pinned MiniLM on fifty constructed texts,
including first/last 254-token views, long inputs and Unicode. Execute and
independent verification both stop after one sealed batch and continue without
replacing it. Changed session identities and vector bytes must refuse.

Verification checkpoints are bound to the exact saved array bytes, original
source identity and verifier source. A separately copied fixture retains all
execute bytes while excluding earlier verification proofs, forcing fresh
model computations in the native verifier. Original verification receipts
and all costs remain. The fixture therefore tests fresh replay as well as
authenticated continuation; it does not treat an earlier in-process check as
proof of a later independent run.

The complete constructed raw/statistical fixture uses eight sessions and runs
the actual v2 encoding, all four 200-reference banks, 2,000 writer draws,
complete original cost/effects/class reducers and original-handler equality.
It adds the first ten global reference indices in each of the four banks,
which are exactly 5% of the full reference work. Discovery pilot values must
equal the corresponding complete-bank values. The test-side candidate superset
is only a work proxy, never the discovered scientific piece list.

`week5_bk_wb1_pilot_forecast` requires complete positive measured execution and
verification costs. Its full-coverage estimate is twice three times the slower
phase divided by 0.05. This deliberately scales the full-shaped bootstrap and
source overhead upward too. Prior attempts, source, effects work, imports and
runtime coordination are additional. No forecast automatically launches work.

**The smaller route.** The fixture is already a bounded constructed case;
there is no reduced draw count or smaller successful-case subset. Production
source/cost admission remains separate. A resource request pauses at a sealed
boundary and retains evidence. The unchanged original scientific sample/full
routes and family ceilings remain those in the WB1 design and packet.

The counted fixture entry point is
`runners.drive.cards.week5_bk_wb1_checkpoint_fixture`. It accepts only the
original `content_model` identity and `content_complete`, with empty config.
The inputs authenticate the model; no participant material enters its texts.
Proposed bounded admission is 600 combined CPU seconds, 900 wall seconds,
three GiB projected peak, two numerical threads, on an original backlog slot.
Owner review, a committed design and a complete fresh native replay remain
required before these successors become runnable scientific work.
