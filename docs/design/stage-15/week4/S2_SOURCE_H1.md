# S2-source.h1: exact UTF-16 materialization

The original complete 140-session cost probe costs 177.078125 CPU seconds.
Its full-source forecast is 2654.274609375 seconds, above the 1560.4375 source
allocation after retaining the frozen 1,800-second analytical reserve. The
original full source stays held. This is amendment B's separately frozen cheaper
exact implementation; the population, source definitions and output fields stay.

DESIGN CHECK: LESSONS 2-5 reread November 3; exact implementations require actual
producer/consumer parity. Replace only UTF-16 list-to-text materialization with
the native unsigned-short array representation, explicitly normalized to little
endian. Copy the original delta application with that same strict decoder.
Malformed operations and broken surrogate pairs still refuse. No parsing,
provenance, sentence, target, population or contrast definition changes.

**Case and check.** Require old/new complete delta equality on Unicode,
replacement, deletion, watched owners and invalid deltas; identical source
records on constructed branches; exact fresh native replay. The new measured
140-session source must equal every original session and the original summary
and index byte-for-byte before full admission. Timing and input bindings remain
separate identities. Full replay still reconstructs every source.

**Smaller route.** The original 3,600 CPU-second allowance, 1,800-second consumer
reserve, 1.5 source cost factor, full population and byte cap stay unchanged.
Charge original native/cost attempts, the original sixty-second reserve, an extra
sixty-second h1 validation/landing reserve, new native rehearsal and new cost probe.
If the complete-source forecast still does not fit, retain the cost hold and
prepare the packet's separately frozen whole-writer route before dispatch.
