# AT precision-control resource guard

This wrapper is restricted to the already dispatched failed scoring cases in
`AT_NUMERICAL_PRECISION.md`. It grants no scientific admission or model/source
selection. The scorer v4 and all original failed and diagnostic outputs remain
immutable. Largest-case fresh verification awaits the owner's counted native
runtime admission; standalone diagnostic launch is not the admission path.

The self-owned guard records its PID, native creation time, executable and
command line directly. It never searches for or kills another process. Before
model loading it requires 26 GiB of system commit headroom and 20 GiB of free
physical memory. Native Windows memory evidence is mandatory. Below 7 GiB
commit or physical headroom, it requests a sealed-block yield; below the 6 GiB
floor, or after 60 seconds without cooperative return, it records its measured
process CPU and exits only itself with code 75. A failed native memory query
also requests a bounded yield rather than pretending that resources are free.
The root runtime's descendant Job accounting remains authoritative on every
exit, including abrupt guard exits. Earlier costs remain charged.

The original scored block and fresh-check numerical implementation is unchanged.
Resource markers reach both the wrapper and the nested score directory. Each
guard invocation writes a distinct PID/creation-time receipt so a resumed phase
cannot overwrite earlier refused or yielded work. No monitor loads a model.
Plans still need a conservative projected peak of at least 20 GiB for the
1.4B control, with the full commit loading margin and current counted-slot
admission. Future models use measured peaks rather than parameter count alone.

## DESIGN CHECK

The native fixture proves pre-load refusal without invoking the model handler,
then actually executes the v4 handler with a tiny constructed transformer and
forces a memory signal after its first sealed block. The monitor causes a
cooperative yield with exactly one model invocation and the checkpoint intact.
An isolated constructed child exercises the real owned exit-75 path, and a
fresh process repeats the proof. Pure boundary checks cover the 26 GiB start,
7 GiB yield, 6 GiB hard floor and 60-second grace. No large model or human source
is used in this resource-control proof.
