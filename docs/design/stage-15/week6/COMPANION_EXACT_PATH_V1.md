# Exact interpreter spelling for the counted companion

The active, already-reviewed companion reader uses the literal interpreter
argument `.local/readers-venv/Scripts/python.exe`. Its other 27 arguments match
the reviewed absolute-path command exactly. The old verifier refuses the relative
spelling even though the observed working directory and native forwarding image
identify the same executable. The refusal and its cost remain recorded.

## DESIGN CHECK

Read: `docs/method/LESSONS.md` sections 3 through 5. Both scientific directions
receive the same ownership proof. An exact reviewed alias resolving to the same
hash-pinned executable may pass; another path, working directory, parent image,
argument, source byte, snapshot, owner, lease, deadline, thread count or GPU
setting must refuse. No arbitrary relative path is normalized.

The additive verifier accepts only the single literal spelling above, resolves it
against the already-checked companion root, requires a regular non-reparse file,
and requires that its resolved path equal the reviewed executable. It compares
the resulting complete argument vector with the existing fixed command inventory.
The actual parent and worker must still have identical raw command vectors and
the original native-image, creation-time, cwd and forwarding relationship.
Observation records are not rewritten. All source and image hashes, snapshot
inventory, exclusive ownership, counted reservation, deadline and CPU-only live
environment checks remain. The complete process census still rejects unknown
or unleased readers. No companion process, environment or file is changed.

Separate transition, policy, runtime and launcher modules bind this verifier;
historical modules and every historical plan pin remain unchanged. CPU accounting,
attempt execution, resource limits, scientific handlers and campaign clocks are
identical to the qualified predecessor. A new review schema prevents activation
through an old review file.

Qualification retains all 142 prior coexistence/boundary cases against the new
binding and adds eleven alias/binding cases. Together with the sixty original
chess cases and 31 recovery cases, the complete constructed bank has 244 cases.
It uses one counted CPU-only slot, two numerical threads, a 600 CPU-second and
1,200 wall-second bound, and the remaining original CH14 allowance. Exact live
companion proof is required before and after the tests. Full filing, a committed
design and a fresh full admission census are required before research release.
