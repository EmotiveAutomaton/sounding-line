# MD3 qualification: complete hash-call path compatibility

DESIGN CHECK: LESSONS 3-5. A valid path represented as either JSON text or a
Path object must hash identical bytes at every call site. Changed bytes must
still fail. Both native entry points must retain full scientific verification.

The first path repair correctly reached beyond the input hash, then failed on
an internal module-file string passed to the same Path-only hash helper. The
0.8125-CPU-second attempt produced no point fit or draw and remains an engineering
failure. Its boundary tests stubbed the numerical handler and therefore missed
dependency construction inside that handler. Retain the original failure and
first repair unchanged; neither provides native numerical qualification.

The v4 fixture scopes a path-compatible call wrapper around the original byte
hash function for the duration of execute or verify, then restores it in a
finally block. Only conversion to Path changes; the original reader computes
every digest. This covers input, module dependency and saved-record paths in
the actual child process. The numerical functions, source files and global
runtime on disk remain unchanged. The v4 exact admission driver changes only
the MD fixture registrations and adds this note to the frozen branch pins.

Regression checks exercise the actual fixture and actual numerical handler
through dependency construction up to a controlled pre-fit yield, reproduce
the first repair's internal-path failure, compare dependency digests with an
independent byte reader, preserve changed-source refusal, and verify restoration
after exceptions. No stubbed check is reported as numerical qualification.

This is shared engineering repair two, the last permitted repair in this
sequence. Preserve the source constructor and both failed attempts, charge all
costs to the original ceilings, then attempt the same full-design native pilot.
If it fails again, record the qualification as invalid and dispatch other
authorized work. All twelve full original cases remain necessary before human
admission; no control, population, draw count, null law or threshold is relaxed.
