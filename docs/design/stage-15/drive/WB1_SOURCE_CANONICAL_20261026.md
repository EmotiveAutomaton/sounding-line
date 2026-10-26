# WB1 canonical event provenance correction

The first real effects-cost attempt refused a mismatch between an occurrence's
source ordinal and its timestamp, before producing a cost or scientific result.
The preparation extractor gives simultaneous revision/deletion/insertion actions
the same mutable ordinal list. Collapsing a subsequent insertion extends that
list for a neighboring action too, while leaving its original timestamp intact.
The earlier fresh replay reproduced the same bug; the effects consumer caught it.

## DESIGN CHECK

LESSONS 2–5 reviewed October 26: preserve raw source and failed attempts, validate
actual serialized/native handlers, and reject changed measurement semantics.
For null and alternative inputs, each action's last ordinal must match its raw
clock without changing the existing tolerance. The canonical successor copies
each action independently before the unchanged collapse operation and retains
the previous canonical elapsed-clock fix. A deep copy of the whole list would
preserve its internal aliases and is insufficient.

Rebuild all 1,399 sessions and repeat independently. Authenticate the predecessor;
require equality of every field except action source-ordinal lists, including
population, event order/types/lengths/timestamps, intervals, writer split, bins,
source identities and aggregate counts. Record all changed action/session counts.
Known-answer cases cover a revision followed by a continuing typing burst,
the exact future-window anchor, immutable caller input, context cleanup, full
serialized replay in another process, and mutation refusal.

This is a canonical source correction under the existing data-defect rule, not
a smaller study, widened clock check or third shared-extractor healing attempt.
Prior completed preparation remains as historical evidence. Dependent corpus
effects are held until this successor lands. Coverage/timing values use fields
required to stay equal; that invariance must be demonstrated on the complete
corpus before retaining the earlier cost measurements. No scientific claim is
licensed by this repair. All execution, verification and build reserves continue
to count against WB1's original cumulative allowance.
