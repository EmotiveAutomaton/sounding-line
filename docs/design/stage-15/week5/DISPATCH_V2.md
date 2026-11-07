# Reviewed-plan dispatch through runtime v4

This is an operational successor to the unchanged Week 5 dispatcher. It uses
the reviewed v4 launcher and bounded-read accounting policy. The owner still
constructs and reviews every immutable plan, input, fixture, design and cost
scope before adding its exact hash and priority to the registry. The dispatcher
does not translate the queue, interpret outcomes, create retries or publish.

## DESIGN CHECK

LESSONS sections 3-5 informed the inherited admission contract; section 5's
identity, immutable receipt, unavailable-accounting and second-entry lessons
were reread for this successor. Completed, failed, paused, already claimed or
already launch-attempted roots cannot start again. Changed plan bytes,
duplicate identities and paths outside this campaign refuse. A resource or
budget refusal before launch remains waiting and may be checked again.

A separate immutable dispatch-attempt receipt is saved before calling the
launcher. This closes the ambiguous-handshake gap where a child might exist
before its attempt file appears. Any launch exception requires owner review;
no subsequent scan retries it. Native fixtures must exercise one real reviewed
arithmetic plan through v4 execution and independent verification, then show
that the next scan starts nothing. Targeted checks cover the same second-entry
rule after a simulated handshake exception and ordinary capacity waiting.

The old dispatcher retains its original registry and sources. The successor
receives a disjoint registry; neither registry may contain an unreviewed plan.
An owner stop request stops only the successor dispatcher, not workers already
launched. The original campaign freeze, drain, ceilings, slot allocation and
build wake remain unchanged. No new scientific or paid authority is introduced.
